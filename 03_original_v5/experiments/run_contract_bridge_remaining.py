"""Execute remaining frozen diagnostics serially, without overwriting earlier runs."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parent.parent
bridge = root / 'contract_bridge_v1'
manifest_sha = '32ee11faea4fee939964cd4ae03a9435d2ebe35877cecd221d7e65b2da30f3dd'
lock = root / 'experiments/v4_registration_01/runtime_paths_v4.json'
lock_sha = '29220d333a6a3f9812ab2c24aecd7877f7cf5c9e919e80b612f880bf1dc92f1f'
prior = {'lt_literal_left_N1', 'lt_literal_left_N2'}
cases = json.loads((bridge / 'fixtures.json').read_text())['cases']
receipt = root / 'experiments/QUEUE_CONTRACT_BRIDGE_REMAINING_32.json'
assert not receipt.exists()
report = {'status': 'REGISTERED', 'full_registered_denominator': 34,
          'previously_executed_cases': sorted(prior),
          'manifest_sha256': manifest_sha,
          'queue_source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          'entries': [{'case_id': c['id'], 'status': 'NOT_RUN'} for c in cases if c['id'] not in prior]}

def save():
    temp = receipt.with_suffix('.tmp')
    temp.write_text(json.dumps(report, indent=2) + '\n'); temp.replace(receipt)

save()
for entry in report['entries']:
    out = bridge / 'runs' / (entry['case_id'] + '_01')
    assert not out.exists()
    command = [sys.executable, '-B', '-I', '-S', str(bridge / 'supervise.py'),
               '--runtime-lock', str(lock), '--runtime-lock-sha256', lock_sha,
               '--manifest-sha256', manifest_sha, '--case-id', entry['case_id'], '--out-dir', str(out)]
    entry.update(status='RUNNING', command=command); save()
    try:
        result = subprocess.run(command, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=30)
    except subprocess.TimeoutExpired:
        entry.update(status='QUEUE_TIMEOUT_EFFECT_UNKNOWN'); report['status']='STOPPED'; save(); raise
    entry.update(status='RETURNED', command_exit=result.returncode, stderr=result.stderr)
    if (out / 'supervision.json').exists():
        s = json.loads((out / 'supervision.json').read_text())
        entry.update(supervisor_exit=s.get('exit_code'), stop_reason=s.get('stop_reason'))
    if (out / 'report.json').exists():
        r = json.loads((out / 'report.json').read_text())
        entry.update(worker_status=r.get('status'), report_sha256=hashlib.sha256((out / 'report.json').read_bytes()).hexdigest())
    save(); print(json.dumps({k: entry.get(k) for k in ('case_id','command_exit','supervisor_exit','stop_reason','worker_status')}), flush=True)
report['status']='ALL_SELECTED_DIAGNOSTICS_RETURNED'; save()
