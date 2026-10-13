"""Pure logging receipt helpers. No imports, target work, or scientific verdicts.

Only the worker's control-flow caller supplies events. RETURNED means dispatch
returned a recorded outcome, not that an SMT/SQL result is scientifically valid.
The parent supervisor must separately acknowledge exit, hashes and resources.
"""

RULE_VERSION = "pair-work-receipt-v1"
PENDING = {"ATTEMPT", "ATTEMPTED_EFFECT_UNKNOWN", "RUNNING", "STARTED"}


def pending_outcome_paths(report):
    """Unclosed attempts cannot be disguised by an outer COMPLETE label."""
    paths = []
    for index, attempt in enumerate(report.get("attempts", [])):
        if attempt.get("status") in PENDING:
            paths.append("attempts/" + str(index) + "/status")
        if attempt.get("oracle_validation", {}).get("status") in PENDING:
            paths.append("attempts/" + str(index) + "/oracle_validation/status")
    for key in ("fallback", "differential"):
        value = report.get(key, {})
        if value.get("status") in PENDING:
            paths.append(key + "/status")
        if value.get("oracle_validation", {}).get("status") in PENDING:
            paths.append(key + "/oracle_validation/status")
    return paths


def outcome_kind(report):
    """Describe a reported outcome; never infer or repair validation."""
    final = report.get("final_decision", "NOT_RUN")
    if report.get("kind") == "differential":
        if final in {"UNSAT_DIFFERENTIAL", "PASS_UNSAT_DIFFERENTIAL"}:
            return "PER_QUERY_DIFFERENTIAL_UNSAT_REPORTED_NOT_PAIR_EQUIVALENCE"
        return "PER_QUERY_DIFFERENTIAL_OUTCOME_REPORTED_NOT_PAIR_EQUIVALENCE"
    if final == "unsat":
        matching = [a for a in report.get("attempts", []) if a.get("status") == final]
        if not matching:
            return "UNATTRIBUTED_UNSAT_LABEL"
        if matching[-1].get("decision_source") == "PURE_FRAGMENT_AND_COMMUTATIVITY":
            return "CANONICAL_AST_IDENTITY_REPORTED_NO_PAIR_SOLVER"
        return "SOLVER_UNSAT_REPORTED_VALIDATION_SEPARATE"
    if final == "sat":
        return "SAT_REPORTED_ORACLE_AND_CONTRACT_VALIDATION_SEPARATE"
    if final == "unknown":
        return "UNKNOWN_NO_SAT_UNSAT_CONCLUSION"
    return "NO_VALIDATED_PAIR_DECISION_INFERRED"


def record_pair_receipt(report, event):
    """Set logging fields only at a real caller-controlled return/stop point.

    Preserve all original attempt, result, error, contract and resource fields.
    Hard termination before a receipt retains ATTEMPTED_EFFECT_UNKNOWN. An
    exception after dispatch returned preserves that earlier return evidence.
    """
    started = report.get("pair_work_started") is True
    pending = pending_outcome_paths(report)
    previous = report.get("pair_work_receipt")
    if event == "DISPATCH_RETURNED":
        if not started:
            state = "INCONSISTENT_RETURN_RECEIPT"
        elif report.get("final_decision", "NOT_RUN") == "NOT_RUN" or pending:
            state = "RETURNED_INCOMPLETE_RECEIPT"
        else:
            state = "RETURNED"
    elif event == "CONTRACT_STOP":
        state = "RETURNED_WITH_CONTRACT_STOP" if started else "NOT_RUN_CONTRACT_STOP"
    elif event == "FRONTEND_STOP":
        state = "RETURNED_WITH_FRONTEND_STOP" if started else "NOT_RUN_FRONTEND_STOP"
    elif event == "ERROR":
        state = "RETURNED_WITH_ERROR" if started else "NOT_RUN_ERROR"
    else:
        # Logging must fail conservatively without changing execution control.
        state = "ATTEMPTED_EFFECT_UNKNOWN" if started else "NOT_RUN"
    receipt = {
        "rule_version": RULE_VERSION,
        "event": event,
        "execution_state": state,
        "pair_dispatch_started": started,
        "raw_final_decision_at_receipt": report.get("final_decision", "NOT_RUN"),
        "reported_outcome_kind": outcome_kind(report),
        "unclosed_outcome_paths": pending,
        "scientific_validation": "NOT_INFERRED_FROM_EXECUTION_RECEIPT",
        "worker_completion": "SEPARATE_FINAL_CHECKPOINT_REQUIRED",
        "process_and_resource_validation": "PENDING_SUPERVISOR_ACKNOWLEDGEMENT",
    }
    if previous is not None:
        receipt["prior_receipt"] = previous
    report["pair_work_status"] = state
    report["pair_work_receipt"] = receipt
    return receipt
