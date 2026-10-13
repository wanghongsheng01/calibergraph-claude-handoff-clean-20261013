"""Independent SQLite check for #1261; no author adapter import, no solver."""
import hashlib,itertools,json,pathlib,sqlite3
ROOT=pathlib.Path(__file__).resolve().parents[2]
SRC=ROOT/'calibergraph_coverage_boundary_20261012_09/sources_local/thrombosis_prediction__1261'
OUT=pathlib.Path(__file__).parent
DDL=(SRC/'full-schema.sql').read_text()
SQL=[(SRC/f).read_text() for f in ('gold.sql','predicted.sql')]
def qi(s):return '"'+s.replace('"','""')+'"'
def new():
 d=sqlite3.connect(':memory:');d.execute('PRAGMA foreign_keys=ON');d.executescript(DDL);return d
seed=new();COLS={t:[r[1] for r in seed.execute('PRAGMA table_info('+qi(t)+')')] for t in ('Patient','Examination','Laboratory')};seed.close()
def abstract_db():
 d=sqlite3.connect(':memory:');d.execute('PRAGMA foreign_keys=ON')
 for t,cols in COLS.items():
  spec=[qi(c)+' INTEGER'+(' NOT NULL' if (t,c) in [('Patient','ID'),('Laboratory','ID'),('Laboratory','Date')] else '') for c in cols]
  if t=='Patient':spec+=['PRIMARY KEY (ID)']
  if t=='Laboratory':spec+=['PRIMARY KEY (ID,Date)']
  if t!='Patient':spec+=['FOREIGN KEY(ID) REFERENCES Patient(ID)']
  d.execute('CREATE TABLE '+qi(t)+'('+','.join(spec)+')')
 return d
def insert(d,t,row):
 d.execute('INSERT INTO '+qi(t)+' VALUES ('+','.join('?' for _ in COLS[t])+')',row)
def outputs(d):return [d.execute(s).fetchall() for s in SQL]
def projection(d):
 result={}
 for t,cols in COLS.items():
  expr=[]
  for c in cols:
   x=qi(c)
   inner='1' if c=='ID' else '0'
   if (t,c)==('Laboratory','RF'):inner=f'CASE WHEN {x}<20 THEN 0 ELSE 20 END'
   if (t,c)==('Examination','Thrombosis'):inner=f'CASE WHEN {x}=0 THEN 0 ELSE 1 END'
   expr.append(f'CASE WHEN {x} IS NULL THEN NULL ELSE {inner} END')
  result[t]=d.execute('SELECT '+','.join(expr)+' FROM '+qi(t)).fetchall()
 return result
def lifting(data):
 result={}
 for t,rs in data.items():
  result[t]=[]
  for r in rs:
   lifted=[]
   for c,v in zip(COLS[t],r):
    if v is None:w=None
    elif c=='ID':w=1
    elif (t,c)==('Laboratory','RF'):w='0' if v<20 else 'z'
    elif (t,c)==('Examination','Thrombosis'):w=0 if v==0 else 1
    else:w=0
    lifted.append(w)
   result[t].append(lifted)
 return result
def fill(d,data):
 for t,rows in data.items():
  for row in rows:insert(d,t,row)
 assert not d.execute('PRAGMA foreign_key_check').fetchall()
 assert d.execute('PRAGMA integrity_check').fetchall()==[('ok',)]
def row(t,id,rf=None,th=None,date='0000-00-00'):
 return [id if c=='ID' else date if (t,c)==('Laboratory','Date') else rf if (t,c)==('Laboratory','RF') else th if (t,c)==('Examination','Thrombosis') else None for c in COLS[t]]
# Storage-class and lexical boundaries, including zero encodings, NUL text and BLOB.
vals=[None,-float('inf'),-100,-1,-0.0,0,0.1,1,2,19,19.999,20,20.0,20.001,21,100,float('inf'),'', '0','00','-0','+0','0.0','0e10',' 0 ','0x0','0x10','1','19','19.99','2','20','020','20.0','20x','200','3','9','100','z','NULL','\x00','0\x00','１９',b'',b'0',b'19',b'20',b'\x00',b'\xff']
count=0;examples=[]
for rf,th in itertools.product(vals,repeat=2):
 d=new();fill(d,{'Patient':[row('Patient',-9223372036854775808)],'Examination':[row('Examination',-9223372036854775808,th=th)],'Laboratory':[row('Laboratory',-9223372036854775808,rf=rf)]})
 a=abstract_db();fill(a,projection(d));l=new();fill(l,lifting(projection(d)))
 assert outputs(d)==outputs(a)==outputs(l),(repr(rf),repr(th),outputs(d),outputs(a),outputs(l))
 if th=='0' and rf in ['19','2','20','3','100','020','20.0']:
  examples.append({'input_rf':rf,'stored':d.execute('SELECT RF,typeof(RF),RF<20 FROM Laboratory').fetchone(),'outputs':outputs(d)})
 count+=1
 for x in [d,a,l]:x.close()
# Every C-valid occupancy and nullable-child shape.
shapes=0
for p,e,l,e_null in itertools.product([False,True],repeat=4):
 if (l or (e and not e_null)) and not p:continue
 data={'Patient':[row('Patient',1)] if p else [],'Examination':[row('Examination',None if e_null else 1,th=0)] if e else [],'Laboratory':[row('Laboratory',1,rf='0')] if l else []}
 d=new();fill(d,data);a=abstract_db();fill(a,projection(d));assert outputs(d)==outputs(a);d.close();a.close();shapes+=1
# Reverse direction accepts all Int predicate classes, not only canonical reps.
reverse=0
for rf,th in itertools.product([None,-10**80,-1,0,1,19,20,21,10**80],repeat=2):
 # Python evaluates exact Int abstract scalar predicate, avoiding SQLite 64-bit limit.
 expected=int(rf is not None and rf<20 and th is not None and th==0)
 data={'Patient':[row('Patient',1)],'Examination':[row('Examination',1,th=th)],'Laboratory':[row('Laboratory',1,rf=rf,date=10**80)]}
 d=new();fill(d,lifting(data));assert outputs(d)==[[(expected,)],[(expected,)]];d.close();reverse+=1
result={'status':'PASS','solver_calls':0,'independent_of_author_adapter':True,'sqlite_version':sqlite3.sqlite_version,'source_hashes':{f:hashlib.sha256((SRC/f).read_bytes()).hexdigest() for f in ['gold.sql','predicted.sql','full-schema.sql']},'column_counts':{t:len(c) for t,c in COLS.items()},'forward_storage_boundary_cases':count,'valid_shape_cases':shapes,'reverse_unbounded_int_class_cases':reverse,'rf_lexical_examples':examples,'scope':'N<=1 per source table; full C; original default SQLite comparison semantics; finite boundary testing supplements proof'}
(OUT/'independent_sqlite_quotient.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
print(json.dumps(result,ensure_ascii=False))
