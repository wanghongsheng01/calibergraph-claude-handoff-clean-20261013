"""One resource-capability check; no SQL, solver, datasets or network."""
import os
import sys
import time
import resource
import signal

START = time.monotonic()
resource.setrlimit(resource.RLIMIT_CPU, (1, 1))
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
signal.signal(signal.SIGALRM, lambda *_: os._exit(124))
signal.setitimer(signal.ITIMER_REAL, 3.0)

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'capability_probe_once'
OUT.mkdir()
report = {'scientific_runs': 0, 'query_calls': 0, 'attempt': 1,
          'retry_allowed': False, 'status': 'NOTCOMPLETED', 'checks': {}}
try:
    assert sys.platform == 'darwin'
    assert sys.version_info[:2] == (3, 12)
    assert sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode
    before = os.getpriority(os.PRIO_PROCESS, 0)
    os.setpriority(os.PRIO_PROCESS, 0, max(before, 15))
    report['checks']['nice'] = os.getpriority(os.PRIO_PROCESS, 0)
    assert report['checks']['nice'] >= 15
    report['checks']['cpu_limit'] = list(resource.getrlimit(resource.RLIMIT_CPU))
    report['checks']['load_1m'] = os.getloadavg()[0]
    memory = subprocess.run(['/usr/bin/memory_pressure', '-Q'], check=True,
                            capture_output=True, text=True, timeout=0.8)
    found = re.search(r'System-wide memory free percentage:\s*(\d+)%', memory.stdout)
    assert found is not None
    report['checks']['memory_free_percent'] = int(found.group(1))
    report['memory_stdout'] = memory.stdout
    own_ps = subprocess.run(['/bin/ps', '-p', str(os.getpid()), '-o',
                             'pid=,ppid=,pgid=,time=,rss='], check=True,
                            capture_output=True, text=True, timeout=0.8)
    assert own_ps.stdout.strip()
    report['own_process_ps'] = own_ps.stdout
    pid = os.fork()
    if pid == 0:
        os._exit(0)
    reaped_pid, wait_status, usage = os.wait4(pid, 0)
    assert reaped_pid == pid and os.WIFEXITED(wait_status) and os.WEXITSTATUS(wait_status) == 0
    report['checks']['wait4_child_cpu_s'] = usage.ru_utime + usage.ru_stime
    report['checks']['wait4_child_peak_rss_bytes'] = usage.ru_maxrss
    assert 0 < usage.ru_maxrss < 128 * 1024 * 1024
    assert report['checks']['load_1m'] <= 4.0
    assert report['checks']['memory_free_percent'] >= 25
    report['status'] = 'RESOURCE_CAPABILITIES_OBSERVED'
except BaseException as error:
    report['error'] = {'type': type(error).__name__, 'message': str(error)}
own = resource.getrusage(resource.RUSAGE_SELF)
children = resource.getrusage(resource.RUSAGE_CHILDREN)
report['usage_before_receipt'] = {
    'self_cpu_s': own.ru_utime + own.ru_stime,
    'reaped_children_cpu_s': children.ru_utime + children.ru_stime,
    'self_peak_rss_bytes': own.ru_maxrss,
    'wall_s': time.monotonic() - START,
    'tail': 'Final JSON write/print/shutdown excluded from sample; charged within registered 10s preparation reserve.'}
assert own.ru_maxrss < 128 * 1024 * 1024
with (OUT / 'receipt.json').open('x') as handle:
    json.dump(report, handle, indent=2)
    handle.write('\n')
print(json.dumps(report))
raise SystemExit(0 if report['status'] == 'RESOURCE_CAPABILITIES_OBSERVED' else 1)
