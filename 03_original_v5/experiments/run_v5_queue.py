"""Run frozen v5 jobs serially and preserve every selected failure/unknown."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

p=argparse.ArgumentParser()
p.add_argument('--kind',choices=['cost','differential'],required=True)
p.add_argument('--start',type=int,required=True)
p.add_argument('--stop',type=int,required=True)
p.add_argument('--mode',choices=['main','spotit'],default='main')
p.add_argument('--runtime-lock-sha256',required=True)
p.add_argument('--suite-sha256',required=True)
a=p.parse_args()
root=Path(__file__).resolve().parent.parent
registration=root/'experiments/v5_registration_01'
suite_path=registration/'REGISTERED_SIX_ARM_SUITE.json'
lock=registration/('runtime_paths_v5.json' if a.mode=='main' else 'spotit_engine_runtime_paths_v5.json')
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
assert sha(suite_path)==a.suite_sha256 and sha(lock)==a.runtime_lock_sha256
suite=json.loads(suite_path.read_text())
total=len(suite['cases'])*6
assert 0 <= a.start < a.stop <= total
if a.mode=='spotit':
    assert a.kind=='cost'
    allowed={6*i+c['arm_order'].index('official') for i,c in enumerate(suite['cases'])}
    batches=[(i,1) for i in range(a.start,a.stop) if i in allowed]
else:
    batches=[(i,min(3,a.stop-i)) for i in range(a.start,a.stop,3)]
path=root/'experiments'/f'QUEUE_V5_{a.mode}_{a.kind}_{a.start:03d}_{a.stop:03d}.json'
assert not path.exists(), 'Never overwrite a queue.'
queue={'status':'REGISTERED','kind':a.kind,'mode':a.mode,
       'full_registered_job_denominator':total,'selected_job_denominator':sum(n for _,n in batches),
       'runtime_lock_sha256':a.runtime_lock_sha256,'suite_sha256':a.suite_sha256,
       'script_sha256':sha(Path(__file__)),
       'entries':[{'start':i,'size':n,'status':'NOT_RUN'} for i,n in batches]}
def save():
    tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(queue,indent=2)+'\n');tmp.replace(path)
save()
for entry in queue['entries']:
    out=root/'runs'/f"fair_v5_{a.mode}_{a.kind}_{entry['start']:03d}_01"
    assert not out.exists()
    cmd=[sys.executable,'-B','-I','-S',str(root/'runtime_fair_v5/supervisor.py'),
         '--runtime-lock',str(lock),'--suite',str(suite_path),'--out-dir',str(out),
         '--kind',a.kind,'--job-start',str(entry['start']),'--job-limit',str(entry['size'])]
    entry.update(status='RUNNING',out=str(out),command=cmd);save()
    began=time.monotonic()
    try:
        result=subprocess.run(cmd,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=94)
    except subprocess.TimeoutExpired:
        entry.update(status='QUEUE_TIMEOUT_EFFECT_UNKNOWN');queue['status']='STOPPED';save();raise
    entry.update(status='RETURNED',exit_code=result.returncode,wall_seconds=time.monotonic()-began,
                 stdout=result.stdout,stderr=result.stderr)
    report=json.loads((out/'supervisor_report.json').read_text())
    selected=report['jobs'][entry['start']:entry['start']+entry['size']]
    entry['decisions']=[{k:j.get(k) for k in ('case_id','arm','query_index','status','final_decision','stop_reason','valid_completed_result')} for j in selected]
    save();print(json.dumps({'start':entry['start'],'decisions':entry['decisions']}),flush=True)
    if any(j['status'] in {'NOT_RUN','STARTED'} for j in selected):
        queue['status']='STOPPED_INCOMPLETE_BATCH';save();raise SystemExit(2)
queue['status']='ALL_SELECTED_BATCHES_RETURNED';save()
