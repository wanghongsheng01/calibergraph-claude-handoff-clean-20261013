"""Independent, bounded fixtures; no process enumeration or foreign PID access."""
import hashlib
import json
from pathlib import Path
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import owned_processes as op

FIX = [sys.executable, '-I', '-S', '-B', str(ROOT/'fixtures.py')]
results = []

def reset(handler, mask):
    signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGALRM})
    signal.setitimer(signal.ITIMER_REAL, 0)
    if signal.SIGALRM in signal.sigpending():
        signal.sigwait({signal.SIGALRM})
    signal.signal(signal.SIGALRM, handler)
    signal.pthread_sigmask(signal.SIG_SETMASK, mask)

def reap(handles):
    for p in handles:
        if p.poll() is None:
            p.kill()
        p.wait(timeout=2)
        for s in (p.stdout, p.stderr):
            if s is not None:
                s.close()

old_handler = signal.getsignal(signal.SIGALRM)
old_mask = signal.pthread_sigmask(signal.SIG_BLOCK, set())
original_popen = subprocess.Popen
captured = []
case = op.OwnedCase(.05, interval=.005)
def delayed_return(*args, **kwargs):
    p = original_popen(*args, **kwargs)
    captured.append(p)
    time.sleep(.12)  # widen the Popen-return -> owned registration window
    return p
subprocess.Popen = delayed_return
try:
    try:
        with case:
            case.spawn(FIX+['hang'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    except BaseException as e:
        error = type(e).__name__+': '+str(e)
    else:
        error = None
finally:
    subprocess.Popen = original_popen
    reset(old_handler, old_mask)
    leaked = [p for p in captured if p not in case.handles]
    results.append({'test':'alarm_registration_window', 'error':error, 'created':len(captured),
                    'registered':len(case.handles), 'unregistered_handles':len(leaked),
                    'unregistered_still_running':sum(p.poll() is None for p in leaked)})
    reap(captured)

case = op.OwnedCase(2)
handles=[]
real_kill=None
try:
    try:
        with case:
            for mode in ('hang', 'ignore_term'):
                p=case.spawn(FIX+[mode], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                handles.append(p)
                assert p.stdout.readline().strip()=='READY'
            real_kill=handles[-1].kill
            def fail_kill():
                raise OSError('controlled owned-handle kill failure')
            handles[-1].kill=fail_kill
    except BaseException as e:
        error=type(e).__name__+': '+str(e)
    else:
        error=None
    results.append({'test':'cleanup_kill_exception','error':error,
                    'handler_restored':signal.getsignal(signal.SIGALRM)==old_handler,
                    'cleanup_errors':case.cleanup_errors,
                    'wait_events':sum(e['kind']=='wait' for e in case.events),
                    'handle_count':len(handles)})
finally:
    reset(old_handler,old_mask)
    if real_kill: handles[-1].kill=real_kill
    reap(handles)

case=op.OwnedCase(2)
handles=[]
class BrokenClose:
    def close(self): raise OSError('controlled close failure')
try:
    try:
        with case:
            p=case.spawn(FIX+['normal'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            handles.append(p)
            assert p.stdout.readline().strip()=='OK'
            p.wait(timeout=1)
            p.stdin=BrokenClose()
    except BaseException as e:
        error=type(e).__name__+': '+str(e)
    else: error=None
    results.append({'test':'stream_close_exception','error':error,
                    'handler_restored':signal.getsignal(signal.SIGALRM)==old_handler,
                    'cleanup_errors':case.cleanup_errors})
finally:
    reset(old_handler,old_mask)
    reap(handles)

case=op.OwnedCase(.000001)
try:
    try:
        with case:
            pass
    except BaseException as e:
        error=type(e).__name__+': '+str(e)
    else: error=None
    results.append({'test':'enter_deadline_exception','error':error,
                    'handler_restored':signal.getsignal(signal.SIGALRM)==old_handler,
                    'closed':case.closed,'thread_created':hasattr(case,'thread')})
finally:
    reset(old_handler,old_mask)
    case.done.set()
    if hasattr(case,'thread') and case.thread.ident is not None: case.thread.join(timeout=2)

result={'source_sha256':{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ('owned_processes.py','fixtures.py','validate.py')},
        'results':results,'science_admission':op.science_admission(), 'scientific_calls':0,
        'process_enumeration_or_foreign_rss_queries':0, 'owned_fixture_children':4,
        'allocated_test_buffer_bytes':0,'emergency_reap_completed':True}
(Path(__file__).parent/'INDEPENDENT_CHECKS.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
