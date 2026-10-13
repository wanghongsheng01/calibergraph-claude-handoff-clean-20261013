"""Resume v5 after observed host-channel loss without overwriting old attempts."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys

here=Path(__file__).resolve().parent
root=here.parent
path=here/'CAMPAIGN_V5_RECOVERY_01.json'
assert not path.exists()
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
main='4221081d3c63096841a902f1c8f70ac16f5d967c08476f26f8377d6bb4924443'
spot='1c5bc696d43fc64ee5b76a2b4f2e0d0b6d46206179900906bd99f4620c1d8b87'
suite='9db84350b498c3e5f37b06adf5868fa0e0429a81a2ebff65f930f78bd8b36485'
assert sha(here/'run_v5_queue.py')=='56c5f768da28e35a3e796638b6754c6274a006eec4ca11331a7260fffa07a933'
assert sha(here/'v5_registration_01/REGISTERED_SIX_ARM_SUITE.json')==suite
verification=[]
for name,expected in [('runtime_paths_v5.json',main),('spotit_engine_runtime_paths_v5.json',spot)]:
    p=here/'v5_registration_01'/name
    assert sha(p)==expected
    lock=json.loads(p.read_text())
    assert lock['status']=='STATIC_REVIEWED_READY_FOR_LOCAL_RUN'
    for file,h in lock['files'].items():
        q=Path(file)
        assert q==q.resolve() and sha(q)==h, file
    verification.append({'path':str(p),'sha256':expected,'files_checked':len(lock['files'])})
old=[here/'CAMPAIGN_V5_REMAINING.json',here/'QUEUE_V5_main_cost_000_084.json',
     root/'runs/fair_v5_main_cost_051_01/supervisor_report.json',
     root/'runs/fair_v5_main_cost_051_01/job_0052/worker_report.json',
     here/'V5_RECOVERY_READONLY_SNAPSHOT_20261011T055109.json']
report={'status':'REGISTERED','registered_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'old_managed_session':49665,'session_recovery':'Unknown process id',
        'process_absence_evidence':{'command':"pgrep -f 'run_v5_remaining_campaign|run_v5_queue|runtime_fair_v5'",
             'mode':'approved read-only process inspection outside sandbox','exit_code':1,'output':'',
             'meaning':'no matching experiment/controller process observed before recovery'},
        'original_cost_slot_state':{'RETURNED':94,'INTERRUPTED_EFFECT_UNKNOWN':1,'NOT_RUN':73},
        'original_interrupted_slot':52,
        'interrupted_policy':'Preserve original STARTED/worker OFFICIAL_ATTEMPT as an incomplete attempt; a new selected attempt completes this same logical slot.',
        'preserved_resource_observation_slots':[19,39,51],
        'new_logical_slot_denominators':{'main_cost':168,'main_differential':168,'spotit_selected_cost':28},
        'runtime_reverification':verification,
        'prior_evidence':[{'path':str(p),'sha256':sha(p)} for p in old],
        'queue_source_sha256':sha(here/'run_v5_queue.py'),'campaign_source_sha256':sha(Path(__file__)),
        'entries':[{'mode':m,'kind':k,'start':a,'stop':b,'lock_sha256':h,'status':'NOT_RUN'} for m,k,a,b,h in [
            ('main','cost',52,84,main),('main','cost',90,132,main),
            ('main','differential',0,168,main),('spotit','cost',0,168,spot)]]}
def save():
    p=path.with_suffix('.tmp');p.write_text(json.dumps(report,indent=2)+'\n');p.replace(path)
save()
for e in report['entries']:
    command=[sys.executable,'-B','-I','-S',str(here/'run_v5_queue.py'),'--kind',e['kind'],'--mode',e['mode'],
        '--start',str(e['start']),'--stop',str(e['stop']),'--runtime-lock-sha256',e['lock_sha256'],'--suite-sha256',suite]
    e.update(status='RUNNING',command=command);save()
    result=subprocess.run(command,stdin=subprocess.DEVNULL)
    e.update(status='RETURNED',exit_code=result.returncode);save()
    if result.returncode:
        report['status']='STOPPED_QUEUE_INCOMPLETE';save();raise SystemExit(result.returncode)
report['status']='ALL_QUEUES_RETURNED';save()
