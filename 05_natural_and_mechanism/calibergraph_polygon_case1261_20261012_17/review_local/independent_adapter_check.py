"""Independent checks of actual author adapter against separate SQLite oracle."""
import copy,hashlib,importlib.util,itertools,json,pathlib,sqlite3,sys
HERE=pathlib.Path(__file__).resolve().parent;RUN=HERE.parent
sys.dont_write_bytecode=True
spec=importlib.util.spec_from_file_location('candidate_adapter',RUN/'case1261_adapter.py');adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)
# Load only definitions/fixtures preceding the independent check loops.
ns={'__file__':str(HERE/'independent_sqlite_quotient.py')};exec((HERE/'independent_sqlite_quotient.py').read_text().split('count=0;examples=[]')[0],ns)
c=adapter.load_contract(ns['SRC']);cases=0
for rf,th in itertools.product(ns['vals'],repeat=2):
 d=ns['new']();ns['fill'](d,{'Patient':[ns['row']('Patient',42)],'Examination':[ns['row']('Examination',42,th=th)],'Laboratory':[ns['row']('Laboratory',42,rf=rf)]})
 data=adapter.project_original(c,d)
 expected=ns['projection'](d)
 assert {t:[list(r) for r in rs] for t,rs in expected.items()}=={t:data[t.lower()][1:] for t in expected}
 replay=adapter.replay_lifted(c,data);assert replay['full_C_valid'] and replay['outputs']==ns['outputs'](d)
 cases+=1;d.close()
def good():
 return {t.lower():[[x.lower() for x in cols],ns['row'](t,10,rf=0,th=0,date=0)] for t,cols in ns['COLS'].items()}
def setval(data,t,col,v):data[t][1][data[t][0].index(col)]=v
negative=[]
def reject(label,func):
 try:func()
 except (ValueError,TypeError,KeyError):negative.append(label)
 else:raise AssertionError(label+' accepted')
for t,col,value in [('laboratory','id',11),('examination','id',11),('patient','id',None),('laboratory','date',None),('laboratory','id',None),('patient','sex','M'),('examination','thrombosis',False),('laboratory','rf',0.0)]:
 data=good();setval(data,t,col,value);reject(str((t,col,value)),lambda:adapter.lift_abstract(c,data))
for t in ['patient','examination','laboratory']:
 data=good();data[t].append(data[t][1][:]);reject(t+' N2',lambda:adapter.lift_abstract(c,data))
reject('bound2',lambda:adapter.load_contract(ns['SRC'],2))
reject('1172 hash',lambda:adapter.load_contract(ns['SRC'].parent/'thrombosis_prediction__1172'))
for sql in ['CREATE TEMP TABLE Patient(ID INTEGER)',"ATTACH DATABASE ':memory:' AS outside"]:
 d=adapter.fresh(c);d.execute(sql);reject(sql,lambda:adapter.project_original(c,d));d.close()
d=adapter.fresh(c);d.execute('PRAGMA foreign_keys=OFF');d.execute('INSERT INTO Examination(ID) VALUES(99)');reject('original orphan FK',lambda:adapter.project_original(c,d));d.close()
d=adapter.fresh(c);d.execute('INSERT INTO Patient(ID) VALUES(1),(2)');reject('original N2',lambda:adapter.project_original(c,d));d.close()
# Invalid UTF8 TEXT stays inside SQLite expressions; no decoding raw observed text.
d=adapter.fresh(c);d.execute('INSERT INTO Patient(ID) VALUES(1)');d.execute("INSERT INTO Examination(ID,Thrombosis) VALUES(1,CAST(X'FF' AS TEXT))");d.execute("INSERT INTO Laboratory(ID,Date,RF) VALUES(1,0,CAST(X'FF' AS TEXT))");assert adapter.replay_lifted(c,adapter.project_original(c,d))['outputs']==ns['outputs'](d);d.close()
reverse=0
for rf,th in itertools.product([None,-10**80,-1,0,1,19,20,21,10**80],repeat=2):
 data=good();setval(data,'laboratory','rf',rf);setval(data,'examination','thrombosis',th)
 for t in data:setval(data,t,'id',10**100)
 setval(data,'laboratory','date',10**100)
 out=adapter.replay_lifted(c,data);value=int(rf is not None and rf<20 and th is not None and th==0)
 assert out['outputs']==[[(value,)],[(value,)]];reverse+=1
result={'status':'PASS','solver_calls':0,'sqlite_version':sqlite3.sqlite_version,'adapter_sha256':hashlib.sha256((RUN/'case1261_adapter.py').read_bytes()).hexdigest(),'worker_sha256':hashlib.sha256((RUN/'slot_worker.py').read_bytes()).hexdigest(),'actual_adapter_boundary_cases':cases,'negative_rejections':negative,'invalid_utf8_text':'PASS','reverse_arbitrary_Int_cases':reverse,'constraints':c['constraints']}
(HERE/'independent_adapter_check.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
