"""Sequential public applicability queue; each target has its own bounded supervisor."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
OUT = HERE / 'QUEUE_CHUNKS_017_023.json'
assert not OUT.exists(), 'Preserve existing queue; recovery needs explicit new attempt.'
queue = {'schema_version': 1, 'status': 'REGISTERED',
         'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
         'unique_target_process': True,
         'jobs': [{'chunk_index': i, 'attempt': '001', 'status': 'NOT_RUN'} for i in range(17, 24)]}
def save():
    tmp = OUT.with_suffix('.tmp')
    tmp.write_text(json.dumps(queue, indent=2) + '\n')
    tmp.replace(OUT)
save()
for job in queue['jobs']:
    job['status'] = 'RUNNING'; save()
    cmd = [sys.executable, '-B', '-I', '-S', str(HERE/'supervise_chunk.py'),
           '--chunk-index', str(job['chunk_index']), '--attempt', job['attempt']]
    start = time.monotonic()
    result = subprocess.run(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True)
    job.update(status='RETURNED', exit_code=result.returncode, wall_seconds=time.monotonic()-start)
    job['supervisor_stdout'] = result.stdout
    job['supervisor_stderr'] = result.stderr
    report_path = HERE/'runs'/('chunk_%03d'%job['chunk_index'])/'attempt_001'/'scan_report.json'
    report = json.loads(report_path.read_text()) if report_path.exists() else {}
    job['scan_status'] = report.get('status', 'NO_REPORT')
    job['summary'] = report.get('summary', {})
    save()
    print(json.dumps({'chunk_index':job['chunk_index'],'exit_code':job['exit_code'],'scan_status':job['scan_status'],'query_status_counts':job['summary'].get('query_status_counts',{}),'remaining':job['summary'].get('uncompleted_query_slots')}), flush=True)
    if result.returncode or job['summary'].get('uncompleted_query_slots', 1):
        queue['status'] = 'STOPPED_INCOMPLETE_CHUNK_REMAINDER_NOT_RUN'; save()
        raise SystemExit(2)
queue['status'] = 'COMPLETED_ALL_REMAINING_CHUNKS'; save()
