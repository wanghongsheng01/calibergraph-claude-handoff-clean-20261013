import argparse,json,subprocess,sys,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--kind',choices=['cost','differential'],required=True);p.add_argument('--start',type=int,required=True);p.add_argument('--stop',type=int,required=True);a=p.parse_args()
root=Path(__file__).resolve().parent.parent
queue=[]
for start in range(a.start,a.stop,3):
 size=min(3,a.stop-start);out=root/'runs'/f'fair_v3_{a.kind}_queue_{start:03d}'
 if out.exists():raise ValueError('refuse overwrite or re-run '+str(out))
 queue.append({'start':start,'size':size,'out':str(out),'status':'NOT_RUN'})
receipt=root/'experiments'/f'QUEUE_{a.kind}_{a.start:03d}_{a.stop:03d}.json'
assert not receipt.exists()
def save():receipt.write_text(json.dumps({'kind':a.kind,'range':[a.start,a.stop],'one_compute_process':True,'jobs':queue},indent=2)+'\n')
save()
for entry in queue:
 cmd=[sys.executable,'-B','-I','-S',str(root/'runtime_fair/supervisor.py'),'--runtime-lock',str(root/'runtime_v3/runtime_paths.json'),'--suite',str(root/'experiments/REGISTERED_STRESS_01.json'),'--out-dir',entry['out'],'--kind',a.kind,'--job-start',str(entry['start']),'--job-limit',str(entry['size'])]
 entry['status']='RUNNING';save();tick=time.monotonic()
 result=subprocess.run(cmd,stdin=subprocess.DEVNULL,timeout=94)
 entry.update(status='RETURNED',exit_code=result.returncode,wall_seconds=time.monotonic()-tick);save()
 print(json.dumps({'queue_kind':a.kind,'completed_start':entry['start'],'exit':result.returncode}),flush=True)
