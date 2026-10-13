"""One prospective bootstrap recovery; authoring does not execute workers.

Run using the frozen Python 3.12 with -B -I -S. All outputs require a fresh
project/runs/batch_* directory. Only owned process groups may be terminated.
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
WORKER = ROOT / "code/official_diagnostic_worker.py"
POLICY = ROOT / "protocols/probe_supervisor_policy.json"
ORIGINAL_PROTOCOL = ROOT / "protocols/official_diagnostic.registered.json"
ORIGINAL_SUPERVISOR = ROOT / "code/probe_supervisor.py"
THREAD_ENV = {key: "1" for key in (
    "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS", "NUMEXPR_MAX_THREADS", "VECLIB_MAXIMUM_THREADS",
    "BLIS_NUM_THREADS", "TBB_NUM_THREADS")}
# No inherited environment, credentials, PYTHONPATH, or user startup settings.
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


def finite_number(value, label, minimum=0.0):
    require(type(value) in (int, float) and math.isfinite(value) and value >= minimum,
            "INVALID_NUMBER_" + label)
    return float(value)


def digest(path, guard=None):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            if guard is not None:
                guard()
            h.update(chunk)
    return h.hexdigest()


def read_json(path, maximum=4 * 1024 * 1024):
    path = Path(path)
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


def accounting(scan_charge):
    own = resource.getrusage(resource.RUSAGE_SELF)
    children = resource.getrusage(resource.RUSAGE_CHILDREN)
    subtotal = own.ru_utime + own.ru_stime + children.ru_utime + children.ru_stime
    return {"pre_registered_prior_cpu_seconds": scan_charge,
            "parent_user_cpu_seconds": own.ru_utime,
            "parent_system_cpu_seconds": own.ru_stime,
            "all_reaped_children_user_cpu_seconds": children.ru_utime,
            "all_reaped_children_system_cpu_seconds": children.ru_stime,
            "supervisor_plus_reaped_cpu_seconds": subtotal,
            "observed_total_cpu_seconds": None if scan_charge is None else scan_charge + subtotal,
            "prior_charge_verified": scan_charge is not None,
            "scope": "Original scan plus charged bootstrap failure/diagnostic reserve, supervisor absolute SELF and all reaped CHILDREN including probes/ps; live worker separately sampled"}


def machine_probe(policy):
    load = list(os.getloadavg())
    require(all(math.isfinite(x) and x >= 0 for x in load), "LOAD_UNOBSERVABLE")
    completed = subprocess.run(["/usr/bin/memory_pressure", "-Q"],
                               capture_output=True, text=True, env=CLEAN_ENV,
                               timeout=policy["machine_probe_timeout_seconds"])
    require(completed.returncode == 0, "MEMORY_PRESSURE_FAILED")
    match = re.search(r"System-wide memory free percentage:\s*(\d+)%", completed.stdout)
    require(match is not None, "MEMORY_PRESSURE_UNOBSERVABLE")
    available = int(match.group(1))
    require(0 <= available <= 100, "MEMORY_PRESSURE_RANGE")
    return {"utc": utc(), "load": load, "memory_available_percentage": available,
            "memory_pressure_output": completed.stdout,
            "admitted": load[0] <= policy["max_1min_load"]
            and available >= policy["min_memory_available_percentage"]}


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
    return finite_number(seconds + days * 86400, "PS_CPU")


def group_sample(pgid, policy, remaining):
    # BSD/macOS-compatible ps fields. Other rows are ignored, never signalled.
    sample = subprocess.run(["/bin/ps", "-A", "-o", "pid=,pgid=,rss=,time="],
                            capture_output=True, text=True, env=CLEAN_ENV,
                            timeout=max(0.001, min(policy["ps_timeout_seconds"], remaining)))
    require(sample.returncode == 0, "PS_FAILED")
    members = []
    for line in sample.stdout.splitlines():
        fields = line.split()
        require(len(fields) == 4, "PS_ROW_FORMAT")
        if int(fields[1]) == pgid:
            members.append({"pid": int(fields[0]), "rss_bytes": int(fields[2]) * 1024,
                            "cpu_seconds": ps_seconds(fields[3])})
    return {"members": members, "rss_bytes": sum(x["rss_bytes"] for x in members),
            "cpu_seconds": sum(x["cpu_seconds"] for x in members)}


def progress_snapshot(directory, case_start, previous, policy):
    path = directory / policy["progress_file"]
    now = time.monotonic()
    if not path.exists():
        require(now - case_start <= policy["initial_progress_grace_seconds"], "PROGRESS_MISSING")
        return None
    value = read_json(path, 65536)
    require(isinstance(value, dict), "PROGRESS_NOT_OBJECT")
    require(isinstance(value.get("active_stage"), str), "PROGRESS_STAGE")
    active = value.get("solver_check_active")
    require(type(active) is bool, "PROGRESS_ACTIVE")
    count = value.get("check_count")
    require(type(count) is int and 0 <= count <= policy["maximum_checks_per_case"], "PROGRESS_CHECK_COUNT")
    spent = finite_number(value.get("solver_spent_wall_seconds"), "SOLVER_SPENT")
    check_start = value.get("solver_check_start_monotonic")
    elapsed = 0.0
    if active:
        check_start = finite_number(check_start, "CHECK_START")
        require(case_start - 0.01 <= check_start <= now + 0.01 and count > 0, "CHECK_START_RANGE")
        elapsed = max(0.0, now - check_start)
    else:
        require(check_start is None, "INACTIVE_CHECK_START_NOT_NULL")
    if previous is not None:
        require(spent + 1e-9 >= previous["solver_spent_wall_seconds"], "SOLVER_SPENT_DECREASED")
        require(count >= previous["check_count"], "CHECK_COUNT_DECREASED")
    return {**value, "observed_monotonic": now,
            "solver_watchdog_estimated_seconds": spent + elapsed,
            "active_elapsed_estimate_seconds": elapsed}


def child_setup():
    os.setpriority(os.PRIO_PROCESS, 0, 15)
    resource.setrlimit(resource.RLIMIT_CPU, (4, 4))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    # Frozen stdlib-only diagnosis found this Darwin RLIMIT_RSS call raises.
    # Keep external RSS sampling and wait4 peak recording; no hard RSS claim.


def reap(proc, block=False):
    if proc.returncode is not None:
        return None
    pid, status, usage = os.wait4(proc.pid, 0 if block else os.WNOHANG)
    if not pid:
        return None
    proc.returncode = os.waitstatus_to_exitcode(status)
    return {"pid": pid, "exit_code": proc.returncode, "user_cpu_seconds": usage.ru_utime,
            "system_cpu_seconds": usage.ru_stime, "cpu_seconds": usage.ru_utime + usage.ru_stime,
            "maxrss_bytes_darwin": usage.ru_maxrss}


def run_case(index, case_id, directory, protocol_path, python_path, scan_charge, policy):
    directory.mkdir()
    receipt = {"case_index": index, "case_id": case_id, "status": "STARTING",
               "started_utc": utc(), "violations": [], "sampled_peak_rss_bytes": 0,
               "sampled_peak_group_cpu_seconds": 0.0, "sample_count": 0,
               "stop_remainder": None}
    proc = None
    previous = None
    start = time.monotonic()
    stop = None
    with (directory / "supervisor_events.jsonl").open("x", encoding="utf-8") as events, \
         (directory / "stdout.log").open("x", encoding="utf-8") as stdout, \
         (directory / "stderr.log").open("x", encoding="utf-8") as stderr:
        try:
            proc = subprocess.Popen([str(python_path), "-B", "-I", "-S", str(WORKER),
                                     "--protocol", str(protocol_path), "--case-index", str(index),
                                     "--out", str(directory)], cwd=ROOT, env=CLEAN_ENV,
                                    stdout=stdout, stderr=stderr, start_new_session=True,
                                    preexec_fn=child_setup)
            receipt.update(pid=proc.pid, owned_pgid=proc.pid, status="RUNNING")
            event(events, "WORKER_STARTED", pid=proc.pid, case_id=case_id)
            while True:
                tick = time.monotonic()
                usage = reap(proc)
                if usage is not None:
                    receipt["worker_wait4_usage"] = usage
                    break
                if STOP_REQUESTED:
                    stop = STOP_REQUESTED
                    receipt["stop_remainder"] = stop
                    break
                charged = accounting(scan_charge)["observed_total_cpu_seconds"]
                if charged >= policy["active_parent_and_reaped_stop_seconds"]:
                    stop = "BATCH_ACTIVE_CPU_RESERVE_STOP"
                    receipt["stop_remainder"] = stop
                    break
                remaining = policy["worker_wall_seconds"] - (tick - start)
                if remaining <= 0:
                    stop = "WALL_BUDGET_STOP"
                    break
                load = list(os.getloadavg())
                require(all(math.isfinite(x) and x >= 0 for x in load), "LOAD_UNOBSERVABLE")
                if load[0] > policy["max_1min_load"]:
                    receipt["stop_remainder"] = "MACHINE_LOAD_ROSE_DURING_CASE"
                current = progress_snapshot(directory, start, previous, policy)
                if current is not None:
                    previous = current
                    if current["solver_watchdog_estimated_seconds"] >= policy["solver_watchdog_trigger_seconds"]:
                        stop = "SOLVER_BUDGET_STOP"
                        break
                sample = group_sample(proc.pid, policy, remaining)
                if not sample["members"]:
                    usage = reap(proc)
                    if usage is not None:
                        receipt["worker_wait4_usage"] = usage
                        break
                    raise RuntimeError("OWNED_GROUP_UNOBSERVABLE")
                require(all(x["pid"] == proc.pid for x in sample["members"]), "UNREGISTERED_WORKER_DESCENDANT")
                receipt["sample_count"] += 1
                receipt["sampled_peak_rss_bytes"] = max(receipt["sampled_peak_rss_bytes"], sample["rss_bytes"])
                receipt["sampled_peak_group_cpu_seconds"] = max(receipt["sampled_peak_group_cpu_seconds"], sample["cpu_seconds"])
                if sample["rss_bytes"] > policy["worker_rss_bytes"]:
                    stop = "RSS_BUDGET_STOP"
                elif sample["cpu_seconds"] > policy["worker_cpu_hard_seconds"]:
                    stop = "CPU_BUDGET_STOP"
                # Recheck wall/solver immediately after the bounded ps subprocess.
                current = progress_snapshot(directory, start, previous, policy)
                if current is not None:
                    previous = current
                    if current["solver_watchdog_estimated_seconds"] >= policy["solver_watchdog_trigger_seconds"]:
                        stop = stop or "SOLVER_BUDGET_STOP"
                if time.monotonic() - start >= policy["worker_wall_seconds"]:
                    stop = stop or "WALL_BUDGET_STOP"
                event(events, "MONITOR", cpu_accounted=accounting(scan_charge)["observed_total_cpu_seconds"],
                      group=sample, load=load, progress=current)
                if stop:
                    break
                time.sleep(max(0.0, policy["poll_target_seconds"] - (time.monotonic() - tick)))
        except BaseException as error:
            stop = "MONITOR_OR_LAUNCH_EXCEPTION"
            receipt["monitor_error"] = {"type": type(error).__name__, "message": str(error)[:2000]}
            receipt["stop_remainder"] = stop
        finally:
            # Mandatory exception-safe cleanup. Never target any unowned pid/group.
            if proc is not None:
                if proc.returncode is None:
                    try:
                        os.killpg(proc.pid, signal.SIGKILL)
                        receipt["cleanup_killpg_sent"] = True
                    except ProcessLookupError:
                        receipt["cleanup_group_already_gone"] = True
                    except BaseException as error:
                        receipt["cleanup_kill_error"] = repr(error)
                        receipt["stop_remainder"] = "CLEANUP_FAILED"
                else:
                    # wait4 released the PID; never signal its reusable number.
                    receipt["cleanup_killpg_skipped_already_reaped"] = True
                try:
                    usage = reap(proc, block=True)
                    if usage is not None:
                        receipt["worker_wait4_usage"] = usage
                    proc.wait()  # Cached after wait4; documents complete Popen cleanup.
                    receipt["cleanup_wait_complete"] = True
                except BaseException as error:
                    receipt["cleanup_wait_error"] = repr(error)
                    receipt["stop_remainder"] = "CLEANUP_FAILED"
            receipt["wall_seconds"] = time.monotonic() - start
            receipt["status"] = stop or ("RETURNED" if proc is not None and proc.returncode == 0 else "WORKER_FAILED")
            receipt["worker_exit_code"] = None if proc is None else proc.returncode
            try:
                final_progress = progress_snapshot(directory, start, previous, policy)
                receipt["final_progress"] = final_progress
                if final_progress is not None:
                    actual_completed = final_progress["solver_spent_wall_seconds"]
                    if actual_completed > policy["solver_cumulative_wall_seconds"]:
                        receipt["violations"].append("RECORDED_COMPLETED_SOLVER_WALL_EXCEEDED_2S")
                    if final_progress["solver_check_active"]:
                        receipt["solver_wall_censored"] = True
                        receipt["active_solver_elapsed_includes_cleanup_tail"] = True
                        if final_progress["solver_watchdog_estimated_seconds"] > policy["solver_cumulative_wall_seconds"]:
                            receipt["violations"].append("ACTIVE_SOLVER_MONITOR_ESTIMATE_EXCEEDED_2S_ACTUAL_CENSORED")
            except BaseException as error:
                receipt["final_progress_error"] = repr(error)
                receipt["stop_remainder"] = "PROGRESS_UNOBSERVABLE"
            worker_usage = receipt.get("worker_wait4_usage", {})
            if worker_usage.get("cpu_seconds", 0.0) > policy["worker_cpu_hard_seconds"]:
                receipt["violations"].append("ACTUAL_WORKER_CPU_EXCEEDED_4S")
            if max(worker_usage.get("maxrss_bytes_darwin", 0), receipt["sampled_peak_rss_bytes"]) > policy["worker_rss_bytes"]:
                receipt["violations"].append("WORKER_RSS_EXCEEDED_256_MIB")
            if receipt["wall_seconds"] > policy["worker_wall_seconds"]:
                receipt["violations"].append("WORKER_LIFECYCLE_WALL_EXCEEDED_5S")
            result_path = directory / policy["worker_results_file"]
            if result_path.exists():
                try:
                    result = read_json(result_path)
                    receipt["worker_results_sha256"] = digest(result_path)
                    receipt["worker_report_status"] = result.get("status")
                    receipt["worker_record_unmodified"] = result.get("record")
                except BaseException as error:
                    receipt["worker_results_error"] = repr(error)
                    receipt["stop_remainder"] = "WORKER_RESULTS_INVALID"
            else:
                # Never overwrite a worker result. This explicitly names its author.
                atomic_json(result_path, {"author": "supervisor", "status": "WORKER_DID_NOT_COMPLETE",
                                         "case_index": index, "case_id": case_id,
                                         "supervisor_stop": receipt["status"], "query_verdict": None})
                receipt["worker_results_missing_supervisor_placeholder"] = True
            receipt["cpu_accounting_after_reap"] = accounting(scan_charge)
            try:
                event(events, "WORKER_FINISHED", status=receipt["status"],
                      stop_remainder=receipt["stop_remainder"], violations=receipt["violations"])
            except BaseException as error:
                receipt["final_event_error"] = repr(error)
                receipt["stop_remainder"] = "EVENT_WRITE_FAILED"
            atomic_json(directory / "supervisor_receipt.json", receipt)
    return receipt


def validate_bootstrap_recovery(protocol, scan_charge, frozen_paths, report):
    recovery = protocol["supervisor"]["bootstrap_recovery"]
    previous_spec = recovery["previous_batch_receipt"]
    previous_path = Path(previous_spec["path"]).resolve()
    require(previous_path == ROOT / "runs/batch_01/batch_receipt.json", "ONLY_ORIGINAL_BATCH_01_MAY_BE_RECOVERED")
    require(digest(previous_path) == previous_spec["sha256"], "PREVIOUS_BATCH_HASH_MISMATCH")
    previous = read_json(previous_path)
    require(previous.get("status") == "STOPPED_REMAINDER_NOT_RUN"
            and previous.get("halt_reason") == "MONITOR_OR_LAUNCH_EXCEPTION"
            and previous.get("registered_attempts") == 1, "PREVIOUS_BATCH_NOT_BOOTSTRAP_ONLY")
    require("bootstrap_recovery" not in previous, "RECURSIVE_RECOVERY_FORBIDDEN")
    original = read_json(ORIGINAL_PROTOCOL)
    require("bootstrap_recovery" not in original["supervisor"], "ORIGINAL_PROTOCOL_IS_RECOVERY")
    require(digest(ORIGINAL_PROTOCOL) == previous["protocol_sha256"]
            and digest(ORIGINAL_SUPERVISOR) == previous["supervisor_sha256"], "ORIGINAL_FROZEN_IDENTITY_MISMATCH")
    mutable = {"status", "registered_utc", "supervisor", "amendment"}
    require({k: v for k, v in protocol.items() if k not in mutable}
            == {k: v for k, v in original.items() if k not in mutable}, "SCIENTIFIC_PROTOCOL_CHANGED")
    require({k: v for k, v in protocol["supervisor"].items() if k != "bootstrap_recovery"}
            == original["supervisor"], "ORIGINAL_SUPERVISOR_CONTRACT_CHANGED")
    ids = protocol["registered_case_ids"]
    require(len(ids) == 21 and previous["registered_case_ids"] == ids
            and previous["registered_denominator"] == 21, "RECOVERY_CASE_ORDER_CHANGED")
    slots = previous["slots"]
    require(len(slots) == 32, "PREVIOUS_SLOTS_INVALID")
    for index, slot in enumerate(slots):
        require(slot.get("slot") == index
                and slot.get("case_id") == (ids[index] if index < len(ids) else None), "PREVIOUS_SLOT_ID_MISMATCH")
        require(slot.get("worker_record_unmodified") is None
                and slot.get("worker_report_status") is None, "PREVIOUS_WORKER_OUTPUT_PRESENT")
        expected = "MONITOR_OR_LAUNCH_EXCEPTION" if index == 0 else ("NOT_RUN" if index < len(ids) else "NOT_REGISTERED")
        require(slot.get("status") == expected, "PREVIOUS_SLOT_STATUS_INVALID")
        case_directory = previous_path.parent / ("case_" + format(index, "02d"))
        require(not (case_directory / "events.jsonl").exists()
                and not (case_directory / "progress.json").exists(), "PREVIOUS_WORKER_ACTIVITY_PRESENT")
        if index > 0:
            require(not case_directory.exists(), "PREVIOUS_EXTRA_CASE_DIRECTORY")
    first_path = previous_path.parent / "case_00/supervisor_receipt.json"
    require(Path(slots[0]["receipt"]).resolve() == first_path, "PREVIOUS_FIRST_RECEIPT_PATH_INVALID")
    first = read_json(first_path)
    require(first.get("status") == "MONITOR_OR_LAUNCH_EXCEPTION"
            and "pid" not in first and "owned_pgid" not in first
            and first.get("final_progress") is None
            and first.get("sample_count") == 0
            and first.get("monitor_error", {}).get("type") == "SubprocessError"
            and first.get("monitor_error", {}).get("message") == "Exception occurred in preexec_fn.",
            "PREVIOUS_FAILURE_NOT_PREEXEC_BOOTSTRAP")
    placeholder = read_json(first_path.parent / "results.json")
    require(placeholder.get("author") == "supervisor"
            and placeholder.get("status") == "WORKER_DID_NOT_COMPLETE"
            and placeholder.get("query_verdict") is None, "PREVIOUS_RESULT_NOT_PLACEHOLDER")
    diagnostic_spec = recovery["stdlib_diagnostic"]
    diagnostic_path = Path(diagnostic_spec["path"]).resolve()
    require(diagnostic_path == ROOT / "audits/launcher_self_diagnostic.json"
            and digest(diagnostic_path) == diagnostic_spec["sha256"], "DIAGNOSTIC_IDENTITY_MISMATCH")
    diagnostic = read_json(diagnostic_path)
    require(diagnostic.get("kind") == "LAUNCHER_SELF_ONLY_STD_LIB_DIAGNOSTIC"
            and diagnostic.get("no_target_import_or_SQL_or_solver") is True
            and diagnostic.get("inherited_nice") == 0 and diagnostic.get("final_nice") == 15,
            "DIAGNOSTIC_SCOPE_INVALID")
    steps = diagnostic.get("steps", [])
    require(len(steps) == 4 and [(x.get("call"), x.get("status")) for x in steps]
            == [("setpriority_15", "RETURNED"), ("CPU_4", "RETURNED"), ("CORE_0", "RETURNED"), ("RSS_256MiB", "FAILED")]
            and steps[3].get("type") == "ValueError"
            and steps[3].get("message") == "current limit exceeds maximum limit", "DIAGNOSTIC_FAILURE_CHANGED")
    require(finite_number(diagnostic["cpu_at_report"], "DIAGNOSTIC_CPU") < 1.0, "DIAGNOSTIC_RESERVE_EXCEEDED")
    old_accounting = previous["cpu_accounting"]
    require(abs(finite_number(old_accounting["pre_registered_scan_cpu_seconds"], "PREVIOUS_SCAN_CHARGE") - scan_charge) < 1e-9,
            "ORIGINAL_SCAN_CHARGE_CHANGED")
    previous_total = finite_number(old_accounting["conservative_charged_total_seconds"], "PREVIOUS_TOTAL")
    require(previous_total >= scan_charge, "PREVIOUS_TOTAL_BELOW_SCAN")
    extra = finite_number(recovery["extra_prior_charge_seconds"], "EXTRA_PRIOR_CHARGE", 1.0)
    require(extra + 1e-9 >= previous_total - scan_charge + 1.0, "RECOVERY_PRIOR_CHARGE_TOO_LOW")
    amendment_spec = protocol["amendment"]
    amendment_path = Path(amendment_spec["path"]).resolve()
    require(amendment_path == ROOT / "decisions/bootstrap_amendment_01.json"
            and digest(amendment_path) == amendment_spec["sha256"], "AMENDMENT_IDENTITY_MISMATCH")
    amendment = read_json(amendment_path)
    require(amendment.get("id") == "ROUND03_BOOTSTRAP_AMENDMENT_01"
            and amendment.get("status") == "PROSPECTIVE_BEFORE_RECOVERY", "AMENDMENT_NOT_PROSPECTIVE")
    diagnostic_accounting_spec = amendment["diagnostic_accounting"]
    diagnostic_accounting_path = Path(diagnostic_accounting_spec["path"]).resolve()
    require(diagnostic_accounting_path == ROOT / "audits/bootstrap_diagnostic_accounting.json"
            and digest(diagnostic_accounting_path) == diagnostic_accounting_spec["sha256"], "DIAGNOSTIC_ACCOUNTING_IDENTITY_MISMATCH")
    diagnostic_accounting = read_json(diagnostic_accounting_path)
    require(finite_number(diagnostic_accounting["observed_CPU_sum_seconds"], "DIAGNOSTIC_TOTAL") < 1.0
            and diagnostic_accounting["additional_conservative_charge_seconds"] == 1.0,
            "DIAGNOSTIC_ACCOUNTING_RESERVE_INVALID")
    evidence = {previous_path, diagnostic_path, ORIGINAL_PROTOCOL.resolve(), ORIGINAL_SUPERVISOR.resolve()}
    evidence.update({amendment_path, diagnostic_accounting_path})
    evidence.update(path.resolve() for path in previous_path.parent.rglob("*") if path.is_file())
    require(evidence <= frozen_paths, "PREVIOUS_EVIDENCE_MISSING_FROM_FREEZE: " + str(sorted(str(x) for x in evidence - frozen_paths)))
    effective = scan_charge + extra
    report.update(bootstrap_recovery=recovery, original_scan_cpu_seconds=scan_charge,
                  extra_prior_charge_seconds=extra, effective_prior_cpu_seconds=effective,
                  bootstrap_diagnostic_reserve_seconds=1.0,
                  bootstrap_note="Prospective one-time amendment after fork/preexec failure; no worker execution. Diagnostic reserve is charged, not measured. No third batch or recursive recovery.")
    return effective, evidence


def validate_inputs(arguments, report):
    require(sys.platform == "darwin" and sys.version_info[:2] == (3, 12), "REQUIRES_DARWIN_PYTHON_3_12")
    require(sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode, "REQUIRES_-B_-I_-S")
    freeze = read_json(arguments.freeze)
    policy = read_json(POLICY)
    protocol = read_json(arguments.protocol)
    require(protocol["id"] == "calibergraph-03-official-diagnostic-v1", "PROTOCOL_ID_MISMATCH")
    require(policy["id"] == "calibergraph-03-probe-supervisor-v1", "POLICY_ID_MISMATCH")
    fixed_policy = {"registered_slot_capacity": 32, "maximum_workers": 1,
                    "worker_cpu_hard_seconds": 4, "worker_wall_seconds": 5.0,
                    "worker_rss_bytes": 268435456, "batch_cpu_seconds": 120.0,
                    "stop_new_case_at_cpu_seconds": 110.0,
                    "minimum_cpu_remaining_before_start": 10.0,
                    "active_parent_and_reaped_stop_seconds": 115.0,
                    "solver_watchdog_trigger_seconds": 1.9,
                    "solver_cumulative_wall_seconds": 2.0,
                    "poll_target_seconds": 0.05, "max_1min_load": 4.0,
                    "min_memory_available_percentage": 25, "maximum_checks_per_case": 4}
    require(all(policy.get(k) == v for k, v in fixed_policy.items()), "SUPERVISOR_FIXED_POLICY_MISMATCH")
    expected = {"worker_cpu_limit_seconds": 4, "worker_wall_limit_seconds": 5,
                "external_rss_limit_bytes": 268435456, "solver_cumulative_wall_limit_seconds": 2,
                "contract_check_timeout_ms": 100, "query_check_timeout_ms": 800}
    require(all(protocol.get(k) == v for k, v in expected.items()), "WORKER_BUDGET_PROTOCOL_MISMATCH")
    python_path = Path(sys.executable).resolve()
    require(python_path == Path(freeze["interpreter"]["resolved"]).resolve(), "FROZEN_INTERPRETER_MISMATCH")
    tentative_charge = finite_number(protocol["supervisor"]["pre_registered_scan_cpu_seconds"], "DECLARED_SCAN_CHARGE", 0.000001)
    tentative_charge += finite_number(protocol["supervisor"]["bootstrap_recovery"]["extra_prior_charge_seconds"], "DECLARED_EXTRA_PRIOR_CHARGE", 1.0)
    def precheck_cpu_guard():
        require(not STOP_REQUESTED, "PRECHECK_EXTERNAL_STOP")
        # An unverified declared charge can conservatively stop precheck, but is
        # not reported as verified until its source receipt passes below.
        require(accounting(tentative_charge)["observed_total_cpu_seconds"] < 110.0,
                "PRECHECK_CPU_RESERVE_STOP")
    precheck_cpu_guard()
    frozen_paths = set()
    for entry in freeze["files"]:
        precheck_cpu_guard()
        path = Path(entry["path"]).resolve()
        require(digest(path, precheck_cpu_guard) == entry["sha256"], "FREEZE_MISMATCH: " + str(path))
        frozen_paths.add(path)
    supervisor = protocol["supervisor"]
    require(Path(supervisor["python_executable"]).resolve() == python_path, "PROTOCOL_INTERPRETER_MISMATCH")
    require(Path(supervisor["policy"]["path"]).resolve() == POLICY.resolve()
            and supervisor["policy"]["sha256"] == digest(POLICY), "PROTOCOL_POLICY_MISMATCH")
    scan_spec = supervisor["scan_cost_receipt"]
    scan_path = Path(scan_spec["path"]).resolve()
    require(digest(scan_path) == scan_spec["sha256"], "SCAN_RECEIPT_HASH_MISMATCH")
    scan = read_json(scan_path)
    require(scan.get("status") == "RETURNED", "SCAN_DID_NOT_RETURN_SUCCESSFULLY")
    scan_observed = finite_number(scan["observed_total_cpu_at_report"], "SCAN_OBSERVED")
    scan_charge = finite_number(supervisor["pre_registered_scan_cpu_seconds"], "SCAN_CHARGE", 0.000001)
    require(scan_charge + 1e-9 >= scan_observed + policy["scan_receipt_tail_charge_seconds"], "SCAN_CHARGE_TOO_LOW")
    # Preserve the verified prior cost even when a later input check fails.
    report["pre_registered_scan_cpu_seconds"] = scan_charge
    report["scan_cost_receipt"] = scan_spec
    effective_prior, recovery_evidence = validate_bootstrap_recovery(protocol, scan_charge, frozen_paths, report)
    input_path = Path(protocol["input"]["path"]).resolve()
    require(digest(input_path, precheck_cpu_guard) == protocol["input"]["sha256"], "INPUT_HASH_MISMATCH")
    require(input_path.stat().st_size <= 4 * 1024 * 1024, "INPUT_TOO_LARGE")
    lines = input_path.read_text(encoding="utf-8").splitlines()
    require(0 < len(lines) <= policy["registered_slot_capacity"] and all(x.strip() for x in lines), "JSONL_MUST_HAVE_1_TO_32_NONEMPTY_LINES")
    cases = [json.loads(line) for line in lines]
    case_ids = [case["id"] for case in cases]
    require(all(isinstance(x, str) and x for x in case_ids), "CASE_IDS_MUST_BE_NONEMPTY_STRINGS")
    require(case_ids == protocol["registered_case_ids"] and len(set(case_ids)) == len(case_ids), "CASE_ORDER_OR_ID_MISMATCH")
    runtime_path = Path(protocol["runtime_lock"]["path"]).resolve()
    require(digest(runtime_path) == protocol["runtime_lock"]["sha256"], "RUNTIME_LOCK_HASH_MISMATCH")
    required = {Path(__file__).resolve(), WORKER.resolve(),
                (ROOT / "code/official_diagnostic_backend.py").resolve(),
                (ROOT / "code/official_contract_admission.py").resolve(),
                POLICY.resolve(), arguments.protocol.resolve(),
                input_path, runtime_path, scan_path, python_path}
    required.update(recovery_evidence)
    require(required <= frozen_paths, "REQUIRED_FILE_MISSING_FROM_FREEZE: " + str(sorted(str(x) for x in required - frozen_paths)))
    for index in range(policy["registered_slot_capacity"]):
        report["slots"][index].update(
            case_id=case_ids[index] if index < len(case_ids) else None,
            status="NOT_RUN" if index < len(case_ids) else "NOT_REGISTERED")
    report.update(registered_denominator=len(case_ids), registered_case_ids=case_ids,
                  policy=policy, pre_registered_scan_cpu_seconds=scan_charge,
                  scan_cost_receipt=scan_spec, runtime_lock=protocol["runtime_lock"],
                  interpreter=str(python_path))
    return policy, case_ids, python_path, effective_prior


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--freeze", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()
    arguments.freeze = arguments.freeze.resolve()
    arguments.protocol = arguments.protocol.resolve()
    output = arguments.out.resolve()
    require(output.parent == ROOT / "runs" and re.fullmatch(r"batch_[A-Za-z0-9_-]+", output.name), "OUTPUT_MUST_BE_PROJECT_RUNS_BATCH_NAME")
    require(output == ROOT / "runs/batch_02", "ONE_RECOVERY_OUTPUT_ONLY_NO_THIRD_BATCH")
    require(not output.exists(), "OUTPUT_ALREADY_EXISTS")
    output.mkdir(parents=True)
    report = {"id": "calibergraph-03-batch-receipt-v1", "status": "REGISTERING",
              "created_utc": utc(), "supervisor_sha256": digest(__file__),
              "freeze_sha256": digest(arguments.freeze), "protocol_sha256": digest(arguments.protocol),
              "registered_denominator": None,
              "slots": [{"slot": i, "case_id": None, "status": "NOT_RUN"} for i in range(32)],
              "violations": [], "read_reserve": False, "worker_count_maximum": 1}
    atomic_json(output / "batch_receipt.json", report)  # All 32 slots predate any worker.
    scan_charge = None
    lock = None
    locked = False
    exit_code = 2
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, request_stop)
    with (output / "batch_events.jsonl").open("x", encoding="utf-8") as events:
        try:
            lock = (ROOT / "runs/.single_worker.lock").open("a")
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            locked = True
            with (ROOT / "runs/.bootstrap_recovery_consumed.json").open("x", encoding="utf-8") as marker:
                json.dump({"created_utc": utc(), "output": str(output), "protocol_sha256": report["protocol_sha256"],
                           "no_further_recovery": True}, marker)
                marker.flush()
                os.fsync(marker.fileno())
            policy, case_ids, python_path, scan_charge = validate_inputs(arguments, report)
            report["status"] = "REGISTERED_BEFORE_WORKERS"
            atomic_json(output / "batch_receipt.json", report)
            event(events, "BATCH_REGISTERED", registered_denominator=len(case_ids), capacity=32)
            halt_reason = None
            for index, case_id in enumerate(case_ids):
                charged = accounting(scan_charge)["observed_total_cpu_seconds"]
                if STOP_REQUESTED:
                    halt_reason = STOP_REQUESTED
                    break
                if charged >= policy["stop_new_case_at_cpu_seconds"] or policy["batch_cpu_seconds"] - charged < policy["minimum_cpu_remaining_before_start"]:
                    halt_reason = "BATCH_START_CPU_RESERVE_STOP"
                    break
                observation = machine_probe(policy)
                event(events, "CASE_PREFLIGHT", case_index=index, observation=observation)
                if not observation["admitted"]:
                    halt_reason = "MACHINE_PREFLIGHT_GATE_STOP"
                    break
                # Resource-probe CPU is reaped and charged before admission.
                charged = accounting(scan_charge)["observed_total_cpu_seconds"]
                if charged >= policy["stop_new_case_at_cpu_seconds"] or policy["batch_cpu_seconds"] - charged < policy["minimum_cpu_remaining_before_start"]:
                    halt_reason = "BATCH_START_CPU_RESERVE_STOP_AFTER_PROBE"
                    break
                slot = report["slots"][index]
                slot.update(status="STARTING", preflight=observation)
                atomic_json(output / "batch_receipt.json", report)
                directory = output / ("case_" + format(index, "02d"))
                result = run_case(index, case_id, directory, arguments.protocol, python_path, scan_charge, policy)
                slot.update(status=result["status"], receipt=str(directory / "supervisor_receipt.json"),
                            worker_report_status=result.get("worker_report_status"),
                            worker_record_unmodified=result.get("worker_record_unmodified"),
                            violations=result["violations"])
                report["cpu_accounting"] = accounting(scan_charge)
                atomic_json(output / "batch_receipt.json", report)
                if result["stop_remainder"]:
                    halt_reason = result["stop_remainder"]
                    break
            report["status"] = "STOPPED_REMAINDER_NOT_RUN" if halt_reason else "REGISTERED_SEQUENCE_FINISHED"
            report["halt_reason"] = halt_reason
            for slot in report["slots"]:
                if slot["status"] == "NOT_RUN":
                    slot["not_run_reason"] = halt_reason or "NOT_ATTEMPTED"
            exit_code = 0 if halt_reason is None else 2
        except BaseException as error:
            report.update(status="BATCH_PRECHECK_OR_MONITOR_FAILED", error={"type": type(error).__name__, "message": str(error)[:4000]})
            for slot in report["slots"]:
                if slot["status"] == "NOT_RUN":
                    slot["not_run_reason"] = "BATCH_FAILURE_NO_REPLACEMENT"
        finally:
            if scan_charge is None:
                scan_charge = report.get("effective_prior_cpu_seconds")
            report["finished_utc"] = utc()
            report["cpu_accounting"] = accounting(scan_charge)
            report["cpu_accounting"]["reserved_final_report_exit_tail_seconds"] = 0.1
            total = report["cpu_accounting"]["observed_total_cpu_seconds"]
            conservative = None if total is None else total + 0.1
            report["cpu_accounting"]["conservative_charged_total_seconds"] = conservative
            if conservative is not None and conservative > 120.0:
                report["violations"].append("BATCH_CONSERVATIVE_CHARGE_EXCEEDED_120S")
                exit_code = 2
            report["registered_attempts"] = sum(x["status"] not in ("NOT_RUN", "NOT_REGISTERED") for x in report["slots"])
            report["measurement_note"] = "Sampled guards may overshoot. Keep all per-case violations and censored durations; no exact wall/RSS/solver hard-bound claim."
            event(events, "BATCH_FINISHED", status=report["status"], accounting=report["cpu_accounting"], violations=report["violations"])
            atomic_json(output / "batch_receipt.json", report)
            if lock is not None:
                if locked:
                    fcntl.flock(lock, fcntl.LOCK_UN)
                lock.close()
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
