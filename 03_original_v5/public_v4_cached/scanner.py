"""Reuse frozen official ALL ASTs; never parse SQL or construct/call a solver.

Run only through supervisor.py. Outputs describe v4 syntactic applicability,
not parser independence, equivalence, IC admissibility, or a cost experiment.
"""
import argparse
import collections
import dataclasses
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import resource
import signal
import sys
import time

HERE = Path(__file__).resolve().parent
TODAY = HERE.parent
KERNEL = TODAY / "runtime_v4/aggregate_kernel.py"
KERNEL_SHA = "17f652323839f0395e3224e5d82f646c143f34ff8245fb4d798724d3d7b9fa78"
OLD_KERNEL_SHA = "defa1812ec36c91a23d428f8d71d2070f808eddeb5f473748d3e7ac09fdfe5f3"
MANIFEST = TODAY / "public_leetcode/GLOBAL_MANIFEST.json"
MANIFEST_SHA = "041d6c0bf43dad8270c099f10bcbcf61cfc4ee5a96f13170ff141e35c5ce45a0"
INPUTS = (
    ("calcite", TODAY / "sources/verieql_v1/benchmarks/calcite/calcite2.jsonlines", 397,
     "5fc6e0740134220856e93743147038cacaf22cb9d9823e7d6b8da2b461939ac4"),
    ("literature", TODAY / "sources/verieql_v1/benchmarks/literature/literature-rewrite.jsonlines", 64,
     "4c5e2661797177fd865a3f57c887376cb01bcbeec57ec77a032124e04c77f42f"),
    ("leetcode", TODAY / "public_leetcode/leetcode.jsonlines", 23994,
     "b97fc1293701682a25a2f6345f3630b3482ce49912463a7f4b76ab52665a13c9"),
)
PAIR_DENOMINATOR = 24455
SLOT_DENOMINATOR = 48910
OLD_KNOWN = {"ELIGIBLE", "INELIGIBLE", "FRONTEND_UNSUPPORTED", "PARSE_OR_AST_RECORD_ERROR",
             "RECOGNIZER_ERROR", "INPUT_ERROR"}
OLD_NOT_RUN = {"NOT_RUN", "NOT_ATTEMPTED"}
OLD_UNKNOWN = {"UNKNOWN", "ATTEMPTED_EFFECT_UNKNOWN", "STARTED"}
START = None


class BudgetStop(Exception):
    pass


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def object_sha(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def sql_sha(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest() if isinstance(value, str) else None


def save(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)


def emit(stream, value):
    stream.write(json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + "\n")


def budget():
    if time.monotonic() - START >= 50:
        raise BudgetStop("50-second cooperative scan budget; remaining slots stay NOT_RUN")


def regular(path):
    if not path.is_file() or any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError("missing/nonregular/symlinked input: " + str(path))


def no_targets(event, args):
    # Defence in depth. The pinned kernel imports z3 only inside encode(), which
    # this program never calls. Ban third-party imports and process/network APIs.
    if event == "import" and args[0].split(".")[0] not in sys.stdlib_module_names:
        raise RuntimeError("nonstdlib import prohibited: " + args[0])
    if event in {"subprocess.Popen", "os.system", "os.fork", "os.forkpty", "os.posix_spawn",
                 "os.exec", "socket.__new__", "socket.connect", "socket.getaddrinfo", "ctypes.dlopen"}:
        raise RuntimeError("target/process/network API prohibited: " + event)


def load_kernel():
    regular(KERNEL)
    if sha(KERNEL) != KERNEL_SHA:
        raise ValueError("v4 kernel identity mismatch")
    spec = importlib.util.spec_from_file_location("cached_ast_v4_kernel", KERNEL)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def source_problem(dataset, record):
    # These are explicit source labels, not inferred independent tasks/people.
    if dataset == "leetcode" and isinstance(record.get("file"), str):
        return [dataset, "file", record["file"]]
    if dataset == "literature" and isinstance(record.get("name"), str):
        return [dataset, "name", record["name"]]
    if dataset == "calcite" and "index" in record and "benchmark" in record:
        return [dataset, "benchmark_index", record["benchmark"], record["index"]]
    return None


def source_rows():
    ordinal = 0
    for dataset, path, expected, _ in INPUTS:
        count = 0
        with path.open("rb") as stream:
            for line, raw in enumerate(stream, 1):
                count += 1
                record = json.loads(raw)
                if not isinstance(record, dict) or not isinstance(record.get("pair"), list) or len(record["pair"]) != 2:
                    raise ValueError("frozen source pair shape changed: " + dataset + ":" + str(line))
                # Missing constraints are never replaced by an inferred empty set.
                yield {"id": dataset + ":" + str(line), "dataset": dataset,
                       "pair_ordinal": ordinal, "line_number_1based": line,
                       "source_file": str(path), "source_line_sha256": hashlib.sha256(raw).hexdigest(),
                       "source_record": record, "source_problem_key": source_problem(dataset, record)}
                ordinal += 1
        if count != expected:
            raise ValueError("source row denominator mismatch: " + dataset)
    if ordinal != PAIR_DENOMINATOR:
        raise ValueError("combined pair denominator mismatch")


def source_blocks():
    block, key = [], None
    for row in source_rows():
        new_key = "dev" if row["dataset"] != "leetcode" else (row["line_number_1based"] - 1) // 1000
        if key is not None and key != new_key:
            yield key, block
            block = []
        key = new_key
        block.append(row)
    if block:
        yield key, block


class Counts:
    def __init__(self):
        self.status = collections.Counter()
        self.reason = collections.Counter()
        self.original_status = collections.Counter()
        self.leaves = collections.Counter()
        self.dataset = {d: collections.Counter() for d, _, _, _ in INPUTS}
        self.all_sql, self.all_context_sql, self.all_problem = set(), set(), set()
        self.all_pair_sql, self.all_full_case = set(), set()
        self.eligible_sql, self.eligible_context_sql, self.eligible_problem = set(), set(), set()
        self.eligible_pair_sql, self.eligible_full_case = set(), set()
        self.initial_slots = 0
        self.processed_slots = 0
        self.processed_pairs = 0
        self.both_pairs = 0
        self.false_pairs = 0
        self.missing_problem_pairs = 0

    def initialize(self, row):
        record, dataset = row["source_record"], row["dataset"]
        schema_digest = object_sha(record.get("schema"))
        context_digest = object_sha({k: v for k, v in record.items() if k != "pair"})
        problem = object_sha(row["source_problem_key"]) if row["source_problem_key"] is not None else None
        if problem:
            self.all_problem.add(problem)
        else:
            self.missing_problem_pairs += 1
        self.all_pair_sql.add(object_sha(record["pair"]))
        self.all_full_case.add(object_sha(record))
        self.dataset[dataset]["pair_denominator"] += 1
        for index, sql in enumerate(record["pair"]):
            digest = sql_sha(sql)
            if digest is not None:
                self.all_sql.add(digest)
                self.all_context_sql.add(object_sha([digest, context_digest]))
            self.initial_slots += 1
            self.dataset[dataset]["query_slot_denominator"] += 1
            yield {"slot_ordinal": 2 * row["pair_ordinal"] + index,
                   "row_id": row["id"], "dataset": dataset, "query_index": index,
                   "original_sql": sql, "sql_sha256": digest,
                   "source_file": row["source_file"], "source_line_number_1based": row["line_number_1based"],
                   "source_line_sha256": row["source_line_sha256"], "schema_sha256": schema_digest,
                   "full_context_sha256": context_digest, "source_problem_key": row["source_problem_key"],
                   "status": "NOT_RUN", "reason": "V4_NOT_ATTEMPTED", "eligible": None,
                   "original_status": "NOT_OBSERVED", "original_reason": None,
                   "ast": None, "ast_sha256": None, "plan": None, "leaf_count": None,
                   "parser_called": False, "solver_called": False}

    def add_pair(self, row, results):
        record, dataset = row["source_record"], row["dataset"]
        context_digest = object_sha({k: v for k, v in record.items() if k != "pair"})
        for result in results:
            self.processed_slots += 1
            self.status[result["status"]] += 1
            self.reason[result["reason"]] += 1
            self.original_status[result["original_status"]] += 1
            self.dataset[dataset][result["status"]] += 1
            if result["eligible"] is True:
                digest = sql_sha(record["pair"][result["query_index"]])
                self.eligible_sql.add(digest)
                self.eligible_context_sql.add(object_sha([digest, context_digest]))
                if row["source_problem_key"] is not None:
                    self.eligible_problem.add(object_sha(row["source_problem_key"]))
                self.leaves[result["leaf_count"]] += 1
        self.processed_pairs += 1
        both = all(r["eligible"] is True for r in results)
        if both:
            self.both_pairs += 1
            self.dataset[dataset]["both_eligible_pairs"] += 1
            self.eligible_pair_sql.add(object_sha(record["pair"]))
            self.eligible_full_case.add(object_sha(record))
        elif any(r["eligible"] is False for r in results):
            self.false_pairs += 1

    def summary(self):
        statuses = self.status.copy()
        statuses["NOT_RUN"] += SLOT_DENOMINATOR - self.processed_slots
        return {"pair_denominator": PAIR_DENOMINATOR, "query_slot_denominator": SLOT_DENOMINATOR,
                "initial_slots_written": self.initial_slots, "result_slots_written": self.processed_slots,
                "v4_not_processed_slots": SLOT_DENOMINATOR - self.processed_slots,
                "query_status_counts": dict(statuses), "query_reason_counts_processed_slots": dict(self.reason),
                "original_status_counts_observed_slots": dict(self.original_status),
                "eligible_queries": self.status["ELIGIBLE"], "both_eligible_pairs": self.both_pairs,
                "pair_known_false": self.false_pairs,
                "pair_unknown_including_not_run": PAIR_DENOMINATOR - self.both_pairs - self.false_pairs,
                "eligible_leaf_count_histogram": {str(k): v for k, v in sorted(self.leaves.items())},
                "eligible_multitable_queries": sum(v for k, v in self.leaves.items() if k >= 1),
                "eligible_at_least_two_leaf_queries": sum(v for k, v in self.leaves.items() if k >= 2),
                "distinct": {"all_raw_sql": len(self.all_sql), "eligible_raw_sql": len(self.eligible_sql),
                    "all_sql_with_full_context": len(self.all_context_sql),
                    "eligible_sql_with_full_context": len(self.eligible_context_sql),
                    "all_source_problem_labels": len(self.all_problem),
                    "eligible_source_problem_labels": len(self.eligible_problem),
                    "source_problem_label_missing_pairs": self.missing_problem_pairs,
                    "all_ordered_sql_pairs": len(self.all_pair_sql), "both_eligible_ordered_sql_pairs": len(self.eligible_pair_sql),
                    "all_full_source_cases": len(self.all_full_case), "both_eligible_full_source_cases": len(self.eligible_full_case)},
                "by_dataset": {k: dict(v) for k, v in self.dataset.items()}}


def validate_cached(report, key, rows):
    if not isinstance(report, dict) or report.get("kernel_sha256") != OLD_KERNEL_SHA:
        raise ValueError("wrong original kernel identity")
    if report.get("dialect") != "ALL" or report.get("identifier_encoding") != "verieql_double_underscore":
        raise ValueError("not fixed official ALL/double-underscore AST provenance")
    if report.get("status", "").startswith("INVALIDATED"):
        raise ValueError("original report invalidated")
    for field in ("inputs_unchanged_after_scan", "kernel_unchanged_after_scan", "runtime_lock_unchanged_after_scan"):
        if report.get(field) is False:
            raise ValueError("original report failed identity check: " + field)
    if key == "dev":
        if (report.get("full_row_denominator"), report.get("full_query_slot_denominator")) != (461, 922):
            raise ValueError("dev denominator mismatch")
    else:
        if (report.get("full_row_denominator"), report.get("full_query_slot_denominator")) != (23994, 47988):
            raise ValueError("leetcode denominator mismatch")
        if report.get("source_sha256") != INPUTS[2][3] or report.get("global_manifest_sha256") != MANIFEST_SHA:
            raise ValueError("leetcode source/manifest identity mismatch")
        chunk = report.get("chunk", {})
        if (chunk.get("chunk_index"), chunk.get("start_line_1based"), chunk.get("end_line_1based"),
                chunk.get("row_count"), chunk.get("query_slots")) != (
                key, rows[0]["line_number_1based"], rows[-1]["line_number_1based"], len(rows), 2 * len(rows)):
            raise ValueError("cached report chunk mismatch")
    old_rows = report.get("rows")
    if not isinstance(old_rows, list) or len(old_rows) != len(rows):
        raise ValueError("cached row count mismatch")
    for old, source in zip(old_rows, rows):
        if not isinstance(old, dict) or any(old.get(k) != source[k] for k in
                ("id", "dataset", "line_number_1based", "source_line_sha256", "source_record")):
            raise ValueError("cached row identity/full source_record mismatch: " + source["id"])
        queries = old.get("queries")
        if not isinstance(queries, list) or len(queries) != 2:
            raise ValueError("cached query slots missing/duplicated: " + source["id"])
        for index, query in enumerate(queries):
            if not isinstance(query, dict) or query.get("query_index") != index or query.get("original_sql") != source["source_record"]["pair"][index]:
                raise ValueError("cached original SQL/slot index mismatch: " + source["id"])
            if query.get("ast") is not None and (report.get("environment_initialization") != "NORMAL_INITIALIZER_COMPLETE" or
                                                  query.get("parser_called") is not True):
                raise ValueError("non-null AST lacks official parser provenance: " + source["id"])
    return old_rows


def report_candidates(key):
    if key == "dev":
        path = TODAY / "public_dev/runs/full_scan_v3_all_01/scan_report.json"
        return [path] if path.exists() else []
    root = TODAY / "public_leetcode/runs" / ("chunk_%03d" % key)
    candidates = list(root.glob("attempt_*/scan_report.json"))
    def sequence(path):
        suffix = path.parent.name.removeprefix("attempt_")
        if not suffix.isdigit():
            raise ValueError("ambiguous nonnumeric attempt name: " + str(path))
        return int(suffix)
    return sorted(candidates, key=sequence, reverse=True)


def latest_report(key, rows):
    provenance = {"block": key, "selected": None, "selection_rule": "largest numeric attempt with valid complete block identity; partial states retained",
                  "examined_candidates": []}
    for path in report_candidates(key):
        budget()
        entry = {"path": str(path), "valid": False}
        provenance["examined_candidates"].append(entry)
        try:
            regular(path)
            raw = path.read_bytes()
            entry.update(sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))
            report = json.loads(raw)
            del raw
            old_rows = validate_cached(report, key, rows)
            entry.update(valid=True, original_report_status=report.get("status"))
            provenance["selected"] = dict(entry)
            provenance["original_provenance"] = {k: report.get(k) for k in (
                "data_role", "program_sha256", "runtime_lock_sha256", "kernel_sha256", "dialect",
                "identifier_encoding", "environment_initialization", "solving_performed", "native_identity")}
            return old_rows, provenance
        except BudgetStop:
            raise
        except Exception as exc:
            entry["reason"] = type(exc).__name__ + ": " + str(exc)
    return None, provenance


def plain_ast(node):
    if node is None or isinstance(node, (str, bool, int)):
        return True
    if isinstance(node, float):
        return math.isfinite(node)
    if isinstance(node, list):
        return all(plain_ast(x) for x in node)
    if isinstance(node, dict):
        return "__type__" not in node and all(isinstance(k, str) and plain_ast(v) for k, v in node.items())
    return False


def scan_slot(kernel, row, index, cached, report_path):
    result = {"slot_ordinal": 2 * row["pair_ordinal"] + index, "row_id": row["id"], "query_index": index,
              "original_status": cached.get("status") if cached else "NOT_RUN",
              "original_reason": cached.get("reason") if cached else "NO_VALID_CACHED_REPORT",
              "cached_report": report_path, "status": "UNKNOWN", "reason": "UNCLASSIFIED_CACHED_STATUS",
              "eligible": None, "ast": cached.get("ast") if cached else None, "ast_sha256": None,
              "plan": None, "leaf_count": None, "v4_raw_guard": "NOT_RUN", "recognizer_called": False,
              "parser_called": False, "solver_called": False}
    old = result["original_status"]
    if old in OLD_NOT_RUN:
        result.update(status="NOT_RUN", reason="ORIGINAL_NOT_RUN" if cached else "NO_VALID_CACHED_REPORT")
        return result
    if old in OLD_UNKNOWN or old not in OLD_KNOWN:
        result.update(status="UNKNOWN", reason="ORIGINAL_UNFINISHED_OR_UNKNOWN")
        return result
    record = row["source_record"]
    sql = record["pair"][index]
    guard_error = None
    try:
        kernel.ensure_raw_identifiers(record.get("schema"), sql)
        result["v4_raw_guard"] = "PASS"
    except kernel.FrontendUnsupported as exc:
        result["v4_raw_guard"] = "REFUSED"
        guard_error = str(exc)
        result["v4_raw_guard_reason"] = guard_error
    # Preserve failed/absent original parse evidence. No AST is regenerated.
    if old in {"PARSE_OR_AST_RECORD_ERROR", "INPUT_ERROR"}:
        result.update(status=old, reason="ORIGINAL_" + old + ": " + str(result["original_reason"]))
        return result
    if result["ast"] is None:
        if old == "FRONTEND_UNSUPPORTED":
            result.update(status="FRONTEND_UNSUPPORTED", eligible=False,
                          reason="ORIGINAL_FRONTEND_UNSUPPORTED_WITHOUT_AST: " + str(result["original_reason"]))
        else:
            result.update(status="UNKNOWN", reason="CACHED_AST_NULL")
        return result
    result["ast_sha256"] = object_sha(result["ast"])
    if guard_error is not None:
        result.update(status="FRONTEND_UNSUPPORTED", eligible=False, reason=guard_error)
        return result
    if "constraint" not in record:
        result.update(status="UNKNOWN", reason="ORIGINAL_CONSTRAINT_FIELD_MISSING")
        return result
    if not plain_ast(result["ast"]):
        result.update(status="UNKNOWN", reason="CACHED_AST_HAS_SERIALIZED_NON_JSON_NODE")
        return result
    try:
        result["recognizer_called"] = True
        plan = kernel.recognize(result["ast"], record["schema"],
                                identifier_encoding="verieql_double_underscore", original_sql=sql)
        if not dataclasses.is_dataclass(plan) or not isinstance(plan.leaves, list):
            raise TypeError("unexpected v4 Plan shape")
        result.update(status="ELIGIBLE", eligible=True, reason="V4_RECOGNIZED_CACHED_OFFICIAL_ALL_AST",
                      plan=dataclasses.asdict(plan), leaf_count=len(plan.leaves))
    except kernel.FrontendUnsupported as exc:
        result.update(status="FRONTEND_UNSUPPORTED", eligible=False, reason=str(exc))
    except kernel.Ineligible as exc:
        result.update(status="INELIGIBLE", eligible=False, reason=str(exc))
    except Exception as exc:
        result.update(status="RECOGNIZER_ERROR", reason=type(exc).__name__ + ": " + str(exc))
    return result


def merge_slots(out):
    # Results form a prefix in source order. Stream the full baseline ledger;
    # neither all AST reports nor all completed slots are held in memory.
    temporary = out / "slots.jsonl.tmp"
    count = 0
    with (out / "initial_slots.jsonl").open() as initial, (out / "slot_results.jsonl").open() as events, temporary.open("x") as target:
        next_result = events.readline()
        for line in initial:
            slot = json.loads(line)
            if next_result:
                result = json.loads(next_result)
                if result["slot_ordinal"] != slot["slot_ordinal"]:
                    raise ValueError("result prefix ordinal mismatch")
                slot.update(result)
                next_result = events.readline()
            emit(target, slot)
            count += 1
        if next_result or count != SLOT_DENOMINATOR:
            raise ValueError("merged slot denominator mismatch")
    temporary.replace(out / "slots.jsonl")


def main():
    global START
    START = time.monotonic()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--supervised", action="store_true", required=True)
    args = parser.parse_args()
    if sys.platform != "darwin" or not (sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode):
        raise ValueError("Darwin -B -I -S required")
    out = args.out_dir.resolve()
    if not out.is_dir() or out.parent != HERE / "runs" or any(p.is_symlink() for p in (args.out_dir, *args.out_dir.parents)):
        raise ValueError("supervisor-created nonsymlink output under public_v4_cached/runs required")
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_CPU, (52, 53))
    signal.signal(signal.SIGALRM, lambda signum, frame: os._exit(124))
    signal.setitimer(signal.ITIMER_REAL, 56)
    sys.addaudithook(no_targets)
    counts = Counts()
    report = {"status": "INITIALIZING", "data_role": "CACHED_OFFICIAL_ALL_AST_V4_RECOGNIZER_EXTENSION",
              "pair_denominator": PAIR_DENOMINATOR, "query_slot_denominator": SLOT_DENOMINATOR,
              "datasets": {d: {"pairs": n, "queries": 2*n} for d, _, n, _ in INPUTS},
              "kernel_sha256": KERNEL_SHA, "original_kernel_sha256": OLD_KERNEL_SHA,
              "dialect": "ALL", "identifier_encoding": "verieql_double_underscore",
              "parser_called": False, "solver_imported": False, "solver_called": False,
              "scientific_claims": {"independent_parser_validation": False, "independent_holdout": False,
                  "runtime_advantage": False, "equivalence_accuracy": False, "constraint_admissibility": False,
                  "new_human_gold": False, "novelty_established": False},
              "scope": "Reuses original stored official ALL AST; only v4 raw guard and recognizer run. All source schema/IC retained unchanged. No SQL reparse, AST reconstruction, IC assertion, fallback, encoding or solve.",
              "leaf_definition": "len(v4 Plan.leaves): joined non-root aliases; root excluded. Null for rejected/unknown/not-run; valid one-table plan has 0.",
              "distinct_definitions": {"raw_sql": "SHA256 of exact original UTF-8 SQL, without normalization",
                  "sql_with_full_context": "exact SQL SHA plus canonical JSON SHA of every original source_record field except pair",
                  "source_problem_labels": "LeetCode file; literature name; Calcite benchmark+index. Source labels are not independently validated semantic problems",
                  "ordered_sql_pairs": "canonical JSON of original ordered pair", "full_source_cases": "canonical JSON of complete original source_record"},
              "denominator_policy": "No sampling, eligibility prefilter or deduplication. Missing/invalid report, incomplete parse and missing AST remain in full denominator.",
              "ledger_policy": "initial_slots.jsonl is all slots before recognition; slot_attempts.jsonl durably records each slot before its evaluation, and slot_results.jsonl overrides the completed ordinal prefix. slots.jsonl merges complete results on normal/cooperative exit. On hard stop replay complete result lines; attempted slots without complete results are UNKNOWN, never NOT_RUN or a positive result. Untouched slots stay NOT_RUN.",
              "inputs": [], "cached_blocks": [], "program_sha256": sha(Path(__file__)),
              "limits": {"scan_soft_wall_seconds": 50, "worker_wall_seconds": 56,
                         "worker_cpu_soft_hard_seconds": [52, 53], "supervisor_wall_seconds": 60,
                         "combined_parent_child_rss_bytes": 1024**3}}
    save(out / "scan_report.json", report)
    exit_code = 2
    try:
        for dataset, path, expected, digest in INPUTS:
            budget()
            regular(path)
            actual = sha(path)
            report["inputs"].append({"kind": "original_source", "dataset": dataset, "path": str(path),
                                     "sha256": actual, "expected_sha256": digest, "pairs": expected})
            if actual != digest:
                raise ValueError("original source hash mismatch: " + dataset)
        regular(MANIFEST)
        actual = sha(MANIFEST)
        report["inputs"].append({"kind": "full_manifest", "path": str(MANIFEST), "sha256": actual,
                                 "expected_sha256": MANIFEST_SHA})
        if actual != MANIFEST_SHA:
            raise ValueError("global manifest identity mismatch")
        manifest = json.loads(MANIFEST.read_text())
        if (manifest["row_denominator"], manifest["query_slot_denominator"], len(manifest["chunks"])) != (23994, 47988, 24):
            raise ValueError("global manifest denominator mismatch")
        del manifest
        report["inputs"].append({"kind": "v4_kernel", "path": str(KERNEL), "sha256": sha(KERNEL), "expected_sha256": KERNEL_SHA})
        with (out / "initial_slots.jsonl.tmp").open("x") as initial:
            for row in source_rows():
                budget()
                for slot in counts.initialize(row):
                    emit(initial, slot)
        (out / "initial_slots.jsonl.tmp").replace(out / "initial_slots.jsonl")
        if counts.initial_slots != SLOT_DENOMINATOR:
            raise ValueError("initial full ledger mismatch")
        kernel = load_kernel()
        report.update(status="SCANNING_CACHED_BLOCKS", summary=counts.summary())
        save(out / "scan_report.json", report)
        with (out / "slot_attempts.jsonl").open("x", buffering=1) as attempts_file, \
             (out / "slot_results.jsonl").open("x", buffering=1) as results_file, \
             (out / "recognized_cases.jsonl").open("x", buffering=1) as cases_file, \
             (out / "both_eligible_pairs.jsonl").open("x", buffering=1) as pairs_file:
            try:
                for key, rows in source_blocks():
                    budget()
                    cached_rows, provenance = latest_report(key, rows)
                    report["cached_blocks"].append(provenance)
                    # Bind even a hard-stopped prefix to the exact cached bytes
                    # before any target call from this block can begin.
                    save(out / "scan_report.json", report)
                    selected_path = provenance["selected"]["path"] if provenance["selected"] else None
                    for position, row in enumerate(rows):
                        budget()
                        cached = cached_rows[position]["queries"] if cached_rows is not None else [None, None]
                        results = []
                        for i in range(2):
                            # The small line is flushed before entering even the
                            # raw guard, so a killed in-flight slot is UNKNOWN.
                            emit(attempts_file, {"slot_ordinal": 2 * row["pair_ordinal"] + i,
                                                "row_id": row["id"], "query_index": i,
                                                "status": "ATTEMPTED_EFFECT_UNKNOWN"})
                            result = scan_slot(kernel, row, i, cached[i], selected_path)
                            emit(results_file, result)
                            results.append(result)
                        counts.add_pair(row, results)
                        admitted = [r["query_index"] for r in results if r["eligible"] is True]
                        if admitted:
                            case = {**row, "eligible_query_indices": admitted, "pair_both_eligible": len(admitted) == 2,
                                    "queries": results, "constraints_checked": False,
                                    "meaning": "recognizer applicability only; complete original schema and IC retained in source_record"}
                            emit(cases_file, case)
                            if len(admitted) == 2:
                                emit(pairs_file, case)
                    report["summary"] = counts.summary()
                    save(out / "scan_report.json", report)
                    del cached_rows
                report["status"] = "COMPLETE_FULL_DENOMINATOR_CACHED_SCAN"
                exit_code = 0
            except BudgetStop as exc:
                report.update(status="STOPPED_RESOURCE_LIMIT_REMAINDER_NOT_RUN", reason=str(exc))
        merge_slots(out)
        # Only immutable source/kernel checks determine identity here. Cached
        # report snapshots may be atomically superseded by the original runner;
        # record both hashes, never silently substitute new contents mid-block.
        for entry in report["inputs"]:
            entry["unchanged_after_scan"] = sha(Path(entry["path"])) == entry["sha256"]
        for block in report["cached_blocks"]:
            if block["selected"]:
                item = block["selected"]
                item["current_sha256_at_end"] = sha(Path(item["path"]))
                item["unchanged_after_scan"] = item["current_sha256_at_end"] == item["sha256"]
        if not all(e["unchanged_after_scan"] for e in report["inputs"]) or any(
                b["selected"] and not b["selected"]["unchanged_after_scan"] for b in report["cached_blocks"]):
            report["status"] = "INVALIDATED_INPUT_CHANGED_DURING_SCAN"
            exit_code = 2
    except Exception as exc:
        report.update(status="FAILED_REMAINDER_NOT_RUN", reason=type(exc).__name__ + ": " + str(exc))
    report["summary"] = counts.summary()
    report["resource_checkpoint"] = {"wall_seconds": time.monotonic() - START,
        "user_seconds": resource.getrusage(resource.RUSAGE_SELF).ru_utime,
        "system_seconds": resource.getrusage(resource.RUSAGE_SELF).ru_stime,
        "max_rss_bytes_darwin": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "role": "operational budget only; not comparative performance"}
    report["output_hashes"] = {p.name: sha(p) for p in out.glob("*.jsonl")}
    save(out / "scan_report.json", report)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
