"""Read-only stdlib receipt/hash/arithmetic audit; never imports target code.

Execute only after ROOT confirms the supervisor has been reaped. This verifies
recorded SQL replay and independently calculates the registered one-row scalar
example; it does not rerun SQLite, Z3, the worker, or any author helper.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

T = Path(__file__).resolve().parent.parent
R = T / "runtime_fair_v5_statusfix/registration"
RUN = T / "runs/statusfix_supervisor_integration_01"
LOCK_SHA = "16c76c134cdca4ef9461506968cecbbdb73ce6bc6304acdbeb7e878f19613d18"
SUITE_SHA = "84b1077a998a5cac1d05e6ad5631fc3f6b0f6a618f0e228402c2eb70c08f12e9"
REF_SHA = "fdcee3a919930013945c571e64b7d4b478186c93ceee4546ff520879e99680e0"
issues = []
evidence = {}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def record(path):
    path = Path(path)
    value = sha(path)
    evidence[str(path)] = value
    return value


def read(path):
    record(path)
    return json.loads(Path(path).read_text())


def check(value, location, expected):
    if not value:
        issues.append({"location": str(location), "expected": expected})


def jsha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def concrete_original_c(ast, a):
    if isinstance(ast, list):
        return all(concrete_original_c(x, a) for x in ast)
    op, args = next(iter(ast.items()))
    if op == "and":
        return all(concrete_original_c(x, a) for x in args)
    if op == "or":
        return any(concrete_original_c(x, a) for x in args)
    operands = [a if x == {"value": "T__A"} else x for x in args]
    if any(x is None for x in operands):
        return False
    left, right = operands
    return {"lt": lambda: left < right, "lte": lambda: left <= right,
            "gt": lambda: left > right, "gte": lambda: left >= right,
            "eq": lambda: left == right, "neq": lambda: left != right}[op]()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root-reaped-confirmation", required=True,
                        help="Exact parent confirmation or path to its receipt; this script cannot observe historical tool state")
    parser.add_argument("--execution-receipt", type=Path)
    args = parser.parse_args()
    out = Path(__file__).with_name("STATUSFIX_SUPERVISOR_EXECUTED_REVIEW.json")
    if out.exists():
        raise SystemExit("Refusing to overwrite a prior review")
    lockp = R / "runtime_paths_statusfix_reviewed_main_01.json"
    suitep = R / "SUPERVISOR_INTEGRATION_14_SLOTS_01.json"
    lock, suite = read(lockp), read(suitep)
    registration = read(R / "SUPERVISOR_INTEGRATION_REGISTRATION_01.json")
    expected_by_index = {x["job_index"]: x for x in registration["selected_identities"]}
    check(record(lockp) == LOCK_SHA, lockp, "exact reviewed READY lock")
    check(record(suitep) == SUITE_SHA, suitep, "exact registered suite")
    bad = [p for p, h in lock["files"].items() if not Path(p).is_file() or sha(p) != h]
    check(len(lock["files"]) == 854 and not bad, lockp, "854 locked bytes match")
    programs = {Path(p).name: h for p, h in lock["runtime_programs"].items()}
    for p, h in lock["runtime_programs"].items():
        check(record(p) == h, p, "six unchanged source identities")
    sp = RUN / "supervisor_report.json"
    supervisor = read(sp)
    initial = read(RUN / "initial_not_run.json")
    check(len(supervisor["jobs"]) == 24 and supervisor["full_job_denominator"] == 24
          and supervisor["full_case_denominator"] == 4, sp, "24 slots / 4 cases")
    check(supervisor["selected_job_start"] == 5 and supervisor["selected_job_limit"] == 14,
          sp, "only14 selected indices5..18")
    check(supervisor["runtime_lock_sha256"] == LOCK_SHA and supervisor["suite_sha256"] == SUITE_SHA
          and supervisor["program_sha256"] == programs, sp, "source/suite hashes")
    check(supervisor["status"] == "COMPLETED_WITH_FAILURES_OR_NOT_RUN", sp,
          "typed controls preserve negative supervisor status")
    check(len(initial["jobs"]) == 24 and all(j["status"] == j["final_decision"] == "NOT_RUN" for j in initial["jobs"]),
          RUN / "initial_not_run.json", "all24 initiallyNOT_RUN")
    if args.execution_receipt:
        execution_receipt = read(args.execution_receipt)
    else:
        execution_receipt = None
    emergency = RUN / "emergency.jsonl"
    record(emergency)
    check(not emergency.read_bytes(), emergency, "empty emergency ledger")
    rows = []
    for i, job in enumerate(supervisor["jobs"]):
        if i not in expected_by_index:
            check(job == initial["jobs"][i], f"unselected/{i}", "unselected exact initial record retained")
            check(not (RUN / f"job_{i:04d}").exists(), f"unselected/{i}", "no output directory or execution")
            continue
        exp = expected_by_index[i]
        wp = RUN / f"job_{i:04d}/worker_report.json"
        if not wp.exists():
            check(False, wp, "selected worker report exists")
            rows.append({"job_index": i, "missing_worker_report": True, "raw_job": job})
            continue
        w = read(wp)
        case = suite["cases"][i // 6]
        decision = exp["integration_expected_final_decision"]
        typed = i >= 12
        check(job.get("output_directory") == str(wp.parent), wp, "registered exact output path")
        check(job.get("worker_report_sha256") == sha(wp), wp, "supervisor matches actual worker bytes")
        check(w["input"] == case and w["job"] == {"case_index": i // 6, "case_id": case["id"],
              "arm": case["arm_order"][i % 6], "kind": "cost"}, wp, "exact original registered case/arm")
        check(w["job_index"] == i and w["pid"] == job.get("pid"), wp, "worker identity")
        check(w["runtime_lock_sha256"] == LOCK_SHA and w["suite_sha256"] == SUITE_SHA, wp, "same source/suite lock")
        check("stop_reason" not in job and job.get("status") == "PROCESS_EXITED", wp, "no resource/observer stop")
        check(job.get("exit_code") == (2 if typed else 0), wp, "expected actual child exit")
        check(w["final_decision"] == job["final_decision"] == decision, wp, "expected decision retained")
        check(w.get("environment_cleanup") == job.get("environment_cleanup") == "COMPLETE", wp, "cleanup complete")
        check(w.get("pair_work_status") == exp["integration_expected_pair_work_status"], wp, "expected recorded work state")
        for key in ["attempts", "fallback", "pair_work_status", "pair_work_receipt", "contract_bridge"]:
            check(w.get(key) == job.get(key), f"{wp}/{key}", "supervisor exact propagation")
        receipt = w.get("pair_work_receipt", {})
        check(receipt.get("event") == ("CONTRACT_STOP" if typed else "DISPATCH_RETURNED")
              and receipt.get("execution_state") == w.get("pair_work_status")
              and receipt.get("pair_dispatch_started") is (not typed)
              and receipt.get("raw_final_decision_at_receipt") == decision
              and receipt.get("unclosed_outcome_paths") == [], wp, "complete actual status receipt")
        check(receipt.get("scientific_validation") == "NOT_INFERRED_FROM_EXECUTION_RECEIPT", wp, "execution not inflated into science")
        check(0 < job.get("full_process_wall_seconds", 0) < 25 and 0 < job.get("full_process_cpu_seconds", 0) < 15
              and 0 < job.get("sampled_peak_rss_bytes", 0) < 2**30, wp, "actual positive resources within registered envelope")
        native = w.get("native_identity", {})
        check(native.get("version") == [4, 12, 0, 0] and native.get("sha256") == lock["files"][lock["native_path"]]
              and native.get("binding_pointer") == native.get("pinned_pointer"), wp, "locked compatible native identity")
        check(all(p in lock["files"] for p in w.get("module_origins", {}).values()), wp, "recorded module origins in lock")
        for name in ["stdout.log", "stderr.log"]:
            record(wp.parent / name)
        phases = [json.loads(line)["phase"] for line in (wp.parent / "stdout.log").read_text().splitlines()
                  if line.startswith('{"phase":')]
        check(phases[-1:] == (["FINAL_CONTRACT_STOP"] if typed else ["FINAL_COMPLETE"]), wp, "actual final stdout phase")
        if not typed:
            check("QUERY_WORK_RETURNED" in phases and "ENVIRONMENT_CLEANUP_ATTEMPT" in phases
                  and phases.index("QUERY_WORK_RETURNED") < phases.index("ENVIRONMENT_CLEANUP_ATTEMPT"), wp,
                  "dispatch receipt precedes cleanup")
        else:
            check(not any(p.startswith("QUERY_WORK_") for p in phases), wp, "typed stop never enters pair dispatch")
        bridge = w.get("contract_bridge", {})
        check(bridge.get("original_ast") == case["constraint"] and bridge.get("original_ast_sha256") == jsha(case["constraint"]), wp, "original source C unchanged")
        if i < 18:
            check(bridge.get("status") == "VERIFIED_BOUNDED_AST_BRIDGE"
                  and bridge["base_only_sat"]["status"] == "sat" and bridge["normalized_vs_reference"]["status"] == "unsat", wp, "nonvacuous base and normalized/reference XOR")
            check(bridge.get("reference_source_sha256") == REF_SHA and bridge["base_only"]["tested_ic_included"] is False
                  and bridge["base_only"]["exact_rows"] == {"T": 1}, wp, "same reference and base excluding tested C")
            check(hashlib.sha256("\n".join(bridge["base_only"]["facts"]).encode()).hexdigest()
                  == bridge["base_only"]["sha256"] == bridge["base_only_sat"]["assertion_sha256"], wp, "base facts hashes")
            check(bridge["compilation"]["status"] == "COMPILED_NORMALIZED_COPY"
                  and bridge["compilation"]["original_ast_passed_to_upstream"] is False
                  and bridge["normalized_ast_sha256"] == jsha(bridge["normalized_ast"]), wp, "normalized copy only with exact AST hash")
            guard = w["contract_guard"]
            check(guard["consistency"] == ("unsat" if typed else "sat") and guard["any_base_row_deleted"] == "unsat"
                  and guard["base_fact_sha256"] == bridge["complete_facts_sha256"], wp, "whole contract guard/exact row/facts identity")
        else:
            check(bridge.get("status") == "UNVERIFIED_CONTRACT"
                  and bridge.get("unsupported_policy") == "WHOLE_CONTRACT_STOP_NO_DROP_NO_FALLBACK"
                  and all(bridge[k]["status"] == "NOT_RUN" for k in ["base_only_sat", "normalized_vs_reference", "compilation"])
                  and "contract_guard" not in w, wp, "unsupported whole C never partially compiled")
        witnesses = []
        if typed:
            check(w["status"] == ("COMPLETE_CONTRACT_REJECTED" if i < 18 else "COMPLETE_CONTRACT_UNVERIFIED")
                  and job.get("valid_completed_result") is False, wp, "typed no-query result not valid pair result")
            check(w["attempts"] == [] and not w.get("pair_work_started", False)
                  and w["fallback"]["status"] == "FORBIDDEN_UNVERIFIED_OR_REJECTED_CONTRACT"
                  and "parsed_asts" not in w, wp, "no query/fallback effects")
            check(all(w.get(k) == "NOT_RUN_CONTRACT_STOP" for k in ["pair_work_status", "pair_parse_status", "pair_solver_status"]), wp, "explicit typed NOT_RUN")
        else:
            check(w["status"] == "COMPLETE" and job.get("valid_completed_result") is True
                  and w.get("pair_work_started") is True and w.get("analytical_expectation_match") is True, wp, "real complete query result")
            check(w["attempts"][-1]["status"] == decision, wp, "last attempt establishes actual decision")
            for attempt in w["attempts"]:
                if attempt["status"] != "sat":
                    continue
                db = attempt["witness"]
                check(db == {"T": [[6]]}, wp, "D01 entire exact-row database is A6")
                a = db["T"][0][0]
                holds = concrete_original_c(case["constraint"], a)
                check(holds and type(a) is int, wp, "independent arithmetic original-order C true")
                calculated = [a if a < 5 else None, a]
                check(case["pair"] == ["SELECT SUM(T.A) FROM T WHERE T.A < 5", "SELECT SUM(T.A) FROM T"], wp, "exact original SQL")
                oracle = attempt["oracle_validation"]
                check(oracle["status"] == "REPLAYED_WITHIN_INT64_DOMAIN" and oracle["queries"] == case["pair"], wp, "recorded original SQL actual replay")
                check(oracle["original_ast_contract_validation"]["holds"] is True
                      and oracle["original_ast_contract_validation"]["original_ast_sha256"] == jsha(case["constraint"]), wp, "oracle original C identity")
                check(all(x["status"] == "SAFE_FOR_SQLITE_INT64" and not x["issues"] for x in oracle["domain_audits"]), wp, "both numeric-domain gates")
                sql = oracle["sqlite"]
                check(sql == attempt["sqlite"] and sql["relations"] == [[[x]] for x in calculated]
                      and sql["unequal_as_bags"] is True and sql["matches_audited_mathematical_values"] == [True, True], wp, "full replay shape NULL/6 agrees with separate arithmetic")
                witnesses.append({"database": db, "original_C_independent_arithmetic": holds,
                                  "independently_calculated_SQL_values": calculated, "recorded_SQLite_relations": sql["relations"], "SQLite_reexecuted_here": False})
            check(len(witnesses) == (1 if i == 5 else 0), wp, "one actual SAT replay overall")
        rows.append({"job_index": i, "case_id": case["id"], "arm": case["arm_order"][i % 6],
                     "worker_sha256": sha(wp), "decision": w["final_decision"], "worker_status": w["status"],
                     "exit_code": job.get("exit_code"), "stop_reason_present": "stop_reason" in job,
                     "work_state": w.get("pair_work_status"), "receipt": receipt, "phase": w.get("phase"),
                     "cleanup": w.get("environment_cleanup"), "attempts": w["attempts"], "fallback": w["fallback"],
                     "bridge_status": bridge["status"], "guard": w.get("contract_guard"), "witness_checks": witnesses,
                     "full_process_wall_seconds": job.get("full_process_wall_seconds"),
                     "full_process_cpu_seconds": job.get("full_process_cpu_seconds"),
                     "sampled_peak_rss_bytes": job.get("sampled_peak_rss_bytes"),
                     "sampled_max_kernel_threads": job.get("sampled_max_kernel_threads"),
                     "worker_resource_last_checkpoint": w.get("resource_last_checkpoint")})
    result = {"status": "FIXED_WITH_EXECUTED_EVIDENCE_FOR_REGISTERED_14_SLOT_SUPERVISOR_INTEGRATION" if not issues else "REVIEW_FINDINGS_REMAIN",
              "reviewed_utc": datetime.now(timezone.utc).isoformat(), "reviewer": "Different AI reviewer, not human; earlier narrow reference module coauthorship disclosed; not author/executor of this statusfix integration.",
              "scope": "Only this separate exposed logging/supervisor integration, not a new scientific cohort; no timings pooled with or replacing frozen main168.",
              "root_reaped_confirmation": args.root_reaped_confirmation, "external_execution_receipt": execution_receipt,
              "execution_by_reviewer": "No target/native/solver/SQLite execution; only stdlib JSON/hash and registered concrete arithmetic.",
              "locked_file_count": len(lock["files"]), "locked_mismatches": bad, "program_hashes": programs,
              "counts": {"registered_cost_slots": 24, "selected_reviewed": len(rows), "unselected_NOT_RUN": 10,
                         "decisions": dict(Counter(r.get("decision", "MISSING") for r in rows)),
                         "work_states": dict(Counter(r.get("work_state", "MISSING") for r in rows)),
                         "exit_codes": dict(Counter(r.get("exit_code", "MISSING") for r in rows)),
                         "resource_stops": sum(r.get("stop_reason_present", True) for r in rows)},
              "supervisor_status": supervisor["status"], "supervisor_wall_before_final_write": supervisor.get("wall_seconds_before_final_write"),
              "limitations": ["RETURNED is a dispatch receipt, not solver validity or scientific acceptance.",
                              "Typed child exits2 and aggregate negative status are deliberate controls, not all-zero-exit PASS.",
                              "RSS is sampled and soft; no continuous hard RSS or single-OS-thread claim.",
                              "No fault injection, resource-stop race coverage, or reachability proof of incomplete-receipt states.",
                              "Recorded solver XOR obligations are not portable proof certificates or general SQL correctness.",
                              "No improvement in novelty, natural defect prevalence, held-out generalization, or selector advantage established."],
              "issues": issues, "slots": rows, "raw_evidence_sha256": evidence, "audit_script_sha256": sha(__file__)}
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"status": result["status"], "counts": result["counts"], "issues": issues,
                      "path": str(out), "sha256": sha(out)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
