"""One computation child at a time across all remaining frozen v5 queues."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

here=Path(__file__).resolve().parent
path=here/'CAMPAIGN_V5_REMAINING.json'
assert not path.exists()
main='4221081d3c63096841a902f1c8f70ac16f5d967c08476f26f8377d6bb4924443'
spot='1c5bc696d43fc64ee5b76a2b4f2e0d0b6d46206179900906bd99f4620c1d8b87'
suite='9db84350b498c3e5f37b06adf5868fa0e0429a81a2ebff65f930f78bd8b36485'
report={'status':'REGISTERED','queue_source_sha256':hashlib.sha256((here/'run_v5_queue.py').read_bytes()).hexdigest(),
        'campaign_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'previous_cost_ranges':[[132,168],[84,90]],
        'entries':[{'mode':m,'kind':k,'start':a,'stop':b,'lock_sha256':h,'status':'NOT_RUN'} for m,k,a,b,h in [
            ('main','cost',0,84,main),('main','cost',90,132,main),
            ('main','differential',0,168,main),('spotit','cost',0,168,spot)]]}
def save():
    t=path.with_suffix('.tmp');t.write_text(json.dumps(report,indent=2)+'\n');t.replace(path)
save()
for e in report['entries']:
    cmd=[sys.executable,'-B','-I','-S',str(here/'run_v5_queue.py'),'--kind',e['kind'],'--mode',e['mode'],
         '--start',str(e['start']),'--stop',str(e['stop']),'--runtime-lock-sha256',e['lock_sha256'],'--suite-sha256',suite]
    e.update(status='RUNNING',command=cmd);save()
    result=subprocess.run(cmd,stdin=subprocess.DEVNULL)
    e.update(status='RETURNED',exit_code=result.returncode);save()
    if result.returncode:
        report['status']='STOPPED_QUEUE_INCOMPLETE';save();raise SystemExit(result.returncode)
report['status']='ALL_QUEUES_RETURNED';save()
