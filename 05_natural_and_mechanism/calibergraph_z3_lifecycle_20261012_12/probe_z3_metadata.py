"""Bounded native metadata/startup checks, never sends check-sat or scientific input."""
import hashlib
import json
from pathlib import Path
import subprocess

from owned_processes import OwnedCase

HERE=Path(__file__).resolve().parent
Z3=HERE/'native_local/z3'
SHA='edae32f9e37ea4b5bb35310d72f0e352d0dc07626cac4e9e30bc1ea9a5bc8efb'


def main():
    assert hashlib.sha256(Z3.read_bytes()).hexdigest()==SHA
    out=HERE/'native_metadata_run_02';out.mkdir(exist_ok=False)
    records=[]
    cases=[('version',['-version'],None),('help',['-h'],None),
           ('memory_description',['-pp:memory_max_size'],None),
           ('startup_internal_limit',['-memory:1','-T:1','-in'],'(exit)\n')]
    for name,args,input_text in cases:
        with OwnedCase(2) as guard:
            p=guard.spawn([str(Z3),*args],stdin=subprocess.PIPE,stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE,text=True,env={'PATH':'/usr/bin:/bin'})
            stdout,stderr=p.communicate(input_text)
        receipt=guard.receipt()
        receipt.update(name=name,args=args,stdin=input_text,
                       stdout=stdout,stderr=stderr,returncode=p.returncode)
        records.append(receipt)
        (out/(name+'.json')).write_text(json.dumps(receipt,indent=2)+'\n')
    result={'binary_sha256':SHA,'records':records,'scientific_calls':0,
            'check_sat_commands':0,'external_z3_rss_measured':False,
            'scope':'metadata and startup-only; deadline/handle lifecycle, not child RSS guarantee'}
    (out/'NATIVE_PROBE.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({r['name']:{'returncode':r['returncode'],'all_reaped':r['all_reaped'],
                               'stdout':r['stdout'] if r['name']!='help' else '[help saved]',
                               'stderr':r['stderr']} for r in records},indent=2))


if __name__=='__main__':main()
