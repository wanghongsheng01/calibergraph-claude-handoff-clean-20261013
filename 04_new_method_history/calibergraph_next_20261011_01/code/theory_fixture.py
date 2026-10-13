#!/usr/bin/env python3
"""Frozen artificial fixture; no solver, network, subprocess, or adaptive search.

Parent must freeze protocol and source before running. This worker was authored
without executing it. The complete search universe is the 18 declared databases.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import os
from pathlib import Path
import resource
import sqlite3
import sys
import time


PROTOCOL_ID = "CG-THEORY-ONE-WITNESS-01"
CPU_CAP_SECONDS = 1.0
WALL_CAP_SECONDS = 1.0
START = time.monotonic()
INITIAL_USAGE = resource.getrusage(resource.RUSAGE_SELF)
SQL_EXISTS = "SELECT COUNT(*) FROM R WHERE EXISTS (SELECT 1 FROM W WHERE W.r=R.r)"
SQL_JOIN = "SELECT COUNT(*) FROM R JOIN W ON W.r=R.r"


def guard() -> None:
    usage = resource.getrusage(resource.RUSAGE_SELF)
    if usage.ru_utime + usage.ru_stime > CPU_CAP_SECONDS:
        raise RuntimeError("BUDGET_STOP: worker CPU exceeds one second")
    if time.monotonic() - START > WALL_CAP_SECONDS:
        raise RuntimeError("BUDGET_STOP: worker wall exceeds one second")


def require(condition: bool, label: str) -> None:
    if not condition:
        raise AssertionError(label)


def legal(roots: tuple[int, ...], witnesses: tuple[tuple[int, int], ...]) -> bool:
    return (
        len(roots) <= 2
        and len(witnesses) <= 2
        and len(set(roots)) == len(roots)
        and len({w for w, _ in witnesses}) == len(witnesses)
        and all(r in (0, 1) for r in roots)
        and all(w in (0, 1) and r in roots for w, r in witnesses)
    )


def python_counts(roots: tuple[int, ...], witnesses: tuple[tuple[int, int], ...]) -> list[int]:
    exists_count = sum(any(target == r for _, target in witnesses) for r in roots)
    join_count = sum(1 for r in roots for _, target in witnesses if target == r)
    return [exists_count, join_count]


def checked_counts(connection: sqlite3.Connection, roots: tuple[int, ...],
                   witnesses: tuple[tuple[int, int], ...]) -> list[int]:
    guard()
    require(legal(roots, witnesses), "illegal supposedly legal input")
    counts = python_counts(roots, witnesses)
    connection.execute("DELETE FROM W")
    connection.execute("DELETE FROM R")
    connection.executemany("INSERT INTO R(r) VALUES (?)", [(r,) for r in roots])
    connection.executemany("INSERT INTO W(w,r) VALUES (?,?)", witnesses)
    sql_counts = [connection.execute(query).fetchone()[0] for query in (SQL_EXISTS, SQL_JOIN)]
    require(counts == sql_counts, "Python/SQLite count disagreement")
    return counts


def databases():
    for root_mask in range(4):
        roots = tuple(r for r in (0, 1) if root_mask & (1 << r))
        for targets in itertools.product((None,) + roots, repeat=2):
            witnesses = tuple((w, target) for w, target in enumerate(targets) if target is not None)
            yield roots, witnesses


def prune_one_witness(witnesses: tuple[tuple[int, int], ...]) -> tuple[tuple[int, int], ...]:
    retained = {}
    for w, r in sorted(witnesses):
        if r not in retained:
            retained[r] = (w, r)
    return tuple(sorted(retained.values()))


def usage_receipt() -> dict:
    usage = resource.getrusage(resource.RUSAGE_SELF)
    fields = (
        "ru_utime", "ru_stime", "ru_maxrss", "ru_ixrss", "ru_idrss", "ru_isrss",
        "ru_minflt", "ru_majflt", "ru_nswap", "ru_inblock", "ru_oublock",
        "ru_msgsnd", "ru_msgrcv", "ru_nsignals", "ru_nvcsw", "ru_nivcsw",
    )
    return {
        "scope": "RUSAGE_SELF; includes imports and SQLite, excludes parent guard",
        "raw": {field: getattr(usage, field) for field in fields},
        "platform": sys.platform,
        "maxrss_unit": "bytes" if sys.platform == "darwin" else "KiB_on_Linux_other_platform_unspecified",
        "cpu_total_seconds": usage.ru_utime + usage.ru_stime,
        "cpu_since_worker_start_seconds": (
            usage.ru_utime + usage.ru_stime - INITIAL_USAGE.ru_utime - INITIAL_USAGE.ru_stime
        ),
        "wall_since_worker_start_seconds": time.monotonic() - START,
        "measurement_point": "Immediately before serializing results.json; output-write overhead excluded",
    }


def main() -> int:
    output_value = os.environ.get("CALIBERGRAPH_RUN_OUT")
    if not output_value:
        raise SystemExit("CALIBERGRAPH_RUN_OUT must name the parent's fresh run directory")
    output_directory = Path(output_value)
    output_directory.mkdir(parents=True, exist_ok=True)
    output_path = output_directory / "results.json"
    require(not output_path.exists(), "refuse to overwrite an existing run")
    report = {
        "protocol_id": PROTOCOL_ID,
        "evidence_type": "ARTIFICIAL_MECHANISM_FIXTURE",
        "status": "STARTED",
        "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "records": [],
        "clone_records": [],
        "interpretation_limits": [
            "All 18 databases cover only the fixed tiny domains.",
            "This can reject one-witness seed cloning, not all small-counterexample bounds.",
            "Neither tiny-domain agreement nor clone agreement establishes unbounded equivalence.",
            "Artificial fixture; no natural-data or performance-generalization claim.",
        ],
    }
    exit_code = 0
    connection = None
    try:
        guard()
        connection = sqlite3.connect(":memory:")
        connection.execute("PRAGMA foreign_keys=ON")
        require(connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1, "foreign keys not enabled")
        connection.execute("CREATE TABLE R(r INTEGER PRIMARY KEY NOT NULL)")
        connection.execute("CREATE TABLE W(w INTEGER PRIMARY KEY NOT NULL, r INTEGER NOT NULL REFERENCES R(r))")
        seen = set()
        original_separators = 0
        pruned_separators = 0
        erased_separators = 0
        for index, (roots, witnesses) in enumerate(databases()):
            require(index < 18, "enumeration exceeded frozen 18-instance cap")
            identity = (roots, witnesses)
            require(identity not in seen, "duplicate enumerated database")
            seen.add(identity)
            original = checked_counts(connection, roots, witnesses)
            pruned_witnesses = prune_one_witness(witnesses)
            pruned = checked_counts(connection, roots, pruned_witnesses)
            separated = original[0] != original[1]
            still_separated = pruned[0] != pruned[1]
            require(original[0] == pruned[0], "pruning changed EXISTS count")
            expected_separation = len(witnesses) == 2 and witnesses[0][1] == witnesses[1][1]
            require(separated == expected_separation, "unexpected separator characterization")
            require(not still_separated, "unexpected pruned separator")
            original_separators += int(separated)
            pruned_separators += int(still_separated)
            erased_separators += int(separated and not still_separated)
            report["records"].append({
                "id": index, "R": roots, "W": witnesses,
                "original_counts": original, "pruned_W": pruned_witnesses,
                "pruned_counts": pruned, "original_separates": separated,
                "difference_erased": separated and not still_separated,
                "legal_original_and_pruned": True, "python_sqlite_parity": True,
            })
        require(len(seen) == 18, "expected exactly 18 legal databases")
        require(original_separators == 4, "expected exactly four original separators")
        require(pruned_separators == 0, "expected zero pruned separators")
        require(erased_separators == 4, "expected four erased differences")
        for n in (1, 2):
            roots = tuple(range(n))
            witnesses = tuple((i, i) for i in range(n))
            counts = checked_counts(connection, roots, witnesses)
            require(counts == [n, n], "unexpected synchronous clone counts")
            report["clone_records"].append({"n": n, "R": roots, "W": witnesses, "counts": counts,
                                             "legal": True, "python_sqlite_parity": True})
        fixed_counts = checked_counts(connection, (0,), ((0, 0), (1, 0)))
        require(fixed_counts == [1, 2], "fixed branching fixture must separate")
        naive_legal = legal((0, 1), ((0, 0), (0, 1)))
        require(not naive_legal, "fixed witness-key clone must violate W primary key")
        report["fixed_fixtures"] = {
            "branching_witness_counts": fixed_counts,
            "invalid_fixed_witness_key_clone": {"R": [0, 1], "W": [[0, 0], [0, 1]],
                                                "legal": naive_legal, "violation": "W primary key"},
        }
        report["summary"] = {"legal_instances": len(seen), "original_separators": original_separators,
                             "pruned_separators": pruned_separators, "erased_separators": erased_separators,
                             "clone_instances": len(report["clone_records"]), "all_registered_checks_passed": True}
        guard()
        report["status"] = "FALSIFIER_OBSERVED"
        report["mechanism_decision"] = "REJECT_ONE_WITNESS_SEED_CLONING"
    except Exception as error:
        exit_code = 1
        report["status"] = "BUDGET_STOP" if str(error).startswith("BUDGET_STOP") else "HARNESS_FAILED"
        report["error"] = {"type": type(error).__name__, "message": str(error)}
        report["mechanism_decision"] = "NO_VALID_EXPERIMENTAL_CONCLUSION"
    finally:
        if connection is not None:
            connection.close()
    report["resource_usage"] = usage_receipt()
    with output_path.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(json.dumps({"protocol_id": PROTOCOL_ID, "status": report["status"],
                      "results": str(output_path)}, ensure_ascii=False))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
