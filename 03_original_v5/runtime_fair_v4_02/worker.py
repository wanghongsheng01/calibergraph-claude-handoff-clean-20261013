"""One fresh process and Environment for one cost arm or query differential."""
import time
START = time.monotonic()
import signal
import resource
signal.signal(signal.SIGALRM, signal.SIG_DFL)
signal.signal(signal.SIGXCPU, signal.SIG_DFL)
signal.setitimer(signal.ITIMER_REAL, max(0.001, 24 - (time.monotonic() - START)))
resource.setrlimit(resource.RLIMIT_CPU, (14, 15))
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
signal.pthread_sigmask(signal.SIG_UNBLOCK, {signal.SIGALRM, signal.SIGXCPU})
import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys
import threading
import traceback

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from common import sha, save, verify_lock, load_runtime, new_env, cpu_seconds, budget_ms, solver, guard, decode, replay, jobs_for, ensure_raw_frontend, guarded_replay, canonicalize_conjunctions, verifier_semantics


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-lock", type=Path, required=True)
    parser.add_argument("--expected-lock-sha256", required=True)
    parser.add_argument("--suite", type=Path, required=True)
    parser.add_argument("--expected-suite-sha256", required=True)
    parser.add_argument("--kind", choices=("cost", "differential"), required=True)
    parser.add_argument("--job-index", type=int, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--expected-programs", required=True)
    args = parser.parse_args()
    output = args.out_dir / "worker_report.json"
    report = {"status": "NOT_RUN", "native_load": "NOT_RUN", "environment_import": "NOT_RUN",
              "pid": os.getpid(), "kind": args.kind, "job_index": args.job_index,
              "runtime_lock_sha256": args.expected_lock_sha256, "suite_sha256": args.expected_suite_sha256,
              "solver_threads": 1, "attempts": [], "fallback": {"status": "NOT_NEEDED"}}
    save(output, report)

    def checkpoint(phase):
        report["phase"] = phase
        report["resource_last_checkpoint"] = {"worker_wall_seconds": time.monotonic() - START,
                                              "cpu_seconds": cpu_seconds(),
                                              "maxrss_bytes_darwin": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                                              "python_threads": [{"name": t.name, "daemon": t.daemon} for t in threading.enumerate()]}
        save(output, report)
        print(json.dumps({"phase": phase, "job_index": args.job_index}), flush=True)

    env = None
    try:
        if not (sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode):
            raise ValueError("-B -I -S required")
        for name, expected in json.loads(args.expected_programs).items():
            if Path(name).name != name or sha(HERE / name) != expected:
                raise ValueError("runner program changed: " + name)
        if sha(args.suite) != args.expected_suite_sha256:
            raise ValueError("suite changed")
        suite = json.loads(args.suite.read_text())
        job = jobs_for(suite, args.kind)[args.job_index]
        case = suite["cases"][job["case_index"]]
        report.update(job=job, input=case, data_role=suite["data_role"], source_provenance=suite.get("source_provenance"),
                      final_decision="NOT_RUN", scientific_result="NOT_ESTABLISHED")
        checkpoint("INPUT_REGISTERED")
        lock = verify_lock(args.runtime_lock, args.expected_lock_sha256)
        library, z3, constants, Environment, kernel = load_runtime(lock, checkpoint, report)
        semantic_start = time.monotonic()
        semantic_cpu_start = cpu_seconds()
        checkpoint("SEMANTIC_E2E_BEGIN")
        report["raw_frontend_guard"] = {"status": "ATTEMPTED_EFFECT_UNKNOWN"}
        checkpoint("RAW_FRONTEND_GUARD_ATTEMPT")
        try:
            report["raw_frontend_guard"] = ensure_raw_frontend(case, kernel)
        except kernel.FrontendUnsupported as exc:
            report["raw_frontend_guard"] = {"status": "FRONTEND_UNSUPPORTED", "reason": str(exc)}
            report["fallback"] = {"status": "FORBIDDEN_FRONTEND_UNSUPPORTED", "reason": "official parser shares irreversible raw-identifier transformation"}
            report.update(status="COMPLETE", final_decision="FRONTEND_UNSUPPORTED",
                          scientific_result="NO_EQUIVALENCE_DECISION_INPUT_RETAINED_IN_DENOMINATOR",
                          environment_construction="NOT_RUN", query_parse="NOT_RUN", solver_work="NOT_RUN",
                          semantic_e2e_wall_seconds=time.monotonic() - semantic_start,
                          semantic_e2e_cpu_seconds=cpu_seconds() - semantic_cpu_start,
                          cost_scope="raw frontend gate; process startup/import/hash included in supervisor cost")
            checkpoint("FINAL_FRONTEND_UNSUPPORTED")
            sys.stdout.flush(); sys.stderr.flush()
            os._exit(2)
        checkpoint("RAW_FRONTEND_GUARD_ADMITTED")
        env = new_env(case, Environment, constants)
        report["actual_verifier_semantics"] = verifier_semantics(env, lock)
        facts, contract = guard(env, z3, constants, START)
        report["contract_guard"] = contract
        checkpoint("CONTRACT_GUARD_RETURNED")
        contract_stop = None
        if contract["consistency"] == "unsat":
            contract_stop = ("COMPLETE_CONTRACT_REJECTED", "CONTRACT_UNSAT_REJECTED")
        elif contract["consistency"] == "unknown":
            contract_stop = ("COMPLETE_CONTRACT_UNVERIFIED", "CONTRACT_SATISFIABILITY_UNKNOWN")
        elif contract["consistency"] != "sat":
            raise ValueError("unrecognized contract consistency result")
        elif contract["any_base_row_deleted"] != "unsat":
            contract_stop = ("COMPLETE_CONTRACT_UNVERIFIED", "EXACT_ROW_CONTRACT_UNVERIFIED")
        if contract_stop is not None:
            # Guard work happened, but no query-pair analysis may start. Keep the
            # raw guard evidence and distinguish rejection from an unrun job.
            report.update(final_decision=contract_stop[1],
                          scientific_result="NO_PAIR_EQUIVALENCE_RESULT_CONTRACT_NOT_ESTABLISHED",
                          pair_parse_status="NOT_RUN_CONTRACT_STOP",
                          pair_solver_status="NOT_RUN_CONTRACT_STOP",
                          environment_cleanup="ATTEMPTED_EFFECT_UNKNOWN")
            checkpoint("CONTRACT_STOP_CLEANUP_ATTEMPT")
            try:
                env.__exit__(None, None, None)
                env = None
                report["environment_cleanup"] = "COMPLETE"
            finally:
                # Preserve charged semantic work even if cleanup itself fails;
                # the existing error handler will retain the attempted effect.
                report.update(semantic_e2e_wall_seconds=time.monotonic() - semantic_start,
                              semantic_e2e_cpu_seconds=cpu_seconds() - semantic_cpu_start,
                              cost_scope="common raw frontend gate/fresh Environment/schema/IC/contract guard/cleanup; cold process startup/import/hash cost additionally captured by supervisor")
            report["status"] = contract_stop[0]
            checkpoint("FINAL_CONTRACT_STOP")
            sys.stdout.flush(); sys.stderr.flush()
            os._exit(2)

        def official(generic=False, reason=None):
            attempt = {"route": "official_generic_smt" if generic else "official", "reason": reason,
                       "status": "ATTEMPTED_EFFECT_UNKNOWN"}
            report["attempts"].append(attempt)
            checkpoint("OFFICIAL_ATTEMPT")
            if generic:
                names = ["simplify", "propagate-values", "solve-eqs", "smt"]
                tactic = z3.Then(*(z3.Tactic(name, ctx=constants.Z3_CONTEXT) for name in names), ctx=constants.Z3_CONTEXT)
                env.solver = tactic.solver()
                attempt["tactic_pipeline"] = names
            timeout = budget_ms(START)
            env.solver.set(timeout=timeout, threads=1)
            attempt["solver_timeout_ms"] = timeout
            try:
                answer = env.analyze(*case["pair"])
            except Exception as exc:
                if type(exc).__name__ == "UnknownError":
                    attempt.update(status="unknown", reason_unknown=env.solver.reason_unknown())
                    checkpoint("OFFICIAL_UNKNOWN")
                    return attempt
                if type(exc).__name__ in {"NotSupportedError", "NotImplementedError", "ParserSyntaxError"}:
                    attempt.update(status="unsupported", error_type=type(exc).__name__, error=str(exc))
                    checkpoint("OFFICIAL_UNSUPPORTED")
                    return attempt
                raise
            if type(answer) is not bool:
                raise ValueError("official result is not boolean: " + repr(answer))
            attempt["status"] = "unsat" if answer else "sat"
            if not answer:
                model = env.solver.model()
                if not all(z3.is_true(model.eval(f, model_completion=True)) for f in facts):
                    raise ValueError("official model violates complete input facts")
                attempt["witness"] = decode(env, model, z3)
                attempt["solver_decision"] = "sat"
                attempt["oracle_validation"] = {"status": "ATTEMPTED_EFFECT_UNKNOWN"}
                checkpoint("OFFICIAL_ORACLE_AUDIT_ATTEMPT")
                attempt["oracle_validation"] = guarded_replay(case, case["pair"], attempt["witness"], env, kernel)
                attempt["sqlite"] = attempt["oracle_validation"]["sqlite"]
                if attempt["oracle_validation"]["status"] != "REPLAYED_WITHIN_INT64_DOMAIN":
                    attempt["status"] = attempt["oracle_validation"]["status"]
                elif not attempt["sqlite"]["unequal_as_bags"]:
                    attempt["status"] = "COUNTEREXAMPLE_REPLAY_MISMATCH"
            checkpoint("OFFICIAL_RETURNED")
            return attempt

        if args.kind == "differential":
            from query_differential import compare_query
            report["differential"] = {}
            checkpoint("QUERY_DIFFERENTIAL_ATTEMPT")
            report["differential"] = compare_query(env=env, sql=case["pair"][job["query_index"]], schema=case["schema"],
                                                  mode=job["arm"], z3=z3, constants=constants, kernel=kernel,
                                                  solver_ms=lambda: budget_ms(START), checkpoint=checkpoint,
                                                  record=report["differential"])
            differential = report["differential"]
            if differential.get("witness") is not None:
                differential["solver_differential_status"] = differential["status"]
                differential["oracle_validation"] = {"status": "ATTEMPTED_EFFECT_UNKNOWN"}
                checkpoint("DIFFERENTIAL_ORACLE_AUDIT_ATTEMPT")
                differential["oracle_validation"] = guarded_replay(case, [case["pair"][job["query_index"]]], differential["witness"], env, kernel)
                differential["sqlite"] = differential["oracle_validation"]["sqlite"]
                if differential["oracle_validation"]["status"] != "REPLAYED_WITHIN_INT64_DOMAIN":
                    differential["status"] = differential["oracle_validation"]["status"]
                else:
                    observed = [list(row) for row in differential["sqlite"]["relations"][0]]
                    metadata = differential["witness_metadata"]
                    differential["sqlite"]["matches_official_output"] = observed == metadata["official_rows"]
                    differential["sqlite"]["matches_candidate_output"] = observed == metadata["candidate_rows"]
                    differential["sqlite"]["both_encoders_disagree_with_sqlite"] = not (
                        differential["sqlite"]["matches_official_output"] or differential["sqlite"]["matches_candidate_output"])
                    differential["status"] = "SAT_OUTPUT_DIFFERENCE_REPLAYED_WITHIN_INT64_DOMAIN"
            report["final_decision"] = differential["status"]
            report["scientific_result"] = "PER_QUERY_MAPPING_DIAGNOSTIC_NOT_FULL_GENERAL_PROOF"
        elif job["arm"] == "official_canonical_sql":
            attempt = {"route": "official_canonical_sql", "status": "ATTEMPTED_EFFECT_UNKNOWN",
                       "normalization": "recursively sort AND children only; preserve all other AST components"}
            report["attempts"].append(attempt)
            checkpoint("CANONICAL_SQL_ATTEMPT")
            canonical_reason = None
            stage = "parse"
            stage_wall, stage_cpu = time.monotonic(), cpu_seconds()
            attempt["stage_costs"] = {}
            try:
                parsed = [env.parse_sql_query(sql) for sql in case["pair"]]
                report["parsed_asts"] = parsed
                attempt["stage_costs"][stage] = {"wall_seconds": time.monotonic() - stage_wall, "cpu_seconds": cpu_seconds() - stage_cpu}
                stage = "recognize"
                stage_wall, stage_cpu = time.monotonic(), cpu_seconds()
                plans = [kernel.recognize(ast, case["schema"], identifier_encoding="verieql_double_underscore", original_sql=sql)
                         for ast, sql in zip(parsed, case["pair"])]
                attempt["expression_contains_variable_product"] = [plan.expression_contains_variable_product for plan in plans]
                attempt["stage_costs"][stage] = {"wall_seconds": time.monotonic() - stage_wall, "cpu_seconds": cpu_seconds() - stage_cpu}
                stage = "normalize"
                stage_wall, stage_cpu = time.monotonic(), cpu_seconds()
                canonical = [canonicalize_conjunctions(ast) for ast in parsed]
                attempt["canonical_asts"] = canonical
                identical = canonical[0] == canonical[1]
                attempt["stage_costs"][stage] = {"wall_seconds": time.monotonic() - stage_wall, "cpu_seconds": cpu_seconds() - stage_cpu}
                if identical:
                    attempt.update(status="unsat", decision_source="PURE_FRAGMENT_AND_COMMUTATIVITY",
                                   soundness="Only order of pure admitted Boolean AND operands changed; three-valued AND is commutative; every other AST component and complete input contract are identical.",
                                   proof_boundary="conditional on admitted raw frontend and AST semantics; no IC inference and no pair-equivalence oracle pre-run")
                    report["final_decision"] = "unsat"
                else:
                    attempt.update(status="NORMALIZED_AST_NOT_IDENTICAL")
                    canonical_reason = "canonical_asts_not_identical"
            except kernel.FrontendUnsupported as exc:
                attempt.update(status="FRONTEND_UNSUPPORTED", reason=str(exc))
                report["fallback"] = {"status": "FORBIDDEN_FRONTEND_UNSUPPORTED", "reason": str(exc)}
                report["final_decision"] = "FRONTEND_UNSUPPORTED"
            except kernel.Ineligible as exc:
                attempt.update(status="INELIGIBLE", reason=str(exc))
                canonical_reason = "canonical_recognizer_ineligible"
            except Exception as exc:
                attempt.update(status="CANONICAL_PARSE_OR_NORMALIZE_ERROR", error_type=type(exc).__name__, reason=str(exc))
                canonical_reason = "canonical_parse_or_normalize_failed"
            finally:
                if stage not in attempt["stage_costs"]:
                    attempt["stage_costs"][stage] = {"wall_seconds": time.monotonic() - stage_wall, "cpu_seconds": cpu_seconds() - stage_cpu}
            checkpoint("CANONICAL_SQL_RETURNED")
            if canonical_reason is not None:
                report["fallback"] = {"status": "ATTEMPTED_EFFECT_UNKNOWN", "reason": canonical_reason, "complete_input_preserved": True}
                checkpoint("CANONICAL_OFFICIAL_FALLBACK")
                result = official(reason=canonical_reason)
                report["fallback"]["status"] = "RETURNED"
                report["final_decision"] = result["status"]
        elif job["arm"] in ("official", "official_generic_smt"):
            result = official(generic=job["arm"] == "official_generic_smt")
            report["final_decision"] = result["status"]
        else:
            attempt = {"route": job["arm"], "status": "ATTEMPTED_EFFECT_UNKNOWN"}
            report["attempts"].append(attempt)
            checkpoint("CANDIDATE_PARSE_RECOGNIZE_ATTEMPT")
            parsed = [env.parse_sql_query(sql) for sql in case["pair"]]
            report["parsed_asts"] = parsed
            try:
                plans = [kernel.recognize(ast, case["schema"], identifier_encoding="verieql_double_underscore",
                                          original_sql=sql) for ast, sql in zip(parsed, case["pair"])]
            except kernel.FrontendUnsupported as exc:
                # Defensive: the common pre-parse gate must have rejected this.
                # Never route a shared frontend information-loss issue to oracle.
                attempt.update(status="FRONTEND_UNSUPPORTED", reason=str(exc))
                report["fallback"] = {"status": "FORBIDDEN_FRONTEND_UNSUPPORTED", "reason": str(exc)}
                report["final_decision"] = "FRONTEND_UNSUPPORTED"
            except kernel.Ineligible as exc:
                attempt.update(status="INELIGIBLE", reason=str(exc))
                report["fallback"] = {"status": "ATTEMPTED_EFFECT_UNKNOWN", "reason": "recognizer_ineligible", "complete_input_preserved": True}
                checkpoint("INELIGIBLE_FALLBACK")
                result = official(reason="recognizer_ineligible")
                report["fallback"]["status"] = "RETURNED"
                report["final_decision"] = result["status"]
            else:
                checkpoint("CANDIDATE_ENCODE_ATTEMPT")
                emitted = [kernel.encode(plan, env, job["arm"], f"fair_{job['arm']}_{i}") for i, plan in enumerate(plans)]
                definitions = emitted[0][2] + emitted[1][2]
                s = solver(z3, constants, START)
                s.add(*(facts + definitions))
                s.add(kernel.unequal(*emitted))
                checkpoint("CANDIDATE_SOLVER_ATTEMPT")
                attempt.update(status=str(s.check()), encoding_counts=[item[3] for item in emitted],
                               auxiliary_definition_count=len(definitions))
                if attempt["status"] == "sat":
                    model = s.model()
                    if not all(z3.is_true(model.eval(f, model_completion=True)) for f in facts + definitions):
                        raise ValueError("candidate model violates complete input facts/definitions")
                    attempt["witness"] = decode(env, model, z3)
                    attempt["solver_decision"] = "sat"
                    attempt["oracle_validation"] = {"status": "ATTEMPTED_EFFECT_UNKNOWN"}
                    checkpoint("CANDIDATE_ORACLE_AUDIT_ATTEMPT")
                    attempt["oracle_validation"] = guarded_replay(case, case["pair"], attempt["witness"], env, kernel, plans=plans)
                    attempt["sqlite"] = attempt["oracle_validation"]["sqlite"]
                    if attempt["oracle_validation"]["status"] != "REPLAYED_WITHIN_INT64_DOMAIN":
                        attempt["status"] = attempt["oracle_validation"]["status"]
                    elif not attempt["sqlite"]["unequal_as_bags"]:
                        attempt["status"] = "COUNTEREXAMPLE_REPLAY_MISMATCH"
                elif attempt["status"] == "unknown":
                    attempt["reason_unknown"] = s.reason_unknown()
                report["final_decision"] = attempt["status"]
                checkpoint("CANDIDATE_RETURNED")
                if attempt["status"] == "unknown":
                    try:
                        available_ms = budget_ms(START)
                    except TimeoutError:
                        available_ms = 0
                    if available_ms >= 500:
                        report["fallback"] = {"status": "ATTEMPTED_EFFECT_UNKNOWN", "reason": "candidate_unknown", "complete_input_preserved": True}
                        result = official(reason="candidate_unknown")
                        report["fallback"]["status"] = "RETURNED"
                        report["final_decision"] = result["status"]
                    else:
                        report["fallback"] = {"status": "NOT_RUN_BUDGET_EXHAUSTED", "reason": "candidate_unknown"}
        env.__exit__(None, None, None)
        env = None
        report["semantic_e2e_wall_seconds"] = time.monotonic() - semantic_start
        report["semantic_e2e_cpu_seconds"] = cpu_seconds() - semantic_cpu_start
        report["cost_scope"] = "common raw frontend gate/fresh Environment/schema/IC/guard/parse/recognize/encode/solve/AND normalization/oracle-domain audit/SAT replay/fallback/cleanup; cold process startup/import/hash cost additionally captured by supervisor"
        if args.kind == "cost":
            report["scientific_result"] = "COST_RECORDED_REQUIRES_SEPARATE_SEMANTIC_VALIDATION_AND_PAIRED_ANALYSIS"
        if args.kind == "cost" and "expected" in case:
            report["analytical_expectation_match"] = report["final_decision"] == case["expected"]
        report["status"] = "COMPLETE"
        checkpoint("FINAL_COMPLETE")
        sys.stdout.flush(); sys.stderr.flush()
        os._exit(0 if report["final_decision"] in {"sat", "unsat", "UNSAT_DIFFERENTIAL", "PASS_UNSAT_DIFFERENTIAL"} else 2)
    except BaseException as exc:
        report.update(status="BLOCKED_OR_ERROR", error_type=type(exc).__name__, reason=str(exc), traceback=traceback.format_exc())
        checkpoint("ERROR")
        sys.stdout.flush(); sys.stderr.flush()
        os._exit(2)


if __name__ == "__main__":
    main()
