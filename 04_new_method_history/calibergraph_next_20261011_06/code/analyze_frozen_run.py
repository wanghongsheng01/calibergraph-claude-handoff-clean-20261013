"""Read existing receipts only; never imports or runs a SQL/SMT backend."""
from pathlib import Path
import collections
import datetime
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / 'runs/generation_replay_01'
OUT = ROOT / 'analysis'
OUT.mkdir(exist_ok=True)
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
read = lambda p: json.loads(Path(p).read_text())
batch = read(RUN / 'batch_receipt.json')
protocol = read(ROOT / 'protocols/generation_replay.registered.json')
assert batch['registration_validated'] and len(batch['slots']) == 12
assert batch['registered_case_ids'] == [s['id'] for s in protocol['registered_cases']]
rows = []
all_checks = []
for i, slot in enumerate(batch['slots']):
    path = RUN / f'case_{i:02d}' / 'results.json'
    d = read(path)
    a = d['latest_attempt_snapshot']
    record = d['record']
    assert d['registered_slot'] == protocol['registered_cases'][i]
    checks = record['solver_calls']
    all_checks += checks
    control = a.get('contract_model_sanity', {})
    replay = control.get('replay', {})
    if replay:
        assert control['scope'] == replay['scope'] == 'C_MODEL_SANITY_ONLY_NOT_QUERY_SAT'
        assert control['query_sat_witness'] is False and replay['query_sat_witness'] is False
        assert replay['original_sql_unchanged'] and replay['query_rewrites'] == 0
        left, right = replay['original_sql_results']
        assert collections.Counter(map(tuple, left)) == collections.Counter(map(tuple, right))
        assert replay['status'] == 'REPLAY_DID_NOT_CONFIRM_DIFFERENCE'
    qcheck = [s for s in a['stages'] if s['name'] == 'OFFICIAL_QUERY_SOLVER_CHECK']
    rows.append({
        'case_id': slot['case_id'], 'source_case_id': d['registered_slot']['source_case_id'],
        'exact_rows_per_table': d['registered_slot']['exact_rows'],
        'supervisor_status': slot['status'], 'worker_exit_code': slot['worker_exit_code'],
        'record_status': record['status'], 'engineering_class': record['engineering_class'],
        'strict_class': record['strict_class'], 'full_C_nonempty': a['full_C_nonempty'],
        'query_verdict': a.get('raw_query_verdict'),
        'query_unknown_reason': qcheck[0].get('reason_unknown') if qcheck else None,
        'failure_stage': a.get('failure_stage'), 'error_type': a.get('error_type'),
        'error': a.get('error'), 'solver_calls': checks,
        'worker_wait4_cpu_seconds': slot['worker_wait4_usage']['cpu_seconds'],
        'worker_wait4_peak_rss_bytes': slot['worker_wait4_usage']['maxrss_bytes_darwin'],
        'worker_wall_from_main_seconds': d['worker_usage']['wall_from_main_seconds'],
        'runtime_phase_cpu_seconds': {s['name']: s['cpu_seconds'] for s in d['runtime']['stages']},
        'exclusive_query_phase_cpu_seconds': a['exclusive_phase_cpu'],
        'attempt_cpu_seconds': a['attempt_cost']['cpu_seconds'],
        'cleanup_cpu_seconds': a['cleanup_cost']['cpu_seconds'],
        'contract_model_sanity': {
            'status': control.get('status'), 'replay_status': replay.get('status'),
            'independent_full_C_status': replay.get('full_C_status'),
            'original_query_executions': len(replay.get('original_sql_results', [])),
            'output_row_counts': [len(x) for x in replay.get('original_sql_results', [])],
            'physical_rows_total': sum(len(x) for x in replay.get('concrete_database', {}).values()),
            'sqlite_version': replay.get('sqlite_version'), 'query_sat_witness': False,
            'costs': replay.get('phase_costs', []),
            'outer_control_costs': [s for s in a['stages'] if s['name'].startswith('C_MODEL_SANITY_')],
            'cost_note': 'Inner phase costs are contained in outer control stages; do not sum both.'
        },
        'input_evidence_sha256': sha(path)
    })

freeze = read(ROOT / 'protocols/generation_replay.freeze.json')
mismatches = [x for x in freeze['files'] if sha(x['path']) != x['sha256']]
assert not mismatches
old_expected = {
    'calibergraph_next_20261011_01/FIRST_ROUND_MANIFEST.json': 'e9f06b3491ba3fdd1f11eb86c29594bd34e75f41b59d9df75b174bd1075925be',
    'calibergraph_next_20261011_02/SECOND_ROUND_MANIFEST.json': 'bee973b3ee811c185e0aa56820c394c02442376104480fc2a265c674a242badc',
    'calibergraph_next_20261011_03/THIRD_ROUND_MANIFEST.json': '042ac37c195010557ba584e57de4e074a3bece282b33710abe305cb4def2e1a6',
}
old = [{'path': str(ROOT.parent / p), 'expected': h, 'actual': sha(ROOT.parent / p)} for p,h in old_expected.items()]
assert all(x['expected'] == x['actual'] for x in old)
query_checks = [x for x in all_checks if x['stage'] == 'OFFICIAL_QUERY_SOLVER_CHECK']
contract_checks = [x for x in all_checks if x['stage'] == 'FULL_C_NONEMPTY_CHECK']
counts = dict(collections.Counter(x['query_verdict'] or 'NO_QUERY_CHECK' for x in rows))
assert len(contract_checks) == 12 and len(query_checks) == 9
assert counts == {'unsat': 5, 'unknown': 4, 'NO_QUERY_CHECK': 3}
assert all(x['full_C_nonempty'] == 'sat' and x['supervisor_status'] == 'RETURNED' for x in rows)
summary = {
    'id': 'calibergraph-06-observed-readout-v1',
    'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'decision': 'NO_NEW_METHOD_NO_FAIR_SUPERIORITY', 'new_validated_mechanism': None,
    'scope': 'Exposed development feasibility and cost evidence; not independent test or natural business-bug evidence.',
    'registered_denominator': 12, 'registered_groups': 4, 'returned': 12,
    'all_C_checks_sat': 12, 'query_checks': len(query_checks), 'query_counts': counts,
    'unknown_reasons': dict(collections.Counter(x['query_unknown_reason'] for x in rows if x['query_verdict'] == 'unknown')),
    'zero_query_check_failure': {'count': 3, 'source_case_id': 'dev03_04',
        'stage': 'OFFICIAL_COMPARISON_FORMULA_ENCODING', 'type': 'NotEquivalenceError',
        'interpretation': 'No query SAT check/model/replay: not accepted as a separating witness or unbounded inequivalence proof.'},
    'query_SAT_models': 0, 'query_SAT_replayed_distinguishing_witnesses': 0,
    'contract_models_replayed': sum(x['contract_model_sanity']['original_query_executions'] == 2 for x in rows),
    'contract_model_original_query_executions': sum(x['contract_model_sanity']['original_query_executions'] for x in rows),
    'contract_model_physical_rows_total': sum(x['contract_model_sanity']['physical_rows_total'] for x in rows),
    'contract_model_replays_confirming_full_C': sum(x['contract_model_sanity']['independent_full_C_status'] == 'COMPLETE_ORIGINAL_OPERATIONAL_C_TRUE' for x in rows),
    'contract_model_distinguishing_outputs': 0,
    'formal_timing_scope': 'One attempt per slot. UNKNOWN timeout/memory limits are observations, not hardness evidence or baseline victory.',
    'query_check_cpu_seconds': sum(x['actual_check_cpu_seconds'] for x in query_checks),
    'contract_check_cpu_seconds': sum(x['actual_check_cpu_seconds'] for x in contract_checks),
    'query_check_wall_seconds': sum(x['actual_check_wall_seconds'] for x in query_checks),
    'worker_wait4_cpu_total_seconds': sum(x['worker_wait4_cpu_seconds'] for x in rows),
    'worker_peak_rss_bytes_max': max(x['worker_wait4_peak_rss_bytes'] for x in rows),
    'worker_wait4_cpu_seconds_max': max(x['worker_wait4_cpu_seconds'] for x in rows),
    'worker_wall_from_main_seconds_max': max(x['worker_wall_from_main_seconds'] for x in rows),
    'runtime_import_cpu_seconds_total': sum(x['runtime_phase_cpu_seconds']['NATIVE_AND_OFFICIAL_IMPORT'] for x in rows),
    'cpu_accounting': batch['cpu_accounting'], 'resource_violations': batch['violations'],
    'load_1min_min_max': [min(s['gate_probe']['load'][0] for s in batch['slots']), max(s['gate_probe']['load'][0] for s in batch['slots'])],
    'memory_available_percent_min_max': [min(s['gate_probe']['memory_available_percentage'] for s in batch['slots']), max(s['gate_probe']['memory_available_percentage'] for s in batch['slots'])],
    'checksums': {'registered_protocol': sha(ROOT/'protocols/generation_replay.registered.json'), 'freeze':sha(ROOT/'protocols/generation_replay.freeze.json'), 'batch_receipt':sha(RUN/'batch_receipt.json')},
    'postrun_integrity': {'frozen_files_rehashed': len(freeze['files']), 'mismatches': mismatches, 'old_manifest_identity_checks':old},
    'independent_final_test_accessed': False, 'automatic_retries': 0,
    'report_generation_scope': 'Read-only receipt aggregation and checksum verification; no scientific workload rerun; this postrun analysis is not included in measured supervisor CPU.',
    'rows': rows,
}
for filename,obj in [('observed_readout.json',summary),('postrun_integrity.json',summary['postrun_integrity'])]:
    target=OUT/filename
    assert not target.exists(), 'Do not overwrite a frozen readout.'
    target.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k not in ('rows','postrun_integrity')},ensure_ascii=False,indent=2))
