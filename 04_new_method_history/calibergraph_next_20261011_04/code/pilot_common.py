"""Round 04 frozen input admission and stdlib guards; no SQL/target imports."""
from pathlib import Path
import hashlib
import json
import os
import resource
import signal
import sys
import time


PROTOCOL_ID = 'calibergraph-04-exact-boundary-pilot-v1'
REGISTRY_SHA256 = 'ab80ebcf869015d324af3e35b9dd8352013e0037dec6922e7788f4cf366e4ffb'
RUNTIME_SHA256 = '505e59253be72e73edf236efe647d84cfcebffe15980517072ae20230bdc38d7'
SQL_SHA256 = [
    'e21b8087c803decd4bad4d7866dff98387caf1f693ed6dfc1a66be94fbdc87d0',
    '1b196a128452b139a661429d22c69c8afbf5b086c3c842f20cf34e347c3e3f8a',
]
SCHEMA_SHA256 = '518a97e07803e763e1459b8c63e18366bedf07587e06d21c4389e4482c41645d'
CONSTRAINT_SHA256 = '28f01a6c2b01d26cdee786e26ee3b5a07212f73747a67bd0d36d5900a15fe15f'
EXPECTED_SCHEMA = {'COURSES': {'CLASS': 'VARCHAR', 'STUDENT': 'VARCHAR'}}
EXPECTED_CONSTRAINT = [{'primary': [{'value': 'COURSES__STUDENT'}]}]


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


def validate_contract(case):
    source = case['source_record']
    if source.get('schema') != EXPECTED_SCHEMA:
        raise ValueError('SCHEMA_NOT_EXACT_ORIGINAL_COURSES_TWO_VARCHAR_COLUMNS')
    if source.get('constraint') != EXPECTED_CONSTRAINT:
        raise ValueError('FULL_C_CHECKER_REJECTS_ANY_ADDITIONAL_OR_UNKNOWN_CLAUSE')
    if list(source['schema']) != ['COURSES'] or list(source['schema']['COURSES']) != ['CLASS', 'STUDENT']:
        raise ValueError('ORIGINAL_SCHEMA_ORDER_CHANGED')
    return {'status': 'COMPLETE_ORIGINAL_C_SUPPORTED', 'clause_count': 1,
        'constraint': source['constraint'], 'primary_key': ['COURSES.STUDENT'],
        'class_nullable': True, 'unknown_or_omitted_clauses': 0,
        'scope': 'Full explicit original operational C; natural/business completeness remains unverified.'}


def load_registered(protocol_path, case_index, kind):
    protocol = json.loads(Path(protocol_path).read_text())
    if protocol.get('id') != PROTOCOL_ID:
        raise ValueError('UNREGISTERED_PROTOCOL')
    required = {
        'worker_cpu_limit_seconds': 3, 'worker_wall_limit_seconds': 4,
        'external_rss_limit_bytes': 268435456, 'contract_check_timeout_ms': 100,
        'query_check_timeout_ms': 700, 'maximum_independent_environment_attempts': 1,
        'maximum_active_workers': 1, 'nice': 15,
        'solver_cumulative_wall_limit_seconds': 2.0, 'solver_timeout_reserve_seconds': 0.1,
        'supervisor_solver_stop_seconds': 1.5, 'internal_z3_memory_parameter_mb': 128,
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
    case = cases[17]
    if case['id'] != protocol.get('source_case_id') or case['id'] != 'dev03_18':
        raise ValueError('ORIGINAL_SOURCE_CASE_MISMATCH')
    slots = protocol['registered_cases']
    if not isinstance(slots, list) or len(slots) != 10 or not 0 <= case_index < len(slots):
        raise ValueError('UNREGISTERED_SLOT')
    if [(slot.get('kind'), slot.get('exact_rows')) for slot in slots] != [
            (worker_kind, n) for n in range(1, 6) for worker_kind in ('concrete', 'official')]:
        raise ValueError('FROZEN_TEN_SLOT_ORDER_CHANGED')
    identities = set()
    for slot in slots:
        expected_fixture = {'official': 'unconstrained_original_C',
                            'concrete': 'all_null_class_and_nonnull_control'}.get(slot.get('kind'))
        identity = (slot.get('kind'), slot.get('exact_rows'))
        if (not isinstance(slot.get('id'), str) or not slot['id']
                or slot.get('source_case_id') != 'dev03_18'
                or type(slot.get('exact_rows')) is not int or slot['exact_rows'] not in range(1, 6)
                or expected_fixture is None or slot.get('fixture') != expected_fixture
                or identity in identities):
            raise ValueError('UNREGISTERED_OR_DUPLICATED_SHAPE_OR_FIXTURE')
        identities.add(identity)
    if len({slot['id'] for slot in slots}) != len(slots):
        raise ValueError('DUPLICATED_SLOT_ID')
    slot = slots[case_index]
    if slot['kind'] != kind:
        raise ValueError('WRONG_WORKER_FOR_REGISTERED_SLOT')
    source = case['source_record']
    if not isinstance(source.get('pair'), list) or len(source['pair']) != 2:
        raise ValueError('ORIGINAL_PAIR_MISSING')
    actual_sql = [hashlib.sha256(sql.encode()).hexdigest() for sql in source['pair']]
    if actual_sql != SQL_SHA256 or case['original_sql_sha256'] != SQL_SHA256 or protocol.get('original_sql_sha256') != SQL_SHA256:
        raise ValueError('ORIGINAL_SQL_BYTES_CHANGED')
    for field, expected in [('schema_sha256', SCHEMA_SHA256), ('constraint_sha256', CONSTRAINT_SHA256)]:
        value = source['schema' if field == 'schema_sha256' else 'constraint']
        if case[field] != expected or protocol.get(field) != expected or objsha(value) != expected:
            raise ValueError('ORIGINAL_' + field.upper() + '_MISMATCH')
    runtime = protocol['runtime_lock']
    if runtime['sha256'] != RUNTIME_SHA256 or sha(runtime['path']) != RUNTIME_SHA256:
        raise ValueError('FROZEN_OFFICIAL_RUNTIME_LOCK_MISMATCH')
    validate_contract(case)
    return protocol, case, slot
