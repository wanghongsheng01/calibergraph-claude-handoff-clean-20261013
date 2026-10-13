"""Independent JSON-only review of existing receipts. Never imports target code or executes SQL/SMT."""
import collections
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
NEW = ROOT / 'calibergraph_next_20261011_16'
OLD = ROOT / 'calibergraph_next_20261011_06'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
objsha = lambda x: hashlib.sha256(json.dumps(x, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
inputs = {}
def read(p):
    p = Path(p); inputs[str(p)] = sha(p)
    return json.loads(p.read_text())
def equal(a, b):
    return abs(a - b) < 1e-9
def total(rows, field):
    values = [r.get(field) for r in rows]
    return None if not values or any(v is None for v in values) else sum(values)

registry_path = ROOT / 'calibergraph_next_20261011_03/data/development_stratified.jsonl'
inputs[str(registry_path)] = sha(registry_path)
registry = [json.loads(x) for x in registry_path.read_text().splitlines() if x.strip()]
derived = read(NEW/'analysis/derived_once/derived_results.json')

def inspect(root, expected_n, drows, current):
    protocol = read(root/'protocols/generation_replay.registered.json')
    batch = read(root/'runs/diagnostic_01/batch_receipt.json' if current else root/'runs/generation_replay_01/batch_receipt.json')
    protocol_sha = sha(root/'protocols/generation_replay.registered.json')
    assert len(protocol['registered_cases']) == len(batch['slots']) == expected_n
    assert batch['status'] == 'REGISTERED_SEQUENCE_FINISHED' and not batch['violations']
    rows = []
    for i, slot in enumerate(protocol['registered_cases']):
        directory = root/('runs/diagnostic_01' if current else 'runs/generation_replay_01')/f'case_{i:02d}'
        worker = read(directory/'results.json'); sup = read(directory/'supervisor_receipt.json')
        rec = worker['record']; bs = batch['slots'][i]; dr = drows[i]
        assert rec['id'] == sup['case_id'] == bs['case_id'] == slot['id'] == dr['id']
        assert rec['case_index'] == sup['case_index'] == i
        assert worker['registered_slot'] == sup['registered_slot'] == bs['registered_slot'] == slot
        assert worker['protocol_sha256'] == batch['protocol_sha256'] == protocol_sha
        assert worker['input'] == protocol['input']
        assert sup['worker_results_sha256'] == sha(directory/'results.json')
        assert sup['worker_result_unmodified'] == worker and sup['worker_record_unmodified'] == rec
        assert sup['worker_exit_code'] == bs['worker_exit_code'] == 0
        assert worker['status'] == 'REGISTERED_GROUP_ATTEMPT_RETURNED'
        assert sup['status'] == bs['status'] == 'RETURNED' and sup['cleanup_wait_complete']
        assert not sup['violations'] and sup['stop_remainder'] is None
        assert len(rec['attempts']) == 1 and rec['attempts'][0]['attempt'] == 1
        assert rec['repeat_triggered'] is False
        case = registry[slot['source_case_index']]; src = case['source_record']
        assert rec['original_source_record'] == src and rec['source'] == case['source']
        assert rec['original_sql_sha256'] == case['original_sql_sha256'] == [hashlib.sha256(q.encode()).hexdigest() for q in src['pair']]
        assert rec['schema_sha256'] == case['schema_sha256'] == objsha(src['schema'])
        assert rec['constraint_sha256'] == case['constraint_sha256'] == objsha(src['constraint'])
        a = rec['attempts'][0]; stages = a['stages']
        assert a['exact_rows'] == {t:slot['exact_rows'] for t in src['schema']}
        cs = [s for s in stages if s['name']=='FULL_C_NONEMPTY_CHECK']
        qs = [s for s in stages if s['name']=='OFFICIAL_QUERY_SOLVER_CHECK']
        assert len(cs)==1 and cs[0]['answer']==a['full_C_nonempty']=='sat'
        assert cs[0]['status']=='RETURNED' and cs[0]['timeout_ms']==100
        calls = rec['solver_calls']; assert len(calls)==1+len(qs)
        for call, stage in zip(calls, cs+qs):
            assert call['stage']==stage['name']
            for field in ('actual_check_cpu_seconds','actual_check_wall_seconds','timeout_ms'):
                assert call[field]==stage[field]
        assert equal(sum(c['actual_check_cpu_seconds'] for c in calls),rec['solver_cumulative_cpu_seconds'])
        assert equal(sum(c['actual_check_wall_seconds'] for c in calls),rec['solver_cumulative_wall_seconds'])
        assert rec['query_solver_called'] == bool(qs)
        if qs:
            assert len(qs)==1 and qs[0]['answer']==a['raw_query_verdict'] and qs[0]['timeout_ms']==700
            assert qs[0]['status']=='RETURNED'
        else:
            assert a['raw_query_verdict'] is None and a['error_type']=='NotEquivalenceError'
            assert a['failure_stage']=='OFFICIAL_COMPARISON_FORMULA_ENCODING'
            assert 'line 53, in cmp_funcs' in a['traceback']
        parse=[s for s in stages if s['name'].startswith('OFFICIAL_PARSE_QUERY_')]
        analyze=[s for s in stages if s['name']=='OFFICIAL_ANALYZE_PARSE_AND_SCOPE_ENCODE']
        assert len(parse)==2 and all(s['status']=='RETURNED' for s in parse)
        assert len(analyze)==1 and analyze[0]['status']=='RETURNED'
        pc=total(parse,'cpu_seconds'); ac=total(analyze,'cpu_seconds'); qc=total(qs,'actual_check_cpu_seconds')
        qw=total(qs,'actual_check_wall_seconds')
        assert equal(a['exclusive_phase_cpu']['parse'],pc)
        assert equal(a['exclusive_phase_cpu']['scope_encode'],max(0,ac-pc))
        if current:
            assert a['exclusive_phase_cpu']['query_check']==qc
            assert a['exclusive_phase_cpu_status']['query_check']==('MEASURED' if qs else 'NOT_REACHED')
            assert a['comparison_formula_encode_status']==('REACHED_QUERY_CHECK' if qs else 'RAISED_BEFORE_QUERY_CHECK')
            assert a['comparison_formula_encode']['cpu_seconds']>=0
            assert rec['repeat_id']==slot['repeat_id']
            assert rec['source_and_structure_admission_cost']['status']=='RETURNED'
        assert dr['C_status']=='sat' and dr['query_verdict']==a['raw_query_verdict']
        assert dr['query_unknown_reason']==(qs[0].get('reason_unknown') if qs else None)
        assert dr['error_type']==a.get('error_type')
        assert dr['receipt_integrity_valid'] and not dr['integrity_problems']
        assert dr['costs']['query_check_cpu_seconds']['value']==qc
        assert dr['costs']['query_check_wall_seconds']['value']==qw
        assert dr['costs']['worker_wait4_usage']['cpu_seconds']==sup['worker_wait4_usage']['cpu_seconds']
        dc=dr['costs']
        assert dc['parse_cpu_seconds']['value']==pc
        assert dc['analyze_including_parse_cpu_seconds']['value']==ac
        assert dc['scope_encode_cpu_seconds']['value']==max(0,ac-pc)
        assert dc['comparison_formula_encode']['cost']==a.get('comparison_formula_encode')
        assert dc['attempt_cost']==a['attempt_cost'] and dc['cleanup_cost']==a['cleanup_cost']
        for actual,copied in zip(stages,dc['attempt_stages']):
            for key in ('name','status','cpu_seconds','wall_seconds','actual_check_cpu_seconds','actual_check_wall_seconds','answer','timeout_ms','error_type'):
                assert actual.get(key)==copied.get(key)
        assert len(stages)==len(dc['attempt_stages'])
        if current:
            assert dc['source_and_structure_admission']=={k:rec['source_and_structure_admission_cost'][k] for k in ('status','cpu_seconds','wall_seconds')}
            assert dc['source_exclusive_phase_cpu_status']==a['exclusive_phase_cpu_status']
            event_path=directory/'events.jsonl';inputs[str(event_path)]=sha(event_path)
            ev=[json.loads(line) for line in event_path.read_text().splitlines() if line.strip()]
            checks=[x for x in ev if x['event']=='SOLVER_CHECK_START']
            assert len(checks)==len(calls)
            assert [x['record']['active_stage'] for x in checks]==[x['stage'] for x in calls]
            assert ev[-1]['event']=='SINGLE_ATTEMPT_COMPLETE'
        control=a['contract_model_sanity']; control_checked=False
        if case['id'] in ('dev03_10','dev03_15'):
            rp=control['replay']; db=rp['concrete_database']
            assert control['status']=='RETURNED' and rp['status']=='REPLAY_DID_NOT_CONFIRM_DIFFERENCE'
            assert control['query_sat_witness'] is False and rp['query_sat_witness'] is False
            assert control['model_origin']==rp['model_origin']=='FULL_C_NONEMPTY_CHECK'
            assert control['scope']==rp['scope']=='C_MODEL_SANITY_ONLY_NOT_QUERY_SAT'
            assert db==control['witness']['all_physical_raw_values']
            assert rp['original_sql_sha256']==rec['original_sql_sha256']
            assert rp['original_sql_unchanged'] is True and rp['query_rewrites']==0
            assert rp['independent_full_C']['checked_clause_count']==len(src['constraint'])
            assert rp['full_C_status']=='COMPLETE_ORIGINAL_OPERATIONAL_C_TRUE'
            assert set(db)==set(src['schema'])
            for t, cols in src['schema'].items():
                assert len(db[t])==slot['exact_rows']
                assert all(set(row)==set(cols) and all(v is None or type(v) is int and -(2**31)<=v<2**31 for v in row.values()) for row in db[t])
            # Check saved finite values only: no SQL, solver, model generation or new database enumeration.
            if case['id']=='dev03_10':
                f=db['FRIENDSHIP']; l=db['LIKES']
                assert all(all(v is not None for v in r.values()) for r in f+l)
                assert len({(r['USER1_ID'],r['USER2_ID']) for r in f})==len(f)
                assert len({(r['USER_ID'],r['PAGE_ID']) for r in l})==len(l)
                assert all(x['USER1_ID']!=y['USER2_ID'] for x in f for y in f)
            else:
                q=db['QUERIES']; n=db['NPV']
                assert all(r['ID'] is not None and r['YEAR'] is not None for r in q+n)
                assert len({(r['ID'],r['YEAR']) for r in q})==len(q)
                assert len({(r['ID'],r['YEAR']) for r in n})==len(n)
                assert all(any(x['ID']==y['ID'] for y in n) for x in q)
                assert all(r['NPV'] is not None and r['NPV']>=0 for r in n)
            outputs=rp['original_sql_results']; assert len(outputs)==2
            assert collections.Counter(map(tuple,outputs[0]))==collections.Counter(map(tuple,outputs[1]))
            assert [x['name'] for x in rp['phase_costs']]==['INDEPENDENT_FULL_C_CHECK','SQLITE_LOAD_GENERATED_DATABASE','SQLITE_ORIGINAL_QUERY_0','SQLITE_ORIGINAL_QUERY_1']
            assert all(x['status']=='RETURNED' for x in rp['phase_costs'])
            control_checked=True
        else:
            assert control['status']=='NOT_ADMITTED' and 'replay' not in control
        assert 'replay' not in a and a['raw_query_verdict']!='sat'
        runtime=worker['runtime']['stages']; imp=[s for s in runtime if s['name']=='NATIVE_AND_OFFICIAL_IMPORT'][0]
        assert all(s['status']=='RETURNED' for s in runtime)
        assert len(runtime)==len(dc['runtime_stages'])
        for actual,copied in zip(runtime,dc['runtime_stages']):
            for key in ('name','status','cpu_seconds','wall_seconds'):
                assert actual.get(key)==copied.get(key)
        rows.append({'slot':i,'id':slot['id'],'source':case['id'],'N':slot['exact_rows'],'repeat':slot.get('repeat_id'),
                     'C':'sat','query':a['raw_query_verdict'],'unknown_reason':qs[0].get('reason_unknown') if qs else None,
                     'error':a.get('error_type'),'query_cpu_s':qc,'query_wall_s':qw,
                     'worker_wait4_cpu_s':sup['worker_wait4_usage']['cpu_seconds'],'worker_wall_s':sup['wall_seconds'],
                     'source_admission_cpu_s':rec.get('source_and_structure_admission_cost',{}).get('cpu_seconds'),
                     'runtime_import_cpu_s':imp['cpu_seconds'],'parse_cpu_s':pc,'scope_cpu_s':max(0,ac-pc),
                     'compare_cpu_s':(a.get('comparison_formula_encode') or {}).get('cpu_seconds'),
                     'C_check_cpu_s':cs[0]['actual_check_cpu_seconds'],'cleanup_cpu_s':a['cleanup_cost']['cpu_seconds'],
                     'saved_C_sanity_values_independently_checked':control_checked,
                     'C_sanity_is_not_query_sat':True,'query_replay_present':False})
    return rows

new=inspect(NEW,24,derived['current_round16']['rows'],True)
old=inspect(OLD,12,derived['historical_round06_separate_not_pooled']['rows'],False)
patterns=[]
for source in ('dev03_07','dev03_10','dev03_15','dev03_04'):
    group={(r['repeat'],r['N']):r for r in new if r['source']==source}
    for low,high in ((2,3),(2,4),(3,4)):
        yes=all(group[(rep,low)]['query']=='unsat' and group[(rep,high)]['query']=='unknown' and group[(rep,high)]['unknown_reason']=='timeout' for rep in (1,2))
        reported=next(p for p in derived['paired_diagnostics'] if p['source_case_id']==source)
        item=next(p for p in reported['comparisons'] if p['low_N']==low and p['high_N']==high)
        assert item['same_reason_repeated_cost_pattern']==yes
        patterns.append({'source':source,'low':low,'high':high,'same_timeout_both_repeats':yes})
report={'schema':'calibergraph.round16.independent_raw_results.v1','all_assertions_pass':True,
        'scope':'JSON-only validation of recorded receipts and saved witness values; no SQL/SMT/scientific rerun.',
        'current_rows':new,'historical_rows_separate':old,'patterns':patterns,
        'new_query_counts':dict(collections.Counter(r['query'] or 'NOT_REACHED' for r in new)),
        'new_C_sat_count':24,'new_C_sanity_checked':sum(r['saved_C_sanity_values_independently_checked'] for r in new),
        'worker_cpu_sum_s':sum(r['worker_wait4_cpu_s'] for r in new),
        'runtime_import_cpu_sum_s':sum(r['runtime_import_cpu_s'] for r in new),
        'query_cpu_sum_s_entered_only':sum(r['query_cpu_s'] for r in new if r['query_cpu_s'] is not None),
        'C_query_costs_not_added_to_worker_or_batch_cpu':True,'raw_inputs':inputs}
(OUT/'INDEPENDENT_RAW_RESULTS.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ('current_rows','historical_rows_separate','raw_inputs')},ensure_ascii=False,indent=2))
