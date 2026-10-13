"""One frozen registered source group per process; parent must enforce all guards.

python3.12 -B -I -S official_diagnostic_worker.py --protocol FILE --case-index N --out DIR
This file is inert on import. It never enumerates external/reserve inputs.
"""
from pathlib import Path
import argparse, json, os, resource, signal, sys, time


def main():
    process_start = time.monotonic()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--protocol',required=True,type=Path)
    ap.add_argument('--case-index',required=True,type=int)
    ap.add_argument('--out',required=True,type=Path)
    args = ap.parse_args()
    if sys.platform!='darwin' or sys.version_info < (3,12) or not (sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode):
        raise ValueError('REQUIRES_DARWIN_PYTHON312_-B_-I_-S_PARENT_WALL_RSS_GLOBAL_CPU_GUARD')
    args.out.mkdir(parents=True, exist_ok=True)
    events = (args.out/'events.jsonl').open('x')
    record = {'id':None,'case_index':args.case_index,'status':'NOT_RUN','engineering_class':'NOT_RUN',
        'strict_class':'NOT_RUN','attempts':[],'active_stage':'WORKER_STARTUP'}
    report = {'status':'STARTED','record':record,'scope':'Registered input only; exact2 official semantics, no business or cross-dialect gold'}
    def save():
        p = args.out/'results.json'; temp = p.with_suffix('.tmp')
        temp.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)+'\n');temp.replace(p)
    budget = None
    def progress():
        data = {'active_stage':record.get('active_stage') or 'BETWEEN_STAGES','latest_stage':record.get('latest_stage'),
            'solver_check_active':bool(budget and budget.solver_check_active),
            'solver_check_start_monotonic':budget.solver_check_start_monotonic if budget else None,
            'solver_spent_wall_seconds':budget.solver_wall if budget else 0.0,
            'check_count':budget.check_count if budget else 0,
            'case_index':args.case_index,'id':record.get('id'),'updated_monotonic':time.monotonic()}
        p = args.out/'progress.json';temp=p.with_suffix('.tmp')
        temp.write_text(json.dumps(data,allow_nan=False)+'\n');temp.replace(p)
    save()
    progress()
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    resource.setrlimit(resource.RLIMIT_CPU,(4,4))
    def emergency(signum, frame):
        os.write(events.fileno(),json.dumps({'event':'HARD_GUARD_SIGNAL','signal':signum,'active_stage':record.get('active_stage'),'outcome':'INCONCLUSIVE_OR_NOT_RUN'}).encode()+b'\n')
        os._exit(124)
    signal.signal(signal.SIGXCPU,emergency);signal.signal(signal.SIGALRM,emergency)
    signal.pthread_sigmask(signal.SIG_UNBLOCK,{signal.SIGXCPU,signal.SIGALRM})
    signal.setitimer(signal.ITIMER_REAL,5.0)
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    from official_diagnostic_backend import Budget, load_runtime, run_case, sha, objsha, cpu, source_class
    from official_contract_admission import AdmissionError, validate_schema_and_contract
    def emit(event, rec):
        record['active_stage'] = rec.get('active_stage',record.get('active_stage'))
        if 'latest_stage' in rec:
            record['latest_stage'] = rec['latest_stage']
        progress()
        entry = {'event':event,'worker_cpu_seconds':cpu(),'record':rec}
        events.write(json.dumps(entry,ensure_ascii=False,allow_nan=False)+'\n');events.flush();os.fsync(events.fileno())
        # Preserve the initial denominator and the latest phase after every boundary.
        report['last_event'] = {'event':event,'id':rec.get('id'),'attempt':rec.get('attempt'),'active_stage':rec.get('active_stage')}
        if rec.get('attempt') is not None:
            report['latest_attempt_snapshot'] = rec
        save()
    exit_code = 2
    try:
        protocol = json.loads(args.protocol.read_text())
        if protocol['id']!='calibergraph-03-official-diagnostic-v1' or protocol['exact_rows_per_table']!=2:
            raise ValueError('UNREGISTERED_PROTOCOL_OR_BOUND')
        if protocol['worker_cpu_limit_seconds']!=4 or protocol['worker_wall_limit_seconds']!=5 or protocol['solver_cumulative_wall_limit_seconds']!=2:
            raise ValueError('PROTOCOL_BUDGET_MISMATCH')
        if protocol['contract_check_timeout_ms']!=100 or protocol['query_check_timeout_ms']!=800 or protocol['solver_timeout_reserve_seconds']!=.1:
            raise ValueError('SOLVER_STAGE_BUDGET_MISMATCH')
        p = Path(protocol['input']['path'])
        if sha(p)!=protocol['input']['sha256']:
            raise ValueError('REGISTERED_INPUT_HASH_MISMATCH')
        cases = [json.loads(line) for line in p.read_text().splitlines() if line.strip()]
        if not 1<=len(cases)<=32 or len({x['source_group_id'] for x in cases})!=len(cases):
            raise ValueError('DENOMINATOR_OR_UNIQUE_SOURCE_GROUP_MISMATCH')
        if [x['id'] for x in cases]!=protocol['registered_case_ids'] or not 0<=args.case_index<len(cases):
            raise ValueError('UNREGISTERED_CASE_OR_ORDER')
        case = cases[args.case_index]
        src = case.get('source_record',{})
        record.update(id=case['id'],source_group_id=case['source_group_id'],source=case.get('source',{}),
            provenance_class=source_class(case),original_source_record=src,
            provenance_eligibility=case.get('provenance_eligibility'),
            semantic_admission=case.get('semantic_admission',{}),status='STARTED',
            natural_contract_provenance='BUSINESS_TRUTH_AND_COMPLETENESS_UNVERIFIED')
        registered_provenance = case.get('provenance_eligibility',{})
        if not isinstance(registered_provenance,dict) or registered_provenance.get('contract_source') != record['provenance_class']:
            raise ValueError('REGISTRAR_CONTRACT_PROVENANCE_MISMATCH')
        report.update(protocol_sha256=sha(args.protocol),input=protocol['input'],
            code_sha256={name:sha(Path(__file__).with_name(name)) for name in (
                'official_diagnostic_worker.py','official_diagnostic_backend.py','official_contract_admission.py')},
            registered_group_count=len(cases),denominator_unchanged=True)
        save()
        budget = Budget(protocol, process_start)
        record['active_stage'] = 'SOURCE_AND_STRUCTURE_ADMISSION'
        emit('STAGE_START',record)
        if 'constraint' not in src or src.get('constraint') is None or 'schema' not in src:
            record.update(status='RETURNED',engineering_class='CONTRACT_SOURCE_INSUFFICIENT',strict_class='CONTRACT_SOURCE_INSUFFICIENT')
        else:
            if not isinstance(src.get('pair'),list) or len(src['pair'])!=2 or not all(isinstance(q,str) and q.strip() for q in src['pair']):
                raise ValueError('ORIGINAL_PAIR_SOURCE_INSUFFICIENT')
            import hashlib
            sqlhash = [hashlib.sha256(q.encode()).hexdigest() for q in src['pair']]
            if sqlhash != case.get('original_sql_sha256'):
                raise ValueError('ORIGINAL_SQL_HASH_MISMATCH')
            record.update(original_sql_sha256=sqlhash,schema_sha256=objsha(src['schema']),constraint_sha256=objsha(src['constraint']))
            for key in ('schema_sha256','constraint_sha256'):
                if case.get(key) is not None and case[key]!=record[key]:
                    raise ValueError('ORIGINAL_'+key.upper()+'_MISMATCH')
            try:
                record['structural_admission'] = validate_schema_and_contract(src['schema'],src['constraint'])
            except AdmissionError as exc:
                record.update(status='RETURNED',engineering_class=exc.kind,strict_class=exc.kind,
                    failure_stage='SOURCE_AND_STRUCTURE_ADMISSION',reason=exc.reason)
            else:
                emit('STRUCTURAL_ADMISSION_COMPLETE',record)
                rt = load_runtime(protocol,budget,emit)
                report['runtime'] = rt.initialization
                run_case(rt,case,protocol,budget,emit,record)
        report['status'] = 'REGISTERED_GROUP_ATTEMPT_RETURNED'
        exit_code = 0
    except BaseException as exc:
        report.update(status='STOPPED_OR_FAILED',error_type=type(exc).__name__,error=str(exc)[:4000])
        record.update(status='INCONCLUSIVE',engineering_class='INCONCLUSIVE',strict_class='INCONCLUSIVE')
    finally:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        report['worker_usage'] = {'cpu_user_seconds':usage.ru_utime,'cpu_system_seconds':usage.ru_stime,
            'peak_rss_bytes_macos':usage.ru_maxrss,'wall_from_main_seconds':time.monotonic()-process_start}
        if budget is not None:
            record['solver_calls'] = budget.solver_calls
            record['solver_cumulative_wall_seconds'] = budget.solver_wall
            record['solver_cumulative_cpu_seconds'] = budget.solver_cpu
        progress();save();events.close()
        print(json.dumps({'status':report['status'],'id':record.get('id'),
            'engineering_class':record['engineering_class'],'strict_class':record['strict_class'],
            'provenance_class':record.get('provenance_class'),'usage':report['worker_usage']}),flush=True)
    os._exit(exit_code)


if __name__=='__main__':
    main()
