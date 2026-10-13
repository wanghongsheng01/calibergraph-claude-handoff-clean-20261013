"""Independent positive paths; bounded children, zero allocation pressure or science."""
import hashlib
import json
from pathlib import Path
import resource
import signal
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from owned_processes import OwnedCase, Stopped, launch_scientific_z3, science_admission
FIX=[sys.executable,'-I','-S','-B',str(ROOT/'fixtures.py')]
results=[]
handler=signal.getsignal(signal.SIGALRM)
mask=signal.pthread_sigmask(signal.SIG_BLOCK,set())
def spawn(case,mode):
    p=case.spawn(FIX+[mode],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    assert p.stdout.readline().strip()=='READY'
    return p

def record(name,case,elapsed):
    r=case.receipt()
    assert r['all_reaped'] and not r['cleanup_errors'],r
    assert signal.getsignal(signal.SIGALRM)==handler
    assert signal.getitimer(signal.ITIMER_REAL)==(0.,0.)
    assert signal.pthread_sigmask(signal.SIG_BLOCK,set())==mask
    assert not case.thread.is_alive()
    for p in case.handles:
        assert p.stdout.closed and p.stderr.closed
    r.update(test=name, measured_elapsed_s=elapsed, signal_state_restored=True, watchdog_joined=True, streams_closed=True)
    results.append(r)

start=time.monotonic()
try:
    with OwnedCase(.25) as case:
        spawn(case,'hang')
        p=spawn(case,'ignore_term')
        p.stdout.readline()
except Stopped as e: assert str(e)=='CASE_DEADLINE'
else: raise AssertionError('deadline failed')
assert len(case.handles)==2 and any(e['kind']=='kill' for e in case.events)
assert time.monotonic()-start < 2
record('deadline_blocked_read_two_owned_handles',case,time.monotonic()-start)

start=time.monotonic()
try:
    with OwnedCase(2,interval=.005) as case:
        p=spawn(case,'ignore_term')
        # Lower only this test instance's threshold beneath already-existing SELF high-water.
        case.self_rss_stop_bytes=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)-1
        p.stdout.readline()  # automatic watchdog must stop and clean while main is blocked
        case.checkpoint()
except Stopped as e: assert str(e)=='SELF_RSS_SAMPLED_STOP'
else: raise AssertionError('automatic SELF stop failed')
assert time.monotonic()-start < 1
record('automatic_self_rss_stop_blocked_read',case,time.monotonic()-start)

start=time.monotonic()
with OwnedCase(1) as case:
    try: launch_scientific_z3(case,['never-executed-review-science'])
    except Stopped as e: assert str(e)=='EXTERNAL_Z3_RSS_COVERAGE_UNAVAILABLE'
    else: raise AssertionError('gate admitted')
    assert not case.handles
record('science_gate_before_launch',case,time.monotonic()-start)

result={'passed':True,'records':results,'science_admission':science_admission(),
        'source_sha256':hashlib.sha256((ROOT/'owned_processes.py').read_bytes()).hexdigest(),
        'owned_fixture_children':3,'scientific_calls':0,'allocated_test_buffer_bytes':0,
        'process_enumeration_or_foreign_rss_queries':0}
(Path(__file__).parent/'INDEPENDENT_LIFECYCLE.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'passed':True,'test_count':len(results),'owned_fixture_children':3,
                  'elapsed_sum_s':sum(r['measured_elapsed_s'] for r in results)}))
