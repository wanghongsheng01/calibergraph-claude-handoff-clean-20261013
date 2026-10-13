"""New fixed-budget admission protocol; no old probe or frozen file is edited."""
from pathlib import Path
import datetime
import hashlib
import json
import os
import re
import resource
import subprocess
import sys
import tempfile
import time

P=Path(__file__).resolve().parents[1]
W=P.parent
BASE=W/'calibergraph_parseval_admission_20261011_03'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    attempt=int(sys.argv[1]);assert 1<=attempt<=2
    protocol=P/'protocols/FIXED_PROTOCOL.json'
    freeze_path=P/f'governance/FREEZE_{attempt:02}.json'
    frozen=json.loads(freeze_path.read_text())
    assert frozen['protocol_sha256']==sha(protocol)
    for e in frozen['files']:assert sha(W/e['path'])==e['sha256'],e['path']
    for n in range(1,attempt):
        old=P/f'runs/admission_{n:02}/RESULT.json'
        assert old.exists(), 'Unknown prior worker outcome: fail closed'
        prior=json.loads(old.read_text())
        assert prior['counters_complete'] and prior['counters']['generation_calls']==0, 'One total generation call; no result-based retry'
        assert prior['status'] in ('PROBE_ERROR','ADMISSION_BLOCKED_LOWERING'), 'No retry of a scientific result'
        receipt=json.loads((old.parent/'LAUNCH_RECEIPT.json').read_text())
        assert receipt['cleanup_status']=='STOPPED'
    seal=json.loads((BASE/'AUTHOR_MANIFEST.json').read_text())
    for e in seal['files']:assert sha(BASE/e['path'])==e['sha256']
    source=json.loads((BASE/'governance/OFFICIAL_SOURCE_LOCK.json').read_text())
    for e in source['files']:assert sha(BASE/'sources_local/parseval_official'/e['path'])==e['sha256']
    dependencies=json.loads((BASE/'governance/DEPENDENCY_ACQUISITION_RECEIPT.json').read_text())
    for package in dependencies['packages']:
        for e in package['extracted_files']:assert sha(BASE/'dependencies_local/site-packages'/e['path'])==e['sha256']
    load=os.getloadavg()
    pressure=subprocess.run(['memory_pressure','-Q'],capture_output=True,text=True,timeout=5)
    match=re.search(r'System-wide memory free percentage: (\d+)%',pressure.stdout)
    observed={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'loadavg':load,'free_percent':int(match.group(1)) if match else None}
    if not match or max(load[:2])>5.5 or int(match.group(1))<25:
        (P/'governance/RESOURCE_GATE_STOP.json').write_text(json.dumps(observed,indent=2)+'\n')
        raise SystemExit('Resource gate failed; no database or worker started')
    with (P/f'ATTEMPT_{attempt:02}.lock').open('x') as f:
        f.write(json.dumps({'protocol_sha256':sha(protocol),'freeze_sha256':sha(freeze_path),'resource':observed})+'\n')
    out=P/f'runs/admission_{attempt:02}';out.mkdir(exist_ok=False)
    runtime=P/f'runtime/attempt_{attempt:02}';runtime.mkdir(parents=True,exist_ok=False)
    pgdata=runtime/'pgdata';socket=Path(tempfile.mkdtemp(prefix='cg-pv04-',dir='/tmp'));socket.chmod(0o700)
    env={'PATH':'/opt/homebrew/bin:/usr/bin:/bin','LANG':'C','LC_ALL':'C','TZ':'UTC','PGPASSFILE':str(P/'runtime/NO_PASSFILE'),
         'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1','VECLIB_MAXIMUM_THREADS':'1'}
    receipt={'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'attempt':attempt,
             'protocol_sha256':sha(protocol),'freeze_sha256':sha(freeze_path),'resource_before':observed,
             'temporary_pgdata':str(pgdata),'temporary_socket':str(socket),'tcp_listen':False,'credential_files_used':False,
             'old_project_read_only':True,'bytecode_cache_read_from_old_project':False,
             'limits':'One nice19 worker,CPU20/21s,wall35s,own RSS512MiB sampling at50ms; no RLIMIT_DATA. PG shared_buffers16MiB/work_mem1MiB/maxconn5. Whole PG RSS unmeasured.'}
    started=False;begin=time.monotonic()
    try:
        with (out/'initdb.log').open('wb') as log:
            subprocess.run(['/opt/homebrew/bin/initdb','-D',str(pgdata),'--username=cg_probe','--auth-local=trust','--auth-host=reject','--encoding=UTF8','--locale=C','--no-instructions'],env=env,stdout=log,stderr=subprocess.STDOUT,timeout=12,check=True)
        opts=f"-k {socket} -p 65433 -c listen_addresses='' -c shared_buffers=16MB -c work_mem=1MB -c max_connections=5 -c max_worker_processes=0 -c max_parallel_workers=0 -c autovacuum=off"
        started=True
        with (out/'pg_ctl.log').open('wb') as log:
            subprocess.run(['/opt/homebrew/bin/pg_ctl','-D',str(pgdata),'-l',str(out/'postgres.log'),'-o',opts,'-w','-t','8','start'],env=env,stdout=log,stderr=subprocess.STDOUT,timeout=10,check=True)
        with (out/'worker.log').open('wb') as log:
            child=subprocess.run(['/opt/homebrew/bin/python3.12','-B','-I','-S',str(P/frozen['worker']),str(out),str(socket)],env=env,stdout=log,stderr=subprocess.STDOUT,timeout=35)
        receipt['worker_exit_code']=child.returncode
    except Exception as e:
        receipt['launcher_error']={'type':type(e).__name__,'message':str(e)}
    finally:
        try:
            if started:
                receipt['stop_attempts']=[]
                for number in (1,2):
                    try:
                        with (out/f'stop_{number}.log').open('wb') as log:
                            stop=subprocess.run(['/opt/homebrew/bin/pg_ctl','-D',str(pgdata),'-m','immediate','-w','-t','5','stop'],env=env,stdout=log,stderr=subprocess.STDOUT,timeout=7)
                        receipt['stop_attempts'].append({'exit_code':stop.returncode})
                        receipt['postgres_stop_exit_code']=stop.returncode
                        if stop.returncode==0 and not (pgdata/'postmaster.pid').exists():break
                    except Exception as e:receipt['stop_attempts'].append({'error_type':type(e).__name__,'message':str(e)})
                receipt['cleanup_status']='STOPPED' if receipt.get('postgres_stop_exit_code')==0 and not (pgdata/'postmaster.pid').exists() else 'BLOCKED_POSSIBLE_OWNED_POSTGRES_ALIVE'
            else:receipt['cleanup_status']='SERVER_NOT_STARTED'
            if receipt['cleanup_status']=='STOPPED':
                for f in socket.iterdir():
                    if f.name.startswith('.s.PGSQL.'):f.unlink()
                socket.rmdir()
        except Exception as e:
            receipt['cleanup_error']={'type':type(e).__name__,'message':str(e)}
            receipt.setdefault('cleanup_status','BLOCKED_CLEANUP_UNVERIFIED')
        finally:
            receipt['elapsed_wall_s']=time.monotonic()-begin
            receipt['resource_after']={'loadavg':os.getloadavg()}
            receipt['child_usage']={'cpu_user_s':resource.getrusage(resource.RUSAGE_CHILDREN).ru_utime,'cpu_system_s':resource.getrusage(resource.RUSAGE_CHILDREN).ru_stime}
            receipt['worker_counters_may_be_partial']=receipt.get('worker_exit_code')!=0
            (out/'LAUNCH_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt))
    if receipt.get('cleanup_status','').startswith('BLOCKED'):raise SystemExit('Owned PG cleanup unresolved: stop all work')

if __name__=='__main__':main()
