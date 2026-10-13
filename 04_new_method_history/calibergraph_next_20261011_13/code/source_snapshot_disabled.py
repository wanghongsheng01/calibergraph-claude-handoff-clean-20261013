"""One-shot, synthetic H12 negative-control SQLite replay. DO NOT IMPORT."""
import time

ENTRY_MONOTONIC = time.monotonic()
EXECUTION_ENABLED = False

if __name__ != "__main__":
    raise RuntimeError("Scientific runner may not be imported")
if not EXECUTION_ENABLED:
    raise SystemExit("NOTRUN: execution remains disabled pending root freeze and independent review")

import os
import signal


def wall_expired(_signum, _frame):
    # No cleanup after the deadline; missing final receipt means NOTCOMPLETED.
    os._exit(124)


signal.signal(signal.SIGALRM, wall_expired)
signal.setitimer(signal.ITIMER_REAL, max(0.000001, 3.0 - (time.monotonic() - ENTRY_MONOTONIC)))
import resource

resource.setrlimit(resource.RLIMIT_CPU, (2, 2))
import sys

if sys.platform != "darwin":
    raise SystemExit("NOTCOMPLETED: only reviewed Darwin RSS units are supported")
if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss > 128 * 1024 * 1024:
    raise SystemExit("NOTCOMPLETED: entry RSS exceeded 128 MiB")
priority = os.getpriority(os.PRIO_PROCESS, 0)
if priority < 15:
    os.nice(15 - priority)
if os.getpriority(os.PRIO_PROCESS, 0) < 15:
    raise SystemExit("NOTCOMPLETED: nice 15 could not be established")

import hashlib
import json
import sqlite3

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROUND12_FREEZE_SHA256 = "dfa81be07edf21839bf83bdaeb9cb1ac065d03d909fc086fbbbaa890155aa33e"
ROUND12_FREEZE_PATH = "/Users/loctek/Documents/Codex/2026-10-11/task-3/calibergraph_next_20261011_12/theory/AUTHOR_MANIFEST.json"
ROUND12_EVIDENCE_PINS = (
    ("SHA256SUMS.outputs", "feb0be27bcd1b8c36efa0045d7a003e9fb4c1507db880e5d479e880fa1e0df4a"),
    ("theory.md", "ea2e8ca63305e05113513fea5cb35f9e8b2772c18ebf7c34bd32310be9b2baca"),
    ("result.json", "d3c21a605667c06c6a319b4eca5ac1741356cd5425ca5186c4aa76dabc195279"),
)
RUN_DIRECTORY = os.path.join(ROOT, "run_once")
LOCK_PATH = os.path.join(ROOT, "EXECUTION_ONCE.lock")
V = (0, 1, 2, 3, 4, 5)
M = (0, 1, 3)
N = (0, 1, 4)
CARTESIAN_SIZES = (2, 2, 1, 2, 1, 1)
# Independently written literal rows are generation-legality evidence only.
CARTESIAN_LITERAL_ROWS = (
    ("v0#0", "v1#0"), ("v0#0", "v1#1"), ("v0#1", "v1#0"), ("v0#1", "v1#1"),
    ("v1#0", "v2#0"), ("v1#1", "v2#0"), ("v2#0", "v3#0"), ("v2#0", "v3#1"),
    ("v3#0", "v4#0"), ("v3#1", "v4#0"), ("v4#0", "v5#0"),
    ("v5#0", "v0#0"), ("v5#0", "v0#1"),
)
CREATE_SQL = "CREATE TABLE R(a TEXT COLLATE BINARY NOT NULL, b TEXT COLLATE BINARY NOT NULL, PRIMARY KEY(a,b)) WITHOUT ROWID"
INSERT_SQL = "INSERT INTO R(a,b) VALUES (?,?)"
SQL_M = """SELECT COUNT(*) FROM (
SELECT DISTINCT r0.a, r1.a, r3.a
FROM R AS r0
INNER JOIN R AS r1 ON r0.b = r1.a
INNER JOIN R AS r2 ON r1.b = r2.a
INNER JOIN R AS r3 ON r2.b = r3.a
INNER JOIN R AS r4 ON r3.b = r4.a
INNER JOIN R AS r5 ON r4.b = r5.a
WHERE r5.b = r0.a
)"""
SQL_N = """SELECT COUNT(*) FROM (
SELECT DISTINCT r0.a, r1.a, r4.a
FROM R AS r0
INNER JOIN R AS r1 ON r0.b = r1.a
INNER JOIN R AS r2 ON r1.b = r2.a
INNER JOIN R AS r3 ON r2.b = r3.a
INNER JOIN R AS r4 ON r3.b = r4.a
INNER JOIN R AS r5 ON r4.b = r5.a
WHERE r5.b = r0.a
)"""
LIMITS = (
    ("SQLITE_LIMIT_LENGTH", 65536), ("SQLITE_LIMIT_SQL_LENGTH", 4096),
    ("SQLITE_LIMIT_COLUMN", 16), ("SQLITE_LIMIT_EXPR_DEPTH", 32),
    ("SQLITE_LIMIT_COMPOUND_SELECT", 4), ("SQLITE_LIMIT_VDBE_OP", 10000),
    ("SQLITE_LIMIT_FUNCTION_ARG", 8), ("SQLITE_LIMIT_ATTACHED", 0),
    ("SQLITE_LIMIT_LIKE_PATTERN_LENGTH", 64), ("SQLITE_LIMIT_VARIABLE_NUMBER", 2),
    ("SQLITE_LIMIT_TRIGGER_DEPTH", 0), ("SQLITE_LIMIT_WORKER_THREADS", 0),
)
state = {"status": "NOTCOMPLETED", "phase": "startup", "denominator_constructed": False,
         "planned_db_instances": 98, "planned_fixed_synthetic_count_sql": 196,
         "attempted_fixed_synthetic_count_sql": 0, "completed_fixed_synthetic_count_sql": 0,
         "attempted_setup_sql": 0, "completed_setup_sql": 0,
         "attempted_budget_verification_sql": 0, "completed_budget_verification_sql": 0,
         "attempted_insert_rows": 0, "completed_insert_rows": 0,
         "entries": [], "phase_costs": [], "failure": None,
         "external_datasets": 0, "synthetic_only": True, "hypotheses": 1}
progress_failure = None


def checkpoint(phase):
    state["phase"] = phase
    usage = resource.getrusage(resource.RUSAGE_SELF)
    if time.monotonic() - ENTRY_MONOTONIC >= 3.0:
        os._exit(124)
    if usage.ru_utime + usage.ru_stime >= 1.95:
        raise RuntimeError("CPU sampled guard reached 1.95 s; hard RLIMIT_CPU remains 2 s")
    if usage.ru_maxrss > 128 * 1024 * 1024:
        raise RuntimeError("Darwin sampled peak RSS exceeds 128 MiB")
    return {"wall_from_entry_s": time.monotonic() - ENTRY_MONOTONIC,
            "cpu_self_total_s": usage.ru_utime + usage.ru_stime,
            "peak_rss_bytes": usage.ru_maxrss}


def start_phase(name):
    return name, checkpoint(name)


def end_phase(mark):
    name, before = mark
    after = checkpoint(name)
    state["phase_costs"].append({"phase": name,
        "wall_s": after["wall_from_entry_s"] - before["wall_from_entry_s"],
        "cpu_s": after["cpu_self_total_s"] - before["cpu_self_total_s"],
        "process_peak_rss_bytes": after["peak_rss_bytes"]})


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_bounded(path, limit):
    checkpoint("read_frozen_inputs")
    with open(path, "rb") as handle:
        data = handle.read(limit + 1)
    if len(data) > limit:
        raise RuntimeError("Input file exceeds fixed byte budget")
    return data


def write_exclusive(name, value):
    checkpoint("serialize_" + name)
    payload = canonical(value) + b"\n"
    if len(payload) > 512 * 1024:
        raise RuntimeError("Receipt exceeds 512 KiB structural budget")
    with open(os.path.join(RUN_DIRECTORY, name), "xb") as handle:
        handle.write(payload)
        handle.flush()
    checkpoint("serialized_" + name)
    return digest(payload)


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def validate_authorization():
    require(len(sys.argv) == 1, "No arbitrary inputs or SQL arguments accepted")
    freeze_bytes = read_bounded(os.path.join(ROOT, "protocols", "execution_freeze.json"), 32768)
    freeze = json.loads(freeze_bytes)
    require(freeze["execution_enabled"] is True, "Root freeze does not enable execution")
    require(freeze["independent_review"]["approved"] is True, "Independent review pending")
    require(freeze["independent_review"]["reviewer_id"] != freeze["author_id"], "Author/reviewer separation missing")
    require(freeze["round12_proof_confirmed"] is True, "Round 12 proof confirmation pending")
    require(len(ROUND12_FREEZE_SHA256) == 64, "Round 12 pin unresolved")
    require(freeze["round12_freeze_sha256"] == ROUND12_FREEZE_SHA256, "Round 12 pin differs")
    require(digest(read_bounded(ROUND12_FREEZE_PATH, 131072)) == ROUND12_FREEZE_SHA256, "Round 12 freeze changed")
    for filename, expected_hash in ROUND12_EVIDENCE_PINS:
        require(digest(read_bounded(os.path.join(os.path.dirname(ROUND12_FREEZE_PATH), filename), 131072)) == expected_hash, "Round 12 evidence changed: " + filename)
    require(digest(read_bounded(__file__, 65536)) == freeze["executable_source_sha256"], "Executable source differs")
    snapshot = read_bounded(os.path.join(ROOT, "code", "source_snapshot_disabled.py"), 65536)
    require(b"EXECUTION_ENABLED = False\n" in snapshot, "Disabled source snapshot missing")
    require(digest(snapshot) == freeze["source_snapshot_disabled_sha256"], "Disabled snapshot differs")
    review_bytes = read_bounded(os.path.join(ROOT, "protocols", "independent_review.json"), 32768)
    require(digest(review_bytes) == freeze["independent_review"]["review_report_sha256"], "Independent review report differs")
    review = json.loads(review_bytes)
    require(review["approved"] is True and review["critical_findings_open"] == 0, "Independent review did not pass")
    require(review["reviewer_id"] == freeze["independent_review"]["reviewer_id"], "Independent reviewer identity differs")
    require(review["author_id"] == freeze["author_id"], "Reviewed author identity differs")
    require(review["reviewed_source_snapshot_disabled_sha256"] == digest(snapshot), "Review is not bound to this source")
    require(freeze["independent_review"]["reviewed_source_snapshot_disabled_sha256"] == digest(snapshot), "Freeze review source differs")
    require(review["round12_freeze_sha256"] == ROUND12_FREEZE_SHA256, "Review Round 12 pin differs")
    preflight_bytes = read_bounded(os.path.join(ROOT, "protocols", "machine_preflight.json"), 8192)
    require(digest(preflight_bytes) == freeze["machine_preflight_sha256"], "Machine preflight hash differs")
    preflight = json.loads(preflight_bytes)
    age = time.time() - preflight["measured_unix_s"]
    require(0 <= age <= 60, "Machine preflight is future-dated or older than 60 s")
    require(preflight["platform"] == "darwin", "Preflight platform differs")
    require(preflight["load_1m"] <= 4.0 and preflight["memory_free_percent"] >= 25.0, "Machine preflight gate failed")
    require(preflight["passed"] is True, "Preflight explicitly failed")
    require(preflight["memory_measurement_source"] == "macOS memory_pressure -Q", "Memory measurement source not reviewed")
    require(os.getloadavg()[0] <= 4.0, "Live 1-minute load exceeds 4.0")
    state["provenance"] = {"freeze_sha256": digest(freeze_bytes),
        "round12_freeze_sha256": ROUND12_FREEZE_SHA256,
        "round12_evidence_pins": ROUND12_EVIDENCE_PINS,
        "source_snapshot_disabled_sha256": freeze["source_snapshot_disabled_sha256"],
        "executable_source_sha256": freeze["executable_source_sha256"],
        "machine_preflight_sha256": digest(preflight_bytes), "preflight_age_s": age,
        "sqlite_version": sqlite3.sqlite_version, "python_version": sys.version,
        "nice": os.getpriority(os.PRIO_PROCESS, 0)}


def validate_rows(rows):
    require(1 <= len(rows) <= 13, "Database row budget violated")
    require(len(rows) == len(set(rows)), "Full-tuple PK uniqueness violated")
    require(all(len(row) == 2 and all(type(x) is str and len(x) == 4 and x[0] == "v" and x[1] in "012345" and x[2] == "#" and x[3] in "01" for x in row) for row in rows), "NOT NULL/opaque-text budget violated")
    require(all((int(a[1]) + 1) % 6 == int(b[1]) for a, b in rows), "Rows do not follow the fixed directed cycle")


def label(variable, tag):
    return "v%d#%d" % (variable, tag)


def components(c):
    remaining = set(V) - set(c)
    answer = []
    while remaining:
        pending = [min(remaining)]
        component = set()
        while pending:
            v = pending.pop()
            if v not in remaining:
                continue
            remaining.remove(v)
            component.add(v)
            pending.extend(w for w in ((v - 1) % 6, (v + 1) % 6) if w in remaining)
        answer.append(tuple(sorted(component)))
    return answer


def make_entry(identifier, c, s, rows, expected, kind):
    rows = tuple(sorted(rows))
    validate_rows(rows)
    cheap = "C=M" if c == M else ("C=N" if c == N else None)
    return {"id": identifier, "kind": kind, "C": c, "S": s,
            "cheap_subfamily": cheap, "DBrows": rows, "DBrows_sha256": digest(canonical(rows)),
            "Nrows": len(rows), "expected_M": expected[0], "expected_N": expected[1],
            "count_M": None, "count_N": None, "expectedmatch": None,
            "status": "NOTRUN", "failed_phase": None, "cost": None}


def construct_fixed_inputs():
    entries = []
    for mask in range(64):
        checkpoint("fixed_input_construction")
        c = tuple(v for v in V if mask & (1 << v))
        for s in components(c):
            # Two complete body assignments share one tag throughout S.
            rows = set()
            for tag in (0, 1):
                assignment = tuple(label(v, tag if v in s else 0) for v in V)
                rows.update((assignment[v], assignment[(v + 1) % 6]) for v in V)
            count = 9 if len(s) == 1 else (11 if len(s) == 2 else 12)
            entries.append(make_entry("family_%03d" % len(entries), c, s, rows, (count, count), "literal_family"))
    require(len(entries) == 97, "Literal family denominator differs from frozen 97")
    require(len({tuple(e["S"]) for e in entries}) == 31, "Distinct-S cost annotation differs from 31")
    require(sum(e["cheap_subfamily"] is not None for e in entries) == 4, "Cheap family mark count differs from 4")
    length_counts = tuple(sum(len(e["S"]) == length for e in entries) for length in range(1, 7))
    require(length_counts == (48, 24, 12, 6, 6, 1), "Frozen component-length denominators differ")
    state["family_length_denominators_1_to_6"] = length_counts
    rows = {(label(v, a), label((v + 1) % 6, b)) for v in V
            for a in range(CARTESIAN_SIZES[v]) for b in range(CARTESIAN_SIZES[(v + 1) % 6])}
    validate_rows(CARTESIAN_LITERAL_ROWS)
    require(len(CARTESIAN_LITERAL_ROWS) == 13 and rows == set(CARTESIAN_LITERAL_ROWS), "Independent 13-row construction-legality check failed")
    entries.append(make_entry("cartesian_control", None, None, rows, (20, 19), "strong_cartesian_control"))
    state["entries"] = entries
    state["generation_legality"] = {"literal_13_rows_unique_notnull": True,
        "cartesian_generator_matches_literal_rows": True, "scientific_second_evaluator": False}
    # This write is charged and precedes every database/SQL evaluation.
    state["initial_ledger_sha256"] = write_exclusive("inputs_and_98_NOTRUN.json", entries)
    state["denominator_constructed"] = True


def sqlite_progress():
    global progress_failure
    try:
        checkpoint("sqlite_progress")
        return 0
    except Exception as error:
        progress_failure = str(error)
        return 1


def replay_entry(entry):
    global progress_failure
    before = checkpoint("entry_start")
    entry["status"] = "RUNNING"
    connection = None
    try:
        connection = sqlite3.connect(":memory:", timeout=0, cached_statements=0, isolation_level=None)
        connection.set_progress_handler(sqlite_progress, 1000)
        require(hasattr(connection, "setlimit") and hasattr(connection, "getlimit"), "SQLite limit interfaces unavailable")
        for name, limit in LIMITS:
            checkpoint("sqlite_limits")
            category = getattr(sqlite3, name)
            connection.setlimit(category, limit)
            require(connection.getlimit(category) == limit, "SQLite limit could not be established: " + name)
        for setter, getter, expected in (
            ("PRAGMA page_size=4096", "PRAGMA page_size", 4096),
            ("PRAGMA max_page_count=32", "PRAGMA max_page_count", 32),
            ("PRAGMA cache_size=-64", "PRAGMA cache_size", -64),
            ("PRAGMA temp_store=MEMORY", "PRAGMA temp_store", 2),
            ("PRAGMA temp.cache_size=-64", "PRAGMA temp.cache_size", -64),
            ("PRAGMA threads=0", "PRAGMA threads", 0),
        ):
            checkpoint("sqlite_budget_setup")
            state["attempted_setup_sql"] += 1
            connection.execute(setter).fetchall()
            state["completed_setup_sql"] += 1
            checkpoint("sqlite_budget_verification")
            state["attempted_budget_verification_sql"] += 1
            actual = connection.execute(getter).fetchone()
            state["completed_budget_verification_sql"] += 1
            require(actual == (expected,), "SQLite PRAGMA budget could not be verified: " + getter)
        checkpoint("sqlite_create")
        state["attempted_setup_sql"] += 1
        connection.execute(CREATE_SQL)
        state["completed_setup_sql"] += 1
        for row in entry["DBrows"]:
            checkpoint("sqlite_insert")
            state["attempted_insert_rows"] += 1
            connection.execute(INSERT_SQL, row)
            state["completed_insert_rows"] += 1
        for name, sql in (("M", SQL_M), ("N", SQL_N)):
            checkpoint("fixed_synthetic_count_sql_" + name)
            state["attempted_fixed_synthetic_count_sql"] += 1
            result = connection.execute(sql).fetchone()
            state["completed_fixed_synthetic_count_sql"] += 1
            checkpoint("fixed_synthetic_count_sql_completed_" + name)
            require(result is not None and len(result) == 1 and type(result[0]) is int, "Unexpected scalar result")
            entry["count_" + name] = result[0]
            if result[0] != entry["expected_" + name]:
                entry["expectedmatch"] = False
                raise RuntimeError("Frozen expected count mismatch: " + name)
        entry["expectedmatch"] = True
        entry["status"] = "COMPLETED"
    except Exception:
        entry["status"] = "FAILED"
        entry["failed_phase"] = state["phase"]
        raise
    finally:
        if connection is not None:
            connection.close()
        after = checkpoint("entry_closed")
        entry["cost"] = {"wall_s": after["wall_from_entry_s"] - before["wall_from_entry_s"],
                         "cpu_s": after["cpu_self_total_s"] - before["cpu_self_total_s"],
                         "process_peak_rss_bytes": after["peak_rss_bytes"]}


def main():
    output_created = False
    try:
        mark = start_phase("authorization_and_preflight")
        # An enabled attempt consumes its lock even when preflight fails.
        descriptor = os.open(LOCK_PATH, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.write(descriptor, b"ONE_ATTEMPT_ONLY\n")
        os.close(descriptor)
        os.mkdir(RUN_DIRECTORY, 0o700)
        output_created = True
        validate_authorization()
        end_phase(mark)
        mark = start_phase("fixed_input_and_NOTRUN_serialization")
        construct_fixed_inputs()
        end_phase(mark)
        mark = start_phase("all_database_and_fixed_synthetic_SQL_replay")
        for entry in state["entries"]:
            replay_entry(entry)
        end_phase(mark)
        require(state["completed_fixed_synthetic_count_sql"] == 196, "SQL denominator incomplete")
        state["status"] = "COMPLETED"
    except Exception as error:
        state["status"] = "NOTCOMPLETED"
        state["failure"] = {"type": type(error).__name__, "message": str(error),
                            "phase": state["phase"], "sqlite_progress_failure": progress_failure}
    if not output_created:
        raise SystemExit("NOTCOMPLETED: no output directory; no successful denominator claimed")
    state["denominator"] = {"planned_entries": 98, "planned_fixed_synthetic_count_sql": 196,
        "completed_entries": sum(e["status"] == "COMPLETED" for e in state["entries"]),
        "failed_entries": sum(e["status"] == "FAILED" for e in state["entries"]),
        "notrun_entries": sum(e["status"] == "NOTRUN" for e in state["entries"]),
        "enumerated_entries": len(state["entries"])}
    state["cost_before_final_receipt"] = checkpoint("before_final_receipt")
    receipt_hash = write_exclusive("result_receipt.json", state)
    # Captures result serialization; its own final bytes and interpreter shutdown
    # remain in external /usr/bin/time -l whole-launch evidence.
    write_exclusive("completion.json", {"status": state["status"], "result_receipt_sha256": receipt_hash,
        "cost_after_result_receipt": checkpoint("after_result_receipt"),
        "whole_launch_cost_requires_external_time_receipt": True})
    raise SystemExit(0 if state["status"] == "COMPLETED" else 1)


main()
