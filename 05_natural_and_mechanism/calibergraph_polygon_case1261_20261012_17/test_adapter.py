"""#1261 independent predicate boundary tests, no scientific solver or subprocess."""
from pathlib import Path
import copy,itertools,json,math,sys,time
P=Path(__file__).resolve().parent;ROOT=P.parent;sys.path.insert(0,str(P))
from case1261_adapter import *
start=time.monotonic();events=[]
def no_process(event,args):
    if event in ('subprocess.Popen','os.system','os.fork','os.posix_spawn'):
        events.append(event);raise AssertionError('No scientific/native launch allowed in tests')
sys.addaudithook(no_process)
c=load_contract(ROOT/'calibergraph_coverage_boundary_20261012_09/sources_local/thrombosis_prediction__1261')
def put(db,table,**values):
    cols=next(t['columns'] for t in c['tables'] if t['table']==table);names=[x['name'] for x in cols]
    db.execute('INSERT INTO '+q(table)+' ('+','.join(map(q,names))+') VALUES ('+','.join('?' for _ in names)+')',[values.get(x) for x in names])
def outputs(db):return [db.execute((c['source']/n).read_text()).fetchall() for n in ('gold.sql','predicted.sql')]
rfs=[None,-math.inf,-1e300,-2**63,-1,0,2,3,19,20,20.0,21,100,2**63-1,math.inf,math.nan,'',' ','-1','0','2','19','20','20.0','020','20x','100','3','z',b'0',b'20',b'\xff']
ths=[None,-2**63,-1,0,-0.0,1,math.nextafter(0.0,1),2**63-1,math.inf,math.nan,'0','0.0','0e0',' 0 ','0x','',b'0']
keys=[-2**63,-1,0,1,2**53,2**63-1];dates=[0,'0000-00-00','not-date',b'\xff',math.inf]
checks=[];example=None
for i,(rf,th) in enumerate(itertools.product(rfs,ths)):
    db=fresh(c);key=keys[i%len(keys)]
    put(db,'Patient',ID=key);put(db,'Laboratory',ID=key,Date=dates[i%len(dates)],RF=rf);put(db,'Examination',ID=key,Thrombosis=th)
    db.commit();before=outputs(db);abstract=project_original(c,db);after=replay_lifted(c,abstract)
    assert before==after['outputs'],(rf,th,before,after)
    # Independent expected branch from original SQLite predicates; assert actual 0/1, not just mutual equality.
    predicates=db.execute('SELECT RF<20,Thrombosis=0 FROM Laboratory CROSS JOIN Examination').fetchone()
    expected=1 if predicates==(1,1) else 0
    assert before==[[(expected,)],[(expected,)]]
    rf_a=abstract['laboratory'][1][abstract['laboratory'][0].index('rf')]
    th_a=abstract['examination'][1][abstract['examination'][0].index('thrombosis')]
    assert (rf_a is not None and rf_a<20)==(predicates[0]==1)
    assert (th_a is not None and th_a==0)==(predicates[1]==1)
    checks.append({'rf_input':repr(rf),'thrombosis_input':repr(th),'stored_rf_type':db.execute('SELECT typeof(RF) FROM Laboratory').fetchone()[0],'predicates':predicates,'output':expected})
    if rf==3 and th==0:assert predicates[0]==0  # proves naive numeric RF semantics wrong
    if rf==100 and th==0:assert predicates[0]==1
    if rf=='0' and th==0:example=abstract
    db.close()
presence=[]
for p,l,e,null_id in itertools.product([False,True],repeat=4):
    if l and not p or e and not null_id and not p:continue
    db=fresh(c)
    if p:put(db,'Patient',ID=1)
    if l:put(db,'Laboratory',ID=1,Date=0,RF='0')
    if e:put(db,'Examination',ID=None if null_id else 1,Thrombosis=0)
    db.commit();before=outputs(db);assert replay_lifted(c,project_original(c,db))['outputs']==before
    presence.append([p,l,e,null_id,before]);db.close()
# Invalid UTF-8 TEXT remains an engine-side observation, never decoded by Python.
db=fresh(c);put(db,'Patient',ID=1);put(db,'Laboratory',ID=1,Date=0,RF='0');put(db,'Examination',ID=1,Thrombosis=0)
db.execute("UPDATE Laboratory SET RF=CAST(X'ff' AS TEXT)");db.commit();assert outputs(db)==replay_lifted(c,project_original(c,db))['outputs'];db.close()
rejects=[]
def reject(name,fn):
    try:fn()
    except (ValueError,sqlite3.IntegrityError):rejects.append(name)
    else:raise AssertionError('Must reject '+name)
for table,col,value,name in [('laboratory','id',999,'invalid FK'),('laboratory','date',None,'NULL date PK'),('patient','id',None,'NULL parent PK'),('laboratory','rf','3','string is not abstract Int')]:
    a=copy.deepcopy(example);a[table][1][a[table][0].index(col)]=value;reject(name,lambda:lift_abstract(c,a))
a=copy.deepcopy(example);a['examination'].append(a['examination'][1][:]);reject('N2 abstract',lambda:lift_abstract(c,a))
a=copy.deepcopy(example);a.pop('examination');reject('missing table',lambda:lift_abstract(c,a))
reject('bound2 not proved',lambda:load_contract(c['source'],2))
reject('1172 query hash refused',lambda:load_contract(ROOT/'calibergraph_coverage_boundary_20261012_09/sources_local/thrombosis_prediction__1172'))
db=fresh(c);db.execute('CREATE TEMP TABLE Laboratory(ID)');reject('TEMP shadow',lambda:project_original(c,db));db.close()
db=fresh(c);db.execute("ATTACH ':memory:' AS extra");reject('ATTACH',lambda:project_original(c,db));db.close()
a=copy.deepcopy(example)
for table in ('patient','laboratory','examination'):a[table][1][a[table][0].index('id')]=10**200
for rf in [-10**200,20,10**200]:
    a['laboratory'][1][a['laboratory'][0].index('rf')]=rf
    assert replay_lifted(c,a)['outputs']==([[(1,)],[(1,)]] if rf<20 else [[(0,)],[(0,)]])
# Actual fixed parser/encoder, both original solver entry points replaced by immediate stop.
sys.path[:0]=[str(ROOT/'calibergraph_polygon_pilot_20261012_13/runtime_local'),str(ROOT/'calibergraph_polygon_pilot_20261012_13/dependencies_local')]
from polygon.environment import Environment
from polygon.smt.formula import FormulaManager
class StopBeforeSolve(BaseException):pass
boundaries=[]
def stop(*args,**kwargs):boundaries.append('ENCODE_COMPLETE_SOLVER_NOT_RUN');raise StopBeforeSolve()
FormulaManager.search=stop;FormulaManager.solve_precise=stop
for mode in [False,True]:
    env=Environment(copy.deepcopy(c['schema']),copy.deepcopy(c['constraints']),bound=1,time_budget=3)
    try:env.check(*[(c['source']/n).read_text() for n in ('gold.sql','predicted.sql')],use_precise_encoding=mode,solver_timeout_seconds=3)
    except StopBeforeSolve:pass
    else:raise AssertionError('Missing solver boundary')
assert len(boundaries)==2 and not events
result={'status':'PASS','sqlite_version':sqlite3.sqlite_version,'case':'1261','boundary_combinations':len(checks),'checks':checks,'presence_cases':presence,'negative_cases_rejected':rejects,'invalid_utf8_text_pass':True,'numeric_RF_shortcut_disproved':['stored TEXT 3 <20 is false','stored TEXT 100 <20 is true'],'parse_encode_modes':boundaries,'native_events':events,'scientific_solver_calls':0,'elapsed_s':time.monotonic()-start,'constraints':c['constraints']}
with (P/'TEST_RESULTS.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in result.items() if k not in ['checks','presence_cases','constraints']}))
