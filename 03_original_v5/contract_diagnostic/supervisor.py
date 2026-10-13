"""One diagnostic child; <=24 s wall, CPU 14/15 s, sampled RSS <=1 GiB."""
import time
START = time.monotonic()
import os
import signal
ACTIVE_PID = None
EMERGENCY_FD = 2


def hard_stop(signum, frame):
    if ACTIVE_PID is not None:
        try:
            os.kill(ACTIVE_PID, signal.SIGKILL)
        except ProcessLookupError:
            pass
    os.write(EMERGENCY_FD, b'{"status":"WALL_24_STOP","uncheckpointed_effects":"UNKNOWN"}\n')
    os._exit(124)


signal.signal(signal.SIGALRM, hard_stop)
signal.pthread_sigmask(signal.SIG_UNBLOCK, {signal.SIGALRM})
signal.setitimer(signal.ITIMER_REAL, max(0.001, 24 - (time.monotonic() - START)))
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import resource
import subprocess
import sys

HERE = Path(__file__).resolve().parent
RSS_LIMIT = 1024 ** 3


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    temp = Path(str(path) + '.tmp')
    with temp.open('w') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
    temp.replace(path)


class ProcTaskInfo(ctypes.Structure):
    _fields_ = [(n, ctypes.c_uint64) for n in ('virtual_size', 'resident_size', 'total_user', 'total_system', 'threads_user', 'threads_system')] + [
        (n, ctypes.c_int32) for n in ('policy', 'faults', 'pageins', 'cow_faults', 'messages_sent', 'messages_received', 'syscalls_mach', 'syscalls_unix', 'csw', 'threadnum', 'numrunning', 'priority')]


def main():
    global ACTIVE_PID, EMERGENCY_FD
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--expected-manifest-sha256', required=True)
    ap.add_argument('--out-dir', type=Path, required=True)
    args = ap.parse_args()
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    if sys.platform != 'darwin' or not (sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode):
        raise ValueError('Darwin -B -I -S required')
    manifest_path = HERE / 'PREPARED_MANIFEST.json'
    if sha(manifest_path) != args.expected_manifest_sha256:
        raise ValueError('prepared manifest changed')
    manifest = json.loads(manifest_path.read_text())
    for raw, digest in manifest['files'].items():
        path = Path(raw)
        if path != path.resolve() or not path.is_file() or sha(path) != digest:
            raise ValueError('frozen diagnostic input/program changed: ' + raw)
    out = args.out_dir.resolve()
    if out.exists() or not out.is_relative_to(HERE / 'runs') or any(p.is_symlink() for p in [args.out_dir, *args.out_dir.parents]):
        raise ValueError('new nonsymlink output directory under contract_diagnostic/runs required')
    out.mkdir(parents=True)
    EMERGENCY_FD = os.open(out / 'emergency.jsonl', os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_APPEND, 0o600)
    report = {'status': 'NOT_RUN', 'manifest_sha256': args.expected_manifest_sha256,
              'cell_denominator': 24, 'result_valid': False, 'sampled_peak_rss_bytes': 0,
              'sampled_max_kernel_threads': 0, 'limits': {'cpu_soft_hard_seconds': [14, 15],
              'total_supervisor_wall_alarm_seconds': 24, 'worker_wall_alarm_seconds': 24,
              'supervisor_stop_work_at_seconds': 23, 'rss_sampled_soft_bytes': RSS_LIMIT,
              'rss_sampling_seconds': 0.05, 'solver_threads': 1},
              'scope': 'One no-network computation child. Child itself does not create subprocesses; temporary upstream monitor threads are observed. RSS is sampled, not a continuous hard cap.'}
    output = out / 'supervisor_report.json'
    save(out / 'initial_not_run.json', report)
    save(output, report)
    libc = ctypes.CDLL(None)
    probe = libc.proc_pidinfo
    probe.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_uint64, ctypes.c_void_p, ctypes.c_int]
    probe.restype = ctypes.c_int
    if ctypes.sizeof(ProcTaskInfo) != 96:
        raise ValueError('proc_taskinfo layout mismatch')
    command = [sys.executable, '-B', '-I', '-S', str(HERE / 'worker.py'),
               '--expected-manifest-sha256', args.expected_manifest_sha256, '--out-dir', str(out)]
    report.update(status='ATTEMPTED_EFFECT_UNKNOWN', command=command)
    save(output, report)
    child_environment = {'PATH': '/usr/bin:/bin', 'OMP_NUM_THREADS': '1', 'OPENBLAS_NUM_THREADS': '1',
                         'MKL_NUM_THREADS': '1', 'VECLIB_MAXIMUM_THREADS': '1'}
    before_usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    began = time.monotonic()
    with (out / 'stdout.log').open('wb') as stdout, (out / 'stderr.log').open('wb') as stderr:
        child = subprocess.Popen(command, cwd=out, env=child_environment, stdin=subprocess.DEVNULL,
                                 stdout=stdout, stderr=stderr, close_fds=True)
        ACTIVE_PID = child.pid
        report['child_pid'] = child.pid
        save(output, report)
        try:
            while child.poll() is None:
                if time.monotonic() - START >= 23:
                    report['stop_reason'] = 'WALL_BUDGET_RESERVE_FOR_REAP_AND_REPORT'
                    child.kill(); break
                info = ProcTaskInfo()
                count = probe(child.pid, 4, 0, ctypes.byref(info), ctypes.sizeof(info))
                if count != ctypes.sizeof(info):
                    if child.poll() is None:
                        report['stop_reason'] = 'RSS_OBSERVATION_UNAVAILABLE'
                        child.kill()
                    break
                report['sampled_peak_rss_bytes'] = max(report['sampled_peak_rss_bytes'], int(info.resident_size))
                report['sampled_max_kernel_threads'] = max(report['sampled_max_kernel_threads'], int(info.threadnum))
                if info.resident_size >= RSS_LIMIT:
                    report['stop_reason'] = 'RSS_SAMPLED_SOFT_LIMIT'
                    child.kill(); break
                time.sleep(0.05)
            report['exit_code'] = child.wait(timeout=0.5)
        finally:
            if child.poll() is None:
                child.kill(); child.wait(timeout=0.5)
            ACTIVE_PID = None
    report['full_child_wall_seconds'] = time.monotonic() - began
    after_usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    report['full_child_cpu_seconds'] = after_usage.ru_utime + after_usage.ru_stime - before_usage.ru_utime - before_usage.ru_stime
    worker_path = out / 'worker_report.json'
    if worker_path.exists():
        worker = json.loads(worker_path.read_text())
        report.update(worker_report_sha256=sha(worker_path), worker_status=worker.get('status'),
                      diagnostic_summary=worker.get('summary'), original_pair=worker.get('original_pair'))
        report['result_valid'] = (report['exit_code'] == 0 and 'stop_reason' not in report
                                  and worker.get('status') == 'COMPLETE_DIAGNOSTIC'
                                  and worker.get('registered_files_unchanged_after_run') is True)
    else:
        report['worker_status'] = 'NO_REPORT_EFFECT_UNKNOWN'
    report['status'] = 'COMPLETE_DIAGNOSTIC' if report['result_valid'] else 'FAILURE_OR_PARTIAL_RETAINED'
    report['supervisor_wall_seconds_before_final_write'] = time.monotonic() - START
    save(output, report)
    print(json.dumps({'status': report['status'], 'report': str(output)}), flush=True)
    os._exit(0 if report['result_valid'] else 2)


if __name__ == '__main__':
    main()
