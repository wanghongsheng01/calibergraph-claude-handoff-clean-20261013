"""A static syntax/admission counter. Never loads a DB driver, Polygon or solver."""
import sys,json,hashlib,time,resource,collections,pathlib,signal,os
from dataclasses import dataclass
ROOT=pathlib.Path(__file__).resolve().parent
FREEZE=json.loads((ROOT/'INPUT_FREEZE.json').read_text())
sys.dont_write_bytecode=True
sys.path.insert(0,FREEZE['parser']['path'])
import sqlglot
from sqlglot import expressions as E
sha=lambda x:hashlib.sha256(x).hexdigest()
def sig(x):return sha(json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode())
class Refuse(Exception):pass
@dataclass(frozen=True)
class N:
 op:str
 data:tuple
 kids:tuple
 types:tuple
def mk(op,data,kids,types):return N(op,tuple(data),tuple(kids),tuple(types))
def nodes(n):
 out=set()
 def rec(a):
  if a is None or a in out:return
  out.add(a)
  for c in a.kids:rec(c)
 rec(n);return out
def tree_size(n):return 0 if n is None else 1+sum(tree_size(c) for c in n.kids)
def normname(s):return str(s).lower()
def colref(e,cols):
 if e.args.get('db') or e.args.get('catalog'):raise Refuse('QUALIFIED_DATABASE_REFERENCE')
 name,qual=normname(e.name),normname(e.table)
 hits=[i for i,(n,q,t) in enumerate(cols) if n==name and (not qual or qual==q)]
 if len(hits)!=1:raise Refuse('UNRESOLVED_OR_AMBIGUOUS_COLUMN')
 return hits[0]
def scalar(e,cols,projection=False):
 if isinstance(e,(E.Alias,E.Paren)):return scalar(e.this,cols,projection)
 if isinstance(e,E.Column):
  i=colref(e,cols);return ('col',i),cols[i][2]
 if isinstance(e,E.Literal):return ('literal',e.is_string,str(e.this)),('LITERAL_TEXT' if e.is_string else 'LITERAL_NUMBER')
 if isinstance(e,E.Null):return ('null',),'NULL'
 if isinstance(e,E.Boolean):return ('boolean',bool(e.this)),'BOOLEAN'
 if projection:raise Refuse('NON_SIMPLE_PROJECTION')
 if isinstance(e,(E.And,E.Or,E.EQ,E.NEQ,E.GT,E.GTE,E.LT,E.LTE,E.Is)):
  a,_=scalar(e.this,cols);b,_=scalar(e.expression,cols)
  if isinstance(e,E.Is) and not isinstance(e.expression,(E.Null,E.Boolean)):raise Refuse('UNSUPPORTED_IS')
  return (e.key,a,b),'BOOLEAN'
 if isinstance(e,E.Not):return ('not',scalar(e.this,cols)[0]),'BOOLEAN'
 if isinstance(e,E.In):
  if e.args.get('query') or any(not isinstance(v,(E.Literal,E.Null,E.Boolean)) for v in e.expressions):raise Refuse('SUBQUERY_OR_NONLITERAL_IN')
  return ('in',scalar(e.this,cols)[0],tuple(scalar(v,cols)[0] for v in e.expressions)),'BOOLEAN'
 raise Refuse('UNSUPPORTED_PREDICATE_'+e.key.upper())
def barriers(q):
 out=set()
 for x in q.walk():
  if isinstance(x,E.AggFunc):out.add('AGGREGATE')
  if isinstance(x,E.Window):out.add('WINDOW')
  if isinstance(x,E.Distinct) or isinstance(x,E.Select) and x.args.get('distinct'):out.add('DISTINCT')
  if isinstance(x,E.Union) and x.args.get('distinct') is not False:out.add('UNION_DISTINCT')
  if isinstance(x,(E.Except,E.Intersect)):out.add('NON_UNION_SET_OPERATION')
  if isinstance(x,E.Group):out.add('GROUP')
  if isinstance(x,E.Having):out.add('HAVING')
  if isinstance(x,E.Order):out.add('ORDER')
  if isinstance(x,(E.Limit,E.Offset)):out.add('LIMIT_OFFSET')
  if isinstance(x,E.With):out.add('CTE')
  if isinstance(x,E.Join):
   if x.args.get('side') or str(x.args.get('kind') or '').upper() in ('SEMI','ANTI') or x.args.get('using') or x.args.get('method'):out.add('OUTER_OR_SPECIAL_JOIN')
 return sorted(out)
def compile_rel(q,schema):
 if isinstance(q,E.Subquery):return compile_rel(q.this,schema)
 if isinstance(q,E.Union):
  a,ac=compile_rel(q.this,schema);b,bc=compile_rel(q.expression,schema)
  if a.types!=b.types:raise Refuse('UNION_OUTPUT_TYPE_MISMATCH')
  if q.args.get('by_name'):raise Refuse('UNION_BY_NAME')
  aa=list(a.kids) if a.op=='union' else [a];bb=list(b.kids) if b.op=='union' else [b]
  return mk('union',[],aa+bb,a.types),ac
 if not isinstance(q,E.Select):raise Refuse('NOT_SELECT_SPJU')
 allowed={'expressions','from','joins','where','kind','hint','distinct','limit'}
 for k,v in q.args.items():
  if v and k not in allowed:raise Refuse('UNSUPPORTED_SELECT_'+k.upper())
 if q.args.get('kind') or q.args.get('hint'):raise Refuse('SELECT_KIND_OR_HINT')
 def relation(e):
  if isinstance(e,E.Table):
   if e.args.get('db') or e.args.get('catalog') or e.args.get('sample') or e.args.get('pivots'):raise Refuse('SPECIAL_TABLE_REFERENCE')
   name=normname(e.name)
   if name not in schema:raise Refuse('UNKNOWN_TABLE')
   if e.args.get('alias') and e.args['alias'].args.get('columns'):raise Refuse('TABLE_COLUMN_ALIAS_LIST')
   cols=[(n,normname(e.alias_or_name),t) for n,t in schema[name]]
   return mk('scan',[name,tuple(schema[name])],[],[t for _,t in schema[name]]),cols
  if isinstance(e,E.Subquery):
   node,cols=compile_rel(e.this,schema)
   if e.args.get('alias') and e.args['alias'].args.get('columns'):raise Refuse('SUBQUERY_COLUMN_ALIAS_LIST')
   return node,[(n,normname(e.alias),t) for n,_,t in cols]
  raise Refuse('UNSUPPORTED_FROM_'+e.key.upper())
 fr=q.args.get('from')
 if fr is None or fr.this is None:raise Refuse('NO_BASE_FROM')
 if fr.expressions:raise Refuse('UNNORMALIZED_MULTI_FROM')
 n,cols=relation(fr.this)
 for j in q.args.get('joins') or []:
  if str(j.args.get('kind') or '').upper() not in ('','INNER','CROSS'):raise Refuse('UNSUPPORTED_JOIN_KIND')
  b,bc=relation(j.this);joined=cols+bc
  pred=scalar(j.args['on'],joined)[0] if j.args.get('on') else ('boolean',True)
  n=mk('join',[pred],[n,b],n.types+b.types);cols=joined
 if q.args.get('where'):
  pred=scalar(q.args['where'].this,cols)[0];n=mk('filter',[pred],[n],n.types)
 exprs=[];out=[]
 for i,e in enumerate(q.expressions):
  if isinstance(e,E.Star) or isinstance(e,E.Column) and isinstance(e.this,E.Star):
   if e.args.get('except') or e.args.get('replace'):raise Refuse('STAR_MODIFIER')
   qual=normname(e.table) if isinstance(e,E.Column) else ''
   ix=[j for j,(_,qq,_) in enumerate(cols) if not qual or qq==qual]
   if not ix:raise Refuse('UNKNOWN_STAR_QUALIFIER')
   for j in ix:exprs.append(('col',j));out.append(cols[j])
  else:
   v,t=scalar(e,cols,True);exprs.append(v)
   nam=normname(e.alias) if isinstance(e,E.Alias) else (normname(e.name) if isinstance(e,E.Column) else '__unnamed_'+str(i))
   out.append((nam,'',t))
 return mk('project',exprs,[n],[c[2] for c in out]),out
def u(xs,types):
 if not xs:return None
 if len(xs)==1:return xs[0]
 return mk('union',[],xs,types)
def difference(a,b,events):
 if a==b:
  events['E_exact_zero']+=1;return None
 if a is None:return mk('neg',[],[b],b.types) if b else None
 if b is None:return a
 if a.op=='union' or b.op=='union':
  aa=list(a.kids) if a.op=='union' else [a];bb=list(b.kids) if b.op=='union' else [b]
  ca,cb=collections.Counter(aa),collections.Counter(bb);common=ca&cb
  if common:
   events['U_canceled_branch_occurrences']+=sum(common.values())
   events['U_canceled_branch_tree_nodes']+=sum(tree_size(n)*v for n,v in common.items())
   ar=list((ca-common).elements());br=list((cb-common).elements())
   return difference(u(ar,a.types),u(br,b.types),events)
 if a.op==b.op and a.data==b.data and a.op in ('project','filter') and a.kids[0].types==b.kids[0].types:
  events['P_common_context' if a.op=='project' else 'S_common_context']+=1
  child=difference(a.kids[0],b.kids[0],events)
  return mk(a.op,a.data,[child],a.types) if child else None
 if a.op==b.op=='join' and a.data==b.data and all(x.types==y.types for x,y in zip(a.kids,b.kids)):
  events['J_exact_identity_opportunity']+=1
  if a.kids[0]==b.kids[0]:
   events['J_zero_term_eliminated']+=1
   c=difference(a.kids[1],b.kids[1],events)
   return mk('join',a.data,[a.kids[0],c],a.types) if c else None
  if a.kids[1]==b.kids[1]:
   events['J_zero_term_eliminated']+=1
   c=difference(a.kids[0],b.kids[0],events)
   return mk('join',a.data,[c,a.kids[1]],a.types) if c else None
 if a.op==b.op=='filter' and a.kids==b.kids and a.data!=b.data:events['S_different_same_input_descriptive']+=1
 return mk('difference',[],[a,b],a.types)
def inspect_pair(a,b,schema,dialect):
 qs=[];flags=set()
 for s in [a,b]:
  if len(s.encode())>32768:raise Refuse('SQL_BYTE_CAP')
  parsed=sqlglot.parse(s,read=dialect)
  if len(parsed)!=1 or parsed[0] is None:raise Refuse('NOT_SINGLE_QUERY')
  q=parsed[0];qs.append(q)
  if sum(1 for _ in q.walk())>500:raise Refuse('AST_NODE_CAP')
  flags.update(barriers(q))
 desc={'barriers':sorted(flags),'ast_nodes':[sum(1 for _ in q.walk()) for q in qs]}
 if flags:return {**desc,'primary_reason':'BARRIER','admitted':False}
 try:
  an,_=compile_rel(qs[0],schema);bn,_=compile_rel(qs[1],schema)
  if an.types!=bn.types:raise Refuse('PAIR_OUTPUT_TYPE_MISMATCH')
 except Refuse as e:return {**desc,'primary_reason':str(e),'admitted':False}
 na,nb=nodes(an),nodes(bn);base=na|nb
 events=collections.Counter();res=difference(an,bn,events);nr=nodes(res)
 saved=len(base)-len(nr);ratio=saved/len(base) if base else 0
 strict=bool(events['U_canceled_branch_occurrences'] or events['J_zero_term_eliminated'])
 equal=an==bn
 qualifies=not equal and strict and saved>=2 and ratio>=.20
 return {**desc,'admitted':True,'primary_reason':'EXACT_PAIR_CACHE_ONLY' if equal else ('GATE_STRUCTURAL_MATCH' if qualifies else ('STRICT_RULE_SMALL_OR_NO_NET_REDUCTION' if strict else 'NO_STRICT_ZERO_ELIMINATION')),
 'events':dict(events),'equal_ast_pair':equal,'tree_nodes':[tree_size(an),tree_size(bn)],'shared_dag_nodes':len(na&nb),'original_shared_dag_nodes':len(base),'residual_dag_nodes':len(nr),'unique_original_nodes_absent_from_residual':len(base-nr),'net_saved_nodes':saved,'net_reduction':ratio,'gate_structural_match':qualifies,
 'original_operator_counts':dict(collections.Counter(n.op for n in base)),'residual_operator_counts':dict(collections.Counter(n.op for n in nr))}
def schemas_from_ddl(ds):
 result={}
 for db,ddls in ds.items():
  schema={}
  for ddl in ddls:
   p=sqlglot.parse_one(ddl,read='sqlite')
   if not isinstance(p,E.Create) or not isinstance(p.this,E.Schema):raise ValueError('unexpected DDL')
   schema[normname(p.this.this.name)]=[(normname(c.name),c.args['kind'].sql()) for c in p.this.expressions if isinstance(c,E.ColumnDef)]
  result[db]=schema
 return result
def summary(rows):
 out={}
 for ds in sorted({r['dataset'] for r in rows}):
  rr=[r for r in rows if r['dataset']==ds];ad=[r for r in rr if r.get('admitted')];good=[r for r in rr if r.get('eligible')]
  def dist(v):
   v=sorted(v)
   return {'n':len(v),'min':v[0] if v else None,'median':v[len(v)//2] if v else None,'p90':v[min(len(v)-1,int(.9*len(v)))] if v else None,'max':v[-1] if v else None}
  out[ds]={'records':len(rr),'prior_developed_exclusions':sum(r['prior_developed'] for r in rr),'reasons':dict(collections.Counter(r['primary_reason'] for r in rr)),
   'barrier_multilabel_counts':dict(collections.Counter(x for r in rr for x in r.get('barriers',[]))),
   'admitted_spju':len(ad),'exact_pair_cache_only':sum(r.get('equal_ast_pair',False) for r in rr),'event_pair_counts':dict(collections.Counter(k for r in ad for k,v in r['events'].items() if v)),
   'eligible_records':len(good),'eligible_unique_pairs':len({r['unordered_pair_context_hash'] for r in good}),'eligible_families':sorted({r['family'] for r in good}),
   'shared_dag_nodes':dist([r['shared_dag_nodes'] for r in ad]),'original_shared_dag_nodes':dist([r['original_shared_dag_nodes'] for r in ad]),'residual_dag_nodes':dist([r['residual_dag_nodes'] for r in ad]),'net_reduction':dist([r['net_reduction'] for r in ad])}
 return out
def main():
 resource.setrlimit(resource.RLIMIT_CPU,(120,120));signal.alarm(240)
 t=time.monotonic();cpu=time.process_time()
 for x in FREEZE['sources']:assert sha(pathlib.Path(x['path']).read_bytes())==x['sha256']
 assert sha((ROOT/'PROTOCOL.md').read_bytes())==FREEZE['protocol_sha256']
 assert sha((ROOT/'EXCLUSION_FREEZE.json').read_bytes())==FREEZE['exclusions_sha256']
 ex=json.loads((ROOT/'EXCLUSION_FREEZE.json').read_text());known=ex['sql_hashes'];known_ids=set(ex['parseval_case_ids'])
 src={pathlib.Path(x['path']).name:x['path'] for x in FREEZE['sources']};ddl=json.loads(pathlib.Path(src['schema.json']).read_text());bird_schemas=schemas_from_ddl(ddl)
 rows=[];eligible_seen=set();cache={}
 with (ROOT/'ALL_RECORDS.jsonl').open('w') as f,(ROOT/'REPRESENTATIVE_POOL.jsonl').open('w') as representatives:
  for ds,path in [('parseval_bird',src['disprove-bird.jsonl']),('verieql_leetcode',src['leetcode.jsonlines'])]:
   for line_no,line in enumerate(pathlib.Path(path).open(),1):
    x=json.loads(line)
    if ds=='parseval_bird':
     a,b=x['gold'],x['predicted'];family=x['dbid'];schema=bird_schemas[family];context=sig(ddl[family]);prior=str(x['index']) in known_ids
    else:
     a,b=x['pair'];family=x['file'];schema={normname(k):[(normname(c),str(v).upper()) for c,v in cols.items()] for k,cols in x['schema'].items()};context=sig([x['schema'],x['constraint']]);prior=False
    ah,bh=sha(a.encode()),sha(b.encode());prior=prior or ah in known or bh in known
    sid=f"{ds}|{family}|{x['index']}|line{line_no}|{sig([ah,bh,context])[:16]}"
    r={'id':sid,'dataset':ds,'source_path':path,'source_line':line_no,'source_index':x['index'],'family':family,'sql_sha256':[ah,bh],'context_sha256':context,'unordered_pair_context_hash':sig([context,sorted([ah,bh])]),'prior_developed':prior,'eligible':False}
    if prior:r.update({'primary_reason':'PRIOR_CASE_DEVELOPMENT_OR_SQL_MATCH','admitted':False})
    else:
     try:r.update(inspect_pair(a,b,schema,'sqlite' if ds=='parseval_bird' else 'mysql'))
     except Refuse as e:r.update({'primary_reason':str(e),'admitted':False})
     except sqlglot.errors.ParseError:r.update({'primary_reason':'PARSE_ERROR','admitted':False})
     except Exception as e:r.update({'primary_reason':'SCANNER_ERROR','admitted':False,'error_type':type(e).__name__,'error':str(e)[:200]})
    r['eligible']=bool(r.get('gate_structural_match'))
    f.write(json.dumps(r,ensure_ascii=False)+'\n');rows.append(r)
    if r.get('admitted'):
     tags=['admitted']
     for key in ['U_canceled_branch_occurrences','J_zero_term_eliminated','P_common_context','S_common_context','S_different_same_input_descriptive']:
      if r['events'].get(key):tags.append(key)
     if r['eligible']:tags.append('eligible')
     representatives.write(json.dumps({'id':sid,'rank':sha(sid.encode()),'tags':tags,'original_sql':[a,b],'source_path':path,'source_line':line_no},ensure_ascii=False)+'\n')
    if len(rows)%1000==0:
     f.flush();print(json.dumps({'processed':len(rows),'cpu_s':round(time.process_time()-cpu,2),'wall_s':round(time.monotonic()-t,2)}),flush=True)
     if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>512*1024*1024:raise RuntimeError('RSS_CAP')
 res=summary(rows);good=[r for r in rows if r.get('eligible')];unique={r['unordered_pair_context_hash'] for r in good};families={(r['dataset'],r['family']) for r in good}
 res['_gate']={'eligible_distinct_pairs':len(unique),'eligible_source_families':len(families),'passed':len(unique)>=20 and len(families)>=3,'decision':'PROPOSE_NARROW_PROTOTYPE' if len(unique)>=20 and len(families)>=3 else 'REJECT_AVAILABLE_WORKLOAD','new_solver_calls':0,'new_sql_executions':0,'wall_s':time.monotonic()-t,'cpu_s':time.process_time()-cpu,'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
 (ROOT/'SUMMARY.json').write_text(json.dumps(res,ensure_ascii=False,indent=2))
 (ROOT/'ELIGIBLE_ID_FREEZE.json').write_text(json.dumps({'ids':[r['id'] for r in good],'all_records_sha256':sha((ROOT/'ALL_RECORDS.jsonl').read_bytes()),'input_freeze_sha256':sha((ROOT/'INPUT_FREEZE.json').read_bytes()),'scanner_sha256':sha(pathlib.Path(__file__).read_bytes()),'new_final_test':False},indent=2))
 print(json.dumps(res,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
