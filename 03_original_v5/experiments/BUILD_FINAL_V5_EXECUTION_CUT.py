"""Aggregate existing v5 files using stdlib only; never import/run a target.

Default: print a logical-slot recovery ledger. --finalize: write new final JSON
and Chinese Markdown only when all registered selected slots have one terminal
result. Historical queue/campaign labels are retained, never completion gates.
"""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import statistics

TODAY = Path(__file__).resolve().parent.parent
EXP = TODAY / "experiments"
REG = EXP / "v5_registration_01"
RUNTIME = TODAY / "runtime_fair_v5"
SUITE_SHA = "9db84350b498c3e5f37b06adf5868fa0e0429a81a2ebff65f930f78bd8b36485"
LOCK_SHA = {"main": "4221081d3c63096841a902f1c8f70ac16f5d967c08476f26f8377d6bb4924443",
            "spotit": "1c5bc696d43fc64ee5b76a2b4f2e0d0b6d46206179900906bd99f4620c1d8b87"}
ARMS = ("official", "official_generic_smt", "flat", "product", "selector", "official_canonical_sql")
CANDIDATES = ("flat", "product", "selector")
GROUPS = (("main", "cost"), ("main", "differential"), ("spotit", "cost"))
FILES, CHECKS = {}, []


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1048576), b""):
            h.update(block)
    return h.hexdigest()


def register(path):
    digest = sha(path)
    FILES[str(path)] = {"sha256": digest, "bytes": path.stat().st_size}
    return digest


def read(path):
    raw = path.read_bytes()
    FILES[str(path)] = {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
    return json.loads(raw)


def jsha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def check(name, value):
    CHECKS.append({"name": name, "pass": bool(value)})
    return bool(value)


def pick(value, fields):
    return {k: value[k] for k in fields if k in value}


def get(value, *keys, default=None):
    for key in keys:
        if not isinstance(value, dict) or key not in value:
            return default
        value = value[key]
    return value


def jobs_for(suite, kind):
    # Local enumeration only; do not import runtime_fair_v5/common.py.
    jobs = []
    for ci, case in enumerate(suite["cases"]):
        spec = [(a, None) for a in case["arm_order"]] if kind == "cost" else [(a,q) for q in (0,1) for a in CANDIDATES]
        for arm, qi in spec:
            job = {"job_index": len(jobs), "case_index": ci, "case_id": case["id"], "arm": arm, "kind": kind}
            if qi is not None:
                job["query_index"] = qi
            jobs.append(job)
    return jobs


def resource_reason(job, worker):
    if "stop_reason" in job:
        return job["stop_reason"] or "STOP_REASON_FIELD_PRESENT_WITH_EMPTY_VALUE"
    if job.get("exit_code") in (-9, -14, -24):
        return {-9:"SIGKILL_UNATTRIBUTED", -14:"SIGALRM_WORKER_WALL", -24:"SIGXCPU_WORKER_CPU"}[job["exit_code"]]
    if worker.get("error_type") == "TimeoutError":
        return "WORKER_TIMEOUTERROR: " + worker.get("reason", "")
    return None


def pair_execution_state(worker):
    """Receipt-based execution status; deliberately not a correctness verdict."""
    status, phase = worker.get("status"), worker.get("phase")
    started = worker.get("pair_work_started") is True
    if phase == "FINAL_CONTRACT_STOP":
        return "RETURNED_WITH_CONTRACT_STOP" if started else "NOT_RUN_CONTRACT_STOP"
    if status == "COMPLETE" and phase == "FINAL_COMPLETE" and started:
        return "RETURNED"
    if status == "BLOCKED_OR_ERROR" and phase == "ERROR" and started:
        return "RETURNED_WITH_ERROR"
    if started:
        return "ATTEMPTED_EFFECT_UNKNOWN"
    return "NOT_RUN" if not worker or status == "NOT_RUN" else "NO_PAIR_RETURN_RECEIPT"


def oracle_ok(oracle, original_sha, queries, pair):
    original = oracle.get("original_ast_contract_validation", {})
    audits, sqlite = oracle.get("domain_audits", []), oracle.get("sqlite", {})
    return (oracle.get("status") == "REPLAYED_WITHIN_INT64_DOMAIN" and original.get("holds") is True and
            original.get("original_ast_sha256") == original_sha and oracle.get("queries") == queries and
            len(audits) == len(queries) and all(a.get("status") == "SAFE_FOR_SQLITE_INT64" for a in audits) and
            sqlite.get("status") == "REPLAYED_WITHIN_INT64_DOMAIN" and
            len(sqlite.get("matches_audited_mathematical_values", [])) == len(queries) and
            all(sqlite.get("matches_audited_mathematical_values", [])) and
            (not pair or sqlite.get("unequal_as_bags") is True))


def classify(expected, case, job, worker, identity):
    decision = worker.get("final_decision", job.get("final_decision", "NOT_RUN"))
    stop = resource_reason(job, worker)
    terminal = job.get("status") in ("PROCESS_EXITED", "RESOURCE_STOP") and type(job.get("exit_code")) is int
    started = terminal or job.get("status") == "STARTED" or bool(worker)
    state = "RETURNED" if terminal else "STARTED_UNFINISHED_OR_UNREAPED" if started else "NOT_RUN"
    bridge, guard = worker.get("contract_bridge", {}), worker.get("contract_guard", {})
    cleanup = worker.get("environment_cleanup") == "COMPLETE"
    clean = job.get("status") == "PROCESS_EXITED" and "stop_reason" not in job and stop is None
    original_sha = jsha(case["constraint"])
    bridge_ok = (bridge.get("status") == "VERIFIED_BOUNDED_AST_BRIDGE" and bridge.get("original_ast") == case["constraint"] and
                 bridge.get("original_ast_sha256") == original_sha and get(bridge,"base_only_sat","status") == "sat" and
                 get(bridge,"base_only","tested_ic_included") is False and get(bridge,"normalized_vs_reference","status") == "unsat" and
                 get(bridge,"compilation","original_ast_passed_to_upstream") is False and bridge.get("no_pair_oracle_run") is True)
    guard_ok = guard.get("consistency") == "sat" and guard.get("any_base_row_deleted") == "unsat"
    attempts = worker.get("attempts", [])
    last = attempts[-1] if attempts else {}
    sat_replay = decision == "sat" and last.get("status") == "sat" and last.get("witness") is not None and oracle_ok(last.get("oracle_validation",{}),original_sha,case["pair"],True)
    common = identity and clean and job.get("exit_code") == 0 and worker.get("status") == "COMPLETE" and cleanup and bridge_ok and guard_ok and worker.get("pair_work_started") is True
    diff = worker.get("differential", {})
    gates = {"full_contract_sat":"sat", "exact_rows_no_deletion":"unsat", "official_premise_sat":"sat",
             "official_scalar_shape":"unsat", "joint_premise_sat":"sat", "output_mismatch":"unsat"}
    diff_valid = (decision in ("UNSAT_DIFFERENTIAL", "PASS_UNSAT_DIFFERENTIAL") and all(get(diff,"gates",k,"status") == v for k,v in gates.items()) and
                  get(diff,"candidate_auxiliary_extension","status") == "CHECKED_ACYCLIC_FRESH_TOTAL_INT_DEFINITIONS" and
                  get(diff,"contract","unchanged_after_both_encoders") is True and
                  get(diff,"source_ast_bridge","complete_facts_sha256") == bridge.get("complete_facts_sha256"))
    strict = common and (((decision == "unsat" and last.get("status") == "unsat") or sat_replay) and worker.get("analytical_expectation_match",True) is not False if expected["kind"] == "cost" else diff_valid)
    no_query = (worker.get("pair_work_started",False) is False and not attempts and not diff and
                all(worker.get(k) == "NOT_RUN_CONTRACT_STOP" for k in ("pair_work_status","pair_parse_status","pair_solver_status")))
    expected_typed = case.get("expected_final_decision")
    if case["id"].startswith("E10_"):
        expected_typed = "CONTRACT_UNSAT_REJECTED"
    typed_valid = False
    if expected_typed == "CONTRACT_UNSAT_REJECTED":
        typed_valid = (identity and clean and job.get("exit_code") == 2 and cleanup and no_query and decision == expected_typed and
                       bridge_ok and guard.get("consistency") == "unsat" and worker.get("status") == "COMPLETE_CONTRACT_REJECTED")
    elif expected_typed == "UNVERIFIED_CONTRACT":
        typed_valid = (identity and clean and job.get("exit_code") == 2 and cleanup and no_query and decision == expected_typed and
                       worker.get("status") == "COMPLETE_CONTRACT_UNVERIFIED" and bridge.get("status") == "UNVERIFIED_CONTRACT" and
                       all(get(bridge,k,"status") == "NOT_RUN" for k in ("base_only_sat","normalized_vs_reference","compilation")) and
                       get(worker,"fallback","status") == "FORBIDDEN_UNVERIFIED_OR_REJECTED_CONTRACT")
    d01 = None
    if case["id"].startswith("D01_") and expected["kind"] == "cost":
        d01 = strict and decision == "sat" and last.get("witness") == {"T":[[6]]} and get(last,"oracle_validation","sqlite","relations") == [[[None]],[[6]]]
    sat_diff = (expected["kind"] == "differential" and identity and clean and cleanup and bridge_ok and guard_ok and job.get("exit_code") == 2 and worker.get("pair_work_started") is True and
                worker.get("status") == "COMPLETE" and decision == "SAT_OUTPUT_DIFFERENCE_REPLAYED_WITHIN_INT64_DOMAIN" and
                diff.get("witness") is not None and oracle_ok(diff.get("oracle_validation",{}),original_sha,[case["pair"][expected["query_index"]]],False))
    category = ("RESOURCE_STOP_OR_BUDGET_FAILURE" if stop else "EXPECTED_TYPED_NO_QUERY_REJECTION" if typed_valid else
                "STRICT_VALID_PAIR_RESULT" if strict and expected["kind"] == "cost" else "STRICT_VALID_BOUNDED_DIFFERENTIAL_AGREEMENT" if strict else
                "VALIDATED_DIFFERENTIAL_COUNTEREXAMPLE" if sat_diff else "ORACLE_DOMAIN_UNPROVEN" if decision == "UNKNOWN_ORACLE_DOMAIN" else
                "SOLVER_UNKNOWN" if decision in ("unknown","UNKNOWN_OUTPUT_DIFFERENCE") else
                "NOT_RUN_OR_UNFINISHED" if state != "RETURNED" else "OTHER_FAILURE_OR_UNVALIDATED_RESULT")
    return {**expected, "ledger_status":state, "started":started, "raw_final_decision":decision,
            "raw_supervisor_final_decision":job.get("final_decision"), "supervisor_valid_completed_result":job.get("valid_completed_result",False),
            "strict_valid_query_result":bool(strict), "expected_typed_rejection":expected_typed, "verified_expected_typed_rejection":bool(typed_valid),
            "derived_category":category, "resource_stop_reason":stop, "process_status":job.get("status"), "exit_code":job.get("exit_code"),
            "worker_status":worker.get("status"), "worker_phase":worker.get("phase"), "worker_error":pick(worker,("error_type","reason","cleanup_error_type","cleanup_error")),
            "identity_verified":identity, "bridge_verified":bridge_ok, "nonvacuous_full_C_guard_verified":guard_ok,
            "SAT_original_C_and_SQL_replay_verified":sat_replay, "D01_NULL_vs_6_verified":d01, "validated_differential_counterexample":sat_diff,
            "pair_work_started":worker.get("pair_work_started",False), "no_query_work_on_contract_stop":no_query,
            "raw_pair_work_status":worker.get("pair_work_status"), "raw_pair_parse_status":worker.get("pair_parse_status"), "raw_pair_solver_status":worker.get("pair_solver_status"),
            "derived_pair_work_status":pair_execution_state(worker), "pair_work_derivation_rule":"V5_RECEIPT_EXECUTION_STATE_2_REQUIRES_STARTED",
            "pair_return_receipt_fields":pick(worker,("status","phase","pair_work_started","final_decision","environment_cleanup")),
            "raw_stop_reason_field_present":"stop_reason" in job, "raw_stop_reason":job.get("stop_reason"),
            "process_reaped_exit_receipt":terminal,
            "environment_cleanup":worker.get("environment_cleanup","NOT_RECORDED"), "fallback":worker.get("fallback"),
            "analytical_expectation_match":worker.get("analytical_expectation_match"),
            "cost":pick(job,("full_process_wall_seconds","full_process_cpu_seconds","full_process_cpu_user_seconds","full_process_cpu_system_seconds",
                "semantic_e2e_wall_seconds","semantic_e2e_cpu_seconds","sampled_peak_rss_bytes")),
            "incomplete_attempt_checkpoint_cost_not_full_cold":worker.get("resource_last_checkpoint") if not terminal else None,
            "actual_verifier_semantics":worker.get("actual_verifier_semantics"),
            "contract_bridge":pick(bridge,("status","reason","original_ast","original_ast_sha256","normalized_ast","normalized_ast_sha256","ledger",
                "base_only_sat","normalized_vs_reference","complete_facts_sha256","reference_source_sha256","no_pair_oracle_run")),
            "contract_guard":guard,
            "attempts":[pick(a,("route","status","solver_decision","reason","reason_unknown","error_type","error","decision_source","encoding_counts",
                "expression_contains_variable_product","stage_costs","witness","sqlite","oracle_validation")) for a in attempts],
            "differential":{**pick(diff,("status","reason","exception_type","counts","source_ast_bridge","candidate_auxiliary_extension","witness","witness_metadata","oracle_validation","sqlite","agreement_scope")),
                "gates":{k:pick(v,("status","reason_unknown","assertions_sha256","model_satisfies_all_submitted_formulas")) for k,v in diff.get("gates",{}).items()}}}


def inventory(suite, recovery_paths):
    locks = {m:read(REG/("runtime_paths_v5.json" if m == "main" else "spotit_engine_runtime_paths_v5.json")) for m in LOCK_SHA}
    program_integrity = True
    for mode,lock in locks.items():
        lp = REG/("runtime_paths_v5.json" if mode == "main" else "spotit_engine_runtime_paths_v5.json")
        program_integrity &= check(mode+":lock", FILES[str(lp)]["sha256"] == LOCK_SHA[mode] and lock["status"] == "STATIC_REVIEWED_READY_FOR_LOCAL_RUN")
        for raw,digest in lock["runtime_programs"].items():
            program_integrity &= check("program:"+raw, register(Path(raw)) == digest and lock["files"].get(raw) == digest)
    groups = {m+"_"+k:[{**j,"selected":m == "main" or j["arm"] == "official", "observations":[]} for j in jobs_for(suite,k)] for m,k in GROUPS}
    orphan_dirs=[]
    for directory in sorted((TODAY/"runs").glob("fair_v5_*")):
        path=directory/"supervisor_report.json"
        if not path.exists():
            orphan_dirs.append(str(directory));continue
        sup=read(path);mode="spotit" if directory.name.startswith("fair_v5_spotit_") else "main";kind=sup["kind"];group=mode+"_"+kind
        lock=locks[mode];expected_programs={Path(p).name:h for p,h in lock["runtime_programs"].items()}
        header_ok=check(str(path)+":header",program_integrity and sup["suite_sha256"] == SUITE_SHA and sup["runtime_lock_sha256"] == LOCK_SHA[mode] and
            sup["program_sha256"] == expected_programs and sup["full_case_denominator"] == 28 and sup["full_job_denominator"] == 168 and len(sup["jobs"]) == 168)
        for index in range(sup["selected_job_start"],sup["selected_job_start"]+sup["selected_job_limit"]):
            slot=groups[group][index];job=sup["jobs"][index];expected={k:v for k,v in slot.items() if k not in ("selected","observations")};case=suite["cases"][expected["case_index"]]
            wp=Path(job.get("output_directory",str(directory/f"job_{index:04d}")))/"worker_report.json";worker=read(wp) if wp.exists() else {}
            actual_sha=FILES.get(str(wp),{}).get("sha256");inner={k:v for k,v in expected.items() if k != "job_index"};native=worker.get("native_identity",{})
            identity=(header_ok and actual_sha is not None and actual_sha == job.get("worker_report_sha256") and worker.get("job_index") == index and
                worker.get("job") == inner and worker.get("input") == case and worker.get("suite_sha256") == SUITE_SHA and worker.get("runtime_lock_sha256") == LOCK_SHA[mode] and
                all(job.get(k) == v for k,v in inner.items()) and job.get("final_decision") == worker.get("final_decision","NOT_RUN") and
                native.get("version") == lock["expected_native_version"] and native.get("sha256") == lock["files"][lock["native_path"]] and
                native.get("binding_pointer") == native.get("pinned_pointer") and bool(native.get("binding_pointer")))
            if job.get("status") in ("PROCESS_EXITED","RESOURCE_STOP"):
                check(str(wp)+":terminal_identity", identity)
            result=classify(expected,case,job,worker,identity)
            result.update(supervisor_report=str(path),supervisor_report_sha256=FILES[str(path)]["sha256"],supervisor_status=sup["status"],
                          worker_report=str(wp),worker_report_sha256=actual_sha,recorded_worker_report_sha256=job.get("worker_report_sha256"))
            result["pair_work_derivation_evidence"]={"worker_path":str(wp),"worker_sha256":actual_sha,
                "worker_json_fields":["/status","/phase","/pair_work_started","/environment_cleanup","/final_decision","/attempts","/differential"],
                "supervisor_path":str(path),"supervisor_sha256":FILES[str(path)]["sha256"],"supervisor_job_index":index,
                "classification_source":str(Path(__file__).resolve()),"classification_source_sha256":sha(Path(__file__)),
                "boundary":"Execution RETURNED does not imply solver_decided, validated, strict success or acceptable resources; canonical shortcut may not run a solver."}
            slot["observations"].append(result)
    recovery=[{"path":str(p),"document":read(p),"sha256":FILES[str(p)]["sha256"]} for p in recovery_paths]
    confirmed_interrupted_workers=set()
    for item in recovery:
        doc=item["document"]
        intact=True
        for prior in doc.get("prior_evidence",[]):
            intact &= check("recovery_prior:"+prior["path"],register(Path(prior["path"])) == prior["sha256"])
        # Bind process-absence evidence only to the exact old worker snapshot.
        # A new currently STARTED worker is never declared interrupted merely
        # because an earlier campaign has a recovery document.
        if intact and get(doc,"process_absence_evidence","exit_code") == 1 and type(doc.get("original_interrupted_slot")) is int:
            suffix=f"job_{doc['original_interrupted_slot']:04d}/worker_report.json"
            confirmed_interrupted_workers.update((p["path"],p["sha256"]) for p in doc.get("prior_evidence",[]) if p["path"].endswith(suffix))
    blockers=[]
    for group,slots in groups.items():
        for slot in slots:
            returned=[x for x in slot["observations"] if x["ledger_status"] == "RETURNED"]
            started=[x for x in slot["observations"] if x["started"]]
            slot["attempt_count"]=len(started)
            slot["not_run_placeholder_observation_count"]=len(slot["observations"])-len(started)
            if not slot["selected"]:
                slot["ledger_status"]="NOT_SELECTED"
                if started: blockers.append(group+":"+str(slot["job_index"])+" unregistered arm was executed")
            elif len(returned)>1:
                slot["ledger_status"]="DUPLICATE_TERMINAL_RESULTS_REQUIRES_REVIEW";blockers.append(group+":"+str(slot["job_index"])+" duplicate terminal results")
            elif returned:
                slot["ledger_status"]="RETURNED";slot["final"]=returned[0]
                prior=[x for x in started if x is not returned[0]]
                slot["prior_incomplete_attempts"]=prior
                for old in prior:
                    confirmed=(old["worker_report"],old["worker_report_sha256"]) in confirmed_interrupted_workers
                    old["derived_recovery_state"]="INTERRUPTED_EFFECT_UNKNOWN_RETAINED" if confirmed else "PRIOR_UNFINISHED_EFFECT_UNKNOWN"
                    if not confirmed:
                        blockers.append(group+":"+str(slot["job_index"])+" exact recovery evidence required for prior unfinished attempt")
            elif started:
                slot["ledger_status"]="INTERRUPTED_EFFECT_UNKNOWN" if all((x["worker_report"],x["worker_report_sha256"]) in confirmed_interrupted_workers for x in started) else "STARTED_UNFINISHED_OR_UNREAPED"
                blockers.append(group+":"+str(slot["job_index"])+" lacks terminal result")
            else:
                slot["ledger_status"]="NOT_RUN";blockers.append(group+":"+str(slot["job_index"])+" not run")
    histories=[]
    for path in sorted(EXP.glob("*V5*.json")):
        if path.name.startswith(("QUEUE_","CAMPAIGN_")):
            d=read(path);histories.append({"path":str(path),"sha256":FILES[str(path)]["sha256"],"status":d.get("status"),
                "entries":[pick(e,("start","stop","size","kind","mode","status","exit_code","out")) for e in d.get("entries",[])]})
    if orphan_dirs: blockers.append("orphan v5 run directories require review")
    summary={g:{"full":len(ss),"selected":sum(s["selected"] for s in ss),"states":dict(Counter(s["ledger_status"] for s in ss if s["selected"])),
                "started_attempts":sum(s["attempt_count"] for s in ss),"terminal_raw":dict(Counter(s["final"]["raw_final_decision"] for s in ss if "final" in s)),
                "not_run_indices":[s["job_index"] for s in ss if s["selected"] and s["ledger_status"]=="NOT_RUN"],
                "unfinished_indices":[s["job_index"] for s in ss if s["selected"] and s["ledger_status"] not in ("RETURNED","NOT_RUN")]} for g,ss in groups.items()}
    return groups, {"ready":not blockers,"blockers":blockers,"summary":summary,"orphan_run_directories":orphan_dirs}, recovery, histories


def distribution(values):
    return {"observed_count":len(values),"sum":sum(values),"min":min(values) if values else None,
            "median":statistics.median(values) if values else None,"max":max(values) if values else None}


def selection_ledger(groups):
    result={}
    for group,slots in groups.items():
        mode,kind=group.split("_",1)
        for slot in slots:
            final=slot.get("final")
            alternatives=[pick(a,("supervisor_report","supervisor_report_sha256","worker_report","worker_report_sha256",
                "ledger_status","started","raw_final_decision","derived_recovery_state")) for a in slot["observations"] if a is not final]
            key=f"{mode}:{kind}:{slot['job_index']}"
            result[key]={"mode":mode,"kind":kind,"index":slot["job_index"],"case_id":slot["case_id"],"arm":slot["arm"],
                "query_index":slot.get("query_index"),"registered_selected":slot["selected"],"logical_status":slot["ledger_status"],
                "supervisor_path":final["supervisor_report"] if final else None,
                "supervisor_sha256":final["supervisor_report_sha256"] if final else None,
                "worker_path":final["worker_report"] if final else None,"worker_sha256":final["worker_report_sha256"] if final else None,
                "attempt_count":slot["attempt_count"],"not_run_placeholder_count":slot["not_run_placeholder_observation_count"],
                "selection_rule":"unique terminal selected-slot observation; never latest whole batch or fastest result",
                "alternatives":alternatives}
    return result


def summarize(slots):
    selected=[s for s in slots if s["selected"]]
    finals=[s["final"] for s in selected if "final" in s]
    attempts=[a for s in selected for a in s["observations"] if a["started"]]
    fields=("full_process_wall_seconds","full_process_cpu_seconds","semantic_e2e_wall_seconds","semantic_e2e_cpu_seconds","sampled_peak_rss_bytes")
    def measured(row, field):
        value=row["cost"].get(field)
        # A process cannot have a measured peak RSS of zero. Preserve its raw
        # initialization placeholder but exclude it from observed statistics.
        return type(value) in (int,float) and (field != "sampled_peak_rss_bytes" or value > 0)
    return {"full_registered_denominator":len(slots),"selected_denominator":len(selected),"unselected_registered_slots":len(slots)-len(selected),
        "logical_slot_states":dict(Counter(s["ledger_status"] for s in selected)),"started_attempt_denominator":len(attempts),
        "returned_attempts":sum(a["ledger_status"] == "RETURNED" for a in attempts),
        "historical_incomplete_attempts":sum(a["ledger_status"] != "RETURNED" for a in attempts),
        "raw_final_decisions":dict(Counter(r["raw_final_decision"] for r in finals)),
        "raw_pair_work_statuses":dict(Counter(r["raw_pair_work_status"] for r in finals)),
        "derived_pair_work_statuses":dict(Counter(r["derived_pair_work_status"] for r in finals)),
        "derived_categories":dict(Counter(r["derived_category"] for r in finals)),
        "supervisor_valid_completed_results":sum(r["supervisor_valid_completed_result"] is True for r in finals),
        "strict_valid_query_results":sum(r["strict_valid_query_result"] for r in finals),
        "verified_expected_typed_rejections":sum(r["verified_expected_typed_rejection"] for r in finals),
        "resource_stops_or_budget_failures":sum(r["resource_stop_reason"] is not None for r in finals),
        "resource_stop_reasons":dict(Counter(r["resource_stop_reason"] for r in finals if r["resource_stop_reason"])),
        "cleanup_states_all_attempts":dict(Counter(r["environment_cleanup"] for r in attempts)),
        "cleanup_states_non_strict_final_results":dict(Counter(r["environment_cleanup"] for r in finals if not r["strict_valid_query_result"])),
        "bridge_statuses":dict(Counter(get(r,"contract_bridge","status",default="NOT_RECORDED") for r in finals)),
        "base_only_SAT_statuses":dict(Counter(get(r,"contract_bridge","base_only_sat","status",default="NOT_RECORDED") for r in finals)),
        "normalized_C_XOR_reference_statuses":dict(Counter(get(r,"contract_bridge","normalized_vs_reference","status",default="NOT_RECORDED") for r in finals)),
        "contract_guard_consistency":dict(Counter(get(r,"contract_guard","consistency",default="NOT_RECORDED") for r in finals)),
        "SAT_with_original_C_and_SQL_replay":sum(r["SAT_original_C_and_SQL_replay_verified"] for r in finals),
        "validated_differential_counterexamples":sum(r["validated_differential_counterexample"] for r in finals),
        "verifier_auto_policies":dict(Counter(get(r,"actual_verifier_semantics","implemented_auto_policy",default="NOT_RECORDED") for r in finals)),
        "cold_and_semantic_cost_all_attempts_including_failures":{k:{**distribution([r["cost"][k] for r in attempts if measured(r,k)]),
            "missing_count":sum(not measured(r,k) for r in attempts)} for k in fields},
        "incomplete_attempt_checkpoint_costs_not_full_cold":[{"case_id":r["case_id"],"job_index":r["job_index"],"worker_report":r["worker_report"],
            "checkpoint":r["incomplete_attempt_checkpoint_cost_not_full_cold"]} for r in attempts if r["ledger_status"] != "RETURNED"],
        "cost_boundary":"All attempts retained, including historical interrupted slot52. Missing cold CPU/wall and nonpositive RSS initialization placeholders are unknown, not zero; worker checkpoint is only a lower bound. No speedup or repeated-trial claim."}


def final_cut(suite, groups, readiness, recovery, histories):
    paths=[EXP/"FINAL_V5_EXECUTION_CUT.json",EXP/"FINAL_V5_EXECUTION_CUT.zh.md"]
    if any(p.exists() for p in paths):
        raise ValueError("final cut is new-only; preserve existing files")
    freeze=read(RUNTIME/"FREEZE_RECEIPT.json")
    check("freeze_suite",freeze["suite"]["sha256"] == SUITE_SHA)
    for item in [freeze["source_and_diff_manifest"],*freeze["registration_files"],*freeze["independent_reviews"]]:
        check("freeze:"+item["path"],register(Path(item["path"])) == item["sha256"])
    old_suite_path=Path(suite["source_provenance"]["inherited_registration_path"]);old_suite=read(old_suite_path)
    check("original22_full_case_dicts_unchanged",suite["cases"][:22] == old_suite["cases"] and FILES[str(old_suite_path)]["sha256"] == suite["source_provenance"]["inherited_registration_sha256"])
    summaries={g:summarize(ss) for g,ss in groups.items()}
    by_arm={g:{a:summarize([s for s in ss if s["arm"]==a]) for a in (ARMS if g.endswith("cost") else CANDIDATES)} for g,ss in groups.items()}
    strata={g:{label:summarize([s for s in ss if low<=s["case_index"]<high]) for label,low,high in
        (("original_dev12",0,12),("v4_constructed_controls10",12,22),("v5_constructed_adapter_controls6",22,28))} for g,ss in groups.items()}
    controls={c["id"]:{"analytical_registration":c,"results":{g:[s for s in ss if s["case_index"]==ci and s["selected"]] for g,ss in groups.items()}}
        for ci,c in enumerate(suite["cases"]) if ci>=22 or c["id"].startswith("E10_")}
    comparison=[];v4_path=EXP/"V4_COMPLETE_COST_132_SUMMARY.json"
    if v4_path.exists():
        old=read(v4_path)
        for prev in old["jobs"]:
            idx=prev["job_index"];new=groups["main_cost"][idx]["final"]
            check("v4_slot_identity:"+str(idx),(prev["case_id"],prev["arm"]) == (new["case_id"],new["arm"]))
            comparison.append({"job_index":idx,"case_id":new["case_id"],"arm":new["arm"],"v4_raw":prev["final_decision"],
                "v4_historical_derived":prev.get("derived_outcome"),"v4_supervisor_valid":prev.get("valid_completed_result"),
                "v5_raw":new["raw_final_decision"],"v5_strict_valid_query_result":new["strict_valid_query_result"],"v5_category":new["derived_category"],
                "v4_full_process_wall_seconds":prev.get("full_process_wall_seconds"),"v5_final_attempt_full_process_wall_seconds":new["cost"].get("full_process_wall_seconds"),
                "v4_full_process_cpu_seconds":prev.get("full_process_cpu_seconds"),"v5_final_attempt_full_process_cpu_seconds":new["cost"].get("full_process_cpu_seconds"),
                "v5_attempt_count":groups["main_cost"][idx]["attempt_count"],"v4_worker_report_sha256":prev.get("worker_report_sha256"),"v5_worker_report_sha256":new["worker_report_sha256"]})
    register(Path(__file__))
    failures=[x for x in CHECKS if not x["pass"]]
    cut={"status":"FINAL_LOGICAL_SELECTIONS_COMPLETE" if not failures else "FINAL_WITH_IDENTITY_AUDIT_DISCREPANCIES",
        "created_utc":datetime.now(timezone.utc).isoformat(),"readiness":readiness,"suite_sha256":SUITE_SHA,"runtime_lock_sha256":LOCK_SHA,
        "method":"Read-only stdlib hash/count existing results; no target/native/parser/solver imported or executed by this aggregator",
        "data_role":suite["data_role"],"denominators":{"case_bound_configurations":28,"inherited_case_bound_configurations":22,"new_constructed_adapter_controls":6,
            "main_cost_logical_slots":168,"main_differential_logical_slots":168,"spotit_full_registered":168,"spotit_selected_official":28,"spotit_unselected":140},
        "summaries":summaries,"by_arm":by_arm,"strata":strata,"controls":controls,"logical_slots_and_all_observations":groups,
        "slot_selection":selection_ledger(groups),
        "recovery_evidence":recovery,"historical_queue_campaign_records":histories,"original22_v4_v5_single_observation_comparison":comparison,
        "recovery_policy":"Unique terminal observation per logical slot. Old interrupted effect-unknown attempt retained, not erased. A duplicate terminal observation blocks finalization. NOT_RUN placeholders are not attempts. Terminal resource observation failures are not retried or replaced.",
        "classification_boundary":"Raw results and supervisor flags remain separate from stricter source-AST/XOR/nonvacuous-C/replay checks. Typed expected no-query contract rejections are not pair UNSAT, query successes or differential agreement.",
        "pair_work_status_boundary":"Raw pair_work_status is preserved. COMPLETE + FINAL_COMPLETE + pair_work_started true derives execution RETURNED only, with source/worker/receipt hashes. Missing start receipt cannot imply return. Solver UNKNOWN, typed rejects and monitoring stops never become valid query performance.",
        "resource_stop_boundary":"RSS_OBSERVATION_UNAVAILABLE means RSS monitoring availability failure. It does not establish excessive RSS, memory exhaustion or an OOM kill. Raw result, exit, cleanup and all observed costs remain retained; strict success is false.",
        "comparison_boundary":"Original22 input dictionaries unchanged, but v5 adds common normalized source-AST C/reference/XOR adaptation to ALL arms. One observation per arm plus retained interruptions is not a speedup/stability experiment; v4 supervisor-valid is not the same guarantee as v5 strict-valid.",
        "scientific_limits":["Exposed controlled regressions, not human gold, natural defects or heldout generalization.",
            "Source-AST faithfulness only; source-text parser completeness and unchanged upstream IC behavior are not established.",
            "D01 requires original-C-valid A=6 and original SQL SQLite NULL versus6, not merely fixed analytical metadata.",
            "E10/D04/D05 C-unsat must reject before query work; D06 unsupported whole C must stop without fallback.",
            "Base-only SAT and normalized-C/reference XOR UNSAT precede separate full-C consistency. C-UNSAT is never pair-UNSAT.",
            "UNSAT differential means bounded encoder-relative agreement, not a general proof of official SQL semantics.",
            "SpotIt retains observed AUTO_SET; scalar set/bag coincidence is not a bag-implementation claim.",
            "Cold cost and failure cleanup retained. Interrupted-attempt missing full cost stays unknown, not zero or omitted."],
        "audit":{"checks":len(CHECKS),"failed_checks":failures},"file_provenance":FILES}
    paths[0].write_text(json.dumps(cut,ensure_ascii=False,indent=2)+"\n")
    lines=["# v5 执行最终截面","","所有注册的逻辑选中槽已有唯一终态。原始结果、严格有效查询结果、预期类型拒绝、资源失败分开记账；新六项只属于构造适配器回归控制。","",
        "| 阶段 | 完整注册槽 | 选中逻辑槽 | 已启动尝试 | 严格有效查询结果 | 预期类型拒绝 | 资源/预算失败 |","|---|---:|---:|---:|---:|---:|---:|"]
    for g,s in summaries.items():
        lines.append(f"| {g} | {s['full_registered_denominator']} | {s['selected_denominator']} | {s['started_attempt_denominator']} | {s['strict_valid_query_results']} | {s['verified_expected_typed_rejections']} | {s['resource_stops_or_budget_failures']} |")
    lines += ["","cost 分母为28×6臂；differential为28×2查询×3candidate，两组168独立。SpotIt仅选每配置official臂28/168，另140未选择，不能说已运行168。旧 campaign/queue 的停滞标签保留；完成依据是逐槽 terminal 与精确 worker SHA。","",
        "| 阶段 | 原始 final_decision | 派生类别 |","|---|---|---|"]
    for g,s in summaries.items():
        lines.append(f"| {g} | {s['raw_final_decisions']} | {s['derived_categories']} |")
    lines += ["","RSS_OBSERVATION_UNAVAILABLE 表示RSS监测不可用，不是实际RSS超限、内存耗尽或OOM证据。这些终态不重跑，原判定、退出码、清理和成本全部保留，严格有效结果计数排除它们。","",
        "旧raw pair_work_status原样保留。只有明确pair_work_started且COMPLETE/FINAL_COMPLETE才派生查询工作RETURNED；该值仅说明子阶段回执，不等于solver已决定、oracle验证通过或资源合格。每条派生均附worker/监督日志/汇总源码路径和SHA。"]
    lines += ["","| main cost 臂 | 严格有效/28 | 预期类型拒绝 | 资源/预算失败 | 冷CPU已知合计秒（含失败） | 未测完整冷CPU尝试 |","|---|---:|---:|---:|---:|---:|"]
    for a,s in by_arm["main_cost"].items():
        cpu=s["cold_and_semantic_cost_all_attempts_including_failures"]["full_process_cpu_seconds"]
        lines.append(f"| {a} | {s['strict_valid_query_results']} | {s['verified_expected_typed_rejections']} | {s['resource_stops_or_budget_failures']} | {cpu['sum']:.6f} | {cpu['missing_count']} |")
    lines += ["","| 新控制 | main cost 原始判定（六臂） | main differential 原始判定（两查询×三臂） | SpotIt official |","|---|---|---|---|"]
    for name,c in controls.items():
        if name.startswith("D"):
            counts={g:dict(Counter(s['final']['raw_final_decision'] for s in ss)) for g,ss in c["results"].items()}
            lines.append(f"| {name} | {counts['main_cost']} | {counts['main_differential']} | {counts['spotit_cost']} |")
    d01=[s["final"] for s in groups["main_cost"] if s["case_id"].startswith("D01_")]
    lines += ["",f"D01 main cost 原C成立、A=6实际见证与原SQL SQLite NULL对6同时验证：{sum(r['D01_NULL_vs_6_verified'] is True for r in d01)}/6。E10、D04、D05的CONTRACT_UNSAT_REJECTED是合同矛盾，不能记作pair UNSAT；D06的UNVERIFIED_CONTRACT须连同无query/无fallback证据保留。","",
        "原slot52的STARTED/ OFFICIAL_ATTEMPT及旧worker哈希保留为INTERRUPTED_EFFECT_UNKNOWN，恢复尝试另计；旧终态RSS观察失败保留，不能因raw sat/unsat或exit0就改成严格成功。历史中断缺少完整冷CPU/墙钟，worker checkpoint只作下界，不当零成本。","",
        "| 阶段 | base-only SAT | normalized C XOR reference | full-C一致性 | 全尝试清理状态 |","|---|---|---|---|---|"]
    for g,s in summaries.items():
        lines.append(f"| {g} | {s['base_only_SAT_statuses']} | {s['normalized_C_XOR_reference_statuses']} | {s['contract_guard_consistency']} | {s['cleanup_states_all_attempts']} |")
    lines += ["","原22配置完整字典与v4一致，逐槽对照仅列单次结果与冷进程耗时。v5新增共同合同适配及XOR审计，不能据此宣称加速比或稳定强基线优势。所有失败、fallback、oracle和cleanup成本保留；无完整计时者明确记缺失。","",
        "结果仍限于注册源AST及有界编码；不证明源文本解析完整性或任意SQL正确性。SpotIt真实AUTO_SET单独披露，单标量set/bag一致不等于bag实现。","",
        f"身份核对失败项：{len(failures)}。完整槽位/尝试账本、原结果、SHA及恢复证据见 [FINAL_V5_EXECUTION_CUT.json](FINAL_V5_EXECUTION_CUT.json)。本汇总只读取既有文件，不执行目标。",""]
    paths[1].write_text("\n".join(lines))
    print(json.dumps({"status":cut["status"],"failed_checks":failures,"summaries":summaries,"outputs":[str(p) for p in paths]},ensure_ascii=False))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--finalize",action="store_true")
    parser.add_argument("--recovery-ledger",type=Path,action="append",default=[])
    parser.add_argument("--snapshot-out",type=Path)
    parser.add_argument("--selection-out",type=Path)
    args=parser.parse_args()
    suite=read(REG/"REGISTERED_SIX_ARM_SUITE.json")
    if FILES[str(REG/"REGISTERED_SIX_ARM_SUITE.json")]["sha256"] != SUITE_SHA or len(suite["cases"]) != 28:
        raise ValueError("frozen suite changed")
    recovery_paths=[p.resolve() for p in args.recovery_ledger]
    if any(not p.is_relative_to(TODAY) for p in recovery_paths):
        raise ValueError("recovery ledger must be within this research directory")
    groups,ready,recovery,histories=inventory(suite,recovery_paths)
    if args.selection_out:
        path=args.selection_out.resolve()
        if path.exists() or path.parent != EXP:
            raise ValueError("use a new selector ledger path directly under experiments")
        path.write_text(json.dumps({"status":"SLOT_SELECTION_SNAPSHOT","utc":datetime.now(timezone.utc).isoformat(),
            "readiness":ready,"slot_selection":selection_ledger(groups)},ensure_ascii=False,indent=2)+"\n")
    if args.snapshot_out:
        path=args.snapshot_out.resolve()
        if path.exists() or path.parent != EXP:
            raise ValueError("use a new snapshot path directly under experiments")
        path.write_text(json.dumps({"status":"READ_ONLY_SNAPSHOT_NOT_PROCESS_LIVENESS_PROOF","utc":datetime.now(timezone.utc).isoformat(),
            "readiness":ready,"slot_selection":selection_ledger(groups),"groups":groups,"recovery_evidence":recovery,"histories":histories,"checks":CHECKS,"file_provenance":FILES},ensure_ascii=False,indent=2)+"\n")
    if not args.finalize or not ready["ready"]:
        print(json.dumps(ready,ensure_ascii=False));return 0 if ready["ready"] else 2
    final_cut(suite,groups,ready,recovery,histories)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
