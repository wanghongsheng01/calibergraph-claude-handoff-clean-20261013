"""Idle native Z3 deadline test: no assertions, parsing, or check-sat input."""
import hashlib
import json
from pathlib import Path
import subprocess
from owned_processes import OwnedCase, Stopped

HERE=Path(__file__).resolve().parent
z3=HERE/'native_local/z3'
assert hashlib.sha256(z3.read_bytes()).hexdigest()=='edae32f9e37ea4b5bb35310d72f0e352d0dc07626cac4e9e30bc1ea9a5bc8efb'
out=HERE/'native_idle_run_01';out.mkdir(exist_ok=False)
try:
    with OwnedCase(.3) as case:
        p=case.spawn([str(z3),'-memory:64','-T:1','-in'],stdin=subprocess.PIPE,
                     stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,
                     env={'PATH':'/usr/bin:/bin'})
        # Keep stdin open, send zero bytes; owned deadline must end idle read.
        p.stdout.readline()
except Stopped as error:
    assert str(error)=='CASE_DEADLINE'
else:
    raise AssertionError('expected case deadline')
receipt=case.receipt()
assert receipt['all_reaped'] and not receipt['cleanup_errors']
receipt.update(scientific_calls=0,smt_input_bytes=0,check_sat_commands=0,
               external_z3_rss_measured=False,
               native_memory_limit_MiB_test_only=64)
(out/'RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({k:receipt[k] for k in ['reason','all_reaped','returncodes','elapsed_s']}))
