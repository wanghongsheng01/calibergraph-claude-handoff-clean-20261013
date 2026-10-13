"""Round 04 exact-shape problem-evidence pilot; no target imports at import.

One registered pair and exact N per cold process; one attempt, no repeat.
The caller must enforce external process wall/RSS and global CPU accounting.
"""
from contextlib import contextmanager
from datetime import date, timedelta
from pathlib import Path
from types import SimpleNamespace
import builtins, ctypes, hashlib, json, os, resource, sys, time, traceback


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
            raise SolverBudgetOverrun('ACTUAL_SOLVER_WALL_EXCEEDS_REGISTERED_CUMULATIVE_LIMIT')
        return answer


def formula_sha(terms, budget):
    h = hashlib.sha256()
    for f in terms:
        budget.check()
        h.update(f.sexpr().encode()); h.update(b'\n')
    return h.hexdigest()


def evidence_text(rec, protocol, name, text, budget):
    """Keep complete text artifacts; no truncation or model/string gold claim."""
    budget.check()
    target = Path(protocol['_out_dir']) / name
    temp = target.with_name(target.name + '.tmp')
    with temp.open('w') as handle:
        handle.write(text)
        if not text.endswith('\n'):
            handle.write('\n')
        handle.flush()
        os.fsync(handle.fileno())
    temp.replace(target)
    rec.setdefault('evidence_artifacts', {})[name] = {
        'path': str(target), 'sha256': sha(target), 'bytes': target.stat().st_size,
        'complete': True,
    }
    budget.check()


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


def validate_target_raw_C(witness, source, exact_rows):
    """Independent Python check for this complete PK-only C, on encoded values."""
    if source['schema'] != {'COURSES': {'CLASS': 'VARCHAR', 'STUDENT': 'VARCHAR'}} \
            or source['constraint'] != [{'primary': [{'value': 'COURSES__STUDENT'}]}]:
        raise ValueError('RAW_MODEL_C_CHECKER_REJECTS_ADDITIONAL_OR_UNKNOWN_C')
    database = witness['all_physical_raw_values']
    if set(database) != {'COURSES'} or len(database['COURSES']) != exact_rows:
        raise ValueError('RAW_MODEL_EXACT_N_MISMATCH')
    students = []
    for row in database['COURSES']:
        if set(row) != {'CLASS', 'STUDENT'} or type(row['STUDENT']) is not int \
                or (row['CLASS'] is not None and type(row['CLASS']) is not int):
            raise ValueError('RAW_MODEL_STUDENT_NONNULL_OR_ENCODED_TYPE_CHECK_FAILED')
        students.append(row['STUDENT'])
    if len(set(students)) != exact_rows:
        raise ValueError('RAW_MODEL_PRIMARY_STUDENT_NOT_UNIQUE')
    return {'status': 'ALL_ORIGINAL_C_CHECKED_ON_ENCODED_MODEL', 'exact_rows': exact_rows,
        'student_nonnull': True, 'student_unique': True, 'checked_clause_count': 1,
        'unknown_or_dropped_clauses': 0,
        'scope': 'Independent Python PK/exact-shape check on complete raw encoded values; no concrete VARCHAR decoding or SQL replay claim.'}


class SolverTap:
    def __init__(self, target, rec, protocol, budget, emit):
        self.target, self.rec, self.protocol, self.budget, self.emit = target, rec, protocol, budget, emit
        self.answer = None
        self.started_wall, self.started_cpu = time.monotonic(), cpu()

    def __getattr__(self, name):
        return getattr(self.target, name)

    def check(self, *args):
        if args:
            raise ValueError('UNEXPECTED_OFFICIAL_CHECK_ASSUMPTIONS')
        if self.answer is not None:
            raise ValueError('UNREGISTERED_SECOND_QUERY_CHECK')
        self.rec['comparison_formula_encode'] = {'wall_seconds':time.monotonic()-self.started_wall,
            'cpu_seconds':cpu()-self.started_cpu}
        self.rec['submitted_query_assertion_count'] = len(self.target.assertions())
        with stage(self.rec, 'EXPORT_COMPLETE_QUERY_ASSERTIONS', self.budget, self.emit):
            evidence_text(self.rec, self.protocol, 'query_assertions.smt2',
                self.target.sexpr(), self.budget)
        self.answer = check_solver(self.target, self.rec, 'OFFICIAL_QUERY_SOLVER_CHECK',
            self.protocol['query_check_timeout_ms'], self.budget, self.emit)
        self.rec['raw_query_verdict'] = str(self.answer)
        return self.answer


def run_attempt(rt, case, protocol, budget, emit, number):
    src = case['source_record']
    rec = {'id':case['id'], 'attempt':number, 'status':'STARTED', 'stages':[],
        'environment_identity':'one cold Environment and Solver; full original schema/C/query re-encoded; no repeat',
        'exact_rows':{t:protocol['exact_rows_per_table'] for t in src['schema']},
        'raw_query_verdict':None, 'full_C_nonempty':None}
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
            rec['exact_shape_semantics'] = {
                'live_rows_per_table': protocol['exact_rows_per_table'],
                'official_create_database_NotDeleted_facts_retained': True,
                'is_up_to_bound': False, 'fixture_constraints_added': False,
            }
        with stage(rec, 'FULL_C_SOLVER_SETUP', budget, emit):
            contract_solver = rt.z3.Solver(ctx=rt.constants.Z3_CONTEXT)
            contract_solver.add(*facts)
        with stage(rec, 'EXPORT_COMPLETE_C_ASSERTIONS', budget, emit):
            evidence_text(rec, protocol, 'contract_assertions.smt2', contract_solver.sexpr(), budget)
        ans = check_solver(contract_solver, rec, 'FULL_C_NONEMPTY_CHECK',
            protocol['contract_check_timeout_ms'], budget, emit)
        rec['full_C_nonempty'] = str(ans)
        if str(ans) != 'sat':
            rec.update(status='CONTRACT_STOP', engineering_class='CONTRACT_INCONSISTENT_EXACT_N'
                if str(ans)=='unsat' else 'CONTRACT_NONEMPTY_UNKNOWN')
            return rec
        with stage(rec, 'FULL_C_SAT_MODEL_VALIDATION', budget, emit):
            contract_model = contract_solver.model()
            verify_facts(rt, contract_model, facts, budget)
            rec['C_SAT_all_original_facts_true'] = True
            rec['C_witness'] = export_complete_model(rt, env, contract_model, src['schema'], budget)
            rec['C_witness_independent_C_check'] = validate_target_raw_C(
                rec['C_witness'], src, protocol['exact_rows_per_table'])
            evidence_text(rec, protocol, 'contract_full_model.sexpr', contract_model.sexpr(), budget)
        env.save_checkpoints()
        original_parse, original_compare = env.parse_sql_query, env.compare
        rec['parsed_asts'] = []
        def parse(sql):
            with stage(rec, 'OFFICIAL_PARSE_QUERY_'+str(len(rec['parsed_asts'])), budget, emit) as st:
                ast = original_parse(sql)
                try:
                    stored = json.loads(json.dumps(ast, ensure_ascii=False, allow_nan=False))
                except (TypeError, ValueError) as exc:
                    raise ValueError('COMPLETE_JSON_AST_EVIDENCE_UNAVAILABLE') from exc
                st['ast_json_lossless'] = True
                rec['parsed_asts'].append(stored)
                st['ast_sha256'] = objsha(stored)
                st['ast_hash_scope'] = 'lossless canonical JSON; actual AST passed unchanged to encoder'
                evidence_text(rec, protocol, 'parsed_ast_' + str(len(rec['parsed_asts'])) + '.json',
                    json.dumps(stored, ensure_ascii=False, indent=2, allow_nan=False), budget)
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
        try:
            rec['official_compare_return'] = original_compare(captured['tables'], captured['result_formulas'])
        except Exception:
            if str(tap.answer) != 'unknown':
                raise
        rec['latest_stage'] = 'OFFICIAL_COMPARISON_FORMULA_ENCODING_AND_CHECK_RETURNED'
        rec['active_stage'] = None
        emit('OFFICIAL_COMPARE_END',rec)
        if tap.answer is None:
            rec.update(status='RETURNED_WITHOUT_SOLVER', engineering_class='FRONTEND_UNSUPPORTED',
                reason='OFFICIAL_COMPARE_EARLY_RETURN_NO_QUERY_CHECK')
            return rec
        if str(tap.answer) == 'sat':
            with stage(rec, 'RAW_SAT_MODEL_VALIDATION_AND_EXPORT', budget, emit):
                model = tap.target.model()
                assertions = list(tap.target.assertions())
                verify_facts(rt, model, facts+assertions, budget)
                rec['SAT_all_original_facts_and_actual_assertions_true'] = True
                rec['witness'] = export_complete_model(rt, env, model, src['schema'], budget)
                rec['witness_independent_C_check'] = validate_target_raw_C(
                    rec['witness'], src, protocol['exact_rows_per_table'])
                evidence_text(rec, protocol, 'query_full_model.sexpr', model.sexpr(), budget)
                rec['complete_operational_C_check'] = 'ALL_ORIGINAL_SUBMITTED_FACTS_MODEL_TRUE'
                rec['independent_concrete_C_checker'] = 'SEPARATE_SQLITE_FIXTURE_WORKER; no generic decoding/replay of this official model'
        rec.update(status='RETURNED', engineering_class='QUERY_RETURNED',
            result_scope='official encoding at exactly N live rows per table only; not up-to-bound, DBMS equivalence or natural bug')
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
        parse_cpu = sum(s.get('cpu_seconds',0) for s in rec['stages'] if s['name'].startswith('OFFICIAL_PARSE_QUERY_'))
        analyze_cpu = sum(s.get('cpu_seconds',0) for s in rec['stages'] if s['name']=='OFFICIAL_ANALYZE_PARSE_AND_SCOPE_ENCODE')
        rec['exclusive_phase_cpu'] = {'parse':parse_cpu,'scope_encode':max(0,analyze_cpu-parse_cpu),
            'compare_encode':rec.get('comparison_formula_encode',{}).get('cpu_seconds'),
            'query_check':sum(s.get('actual_check_cpu_seconds',0) for s in rec['stages'] if s['name']=='OFFICIAL_QUERY_SOLVER_CHECK')}
        rec['attempt_cost'] = {'cpu_seconds':cpu()-c, 'wall_seconds':time.monotonic()-w,
            'worker_peak_rss_bytes_macos':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
        emit('ATTEMPT_END', rec)
    return rec


def run_case(rt, case, protocol, budget, emit, record):
    attempt = run_attempt(rt, case, protocol, budget, emit, 1)
    record['attempts'].append(attempt)
    record['repeat_triggered'] = False
    record['maximum_attempts'] = 1
    record['repeat_policy'] = 'NO_INDEPENDENT_REPEAT_REGISTERED'
    record['status'] = 'RETURNED'
    record['engineering_class'] = attempt['engineering_class']
    known = (attempt.get('status') == 'RETURNED' and attempt.get('full_C_nonempty') == 'sat'
        and attempt.get('raw_query_verdict') in ('sat', 'unsat'))
    record['strict_class'] = 'OFFICIAL_EXACT_N_OBSERVATION' if known else 'INCONCLUSIVE'
    record['solver_calls'] = budget.solver_calls
    record['solver_cumulative_wall_seconds'] = budget.solver_wall
    record['solver_cumulative_cpu_seconds'] = budget.solver_cpu
    record['natural_bug_or_business_equivalence'] = 'NOT_ESTABLISHED'
    record['mechanism_or_competitive_win'] = 'NOT_ESTABLISHED'
    record['stable_cost_evidence'] = 'NOT_ESTABLISHED_SINGLE_ATTEMPT'
    if budget.solver_wall > protocol['solver_cumulative_wall_limit_seconds']:
        record.update(status='BUDGET_VIOLATION', engineering_class='INCONCLUSIVE', strict_class='INCONCLUSIVE')
    emit('SINGLE_ATTEMPT_COMPLETE', record)
    return record
