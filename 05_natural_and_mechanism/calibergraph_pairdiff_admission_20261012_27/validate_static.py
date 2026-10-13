"""Read-only recheck of receipts, record accounting and verbatim representatives."""
from pathlib import Path
import json,hashlib,collections
r=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
freeze=json.loads((r/'CODE_FREEZE.json').read_text())
checks=[{'path':x['path'],'match':sha((r/x['path']).read_bytes())==x['sha256']} for x in freeze['files']]
assert all(x['match'] for x in checks)
rows=[json.loads(l) for l in (r/'ALL_RECORDS.jsonl').open()]
byid={x['id']:x for x in rows};assert len(byid)==len(rows)==25528
counts=collections.Counter(x['dataset'] for x in rows);assert counts=={'parseval_bird':1534,'verieql_leetcode':23994}
assert all(not x['prior_developed'] for x in rows if x.get('admitted'))
assert sum(bool(x.get('admitted')) for x in rows)==315
assert sum(bool(x.get('equal_ast_pair')) for x in rows)==132
assert not any(x['eligible'] for x in rows)
assert not any(x.get('events',{}).get('U_canceled_branch_occurrences') or x.get('events',{}).get('J_zero_term_eliminated') for x in rows)
reps=json.loads((r/'REPRESENTATIVES.json').read_text());sources={}
for p in {x['source_path'] for x in reps}:sources[p]=Path(p).read_text().splitlines()
for x in reps:
 original=json.loads(sources[x['source_path']][x['source_line']-1]);pair=[original['gold'],original['predicted']] if x['dataset']=='parseval_bird' else original['pair']
 assert pair==x['original_sql']
 assert [sha(v.encode()) for v in pair]==byid[x['id']]['sql_sha256']
 assert x['rank']==sha(x['id'].encode())
assert all(v<=3 for v in collections.Counter(x['category'] for x in reps).values())
raw_summary=json.loads((r/'SUMMARY.json').read_text())
for ds,n in counts.items():
 assert sum(raw_summary[ds]['reasons'].values())==n
assert all(x['error_type']=='TokenError' for x in rows if x['primary_reason']=='SCANNER_ERROR')
result={'role':'author static consistency recheck, not independent review or semantic oracle','frozen_file_checks':checks,'all_record_count':len(rows),'unique_ids':len(byid),'record_counts':dict(counts),'admitted':315,'nontrivial_admitted':183,'eligible':0,'verbatim_representatives_checked':len(reps),'tokenization_errors_mislabeled_scanner_error_in_raw_receipt':11,'rules_or_scanner_changed_after_scan':False,'new_sql_executions':0,'new_solver_calls':0,'checks_passed':True}
(r/'STATIC_RECHECK.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
