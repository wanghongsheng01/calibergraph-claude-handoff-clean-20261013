"""One short local worker; observe resources without touching other tasks."""
import argparse
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import signal
import subprocess
import sys
import time


def digest(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def probe():
    vm = subprocess.run(['/usr/bin/vm_stat'], capture_output=True, text=True, timeout=3)
    nc = subprocess.run(['/usr/sbin/sysctl', '-n', 'hw.ncpu', 'hw.memsize'], capture_output=True, text=True, timeout=3)
    if vm.returncode or nc.returncode:
        raise RuntimeError('RESOURCE_PROBE_UNAVAILABLE')
    page = int(re.search(r'page size of (\d+)', vm.stdout).group(1))
    fields = {k: int(v) for k, v in re.findall(r'^([^:\n]+):\s+(\d+)\.', vm.stdout, re.M)}
    cpu, memory = map(int, nc.stdout.split())
    return {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'load': list(os.getloadavg()), 'logical_cpu': cpu, 'memory_bytes': memory,
            'compressor_bytes': fields['Pages occupied by compressor'] * page,
            'free_bytes': fields['Pages free'] * page, 'vm_stat': fields}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--freeze', required=True)
    ap.add_argument('--kind', choices=['static_or_sqlite', 'solver'], default='static_or_sqlite')
    ap.add_argument('worker')
    args = ap.parse_args()
    root = Path(__file__).resolve().parents[1]
    out = Path(args.out).resolve()
    if not out.is_relative_to(root) or out.exists():
        raise SystemExit('Output must be a fresh directory within the new project')
    out.mkdir(parents=True)
    freeze = json.loads(Path(args.freeze).read_text())
    receipt = {'start_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
               'freeze_sha256': digest(args.freeze), 'supervisor_sha256': digest(__file__),
               'kind': args.kind, 'status': 'PRECHECK', 'worker': str(Path(args.worker).resolve()),
               'resource_policy': json.loads((root/'governance/RESOURCE_POLICY.json').read_text()),
               'sampled_peak_rss_bytes': 0, 'observations': 0}
    def save():
        (out/'receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
    lock = (root/'runs/.single_worker.lock').open('a')
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        receipt['status'] = 'NOT_RUN_CONCURRENCY_LOCK'
        save()
        return 2
    try:
        for item in freeze['files']:
            if digest(item['path']) != item['sha256']:
                raise RuntimeError('FROZEN_FILE_IDENTITY_MISMATCH: '+item['path'])
        receipt['preflight'] = probe()
    except Exception as e:
        receipt['status'] = 'NOT_RUN_PRECHECK_FAILED'
        receipt['reason'] = str(e)
        save()
        return 2
    if receipt['preflight']['load'][0] > 6:
        receipt['status'] = 'NOT_RUN_LOAD_LIMIT'
        save()
        return 2
    if args.kind == 'solver' and receipt['preflight']['compressor_bytes'] > 6 * 1024**3:
        receipt['status'] = 'NOT_RUN_MEMORY_PRESSURE'
        save()
        return 2
    limit = receipt['resource_policy'][args.kind]
    max_wall = limit.get('max_wall_seconds', 60)
    max_rss = limit['max_rss_mib'] * 1024**2
    def child_setup():
        os.nice(15)
        resource.setrlimit(resource.RLIMIT_CPU, (30, 31))
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    env = os.environ.copy()
    env.update({k: '1' for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']})
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    env['CALIBERGRAPH_RUN_OUT'] = str(out)
    start = time.monotonic()
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    with (out/'stdout.log').open('w') as stdout, (out/'stderr.log').open('w') as stderr:
        proc = subprocess.Popen([sys.executable, '-B', '-I', str(Path(args.worker).resolve())],
                                cwd=root, env=env, stdout=stdout, stderr=stderr,
                                preexec_fn=child_setup, start_new_session=True)
        receipt.update({'status': 'RUNNING', 'pid': proc.pid})
        save()
        stop = None
        while proc.poll() is None:
            if time.monotonic() - start > max_wall:
                stop = 'STOP_WALL_LIMIT'
            obs = subprocess.run(['/bin/ps', '-p', str(proc.pid), '-o', 'rss='], capture_output=True, text=True)
            if obs.returncode == 0 and obs.stdout.strip():
                rss = int(obs.stdout.strip()) * 1024
                receipt['observations'] += 1
                receipt['sampled_peak_rss_bytes'] = max(receipt['sampled_peak_rss_bytes'], rss)
                if rss > max_rss:
                    stop = 'STOP_RSS_LIMIT'
            elif proc.poll() is None:
                stop = 'STOP_UNOBSERVABLE'
            if stop:
                os.killpg(proc.pid, signal.SIGTERM)
                try:
                    proc.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    os.killpg(proc.pid, signal.SIGKILL)
                break
            time.sleep(0.05)
        code = proc.wait()
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    receipt.update({'status': stop or ('RETURNED' if code == 0 else 'WORKER_FAILED'),
                    'worker_exit_code': code, 'wall_seconds': time.monotonic()-start,
                    'child_cpu_user_seconds_including_ps': after.ru_utime-before.ru_utime,
                    'child_cpu_system_seconds_including_ps': after.ru_stime-before.ru_stime,
                    'cpu_note': 'Includes ps sampling overhead; worker-specific self usage is reported by the worker.',
                    'monitor_note': 'Sampled RSS, not a hard allocation cap; no other task was modified.',
                    'end_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()})
    try:
        receipt['postflight'] = probe()
    except Exception as e:
        receipt['postflight_error'] = str(e)
    save()
    print(json.dumps(receipt, indent=2))
    return code if code else (2 if stop else 0)


if __name__ == '__main__':
    raise SystemExit(main())
