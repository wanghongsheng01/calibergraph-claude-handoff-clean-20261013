"""Prepare one-case worker diff from frozen pilot13; never execute it."""
from pathlib import Path
import difflib,hashlib,json
P=Path(__file__).resolve().parent
src=P.parent/'calibergraph_polygon_pilot_20261012_13/slot_worker.py'
s=src.read_text();old=s
expected=json.loads((src.parent/'FREEZE.json').read_text())['files_sha256']['slot_worker.py']
assert hashlib.sha256(src.read_bytes()).hexdigest()==expected

def change(a,b):
    global s
    assert s.count(a)==1,a
    s=s.replace(a,b)
change("sys.path[:0]=[str(HERE/'runtime_local'),str(HERE/'dependencies_local')]", "PILOT=HERE.parent/'calibergraph_polygon_pilot_20261012_13'\nsys.path[:0]=[str(PILOT/'runtime_local'),str(PILOT/'dependencies_local'),str(PILOT)]")
change('from replay import replay','from case1172_adapter import load_contract, replay_lifted')
change('    case_id,mode,fd,outpath,deadline=sys.argv[1:]','    if not json.loads((HERE/\'FREEZE.json\').read_text())[\'solver_execution_authorized\']:\n        raise RuntimeError(\'Prepared adapter only; scientific execution not authorized in this batch\')\n    case_id,mode,fd,outpath,deadline=sys.argv[1:]\n    if case_id != \'thrombosis_prediction__1172\' or mode not in (\'UA\',\'precise\'):\n        raise ValueError(\'Only frozen #1172 UA/precise allowed\')')
a="                inventory=json.loads((HERE/'inputs_local'/f'{case_id}.json').read_text())\n                schema=[]\n                for table in inventory['tables']:\n                    schema.append({'TableName':table['table'],'PKeys':[],'FKeys':[],\n                                   'Others':[{'Name':c['name'],'Type':{'INTEGER':'int','TEXT':'varchar'}[c['source_type']]} for c in table['columns']]})\n                constraints=inventory['proposed_polygon_constraint_entries']"
b="                t=time.monotonic();contract=load_contract(HERE.parent/'calibergraph_coverage_boundary_20261012_09/sources_local'/case_id)\n                schema=contract['schema'];constraints=contract['constraints']"
change(a,b)
change('                t=time.monotonic();env=environment.Environment', '                env=environment.Environment')
change("                case_dir=HERE/'inputs_local'/case_id", "                case_dir=contract['source']")
change("(out/'witness.json').write_text(json.dumps(raw[1],indent=2)+'\\n')", "(out/'abstract_witness.json').write_text(json.dumps(raw[1],indent=2)+'\\n')")
change("result['replay']=timed('replay',replay)(case_dir,inventory,raw[1])", "result['replay']=timed('replay',replay_lifted)(contract,raw[1])\n                        (out/'witness.json').write_text(json.dumps(result['replay']['concrete'],indent=2)+'\\n')")
change("result['interpretation']='N=1 symbolic typed fragment; no whole SQLite-domain equivalence claim'", "result['interpretation']='Frozen #1172 N=1 observation quotient; original SQL/DDL retained; adapter is not generic REAL/DATE support or unmodified baseline'\n                result['countermodel_lifting']='Validate abstract C first, apply frozen quotient lift, then original full-C replay; no repairs or retries'")
(P/'slot_worker.py').write_text(s)
(P/'INTEGRATION.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),s.splitlines(True),fromfile='pilot13/slot_worker.py',tofile='adapter15/slot_worker.py')))
print('Prepared worker only; source SHA',expected)
