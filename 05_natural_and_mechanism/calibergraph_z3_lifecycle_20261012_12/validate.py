"""Real lightweight child lifecycle tests; zero SQL/SMT solving and zero PID inspection."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

from owned_processes import OwnedCase, Stopped, launch_scientific_z3, science_admission

HERE = Path(__file__).resolve().parent
PYTHON = '/opt/homebrew/bin/python3.12'
FIXTURE = [PYTHON, '-I', '-S', '-B', str(HERE/'fixtures.py')]


def fixture(case, mode):
    return case.spawn(FIXTURE+[mode], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                      text=True, env={'PATH': '/usr/bin:/bin'})


def read_state(proc):
    """Protocol guard for tests; not a modification of Polygon solver decisions."""
    value = proc.stdout.readline()
    if not value:
        raise Stopped('PROTOCOL_EOF')
    if value.strip() not in {'sat', 'unsat'}:
        raise Stopped('PROTOCOL_NON_BOOLEAN_STATE')
    return value.strip()


def main():
    out = HERE/(sys.argv[1] if len(sys.argv)>1 else 'validation_run_01')
    out.mkdir(exist_ok=False)
    records=[]
    def record(name, case, expected):
        receipt=case.receipt();receipt['test']=name;receipt['expected']=expected
        assert receipt['all_reaped'] and not receipt['cleanup_errors'], receipt
        records.append(receipt)
        (out/(name+'.json')).write_text(json.dumps(receipt,indent=2)+'\n')

    with OwnedCase(2) as case:
        p=fixture(case,'normal'); assert p.stdout.readline().strip()=='OK'
        assert p.wait(timeout=1)==0
    record('normal',case,'normal return + wait')

    try:
        with OwnedCase(.5) as case:
            p=fixture(case,'ignore_term');assert p.stdout.readline().strip()=='READY'
            p.stdout.readline()  # blocks; deadline must break it and force-reap child
    except Stopped as e:
        assert str(e)=='CASE_DEADLINE'
    else: raise AssertionError('deadline did not fire')
    assert any(e['kind']=='kill' for e in case.events)
    record('deadline_kill',case,'CASE_DEADLINE + SIGKILL escalation + wait')

    try:
        with OwnedCase(2) as case:
            for mode in ['hang','ignore_term']:
                p=fixture(case,mode);assert p.stdout.readline().strip()=='READY'
            raise ValueError('controlled exception')
    except ValueError: pass
    assert len(case.handles)==2
    record('exception_two_handles',case,'all retained handles cleaned, not only newest')

    for mode in ['eof','unknown']:
        try:
            with OwnedCase(2) as case:
                read_state(fixture(case,mode))
        except Stopped as e:
            assert str(e)==('PROTOCOL_EOF' if mode=='eof' else 'PROTOCOL_NON_BOOLEAN_STATE')
        else: raise AssertionError('unexpected protocol success')
        record('protocol_'+mode,case,'non-success state is not EQU')

    # Test-only 48 MiB threshold; bounded 40 MiB allocation in this Python process.
    # This demonstrates allowed SELF RSS stop and child cleanup, never child RSS coverage.
    allocation=None
    try:
        with OwnedCase(2, self_rss_stop_bytes=48*1024**2) as case:
            p=fixture(case,'hang');assert p.stdout.readline().strip()=='READY'
            allocation=bytearray(40*1024**2)
            case.sample_self()
            time.sleep(.1)
            case.checkpoint()
    except Stopped as e:
        assert str(e)=='SELF_RSS_SAMPLED_STOP'
    else: raise AssertionError('RSS sample did not stop')
    finally:
        del allocation
    record('self_rss_stop',case,'own RSS crossed test threshold; child reaped')

    with OwnedCase(2) as case:
        try: launch_scientific_z3(case,['never-executed-z3'])
        except Stopped as e: assert str(e)=='EXTERNAL_Z3_RSS_COVERAGE_UNAVAILABLE'
        else: raise AssertionError('science gate incorrectly admitted')
        assert len(case.handles)==0
    record('science_gate',case,'reject before Popen')
    result={'passed':True,'test_count':len(records),'records':records,
            'science_admission':science_admission(),'scientific_calls':0,
            'system_process_queries':0,'fixtures_max_allocation_bytes':40*1024**2}
    (out/'VALIDATION.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'passed':True,'test_count':len(records),
                      'owned_child_count':sum(r['handle_count'] for r in records),
                      'elapsed_sum_s':sum(r['elapsed_s'] for r in records)}))


if __name__=='__main__': main()
