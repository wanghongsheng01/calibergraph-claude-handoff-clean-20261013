"""Pinned VeriEQL backend; importing this file does not import target code.

Public API: Budget, load_runtime(protocol, budget, emit),
run_case(runtime, case, protocol, budget, emit), validate_operational_contract.
No old source is modified. Query encoding/check is the official implementation.
"""
from collections import Counter
from contextlib import contextmanager
from datetime import date, timedelta
from pathlib import Path
from types import SimpleNamespace
import builtins, ctypes, gc, hashlib, json, resource, sqlite3, sys, time, traceback


class BudgetStop(RuntimeError):
    pass


def cpu():
    r = resource.getrusage(resource.RUSAGE_SELF)
    return r.ru_utime + r.ru_stime


class Budget:
    def __init__(self, cpu_limit=10.0, wall_limit=25.0):
        self.start_wall = time.monotonic()
        self.cpu_limit = float(cpu_limit)  # whole-process CPU includes imports
        self.wall_limit = float(wall_limit)

    def check(self):
        if cpu() >= self.cpu_limit - 0.75:
            raise BudgetStop('WORKER_CPU_RESERVE_REACHED')
        if time.monotonic() - self.start_wall >= self.wall_limit - 1.0:
            raise BudgetStop('WORKER_WALL_RESERVE_REACHED')
        if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss >= 256 * 1024**2:
            raise BudgetStop('WORKER_OBSERVED_PEAK_RSS_256_MIB')

    def solver_ms(self, stage_maximum=500):
        self.check()
        remaining = min(self.cpu_limit - cpu() - 0.75,
                        self.wall_limit - (time.monotonic()-self.start_wall) - 1.0)
        return max(1, min(int(stage_maximum), int(remaining*1000)))


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(262144), b''):
            h.update(b)
    return h.hexdigest()


def objsha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                          separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def formula_sha(items, budget):
    h = hashlib.sha256()
    for term in items:
        budget.check()
        h.update(term.sexpr().encode()); h.update(b'\n')
    return h.hexdigest()


@contextmanager
def stage(record, name, budget, emit):
    budget.check()
    item = {'status':'STARTED','name':name}
    record.setdefault('stages', []).append(item)
    record['active_stage'] = name
    emit('STAGE_START', record)
    w, c = time.monotonic(), cpu()
    try:
        yield item
        item['status'] = 'RETURNED'
    except BaseException as exc:
        item.update(status='RAISED', error_type=type(exc).__name__, error=str(exc)[:2000])
        raise
    finally:
        item.update(wall_seconds=time.monotonic()-w, cpu_seconds=cpu()-c)
        emit('STAGE_END', record)


def load_runtime(protocol, budget, emit):
    rec = {'id':'runtime','stages':[]}
    with stage(rec, 'LOCK_AND_DEPENDENCY_HASH', budget, emit) as st:
        lp = Path(protocol['runtime_lock']['path'])
        if sha(lp) != protocol['runtime_lock']['sha256']:
            raise ValueError('RUNTIME_LOCK_HASH_MISMATCH')
        lock = json.loads(lp.read_text())
        checked = 0
        for raw, expected in lock['files'].items():
            budget.check()
            p = Path(raw)
            if not p.is_file() or p.is_symlink() or sha(p) != expected:
                raise ValueError('PINNED_FILE_MISMATCH: '+raw)
            checked += 1
        st['checked_files'] = checked
    with stage(rec, 'NATIVE_AND_OFFICIAL_IMPORT', budget, emit) as st:
        library = ctypes.CDLL(lock['native_path'])
        builtins.Z3_LIB_DIRS = [str(Path(lock['native_path']).parent)]
        sys.path[:0] = [lock['binding_root'], lock['support_root'], *lock['dependency_roots'], lock['source_root']]
        import z3
        from z3 import z3core
        defaults = z3core.Z3_get_version.__defaults__
        if len(defaults) != 1:
            raise ValueError('UNEXPECTED_NATIVE_WRAPPER')
        ptr1 = ctypes.cast(defaults[0].f, ctypes.c_void_p).value
        ptr2 = ctypes.cast(library.Z3_get_version, ctypes.c_void_p).value
        if ptr1 != ptr2 or not ptr1 or list(z3.get_version()) != lock['expected_native_version']:
            raise ValueError('NATIVE_IDENTITY_MISMATCH')
        from environment import Environment
        import constants
        if Path(sys.modules['environment'].__file__).resolve() != Path(lock['source_root'])/'environment.py':
            raise ValueError('OFFICIAL_SOURCE_ORIGIN_MISMATCH')
        if not Path(z3.__file__).resolve().is_relative_to(Path(lock['binding_root'])):
            raise ValueError('BINDING_SOURCE_ORIGIN_MISMATCH')
        z3.set_param('parallel.enable', False)
        z3.set_param('memory_max_size', 128)
        st.update(version=list(z3.get_version()), native_path=lock['native_path'],
                  native_sha256=sha(lock['native_path']), solver_memory_parameter_mb=128)
    return SimpleNamespace(z3=z3, constants=constants, Environment=Environment,
                           library=library, lock=lock, initialization=rec)


def _ref(raw, schema):
    if not isinstance(raw, dict) or set(raw) != {'value'} or not isinstance(raw['value'], str):
        raise ValueError('UNSUPPORTED_OPERATIONAL_REFERENCE')
    table, col = raw['value'].split('__', 1)
    if table not in schema or col not in schema[table]:
        raise ValueError('UNKNOWN_OPERATIONAL_REFERENCE')
    return table, col


def validate_operational_contract(schema, constraints, database):
    """Concrete OFFICIAL_OPERATIONAL_IC_V1 for exactly the six registered cases.

    FK is strict non-NULL. Column-column neq is ALL Cartesian pairs, not rowwise.
    Preserves complete schema/C; does not interpret SQL DDL CHECK conventions.
    """
    if set(database) != set(schema):
        raise ValueError('INCOMPLETE_PHYSICAL_SCHEMA')
    for table, fields in schema.items():
        for row in database[table]:
            if set(row) != set(fields):
                raise ValueError('INCOMPLETE_PHYSICAL_ROW')
            for col, typ in fields.items():
                val = row[col]
                if val is not None and not ((typ == 'INT' and type(val) is int) or
                    (typ in ('VARCHAR','DATE') and isinstance(val,str))):
                    raise ValueError('CONCRETE_PHYSICAL_TYPE_MISMATCH')
    observations = []
    for clause in constraints or []:
        if not isinstance(clause, dict) or len(clause) != 1:
            raise ValueError('MALFORMED_OPERATIONAL_CLAUSE')
        op, args = next(iter(clause.items()))
        if op == 'primary':
            refs = [_ref(x,schema) for x in args]
            if not refs or len({t for t,c in refs}) != 1:
                raise ValueError('UNSUPPORTED_CROSS_TABLE_PRIMARY')
            vals = [tuple(row[c] for t,c in refs) for row in database[refs[0][0]]]
            holds = all(all(v is not None for v in tup) for tup in vals) and len(vals)==len(set(vals))
        elif op == 'foreign':
            if len(args)!=2:
                raise ValueError('UNSUPPORTED_FOREIGN_ARITY')
            (a,c),(b,d) = [_ref(x,schema) for x in args]
            target = {row[d] for row in database[b] if row[d] is not None}
            holds = all(row[c] is not None and row[c] in target for row in database[a])
        elif op == 'gte':
            if len(args)!=2 or type(args[1]) is not int:
                raise ValueError('UNSUPPORTED_GTE_PROFILE')
            t,c = _ref(args[0],schema)
            holds = all(row[c] is not None and row[c] >= args[1] for row in database[t])
        elif op == 'neq':
            if len(args)!=2:
                raise ValueError('UNSUPPORTED_NEQ_PROFILE')
            (a,c),(b,d) = [_ref(x,schema) for x in args]
            holds = all(x[c] is not None and y[d] is not None and x[c] != y[d]
                        for x in database[a] for y in database[b])
        else:
            raise ValueError('UNSUPPORTED_WHOLE_OPERATIONAL_CONTRACT: '+str(op))
        observations.append({'clause':clause,'holds':holds})
    return {'profile':'OFFICIAL_OPERATIONAL_IC_V1','holds':all(x['holds'] for x in observations),
            'clauses':observations,'scope':'locked official operational clauses; not inferred natural/SQL-DDL truth'}


def decode_model(rt, env, model, schema, budget):
    raw, typed, symbol_map = {}, {}, {}
    for table, fields in schema.items():
        attrs = list(env.base_databases[table].attributes)
        if [a.name.upper() for a in attrs] != list(fields):
            raise ValueError('ATTRIBUTE_ORDER_MISMATCH')
        raw[table], typed[table] = [], []
        for tup in env.base_databases[table]:
            budget.check()
            if not rt.z3.is_false(model.eval(env.DELETED_FUNCTION(tup.SORT), model_completion=True)):
                raise ValueError('EXACT_ROW_MODEL_HAS_DELETED_BASE_ROW')
            rr, tr = {}, {}
            for (col,typ),attr in zip(fields.items(),attrs):
                isnull = rt.z3.is_true(model.eval(attr.NULL(tup.SORT), model_completion=True))
                value = None if isnull else model.eval(attr.VALUE(tup.SORT), model_completion=True).as_long()
                rr[col] = value
                if value is None or typ == 'INT':
                    tr[col] = value
                elif typ == 'VARCHAR':
                    symbol_map.setdefault(value, 'cg_string_'+str(value))
                    tr[col] = symbol_map[value]
                elif typ == 'DATE':
                    tr[col] = (date(1970,1,1)+timedelta(days=value-1)).isoformat()
                else:
                    raise ValueError('UNSUPPORTED_MODEL_REPLAY_TYPE: '+typ)
            raw[table].append(rr); typed[table].append(tr)
    return {'raw_official_values':raw,'database':typed,'string_value_map':{str(k):v for k,v in symbol_map.items()},
            'string_mapping_scope':'injective shared symbols; registered SQL has no string literals or string arithmetic'}


def replay_sqlite(case, decoded, protocol, budget):
    src = case['source_record']
    rows = decoded['database']
    result = {'status':'STARTED','sqlite_version':sqlite3.sqlite_version,
              'original_sql_sha256':case['original_sql_sha256'],'relations':[]}
    def quote(v):
        return '"'+v.replace('"','""')+'"'
    def run(reverse=False):
        conn=sqlite3.connect(':memory:')
        try:
            conn.set_progress_handler(lambda:int(cpu()>=budget.cpu_limit-0.75 or time.monotonic()-budget.start_wall>=budget.wall_limit-1), 1000)
            for table,fields in src['schema'].items():
                conn.execute('CREATE TABLE '+quote(table)+' ('+', '.join(quote(c)+' '+t for c,t in fields.items())+')')
                ordered=list(reversed(rows[table])) if reverse else rows[table]
                conn.executemany('INSERT INTO '+quote(table)+' VALUES ('+','.join('?' for _ in fields)+')',
                                 [[r[c] for c in fields] for r in ordered])
            conn.execute('PRAGMA query_only=ON')
            outputs=[]
            for sql in src['pair']:
                budget.check()
                outputs.append(conn.execute(sql).fetchall())
            return outputs
        finally:
            conn.close()
    result['relations']=run()
    result['unequal_as_bags']=Counter(map(tuple,result['relations'][0])) != Counter(map(tuple,result['relations'][1]))
    profile=protocol['sqlite_replay_intersection'][case['id']]
    result['intersection']=profile
    if case['id']=='dev_01':
        result['reverse_insertion_relations']=run(reverse=True)
    result['status']='VALIDATED_SAT_SQLITE_INTERSECTION' if profile['eligible'] and result['unequal_as_bags'] else (
        'DIALECT_UNKNOWN' if not profile['eligible'] else 'COUNTEREXAMPLE_REPLAY_MISMATCH')
    result['scope']='original SQLite bag outputs for this concrete full-C database only; no cross-dialect gold'
    return result


class SolverTap:
    """Transparent solver delegate; records the official compare's actual check."""
    def __init__(self, target, record, protocol, budget, emit):
        self.target,self.record,self.protocol,self.budget,self.emit=target,record,protocol,budget,emit
        self.answer=None
        self.started_wall=time.monotonic(); self.started_cpu=cpu()

    def __getattr__(self,name):
        return getattr(self.target,name)

    def check(self,*args):
        self.record['comparison_formula_encode']={'wall_seconds':time.monotonic()-self.started_wall,
                                                    'cpu_seconds':cpu()-self.started_cpu}
        with stage(self.record,'OFFICIAL_QUERY_SOLVER_CHECK',self.budget,self.emit) as st:
            timeout=self.budget.solver_ms(self.protocol['solver_stage_timeout_ms'])
            self.target.set(timeout=timeout,threads=1)
            st['timeout_ms']=timeout
            self.answer=self.target.check(*args)
            st['answer']=str(self.answer)
            if str(self.answer)=='unknown':
                st['reason_unknown']=self.target.reason_unknown()
            self.record['raw_solver_verdict']=str(self.answer)
            return self.answer


def run_case(rt, case, protocol, budget, emit=lambda event, record:None):
    """One registered original pair, full operational C, exact positive shape.

    Returns JSON-serializable evidence. No exception/result implies unbounded EQ.
    The caller owns the total budget/RSS/process guard and durable event sink.
    """
    src=case['source_record']
    n=protocol['exact_rows_per_table']
    rec={'id':case['id'],'status':'STARTED','source_group_id':case['source_group_id'],
         'original_sql_sha256':case['original_sql_sha256'],'schema_sha256':objsha(src['schema']),
         'constraint_sha256':objsha(src['constraint']),'contract_profile':protocol['contract_profile'],
         'exact_rows':{t:n for t in src['schema']},'row_bound_semantics':'EXACT_POSITIVE_SHAPE_NOT_UP_TO_N',
         'raw_solver_verdict':None,'effective_verdict':None,'stages':[],
         'full_schema':src['schema'],'full_constraint':src['constraint'],'original_sql':src['pair']}
    beginw,beginc=time.monotonic(),cpu()
    env=None
    try:
        budget.check()
        if case['id'] not in protocol['case_ids'] or n not in (1,2):
            raise ValueError('UNREGISTERED_CASE_OR_BOUND')
        if [hashlib.sha256(s.encode()).hexdigest() for s in src['pair']] != case['original_sql_sha256']:
            raise ValueError('ORIGINAL_SQL_HASH_MISMATCH')
        # Concrete empty evaluation verifies grammar and complete schema traversal only.
        # It is deliberately not a satisfiability result for the chosen positive shape.
        validate_operational_contract(src['schema'],src['constraint'],{t:[] for t in src['schema']})
        with stage(rec,'ENVIRONMENT_AND_FULL_SCHEMA',budget,emit):
            env=rt.Environment(timer=False,generate_code=False,show_counterexample=False,dialect=rt.constants.DIALECT.ALL)
            env.__enter__()
            for table,fields in src['schema'].items():
                budget.check(); env.create_database(attributes=fields,bound_size=n,name=table)
        with stage(rec,'FULL_ORIGINAL_IC_ADMISSION',budget,emit) as st:
            before=len(env.DBMS_facts)
            env.add_constraints(src['constraint'])
            st.update(original_clause_count=len(src['constraint'] or []),base_fact_count=before,
                      admitted_delta_facts=len(env.DBMS_facts)-before)
            facts=list(env.DBMS_facts)+sorted(env.bound_constraints,key=lambda x:x.sexpr())
            rec['full_contract_fact_sha256']=formula_sha(facts,budget)
        with stage(rec,'FULL_C_NONEMPTY_CHECK',budget,emit) as st:
            probe=rt.z3.Solver(ctx=rt.constants.Z3_CONTEXT)
            timeout=budget.solver_ms(protocol['solver_stage_timeout_ms'])
            probe.set(timeout=timeout,threads=1);probe.add(*facts)
            answer=probe.check()
            st.update(timeout_ms=timeout,answer=str(answer),assertion_count=len(facts))
            if str(answer)=='unknown':
                st['reason_unknown']=probe.reason_unknown()
            if str(answer)=='sat':
                m=probe.model()
                if not all(rt.z3.is_true(m.eval(f,model_completion=True)) for f in facts):
                    raise ValueError('NONEMPTY_MODEL_FAILED_FULL_FACTS')
            rec['full_C_nonempty']=str(answer)
        if str(answer)!='sat':
            rec.update(status='CONTRACT_STOP',effective_verdict='CONTRACT_UNSAT' if str(answer)=='unsat' else 'CONTRACT_NONEMPTY_UNKNOWN')
            return rec
        env.save_checkpoints()
        old_parse=env.parse_sql_query
        rec['parsed_asts']=[]
        def timed_parse(sql):
            with stage(rec,'OFFICIAL_PARSE_QUERY_'+str(len(rec['parsed_asts'])),budget,emit) as st:
                ast=old_parse(sql)
                saved=json.loads(json.dumps(ast,ensure_ascii=False,allow_nan=False))
                rec['parsed_asts'].append(saved);st['ast_sha256']=objsha(saved)
                return ast
        env.parse_sql_query=timed_parse
        official_compare=env.compare
        captured={}
        def capture_compare(tables,result_formulas,out_file=None):
            captured.update(tables=tables,result_formulas=result_formulas)
            return None
        env.compare=capture_compare
        with stage(rec,'OFFICIAL_ANALYZE_PARSE_AND_SCOPE_ENCODE',budget,emit) as st:
            try:
                env.analyze(*src['pair'])
            finally:
                env.compare=official_compare
                env.parse_sql_query=old_parse
            if not captured:
                raise ValueError('OFFICIAL_ANALYZE_DID_NOT_REACH_COMPARE')
            st['formula_counts']=[len(x) for x in captured['result_formulas']]
            st['output_table_tuple_counts']=[len(x) for x in captured['tables']]
        # Preserve official compare (type checks + auto bag/list verifier + check).
        tap=SolverTap(env.solver,rec,protocol,budget,emit)
        env.solver=tap
        rec['active_stage']='OFFICIAL_COMPARISON_FORMULA_ENCODING'
        emit('STAGE_START',rec)
        try:
            rec['official_compare_return']=official_compare(captured['tables'],captured['result_formulas'])
        except Exception as exc:
            if str(tap.answer)!='unknown':
                raise
            rec['official_unknown_exception']=type(exc).__name__
        if tap.answer is None:
            rec.update(status='QUERY_NOT_SOLVED',effective_verdict='OFFICIAL_COMPARE_EARLY_RETURN')
        elif str(tap.answer)=='unsat':
            rec.update(status='RETURNED',effective_verdict='UNSAT_EXACT_SHAPE_OFFICIAL_SEMANTICS')
        elif str(tap.answer)=='unknown':
            rec.update(status='RETURNED',effective_verdict='SOLVER_UNKNOWN')
        elif str(tap.answer)=='sat':
            with stage(rec,'SAT_MODEL_FULL_C_AND_ORIGINAL_SQL_REPLAY',budget,emit):
                model=tap.target.model()
                assertions=list(tap.target.assertions())
                if not all(rt.z3.is_true(model.eval(f,model_completion=True)) for f in facts+assertions):
                    raise ValueError('QUERY_SAT_MODEL_FAILED_COMPLETE_ASSERTIONS')
                rec['SAT_all_submitted_assertions_true']=True
                decoded=decode_model(rt,env,model,src['schema'],budget)
                rec['witness']=decoded
                cv=validate_operational_contract(src['schema'],src['constraint'],decoded['database'])
                rec['concrete_full_original_C_validation']=cv
                if not cv['holds']:
                    raise ValueError('SAT_WITNESS_FAILS_OPERATIONAL_C')
                rec['sqlite_replay']=replay_sqlite(case,decoded,protocol,budget)
                rec.update(status='RETURNED',effective_verdict=rec['sqlite_replay']['status'])
        else:
            raise ValueError('UNRECOGNIZED_OFFICIAL_SOLVER_ANSWER')
    except BudgetStop as exc:
        rec.update(status='RESOURCE_STOP',effective_verdict='BUDGET_STOP',error=str(exc))
    except Exception as exc:
        name=type(exc).__name__
        rec.update(status='QUERY_UNSUPPORTED_OR_ERROR',effective_verdict='UNSUPPORTED_OR_ERROR',
                   error_type=name,error=str(exc)[:4000],traceback=traceback.format_exc()[-12000:])
        if rec.get('raw_solver_verdict')=='sat':
            rec['effective_verdict']='SAT_VALIDATION_ERROR_OR_DOMAIN_UNKNOWN'
    finally:
        if env is not None:
            cw,cc=time.monotonic(),cpu()
            try:
                env.__exit__(None,None,None); rec['cleanup']='COMPLETE'
            except BaseException as exc:
                rec.update(cleanup='FAILED',cleanup_error=type(exc).__name__+': '+str(exc))
            rec['cleanup_cost']={'wall_seconds':time.monotonic()-cw,'cpu_seconds':cpu()-cc}
        rec['case_cost']={'wall_seconds':time.monotonic()-beginw,'cpu_seconds':cpu()-beginc,
                          'worker_cumulative_cpu_seconds':cpu(),
                          'worker_peak_rss_bytes_macos':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
        # Analyze outer stage includes parsing; subtraction prevents phase double-counting.
        parse_cpu=sum(x.get('cpu_seconds',0) for x in rec['stages'] if x['name'].startswith('OFFICIAL_PARSE_QUERY_'))
        analysis_cpu=sum(x.get('cpu_seconds',0) for x in rec['stages'] if x['name']=='OFFICIAL_ANALYZE_PARSE_AND_SCOPE_ENCODE')
        rec['exclusive_phase_cpu']={'parse':parse_cpu,'scope_encode':max(0,analysis_cpu-parse_cpu),
            'comparison_formula_encode':rec.get('comparison_formula_encode',{}).get('cpu_seconds'),
            'query_check':sum(x.get('cpu_seconds',0) for x in rec['stages'] if x['name']=='OFFICIAL_QUERY_SOLVER_CHECK')}
        emit('CASE_END',rec)
        gc.collect()
    return rec
