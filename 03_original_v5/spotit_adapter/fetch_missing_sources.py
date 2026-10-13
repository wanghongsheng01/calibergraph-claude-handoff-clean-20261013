"""Fetch a fixed runtime-file inventory from the published SpotIt+ gitlink."""
import concurrent.futures, hashlib, json, subprocess, threading
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent
old=ROOT/'research_phase2/baseline_audit/source/verieql_v1'
prior=ROOT/'research_phase2/baseline_audit/source/spotit_engine'
commit='fb1bdaae8f3e4a544d08feffa44bc14270d99329'
paths=json.loads((HERE/'MISSING_SOURCE_CLOSURE.json').read_text())['fetch_paths']
out=HERE/'source'
assert all(not (out/rel).exists() for rel in paths)
stopped=threading.Event()
def fetch(rel):
    if stopped.is_set():return {'path':rel,'status':'NOT_RUN_AFTER_HTTP_DENIAL'}
    dest=out/rel;dest.parent.mkdir(parents=True,exist_ok=True)
    url=f'https://raw.githubusercontent.com/atremante26/VeriEQL/{commit}/{rel}'
    c=subprocess.run(['/usr/bin/curl','-q','--proto','=https','--connect-timeout','8','--max-time','15','--max-filesize','2000000','--max-redirs','0','--fail','--silent','--show-error','--output',str(dest)+'.part','--write-out','%{http_code}',url],capture_output=True,text=True,stdin=subprocess.DEVNULL,timeout=18)
    r={'path':rel,'url':url,'exit':c.returncode,'http_status':c.stdout,'stderr':c.stderr}
    part=Path(str(dest)+'.part')
    if c.returncode==0:
        part.rename(dest);r.update(status='FIXED_COMMIT_HTTPS_SOURCE',size_bytes=dest.stat().st_size,sha256=hashlib.sha256(dest.read_bytes()).hexdigest())
        if (prior/rel).is_file():r['previous_pinned_copy_matches']=dest.read_bytes()==(prior/rel).read_bytes()
    else:r['status']='DOWNLOAD_FAILED'
    if c.stdout in ['401','403']:stopped.set()
    return r
results=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
    for result in pool.map(fetch,paths):
        results.append(result)
        (HERE/'MISSING_SOURCE_FETCH_RECEIPT.json').write_text(json.dumps({'commit':commit,'scope':'Static import closure additions only; same fixed SpotIt gitlink; no target executed','results':results},indent=2)+'\n')
        print(json.dumps(result),flush=True)
raise SystemExit(0 if all(x['exit']==0 for x in results) else 2)
