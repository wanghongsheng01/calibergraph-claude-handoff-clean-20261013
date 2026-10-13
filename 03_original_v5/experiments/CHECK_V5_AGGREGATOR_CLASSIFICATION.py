"""Stdlib-only summary classifier checks; never execute any experimental target."""
import argparse
import ast
import copy
import hashlib
import json
from pathlib import Path
import runpy

EXP = Path(__file__).resolve().parent
PROGRAM = EXP / "BUILD_FINAL_V5_EXECUTION_CUT.py"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    if out.parent != EXP or out.exists():
        raise ValueError("output must be a new file directly under experiments")
    ast.parse(PROGRAM.read_text())
    m = runpy.run_path(str(PROGRAM))
    inputs = {}

    def read(path):
        raw = path.read_bytes()
        inputs[str(path)] = hashlib.sha256(raw).hexdigest()
        return json.loads(raw)

    suite = read(EXP / "v5_registration_01/REGISTERED_SIX_ARM_SUITE.json")
    snapshot = read(EXP / "V5_READONLY_RECOVERY_RECONCILED_01.json")
    checks = []

    def trial(name, group, index, change, good):
        row = snapshot["groups"][group][index]
        final = row["final"]
        sup = read(Path(final["supervisor_report"]))
        job = copy.deepcopy(sup["jobs"][index])
        worker = copy.deepcopy(read(Path(final["worker_report"])))
        change(job, worker)
        fields = ("job_index", "case_index", "case_id", "arm", "kind", "query_index")
        expected = {k:row[k] for k in fields if k in row}
        result = m["classify"](expected, suite["cases"][row["case_index"]], job, worker, True)
        checks.append({"name":name, "pass":bool(good(result)),
            "strict":result["strict_valid_query_result"], "category":result["derived_category"],
            "derived_pair":result["derived_pair_work_status"]})

    same = lambda j,w: None
    trial("actual_completed_unsat", "main_cost", 0, same,
          lambda r:r["strict_valid_query_result"] and r["derived_pair_work_status"] == "RETURNED")
    trial("empty_stop_field_is_not_clean", "main_cost", 0, lambda j,w:j.update(stop_reason=""),
          lambda r:not r["strict_valid_query_result"] and r["resource_stop_reason"] is not None)
    trial("null_stop_field_is_not_clean", "main_cost", 0, lambda j,w:j.update(stop_reason=None),
          lambda r:not r["strict_valid_query_result"] and r["resource_stop_reason"] is not None)
    trial("stale_unsat_final_missing_attempt", "main_cost", 0, lambda j,w:w.update(attempts=[]),
          lambda r:not r["strict_valid_query_result"])
    trial("pair_started_false_has_no_return_receipt", "main_cost", 0, lambda j,w:w.update(pair_work_started=False),
          lambda r:not r["strict_valid_query_result"] and r["derived_pair_work_status"] == "NO_PAIR_RETURN_RECEIPT")
    trial("pair_started_missing_has_no_return_receipt", "main_cost", 0, lambda j,w:w.pop("pair_work_started"),
          lambda r:not r["strict_valid_query_result"] and r["derived_pair_work_status"] == "NO_PAIR_RETURN_RECEIPT")
    trial("unclean_exit_not_strict", "main_cost", 0, lambda j,w:j.update(exit_code=2),
          lambda r:not r["strict_valid_query_result"])
    trial("resource_reaped_raw_sat_stays_not_strict", "main_cost", 19, same,
          lambda r:not r["strict_valid_query_result"] and r["derived_pair_work_status"] == "RETURNED")
    trial("canonical_shortcut_returned_not_solver_claim", "main_cost", 41, same,
          lambda r:r["strict_valid_query_result"] and r["attempts"][-1]["decision_source"] == "PURE_FRAGMENT_AND_COMMUTATIVITY")
    trial("typed_reject_not_query_success", "main_cost", 126, same,
          lambda r:r["verified_expected_typed_rejection"] and not r["strict_valid_query_result"] and r["derived_pair_work_status"] == "NOT_RUN_CONTRACT_STOP")
    trial("actual_differential_agreement", "main_differential", 0, same,
          lambda r:r["strict_valid_query_result"])
    trial("diff_missing_pair_start_not_strict", "main_differential", 0, lambda j,w:w.pop("pair_work_started"),
          lambda r:not r["strict_valid_query_result"] and r["derived_pair_work_status"] == "NO_PAIR_RETURN_RECEIPT")
    trial("diff_failed_exit_not_strict", "main_differential", 0, lambda j,w:j.update(exit_code=2),
          lambda r:not r["strict_valid_query_result"])
    trial("diff_solver_unknown_not_strict", "main_differential", 0,
          lambda j,w:w["differential"]["gates"]["output_mismatch"].update(status="unknown"),
          lambda r:not r["strict_valid_query_result"])
    old = read(EXP.parent / "runs/fair_v5_main_cost_051_01/job_0052/worker_report.json")
    checks.append({"name":"old52_official_attempt_remains_unknown",
                   "pass":m["pair_execution_state"](old) == "ATTEMPTED_EFFECT_UNKNOWN"})
    # Apply only the cost measurement function to preserved rows. Missing/zero
    # RSS is never a valid measured peak and checkpoints do not replace it.
    rows = copy.deepcopy(snapshot["groups"]["main_cost"])
    for row in rows:
        for record in [*row["observations"], *([row["final"]] if "final" in row else [])]:
            record.setdefault("raw_pair_work_status", None)
            record.setdefault("derived_pair_work_status", "NOT_USED_FOR_COST_TEST")
    stats = m["summarize"](rows)
    rss = stats["cold_and_semantic_cost_all_attempts_including_failures"]["sampled_peak_rss_bytes"]
    checks.append({"name":"old52_zero_RSS_excluded_not_replaced_by_checkpoint",
                   "pass":rss["observed_count"] == 168 and rss["missing_count"] == 1 and rss["min"] > 0,
                   "RSS_distribution":rss})
    result = {"status":"PASS" if all(x["pass"] for x in checks) else "FAIL",
        "scope":"Pure stdlib aggregator classifier regression only; identity=True is a unit fixture, not an experimental verification claim. No target/native/parser/solver run.",
        "aggregator_path":str(PROGRAM), "aggregator_sha256":hashlib.sha256(PROGRAM.read_bytes()).hexdigest(),
        "check_source_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "fixture_inputs_sha256":inputs, "checks":checks}
    out.write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps({"status":result["status"],"checks":len(checks),"failed":[x for x in checks if not x["pass"]],
                      "aggregator_sha256":result["aggregator_sha256"],"out":str(out)}))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
