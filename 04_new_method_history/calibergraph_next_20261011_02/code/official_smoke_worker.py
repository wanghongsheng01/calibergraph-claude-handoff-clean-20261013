"""Six explicit development pairs only. Parent must enforce RSS and hard wall time.

No solver/parser work is performed at import. Use python3 -B -I -S SCRIPT
--protocol .../protocols/official_smoke.json --out NEW_RUN_DIRECTORY.
"""
from pathlib import Path
from collections import Counter
import argparse, hashlib, json, os, resource, signal, sys, time


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--protocol',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args()
    if not (sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode) or sys.platform!='darwin':
        raise ValueError('REQUIRES_DARWIN_-B_-I_-S_AND_PARENT_RSS_AND_WALL_GUARD')
    args.out.mkdir(parents=True,exist_ok=True)
    event_path=args.out/'official_smoke_events.jsonl'
    event_stream=event_path.open('x')
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    resource.setrlimit(resource.RLIMIT_CPU,(9,10))
    def emergency(signum,frame):
        os.write(event_stream.fileno(),json.dumps({'event':'HARD_GUARD_STOP','signal':signum,'effects':'UNKNOWN_UNFINISHED'}).encode()+b'\n')
        os._exit(124)
    signal.signal(signal.SIGXCPU,emergency)
    signal.signal(signal.SIGALRM,emergency)
    signal.pthread_sigmask(signal.SIG_UNBLOCK,{signal.SIGXCPU,signal.SIGALRM})
    signal.setitimer(signal.ITIMER_REAL,25.0)
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    from official_smoke_backend import Budget, BudgetStop, load_runtime, run_case, sha, cpu
    protocol=json.loads(args.protocol.read_text())
    if protocol['id']!='calibergraph-02-official-smoke-v1' or protocol['case_ids']!=['dev_01','dev_02','dev_03','dev_04','dev_05','dev_06']:
        raise ValueError('UNREGISTERED_PROTOCOL_OR_CASE_LIST')
    data=Path(protocol['input']['path'])
    if sha(data)!=protocol['input']['sha256']:
        raise ValueError('REGISTERED_INPUT_HASH_MISMATCH')
    cases=[json.loads(line) for line in data.read_text().splitlines()]
    if [c['id'] for c in cases]!=protocol['case_ids']:
        raise ValueError('INPUT_ORDER_OR_DENOMINATOR_MISMATCH')
    report={'protocol_id':protocol['id'],'protocol_sha256':sha(args.protocol),
       'worker_sha256':sha(Path(__file__)),'backend_sha256':sha(Path(__file__).with_name('official_smoke_backend.py')),
       'input':protocol['input'],'status':'STARTED','denominator':{'pairs':6,'query_slots':12},
       'scope':protocol['scope'],'records':[{'id':c['id'],'status':'NOT_RUN'} for c in cases]}
    def save():
        dst=args.out/'official_smoke_report.json'
        tmp=dst.with_suffix('.tmp')
        tmp.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');tmp.replace(dst)
    def emit(event,rec):
        entry={'event':event,'id':rec['id'],'record':rec,'worker_cpu_seconds':cpu()}
        event_stream.write(json.dumps(entry,ensure_ascii=False,allow_nan=False)+'\n');event_stream.flush()
        os.fsync(event_stream.fileno())
    save()
    budget=Budget(cpu_limit=protocol['worker_cpu_limit_seconds'],wall_limit=protocol['worker_wall_limit_seconds'])
    try:
        rt=load_runtime(protocol,budget,emit)
        report['runtime']=rt.initialization
        for i,case in enumerate(cases):
            budget.check()
            report['records'][i]=run_case(rt,case,protocol,budget,emit)
            save()
            if report['records'][i]['status']=='RESOURCE_STOP':
                raise BudgetStop(report['records'][i].get('error','RESOURCE_STOP'))
        report['status']='ALL_SIX_ATTEMPTS_RETURNED'
    except BaseException as exc:
        report.update(status='STOPPED_OR_FAILED_REMAINDER_NOT_RUN',error_type=type(exc).__name__,error=str(exc)[:4000])
    finally:
        usage=resource.getrusage(resource.RUSAGE_SELF)
        report['worker_usage']={'cpu_user_seconds':usage.ru_utime,'cpu_system_seconds':usage.ru_stime,
            'peak_rss_bytes_macos':usage.ru_maxrss,'wall_seconds':time.monotonic()-budget.start_wall}
        report['status_counts']=dict(Counter(x['status'] for x in report['records']))
        report['effective_verdict_counts']=dict(Counter(x.get('effective_verdict','NOT_RUN') for x in report['records']))
        save();event_stream.close()
        print(json.dumps({'status':report['status'],'status_counts':report['status_counts'],
                          'effective_verdict_counts':report['effective_verdict_counts'],'usage':report['worker_usage']}),flush=True)
    sys.stdout.flush();sys.stderr.flush()
    os._exit(0 if report['status']=='ALL_SIX_ATTEMPTS_RETURNED' else 2)


if __name__=='__main__':
    main()
