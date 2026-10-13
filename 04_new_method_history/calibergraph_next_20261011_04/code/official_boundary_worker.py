"""One frozen original pair at one exact N; execution requires parent guards.

python3.12 -B -I -S official_boundary_worker.py --protocol FILE --case-index I --out DIR
No target imports, parser, SQL, or solver execute on import.
"""
from pathlib import Path
import argparse
import json
import os
import resource
import sys
import time


def main():
    process_start = time.monotonic()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--protocol', required=True, type=Path)
    parser.add_argument('--case-index', required=True, type=int)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    events = (args.out / 'events.jsonl').open('x')
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from pilot_common import atomic_json, cpu, install_guards, load_registered, sha, validate_contract
    record = {'id': None, 'case_index': args.case_index, 'status': 'NOT_RUN',
        'engineering_class': 'NOT_RUN', 'strict_class': 'NOT_RUN', 'attempts': [],
        'active_stage': 'WORKER_STARTUP'}
    report = {'status': 'STARTED', 'record': record,
        'scope': 'Problem-evidence pilot on exposed dev03_18; exactly N official live rows; no new mechanism, natural label or competitive win.'}
    budget = None
    def save():
        atomic_json(args.out / 'results.json', report)
    def progress():
        atomic_json(args.out / 'progress.json', {
            'active_stage': record.get('active_stage') or 'BETWEEN_STAGES',
            'latest_stage': record.get('latest_stage'),
            'solver_check_active': bool(budget and budget.solver_check_active),
            'solver_check_start_monotonic': budget.solver_check_start_monotonic if budget else None,
            'solver_spent_wall_seconds': budget.solver_wall if budget else 0.0,
            'check_count': budget.check_count if budget else 0,
            'case_index': args.case_index, 'id': record.get('id'), 'updated_monotonic': time.monotonic(),
        })
    def emit(event, rec):
        record['active_stage'] = rec.get('active_stage', record.get('active_stage'))
        if 'latest_stage' in rec:
            record['latest_stage'] = rec['latest_stage']
        progress()
        entry = {'event': event, 'worker_cpu_seconds': cpu(), 'record': rec}
        events.write(json.dumps(entry, ensure_ascii=False, allow_nan=False) + '\n')
        events.flush()
        os.fsync(events.fileno())
        report['last_event'] = {'event': event, 'id': rec.get('id'),
            'attempt': rec.get('attempt'), 'active_stage': rec.get('active_stage')}
        if rec.get('attempt') is not None:
            report['latest_attempt_snapshot'] = rec
        save()
    save()
    progress()
    exit_code = 2
    try:
        install_guards(events, record, process_start)
        protocol, case, slot = load_registered(args.protocol, args.case_index, 'official')
        record.update(id=slot['id'], source_case_id=case['id'], registered_slot=slot,
            source_group_id=case['source_group_id'], source=case['source'],
            original_source_record=case['source_record'], original_sql_sha256=case['original_sql_sha256'],
            schema_sha256=case['schema_sha256'], constraint_sha256=case['constraint_sha256'],
            provenance_eligibility=case['provenance_eligibility'],
            source_exposure=case['exposure'], natural_contract_provenance='BUSINESS_TRUTH_AND_COMPLETENESS_UNVERIFIED',
            status='STARTED', exact_rows={'COURSES': slot['exact_rows']},
            full_C_checker_admission=validate_contract(case))
        report.update(protocol_sha256=sha(args.protocol), input=protocol['input'],
            code_sha256={name: sha(Path(__file__).with_name(name)) for name in (
                'official_boundary_worker.py', 'official_boundary_backend.py',
                'official_contract_admission.py', 'pilot_common.py')},
            registered_task_count=len(protocol['registered_cases']), denominator_unchanged=True,
            budget_policy={key: protocol[key] for key in (
                'worker_cpu_limit_seconds', 'worker_wall_limit_seconds', 'external_rss_limit_bytes',
                'contract_check_timeout_ms', 'query_check_timeout_ms', 'solver_cumulative_wall_limit_seconds',
                'supervisor_solver_stop_seconds', 'maximum_independent_environment_attempts')})
        local_protocol = dict(protocol, exact_rows_per_table=slot['exact_rows'], _out_dir=str(args.out.resolve()))
        from official_boundary_backend import Budget, load_runtime, run_case
        from official_contract_admission import validate_schema_and_contract
        budget = Budget(local_protocol, process_start)
        record['active_stage'] = 'SOURCE_AND_STRUCTURE_ADMISSION'
        emit('STAGE_START', record)
        record['structural_admission'] = validate_schema_and_contract(
            case['source_record']['schema'], case['source_record']['constraint'])
        emit('STRUCTURAL_ADMISSION_COMPLETE', record)
        runtime = load_runtime(local_protocol, budget, emit)
        report['runtime'] = runtime.initialization
        run_case(runtime, case, local_protocol, budget, emit, record)
        report['status'] = 'REGISTERED_EXACT_SHAPE_ATTEMPT_RETURNED'
        exit_code = 0
    except BaseException as exc:
        report.update(status='STOPPED_OR_FAILED', error_type=type(exc).__name__, error=str(exc)[:4000])
        record.update(status='INCONCLUSIVE', engineering_class='INCONCLUSIVE', strict_class='INCONCLUSIVE')
    finally:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        report['worker_usage'] = {'cpu_user_seconds': usage.ru_utime, 'cpu_system_seconds': usage.ru_stime,
            'peak_rss_bytes_macos': usage.ru_maxrss, 'wall_from_main_seconds': time.monotonic() - process_start}
        if budget is not None:
            record['solver_calls'] = budget.solver_calls
            record['solver_cumulative_wall_seconds'] = budget.solver_wall
            record['solver_cumulative_cpu_seconds'] = budget.solver_cpu
        progress()
        save()
        events.close()
        print(json.dumps({'status': report['status'], 'id': record.get('id'),
            'engineering_class': record['engineering_class'], 'strict_class': record['strict_class'],
            'usage': report['worker_usage']}), flush=True)
    os._exit(exit_code)


if __name__ == '__main__':
    main()
