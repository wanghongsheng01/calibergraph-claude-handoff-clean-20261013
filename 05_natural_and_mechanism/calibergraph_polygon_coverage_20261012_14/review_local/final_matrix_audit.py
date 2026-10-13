"""Validate saved matrix and bind the reviewed prose. No database or solver execution."""
from pathlib import Path
import collections
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
P = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
load = lambda p: json.loads(p.read_text())
ind = load(OUT/'STATIC_AUDIT.json')
auth = load(P/'STATIC_CLASSIFICATION.json')
matrix = load(P/'COVERAGE_MATRIX.json')
decision = load(P/'PRE_RUN_DECISION.json')
replay = load(OUT/'SAVED_WITNESS_REPLAY.json')
manifest = load(ROOT/'calibergraph_coverage_boundary_20261012_09/CANDIDATES.json')
ordered = [c['case_id'] for c in manifest]
assert ordered == [r['case_id'] for r in matrix['rows']] == decision['ordered_frozen_cases']
assert ordered == [r['case_id'] for r in auth['rows']] == [r['case_id'] for r in ind['cases']]
assert decision['new_run_slots'] == []
assert matrix['denominator'] == {
 'frozen_cases':10,'valid_SQL_pairs':8,'invalid_SQL_pairs':2,'typed_full_C_admitted_cases':2,
 'other_valid_not_admitted_cases':6,'potential_case_modes':20,'prior_executed_case_modes':4,
 'new_executed_case_modes':0,'static_NOT_RUN_case_modes':16}
statuses = collections.Counter()
for a,i,m in zip(auth['rows'],ind['cases'],matrix['rows']):
    assert a['table_count'] == i['table_count'] == m['table_count']
    assert a['column_count'] == i['column_count'] == m['column_count']
    assert a['type_counts'] == {k.upper():v for k,v in i['declared_type_counts'].items()} == m['type_counts']
    assert a['category'] == m['category']
    assert m['new_attempts'] == 0 and m['development_only']
    for at,it in zip(a['full_C_inventory'],i['tables']):
        assert at['table'] == it['table']
        norm = lambda cols:[dict(c,type=c['type'].upper()) for c in cols]
        assert norm(at['columns']) == norm(it['columns'])
        assert at['foreign_keys'] == it['foreign_keys']
        norm_i = [{k:v for k,v in idx.items() if k!='seq'} for idx in it['indexes']]
        for idx in norm_i:
            idx['columns'] = [[c['seqno'],c['cid'],c['name']] for c in idx['columns']]
        assert at['indexes'] == norm_i
    for name, c in a['compile_only'].items():
        assert c['status'] == i['sqlite_explain'][name]['status']
        if 'error' in c: assert c['error'] == i['sqlite_explain'][name]['error']
    for mode in ('UA','precise'):
        rec = m[mode]
        assert rec['new_run'] is False
        if a['category'] == 'PREVIOUSLY_EXECUTED':
            prior = load(ROOT/rec['result_path'])
            assert sha(ROOT/rec['result_path']) == rec['result_sha256']
            assert prior['status'] == rec['status']
            if rec['witness_sha256']:
                wp = (ROOT/rec['result_path']).parent/'witness.json'
                assert sha(wp) == rec['witness_sha256']
                rr = next(x for x in replay['slots'] if x['mode']==mode)
                assert rr['witness_sha256'] == rec['witness_sha256'] and rr['different']
        else:
            assert rec['status'] == 'NOT_RUN_' + a['category'] and rec['stage_times'] is None
        statuses[rec['status']]+=1
for c in load(P/'SOURCE_HASHES.json')['checks']:
    assert sha(ROOT/c['path']) == c['sha256']
preserved = load(P/'OLD_PRESERVATION.json')
assert all(sha(ROOT/c['path']) == c['sha256'] for c in preserved['old_files'])
frozen = load(P/'FREEZE.json')
assert frozen['frozen_run_slots'] == []
assert all(sha(P/p) == h for p,h in frozen['files_sha256'].items())
closed = load(P/'BATCH_CLOSED.json')
assert closed['freeze_sha256'] == sha(P/'FREEZE.json')
assert closed['status'] == 'CLOSED_NO_NEW_ADMITTED_CASES'
assert closed['science_attempts'] == closed['new_workers'] == closed['new_z3_processes'] == 0
assert closed['static_NOT_RUN_case_modes'] == 16
names = ['RESULT.zh.md','RECOVERY.zh.md','STATIC_CLASSIFICATION.json','COVERAGE_MATRIX.json',
         'COVERAGE_MATRIX.csv','PRE_RUN_DECISION.json','SOURCE_HASHES.json','CODE_EVIDENCE.json',
         'CLASSIFICATION_REFINEMENT.json','classify_static.py','OLD_PRESERVATION.json',
         'FREEZE.json','BATCH_CLOSED.json','PRESERVATION_FINAL.json']
audit = {
 'reviewer':'independent polygon14 coverage reviewer',
 'verdict':'ACCEPT_STATIC_CLOSURE_WITH_STATED_TYPE_AND_DEVELOPMENT_BOUNDARIES',
 'denominators':matrix['denominator'], 'case_mode_status_counts':dict(statuses),
 'original_10_order_and_membership_verified':True,
 'all_40_source_hashes_verified':True,
 'full_metadata_matches_independent_audit':True,
 'full_metadata_comparison':'Table names, all columns/defaults/PK/NN, FK actions, unique/index metadata; type spelling case-normalized only for comparing metadata, no runtime mapping extended.',
 'author_sqlite_version':auth['sqlite_version'], 'reviewer_sqlite_version':ind['sqlite_version'],
 'opcode_counts_not_expected_identical_across_versions':True,
 'additional_admitted_cases':[], 'new_scientific_slots':0, 'new_solver_calls':0,
 'frozen_empty_run_list_and_batch_closure_verified':True,
 'old_saved_witnesses_independently_replayed_this_round':2,
 'original_queries_executed_in_saved_replay_only':4,
 'new_witnesses_generated':0,
 'pilot_frozen_file_hashes_verified':replay['pilot_frozen_file_hashes_verified'],
 'preserved_old_file_hashes_verified':len(preserved['old_files']),
 'remaining_valid_not_admitted_cases_are_not_solver_failures':True,
 'valid_input_support_fraction':'2/8 (25%), descriptive of this frozen exposed development package only',
 'all_cases_development_only':True,
 'full_sqlite_type_domain_semantics_closed':False,
 'novelty_or_method_superiority_supported':False,
 'memory_contract':'512 MiB per Z3 internal allocation, not aggregate RSS; no new Z3 launched.',
 'process_RSS_queries':0, 'unrelated_project_operations':0,
 'findings_resolved':['#45 N=1 limit separated from actual full-schema type admission blocker.',
   'Secondary static tags distinguish implementation/semantic gaps from full-C mapping; no dynamic Unsupported result asserted.',
   'Future question no longer presumes a prior solver failure in six unrun valid cases.'],
 'one_supported_followup_question':'After preserving original SQLite types, original SQL and complete C and completing faithful modeling/concretization, do existing strong baselines exhibit independently verifiable failures on the remaining six valid inputs?',
 'reviewed_documents':[{'path':n,'sha256':sha(P/n),'verdict':'ACCEPT_WITH_STATED_BOUNDARIES'} for n in names],
 'evidence':[{'path':str((OUT/n).relative_to(P)),'sha256':sha(OUT/n)} for n in
             ['STATIC_AUDIT.json','SAVED_WITNESS_REPLAY.json','STATIC_REVIEW.zh.md',
              'independent_static_audit.py','independent_saved_replay.py']],
 'recovery_review_scope':'Static instructions and path contract only. No source/dependency reacquisition, new scientific run, remote backup verification or DataHub registry operation.',
 'remaining_external_blockers':['Historical external artifact availability and DataHub canonical registration limitations are preserved, not solved by this audit.'],
 'author_deliverable_blockers':[],
 'reviewer_script_sha256':sha(Path(__file__))}
(OUT/'INDEPENDENT_REVIEW.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'verdict':audit['verdict'],'status_counts':dict(statuses),
 'result_sha256':sha(P/'RESULT.zh.md'),'recovery_sha256':sha(P/'RECOVERY.zh.md')},ensure_ascii=False,indent=2))
