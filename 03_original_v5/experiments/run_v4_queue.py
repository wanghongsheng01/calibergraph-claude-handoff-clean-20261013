"""Sequential registered v4 jobs, retaining every decision/error and unrun slot."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

p=argparse.ArgumentParser(); p.add_argument('--kind',choices=['cost','differential'],required=True)
p.add_argument('--start',type=int,required=True);p.add_argument('--stop',type=int,required=True)
a=p.parse_args(); assert 0 <= a.start < a.stop <= 132
root=Path(__file__).resolve().parent.parent
registration=root/'experiments'/'v4_registration_01'
path=root/'experiments'/('QUEUE_V4_%s_%03d_%03d.json'%(a.kind,a.start,a.stop))
assert not path.exists(), 'Do not overwrite a queue.'
queue={'status':'REGISTERED','kind':a.kind,'full_registered_job_denominator':132,
       'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
       'entries':[{'start':i,'size':min(3,a.stop-i),'status':'NOT_RUN'} for i in range(a.start,a.stop,3)]}
def save():
    tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(queue,indent=2)+'\n');tmp.replace(path)
save()
for entry in queue['entries']:
    out=root/'runs'/('fair_v4_%s_queue_%03d'%(a.kind,entry['start']))
    assert not out.exists()
    entry.update(status='RUNNING',out=str(out));save()
    cmd=[sys.executable,'-B','-I','-S',str(root/'runtime_fair_v4/supervisor.py'),
         '--runtime-lock',str(registration/'runtime_paths_v4.json'),
         '--suite',str(registration/'REGISTERED_SIX_ARM_SUITE.json'),'--out-dir',str(out),
         '--kind',a.kind,'--job-start',str(entry['start']),'--job-limit',str(entry['size'])]
    began=time.monotonic();result=subprocess.run(cmd,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=94)
    entry.update(status='RETURNED',exit_code=result.returncode,wall_seconds=time.monotonic()-began,
                 stdout=result.stdout,stderr=result.stderr)
    report=json.loads((out/'supervisor_report.json').read_text())
    selected=report['jobs'][entry['start']:entry['start']+entry['size']]
    entry['decisions']=[{k:j.get(k) for k in ('case_id','arm','query_index','status','final_decision','stop_reason')} for j in selected]
    save();print(json.dumps({'start':entry['start'],'decisions':entry['decisions']}),flush=True)
    if any(j['status'] in {'NOT_RUN','STARTED'} for j in selected):
        queue['status']='STOPPED_INCOMPLETE_BATCH';save();raise SystemExit(2)
queue['status']='ALL_SELECTED_BATCHES_RETURNED';save()
