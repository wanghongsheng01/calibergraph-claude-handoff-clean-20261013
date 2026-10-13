"""Frozen round15 single-worker supervisor; importing this file runs no work.

CLI: frozen-python3.12 -B -I -S generation_supervisor.py --protocol FILE
     --freeze FILE --out NEW_DIRECTORY_UNDER_ROUND15_RUNS
All resource probes and workers run only inside main(). No automatic retries.
"""
from __future__ import annotations

import argparse
import datetime
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import resource
import signal
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
POLICY = {
    "worker_cpu_hard_seconds": 3, "worker_wall_seconds": 4.0,
    "worker_rss_bytes": 268435456, "batch_cpu_seconds": 60.0,
    "prior_preflight_cpu_charge_seconds": 0.0,
    "final_report_exit_tail_reserve_seconds": 0.2,
    "start_new_slot_max_charged_cpu_seconds": 50.0,
    "active_parent_and_reaped_stop_seconds": 56.0,
    "solver_watchdog_trigger_seconds": 1.5,
    "solver_cumulative_wall_seconds": 2.0, "maximum_checks_per_case": 2,
    "max_1min_load": 4.0, "min_memory_available_percentage": 25,
    "machine_probe_timeout_seconds": 0.5, "ps_timeout_seconds": 0.3,
    "poll_target_seconds": 0.1, "initial_progress_grace_seconds": 0.5,
    "maximum_workers": 1, "nice_minimum": 15,
}
THREAD_ENV = {name: "1" for name in (
    "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS", "NUMEXPR_MAX_THREADS", "VECLIB_MAXIMUM_THREADS",
    "BLIS_NUM_THREADS", "TBB_NUM_THREADS")}
CLEAN_ENV = {"PATH": "/usr/bin:/bin", "LANG": "C", "LC_ALL": "C",
             "PYTHONDONTWRITEBYTECODE": "1", **THREAD_ENV}
STOP_REQUESTED = None


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def request_stop(signum, _frame):
    global STOP_REQUESTED
    STOP_REQUESTED = "EXTERNAL_SIGNAL_" + str(signum)


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def number(value, label):
    require(type(value) in (int, float) and math.isfinite(value) and value >= 0,
            "INVALID_NUMBER_" + label)
    return float(value)


def read_json(path, maximum=8 * 1024 * 1024):
    path = Path(path)
    require(path.is_file() and not path.is_symlink(), "JSON_NOT_REGULAR_FILE: " + str(path))
    require(path.stat().st_size <= maximum, "JSON_SIZE_LIMIT: " + str(path))
    return json.loads(path.read_text(encoding="utf-8"))


def atomic_json(path, value):
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, allow_nan=False, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def event(stream, name, **fields):
    stream.write(json.dumps({"event": name, "utc": utc(),
                             "monotonic": time.monotonic(), **fields},
                            ensure_ascii=False, allow_nan=False) + "\n")
    stream.flush()


def accounting():
    own = resource.getrusage(resource.RUSAGE_SELF)
    children = resource.getrusage(resource.RUSAGE_CHILDREN)
    subtotal = own.ru_utime + own.ru_stime + children.ru_utime + children.ru_stime
    observed = POLICY["prior_preflight_cpu_charge_seconds"] + subtotal
    return {
        "pre_registered_prior_cpu_seconds": POLICY["prior_preflight_cpu_charge_seconds"],
        "prior_charge_kind": "Conservative preflight reserve, not a measured CPU result",
        "parent_user_cpu_seconds": own.ru_utime, "parent_system_cpu_seconds": own.ru_stime,
        "all_reaped_children_user_cpu_seconds": children.ru_utime,
        "all_reaped_children_system_cpu_seconds": children.ru_stime,
        "supervisor_plus_reaped_cpu_seconds": subtotal,
        "observed_total_cpu_seconds": observed,
        "reserved_final_report_exit_tail_seconds": POLICY["final_report_exit_tail_reserve_seconds"],
        "conservative_charged_total_seconds": observed + POLICY["final_report_exit_tail_reserve_seconds"],
        "scope": "Absolute parent SELF and all reaped CHILDREN, including memory_pressure, ps, failed preexec children and workers; live worker CPU separately sampled. Child CPU is not added twice.",
    }


def precheck_guard():
    require(STOP_REQUESTED is None, STOP_REQUESTED or "EXTERNAL_STOP")
    require(accounting()["conservative_charged_total_seconds"] <=
            POLICY["start_new_slot_max_charged_cpu_seconds"], "PRECHECK_CPU_RESERVE_STOP")


def digest(path, guard=None):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(262144), b""):
            if guard is not None:
                guard()
            h.update(block)
    return h.hexdigest()


def verify_manifest(entries):
    for path, expected in entries.items():
        precheck_guard()
        require(path.is_file() and not path.is_symlink(), "FROZEN_FILE_INVALID: " + str(path))
        require(digest(path, precheck_guard) == expected, "FREEZE_MISMATCH: " + str(path))


def validate_inputs(args, report):
    require(sys.platform == "darwin" and sys.version_info[:2] == (3, 12),
            "REQUIRES_DARWIN_PYTHON_3_12")
    require(sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode,
            "REQUIRES_-B_-I_-S")
    protocol = read_json(args.protocol)
    freeze = read_json(args.freeze)
    require(protocol.get("id") == "calibergraph-15-generation-replay-v1", "PROTOCOL_ID_MISMATCH")
    require(isinstance(protocol.get("status"), str) and protocol["status"].startswith("REGISTERED")
            and isinstance(protocol.get("registered_utc"), str) and protocol["registered_utc"],
            "EXECUTION_REQUIRES_REGISTERED_PROTOCOL_NOT_TEMPLATE")
    expected = {
        "worker_cpu_limit_seconds": 3, "worker_wall_limit_seconds": 4,
        "external_rss_limit_bytes": 268435456, "solver_cumulative_wall_limit_seconds": 2.0,
        "supervisor_solver_stop_seconds": 1.5, "maximum_independent_environment_attempts": 1,
        "maximum_active_workers": 1, "nice": 15, "total_parent_cpu_limit_seconds": 60,
        "contract_check_timeout_ms": 100, "query_check_timeout_ms": 700,
        "solver_timeout_reserve_seconds": 0.1, "internal_z3_memory_parameter_mb": 128,
        "maximum_batch_attempts": 1,
    }
    require(all(protocol.get(k) == v for k, v in expected.items()), "FIXED_BUDGET_MISMATCH")
    require(protocol.get("artifacts") == {"result": "results.json", "events": "events.jsonl",
                                         "progress": "progress.json"}, "ARTIFACT_NAMES_CHANGED")
    sys.path.insert(0, str(ROOT / 'implementation'))
    from generation_common import load_registered
    # This also denies execution while PREPARATION_ONLY remains enabled.
    _, _, _ = load_registered(args.protocol, 0)
    prior_charge = number(protocol['supervisor']['prior_preparation_cpu_charge_seconds'], 'PRIOR_CPU')
    require(prior_charge > 0, 'PREPARATION_AND_SOURCE_SCAN_CPU_MUST_BE_CHARGED')
    POLICY['prior_preflight_cpu_charge_seconds'] = prior_charge
    slots = protocol['registered_cases']
    report['registered_denominator'] = len(slots)
    report['registered_case_ids'] = [slot['id'] for slot in slots]
    report['slots'] = [{'slot': i, 'case_id': slot['id'], 'registered_slot': slot,
                        'status': 'NOT_RUN'} for i, slot in enumerate(slots)]
    report['registration_validated'] = False
    python_path = Path(protocol["supervisor"]["python_executable"]).resolve()
    require(python_path == Path(sys.executable).resolve(), "FROZEN_INTERPRETER_MISMATCH")
    require(protocol["supervisor"].get("required_flags") == ["-B", "-I", "-S"], "FLAGS_CHANGED")
    workers = {kind: Path(protocol["worker_paths"][kind]).resolve() for kind in ("official",)}
    require(workers == {kind: ROOT / "implementation" / "official_generation_worker.py"
                        for kind in workers}, "UNREGISTERED_WORKER_PATH")
    entries = freeze.get("files")
    require(isinstance(entries, list) and entries, "FREEZE_FILES_MISSING")
    manifest = {}
    for entry in entries:
        require(isinstance(entry, dict) and isinstance(entry.get("path"), str)
                and re.fullmatch(r"[0-9a-f]{64}", entry.get("sha256", "")) is not None,
                "MALFORMED_FREEZE_ENTRY")
        path = Path(entry["path"]).resolve()
        require(path not in manifest or manifest[path] == entry["sha256"], "CONFLICTING_FREEZE_ENTRY")
        manifest[path] = entry["sha256"]
    required = {Path(__file__).resolve(), args.protocol, python_path,
                Path(protocol["input"]["path"]).resolve(),
                Path(protocol["runtime_lock"]["path"]).resolve(), *workers.values()}
    required.update(p.resolve() for p in (ROOT / "implementation").glob("*.py"))
    require(required <= manifest.keys(), "CODE_PROTOCOL_INPUT_RUNTIME_INTERPRETER_MISSING_FROM_FREEZE")
    verify_manifest(manifest)
    for name in ("input", "runtime_lock"):
        spec = protocol[name]
        require(manifest[Path(spec["path"]).resolve()] == spec["sha256"], name.upper() + "_HASH_MISMATCH")
    runtime = read_json(protocol["runtime_lock"]["path"])
    require(isinstance(runtime.get("files"), dict), "RUNTIME_FILE_MANIFEST_MISSING")
    for raw_path, expected_hash in runtime["files"].items():
        require(manifest.get(Path(raw_path).resolve()) == expected_hash, "RUNTIME_DEPENDENCY_NOT_FROZEN: " + raw_path)
    report.update(protocol_sha256=digest(args.protocol), freeze_sha256=digest(args.freeze),
                  supervisor_sha256=digest(__file__), frozen_file_count=len(manifest),
                  interpreter=str(python_path), interpreter_sha256=manifest[python_path],
                  fixed_policy=dict(POLICY), clean_worker_environment=dict(CLEAN_ENV))
    # These are rehashed before every worker. Full runtime dependencies were
    # checked above and the official worker checks the same lock before import.
    immediate = {p: manifest[p] for p in required}
    report['registration_validated'] = True
    return protocol, workers, python_path, immediate


def machine_probe(observation):
    observation.update(started_utc=utc(), status="STARTED")
    load = list(os.getloadavg())
    require(all(math.isfinite(x) and x >= 0 for x in load), "LOAD_UNOBSERVABLE")
    observation["load"] = load
    completed = subprocess.run(["/usr/bin/memory_pressure", "-Q"], capture_output=True,
                               text=True, env=CLEAN_ENV, timeout=0.5)
    observation.update(memory_pressure_exit_code=completed.returncode,
                       memory_pressure_output=completed.stdout,
                       memory_pressure_stderr=completed.stderr)
    require(completed.returncode == 0, "MEMORY_PRESSURE_FAILED")
    match = re.search(r"System-wide memory free percentage:\s*(\d+)%", completed.stdout)
    require(match is not None, "MEMORY_PRESSURE_UNOBSERVABLE")
    available = int(match.group(1))
    require(0 <= available <= 100, "MEMORY_PRESSURE_RANGE")
    observation.update(status="RETURNED", memory_available_percentage=available,
                       admitted=load[0] <= 4.0 and available >= 25,
                       cpu_accounting_after_probe=accounting())


def ps_seconds(value):
    days = 0
    if "-" in value:
        day, value = value.split("-", 1)
        days = int(day)
    fields = value.split(":")
    require(len(fields) in (2, 3), "PS_CPU_FORMAT")
    seconds = float(fields[-1]) + 60 * int(fields[-2])
    if len(fields) == 3:
        seconds += 3600 * int(fields[0])
    return number(seconds + days * 86400, "PS_CPU")


def group_sample(owned_pgid, remaining):
    sample = subprocess.run(["/bin/ps", "-A", "-o", "pid=,pgid=,rss=,time="],
                            capture_output=True, text=True, env=CLEAN_ENV,
                            timeout=max(0.001, min(0.3, remaining)))
    require(sample.returncode == 0, "PS_FAILED")
    members = []
    for line in sample.stdout.splitlines():
        fields = line.split()
        require(len(fields) == 4, "PS_ROW_FORMAT")
        if int(fields[1]) != owned_pgid:
            continue
        rss = int(fields[2]) * 1024
        require(rss >= 0, "PS_RSS_RANGE")
        members.append({"pid": int(fields[0]), "rss_bytes": rss,
                        "cpu_seconds": ps_seconds(fields[3])})
    return {"owned_pgid": owned_pgid, "members": members,
            "rss_bytes": sum(x["rss_bytes"] for x in members),
            "cpu_seconds": sum(x["cpu_seconds"] for x in members)}


def progress_snapshot(directory, start, previous, index, case_id, final=False):
    path = directory / "progress.json"
    now = time.monotonic()
    if not path.exists():
        require(not final and now - start <= 0.5, "PROGRESS_MISSING")
        return None
    value = read_json(path, 65536)
    require(isinstance(value, dict) and isinstance(value.get("active_stage"), str), "PROGRESS_STAGE")
    require(value.get("case_index") == index and value.get("id") in (None, case_id), "PROGRESS_IDENTITY")
    require(not final or value.get("id") == case_id, "FINAL_PROGRESS_IDENTITY")
    active = value.get("solver_check_active")
    count = value.get("check_count")
    require(type(active) is bool and type(count) is int and 0 <= count <= 2, "PROGRESS_CHECK_COUNT_OR_ACTIVE")
    spent = number(value.get("solver_spent_wall_seconds"), "SOLVER_SPENT")
    updated = number(value.get("updated_monotonic"), "PROGRESS_UPDATED")
    require(start - 0.01 <= updated <= now + 0.01, "PROGRESS_UPDATED_RANGE")
    check_start = value.get("solver_check_start_monotonic")
    elapsed = 0.0
    if active:
        check_start = number(check_start, "CHECK_START")
        require(start - 0.01 <= check_start <= updated + 0.01 and count > 0, "CHECK_START_RANGE")
        elapsed = max(0.0, now - check_start)
    else:
        require(check_start is None, "INACTIVE_CHECK_START_NOT_NULL")
    if previous is not None:
        require(spent + 1e-9 >= previous["solver_spent_wall_seconds"]
                and count >= previous["check_count"] and updated >= previous["updated_monotonic"],
                "PROGRESS_COUNTER_OR_TIME_DECREASED")
    return {**value, "observed_monotonic": now,
            "solver_watchdog_estimated_seconds": spent + elapsed,
            "active_elapsed_estimate_seconds": elapsed}


def child_setup():
    os.setpriority(os.PRIO_PROCESS, 0, max(os.getpriority(os.PRIO_PROCESS, 0), 15))
    resource.setrlimit(resource.RLIMIT_CPU, (3, 3))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    # Deliberately no RLIMIT_RSS: the earlier Darwin call is known to fail.


def reap(proc, block=False):
    if proc.returncode is not None:
        return None
    pid, status, usage = os.wait4(proc.pid, 0 if block else os.WNOHANG)
    if pid == 0:
        return None
    proc.returncode = os.waitstatus_to_exitcode(status)
    return {"pid": pid, "exit_code": proc.returncode, "user_cpu_seconds": usage.ru_utime,
            "system_cpu_seconds": usage.ru_stime, "cpu_seconds": usage.ru_utime + usage.ru_stime,
            "maxrss_bytes_darwin": usage.ru_maxrss}


def resource_status_in(value):
    if isinstance(value, dict):
        if value.get("status") in ("RESOURCE_STOP", "BUDGET_VIOLATION"):
            return True
        return any(resource_status_in(v) for v in value.values())
    if isinstance(value, list):
        return any(resource_status_in(v) for v in value)
    return False


def run_slot(index, slot, directory, args, worker, python_path):
    directory.mkdir()
    receipt = {"case_index": index, "case_id": slot["id"], "registered_slot": slot,
               "status": "STARTING", "started_utc": utc(), "violations": [],
               "sampled_peak_rss_bytes": 0, "sampled_peak_group_cpu_seconds": 0.0,
               "sample_count": 0, "stop_remainder": None, "worker_wait4_usage": None,
               "observed_stage_sequence": [], "cpu_accounting_before_launch": accounting()}
    proc = None
    previous = None
    stop = None
    start = time.monotonic()
    with (directory / "supervisor_events.jsonl").open("x", encoding="utf-8") as events, \
         (directory / "stdout.log").open("x", encoding="utf-8") as stdout, \
         (directory / "stderr.log").open("x", encoding="utf-8") as stderr:
        try:
            command = [str(python_path), "-B", "-I", "-S", str(worker),
                       "--protocol", str(args.protocol), "--case-index", str(index), "--out", str(directory)]
            receipt["command"] = command
            proc = subprocess.Popen(command, cwd=ROOT, env=CLEAN_ENV, stdout=stdout, stderr=stderr,
                                    start_new_session=True, preexec_fn=child_setup)
            receipt.update(pid=proc.pid, owned_pgid=proc.pid, status="RUNNING")
            event(events, "WORKER_STARTED", pid=proc.pid, case_id=slot["id"])
            while True:
                tick = time.monotonic()
                usage = reap(proc)
                if usage is not None:
                    receipt["worker_wait4_usage"] = usage
                    break
                if STOP_REQUESTED:
                    stop = STOP_REQUESTED
                    break
                if accounting()["observed_total_cpu_seconds"] >= 56.0:
                    stop = "BATCH_ACTIVE_CPU_RESERVE_STOP"
                    break
                remaining = 4.0 - (tick - start)
                if remaining <= 0:
                    stop = "WORKER_WALL_STOP"
                    break
                load = list(os.getloadavg())
                require(all(math.isfinite(x) and x >= 0 for x in load), "LOAD_UNOBSERVABLE")
                if load[0] > 4.0:
                    stop = "MACHINE_LOAD_ROSE_DURING_SLOT"
                    break
                current = progress_snapshot(directory, start, previous, index, slot["id"])
                if current is not None:
                    previous = current
                    stage = current["active_stage"]
                    if not receipt["observed_stage_sequence"] or receipt["observed_stage_sequence"][-1] != stage:
                        receipt["observed_stage_sequence"].append(stage)
                    if current["solver_watchdog_estimated_seconds"] >= 1.5:
                        stop = "SOLVER_WATCHDOG_STOP"
                        break
                sample = group_sample(proc.pid, remaining)
                if not sample["members"]:
                    usage = reap(proc)
                    if usage is not None:
                        receipt["worker_wait4_usage"] = usage
                        break
                    raise RuntimeError("OWNED_GROUP_UNOBSERVABLE")
                require(all(m["pid"] == proc.pid for m in sample["members"]), "UNREGISTERED_WORKER_DESCENDANT")
                receipt["sample_count"] += 1
                receipt["sampled_peak_rss_bytes"] = max(receipt["sampled_peak_rss_bytes"], sample["rss_bytes"])
                receipt["sampled_peak_group_cpu_seconds"] = max(receipt["sampled_peak_group_cpu_seconds"], sample["cpu_seconds"])
                if sample["rss_bytes"] > 268435456:
                    stop = "WORKER_RSS_STOP"
                elif sample["cpu_seconds"] >= 3.0:
                    stop = "WORKER_CPU_STOP"
                if accounting()["observed_total_cpu_seconds"] >= 56.0:
                    stop = stop or "BATCH_ACTIVE_CPU_RESERVE_STOP"
                if accounting()["conservative_charged_total_seconds"] + sample["cpu_seconds"] >= 60.0:
                    stop = stop or "BATCH_LIVE_CPU_STOP"
                current = progress_snapshot(directory, start, previous, index, slot["id"])
                if current is not None:
                    previous = current
                    if current["solver_watchdog_estimated_seconds"] >= 1.5:
                        stop = stop or "SOLVER_WATCHDOG_STOP"
                if time.monotonic() - start >= 4.0:
                    stop = stop or "WORKER_WALL_STOP"
                event(events, "MONITOR", group=sample, load=load, progress=current, accounting=accounting())
                if stop:
                    break
                time.sleep(max(0.0, 0.1 - (time.monotonic() - tick)))
        except BaseException as error:
            stop = "MONITOR_OR_LAUNCH_EXCEPTION"
            receipt["monitor_error"] = {"type": type(error).__name__, "message": str(error)[:2000]}
        finally:
            if stop is not None:
                receipt["stop_remainder"] = stop
            if proc is not None:
                # First reap if it exited since the last monitor. Once wait4
                # releases its PID, never signal that recyclable pid/pgid.
                wait_ownership_lost = False
                try:
                    usage = reap(proc)
                    if usage is not None:
                        receipt["worker_wait4_usage"] = usage
                except ChildProcessError as error:
                    # Another wait has released ownership; fail closed and
                    # never signal this now potentially recyclable number.
                    wait_ownership_lost = True
                    receipt["cleanup_wait_ownership_lost"] = repr(error)
                    receipt["stop_remainder"] = "CLEANUP_FAILED"
                except BaseException as error:
                    receipt["cleanup_initial_reap_error"] = repr(error)
                    receipt["stop_remainder"] = "CLEANUP_FAILED"
                try:
                    if proc.returncode is None and not wait_ownership_lost:
                        try:
                            os.killpg(proc.pid, signal.SIGKILL)
                            receipt["cleanup_killpg_sent"] = True
                        except ProcessLookupError:
                            receipt["cleanup_group_already_gone"] = True
                        except BaseException as error:
                            receipt["cleanup_kill_error"] = repr(error)
                            receipt["stop_remainder"] = "CLEANUP_FAILED"
                    else:
                        receipt["cleanup_killpg_skipped_already_reaped"] = True
                    if not wait_ownership_lost:
                        usage = reap(proc, block=True)
                        if usage is not None:
                            receipt["worker_wait4_usage"] = usage
                        proc.wait()  # Cached returncode; no second OS wait.
                        receipt["cleanup_wait_complete"] = True
                except BaseException as error:
                    receipt["cleanup_error"] = repr(error)
                    receipt["stop_remainder"] = "CLEANUP_FAILED"
            receipt["wall_seconds"] = time.monotonic() - start
            receipt["worker_exit_code"] = None if proc is None else proc.returncode
            receipt["status"] = stop or ("RETURNED" if proc is not None and proc.returncode == 0 else "WORKER_FAILED")
            if receipt["status"] == "WORKER_FAILED":
                receipt["stop_remainder"] = receipt["stop_remainder"] or "WORKER_FAILED"
            try:
                final = progress_snapshot(directory, start, previous, index, slot["id"], final=True)
                receipt["final_progress"] = final
                if final["solver_spent_wall_seconds"] > 2.0:
                    receipt["violations"].append("COMPLETED_SOLVER_WALL_EXCEEDED_2S")
                if final["solver_check_active"]:
                    receipt["solver_wall_censored"] = True
                    receipt["active_elapsed_includes_cleanup_tail"] = True
                    if final["solver_watchdog_estimated_seconds"] > 2.0:
                        receipt["violations"].append("ACTIVE_SOLVER_ESTIMATE_EXCEEDED_2S_ACTUAL_CENSORED")
                if final["solver_watchdog_estimated_seconds"] >= 1.5:
                    receipt["stop_remainder"] = receipt["stop_remainder"] or "SOLVER_WATCHDOG_FINAL_THRESHOLD"
            except BaseException as error:
                receipt["final_progress_error"] = repr(error)
                receipt["stop_remainder"] = receipt["stop_remainder"] or "PROGRESS_UNOBSERVABLE"
            usage = receipt["worker_wait4_usage"] or {}
            if usage.get("cpu_seconds", 0.0) > 3.0:
                receipt["violations"].append("ACTUAL_WORKER_CPU_EXCEEDED_3S")
            if max(usage.get("maxrss_bytes_darwin", 0), receipt["sampled_peak_rss_bytes"]) > 268435456:
                receipt["violations"].append("ACTUAL_OR_SAMPLED_RSS_EXCEEDED_256_MIB")
            if receipt["wall_seconds"] > 4.0:
                receipt["violations"].append("WORKER_LIFECYCLE_WALL_EXCEEDED_4S")
            if receipt["violations"]:
                receipt["stop_remainder"] = receipt["stop_remainder"] or "RESOURCE_VIOLATION_AFTER_REAP"
            result_path = directory / "results.json"
            if result_path.exists():
                try:
                    result = read_json(result_path)
                    require(isinstance(result, dict), "WORKER_RESULT_NOT_OBJECT")
                    receipt["worker_results_sha256"] = digest(result_path)
                    receipt["worker_report_status"] = result.get("status")
                    receipt["worker_record_unmodified"] = result.get("record", result)
                    receipt["worker_result_unmodified"] = result
                    if resource_status_in(result):
                        receipt["stop_remainder"] = receipt["stop_remainder"] or "WORKER_REPORTED_RESOURCE_STOP"
                except BaseException as error:
                    receipt["worker_results_error"] = repr(error)
                    receipt["stop_remainder"] = receipt["stop_remainder"] or "WORKER_RESULTS_INVALID"
            else:
                atomic_json(result_path, {"author": "supervisor", "status": "WORKER_DID_NOT_COMPLETE",
                                         "case_index": index, "case_id": slot["id"], "query_verdict": None})
                receipt["worker_results_missing_supervisor_placeholder"] = True
                receipt["stop_remainder"] = receipt["stop_remainder"] or "WORKER_RESULTS_MISSING"
            receipt["cpu_accounting_after_reap"] = accounting()
            event(events, "WORKER_FINISHED", status=receipt["status"],
                  stop_remainder=receipt["stop_remainder"], violations=receipt["violations"])
            atomic_json(directory / "supervisor_receipt.json", receipt)
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--freeze", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.protocol = args.protocol.resolve()
    args.freeze = args.freeze.resolve()
    output = args.out.resolve()
    runs = ROOT / "runs"
    require(output.parent == runs.resolve() and not output.exists(), "OUTPUT_MUST_BE_FRESH_DIRECT_CHILD_OF_ROUND15_RUNS")
    runs.mkdir(exist_ok=True)
    output.mkdir()
    report = {"id": "calibergraph-15-generation-supervisor-receipt-v1", "status": "REGISTERING",
              "created_utc": utc(), "registered_denominator": None,
              "planned_denominator": 24, "registration_validated": False,
              "slots": [{"slot": position, "case_id": f'dev03_{source_index + 1:02d}_exact{exact_rows}_rep{repeat_id}', "status": "NOT_RUN",
                         "planned_slot": {"id": f'dev03_{source_index + 1:02d}_exact{exact_rows}_rep{repeat_id}', "source_case_index": source_index,
                             "source_case_id": "dev03_" + str(source_index + 1).zfill(2),
                             "exact_rows": exact_rows, "repeat_id": repeat_id, "kind": "official"}}
                        for position, (repeat_id, source_index, exact_rows) in enumerate(
                            (r, i, n) for r, source_order, bounds in (
                                (1, (6, 9, 14, 3), (2, 3, 4)),
                                (2, (3, 14, 9, 6), (4, 3, 2)))
                            for i in source_order for n in bounds)],
              "violations": [], "fixed_policy": dict(POLICY), "maximum_workers": 1,
              "read_reserve": False, "automatic_retries": 0}
    atomic_json(output / "batch_receipt.json", report)
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, request_stop)
    lock = None
    locked = False
    halt = None
    exit_code = 2
    with (output / "batch_events.jsonl").open("x", encoding="utf-8") as events:
        try:
            lock = (ROOT / ".pilot_single_worker.lock").open("a")
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            locked = True
            protocol, workers, python_path, immediate = validate_inputs(args, report)
            report["status"] = "REGISTERED_BEFORE_WORKERS"
            atomic_json(output / "batch_receipt.json", report)
            for index, slot in enumerate(protocol["registered_cases"]):
                if STOP_REQUESTED:
                    halt = STOP_REQUESTED
                    break
                if accounting()["conservative_charged_total_seconds"] > 50.0:
                    halt = "START_SLOT_CPU_RESERVE_STOP"
                    break
                observation = {}
                report["slots"][index]["gate_probe"] = observation
                try:
                    machine_probe(observation)
                except BaseException as error:
                    observation.update(status="FAILED", error={"type": type(error).__name__, "message": str(error)[:2000]},
                                       cpu_accounting_after_probe=accounting())
                    halt = "MACHINE_PROBE_EXCEPTION"
                    break
                event(events, "SLOT_GATE_PROBE", case_index=index, observation=observation)
                if not observation["admitted"]:
                    halt = "MACHINE_PREFLIGHT_GATE_STOP"
                    break
                verify_manifest(immediate)
                if STOP_REQUESTED or accounting()["conservative_charged_total_seconds"] > 50.0:
                    halt = STOP_REQUESTED or "START_SLOT_CPU_RESERVE_STOP_AFTER_PROBE"
                    break
                output_slot = report["slots"][index]
                output_slot.update(status="STARTING")
                atomic_json(output / "batch_receipt.json", report)
                directory = output / ("case_" + format(index, "02d"))
                result = run_slot(index, slot, directory, args, workers[slot["kind"]], python_path)
                output_slot.update(status=result["status"], receipt=str(directory / "supervisor_receipt.json"),
                                   worker_exit_code=result["worker_exit_code"], worker_wait4_usage=result["worker_wait4_usage"],
                                   worker_report_status=result.get("worker_report_status"),
                                   observed_stage_sequence=result["observed_stage_sequence"],
                                   stop_remainder=result["stop_remainder"], violations=result["violations"])
                report["cpu_accounting"] = accounting()
                atomic_json(output / "batch_receipt.json", report)
                if result["stop_remainder"]:
                    halt = result["stop_remainder"]
                    break
            report["status"] = "STOPPED_REMAINDER_NOT_RUN" if halt else "REGISTERED_SEQUENCE_FINISHED"
            exit_code = 2 if halt else 0
        except BaseException as error:
            halt = halt or "BATCH_PRECHECK_OR_MONITOR_FAILED"
            report.update(status="BATCH_PRECHECK_OR_MONITOR_FAILED",
                          error={"type": type(error).__name__, "message": str(error)[:4000]})
        finally:
            report.update(halt_reason=halt, finished_utc=utc())
            for slot in report["slots"]:
                if slot["status"] == "NOT_RUN":
                    slot["not_run_reason"] = halt or "NOT_ATTEMPTED"
            report["registered_attempts"] = sum(s["status"] != "NOT_RUN" for s in report["slots"])
            report["cpu_accounting"] = accounting()
            if report["cpu_accounting"]["conservative_charged_total_seconds"] > 60.0:
                report["violations"].append("BATCH_CONSERVATIVE_CHARGE_EXCEEDED_60S")
                exit_code = 2
            report["measurement_note"] = "RSS, solver and wall checks are sampled and can overshoot; actual wait4 usage, all violations and censored timings are preserved. The registered preparation CPU charge and 0.2s exit tail are preserved separately from measured parent/child CPU."
            try:
                event(events, "BATCH_FINISHED", status=report["status"], accounting=report["cpu_accounting"])
                atomic_json(output / "batch_receipt.json", report)
            finally:
                if lock is not None:
                    if locked:
                        fcntl.flock(lock, fcntl.LOCK_UN)
                    lock.close()
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
