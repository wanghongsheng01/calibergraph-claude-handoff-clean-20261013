"""One selected contract-bridge diagnostic; root executor only, via supervise.py."""
import time
START = time.monotonic()
import resource
import signal
signal.signal(signal.SIGALRM, signal.SIG_DFL)
signal.signal(signal.SIGXCPU, signal.SIG_DFL)
signal.setitimer(signal.ITIMER_REAL, max(0.001, 24 - (time.monotonic() - START)))
resource.setrlimit(resource.RLIMIT_CPU, (14, 15))
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
signal.pthread_sigmask(signal.SIG_UNBLOCK, {signal.SIGALRM, signal.SIGXCPU})
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import threading
import traceback

HERE = Path(__file__).resolve().parent


class CompletedUnverified(Exception):
    """Control flow for a registered rejection, while retaining final cleanup."""


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, item):
    temporary = path.with_suffix(path.suffix + ".tmp")
    if temporary.is_symlink():
        raise ValueError("temporary path is symlinked")
    with temporary.open("w") as stream:
        json.dump(item, stream, ensure_ascii=False, indent=2)
        stream.write("\n"); stream.flush(); os.fsync(stream.fileno())
    temporary.replace(path)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def verify_manifest(expected):
    path = HERE / "MANIFEST.json"
    if path.is_symlink() or sha(path) != expected:
        raise ValueError("manifest hash mismatch")
    manifest = json.loads(path.read_text())
    for item in manifest["files"]:
        file = Path(item["path"])
        if file != file.resolve() or not file.is_file() or sha(file) != item["sha256"]:
            raise ValueError("locked file changed: " + str(file))
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-lock", type=Path, required=True)
    parser.add_argument("--runtime-lock-sha256", required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    if sys.platform != "darwin" or not (sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode):
        raise ValueError("Darwin and -B -I -S required")
    # Supervisor creates a new directory; child rejects every symlinked ancestor.
    out = args.out_dir.absolute()
    allowed = HERE / "runs"
    if allowed.is_symlink() or out != out.resolve() or not out.is_relative_to(allowed) or out == allowed:
        raise ValueError("result directory must be an unaliased new child under runs")
    for parent in [out, *out.parents]:
        if parent.is_symlink():
            raise ValueError("symlink in output ancestry")
        if parent == HERE:
            break
    if not out.is_dir() or any((out / n).exists() or (out / n).is_symlink() for n in ["report.json", "report.json.tmp"]):
        raise ValueError("supervisor-created directory required; report must not exist")
    output = out / "report.json"
    report = {"status": "NOT_RUN", "pid": os.getpid(), "case_id": args.case_id,
              "native_load": "NOT_RUN", "environment_import": "NOT_RUN", "checks": [],
              "source_parser": {"status": "NOT_RUN"}, "pair_check": {"status": "NOT_RUN"},
              "limits": {"cpu_soft_hard_seconds": [14, 15], "wall_alarm_seconds": 24,
                         "rss_soft_bytes": 1024 ** 3, "external_supervisor_required": True},
              "manifest_sha256": args.manifest_sha256, "runtime_lock_sha256": args.runtime_lock_sha256,
              "not_claimed": ["general certificate", "natural defect incidence", "novelty", "performance advantage"]}
    save(output, report)

    def checkpoint(phase):
        usage = resource.getrusage(resource.RUSAGE_SELF)
        report["phase"] = phase
        report["resource_last_checkpoint"] = {"wall_seconds": time.monotonic() - START,
            "cpu_seconds": usage.ru_utime + usage.ru_stime, "peak_rss_bytes_darwin": usage.ru_maxrss,
            "python_threads": [{"name": t.name, "daemon": t.daemon} for t in threading.enumerate()]}
        save(output, report)
        if usage.ru_maxrss >= 1024 ** 3:
            raise MemoryError("RSS soft limit at checkpoint")

    env = None
    exit_code = 2
    try:
        manifest = verify_manifest(args.manifest_sha256)
        suite = json.loads((HERE / "fixtures.json").read_text())
        registered = suite["cases"]
        if len({case["id"] for case in registered}) != len(registered):
            raise ValueError("duplicate case IDs")
        case = next(case for case in registered if case["id"] == args.case_id)
        report.update(input=case, data_role=suite["data_role"], full_case_denominator=len(registered),
                      cases=[{"id": item["id"], "status": "SELECTED" if item["id"] == args.case_id else "NOT_RUN"} for item in registered],
                      fixed_databases=[dict(item, status="NOT_RUN") for item in case["fixed_databases"]])
        planned_checks = ["base_only_sat", "base_exact_rows", "original_vs_reference", "normalized_vs_reference"]
        planned_checks += ["fixed_" + item["id"] for item in case["fixed_databases"]]
        planned_checks += ["reference_contract_sat"]
        report["checks"] = [{"label": label, "status": "NOT_RUN"} for label in planned_checks]
        checkpoint("REGISTERED_ALL_CASES")
        bridge = load("caliber_independent_contract_reference_v1", HERE / "contract_reference.py")
        report["admission_regressions"] = [dict(item, status="NOT_RUN") for item in suite["admission_regressions"]]
        checkpoint("ADMISSION_REGRESSIONS_REGISTERED")
        for regression in report["admission_regressions"]:
            try:
                bridge.prepare(regression["constraint"], regression["schema"])
                observed = "SUPPORTED_REFERENCE"
            except bridge.UnverifiedContract as exc:
                observed = "UNVERIFIED_CONTRACT"
                regression["reason"] = str(exc)
            regression.update(status="EVALUATED_PURE_ADMISSION_ONLY", observed_admission=observed,
                              expected_match=observed == regression["expected_admission"])
            if not regression["expected_match"]:
                raise ValueError("registered identifier admission regression failed")
        checkpoint("ADMISSION_REGRESSIONS_RETURNED_NO_NATIVE")
        try:
            contract = bridge.prepare(case["constraint"], case["schema"])
        except bridge.UnverifiedContract as exc:
            report.update(status="UNVERIFIED_CONTRACT", reason=str(exc), solver_status="NOT_RUN",
                          expected_admission_match=case["expected_admission"] == "UNVERIFIED_CONTRACT")
            for entry in report["cases"]:
                if entry["id"] == args.case_id:
                    entry["status"] = "UNVERIFIED_CONTRACT"
            exit_code = 0 if report["expected_admission_match"] else 2
            checkpoint("UNVERIFIED_CONTRACT_RETAINED")
            raise CompletedUnverified
        if case["expected_admission"] != "SUPPORTED_REFERENCE":
            raise ValueError("unexpected admission of registered unsupported contract")
        report["bridge"] = {"original_ast": contract.original_ast, "normalized_ast": contract.normalized_ast,
                            "ledger": contract.ledger, "status": "PREPARED_NOT_CERTIFIED"}
        common = load("caliber_locked_fair_v4_helpers_for_bridge", Path(manifest["common_path"]))
        lock = common.verify_lock(args.runtime_lock, args.runtime_lock_sha256)
        if lock["source_root"] != manifest["required_source_root"] or lock["kernel_path"] != manifest["required_kernel_path"]:
            raise ValueError("only pinned VeriEQL source and reviewed v4 kernel are registered")
        library, z3, constants, Environment, kernel = common.load_runtime(lock, checkpoint, report)
        if case["source_contract_text"] is not None:
            report["source_parser"] = {"status": "ATTEMPTED_EFFECT_UNKNOWN", "text": case["source_contract_text"]}
            checkpoint("SOURCE_CONTRACT_PARSE_ATTEMPT")
            from parsers import ConstraintParser
            actual_ast = ConstraintParser().parse(case["source_contract_text"])
            report["source_parser"].update(status="PARSED", actual_ast=actual_ast,
                                            expected_ast_match=actual_ast == case["expected_parser_ast"])
            if actual_ast != case["expected_parser_ast"] or actual_ast != case["constraint"]:
                raise ValueError("actual source parser AST differs from registered original AST")
        else:
            report["source_parser"] = {"status": "NOT_APPLICABLE_JSON_API_CONTROL", "scope": case["parser_scope"]}
        env = Environment(timer=False, generate_code=False, show_counterexample=False, dialect=constants.DIALECT.MYSQL)
        for table, fields in case["schema"].items():
            count = case["exact_rows"][table]
            if type(count) is not int or count not in [1, 2]:
                raise ValueError("registered exact cardinalities are only N1/N2")
            env.create_database(attributes=fields, bound_size=count, name=table)
        env.save_checkpoints()
        # Capture BASE ONLY. No tested IC has been passed to add_constraints yet.
        base_facts = list(env.DBMS_facts)
        bounds = sorted(env.bound_constraints, key=lambda term: term.sexpr())
        base = base_facts + bounds
        base_text = [term.sexpr() for term in base]
        report["base_only"] = {"facts": base_text, "sha256": hashlib.sha256(json.dumps(base_text).encode()).hexdigest(),
                                "tested_ic_included": False, "exact_rows": case["exact_rows"]}

        def solve(label, assertions):
            item = next(entry for entry in report["checks"] if entry["label"] == label)
            if item["status"] != "NOT_RUN":
                raise ValueError("registered solver slot already attempted")
            item.update(status="ATTEMPTED_EFFECT_UNKNOWN", assertion_count=len(assertions),
                        assertion_sha256=hashlib.sha256("\n".join(term.sexpr() for term in assertions).encode()).hexdigest())
            checkpoint(label + "_ATTEMPT")
            solver = common.solver(z3, constants, START, maximum_ms=1200)
            solver.add(*assertions)
            answer = str(solver.check()); item["status"] = answer
            model = solver.model() if answer == "sat" else None
            if model is not None:
                if not all(z3.is_true(model.eval(term, model_completion=True)) for term in assertions):
                    raise ValueError("solver model fails its recorded assertions")
                item["witness"] = common.decode(env, model, z3)
            if answer == "unknown":
                item["reason_unknown"] = solver.reason_unknown()
            checkpoint(label + "_RETURNED")
            return item, model

        gate, _ = solve("base_only_sat", base)
        if gate["status"] != "sat":
            raise ValueError("BASE_NOT_ESTABLISHED: " + gate["status"])
        deleted = [env.DELETED_FUNCTION(row.SORT) for table in env.base_databases.values() for row in table]
        gate, _ = solve("base_exact_rows", base + [constants.Or(*deleted)])
        if gate["status"] != "unsat":
            raise ValueError("EXACT_ROWS_NOT_ESTABLISHED: " + gate["status"])
        reference = bridge.emit_reference(contract, env, constants)

        def compile_upstream(ast):
            if [term.sexpr() for term in env.DBMS_facts] != [term.sexpr() for term in base_facts]:
                raise ValueError("IC contamination before compilation")
            try:
                env.add_constraints(ast)
                emitted = list(env.DBMS_facts[len(base_facts):])
                return constants.And(*emitted) if emitted else constants.Z3_TRUE
            finally:
                env.DBMS_facts[:] = base_facts
                if sorted(term.sexpr() for term in env.bound_constraints) != sorted(term.sexpr() for term in bounds):
                    raise ValueError("upstream IC compilation changed physical bounds")

        original = compile_upstream(contract.original_ast)
        normalized = compile_upstream(contract.normalized_ast)
        report["formulas"] = {"reference": reference.sexpr(), "original_emitted": original.sexpr(),
                              "normalized_emitted": normalized.sexpr(), "base_restored_after_each_compilation": True}

        def difference(left, right):
            return constants.Or(constants.And(left, constants.Not(right)), constants.And(constants.Not(left), right))

        for label, emitted, expected in [("original_vs_reference", original, case["expected_original_xor"]),
                                          ("normalized_vs_reference", normalized, case["expected_normalized_xor"])]:
            item, model = solve(label, base + [difference(emitted, reference)])
            item["mathematical_expectation"] = expected
            item["expectation_match"] = item["status"] == expected
            if model is not None:
                concrete = bridge.evaluate_reference(contract, item["witness"])
                item["reference_concrete"] = concrete
                item["reference_smt"] = z3.is_true(model.eval(reference, model_completion=True))
                item["emitted_smt"] = z3.is_true(model.eval(emitted, model_completion=True))
                if concrete["holds"] != item["reference_smt"] or item["reference_smt"] == item["emitted_smt"]:
                    raise ValueError("bridge countermodel did not reproduce both truth values")
        for fixed in report["fixed_databases"]:
            fixed["status"] = "ATTEMPTED_EFFECT_UNKNOWN"; checkpoint("FIXED_DATABASE_ATTEMPT")
            assignments = []
            if set(fixed["database"]) != set(case["schema"]):
                raise ValueError("fixed DB not complete")
            for table, rows in fixed["database"].items():
                actual = list(env.base_databases[table]); attrs = list(env.base_databases[table].attributes)
                if len(rows) != len(actual):
                    raise ValueError("fixed DB cardinality differs from exact-N")
                for values, row in zip(rows, actual):
                    if len(values) != len(attrs):
                        raise ValueError("fixed DB row width mismatch")
                    for value, attr in zip(values, attrs):
                        assignments.append(attr.NULL(row.SORT) == (constants.Z3_TRUE if value is None else constants.Z3_FALSE))
                        if value is not None:
                            if type(value) is not int:
                                raise ValueError("fixed DB value must be int or NULL")
                            assignments.append(attr.VALUE(row.SORT) == constants.IntVal(str(value)))
            item, model = solve("fixed_" + fixed["id"], base + assignments)
            if model is None:
                fixed["status"] = "FIXED_BASE_NOT_ESTABLISHED_" + item["status"]
                continue
            fixed["reference_concrete"] = bridge.evaluate_reference(contract, fixed["database"])
            fixed["reference_smt"] = z3.is_true(model.eval(reference, model_completion=True))
            fixed["original_smt"] = z3.is_true(model.eval(original, model_completion=True))
            fixed["normalized_smt"] = z3.is_true(model.eval(normalized, model_completion=True))
            fixed["reference_agrees"] = fixed["reference_concrete"]["holds"] == fixed["reference_smt"]
            fixed["normalized_agrees"] = fixed["normalized_smt"] == fixed["reference_smt"]
            fixed["status"] = "EVALUATED" if fixed["reference_agrees"] and fixed["normalized_agrees"] else "MISMATCH"
        reference_feasibility, _ = solve("reference_contract_sat", base + [reference])
        if case["pair_check"]:
            if reference_feasibility["status"] != "sat":
                raise ValueError("reference contract not established for actual SQL pair")
            attempt = {"status": "ATTEMPTED_EFFECT_UNKNOWN", "queries": case["pair"],
                       "contract_source": "independent original-order reference; no upstream add_constraints here"}
            report["pair_check"] = attempt; checkpoint("OFFICIAL_PAIR_USING_REFERENCE_ATTEMPT")
            env.DBMS_facts[:] = base_facts + [reference]
            env.solver.set(timeout=common.budget_ms(START), threads=1)
            answer = env.analyze(*case["pair"])
            if type(answer) is not bool:
                raise ValueError("non-Boolean official pair result")
            attempt["solver_decision"] = "unsat" if answer else "sat"
            if answer:
                attempt["status"] = "UNEXPECTED_UNSAT"  # Registered source-derived SAT control.
            else:
                model = env.solver.model()
                actual_assertions = list(env.solver.assertions())
                attempt["solver_assertions_sha256"] = hashlib.sha256("\n".join(term.sexpr() for term in actual_assertions).encode()).hexdigest()
                attempt["solver_assertion_count"] = len(actual_assertions)
                if not all(z3.is_true(model.eval(term, model_completion=True)) for term in base + [reference] + actual_assertions):
                    raise ValueError("pair witness violates base/reference contract")
                attempt["witness"] = common.decode(env, model, z3)
                attempt["reference_concrete"] = bridge.evaluate_reference(contract, attempt["witness"])
                attempt["oracle_validation"] = common.guarded_replay(case, case["pair"], attempt["witness"], env, kernel)
                safe = attempt["oracle_validation"]["status"] == "REPLAYED_WITHIN_INT64_DOMAIN"
                different = safe and attempt["oracle_validation"]["sqlite"].get("unequal_as_bags") is True
                attempt["status"] = "SAT_REPLAYED_UNDER_REFERENCE" if different and attempt["reference_concrete"]["holds"] else "PAIR_WITNESS_NOT_VALIDATED"
        else:
            report["pair_check"] = {"status": "NOT_REGISTERED_FOR_THIS_CASE"}
        normalized_check = next(item for item in report["checks"] if item["label"] == "normalized_vs_reference")
        original_check = next(item for item in report["checks"] if item["label"] == "original_vs_reference")
        fixed_ok = all(item["status"] == "EVALUATED" for item in report["fixed_databases"])
        pair_ok = report["pair_check"]["status"] in {"SAT_REPLAYED_UNDER_REFERENCE", "NOT_REGISTERED_FOR_THIS_CASE"}
        passed = normalized_check["status"] == "unsat" and original_check["expectation_match"] and fixed_ok and pair_ok and reference_feasibility["status"] == "sat"
        report["status"] = "COMPLETE_REGISTERED_DIAGNOSTIC" if passed else "COMPLETE_WITH_UNRESOLVED_OR_MISMATCH"
        report["scope"] = "exact registered bounded bridge diagnostic; not a general certificate or novelty result"
        for entry in report["cases"]:
            if entry["id"] == args.case_id:
                entry["status"] = report["status"]
        exit_code = 0 if passed else 2
    except CompletedUnverified:
        pass
    except BaseException as exc:
        report.update(status="ERROR_RETAINED", error_type=type(exc).__name__, reason=str(exc), traceback=traceback.format_exc())
        exit_code = 2
    finally:
        if env is not None:
            try:
                env.__exit__(None, None, None)
                report["environment_cleanup"] = "COMPLETE"
            except Exception as exc:
                report["environment_cleanup"] = {"status": "ERROR", "reason": str(exc)}
        try:
            checkpoint("FINAL_BEFORE_WRITE_EXIT")
        except BaseException as exc:
            report["final_checkpoint_error"] = str(exc)
            save(output, report)
            exit_code = 2
    return exit_code


if __name__ == "__main__":
    code = main()
    sys.stdout.flush(); sys.stderr.flush()
    os._exit(code)
