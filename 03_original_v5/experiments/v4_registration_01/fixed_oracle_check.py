"""Parent-controlled fixed-database v4 oracle-domain controls; no pair oracle."""
import time
START = time.monotonic()
import os
import signal
ACTIVE_PID = None

def hard_stop(signum, frame):
    if ACTIVE_PID is not None:
        try:
            os.kill(ACTIVE_PID, signal.SIGKILL)
        except ProcessLookupError:
            pass
    os.write(2, b'{"status":"FIXED_CONTROL_WALL_STOP","last_effect":"UNKNOWN"}\n')
    os._exit(124)

signal.signal(signal.SIGALRM, hard_stop)
signal.setitimer(signal.ITIMER_REAL, max(.001, 89-(time.monotonic()-START)))
signal.pthread_sigmask(signal.SIG_UNBLOCK, {signal.SIGALRM, signal.SIGXCPU})
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import resource
import subprocess
import sys
import traceback

REG = Path(__file__).resolve().parent
TODAY = REG.parents[1]
FAIR = TODAY / 'runtime_fair_v4'
PINNED_PROGRAMS = {
 'common.py':'035f30492e9fc2f9a46247da0b7a35f5ecc645323f7b3aaec7a1b8a63d1a78e8',
 'worker.py':'5baf3d5719db583abfc58553392ab4e711ee1c37ca8e0bdc1217dabd8f52efc1',
 'supervisor.py':'c4bf0a1500198c3e709de8f2baa8eb6743fdca49e965cd7a9368590894c96479',
 'query_differential.py':'da18141d16395d94c87c4f6b1b9bb1229290b7fd856b5683f5c1d103feffd74e'}

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

class ProcTaskInfo(ctypes.Structure):
    _fields_ = [(n,ctypes.c_uint64) for n in ('virtual_size','resident_size','total_user','total_system','threads_user','threads_system')] + [(n,ctypes.c_int32) for n in ('policy','faults','pageins','cow_faults','messages_sent','messages_received','syscalls_mach','syscalls_unix','csw','threadnum','numrunning','priority')]

def main():
    global ACTIVE_PID
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--stage', choices=('supervisor','worker'), default='supervisor')
    ap.add_argument('--runtime-lock', type=Path, required=True)
    ap.add_argument('--expected-lock-sha256', required=True)
    ap.add_argument('--cases', type=Path, required=True)
    ap.add_argument('--expected-cases-sha256', required=True)
    ap.add_argument('--out-dir', type=Path, required=True)
    ap.add_argument('--case-start', type=int, default=0)
    ap.add_argument('--case-limit', type=int, default=1)
    ap.add_argument('--expected-runner-sha256')
    args=ap.parse_args()
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    if sys.platform!='darwin' or not (sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode):
        raise ValueError('Darwin -B -I -S required')
    if args.stage=='worker':
        resource.setrlimit(resource.RLIMIT_CPU,(14,15))
        signal.signal(signal.SIGXCPU,signal.SIG_DFL)
        signal.signal(signal.SIGALRM,signal.SIG_DFL)
        signal.setitimer(signal.ITIMER_REAL,max(.001,24-(time.monotonic()-START)))
        if digest(__file__)!=args.expected_runner_sha256:
            raise ValueError('runner changed')
    for name,expected in PINNED_PROGRAMS.items():
        if digest(FAIR/name)!=expected:raise ValueError('shared fair program changed: '+name)
    if digest(args.runtime_lock)!=args.expected_lock_sha256 or digest(args.cases)!=args.expected_cases_sha256:
        raise ValueError('registered input changed')
    sys.path.insert(0,str(FAIR))
    import common
    suite=json.loads(args.cases.read_text())
    if suite['case_denominator']!=len(suite['cases']) or suite['query_denominator']!=sum(len(c['pair']) for c in suite['cases']):
        raise ValueError('denominator registration mismatch')
    if args.case_start<0 or args.case_limit<1 or args.case_start+args.case_limit>len(suite['cases']):
        raise ValueError('invalid case range')
    if args.stage=='worker':
        case=suite['cases'][args.case_start]
        report={'status':'NOT_RUN','id':case['id'],'input':case,'native_load':'NOT_RUN','environment_import':'NOT_RUN',
                'queries':[{'query_index':i,'status':'NOT_RUN'} for i in range(len(case['pair']))],
                'interpretation':'Fixed-control expectation checks are not algorithm successes or performance wins.',
                'runtime_lock_sha256':args.expected_lock_sha256,'cases_sha256':args.expected_cases_sha256}
        output=args.out_dir/'worker_report.json'
        def checkpoint(phase):
            report['phase']=phase
            report['resources']={'wall_seconds':time.monotonic()-START,'cpu_seconds':common.cpu_seconds(),'maxrss_bytes_darwin':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
            common.save(output,report)
        checkpoint('INPUT_REGISTERED')
        try:
            lock=common.verify_lock(args.runtime_lock,args.expected_lock_sha256)
            library,z3,constants,Environment,kernel=common.load_runtime(lock,checkpoint,report)
            common.ensure_raw_frontend(case,kernel)
            env=common.new_env(case,Environment,constants)
            report['actual_verifier_semantics']=common.verifier_semantics(env,lock)
            facts,contract=common.guard(env,z3,constants,START)
            report['contract_guard']=contract
            if contract['consistency']!='sat' or contract['any_base_row_deleted']!='unsat':
                raise ValueError('complete satisfiable exact-row contract not established')
            database=case['point_database']
            if set(database)!=set(case['schema']):raise ValueError('fixed database omitted a table')
            pinned=common.solver(z3,constants,START,maximum_ms=1000)
            pinned.add(*facts)
            for table,fields in case['schema'].items():
                concrete=database[table]
                if len(concrete)!=case['exact_rows'][table]:raise ValueError('fixed cardinality mismatch')
                for row,values in zip(env.base_databases[table],concrete):
                    if len(values)!=len(fields):raise ValueError('fixed row width mismatch')
                    for attr,value in zip(env.base_databases[table].attributes,values):
                        if value is None:pinned.add(attr.NULL(row.SORT))
                        else:
                            if type(value) is not int:raise ValueError('fixed physical cell is not an integer')
                            pinned.add(constants.Not(attr.NULL(row.SORT)),attr.VALUE(row.SORT)==constants.IntVal(str(value)))
            report['fixed_database_contract_check']='ATTEMPTED_EFFECT_UNKNOWN'
            checkpoint('FIXED_DATABASE_CONTRACT_SAT_ATTEMPT')
            report['fixed_database_contract_check']=str(pinned.check())
            if report['fixed_database_contract_check']!='sat':
                raise ValueError('registered fixed database not established to satisfy all facts/ICs')
            for index,sql in enumerate(case['pair']):
                slot=report['queries'][index]
                slot.update(status='ATTEMPTED_EFFECT_UNKNOWN',original_sql=sql)
                checkpoint('FIXED_QUERY_ORACLE_ATTEMPT')
                answer=common.guarded_replay(case,[sql],database,env,kernel)
                slot.update(status=answer['status'],result=answer)
                actual_domain=answer['domain_audits'][0]['status']
                slot['expected_domain']=case['expected_domain'][index]
                matched=actual_domain==slot['expected_domain']
                if slot['expected_domain']=='SAFE_FOR_SQLITE_INT64':
                    matched=matched and answer['status']=='REPLAYED_WITHIN_INT64_DOMAIN'
                    expected=case.get('point_expected_relations')
                    relation=expected[index] if expected is not None else case.get('oracle_expectation',{}).get('safe_query_sqlite_relations',{}).get(str(index))
                    if relation is not None:
                        slot['analytical_sqlite_relation']=relation
                        observed=answer['sqlite'].get('relations',[None])[0]
                        matched=matched and json.loads(json.dumps(observed))==relation
                else:
                    matched=matched and answer['status']=='UNKNOWN_ORACLE_DOMAIN' and answer['sqlite']['status']=='NOT_RUN_ORACLE_DOMAIN_UNPROVED'
                slot['control_expectation_match']=matched
                checkpoint('FIXED_QUERY_ORACLE_RETURNED')
            env.__exit__(None,None,None)
            report['status']='COMPLETE'
            report['control_expectation_match']=all(q['control_expectation_match'] for q in report['queries'])
            checkpoint('FINAL')
            os._exit(0 if report['control_expectation_match'] else 2)
        except BaseException as exc:
            report.update(status='ERROR_OR_BLOCKED',error_type=type(exc).__name__,reason=str(exc),traceback=traceback.format_exc())
            checkpoint('ERROR');os._exit(2)
    if args.out_dir.exists() or not args.out_dir.resolve().is_relative_to(TODAY):raise ValueError('new result dir under today required')
    args.out_dir.mkdir(parents=True)
    jobs=[{'case_index':i,'id':c['id'],'status':'NOT_RUN','queries':[{'query_index':j,'status':'NOT_RUN'} for j in range(len(c['pair']))]} for i,c in enumerate(suite['cases'])]
    report={'status':'RUNNING','case_denominator':suite['case_denominator'],'query_denominator':suite['query_denominator'],
            'selected_start':args.case_start,'selected_limit':args.case_limit,'cases':jobs,'runner_sha256':digest(__file__),
            'runtime_lock_sha256':args.expected_lock_sha256,'cases_sha256':args.expected_cases_sha256,
            'limits':{'cpu_soft_hard':[14,15],'child_wall':24,'parent_child_wall':25,'total_wall':89,'rss_soft_bytes':1024**3,'solver_threads':1},
            'no_pair_oracle':'Only complete contract + pinned fixed DB SAT checks; never solve query-pair equivalence.'}
    output=args.out_dir/'supervisor_report.json';common.save(args.out_dir/'initial_not_run.json',report);common.save(output,report)
    libc=ctypes.CDLL(None);probe=libc.proc_pidinfo
    probe.argtypes=[ctypes.c_int,ctypes.c_int,ctypes.c_uint64,ctypes.c_void_p,ctypes.c_int];probe.restype=ctypes.c_int
    if ctypes.sizeof(ProcTaskInfo)!=96:raise ValueError('task info layout mismatch')
    child_env={'PATH':'/usr/bin:/bin','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','VECLIB_MAXIMUM_THREADS':'1'}
    for index in range(args.case_start,args.case_start+args.case_limit):
        job=jobs[index]
        if time.monotonic()-START>=86:job['not_run_reason']='TOTAL_BUDGET';continue
        jobdir=args.out_dir/f'case_{index:03d}';jobdir.mkdir()
        cmd=[sys.executable,'-B','-I','-S',str(Path(__file__).resolve()),'--stage','worker','--runtime-lock',str(args.runtime_lock.resolve()),'--expected-lock-sha256',args.expected_lock_sha256,'--cases',str(args.cases.resolve()),'--expected-cases-sha256',args.expected_cases_sha256,'--out-dir',str(jobdir.resolve()),'--case-start',str(index),'--case-limit','1','--expected-runner-sha256',report['runner_sha256']]
        job.update(status='STARTED',sampled_peak_rss_bytes=0,sampled_max_threads=0)
        common.save(output,report);began=time.monotonic();before=resource.getrusage(resource.RUSAGE_CHILDREN)
        with (jobdir/'stdout.log').open('wb') as out,(jobdir/'stderr.log').open('wb') as err:
            child=subprocess.Popen(cmd,cwd=jobdir,env=child_env,stdout=out,stderr=err,stdin=subprocess.DEVNULL,close_fds=True);ACTIVE_PID=child.pid
            try:
                while child.poll() is None:
                    if time.monotonic()-began>=25 or time.monotonic()-START>=88:job['stop_reason']='WALL_LIMIT';child.kill();break
                    info=ProcTaskInfo();count=probe(child.pid,4,0,ctypes.byref(info),ctypes.sizeof(info))
                    if count!=ctypes.sizeof(info):
                        if child.poll() is None:job['stop_reason']='RSS_OBSERVATION_UNAVAILABLE';child.kill()
                        break
                    job['sampled_peak_rss_bytes']=max(job['sampled_peak_rss_bytes'],int(info.resident_size));job['sampled_max_threads']=max(job['sampled_max_threads'],int(info.threadnum))
                    if info.resident_size>=1024**3:job['stop_reason']='RSS_SOFT_LIMIT';child.kill();break
                    time.sleep(.1)
                job['exit_code']=child.wait(timeout=1)
            finally:
                if child.poll() is None:child.kill();child.wait(timeout=1)
                ACTIVE_PID=None
        after=resource.getrusage(resource.RUSAGE_CHILDREN)
        job.update(status='RESOURCE_STOP' if 'stop_reason' in job else 'PROCESS_EXITED',full_wall_seconds=time.monotonic()-began,full_cpu_seconds=after.ru_utime+after.ru_stime-before.ru_utime-before.ru_stime)
        worker=jobdir/'worker_report.json'
        if worker.exists():
            job['worker']=json.loads(worker.read_text());job['queries']=job['worker']['queries'];job['worker_sha256']=digest(worker)
            job['control_expectation_match']=job['exit_code']==0 and job['worker'].get('control_expectation_match',False)
        common.save(output,report)
    report['status']='SELECTED_FIXED_CONTROLS_AS_EXPECTED' if all(j.get('control_expectation_match') for j in jobs[args.case_start:args.case_start+args.case_limit]) else 'FIXED_CONTROLS_WITH_FAILURES_OR_NOT_RUN'
    common.save(output,report);print(json.dumps({'status':report['status'],'report':str(output)}),flush=True)
    os._exit(0 if report['status']=='SELECTED_FIXED_CONTROLS_AS_EXPECTED' else 2)

if __name__=='__main__':main()
