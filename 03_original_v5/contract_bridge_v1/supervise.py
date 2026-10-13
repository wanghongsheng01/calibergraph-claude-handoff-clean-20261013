"""Single computation-child supervisor; only the root executor may invoke it."""
import time
START = time.monotonic()
import os
import signal
ACTIVE_PID = None


def stop(signum, frame):
    if ACTIVE_PID is not None:
        try:
            os.kill(ACTIVE_PID, signal.SIGKILL)
        except ProcessLookupError:
            pass
    os.write(2, b'CONTRACT_BRIDGE_SUPERVISOR_WALL_STOP_LAST_EFFECT_UNKNOWN\n')
    os._exit(124)


signal.signal(signal.SIGALRM, stop)
signal.setitimer(signal.ITIMER_REAL, max(0.001, 26 - (time.monotonic() - START)))
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


class ProcTaskInfo(ctypes.Structure):
    _fields_ = [(name, ctypes.c_uint64) for name in (
        "virtual_size", "resident_size", "total_user", "total_system", "threads_user", "threads_system")] + [
        (name, ctypes.c_int32) for name in ("policy", "faults", "pageins", "cow_faults", "messages_sent", "messages_received",
        "syscalls_mach", "syscalls_unix", "csw", "threadnum", "numrunning", "priority")]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    global ACTIVE_PID
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-lock", type=Path, required=True)
    parser.add_argument("--runtime-lock-sha256", required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    if sys.platform != "darwin" or not (sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode):
        raise ValueError("Darwin -B -I -S required")
    if sha(HERE / "MANIFEST.json") != args.manifest_sha256:
        raise ValueError("manifest changed")
    manifest = json.loads((HERE / "MANIFEST.json").read_text())
    for item in manifest["files"]:
        file = Path(item["path"])
        if file != file.resolve() or not file.is_file() or sha(file) != item["sha256"]:
            raise ValueError("locked source changed")
    if sha(args.runtime_lock) != args.runtime_lock_sha256:
        raise ValueError("runtime lock changed")
    out = args.out_dir.absolute(); allowed = HERE / "runs"
    if out.exists() or out.is_symlink() or out != out.resolve() or out == allowed or not out.is_relative_to(allowed):
        raise ValueError("new unaliased output directory under contract_bridge_v1/runs required")
    for parent in [out.parent, *out.parent.parents]:
        if parent.is_symlink():
            raise ValueError("output ancestry is symlinked")
        if parent == HERE:
            break
    out.mkdir(parents=True)
    report = {"status": "NOT_RUN", "case_id": args.case_id, "manifest_sha256": args.manifest_sha256,
              "runtime_lock_sha256": args.runtime_lock_sha256, "sampled_peak_rss_bytes": 0, "sampled_max_threads": 0,
              "limits": {"child_cpu_soft_hard_seconds": [14, 15], "child_wall_alarm_seconds": 24,
                         "supervisor_child_wall_seconds": 25, "supervisor_internal_wall_seconds": 26,
                         "child_rss_soft_bytes": 1024 ** 3, "rss_sampling_seconds": 0.05},
              "boundary": "one computation child; RSS sampled, not a hard RSS cap; initial interpreter launch excluded from own timer"}
    output = out / "supervision.json"

    def save():
        tmp = out / "supervision.json.tmp"
        if tmp.is_symlink():
            raise ValueError("temporary symlink")
        with tmp.open("w") as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2); stream.write("\n"); stream.flush(); os.fsync(stream.fileno())
        tmp.replace(output)

    save()
    probe = ctypes.CDLL(None).proc_pidinfo
    probe.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_uint64, ctypes.c_void_p, ctypes.c_int]
    probe.restype = ctypes.c_int
    if ctypes.sizeof(ProcTaskInfo) != 96:
        raise ValueError("proc_taskinfo size mismatch")
    command = [sys.executable, "-B", "-I", "-S", str(HERE / "run_diagnostic.py"),
               "--runtime-lock", str(args.runtime_lock.resolve()), "--runtime-lock-sha256", args.runtime_lock_sha256,
               "--manifest-sha256", args.manifest_sha256, "--case-id", args.case_id, "--out-dir", str(out)]
    clean_env = {"PATH": "/usr/bin:/bin", "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1", "VECLIB_MAXIMUM_THREADS": "1"}
    began = time.monotonic(); before = resource.getrusage(resource.RUSAGE_CHILDREN)
    with (out / "stdout.log").open("wb") as stdout, (out / "stderr.log").open("wb") as stderr:
        child = subprocess.Popen(command, cwd=out, env=clean_env, stdout=stdout, stderr=stderr,
                                 stdin=subprocess.DEVNULL, close_fds=True)
        ACTIVE_PID = child.pid; report.update(status="RUNNING", pid=child.pid, command=command); save()
        try:
            while child.poll() is None:
                if time.monotonic() - began >= 25 or time.monotonic() - START >= 25.5:
                    report["stop_reason"] = "WALL_LIMIT"; child.kill(); break
                info = ProcTaskInfo()
                size = probe(child.pid, 4, 0, ctypes.byref(info), ctypes.sizeof(info))
                if size != ctypes.sizeof(info):
                    if child.poll() is None:
                        report["stop_reason"] = "RSS_OBSERVATION_UNAVAILABLE"; child.kill()
                    break
                report["sampled_peak_rss_bytes"] = max(report["sampled_peak_rss_bytes"], int(info.resident_size))
                report["sampled_max_threads"] = max(report["sampled_max_threads"], int(info.threadnum))
                if info.resident_size >= 1024 ** 3:
                    report["stop_reason"] = "RSS_SOFT_LIMIT"; child.kill(); break
                time.sleep(0.05)
            report["exit_code"] = child.wait(timeout=1)
        finally:
            if child.poll() is None:
                child.kill(); child.wait(timeout=1)
            ACTIVE_PID = None
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    report.update(status="EXITED", child_process_wall_seconds=time.monotonic() - began,
                  child_cpu_seconds=(after.ru_utime + after.ru_stime) - (before.ru_utime + before.ru_stime))
    save()
    return report["exit_code"]


if __name__ == "__main__":
    code = main()
    sys.stdout.flush(); sys.stderr.flush()
    os._exit(code)
