"""Real parser -> original encoders/formulas -> concrete AST evaluation -> SQLite.
No SMT translation/solver. Single-thread dependency watchdog adapter only.
"""
from pathlib import Path
import collections,hashlib,itertools,json,sqlite3,sys,types,traceback
H=Path(__file__).resolve().parent;P=H.parent/'calibergraph_polygon_pilot_20261012_13'
sys.path[:0]=[str(P/'runtime_local'),str(P/'dependencies_local')]
import mo_imports
class SynchronousWatchdog:
    starts=0
    def __init__(self,*a,**kw):self.daemon=False
    def start(self):type(self).starts+=1
    def join(self,*a,**kw):pass
# mo_imports worker merely reports unresolved exports after a timeout. Resolve the
# real imports synchronously and fail closed on any outstanding export instead.
mo_imports.Thread=SynchronousWatchdog
from polygon.sql_parser import SQLParser
from polygon.schemas import TableSchema,ColumnSchema
from polygon.variables import Database
from polygon.smt.ast import SMTGrouping,And
import polygon.formulas.project as project_module
import polygon.formulas.group_by as group_module
assert not mo_imports._expectations,[(x.module.__name__,x.name) for x in mo_imports._expectations]

class State:
    def __init__(self):self.data={}
    def put(self,k,*args,value):self.data[(k,*args)]=value
    def evaluate(self,n):
        k=type(n).__name__
        if k in ('Int','Bool'):
            assert type(n.x) is (int if k=='Int' else bool);return k,n.x
        fields={'Deleted':['table_id','tuple_id'],'Choice':['table_id','bit_id'],'SMTGrouping':['table_id','tuple_id','group_id'],'SMTCell':['table_id','row_id','column_id'],'SMTNull':['table_id','row_id','column_id']}
        if k in fields:
            v=self.data[(k,*[getattr(n,f) for f in fields[k]])];t='Bool' if k in ('Deleted','SMTGrouping','SMTNull') else 'Int';assert type(v) is (bool if t=='Bool' else int),(k,v);return t,v
        if k=='Not':
            t,v=self.evaluate(n.node);assert t=='Bool';return 'Bool',not v
        if k in ('And','Or'):
            a=[self.evaluate(x) for x in (n.conjunct if k=='And' else n.disjunct)];assert all(t=='Bool' for t,v in a);return 'Bool',(all(v for t,v in a) if k=='And' else any(v for t,v in a))
        if k=='If':
            ta,a=self.evaluate(n.a);tb,b=self.evaluate(n.b);tc,c=self.evaluate(n.c);assert ta=='Bool' and tb==tc;return tb,b if a else c
        if k=='Implies':
            ta,a=self.evaluate(n.premise);tb,b=self.evaluate(n.conclusion);assert ta==tb=='Bool';return 'Bool',(not a) or b
        ta,a=self.evaluate(n.a);tb,b=self.evaluate(n.b)
        if k in ('Eq','Neq','Gt','Gte','Lt','Lte'):
            assert ta==tb,(k,ta,tb);return 'Bool',{'Eq':lambda:a==b,'Neq':lambda:a!=b,'Gt':lambda:a>b,'Gte':lambda:a>=b,'Lt':lambda:a<b,'Lte':lambda:a<=b}[k]()
        if k=='Plus':assert ta==tb=='Int',('ill-sorted Plus',ta,tb);return 'Int',a+b
        raise AssertionError(('Unsupported AST',k))
    def val(self,n):return self.evaluate(n)[1]

class Formulas:
    def __init__(self):self.rows=[];self.under_table_id_to_original={}
    def append(self,n,**kw):self.rows.append(n)
class Env:
    def __init__(self,bound):
        self.db=Database();self.formulas=Formulas();self.counter=0;self.string_hash_table={};self.hash_string_table={}
        self.schema=TableSchema(0,'t',bound,lineage='Input')
        for i,name in enumerate(['x','g']):self.schema.append(ColumnSchema(i,name,'int','t'))
        self.db.add_table(self.schema)
    def string_hash(self, string):
        # Verbatim behavior of frozen Environment.string_hash, no Environment import.
        if not isinstance(string,str):string=str(string)
        if string in self.string_hash_table:return self.string_hash_table[string]
        try:h=int(string)
        except:h=hash(string)
        self.string_hash_table[string]=h;self.hash_string_table[h]=string
        return h
    def next_table_id(self):self.counter+=1;return self.counter
    def grouping(self,*a):return SMTGrouping(*a)
    def copy_cell(self,a,b):return And([a.VAL==b.VAL,a.NULL==b.NULL])

def parse(sql):
    p=CURRENT_PARSER();raw=p.parse(sql);q=p.parse_query(raw);return raw,q

def classes(ver):
    global CURRENT_PARSER
    base=P/'runtime_local/polygon' if ver=='original' else H/('patched_'+ver)/'polygon'
    pm=types.ModuleType('isolated_'+ver+'_parser');exec(compile((base/'sql_parser.py').read_text(),str(base/'sql_parser.py'),'exec'),pm.__dict__);CURRENT_PARSER=pm.SQLParser
    em=types.ModuleType('isolated_'+ver+'_expr');exec(compile((base/'visitors/expression_encoder.py').read_text(),str(base/'visitors/expression_encoder.py'),'exec'),em.__dict__)
    gm=types.ModuleType('isolated_'+ver+'_group');exec(compile((base/'visitors/group_expression_encoder.py').read_text(),str(base/'visitors/group_expression_encoder.py'),'exec'),gm.__dict__)
    gm.ExpressionEncoder=em.ExpressionEncoder
    for m in [project_module,group_module]:m.ExpressionEncoder=em.ExpressionEncoder;m.GroupExpressionEncoder=gm.GroupExpressionEncoder
    return em.ExpressionEncoder,gm.GroupExpressionEncoder

def oracle(sql,rows,deleted):
    c=sqlite3.connect(':memory:');c.execute('PRAGMA threads=0');c.execute('CREATE TABLE t(x INTEGER,g INTEGER)')
    c.executemany('INSERT INTO t VALUES (?,?)',[r for r,d in zip(rows,deleted) if not d]);result=[list(r) for r in c.execute(sql)];c.close();return result

def input_state(rows,deleted):
    s=State()
    for i,(row,d) in enumerate(zip(rows,deleted)):
        s.put('Deleted',0,i,value=d)
        for j,v in enumerate(row):s.put('SMTCell',0,i,j,value=0 if v is None else v);s.put('SMTNull',0,i,j,value=v is None)
    return s

def expression_case(cls,sql,rows,deleted):
    raw,q=parse(sql);env=Env(len(rows));s=input_state(rows,deleted)
    val,null=cls(env.schema,env).expression_for_tuple(q.select_clause.target_list[0],0)
    tv,v=s.evaluate(val);tn,n=s.evaluate(null);assert tv=='Int' and tn=='Bool'
    actual=[[None if n else v]];expected=oracle(sql,rows,deleted)
    return {'parser_json':raw,'parsed_ast':repr(q),'encoded_value':str(val),'encoded_null':str(null),'actual':actual,'sqlite':expected,'matches':actual==expected}

def pipeline_case(cls,gcls,sql,rows,deleted):
    raw,q=parse(sql);env=Env(len(rows));s=input_state(rows,deleted);schema=env.schema;groups={}
    if q.group_by_clause is not None:
        q.group_by_clause.ctx['select_list']=q.select_clause.target_list
        grouped=group_module.FGroupBy(schema,q.group_by_clause,env,len(rows)).output
        first={}
        for i,((x,g),d) in enumerate(zip(rows,deleted)):
            if not d:first.setdefault(g,i)
        for g,idx in first.items():groups[idx]=[i for i,(row,d) in enumerate(zip(rows,deleted)) if not d and row[1]==g]
        for idx in range(len(rows)):
            active=idx in groups
            s.put('Choice',grouped.table_id,idx,value=int(active));s.put('Choice',grouped.table_id,len(rows)+idx,value=int(active))
            s.put('Deleted',grouped.table_id,idx,value=not active);s.put('Deleted',-grouped.table_id,idx,value=not active)
            for i in range(len(rows)):s.put('SMTGrouping',grouped.table_id,i,idx,value=i in groups.get(idx,[]))
        schema=grouped
    f=project_module.FProject(schema,q.select_clause,env,k=max(1,len(rows)));out=f.output;actual=[]
    if q.group_by_clause is None:
        s.put('Choice',out.table_id,0,value=1);s.put('Deleted',out.table_id,0,value=False)
        for j,target in enumerate(q.select_clause.target_list):
            v,n=cls(env.schema,env).expression_for_tuple(target,0);vv,nn=s.val(v),s.val(n);s.put('SMTCell',out.table_id,0,j,value=vv);s.put('SMTNull',out.table_id,0,j,value=nn)
        actual=[[None if s.data[('SMTNull',out.table_id,0,j)] else s.data[('SMTCell',out.table_id,0,j)] for j in range(len(out))]]
    else:
        enc=gcls(schema,env.schema,env)
        for idx in range(out.bound):
            vals=[]
            for j,target in enumerate(q.select_clause.target_list):
                if type(target).__name__=='Attribute':
                    value=rows[groups[idx][0]][env.schema[target.name].column_id] if idx in groups else None;vv=0 if value is None else value;nn=value is None
                else:
                    v,n=enc.expression_for_group(target,idx);vv,nn=s.val(v),s.val(n)
                s.put('SMTCell',out.table_id,idx,j,value=vv);s.put('SMTNull',out.table_id,idx,j,value=nn);vals.append(None if nn else vv)
            if idx in groups:actual.append(vals)
    checks=[s.evaluate(n) for n in env.formulas.rows];assert all(t=='Bool' and v for t,v in checks),('operator_constraints_failed',checks)
    expected=oracle(sql,rows,deleted);bag=lambda rs:collections.Counter(tuple(r) for r in rs)
    return {'parser_json':raw,'parsed_ast':repr(q),'actual':actual,'sqlite':expected,'matches':bag(actual)==bag(expected),'all_real_operator_formulas_satisfied':True,'operator_formula_count':len(checks),'operators':['FGroupBy','FProject'] if q.group_by_clause is not None else ['FProject'],'group_assignments':groups}

def run():
    matrix=[]
    for bound in [0,1,2]:
        for ds in itertools.product([False,True],repeat=bound):
            for filt in ['absent','1','0','NULL']:
                matrix.append({'id':f'b{bound}_{list(ds)}_{filt}','sql':'SELECT COUNT(*)'+('' if filt=='absent' else f' FILTER (WHERE {filt})')+' FROM t','rows':[[None,0]]*bound,'deleted':list(ds)})
    specs=[
      ('empty','SELECT COUNT(*) FROM t',[[None,0]],[True]),
      ('null_row','SELECT COUNT(*) FROM t',[[None,0]],[False]),
      ('duplicates','SELECT COUNT(*) FROM t',[[7,0],[7,0]],[False,False]),
      ('count_x_null','SELECT COUNT(x) FROM t',[[None,0],[7,0]],[False,False]),
      ('count_distinct','SELECT COUNT(DISTINCT x) FROM t',[[7,0],[7,0]],[False,False]),
      ('filter_null_column','SELECT COUNT(*) FILTER (WHERE x) FROM t',[[None,0],[7,0],[0,0]],[False]*3),
      ('group_empty','SELECT g, COUNT(*) FROM t GROUP BY g',[[None,0]],[True]),
      ('group_duplicates','SELECT g, COUNT(*) FROM t GROUP BY g',[[7,1],[7,1],[None,2]],[False]*3),
      ('group_null_keys','SELECT g, COUNT(*) FROM t GROUP BY g',[[None,None],[7,None],[9,2]],[False]*3),
      ('group_false','SELECT g, COUNT(*) FILTER (WHERE 0) FROM t GROUP BY g',[[7,1],[7,1],[None,2]],[False]*3),
      ('group_filter_null','SELECT g, COUNT(*) FILTER (WHERE NULL) FROM t GROUP BY g',[[7,1],[7,1],[None,2]],[False]*3),
      ('group_filter_values','SELECT g, COUNT(*) FILTER (WHERE x) FROM t GROUP BY g',[[None,1],[7,1],[0,2]],[False]*3),
      ('group_deleted','SELECT g, COUNT(*) FILTER (WHERE x) FROM t GROUP BY g',[[8,1],[7,1],[None,2]],[True,False,False]),
      ('group_count_x','SELECT g, COUNT(x) FROM t GROUP BY g',[[None,1],[7,1],[7,1]],[False]*3)]
    results={}
    for ver in ['original','p1','p2','p3']:
        cls,gcls=classes(ver);record={'matrix':[],'pipeline':[]}
        for kind,cases in [('matrix',matrix),('pipeline',[{'id':i,'sql':sql,'rows':rows,'deleted':ds} for i,sql,rows,ds in specs])]:
            for case in cases:
                row=dict(case)
                try:row.update((expression_case(cls,case['sql'],case['rows'],case['deleted']) if kind=='matrix' else pipeline_case(cls,gcls,case['sql'],case['rows'],case['deleted'])));row['status']='PASS' if row['matches'] else 'MISMATCH'
                except Exception as e:row.update(status='ERROR',error=repr(e),traceback=traceback.format_exc())
                record[kind].append(row)
        results[ver]=record
    out={'scope':'Real SQLParser + ExpressionEncoder and FProject/FGroupBy formulas, concrete fixed assignment, SQLite reference; no search or solver; not the complete Environment.check pipeline','watchdog_adapter':{'monitor_instances':SynchronousWatchdog.starts,'real_threads_started':0,'unresolved_exports':len(mo_imports._expectations),'parser_source_changes':'original/P1/P2 unchanged; P3 explicit aggregate FILTER bare identifier fix'},'sqlite_version':sqlite3.sqlite_version,'versions':results}
    (H/'PARSER_RESULTS_V2.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({v:{k:dict(collections.Counter(r['status'] for r in rows)) for k,rows in d.items()} for v,d in results.items()}))
if __name__=='__main__':run()
