"""Only stdlib JSON/text extraction. Never import SQL engines or research code."""
from pathlib import Path
from collections import Counter
import hashlib
import json
import re

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent
protocol = json.loads((BASE / 'SELECTION_PROTOCOL.json').read_text())
sha = lambda data: hashlib.sha256(data).hexdigest()
for name, expected in protocol['source_hashes'].items():
    assert sha((ROOT / name).read_bytes()) == expected
rows = [json.loads(s) for s in (ROOT / protocol['source_jsonl']).read_text().splitlines() if s.strip()]
schemas = json.loads((ROOT / protocol['source_schema']).read_text())
anchor = tuple(protocol['anchor'])
ident = lambda r: (r['dbid'], str(r['index']))
pairhash = lambda r: sha(json.dumps(sorted([r['gold'], r['predicted']]), ensure_ascii=False).encode())
rank = lambda r: sha(('cg-boundary09-v1|' + '|'.join(ident(r))).encode())
groups = {'EQ': [], 'NEQ': [], 'UNRESOLVED': []}
inventory = []
for line, r in enumerate(rows, 1):
    q = r.get('gold', '') + '\n' + r.get('predicted', '')
    lexical = bool(re.search(r'\bJOIN\b', q, re.I) and re.search(r'\b(?:COUNT|SUM|AVG|MIN|MAX)\s*\(', q, re.I))
    has_c = r.get('dbid') in schemas and bool(schemas[r['dbid']])
    group = r['verdict'] if r['verdict'] in ('EQ', 'NEQ') else 'UNRESOLVED' if r['verdict'] in protocol['selection_rule']['unresolved_verdicts'] else None
    entry = {'line_1based': line, 'dbid': r['dbid'], 'index': str(r['index']), 'official_verdict': r['verdict'], 'lexical_join_aggregate': lexical, 'full_source_schema_present': has_c, 'stratum': group, 'rank': rank(r), 'selected': False, 'selection_note': 'outside lexical pool' if not lexical else 'eligible not selected'}
    inventory.append(entry)
    if lexical and has_c and group and ident(r) != anchor:
        groups[group].append((rank(r), line, r, entry))

ar = next(r for r in rows if ident(r) == anchor)
selected = [('ANCHOR', rows.index(ar)+1, ar)]
dbcounts = Counter([ar['dbid']]); hashes = {pairhash(ar)}
for group in protocol['selection_rule']['stratum_order']:
    count = 0
    for _, line, r, entry in sorted(groups[group]):
        if count >= protocol['selection_rule']['strata'][group]:
            entry['selection_note'] = 'stratum quota already full'; continue
        if dbcounts[r['dbid']] >= 2:
            entry['selection_note'] = 'database diversity cap'; continue
        if pairhash(r) in hashes:
            entry['selection_note'] = 'exact unordered pair duplicate'; continue
        selected.append((group, line, r)); dbcounts[r['dbid']] += 1; hashes.add(pairhash(r)); count += 1
        entry['selected'] = True; entry['selection_note'] = 'selected deterministic stratum rank'
inventory[rows.index(ar)]['selected'] = True
inventory[rows.index(ar)]['selection_note'] = 'previously exposed fixed anchor'
out = BASE / 'sources_local'; out.mkdir(exist_ok=False)
records = []
for group, line, r in selected:
    key = r['dbid'] + '__' + str(r['index']); d = out / key; d.mkdir()
    full_c = ';\n'.join(schemas[r['dbid']])
    contents = {'gold.sql': r['gold'], 'predicted.sql': r['predicted'], 'full-schema.sql': full_c, 'official-record.json': json.dumps(r, ensure_ascii=False, indent=2)+'\n'}
    for name, content in contents.items(): (d/name).write_text(content)
    rec = {'case_id':key, 'dbid':r['dbid'], 'index':str(r['index']), 'stratum':group, 'rank':rank(r), 'artifact_line_1based':line, 'official_verdict':r['verdict'], 'official_reason':r.get('reason'), 'official_end_to_end_s':r.get('end_to_end_s'), 'official_results_present':r.get('results') is not None, 'source_table_count':len(schemas[r['dbid']]), 'role':'EXPOSED_DEVELOPMENT_ONLY', 'independent_final_test':False, 'files':{name:{'local_path':str((d/name).relative_to(BASE)), 'sha256':sha((d/name).read_bytes())} for name in contents}, 'new_sql_calls':0, 'new_solver_calls':0}
    records.append(rec)
summary = {'records':len(rows), 'official_verdict_counts':dict(Counter(r['verdict'] for r in rows)), 'lexical_join_aggregate':sum(x['lexical_join_aggregate'] for x in inventory), 'lexical_pool_verdict_counts':dict(Counter(x['official_verdict'] for x in inventory if x['lexical_join_aggregate'])), 'missing_schema_in_lexical_pool':sum(x['lexical_join_aggregate'] and not x['full_source_schema_present'] for x in inventory), 'selected_count':len(records), 'selected_strata':dict(Counter(x['stratum'] for x in records)), 'selected_databases':dict(dbcounts), 'all_read_records_exposed_development':True, 'protocol_sha256':sha((BASE/'SELECTION_PROTOCOL.json').read_bytes()), 'extractor_sha256':sha(Path(__file__).read_bytes()), 'science_executions':0}
for filename, value in [('CANDIDATES.json',records),('SELECTION_INVENTORY.json',inventory),('EXTRACTION_RECEIPT.json',summary)]:
    (BASE/filename).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(summary,ensure_ascii=False))
for r, (_,_,raw) in zip(records, selected):
    print(json.dumps({'case':r['case_id'],'verdict':r['official_verdict'],'reason':r['official_reason'],'time':r['official_end_to_end_s'],'gold':raw['gold'],'predicted':raw['predicted'],'tables':r['source_table_count']},ensure_ascii=False))
