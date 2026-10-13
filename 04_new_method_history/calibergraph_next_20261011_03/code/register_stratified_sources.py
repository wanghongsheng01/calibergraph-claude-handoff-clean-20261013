"""Prepared offline JSON/token inventory; no SQL parser, SQL engine, or solver.

Run only after parent protocol freeze and resource guard. One streaming pass over
the three exact source snapshots, plus <=32 selected-line rereads. No reserve file
is opened; reserved source groups bypass SQL JSON decoding/tokenization.
"""
from collections import Counter, defaultdict
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import resource
import signal
import sys
import time

TOKEN = re.compile(r"(?P<WS>\s+)|(?P<COMMENT>--[^\n]*|/\*[\s\S]*?\*/)|(?P<STRING>'(?:''|[^'])*')|(?P<QID>\"(?:\"\"|[^\"])*\"|`(?:``|[^`])*`|\[[^\]]*\])|(?P<WORD>[A-Za-z_][A-Za-z_0-9$]*)|(?P<NUMBER>\d+(?:\.\d+)?)|(?P<SYMBOL>[(),.*+/%=<>!|&;:-])|(?P<OTHER>.)")
AGGS = {'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'GROUP_CONCAT', 'STRING_AGG'}
BREAK_FROM = {'WHERE', 'GROUP', 'HAVING', 'ORDER', 'LIMIT', 'UNION', 'INTERSECT', 'EXCEPT', 'QUALIFY', 'WINDOW'}

def canonical(v):
    return json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()

def sha(v):
    return hashlib.sha256(v).hexdigest()

def tie(seed, *parts):
    return sha(('\0'.join([seed, *map(str, parts)])).encode())

def contract_axis(record):
    if 'constraint' not in record:
        return 'MISSING'
    value = record['constraint']
    if value is None:
        return 'NULL_UNSPECIFIED'
    if value == []:
        return 'EXPLICIT_EMPTY_OPERATIONAL'
    if isinstance(value, list) and value and all(isinstance(x, dict) and x for x in value):
        return 'PRESENT_JSON'
    return 'INSUFFICIENT'

def metadata_before_pair(raw):
    """Decode only object prefix preceding top-level pair key, never its SQL."""
    depth, i = 0, 0
    while i < len(raw):
        ch = raw[i]
        if ch == 34:
            start = i
            i += 1
            while i < len(raw):
                if raw[i] == 92:
                    i += 2
                elif raw[i] == 34:
                    i += 1
                    break
                else:
                    i += 1
            j = i
            while j < len(raw) and raw[j] in b' \t\r\n':
                j += 1
            if depth == 1 and j < len(raw) and raw[j] == 58 and json.loads(raw[start:i]) == 'pair':
                prefix = raw[:start].rstrip()
                if prefix.endswith(b','):
                    prefix = prefix[:-1]
                result = json.loads(prefix+b'}')
                if not isinstance(result, dict):
                    raise ValueError('INVALID_METADATA_PREFIX')
                return result
        else:
            if ch in (123, 91):
                depth += 1
            elif ch in (125, 93):
                depth -= 1
            i += 1
    raise ValueError('PAIR_PREFIX_NOT_LOCATED_NO_SQL_INSPECTION')

def lexical_shape(sql, schema):
    ts = []
    for match in TOKEN.finditer(sql):
        kind, value = match.lastgroup, match.group()
        if kind in ('WS', 'COMMENT'):
            continue
        if kind == 'OTHER':
            raise ValueError('UNSUPPORTED_LEXICAL_CHARACTER')
        if kind == 'QID':
            value = value[1:-1].replace('""', '"').replace('``', '`')
        ts.append((kind, value.upper() if kind in ('WORD', 'QID') else value))
    depth, depths = 0, []
    for kind, value in ts:
        depths.append(depth)
        if value == '(' and kind == 'SYMBOL':
            depth += 1
        elif value == ')' and kind == 'SYMBOL':
            depth -= 1
            if depth < 0:
                raise ValueError('UNBALANCED_LEXICAL_PARENTHESES')
    if depth:
        raise ValueError('UNBALANCED_LEXICAL_PARENTHESES')
    def kw(i, name):
        return 0 <= i < len(ts) and ts[i] == ('WORD', name)
    def sym(i, value):
        return 0 <= i < len(ts) and ts[i] == ('SYMBOL', value)
    aggs = [i for i,(k,v) in enumerate(ts) if k == 'WORD' and v in AGGS and sym(i+1, '(')]
    relation_names, from_depths = [], set()
    known = {x.upper() for x in schema}
    for i,(kind,value) in enumerate(ts):
        d = depths[i]
        if kind == 'WORD' and value in BREAK_FROM:
            from_depths.discard(d)
        if sym(i, ')'):
            from_depths.discard(d)
        starts = kw(i, 'FROM') or kw(i, 'JOIN') or (sym(i, ',') and d in from_depths)
        if kw(i, 'FROM'):
            from_depths.add(d)
        if starts and i+1 < len(ts) and ts[i+1][0] in ('WORD', 'QID'):
            name = ts[i+1][1]
            if sym(i+2, '.') and i+3 < len(ts) and ts[i+3][0] in ('WORD', 'QID'):
                name = ts[i+3][1]
            if name in known:
                relation_names.append(name)
    derived_aggregate = False
    for i in range(len(ts)):
        if (kw(i,'FROM') or kw(i,'JOIN')) and sym(i+1,'(') and kw(i+2,'SELECT'):
            d = depths[i+1]
            end = next((j for j in range(i+2,len(ts)) if sym(j,')') and depths[j] == d+1), len(ts))
            derived_aggregate |= any(i+2 <= a < end for a in aggs)
    in_exists = any((kw(i,'IN') or kw(i,'EXISTS')) and sym(i+1,'(') and kw(i+2,'SELECT') for i in range(len(ts)))
    select_count = sum(kw(i,'SELECT') for i in range(len(ts)))
    outer_q, inner_q = set(), set()
    for i,(kind,value) in enumerate(ts):
        if kind in ('WORD','QID') and sym(i+1,'.'):
            (outer_q if depths[i] == 0 else inner_q).add(value)
    correlated_hint = select_count > 1 and bool(outer_q & inner_q)
    outer_join = any(ts[i][0] == 'WORD' and ts[i][1] in ('LEFT','RIGHT','FULL') and (kw(i+1,'JOIN') or (kw(i+1,'OUTER') and kw(i+2,'JOIN'))) for i in range(len(ts)))
    join_tokens = sum(kw(i,'JOIN') for i in range(len(ts)))
    set_ops = sum(ts[i][0] == 'WORD' and ts[i][1] in ('UNION','INTERSECT','EXCEPT') for i in range(len(ts)))
    return {'token_count':len(ts),'select_count':select_count,'aggregate_calls':len(aggs),'join_tokens':join_tokens,'set_operations':set_ops,'derived_aggregate_hint':derived_aggregate,'in_exists_subquery_hint':in_exists,'correlated_qualifier_hint':correlated_hint,'outer_join_hint':outer_join,'relation_occurrences':relation_names,'distinct_relation_count':len(set(relation_names)),'repeated_relation_hint':len(relation_names)>len(set(relation_names)),'join_hint':join_tokens>0 or len(relation_names)>=2,'classification_scope':'LEXICAL_APPROXIMATION_NOT_AST_OR_SEMANTIC_VALIDATION'}

def first_stratum(shapes):
    rules = [
        ('S1_SET_OPERATION', lambda s:s['set_operations']>0),
        ('S2_DERIVED_TABLE_AGGREGATE', lambda s:s['derived_aggregate_hint']),
        ('S3_IN_EXISTS_OR_CORRELATED_HINT', lambda s:s['in_exists_subquery_hint'] or s['correlated_qualifier_hint']),
        ('S4_OUTER_JOIN', lambda s:s['outer_join_hint']),
        ('S5_SELF_OR_REPEATED_RELATION', lambda s:s['repeated_relation_hint']),
        ('S6_MULTI_JOIN_3_TABLES', lambda s:s['distinct_relation_count']>=3),
        ('S7_JOIN_AGGREGATE', lambda s:s['join_hint'] and s['aggregate_calls']>0),
        ('S8_PURE_JOIN_NONAGGREGATE', lambda s:s['join_hint'] and s['aggregate_calls']==0)]
    return next((name for name,predicate in rules if any(predicate(s) for s in shapes)),None)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--protocol',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args()
    start=time.monotonic()
    protocol=json.loads(args.protocol.read_text())
    if protocol['id']!='calibergraph-03-stratified-source-selection-v1' or sha(Path(__file__).read_bytes())!=protocol['scanner_sha256']:
        raise ValueError('PROTOCOL_OR_CODE_IDENTITY_MISMATCH')
    if not (sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode):
        raise ValueError('REQUIRES_-B_-I_-S_AND_PARENT_RESOURCE_GUARD')
    root=Path(__file__).resolve().parents[1]
    out=args.out.resolve()
    owned=['inventory.jsonl','report.json','report.tmp','selected.jsonl','selection_attempts.jsonl','source_groups.json']
    selected_export=root/'data/development_stratified.jsonl'
    if not out.is_relative_to(root/'runs') or any((out/name).exists() for name in owned) or selected_export.exists():
        raise ValueError('OWN_OUTPUTS_MUST_BE_NEW_UNDER_03_RUNS_AND_DATA')
    out.mkdir(parents=True,exist_ok=True)
    signal.alarm(24)
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    resource.setrlimit(resource.RLIMIT_CPU,(9,10))
    def guard():
        usage=resource.getrusage(resource.RUSAGE_SELF)
        if time.monotonic()-start>22 or usage.ru_utime+usage.ru_stime>8 or usage.ru_maxrss>=256*1024**2:
            raise RuntimeError('LOCAL_TIME_OR_OBSERVED_RSS_LIMIT')
    report={'status':'STARTED_NO_SELECTED_OUTPUT_VALIDATED','protocol_sha256':sha(args.protocol.read_bytes()),'source_denominators':protocol['source_denominators'],'sources':[],'input_rows_seen':0,'failed_inventory_rows':0,'selection_performed':False}
    def save():
        tmp=out/'report.tmp'
        tmp.write_bytes(json.dumps(report,ensure_ascii=False,indent=2).encode()+b'\n')
        tmp.replace(out/'report.json')
    save()
    buckets=defaultdict(list)
    groups={}
    statuses=Counter()
    ccounts=defaultdict(Counter)
    private_hashes=set(protocol['excluded_known_reserve_group_sha256'])
    olddev=set(protocol['excluded_previous_development_group_ids'])
    seed=protocol['seed']
    ledger=(out/'inventory.jsonl').open('x')
    try:
        for source in protocol['sources']:
            digest=hashlib.sha256(); row_count=0; offset=0
            with Path(source['path']).open('rb') as stream:
                for raw in stream:
                    guard(); digest.update(raw); row_count+=1; report['input_rows_seen']+=1
                    if report['input_rows_seen']>24455:
                        raise RuntimeError('SOURCE_DENOMINATOR_CEILING_EXCEEDED')
                    item={'dataset':source['dataset'],'source_path':source['path'],'source_file_sha256':source['sha256'],'line_1based':row_count,'byte_offset':offset,'byte_length':len(raw),'raw_line_sha256':sha(raw),'status':'STARTED'}
                    offset+=len(raw)
                    try:
                        meta=metadata_before_pair(raw)
                        if source['dataset']=='leetcode':
                            if not isinstance(meta.get('file'),str) or not meta['file']:
                                raise ValueError('SOURCE_FILE_LABEL_UNAVAILABLE_BEFORE_SQL')
                            gid='leetcode:'+meta['file']; gh=sha(gid.encode())
                            if gh in private_hashes:
                                axis=contract_axis(meta) if 'constraint' in meta else 'RESERVED_METADATA_UNINSPECTED'
                                ccounts[source['dataset']][axis]+=1
                                item.update(source_group_id=None,source_group_sha256=gh,contract_source=axis,status='KNOWN_RESERVE_GROUP_EXCLUDED_BEFORE_SQL_DECODE',sql_inspected=False)
                                group=groups.setdefault('reserved:'+gh,{'source_group_id':None,'source_group_sha256':gh,'dataset':'leetcode','rows':0,'status':'KNOWN_RESERVE_GROUP_EXCLUDED','stratum_pair_counts':{}})
                                group['rows']+=1
                                continue
                        record=json.loads(raw)
                        axis=contract_axis(record); ccounts[source['dataset']][axis]+=1
                        labels={k:record[k] for k in ('file','benchmark','name','index') if k in record}
                        item.update(original_source_labels=labels,contract_source=axis)
                        if source['dataset']=='calcite':
                            item.update(source_group_id=None,status='SOURCE_GROUP_NOT_ESTABLISHED',origin='SYNTHETIC_OPTIMIZER_BENCHMARK_NOT_NATURAL_BUSINESS')
                            continue
                        if source['dataset']=='literature':
                            name=record.get('name')
                            gid='literature:name:'+str(name) if isinstance(name,str) and name else None
                            item.update(source_group_id=gid,status='UPSTREAM_REWRITTEN_NONNATURAL_CONTROL_NOT_PRIMARY',origin='UPSTREAM_REWRITTEN_LITERATURE_EXAMPLE')
                            if gid:
                                groups.setdefault(gid,{'source_group_id':gid,'dataset':'literature','rows':0,'status':'CONTROL_LABEL_ONLY_NOT_STATISTICALLY_INDEPENDENT','stratum_pair_counts':{}})['rows']+=1
                            continue
                        gid='leetcode:'+record['file']
                        item['source_group_id']=gid
                        group=groups.setdefault(gid,{'source_group_id':gid,'dataset':'leetcode','rows':0,'status':'SOURCE_FILE_LABEL_ONLY_NOT_STATISTICALLY_INDEPENDENT','stratum_pair_counts':{}})
                        group['rows']+=1
                        if gid in olddev:
                            item['status']='PREVIOUS_DEVELOPMENT_GROUP_EXCLUDED'
                            continue
                        pair=record.get('pair'); schema=record.get('schema')
                        if not isinstance(pair,list) or len(pair)!=2 or not all(isinstance(q,str) for q in pair):
                            raise ValueError('INVALID_SOURCE_PAIR_STRUCTURE')
                        if not isinstance(schema,dict) or not schema or not all(isinstance(cols,dict) for cols in schema.values()):
                            raise ValueError('INVALID_ORIGINAL_SCHEMA_STRUCTURE')
                        item['original_sql_sha256']=[sha(q.encode()) for q in pair]
                        if pair[0]==pair[1]:
                            item['status']='BYTE_IDENTICAL_PAIR_EXCLUDED_STRUCTURALLY'
                            continue
                        shapes=[lexical_shape(q,schema) for q in pair]
                        stratum=first_stratum(shapes)
                        complexity=sum(s['token_count']+8*max(0,s['select_count']-1)+4*s['join_tokens']+4*s['aggregate_calls']+4*s['set_operations'] for s in shapes)
                        item.update(lexical_shapes=shapes,stratum=stratum,token_complexity=complexity)
                        if stratum is None:
                            item['status']='NO_REGISTERED_LEXICAL_STRATUM'
                            continue
                        item['status']='STRATUM_CANDIDATE_BEFORE_GROUP_MEDIAN_AND_DEDUP'
                        group['stratum_pair_counts'][stratum]=group['stratum_pair_counts'].get(stratum,0)+1
                        compact={k:item[k] for k in ('source_path','source_file_sha256','line_1based','byte_offset','byte_length','raw_line_sha256','source_group_id','stratum','token_complexity','original_sql_sha256')}
                        compact['tie_hash']=tie(seed,'PAIR',gid,*item['original_sql_sha256'],item['raw_line_sha256'])
                        buckets[gid,stratum].append(compact)
                    except (ValueError,TypeError,KeyError,UnicodeError) as exc:
                        item.update(status='INVENTORY_FAILURE_RETAINED_NO_REPLACEMENT',error_type=type(exc).__name__,error=str(exc))
                        report['failed_inventory_rows']+=1
                    finally:
                        statuses[item['status']]+=1
                        ledger.write(canonical(item).decode()+'\n')
                        if row_count%500==0:
                            ledger.flush()
            actual=digest.hexdigest()
            verified=actual==source['sha256'] and row_count==source['previous_frozen_pairs'] and offset==source['bytes']
            report['sources'].append({'dataset':source['dataset'],'sha256':actual,'bytes':offset,'pairs':row_count,'matches_frozen':verified})
            ledger.flush(); os.fsync(ledger.fileno()); save()
            if not verified:
                raise ValueError('FROZEN_SOURCE_IDENTITY_OR_DENOMINATOR_MISMATCH')
        if ccounts['leetcode']['NULL_UNSPECIFIED'] != protocol['source_denominators']['expected_previously_reported_LeetCode_null_contract_rows'] or sum(ccounts['leetcode'].values()) != 23994:
            raise ValueError('LEETCODE_CONTRACT_AXIS_DENOMINATOR_MISMATCH')
        if sum(gid.startswith('reserved:') for gid in groups) != len(private_hashes):
            raise ValueError('KNOWN_RESERVE_GROUP_EXCLUSION_COUNT_MISMATCH')
        representatives=defaultdict(list)
        for (gid,stratum),items in buckets.items():
            ranked=sorted(items,key=lambda x:(x['token_complexity'],x['tie_hash'],x['raw_line_sha256']))
            chosen=dict(ranked[(len(ranked)-1)//2])
            chosen['group_stratum_pair_count']=len(ranked)
            chosen['median_rank_1based']=(len(ranked)-1)//2+1
            chosen['group_order_hash']=tie(seed,'GROUP',stratum,gid)
            representatives[stratum].append(chosen)
        selected=[]; used_groups=set(); used_sql=set(); attempts=[]; strata=[]
        for stratum in protocol['stratum_priority']:
            count=0
            ordered=sorted(representatives[stratum],key=lambda x:(x['group_order_hash'],x['source_group_id']))
            for rep in ordered:
                item=dict(rep)
                if count>=4:
                    item['selection_status']='STRATUM_CAP_NOT_SELECTED'
                elif rep['source_group_id'] in used_groups:
                    item['selection_status']='SOURCE_GROUP_ALREADY_SELECTED_IN_PRIOR_STRATUM'
                elif set(rep['original_sql_sha256']) & used_sql:
                    item['selection_status']='CROSS_GROUP_EXACT_SQL_HASH_DUPLICATE_EXCLUDED'
                else:
                    item['selection_status']='SELECTED_PRE_REPLAY_NO_OUTCOMES'
                    selected.append(rep); count+=1
                    used_groups.add(rep['source_group_id']); used_sql.update(rep['original_sql_sha256'])
                attempts.append(item)
            strata.append({'stratum':stratum,'candidate_source_labels':len(ordered),'selected_groups':count,'shortfall_from_four':4-count})
        cases=[]
        for index, rep in enumerate(selected):
            with Path(rep['source_path']).open('rb') as stream:
                stream.seek(rep['byte_offset']); raw=stream.read(rep['byte_length'])
            if sha(raw)!=rep['raw_line_sha256']:
                raise ValueError('SELECTED_ORIGINAL_LINE_CHANGED')
            record=json.loads(raw)
            case={'id':f'dev03_{index+1:02d}','case_index_0based':index,'source_group_id':rep['source_group_id'],'source_record':record,'source':{'dataset':'leetcode','path':rep['source_path'],'file_sha256':rep['source_file_sha256'],'line_1based':rep['line_1based'],'raw_line_sha256':rep['raw_line_sha256'],'upstream_commit':protocol['upstream_commit']},'original_sql_sha256':rep['original_sql_sha256'],'schema_sha256':sha(canonical(record['schema'])),'constraint_sha256':sha(canonical(record['constraint'])) if 'constraint' in record else None,'constraint_field_present':'constraint' in record,'provenance_eligibility':{'contract_source':contract_axis(record),'business_contract_truth':'UNVERIFIED','pair_label_truth':'UNVERIFIED','SQL_semantic_fidelity':'UNPROVEN','natural_business_origin':'UNKNOWN','source_group_independence':'ORIGINAL_SOURCE_FILE_LABEL_DEDUP_ONLY_NO_STATISTICAL_GUARANTEE'},'selection':rep,'exposure':'PRIOR_FULL_48910_QUERY_APPLICABILITY_SCAN_PLUS_CURRENT_LEXICAL_DEVELOPMENT_SELECTION','status':'DEVELOPMENT_HOLD_NOT_HIDDEN_TEST'}
            if [sha(q.encode()) for q in record['pair']]!=case['original_sql_sha256']:
                raise ValueError('SELECTED_SQL_IDENTITY_MISMATCH')
            cases.append(case)
        selected_bytes=b''.join(canonical(x)+b'\n' for x in cases)
        for path,raw_out in [(out/'selected.jsonl',selected_bytes),(out/'selection_attempts.jsonl',b''.join(canonical(x)+b'\n' for x in attempts)),(out/'source_groups.json',json.dumps(list(groups.values()),ensure_ascii=False,indent=2).encode()+b'\n')]:
            with path.open('xb') as stream:
                stream.write(raw_out)
        selected_export.parent.mkdir(parents=True,exist_ok=True)
        with selected_export.open('xb') as stream:
            stream.write(selected_bytes)
        report.update(status='COMPLETE_STATIC_SELECTION_NOT_EXECUTED',selection_performed=True,inventory_status_counts=dict(statuses),contract_source_counts={k:dict(v) for k,v in ccounts.items()},strata=strata,selected_pairs=len(cases),selected_query_slots=2*len(cases),source_groups_selected=len(used_groups),selected_path=str(selected_export),selected_run_copy_path=str(out/'selected.jsonl'),selected_sha256=sha(selected_bytes),source_group_cross_split_rule='previous six development and four known reserve groups excluded before selection; no reserve SQL decoded',cross_selected_group_SQL_overlap=0,SQL_or_parser_or_solver_executed=False,usage={'wall_seconds':time.monotonic()-start,'peak_rss_bytes_macos':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss},science_status='HOLD')
    except BaseException as exc:
        report.update(status='FAILED_OR_PARTIAL_NO_SELECTED_DATASET_CLAIM',error_type=type(exc).__name__,error=str(exc),inventory_status_counts=dict(statuses),contract_source_counts={k:dict(v) for k,v in ccounts.items()})
        raise
    finally:
        ledger.flush(); os.fsync(ledger.fileno()); ledger.close(); save()
    print(json.dumps({'status':report['status'],'selected_pairs':report['selected_pairs'],'strata':report['strata'],'inventory_status_counts':report['inventory_status_counts'],'contract_source_counts':report['contract_source_counts'],'usage':report['usage']}))

if __name__=='__main__':
    main()
