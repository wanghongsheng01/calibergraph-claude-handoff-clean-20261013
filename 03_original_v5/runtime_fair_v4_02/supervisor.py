"""Full-denominator, sequential independent-arm cost/correctness supervisor."""
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
    os.write(EMERGENCY_FD, b'{"status":"TOTAL_WALL_STOP","last_checkpoint_effects":"UNKNOWN"}\n')
    os._exit(124)


signal.signal(signal.SIGALRM, hard_stop)
signal.setitimer(signal.ITIMER_REAL, max(0.001, 89 - (time.monotonic() - START)))
signal.pthread_sigmask(signal.SIG_UNBLOCK, {signal.SIGALRM})
import argparse
import ctypes
import json
from pathlib import Path
import resource
import subprocess
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from common import sha, save, jobs_for
RSS_LIMIT = 1024 ** 3


class ProcTaskInfo(ctypes.Structure):
    _fields_ = [(n, ctypes.c_uint64) for n in ("virtual_size", "resident_size", "total_user", "total_system", "threads_user", "threads_system")] + [
        (n, ctypes.c_int32) for n in ("policy", "faults", "pageins", "cow_faults", "messages_sent", "messages_received", "syscalls_mach", "syscalls_unix", "csw", "threadnum", "numrunning", "priority")]


def main():
    global ACTIVE_PID, EMERGENCY_FD
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-lock", type=Path, required=True)
    parser.add_argument("--suite", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--kind", choices=("cost", "differential"), required=True)
    parser.add_argument("--job-start", type=int, default=0)
    parser.add_argument("--job-limit", type=int, default=5)
    args = parser.parse_args()
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    if sys.platform != "darwin" or not (sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode):
        raise ValueError("Darwin -B -I -S required")
    suite = json.loads(args.suite.read_text())
    jobs = jobs_for(suite, args.kind)
    if args.job_start < 0 or args.job_limit < 1 or args.job_start + args.job_limit > len(jobs):
        raise ValueError("invalid registered job selection")
    if args.out_dir.exists() or not args.out_dir.resolve().is_relative_to(HERE.parent):
        raise ValueError("use a new result directory under today_20261011")
    args.out_dir.mkdir(parents=True)
    EMERGENCY_FD = os.open(args.out_dir / "emergency.jsonl", os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_APPEND, 0o600)
    program_hashes = {name: sha(HERE / name) for name in ("common.py", "worker.py", "supervisor.py", "query_differential.py")}
    for job in jobs:
        job.update(status="NOT_RUN", final_decision="NOT_RUN", attempts=[], fallback={"status": "NOT_RUN"})
    report = {"status": "RUNNING", "kind": args.kind, "data_role": suite["data_role"],
              "source_provenance": suite.get("source_provenance"), "suite_sha256": sha(args.suite),
              "runtime_lock_sha256": sha(args.runtime_lock), "program_sha256": program_hashes,
              "full_case_denominator": len(suite["cases"]), "full_job_denominator": len(jobs),
              "selected_job_start": args.job_start, "selected_job_limit": args.job_limit, "jobs": jobs,
              "limits": {"per_child_cpu_soft_hard_seconds": [14, 15], "per_child_wall_supervisor_seconds": 25,
                         "per_child_wall_alarm_seconds": 24, "total_internal_wall_seconds": 89,
                         "child_rss_soft_bytes": RSS_LIMIT, "solver_threads": 1},
              "cost_contract": "Common raw-identifier gate for all arms; rejected input stays in denominator without equivalence decision. Six arms include pure-fragment AND canonicalization. Fresh process/Environment per admitted arm. Full schema, exact rows and IC unchanged. Common SAT/exact-row guard. Uniform remaining-budget policy. All failures and fallback costs retained.",
              "fallback_policy": "FrontendUnsupported -> no parser/solver/fallback; admitted Candidate or canonical Ineligible/normalization miss -> raw official; candidate unknown -> raw official only if >=500ms remains; exceptions or invalid witnesses are errors, not silently erased.",
              "oracle_domain_policy": "SAT replay requires common int64-domain audit; out-of-domain/errors retain witnesses and denominator and cannot count as success or a win.",
              "correctness_requirement": "Cost numbers alone do not establish equal guarantees. Per-query mapping validation/proof and replay checks must be assessed separately before comparative claims.",
              "thread_observation": "One computation child. Solver threads=1/parallel disabled; temporary mo-imports Python monitor threads recorded.",
              "clock_boundary": "89s guard starts after initial stdlib time import; per-child supervisor wall includes spawn/startup through reap. Worker final checkpoint excludes final write, full process wall/CPU measured here."}
    output = args.out_dir / "supervisor_report.json"
    save(args.out_dir / "initial_not_run.json", report)
    save(output, report)
    libc = ctypes.CDLL(None)
    probe = libc.proc_pidinfo
    probe.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_uint64, ctypes.c_void_p, ctypes.c_int]
    probe.restype = ctypes.c_int
    if ctypes.sizeof(ProcTaskInfo) != 96:
        raise ValueError("proc_taskinfo layout mismatch")
    child_env = {"PATH": "/usr/bin:/bin", "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1", "VECLIB_MAXIMUM_THREADS": "1"}
    for index in range(args.job_start, args.job_start + args.job_limit):
        job = jobs[index]
        if time.monotonic() - START >= 86:
            job["not_run_reason"] = "remaining total budget below 3 seconds"
            continue
        job_dir = args.out_dir / f"job_{index:04d}"
        job_dir.mkdir()
        job.update(status="STARTED", output_directory=str(job_dir), sampled_peak_rss_bytes=0, sampled_max_kernel_threads=0)
        save(output, report)
        command = [sys.executable, "-B", "-I", "-S", str(HERE / "worker.py"), "--runtime-lock", str(args.runtime_lock.resolve()),
                   "--expected-lock-sha256", report["runtime_lock_sha256"], "--suite", str(args.suite.resolve()),
                   "--expected-suite-sha256", report["suite_sha256"], "--kind", args.kind, "--job-index", str(index),
                   "--out-dir", str(job_dir.resolve()), "--expected-programs", json.dumps(program_hashes, sort_keys=True)]
        before_usage = resource.getrusage(resource.RUSAGE_CHILDREN)
        began = time.monotonic()
        with (job_dir / "stdout.log").open("wb") as stdout, (job_dir / "stderr.log").open("wb") as stderr:
            child = subprocess.Popen(command, cwd=job_dir, env=child_env, stdout=stdout, stderr=stderr,
                                     stdin=subprocess.DEVNULL, close_fds=True)
            ACTIVE_PID = child.pid
            job["pid"] = child.pid
            try:
                while child.poll() is None:
                    now = time.monotonic()
                    if now - began >= 25 or now - START >= 88:
                        job["stop_reason"] = "WALL_LIMIT"
                        child.kill(); break
                    info = ProcTaskInfo()
                    count = probe(child.pid, 4, 0, ctypes.byref(info), ctypes.sizeof(info))
                    if count != ctypes.sizeof(info):
                        if child.poll() is None:
                            job["stop_reason"] = "RSS_OBSERVATION_UNAVAILABLE"
                            child.kill()
                        break
                    job["sampled_peak_rss_bytes"] = max(job["sampled_peak_rss_bytes"], int(info.resident_size))
                    job["sampled_max_kernel_threads"] = max(job["sampled_max_kernel_threads"], int(info.threadnum))
                    if info.resident_size >= RSS_LIMIT:
                        job["stop_reason"] = "RSS_SOFT_LIMIT"
                        child.kill(); break
                    time.sleep(0.1)
                job["exit_code"] = child.wait(timeout=1)
            finally:
                if child.poll() is None:
                    child.kill(); child.wait(timeout=1)
                ACTIVE_PID = None
        job["full_process_wall_seconds"] = time.monotonic() - began
        after_usage = resource.getrusage(resource.RUSAGE_CHILDREN)
        job["full_process_cpu_user_seconds"] = after_usage.ru_utime - before_usage.ru_utime
        job["full_process_cpu_system_seconds"] = after_usage.ru_stime - before_usage.ru_stime
        job["full_process_cpu_seconds"] = job["full_process_cpu_user_seconds"] + job["full_process_cpu_system_seconds"]
        job["status"] = "RESOURCE_STOP" if "stop_reason" in job else "PROCESS_EXITED"
        path = job_dir / "worker_report.json"
        if path.exists():
            worker = json.loads(path.read_text())
            job["worker_report_sha256"] = sha(path)
            job["worker_status"] = worker["status"]
            job["final_decision"] = worker.get("final_decision", "NOT_RUN")
            job["attempts"] = worker.get("attempts", [])
            job["fallback"] = worker.get("fallback", {"status": "NOT_RUN"})
            for field in ("semantic_e2e_wall_seconds", "semantic_e2e_cpu_seconds", "analytical_expectation_match", "differential", "raw_frontend_guard", "actual_verifier_semantics"):
                if field in worker:
                    job[field] = worker[field]
            job["valid_completed_result"] = (job["exit_code"] == 0 and worker["status"] == "COMPLETE"
                                             and worker.get("analytical_expectation_match", True) is not False)
        else:
            job.update(worker_status="NO_REPORT_EFFECT_UNKNOWN", valid_completed_result=False)
        save(output, report)
    selected = jobs[args.job_start:args.job_start + args.job_limit]
    report["status"] = "SELECTED_JOBS_COMPLETE" if all(j.get("valid_completed_result") for j in selected) else "COMPLETED_WITH_FAILURES_OR_NOT_RUN"
    report["wall_seconds_before_final_write"] = time.monotonic() - START
    save(output, report)
    print(json.dumps({"status": report["status"], "report": str(output)}), flush=True)
    os._exit(0 if report["status"] == "SELECTED_JOBS_COMPLETE" else 2)


if __name__ == "__main__":
    main()
