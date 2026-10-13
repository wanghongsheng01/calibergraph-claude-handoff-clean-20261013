"""One 60-second batch; broker owns every worker and every native Z3 Popen handle."""
import array
import fcntl
import hashlib
import json
import os
from pathlib import Path
import select
import socket
import subprocess
import sys
import time

from owned_processes import OwnedCase,Stopped

HERE=Path(__file__).resolve().parent
PYTHON='/opt/homebrew/bin/python3.12'
LOCK=HERE.parent/'calibergraph_launch_protocol_v2_20261012_05/runtime/owned.lock'


def run(validation=False):
    freeze=json.loads((HERE/'FREEZE.json').read_text())
    for rel,digest in freeze['files_sha256'].items():
        assert hashlib.sha256((HERE/rel).read_bytes()).hexdigest()==digest,rel
    assert freeze['authorization']['internal_limit_instead_of_external_RSS_approved'] is True
    with LOCK.open('r') as lock:
        fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        out=HERE/('broker_validation_02' if validation else 'science_run_01')
        out.mkdir(exist_ok=False)
        if not validation:
            with (HERE/'ATTEMPT_STARTED.json').open('x') as f:
                json.dump({'freeze_sha256':hashlib.sha256((HERE/'FREEZE.json').read_bytes()).hexdigest(),
                           'monotonic':time.monotonic(),'no_retries':True},f)
                f.flush();os.fsync(f.fileno())
        slots=[('fixture','fixture')] if validation else [tuple(s) for s in freeze['slots']]
        wall=5 if validation else 60
        records=[];started=time.monotonic();deadline=started+wall
        guard=OwnedCase(wall)
        try:
            with guard:
                for case_id,mode in slots:
                    guard.checkpoint()
                    slot=out/(case_id+'_'+mode);slot.mkdir()
                    parent,child=socket.socketpair(socket.AF_UNIX,socket.SOCK_DGRAM)
                    env={'PATH':'/usr/bin:/bin','LANG':'C','LC_ALL':'C','TZ':'UTC','PYTHONHASHSEED':'0',
                         'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1',
                         'VECLIB_MAXIMUM_THREADS':'1'}
                    handles_before=len(guard.handles);t=time.monotonic();launches=[]
                    try:
                        with (slot/'stdout.txt').open('wb') as stdout,(slot/'stderr.txt').open('wb') as stderr:
                            worker=guard.spawn([PYTHON,'-S','-B',str(HERE/'slot_worker.py'),case_id,mode,
                                               str(child.fileno()),str(slot),str(deadline)],
                                              pass_fds=(child.fileno(),),stdout=stdout,stderr=stderr,env=env)
                        child.close()
                        while worker.poll() is None:
                            guard.checkpoint()
                            ready,_,_=select.select([parent],[],[],.01)
                            if not ready:continue
                            try:
                                message=parent.recv(4096)
                            except ConnectionResetError:
                                worker.wait(timeout=1)
                                break
                            if not message:
                                worker.wait(timeout=1)
                                break
                            request=json.loads(message)
                            expected=['z3','-version'] if validation else ['z3','--in','-T:3']
                            if request['op']!='spawn_z3' or request['argv']!=expected:
                                parent.send(json.dumps({'ok':False,'error':'non-frozen argv'}).encode());continue
                            args=[str(HERE/'native_local/z3'),*expected[1:],'-memory:512']
                            with (slot/f'z3_{len(launches)}_stderr.txt').open('wb') as stderr:
                                z3=guard.spawn(args,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=stderr,env=env)
                            launches.append({'pid_for_logging_only':z3.pid,'args':args,'handle_index':len(guard.handles)-1})
                            fds=array.array('i',[z3.stdin.fileno(),z3.stdout.fileno()])
                            parent.sendmsg([json.dumps({'ok':True}).encode()],[(socket.SOL_SOCKET,socket.SCM_RIGHTS,fds)])
                        worker.wait(timeout=1)
                    finally:
                        parent.close();child.close()
                        # No other slot is alive. All created handles are retained by guard.
                        guard.cleanup()
                    result_path=slot/'RESULT.json'
                    result=json.loads(result_path.read_text()) if result_path.exists() else {'status':'WORKER_EXIT_WITHOUT_RESULT'}
                    errors='\n'.join(p.read_text() for p in slot.glob('z3_*_stderr.txt'))
                    if 'out of memory' in errors.lower():result['controller_classification']='Z3_INTERNAL_MEMORY_LIMIT'
                    record={'case':case_id,'mode':mode,'status':result['status'],'wall_elapsed_s':time.monotonic()-t,
                            'native_launches':launches,'worker_returncode':worker.returncode,
                            'all_slot_handles_reaped':all(p.returncode is not None for p in guard.handles[handles_before:]),
                            'result_path':str(result_path.relative_to(HERE))}
                    records.append(record);(slot/'CONTROLLER.json').write_text(json.dumps(record,indent=2)+'\n')
        except Stopped as error:
            records.append({'status':'BATCH_STOP','reason':str(error)})
        finally:
            done={(r.get('case'),r.get('mode')) for r in records}
            for case_id,mode in slots:
                if (case_id,mode) not in done:
                    records.append({'case':case_id,'mode':mode,'status':'NOT_COMPLETED_BATCH_CUTOFF'})
            receipt={'validation_only':validation,'wall_budget_s':wall,'elapsed_s':time.monotonic()-started,
                     'records':records,'guard':guard.receipt(),'science_attempts':0 if validation else len(slots),
                     'memory_contract':'512 MiB native allocator per Z3, own Python sampling; no aggregate RSS guarantee'}
            (out/'BATCH_RESULT.json').write_text(json.dumps(receipt,indent=2)+'\n')
        print(json.dumps({'elapsed_s':receipt['elapsed_s'],'all_reaped':receipt['guard']['all_reaped'],
                          'slots':[{'case':r.get('case'),'mode':r.get('mode'),'status':r['status']} for r in records]}))


if __name__=='__main__':run('--validate' in sys.argv)
