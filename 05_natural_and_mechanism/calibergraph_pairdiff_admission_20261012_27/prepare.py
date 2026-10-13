import pathlib,json,hashlib,re,subprocess,datetime
ROOT=pathlib.Path(__file__).resolve().parent; WS=ROOT.parent
sha=lambda b:hashlib.sha256(b).hexdigest()
files=subprocess.check_output(['rg','--files','-g','*.sql','-g','*.json','-g','*.jsonl',str(WS)],text=True).splitlines()
selected=[]; known={};errors=[]
for x in files:
 p=pathlib.Path(x); rel=str(p.relative_to(WS)); parts=p.parts
 if not rel.startswith('calibergraph_') or p.is_relative_to(ROOT):continue
 if any(z in rel for z in ['round04_author_backup','dependencies_local','upstream_local','runtime_local','reserve_private','/protected/','/literature','/ledger/']):continue
 take=p.suffix=='.sql' or bool(re.search(r'/data/(development[^/]*|probe_pool)\.jsonl$',rel)) or p.name in ['CANDIDATES.json','natural_fixtures.json'] or '/inputs_local/' in rel
 if not take or p.stat().st_size>4*1024*1024:continue
 b=p.read_bytes();selected.append({'path':rel,'sha256':sha(b)})
 def collect(v):
  if isinstance(v,str) and re.match(r'^\s*(SELECT|WITH)\b',v,re.I):known.setdefault(sha(v.encode()),[]).append(rel)
  elif isinstance(v,dict):
   for z in v.values():collect(z)
  elif isinstance(v,list):
   for z in v:collect(z)
 try:
  if p.suffix=='.sql':collect(b.decode())
  elif p.suffix=='.jsonl':
   for line in b.decode().splitlines():
    if line.strip():collect(json.loads(line))
  else:collect(json.loads(b))
 except Exception as e:errors.append({'path':rel,'error':type(e).__name__})
cases=json.loads((WS/'calibergraph_coverage_boundary_20261012_09/CANDIDATES.json').read_text())
ex={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'artifact_scope':selected,'errors':errors,'sql_hashes':known,'parseval_case_ids':[str(x['index']) for x in cases], 'limitation':'Artifact-level known development exclusion, not proof of never-accessed data. All public sources have prior corpus-level static exposure. Protected/reserve_private not read.'}
(ROOT/'EXCLUSION_FREEZE.json').write_text(json.dumps(ex,ensure_ascii=False,indent=2))
inv=json.loads((WS/'calibergraph_batch_mechanism_20261012_26/workload/inventory.json').read_text())
src=[]
for p,v in inv['provenance'].items():
 if p.endswith(('disprove-bird.jsonl','/sources_local/schema.json','/public_leetcode/leetcode.jsonlines')):
  actual=sha(pathlib.Path(p).read_bytes());assert actual==v['sha256'];src.append({'path':p,'sha256':actual,'bytes':v['bytes']})
wheel=WS/'calibergraph_parseval_admission_20261011_03/dependencies_local/wheels/sqlglot-23.12.1-py3-none-any.whl'
freeze={'created_utc':ex['created_utc'],'protocol_sha256':sha((ROOT/'PROTOCOL.md').read_bytes()),'exclusions_sha256':sha((ROOT/'EXCLUSION_FREEZE.json').read_bytes()),'sources':src,'parser':{'path':str(wheel),'sha256':sha(wheel.read_bytes()),'version':'23.12.1'},'outcome_fields_used':False,'new_final_test':False}
(ROOT/'INPUT_FREEZE.json').write_text(json.dumps(freeze,indent=2));print(json.dumps({'source_files':len(src),'prior_artifacts':len(selected),'known_sql_hashes':len(known),'explicit_parseval_exclusions':len(cases),'errors':errors},indent=2))
