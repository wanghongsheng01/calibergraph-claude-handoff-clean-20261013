"""Single-thread, solver-free total 60 s ledger; each frozen attempt is retained."""
from pathlib import Path
import datetime,fcntl,hashlib,json,os,resource,runpy,signal,sys,threading,time,traceback
H=Path(__file__).resolve().parent;LOCK=H.parent/'calibergraph_launch_protocol_v2_20261012_05/runtime/owned.lock'
def main():
    freeze_path=Path(sys.argv[1]).resolve();f=json.loads(freeze_path.read_text());attempt=f['attempt'];prior=sum(json.loads(x.read_text())['elapsed_s'] for x in H.glob('RECEIPT_*.json'));remaining=60-prior
    assert remaining>0
    for rel,sha in f['files_sha256'].items():assert hashlib.sha256((H/rel).read_bytes()).hexdigest()==sha,rel
    for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[k]='1'
    sys.dont_write_bytecode=True
    class Stop(BaseException):pass
    def timeout(*a):raise Stop('TOTAL_EXECUTION_BUDGET')
    def memory(*a):
        if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>256*1024**2:raise Stop('RSS_256_MiB_CAP')
    events=[]
    def audit(event,args):
        if event in ['subprocess.Popen','os.system','os.fork','os.posix_spawn','os.exec','socket.connect','socket.bind']:
            events.append(event);raise RuntimeError('Forbidden event '+event)
    def no_thread(*a,**k):events.append('Thread.start');raise RuntimeError('single-thread guard')
    with LOCK.open() as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert threading.active_count()==1
        load=os.getloadavg();assert load[0]<min(6,os.cpu_count()*.75),load
        assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss<128*1024**2
        with (H/f'STARTED_{attempt}.json').open('x') as out:json.dump({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'freeze_sha256':hashlib.sha256(freeze_path.read_bytes()).hexdigest(),'prior_elapsed_s':prior,'remaining_budget_s':remaining,'loadavg':load,'cpus':os.cpu_count(),'RSS_cap_bytes':256*1024**2,'common_lock':True},out,indent=2)
        oldthread=threading.Thread.start;threading.Thread.start=no_thread;sys.addaudithook(audit)
        signal.signal(signal.SIGALRM,timeout);signal.signal(signal.SIGVTALRM,memory)
        signal.setitimer(signal.ITIMER_REAL,remaining);signal.setitimer(signal.ITIMER_VIRTUAL,.05,.05)
        t=time.monotonic();results=[]
        try:
            for script in f['scripts']:
                try:runpy.run_path(str(H/script),run_name='__main__');results.append({'script':script,'status':'RETURNED'})
                except Exception as e:results.append({'script':script,'status':'ERROR','error':repr(e),'traceback':traceback.format_exc()})
        except BaseException as e:results.append({'status':'STOP','error':repr(e)})
        finally:
            elapsed=time.monotonic()-t;signal.setitimer(signal.ITIMER_REAL,0);signal.setitimer(signal.ITIMER_VIRTUAL,0);threading.Thread.start=oldthread
            receipt={'elapsed_s':elapsed,'cumulative_s':prior+elapsed,'budget_s':60,'results':results,'events':events,'thread_count':threading.active_count(),'RSS_peak_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'solver_calls':0}
            (H/f'RECEIPT_{attempt}.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
if __name__=='__main__':main()
