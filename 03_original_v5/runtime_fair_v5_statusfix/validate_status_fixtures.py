"""Stdlib-only logging fixtures and AST checks; no target module is imported."""
import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    # Executing only the zero-import pure logging module is intentional.
    source = (HERE / "pair_status.py").read_text()
    tree = ast.parse(source)
    assert not any(isinstance(n, (ast.Import, ast.ImportFrom)) for n in ast.walk(tree))
    namespace = {}
    exec(compile(tree, str(HERE / "pair_status.py"), "exec"), namespace)
    record = namespace["record_pair_receipt"]
    rows = []

    def check(name, report, event, expected, outcome=None):
        before = deepcopy(report)
        receipt = record(report, event)
        assert report["pair_work_status"] == expected, name
        assert receipt["scientific_validation"] == "NOT_INFERRED_FROM_EXECUTION_RECEIPT", name
        assert receipt["process_and_resource_validation"] == "PENDING_SUPERVISOR_ACKNOWLEDGEMENT", name
        if outcome:
            assert receipt["reported_outcome_kind"] == outcome, name
        # The logger cannot change any decision, attempt, oracle or resource data.
        for key, value in before.items():
            if key not in {"pair_work_status", "pair_work_receipt"}:
                assert report[key] == value, (name, key)
        rows.append({"fixture": name, "event": event, "expected_execution_state": expected,
                     "observed_execution_state": report["pair_work_status"], "status": "PASS"})
        return report

    def base(decision="unsat", kind="cost"):
        return {"kind": kind, "pair_work_started": True,
                "pair_work_status": "ATTEMPTED_EFFECT_UNKNOWN", "final_decision": decision,
                "attempts": [{"route": "official", "status": decision}], "fallback": {"status": "NOT_NEEDED"}}

    check("solver_unsat", base(), "DISPATCH_RETURNED", "RETURNED", "SOLVER_UNSAT_REPORTED_VALIDATION_SEPARATE")
    sat = base("sat")
    sat["attempts"][0]["oracle_validation"] = {"status": "REPLAYED_WITHIN_INT64_DOMAIN"}
    check("sat_with_finished_oracle", sat, "DISPATCH_RETURNED", "RETURNED")
    canonical = base()
    canonical["attempts"][0].update(route="official_canonical_sql", decision_source="PURE_FRAGMENT_AND_COMMUTATIVITY")
    check("canonical_without_pair_solver", canonical, "DISPATCH_RETURNED", "RETURNED", "CANONICAL_AST_IDENTITY_REPORTED_NO_PAIR_SOLVER")
    check("differential_not_pair_unsat", base("PASS_UNSAT_DIFFERENTIAL", "differential"), "DISPATCH_RETURNED", "RETURNED", "PER_QUERY_DIFFERENTIAL_UNSAT_REPORTED_NOT_PAIR_EQUIVALENCE")
    check("unknown_not_decided", base("unknown"), "DISPATCH_RETURNED", "RETURNED", "UNKNOWN_NO_SAT_UNSAT_CONCLUSION")
    for status in ("unsupported", "UNKNOWN_ORACLE_DOMAIN", "COUNTEREXAMPLE_REPLAY_MISMATCH", "INELIGIBLE"):
        check(status, base(status), "DISPATCH_RETURNED", "RETURNED", "NO_VALIDATED_PAIR_DECISION_INFERRED")
    check("early_contract_stop", {"final_decision": "CONTRACT_UNSAT_REJECTED"}, "CONTRACT_STOP", "NOT_RUN_CONTRACT_STOP")
    check("late_contract_stop", base("UNVERIFIED_CONTRACT"), "CONTRACT_STOP", "RETURNED_WITH_CONTRACT_STOP")
    check("frontend_before_pair", {"final_decision": "FRONTEND_UNSUPPORTED"}, "FRONTEND_STOP", "NOT_RUN_FRONTEND_STOP")
    check("error_before_pair", {"final_decision": "NOT_RUN"}, "ERROR", "NOT_RUN_ERROR")
    check("error_after_pair_started", base("NOT_RUN"), "ERROR", "RETURNED_WITH_ERROR")
    cleanup = check("dispatch_before_cleanup_error", base(), "DISPATCH_RETURNED", "RETURNED")
    check("cleanup_error_preserves_prior_receipt", cleanup, "ERROR", "RETURNED_WITH_ERROR")
    assert cleanup["pair_work_receipt"]["prior_receipt"]["execution_state"] == "RETURNED"
    check("dispatch_without_final_label", base("NOT_RUN"), "DISPATCH_RETURNED", "RETURNED_INCOMPLETE_RECEIPT")
    pending = base("sat")
    pending["attempts"][0]["oracle_validation"] = {"status": "ATTEMPTED_EFFECT_UNKNOWN"}
    check("sat_with_oracle_unfinished", pending, "DISPATCH_RETURNED", "RETURNED_INCOMPLETE_RECEIPT")
    pending = base()
    pending["attempts"][0]["status"] = "ATTEMPTED_EFFECT_UNKNOWN"
    check("attempt_unfinished", pending, "DISPATCH_RETURNED", "RETURNED_INCOMPLETE_RECEIPT")
    pending = base()
    pending["fallback"]["status"] = "ATTEMPTED_EFFECT_UNKNOWN"
    check("fallback_unfinished", pending, "DISPATCH_RETURNED", "RETURNED_INCOMPLETE_RECEIPT")
    pending = base("SAT_OUTPUT_DIFFERENCE_REPLAYED_WITHIN_INT64_DOMAIN", "differential")
    pending["differential"] = {"status": "sat", "oracle_validation": {"status": "ATTEMPTED_EFFECT_UNKNOWN"}}
    check("differential_oracle_unfinished", pending, "DISPATCH_RETURNED", "RETURNED_INCOMPLETE_RECEIPT")
    check("unrecognized_event", base(), "UNRECOGNIZED", "ATTEMPTED_EFFECT_UNKNOWN")
    check("return_without_start", {"final_decision": "unsat"}, "DISPATCH_RETURNED", "INCONSISTENT_RETURN_RECEIPT")
    resource = base("sat")
    resource.update(stop_reason="RSS_OBSERVATION_UNAVAILABLE", exit_code=0, valid_completed_result=False)
    check("resource_stop_not_promoted", resource, "DISPATCH_RETURNED", "RETURNED")
    assert resource["valid_completed_result"] is False
    interrupted = base("NOT_RUN")
    # A hard stop never reaches a logger callback; persisted attempt remains unknown.
    assert interrupted["pair_work_status"] == "ATTEMPTED_EFFECT_UNKNOWN"
    rows.append({"fixture": "interrupted_no_callback", "status": "PASS"})

    class RemoveLogging(ast.NodeTransformer):
        def visit_ImportFrom(self, node):
            return None if node.module == "pair_status" else node

        def visit_Expr(self, node):
            call = node.value
            if isinstance(call, ast.Call) and isinstance(call.func, ast.Name):
                if call.func.id == "record_pair_receipt":
                    return None
                if call.func.id == "checkpoint" and len(call.args) == 1 and isinstance(call.args[0], ast.Constant) and call.args[0].value == "QUERY_WORK_RETURNED":
                    return None
            return self.generic_visit(node)

    old = ast.parse((HERE.parent / "runtime_fair_v5/worker.py").read_text())
    new = RemoveLogging().visit(ast.parse((HERE / "worker.py").read_text()))
    assert ast.dump(old, include_attributes=False) == ast.dump(new, include_attributes=False)
    receipt = {"status": "PASS_PURE_STDLIB_LOGGING_FIXTURES_ONLY", "fixture_count": len(rows), "fixtures": rows,
               "worker_control_flow_ast_equal_after_removing_logging_only_additions": True,
               "target_native_solver_SQL_import_or_execution": "NONE",
               "module_import_policy": "zero-import pair_status.py only; worker inspected as AST, never executed",
               "programs": {name: sha(HERE / name) for name in ("pair_status.py", "worker.py", "validate_status_fixtures.py")}}
    path = HERE / "PURE_STATUS_FIXTURE_RECEIPT.json"
    with path.open("x") as stream:
        json.dump(receipt, stream, indent=2)
        stream.write("\n")
    print(json.dumps({"status": receipt["status"], "fixtures": len(rows), "receipt_sha256": sha(path)}))


if __name__ == "__main__":
    main()
