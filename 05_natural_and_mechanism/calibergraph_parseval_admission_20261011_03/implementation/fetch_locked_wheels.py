"""Fetch identified official, hash-pinned wheels; no installation hooks or imports."""
import hashlib
import json
from pathlib import Path
import subprocess
from urllib.parse import urlparse
import zipfile

P=Path(__file__).resolve().parents[1]
lock=json.loads((P/'governance/OFFICIAL_DEPENDENCY_LOCK.json').read_text())
wheelhouse=P/'dependencies_local/wheels'
site=P/'dependencies_local/site-packages'
wheelhouse.mkdir(parents=True,exist_ok=True)
site.mkdir(parents=True,exist_ok=True)
receipts=[]
for e in lock['files']:
    assert urlparse(e['url']).scheme=='https' and urlparse(e['url']).hostname=='files.pythonhosted.org'
    dst=wheelhouse/e['filename']
    if not dst.exists():
        subprocess.run(['/usr/bin/curl','--fail','--silent','--show-error','--proto','=https','--tlsv1.2','--max-time','45','--max-filesize',str(e['bytes']+1024),'-o',str(dst),e['url']],check=True)
    assert hashlib.sha256(dst.read_bytes()).hexdigest()==e['sha256'], e['name']
    assert dst.stat().st_size==e['bytes'], e['name']
    files=[]
    with zipfile.ZipFile(dst) as z:
        for info in z.infolist():
            rel=Path(info.filename)
            assert not rel.is_absolute() and '..' not in rel.parts
            assert (info.external_attr>>16)&0o170000 != 0o120000
            if info.is_dir():continue
            assert not info.filename.endswith('.pth'), 'Do not execute path hooks'
            raw=z.read(info);target=site/rel
            target.parent.mkdir(parents=True,exist_ok=True)
            if target.exists(): assert target.read_bytes()==raw
            else: target.write_bytes(raw)
            files.append({'path':str(rel),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)})
    receipts.append({**e,'verified':True,'extracted_files':files,'target_code_executed':False})
    print(e['name']+' '+e['version']+' downloaded, hash verified, extracted without execution',flush=True)
(P/'governance/DEPENDENCY_ACQUISITION_RECEIPT.json').write_text(json.dumps({'status':'OFFICIAL_LOCKED_WHEELS_EXTRACTED_NOT_IMPORTED','lock_sha256':hashlib.sha256((P/'governance/OFFICIAL_DEPENDENCY_LOCK.json').read_bytes()).hexdigest(),'packages':receipts,'third_party_redistribution':False},indent=2)+'\n')
