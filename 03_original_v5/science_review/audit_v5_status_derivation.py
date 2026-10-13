"""Independent read/hash/AST audit; no target or author classifier is imported."""
from pathlib import Path
import ast
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone

T = Path(__file__).resolve().parent.parent
E = T / 'experiments'
N = T / 'runtime_fair_v5_statusfix'
OUT = Path(__file__).with_name('PAIR_WORK_STATUS_FIX_INDEPENDENT_REVIEW.json')
errors, evidence, observations = [], {}, []


def h(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def file(path):
    path = Path(path).resolve()
    digest = h(path)
    evidence[str(path)] = digest
    return digest


cache = {}
def read(path):
    key = str(Path(path).resolve())
    if key not in cache:
        file(path)
        cache[key] = json.loads(Path(path).read_text())
    return cache[key]


def ck(ok, where, reason):
    if not ok:
        errors.append({'where': where, 'expected': reason})


def jh(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


cutpath = E / 'FINAL_V5_EXECUTION_CUT.json'
cut = read(cutpath)
ck(file(cutpath) == '1d6d0291fda36937a26da6b46c9d07b18899a21686708fa4279c7a814e48b95c', 'cut', 'frozen final cut')
selector = read(E / 'V5_SLOT_SELECTION_FINAL.json')
ck(selector['slot_selection'] == cut['slot_selection'], 'selector', 'external exact selector equals embedded ledger')
suite = read(E / 'v5_registration_01/REGISTERED_SIX_ARM_SUITE.json')
for path, meta in cut['file_provenance'].items():
    ck(file(path) == meta['sha256'] and Path(path).stat().st_size == meta['bytes'], path, 'frozen provenance bytes/hash')
locks = {}
locked_checked = {}
for mode, name in [('main', 'runtime_paths_v5.json'), ('spotit', 'spotit_engine_runtime_paths_v5.json')]:
    lp = E / 'v5_registration_01' / name
    lock = read(lp)
    ck(file(lp) == cut['runtime_lock_sha256'][mode], str(lp), 'same frozen source lock')
    for path, digest in lock['files'].items():
        if path not in locked_checked:
            locked_checked[path] = h(path)
        ck(locked_checked[path] == digest, path, 'source/dependency file matches runtime lock')
    locks[mode] = lock

groups = cut['logical_slots_and_all_observations']
counts = {}
for group, slots in groups.items():
    mode, kind = group.split('_', 1)
    final_rows = []
    ck(len(slots) == 168, group, 'full denominator retained')
    for slot in slots:
        idx = slot['job_index']
        key = f'{mode}:{kind}:{idx}'
        selected = slot['selected']
        expected_selected = mode == 'main' or slot['arm'] == 'official'
        ck(selected == expected_selected, key, 'selected registration exactly respected')
        if not selected:
            ck(slot['ledger_status'] == 'NOT_SELECTED' and 'final' not in slot and not slot['observations'], key, '140 SpotIt unselected arms untouched')
            continue
        row = slot['final']
        final_rows.append(row)
        terminal = [r for r in slot['observations'] if r['ledger_status'] == 'RETURNED']
        ck(len(terminal) == 1 and terminal[0] == row, key, 'unique terminal observation, not best/latest wins')
        chosen = cut['slot_selection'][key]
        ck(chosen['worker_path'] == row['worker_report'] and chosen['worker_sha256'] == row['worker_report_sha256'], key, 'selector binds exact final worker')
        for obs in [row, *slot.get('prior_incomplete_attempts', [])]:
            wp, sp = Path(obs['worker_report']), Path(obs['supervisor_report'])
            w, s = read(wp), read(sp)
            j = s['jobs'][idx]
            ck(file(wp) == obs['worker_report_sha256'] and file(sp) == obs['supervisor_report_sha256'], key, 'raw report evidence exact hashes')
            case = suite['cases'][slot['case_index']]
            ck(w['input'] == case and w['job_index'] == idx and w['job']['arm'] == slot['arm'], key, 'same full registered input/job')
            ck(w['runtime_lock_sha256'] == cut['runtime_lock_sha256'][mode] and w['suite_sha256'] == cut['suite_sha256'], key, 'worker source and suite identity')
            ck(obs['raw_pair_work_status'] == w.get('pair_work_status') and obs['raw_pair_parse_status'] == w.get('pair_parse_status') and obs['raw_pair_solver_status'] == w.get('pair_solver_status'), key, 'raw pair fields unmodified')
            ck(obs['raw_final_decision'] == w['final_decision'] and obs['raw_supervisor_final_decision'] == j['final_decision'], key, 'raw final result unmodified')
            ck(obs['raw_stop_reason_field_present'] == ('stop_reason' in j) and obs['raw_stop_reason'] == j.get('stop_reason'), key, 'raw observer anomaly retained')
            ck(obs['pair_return_receipt_fields'] == {k:w[k] for k in ['status','phase','pair_work_started','final_decision','environment_cleanup'] if k in w}, key, 'precise receipt fields preserved')
            started = w.get('pair_work_started') is True
            if w.get('phase') == 'FINAL_CONTRACT_STOP':
                derived = 'RETURNED_WITH_CONTRACT_STOP' if started else 'NOT_RUN_CONTRACT_STOP'
            elif w.get('status') == 'COMPLETE' and w.get('phase') == 'FINAL_COMPLETE' and started:
                derived = 'RETURNED'
            elif w.get('status') == 'BLOCKED_OR_ERROR' and w.get('phase') == 'ERROR' and started:
                derived = 'RETURNED_WITH_ERROR'
            elif started:
                derived = 'ATTEMPTED_EFFECT_UNKNOWN'
            else:
                derived = 'NOT_RUN' if not w or w.get('status') == 'NOT_RUN' else 'NO_PAIR_RETURN_RECEIPT'
            ck(obs['derived_pair_work_status'] == derived, key, 'independently derived execution state matches')
            ck(obs['pair_work_derivation_rule'] == 'V5_RECEIPT_EXECUTION_STATE_2_REQUIRES_STARTED', key, 'corrected rule version')
            stop = 'stop_reason' in j or j.get('status') == 'RESOURCE_STOP' or j.get('exit_code') in [-9,-14,-24] or w.get('error_type') == 'TimeoutError'
            strict, typed = obs['strict_valid_query_result'], obs['verified_expected_typed_rejection']
            if stop:
                ck(not strict and not typed and obs['derived_category'] == 'RESOURCE_STOP_OR_BUDGET_FAILURE', key, 'any observer/resource failure stays invalid even with final receipt')
            if strict or typed:
                ck(obs['identity_verified'] and j['status'] == 'PROCESS_EXITED' and not stop and w.get('environment_cleanup') == 'COMPLETE', key, 'identity, clean exit and cleanup required')
            if strict:
                ck(started and w['status'] == 'COMPLETE' and j['exit_code'] == 0, key, 'strict successful result has dispatch and exit 0')
                b, g = w['contract_bridge'], w['contract_guard']
                ck(b['status'] == 'VERIFIED_BOUNDED_AST_BRIDGE' and b['original_ast'] == case['constraint'] and b['original_ast_sha256'] == jh(case['constraint']), key, 'strict original AST identity')
                ck(b['base_only_sat']['status'] == 'sat' and b['normalized_vs_reference']['status'] == 'unsat' and b['base_only']['tested_ic_included'] is False, key, 'strict nonvacuous base / XOR gate')
                ck(g['consistency'] == 'sat' and g['any_base_row_deleted'] == 'unsat' and g['base_fact_sha256'] == b['complete_facts_sha256'], key, 'strict usable full C same fact hash')
                if kind == 'cost':
                    last = w['attempts'][-1]
                    ck(w['final_decision'] == last['status'] and last['status'] in ['sat','unsat'], key, 'last result-bearing attempt agrees')
                    if last['status'] == 'sat':
                        ov = last['oracle_validation']
                        ck(ov['status'] == 'REPLAYED_WITHIN_INT64_DOMAIN' and ov['queries'] == case['pair'] and ov['original_ast_contract_validation']['holds'] is True and ov['original_ast_contract_validation']['original_ast_sha256'] == jh(case['constraint']), key, 'SAT original C and original SQL replay identity')
                        ck(ov['sqlite']['unequal_as_bags'] is True and ov['sqlite']['matches_audited_mathematical_values'] == [True,True], key, 'complete SAT replay success')
                else:
                    d = w['differential']
                    expected_gates = {'full_contract_sat':'sat','exact_rows_no_deletion':'unsat','official_premise_sat':'sat','official_scalar_shape':'unsat','joint_premise_sat':'sat','output_mismatch':'unsat'}
                    ck(w['final_decision'] in ['UNSAT_DIFFERENTIAL','PASS_UNSAT_DIFFERENTIAL'] and all(d['gates'][k]['status'] == v for k,v in expected_gates.items()), key, 'bounded differential six obligation gates')
            if typed:
                ck(not started and not w['attempts'] and j['exit_code'] == 2 and all(w.get(k) == 'NOT_RUN_CONTRACT_STOP' for k in ['pair_work_status','pair_parse_status','pair_solver_status']), key, 'typed rejection not query success or pair UNSAT')
            if w['final_decision'] in ['unknown','UNKNOWN_OUTPUT_DIFFERENCE','UNKNOWN_ORACLE_DOMAIN']:
                ck(not strict and not typed, key, 'unknown or domain failure never promoted')
            if obs is not row:
                ck(idx == 52 and group == 'main_cost' and obs['derived_recovery_state'] == 'INTERRUPTED_EFFECT_UNKNOWN_RETAINED' and derived == 'ATTEMPTED_EFFECT_UNKNOWN' and not strict and not typed, key, 'old52 incomplete attempt retained separately')
                ck(obs['cost'] == {'sampled_peak_rss_bytes':0} and obs['environment_cleanup'] == 'NOT_RECORDED', key, 'missing full costs/cleanup not invented')
            observations.append({'logical_slot':key,'is_selected_final':obs is row,'worker_path':str(wp),'worker_sha256':file(wp),'supervisor_path':str(sp),'supervisor_sha256':file(sp),'raw_pair_work_status':w.get('pair_work_status'),'derived_pair_work_status':derived,'raw_decision':w['final_decision'],'strict_valid':strict,'typed_valid':typed,'resource_or_observer_stop':stop,'derived_category':obs['derived_category']})
    counts[group] = {'selected':len(final_rows),'strict':sum(r['strict_valid_query_result'] for r in final_rows),'typed':sum(r['verified_expected_typed_rejection'] for r in final_rows),'raw_pair_status':dict(Counter(r['raw_pair_work_status'] for r in final_rows)),'derived_pair_status':dict(Counter(r['derived_pair_work_status'] for r in final_rows)),'categories':dict(Counter(r['derived_category'] for r in final_rows))}
    summary = cut['summaries'][group]
    ck(counts[group]['strict'] == summary['strict_valid_query_results'] and counts[group]['typed'] == summary['verified_expected_typed_rejections'] and counts[group]['categories'] == summary['derived_categories'], group, 'independent count equals published count')

# Static validation of the future logging-only patch; no helper execution.
manifest = read(N / 'SOURCE_AND_DIFF_MANIFEST.json')
for d in manifest['diffs']:
    for pk,hk in [('old_path','old_sha256'),('new_path','new_sha256'),('diff_path','diff_sha256')]:
        ck(file(d[pk]) == d[hk], d[pk], 'frozen source/diff unchanged')
for d in manifest['added_files'] + manifest['future_runtime_locks']:
    ck(file(d['path']) == d['sha256'], d['path'], 'statusfix manifest hash match')
for d in manifest['future_runtime_locks']:
    lk=read(d['path']);ck(lk['status'] != 'STATIC_REVIEWED_READY_FOR_LOCAL_RUN',d['path'],'future lock not runtime-enabled by this review')
class RemoveLogging(ast.NodeTransformer):
    def visit_ImportFrom(self,node):
        return None if node.module == 'pair_status' else node
    def visit_Expr(self,node):
        c=node.value
        if isinstance(c,ast.Call) and isinstance(c.func,ast.Name):
            if c.func.id == 'record_pair_receipt': return None
            if c.func.id == 'checkpoint' and len(c.args)==1 and isinstance(c.args[0],ast.Constant) and c.args[0].value=='QUERY_WORK_RETURNED': return None
        return self.generic_visit(node)
old=ast.parse((T/'runtime_fair_v5/worker.py').read_text())
new=RemoveLogging().visit(ast.parse((N/'worker.py').read_text()))
ck(ast.dump(old,include_attributes=False)==ast.dump(new,include_attributes=False),'worker AST','identical control flow after removing logging additions')
fixture=read(N/'PURE_STATUS_FIXTURE_RECEIPT.json')
ck(fixture['fixture_count']==25 and all(x['status']=='PASS' for x in fixture['fixtures']),'statusfix fixture receipt','25 author-run pure-helper fixtures only')
for name,digest in fixture['programs'].items():ck(file(N/name)==digest,name,'fixture bound to actual source')
reg=read(E/'V5_AGGREGATOR_CLASSIFICATION_REGRESSION_02.json')
ck(reg['status']=='PASS' and len(reg['checks'])==16 and all(x['pass'] for x in reg['checks']),'aggregator regression','16 author-run stdlib classifier fixtures')
ck(file(E/'BUILD_FINAL_V5_EXECUTION_CUT.py')==reg['aggregator_sha256'] and file(E/'CHECK_V5_AGGREGATOR_CLASSIFICATION.py')==reg['check_source_sha256'],'classifier source','exact frozen tested classifier')
for path,digest in reg['fixture_inputs_sha256'].items():ck(file(path)==digest,path,'regression raw fixture identity')
for path in [E/'FINAL_V5_EXECUTION_CUT.zh.md', N/'STATUS_DERIVATION_SPEC.txt']:file(path)
result={'status':'STATIC_FIX_ACCEPTED_AND_FROZEN_FINAL_DERIVATIONS_VERIFIED' if not errors else 'FINDINGS_REMAIN','utc':datetime.now(timezone.utc).isoformat(),'reviewer':'Different AI agent /root/independent_review, not human; read/hash/AST and receipt recomputation only','scope':'Future logging-only candidate plus 364 selected terminal observations and one preserved incomplete attempt; no target/native/solver/SQLite/classifier/helper execution by reviewer','source_statusfix_manifest_sha256':file(N/'SOURCE_AND_DIFF_MANIFEST.json'),'final_cut_sha256':file(cutpath),'selector_sha256':file(E/'V5_SLOT_SELECTION_FINAL.json'),'locked_unique_file_bytes_checked':len(locked_checked),'final_cut_provenance_files_checked':len(cut['file_provenance']),'counts':counts,'observation_count':len(observations),'findings_history':[{'id':'P1-DERIVE-NO-START','old_classifier_sha256':'ad8348500cf99853ac31327716563cae5832245aef3b12f3d4b2283463d7111c','issue':'COMPLETE/FINAL_COMPLETE without pair_work_started derived RETURNED.','status':'Fixed-with-static-and-author-fixture-evidence','new_classifier_sha256':reg['aggregator_sha256'],'regression':'missing and false started both NO_PAIR_RETURN_RECEIPT'}],'open_P0':[],'open_P1':errors,'limitations':['RETURNED only records dispatch execution; it does not mean correct, solver-decided, process clean or resource-valid.','All 11 RSS_OBSERVATION_UNAVAILABLE terminals remain invalid; SpotIt129 typed raw outcome remains a resource failure.','Old52 raw partial report and missing full costs/cleanup remain separate; its started attempt is not erased or changed to NOT_RUN.','The future statusfix worker has not run with native/solver/SQL; 25 fixtures execute only pure logger. New lock remains pending.','16 classifier fixtures use identity=True as a unit fixture and are not independent experiment execution.','Current final cut derives statuses on old frozen v5 bytes; it does not pretend statusfix generated historical reports.','No performance/generalization or manuscript acceptance claim is established by this status audit.'],'observations':observations,'file_sha256':evidence,'audit_script_sha256':h(__file__)}
if OUT.exists():raise SystemExit('Refuse to overwrite existing independent report')
OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'status':result['status'],'errors':errors,'counts':counts,'observations':len(observations),'locked_unique_file_bytes_checked':len(locked_checked),'out':str(OUT),'sha256':h(OUT)},ensure_ascii=False,indent=2))
