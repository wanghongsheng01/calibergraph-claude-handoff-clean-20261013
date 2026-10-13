"""Sequential single-computation-child supervisor; existing DEV, not benchmark."""
import time
START = time.monotonic()
import signal
import os
ACTIVE_PID = None
EMERGENCY_FD = 2


def hard_stop(signum, frame):
    if ACTIVE_PID is not None:
        try:
            os.kill(ACTIVE_PID, signal.SIGKILL)
        except ProcessLookupError:
            pass
    os.write(EMERGENCY_FD, b'{"status":"SUPERVISOR_WALL_STOP","last_checkpoint_effects":"UNKNOWN"}\n')
    os._exit(124)


signal.signal(signal.SIGALRM, hard_stop)
signal.setitimer(signal.ITIMER_REAL, max(0.001, 89 - (time.monotonic() - START)))
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
ARMS = ("official", "flat", "product", "selector")
RSS_LIMIT = 1024 * 1024 * 1024


class ProcTaskInfo(ctypes.Structure):
    _fields_ = [(n, ctypes.c_uint64) for n in ("virtual_size", "resident_size", "total_user", "total_system", "threads_user", "threads_system")] + [
        (n, ctypes.c_int32) for n in ("policy", "faults", "pageins", "cow_faults", "messages_sent", "messages_received", "syscalls_mach", "syscalls_unix", "csw", "threadnum", "numrunning", "priority")]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    tmp = path.with_suffix(".tmp")
    with tmp.open("w") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n"); stream.flush(); os.fsync(stream.fileno())
    tmp.replace(path)


def main():
    global ACTIVE_PID, EMERGENCY_FD
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-lock", type=Path, required=True)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--case-limit", type=int, default=2)
    parser.add_argument("--case-start", type=int, default=0)
    args = parser.parse_args()
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    if sys.platform != "darwin" or not (sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode):
        raise ValueError("Darwin -B -I -S required")
    fixture = json.loads(args.fixture.read_text())
    if not 1 <= args.case_limit <= 6 or args.case_start < 0 or args.case_start + args.case_limit > len(fixture["cases"]):
        raise ValueError("invalid retained-denominator selection")
    if args.out_dir.exists() or not args.out_dir.resolve().is_relative_to(HERE.parent):
        raise ValueError("use a new result directory within today_20261011")
    args.out_dir.mkdir(parents=True)
    EMERGENCY_FD = os.open(args.out_dir / "emergency.jsonl", os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_APPEND, 0o600)
    report = {"status": "RUNNING", "data_role": "EXISTING_EXPOSED_ANALYTICAL_DEV_NOT_NEW_TEST", "performance_claim": False,
              "fixture_sha256": sha(args.fixture), "runtime_lock_sha256": sha(args.runtime_lock),
              "worker_sha256": sha(HERE / "case_worker.py"), "supervisor_sha256": sha(Path(__file__)),
              "limits": {"per_child_cpu_soft_hard_seconds": [14, 15], "per_child_wall_seconds": 25,
                         "total_internal_wall_seconds": 89, "child_rss_soft_bytes": RSS_LIMIT, "solver_threads": 1},
              "thread_note": "One computation child at a time; mo-imports temporary monitor threads are observed, not mislabeled as solver workers.",
              "full_case_denominator": len(fixture["cases"]), "full_arm_denominator": len(fixture["cases"]) * len(ARMS),
              "scheduled_case_start": args.case_start, "scheduled_case_limit": args.case_limit,
              "cases": [{"id": c["id"], "expected": c["expected"], "status": "NOT_RUN", "arms": {a: {"status": "NOT_RUN"} for a in ARMS}} for c in fixture["cases"]],
              "rejection_queries": [{"id": x["id"], "status": "NOT_RUN", "reason": "outside this finite diagnostic"} for x in fixture.get("rejection_queries", [])],
              "spotit_status": "NOT_RUN_LOCAL_SOURCE_CLOSURE_INCOMPLETE_NOT_FULL_SPOTIT_PLUS_REPRODUCTION"}
    output = args.out_dir / "supervisor_report.json"
    save(args.out_dir / "initial_not_run.json", report)
    save(output, report)
    process_symbols = ctypes.CDLL(None)
    probe = process_symbols.proc_pidinfo
    probe.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_uint64, ctypes.c_void_p, ctypes.c_int]
    probe.restype = ctypes.c_int
    if ctypes.sizeof(ProcTaskInfo) != 96:
        raise ValueError("wrong Darwin proc_taskinfo layout")
    env = {"PATH": "/usr/bin:/bin", "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1", "VECLIB_MAXIMUM_THREADS": "1"}
    for index in range(args.case_start, args.case_start + args.case_limit):
        entry = report["cases"][index]
        remaining = 89 - (time.monotonic() - START)
        if remaining < 2:
            entry["not_run_reason"] = "global budget exhausted"
            continue
        case_dir = args.out_dir / f"case_{index:02d}"
        case_dir.mkdir()
        entry.update(status="STARTED", case_directory=str(case_dir), sampled_peak_rss_bytes=0, sampled_max_kernel_threads=0)
        save(output, report)
        command = [sys.executable, "-B", "-I", "-S", str(HERE / "case_worker.py"), "--runtime-lock", str(args.runtime_lock.resolve()),
                   "--expected-lock-sha256", report["runtime_lock_sha256"], "--fixture", str(args.fixture.resolve()),
                   "--expected-fixture-sha256", report["fixture_sha256"], "--case-index", str(index), "--out-dir", str(case_dir.resolve())]
        began = time.monotonic()
        with (case_dir / "stdout.log").open("wb") as stdout, (case_dir / "stderr.log").open("wb") as stderr:
            child = subprocess.Popen(command, cwd=case_dir, env=env, stdout=stdout, stderr=stderr, stdin=subprocess.DEVNULL, close_fds=True)
            ACTIVE_PID = child.pid
            entry["pid"] = child.pid
            try:
                while child.poll() is None:
                    now = time.monotonic()
                    if now - began >= 25 or now - START >= 88:
                        entry["stop_reason"] = "WALL_LIMIT"
                        child.kill(); break
                    info = ProcTaskInfo()
                    count = probe(child.pid, 4, 0, ctypes.byref(info), ctypes.sizeof(info))
                    if count != ctypes.sizeof(info):
                        if child.poll() is None:
                            entry["stop_reason"] = "RSS_OBSERVATION_UNAVAILABLE"
                            child.kill()
                        break
                    entry["sampled_peak_rss_bytes"] = max(entry["sampled_peak_rss_bytes"], int(info.resident_size))
                    entry["sampled_max_kernel_threads"] = max(entry["sampled_max_kernel_threads"], int(info.threadnum))
                    if info.resident_size >= RSS_LIMIT:
                        entry["stop_reason"] = "RSS_SOFT_LIMIT"
                        child.kill(); break
                    time.sleep(0.1)
                entry["exit_code"] = child.wait(timeout=1)
            finally:
                if child.poll() is None:
                    child.kill(); child.wait(timeout=1)
                ACTIVE_PID = None
        entry["supervised_wall_seconds"] = time.monotonic() - began
        entry["status"] = "PROCESS_EXITED" if "stop_reason" not in entry else "RESOURCE_STOP"
        worker_output = case_dir / "worker_report.json"
        if worker_output.exists():
            worker = json.loads(worker_output.read_text())
            entry["worker_status"] = worker["status"]
            entry["arms"] = worker["arms"]
            entry["point_checks"] = worker["point_checks"]
            entry["worker_report_sha256"] = sha(worker_output)
            entry["success"] = entry["exit_code"] == 0 and worker["status"] == "COMPLETE_DEV_AGREEMENT"
        else:
            entry["success"] = False
            entry["worker_status"] = "NO_REPORT_EFFECT_UNKNOWN"
        save(output, report)
    selected = report["cases"][args.case_start:args.case_start + args.case_limit]
    report["status"] = "COMPLETE_SELECTED_DEV_AGREEMENT" if all(x.get("success") for x in selected) else "COMPLETE_WITH_FAILURES_OR_NOT_RUN"
    report["resource_wall_seconds_before_final_write"] = time.monotonic() - START
    report["scientific_limitations"] = ["Exposed constructed DEV; no new held-out test or human gold.", "Shared Environment facts and unequal solver sub-budgets: timings are resource audits, not fair comparative cost results.", "No full SpotIt+ reproduction, generic strong rewrite baseline, novelty or SIGMOD847 overlap clearance."]
    save(output, report)
    print(json.dumps({"status": report["status"], "report": str(output)}), flush=True)
    os._exit(0 if report["status"] == "COMPLETE_SELECTED_DEV_AGREEMENT" else 2)


if __name__ == "__main__":
    main()
