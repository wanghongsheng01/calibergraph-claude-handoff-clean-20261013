"""v3 raw-frontend-guard ALL scan of the same exposed DEV; no solving.

Separate from retained v2 MYSQL/ALL runs; no prior eligibility is reused.
This does not create an independent test.

Only the parent runs this program. Use a fresh -B -I -S child, and supervise the
whole process externally for 60 s wall / 1 GiB RSS. The child also applies CPU,
wall and sampled-RSS limits. Normal Environment initialization is intentional;
it constructs a Solver object but never submits or checks a solver problem.
"""
import time
START = time.monotonic()
import os
import signal
import resource

EMERGENCY_FD = 2


def terminate_for_limit(signum, frame):
    message = (b'{"status":"PROCESS_RESOURCE_STOP","reason":"WALL_60_SECONDS",'
               b'"last_attempt_effect":"UNKNOWN"}\n' if signum == signal.SIGALRM else
               b'{"status":"PROCESS_RESOURCE_STOP","reason":"CPU_LIMIT",'
               b'"last_attempt_effect":"UNKNOWN"}\n')
    os.write(EMERGENCY_FD, message)
    os._exit(124)


signal.signal(signal.SIGALRM, terminate_for_limit)
signal.signal(signal.SIGXCPU, terminate_for_limit)
signal.pthread_sigmask(signal.SIG_UNBLOCK, {signal.SIGALRM, signal.SIGXCPU})
signal.setitimer(signal.ITIMER_REAL, max(0.001, 60 - (time.monotonic() - START)))
resource.setrlimit(resource.RLIMIT_CPU, (44, 45))
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))

import argparse
import builtins
from collections import Counter
import ctypes
from dataclasses import asdict, is_dataclass
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
import threading
import traceback

HERE = Path(__file__).resolve().parent
TODAY = HERE.parent
SOURCE = TODAY / 'sources' / 'verieql_v1'
RUNTIME = TODAY / 'runtime_v3'
RSS_LIMIT = 1024 * 1024 * 1024
KERNEL_SHA = 'defa1812ec36c91a23d428f8d71d2070f808eddeb5f473748d3e7ac09fdfe5f3'
RUNTIME_LOCK_SHA = '505e59253be72e73edf236efe647d84cfcebffe15980517072ae20230bdc38d7'
INPUTS = (
    ('calcite', 'benchmarks/calcite/calcite2.jsonlines', 397,
     '5fc6e0740134220856e93743147038cacaf22cb9d9823e7d6b8da2b461939ac4'),
    ('literature', 'benchmarks/literature/literature-rewrite.jsonlines', 64,
     '4c5e2661797177fd865a3f57c887376cb01bcbeec57ec77a032124e04c77f42f'),
)


class ResourceStop(RuntimeError):
    pass


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(262144), b''):
            digest.update(block)
    return digest.hexdigest()


def usage():
    used = resource.getrusage(resource.RUSAGE_SELF)
    return {'wall_seconds_before_write': time.monotonic() - START,
            'cpu_seconds': used.ru_utime + used.ru_stime,
            'peak_rss_bytes_darwin': used.ru_maxrss,
            'python_threads': [{'name': t.name, 'daemon': t.daemon, 'alive': t.is_alive()}
                               for t in threading.enumerate()]}


def budget():
    used = usage()
    if used['wall_seconds_before_write'] >= 57:
        raise ResourceStop('WALL_SOFT_57_SECONDS_RESERVE_3_SECONDS_FOR_FINAL_REPORT')
    if used['cpu_seconds'] >= 43:
        raise ResourceStop('CPU_SOFT_43_SECONDS_RESERVE_FOR_FINAL_REPORT')
    if used['peak_rss_bytes_darwin'] >= RSS_LIMIT:
        raise ResourceStop('RSS_SOFT_1_GIB')


def save(path, value):
    temporary = path.with_suffix(path.suffix + '.tmp')
    with temporary.open('w', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, allow_nan=False, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def event(stream, value):
    stream.write(json.dumps(value, ensure_ascii=False, allow_nan=False) + '\n')
    stream.flush()
    os.fsync(stream.fileno())


def serialize_ast(value):
    """Record real parser objects without feeding a transformed AST to recognize."""
    if type(value) is float and not math.isfinite(value):
        return {'__type__': 'nonfinite_float', 'value': repr(value)}
    if value is None or type(value) in (str, bool, int, float):
        return value
    if type(value) is dict:
        if not all(type(k) is str for k in value):
            return {'__type__': 'dict_with_non_string_keys',
                    'items': [[serialize_ast(k), serialize_ast(v)] for k, v in value.items()]}
        return {k: serialize_ast(v) for k, v in value.items()}
    if type(value) is list:
        return [serialize_ast(v) for v in value]
    if type(value) is tuple:
        return {'__type__': 'tuple', 'items': [serialize_ast(v) for v in value]}
    if type(value).__module__ == 'utils' and type(value).__name__ == 'ValuesTable':
        return {'__type__': 'utils.ValuesTable', 'fields': serialize_ast(vars(value))}
    raise TypeError('unrecorded parser AST type: ' + type(value).__module__ + '.' + type(value).__name__)


def read_all_inputs():
    rows, inputs = [], []
    for dataset, relative, expected_count, expected_sha in INPUTS:
        path = SOURCE / relative
        if path.is_symlink() or sha(path) != expected_sha:
            raise ValueError('frozen public DEV input changed: ' + relative)
        raw = path.read_bytes()
        lines = raw.splitlines(keepends=True)
        if len(lines) != expected_count:
            raise ValueError('physical line denominator changed: ' + relative)
        inputs.append({'dataset': dataset, 'path': str(path), 'sha256': expected_sha,
                       'physical_lines': expected_count})
        for line_number, line in enumerate(lines, 1):
            record = {'id': dataset + ':' + str(line_number), 'dataset': dataset,
                      'line_number_1based': line_number,
                      'source_line_sha256': hashlib.sha256(line).hexdigest(),
                      'source_line_text': line.decode('utf-8'),
                      'status': 'NOT_RUN', 'pair_both_eligible': None, 'queries': []}
            try:
                source = json.loads(line)
                record['source_record'] = source
                if not isinstance(source, dict) or not isinstance(source.get('pair'), list) or len(source['pair']) != 2:
                    raise ValueError('expected exactly two queries in original pair')
                for query_index, sql in enumerate(source['pair']):
                    record['queries'].append({'query_index': query_index, 'original_sql': sql,
                                              'status': 'NOT_RUN', 'ast': None, 'eligible': None,
                                              'reason': 'NOT_ATTEMPTED'})
            except Exception as exc:
                record.update(status='INPUT_ERROR', error_type=type(exc).__name__, reason=str(exc))
            rows.append(record)
    if len(rows) != 461:
        raise ValueError('full row denominator changed')
    return inputs, rows


def verify_runtime(lock_path, expected_sha):
    if expected_sha != RUNTIME_LOCK_SHA or lock_path.resolve() != RUNTIME / 'runtime_paths.json' or sha(lock_path) != expected_sha:
        raise ValueError('runtime lock location/hash mismatch')
    lock = json.loads(lock_path.read_text())
    if lock.get('schema_version') != 1 or lock.get('status') != 'STATIC_REVIEWED_READY_FOR_LOCAL_RUN':
        raise ValueError('runtime lock is not READY; pending review is not accepted')
    if lock['source_root'] != str(SOURCE) or lock['kernel_path'] != str(RUNTIME / 'aggregate_kernel.py'):
        raise ValueError('wrong official source or adapter path')
    if lock['expected_native_version'] != [4, 12, 0, 0] or not lock['files']:
        raise ValueError('wrong native lock or missing file inventory')
    for raw, expected in lock['files'].items():
        budget()
        path = Path(raw)
        if not path.is_absolute() or path != path.resolve() or not path.is_file() or sha(path) != expected:
            raise ValueError('runtime file missing/changed/symlinked: ' + raw)
    for root in [lock['source_root'], lock['binding_root'], lock['support_root'], *lock['dependency_roots']]:
        path = Path(root)
        actual = {str(p) for p in path.rglob('*') if p.is_file()}
        expected = {p for p in lock['files'] if Path(p).is_relative_to(path)}
        if actual != expected or any(p.is_symlink() for p in path.rglob('*')):
            raise ValueError('runtime root inventory mismatch: ' + root)
    if lock['native_path'] not in lock['files'] or lock['files'].get(lock['kernel_path']) != KERNEL_SHA:
        raise ValueError('native omitted or wrong reviewed adapter kernel')
    return lock


def summarize(rows):
    counts = Counter(q['status'] for row in rows for q in row['queries'])
    reasons = Counter(q['reason'] for row in rows for q in row['queries'])
    return {'row_denominator': 461, 'query_slot_denominator': 922,
            'recorded_query_slots': sum(len(r['queries']) for r in rows),
            'row_status_counts': dict(Counter(r['status'] for r in rows)),
            'query_status_counts': dict(counts), 'query_reason_counts': dict(reasons),
            'eligible_queries': sum(q['eligible'] is True for r in rows for q in r['queries']),
            'both_eligible_pairs': sum(r['pair_both_eligible'] is True for r in rows),
            'pair_unknown': sum(r['pair_both_eligible'] is None for r in rows),
            'by_dataset': {dataset: {
                'row_denominator': expected_count,
                'query_slot_denominator': 2 * expected_count,
                'eligible_queries': sum(q['eligible'] is True for r in rows if r['dataset'] == dataset for q in r['queries']),
                'both_eligible_pairs': sum(r['pair_both_eligible'] is True for r in rows if r['dataset'] == dataset),
            } for dataset, _, expected_count, _ in INPUTS}}


def main():
    global EMERGENCY_FD
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-lock', type=Path, default=RUNTIME / 'runtime_paths.json')
    parser.add_argument('--expected-lock-sha256', required=True)
    parser.add_argument('--out-dir', type=Path, default=HERE / 'runs' / 'full_scan_v3_all_01')
    args = parser.parse_args()
    if sys.platform != 'darwin' or not (sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode):
        raise ValueError('Darwin -B -I -S is required')
    out = args.out_dir.resolve()
    if out.exists() or not out.is_relative_to(HERE) or any(p.is_symlink() for p in [args.out_dir, *args.out_dir.parents]):
        raise ValueError('new nonsymlink result directory under public_dev required')
    out.mkdir(parents=True)
    EMERGENCY_FD = os.open(out / 'emergency.jsonl', os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_APPEND, 0o600)
    inputs, rows = read_all_inputs()
    report = {'status': 'INITIAL_NOT_RUN', 'data_role': 'EXISTING_EXPOSED_PUBLIC_DEV_NOT_NEW_TEST',
              'pid': os.getpid(), 'program_sha256': sha(Path(__file__)),
              'runtime_lock_sha256': args.expected_lock_sha256, 'kernel_sha256': KERNEL_SHA,
              'inputs': inputs, 'full_row_denominator': 461, 'full_query_slot_denominator': 922,
              'rows': rows, 'dialect': 'ALL', 'identifier_encoding': 'verieql_double_underscore',
              'dialect_sensitivity': {'status': 'V3_FRONTEND_GUARDED_ALL_DEV_RESCAN_NOT_NEW_TEST',
                  'comparison': 'Existing v2 MYSQL/ALL results and failures remain unchanged; same 461 rows/922 slots. Prior v2 eligibility is not v3 coverage.',
                  'basis': 'Official parallel/cli_within_bound.py:37 omits dialect; Environment.__init__:90 defaults DIALECT.ALL.',
                  'prior_mysql_script_sha256': 'b68dd5d5dfe45166fe9aae07c773f26b7c20ed0f2eb96bdd532f735b2dcca076',
                  'prior_all_script_sha256': '27e285f8e9fc36fcc558336d91aea2fc46a093ae1d873064449ab2a5032039ee'},
              'frontend_guard': {'version': 3, 'before_parser': True, 'raw_schema_and_sql_unchanged': True,
                  'frontend_unsupported_is_separate': True, 'fallback_permitted': False,
                  'conservative_gate': 'Raw identifier guard may reject special characters even inside SQL strings/comments; refusal is retained in the full denominator.'},
              'schema_and_constraints': 'Retained exactly in source_record; no database creation or constraint assertion; recognize receives original schema.',
              'scope': 'Official Environment normal initialization, official parse_sql_query, reviewed fragment recognizer only. Eligibility does not prove semantic equivalence or contract admissibility.',
              'solver_object': 'Created by normal Environment initializer; no add/check/solve/encode/analyze calls.',
              'limits': {'cpu_soft_hard_seconds': [44, 45], 'wall_hard_seconds': 60,
                         'wall_soft_seconds': 57, 'rss_soft_bytes': RSS_LIMIT,
                         'parent_supervision_required': True},
              'native_load': 'NOT_ATTEMPTED', 'environment_import': 'NOT_ATTEMPTED',
              'environment_initialization': 'NOT_ATTEMPTED', 'solving_performed': False,
              'scientific_claims': {'heldout_generalization': False, 'equivalence_accuracy': False,
                                    'runtime_advantage': False, 'novelty_established': False},
              'resource_last_checkpoint': usage()}
    save(out / 'initial_not_run.json', report)
    save(out / 'scan_report.json', report)
    with (out / 'query_events.jsonl').open('x', encoding='utf-8') as events:
        try:
            lock = verify_runtime(args.runtime_lock, args.expected_lock_sha256)
            report['input_hash_gate'] = 'PASS'
            report['native_load'] = 'ATTEMPTED_EFFECT_UNKNOWN'
            save(out / 'scan_report.json', report)
            native = Path(lock['native_path'])
            library = ctypes.CDLL(str(native))
            report['native_load'] = 'LOADED'
            builtins.Z3_LIB_DIRS = [str(native.parent)]
            sys.path[:0] = [lock['binding_root'], lock['support_root'], *lock['dependency_roots'], lock['source_root']]
            report['environment_import'] = 'ATTEMPTED_EFFECT_UNKNOWN'
            save(out / 'scan_report.json', report)
            import z3
            from z3 import z3core
            defaults = z3core.Z3_get_version.__defaults__
            if len(defaults) != 1:
                raise ValueError('unexpected native version wrapper')
            bound = ctypes.cast(defaults[0].f, ctypes.c_void_p).value
            pinned = ctypes.cast(library.Z3_get_version, ctypes.c_void_p).value
            if not bound or bound != pinned or list(z3.get_version()) != lock['expected_native_version']:
                raise ValueError('binding/native identity or version mismatch')
            if not Path(z3.__file__).resolve().is_relative_to(Path(lock['binding_root'])):
                raise ValueError('wrong binding source')
            from environment import Environment
            from constants import DIALECT
            if Path(sys.modules['environment'].__file__).resolve() != SOURCE / 'environment.py':
                raise ValueError('wrong Environment source')
            spec = importlib.util.spec_from_file_location('caliber_public_dev_v3_kernel', lock['kernel_path'])
            kernel = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = kernel
            spec.loader.exec_module(kernel)
            report['environment_import'] = 'IMPORTED'
            report['native_identity'] = {'version': list(z3.get_version()), 'path': str(native),
                                         'sha256': sha(native), 'binding_pointer': bound, 'pinned_pointer': pinned}
            report['loaded_module_paths'] = {name: getattr(module, '__file__', None)
                for name, module in list(sys.modules.items())
                if name.split('.')[0] in {'environment','constants','mo_sql_parsing','mo_parsing','mo_dots','mo_imports','mo_future','ordered_set','lark','ujson','yaml','pkg_resources','z3'}}
            z3.set_param('parallel.enable', False)
            z3.set_param('memory_max_size', 768)
            report['environment_initialization'] = 'ATTEMPTED_EFFECT_UNKNOWN'
            save(out / 'scan_report.json', report)
            budget()
            with Environment(timer=False, generate_code=False, show_counterexample=False, dialect=DIALECT.ALL) as env:
                report['environment_initialization'] = 'NORMAL_INITIALIZER_COMPLETE'
                report['status'] = 'SCANNING_ALL_ROWS_IN_SOURCE_ORDER'
                save(out / 'scan_report.json', report)
                for row in rows:
                    budget()
                    if row['status'] == 'INPUT_ERROR':
                        continue
                    source = row['source_record']
                    for query in row['queries']:
                        budget()
                        query.update(status='ATTEMPTED_EFFECT_UNKNOWN', reason='RAW_FRONTEND_GUARD_IN_PROGRESS',
                                     parser_called=False, fallback_permitted=False)
                        event(events, {'event': 'QUERY_ATTEMPT', 'row_id': row['id'], 'query_index': query['query_index']})
                        try:
                            if not isinstance(query['original_sql'], str):
                                raise TypeError('original query is not a string')
                            kernel.ensure_raw_identifiers(source['schema'], query['original_sql'])
                            query.update(frontend_guard='PASS', parser_called=True, reason='PARSER_CALL_IN_PROGRESS')
                            actual_ast = env.parse_sql_query(query['original_sql'])
                            query['ast'] = serialize_ast(actual_ast)
                            budget()
                        except kernel.FrontendUnsupported as exc:
                            query.update(status='FRONTEND_UNSUPPORTED', eligible=False,
                                         reason=str(exc), frontend_guard='REFUSED', fallback_permitted=False)
                        except ResourceStop:
                            raise
                        except Exception as exc:
                            query.update(status='PARSE_OR_AST_RECORD_ERROR', eligible=None,
                                         reason=type(exc).__name__ + ': ' + str(exc), traceback=traceback.format_exc())
                        else:
                            try:
                                plan = kernel.recognize(actual_ast, source['schema'], identifier_encoding='verieql_double_underscore',
                                                        original_sql=query['original_sql'])
                                if not is_dataclass(plan):
                                    raise TypeError('unexpected recognizer plan type')
                                query.update(status='ELIGIBLE', eligible=True, reason='recognized_fragment', plan=asdict(plan))
                            except kernel.FrontendUnsupported as exc:
                                query.update(status='FRONTEND_UNSUPPORTED', eligible=False, reason=str(exc),
                                             frontend_guard='REFUSED_IN_RECOGNIZER', fallback_permitted=False)
                            except kernel.Ineligible as exc:
                                query.update(status='INELIGIBLE', eligible=False, reason=str(exc))
                            except Exception as exc:
                                query.update(status='RECOGNIZER_ERROR', eligible=None,
                                             reason=type(exc).__name__ + ': ' + str(exc), traceback=traceback.format_exc())
                        event(events, {'event': 'QUERY_RESULT', 'row_id': row['id'], 'result': query})
                    known = [q['eligible'] for q in row['queries']]
                    row['pair_both_eligible'] = False if False in known else (True if all(x is True for x in known) else None)
                    row['status'] = 'SCANNED' if all(type(x) is bool for x in known) else 'SCANNED_WITH_ERRORS'
                    report['resource_last_checkpoint'] = usage()
                    report['summary'] = summarize(rows)
                    # Detailed per-query durable events avoid rewriting every accumulated AST.
                    save(out / 'progress.json', {'last_row': row['id'], 'summary': report['summary'],
                                                 'resource': report['resource_last_checkpoint']})
            report['environment_cleanup'] = 'CONTEXT_EXIT_COMPLETE'
            report['status'] = 'COMPLETE_FULL_DEV_SCAN_WITH_ERRORS' if any(r['status'] != 'SCANNED' for r in rows) else 'COMPLETE_FULL_DEV_SCAN'
        except ResourceStop as exc:
            report.update(status='STOPPED_RESOURCE_LIMIT_REMAINDER_NOT_RUN', stop_reason=str(exc))
        except Exception as exc:
            report.update(status='FAILED_REMAINDER_NOT_RUN', error_type=type(exc).__name__,
                          reason=str(exc), traceback=traceback.format_exc())
        report['summary'] = summarize(rows)
        report['resource_last_checkpoint'] = usage()
        report['query_events_sha256'] = sha(out / 'query_events.jsonl')
        report['runtime_lock_unchanged_after_scan'] = sha(args.runtime_lock) == args.expected_lock_sha256
        report['kernel_unchanged_after_scan'] = sha(RUNTIME / 'aggregate_kernel.py') == KERNEL_SHA
        report['inputs_unchanged_after_scan'] = all(sha(SOURCE / rel) == expected for _, rel, _, expected in INPUTS)
        if not all(report[k] for k in ('runtime_lock_unchanged_after_scan','kernel_unchanged_after_scan','inputs_unchanged_after_scan')):
            report['status'] = 'INVALIDATED_INPUT_CHANGED'
        save(out / 'scan_report.json', report)
        print(json.dumps({'status': report['status'], 'report': str(out / 'scan_report.json'),
                          'summary': report['summary']}), flush=True)
    # Interpreter shutdown can wait for upstream mo_imports monitor. The 60s
    # alarm remains armed and the parent's process/RSS supervisor remains owner.
    return 0 if report['status'] in ('COMPLETE_FULL_DEV_SCAN','COMPLETE_FULL_DEV_SCAN_WITH_ERRORS') else 2


if __name__ == '__main__':
    sys.exit(main())
