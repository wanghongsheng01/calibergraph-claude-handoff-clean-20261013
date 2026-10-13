"""Real COUNT(*) AST; concrete AST evaluation and SQLite oracle, never an SMT solver."""
from pathlib import Path
import difflib,hashlib,itertools,json,sqlite3,sys,time,types
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;P=ROOT/'calibergraph_polygon_pilot_20261012_13'
sys.path[:0]=[str(P/'runtime_local'),str(P/'dependencies_local')]
from polygon.visitors.expression_encoder import ExpressionEncoder
from polygon.ast.expressions.expression import Expression
from polygon.ast.expressions.attribute import Attribute
from polygon.ast.expressions.literal import Literal
from polygon.sql_parser import SQLParser
SOURCE=P/'runtime_local/polygon/visitors/expression_encoder.py'
BEFORE='                            indicators.append(Not(deleted))\n'
AFTER='                        indicators.append(If(Not(deleted), Int(1), Int(0)))\n'

def strict(n,deleted):
    k=type(n).__name__
    if k=='Int':assert type(n.x) is int;return 'Int',n.x
    if k=='Bool':assert type(n.x) is bool;return 'Bool',n.x
    if k=='Deleted':return 'Bool',deleted[n.tuple_id]
    if k=='Not':
        t,v=strict(n.node,deleted);assert t=='Bool',(k,t);return 'Bool',not v
    if k in ('And','Or'):
        xs=[strict(x,deleted) for x in (n.conjunct if k=='And' else n.disjunct)]
        assert all(t=='Bool' for t,v in xs),(k,xs)
        return 'Bool',(all(v for t,v in xs) if k=='And' else any(v for t,v in xs))
    if k=='If':
        ta,a=strict(n.a,deleted);tb,b=strict(n.b,deleted);tc,c=strict(n.c,deleted)
        assert ta=='Bool' and tb==tc,('ill-sorted If',ta,tb,tc);return tb,b if a else c
    if k=='Plus':
        ta,a=strict(n.a,deleted);tb,b=strict(n.b,deleted)
        assert ta==tb=='Int',('ill-sorted Plus',ta,tb);return 'Int',a+b
    if k in ('Eq','Neq'):
        ta,a=strict(n.a,deleted);tb,b=strict(n.b,deleted);assert ta==tb
        return 'Bool',(a==b if k=='Eq' else a!=b)
    raise AssertionError('Unhandled AST '+k)

def matrix(cls):
    rows=[]
    for bound in [0,1,2]:
        for deleted in itertools.product([False,True],repeat=bound):
            for filt,lit in [('absent',None),('true',True),('false',False),('null',None)]:
                node=Expression('count',[False,Attribute('*')],filter_clause=None if filt=='absent' else Literal(lit))
                encoder=cls(types.SimpleNamespace(table_id=0,bound=bound),None)
                value,null=encoder.expression_for_tuple(node,0)
                db=sqlite3.connect(':memory:');db.execute('PRAGMA threads=0');db.execute('CREATE TABLE t(x INTEGER)')
                db.executemany('INSERT INTO t VALUES (?)',[(None,) for d in deleted if not d])
                sql='SELECT COUNT(*)'+('' if filt=='absent' else ' FILTER (WHERE '+{'true':'1','false':'0','null':'NULL'}[filt]+')')+' FROM t'
                expected=db.execute(sql).fetchone()[0];db.close()
                r={'bound':bound,'deleted':list(deleted),'filter':filt,'sqlite_expected':expected,'value_AST':str(value),'null_AST':str(null)}
                try:
                    typ,actual=strict(value,deleted);nt,nv=strict(null,deleted)
                    assert typ=='Int' and nt=='Bool' and not nv
                    r.update(actual=actual,well_sorted=True,matches=actual==expected)
                except AssertionError as e:r.update(well_sorted=False,matches=False,error=repr(e))
                rows.append(r)
    return rows

def run():
    t=time.monotonic();source=SOURCE.read_text();assert source.count(BEFORE)==1
    parser=SQLParser();paths=[]
    for sql in ['SELECT COUNT(*) FROM t','SELECT COUNT(*) FROM t WHERE x = 1']:
        query=parser.parse_query(parser.parse(sql));node=query.select_clause.target_list[0]
        assert node.operator=='count' and node.args[0] is False and node.args[1].name=='*'
        assert node.filter_clause is None and query.group_by_clause is None
        val,null=ExpressionEncoder(types.SimpleNamespace(table_id=0,bound=1),None).expression_for_tuple(node,0)
        paths.append({'sql':sql,'group_by':False,'aggregate_filter':False,'where_present':query.where_clause is not None,'original_count_with_one_matching_live_input':strict(val,[False])[1]})
    original=matrix(ExpressionEncoder)
    wrong=[r for r in original if r['well_sorted'] and not r['matches']]
    sort_errors=[r for r in original if not r['well_sorted']]
    assert wrong and sort_errors
    # Only after observing both defects, produce a separate minimal proposal; old file untouched.
    patched_source=source.replace(BEFORE,AFTER)
    patch=''.join(difflib.unified_diff(source.splitlines(True),patched_source.splitlines(True),fromfile='a/polygon/visitors/expression_encoder.py',tofile='b/polygon/visitors/expression_encoder.py'))
    (HERE/'COUNT_STAR.patch').write_text(patch)
    module=types.ModuleType('count_star_isolated_patch');exec(compile(patched_source,str(SOURCE)+' [isolated patch]','exec'),module.__dict__)
    patched=matrix(module.ExpressionEncoder);assert all(r['matches'] for r in patched)
    assert SOURCE.read_text()==source
    result={'status':'BUG_CONFIRMED_PATCH_UNIT_PASS','source_sha256':hashlib.sha256(source.encode()).hexdigest(),'patch_sha256':hashlib.sha256(patch.encode()).hexdigest(),'patched_source_sha256':hashlib.sha256(patched_source.encode()).hexdigest(),'parsed_paths':paths,'original_rows':original,'patched_rows':patched,'cases_per_version':len(original),'original_value_mismatches':len(wrong),'original_sort_errors':len(sort_errors),'patched_all_pass':True,'old_source_unchanged':True,'solver_calls':0,'complete_natural_query_pipeline_tested':False,'elapsed_s':time.monotonic()-t}
    (HERE/'count_star_results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['original_rows','patched_rows','parsed_paths']}))
if __name__=='__main__':run()
