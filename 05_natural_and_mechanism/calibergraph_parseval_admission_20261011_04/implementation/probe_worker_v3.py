"""One bounded original-query admission probe; invoked only by reviewed launcher."""
from pathlib import Path
import collections
import datetime
import hashlib
import json
import os
import resource
import sys
import time
import traceback
import threading

P=Path(__file__).resolve().parents[1]
W=P.parent
BASE=W/'calibergraph_parseval_admission_20261011_03'
OUT=Path(sys.argv[1])
SOCKET=sys.argv[2]
START=time.monotonic()
CPU=time.process_time()
resource.setrlimit(resource.RLIMIT_CPU,(20,21))
resource.setrlimit(resource.RLIMIT_FSIZE,(8*1024**2,8*1024**2))
os.nice(19)
sys.dont_write_bytecode=True
sys.pycache_prefix=str(P/'runtime/NO_BYTECODE_CACHE')
sys.path[:0]=[str(BASE/'dependencies_local/site-packages'),str(BASE/'sources_local/parseval_official/src'),str(BASE/'implementation')]
R={'status':'STARTED','stage':'IMPORTS_PENDING','counters_complete':False,
   'parser_internal_calls':'NOT_COLLECTED; explicit lowering invocations are counted; generator internal lowering is included in generation cost only',
   'case':'gitlab#47','historical_server_reproduction':False,'variant':'ParSEval_with_ordinary_PostgreSQL_BOOLEAN_literal_adapter','original_SQL_rewritten':False,
   'counters':{'generation_calls':0,'solver_checks':0,'solver_results':{},'candidate_callbacks':0,
               'original_query_replays':0,'confirmation_query_replays':0,'driver_execute_calls':0,'explicit_lowering_calls':0},
   'calibration':[],'lowering':[],'candidates':[],'attempts':[],'new_test':False}

class BudgetStop(RuntimeError):pass
class CandidateStop(RuntimeError):pass

def typed(x):
    if x is None:return None
    if isinstance(x,(datetime.datetime,datetime.date,datetime.time)):
        return {'type':type(x).__name__,'value':x.isoformat()}
    if type(x) in (str,int,float,bool):return x
    if isinstance(x,(tuple,list)):return [typed(v) for v in x]
    if isinstance(x,dict):return {str(k):typed(v) for k,v in x.items()}
    return {'type':type(x).__name__,'value':str(x)}

def digest_object(x):
    return hashlib.sha256(json.dumps(typed(x),sort_keys=True,ensure_ascii=False).encode()).hexdigest()

def checkpoint():
    R['elapsed_wall_s']=time.monotonic()-START
    R['cpu_s']=time.process_time()-CPU
    R['worker_peak_rss_bytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    (OUT/'RESULT.json').write_text(json.dumps(typed(R),ensure_ascii=False,indent=2)+'\n')

def error_record(e):
    # Raw diagnostics may echo upstream SQL, so retain them only in excluded local logs.
    raw=''.join(traceback.format_exception(type(e),e,e.__traceback__))
    name='error_'+str(len(list(OUT.glob('error_*.txt')))+1)+'.txt'
    (OUT/name).write_text(raw)
    return {'type':type(e).__name__,'raw_local_path':name,'raw_sha256':hashlib.sha256(raw.encode()).hexdigest(),
            'message_sha256':hashlib.sha256(str(e).encode()).hexdigest()}

def execute(conn,sql,params=None):
    R['counters']['driver_execute_calls']+=1
    with conn.cursor() as cur:
        cur.execute(sql,params)
        if cur.description:
            return {'columns':[c.name for c in cur.description],
                    'type_oids':[c.type_code for c in cur.description], 'rows':cur.fetchall()}
        return None

def calibrate(conn,label,sql,params=None,expected_sqlstate=None):
    try:
        v=execute(conn,sql,params)
    except Exception as e:
        code=getattr(e,'pgcode',None)
        R['calibration'].append({'label':label,'sqlstate':code,'expected':expected_sqlstate,'pass':code==expected_sqlstate})
        if code!=expected_sqlstate:raise
        return
    R['calibration'].append({'label':label,'sqlstate':None,'expected':expected_sqlstate,'pass':expected_sqlstate is None,'result':v})
    if expected_sqlstate is not None:raise AssertionError('Expected constraint rejection did not occur: '+label)

def independent_C(tables,data):
    failures=[]
    for name,t in tables.items():
        rows=data[name];columns=t['columns'];names=[c['name'] for c in columns]
        for n,row in enumerate(rows):
            if len(row)!=len(columns):failures.append([name,n,'width']);continue
            for c,v in zip(columns,row):
                if v is None:
                    if not c['nullable']:failures.append([name,n,c['name'],'NOT_NULL'])
                    continue
                kind=c['source_type']
                ok={'integer':lambda:type(v) is int and -(2**31)<=v<2**31,
                    'boolean':lambda:type(v) is bool,
                    'string':lambda:type(v) is str and '\x00' not in v,
                    'text':lambda:type(v) is str and '\x00' not in v,
                    'datetime':lambda:type(v) is datetime.datetime and v.tzinfo is None,
                    'date':lambda:type(v) is datetime.date}[kind]()
                if not ok:failures.append([name,n,c['name'],'TYPE_OR_STORAGE'])
        for key in ([t['primary_key']] if t['primary_key'] else [])+t['unique_keys']:
            seen=set()
            for row in rows:
                k=tuple(row[names.index(c)] for c in key)
                if None in k:continue
                if k in seen:failures.append([name,key,'KEY_DUPLICATE'])
                seen.add(k)
        for fk in t['foreign_keys']:
            rn=[c['name'] for c in tables[fk['ref_table']]['columns']]
            parent={tuple(row[rn.index(c)] for c in fk['ref_columns']) for row in data[fk['ref_table']]}
            for row in rows:
                k=tuple(row[names.index(c)] for c in fk['columns'])
                if None not in k and k not in parent:failures.append([name,fk['columns'],'FK'])
    return {'pass':not failures,'failures':failures,'text_equality_scope':'New PostgreSQL deterministic C collation; not historical unknown collation'}

def main():
    checkpoint()
    assert sys.platform == 'darwin', 'RSS byte accounting is pinned to macOS'
    def monitor_own_rss():
        while not RSS_DONE.wait(0.05):
            used=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            if used>512*1024**2:
                (OUT/'memory_guard.json').write_text(json.dumps({'status':'OWN_PROCESS_RSS_GUARD_EXIT','observed_peak_rss_bytes':used,'threshold_bytes':512*1024**2,'sample_interval_s':0.05})+'\n')
                os._exit(86)
    threading.Thread(target=monitor_own_rss,daemon=True).start()
    R['resource_limits']={name:list(resource.getrlimit(getattr(resource,name))) for name in ('RLIMIT_CPU','RLIMIT_FSIZE')}
    R['rss_guard']={'threshold_MiB':512,'sample_interval_s':0.05,'scope':'Own worker peak RSS only; sampled guard may overshoot, not an OS hard RSS limit'}
    import sqlglot
    import z3
    import psycopg2
    from parseval.generator import generate,GenerationConfig
    from parseval.parser.query.compiler import lower_query
    from parseval.terms.sorts import TypeKind,BOOLEAN
    import gitlab_schema as schema
    from boolean_adapter import postgres_tf_literal_aliases,PATCH_ID
    assert sqlglot.__version__=='23.12.1'
    assert z3.get_version()==(4,16,0,0)
    R['versions']={'python':sys.version,'sqlglot':sqlglot.__version__,'z3':z3.get_version_string(),'psycopg2':psycopg2.__version__}
    case=schema.load_case();tables=case['tables']
    ddl=schema.make_ddl(tables)
    R['derived_ddl_sha256']=hashlib.sha256(ddl.encode()).hexdigest()
    (OUT/'derived_schema.sql').write_text(ddl)
    queries={k:(W/v['path']).read_text() for k,v in case['queries'].items()}
    R['query_hashes']={k:hashlib.sha256(v.encode()).hexdigest() for k,v in queries.items()}
    catalog=schema.build_catalog(case)
    R['catalog_audit']=schema.audit_catalog(catalog,case)
    R['adapter']=PATCH_ID
    try:
        R['stage']='STOCK_LOWERING';R['counters']['explicit_lowering_calls']+=1;checkpoint()
        q=lower_query(queries['after'],catalog)
        R['lowering'].append({'variant':'stock','side':'after','status':'PASS','columns':len(q.columns)})
    except Exception as e:
        R['lowering'].append({'variant':'stock','side':'after','status':'ERROR','error':error_record(e)})
    checkpoint()
    conn=psycopg2.connect(host=SOCKET,port=65433,user='cg_probe',dbname='postgres',connect_timeout=3,
        passfile=str(P/'runtime/NO_PASSFILE'),options='-c statement_timeout=1000 -c lock_timeout=500 -c timezone=UTC -c search_path=public -c client_encoding=UTF8')
    conn.autocommit=True
    try:
        R['backend']=execute(conn,"SELECT version(), current_setting('server_version_num'), d.datlocprovider, d.datcollate, d.datctype, pg_catalog.pg_encoding_to_char(d.encoding), current_setting('TimeZone') FROM pg_catalog.pg_database d WHERE d.datname=current_database()")
        assert len(R['backend']['rows'])==1 and R['backend']['rows'][0][1:]==('160014','c','C','C','UTF8','UTC')
        R['stage']='BACKEND_DDL';checkpoint()
        execute(conn,ddl)
        # Backend column census checks every actual type, length, nullability and order.
        meta=execute(conn,"SELECT table_name,column_name,data_type,is_nullable,character_maximum_length FROM information_schema.columns WHERE table_schema='public' ORDER BY table_name,ordinal_position")
        pgtypes={'integer':'integer','boolean':'boolean','string':'character varying','text':'text','datetime':'timestamp without time zone','date':'date'}
        expected=sorted([(name,c['name'],pgtypes[c['source_type']],'YES' if c['nullable'] else 'NO',None,n)
                         for name,t in tables.items() for n,c in enumerate(t['columns'])],key=lambda x:(x[0],x[5]))
        assert meta['rows']==[x[:5] for x in expected]
        R['postgres_columns']=meta
        defaults=execute(conn,"SELECT table_name,column_name,column_default FROM information_schema.columns WHERE table_schema='public' ORDER BY table_name,ordinal_position")
        default_map={(t,c):v for t,c,v in defaults['rows']}
        checked_defaults=[]
        for name,t in tables.items():
            for c in t['columns']:
                actual=default_map[(name,c['name'])]
                if c.get('implicit'):
                    seq=execute(conn,'SELECT pg_get_serial_sequence(%s,%s)',('public.'+name,c['name']))['rows'][0][0]
                    assert seq is not None and actual.startswith('nextval(')
                    checked_defaults.append({'table':name,'column':c['name'],'kind':'SERIAL','sequence':seq,'default':actual})
                elif 'default' in c:
                    assert actual is not None
                    value=execute(conn,'SELECT ('+actual+')')['rows'][0][0]
                    assert type(value) is type(c['default']) and value==c['default']
                    checked_defaults.append({'table':name,'column':c['name'],'kind':'EXPLICIT_DEFAULT','value':value,'expression':actual})
                else:assert actual is None
        R['postgres_defaults']=checked_defaults
        keys=execute(conn,"SELECT t.relname,c.contype,c.conkey,i.indnullsnotdistinct,i.indisunique,i.indisvalid,i.indimmediate FROM pg_constraint c JOIN pg_class t ON t.oid=c.conrelid JOIN pg_namespace n ON n.oid=t.relnamespace JOIN pg_index i ON i.indexrelid=c.conindid WHERE n.nspname='public' AND c.contype IN ('p','u') ORDER BY t.relname,c.contype,c.conkey")
        assert len(keys['rows'])==9 and all(row[3:]==(False,True,True,True) for row in keys['rows'])
        R['postgres_key_policy']=keys
        constraints=execute(conn,"SELECT r.relname,c.contype,c.conkey,c.confrelid::regclass::text,c.confkey,c.confdeltype,c.confmatchtype,c.condeferrable,c.condeferred,c.convalidated,c.confupdtype FROM pg_constraint c JOIN pg_class r ON r.oid=c.conrelid JOIN pg_namespace n ON n.oid=r.relnamespace WHERE n.nspname='public' ORDER BY r.relname,c.contype,c.conkey")
        got=[]
        for name,kind,cols,ref,refcols,delete,match,defer,deferred,validated,update in constraints['rows']:
            assert not defer and not deferred and validated
            if kind=='f':assert update=='a'
            nn=[c['name'] for c in tables[name]['columns']]
            rc=[c['name'] for c in tables[ref]['columns']] if kind=='f' else []
            got.append((name,kind,tuple(nn[i-1] for i in cols),ref if kind=='f' else None,
                        tuple(rc[i-1] for i in refcols) if kind=='f' else (),delete if kind=='f' else None,match if kind=='f' else None))
        want=[]
        for name,t in tables.items():
            if t['primary_key']:want.append((name,'p',tuple(t['primary_key']),None,(),None,None))
            want.extend((name,'u',tuple(k),None,(),None,None) for k in t['unique_keys'])
            want.extend((name,'f',tuple(k['columns']),k['ref_table'],tuple(k['ref_columns']),'c','s') for k in t['foreign_keys'])
        assert sorted(got)==sorted(want)
        R['postgres_constraints']={'verified_signature':got,'counts':dict(collections.Counter(x[1] for x in got))}
        truth=execute(conn,"SELECT b,b='f',b=FALSE,b='t',b=TRUE FROM (VALUES (FALSE),(TRUE),(NULL::boolean)) AS domain(b)")
        assert truth['rows']==[(False,True,True,False,False),(True,False,False,True,True),(None,None,None,None,None)]
        R['postgres_original_literal_equivalence']={'complete_nullable_boolean_domain':True,'observed':truth,'query_bytes_unchanged':True}
        with postgres_tf_literal_aliases(catalog.dialect,TypeKind.BOOLEAN):
            for value in ['f','t','false','true','0','1','F','T']:
                pg=execute(conn,'SELECT %s::boolean',(value,))['rows'][0][0]
                pv=catalog.dialect.parse_string_cast_literal(value,BOOLEAN)
                assert type(pv) is bool and pv==pg
                R['calibration'].append({'label':'boolean_literal','input':value,'postgres':pg,'parseval_adapter':pv,'pass':True})
            calibrate(conn,'NULL_not_false','SELECT NULL::boolean IS NULL, NULL::boolean = FALSE')
            assert R['calibration'][-1]['result']['rows']==[(True,None)]
            calibrate(conn,'nullable_triple_unique_duplicate_NULL_allowed','INSERT INTO project_authorizations(user_id,project_id,access_level) VALUES(NULL,NULL,NULL),(NULL,NULL,NULL)')
            calibrate(conn,'star_no_invented_FK','INSERT INTO users_star_projects(id,user_id,project_id) VALUES(1,987,654)')
            calibrate(conn,'star_nonNULL_unique_reject','INSERT INTO users_star_projects(id,user_id,project_id) VALUES(2,987,654)',expected_sqlstate='23505')
            calibrate(conn,'star_source_NOT_NULL_reject','INSERT INTO users_star_projects(id,user_id,project_id) VALUES(3,NULL,655)',expected_sqlstate='23502')
            calibrate(conn,'auth_project_FK_reject','INSERT INTO project_authorizations(user_id,project_id,access_level) VALUES(NULL,987,NULL)',expected_sqlstate='23503')
            calibrate(conn,'auth_user_FK_reject','INSERT INTO project_authorizations(user_id,project_id,access_level) VALUES(987,NULL,NULL)',expected_sqlstate='23503')
            calibrate(conn,'signed_int32_reject','INSERT INTO users_star_projects(id,user_id,project_id) VALUES(2147483648,1,1)',expected_sqlstate='22003')
            # Generation is guided only by the selected original AFTER query.
            # The BEFORE query is independently executed unchanged in PostgreSQL;
            # this probe does not claim that ParSEval can lower BEFORE.
            for side,q in [('after',queries['after'])]:
                try:
                    R['stage']='ADAPTED_LOWERING';R['counters']['explicit_lowering_calls']+=1;checkpoint()
                    lowered=lower_query(q,catalog)
                    assert [c.name.text for c in lowered.columns]==[c['name'] for c in tables['projects']['columns']]
                    R['lowering'].append({'variant':'ordinary_boolean_adapter','side':side,'status':'PASS','columns':len(lowered.columns)})
                except Exception as e:
                    R['lowering'].append({'variant':'ordinary_boolean_adapter','side':side,'status':'ERROR','error':error_record(e)})
                    R['status']='ADMISSION_BLOCKED_LOWERING';checkpoint();return
            # All synthetic calibration rows are removed before baseline generation.
            clear='TRUNCATE projects,users,users_star_projects,project_authorizations RESTART IDENTITY CASCADE'
            execute(conn,clear)
            original_check=z3.Solver.check
            def counted_check(solver,*args,**kwargs):
                if R['counters']['solver_checks']>=4:raise BudgetStop('solver check budget reached')
                R['counters']['solver_checks']+=1
                checkpoint()
                outcome=original_check(solver,*args,**kwargs)
                d=R['counters']['solver_results'];d[str(outcome)]=d.get(str(outcome),0)+1
                return outcome
            z3.Solver.check=counted_check
            seen=set()
            def replay(data,confirmation=False,replay_conn=None):
                target=conn if replay_conn is None else replay_conn
                execute(target,clear)
                for name,t in tables.items():
                    cols=','.join(schema.ident(c['name']) for c in t['columns'])
                    command='INSERT INTO '+schema.ident(name)+' ('+cols+') VALUES ('+','.join(['%s']*len(t['columns']))+')'
                    for row in data[name]:execute(target,command,row)
                observed={}
                for side,query in queries.items():
                    R['counters']['confirmation_query_replays' if confirmation else 'original_query_replays']+=1
                    observed[side]=execute(target,query)
                return observed
            def accept(instance):
                if R['counters']['candidate_callbacks']>=3:raise BudgetStop('candidate callback budget reached')
                R['counters']['candidate_callbacks']+=1
                if instance.row_count>32:
                    R['candidates'].append({'rows':instance.row_count,'status':'SKIPPED_ROW_BUDGET','D_materialized_for_export':False})
                    checkpoint()
                    raise BudgetStop('generated row budget exceeded; candidate not replayed')
                data={t.name.qualified_name:list(instance.rows(t.relation)) for t in catalog.tables()}
                h=digest_object(data)
                item={'D_sha256':h,'duplicate':h in seen,'rows':instance.row_count,'D':data}
                R['candidates'].append(item);seen.add(h)
                item['independent_fullC']=independent_C(tables,data)
                if not item['independent_fullC']['pass']:
                    item['status']='INVALID_CANDIDATE';R['status']='ADMISSION_INVALID_GENERATED_C';checkpoint();raise CandidateStop('Generated candidate violates independent fullC; never continue or classify as ordinary empty')
                try:
                    item['observed']=replay(data)
                except Exception as e:
                    item['status']='INSERT_OR_ORIGINAL_QUERY_ERROR';item['error']=error_record(e);R['status']='ADMISSION_BACKEND_REPLAY_ERROR';checkpoint();raise CandidateStop('Backend insertion/original replay failed; no generation retry')
                for result in item['observed'].values():
                    assert result['columns']==[c['name'] for c in tables['projects']['columns']]
                item['original_fullC_backend_accepted']=True
                item['nonempty_after']=bool(item['observed']['after']['rows'])
                item['difference']=item['observed']['before']!=item['observed']['after']
                item['status']='VALID_NONEMPTY' if item['nonempty_after'] else 'VALID_EMPTY'
                if item['nonempty_after'] or item['difference']:
                    # Fresh independent database and connection in this isolated cluster.
                    execute(conn,"CREATE DATABASE cg_confirmation TEMPLATE template0 ENCODING 'UTF8' LC_COLLATE 'C' LC_CTYPE 'C'")
                    confirm=psycopg2.connect(host=SOCKET,port=65433,user='cg_probe',dbname='cg_confirmation',connect_timeout=3,
                        passfile=str(P/'runtime/NO_PASSFILE'),options='-c statement_timeout=1000 -c lock_timeout=500 -c timezone=UTC -c search_path=public -c client_encoding=UTF8')
                    confirm.autocommit=True
                    try:
                        execute(confirm,ddl)
                        item['confirmation']=replay(data,confirmation=True,replay_conn=confirm)
                    finally:
                        confirm.close()
                        execute(conn,'DROP DATABASE cg_confirmation')
                    assert item['confirmation']==item['observed']
                    item['confirmed']=True
                checkpoint()
                return item['nonempty_after'] or item['difference']
            def attempt(a):
                R['attempts'].append({'label':a.label,'status':a.status.value,'accepted':a.accepted,'reason':a.reason})
            try:
                R['counters']['generation_calls']+=1
                R['stage']='GENERATION_IN_PROGRESS';checkpoint()
                config=GenerationConfig(timeout_ms=500,time_limit_s=5.0,seed=0,speculate=True,set_semantics=False)
                result=generate(queries['after'],catalog,config=config,on_attempt=attempt,on_instance=accept)
                R['generator_result']={'nonempty':result.nonempty,'reached':result.reached,'covered':result.covered,'failed':result.failed,'unsupported':result.unsupported,'timed_out':result.timed_out}
                if result.instance is not None and digest_object({t.name.qualified_name:list(result.instance.rows(t.relation)) for t in catalog.tables()}) not in seen:
                    accept(result.instance)
            except BudgetStop as e:R['budget_stop']=str(e)
            except CandidateStop as e:R['candidate_stop']=str(e)
            finally:z3.Solver.check=original_check
            if R.get('candidate_stop'):pass
            elif any(x.get('confirmed') and x.get('difference') for x in R['candidates']):R['status']='ADAPTED_BASELINE_ORIGINAL_QUERY_DIFFERENCE_CONFIRMED'
            elif any(x.get('confirmed') and x.get('nonempty_after') for x in R['candidates']):R['status']='ADAPTED_BASELINE_ORIGINAL_QUERY_NONEMPTY_CONFIRMED'
            elif R.get('generator_result',{}).get('unsupported'):R['status']='ADAPTED_BASELINE_GENERATOR_UNSUPPORTED'
            else:R['status']='NO_NONEMPTY_WITHIN_ONE_SMALL_PROBE_NOT_MECHANISM_FAILURE'
    finally:conn.close()

RSS_DONE=threading.Event()
try:
    main()
except BaseException as e:
    R['status']='PROBE_ERROR';R['error']=error_record(e)
finally:
    RSS_DONE.set()
    R['stage']='WORKER_FINISHED';R['counters_complete']=True
    checkpoint()
