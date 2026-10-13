"""Single process: guard, SQLite control, one pinned disprove and independent replay."""
from pathlib import Path
import json
import os
import sys
import time
import traceback

P = Path(__file__).resolve().parent
sys.path.insert(0, str(P))
from guard import Guard, check_contender
mode, lockfd, pipefd, lifefd, threshold, directory = sys.argv[1:]
OUT = Path(directory)
guard = Guard(int(lockfd), int(pipefd), int(lifefd), int(threshold))
lock_path = P.parent / "calibergraph_launch_protocol_v2_20261012_05/runtime/owned.lock"
(OUT/"LOCK_CHECK.json").write_text(json.dumps({"contender_blocked":check_contender(lock_path)}))
if mode == "synthetic_memory":
    retained = bytearray(80*1024**2)
    time.sleep(5)
    raise RuntimeError("Memory guard failed")
if mode == "synthetic_deadline":
    time.sleep(5)
    raise RuntimeError("Parent deadline failed")
if mode == "synthetic_silence":
    guard.done.set(); guard.thread.join()
    time.sleep(5)
    raise RuntimeError("Parent silence detector failed")
assert mode == "science"

START = time.monotonic()
R = {"status":"STARTED","phase":"INIT","disprove_calls":0,"solver_check_calls":0,
     "generation_calls":0,"scientific_retries":0,"generated_candidates":[],"generations":[],
     "candidate_replays":[],"versions":{},"known_control_supplied_to_generator":False}

def serial(value):
    if value is None or isinstance(value,(str,int,float,bool)): return value
    if isinstance(value,(list,tuple)): return [serial(v) for v in value]
    if isinstance(value,dict): return {str(k):serial(v) for k,v in value.items()}
    return {"type":type(value).__name__,"value":str(value)}

def event(phase, state, **data):
    R["phase"] = phase
    item={"t_s":time.monotonic()-START,"phase":phase,"state":state,**serial(data)}
    with (OUT/"STAGES.jsonl").open("a") as f: f.write(json.dumps(item)+"\n")

def checkpoint():
    R["wall_s"] = time.monotonic()-START
    (OUT/"RESULT.json").write_text(json.dumps(serial(R),indent=2)+"\n")

def main():
    import sqlite3
    from collections import Counter
    BASE=P.parent/"calibergraph_parseval_admission_20261011_03"
    INPUT=P.parent/"calibergraph_distinct_evidence_20261012_03/sources_local"
    queries=[(INPUT/f"case1172.{side}.sql").read_text() for side in ("gold","predicted")]
    ddl=(INPUT/"case1172.full-schema.sql").read_text()
    quote=lambda name:'"'+name.replace('"','""')+'"'
    def fresh():
        db=sqlite3.connect(":memory:")
        db.execute("PRAGMA foreign_keys=ON")
        assert db.execute("PRAGMA foreign_keys").fetchone()==(1,)
        db.executescript(ddl)
        return db
    def replay(data):
        db=fresh()
        try:
            for name in ("Patient","Examination","Laboratory"):
                table=data[name]
                names=table["columns"]; rows=table["rows"]
                stmt=f'INSERT INTO {quote(name)} ('+','.join(map(quote,names))+') VALUES ('+','.join('?' for _ in names)+')'
                db.executemany(stmt,rows)
            fk=db.execute("PRAGMA foreign_key_check").fetchall()
            integrity=db.execute("PRAGMA integrity_check").fetchall()
            outputs=[db.execute(q).fetchall() for q in queries]
            return {"foreign_key_check":fk,"integrity_check":integrity,"outputs":outputs,
                    "different":Counter(outputs[0])!=Counter(outputs[1])}
        finally:db.close()

    event("FULL_C_AND_KNOWN_CONTROL","START")
    control={}; metadata={}
    db=fresh()
    try:
        actual=db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
        assert actual==[("Examination",),("Laboratory",),("Patient",)]
        for name in ("Patient","Examination","Laboratory"):
            cols=db.execute(f'PRAGMA table_info({quote(name)})').fetchall()
            metadata[name]={"columns":cols,"foreign_keys":db.execute(f'PRAGMA foreign_key_list({quote(name)})').fetchall(),
                            "indexes":db.execute(f'PRAGMA index_list({quote(name)})').fetchall()}
            names=[c[1] for c in cols]
            values={"Patient":{"ID":1,"SEX":"M"},"Laboratory":{"ID":1,"Date":"2000-01-01","T-BIL":2.0}}
            control[name]={"columns":names,"rows":[] if name=="Examination" else [[values[name].get(c) for c in names]]}
        # Independent explicit source-contract checks plus backend enforcement.
        assert len(metadata["Patient"]["columns"])==7
        assert len(metadata["Examination"]["columns"])==13
        assert len(metadata["Laboratory"]["columns"])==44
        assert [c[1] for c in metadata['Patient']['columns'] if c[5]]==['ID']
        assert [c[1] for c in metadata['Laboratory']['columns'] if c[5]]==['ID','Date']
        assert sum(len(v['foreign_keys']) for v in metadata.values())==2
        for n in ('Laboratory','Examination'):
            fk=metadata[n]['foreign_keys'][0]
            assert fk[2:7]==('Patient','ID','ID','CASCADE','CASCADE')
    finally: db.close()
    control_result=replay(control)
    assert control_result['outputs']==[[(1,)],[(0,)]]
    assert not control_result['foreign_key_check'] and control_result['integrity_check']==[('ok',)]
    R['known_control']={"kind":"OUR_CONSTRUCTED_CONTROL_NOT_AUTHOR_WITNESS","database":control,
                        "metadata":metadata,"check":control_result,"supplied_to_generator":False}
    event("FULL_C_AND_KNOWN_CONTROL","PASS",outputs=control_result['outputs']);checkpoint()

    event("RUNTIME_IMPORT","START")
    sys.path[:0]=[str(BASE/'dependencies_local/site-packages'),str(BASE/'sources_local/parseval_official/src')]
    import importlib
    import sqlglot,z3,sqlalchemy
    pm=importlib.import_module('parseval.main')
    gm=importlib.import_module('parseval.generator.generate')
    from parseval.generator import GenerationConfig
    from parseval.db_manager import Connect
    R['versions']={'python':sys.version,'sqlite':sqlite3.sqlite_version,'sqlglot':sqlglot.__version__,
                   'z3':z3.get_version_string(),'sqlalchemy':sqlalchemy.__version__}
    assert sqlglot.__version__=='23.12.1' and z3.get_version()==(4,16,0,0) and sqlalchemy.__version__=='2.0.49'
    event('RUNTIME_IMPORT','PASS',versions=R['versions'])

    # Observers forward identical args/returns; no additional generation callbacks.
    orig_parse=sqlglot.parse
    def parse(*args,**kwargs):
        selected=bool(args and args[0] in queries)
        if selected:event('ORIGINAL_SQL_PARSE','START',side=queries.index(args[0]))
        answer=orig_parse(*args,**kwargs)
        if selected:event('ORIGINAL_SQL_PARSE','PASS',statements=len(answer))
        return answer
    sqlglot.parse=parse
    orig_catalog=pm.Catalog.from_ddl.__func__
    def catalog(cls,*args,**kwargs):
        event('OFFICIAL_CONSTRAINT_LOAD','START')
        answer=orig_catalog(cls,*args,**kwargs)
        R['official_catalog']=[{'table':t.name.qualified_name,'columns':[c.name.text for c in t.columns],
                               'constraints':[type(c).__name__ for c in t.constraints]} for t in answer.tables()]
        event('OFFICIAL_CONSTRAINT_LOAD','PASS',tables=R['official_catalog']);return answer
    pm.Catalog.from_ddl=classmethod(catalog)
    orig_lower=gm.lower_query
    def lower(*args,**kwargs):
        event('QUERY_LOWERING','START')
        answer=orig_lower(*args,**kwargs)
        event('QUERY_LOWERING','PASS');return answer
    gm.lower_query=lower
    orig_solve=gm.solve
    def solve(*args,**kwargs):
        event('GENERATOR_SOLVE','START')
        answer=orig_solve(*args,**kwargs)
        event('GENERATOR_SOLVE','END',status=str(answer.status));return answer
    gm.solve=solve
    orig_check=z3.Solver.check
    def check(self,*args,**kwargs):
        R['solver_check_calls']+=1
        answer=orig_check(self,*args,**kwargs)
        event('Z3_CHECK','END',result=str(answer));return answer
    z3.Solver.check=check
    orig_generate=pm.generate
    def generate(sql,*args,**kwargs):
        R['generation_calls']+=1
        event('GENERATION','START',side=queries.index(sql));checkpoint()
        answer=orig_generate(sql,*args,**kwargs)
        summary={'side':queries.index(sql),'nonempty':answer.nonempty,'reached':answer.reached,'covered':answer.covered,
                 'timed_out':answer.timed_out,'unsupported':answer.unsupported,
                 'attempts':[{'label':a.label,'status':str(a.status),'accepted':a.accepted,'reason':a.reason} for a in answer.attempts]}
        R['generations'].append(summary)
        event('GENERATION','END',**summary);checkpoint();return answer
    pm.generate=generate
    orig_load=Connect.load
    def load(self,instance):
        data={t.name.qualified_name:{'columns':[c.name.text for c in t.columns],
                                   'rows':[list(row) for row in instance.rows(t.relation)]} for t in instance.catalog.tables()}
        R['generated_candidates'].append({'database':data,'official_outputs':[]})
        event('CANDIDATE_LOAD','START',candidate=len(R['generated_candidates'])-1,
              row_counts={n:len(t['rows']) for n,t in data.items()})
        checkpoint()
        answer=orig_load(self,instance)
        event('CANDIDATE_LOAD','PASS');return answer
    Connect.load=load
    orig_execute=Connect.execute
    def execute(self,sql,*args,**kwargs):
        event('ORIGINAL_QUERY_EXECUTION','START',side=queries.index(sql) if sql in queries else None)
        answer=orig_execute(self,sql,*args,**kwargs)
        if sql in queries:
            R['generated_candidates'][-1]['official_outputs'].append({'side':queries.index(sql),'rows':answer})
        event('ORIGINAL_QUERY_EXECUTION','END',rows=answer);return answer
    Connect.execute=execute
    orig_differ=pm.differ
    def differ(*args,**kwargs):
        answer=orig_differ(*args,**kwargs)
        event('DIFFERENCE_CHECK','END',different=answer,inputs=args);return answer
    pm.differ=differ
    config=GenerationConfig(timeout_ms=5000,time_limit_s=360,min_string_length=1,speculate=True,seed=0,set_semantics=False)
    event('OFFICIAL_DISPROVE','START');R['disprove_calls']=1;checkpoint()
    began=time.monotonic()
    answer=pm.disprove(*queries,ddl,'sqlite:///:memory:','sqlite',config=config,timeout_s=15,set_semantics=False)
    R['baseline_wall_s']=time.monotonic()-began
    R['baseline_verdict']=answer.verdict.value;R['baseline_reason']=answer.reason;R['baseline_results']=answer.results
    event('OFFICIAL_DISPROVE','END',verdict=answer.verdict.value,reason=answer.reason);checkpoint()

    event('INDEPENDENT_CANDIDATE_REPLAY','START')
    for i,candidate in enumerate(R['generated_candidates']):
        checked=replay(candidate['database'])
        official=[entry['rows'] for entry in candidate['official_outputs']]
        checked['candidate']=i
        checked['official_outputs_match']=official==checked['outputs']
        R['candidate_replays'].append(checked)
        assert not checked['foreign_key_check'] and checked['integrity_check']==[('ok',)]
        assert checked['official_outputs_match']
    R['all_candidate_replays_complete']=True
    R['status']='COMPLETED_BASELINE_DIAGNOSTIC'
    event('INDEPENDENT_CANDIDATE_REPLAY','PASS',count=len(R['candidate_replays']))

try:
    main()
except BaseException as error:
    R['status']='ERROR_NOT_ALGORITHM_FAILURE'
    R['error']={'type':type(error).__name__,'message':str(error),'phase':R['phase']}
    (OUT/'error.txt').write_text(traceback.format_exc())
    event(R['phase'],'ERROR',error=R['error'])
finally:
    checkpoint()
    guard.finish()
