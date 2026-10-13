"""Complete COUNT units under remaining cumulative 60s budget; preserve closed first batch."""
from pathlib import Path
import datetime,fcntl,hashlib,json,os,resource,runpy,signal,sys,threading,time,traceback
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
LOCK=ROOT/'calibergraph_launch_protocol_v2_20261012_05/runtime/owned.lock'

def main():
    freeze=json.loads((HERE/'COUNT_COMPLETION_FREEZE.json').read_text())
    prior=json.loads((HERE/'BATCH_RESULT.json').read_text())['elapsed_s']
    remaining=60-prior
    assert 0<remaining<60
    for rel,h in freeze['files_sha256'].items():assert hashlib.sha256((HERE/rel).read_bytes()).hexdigest()==h,rel
    assert threading.active_count()==1
    assert signal.getitimer(signal.ITIMER_REAL)==(0.0,0.0)
    events=[];results=[]
    def audit(event,args):
        if event in {'subprocess.Popen','os.system','os.fork','os.posix_spawn','os.exec','socket.connect','socket.bind'}:
            events.append(event);raise RuntimeError('Forbidden subprocess/network: '+event)
    def no_thread(*a,**k):raise RuntimeError('Single-thread batch prohibits Thread.start')
    class Deadline(BaseException):pass
    def timeout(*a):raise Deadline('60 second combined batch budget')
    for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[key]='1'
    with LOCK.open() as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert not (HERE/'COUNT_COMPLETION_STARTED.json').exists()
        load=os.getloadavg();assert load[0]<os.cpu_count(),load
        receipt={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'loadavg':load,'logical_cpus':os.cpu_count(),'self_RSS_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'common_lock_acquired':True,'foreign_process_inspection':False}
        (HERE/'COUNT_COMPLETION_PREFLIGHT.json').write_text(json.dumps(receipt,indent=2)+'\n')
        with (HERE/'COUNT_COMPLETION_STARTED.json').open('x') as f:json.dump({'freeze_sha256':hashlib.sha256((HERE/'COUNT_COMPLETION_FREEZE.json').read_bytes()).hexdigest(),'budget_s':remaining,'single_thread':True,'solver_authorized':False},f,indent=2)
        started=time.monotonic();old_alarm=signal.signal(signal.SIGALRM,timeout)
        old_thread=threading.Thread.start;threading.Thread.start=no_thread
        sys.addaudithook(audit);signal.setitimer(signal.ITIMER_REAL,remaining)
        try:
            for rel in freeze['scripts_in_order']:
                t=time.monotonic()
                try:
                    assert threading.active_count()==1
                    runpy.run_path(str(HERE/rel),run_name='__main__')
                    results.append({'script':rel,'status':'RETURNED','elapsed_s':time.monotonic()-t})
                except Deadline:raise
                except BaseException as error:
                    results.append({'script':rel,'status':'ERROR','error':repr(error),'traceback':traceback.format_exc(),'elapsed_s':time.monotonic()-t})
        except Deadline as error:results.append({'status':'BUDGET_STOP','error':str(error)})
        finally:
            signal.setitimer(signal.ITIMER_REAL,0);signal.signal(signal.SIGALRM,old_alarm);threading.Thread.start=old_thread
            elapsed=time.monotonic()-started
            done={r.get('script') for r in results}
            for rel in freeze['scripts_in_order']:
                if rel not in done:results.append({'script':rel,'status':'NOT_COMPLETED_WITHIN_BUDGET'})
            result={'elapsed_s':elapsed,'budget_s':remaining,'results':results,'forbidden_events':events,'thread_count_at_end':threading.active_count(),'new_solver_calls':0 if not events else 'BLOCKED_ATTEMPT_REVIEW_REQUIRED','self_RSS_peak_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'all_runtime_inside_one_continuous_budget':False,'prior_elapsed_s':prior,'cumulative_execution_elapsed_s':prior+elapsed,'total_execution_budget_s':60}
            (HERE/'COUNT_COMPLETION_RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
            (HERE/'COUNT_COMPLETION_CLOSED.json').write_text(json.dumps({'elapsed_s':elapsed,'no_reentry':True,'science_solver_runs':0,'receipt_sha256':hashlib.sha256((HERE/'COUNT_COMPLETION_RESULT.json').read_bytes()).hexdigest()},indent=2)+'\n')
            print(json.dumps(result))
if __name__=='__main__':main()
