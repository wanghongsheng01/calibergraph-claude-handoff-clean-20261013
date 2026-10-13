"""Prepared probe ordering diagnostic. Importing performs no work.

No CLI auto-run. Parent must review/freeze and supply pinned smoke ASTs, a durable
event sink, and an external one-worker RSS/CPU/wall guard before calling APIs.
"""
from collections import Counter
from pathlib import Path
import hashlib
import importlib.util
import json
import os
import resource
import sqlite3
import signal
import sys
import time

KINDS = {'null_all': 0, 'null_single': 1, 'duplicate_nonkey': 2, 'base': 3}
EXCLUDED = {'dev_01', 'dev_03'}

def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()

def objsha(value):
    return hashlib.sha256(canonical(value)).hexdigest()

def filesha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def cpu():
    r = resource.getrusage(resource.RUSAGE_SELF)
    return r.ru_utime + r.ru_stime

class ProbeStop(RuntimeError):
    pass

class QueryStop(RuntimeError):
    pass

class DurableEvents:
    """One exclusive-create shared stream. START without END means unknown effect."""
    def __init__(self, path):
        self.stream = Path(path).open('x')
        self.seq = 0
        self.wall_seconds = self.cpu_seconds = 0.0

    def emit(self, event, payload):
        w, c = time.monotonic(), cpu()
        self.seq += 1
        self.stream.write(json.dumps({'seq': self.seq, 'event': event, 'record': payload}, ensure_ascii=False, allow_nan=False) + '\n')
        self.stream.flush()
        os.fsync(self.stream.fileno())
        self.wall_seconds += time.monotonic() - w
        self.cpu_seconds += cpu() - c

    def close(self):
        self.stream.flush()
        os.fsync(self.stream.fileno())
        self.stream.close()

class ProbeBudget:
    def __init__(self, sink, arm, checker, protocol, cpu_seconds=0.5, wall_seconds=0.75, outer_check=None, preprocessing_debit=None):
        self.sink, self.arm, self.checker, self.protocol = sink, arm, checker, protocol
        self.cpu_seconds, self.wall_seconds = float(cpu_seconds), float(wall_seconds)
        self.outer_check = outer_check
        self.preprocessing_debit = preprocessing_debit or {'cpu_seconds': 0.0, 'wall_seconds': 0.0}
        self.start_cpu, self.start_wall = cpu(), time.monotonic()
        self.query_cpu_seconds = 0.1
        self.query_wall_seconds = 0.1
        self.result_row_limit = 1024

    def check(self):
        if self.outer_check is not None:
            self.outer_check()
        if cpu() - self.start_cpu + self.preprocessing_debit['cpu_seconds'] >= self.cpu_seconds:
            raise ProbeStop('ARM_CPU_BUDGET')
        if time.monotonic() - self.start_wall + self.preprocessing_debit['wall_seconds'] >= self.wall_seconds:
            raise ProbeStop('ARM_WALL_BUDGET')
        if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss >= 256 * 1024**2:
            raise ProbeStop('OBSERVED_PEAK_RSS_256_MIB')

    def emit(self, event, payload):
        self.sink.emit(event, {'arm': self.arm, **payload})

def load_inputs(protocol):
    """Shared pure-file preparation; no SQL, target imports, or ordering outputs."""
    startw, startc = time.monotonic(), cpu()
    def read(binding):
        p = Path(binding['path'])
        if filesha(p) != binding['sha256']:
            raise ValueError('PINNED_INPUT_HASH_MISMATCH:' + str(p))
        return p.read_bytes()
    cases = [json.loads(x) for x in read(protocol['development']).splitlines()]
    pool = [json.loads(x) for x in read(protocol['pool']).splitlines()]
    if [c['id'] for c in cases] != protocol['case_ids'] or len(pool) != 32:
        raise ValueError('REGISTERED_DENOMINATOR_MISMATCH')
    if len({r['id'] for r in pool}) != len(pool):
        raise ValueError('DUPLICATE_POOL_ID')
    for case in cases:
        src = case['source_record']
        if [hashlib.sha256(q.encode()).hexdigest() for q in src['pair']] != case['original_sql_sha256']:
            raise ValueError('ORIGINAL_SQL_HASH_MISMATCH')
        for r in (x for x in pool if x['case_id'] == case['id']):
            if (r['schema_sha256'] != objsha(src['schema']) or r['constraint_sha256'] != objsha(src['constraint']) or r['rows_sha256'] != objsha(r['rows'])):
                raise ValueError('POOL_CASE_IDENTITY_MISMATCH')
    binding = protocol['checker']
    read(binding)
    spec = importlib.util.spec_from_file_location('pinned_probe_checker', binding['path'])
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # pure stdlib declarations; never main()
    return cases, pool, module.check_contract, {'wall_seconds': time.monotonic()-startw, 'cpu_seconds': cpu()-startc, 'scope': 'shared file hashing/loading and checker import; charged once as shared, added in full to each standalone arm scenario'}

def load_smoke_asts(report_path, expected_sha256, cases, protocol):
    """Only AST/provenance/cost fields influence ordering; never verdict/outputs."""
    if report_path is None or expected_sha256 is None:
        return {c['id']: {'status': 'AST_FEATURE_UNAVAILABLE', 'reason': 'NO_FROZEN_SMOKE_REPORT_BINDING'} for c in cases}
    p = Path(report_path)
    if not p.is_file() or p.stat().st_size > 8*1024**2 or filesha(p) != expected_sha256:
        raise ValueError('SMOKE_REPORT_MISSING_TOO_LARGE_OR_HASH_MISMATCH')
    report = json.loads(p.read_text())
    if report.get('input', {}).get('sha256') != protocol['development']['sha256']:
        raise ValueError('SMOKE_INPUT_IDENTITY_MISMATCH')
    for report_field, binding_name in [('backend_sha256', 'official_backend'), ('protocol_sha256', 'official_protocol')]:
        if report.get(report_field) != protocol[binding_name]['sha256']:
            raise ValueError('SMOKE_CODE_OR_PROTOCOL_IDENTITY_MISMATCH')
    records = report.get('records', [])
    if len({r.get('id') for r in records}) != len(records):
        raise ValueError('DUPLICATE_SMOKE_RECORD')
    result = {}
    for case in cases:
        rec = next((r for r in records if r.get('id') == case['id']), {})
        src = case['source_record']
        if (rec.get('original_sql_sha256') != case['original_sql_sha256'] or rec.get('schema_sha256') != objsha(src['schema']) or rec.get('constraint_sha256') != objsha(src['constraint'])):
            result[case['id']] = {'status': 'AST_FEATURE_UNAVAILABLE', 'reason': 'ABSENT_OR_UNBOUND_SMOKE_CASE'}
            continue
        asts = rec.get('parsed_asts')
        if not isinstance(asts, list) or len(asts) != 2 or not all(isinstance(a, dict) for a in asts):
            result[case['id']] = {'status': 'AST_FEATURE_UNAVAILABLE', 'reason': 'BOTH_ORIGINAL_ASTS_NOT_RECORDED'}
            continue
        result[case['id']] = {'status': 'AST_AVAILABLE', 'parsed_asts': asts, 'ast_sha256': [objsha(a) for a in asts], 'report_path': str(p), 'report_sha256': expected_sha256,
            'predecessor_parser_stages': [{k: s[k] for k in ('name', 'wall_seconds', 'cpu_seconds') if k in s} for s in rec.get('stages', []) if s.get('name', '').startswith('OFFICIAL_PARSE_QUERY_')],
            'predecessor_runtime_stages': [{k: s[k] for k in ('name', 'wall_seconds', 'cpu_seconds') if k in s} for s in report.get('runtime', {}).get('stages', [])],
            'cost_scope': 'historical smoke predecessor evidence, not a fresh standalone frontend timing; solver outputs/verdicts not used'}
    return result

def ast_features(asts, schema):
    features, count_columns, group_columns = set(), set(), set()
    aliases = {'count': 'count', 'distinct': 'distinct', 'selectdistinct': 'distinct', 'notin': 'notin', 'nin': 'notin', 'leftjoin': 'left', 'leftouterjoin': 'left', 'groupby': 'group', 'having': 'having'}
    def resolve(value):
        # Strictly unique original column references only; no guessed alias binding.
        if not isinstance(value, str):
            return None
        name = value.upper()
        if '.' in name:
            table, col = name.split('.', 1)
            return (table, col) if table in schema and col in schema[table] else None
        hits = [(t, name) for t, cols in schema.items() if name in cols]
        return hits[0] if len(hits) == 1 else None
    def column_values(node, target):
        if isinstance(node, str):
            r = resolve(node)
            if r:
                target.add(r)
        elif isinstance(node, list):
            for v in node:
                column_values(v, target)
        elif isinstance(node, dict):
            for key, value in node.items():
                if key != 'literal':
                    column_values(value, target)
    def walk(node):
        if isinstance(node, dict):
            for key, value in node.items():
                normalized = ''.join(c for c in key.lower() if c.isalnum())
                if normalized in aliases:
                    features.add(aliases[normalized])
                if normalized == 'count':
                    column_values(value, count_columns)
                if normalized == 'groupby':
                    column_values(value, group_columns)
                if key != 'literal':
                    walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)
    walk(asts)
    return {'nodes': sorted(features), 'count_columns': sorted(count_columns), 'group_columns': sorted(group_columns), 'binding_scope': 'exact original table.column or unique unqualified column; unresolved aliases receive no column bonus'}

def build_orders(case, pool, ast_record):
    w, c = time.monotonic(), cpu()
    rows = [r for r in pool if r['case_id'] == case['id']]
    generic = sorted(rows, key=lambda r: (KINDS[r['kind']], r['candidate_index'], r['id']))
    result = {'case_id': case['id'], 'pool_ids': [r['id'] for r in rows], 'B': {'status': 'READY', 'orderedids': [r['id'] for r in generic]}, 'C': {'status': 'AST_FEATURE_UNAVAILABLE', 'orderedids': []}, 'generic_sort_seconds': time.monotonic()-w}
    bcost = {'wall_seconds': time.monotonic()-w, 'cpu_seconds': cpu()-c}
    cw, cc = time.monotonic(), cpu()
    if ast_record.get('status') == 'AST_AVAILABLE':
        feat = ast_features(ast_record['parsed_asts'], case['source_record']['schema'])
        fs = set(feat['nodes'])
        scores = {}
        for r in rows:
            kind, mut = r['kind'], r['mutation']
            target = (mut['table'], mut['column']) if mut else None
            score = 0
            if kind in ('null_all', 'null_single'):
                score += (30 if kind == 'null_all' else 20) * ('count' in fs)
                score += 25 * ('notin' in fs) + 20 * ('left' in fs)
                score += 40 * (target in [tuple(x) for x in feat['count_columns']])
            if kind == 'duplicate_nonkey':
                score += 40 * ('group' in fs) + 35 * ('distinct' in fs) + 25 * ('having' in fs) + 10 * ('count' in fs)
                score += 60 * (target in [tuple(x) for x in feat['group_columns']])
            scores[r['id']] = score
        candidate = sorted(rows, key=lambda r: (-scores[r['id']], KINDS[r['kind']], r['candidate_index'], r['id']))
        result['C'] = {'status': 'READY', 'orderedids': [r['id'] for r in candidate], 'features': feat, 'scores': scores, 'ast_sha256': ast_record['ast_sha256'], 'smoke_report_sha256': ast_record['report_sha256']}
    else:
        result['C']['reason'] = ast_record.get('reason', 'AST_FEATURE_UNAVAILABLE')
    result['ordering_cost'] = {'B': bcost, 'C': {'wall_seconds': time.monotonic()-cw, 'cpu_seconds': cpu()-cc}, 'scope': 'B sort and C feature extraction/ranking charged to corresponding arm budgets; shared AST loading recorded separately'}
    return result

def _replay(case, rows, budget, probe_id, phase, reverse=False):
    src = case['source_record']
    conn = sqlite3.connect(':memory:')
    outputs, slots = [], []
    def quote(s):
        return '"' + s.replace('"', '""') + '"'
    try:
        for table, fields in src['schema'].items():
            budget.check()
            conn.execute('CREATE TABLE ' + quote(table) + ' (' + ', '.join(quote(k) + ' ' + v for k, v in fields.items()) + ')')
            source_rows = list(reversed(rows[table])) if reverse else rows[table]
            conn.executemany('INSERT INTO ' + quote(table) + ' VALUES (' + ','.join('?' for _ in fields) + ')', [[r[k] for k in fields] for r in source_rows])
        conn.execute('PRAGMA query_only=ON')
        blocked = {sqlite3.SQLITE_ATTACH, sqlite3.SQLITE_DETACH, sqlite3.SQLITE_PRAGMA, sqlite3.SQLITE_INSERT, sqlite3.SQLITE_UPDATE, sqlite3.SQLITE_DELETE}
        conn.set_authorizer(lambda action, *unused: sqlite3.SQLITE_DENY if action in blocked else sqlite3.SQLITE_OK)
        for qi, sql in enumerate(src['pair']):
            budget.check()
            slot = {'case_id': case['id'], 'probe_id': probe_id, 'phase': phase, 'query_index': qi, 'status': 'STARTED', 'original_sql_sha256': case['original_sql_sha256'][qi]}
            budget.emit('QUERY_SLOT_START', slot)
            w, c = time.monotonic(), cpu()
            def progress():
                try:
                    budget.check()
                    return int(time.monotonic()-w >= budget.query_wall_seconds or cpu()-c >= budget.query_cpu_seconds)
                except ProbeStop:
                    return 1
            conn.set_progress_handler(progress, 100)
            try:
                cur = conn.execute(sql)
                values = cur.fetchmany(budget.result_row_limit + 1)
                if len(values) > budget.result_row_limit:
                    raise QueryStop('RESULT_ROW_LIMIT_NO_PARTIAL_COMPARISON')
                if time.monotonic()-w >= budget.query_wall_seconds or cpu()-c >= budget.query_cpu_seconds:
                    raise QueryStop('QUERY_LOCAL_BUDGET_NO_OUTPUT_ADMISSION')
                budget.check()
                slot.update(status='RETURNED', rows=values, column_names=[d[0] for d in cur.description])
                outputs.append(values)
            except (sqlite3.Error, QueryStop) as exc:
                slot.update(status='QUERY_FAILED', error_type=type(exc).__name__, error=str(exc))
                outputs.append(None)
            except ProbeStop as exc:
                slot.update(status='BUDGET_STOP', error=str(exc))
                raise
            finally:
                slot.update(wall_seconds=time.monotonic()-w, cpu_seconds=cpu()-c)
                slots.append(slot)
                budget.emit('QUERY_SLOT_END', slot)
        return outputs, slots
    finally:
        conn.close()

def run_probes(case, pool, orderedids, budget):
    """Run one reviewed arm. All C/SQL/slots/costs retained; NOT_FOUND is not EQ."""
    w, c = time.monotonic(), cpu()
    allrows = {r['id']: r for r in pool if r['case_id'] == case['id']}
    if len(orderedids) != len(allrows) or set(orderedids) != set(allrows):
        raise ValueError('ORDER_MUST_PERMUTE_ENTIRE_SAME_POOL')
    src = case['source_record']
    if [hashlib.sha256(s.encode()).hexdigest() for s in src['pair']] != case['original_sql_sha256']:
        raise ValueError('ORIGINAL_SQL_CHANGED')
    profile = budget.protocol['semantic_intersection'][case['id']]
    if (case['id'] not in EXCLUDED) != profile['eligible']:
        raise ValueError('SEMANTIC_PROFILE_CHANGED')
    result = {'case_id': case['id'], 'arm': budget.arm, 'status': 'STARTED', 'pool_size': len(allrows), 'orderedids': orderedids, 'first_validated_difference': None, 'probes': [{'id': pid, 'status': 'NOT_RUN', 'queries': [{'query_index': i, 'status': 'NOT_RUN'} for i in range(2)]} for pid in orderedids], 'dialect_difference_count': 0, 'failure_count': 0, 'semantic_intersection': profile}
    budget.emit('ARM_REGISTERED_ALL_PROBES_AND_TWO_INITIAL_SQL_SLOTS_EACH', result)
    try:
        for index, pid in enumerate(orderedids):
            budget.check()
            probe = allrows[pid]
            p = {'id': pid, 'status': 'STARTED', 'kind': probe['kind'], 'rows_sha256': probe['rows_sha256'], 'queries': [{'query_index': i, 'status': 'NOT_RUN'} for i in range(2)]}
            result['probes'][index] = p
            budget.emit('PROBE_START', {'case_id': case['id'], **p})
            pw, pc = time.monotonic(), cpu()
            try:
                if probe['rows_sha256'] != objsha(probe['rows']) or probe['schema_sha256'] != objsha(src['schema']) or probe['constraint_sha256'] != objsha(src['constraint']):
                    raise ValueError('PROBE_IDENTITY_MISMATCH')
                p['full_C'] = budget.checker(src['schema'], src['constraint'], probe['rows'])
                if p['full_C']['status'] != 'PASS':
                    p['status'] = 'FULL_C_REJECTED'
                    result['failure_count'] += 1
                    continue
                outputs, p['queries'] = _replay(case, probe['rows'], budget, pid, 'initial')
                if any(x is None for x in outputs):
                    p['status'] = 'QUERY_FAILED'
                    result['failure_count'] += 1
                    continue
                unequal = Counter(map(tuple, outputs[0])) != Counter(map(tuple, outputs[1]))
                p['bag_unequal'] = unequal
                p['status'] = 'NO_DIFFERENCE_ON_THIS_DB'
                if not unequal:
                    continue
                if not profile['eligible']:
                    p['status'] = 'DIALECT_UNKNOWN'
                    result['dialect_difference_count'] += 1
                    if case['id'] == 'dev_01':
                        p['reverse_insertion_outputs'], p['reverse_insertion_slots'] = _replay(case, probe['rows'], budget, pid, 'excluded_reverse_control', reverse=True)
                    continue
                p['validation_full_C'] = budget.checker(src['schema'], src['constraint'], probe['rows'])
                validated, p['validation_slots'] = _replay(case, probe['rows'], budget, pid, 'witness_validation')
                stable = p['validation_full_C']['status'] == 'PASS' and all(x is not None for x in validated) and all(Counter(map(tuple,a)) == Counter(map(tuple,b)) for a,b in zip(outputs,validated))
                if stable:
                    p['status'] = 'VALIDATED_DIFFERENCE_SQLITE_INTERSECTION'
                    result['first_validated_difference'] = {'probe_id': pid, 'candidate_rank_1based': index+1, 'database': probe['rows'], 'outputs': outputs, 'wall_seconds': time.monotonic()-w, 'cpu_seconds': cpu()-c, 'scope': 'specific legal artificial DB under registered SQLite intersection; not natural defect gold'}
                    result['status'] = 'FOUND_VALIDATED_DIFFERENCE'
                    break
                p['status'] = 'WITNESS_VALIDATION_FAILED'
                result['failure_count'] += 1
            except ProbeStop:
                p['status'] = 'BUDGET_STOP'
                raise
            except (ValueError, TypeError, KeyError, sqlite3.Error) as exc:
                p.update(status='FAILED', error_type=type(exc).__name__, error=str(exc))
                result['failure_count'] += 1
            finally:
                p.update(wall_seconds=time.monotonic()-pw, cpu_seconds=cpu()-pc)
                budget.emit('PROBE_END', {'case_id': case['id'], **p})
        if result['status'] == 'STARTED':
            result['status'] = 'NOT_FOUND'
    except ProbeStop as exc:
        result.update(status='BUDGET_STOP_REMAINDER_NOT_RUN', error=str(exc))
    finally:
        result.update(pool_exhausted=all(p['status'] != 'NOT_RUN' for p in result['probes']), successfully_scanned_all=all(p['status'] in ('NO_DIFFERENCE_ON_THIS_DB', 'DIALECT_UNKNOWN') for p in result['probes']), wall_seconds=time.monotonic()-w, cpu_seconds=cpu()-c, ordering_cost_debit=budget.preprocessing_debit, sqlite_version=sqlite3.sqlite_version, equivalence_claim=False)
        budget.emit('ARM_END', result)
    return result

def run_comparison(cases, pool, orders, make_budget, sink, checkpoint=None):
    """Registered execution order: case order, then B followed by C; no solver."""
    results = []
    for case in cases:
        record = orders[case['id']]
        for arm in ('B', 'C'):
            if record[arm]['status'] != 'READY':
                item = {'case_id': case['id'], 'arm': arm, 'status': 'AST_FEATURE_UNAVAILABLE', 'pool_size': len(record['pool_ids']), 'probes': [{'id': p, 'status': 'NOT_RUN', 'queries': [{'query_index': i, 'status': 'NOT_RUN'} for i in range(2)]} for p in record['pool_ids']], 'equivalence_claim': False}
                sink.emit('ARM_NOT_RUN_AST_FEATURE_UNAVAILABLE', item)
            else:
                item = run_probes(case, pool, record[arm]['orderedids'], make_budget(case, arm))
            results.append(item)
            if checkpoint is not None:
                checkpoint(item)
    return results

def no_fallback_savings_gate(results):
    eligible = ('dev_02', 'dev_04', 'dev_05', 'dev_06')
    indexed = {(r['case_id'], r['arm']): r for r in results}
    ready = all((cid, arm) in indexed and indexed[cid, arm].get('status') == 'NOT_FOUND' and indexed[cid, arm].get('successfully_scanned_all') is True and indexed[cid, arm].get('first_validated_difference') is None and indexed[cid, arm].get('failure_count') == 0 for cid in eligible for arm in ('B', 'C'))
    return {'status': 'STOP_FALLBACK_SAVINGS_CLAIM_NO_SOLVER_REPEAT_NEEDED' if ready else 'INSUFFICIENT_COMPLETE_PROBE_EVIDENCE', 'applicable': ready, 'reason': 'Both permutations completely scanned the identical fixed pool and found zero eligible witnesses; neither can avoid fallback on these four exposed groups.' if ready else 'Missing/failed/truncated/positive arms cannot satisfy this stopping rule.', 'claim_scope': 'this frozen candidate set and exposed development groups only; no equivalence or unseen generalization claim', 'automatic_solver_call': False}

def fusion_plan(case, probe_result, protocol):
    """Deferred descriptor only; this comparison never automatically reruns solver."""
    if probe_result.get('status') == 'FOUND_VALIDATED_DIFFERENCE':
        return {'status': 'FALLBACK_AVOIDED_ON_THIS_ARTIFICIAL_WITNESS', 'case_id': case['id'], 'execute': False}
    return {'status': 'FALLBACK_DEFERRED_DEPENDS_ON_PINNED_OFFICIAL_SMOKE', 'case_id': case['id'], 'execute': False, 'official_backend': protocol['official_backend'], 'official_protocol': protocol['official_protocol'], 'required_call_if_separately_authorized': 'same official_smoke_backend.load_runtime/run_case with original case, fullC, exact2rows and remaining total budget; charge all fresh imports/frontend/solver/validation cost', 'speed_claim': 'probe costs plus predecessor dependency evidence only; not measured end-to-end speed'}

def main():
    """Callable only after parent review/freeze, beneath its external RSS guard."""
    import argparse
    start = time.monotonic()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--protocol', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    if not (sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode) or sys.platform != 'darwin':
        raise ValueError('REQUIRES_DARWIN_-B_-I_-S_AND_PARENT_RSS_GUARD')
    protocol = json.loads(args.protocol.read_text())
    if protocol['id'] != 'calibergraph-02-probe-ordering-v1':
        raise ValueError('UNREGISTERED_ORDERING_PROTOCOL')
    if filesha(Path(__file__)) != protocol['worker_sha256']:
        raise ValueError('WORKER_IDENTITY_MISMATCH')
    args.out.mkdir(parents=True, exist_ok=True)
    if (args.out/'probe_report.json').exists():
        raise ValueError('EXISTING_REPORT_MUST_NOT_BE_OVERWRITTEN')
    sink = DurableEvents(args.out/'probe_events.jsonl')
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_CPU, (7, 8))
    def emergency(signum, frame):
        os.write(sink.stream.fileno(), canonical({'event': 'HARD_GUARD_STOP', 'signal': signum, 'unfinished_started_slots': 'ATTEMPTED_EFFECT_UNKNOWN', 'untouched_registered_slots': 'NOT_RUN'})+b'\n')
        os.fsync(sink.stream.fileno())
        os._exit(124)
    signal.signal(signal.SIGXCPU, emergency)
    signal.signal(signal.SIGALRM, emergency)
    signal.pthread_sigmask(signal.SIG_UNBLOCK, {signal.SIGXCPU, signal.SIGALRM})
    signal.setitimer(signal.ITIMER_REAL, 15.0)
    report = {'protocol_id': protocol['id'], 'protocol_sha256': filesha(args.protocol), 'worker_sha256': filesha(Path(__file__)), 'status': 'STARTED', 'scope': 'Probe-cost diagnostic plus pinned official-smoke dependency; no end-to-end speed measurement', 'records': [{'case_id': cid, 'arm': arm, 'status': 'NOT_RUN'} for cid in protocol['case_ids'] for arm in ('B', 'C')], 'pure_fallback': {'status': 'PINNED_DEPENDENCY_EVIDENCE_ONLY_NOT_RERUN', 'smoke_report': protocol['smoke_report'], 'speed_claim': False}}
    def save():
        destination = args.out/'probe_report.json'
        tmp = destination.with_suffix('.tmp')
        with tmp.open('w') as f:
            json.dump(report, f, ensure_ascii=False, indent=2, allow_nan=False)
            f.write('\n'); f.flush(); os.fsync(f.fileno())
        tmp.replace(destination)
    def global_check():
        if cpu() >= 6.75:
            raise ProbeStop('GLOBAL_CPU_RESERVE')
        if time.monotonic()-start >= 13.5:
            raise ProbeStop('GLOBAL_WALL_RESERVE')
        if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss >= 256*1024**2:
            raise ProbeStop('GLOBAL_RSS_OBSERVATION')
    save()
    try:
        cases, pool, checker, preparation = load_inputs(protocol)
        report['shared_preparation'] = preparation
        global_check()
        fw, fc = time.monotonic(), cpu()
        asts = load_smoke_asts(protocol['smoke_report']['path'], protocol['smoke_report']['sha256'], cases, protocol)
        report['shared_ast_cache_read_cost'] = {'wall_seconds': time.monotonic()-fw, 'cpu_seconds': cpu()-fc, 'charge': 'once shared in actual diagnostic; add in full to each standalone B/C scenario; historical parser/import costs separately reported and not free frontend'}
        orders = {case['id']: build_orders(case, pool, asts[case['id']]) for case in cases}
        report['orders'] = orders
        report['ast_provenance'] = {cid: {k: v for k,v in rec.items() if k != 'parsed_asts'} for cid,rec in asts.items()}
        report['registered_matrix'] = [{'case_id': case['id'], 'arm': arm, 'probes': [{'id': p['id'], 'status': 'NOT_RUN', 'initial_query_slots': [{'query_index': qi, 'status': 'NOT_RUN'} for qi in (0, 1)]} for p in pool if p['case_id'] == case['id']]} for case in cases for arm in ('B', 'C')]
        sink.emit('COMPLETE_MATRIX_REGISTERED_BEFORE_SQL', report['registered_matrix'])
        sink.emit('ORDERINGS_FROZEN_BEFORE_SQL', orders)
        save()
        def make_budget(case, arm):
            global_check()
            return ProbeBudget(sink, arm, checker, protocol, outer_check=global_check, preprocessing_debit=orders[case['id']]['ordering_cost'][arm])
        def checkpoint(item):
            index = protocol['case_ids'].index(item['case_id'])*2 + ('B', 'C').index(item['arm'])
            report['records'][index] = item
            save()
        run_comparison(cases, pool, orders, make_budget, sink, checkpoint)
        report['no_fallback_savings_gate'] = no_fallback_savings_gate(report['records'])
        report['status'] = 'ALL_REGISTERED_ARMS_RETURNED'
    except BaseException as exc:
        report.update(status='STOPPED_OR_FAILED_REMAINDER_NOT_RUN', error_type=type(exc).__name__, error=str(exc))
    finally:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        report['worker_usage'] = {'whole_process_cpu_user_seconds': usage.ru_utime, 'whole_process_cpu_system_seconds': usage.ru_stime, 'main_wall_seconds': time.monotonic()-start, 'peak_rss_bytes_macos': usage.ru_maxrss, 'event_io_wall_seconds_included_in_arm_or_shared_work': sink.wall_seconds, 'event_io_cpu_seconds_included_in_arm_or_shared_work': sink.cpu_seconds, 'final_save_cleanup_cost': 'only external supervisor complete-process totals include final report serialization/fsync/close'}
        report['status_counts'] = dict(Counter(r['status'] for r in report['records']))
        save(); sink.close()
        signal.setitimer(signal.ITIMER_REAL, 0)
        print(json.dumps({'status': report['status'], 'status_counts': report['status_counts'], 'stop_gate': report.get('no_fallback_savings_gate'), 'usage': report['worker_usage']}), flush=True)
    return 0 if report['status'] == 'ALL_REGISTERED_ARMS_RETURNED' else 2

if __name__ == '__main__':
    raise SystemExit(main())
