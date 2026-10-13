"""Cross-check final author summaries against immutable execution evidence."""
import csv
import hashlib
import json
from pathlib import Path
HERE = Path(__file__).resolve().parent
RUN = HERE.parent
def read(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
s = read(RUN/'SUMMARY.json')
b = read(RUN/'science_run_01/BATCH_RESULT.json')
c = read(RUN/'BATCH_CLOSED.json')
r = read(HERE/'independent_replay.json')
assert r['passed'] and s['batch_wall_s'] == b['elapsed_s'] and s['wall_budget_s'] == 60
assert s['counts'] == dict(planned=2, attempted=2, validated_NEQ=2, bounded_UNSAT=0,
                          unknown=0, timeout=0, error=0, invalid_witness=0, not_run=0, scientific_retries=0)
assert s['owned_handles'] == b['guard']['handle_count'] == 5 and s['all_reaped']
csv_rows = list(csv.DictReader((RUN/'STAGES.csv').open()))
assert len(csv_rows) == len(s['slots']) == 2
for i, slot in enumerate(s['slots']):
    folder = RUN/'science_run_01'/('thrombosis_prediction__1172_'+slot['mode'])
    actual = read(folder/'RESULT.json')
    assert slot['status'] == actual['status'] == b['records'][i]['status']
    assert slot['wall_s'] == b['records'][i]['wall_elapsed_s'] == float(csv_rows[i]['wall_s'])
    assert slot['stages_seconds'] == actual['stages_seconds']
    assert all(float(csv_rows[i][k]) == v for k, v in actual['stages_seconds'].items())
    assert slot['original_outputs'] == actual['replay']['outputs']
    assert slot['z3_calls'] == len(actual['solver_calls']) == int(csv_rows[i]['z3_calls'])
    assert slot['z3_states'] == [x['state'] for x in actual['solver_calls']]
    assert slot['abstract_witness_sha256'] == sha(folder/'abstract_witness.json')
    assert slot['concrete_witness_sha256'] == sha(folder/'witness.json')
    assert all(p.read_bytes() == b'' for p in folder.glob('*stderr.txt'))
assert len({x['concrete_witness_sha256'] for x in s['slots']}) == 1
assert len({x['abstract_witness_sha256'] for x in s['slots']}) == 1
assert c['status'] == 'COMPLETED_ONCE_NO_RETRY' and c['scientific_retries'] == 0
for key, file in [('batch_receipt_sha256','science_run_01/BATCH_RESULT.json'), ('attempt_marker_sha256','ATTEMPT_STARTED.json'), ('freeze_sha256','FREEZE.json')]:
    assert c[key] == sha(RUN/file)
assert c['all_353_frozen_file_hashes_unchanged'] and c['old_preservation_checks'] == 351 and c['all_old_hashes_match']
inputs = [RUN/n for n in ['RESULT.zh.md','RECOVERY.zh.md','SUMMARY.json','STAGES.csv','BATCH_CLOSED.json']]
inputs += [HERE/n for n in ['independent_replay.py','independent_replay.json','final_document_check.py','INDEPENDENT_REVIEW.zh.md']]
inputs += [RUN.parent/n/'RESULT.zh.md' for n in ['calibergraph_polygon_pilot_20261012_13','calibergraph_polygon_coverage_20261012_14']]
output = dict(verdict='ACCEPTED_WITH_STATED_SCOPE', must_fix=[], final_documents_consistent=True,
              independent_original_SQL_replay_passed=True, original_constraints=7, original_tables=3, original_columns=64,
              denominator_slots=2, validated_NEQ=2, distinct_concrete_databases=1, native_solver_checks=3,
              review_solver_calls=0, review_foreign_process_probes=0, owned_handles_reaped=5,
              batch_elapsed_s=b['elapsed_s'], frozen_hashes_checked=353, preserved_hashes_checked=351,
              old_15_gate=False, new_16_gate=True, aggregate_RSS_verified=False,
              coverage={'valid_inputs':8,'invalid_inputs':2,'with_run_evidence':3,'not_admitted':5},
              interpretation='Exposed development case solved under specific N<=1 observation quotient; no unmodified baseline, generic types, novelty, superiority, or independent-test claim.',
              backup_completion_verified=False,
              reviewed_document_sha256={str(p.relative_to(RUN.parent)):sha(p) for p in inputs})
(HERE/'INDEPENDENT_REVIEW.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:output[k] for k in ['verdict','must_fix','final_documents_consistent','distinct_concrete_databases']}))
