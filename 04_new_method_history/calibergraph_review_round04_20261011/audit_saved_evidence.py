"""Independent read-only audit of saved JSON/text evidence. No author imports,
SQL, SQL parser, SMT parser, solver, DBMS, or experiment is executed.
"""
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import re

AUTHOR = Path('/Users/loctek/Documents/Codex/2026-10-11/task-3/calibergraph_next_20261011_04')
REVIEW = Path(__file__).resolve().parent
reads = {}

def read(relative, mode):
    p = AUTHOR / relative
    assert p.is_file() and not p.is_symlink()
    b = p.read_bytes()
    reads[relative] = {'path': str(p), 'relative_path': relative,
        'sha256': hashlib.sha256(b).hexdigest(), 'bytes': len(b), 'review_mode': mode}
    return b.decode()

def jread(relative, mode='saved JSON structure and evidence reconciliation'):
    return json.loads(read(relative, mode))

def close(a, b):
    return abs(a-b) < 1e-8

def objsha(x):
    return hashlib.sha256(json.dumps(x, sort_keys=True, ensure_ascii=False,
        separators=(',', ':'), allow_nan=False).encode()).hexdigest()

def bag(rows):
    c = Counter(tuple(x) for x in rows)
    return [{'row': list(x), 'multiplicity': c[x]} for x in sorted(c,
        key=lambda x: json.dumps(list(x), ensure_ascii=False, separators=(',', ':')))]

def main():
    protocol = jread('protocols/boundary_pilot.registered.json')
    recovery = jread('protocols/boundary_pilot.recovery_registered.json')
    f1 = jread('protocols/execution_freeze.json', 'manifest metadata, full binding-map comparison; external targets not opened')
    f2 = jread('protocols/execution_recovery_freeze.json', 'manifest metadata, full binding-map comparison; external targets not opened')
    read('protocols/PROBLEM_EVIDENCE_PILOT.zh.md', 'manual full text review')
    amendment = jread('decisions/bootstrap_amendment_01.json')
    diagnosis_protocol = jread('decisions/stdlib_preexec_diagnosis.registered.json')
    diagnostics = [jread('audits/stdlib_preexec_diagnosis.json'), jread('audits/stdlib_nice_context_diagnosis.json')]
    for name in ['pilot_common.py', 'concrete_boundary_worker.py', 'official_boundary_worker.py',
                 'official_boundary_backend.py', 'official_contract_admission.py', 'pilot_supervisor.py',
                 'pilot_supervisor_recovery.py']:
        read('code/' + name, 'manual full source or exact full-source diff review; source never imported/executed')
    original_code = (AUTHOR/'code/pilot_supervisor.py').read_text()
    recovery_code = (AUTHOR/'code/pilot_supervisor_recovery.py').read_text()
    assert original_code.replace('"prior_preflight_cpu_charge_seconds": 1.0,',
        '"prior_preflight_cpu_charge_seconds": 3.408329,', 1) == recovery_code
    pchanges = {k for k in protocol.keys() | recovery.keys() if protocol.get(k) != recovery.get(k)}
    assert pchanges == {'status', 'repeat_policy', 'registered_utc', 'prior_charge_cpu_seconds',
                        'execution_context', 'bootstrap_exception'}
    m1 = {x['path']: x['sha256'] for x in f1['files']}
    m2 = {x['path']: x['sha256'] for x in f2['files']}
    assert all(m2.get(k) == v for k, v in m1.items())
    assert f2['previous_freeze_sha256'] == reads['protocols/execution_freeze.json']['sha256']
    for mapping in (m1, m2):
        for path, digest in mapping.items():
            rel = str(Path(path).relative_to(AUTHOR)) if Path(path).is_relative_to(AUTHOR) else None
            if rel in reads:
                assert reads[rel]['sha256'] == digest, (rel, 'freeze mismatch')
    batches = {}
    files = {}
    for bn in ['boundary_pilot_01', 'boundary_pilot_02']:
        for p in sorted((AUTHOR/'runs'/bn).rglob('*')):
            if not p.is_file():
                continue
            rel = str(p.relative_to(AUTHOR))
            t = read(rel, 'full saved text/JSON structural scan, artifact hash and numerical reconciliation; no scientific rerun')
            if p.suffix == '.json':
                files[rel] = json.loads(t)
            elif p.suffix == '.jsonl':
                files[rel] = [json.loads(line) for line in t.splitlines() if line.strip()]
            else:
                files[rel] = t
        batches[bn] = files['runs/'+bn+'/batch_receipt.json']
    old, new = batches['boundary_pilot_01'], batches['boundary_pilot_02']
    expected_slots = [(k, n) for n in range(1,6) for k in ['concrete','official']]
    assert [(x['kind'], x['exact_rows']) for x in recovery['registered_cases']] == expected_slots
    assert old['registered_denominator'] == new['registered_denominator'] == 10
    assert old['registered_case_ids'] == new['registered_case_ids'] == [x['id'] for x in recovery['registered_cases']]
    assert [x['status'] for x in old['slots']] == ['MONITOR_OR_LAUNCH_EXCEPTION'] + ['NOT_RUN']*9
    first = files['runs/boundary_pilot_01/case_00/supervisor_receipt.json']
    assert first['monitor_error']['type'] == 'SubprocessError'
    assert first['monitor_error']['message'] == 'Exception occurred in preexec_fn.'
    assert first['observed_stage_sequence'] == [] and first['sample_count'] == 0
    assert not (AUTHOR/'runs/boundary_pilot_01/case_00/events.jsonl').exists()
    assert not (AUTHOR/'runs/boundary_pilot_01/case_00/progress.json').exists()
    assert old['finished_utc'] < amendment['utc'] == recovery['registered_utc'] < f2['utc'] < new['created_utc']
    assert diagnosis_protocol['recovery_authorized_by_this_diagnosis'] is False
    assert diagnosis_protocol['binding']['batch_sha256'] == reads['runs/boundary_pilot_01/batch_receipt.json']['sha256']
    assert new['protocol_sha256'] == reads['protocols/boundary_pilot.recovery_registered.json']['sha256']
    assert new['freeze_sha256'] == reads['protocols/execution_recovery_freeze.json']['sha256']
    assert new['supervisor_sha256'] == reads['code/pilot_supervisor_recovery.py']['sha256']
    assert new['violations'] == [] and new['halt_reason'] is None
    assert all(x['status'] == 'RETURNED' for x in new['slots'])
    rows = []
    worker_cpu = 0.0
    expected_source = None
    for i, (kind, n) in enumerate(expected_slots):
        base = f'runs/boundary_pilot_02/case_{i:02}'
        result = files[base+'/results.json']
        receipt = files[base+'/supervisor_receipt.json']
        rec = result.get('record', result)
        source = rec['original_source_record']
        if expected_source is None:
            expected_source = source
        assert source == expected_source
        assert [hashlib.sha256(s.encode()).hexdigest() for s in source['pair']] == recovery['original_sql_sha256']
        assert objsha(source['schema']) == recovery['schema_sha256']
        assert objsha(source['constraint']) == recovery['constraint_sha256']
        assert source['constraint'] == [{'primary':[{'value':'COURSES__STUDENT'}]}]
        assert receipt['worker_results_sha256'] == reads[base+'/results.json']['sha256']
        assert receipt['worker_result_unmodified'] == result
        assert receipt['violations'] == [] and receipt['stop_remainder'] is None
        assert receipt['worker_exit_code'] == 0 and receipt['status'] == 'RETURNED'
        use = receipt['worker_wait4_usage']
        assert close(use['cpu_seconds'], use['user_cpu_seconds']+use['system_cpu_seconds'])
        assert use['cpu_seconds'] < 3 and use['maxrss_bytes_darwin'] < 268435456
        assert receipt['wall_seconds'] < 4
        worker_cpu += use['cpu_seconds']
        row = {'id': rec['id'], 'kind':kind, 'N':n, 'worker_cpu_seconds':use['cpu_seconds'],
            'worker_lifecycle_wall_seconds':receipt['wall_seconds'],
            'wait4_maxrss_bytes':use['maxrss_bytes_darwin']}
        events = files[base+'/events.jsonl']
        if kind == 'concrete':
            assert rec['runtime']['nice'] >= 15
            out = {}
            for key, fixture in rec['fixtures'].items():
                inp = fixture['input_rows']
                assert len(inp) == n and len({x[1] for x in inp}) == n
                assert all(type(x[1]) is str for x in inp)
                assert all(x[0] is None for x in inp) if key == 'all_null_class' else all(x[0] == 'same_nonnull_class' for x in inp)
                bags = []
                for qi, query in enumerate(fixture['queries']):
                    assert query['original_sql'] == source['pair'][qi]
                    assert query['bag'] == bag(query['rows']) and query['row_count'] == len(query['rows'])
                    bags.append(query['bag'])
                assert fixture['observed_bag_equal'] == (bags[0] == bags[1])
                expected = [[], []] if n < 5 else ([[[None]], []] if key == 'all_null_class' else [[['same_nonnull_class']], [['same_nonnull_class']]])
                assert [q['rows'] for q in fixture['queries']] == expected
                out[key] = {'outputs':expected, 'bag_equal':fixture['observed_bag_equal']}
            assert [x[1] for x in rec['fixtures']['all_null_class']['input_rows']] == [x[1] for x in rec['fixtures']['nonnull_class_control']['input_rows']]
            row['fixtures'] = out
            row['sqlite_version'] = rec['runtime']['sqlite_version']
            assert sum(x['event'] == 'ORIGINAL_QUERY_COMPLETE' for x in events) == 4
        else:
            assert len(rec['attempts']) == 1
            attempt = rec['attempts'][0]
            assert rec['engineering_class'] == rec['strict_class'] == 'INCONCLUSIVE'
            assert attempt['full_C_nonempty'] == 'sat' and attempt['raw_query_verdict'] is None
            assert attempt['failure_stage'] == 'OFFICIAL_ANALYZE_PARSE_AND_SCOPE_ENCODE'
            assert attempt['error_type'] == 'CorrelatedQueryError'
            assert [x['stage'] for x in rec['solver_calls']] == ['FULL_C_NONEMPTY_CHECK']
            assert sum(x['event'] == 'SOLVER_CHECK_START' for x in events) == 1
            assert sum(x['event'] == 'SOLVER_CHECK_END' for x in events) == 1
            assert attempt['exact_shape_semantics']['is_up_to_bound'] is False
            raw = attempt['C_witness']['all_physical_raw_values']['COURSES']
            assert len(raw) == n and len({x['STUDENT'] for x in raw}) == n
            assert all(type(x['STUDENT']) is int for x in raw)
            for name, artifact in attempt['evidence_artifacts'].items():
                assert artifact['sha256'] == reads[base+'/'+name]['sha256']
            assertion_text = files[base+'/contract_assertions.smt2']
            live = re.findall(r'\(assert \(not \(DELETED (t\d+)\)\)\)', assertion_text)
            assert len(live) == n and len(set(live)) == n
            assert all(files[base+f'/parsed_ast_{k}.json'] == attempt['parsed_asts'][k-1] for k in [1,2])
            assert not (AUTHOR/base/'query_assertions.smt2').exists()
            row.update(C_sat=True, query_solver_calls=0, raw_class=rec['engineering_class'],
                derived_class='FRONTEND_CORRELATED_SUBQUERY_REJECTION', exact_live_assertions=len(live),
                C_check_wall_seconds=rec['solver_calls'][0]['actual_check_wall_seconds'])
        rows.append(row)
    ac = new['cpu_accounting']
    subtotal = sum(ac[k] for k in ['parent_user_cpu_seconds','parent_system_cpu_seconds',
        'all_reaped_children_user_cpu_seconds','all_reaped_children_system_cpu_seconds'])
    assert close(subtotal, ac['supervisor_plus_reaped_cpu_seconds'])
    assert close(subtotal+recovery['prior_charge_cpu_seconds']+recovery['tail_reserve_cpu_seconds'], ac['conservative_charged_total_seconds'])
    assert close(sum(amendment['charge_decomposition'].values()), recovery['prior_charge_cpu_seconds'])
    assert close(amendment['charge_decomposition']['failed_batch_conservative_including_original_preflight_and_tail'], old['cpu_accounting']['conservative_charged_total_seconds'])
    assert sum(x['cpu_seconds_snapshot'] for x in diagnostics) < 1.0
    assert f2['preflight_cpu_snapshot_seconds'] < 1.0
    gates = [x['gate_probe'] for x in new['slots']]
    assert all(x['admitted'] and x['load'][0] <= 4 and x['memory_available_percentage'] >= 25 for x in gates)
    author_report = read('FOURTH_ROUND_REPORT.zh.md', 'manual full-text claim audit against pinned saved evidence')
    author_recount = jread('analyses/pilot_recount.json')
    stage_decision = jread('decisions/stage_decision.json')
    assert reads['FOURTH_ROUND_REPORT.zh.md']['sha256'] == '67699010beb50164542b16d821dc7a631b097f03716ddeeb00a2a05342afb859'
    assert reads['analyses/pilot_recount.json']['sha256'] == '3629e64101ce66f2f47e2b8a9762890a470902c400fc67a699745c9dd1df44b7'
    assert stage_decision['report_sha256'] == reads['FOURTH_ROUND_REPORT.zh.md']['sha256']
    assert stage_decision['recount_sha256'] == reads['analyses/pilot_recount.json']['sha256']
    assert stage_decision['hypothesis'] is None and stage_decision['overall_research_terminated'] is False
    assert author_recount['registered_slots'] == 10 and author_recount['official_C_checks'] == 5 and author_recount['official_query_checks'] == 0
    assert author_recount['actual_original_SQL_query_executions'] == 20
    assert author_recount['actual_concrete_SQL_pair_executions'] == 10
    assert len(author_recount['rows']) == len(rows)
    assert close(author_recount['worker_cpu_sum_seconds'], worker_cpu)
    assert author_recount['recovery_accounting'] == ac
    for ours, theirs in zip(rows, author_recount['rows']):
        assert (ours['id'], ours['kind'], ours['N']) == (theirs['id'], theirs['kind'], theirs['N'])
        assert ours['worker_cpu_seconds'] == theirs['worker_cpu_seconds']
        assert ours['worker_lifecycle_wall_seconds'] == theirs['lifecycle_wall_seconds']
        assert ours['wait4_maxrss_bytes'] == theirs['worker_peak_rss_bytes']
        if ours['kind'] == 'concrete':
            assert ours['fixtures'] == theirs['fixtures']
        else:
            assert ours['raw_class'] == theirs['raw_engineering_class']
            assert ours['derived_class'] == theirs['derived_class']
            assert theirs['raw_query_verdict'] is None and theirs['C_result'] == 'sat'
    assert '首次失败后、首次科学执行前' in author_report
    assert '数值字段和实际计账是3.408329' in author_report
    summary = {
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'audit_scope':'Saved evidence hashes, JSON consistency, bag/PK recount and arithmetic only; no SQL/parser/solver rerun. No reserve/test or credentials opened.',
        'status':'ALL_SAVED_EVIDENCE_RECONCILIATIONS_PASSED',
        'author_report_sha256':reads['FOURTH_ROUND_REPORT.zh.md']['sha256'],
        'author_recount_sha256':reads['analyses/pilot_recount.json']['sha256'],
        'registered_scientific_slots':10, 'failed_bootstrap_launches':1,
        'failed_bootstrap_worker_exec':0, 'recovery_completed_slots':10,
        'concrete_original_pair_executions':10, 'concrete_original_query_executions':20,
        'official_C_checks':5, 'official_query_checks':0,
        'unchanged_previous_freeze_bindings':len(m1), 'recovery_freeze_bindings':len(m2),
        'source_provenance_limit':'Original source repeated in saved workers, byte/schema/C bindings checked. Original frozen JSONL and upstream source repository were not independently opened.',
        'cost':{'prior_conservative_seconds':recovery['prior_charge_cpu_seconds'],
            'current_parent_and_all_reaped_seconds':subtotal, 'worker_wait4_cpu_sum_seconds':worker_cpu,
            'current_monitor_children_cpu_seconds':ac['all_reaped_children_user_cpu_seconds']+ac['all_reaped_children_system_cpu_seconds']-worker_cpu,
            'current_parent_cpu_seconds':ac['parent_user_cpu_seconds']+ac['parent_system_cpu_seconds'],
            'tail_reserve_seconds':recovery['tail_reserve_cpu_seconds'],
            'conservative_total_seconds':ac['conservative_charged_total_seconds'],
            'charged_not_measured':True},
        'resource_summary':{'max_worker_cpu_seconds':max(x['worker_cpu_seconds'] for x in rows),
            'max_worker_lifecycle_wall_seconds':max(x['worker_lifecycle_wall_seconds'] for x in rows),
            'max_wait4_rss_bytes':max(x['wait4_maxrss_bytes'] for x in rows),
            'max_slot_start_load1':max(x['load'][0] for x in gates),
            'min_slot_start_memory_available_percentage':min(x['memory_available_percentage'] for x in gates),
            'saved_violations':[]},
        'rows':rows,
        'minor_discrepancy':'Frozen recovery measurement_note still says 1.0s prior; numerical policy/accounting correctly says 3.408329. Preserve raw log and clarify in author narrative.',
        'reviewed_author_files':list(reads.values())}
    (REVIEW/'saved_evidence_audit.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k not in ['reviewed_author_files','rows']},ensure_ascii=False,indent=2))
    print('reviewed_author_files',len(reads))

if __name__ == '__main__':
    main()
