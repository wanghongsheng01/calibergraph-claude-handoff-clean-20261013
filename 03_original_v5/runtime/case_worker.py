"""Finite existing-DEV Environment/SQL diagnostic. No downloads or source edits."""
import time
START = time.monotonic()
import signal
import resource
signal.signal(signal.SIGALRM, signal.SIG_DFL)
signal.setitimer(signal.ITIMER_REAL, max(0.001, 24 - (time.monotonic() - START)))
resource.setrlimit(resource.RLIMIT_CPU, (14, 15))
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
signal.pthread_sigmask(signal.SIG_UNBLOCK, {signal.SIGALRM, signal.SIGXCPU})

import argparse
import builtins
from collections import Counter
import ctypes
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import sys
import threading
import traceback

ARMS = ("official", "flat", "product", "selector")


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(262144), b""):
            h.update(chunk)
    return h.hexdigest()


def save(path, value):
    tmp = path.with_suffix(".tmp")
    with tmp.open("w") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    tmp.replace(path)


def verify(lock_path, expected):
    if sha(lock_path) != expected:
        raise ValueError("runtime lock changed")
    lock = json.loads(lock_path.read_text())
    if lock.get("schema_version") != 1 or lock.get("status") != "STATIC_REVIEWED_READY_FOR_LOCAL_RUN":
        raise ValueError("runtime lock is not reviewed/ready")
    if lock["expected_native_version"] != [4, 12, 0, 0] or not lock["files"]:
        raise ValueError("wrong native version or empty file lock")
    for raw, expected_sha in lock["files"].items():
        path = Path(raw)
        if not path.is_absolute() or path != path.resolve() or not path.is_file() or sha(path) != expected_sha:
            raise ValueError("runtime file missing/changed/symlinked: " + raw)
    for root in [lock["source_root"], lock["binding_root"], lock["support_root"], *lock["dependency_roots"]]:
        root = Path(root)
        actual = {str(p) for p in root.rglob("*") if p.is_file()}
        expected = {p for p in lock["files"] if Path(p).is_relative_to(root)}
        if actual != expected or any(p.is_symlink() for p in root.rglob("*")):
            raise ValueError("runtime inventory mismatch: " + str(root))
    if lock["native_path"] not in lock["files"] or lock["kernel_path"] not in lock["files"]:
        raise ValueError("native/kernel omitted from lock")
    return lock


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-lock", type=Path, required=True)
    parser.add_argument("--expected-lock-sha256", required=True)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--expected-fixture-sha256", required=True)
    parser.add_argument("--case-index", type=int, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    if not (sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode):
        raise ValueError("require -B -I -S")
    fixture = json.loads(args.fixture.read_text())
    case = fixture["cases"][args.case_index]
    out = args.out_dir / "worker_report.json"
    report = {"status": "NOT_RUN", "id": case["id"], "expected": case["expected"],
              "pid": os.getpid(), "case_index": args.case_index,
              "data_role": "EXISTING_EXPOSED_ANALYTICAL_DEV_NOT_NEW_TEST", "performance_claim": False,
              "runtime_lock_sha256": args.expected_lock_sha256, "fixture_sha256": args.expected_fixture_sha256,
              "input": {"schema": fixture["schema"], "exact_rows": fixture["exact_rows"],
                        "constraint": case["constraint"], "pair": case["pair"]},
              "gates": {}, "arms": {a: {"status": "NOT_RUN"} for a in ARMS},
              "point_checks": {a: {"status": "NOT_RUN"} for a in ARMS[1:]},
              "solver_threads": 1, "native_load": "NOT_RUN", "environment_import": "NOT_RUN"}
    save(out, report)

    def checkpoint(phase):
        usage = resource.getrusage(resource.RUSAGE_SELF)
        report["phase"] = phase
        report["resource_last_checkpoint"] = {
            "elapsed_wall_seconds": time.monotonic() - START,
            "cpu_seconds": usage.ru_utime + usage.ru_stime, "peak_rss_bytes_darwin": usage.ru_maxrss,
            "python_threads": [{"name": t.name, "daemon": t.daemon} for t in threading.enumerate()]}
        save(out, report)
        print(json.dumps({"phase": phase, "case_id": case["id"]}), flush=True)

    def operation(target, name, fn):
        target["status"] = "ATTEMPTED_EFFECT_UNKNOWN"
        checkpoint(name + "_ATTEMPT")
        tick = time.monotonic()
        try:
            target.update(fn())
        except Exception as exc:
            target.update(status="ERROR", error_type=type(exc).__name__, reason=str(exc),
                          traceback=traceback.format_exc())
        target["resource_wall_seconds"] = time.monotonic() - tick
        checkpoint(name + "_RETURNED")

    try:
        if sha(args.fixture) != args.expected_fixture_sha256:
            raise ValueError("fixture changed")
        lock = verify(args.runtime_lock, args.expected_lock_sha256)
        report["gates"]["input_hash_lock"] = "PASS"
        report["native_load"] = "ATTEMPTED_EFFECT_UNKNOWN"
        checkpoint("NATIVE_LOAD")
        native = Path(lock["native_path"])
        library = ctypes.CDLL(str(native))
        report["native_load"] = "LOADED"
        builtins.Z3_LIB_DIRS = [str(native.parent)]
        sys.path[:0] = [lock["binding_root"], lock["support_root"], *lock["dependency_roots"], lock["source_root"]]
        report["environment_import"] = "ATTEMPTED_EFFECT_UNKNOWN"
        checkpoint("BINDING_AND_ENVIRONMENT_IMPORT")
        import z3
        from z3 import z3core
        defaults = z3core.Z3_get_version.__defaults__
        if len(defaults) != 1:
            raise ValueError("unexpected generated version wrapper defaults")
        bound_pointer = ctypes.cast(defaults[0].f, ctypes.c_void_p).value
        pinned_pointer = ctypes.cast(library.Z3_get_version, ctypes.c_void_p).value
        if not bound_pointer or bound_pointer != pinned_pointer:
            raise ValueError("binding/native function pointer identity mismatch")
        if list(z3.get_version()) != lock["expected_native_version"]:
            raise ValueError("native version differs")
        if not Path(z3.__file__).resolve().is_relative_to(Path(lock["binding_root"])):
            raise ValueError("binding imported outside locked tree")
        report["native_identity"] = {"pinned_path": str(native), "sha256": sha(native),
                                     "version": list(z3.get_version()), "symbol": "Z3_get_version",
                                     "binding_pointer": bound_pointer, "pinned_pointer": pinned_pointer,
                                     "method": "same_process_function_identity_plus_pinned_source"}
        from environment import Environment
        from constants import DIALECT, Z3_CONTEXT, Or, BoolVal, IntVal
        if not Path(sys.modules["environment"].__file__).resolve().is_relative_to(Path(lock["source_root"])):
            raise ValueError("wrong Environment source")
        spec = importlib.util.spec_from_file_location("caliber_diagnostic_kernel", lock["kernel_path"])
        kernel = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = kernel
        spec.loader.exec_module(kernel)
        report["environment_import"] = "IMPORTED"
        report["loaded_module_paths"] = {name: getattr(module, "__file__", None) for name, module in list(sys.modules.items())
                                        if name.split(".")[0] in {"environment", "constants", "mo_sql_parsing", "mo_parsing", "mo_dots", "mo_imports", "mo_future", "ordered_set", "lark", "ujson", "yaml", "pkg_resources", "z3"}}
        z3.set_param("parallel.enable", False)
        z3.set_param("memory_max_size", 768)
        checkpoint("ENVIRONMENT_IMPORT_COMPLETE")

        def solve(facts, goal=None, milliseconds=1000):
            solver = z3.Solver(ctx=Z3_CONTEXT)
            solver.set(timeout=milliseconds, threads=1)
            solver.add(*facts)
            if goal is not None:
                solver.add(goal)
            return solver, str(solver.check())

        def decode(env, model):
            database = {}
            for name, table in env.base_databases.items():
                rows = []
                for row in table:
                    if z3.is_true(model.eval(env.DELETED_FUNCTION(row.SORT), model_completion=True)):
                        raise ValueError("exact-row witness contains deleted base row")
                    rows.append([None if z3.is_true(model.eval(attr.NULL(row.SORT), model_completion=True)) else
                                 model.eval(attr.VALUE(row.SORT), model_completion=True).as_long() for attr in table.attributes])
                database[name] = rows
            return database

        def replay(database):
            with sqlite3.connect(":memory:") as conn:
                for name, fields in fixture["schema"].items():
                    conn.execute('CREATE TABLE "' + name + '" (' + ','.join('"' + col + '" INTEGER' for col in fields) + ')')
                    conn.executemany('INSERT INTO "' + name + '" VALUES (' + ','.join('?' for _ in fields) + ')', database[name])
                relations = [conn.execute(sql).fetchall() for sql in case["pair"]]
            return {"relations": relations, "unequal_as_bags": Counter(relations[0]) != Counter(relations[1]),
                    "sqlite_version": sqlite3.sqlite_version, "scope": "fixed scalar INT32 constructed DEV"}

        with Environment(timer=True, generate_code=False, show_counterexample=False, dialect=DIALECT.MYSQL) as env:
            for name, fields in fixture["schema"].items():
                env.create_database(attributes=fields, bound_size=fixture["exact_rows"][name], name=name)
            env.add_constraints(case["constraint"])
            env.save_checkpoints()
            env.solver.set(timeout=5000, threads=1)
            facts = list(env.DBMS_facts)
            facts_text = [x.sexpr() for x in facts]
            def fingerprint():
                return [[name, [[row.SORT.sexpr(), [[a.name, a.NULL(row.SORT).sexpr(), a.VALUE(row.SORT).sexpr()]
                                                  for a in table.attributes]] for row in table]] for name, table in env.base_databases.items()]
            before = fingerprint()
            report["base_fact_count"] = len(facts)
            report["base_facts_sha256"] = hashlib.sha256("\n".join(facts_text).encode()).hexdigest()
            checkpoint("CONTRACT_GUARD_ATTEMPT")
            _, consistent = solve(facts)
            _, exact = solve(facts, Or(*(env.DELETED_FUNCTION(row.SORT) for table in env.base_databases.values() for row in table)))
            report["gates"]["contract"] = {"consistency": consistent, "any_base_row_deleted": exact}
            if consistent != "sat" or exact != "unsat":
                raise ValueError("full contract satisfiability/exact-row guard not established")

            def official():
                try:
                    answer = env.analyze(*case["pair"])
                except Exception as exc:
                    if type(exc).__name__ == "UnknownError":
                        return {"status": "unknown", "reason": env.solver.reason_unknown()}
                    if type(exc).__name__ in {"NotSupportedError", "NotImplementedError", "ParserSyntaxError"}:
                        return {"status": "unsupported", "reason": str(exc)}
                    raise
                if type(answer) is not bool:
                    raise ValueError("nonboolean official analyze result: " + repr(answer))
                result = {"status": "unsat" if answer else "sat"}
                if not answer:
                    result["witness"] = decode(env, env.solver.model())
                    result["sqlite"] = replay(result["witness"])
                    if not result["sqlite"]["unequal_as_bags"]:
                        result["status"] = "COUNTEREXAMPLE_REPLAY_MISMATCH"
                return result
            operation(report["arms"]["official"], "OFFICIAL_ANALYZE", official)
            if [x.sexpr() for x in env.DBMS_facts] != facts_text or fingerprint() != before:
                raise ValueError("official analysis changed shared base contract/mapping")
            checkpoint("CANDIDATE_RECOGNITION_ATTEMPT")
            try:
                plans = [kernel.recognize(env.parse_sql_query(sql), fixture["schema"]) for sql in case["pair"]]
            except kernel.Ineligible as exc:
                for mode in ARMS[1:]:
                    report["arms"][mode] = {"status": "INELIGIBLE", "reason": str(exc),
                                            "fallback": "full official result above; same schema/IC/queries"}
                plans = None
            emissions = {}
            if plans is not None:
                for mode in ARMS[1:]:
                    def candidate(mode=mode):
                        emitted = [kernel.encode(plan, env, mode, f"{case['id']}_{mode}_{i}") for i, plan in enumerate(plans)]
                        emissions[mode] = emitted
                        definitions = emitted[0][2] + emitted[1][2]
                        solver, status = solve(facts + definitions, kernel.unequal(*emitted), milliseconds=2000)
                        result = {"status": status, "counts": [item[3] for item in emitted]}
                        if status == "unknown":
                            result["reason"] = solver.reason_unknown()
                        elif status == "sat":
                            model = solver.model()
                            if not all(z3.is_true(model.eval(f, model_completion=True)) for f in facts + definitions):
                                raise ValueError("candidate model violates original facts or definitions")
                            result["witness"] = decode(env, model)
                            result["sqlite"] = replay(result["witness"])
                            if not result["sqlite"]["unequal_as_bags"]:
                                result["status"] = "COUNTEREXAMPLE_REPLAY_MISMATCH"
                        return result
                    operation(report["arms"][mode], mode.upper(), candidate)
                database = case["point_database"]
                expected_relations = [[tuple(row) for row in relation] for relation in case["point_expected_relations"]]
                point_replay = replay(database)
                report["point_sqlite"] = point_replay
                if point_replay["relations"] != expected_relations:
                    raise ValueError("frozen analytical point disagrees with SQLite")
                concrete = []
                for name, table in env.base_databases.items():
                    if len(database[name]) != fixture["exact_rows"][name]:
                        raise ValueError("point row count differs from full bound")
                    for row, values in zip(table, database[name]):
                        if len(values) != len(table.attributes):
                            raise ValueError("point omitted schema columns")
                        for attr, value in zip(table.attributes, values):
                            concrete.append(attr.NULL(row.SORT) == BoolVal(value is None))
                            if value is not None:
                                concrete.append(attr.VALUE(row.SORT) == IntVal(str(value)))
                for mode, emitted in emissions.items():
                    def point(mode=mode, emitted=emitted):
                        solver, status = solve(facts + concrete + emitted[0][2] + emitted[1][2])
                        if status != "sat":
                            return {"status": status, "reason": "point satisfiability not established"}
                        model = solver.model()
                        relations = [[(None if z3.is_true(model.eval(e[0], model_completion=True)) else
                                       model.eval(e[1], model_completion=True).as_long(),)] for e in emitted]
                        return {"status": "POINT_VALUES_MATCH" if relations == expected_relations else "POINT_VALUE_MISMATCH",
                                "relations": relations, "expected_relations": expected_relations}
                    operation(report["point_checks"][mode], mode.upper() + "_POINT", point)
        report["expectation_matches"] = {mode: result["status"] == case["expected"] for mode, result in report["arms"].items()}
        report["status"] = "COMPLETE_DEV_AGREEMENT" if all(report["expectation_matches"].values()) and all(
            p["status"] == "POINT_VALUES_MATCH" for p in report["point_checks"].values()) else "COMPLETE_WITH_FAILURES_OR_DIFFERENCES"
        checkpoint("FINAL")
        sys.stdout.flush(); sys.stderr.flush()
        os._exit(0 if report["status"] == "COMPLETE_DEV_AGREEMENT" else 2)
    except BaseException as exc:
        report.update(status="BLOCKED_OR_ERROR", error_type=type(exc).__name__, reason=str(exc), traceback=traceback.format_exc())
        checkpoint("ERROR")
        sys.stdout.flush(); sys.stderr.flush()
        os._exit(2)


if __name__ == "__main__":
    main()
