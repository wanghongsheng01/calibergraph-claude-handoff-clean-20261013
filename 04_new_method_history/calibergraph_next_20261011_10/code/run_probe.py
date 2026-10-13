"""Darwin-only, default-disabled, one-shot owned-process supervisor.

STATIC DRAFT: do not run before independent review and root freeze. Importing
this module defines functions only. No child, file, or enumeration at import.
"""

import argparse
from contextlib import contextmanager
import ctypes
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import sys
import time

from finite_core import (
    EXPECTED_BODIES, EXPECTED_COMPARISONS, EXPECTED_MODELS, EXPECTED_PAIRS,
    active_variables, canonical_json, check_controls, classify, covers,
    digest, enumerate_endomorphisms, full_key_chase, inventory, models,
    original_counts, subsets,
)

EXECUTION_ENABLED = False  # Root may edit only after independent pre-review.
SUPERVISOR_CPU_HARD_S = 1
WORKER_CPU_HARD_S = 1
WALL_HARD_S = 3.0
RSS_LIMIT_BYTES = 128 * 1024 * 1024
MAX_LOAD_1M = 4.0
MIN_AVAILABLE_FRACTION = 0.25
NICE = 15
POLL_SECONDS = 0.01
RUN_LABEL = "only_attempt"


def write_json(path, payload):
    with path.open("x", encoding="ascii") as stream:
        stream.write(canonical_json(payload) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def append_json(stream, payload):
    stream.write(canonical_json(payload) + "\n")


def add_costs(target, addition):
    for key, value in addition.items():
        target[key] = target.get(key, 0) + value


def file_sha256(path):
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def verify_freeze(root, supplied):
    """Review receipt and hashes are root-authored, never created by a run."""
    expected = root / "protocols" / "freeze.json"
    if supplied.resolve() != expected.resolve() or supplied.is_symlink():
        raise RuntimeError("freeze must be protocols/freeze.json, not a symlink")
    receipt = json.loads(supplied.read_text(encoding="ascii"))
    if (receipt.get("status") != "FROZEN_AFTER_INDEPENDENT_PRE_REVIEW"
            or receipt.get("execution_authorized") is not True
            or not receipt.get("independent_reviewer")
            or not receipt.get("review_receipt_relative_path")):
        raise RuntimeError("missing independent pre-review/root freeze evidence")
    review = root / receipt["review_receipt_relative_path"]
    if not review.resolve().is_relative_to(root.resolve()) or not review.is_file():
        raise RuntimeError("review evidence must be a local file under round 10")
    if file_sha256(review) != receipt.get("review_receipt_sha256"):
        raise RuntimeError("review evidence hash mismatch")
    required = ("code/finite_core.py", "code/run_probe.py",
                "protocols/bounded_probe_draft.md")
    for relative in required:
        path = root / relative
        if path.is_symlink() or file_sha256(path) != receipt.get("sha256", {}).get(relative):
            raise RuntimeError("missing/mismatched frozen source hash: " + relative)
    if receipt.get("denominators") != {
            "bodies": 129, "pairs": 2739, "models": 64, "pair_models": 175296}:
        raise RuntimeError("frozen denominator mismatch")
    runtime = receipt.get("runtime", {})
    executable = Path(runtime.get("executable", ""))
    if (not executable.is_absolute() or not executable.is_file()
            or executable.resolve() != Path(sys.executable).resolve()
            or file_sha256(executable) != runtime.get("sha256")
            or runtime.get("version") != sys.version.split()[0]
            or runtime.get("implementation") != sys.implementation.name
            or runtime.get("worker_flags") != ["-B", "-E", "-s", "-S"]
            or not all((sys.flags.dont_write_bytecode, sys.flags.ignore_environment,
                        sys.flags.no_user_site, sys.flags.no_site))):
        raise RuntimeError("unreviewed Python runtime or worker flags")
    return receipt


class DarwinReadOnlyResources:
    """Only four read-only native APIs, plus release of the acquired port.

    Whitelist: sysctlbyname(hw.memsize), mach_host_self,
    host_statistics64(HOST_VM_INFO64), proc_pidinfo(PROC_PIDTASKINFO), and
    mach_port_deallocate for our host port. No shell, helper, network, or GPU.
    """

    def __init__(self):
        if sys.platform != "darwin":
            raise RuntimeError("reviewed platform is Darwin only")
        self.system = ctypes.CDLL("/usr/lib/libSystem.B.dylib", use_errno=True)
        self.proc = ctypes.CDLL("/usr/lib/libproc.dylib", use_errno=True)
        self.system.sysctlbyname.argtypes = (
            ctypes.c_char_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_size_t),
            ctypes.c_void_p, ctypes.c_size_t)
        self.system.sysctlbyname.restype = ctypes.c_int
        self.system.mach_host_self.argtypes = ()
        self.system.mach_host_self.restype = ctypes.c_uint
        self.system.host_statistics64.argtypes = (
            ctypes.c_uint, ctypes.c_int, ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_uint))
        self.system.host_statistics64.restype = ctypes.c_int
        self.system.mach_port_deallocate.argtypes = (ctypes.c_uint, ctypes.c_uint)
        self.system.mach_port_deallocate.restype = ctypes.c_int
        self.proc.proc_pidinfo.argtypes = (
            ctypes.c_int, ctypes.c_int, ctypes.c_uint64,
            ctypes.c_void_p, ctypes.c_int)
        self.proc.proc_pidinfo.restype = ctypes.c_int

    def available_memory(self):
        physical = ctypes.c_uint64()
        size = ctypes.c_size_t(ctypes.sizeof(physical))
        if self.system.sysctlbyname(b"hw.memsize", ctypes.byref(physical),
                                   ctypes.byref(size), None, 0) != 0:
            raise RuntimeError("hw.memsize unavailable")
        # HOST_VM_INFO64 starts with free, active, inactive, wire uint32 counts.
        # Deliberately omit speculative/purgeable/compressed pages; free+inactive
        # is a conservative available-memory proxy, not Apple's pressure metric.
        words = (ctypes.c_uint32 * 64)()
        count = ctypes.c_uint(64)
        host = self.system.mach_host_self()
        try:
            result = self.system.host_statistics64(host, 4, words, ctypes.byref(count))
        finally:
            task = ctypes.c_uint.in_dll(self.system, "mach_task_self_").value
            self.system.mach_port_deallocate(task, host)
        if result != 0 or count.value < 4 or physical.value <= 0:
            raise RuntimeError("HOST_VM_INFO64 unavailable")
        available = (int(words[0]) + int(words[2])) * os.sysconf("SC_PAGE_SIZE")
        if not 0 <= available <= physical.value:
            raise RuntimeError("invalid native memory telemetry")
        return {"physical_bytes": physical.value,
                "available_proxy_bytes": available,
                "available_fraction": available / physical.value,
                "definition": "Darwin free_count+inactive_count times page size"}

    def rss(self, pid):
        # PROC_PIDTASKINFO begins with uint64 virtual_size, resident_size.
        buffer = (ctypes.c_uint64 * 32)()
        size = self.proc.proc_pidinfo(pid, 4, 0, buffer, ctypes.sizeof(buffer))
        if size < 16:
            raise RuntimeError("RSS telemetry unavailable for owned PID")
        return int(buffer[1])


def prepare_notrun_slots(run_dir):
    """All denominators exist BEFORE host precheck or science begins."""
    write_json(run_dir / "denominator-contract.json", {
        "status": "KNOWN_DENOMINATORS_SLOT_MATERIALIZATION_PENDING",
        "bodies": 129, "pairs": 2739, "models": 64, "pair_models": 175296,
        "scientific_pairs_started": 0,
        "partial_baseline_never_means_full_slot_materialization": True})
    actual_bodies = 0
    actual_pairs = 0
    with (run_dir / "body-inventory.jsonl").open("x", encoding="ascii") as body_stream, \
            (run_dir / "pair-slots-notrun.jsonl").open("x", encoding="ascii") as pair_stream:
        for body_index, body, pairs in inventory():
            actual_bodies += 1
            append_json(body_stream, {"body_index": body_index, "original_body": body,
                        "active_variables": active_variables(body),
                        "subset_order": subsets(active_variables(body)),
                        "pair_count": len(pairs), "chase_status": "NOTRUN",
                        "chase_map": None, "chased_body": None})
            for pair in pairs:
                actual_pairs += 1
                append_json(pair_stream, {**pair, "status": "NOTRUN", "cover": None,
                                         "counts_M_64": [None] * 64,
                                         "counts_N_64": [None] * 64,
                                         "equal_64": None,
                                         "first_distinguishing_model": None})
        for stream in (body_stream, pair_stream):
            stream.flush()
            os.fsync(stream.fileno())
    model_table = tuple(models())
    write_json(run_dir / "model-inventory.json", {
        "models": [{"model_index": index, "key_choices": choices, "rows": rows}
                   for index, choices, rows in model_table],
        "model_order_sha256": digest(model_table),
        "all_model_status_before_precheck": "NOTRUN"})
    if (actual_bodies, actual_pairs, len(model_table)) != (129, 2739, 64):
        raise RuntimeError("metadata denominator mismatch")
    write_json(run_dir / "initial-status.json", {
        "status": "NOTRUN_BEFORE_HOST_PRECHECK", "body_denominator": actual_bodies,
        "pair_denominator": actual_pairs, "model_denominator": len(model_table),
        "pair_model_denominator": EXPECTED_COMPARISONS,
        "completed_pair_models": 0, "notrun_pair_models": EXPECTED_COMPARISONS})
    write_json(run_dir / "control-slots-notrun.json", {
        "controls": [{"name": name, "status": "NOTRUN"} for name in (
            "same_key_chase", "triangle_legal_PK", "legal_projection_distinction")],
        "rejected_old_control": "CONTROL_SPEC_INVALID_REJECTED; see draft protocol"})


def worker(run_dir):
    model_table = tuple(models())
    total_costs = {}
    timings = {"chase_cpu_ns": 0, "endomorphisms_cpu_ns": 0,
               "cover_cpu_ns": 0, "original_evaluator_cpu_ns": 0,
               "result_serialization_cpu_ns": 0}
    all_controls = []
    completed_pairs = 0
    completed_bodies = 0
    stop_reason = None
    with (run_dir / "body-results.jsonl").open("x", encoding="ascii") as body_stream, \
            (run_dir / "pair-results.jsonl").open("x", encoding="ascii") as pair_stream:
        for body_index, original_body, pair_specs in inventory():
            projections = subsets(active_variables(original_body))
            start = time.process_time_ns()
            chased_body, chase_map, chase_cost = full_key_chase(original_body)
            timings["chase_cpu_ns"] += time.process_time_ns() - start
            start = time.process_time_ns()
            endomorphisms, endo_cost = enumerate_endomorphisms(chased_body)
            timings["endomorphisms_cpu_ns"] += time.process_time_ns() - start
            add_costs(total_costs, endo_cost)
            count_vectors = [[] for _ in projections]
            evaluator_cost = {}
            start = time.process_time_ns()
            for model_index, choices, rows in model_table:
                counts, costs = original_counts(original_body, projections, rows)
                add_costs(evaluator_cost, costs)
                for vector, value in zip(count_vectors, counts):
                    vector.append(value)
            timings["original_evaluator_cpu_ns"] += time.process_time_ns() - start
            add_costs(total_costs, evaluator_cost)
            results = []
            cover_cost = {}
            start = time.process_time_ns()
            for pair in pair_specs:
                left, right = pair["subset_indices"]
                M, N = projections[left], projections[right]
                chased_M = tuple(sorted({chase_map[variable] for variable in M}))
                chased_N = tuple(sorted({chase_map[variable] for variable in N}))
                cover, costs = covers(chased_body, chased_M, chased_N, endomorphisms)
                add_costs(cover_cost, costs)
                equality = "".join("1" if m == n else "0"
                                   for m, n in zip(count_vectors[left], count_vectors[right]))
                first = equality.find("0")
                distinguishing = None if first == -1 else {
                    "model_index": first, "rows": model_table[first][2],
                    "count_M": count_vectors[left][first],
                    "count_N": count_vectors[right][first]}
                results.append({**pair, "status": "COMPLETE",
                    "chased_M": chased_M, "chased_N": chased_N, "cover": cover,
                    "counts_M_64": count_vectors[left], "counts_N_64": count_vectors[right],
                    "equal_64": equality, "first_distinguishing_model": distinguishing,
                    "classification": classify(cover["cover_EQ"], equality)})
            timings["cover_cpu_ns"] += time.process_time_ns() - start
            add_costs(total_costs, cover_cost)
            controls = check_controls(original_body, projections, count_vectors,
                                      chased_body, chase_map, results, model_table)
            all_controls.extend(controls)
            start = time.process_time_ns()
            append_json(body_stream, {
                "body_index": body_index, "original_body": original_body,
                "original_pair_count": len(pair_specs), "chased_body": chased_body,
                "chase_map": chase_map, "chase_cost": chase_cost,
                "endomorphisms": endomorphisms, "endomorphism_cost": endo_cost,
                "cover_cost": cover_cost, "evaluator_cost": evaluator_cost,
                "controls": controls, "status": "COMPLETE"})
            for result in results:
                append_json(pair_stream, result)
                completed_pairs += 1
            for stream in (body_stream, pair_stream):
                stream.flush()
            timings["result_serialization_cpu_ns"] += time.process_time_ns() - start
            completed_bodies += 1
            if any(control["status"] != "PASS" for control in controls):
                stop_reason = "CONTROL_FAILURE"
                break
            if any(result["classification"] == "SUFFICIENCY_FALSIFIED" for result in results):
                stop_reason = "SUFFICIENCY_FALSIFIED"
                break
        for stream in (body_stream, pair_stream):
            stream.flush()
            os.fsync(stream.fileno())
    control_names = {control["name"] for control in all_controls}
    if stop_reason is None and (completed_bodies != EXPECTED_BODIES
            or completed_pairs != EXPECTED_PAIRS
            or control_names != {"same_key_chase", "triangle_legal_PK",
                                 "legal_projection_distinction"}):
        stop_reason = "DENOMINATOR_OR_CONTROL_COVERAGE_FAILURE"
    write_json(run_dir / "worker-receipt.json", {
        "status": stop_reason or "COMPLETE", "completed_bodies": completed_bodies,
        "completed_pairs": completed_pairs, "controls": all_controls,
        "cost_counters": total_costs, "timings": timings,
        "worker_self_cpu_s": time.process_time(),
        "scientific_scope": "finite-domain observation only; no unbounded necessity claim"})
    return 0 if stop_reason is None else 3


def read_result_overlay(run_dir):
    """Conservative recovery: validate each complete line; keep tail forensic."""
    result_path = run_dir / "pair-results.jsonl"
    overlay = {}
    parse_errors = []
    if result_path.exists():
        with result_path.open("r", encoding="ascii") as stream:
            for line_number, line in enumerate(stream, 1):
                try:
                    row = json.loads(line)
                    if row["pair_id"] in overlay:
                        raise ValueError("duplicate pair ID")
                    if row["status"] != "COMPLETE" or len(row["equal_64"]) != 64:
                        raise ValueError("incomplete result")
                    if len(row["counts_M_64"]) != 64 or len(row["counts_N_64"]) != 64:
                        raise ValueError("incomplete count arrays")
                    if digest(row["signature"]) != row["signature_sha256"]:
                        raise ValueError("signature digest mismatch")
                    M, N = row["counts_M_64"], row["counts_N_64"]
                    if any(type(value) is not int or value < 0 for value in M + N):
                        raise ValueError("invalid count value")
                    equality = "".join("1" if m == n else "0" for m, n in zip(M, N))
                    if equality != row["equal_64"]:
                        raise ValueError("equality bits disagree with counts")
                    cover = row["cover"]
                    if (any(type(cover[key]) is not bool for key in ("forward", "reverse", "cover_EQ"))
                            or cover["cover_EQ"] != (cover["forward"] and cover["reverse"])):
                        raise ValueError("invalid cover booleans")
                    if row["classification"] != classify(cover["cover_EQ"], equality):
                        raise ValueError("classification mismatch")
                    overlay[row["pair_id"]] = row
                except (ValueError, KeyError, TypeError) as error:
                    parse_errors.append({"line": line_number, "error": str(error)})
    return overlay, parse_errors


def finalize(run_dir, status, evidence, native):
    overlay, parse_errors = read_result_overlay(run_dir)
    evidence["supervisor_rss_after_overlay_bytes"] = native.rss(os.getpid())
    if evidence["supervisor_rss_after_overlay_bytes"] > RSS_LIMIT_BYTES:
        # Do not keep allocating/serializing after detecting an overage.
        raise MemoryError("TRUNCATED_FINALIZATION_RSS; raw ledger/logs retained")
    complete = 0
    classes = {}
    body_ids = set()
    baseline_ids = set()
    baseline_errors = []
    with (run_dir / "pair-slots-notrun.jsonl").open("r", encoding="ascii") as baseline, \
            (run_dir / "pair-slots-final.jsonl").open("x", encoding="ascii") as final_stream:
        for line_number, line in enumerate(baseline, 1):
            try:
                baseline_row = json.loads(line)
                pair_id = baseline_row["pair_id"]
                if pair_id in baseline_ids or digest(baseline_row["signature"]) != baseline_row["signature_sha256"]:
                    raise ValueError("duplicate or corrupt baseline slot")
                baseline_ids.add(pair_id)
            except (ValueError, KeyError, TypeError) as error:
                baseline_errors.append({"line": line_number, "error": str(error)})
                continue
            result = overlay.pop(baseline_row["pair_id"], None)
            if result is not None and result["signature_sha256"] == baseline_row["signature_sha256"]:
                append_json(final_stream, result)
                complete += 1
                body_ids.add(result["body_index"])
                classification = result["classification"]
                classes[classification] = classes.get(classification, 0) + 1
            else:
                baseline_row["notrun_reason"] = status
                append_json(final_stream, baseline_row)
                if result is not None:
                    parse_errors.append({"error": "signature mismatch", "pair_id": result["pair_id"]})
        final_stream.flush()
        os.fsync(final_stream.fileno())
    if overlay:
        parse_errors.append({"error": "unknown result pair IDs", "count": len(overlay)})
    baseline_complete = len(baseline_ids) == EXPECTED_PAIRS and not baseline_errors
    if not baseline_complete:
        status = "FAILED_BASELINE_INCOMPLETE"
    worker_receipt = None
    receipt_path = run_dir / "worker-receipt.json"
    if receipt_path.exists():
        try:
            worker_receipt = json.loads(receipt_path.read_text(encoding="ascii"))
        except (ValueError, OSError) as error:
            parse_errors.append({"error": "worker receipt unreadable: " + str(error)})
    if status == "CHILD_EXITED":
        if (evidence.get("child_exit_code") == 0 and complete == EXPECTED_PAIRS
                and len(body_ids) == EXPECTED_BODIES and not parse_errors
                and worker_receipt is not None and worker_receipt.get("status") == "COMPLETE"):
            status = "COMPLETE_BOUNDED_PROBE"
        else:
            status = "FAILED_OR_TRUNCATED"
    write_json(run_dir / "supervisor-receipt.json", {
        "status": status, "evidence": evidence, "parse_errors": parse_errors,
        "baseline_slots_persisted": len(baseline_ids),
        "baseline_complete": baseline_complete, "baseline_errors": baseline_errors,
        "missing_baseline_slots": EXPECTED_PAIRS - len(baseline_ids),
        "body_denominator": 129, "bodies_with_result_pairs": len(body_ids),
        "pair_denominator": 2739, "complete_pairs": complete,
        "notrun_pairs": EXPECTED_PAIRS - complete,
        "model_denominator": 64, "pair_model_denominator": 175296,
        "complete_pair_models": complete * 64,
        "notrun_pair_models": (EXPECTED_PAIRS - complete) * 64,
        "classifications": classes, "worker_receipt": worker_receipt,
        "no_receipt_rule": "Absent supervisor receipt NEVER means success.",
        "success_requires": ["supervisor-receipt COMPLETE_BOUNDED_PROBE",
                             "accounting-after-finalization present and within budgets",
                             "external caller observes supervisor exit code zero"],
        "unbounded_equivalence_or_necessity_proven": False})
    return status


def kill_and_reap_owned(pid):
    """Only the exact unreaped child PID and its verified self-owned group."""
    try:
        if os.getpgid(pid) == pid:
            os.killpg(pid, signal.SIGKILL)
        else:
            os.kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    return os.wait4(pid, 0)


@contextmanager
def blocked_alarm():
    """Keep fork/ownership and wait4/ownership updates atomic to SIGALRM."""
    previous = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGALRM})
    try:
        yield
    finally:
        signal.pthread_sigmask(signal.SIG_SETMASK, previous)


def poll_owned(owned):
    with blocked_alarm():
        result = os.wait4(owned["pid"], os.WNOHANG)
        if result[0]:
            owned["pid"] = None
            owned["last_wait4"] = result
            owned["exec_reaped_at"] = time.monotonic()
        return result


def terminate_owned(owned):
    with blocked_alarm():
        if owned["pid"] is None:
            return None
        result = kill_and_reap_owned(owned["pid"])
        owned["pid"] = None
        owned["last_wait4"] = result
        owned["exec_reaped_at"] = time.monotonic()
        return result


def usage_payload(usage):
    return {"user_cpu_s": usage.ru_utime, "system_cpu_s": usage.ru_stime,
            "cpu_s": usage.ru_utime + usage.ru_stime,
            "peak_rss_bytes_Darwin": usage.ru_maxrss}


def supervise(root, freeze_path):
    started = time.monotonic()
    usage_at_entry = resource.getrusage(resource.RUSAGE_SELF)
    os.setpriority(os.PRIO_PROCESS, 0, max(NICE, os.getpriority(os.PRIO_PROCESS, 0)))
    resource.setrlimit(resource.RLIMIT_CPU, (SUPERVISOR_CPU_HARD_S, SUPERVISOR_CPU_HARD_S))
    # Parent SIGALRM fallback reaps only the child owned by this invocation.
    # If SIGKILL wins, NOTRUN baseline remains and no receipt is success.
    owned = {"pid": None, "deadline_wait4": None, "last_wait4": None,
             "exec_launch_started": None, "exec_reaped_at": None}

    def deadline_handler(signum, frame):
        pid = owned["pid"]
        if pid is not None:
            try:
                owned["deadline_wait4"] = terminate_owned(owned)
            except ChildProcessError:
                pass
            owned["pid"] = None
        # The one-shot wall timer is exhausted. No exception handler may resume
        # finalization outside it; missing receipts are explicit failure.
        os._exit(124)

    signal.signal(signal.SIGALRM, deadline_handler)
    signal.setitimer(signal.ITIMER_REAL, max(0.001, WALL_HARD_S - (time.monotonic() - started)))
    freeze = verify_freeze(root, freeze_path)
    # A persistent O_EXCL marker is the single attempt gate. No automatic retry.
    runs = root / "runs"
    if runs.is_symlink():
        raise RuntimeError("runs may not be a symlink")
    runs.mkdir(exist_ok=True)
    if runs.resolve().parent != root.resolve():
        raise RuntimeError("runs must be a direct child of round 10")
    with (runs / "attempt.lock").open("x", encoding="ascii") as stream:
        stream.write("Single attempt consumed; do not delete to retry.\n")
    run_dir = runs / RUN_LABEL
    run_dir.mkdir(exist_ok=False)
    evidence = {"pid_supervisor": os.getpid(), "nice": os.getpriority(os.PRIO_PROCESS, 0),
                "budget": {"supervisor_cpu_hard_s": 1, "worker_cpu_hard_s": 1,
                           "aggregate_nominal_cpu_hard_s": 2, "wall_s": 3,
                           "aggregate_sampled_rss_bytes": RSS_LIMIT_BYTES},
                "source_freeze_sha256": file_sha256(freeze_path),
                "self_usage_at_entry": usage_payload(usage_at_entry)}
    status = "FAILED_BEFORE_WORKER"
    child_usage = None
    native = None
    try:
        prepare_notrun_slots(run_dir)
        native = DarwinReadOnlyResources()
        load = os.getloadavg()[0]
        memory = native.available_memory()
        initial_rss = native.rss(os.getpid())
        evidence["host_precheck"] = {"load_1m": load, "memory": memory,
                                      "supervisor_rss_bytes": initial_rss}
        write_json(run_dir / "host-precheck.json", evidence["host_precheck"])
        if (load > MAX_LOAD_1M or memory["available_fraction"] < MIN_AVAILABLE_FRACTION
                or initial_rss * 2 > RSS_LIMIT_BYTES):
            status = "NOTRUN_HOST_PRECHECK_REJECTED"
        elif time.monotonic() - started >= WALL_HARD_S - 0.2:
            status = "NOTRUN_PREPARATION_WALL_BUDGET"
        elif time.process_time() >= 0.8:
            status = "NOTRUN_PREPARATION_CPU_BUDGET"
        else:
            read_fd, write_fd = os.pipe()
            os.set_inheritable(read_fd, True)
            parent_pid = os.getpid()
            with blocked_alarm():
                owned["exec_launch_started"] = time.monotonic()
                pid = os.fork()
                if pid:
                    owned["pid"] = pid
                    # No SIGALRM can run before this child is registered.
                    try:
                        os.setpgid(pid, pid)
                    except PermissionError:
                        # Child may already have set its group and exec'd.
                        if os.getpgid(pid) != pid:
                            raise
            if pid == 0:
                try:
                    os.close(write_fd)
                    # Parent's interval timer is not inherited across fork.
                    # Give the child its own remaining-wall timer so an
                    # unexpected parent SIGKILL cannot create an unbounded orphan.
                    signal.signal(signal.SIGALRM, signal.SIG_DFL)
                    signal.setitimer(signal.ITIMER_REAL, max(
                        0.001, WALL_HARD_S - (time.monotonic() - started)))
                    os.setpgid(0, 0)
                    resource.setrlimit(resource.RLIMIT_CPU, (WORKER_CPU_HARD_S, WORKER_CPU_HARD_S))
                    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
                    executable = freeze["runtime"]["executable"]
                    # ITIMER_REAL and CPU limits survive exec on Darwin. Thus
                    # worker interpreter startup/import is inside both limits.
                    os.execv(executable, [executable, "-B", "-E", "-s", "-S",
                        str(Path(__file__).resolve()), "--freeze", str(freeze_path.resolve()),
                        "--owned-worker", "--run-dir", str(run_dir),
                        "--expected-parent", str(parent_pid),
                        "--authorization-fd", str(read_fd)])
                    raise RuntimeError("exec unexpectedly returned")
                except BaseException as error:
                    try:
                        write_json(run_dir / "worker-error.json", {
                            "status": "WORKER_EXCEPTION", "type": type(error).__name__,
                            "message": str(error)[:500]})
                    except BaseException:
                        pass
                    exit_code = 4
                os._exit(exit_code)
            os.close(read_fd)
            os.write(write_fd, b"ROUND10_OWNED_WORKER\n")
            os.close(write_fd)
            evidence["pid_worker"] = pid
            evidence["worker_pgid"] = os.getpgid(pid)
            peak_rss = 0
            samples = 0
            while True:
                ended, wait_status, usage = poll_owned(owned)
                if ended == pid:
                    child_usage = usage
                    evidence["child_exit_code"] = os.waitstatus_to_exitcode(wait_status)
                    status = "CHILD_EXITED"
                    break
                elapsed = time.monotonic() - started
                supervisor_cpu = time.process_time()
                if elapsed >= WALL_HARD_S - 0.15:
                    status = "TRUNCATED_WALL_BUDGET"
                elif supervisor_cpu >= 0.8:
                    status = "TRUNCATED_SUPERVISOR_CPU_RESERVE"
                else:
                    try:
                        rss = native.rss(os.getpid()) + native.rss(pid)
                    except RuntimeError:
                        # A just-exited worker can disappear from telemetry.
                        ended, wait_status, usage = poll_owned(owned)
                        if ended == pid:
                            child_usage = usage
                            evidence["child_exit_code"] = os.waitstatus_to_exitcode(wait_status)
                            status = "CHILD_EXITED"
                            break
                        raise
                    peak_rss = max(peak_rss, rss)
                    samples += 1
                    if rss > RSS_LIMIT_BYTES:
                        status = "TRUNCATED_AGGREGATE_RSS"
                    else:
                        time.sleep(POLL_SECONDS)
                        continue
                _, wait_status, child_usage = terminate_owned(owned)
                evidence["child_exit_code"] = os.waitstatus_to_exitcode(wait_status)
                break
            evidence["aggregate_rss_peak_sampled_bytes"] = peak_rss
            evidence["rss_samples"] = samples
    except BaseException as error:
        status = "FAILED_OR_TRUNCATED_" + type(error).__name__
        evidence["error"] = str(error)[:500]
    finally:
        if owned["pid"] is not None:
            try:
                _, wait_status, child_usage = terminate_owned(owned)
                evidence["child_exit_code"] = os.waitstatus_to_exitcode(wait_status)
            except ChildProcessError:
                pass
            owned["pid"] = None
        if owned["deadline_wait4"] is not None:
            _, wait_status, child_usage = owned["deadline_wait4"]
            evidence["child_exit_code"] = os.waitstatus_to_exitcode(wait_status)
        elif owned["last_wait4"] is not None:
            _, wait_status, child_usage = owned["last_wait4"]
            evidence["child_exit_code"] = os.waitstatus_to_exitcode(wait_status)
        if child_usage is not None:
            evidence["worker_wait4"] = usage_payload(child_usage)
        if owned["exec_launch_started"] is not None and owned["exec_reaped_at"] is not None:
            evidence["worker_exec_lifecycle_wall"] = (
                owned["exec_reaped_at"] - owned["exec_launch_started"])
        evidence["worker_exec_lifecycle_definition"] = (
            "supervisor monotonic immediately before fork through wait4 reap; "
            "includes worker exec/startup/exit and polling latency; "
            "does not cover supervisor interpreter startup wall")
        current_usage = resource.getrusage(resource.RUSAGE_SELF)
        evidence["supervisor_self_at_finalization"] = usage_payload(current_usage)
        evidence["aggregate_cpu_s_before_finalization"] = (
            current_usage.ru_utime + current_usage.ru_stime
            + (child_usage.ru_utime + child_usage.ru_stime if child_usage is not None else 0))
        evidence["wall_s_before_finalization"] = time.monotonic() - started
    # Finalization remains inside the same CPU/wall budgets, including hashing
    # and serialization. Timeout here leaves no success receipt; no retry.
    if native is None:
        # Native telemetry failure is a failed attempt. Preserve the original
        # ledger even if finalization cannot obtain a safe RSS sample.
        write_json(run_dir / "supervisor-failure.json", {
            "status": status, "evidence": evidence, "pair_denominator": 2739,
            "pair_model_denominator": 175296, "complete_pairs": 0,
            "notrun_pairs": 2739, "notrun_pair_models": 175296,
            "slot_materialization_may_be_incomplete": True})
        return 2
    if status == "TRUNCATED_AGGREGATE_RSS":
        write_json(run_dir / "supervisor-failure.json", {
            "status": status, "evidence": evidence, "pair_denominator": 2739,
            "pair_model_denominator": 175296,
            "completed_or_notrun_counts": "UNRECOVERED; inspect immutable baseline and raw logs",
            "recovery_skipped_to_avoid_more_memory_work": True})
        return 2
    final_status = finalize(run_dir, status, evidence, native)
    final_usage = resource.getrusage(resource.RUSAGE_SELF)
    aggregate_cpu = (final_usage.ru_utime + final_usage.ru_stime
                     + (child_usage.ru_utime + child_usage.ru_stime if child_usage is not None else 0))
    wall = time.monotonic() - started
    aggregate_peak_rss_bound = (final_usage.ru_maxrss
                               + (child_usage.ru_maxrss if child_usage is not None else 0))
    accounting_compliant = (aggregate_cpu <= 2.0 and wall <= WALL_HARD_S
                            and aggregate_peak_rss_bound <= RSS_LIMIT_BYTES)
    if not accounting_compliant:
        final_status = "FAILED_FINAL_RESOURCE_ACCOUNTING"
    write_json(run_dir / "accounting-after-finalization.json", {
        "status": "TERMINAL_ACCOUNTING_RECORDED",
        "final_status": final_status,
        "budgets_compliant": accounting_compliant,
        "supervisor_self": usage_payload(final_usage),
        "worker_wait4": usage_payload(child_usage) if child_usage is not None else None,
        "aggregate_cpu_s": aggregate_cpu,
        "wall_s": wall,
        "aggregate_sum_of_peak_rss_bytes_conservative": aggregate_peak_rss_bound,
        "excludes": "Only writing this small terminal accounting file and interpreter exit.",
        "kernel_granularity_and_sampling_limits_apply": True})
    signal.setitimer(signal.ITIMER_REAL, 0)
    print(canonical_json({"status": final_status, "run_dir": str(run_dir)}))
    return 0 if final_status == "COMPLETE_BOUNDED_PROBE" else 2


def main():
    if not EXECUTION_ENABLED:
        raise SystemExit("NOTRUN: EXECUTION_ENABLED=False; independent pre-review and root freeze required")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--freeze", required=True, type=Path)
    parser.add_argument("--owned-worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--run-dir", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--expected-parent", type=int, help=argparse.SUPPRESS)
    parser.add_argument("--authorization-fd", type=int, help=argparse.SUPPRESS)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if args.owned_worker:
        # This is a single-use internal continuation, not a second run API.
        expected_run = root / "runs" / RUN_LABEL
        if (args.run_dir is None or args.run_dir.resolve() != expected_run.resolve()
                or args.expected_parent != os.getppid() or os.getpgid(0) != os.getpid()
                or args.authorization_fd is None
                or not (root / "runs" / "attempt.lock").is_file()
                or not (expected_run / "initial-status.json").is_file()
                or os.getpriority(os.PRIO_PROCESS, 0) < NICE
                or resource.getrlimit(resource.RLIMIT_CPU) != (1, 1)
                or signal.getitimer(signal.ITIMER_REAL)[0] <= 0):
            raise SystemExit("NOTRUN: invalid owned-worker handoff")
        handoff = os.read(args.authorization_fd, 64)
        os.close(args.authorization_fd)
        if handoff != b"ROUND10_OWNED_WORKER\n":
            raise SystemExit("NOTRUN: missing owned-worker handoff")
        verify_freeze(root, args.freeze)
        with (expected_run / "worker-claim.lock").open("x", encoding="ascii") as stream:
            stream.write(str(os.getpid()) + "\n")
        return worker(expected_run)
    if any(value is not None for value in (args.run_dir, args.expected_parent, args.authorization_fd)):
        raise SystemExit("NOTRUN: internal worker arguments forbidden at supervisor entry")
    return supervise(root, args.freeze)


if __name__ == "__main__":
    raise SystemExit(main())
