"""One registered N and two constructed mechanism fixtures; no import-time work.

Run only through the external supervisor with native Python 3.12 -B -I -S,
nice >= 15, and an external 256 MiB RSS limit. This worker does not infer
natural benchmark labels, establish business provenance, or expose new data.
"""

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import resource
import sys
import time


def _validate_fixture(case, rows, exact_rows, class_value):
    """Independently check every original C clause before touching the DB."""
    source = case["source_record"]
    expected_schema = {"COURSES": {"CLASS": "VARCHAR", "STUDENT": "VARCHAR"}}
    expected_constraint = [{"primary": [{"value": "COURSES__STUDENT"}]}]
    if source.get("schema") != expected_schema:
        raise ValueError("INDEPENDENT_CHECK_REJECTS_NONEXACT_SCHEMA")
    if (list(source["schema"]) != ["COURSES"]
            or list(source["schema"]["COURSES"]) != ["CLASS", "STUDENT"]):
        raise ValueError("INDEPENDENT_CHECK_REJECTS_CHANGED_COLUMN_ORDER")
    if source.get("constraint") != expected_constraint:
        raise ValueError("INDEPENDENT_CHECK_REJECTS_EXTRA_OR_UNKNOWN_C_CLAUSE")
    if type(exact_rows) is not int or exact_rows not in range(1, 6):
        raise ValueError("EXACT_N_OUTSIDE_REGISTERED_1_TO_5")
    if not isinstance(rows, list) or len(rows) != exact_rows:
        raise ValueError("FIXTURE_ROW_COUNT_MISMATCH")
    if class_value is not None and type(class_value) is not str:
        raise ValueError("FIXTURE_CLASS_MUST_BE_NULL_OR_STRING")
    students = []
    for row in rows:
        if type(row) is not tuple or len(row) != 2:
            raise ValueError("FIXTURE_ROW_SHAPE_MISMATCH")
        if row[0] is not None and type(row[0]) is not str:
            raise ValueError("CLASS_VARCHAR_OR_NULL_REQUIRED")
        if row[0] != class_value:
            raise ValueError("CLASS_NOT_UNIFORMLY_REQUESTED_VALUE")
        if type(row[1]) is not str:
            raise ValueError("PRIMARY_STUDENT_MUST_BE_NONNULL_VARCHAR")
        students.append(row[1])
    if len(set(students)) != exact_rows:
        raise ValueError("PRIMARY_STUDENT_NOT_UNIQUE")
    return {
        "status": "ALL_ORIGINAL_C_CLAUSES_SATISFIED",
        "independent_python_check": True,
        "exact_rows": exact_rows,
        "row_shape_and_types_valid": True,
        "student_nonnull": True,
        "student_unique": True,
        "all_class_values": class_value,
        "original_constraint": source["constraint"],
        "original_clause_count": 1,
        "checked_clause_count": 1,
        "unknown_or_dropped_clauses": 0,
        "scope": "Complete explicit original C; business completeness unverified.",
    }


def _bag(rows):
    counts = Counter(tuple(row) for row in rows)
    keys = sorted(counts, key=lambda row: json.dumps(
        list(row), ensure_ascii=False, separators=(",", ":"), allow_nan=False))
    return [{"row": list(row), "multiplicity": counts[row]} for row in keys]


def _execute_original_pair(connection, pair, expected_hashes, checkpoint):
    executions = []
    for query_index, query in enumerate(pair):
        # No stripping, substitution, rewriting, or regenerated SQL is allowed.
        query_hash = hashlib.sha256(query.encode("utf-8")).hexdigest()
        if query_hash != expected_hashes[query_index]:
            raise ValueError("SQL_BYTES_CHANGED_IMMEDIATELY_BEFORE_EXECUTE")
        checkpoint("ORIGINAL_QUERY_EXECUTE", query_index=query_index,
                   original_sql_sha256=query_hash)
        cursor = connection.execute(query)
        rows = cursor.fetchall()
        executions.append({
            "query_index_0based": query_index,
            "original_sql": query,
            "original_sql_utf8_sha256": query_hash,
            "execution_api": "sqlite3.Connection.execute(original_registry_string)",
            "columns": [column[0] for column in cursor.description or []],
            "rows": [list(row) for row in rows],
            "row_count": len(rows),
            "bag": _bag(rows),
        })
        checkpoint("ORIGINAL_QUERY_COMPLETE", query_index=query_index,
                   execution=executions[-1])
    return {"queries": executions,
            "observed_bag_equal": executions[0]["bag"] == executions[1]["bag"]}


def main():
    process_start = time.monotonic()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", required=True)
    parser.add_argument("--case-index", type=int, required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    # -I excludes the script directory. Add only this new worker directory.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from pilot_common import (atomic_json, cpu, install_guards, load_registered,
                              objsha, sha, validate_contract)

    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    if any((out / name).exists() for name in ("results.json", "progress.json", "events.jsonl")):
        raise ValueError("REFUSE_TO_OVERWRITE_EXISTING_WORKER_EVIDENCE")
    record = {
        "kind": "concrete",
        "case_index": args.case_index,
        "status": "STARTED",
        "outcome": "NOT_RUN",
        "active_stage": "INSTALL_GUARDS",
        "mechanism_fixture_only": True,
        "is_natural_label": False,
        "is_new_hidden_test": False,
        "fixtures": {},
        "resource_limits": {
            "worker_cpu_seconds": 3,
            "worker_wall_seconds": 4,
            "required_nice_minimum": 15,
            "external_rss_limit_bytes": 268435456,
            "external_rss_enforcement": "REQUIRED_PARENT_SUPERVISOR",
        },
        "scope": "Constructed mechanism fixtures on already exposed dev03_18; "
                 "SQLite observations only, not natural pair labels or a new test set.",
    }
    connection = None
    with (out / "events.jsonl").open("x", encoding="utf-8") as events:
        def checkpoint(stage, **details):
            previous_stage = record.get('active_stage')
            record["active_stage"] = stage
            record["worker_cpu_seconds"] = cpu()
            record["worker_wall_seconds"] = time.monotonic() - process_start
            event = {"event": stage, "monotonic": time.monotonic(),
                     "worker_cpu_seconds": record["worker_cpu_seconds"],
                     "case_index": args.case_index, "details": details}
            events.write(json.dumps(event, ensure_ascii=False, allow_nan=False) + "\n")
            events.flush()
            os.fsync(events.fileno())
            atomic_json(out / "results.json", record)
            atomic_json(out / "progress.json", {
                "id": record.get("id"), "case_index": args.case_index,
                "kind": "concrete", "status": record["status"],
                "active_stage": stage, "latest_stage": previous_stage,
                "solver_check_active": False, "solver_check_start_monotonic": None,
                "solver_spent_wall_seconds": 0.0, "check_count": 0,
                "updated_monotonic": time.monotonic(),
                "worker_cpu_seconds": record["worker_cpu_seconds"],
            })

        try:
            install_guards(events, record, process_start)
            checkpoint("FROZEN_SOURCE_ADMISSION")
            protocol, case, slot = load_registered(args.protocol, args.case_index, "concrete")
            if (slot["source_case_id"] != "dev03_18"
                    or slot["fixture"] != "all_null_class_and_nonnull_control"):
                raise ValueError("WRONG_CONCRETE_FIXTURE")
            n = slot["exact_rows"]
            source = case["source_record"]
            pair = source["pair"]
            contract = validate_contract(case)
            record.update({
                "id": slot["id"], "source_case_id": case["id"], "exact_rows": n,
                "registered_slot": slot,
                "protocol_id": protocol["id"], "protocol_sha256": sha(args.protocol),
                "worker_sha256": sha(__file__),
                "common_sha256": sha(Path(__file__).with_name('pilot_common.py')),
                "registered_task_count": len(protocol['registered_cases']),
                "denominator_unchanged": True,
                "source": case["source"], "source_group_id": case["source_group_id"],
                "provenance_eligibility": case["provenance_eligibility"],
                "original_source_record": source,
                "original_source_record_sha256": objsha(source),
                "original_sql_sha256": case["original_sql_sha256"],
                "schema_sha256": case["schema_sha256"],
                "constraint_sha256": case["constraint_sha256"],
                "full_original_contract_admission": contract,
                "runtime": {"executable": sys.executable, "python": sys.version,
                            "platform": sys.platform, "nice": os.getpriority(os.PRIO_PROCESS, 0)},
            })
            checkpoint("SQLITE_IMPORT")
            import sqlite3
            record["runtime"]["sqlite_version"] = sqlite3.sqlite_version

            null_rows = [(None, "student_" + str(i).zfill(2)) for i in range(1, n + 1)]
            control_value = "same_nonnull_class"
            control_rows = [(control_value, student) for _, student in null_rows]
            null_check = _validate_fixture(case, null_rows, n, None)
            control_check = _validate_fixture(case, control_rows, n, control_value)
            record["full_C_before_insert"] = null_check
            record["full_C_control_before_update"] = control_check
            record["fixtures"]["all_null_class"] = {"input_rows": [list(row) for row in null_rows]}
            record["fixtures"]["nonnull_class_control"] = {"input_rows": [list(row) for row in control_rows]}
            checkpoint("FIXTURE_AND_ALL_ORIGINAL_C_VALIDATED_BEFORE_INSERT")

            connection = sqlite3.connect(":memory:")
            connection.execute("CREATE TABLE COURSES (CLASS VARCHAR, STUDENT VARCHAR)")
            connection.executemany("INSERT INTO COURSES (CLASS, STUDENT) VALUES (?, ?)", null_rows)
            stored = connection.execute("SELECT CLASS, STUDENT FROM COURSES ORDER BY STUDENT").fetchall()
            if stored != null_rows:
                raise ValueError("DATABASE_ROWS_DIFFER_FROM_VALIDATED_NULL_FIXTURE")
            record["full_C_after_insert"] = _validate_fixture(case, stored, n, None)
            record["current_fixture"] = "all_null_class"
            checkpoint("NULL_FIXTURE_STORED")
            record["fixtures"]["all_null_class"].update(_execute_original_pair(
                connection, pair, case["original_sql_sha256"], checkpoint))
            checkpoint("NULL_FIXTURE_COMPLETE")

            # The same N rows and STUDENT values remain in the same in-memory DB.
            connection.execute("UPDATE COURSES SET CLASS = ?", (control_value,))
            stored_control = connection.execute(
                "SELECT CLASS, STUDENT FROM COURSES ORDER BY STUDENT").fetchall()
            if stored_control != control_rows:
                raise ValueError("CONTROL_CHANGED_N_OR_STUDENT_OR_CLASS_VALUE")
            record["full_C_after_update"] = _validate_fixture(case, stored_control, n, control_value)
            record["control_same_N_and_same_STUDENT"] = True
            record["current_fixture"] = "nonnull_class_control"
            checkpoint("NONNULL_CONTROL_STORED_AND_ALL_ORIGINAL_C_VALIDATED")
            record["fixtures"]["nonnull_class_control"].update(_execute_original_pair(
                connection, pair, case["original_sql_sha256"], checkpoint))
            connection.close()
            connection = None
            record["status"] = "COMPLETED"
            record["outcome"] = "CONCRETE_MECHANISM_FIXTURES_OBSERVED"
            usage = resource.getrusage(resource.RUSAGE_SELF)
            record['worker_usage'] = {'cpu_user_seconds': usage.ru_utime,
                'cpu_system_seconds': usage.ru_stime, 'peak_rss_bytes_macos': usage.ru_maxrss,
                'wall_from_main_seconds': time.monotonic() - process_start}
            record["observation"] = {
                "all_null_class_bag_equal": record["fixtures"]["all_null_class"]["observed_bag_equal"],
                "nonnull_class_control_bag_equal": record["fixtures"]["nonnull_class_control"]["observed_bag_equal"],
                "exhaustive_for_all_databases_at_N": False,
                "supports_unbounded_equivalence_claim": False,
                "supports_natural_benchmark_label": False,
            }
            checkpoint("COMPLETED")
            return 0
        except Exception as error:
            record["status"] = "FAILED"
            record["outcome"] = "INCONCLUSIVE_OR_NOT_RUN"
            record["error"] = {"type": type(error).__name__, "message": str(error)}
            checkpoint("FAILED")
            return 1
        finally:
            if connection is not None:
                connection.close()


if __name__ == "__main__":
    raise SystemExit(main())
