"""Reviewed, once-only sequential launcher; isolated PostgreSQL, no TCP or credentials."""
from pathlib import Path
import datetime
import hashlib
import json
import os
import re
import resource
import shutil
import subprocess
import tempfile
import time

P=Path(__file__).resolve().parents[1]
ROOT=P.parent
PROTO=P/'protocols/PROBE_PROTOCOL.json'
FREEZE=P/'governance/PRE_EXEC_FREEZE.json'
REVIEW=ROOT/'calibergraph_parseval_admission_review_20261011_03/PRE_EXEC_REVIEW.json'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    protocol=json.loads(PROTO.read_text());freeze=json.loads(FREEZE.read_text());review=json.loads(REVIEW.read_text())
    assert review['execution_approved'] is True and review['freeze_sha256']==sha(FREEZE)
    assert protocol['execution_enabled'] is True
    for e in freeze['files']:assert sha(ROOT/e['path'])==e['sha256'],e['path']
    source=json.loads((P/'governance/OFFICIAL_SOURCE_LOCK.json').read_text())
    for e in source['files']:assert sha(P/'sources_local/parseval_official'/e['path'])==e['sha256']
    deps=json.loads((P/'governance/DEPENDENCY_ACQUISITION_RECEIPT.json').read_text())
    for package in deps['packages']:
        for e in package['extracted_files']:assert sha(P/'dependencies_local/site-packages'/e['path'])==e['sha256']
    load=os.getloadavg();pressure=subprocess.run(['memory_pressure','-Q'],capture_output=True,text=True,timeout=5)
    m=re.search(r'System-wide memory free percentage: (\d+)%',pressure.stdout)
    observation={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'loadavg':load,'free_percent':int(m.group(1)) if m else None}
    if not m or min(load[0],load[1])<0 or max(load[:2])>5.5 or int(m.group(1))<25:
        (P/'governance/RESOURCE_GATE_STOP.json').write_text(json.dumps(observation,indent=2)+'\n');raise SystemExit('Resource gate did not pass; no execution')
    lock=P/'ADMISSION_RUN.lock'
    with lock.open('x') as f:f.write(json.dumps({'freeze_sha256':sha(FREEZE),'review_sha256':sha(REVIEW),'resource':observation})+'\n')
    out=P/'runs/admission_01';out.mkdir(parents=True,exist_ok=False)
    runtime=P/'runtime_local';runtime.mkdir(exist_ok=False)
    pgdata=runtime/'pgdata'
    socket=Path(tempfile.mkdtemp(prefix='cg-pv03-',dir='/tmp'));socket.chmod(0o700)
    env={'PATH':'/opt/homebrew/bin:/usr/bin:/bin','LANG':'C','LC_ALL':'C','TZ':'UTC','PGPASSFILE':str(runtime/'NO_PASSFILE'),
         'PYTHONDONTWRITEBYTECODE':'1','OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1','VECLIB_MAXIMUM_THREADS':'1'}
    receipt={'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'freeze_sha256':sha(FREEZE),'review_sha256':sha(REVIEW),'resource_before':observation,
             'one_worker':True,'temporary_pgdata':str(pgdata),'temporary_socket':str(socket),'tcp_listen':False,'credentials_read':False,
             'memory_limit_note':'Worker RLIMIT_DATA 768 MiB; RSS measured for worker only. PostgreSQL shared_buffers16MiB/work_mem1MiB; whole-server RSS is not measured.'}
    start=time.monotonic();started=False
    try:
        with (out/'initdb.log').open('wb') as log:
            subprocess.run(['/opt/homebrew/bin/initdb','-D',str(pgdata),'--username=cg_probe','--auth-local=trust','--auth-host=reject','--encoding=UTF8','--locale=C','--no-instructions'],env=env,stdout=log,stderr=subprocess.STDOUT,timeout=12,check=True)
        opts=f"-k {socket} -p 65433 -c listen_addresses='' -c shared_buffers=16MB -c work_mem=1MB -c max_connections=5 -c max_worker_processes=0 -c max_parallel_workers=0 -c autovacuum=off"
        started=True
        with (out/'pg_ctl.log').open('wb') as log:
            subprocess.run(['/opt/homebrew/bin/pg_ctl','-D',str(pgdata),'-l',str(out/'postgres.log'),'-o',opts,'-w','-t','8','start'],env=env,stdout=log,stderr=subprocess.STDOUT,timeout=10,check=True)
        with (out/'worker.log').open('wb') as log:
            child=subprocess.run(['/opt/homebrew/bin/python3.12','-I','-S',str(P/'implementation/probe_worker.py'),str(out),str(socket)],env=env,stdout=log,stderr=subprocess.STDOUT,timeout=35)
        receipt['worker_exit_code']=child.returncode
    except Exception as e:
        receipt['launcher_error']={'type':type(e).__name__,'message':str(e)}
    finally:
        try:
            if started:
                receipt['stop_attempts']=[]
                # Retry only the same owned cluster's shutdown, never a scientific run.
                for attempt in range(2):
                    try:
                        with (out/('stop_'+str(attempt+1)+'.log')).open('wb') as log:
                            stop=subprocess.run(['/opt/homebrew/bin/pg_ctl','-D',str(pgdata),'-m','immediate','-w','-t','5','stop'],env=env,stdout=log,stderr=subprocess.STDOUT,timeout=7)
                        receipt['stop_attempts'].append({'exit_code':stop.returncode})
                        receipt['postgres_stop_exit_code']=stop.returncode
                        if stop.returncode==0 and not (pgdata/'postmaster.pid').exists():break
                    except Exception as e:
                        receipt['stop_attempts'].append({'error_type':type(e).__name__,'message':str(e)})
                receipt['cleanup_status']='STOPPED' if receipt.get('postgres_stop_exit_code')==0 and not (pgdata/'postmaster.pid').exists() else 'BLOCKED_POSSIBLE_OWNED_POSTGRES_ALIVE'
            else:receipt['cleanup_status']='SERVER_NOT_STARTED'
            # Keep data/logs; remove only the owned socket directory after confirmed shutdown.
            if receipt['cleanup_status']=='STOPPED':
                for f in socket.iterdir():
                    if f.name.startswith('.s.PGSQL.'):f.unlink()
                socket.rmdir()
        except Exception as e:
            receipt['cleanup_error']={'type':type(e).__name__,'message':str(e)}
            receipt.setdefault('cleanup_status','BLOCKED_CLEANUP_UNVERIFIED')
        finally:
            receipt['elapsed_wall_s']=time.monotonic()-start
            receipt['resource_after']={'loadavg':os.getloadavg()}
            receipt['child_usage']=dict(cpu_user_s=resource.getrusage(resource.RUSAGE_CHILDREN).ru_utime,cpu_system_s=resource.getrusage(resource.RUSAGE_CHILDREN).ru_stime)
            receipt['worker_counters_may_be_partial']=receipt.get('worker_exit_code')!=0
            (out/'LAUNCH_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({'receipt':str(out/'LAUNCH_RECEIPT.json'),'worker_exit_code':receipt.get('worker_exit_code'),'stopped':receipt.get('postgres_stop_exit_code'),'elapsed_wall_s':receipt['elapsed_wall_s']}))
    if receipt.get('cleanup_status','').startswith('BLOCKED'):raise SystemExit('Owned PostgreSQL shutdown unconfirmed; stop all further work and resolve cleanup')

if __name__=='__main__':main()
