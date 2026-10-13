"""Serial, bounded local experiment guard. Never controls any other task."""
import argparse, datetime, fcntl, hashlib, json, os, re, resource
import signal, subprocess, sys, time
from pathlib import Path

def digest(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def probe():
    p = subprocess.run(['/usr/bin/memory_pressure', '-Q'], capture_output=True, text=True, timeout=5)
    v = subprocess.run(['/usr/bin/vm_stat'], capture_output=True, text=True, timeout=5)
    if p.returncode or v.returncode:
        raise RuntimeError('RESOURCE_OBSERVATION_UNAVAILABLE')
    m = re.search(r'System-wide memory free percentage:\s+(\d+)%', p.stdout)
    if not m:
        raise RuntimeError('MEMORY_PRESSURE_OUTPUT_UNKNOWN')
    return {'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'load':list(os.getloadavg()), 'memory_available_percentage':int(m.group(1)),
            'memory_pressure_output':p.stdout, 'vm_stat_output':v.stdout}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--freeze',required=True,type=Path)
    ap.add_argument('--protocol',required=True,type=Path)
    ap.add_argument('--out',required=True,type=Path)
    ap.add_argument('worker',type=Path)
    a=ap.parse_args(); root=Path(__file__).resolve().parents[1]
    out=a.out.resolve()
    if not out.is_relative_to(root/'runs') or out.exists():
        raise ValueError('FRESH_OUTPUT_DIRECTORY_REQUIRED')
    out.mkdir(parents=True)
    policy=json.loads((root/'governance/RESOURCE_POLICY_V2.json').read_text())
    receipt={'status':'PRECHECK','supervisor_sha256':digest(__file__),
             'freeze_sha256':digest(a.freeze),'protocol_sha256':digest(a.protocol),
             'worker':str(a.worker.resolve()),'resource_policy':policy,'sampled_peak_rss_bytes':0,'observations':0}
    def save():
        (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    lock=(root/'runs/.single_worker.lock').open('a')
    try:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        for item in json.loads(a.freeze.read_text())['files']:
            if digest(item['path'])!=item['sha256']:
                raise ValueError('FREEZE_MISMATCH: '+item['path'])
        receipt['preflight']=probe()
    except Exception as exc:
        receipt.update(status='NOT_RUN_PRECHECK_FAILED',error=str(exc));save();return 2
    if receipt['preflight']['load'][0]>policy['max_1min_load'] or receipt['preflight']['memory_available_percentage']<policy['min_memory_available_percentage']:
        receipt['status']='NOT_RUN_RESOURCE_GATE';save();return 2
    env=os.environ.copy()
    env.update({k:'1' for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']})
    env['PYTHONDONTWRITEBYTECODE']='1'
    def setup():
        os.nice(15)
        resource.setrlimit(resource.RLIMIT_CPU,(9,10))
        resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    start=time.monotonic();before=resource.getrusage(resource.RUSAGE_CHILDREN)
    with (out/'stdout.log').open('w') as so,(out/'stderr.log').open('w') as se:
        p=subprocess.Popen([sys.executable,'-B','-I','-S',str(a.worker.resolve()),'--protocol',str(a.protocol.resolve()),'--out',str(out)],
                           cwd=root,env=env,stdout=so,stderr=se,preexec_fn=setup,start_new_session=True)
        stop=None
        try:
            receipt.update(status='RUNNING',pid=p.pid);save()
            while p.poll() is None:
                if time.monotonic()-start>policy['max_wall_seconds']:
                    stop='STOP_WALL_LIMIT';break
                remaining=policy['max_wall_seconds']-(time.monotonic()-start)
                sample=subprocess.run(['/bin/ps','-p',str(p.pid),'-o','rss='],capture_output=True,text=True,timeout=max(.001,min(.5,remaining)))
                if sample.returncode==0 and sample.stdout.strip():
                    rss=int(sample.stdout.strip())*1024
                    receipt['observations']+=1
                    receipt['sampled_peak_rss_bytes']=max(receipt['sampled_peak_rss_bytes'],rss)
                    if rss>policy['max_rss_bytes']:stop='STOP_RSS_LIMIT'
                elif p.poll() is None:stop='STOP_UNOBSERVABLE'
                if stop:break
                time.sleep(.05)
        except BaseException as exc:
            stop='STOP_UNOBSERVABLE'
            receipt['monitor_error']=type(exc).__name__+': '+str(exc)
        finally:
            if p.poll() is None:
                # All monitor failures and deadlines stop only this owned group.
                try:os.killpg(p.pid,signal.SIGKILL)
                except ProcessLookupError:pass
            code=p.wait()
    after=resource.getrusage(resource.RUSAGE_CHILDREN)
    receipt.update(status=stop or ('RETURNED' if code==0 else 'WORKER_FAILED'),worker_exit_code=code,
                   wall_seconds=time.monotonic()-start,
                   child_cpu_user_seconds_including_ps=after.ru_utime-before.ru_utime,
                   child_cpu_system_seconds_including_ps=after.ru_stime-before.ru_stime,
                   monitor_note='RSS sampled every 50ms, not a hard allocation cap. CPU accounting includes ps. No other process modified.')
    try:receipt['postflight']=probe()
    except Exception as exc:receipt['postflight_error']=str(exc)
    save();print(json.dumps({k:v for k,v in receipt.items() if k not in ['preflight','postflight','resource_policy']}))
    return 0 if receipt['status']=='RETURNED' else 2

if __name__=='__main__':raise SystemExit(main())
