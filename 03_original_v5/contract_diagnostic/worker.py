"""Frozen, constructed IC direction diagnostic. Root controls actual execution."""
import time
START = time.monotonic()
import signal
import resource
signal.signal(signal.SIGALRM, signal.SIG_DFL)
signal.signal(signal.SIGXCPU, signal.SIG_DFL)
signal.pthread_sigmask(signal.SIG_UNBLOCK, {signal.SIGALRM, signal.SIGXCPU})
signal.setitimer(signal.ITIMER_REAL, max(0.001, 24 - (time.monotonic() - START)))
resource.setrlimit(resource.RLIMIT_CPU, (14, 15))
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))

import argparse
import hashlib
import importlib.util
import json
import operator
import os
from pathlib import Path
import sys
import threading
import traceback

HERE = Path(__file__).resolve().parent
TODAY = HERE.parent
OPS = {'lt': operator.lt, 'lte': operator.le, 'gt': operator.gt,
       'gte': operator.ge, 'eq': operator.eq, 'neq': operator.ne}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    temporary = Path(str(path) + '.tmp')
    with temporary.open('w') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
    temporary.replace(path)


def original_truth(ast, point):
    """Independent Python AST evaluator; original operand order is preserved."""
    if not isinstance(ast, dict) or len(ast) != 1:
        raise ValueError('expected one binary comparison')
    op, operands = next(iter(ast.items()))
    if op not in OPS or not isinstance(operands, list) or len(operands) != 2:
        raise ValueError('outside registered binary comparison domain')
    def value(node):
        if type(node) is int:
            return node
        if node == {'value': 'T__A'}:
            return point
        raise ValueError('unregistered operand')
    left, right = map(value, operands)
    truth = None if left is None or right is None else OPS[op](left, right)
    return {'left': left, 'right': right, 'three_valued_truth': 'UNKNOWN' if truth is None else truth,
            'satisfies_strict_contract': truth is True}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--expected-manifest-sha256', required=True)
    ap.add_argument('--out-dir', type=Path, required=True)
    args = ap.parse_args()
    if sys.platform != 'darwin' or not (sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode):
        raise ValueError('Darwin -B -I -S required')
    out = args.out_dir.resolve()
    if not out.is_relative_to(HERE / 'runs') or not out.is_dir() or any(p.is_symlink() for p in [args.out_dir, *args.out_dir.parents]):
        raise ValueError('supervisor-created nonsymlink result directory required')
    report = {'status': 'NOT_RUN', 'native_load': 'NOT_RUN', 'environment_import': 'NOT_RUN',
              'pid': os.getpid(), 'data_role': 'CONSTRUCTED_CONTRACT_DIAGNOSTIC_NOT_BENCHMARK',
              'cells': [], 'fixed_base_models': [], 'sqlite_controls': [],
              'original_pair': {'status': 'NOT_RUN'}, 'reserved_or_attempted_check_slots': 0,
              'solver_slot_count_scope': 'Guard reserves two slots and analyze reserves one; failure before a check can overcount actual calls. This is not an exact completed-check counter.',
              'scientific_claim': 'No natural defect prevalence, performance, or new contribution claim.'}
    output = out / 'worker_report.json'
    save(output, report)

    def checkpoint(phase):
        r = resource.getrusage(resource.RUSAGE_SELF)
        report.update(phase=phase, resource_last_checkpoint={
            'wall_seconds': time.monotonic() - START, 'cpu_seconds': r.ru_utime + r.ru_stime,
            'peak_rss_bytes_darwin': r.ru_maxrss,
            'python_threads': [{'name': t.name, 'daemon': t.daemon} for t in threading.enumerate()]})
        save(output, report)
        print(json.dumps({'phase': phase}), flush=True)
        if r.ru_maxrss >= 1024 ** 3:
            raise MemoryError('sampled worker RSS reached 1 GiB')

    env = pair_env = None
    try:
        manifest_path = HERE / 'PREPARED_MANIFEST.json'
        if sha(manifest_path) != args.expected_manifest_sha256:
            raise ValueError('prepared manifest changed')
        manifest = json.loads(manifest_path.read_text())
        for raw, digest in manifest['files'].items():
            path = Path(raw)
            if path != path.resolve() or not path.is_file() or sha(path) != digest:
                raise ValueError('registered file changed: ' + raw)
        registration = json.loads((HERE / 'INPUT_REGISTRATION.json').read_text())
        report.update(input=registration, manifest_sha256=args.expected_manifest_sha256)
        points = [6, 4, None, 5]
        report['cells'] = [{'operator': entry['operator'], 'value': point, 'status': 'NOT_RUN'}
                           for entry in registration['comparisons'] for point in points]
        report['cell_denominator'] = len(report['cells'])
        checkpoint('INPUT_REGISTERED_ALL_24_CELLS_NOT_RUN')
        common_path = Path(registration['reused_common']['path'])
        spec = importlib.util.spec_from_file_location('contract_diagnostic_frozen_common', common_path)
        common = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = common
        spec.loader.exec_module(common)
        lock_path = Path(registration['expected_runtime_lock']['path'])
        lock = common.verify_lock(lock_path, registration['expected_runtime_lock']['sha256'])
        library, z3, constants, Environment, kernel = common.load_runtime(lock, checkpoint, report)
        case = {key: registration[key] for key in ('schema', 'exact_rows', 'pair')}
        case['constraint'] = []
        report['raw_frontend_guard'] = common.ensure_raw_frontend(case, kernel)
        checkpoint('RAW_FRONTEND_GUARD_ADMITTED')
        from parsers.constraint_parser import ConstraintParser
        parser_file = Path(sys.modules['parsers.constraint_parser'].__file__).resolve()
        if str(parser_file) not in lock['files'] or sha(parser_file) != lock['files'][str(parser_file)]:
            raise ValueError('constraint parser origin/hash mismatch')
        producer = ConstraintParser()
        env = common.new_env(case, Environment, constants)
        report['reserved_or_attempted_check_slots'] += 2
        base_facts, report['baseline_guard'] = common.guard(env, z3, constants, START)
        if report['baseline_guard']['consistency'] != 'sat' or report['baseline_guard']['any_base_row_deleted'] != 'unsat':
            raise ValueError('baseline exact-row contract guard failed')
        report['baseline_fact_sexprs'] = [f.sexpr() for f in base_facts]
        table = env.base_databases['T']
        rows, attributes = list(table), list(table.attributes)
        if len(rows) != 1 or len(attributes) != 1:
            raise ValueError('registered exact-one-row/one-column shape changed')
        row, attr = rows[0], attributes[0]
        value, null = attr.VALUE(row.SORT), attr.NULL(row.SORT)
        deleted = env.DELETED_FUNCTION(row.SORT)
        if value.sort().kind() != z3.Z3_INT_SORT:
            raise ValueError('registered scalar integer domain not established')

        def do_check(solver, label):
            if report['reserved_or_attempted_check_slots'] >= registration['limits']['maximum_solver_check_calls']:
                raise ValueError('registered solver-call maximum exceeded')
            report['reserved_or_attempted_check_slots'] += 1
            checkpoint('SOLVER_ATTEMPT_' + label)
            status = str(solver.check())
            return {'status': status, 'reason_unknown': solver.reason_unknown() if status == 'unknown' else None}

        def fixed_conditions(point):
            return [constants.Not(deleted), constants.Not(null), value == constants.IntVal(str(point))]

        models = {}
        for point in (6, 4):
            item = {'value': point, 'status': 'ATTEMPTED_EFFECT_UNKNOWN'}
            report['fixed_base_models'].append(item)
            s = common.solver(z3, constants, START, maximum_ms=1000)
            s.add(*(base_facts + fixed_conditions(point)))
            item.update(do_check(s, 'BASE_A_' + str(point)))
            if item['status'] != 'sat':
                raise ValueError('fixed baseline model unavailable: ' + item['status'])
            model = s.model()
            if not all(z3.is_true(model.eval(f, model_completion=True)) for f in base_facts + fixed_conditions(point)):
                raise ValueError('fixed model failed complete baseline/fixed binding audit')
            models[point] = model
            item.update(database=common.decode(env, model, z3), model_sexpr=model.sexpr())
            checkpoint('FIXED_BASE_MODEL_RECORDED_' + str(point))

        for entry_index, entry in enumerate(registration['comparisons']):
            op = entry['operator']
            parsed = (entry['constraint'] if op == 'eq' else producer.parse(entry['original_text']))
            entry_record = {'operator': op, 'input_origin': entry['input_origin'],
                            'original_text': entry['original_text'], 'actual_ast': parsed,
                            'matches_registered_ast': parsed == entry['constraint']}
            report.setdefault('producer_outputs', []).append(entry_record)
            if parsed != entry['constraint']:
                for cell in report['cells'][4 * entry_index:4 * entry_index + 4]:
                    cell.update(status='PRODUCER_AST_MISMATCH_NO_SUBSTITUTED_INPUT')
                checkpoint('PRODUCER_AST_MISMATCH_' + op)
                continue
            before = len(env.DBMS_facts)
            env.add_constraints(parsed)
            emitted = list(env.DBMS_facts[before:])
            if not emitted:
                raise ValueError('actual add_constraints emitted no IC facts')
            formula = constants.And(*emitted)
            entry_record.update(emitted_fact_sexprs=[f.sexpr() for f in emitted],
                                emitted_fact_sha256=hashlib.sha256('\n'.join(f.sexpr() for f in emitted).encode()).hexdigest(),
                                emission_scope='Only this append delta is tested against captured no-IC baseline. Cumulative operator controls are never solved together.')
            for point_index, point in enumerate(points):
                cell = report['cells'][4 * entry_index + point_index]
                cell.update(status='ATTEMPTED_EFFECT_UNKNOWN', original_ast=parsed[0],
                            original_truth=original_truth(parsed[0], point))
                if point in (6, 4):
                    truth = models[point].eval(formula, model_completion=True)
                    cell['formula_evaluation_kind'] = 'ACTUAL_FACT_EVALUATED_IN_FIXED_BASE_MODEL'
                    s = common.solver(z3, constants, START, maximum_ms=1000)
                    s.add(*(base_facts + fixed_conditions(point) + emitted))
                    cell['fixed_smt'] = do_check(s, op.upper() + '_A_' + str(point))
                else:
                    bindings = [(null, constants.BoolVal(point is None))]
                    if point is not None:
                        bindings.append((value, constants.IntVal(str(point))))
                    substituted = z3.substitute(formula, *bindings)
                    truth = models[6].eval(substituted, model_completion=True)
                    cell.update(formula_evaluation_kind='EXACT_FORMULA_SUBSTITUTION_CONTROL_NO_NEW_MODEL_SOLVE',
                                substituted_formula_sexpr=substituted.sexpr(),
                                fixed_smt={'status': 'NOT_RUN_BY_DESIGN_NULL_OR_BOUNDARY_CONTROL'})
                emitted_truth = True if z3.is_true(truth) else False if z3.is_false(truth) else None
                cell.update(official_fact_eval=emitted_truth, official_fact_eval_text=str(truth))
                if emitted_truth is None:
                    cell['status'] = 'UNRESOLVED_FACT_EVALUATION'
                else:
                    cell['matches_original_strict_contract'] = emitted_truth == cell['original_truth']['satisfies_strict_contract']
                    cell['status'] = 'RECORDED_AGREEMENT' if cell['matches_original_strict_contract'] else 'RECORDED_DISAGREEMENT'
                    if point in (6, 4):
                        cell['fixed_smt_matches_fact_evaluation'] = cell['fixed_smt']['status'] == ('sat' if emitted_truth else 'unsat')
                        if not cell['fixed_smt_matches_fact_evaluation']:
                            cell['status'] = 'FIXED_SMT_UNKNOWN_OR_DISAGREEMENT'
                checkpoint('CELL_RECORDED_' + op.upper() + '_' + str(point))

        # SQLite executes the original strings, including NULL and duplicate semantics.
        # Here every table has one INT value in {4,6,NULL}, so integer overflow is impossible.
        for point_case in registration['fixed_databases']:
            replay = common.replay(case['schema'], case['pair'], point_case['database'])
            observed = json.loads(json.dumps(replay['relations']))
            report['sqlite_controls'].append({'id': point_case['id'], 'database': point_case['database'],
                'status': 'RECORDED', 'raw_sql_unchanged': True, 'replay': replay,
                'explicit_domain': 'One integer or NULL, absolute value <=6; SUM has at most one addend.',
                'original_lt_truth': original_truth(registration['primary_constraint'][0], point_case['database']['T'][0][0]),
                'matches_pre_registered_relations': observed == point_case['expected_original_sql_results']})
            checkpoint('SQLITE_CONTROL_RECORDED_' + point_case['id'])
        env.__exit__(None, None, None)
        env = None

        pair_case = dict(case, constraint=producer.parse(registration['original_constraint_text']))
        if pair_case['constraint'] != registration['primary_constraint']:
            raise ValueError('primary parser AST changed before original-pair run')
        common.ensure_raw_frontend(pair_case, kernel)
        pair_env = common.new_env(pair_case, Environment, constants)
        pair_report = report['original_pair']
        pair_report.update(status='ATTEMPTED_EFFECT_UNKNOWN', original_pair=pair_case['pair'],
                           actual_constraint_ast=pair_case['constraint'],
                           constraint_scope='Official emitted constraint; not a correction to the original AST semantics.')
        report['reserved_or_attempted_check_slots'] += 2
        pair_facts, pair_report['contract_guard'] = common.guard(pair_env, z3, constants, START)
        pair_report['complete_fact_sexprs'] = [f.sexpr() for f in pair_facts]
        if pair_report['contract_guard']['consistency'] != 'sat' or pair_report['contract_guard']['any_base_row_deleted'] != 'unsat':
            raise ValueError('original-pair emitted contract guard failed')
        pair_report['actual_verifier_semantics'] = common.verifier_semantics(pair_env, lock)
        pair_env.solver.set(timeout=common.budget_ms(START), threads=1)
        report['reserved_or_attempted_check_slots'] += 1
        checkpoint('ORIGINAL_PAIR_OFFICIAL_ANALYZE_ATTEMPT')
        try:
            answer = pair_env.analyze(*pair_case['pair'])
            if type(answer) is not bool:
                raise TypeError('official pair result is not a Boolean')
            pair_report.update(status='RECORDED', equivalence_boolean=answer,
                               solver_verdict='unsat' if answer else 'sat',
                               matches_registered_emitted_contract_prediction=(answer is True),
                               prediction_scope='Prediction is equivalence under emitted reversed IC; completion status is separate from prediction agreement.')
            if not answer:
                pair_report['database'] = common.decode(pair_env, pair_env.solver.model(), z3)
        except Exception as exc:
            pair_report.update(status='OFFICIAL_PAIR_ERROR_OR_UNKNOWN', error_type=type(exc).__name__,
                               reason=str(exc), reason_unknown=pair_env.solver.reason_unknown())
        pair_report['solver_assertions_sexprs'] = [f.sexpr() for f in pair_env.solver.assertions()]
        checkpoint('ORIGINAL_PAIR_RETURNED')
        pair_env.__exit__(None, None, None)
        pair_env = None
        report['registered_files_unchanged_after_run'] = all(sha(p) == h for p, h in manifest['files'].items())
        report['summary'] = {'cell_denominator': 24, 'cells_recorded': sum(c['status'].startswith('RECORDED_') for c in report['cells']),
            'agreement_cells': sum(c['status'] == 'RECORDED_AGREEMENT' for c in report['cells']),
            'disagreement_cells': sum(c['status'] == 'RECORDED_DISAGREEMENT' for c in report['cells']),
            'null_is_not_true': all(c['original_truth']['satisfies_strict_contract'] is False for c in report['cells'] if c['value'] is None and 'original_truth' in c)}
        complete = (report['summary']['cells_recorded'] == 24 and len(report['sqlite_controls']) == 3
                    and all(c['matches_pre_registered_relations'] for c in report['sqlite_controls'])
                    and pair_report['status'] == 'RECORDED' and report['registered_files_unchanged_after_run'])
        report['status'] = 'COMPLETE_DIAGNOSTIC' if complete else 'PARTIAL_DIAGNOSTIC_WITH_FAILURES'
        checkpoint('FINAL_' + report['status'])
        code = 0 if complete else 2
    except BaseException as exc:
        report.update(status='BLOCKED_OR_ERROR', error_type=type(exc).__name__, reason=str(exc), traceback=traceback.format_exc())
        save(output, report)
        code = 2
    sys.stdout.flush(); sys.stderr.flush()
    os._exit(code)


if __name__ == '__main__':
    main()
