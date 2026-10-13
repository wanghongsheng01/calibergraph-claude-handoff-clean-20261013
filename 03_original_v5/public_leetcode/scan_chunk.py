"""Fixed-source external applicability chunks, ALL dialect, v3 raw frontend guard.

No solving, human-gold accuracy, performance, or independent-holdout claim.

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
SOURCE_SHA = 'b97fc1293701682a25a2f6345f3630b3482ce49912463a7f4b76ab52665a13c9'
MANIFEST_SHA = '041d6c0bf43dad8270c099f10bcbcf61cfc4ee5a96f13170ff141e35c5ce45a0'
SOURCE_FILE = HERE / 'leetcode.jsonlines'
GLOBAL_MANIFEST = HERE / 'GLOBAL_MANIFEST.json'
FULL_ROWS = 23994
FULL_QUERIES = 47988
TERMINAL = {'ELIGIBLE', 'INELIGIBLE', 'FRONTEND_UNSUPPORTED',
            'PARSE_OR_AST_RECORD_ERROR', 'RECOGNIZER_ERROR', 'INPUT_ERROR'}



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


def read_chunk(chunk_index):
    if sha(GLOBAL_MANIFEST) != MANIFEST_SHA or sha(SOURCE_FILE) != SOURCE_SHA:
        raise ValueError('complete source/global manifest hash changed')
    manifest = json.loads(GLOBAL_MANIFEST.read_text())
    if manifest['row_denominator'] != FULL_ROWS or manifest['query_slot_denominator'] != FULL_QUERIES:
        raise ValueError('full source denominator changed')
    if not 0 <= chunk_index < len(manifest['chunks']):
        raise ValueError('chunk index must be 0..23')
    chunk = manifest['chunks'][chunk_index]
    records = manifest['rows'][chunk['start_line_1based']-1:chunk['end_line_1based']]
    rows = []
    with SOURCE_FILE.open('rb') as stream:
        for descriptor in records:
            stream.seek(descriptor['byte_offset'])
            raw = stream.read(descriptor['byte_length'])
            if hashlib.sha256(raw).hexdigest() != descriptor['line_sha256']:
                raise ValueError('selected original source line changed')
            source = json.loads(raw)
            row = {'id': 'leetcode:' + str(descriptor['line_number_1based']),
                   'dataset': 'leetcode', 'line_number_1based': descriptor['line_number_1based'],
                   'source_line_sha256': descriptor['line_sha256'],
                   'source_line_text': raw.decode('utf-8'), 'source_record': source,
                   'status': 'NOT_RUN', 'pair_both_eligible': None, 'queries': []}
            for query_index, sql in enumerate(source['pair']):
                if hashlib.sha256(sql.encode()).hexdigest() != descriptor['queries'][query_index]['sql_sha256']:
                    raise ValueError('query hash changed')
                row['queries'].append({'query_index': query_index, 'original_sql': sql,
                    'status': 'NOT_RUN', 'ast': None, 'eligible': None, 'reason': 'NOT_ATTEMPTED'})
            rows.append(row)
    return manifest, chunk, rows


def restore_completed(chunk_root, rows, runtime_sha):
    by_id = {r['id']: r for r in rows}
    restored = []
    partial_tail_events = []
    for attempt in sorted(chunk_root.glob('attempt_*')) if chunk_root.exists() else []:
        initial_path = attempt / 'initial_not_run.json'
        events_path = attempt / 'query_events.jsonl'
        if not initial_path.exists() or not events_path.exists():
            continue
        prior = json.loads(initial_path.read_text())
        for name, expected in [('source_sha256', SOURCE_SHA), ('global_manifest_sha256', MANIFEST_SHA),
                               ('kernel_sha256', KERNEL_SHA), ('runtime_lock_sha256', runtime_sha),
                               ('program_sha256', sha(Path(__file__)))]:
            if prior.get(name) != expected:
                raise ValueError('resume protocol/source mismatch: ' + str(attempt) + ' ' + name)
        lines = events_path.read_bytes().splitlines(keepends=True)
        for number, raw in enumerate(lines):
            try:
                entry = json.loads(raw)
            except Exception:
                if number == len(lines)-1 and not raw.endswith(b'\n'):
                    partial_tail_events.append({'path': str(events_path), 'line': number+1})
                    continue
                raise
            if entry.get('event') != 'QUERY_RESULT':
                continue
            result = entry['result'];row = by_id[entry['row_id']];index = result['query_index']
            current = row['queries'][index]
            if current['original_sql'] != result['original_sql'] or result['status'] not in TERMINAL:
                raise ValueError('invalid completed event identity/status')
            if current['status'] in TERMINAL and current != result:
                raise ValueError('conflicting prior completed query results')
            row['queries'][index] = result
        restored.append({'attempt': str(attempt), 'events_sha256': sha(events_path)})
    return {'prior_attempts': restored, 'ignored_incomplete_trailing_event': partial_tail_events,
            'completed_queries_not_rerun': sum(q['status'] in TERMINAL for r in rows for q in r['queries'])}


def update_global_progress(report):
    path = HERE / 'GLOBAL_PROGRESS.json'
    if path.exists():
        progress = json.loads(path.read_text())
        if progress['source_sha256'] != SOURCE_SHA or progress['global_manifest_sha256'] != MANIFEST_SHA:
            raise ValueError('global progress source mismatch')
    else:
        manifest = json.loads(GLOBAL_MANIFEST.read_text())
        progress = {'status': 'PARTIAL_EXTERNAL_APPLICABILITY_SCAN', 'source_sha256': SOURCE_SHA,
            'global_manifest_sha256': MANIFEST_SHA, 'row_denominator': FULL_ROWS,
            'query_slot_denominator': FULL_QUERIES, 'chunks': {},
            'rows': [{'line_number_1based': row['line_number_1based'], 'status': 'NOT_RUN',
                      'queries': [{'query_index': j, 'status': 'NOT_RUN'} for j in (0,1)]}
                     for row in manifest['rows']]}
    for row in report['rows']:
        progress['rows'][row['line_number_1based']-1] = {'line_number_1based': row['line_number_1based'],
            'status': row['status'], 'pair_both_eligible': row['pair_both_eligible'],
            'queries': [{k:q.get(k) for k in ('query_index','status','eligible','reason')} for q in row['queries']]}
    progress['chunks'][str(report['chunk']['chunk_index'])] = {
        'status': report['status'], 'report': report['output_report'], 'summary': report['summary'],
        'kernel_sha256': KERNEL_SHA, 'runtime_lock_sha256': report['runtime_lock_sha256']}
    progress['query_status_counts'] = dict(Counter(q['status'] for r in progress['rows'] for q in r['queries']))
    progress['completed_query_slots'] = sum(q['status'] in TERMINAL for r in progress['rows'] for q in r['queries'])
    save(path, progress)


def verify_runtime(lock_path, expected_sha):
    if lock_path.resolve() != RUNTIME / 'runtime_paths.json' or sha(lock_path) != expected_sha:
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
    queries = [q for row in rows for q in row['queries']]
    return {'global_row_denominator': FULL_ROWS, 'global_query_slot_denominator': FULL_QUERIES,
            'chunk_row_denominator': len(rows), 'chunk_query_slot_denominator': 2*len(rows),
            'query_status_counts': dict(Counter(q['status'] for q in queries)),
            'query_reason_counts': dict(Counter(q['reason'] for q in queries)),
            'eligible_queries': sum(q['eligible'] is True for q in queries),
            'both_eligible_pairs': sum(r['pair_both_eligible'] is True for r in rows),
            'eligible_multitable_queries': sum(q.get('eligible') is True and len(q.get('plan',{}).get('tables',{}))>1 for q in queries),
            'completed_query_slots': sum(q['status'] in TERMINAL for q in queries),
            'uncompleted_query_slots': sum(q['status'] not in TERMINAL for q in queries),
            'pair_unknown': sum(r['pair_both_eligible'] is None for r in rows)}


def main():
    global EMERGENCY_FD
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-lock', type=Path, default=RUNTIME / 'runtime_paths.json')
    parser.add_argument('--expected-lock-sha256', required=True)
    parser.add_argument('--chunk-index', type=int, required=True)
    parser.add_argument('--out-dir', type=Path, required=True)
    args = parser.parse_args()
    if sys.platform != 'darwin' or not (sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode):
        raise ValueError('Darwin -B -I -S is required')
    out = args.out_dir.resolve()
    chunk_root = HERE / 'runs' / ('chunk_%03d' % args.chunk_index)
    if out.exists() or out.parent != chunk_root or not out.name.startswith('attempt_') or any(p.is_symlink() for p in [args.out_dir, *args.out_dir.parents]):
        raise ValueError('new output must be public_leetcode/runs/chunk_NNN/attempt_NAME')
    out.mkdir(parents=True)
    EMERGENCY_FD = os.open(out / 'emergency.jsonl', os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_APPEND, 0o600)
    manifest, chunk, rows = read_chunk(args.chunk_index)
    if args.chunk_index:
        progress_path = HERE / 'GLOBAL_PROGRESS.json'
        if not progress_path.exists():
            raise ValueError('scan chunk0 first; no skipping original source order')
        progress = json.loads(progress_path.read_text())
        if progress.get('source_sha256') != SOURCE_SHA or progress.get('global_manifest_sha256') != MANIFEST_SHA:
            raise ValueError('previous progress belongs to another frozen source')
        for previous in range(args.chunk_index):
            done = progress['chunks'].get(str(previous), {}).get('summary', {})
            if done.get('completed_query_slots') != manifest['chunks'][previous]['query_slots']:
                raise ValueError('resume incomplete earlier chunk before advancing')
    resume = restore_completed(chunk_root, rows, args.expected_lock_sha256)
    report = {'status': 'INITIAL_CHUNK_STATE_BEFORE_NEW_TARGET_IMPORT', 'data_role': 'EXTERNAL_APPLICABILITY_NOT_INDEPENDENT_HOLDOUT_HUMAN_GOLD_OR_PERFORMANCE',
              'pid': os.getpid(), 'program_sha256': sha(Path(__file__)),
              'runtime_lock_sha256': args.expected_lock_sha256, 'kernel_sha256': KERNEL_SHA,
              'source_sha256': SOURCE_SHA, 'global_manifest_sha256': MANIFEST_SHA,
              'full_row_denominator': FULL_ROWS, 'full_query_slot_denominator': FULL_QUERIES,
              'chunk': chunk, 'resume': resume, 'output_report': str(out / 'scan_report.json'),
              'exposure_disclosure': manifest['exposure_disclosure'],
              'rows': rows, 'dialect': 'ALL', 'identifier_encoding': 'verieql_double_underscore',
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
            spec = importlib.util.spec_from_file_location('caliber_public_dev_kernel', lock['kernel_path'])
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
                report['status'] = 'SCANNING_CHUNK_ORIGINAL_ORDER_WITH_COMPLETED_QUERY_RESUME'
                save(out / 'scan_report.json', report)
                for row in rows:
                    budget()
                    if row['status'] == 'INPUT_ERROR':
                        continue
                    source = row['source_record']
                    for query in row['queries']:
                        if query['status'] in TERMINAL:
                            continue
                        budget()
                        query.update(status='ATTEMPTED_EFFECT_UNKNOWN', reason='RAW_GUARD_THEN_PARSER_IN_PROGRESS',
                                     parser_called=False, raw_frontend_guard='ATTEMPTED_EFFECT_UNKNOWN')
                        event(events, {'event': 'QUERY_ATTEMPT', 'row_id': row['id'], 'query_index': query['query_index']})
                        try:
                            if not isinstance(query['original_sql'], str):
                                raise TypeError('original query is not a string')
                            kernel.ensure_raw_identifiers(source['schema'], query['original_sql'])
                            query.update(raw_frontend_guard='PASS', parser_called=True)
                            actual_ast = env.parse_sql_query(query['original_sql'])
                            query['ast'] = serialize_ast(actual_ast)
                            budget()
                        except ResourceStop:
                            raise
                        except kernel.FrontendUnsupported as exc:
                            query.update(status='FRONTEND_UNSUPPORTED', eligible=False, reason=str(exc),
                                         fallback_permitted=False, parser_called=False,
                                         raw_frontend_guard='FRONTEND_UNSUPPORTED')
                        except Exception as exc:
                            query.update(status='PARSE_OR_AST_RECORD_ERROR', eligible=None,
                                         reason=type(exc).__name__ + ': ' + str(exc), traceback=traceback.format_exc())
                        else:
                            try:
                                plan = kernel.recognize(actual_ast, source['schema'], identifier_encoding='verieql_double_underscore', original_sql=query['original_sql'])
                                if not is_dataclass(plan):
                                    raise TypeError('unexpected recognizer plan type')
                                query.update(status='ELIGIBLE', eligible=True, reason='recognized_fragment', plan=asdict(plan))
                            except kernel.FrontendUnsupported as exc:
                                query.update(status='FRONTEND_UNSUPPORTED', eligible=False, reason=str(exc), fallback_permitted=False)
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
            report['status'] = 'COMPLETE_CHUNK_SCAN_WITH_ERRORS' if any(r['status'] != 'SCANNED' for r in rows) else 'COMPLETE_CHUNK_SCAN'
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
        report['inputs_unchanged_after_scan'] = sha(SOURCE_FILE) == SOURCE_SHA and sha(GLOBAL_MANIFEST) == MANIFEST_SHA
        if not all(report[k] for k in ('runtime_lock_unchanged_after_scan','kernel_unchanged_after_scan','inputs_unchanged_after_scan')):
            report['status'] = 'INVALIDATED_INPUT_CHANGED'
        save(out / 'scan_report.json', report)
        update_global_progress(report)
        print(json.dumps({'status': report['status'], 'report': str(out / 'scan_report.json'),
                          'summary': report['summary']}), flush=True)
    # Interpreter shutdown can wait for upstream mo_imports monitor. The 60s
    # alarm remains armed and the parent's process/RSS supervisor remains owner.
    return 0 if report['status'] in ('COMPLETE_CHUNK_SCAN','COMPLETE_CHUNK_SCAN_WITH_ERRORS') else 2


if __name__ == '__main__':
    sys.exit(main())
