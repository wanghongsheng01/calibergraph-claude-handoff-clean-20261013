"""Round 16 official generation preparation; no target imports at module import.

One registered pair per process, complete input, one independent Environment only.
The caller must enforce external process wall/RSS and global CPU accounting.
"""
from contextlib import contextmanager
from datetime import date, timedelta
from pathlib import Path
from types import SimpleNamespace
import builtins, ctypes, gc, hashlib, json, resource, sys, time, traceback


class BudgetStop(RuntimeError):
    pass


class SolverBudgetOverrun(BudgetStop):
    pass


def cpu():
    x = resource.getrusage(resource.RUSAGE_SELF)
    return x.ru_utime + x.ru_stime


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(262144), b''):
            h.update(block)
    return h.hexdigest()


def objsha(x):
    return hashlib.sha256(json.dumps(x, sort_keys=True, ensure_ascii=False,
        separators=(',', ':'), allow_nan=False).encode()).hexdigest()


class Budget:
    def __init__(self, protocol, process_start_wall):
        self.protocol = protocol
        self.start_wall = process_start_wall
        self.solver_wall = 0.0
        self.solver_cpu = 0.0
        self.solver_calls = []
        self.solver_check_active = False
        self.solver_check_start_monotonic = None
        self.check_count = 0

    def check(self):
        if cpu() >= self.protocol['worker_cpu_limit_seconds'] - .25:
            raise BudgetStop('CPU_RESERVE_REACHED')
        if time.monotonic() - self.start_wall >= self.protocol['worker_wall_limit_seconds'] - .25:
            raise BudgetStop('WALL_RESERVE_REACHED')
        if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss >= self.protocol['external_rss_limit_bytes']:
            raise BudgetStop('OBSERVED_RSS_LIMIT')

    def solver_timeout(self, requested_ms):
        self.check()
        remaining = min(self.protocol['solver_cumulative_wall_limit_seconds'] - self.solver_wall - self.protocol['solver_timeout_reserve_seconds'],
            self.protocol['worker_cpu_limit_seconds'] - cpu() - .25,
            self.protocol['worker_wall_limit_seconds'] - (time.monotonic()-self.start_wall) - .25)
        timeout = min(int(requested_ms), int(remaining * 1000))
        if timeout < 1:
            raise BudgetStop('NO_SOLVER_BUDGET_REMAINING')
        return timeout


@contextmanager
def stage(rec, name, budget, emit):
    budget.check()
    previous_stage = rec.get('active_stage')
    st = {'name':name, 'status':'STARTED'}
    rec.setdefault('stages', []).append(st)
    rec['active_stage'] = name
    emit('STAGE_START', rec)
    w, c = time.monotonic(), cpu()
    try:
        yield st
        st['status'] = 'RETURNED'
    except BaseException as exc:
        st.update(status='RAISED', error_type=type(exc).__name__, error=str(exc)[:2000])
        rec.setdefault('failure_stage', name)
        raise
    finally:
        st.update(wall_seconds=time.monotonic()-w, cpu_seconds=cpu()-c)
        rec['latest_stage'] = name
        rec['active_stage'] = previous_stage
        emit('STAGE_END', rec)


def load_runtime(protocol, budget, emit):
    rec = {'id':'runtime', 'stages':[]}
    with stage(rec, 'LOCK_AND_DEPENDENCY_HASH', budget, emit) as st:
        p = Path(protocol['runtime_lock']['path'])
        if sha(p) != protocol['runtime_lock']['sha256']:
            raise ValueError('RUNTIME_LOCK_HASH_MISMATCH')
        lock = json.loads(p.read_text())
        for path, expected in lock['files'].items():
            budget.check()
            f = Path(path)
            if not f.is_file() or f.is_symlink() or sha(f) != expected:
                raise ValueError('PINNED_FILE_MISMATCH: '+path)
        st['checked_files'] = len(lock['files'])
    with stage(rec, 'NATIVE_AND_OFFICIAL_IMPORT', budget, emit) as st:
        library = ctypes.CDLL(lock['native_path'])
        builtins.Z3_LIB_DIRS = [str(Path(lock['native_path']).parent)]
        sys.path[:0] = [lock['binding_root'], lock['support_root'], *lock['dependency_roots'], lock['source_root']]
        import z3
        from z3 import z3core
        defaults = z3core.Z3_get_version.__defaults__
        if len(defaults) != 1:
            raise ValueError('UNEXPECTED_NATIVE_WRAPPER')
        a = ctypes.cast(defaults[0].f, ctypes.c_void_p).value
        b = ctypes.cast(library.Z3_get_version, ctypes.c_void_p).value
        if not a or a != b or list(z3.get_version()) != lock['expected_native_version']:
            raise ValueError('NATIVE_IDENTITY_MISMATCH')
        from environment import Environment
        import constants
        if Path(sys.modules['environment'].__file__).resolve() != Path(lock['source_root'])/'environment.py':
            raise ValueError('OFFICIAL_SOURCE_ORIGIN_MISMATCH')
        if not Path(z3.__file__).resolve().is_relative_to(Path(lock['binding_root'])):
            raise ValueError('BINDING_SOURCE_ORIGIN_MISMATCH')
        z3.set_param('parallel.enable', False)
        z3.set_param('memory_max_size', protocol['internal_z3_memory_parameter_mb'])
        st.update(version=list(z3.get_version()), native_path=lock['native_path'], native_sha256=sha(lock['native_path']))
    return SimpleNamespace(z3=z3, constants=constants, Environment=Environment,
        library=library, lock=lock, initialization=rec)


def source_class(case):
    src = case.get('source_record')
    if not isinstance(src, dict) or 'constraint' not in src:
        return 'MISSING'
    if src['constraint'] is None:
        return 'NULL_UNSPECIFIED'
    if src['constraint'] == []:
        return 'EXPLICIT_EMPTY_OPERATIONAL'
    value = src['constraint']
    return 'PRESENT_JSON' if isinstance(value,list) and value and all(isinstance(x,dict) and x for x in value) else 'INSUFFICIENT'


def evidence_complete(case):
    e = case.get('semantic_admission', {})
    source = case.get('source', {})
    return isinstance(source,dict) and bool(source.get('raw_line_sha256')) and bool(case.get('source_group_id')) \
        and isinstance(e, dict) and all(e.get(k) is True for k in (
        'complete_original_schema_and_C', 'original_sql_to_official_ast_reviewed'))


def check_solver(solver, rec, name, requested_ms, budget, emit):
    with stage(rec, name, budget, emit) as st:
        timeout = budget.solver_timeout(requested_ms)
        solver.set(timeout=timeout, threads=1)
        st['timeout_ms'] = timeout
        budget.check_count += 1
        budget.solver_check_active = True
        budget.solver_check_start_monotonic = time.monotonic()
        emit('SOLVER_CHECK_START',rec)
        w, c = time.monotonic(), cpu()
        try:
            answer = solver.check()
        finally:
            elapsed_w, elapsed_c = time.monotonic()-w, cpu()-c
            budget.solver_wall += elapsed_w
            budget.solver_cpu += elapsed_c
            budget.solver_check_active = False
            budget.solver_check_start_monotonic = None
            call = {'attempt':rec.get('attempt'), 'stage':name, 'actual_check_wall_seconds':elapsed_w,
                'actual_check_cpu_seconds':elapsed_c, 'timeout_ms':timeout}
            budget.solver_calls.append(call)
            st.update(call)
            rec['solver_cumulative_wall_seconds'] = budget.solver_wall
            rec['solver_cumulative_cpu_seconds'] = budget.solver_cpu
            emit('SOLVER_CHECK_END',rec)
        st['answer'] = str(answer)
        if str(answer) == 'unknown':
            st['reason_unknown'] = solver.reason_unknown()
        if budget.solver_wall > budget.protocol['solver_cumulative_wall_limit_seconds']:
            st['budget_overrun_seconds'] = budget.solver_wall-budget.protocol['solver_cumulative_wall_limit_seconds']
            raise SolverBudgetOverrun('ACTUAL_SOLVER_WALL_EXCEEDS_2_SECONDS')
        return answer


def formula_sha(terms, budget):
    h = hashlib.sha256()
    for f in terms:
        budget.check()
        h.update(f.sexpr().encode()); h.update(b'\n')
    return h.hexdigest()


def verify_facts(rt, model, facts, budget):
    for f in facts:
        budget.check()
        if not rt.z3.is_true(model.eval(f, model_completion=True)):
            raise ValueError('SAT_MODEL_FAILED_SUBMITTED_FACT_OR_ASSERTION')


def export_complete_model(rt, env, model, schema, budget):
    """Full raw operational values; no generic SQLite/string/date gold claim."""
    database, decoded = {}, {}
    for table, columns in schema.items():
        physical = env.base_databases[table.upper()]
        attrs = list(physical.attributes)
        if [a.name.upper() for a in attrs] != [c.upper() for c in columns]:
            raise ValueError('MODEL_ATTRIBUTE_ORDER_MISMATCH')
        database[table], decoded[table] = [], []
        for tup in physical:
            budget.check()
            if not rt.z3.is_false(model.eval(env.DELETED_FUNCTION(tup.SORT), model_completion=True)):
                raise ValueError('EXACT_SHAPE_MODEL_HAS_DELETED_ROW')
            raw, row = {}, {}
            for (col, typ), attr in zip(columns.items(), attrs):
                nul = rt.z3.is_true(model.eval(attr.NULL(tup.SORT), model_completion=True))
                value = None if nul else model.eval(attr.VALUE(tup.SORT), model_completion=True).as_long()
                raw[col] = value
                if value is None or typ.upper() == 'INT':
                    row[col] = value
                elif typ.upper() in ('BOOL','BOOLEAN'):
                    row[col] = bool(value)
                elif typ.upper() == 'DATE':
                    row[col] = (date(1970,1,1)+timedelta(days=value-1)).isoformat()
                elif typ.upper() == 'VARCHAR':
                    row[col] = {'official_encoded_string_symbol':value}
                else:
                    raise ValueError('UNSUPPORTED_MODEL_TYPE')
            database[table].append(raw); decoded[table].append(row)
    return {'all_physical_raw_values':database, 'decoded_values':decoded,
        'scope':'complete official model; VARCHAR stays encoded, literals/order/collation not decoded; no DBMS replay or business gold'}


class SolverTap:
    def __init__(self, target, rec, protocol, budget, emit):
        self.target, self.rec, self.protocol, self.budget, self.emit = target, rec, protocol, budget, emit
        self.answer = None
        self.started_wall, self.started_cpu = time.monotonic(), cpu()
        self.rec['comparison_formula_encode_status'] = 'STARTED'

    def __getattr__(self, name):
        return getattr(self.target, name)

    def check(self, *args):
        if args:
            raise ValueError('UNEXPECTED_OFFICIAL_CHECK_ASSUMPTIONS')
        self.rec['comparison_formula_encode'] = {'wall_seconds':time.monotonic()-self.started_wall,
            'cpu_seconds':cpu()-self.started_cpu}
        self.rec['comparison_formula_encode_status'] = 'REACHED_QUERY_CHECK'
        self.rec['submitted_query_assertion_count'] = len(self.target.assertions())
        self.answer = check_solver(self.target, self.rec, 'OFFICIAL_QUERY_SOLVER_CHECK',
            self.protocol['query_check_timeout_ms'], self.budget, self.emit)
        self.rec['raw_query_verdict'] = str(self.answer)
        return self.answer


def measured_stage_cpu(stages, field='cpu_seconds'):
    """Read timing evidence only; an absent stage is never a measured zero."""
    if not stages:
        return None, 'NOT_REACHED'
    if any(s.get(field) is None for s in stages):
        return None, 'UNMEASURED_OR_CENSORED'
    return sum(s[field] for s in stages), 'MEASURED'


def run_attempt(rt, case, protocol, budget, emit, number):
    src = case['source_record']
    rec = {'id':case['id'], 'attempt':number, 'status':'STARTED', 'stages':[],
        'environment_identity':'new independent Environment and Solver; full schema/C/query re-encoded',
        'exact_rows':{t:protocol['exact_rows_per_table'] for t in src['schema']},
        'raw_query_verdict':None, 'full_C_nonempty':None,
        'comparison_formula_encode':None,
        'comparison_formula_encode_status':'NOT_REACHED',
        'contract_model_sanity': {'status': 'NOT_REACHED' if case['id'] in ('dev03_10', 'dev03_15') else 'NOT_ADMITTED',
            'model_origin': 'FULL_C_NONEMPTY_CHECK', 'scope': 'C_MODEL_SANITY_ONLY_NOT_QUERY_SAT',
            'query_sat_witness': False, 'method_claim': 'EXISTING_C_SAMPLING_SANITY_CONTROL_ONLY'}}
    env = None
    w, c = time.monotonic(), cpu()
    try:
        with stage(rec, 'ENVIRONMENT_AND_FULL_SCHEMA', budget, emit):
            env = rt.Environment(timer=False, generate_code=False, show_counterexample=False,
                dialect=rt.constants.DIALECT.ALL)
            env.__enter__()
            for table, fields in src['schema'].items():
                budget.check()
                env.create_database(attributes=fields, bound_size=protocol['exact_rows_per_table'], name=table)
        with stage(rec, 'FULL_ORIGINAL_IC_ADMISSION', budget, emit) as st:
            before = len(env.DBMS_facts)
            env.add_constraints(src['constraint'])
            facts = list(env.DBMS_facts) + sorted(env.bound_constraints, key=lambda f:f.sexpr())
            st.update(original_clause_count=len(src['constraint'] or []), base_fact_count=before,
                admitted_delta_facts=len(env.DBMS_facts)-before, full_fact_count=len(facts))
            rec['full_contract_fact_sha256'] = formula_sha(facts, budget)
        with stage(rec, 'FULL_C_SOLVER_SETUP', budget, emit):
            contract_solver = rt.z3.Solver(ctx=rt.constants.Z3_CONTEXT)
            contract_solver.add(*facts)
        ans = check_solver(contract_solver, rec, 'FULL_C_NONEMPTY_CHECK',
            protocol['contract_check_timeout_ms'], budget, emit)
        rec['full_C_nonempty'] = str(ans)
        if str(ans) != 'sat':
            rec.update(status='CONTRACT_STOP', engineering_class='CONTRACT_INCONSISTENT_AT_REGISTERED_EXACT_N'
                if str(ans)=='unsat' else 'CONTRACT_NONEMPTY_UNKNOWN')
            return rec
        with stage(rec, 'FULL_C_SAT_MODEL_VALIDATION', budget, emit):
            contract_model = contract_solver.model()
            verify_facts(rt, contract_model, facts, budget)
        # Existing C-sampling sanity control: same already validated full-C model.
        # It makes no query-SAT assertion and never feeds run_case strict_class.
        if protocol.get('contract_model_sanity_control') is True and case['id'] in ('dev03_10', 'dev03_15'):
            sanity = rec['contract_model_sanity']
            sanity['status'] = 'STARTED'
            try:
                with stage(rec, 'C_MODEL_SANITY_RAW_EXPORT', budget, emit):
                    sanity['witness'] = export_complete_model(rt, env, contract_model, src['schema'], budget)
                with stage(rec, 'C_MODEL_SANITY_FULL_C_AND_ORIGINAL_SQL_REPLAY', budget, emit):
                    from safe_sqlite_replay import replay_generated_witness
                    sanity['replay'] = replay_generated_witness(case, sanity['witness'], env, protocol, budget)
                    sanity['replay'].update(model_origin='FULL_C_NONEMPTY_CHECK',
                        scope='C_MODEL_SANITY_ONLY_NOT_QUERY_SAT', query_sat_witness=False)
                sanity['status'] = 'RETURNED'
            except (BudgetStop, SolverBudgetOverrun):
                # The control shares the worker's fixed budget; no extra allowance.
                sanity['status'] = 'RESOURCE_STOP'
                raise
            except Exception as exc:
                sanity.update(status='CONTROL_ERROR', error_type=type(exc).__name__, error=str(exc)[:2000])
                # A control failure must not contaminate later query-stage classification.
                if rec.get('failure_stage', '').startswith('C_MODEL_SANITY_'):
                    rec.pop('failure_stage')
            emit('C_MODEL_SANITY_COMPLETE', rec)
        env.save_checkpoints()
        original_parse, original_compare = env.parse_sql_query, env.compare
        rec['parsed_asts'] = []
        def parse(sql):
            with stage(rec, 'OFFICIAL_PARSE_QUERY_'+str(len(rec['parsed_asts'])), budget, emit) as st:
                ast = original_parse(sql)
                try:
                    stored = json.loads(json.dumps(ast, ensure_ascii=False, allow_nan=False))
                except (TypeError, ValueError):
                    # Do not reject official ValuesTable merely because JSON cannot store it.
                    stored = {'representation':'NON_JSON_AST', 'type':type(ast).__name__, 'repr':repr(ast)[:16000]}
                    st['ast_json_lossless'] = False
                else:
                    st['ast_json_lossless'] = True
                rec['parsed_asts'].append(stored)
                st['ast_sha256'] = objsha(stored)
                st['ast_hash_scope'] = 'lossless canonical JSON' if st['ast_json_lossless'] else 'tagged truncated repr only; actual AST passed unchanged to encoder'
                return ast
        captured = {}
        def capture(tables, result_formulas, out_file=None):
            captured.update(tables=tables, result_formulas=result_formulas)
            return None
        env.parse_sql_query, env.compare = parse, capture
        with stage(rec, 'OFFICIAL_ANALYZE_PARSE_AND_SCOPE_ENCODE', budget, emit) as st:
            try:
                env.analyze(*src['pair'])
            finally:
                env.parse_sql_query, env.compare = original_parse, original_compare
            if not captured:
                raise ValueError('OFFICIAL_ANALYZE_DID_NOT_REACH_COMPARE')
            st['formula_counts'] = [len(x) for x in captured['result_formulas']]
            st['output_tuple_counts'] = [len(x) for x in captured['tables']]
        tap = SolverTap(env.solver, rec, protocol, budget, emit)
        env.solver = tap
        rec['active_stage'] = 'OFFICIAL_COMPARISON_FORMULA_ENCODING'
        emit('STAGE_START', rec)
        comparison_returned = False
        try:
            try:
                rec['official_compare_return'] = original_compare(captured['tables'], captured['result_formulas'])
            except Exception:
                if str(tap.answer) != 'unknown':
                    raise
            comparison_returned = True
        finally:
            # Pure measurement: no added solver call or budget extension. If a
            # hard signal prevents finally, STARTED remains censored, not zero.
            if rec.get('comparison_formula_encode') is None:
                rec['comparison_formula_encode'] = {
                    'wall_seconds':time.monotonic()-tap.started_wall,
                    'cpu_seconds':cpu()-tap.started_cpu}
                rec['comparison_formula_encode_status'] = (
                    'RETURNED_WITHOUT_QUERY_CHECK' if comparison_returned else 'RAISED_BEFORE_QUERY_CHECK')
        rec['latest_stage'] = 'OFFICIAL_COMPARISON_FORMULA_ENCODING_AND_CHECK_RETURNED'
        rec['active_stage'] = None
        emit('OFFICIAL_COMPARE_END',rec)
        if tap.answer is None:
            rec.update(status='RETURNED_WITHOUT_SOLVER', engineering_class='FRONTEND_UNSUPPORTED',
                reason='OFFICIAL_COMPARE_EARLY_RETURN_NO_QUERY_CHECK')
            return rec
        if str(tap.answer) == 'sat':
            with stage(rec, 'SAT_MODEL_FULL_FACT_VALIDATION', budget, emit):
                model = tap.target.model()
                assertions = list(tap.target.assertions())
                verify_facts(rt, model, facts+assertions, budget)
                rec['SAT_all_original_facts_and_actual_assertions_true'] = True
                rec['complete_operational_C_check'] = 'ALL_ORIGINAL_SUBMITTED_FACTS_MODEL_TRUE'
                rec['independent_concrete_C_checker'] = 'PENDING_STRICT_REPLAY_ADMISSION'
            with stage(rec, 'RAW_MODEL_EXPORT', budget, emit):
                rec['witness'] = export_complete_model(rt, env, model, src['schema'], budget)
            with stage(rec, 'DECODE_INDEPENDENT_FULL_C_AND_ORIGINAL_SQL_REPLAY', budget, emit):
                from safe_sqlite_replay import replay_generated_witness
                rec['replay'] = replay_generated_witness(case, rec['witness'], env, protocol, budget)
                rec['independent_concrete_C_checker'] = rec['replay'].get('full_C_status', 'NOT_CHECKED')
        rec.update(status='RETURNED', engineering_class='QUERY_RETURNED',
            result_scope='official encoding at registered exact N live rows per table only; no up-to bound, DBMS equivalence or natural bug')
    except SolverBudgetOverrun as exc:
        rec.update(status='BUDGET_VIOLATION', engineering_class='INCONCLUSIVE', reason=str(exc))
    except BudgetStop as exc:
        phase = rec.get('failure_stage') or rec.get('active_stage') or rec.get('latest_stage') or 'UNKNOWN'
        encoding = phase in ('OFFICIAL_ANALYZE_PARSE_AND_SCOPE_ENCODE','OFFICIAL_COMPARISON_FORMULA_ENCODING')
        rec.update(status='RESOURCE_STOP', engineering_class='COST_SIGNAL_ENCODING_UNCONFIRMED' if encoding else 'INCONCLUSIVE',
            resource_stop_phase=phase, resource_component='PARSING' if phase.startswith('OFFICIAL_PARSE_QUERY_') else ('ENCODING' if encoding else 'OTHER'),
            reason=str(exc))
    except Exception as exc:
        phase = rec.get('failure_stage') or rec.get('active_stage') or rec.get('latest_stage') or 'UNKNOWN'
        if phase in ('FULL_ORIGINAL_IC_ADMISSION','FULL_C_SOLVER_SETUP','FULL_C_NONEMPTY_CHECK'):
            kind = 'CONTRACT_UNSUPPORTED' if type(exc).__name__ in ('NotSupportedError','NotImplementedError','SyntaxError','KeyError') else 'INCONCLUSIVE'
        elif phase == 'ENVIRONMENT_AND_FULL_SCHEMA':
            kind = 'SCHEMA_UNSUPPORTED'
        elif phase.startswith('OFFICIAL_PARSE') or phase in ('OFFICIAL_ANALYZE_PARSE_AND_SCOPE_ENCODE','OFFICIAL_COMPARISON_FORMULA_ENCODING'):
            kind = 'FRONTEND_UNSUPPORTED' if type(exc).__name__ in ('NotSupportedError','NotImplementedError','SyntaxError','ParseException','ParseSyntaxException') else 'INCONCLUSIVE'
        else:
            kind = 'INCONCLUSIVE'
        rec.update(status='STAGE_ERROR', engineering_class=kind, failure_stage=phase,
            error_type=type(exc).__name__, error=str(exc)[:4000], traceback=traceback.format_exc()[-10000:])
        if isinstance(exc, MemoryError):
            rec['engineering_class'] = 'COST_SIGNAL_ENCODING_UNCONFIRMED' if 'ENCODE' in phase or 'ENCODING' in phase else 'INCONCLUSIVE'
    finally:
        if env is not None:
            rec['active_stage'] = 'CLEANUP'
            emit('CLEANUP_START',rec)
            cw, cc = time.monotonic(), cpu()
            try:
                env.__exit__(None,None,None)
                rec['cleanup'] = 'OFFICIAL_EXIT_RETURNED_NOT_OBJECT_RELEASE_PROOF'
            except BaseException as exc:
                rec['cleanup'] = 'FAILED'
                rec['cleanup_error'] = type(exc).__name__+': '+str(exc)
            rec['cleanup_cost'] = {'wall_seconds':time.monotonic()-cw,'cpu_seconds':cpu()-cc}
            rec['active_stage'] = None
            rec['latest_stage'] = 'CLEANUP'
        parse_cpu, parse_status = measured_stage_cpu(
            [s for s in rec['stages'] if s['name'].startswith('OFFICIAL_PARSE_QUERY_')])
        analyze_cpu, analyze_status = measured_stage_cpu(
            [s for s in rec['stages'] if s['name']=='OFFICIAL_ANALYZE_PARSE_AND_SCOPE_ENCODE'])
        query_cpu, query_status = measured_stage_cpu(
            [s for s in rec['stages'] if s['name']=='OFFICIAL_QUERY_SOLVER_CHECK'],
            'actual_check_cpu_seconds')
        scope_cpu = None if analyze_cpu is None or parse_cpu is None else max(0,analyze_cpu-parse_cpu)
        scope_status = (analyze_status if analyze_cpu is None else
            ('UNMEASURED_PARSE_DEPENDENCY' if parse_cpu is None else 'DERIVED_ANALYZE_MINUS_PARSE'))
        rec['exclusive_phase_cpu'] = {'parse':parse_cpu,'scope_encode':scope_cpu,
            'compare_encode':(rec.get('comparison_formula_encode') or {}).get('cpu_seconds'),
            'query_check':query_cpu}
        rec['exclusive_phase_cpu_status'] = {'parse':parse_status,'scope_encode':scope_status,
            'compare_encode':rec['comparison_formula_encode_status'],'query_check':query_status}
        rec['attempt_cost'] = {'cpu_seconds':cpu()-c, 'wall_seconds':time.monotonic()-w,
            'worker_peak_rss_bytes_macos':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
        emit('ATTEMPT_END', rec)
    return rec


def run_case(rt, case, protocol, budget, emit, record):
    if protocol['maximum_independent_environment_attempts'] != 1:
        raise ValueError('ONE_OFFICIAL_ATTEMPT_ONLY')
    first = run_attempt(rt, case, protocol, budget, emit, 1)
    record['attempts'].append(first)
    record.update(status=first['status'], engineering_class=first['engineering_class'],
        strict_class='INCONCLUSIVE', repeat_triggered=False,
        natural_bug_or_business_equivalence='NOT_ESTABLISHED',
        solver_calls=budget.solver_calls, solver_cumulative_wall_seconds=budget.solver_wall,
        solver_cumulative_cpu_seconds=budget.solver_cpu)
    query_calls = [c for c in budget.solver_calls if c['stage'] == 'OFFICIAL_QUERY_SOLVER_CHECK']
    record['query_solver_called'] = bool(query_calls)
    record['hardness_claim'] = 'NOT_ESTABLISHED_SINGLE_ATTEMPT'
    if not query_calls:
        record['hardness_claim'] = 'NOT_APPLICABLE_QUERY_SOLVER_ZERO_CALLS'
    replay = first.get('replay', {})
    if replay.get('status') == 'REPLAY_CONFIRMED_DIFFERENCE':
        record['strict_class'] = 'GENERATED_WITNESS_REPLAY_CONFIRMED_EXACT_N_OPERATIONAL_C'
    elif first.get('raw_query_verdict') == 'unsat':
        record['strict_class'] = 'OFFICIAL_EXACT_N_UNSAT_ONLY'
    record['result_scope'] = 'Exposed development case; exact N, full operational C; not natural SAT/UNSAT gold or hardness.'
    emit('SINGLE_ATTEMPT_COMPLETE', record)
    return record
