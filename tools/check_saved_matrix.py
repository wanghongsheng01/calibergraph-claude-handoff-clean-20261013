"""Read saved artifacts only. No SQLite import, no subprocess and no solver."""
import argparse,collections,json,zipfile
p=argparse.ArgumentParser();p.add_argument('--zip',required=True);a=p.parse_args()
with zipfile.ZipFile(a.zip) as z:
 rows=json.loads(z.read('matrix29/MATRIX.json'));selection=json.loads(z.read('matrix29/SELECTION.json'))['selected']
 assert len(selection)==33 and len(rows)==66 and len({(r['case_id'],r['system']) for r in rows})==66
 counts={s:dict(collections.Counter(r['status'] for r in rows if r['system']==s)) for s in ['parseval','polygon']}
 assert counts['parseval']=={'VALIDATED_NEQ':18,'SAMPLED_AGREEMENT_NOT_PROOF':8,'INVALID_ORIGINAL_SQL':3,'UNSUPPORTED_OR_UNKNOWN':1,'CONTROLLER_10S_DEADLINE':3}
 assert counts['polygon']=={'UNSUPPORTED_SCHEMA_MAPPING':25,'INVALID_ORIGINAL_SQL':3,'UNSUPPORTED_QUERY_SEMANTICS':2,'VALIDATED_NEQ':1,'BOUNDED_SYMBOLIC_UNSAT_NOT_SQLITE_EQ':1,'INVALID_OR_NON_DISTINGUISHING_WITNESS':1}
 candidates=[n for n in z.namelist() if n.startswith('matrix29/run_01/') and n.rsplit('/',1)[-1].startswith('candidate_') and n.endswith('.json')]
 assert len(candidates)==116
 print(json.dumps({'pairs':33,'slots':66,'candidate_files':116,'statuses':counts,'SQL_or_solver_executed':False},indent=2))
