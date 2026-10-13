from pathlib import Path
import json,hashlib,csv
root=Path(__file__).resolve().parent;ws=root.parent
paths=['calibergraph_polygon_pilot_20261012_13/SUMMARY.json','calibergraph_polygon_case1172_20261012_16/SUMMARY.json','calibergraph_polygon_case1261_20261012_17/SUMMARY.json']
rows=[];sources=[]
for rel in paths:
 p=ws/rel;x=json.loads(p.read_text());sources.append({'path':rel,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
 for d in x.get('slots',x.get('rows',[])):
  st=d.get('stages_seconds') or {k:d.get(k+'_seconds') for k in ['imports','schema_C','parse','encode','search_including_solver','solver_calls','decode','replay']}
  rows.append({'source':rel,'case':d.get('case',x.get('case')),'mode':d['mode'],'status':d['status'],'worker_wall_s':d.get('wall_seconds',d.get('wall_s',d.get('wall_elapsed_s'))),**st})
keys=['imports','schema_C','parse','encode','search_including_solver','solver_calls','decode','replay']
sums={k:sum(d[k] or 0 for d in rows) for k in keys};wall=sum(d['worker_wall_s'] for d in rows)
report={'source_files':sources,'rows':rows,'sums':sums,'worker_wall_sum':wall,'shares_of_worker_wall':{k:v/wall for k,v in sums.items()},'schema_C_plus_encode_s':sums['schema_C']+sums['encode'],'schema_C_plus_encode_share':(sums['schema_C']+sums['encode'])/wall,'limitations':['8 exposed slots across4 querypairs; not a batch experiment','source-specific N<=1 adapters and different modes; no population estimate','imports/startup process costs and generic AST parse caching belong to strong engineering controls','schema_C field measures setup construction, not all downstream constraint solving','solver_calls is nested inside search_including_solver; do not sum both','no per-target time savings or cache hit rate measured','decode/replay null for UNSAT not evidence of zero cost for all tasks','no causal cost-ablation or Amdahl bound for unseen natural batches'], 'new_SQL_calls':0,'new_solver_calls':0}
(root/'SAVED_COST_INVENTORY.json').write_text(json.dumps(report,indent=2))
by_mode={}
for mode in sorted({d['mode'] for d in rows}):
 selected=[d for d in rows if d['mode']==mode]
 mode_sums={k:sum(d[k] or 0 for d in selected) for k in keys}
 mode_wall=sum(d['worker_wall_s'] for d in selected)
 by_mode[mode]={'n':len(selected),'wall_s':mode_wall,'stage_sums':mode_sums,
  'solver_share':mode_sums['solver_calls']/mode_wall,
  'schema_plus_encode_share':(mode_sums['schema_C']+mode_sums['encode'])/mode_wall}
(root/'SAVED_COST_BY_MODE.json').write_text(json.dumps(by_mode,indent=2))
with (root/'SAVED_COST_INVENTORY.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
print(json.dumps({k:v for k,v in report.items() if k not in ('rows','source_files')},indent=2))
