"""Round 16 frozen input admission and stdlib guards; no SQL/target imports."""
from pathlib import Path
import hashlib
import json
import os
import resource
import signal
import sys
import time


PROTOCOL_ID = 'calibergraph-16-generation-replay-v1'
# Root must independently review, amend, and freeze before enabling execution.
EXECUTION_ENABLED = True
REGISTRY_SHA256 = 'ab80ebcf869015d324af3e35b9dd8352013e0037dec6922e7788f4cf366e4ffb'
RUNTIME_SHA256 = '505e59253be72e73edf236efe647d84cfcebffe15980517072ae20230bdc38d7'


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda: handle.read(262144), b''):
            h.update(block)
    return h.hexdigest()


def objsha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
        separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def cpu():
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return usage.ru_utime + usage.ru_stime


def atomic_json(path, value):
    path = Path(path)
    temp = path.with_name(path.name + '.tmp')
    with temp.open('w') as handle:
        handle.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
        handle.flush()
        os.fsync(handle.fileno())
    temp.replace(path)


def install_guards(events, record, process_start):
    if (sys.platform != 'darwin' or sys.version_info[:2] != (3, 12)
            or not (sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode)):
        raise ValueError('REQUIRES_DARWIN_PYTHON312_-B_-I_-S')
    if os.getpriority(os.PRIO_PROCESS, 0) < 15:
        raise ValueError('PARENT_MUST_SET_NICE_AT_LEAST_15')
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_CPU, (3, 3))
    def emergency(signum, frame):
        os.write(events.fileno(), json.dumps({'event': 'HARD_GUARD_SIGNAL', 'signal': signum,
            'active_stage': record.get('active_stage'), 'outcome': 'INCONCLUSIVE_OR_NOT_RUN'}).encode() + b'\n')
        os.fsync(events.fileno())
        os._exit(124)
    signal.signal(signal.SIGXCPU, emergency)
    signal.signal(signal.SIGALRM, emergency)
    signal.pthread_sigmask(signal.SIG_UNBLOCK, {signal.SIGXCPU, signal.SIGALRM})
    remaining = 4.0 - (time.monotonic() - process_start)
    if remaining <= 0:
        raise ValueError('WORKER_WALL_BUDGET_ALREADY_EXHAUSTED')
    signal.setitimer(signal.ITIMER_REAL, remaining)


def load_registered(protocol_path, case_index, kind='official'):
    if not EXECUTION_ENABLED:
        raise ValueError('PREPARATION_ONLY_EXECUTION_DISABLED_PENDING_INDEPENDENT_REVIEW')
    protocol = json.loads(Path(protocol_path).read_text())
    if protocol.get('id') != PROTOCOL_ID or protocol.get('status') != 'REGISTERED':
        raise ValueError('UNREGISTERED_PROTOCOL')
    if protocol.get('contract_model_sanity_control') is not True:
        raise ValueError('EXPLICIT_REGISTERED_C_MODEL_SANITY_CONTROL_REQUIRED')
    required = {
        'worker_cpu_limit_seconds': 3, 'worker_wall_limit_seconds': 4,
        'external_rss_limit_bytes': 268435456, 'contract_check_timeout_ms': 100,
        'query_check_timeout_ms': 700, 'maximum_independent_environment_attempts': 1,
        'maximum_active_workers': 1, 'nice': 15, 'total_parent_cpu_limit_seconds': 60,
        'solver_cumulative_wall_limit_seconds': 2.0, 'solver_timeout_reserve_seconds': 0.1,
        'supervisor_solver_stop_seconds': 1.5, 'internal_z3_memory_parameter_mb': 128,
        'maximum_batch_attempts': 1,
    }
    if any(protocol.get(key) != value for key, value in required.items()):
        raise ValueError('REGISTERED_RESOURCE_BUDGET_MISMATCH')
    registry = protocol['input']
    path = Path(registry['path'])
    if registry['sha256'] != REGISTRY_SHA256 or sha(path) != REGISTRY_SHA256:
        raise ValueError('ORIGINAL_03_21_CASE_REGISTRY_HASH_MISMATCH')
    cases = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    if [case['id'] for case in cases] != ['dev03_' + str(n).zfill(2) for n in range(1, 22)]:
        raise ValueError('ORIGINAL_03_21_CASE_DENOMINATOR_CHANGED')
    indices = protocol['source_case_indices']
    if indices != [6, 9, 14, 3] or any(type(i) is not int for i in indices):
        raise ValueError('ONLY_FROZEN_EXPOSED_03_DEVELOPMENT_INDICES_ALLOWED')
    slots = protocol['registered_cases']
    expected = [{'id': f'dev03_{i + 1:02d}_exact{n}_rep{repeat_id}', 'kind': 'official',
                 'source_case_index': i, 'source_case_id': f'dev03_{i + 1:02d}',
                 'exact_rows': n, 'repeat_id': repeat_id}
                for repeat_id, source_order, bounds in (
                    (1, (6, 9, 14, 3), (2, 3, 4)),
                    (2, (3, 14, 9, 6), (4, 3, 2)))
                for i in source_order for n in bounds]
    if (slots != expected or any(type(s.get('source_case_index')) is not int or
            type(s.get('exact_rows')) is not int or type(s.get('repeat_id')) is not int for s in slots)):
        raise ValueError('CASE_BOUND_DENOMINATOR_OR_ORDER_CHANGED')
    if (not 0 <= case_index < len(slots) or len({s['id'] for s in slots}) != len(slots)
            or any(s.get('kind') != 'official' for s in slots)):
        raise ValueError('UNREGISTERED_SLOT_OR_METHOD')
    slot = slots[case_index]
    case = cases[slot['source_case_index']]
    if slot.get('source_case_id') != case['id']:
        raise ValueError('SOURCE_CASE_ID_MISMATCH')
    source = case['source_record']
    if ([hashlib.sha256(q.encode()).hexdigest() for q in source['pair']]
            != case['original_sql_sha256']):
        raise ValueError('ORIGINAL_SQL_BYTES_CHANGED')
    for field, key in [('schema_sha256', 'schema'), ('constraint_sha256', 'constraint')]:
        if objsha(source[key]) != case[field]:
            raise ValueError('ORIGINAL_' + field.upper() + '_MISMATCH')
    runtime = protocol['runtime_lock']
    if runtime['sha256'] != RUNTIME_SHA256 or sha(runtime['path']) != RUNTIME_SHA256:
        raise ValueError('FROZEN_OFFICIAL_RUNTIME_LOCK_MISMATCH')
    return protocol, case, slot
