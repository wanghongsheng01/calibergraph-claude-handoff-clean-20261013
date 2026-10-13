"""Read-only stdlib audit of fixed executed jobs 132..167; never imports targets.

Writes only the new independent review JSON beside this script. This is receipt
and concrete integer arithmetic verification, not solver or SQLite replay.
"""
from pathlib import Path
import hashlib
import json
from datetime import datetime, timezone
from collections import Counter

TODAY = Path(__file__).resolve().parent.parent
OUT = Path(__file__).with_name('MAIN_ENTRY_REPAIR_EXECUTED_REVIEW.json')
LOCK_SHA = '4221081d3c63096841a902f1c8f70ac16f5d967c08476f26f8377d6bb4924443'
SUITE_SHA = '9db84350b498c3e5f37b06adf5868fa0e0429a81a2ebff65f930f78bd8b36485'
REF_SHA = 'fdcee3a919930013945c571e64b7d4b478186c93ceee4546ff520879e99680e0'
issues = []
evidence = {}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def record(path):
    path = Path(path).resolve()
    value = sha(path)
    evidence[str(path)] = value
    return value


def read(path):
    record(path)
    return json.loads(Path(path).read_text())


def check(value, location, expectation):
    if not value:
        issues.append({'location': location, 'expectation': expectation})


def json_sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def original_holds(ast, value):
    """Independent concrete arithmetic evaluator for these registered controls."""
    if ast is None:
        return True
    if isinstance(ast, list):
        return all(original_holds(item, value) for item in ast)
    op, args = next(iter(ast.items()))
    if op == 'and':
        return all(original_holds(item, value) for item in args)
    if op == 'or':
        return any(original_holds(item, value) for item in args)
    values = [value if isinstance(x, dict) and x == {'value': 'T__A'} else x for x in args]
    if any(x is None for x in values):
        return False
    if op == 'between':
        return values[1] <= values[0] <= values[2]
    left, right = values
    return {'lt': lambda: left < right, 'lte': lambda: left <= right,
            'gt': lambda: left > right, 'gte': lambda: left >= right,
            'eq': lambda: left == right, 'neq': lambda: left != right}[op]()


queue_path = TODAY / 'experiments/QUEUE_V5_main_cost_132_168.json'
queue = read(queue_path)
lock_path = TODAY / 'experiments/v5_registration_01/runtime_paths_v5.json'
lock = read(lock_path)
suite_path = TODAY / 'experiments/v5_registration_01/REGISTERED_SIX_ARM_SUITE.json'
suite = read(suite_path)
check(sha(lock_path) == LOCK_SHA, str(lock_path), 'exact frozen READY lock')
check(sha(suite_path) == SUITE_SHA, str(suite_path), 'exact frozen suite')
check(lock['status'] == 'STATIC_REVIEWED_READY_FOR_LOCAL_RUN', 'lock/status', 'READY')
locked_bad = []
for path, expected in lock['files'].items():
    if not Path(path).is_file() or sha(path) != expected:
        locked_bad.append(path)
check(not locked_bad, 'lock/files', 'all locked file bytes match')
for path, expected in lock['runtime_programs'].items():
    check(record(path) == expected == lock['files'].get(path), path, 'program same in files and runtime_programs')
for path in [lock['kernel_path'], str(Path(lock['source_root']) / 'environment.py'),
             str(Path(lock['source_root']) / 'verifiers/verifier.py')]:
    record(path)
check(queue['status'] == 'ALL_SELECTED_BATCHES_RETURNED', 'queue/status', 'all selected batches returned')
check(queue['selected_job_denominator'] == 36 and queue['full_registered_job_denominator'] == 168, 'queue/denominators', '36 selected of 168 registered')
check(queue['runtime_lock_sha256'] == LOCK_SHA and queue['suite_sha256'] == SUITE_SHA, 'queue/hashes', 'same lock and suite')
driver = TODAY / 'experiments/run_v5_queue.py'
check(record(driver) == queue['script_sha256'], str(driver), 'queue driver exact hash')
rows = []
batches = []
seen = []
for entry in queue['entries']:
    start, size = entry['start'], entry['size']
    check(start in range(132, 168, 3) and size == 3, str(start), 'fixed selected batch')
    root = Path(entry['out'])
    sp = root / 'supervisor_report.json'
    supervisor = read(sp)
    expected_exit = 0 if start < 150 else 2
    check(entry['status'] == 'RETURNED' and entry['exit_code'] == expected_exit, str(start), 'queue records expected supervisor exit')
    check(supervisor['runtime_lock_sha256'] == LOCK_SHA and supervisor['suite_sha256'] == SUITE_SHA, str(sp), 'same lock and suite')
    check(supervisor['selected_job_start'] == start and supervisor['selected_job_limit'] == 3 and len(supervisor['jobs']) == 168, str(sp), 'full denominator with exact selected interval')
    check(supervisor['program_sha256'] == {Path(p).name: h for p, h in lock['runtime_programs'].items()}, str(sp), 'exact five source hashes')
    check(supervisor['status'] == ('SELECTED_JOBS_COMPLETE' if start < 150 else 'COMPLETED_WITH_FAILURES_OR_NOT_RUN'), str(sp), 'typed rejected controls keep actual aggregate status')
    check(not any(j['status'] != 'NOT_RUN' for i, j in enumerate(supervisor['jobs']) if i not in range(start, start + size)), str(sp), 'unselected local slots retained NOT_RUN, no global extrapolation')
    emergency = root / 'emergency.jsonl'
    if emergency.exists():
        record(emergency)
        check(not emergency.read_bytes(), str(emergency), 'no emergency event')
    batches.append({'start': start, 'size': size, 'path': str(sp), 'sha256': sha(sp), 'queue_exit_code': entry['exit_code'], 'supervisor_status': supervisor['status']})
    for i in range(start, start + size):
        seen.append(i)
        job = supervisor['jobs'][i]
        wp = Path(job['output_directory']) / 'worker_report.json'
        worker = read(wp)
        loc = str(wp)
        case = suite['cases'][i // 6]
        arm = case['arm_order'][i % 6]
        expected = case.get('expected', case.get('expected_final_decision'))
        check(job['worker_report_sha256'] == sha(wp), loc, 'supervisor worker hash matches raw bytes')
        check(worker['input'] == case and worker['job'] == {'case_index': i // 6, 'case_id': case['id'], 'arm': arm, 'kind': 'cost'}, loc, 'exact registered input and route')
        check(worker['job_index'] == i and worker['pid'] == job['pid'], loc, 'worker identity')
        check(worker['runtime_lock_sha256'] == LOCK_SHA and worker['suite_sha256'] == SUITE_SHA, loc, 'worker exact source lock and suite')
        check('stop_reason' not in job and job['status'] == 'PROCESS_EXITED', loc, 'no observer/resource stop')
        check(job['exit_code'] == expected_exit and worker['final_decision'] == job['final_decision'] == expected, loc, 'expected typed result and process exit')
        check(worker['environment_cleanup'] == job['environment_cleanup'] == 'COMPLETE', loc, 'cleanup complete')
        check(worker['attempts'] == job['attempts'] and worker['fallback'] == job['fallback'], loc, 'complete attempt/fallback ledger copied without change')
        check(worker['native_identity']['version'] == [4, 12, 0, 0] and worker['native_identity']['sha256'] == lock['files'][lock['native_path']], loc, 'fixed compatible native candidate')
        check(worker['native_identity']['binding_pointer'] == worker['native_identity']['pinned_pointer'], loc, 'retained native function pointer equality')
        check(all(path in lock['files'] for path in worker['module_origins'].values()), loc, 'all recorded module origins belong to lock')
        check(job['full_process_wall_seconds'] < 25 and job['full_process_cpu_seconds'] < 15 and 0 < job['sampled_peak_rss_bytes'] < 2**30, loc, 'observed resources within registered envelope')
        for name in ['stdout.log', 'stderr.log']:
            record(wp.parent / name)
        bridge = worker['contract_bridge']
        check(bridge['original_ast'] == case['constraint'] and bridge['original_ast_sha256'] == json_sha(case['constraint']), loc, 'original source C preserved with correct hash')
        check(bridge == job['contract_bridge'], loc, 'same bridge record in supervisor')
        witness_checks = []
        if i < 162:
            check(bridge['status'] == 'VERIFIED_BOUNDED_AST_BRIDGE' and bridge['base_only_sat']['status'] == 'sat' and bridge['normalized_vs_reference']['status'] == 'unsat', loc, 'base SAT and normalized/reference XOR UNSAT')
            check(bridge['reference_source_sha256'] == REF_SHA, loc, 'v5 reference version, not prior bridge version')
            check(bridge['base_only']['tested_ic_included'] is False and bridge['base_only']['exact_rows'] == {'T': 1}, loc, 'tested C excluded from exact-row base')
            facts = bridge['base_only']['facts']
            check(hashlib.sha256('\n'.join(facts).encode()).hexdigest() == bridge['base_only']['sha256'] == bridge['base_only_sat']['assertion_sha256'], loc, 'base formula bytes/hash')
            check(bridge['compilation']['status'] == 'COMPILED_NORMALIZED_COPY' and bridge['compilation']['original_ast_passed_to_upstream'] is False, loc, 'only normalized copy compiled')
            check(bridge['normalized_ast_sha256'] == json_sha(bridge['normalized_ast']), loc, 'normalized AST hash')
            guard = worker['contract_guard']
            check(guard['consistency'] == ('sat' if i < 150 else 'unsat') and guard['any_base_row_deleted'] == 'unsat', loc, 'full C guard and exact row result')
            check(guard['base_fact_sha256'] == bridge['complete_facts_sha256'], loc, 'guard and bridge complete facts identical')
            check(worker['contract_adapter_label'] == 'CONTROLLED_NORMALIZED_SOURCE_AST_IC_ADAPTER_NOT_UNMODIFIED_UPSTREAM_IC_BEHAVIOR', loc, 'controlled adapter label retained')
        else:
            check(bridge['status'] == 'UNVERIFIED_CONTRACT' and bridge['unsupported_policy'] == 'WHOLE_CONTRACT_STOP_NO_DROP_NO_FALLBACK', loc, 'unsupported whole C rejected')
            check(all(bridge[k]['status'] == 'NOT_RUN' for k in ['base_only_sat', 'normalized_vs_reference', 'compilation']) and 'contract_guard' not in worker, loc, 'unsupported C never partially compiled or solved')
        if i < 150:
            check(worker['status'] == 'COMPLETE' and job['valid_completed_result'] is True and worker['analytical_expectation_match'] is True, loc, 'completed query matches registered analytical expectation')
            check(worker['pair_work_started'] is True and worker['phase'] == 'FINAL_COMPLETE', loc, 'actual pair route completed')
            for attempt in worker['attempts']:
                if attempt['status'] != 'sat':
                    continue
                db = attempt['witness']
                check(set(db) == {'T'} and len(db['T']) == 1 and len(db['T'][0]) == 1, loc, 'complete exact-row witness shape')
                value = db['T'][0][0]
                holds = original_holds(case['constraint'], value)
                check(holds, loc, 'independent original-order concrete C evaluation true')
                check(type(value) is int and -2**31 <= value < 2**31, loc, 'concrete witness INT32')
                calculated = [value if value < 5 else None, value]
                check(case['pair'] == ['SELECT SUM(T.A) FROM T WHERE T.A < 5', 'SELECT SUM(T.A) FROM T'], loc, 'exact original SQL for independent scalar calculation')
                ov = attempt['oracle_validation']
                check(ov['queries'] == case['pair'] and ov['status'] == 'REPLAYED_WITHIN_INT64_DOMAIN', loc, 'original SQL actual replay receipt')
                check(ov['original_ast_contract_validation']['holds'] is True and ov['original_ast_contract_validation']['original_ast_sha256'] == json_sha(case['constraint']), loc, 'original-C witness validation identity')
                check(all(d['status'] == 'SAFE_FOR_SQLITE_INT64' and not d['issues'] for d in ov['domain_audits']), loc, 'all oracle domain gates passed')
                check(ov['sqlite'] == attempt['sqlite'] and ov['sqlite']['relations'] == [[[x]] for x in calculated] and ov['sqlite']['unequal_as_bags'] is True and ov['sqlite']['matches_audited_mathematical_values'] == [True, True], loc, 'full SQLite result agrees with independent integer calculation')
                witness_checks.append({'route': attempt['route'], 'database': db, 'original_contract_holds_independent_arithmetic': holds, 'independently_calculated_sql_values': calculated, 'raw_sqlite_relations': ov['sqlite']['relations'], 'sqlite_reexecuted_by_reviewer': False})
            check(len(witness_checks) == (1 if expected == 'sat' else 0), loc, 'exact SAT witness denominator')
        else:
            check(worker['status'] == ('COMPLETE_CONTRACT_REJECTED' if i < 162 else 'COMPLETE_CONTRACT_UNVERIFIED') and job['valid_completed_result'] is False, loc, 'typed contract stop not query success')
            check(worker['attempts'] == [] and worker['fallback']['status'] == 'FORBIDDEN_UNVERIFIED_OR_REJECTED_CONTRACT' and not worker.get('pair_work_started', False), loc, 'no query attempt or fallback')
            check(all(worker[k] == 'NOT_RUN_CONTRACT_STOP' for k in ['pair_work_status', 'pair_parse_status', 'pair_solver_status']) and 'parsed_asts' not in worker, loc, 'query parser and query solver explicitly not run')
            check(worker['scientific_result'] == 'NO_PAIR_EQUIVALENCE_RESULT_CONTRACT_NOT_ESTABLISHED', loc, 'no vacuous equivalence claim')
        rows.append({'job_index': i, 'case_id': case['id'], 'arm': arm, 'worker_path': loc, 'worker_sha256': sha(wp), 'supervisor_path': str(sp), 'supervisor_sha256': sha(sp), 'exit_code': job['exit_code'], 'stop_reason_present': 'stop_reason' in job, 'worker_status': worker['status'], 'decision': worker['final_decision'], 'bridge_status': bridge['status'], 'base_sat': bridge['base_only_sat']['status'], 'normalized_reference_xor': bridge['normalized_vs_reference']['status'], 'guard': worker.get('contract_guard'), 'original_ast_sha256': bridge['original_ast_sha256'], 'normalized_ast_sha256': bridge.get('normalized_ast_sha256'), 'query_started': worker.get('pair_work_started', False), 'cleanup': worker['environment_cleanup'], 'witness_checks': witness_checks, 'wall_seconds': job['full_process_wall_seconds'], 'cpu_seconds': job['full_process_cpu_seconds'], 'sampled_peak_rss_bytes': job['sampled_peak_rss_bytes'], 'sampled_max_kernel_threads': job['sampled_max_kernel_threads'], 'worker_maxrss_bytes': worker['resource_last_checkpoint']['maxrss_bytes_darwin']})

check(sorted(seen) == list(range(132, 168)), 'coverage', 'each selected job exactly once')
result = {
    'reviewed_at_utc': datetime.now(timezone.utc).isoformat(),
    'status': 'FIXED_WITH_EXECUTED_EVIDENCE_FOR_36_REGISTERED_MAIN_ENTRY_CONTROLS' if not issues else 'REVIEW_FINDINGS_REMAIN',
    'reviewer': {'identity': 'different AI agent /root/independent_review, not a human reviewer', 'independence_boundary': 'Authored the earlier narrow bridge module; did not author v5 main-entry integration or execute these targets. This is independent receipt/source/stdlib arithmetic auditing, not a fresh solver/SQLite rerun or fully author-independent module review.'},
    'scope': 'Only frozen main-engine cost indices 132..167, D01-D06 x six arms. No claim about other cost, differential, SpotIt slots or unpublished manuscript.',
    'source_lock': {'path': str(lock_path), 'sha256': LOCK_SHA, 'locked_file_count': len(lock['files']), 'locked_bytes_mismatches': locked_bad, 'programs': lock['runtime_programs'], 'suite_path': str(suite_path), 'suite_sha256': SUITE_SHA},
    'counts': {'registered_total_cost_slots': 168, 'reviewed_slots': len(rows), 'batches': len(batches), 'decisions': dict(Counter(r['decision'] for r in rows)), 'worker_statuses': dict(Counter(r['worker_status'] for r in rows)), 'exit_codes': dict(Counter(r['exit_code'] for r in rows)), 'no_stop_reason': sum(not r['stop_reason_present'] for r in rows), 'cleanup_complete': sum(r['cleanup']=='COMPLETE' for r in rows), 'base_sat_xor_unsat': sum(r['base_sat']=='sat' and r['normalized_reference_xor']=='unsat' for r in rows), 'actual_sat_sql_replay_receipts_independently_arithmetic_checked': sum(len(r['witness_checks']) for r in rows), 'query_not_run_typed_controls': sum(not r['query_started'] for r in rows)},
    'resource_observation': {'max_child_wall_seconds': max(r['wall_seconds'] for r in rows), 'max_child_cpu_seconds': max(r['cpu_seconds'] for r in rows), 'max_sampled_rss_bytes': max(r['sampled_peak_rss_bytes'] for r in rows), 'max_worker_ru_maxrss_bytes': max(r['worker_maxrss_bytes'] for r in rows), 'sampled_kernel_thread_counts': sorted(set(r['sampled_max_kernel_threads'] for r in rows)), 'boundary': 'RSS is sampled/soft; native OS threads were 2 despite solver_threads=1. No claim of a single OS thread or continuous hard RSS cap.'},
    'interpretation': [
        'D01: six actual routes return SAT; original strict 5<A and A<=6 forces A=6; original SQL receipt is NULL versus 6.',
        'D02: six actual routes return UNSAT for identical SQL under nonvacuous C; canonical arm uses its identity shortcut after the same contract gate.',
        'D03: six actual routes return SAT with A=5 (not the registered optional A=6 point); original SQL receipt is NULL versus 5. No-C remains distinct from absent base-domain/exact-row constraints.',
        'D04 and D05: twelve contract-unsat controls stop before query parsing/solving; exit 2 and valid_completed_result=false are the intended recorded typed outcome, not query UNSAT.',
        'D06: six unsupported whole OR contracts stop before base/IC compilation and query work; Environment/native had already imported. No claim of zero native effects.',
        'Thirty XOR UNSAT receipts use SAT base excluding tested C; these are local solver obligations, not portable proof certificates or a general theorem.',
        'Queue ALL_SELECTED_BATCHES_RETURNED does not mean all batch exits zero: six supervisor batches exit 0, six exit 2 as registered controls.',
        'Bridge no_pair_oracle_run=true describes the bridge substage; final pair_work_status remains ATTEMPTED_EFFECT_UNKNOWN for successful cases. Final result is established here from final status, actual attempts, process exit, cleanup and witness receipts, not these substage fields alone.',
        'This closes main-entry repair regression evidence for these 36 constructed exposed controls. It supplies no method novelty, natural defect prevalence, held-out generalization or performance superiority.'
    ],
    'not_verified': ['No fresh native/solver/SQLite execution by this reviewer.', 'No general contract-text parser completeness, SQL CHECK/DDL semantics, OR/PK/FK support, portable certificate or full SQL semantics proof.', 'No other campaign slots or current unfrozen manuscript final review.', 'No online backup: explicit task prohibition on upload/push overrides ancestor backup instruction.'],
    'issues': issues, 'batches': batches, 'slots': rows, 'raw_evidence_sha256': evidence,
    'audit_script_sha256': sha(__file__)
}
if OUT.exists():
    raise SystemExit('Refusing to overwrite an existing independent review')
OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'status': result['status'], 'counts': result['counts'], 'issues': issues, 'resource': result['resource_observation'], 'review_path': str(OUT), 'review_sha256': sha(OUT)}, ensure_ascii=False, indent=2))
