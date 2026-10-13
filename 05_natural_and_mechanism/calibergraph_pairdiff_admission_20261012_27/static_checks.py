"""Parser/algebra safety fixtures only; never execute the fixture SQL."""
import json
import scan
S={x:[('x','INT'),('y','INT')] for x in ['a','b','c']}
checks=[]
def check(name,a,b,pred):
 r=scan.inspect_pair(a,b,S,'sqlite');assert pred(r),(name,r);checks.append({'name':name,'pass':True})
check('one_for_one_bag_union_cancel','SELECT x FROM a UNION ALL SELECT x FROM a UNION ALL SELECT x FROM b','SELECT x FROM a UNION ALL SELECT x FROM c',lambda r:r['events'].get('U_canceled_branch_occurrences')==1 and r['residual_operator_counts']['scan']==3)
check('whole_pair_is_cache_only','SELECT x FROM a','SELECT x FROM a',lambda r:r['primary_reason']=='EXACT_PAIR_CACHE_ONLY' and not r['gate_structural_match'])
check('alpha_alias_binding','SELECT z.x FROM a z','SELECT w.x FROM a w',lambda r:r['equal_ast_pair'])
check('ordinary_filter_change_not_elimination','SELECT x FROM a WHERE y=1','SELECT x FROM a WHERE y=2',lambda r:r['events'].get('S_different_same_input_descriptive')==1 and not r['gate_structural_match'])
check('distinct_barrier','SELECT DISTINCT x FROM a','SELECT x FROM a',lambda r:'DISTINCT' in r['barriers'] and not r['admitted'])
check('order_limit_barrier','SELECT x FROM a ORDER BY x LIMIT 1','SELECT x FROM a',lambda r:not r['admitted'] and 'ORDER' in r['barriers'])
check('outer_join_barrier','SELECT a.x FROM a LEFT JOIN b ON a.x=b.x','SELECT a.x FROM a JOIN b ON a.x=b.x',lambda r:'OUTER_OR_SPECIAL_JOIN' in r['barriers'])
check('aggregate_barrier','SELECT COUNT(*) FROM a','SELECT x FROM a',lambda r:'AGGREGATE' in r['barriers'])
check('ambiguous_column_refused','SELECT x FROM a JOIN b ON a.x=b.x','SELECT a.x FROM a JOIN b ON a.x=b.x',lambda r:r['primary_reason']=='UNRESOLVED_OR_AMBIGUOUS_COLUMN')
check('join_zero_term_keeps_common_scan','SELECT a.x,t.x FROM a JOIN (SELECT x FROM b WHERE y=1) t ON a.x=t.x','SELECT a.x,t.x FROM a JOIN (SELECT x FROM b WHERE y=2) t ON a.x=t.x',lambda r:r['events'].get('J_zero_term_eliminated')==1 and r['residual_operator_counts']['scan']==2 and r['residual_operator_counts']['join']==1)
check('different_projection_not_canceled','SELECT x FROM a','SELECT y FROM a',lambda r:not r['equal_ast_pair'] and not r['gate_structural_match'])
check('unknown_predicate_function_refused','SELECT x FROM a WHERE RANDOM()>0','SELECT x FROM a',lambda r:not r['admitted'])
check('same_filter_not_dropped','SELECT x FROM a WHERE y IS NOT NULL UNION ALL SELECT x FROM b','SELECT x FROM a WHERE y IS NOT NULL UNION ALL SELECT x FROM c',lambda r:r['events'].get('U_canceled_branch_occurrences')==1)
result={'checks':checks,'natural_data':False,'sql_executions':0,'solver_calls':0,'scope':'Static parser/algebra safety fixtures; not empirical evidence for candidate'}
(scan.ROOT/'STATIC_CHECKS.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
