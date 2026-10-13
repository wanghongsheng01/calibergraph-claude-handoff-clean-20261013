"""SQLite semantic unit tests and parse/encode-only integration. Native subprocess forbidden."""
from pathlib import Path
import copy,hashlib,itertools,json,math,sqlite3,sys,time
P=Path(__file__).resolve().parent;ROOT=P.parent
sys.path.insert(0,str(P))
from case1172_adapter import *
START=time.monotonic();events=[]
def audit(event,args):
    if event in ('subprocess.Popen','os.system','os.fork','os.posix_spawn'):
        events.append(event);raise AssertionError('No native child or scientific solver permitted')
sys.addaudithook(audit)
c=load_contract(ROOT/'calibergraph_coverage_boundary_20261012_09/sources_local/thrombosis_prediction__1172')
def original_outputs(db):return [db.execute((c['source']/s).read_text()).fetchall() for s in ['gold.sql','predicted.sql']]
def insert(db,table,values):
    cols=next(t['columns'] for t in c['tables'] if t['table']==table)
    names=[x['name'] for x in cols]
    db.execute('INSERT INTO '+q(table)+' ('+','.join(map(q,names))+') VALUES ('+','.join('?' for _ in names)+')',[values.get(x) for x in names])
values=[None,-math.inf,-1e300,-2**63,-1.5,-0.0,0,1,math.nextafter(2.0,-math.inf),2,2.0,math.nextafter(2.0,math.inf),3,2**53,2**63-1,1e300,math.inf,math.nan,'2','2.0','2e0',' 2 ','02','2.0000000000000001','2x','NaN','Inf','',b'2',b'\xff',sqlite3.Binary(b'\x00')]
sexes=[None,'M','m','M ','M\x00',b'M',2]
dates=[0,'0000-00-00','not-a-date',2.25,b'\xff',math.inf]
ids=[-2**63,-1,0,1,2**53,2**63-1]
checks=[]
for idx,(value,sex) in enumerate(itertools.product(values,sexes)):
    db=fresh(c);key=ids[idx%len(ids)]
    insert(db,'Patient',{'ID':key,'SEX':sex,'Birthday':dates[idx%len(dates)]})
    insert(db,'Laboratory',{'ID':key,'Date':dates[idx%len(dates)],'T-BIL':value,'TP':math.inf,'RF':b'\xff'})
    if idx%2:insert(db,'Examination',{'ID':key if idx%3 else None,'aCL IgG':-1.5,'Examination Date':dates[idx%len(dates)]})
    db.commit();before=original_outputs(db)
    projected=project_original(c,db);after=replay_lifted(c,projected)
    assert before==after['outputs'],(repr(value),repr(sex),before,after)
    checks.append({'input_tbil':repr(value),'input_sex':repr(sex),'stored_tbil_type':db.execute('SELECT typeof("T-BIL") FROM Laboratory').fetchone()[0],'outputs':before,'preserved':True})
    db.close()
# Illegal UTF-8 TEXT is observed by SQLite expressions, never decoded by Python.
db=fresh(c);insert(db,'Patient',{'ID':1,'SEX':'M'});insert(db,'Laboratory',{'ID':1,'Date':0,'T-BIL':0})
db.execute("UPDATE Laboratory SET \"T-BIL\"=CAST(X'ff' AS TEXT)");db.execute("UPDATE Patient SET SEX=CAST(X'ff' AS TEXT)");db.commit()
assert original_outputs(db)==replay_lifted(c,project_original(c,db))['outputs'];db.close()
# Empty/deleted table patterns permitted by original FK. Reject other patterns explicitly.
presence=[]
for patient,lab,exam in itertools.product([False,True],repeat=3):
    if lab and not patient:continue
    db=fresh(c)
    if patient:insert(db,'Patient',{'ID':1,'SEX':'M'})
    if lab:insert(db,'Laboratory',{'ID':1,'Date':0,'T-BIL':2.0})
    if exam:insert(db,'Examination',{'ID':1 if patient else None})
    db.commit();a=project_original(c,db);assert original_outputs(db)==replay_lifted(c,a)['outputs'];presence.append([patient,lab,exam]);db.close()
# Existing full-C legal control; used solely for semantic unit testing, never as solver seed.
control_file=ROOT/'calibergraph_sampled_diagnostic_20261012_07/science/RESULT.json'
old=json.loads(control_file.read_text())['known_control']['database'];db=fresh(c)
for table,t in old.items():
    for row in t['rows']:insert(db,table,dict(zip(t['columns'],row)))
db.commit();abstract=project_original(c,db);lifted=replay_lifted(c,abstract)
assert original_outputs(db)==lifted['outputs']==[[(1,)],[(0,)]];db.close()
# Unbounded abstract integer renaming is explicit and declared, not overflow clipping.
wide=copy.deepcopy(abstract)
for table in ('patient','laboratory'):
    wide[table][1][wide[table][0].index('id')]=10**200
wide['laboratory'][1][wide['laboratory'][0].index('date')]=-10**200
assert replay_lifted(c,wide)['outputs']==[[(1,)],[(0,)]]
for v in [-10**200,10**200]:
    x=copy.deepcopy(wide);x['laboratory'][1][x['laboratory'][0].index('t-bil')]=v
    expected=[[(0,)],[(0,)]] if v<2 else [[(1,)],[(1,)]]
    assert replay_lifted(c,x)['outputs']==expected
rejections=[]
def rejected(name,fn):
    try:fn()
    except (ValueError,sqlite3.IntegrityError):rejections.append(name)
    else:raise AssertionError('Expected rejection: '+name)
x=copy.deepcopy(abstract);x['laboratory'][1][x['laboratory'][0].index('id')]=99
rejected('abstract dangling FK not repaired',lambda:lift_abstract(c,x))
x=copy.deepcopy(abstract);x['laboratory'][1][x['laboratory'][0].index('date')]=None
rejected('abstract NULL date PK not filled',lambda:lift_abstract(c,x))
x=copy.deepcopy(abstract);x['patient'].append(x['patient'][1][:]);rejected('abstract N2',lambda:lift_abstract(c,x))
x=copy.deepcopy(abstract);x.pop('examination');rejected('missing unused table',lambda:lift_abstract(c,x))
x=copy.deepcopy(abstract);x['laboratory'][1][x['laboratory'][0].index('t-bil')]=1.5
rejected('float passed as abstract Int',lambda:lift_abstract(c,x))
rejected('bound2 requires new proof',lambda:load_contract(c['source'],2))
db=fresh(c);db.execute('PRAGMA foreign_keys=OFF');insert(db,'Laboratory',{'ID':9,'Date':0,'T-BIL':2});db.commit()
rejected('original invalid FK',lambda:project_original(c,db));db.close()
db=fresh(c);insert(db,'Patient',{'ID':1,'SEX':'M'});insert(db,'Patient',{'ID':2,'SEX':'M'});db.commit()
rejected('original N2',lambda:project_original(c,db));db.close()
db=fresh(c);insert(db,'Patient',{'ID':1,'SEX':'M'});db.execute('CREATE TEMP TABLE Laboratory AS SELECT * FROM main.Laboratory');db.execute('INSERT INTO temp.Laboratory(ID, Date, \"T-BIL\") VALUES(99,0,2)')
rejected('TEMP shadowing original schema',lambda:project_original(c,db));db.close()
db=fresh(c);db.execute("ATTACH ':memory:' AS extra")
rejected('attached schema outside contract',lambda:project_original(c,db));db.close()
# Negative control: naive int(v) destroys the just-above-2 predicate.
v=math.nextafter(2.0,math.inf);assert int(v)==2 and v>2.0
# Real pinned Polygon parse+encode; fail before both possible solver entry points.
sys.path[:0]=[str(ROOT/'calibergraph_polygon_pilot_20261012_13/runtime_local'),str(ROOT/'calibergraph_polygon_pilot_20261012_13/dependencies_local')]
from polygon.environment import Environment
from polygon.smt.formula import FormulaManager
class NoScientificSolve(BaseException):pass
boundaries=[]
def stop(self,*args,**kwargs):boundaries.append('ENCODE_COMPLETE_SOLVER_NOT_CALLED');raise NoScientificSolve()
FormulaManager.search=stop;FormulaManager.solve_precise=stop
for precise in [False,True]:
    env=Environment(copy.deepcopy(c['schema']),copy.deepcopy(c['constraints']),bound=1,time_budget=3)
    try:env.check(*[(c['source']/s).read_text() for s in ['gold.sql','predicted.sql']],use_precise_encoding=precise,solver_timeout_seconds=3)
    except NoScientificSolve:pass
    else:raise AssertionError('Encoding did not reach protected solver boundary')
assert len(boundaries)==2 and events==[]
out={'status':'PASS','sqlite_version':sqlite3.sqlite_version,'boundary_value_sex_combinations':len(checks),'boundary_checks':checks,'presence_cases':presence,'invalid_utf8_text_pass':True,'known_control_sha256':hashlib.sha256(control_file.read_bytes()).hexdigest(),'known_control_outputs':lifted['outputs'],'control_supplied_to_solver':False,'negative_tests_rejected':rejections,'naive_integerization_falsified_at':repr(v),'schema_tables':3,'schema_columns':64,'full_C_entries':c['constraints'],'parse_encode_only_modes':boundaries,'new_scientific_solver_calls':0,'native_process_events':events,'elapsed_s':time.monotonic()-START}
with (P/'TEST_RESULTS.revision02.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in out.items() if k not in ['boundary_checks','full_C_entries']},default=str))
