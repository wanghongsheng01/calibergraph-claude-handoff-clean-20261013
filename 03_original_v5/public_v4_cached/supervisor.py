"""One bounded pure-Python cached-AST worker; no parser or solver execution."""
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
    os.write(EMERGENCY_FD, b'{"status":"TOTAL_WALL_STOP","denominator":48910,"unfinished":"NOT_RUN_OR_UNKNOWN"}\n')
    os._exit(124)


signal.signal(signal.SIGALRM, hard_stop)
signal.setitimer(signal.ITIMER_REAL, max(0.001, 59 - (time.monotonic() - START)))
signal.pthread_sigmask(signal.SIG_UNBLOCK, {signal.SIGALRM})
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import resource
import subprocess
import sys

HERE = Path(__file__).resolve().parent
RSS_LIMIT = 1024**3


class ProcTaskInfo(ctypes.Structure):
    _fields_ = [(n, ctypes.c_uint64) for n in ("virtual_size", "resident_size", "total_user", "total_system", "threads_user", "threads_system")] + [
        (n, ctypes.c_int32) for n in ("policy", "faults", "pageins", "cow_faults", "messages_sent", "messages_received", "syscalls_mach", "syscalls_unix", "csw", "threadnum", "numrunning", "priority")]


def save(path, value):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(path)


def main():
    global ACTIVE_PID, EMERGENCY_FD
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    if sys.platform != "darwin" or not (sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode):
        raise ValueError("Darwin -B -I -S required")
    out = args.out_dir.resolve()
    if out.exists() or out.parent != HERE / "runs" or any(p.is_symlink() for p in (args.out_dir, *args.out_dir.parents)):
        raise ValueError("new nonsymlink directory directly under public_v4_cached/runs required")
    out.mkdir(parents=True)
    EMERGENCY_FD = os.open(out / "emergency.jsonl", os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_APPEND, 0o600)
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_CPU, (57, 58))
    libc = ctypes.CDLL(None)
    probe = libc.proc_pidinfo
    probe.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_uint64, ctypes.c_void_p, ctypes.c_int]
    probe.restype = ctypes.c_int
    if ctypes.sizeof(ProcTaskInfo) != 96:
        raise ValueError("unexpected proc_taskinfo ABI")
    report = {"status": "NOT_RUN", "pair_denominator": 24455, "query_slot_denominator": 48910,
              "limits": {"total_wall_seconds": 60, "internal_alarm_seconds": 59,
                         "worker_wall_seconds": 56, "worker_cpu_soft_hard_seconds": [52, 53],
                         "combined_parent_worker_rss_bytes": RSS_LIMIT, "rss_poll_seconds": 0.1},
              "scope": "Pure Python cached-AST applicability; no parser/solver. Worker audit hook forbids child processes, network and nonstdlib imports.",
              "unmaterialized_slots": "NOT_RUN; if interrupted mid-slot, effects UNKNOWN; full declared denominator is unchanged",
              "program_sha256": {name: hashlib.sha256((HERE / name).read_bytes()).hexdigest() for name in ("scanner.py", "supervisor.py")},
              "sampled_peak_combined_rss_bytes": 0, "sampled_peak_worker_rss_bytes": 0}
    output = out / "supervisor_report.json"
    save(output, report)
    command = [sys.executable, "-B", "-I", "-S", str(HERE / "scanner.py"), "--out-dir", str(out), "--supervised"]
    env = {"PATH": "/usr/bin:/bin", "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1",
           "MKL_NUM_THREADS": "1", "VECLIB_MAXIMUM_THREADS": "1"}
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    started = time.monotonic()
    with (out / "worker.stdout").open("x") as stdout, (out / "worker.stderr").open("x") as stderr:
        child = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr,
                                 env=env, cwd=str(HERE), close_fds=True)
        ACTIVE_PID = child.pid
        report.update(status="RUNNING", pid=child.pid, command=command)
        save(output, report)
        try:
            while child.poll() is None:
                if time.monotonic() - START >= 57:
                    report["status"] = "TIMEOUT"
                    child.kill()
                    break
                values = []
                for pid in (os.getpid(), child.pid):
                    info = ProcTaskInfo()
                    returned = probe(pid, 4, 0, ctypes.byref(info), ctypes.sizeof(info))
                    if returned != ctypes.sizeof(info):
                        if pid == child.pid and child.poll() is not None:
                            break
                        report["status"] = "RSS_OBSERVATION_FAILED"
                        child.kill()
                        break
                    values.append(info.resident_size)
                if report["status"] != "RUNNING":
                    break
                if len(values) == 2:
                    report["sampled_peak_combined_rss_bytes"] = max(report["sampled_peak_combined_rss_bytes"], sum(values))
                    report["sampled_peak_worker_rss_bytes"] = max(report["sampled_peak_worker_rss_bytes"], values[1])
                    if sum(values) >= RSS_LIMIT:
                        report["status"] = "MEMORY_LIMIT"
                        child.kill()
                        break
                time.sleep(0.1)
        finally:
            if child.poll() is None:
                child.kill()
            child.wait(timeout=1)
            ACTIVE_PID = None
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    report.update(worker_returncode=child.returncode, wall_spawn_through_reap_seconds=time.monotonic() - started,
                  worker_cpu_user_seconds=after.ru_utime-before.ru_utime,
                  worker_cpu_system_seconds=after.ru_stime-before.ru_stime)
    worker_report = out / "scan_report.json"
    if worker_report.exists():
        result = json.loads(worker_report.read_text())
        report["worker_status"] = result.get("status")
        report["worker_summary"] = result.get("summary")
    if report["status"] == "RUNNING":
        report["status"] = "COMPLETE" if child.returncode == 0 and report.get("worker_status") == "COMPLETE_FULL_DENOMINATOR_CACHED_SCAN" else "WORKER_FAILED_OR_PARTIAL"
    report["total_wall_seconds"] = time.monotonic() - START
    report["measurement_role"] = "operational resource guard only, not comparative performance"
    save(output, report)
    return 0 if report["status"] == "COMPLETE" else 2


if __name__ == "__main__":
    sys.exit(main())
