"""Read existing cached-AST evidence only; never load parser/kernel/solver.

Streams one existing JSONL record at a time, caps elapsed time at 45 seconds,
and writes new audit files only. Structural features are not an eligibility test.
"""
from pathlib import Path
from collections import Counter, defaultdict
import hashlib, json, resource, time

OLD = Path('/Users/loctek/Documents/Codex/2026-10-09/task-7/calibergraph_revision_20261009/today_20261011')
OUT = Path(__file__).resolve().parent
SRC = OLD / 'public_v4_cached/runs/run_001/slots.jsonl'
started = time.monotonic()
status, reason, features = Counter(), Counter(), Counter()
feature_by_reason = defaultdict(Counter)
shapes = Counter()
examples = defaultdict(list)
candidates = []
digest = hashlib.sha256()

def walk(node):
    yield node
    if isinstance(node, dict):
        for value in node.values():
            yield from walk(value)
    elif isinstance(node, list):
        for value in node:
            yield from walk(value)

def single_agg(ast):
    if not isinstance(ast, dict):
        return None
    s = ast.get('select')
    if isinstance(s, list):
        if len(s) != 1:
            return None
        s = s[0]
    if not isinstance(s, dict) or 'value' not in s:
        return None
    v = s['value']
    if not isinstance(v, dict) or len(v) != 1:
        return None
    op, arg = next(iter(v.items()))
    return (op, arg) if op in {'sum', 'count'} else None

with SRC.open('rb') as stream:
    for raw in stream:
        if time.monotonic() - started > 45:
            raise RuntimeError('45 second budget reached; no partial audit promoted')
        digest.update(raw)
        q = json.loads(raw)
        status[q['status']] += 1
        r = q['original_reason'] if q['status'] == 'PARSE_OR_AST_RECORD_ERROR' else q['reason']
        r = 'PARSE_OR_AST_RECORD_ERROR' if q['status'] == 'PARSE_OR_AST_RECORD_ERROR' else r
        reason[r] += 1
        ast = q.get('ast')
        fs = set()
        if isinstance(ast, dict):
            nodes = list(walk(ast))
            keys = {k for n in nodes if isinstance(n, dict) for k in n}
            extra = set(ast) - {'select', 'from', 'where'}
            agg = single_agg(ast)
            items = ast.get('from', [])
            items = items if isinstance(items, list) else [items]
            base_tables, from_shapes = [], []
            top_join_kinds = []
            for item in items:
                if isinstance(item, dict):
                    joins = [k for k in item if 'join' in k]
                    top_join_kinds.extend(joins)
                    if joins:
                        item = item[joins[0]]
                if isinstance(item, str):
                    base_tables.append(item)
                    from_shapes.append('base_string')
                elif isinstance(item, dict) and 'value' in item:
                    if isinstance(item['value'], str):
                        base_tables.append(item['value'])
                        from_shapes.append('base_alias')
                    else:
                        from_shapes.append('derived_value_' + type(item['value']).__name__)
                else:
                    from_shapes.append(type(item).__name__)
            if keys & {'join','inner join','left join','right join','full join','left outer join','right outer join','full outer join','cross join','natural join'}:
                fs.add('explicit_join_anywhere')
            if top_join_kinds:
                fs.add('explicit_join_top_from')
            if len(items) > 1:
                fs.add('multiple_top_from_items')
            if base_tables and len(base_tables) != len(set(base_tables)):
                fs.add('repeated_top_base_table')
            if any(x.startswith('derived_value_') for x in from_shapes):
                fs.add('derived_top_from_value')
            if isinstance(ast.get('select'), list) and len(ast['select']) > 1:
                fs.add('multiple_top_select_outputs')
            if extra:
                fs.add('extra_top_clause')
            if any(k in ast for k in ('groupby','having')):
                fs.add('top_groupby_or_having')
            if keys & {'union','union_all','intersect','except','minus'}:
                fs.add('set_operator_anywhere')
            if agg:
                fs.add('top_single_sum_or_count')
                if not any(k in ast for k in ('groupby','having')):
                    fs.add('top_scalar_sum_or_count_shape')
                if top_join_kinds or len(items) > 1:
                    fs.add('top_single_sum_count_with_join_or_comma')
                    if not extra:
                        fs.add('no_extra_clause_single_sum_count_with_join_or_comma')
                        candidates.append({k:q.get(k) for k in ('slot_ordinal','row_id','query_index','dataset','status','reason','original_sql','sql_sha256','ast_sha256','cached_report')} | {'ast':ast,'from_shapes':from_shapes})
            if r == 'unsupported_identifier':
                shapes[','.join(from_shapes)] += 1
        for f in fs:
            features[f] += 1
            feature_by_reason[r][f] += 1
        if r in {'unsupported_identifier','unknown_table_or_repeated_relation','extra_select_clause','non_integer_column','unsupported_join'} and len(examples[r]) < 3:
            examples[r].append({k:q.get(k) for k in ('row_id','query_index','status','reason','original_sql','ast','sql_sha256','ast_sha256','cached_report')})

result = {
    'role':'RESEARCH_AUTHOR_DIAGNOSIS_NOT_INDEPENDENT_REVIEW',
    'method':'Stream-only stdlib aggregation of existing logs and cached AST structure; no SQL parsing, no recognizer invocation, no schema/IC inference, no solver, no eligibility repair or claim',
    'source':{'path':str(SRC),'bytes':SRC.stat().st_size,'sha256':digest.hexdigest()},
    'query_slots':sum(status.values()),'status_counts':dict(status),'first_reason_counts':dict(reason),
    'structural_feature_counts_overlapping_not_additive':dict(features),
    'features_by_first_reason':{k:dict(v) for k,v in feature_by_reason.items()},
    'unsupported_identifier_from_shapes':dict(shapes),
    'examples':dict(examples),
    'scalar_sum_count_join_shape_candidates':candidates,
    'cautions':['FIRST_REASON counts do not measure all causes. AST features overlap and are not repair yield.',
                'Non-null cached AST is official parser output, not proof of original SQL semantics.',
                'JOIN-or-comma selection is structural; may include subqueries, unsupported types, DISTINCT, multiple roots or self joins.'],
    'resource':{'wall_seconds':time.monotonic()-started,'peak_rss_bytes_darwin':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss},
}
dest = OUT / 'code_diagnosis_log_aggregate.json'
with dest.open('x') as f:
    json.dump(result,f,ensure_ascii=False,indent=2)
    f.write('\n')
print(json.dumps({'output':str(dest),'status':result['status_counts'],'features':result['structural_feature_counts_overlapping_not_additive'],'unsupported_identifier_from_shapes':dict(shapes),'candidate_count':len(candidates),'candidate_reason_counts':dict(Counter(q['reason'] for q in candidates)),'resource':result['resource']},ensure_ascii=False,indent=2))
