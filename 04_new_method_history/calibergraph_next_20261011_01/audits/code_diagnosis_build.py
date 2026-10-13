"""Bind author static diagnosis to existing small manifests and source hashes."""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import hashlib, json, resource, time

started = time.monotonic()
OLD = Path('/Users/loctek/Documents/Codex/2026-10-09/task-7/calibergraph_revision_20261009/today_20261011')
OUT = Path(__file__).resolve().parent
def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(262144),b''):
            h.update(b)
    return h.hexdigest()

public = json.loads((OLD/'experiments/PUBLIC_APPLICABILITY_FINAL_CUT.json').read_text())
final = json.loads((OLD/'experiments/FINAL_V5_EXECUTION_CUT.json').read_text())
lock = json.loads((OLD/'runtime_v3/runtime_paths.json').read_text())
dev = json.loads((OLD/'public_dev/runs/full_scan_v3_all_01/scan_report.json').read_text())
aggregate = json.loads((OUT/'code_diagnosis_log_aggregate.json').read_text())
expected = {}
for d in (public.get('file_provenance',{}),final.get('file_provenance',{})):
    for p, entry in d.items():
        expected[p] = entry['sha256'] if isinstance(entry,dict) else entry
expected.update(lock['files'])
paths = [
 'FINAL_CALIBERGRAPH_HANDOFF.zh.md','wording_revision_20261011_01/README.zh.md',
 'experiments/PUBLIC_APPLICABILITY_FINAL_CUT.json','experiments/PUBLIC_APPLICABILITY_FINAL_CUT.zh.md',
 'experiments/BUILD_PUBLIC_APPLICABILITY_FINAL_CUT.py','experiments/FINAL_V5_EXECUTION_CUT.json',
 'experiments/FINAL_V5_EXECUTION_CUT.zh.md',
 'public_leetcode/scan_chunk.py','public_dev/scan_eligibility_v3_all.py','public_v4_cached/scanner.py',
 'public_dev/runs/full_scan_v3_all_01/scan_report.json','runtime_v3/runtime_paths.json',
 'runtime_v3/aggregate_kernel.py','runtime_v4/aggregate_kernel.py',
 'runtime_fair_v5/worker.py','runtime_fair_v5/common.py','runtime_fair_v5/contract_reference.py',
 'sources/verieql_v1/environment.py','sources/verieql_v1/parsers/sql_parser.py',
 'manuscript_v2/results_current.tex',
]
sources = []
for rel in paths:
    p = OLD/rel
    s = sha(p)
    sources.append({'path':str(p),'relative_to_old':rel,'bytes':p.stat().st_size,'sha256':s,
                    'frozen_expected_sha256':expected.get(str(p)),
                    'matches_prior_frozen_identity':s == expected[str(p)] if str(p) in expected else None})
lp = aggregate['source']['path']
sources.append(aggregate['source'] | {'relative_to_old':str(Path(lp).relative_to(OLD)),
    'frozen_expected_sha256':expected.get(lp),'matches_prior_frozen_identity':aggregate['source']['sha256']==expected.get(lp),
    'hash_method':'streamed during fresh log aggregation; not re-read by this builder'})

positive_contexts=[]
for row in dev['rows']:
    qs=[q for q in row['queries'] if q.get('eligible')]
    if not qs:
        continue
    rec=row['source_record']
    types=Counter(str(t).upper() for cols in rec['schema'].values() for t in cols.values())
    ops=Counter(next(iter(c)) for c in rec['constraint']) if isinstance(rec['constraint'],list) else Counter()
    positive_contexts.append({'row_id':row['id'],'eligible_query_indices':[q['query_index'] for q in qs],
       'original_sql':[q['original_sql'] for q in qs],
       'schema':rec['schema'],'constraint':rec['constraint'],'physical_type_counts':dict(types),
       'contract_top_operator_counts':dict(ops),'v5_schema_all_fields_exact_INT_static_condition':set(types)=={'INT'},
       'original_source_line_sha256':row['source_line_sha256'],
       'inference':'At least one non-INT field forces v5 contract_reference._schema rejection before solver; not experimentally executed.' if set(types)!={'INT'} else 'Avoids static all-INT schema rejection; no new runtime admission or solver decision asserted.'})

arm_costs={}
for arm,data in final['by_arm']['main_cost'].items():
    costs=data['cold_and_semantic_cost_all_attempts_including_failures']
    arm_costs[arm]={'selected_denominator':data['selected_denominator'],
         'strict_valid_query_results':data['strict_valid_query_results'],
         'derived_categories':data['derived_categories'],
         'started_attempt_denominator':data['started_attempt_denominator'],
         'cold_cpu':costs['full_process_cpu_seconds'],
         'semantic_e2e_cpu':costs['semantic_e2e_cpu_seconds'],
         'cold_wall':costs['full_process_wall_seconds'],
         'scope':'Existing selected returned observations, failures/refusals included; official interrupted attempt remains missing, not zero.'}
code_regions={
 'public_leetcode/scan_chunk.py':{'pre_solver_scope':[[1,8],[298,314]],'query_entry_and_status_order':[[378,407]]},
 'public_v4_cached/scanner.py':{'cache_gate_order':[[346,405]],'serialized_special_node_rejection':[[334,343],[389,391]]},
 'runtime_v4/aggregate_kernel.py':{'raw_identifier_gate':[[24,51]],'ast_from_output_and_predicates':[[113,268]],'encoding_and_NULL_semantics':[[271,400]],'sqlite_domain_boundary':[[403,455]]},
 'runtime_fair_v5/worker.py':{'contract_before_query':[[93,128]],'candidate_and_fallback':[[262,323]]},
 'runtime_fair_v5/common.py':{'contract_reference_XOR':[[137,224]],'shared_budget':[[255,279]],'positive_exact_rows':[[319,322]]},
 'runtime_fair_v5/contract_reference.py':{'complete_schema_INT_only':[[42,54]],'narrow_whole_contract':[[57,133]],'strict_true_all_rows':[[153,188]]},
 'sources/verieql_v1/parsers/sql_parser.py':{'global_rewrites':[[85,92],[166,168]],'typed_literal_loss':[[100,164]],'NULL_workaround':[[265,318]]},
 'sources/verieql_v1/environment.py':{'parser_forward':[[834,835]]},
}
outputs=[]
for name in ('code_diagnosis.zh.md','code_diagnosis_log_aggregate.py','code_diagnosis_log_aggregate.json','code_diagnosis_build.py'):
    p=OUT/name
    outputs.append({'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size})
result={
 'created_utc':datetime.now(timezone.utc).isoformat(),
 'role':'RESEARCH_AUTHOR_DIAGNOSIS_NOT_INDEPENDENT_REVIEW',
 'scientific_decision':'SCIENCE_HOLD_PREVIOUS_NO_GO_NOT_CLOSED',
 'confirmed_new_mechanism_candidates':0,
 'execution_scope':{'target_parser_runs':0,'target_recognizer_runs':0,'solver_runs':0,'SQL_runs':0,'load_experiments':0,'network_or_API_calls':0,'GPU_calls':0,'old_source_mutations':0,'method':'Static source reading, streamed existing log aggregation, existing small JSON evidence extraction'},
 'important_findings':[
  'Public no-JOIN eligibility is frontend/fragment applicability evidence, not solver failure evidence.',
  'Every one of 6889 v4 unsupported_identifier slots contains a top FROM derived table value=dict; label hides structural cause.',
  '1441 of 1453 unknown_table_or_repeated_relation slots contain repeated top base tables; remaining 12 not individually attributed.',
  'Only 12 cached AST slots have one top SUM/COUNT, join-or-comma FROM and no extra top clause; they have additional semantic/structural obstacles.',
  'Four of six public eligible slots statically fail v5 complete schema INT-only contract gate; two literature slots merely avoid that static rejection.',
  'Original complete IC includes primary/foreign beyond v5 reference grammar; dropping them is not lossless adaptation.',
  'Single cold observations and mixed outcomes do not demonstrate selector speed or isolate solver cost.',
 ],
 'public_frozen_denominators':public['full_denominators'],
 'fresh_log_aggregate':{'path':str(OUT/'code_diagnosis_log_aggregate.json'),'sha256':sha(OUT/'code_diagnosis_log_aggregate.json'),
                        'query_slots':aggregate['query_slots'],'status_counts':aggregate['status_counts'],'resource':aggregate['resource']},
 'public_eligible_original_contexts':positive_contexts,
 'existing_main_cost_by_arm':arm_costs,
 'code_regions':code_regions,'sources':sources,'outputs_excluding_self':outputs,
 'identity_audit':{'comparisons':sum(x['matches_prior_frozen_identity'] is not None for x in sources),
                   'mismatches':[x['path'] for x in sources if x['matches_prior_frozen_identity'] is False],
                   'scope':'Comparison to stored prior provenance where available; null means no prior digest in the read manifests, not a verification pass.'},
 'limitations':['No independent review performed by this author agent.','No parser repair, eligibility re-run, target execution or new scientific evidence.','Prior-art threats relayed by parent task; this code-only task did not independently verify papers.','No old full-package rehash or remote backup performed.'],
 'resource':{'wall_seconds':time.monotonic()-started,'peak_rss_bytes_darwin':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss},
}
dest=OUT/'code_diagnosis.json'
with dest.open('x') as f:
    json.dump(result,f,ensure_ascii=False,indent=2)
    f.write('\n')
print(json.dumps({'output':str(dest),'identity_audit':result['identity_audit'],'costs':{k:{'cold':v['cold_cpu']['sum'],'semantic':v['semantic_e2e_cpu']['sum']} for k,v in arm_costs.items()},'resource':result['resource']},ensure_ascii=False,indent=2))
