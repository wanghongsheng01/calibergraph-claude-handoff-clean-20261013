"""Root-owned sequential execution of frozen controls and applicable engine baseline."""
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parent.parent
REG=ROOT/'experiments/v4_registration_01'
OUT=ROOT/'experiments/QUEUE_FIXED_AND_SPOTIT_V4.json'
assert not OUT.exists()
fixed=[{'kind':'fixed','index':i,'limit':2,'status':'NOT_RUN'} for i in [10,0,2,4,6]]
spotit=[{'kind':'spotit','index':i,'limit':1,'status':'NOT_RUN'} for i in [0,11,16,21,26,31,36,47,52,57,62,67,72,83,88,93,98,103,108,119,124,129]]
queue={'status':'REGISTERED','fixed_previous_completed_indices':[8,9],
       'fixed_case_denominator':12,'fixed_query_denominator':21,
       'spotit_selected_official_denominator':22,'spotit_full_registered_slot_denominator':132,
       'jobs':fixed+spotit}
def save():
    p=OUT.with_suffix('.tmp');p.write_text(json.dumps(queue,indent=2)+'\n');p.replace(OUT)
save()
for job in queue['jobs']:
    i=job['index'];job['status']='RUNNING';save()
    if job['kind']=='fixed':
        out=ROOT/'runs'/('fixed_v4_%03d_01'%i)
        cmd=[sys.executable,'-B','-I','-S',str(REG/'fixed_oracle_check.py'),
             '--runtime-lock',str(REG/'runtime_paths_v4.json'),'--expected-lock-sha256','29220d333a6a3f9812ab2c24aecd7877f7cf5c9e919e80b612f880bf1dc92f1f',
             '--cases',str(REG/'REGISTERED_FIXED_DATABASE_ORACLES.json'),'--expected-cases-sha256','a664a9d74b2ee4b3845edeb6a396a56b0942b58d601b9b2f28bad7e45898246e',
             '--out-dir',str(out),'--case-start',str(i),'--case-limit','2']
    else:
        out=ROOT/'runs'/('spotit_v4_official_%03d_01'%i)
        cmd=[sys.executable,'-B','-I','-S',str(ROOT/'runtime_fair_v4/supervisor.py'),
             '--runtime-lock',str(REG/'spotit_engine_runtime_paths_v4.json'),
             '--suite',str(REG/'REGISTERED_SIX_ARM_SUITE.json'),'--out-dir',str(out),
             '--kind','cost','--job-start',str(i),'--job-limit','1']
    assert not out.exists()
    began=time.monotonic()
    result=subprocess.run(cmd,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=94)
    job.update(status='RETURNED',exit_code=result.returncode,wall_seconds=time.monotonic()-began,
               stdout=result.stdout,stderr=result.stderr,out=str(out))
    report=json.loads((out/'supervisor_report.json').read_text())
    if job['kind']=='fixed':
        selected=report['cases'][i:i+2]
        job['decisions']=[{'id':x['id'],'status':x['status'],'exit_code':x.get('exit_code'),
                           'worker_status':x.get('worker',{}).get('status'),'stop_reason':x.get('stop_reason'),
                           'control_expectation_match':x.get('control_expectation_match'),
                           'query_statuses':[q['status'] for q in x['queries']]} for x in selected]
        job['strict_completed_controls']=all(x.get('exit_code')==0 and not x.get('stop_reason') and x.get('worker',{}).get('status')=='COMPLETE' and x.get('control_expectation_match') for x in selected)
    else:
        selected=[report['jobs'][i]]
        job['decisions']=[{k:x.get(k) for k in ['case_id','arm','status','final_decision','stop_reason','full_process_cpu_seconds']} for x in selected]
    save();print(json.dumps({k:job[k] for k in ['kind','index','decisions']}),flush=True)
    if any(x['status'] in ['NOT_RUN','STARTED'] for x in selected):
        queue['status']='STOPPED_INCOMPLETE_CHILD';save();raise SystemExit(2)
queue['status']='ALL_SELECTED_TARGETS_RETURNED';save()
