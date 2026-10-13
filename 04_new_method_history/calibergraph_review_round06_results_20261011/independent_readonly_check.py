"""Independent round-06 artifact audit. Standard library only; no target imports or SQL/SMT.

Reads only round06, the previous static review, and exact frozen paths authorized
for hash-only reads. Evaluates saved concrete values against the seven published
INT contract clauses; never generates new models or executes queries.
"""
from pathlib import Path
import collections
import hashlib
import json
import math

ROOT = Path(__file__).resolve().parent.parent
AUTHOR = ROOT / 'calibergraph_next_20261011_06'
OUT = Path(__file__).resolve().parent
PRE = ROOT / 'calibergraph_review_round06_preexec_20261011' / 'followup_01'
inputs = {}
checks = []

def read(path):
    p = Path(path)
    raw = p.read_bytes()
    inputs[str(p)] = {'path': str(p), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
    return raw

def load(path):
    return json.loads(read(path))

def lines(path):
    return [json.loads(x) for x in read(path).splitlines() if x.strip()]

def sha(path):
    return hashlib.sha256(read(path)).hexdigest()

def objsha(x):
    return hashlib.sha256(json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()

def test(label, value, detail=None):
    checks.append({'check': label, 'passed': bool(value), **({'detail': detail} if detail is not None else {})})

def near(a, b):
    return math.isclose(a, b, rel_tol=1e-10, abs_tol=1e-10)

manifest = load(AUTHOR/'SIXTH_ROUND_AUTHOR_MANIFEST.json')
test('author manifest identity', sha(AUTHOR/'SIXTH_ROUND_AUTHOR_MANIFEST.json') == 'ab22d1fcb9ec4964441c6b6f5b316b23a3978c094298b9d25bbc26d17a3e8b57')
test('author snapshot has 115 entries', len(manifest['files']) == 115)
for f in manifest['files']:
    p = Path(f['path'])
    assert p.is_relative_to(AUTHOR)
    test('author snapshot bytes: '+f['relative_path'], sha(p) == f['sha256'] and p.stat().st_size == f['bytes'])
freeze = load(AUTHOR/'protocols/generation_replay.freeze.json')
test('freeze entries exactly 880 unique paths', len(freeze['files']) == len({x['path'] for x in freeze['files']}) == 880)
for f in freeze['files']:
    # Exact paths only: no glob, sibling reads, imports, or interpretation.
    test('frozen hash: '+f['path'], sha(f['path']) == f['sha256'])
post = load(AUTHOR/'analysis/postrun_integrity.json')
for f in post['old_manifest_identity_checks']:
    test('historical manifest hash: '+f['path'], sha(f['path']) == f['expected'] == f['actual'])
allowed = load(PRE/'allowed_finalization_changes.json')
for p in PRE.iterdir():
    if p.is_file():
        read(p)
common = read(AUTHOR/'code/generation_common.py')
test('single execution-enable transition', common.count(b'EXECUTION_ENABLED = True') == 1 and hashlib.sha256(common.replace(b'EXECUTION_ENABLED = True', b'EXECUTION_ENABLED = False')).hexdigest() == allowed['common_reviewed_sha256'])
test('enabled common exact expected hash', hashlib.sha256(common).hexdigest() == allowed['common_enabled_expected_sha256'])
draft = load(AUTHOR/'protocols/generation_replay.draft.json')
protocol = load(AUTHOR/'protocols/generation_replay.registered.json')
norm = lambda x: {k:v for k,v in x.items() if k not in ('status','registered_utc')}
test('only protocol allowed finalization values changed', norm(draft) == norm(protocol) and objsha(norm(protocol)) == allowed['protocol_sha256_excluding_status_and_registered_utc'])
test('truthful timestamp order', protocol['registered_utc'] < freeze['created_utc'])
reviewed = load(PRE/'reviewed_input_hashes.json')
# Traverse only already-reviewed hash entries, without opening unexpected paths.
def hash_entries(x):
    if isinstance(x, dict):
        if 'path' in x and 'sha256' in x:
            yield x
        for v in x.values():
            yield from hash_entries(v)
    elif isinstance(x, list):
        for v in x:
            yield from hash_entries(v)
for entry in hash_entries(reviewed):
    p = Path(entry['path'])
    if p.parent == AUTHOR/'code' and p.name != 'generation_common.py':
        test('execution source identical to static review: '+p.name, sha(p) == entry['sha256'])

run = AUTHOR/'runs/generation_replay_01'
batch = load(run/'batch_receipt.json')
observed = load(AUTHOR/'analysis/observed_readout.json')
sources = {x['id']:x for x in lines(AUTHOR/'data/selected_source_groups.jsonl')}
test('batch identity', sha(run/'batch_receipt.json') == '16ca6e4d6e056e97afe764754eb3091f5d374fea2edc1ca53271ecad35538029')
test('report identity', sha(AUTHOR/'analysis/RESULTS.zh.md') == '80c6a8ca5ccb1a2f2bac4e8f8b452a4da990823f4b746701b639003d70abfe4a')
test('registered denominator and order preserved', batch['registered_denominator'] == batch['planned_denominator'] == len(batch['slots']) == 12 and [s['registered_slot'] for s in batch['slots']] == protocol['registered_cases'])
test('protocol precedes execution', protocol['registered_utc'] < batch['created_utc'] < batch['finished_utc'])
test('freeze anchors analytic controls', any(x['path'] == str(AUTHOR/'protocols/ANALYTIC_CONTROLS.zh.md') for x in freeze['files']))
counts = collections.Counter()
unknown = collections.Counter()
all_calls, rows, replays = [], [], []
workers, monitors = [], []
last_end = None
for i, slot in enumerate(batch['slots']):
    d = run/f'case_{i:02d}'
    result = load(d/'results.json')
    receipt = load(d/'supervisor_receipt.json')
    events = lines(d/'events.jsonl')
    se = lines(d/'supervisor_events.jsonl')
    progress = load(d/'progress.json')
    record = result['record']
    test(f'{i} one attempt', len(record['attempts']) == 1 and record['attempts'][0]['attempt'] == 1 and record['repeat_triggered'] is False)
    a = record['attempts'][0]
    test(f'{i} exact slot identity', result['registered_slot'] == receipt['registered_slot'] == slot['registered_slot'] and record['case_index'] == i and record['id'] == slot['case_id'])
    test(f'{i} original source preserved', record['original_source_record'] == sources[record['source_case_id']]['source_record'])
    src = record['original_source_record']
    test(f'{i} SQL schema C hashes', record['original_sql_sha256'] == [hashlib.sha256(x.encode()).hexdigest() for x in src['pair']] and record['schema_sha256'] == objsha(src['schema']) and record['constraint_sha256'] == objsha(src['constraint']))
    test(f'{i} result hash and redundant copies', receipt['worker_results_sha256'] == sha(d/'results.json') and receipt['worker_result_unmodified'] == result and receipt['worker_record_unmodified'] == record and result['latest_attempt_snapshot'] == a)
    test(f'{i} returned and reaped', slot['status'] == receipt['status'] == 'RETURNED' and receipt['worker_exit_code'] == 0 and receipt['cleanup_wait_complete'] and not receipt['violations'] and receipt['stop_remainder'] is None)
    calls = record['solver_calls']; all_calls.extend(calls)
    nquery = sum(x['stage'] == 'OFFICIAL_QUERY_SOLVER_CHECK' for x in calls)
    cchecks = [x for x in a['stages'] if x['name'] == 'FULL_C_NONEMPTY_CHECK']
    qchecks = [x for x in a['stages'] if x['name'] == 'OFFICIAL_QUERY_SOLVER_CHECK']
    test(f'{i} C SAT and complete admission stages', len(cchecks) == 1 and cchecks[0]['answer'] == a['full_C_nonempty'] == 'sat' and any(x['name'] == 'FULL_C_SAT_MODEL_VALIDATION' and x['status'] == 'RETURNED' for x in a['stages']) and next(x for x in a['stages'] if x['name']=='FULL_ORIGINAL_IC_ADMISSION')['original_clause_count'] == len(src['constraint']))
    test(f'{i} solver check events and final progress', sum(x['event']=='SOLVER_CHECK_START' for x in events) == sum(x['event']=='SOLVER_CHECK_END' for x in events) == len(calls) == progress['check_count'] == receipt['final_progress']['check_count'] and not progress['solver_check_active'])
    test(f'{i} final event record', events[-1]['event'] == 'SINGLE_ATTEMPT_COMPLETE' and events[-1]['record'] == record)
    test(f'{i} exact N declaration', a['exact_rows'] == {t:slot['registered_slot']['exact_rows'] for t in src['schema']})
    verdict = a.get('raw_query_verdict')
    reason = next((x.get('reason_unknown') for x in qchecks if x.get('answer')=='unknown'),None)
    counts[verdict or 'NO_QUERY_CHECK'] += 1
    if reason: unknown[reason] += 1
    test(f'{i} verdict matches actual query checks', (len(qchecks)==nquery==1 and qchecks[0]['answer']==verdict) if verdict else len(qchecks)==nquery==0)
    if not verdict:
        test(f'{i} comparison exception never promoted', a.get('error_type') == 'NotEquivalenceError' and a.get('failure_stage') == 'OFFICIAL_COMPARISON_FORMULA_ENCODING' and record['strict_class'] == 'INCONCLUSIVE')
    sanity = a['contract_model_sanity']
    replay = sanity.get('replay')
    if replay:
        db = replay['concrete_database']; n = slot['registered_slot']['exact_rows']
        test(f'{i} concrete data exact N and typed shape', set(db) == set(src['schema']) and all(len(data)==n and all(set(row)==set(src['schema'][table]) and all(v is None or type(v) is int and -2147483648<=v<=2147483647 for v in row.values()) for row in data) for table,data in db.items()))
        test(f'{i} complete saved model copied without changes', db == sanity['witness']['all_physical_raw_values'] == sanity['witness']['decoded_values'])
        # Independently spell out these two sources' full contracts, including
        # the official Cartesian inequality and strict non-NULL FK rule.
        def unique_key(table, columns):
            tuples = [tuple(r[c] for c in columns) for r in db[table]]
            return len(set(tuples)) == len(tuples) and all(None not in x for x in tuples)
        if record['source_case_id']=='dev03_10':
            passed_clauses = [unique_key('FRIENDSHIP',['USER1_ID','USER2_ID']), unique_key('LIKES',['USER_ID','PAGE_ID']), all(x['USER1_ID'] is not None and y['USER2_ID'] is not None and x['USER1_ID'] != y['USER2_ID'] for x in db['FRIENDSHIP'] for y in db['FRIENDSHIP'])]
        elif record['source_case_id']=='dev03_15':
            passed_clauses = [unique_key('NPV',['ID','YEAR']), unique_key('QUERIES',['ID','YEAR']), all(q['ID'] is not None and any(n['ID'] is not None and n['ID']==q['ID'] for n in db['NPV']) for q in db['QUERIES']), all(n['NPV'] is not None and n['NPV']>=0 for n in db['NPV'])]
        else:
            raise ValueError('unexpected replay source')
        test(f'{i} independently recomputed every saved C clause', len(passed_clauses)==len(src['constraint']) and all(passed_clauses))
        bags = [collections.Counter(tuple(x) for x in output) for output in replay['original_sql_results']]
        test(f'{i} saved SQL output bag equality', bags[0] == bags[1] and replay['status']=='REPLAY_DID_NOT_CONFIRM_DIFFERENCE')
        test(f'{i} original SQL identity and 2 recorded executions', replay['original_sql_sha256']==record['original_sql_sha256'] and replay['original_sql_unchanged'] and replay['query_rewrites']==0 and len([x for x in replay['phase_costs'] if x['name'].startswith('SQLITE_ORIGINAL_QUERY_') and x['status']=='RETURNED'])==2)
        test(f'{i} C sanity not query SAT', sanity['model_origin']==replay['model_origin']=='FULL_C_NONEMPTY_CHECK' and sanity['scope']==replay['scope']=='C_MODEL_SANITY_ONLY_NOT_QUERY_SAT' and sanity['query_sat_witness'] is replay['query_sat_witness'] is False and 'replay' not in a)
        replays.append({'case':record['id'],'clause_checks':passed_clauses,'physical_rows':sum(len(x) for x in db.values()),'saved_output_rows':[len(x) for x in replay['original_sql_results']],'sqlite_version_recorded':replay['sqlite_version'],'input_null_cells':sum(v is None for x in db.values() for r in x for v in r.values()),'output_null_cells':sum(v is None for x in replay['original_sql_results'] for r in x for v in r),'query_sat_witness':False})
    else:
        test(f'{i} non-INT source replay refused', sanity['status']=='NOT_ADMITTED')
    mon = [x for x in se if x['event']=='MONITOR']; monitors.extend(mon)
    test(f'{i} monitor count and resources', len(mon)==receipt['sample_count'] and all(x['load'][0]<=4 and x['group']['rss_bytes']<=268435456 and x['group']['cpu_seconds']<3 for x in mon))
    start, finish = se[0],se[-1]
    test(f'{i} serial worker sequence', start['event']=='WORKER_STARTED' and finish['event']=='WORKER_FINISHED' and (last_end is None or last_end < start['monotonic']))
    last_end = finish['monotonic']
    u = receipt['worker_wait4_usage']; workers.append((u,receipt,result))
    test(f'{i} completed worker limits', near(u['cpu_seconds'],u['user_cpu_seconds']+u['system_cpu_seconds']) and u['cpu_seconds']<=3 and u['maxrss_bytes_darwin']<=268435456 and receipt['wall_seconds']<=4 and a['solver_cumulative_wall_seconds']<=2)
    o = observed['rows'][i]
    test(f'{i} author row matches raw evidence', o['case_id']==record['id'] and o['query_verdict']==verdict and o['solver_calls']==calls and o['input_evidence_sha256']==sha(d/'results.json') and o['worker_wait4_cpu_seconds']==u['cpu_seconds'])
    parse_cpu = sum(x['cpu_seconds'] for x in a['stages'] if x['name'] in ('OFFICIAL_PARSE_QUERY_0','OFFICIAL_PARSE_QUERY_1'))
    analyze_cpu = next(x['cpu_seconds'] for x in a['stages'] if x['name']=='OFFICIAL_ANALYZE_PARSE_AND_SCOPE_ENCODE')
    test(f'{i} exclusive parse and scope costs', near(a['exclusive_phase_cpu']['parse'],parse_cpu) and near(a['exclusive_phase_cpu']['scope_encode'],analyze_cpu-parse_cpu))
    test(f'{i} author phase accounting equals raw nested records', o['runtime_phase_cpu_seconds']=={x['name']:x['cpu_seconds'] for x in result['runtime']['stages']} and o['exclusive_query_phase_cpu_seconds']==a['exclusive_phase_cpu'] and o['attempt_cpu_seconds']==a['attempt_cost']['cpu_seconds'] and o['cleanup_cpu_seconds']==a['cleanup_cost']['cpu_seconds'])
    test(f'{i} original replay nested costs preserved', o['contract_model_sanity']['costs']==(replay.get('phase_costs',[]) if replay else []) and o['contract_model_sanity']['outer_control_costs']==[{k:x[k] for k in ('name','status','wall_seconds','cpu_seconds')} for x in a['stages'] if x['name'] in ('C_MODEL_SANITY_RAW_EXPORT','C_MODEL_SANITY_FULL_C_AND_ORIGINAL_SQL_REPLAY')])
    rows.append({'slot':i,'case':record['id'],'C':a['full_C_nonempty'],'query_checks':nquery,'verdict':verdict,'reason':reason,'failure_stage':a.get('failure_stage'),'error_type':a.get('error_type'),'worker_cpu':u['cpu_seconds'],'worker_peak_rss':u['maxrss_bytes_darwin'],'worker_wall_from_main':result['worker_usage']['wall_from_main_seconds'],'lifecycle_wall':receipt['wall_seconds']})

acct = batch['cpu_accounting']
measured = sum(acct[k] for k in ('parent_user_cpu_seconds','parent_system_cpu_seconds','all_reaped_children_user_cpu_seconds','all_reaped_children_system_cpu_seconds'))
test('CPU accounting no double charge', near(measured,acct['supervisor_plus_reaped_cpu_seconds']) and near(measured+10+0.2,acct['conservative_charged_total_seconds']) and acct['conservative_charged_total_seconds']<=60)
batch_events = lines(run/'batch_events.jsonl')
gates = [x['observation'] for x in batch_events if x['event']=='SLOT_GATE_PROBE']
test('12 successful load and memory gates', len(gates)==12 and all(x['admitted'] and x['status']=='RETURNED' and x['load'][0]<=4 and x['memory_available_percentage']>=25 for x in gates))
totals = {'registered':12,'returned':sum(s['status']=='RETURNED' for s in batch['slots']),'C_checks':sum(x['stage']=='FULL_C_NONEMPTY_CHECK' for x in all_calls),'query_checks':sum(x['stage']=='OFFICIAL_QUERY_SOLVER_CHECK' for x in all_calls),'query_counts':dict(counts),'unknown_reasons':dict(unknown),'solver_checks_total':len(all_calls),'models_replayed':len(replays),'recorded_SQL_executions':len(replays)*2,'physical_rows':sum(x['physical_rows'] for x in replays),'input_NULL_cells':sum(x['input_null_cells'] for x in replays),'output_NULL_cells':sum(x['output_null_cells'] for x in replays),'worker_cpu_total':sum(x[0]['cpu_seconds'] for x in workers),'worker_cpu_max':max(x[0]['cpu_seconds'] for x in workers),'worker_peak_rss_max':max(x[0]['maxrss_bytes_darwin'] for x in workers),'worker_main_wall_max':max(x[2]['worker_usage']['wall_from_main_seconds'] for x in workers),'worker_lifecycle_wall_max':max(x[1]['wall_seconds'] for x in workers),'query_check_cpu':sum(x['actual_check_cpu_seconds'] for x in all_calls if x['stage']=='OFFICIAL_QUERY_SOLVER_CHECK'),'C_check_cpu':sum(x['actual_check_cpu_seconds'] for x in all_calls if x['stage']=='FULL_C_NONEMPTY_CHECK'),'import_cpu':sum(s['cpu_seconds'] for _,_,r in workers for s in r['runtime']['stages'] if s['name']=='NATIVE_AND_OFFICIAL_IMPORT'),'measured_supervisor_children_cpu':measured,'charged_cpu':measured+10+0.2,'load_gate_range':[min(x['load'][0] for x in gates),max(x['load'][0] for x in gates)],'memory_gate_range':[min(x['memory_available_percentage'] for x in gates),max(x['memory_available_percentage'] for x in gates)],'monitor_samples':len(monitors)}
test('primary counts exact match', counts=={'unsat':5,'unknown':4,'NO_QUERY_CHECK':3} and unknown=={'timeout':2,'out of memory':2} and totals['C_checks']==12 and totals['solver_checks_total']==21 and totals['physical_rows']==56)
for ours, theirs in [('worker_cpu_total','worker_wait4_cpu_total_seconds'),('worker_cpu_max','worker_wait4_cpu_seconds_max'),('worker_peak_rss_max','worker_peak_rss_bytes_max'),('worker_main_wall_max','worker_wall_from_main_seconds_max'),('query_check_cpu','query_check_cpu_seconds'),('C_check_cpu','contract_check_cpu_seconds'),('import_cpu','runtime_import_cpu_seconds_total')]:
    test('author aggregate '+theirs, near(totals[ours],observed[theirs]))
test('no retry or supervisor violation', batch['automatic_retries']==0 and batch['violations']==[] and batch['maximum_workers']==1)
output = {'id':'round06-independent-readonly-evidence-v1','scope':'Saved artifacts and concrete arithmetic only; no SQL/SMT or target code executed. Recorded SQLite execution evidence is not an independent rerun.','totals':totals,'rows':rows,'concrete_C_and_recorded_replay_checks':replays,'checks_count':len(checks),'failed_checks':[x for x in checks if not x['passed']],'checks':checks,'inputs':sorted(inputs.values(),key=lambda x:x['path'])}
(OUT/'independent_evidence.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'totals':totals,'checks_count':len(checks),'failed_checks':output['failed_checks'],'input_count':len(inputs)},ensure_ascii=False,indent=2))
