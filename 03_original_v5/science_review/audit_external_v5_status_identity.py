"""Offline identity/receipt comparison only. No target imports or execution."""
from pathlib import Path
import json
import hashlib
from datetime import datetime, timezone
from collections import Counter

T=Path(__file__).resolve().parent.parent
R=Path('/Users/loctek/Documents/Codex/2026-10-10/task-3/calibergraph_audit_20261011/integration_review_v5')
OUT=Path(__file__).with_name('EXTERNAL_V5_STATUS_REGRESSION_IDENTITY.json')
evidence,errors={},[]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def record(p):
    p=Path(p).resolve();s=sha(p);evidence[str(p)]=s;return s
def read(p):record(p);return json.loads(Path(p).read_text())
def ck(ok,where,want):
    if not ok:errors.append({'where':str(where),'expected':want})

record(R/'CALIBERGRAPH_V5_FINAL_HANDOFF.zh.md')
status=read(R/'FINAL_REVIEW_STATUS.json')
local_main_lock=read(T/'experiments/v5_registration_01/runtime_paths_v5.json')
local_fix_lock=read(T/'runtime_fair_v5_statusfix/registration/runtime_paths_statusfix.json')
versions={}
for label,base,local,lockpath in [
    ('v5',R,T/'runtime_fair_v5',T/'experiments/v5_registration_01/runtime_paths_v5.json'),
    ('statusfix',R/'statusfix_review',T/'runtime_fair_v5_statusfix',R/'statusfix_review/AUDITOR_RUNTIME_LOCK.json')]:
    manifest=read(base/'FREEZE_MANIFEST.json');receipt=read(base/'independent_run_01/SUPERVISION.json')
    lock=read(lockpath);runner=base/'run_independent_entry_regression.py'
    ck(record(runner)==receipt['script_sha256'],runner,'actual external coordinator bytes')
    ck(record(base/'FREEZE_MANIFEST.json')==receipt['freeze_manifest_sha256'],label,'freeze linked by actual receipt')
    ck(record(lockpath)==receipt['runtime_lock_sha256'],label,'actual run lock linked by receipt')
    for f in manifest['files']:
        copied=base/'frozen'/f['path'];original=Path(manifest['source'])/f['path']
        ck(record(copied)==f['sha256'] and copied.stat().st_size==f['bytes'],copied,'all frozen copied bytes match')
        ck(record(original)==f['sha256'],original,'current original same as external freeze')
    program_rows=[]
    for name,digest in receipt['program_sha256'].items():
        actual_path=next(Path(p) for p in lock['runtime_programs'] if Path(p).name==name)
        ours=local/name
        ck(record(ours)==digest==record(actual_path)==lock['runtime_programs'][str(actual_path)],name,'all frozen 5/6 sources match ours and actual test lock')
        program_rows.append({'name':name,'our_path':str(ours),'actual_test_path':str(actual_path),'sha256':digest,'direct_child_entry_executed':name=='worker.py','supervisor_process_executed':False if name=='supervisor.py' else None})
    ck(len(program_rows)==(5 if label=='v5' else 6),label,'exact program inventory')
    mismatches=[]
    for path,digest in lock['files'].items():
        if sha(path)!=digest:mismatches.append(path)
    ck(not mismatches,label,'all actual run lock files unchanged')
    suitepath=base/'independent_run_01/AUDITOR_SUITE.json';suite=read(suitepath)
    ck(record(suitepath)==receipt['suite_sha256'],label,'actual auditor suite')
    jobs=[]
    for job in receipt['jobs']:
        idx=job['index'];wp=base/f'independent_run_01/job_{idx:04d}/worker_report.json';w=read(wp)
        ck(record(wp)==job['worker_report_sha256'],wp,'raw worker linked by coordinator')
        case=suite['cases'][idx//6]
        ck(w['input']==case and w['job_index']==idx and w['job']['arm']==job['arm'],wp,'registered external case/arm exact')
        ck(w['runtime_lock_sha256']==receipt['runtime_lock_sha256'] and w['suite_sha256']==receipt['suite_sha256'],wp,'same actual suite and lock')
        argv=job['argv'];actual_worker=Path(argv[4])
        expected_worker=local/'worker.py' if label=='v5' else base/'frozen/worker.py'
        ck(actual_worker==expected_worker and record(actual_worker)==receipt['program_sha256']['worker.py'],wp,'actual argv is worker, not supervisor')
        ck(json.loads(argv[argv.index('--expected-programs')+1])==receipt['program_sha256'],wp,'child expected six/five source hashes')
        ck(job['status']=='PROCESS_EXITED' and 'stop_reason' not in job and job['exit_code']==(0 if idx<12 else 2),wp,'normal child exit or explicit expected contract stop')
        ck(w['final_decision']==case['expected'] and w['environment_cleanup']=='COMPLETE' and job['regression_pass'] is True and all(job['checks'].values()),wp,'reported checks and raw outcome agree')
        original=w['contract_bridge']['original_ast'];ck(original==case['constraint'],wp,'source contract preserved')
        expected_pair=('ATTEMPTED_EFFECT_UNKNOWN' if label=='v5' else 'RETURNED') if idx<12 else 'NOT_RUN_CONTRACT_STOP'
        ck(w['pair_work_status']==expected_pair,wp,'version-specific pair state')
        if label=='statusfix':
            pr=w['pair_work_receipt'];ck(pr['event']==('DISPATCH_RETURNED' if idx<12 else 'CONTRACT_STOP') and pr['scientific_validation']=='NOT_INFERRED_FROM_EXECUTION_RECEIPT' and pr['process_and_resource_validation']=='PENDING_SUPERVISOR_ACKNOWLEDGEMENT',wp,'new logger keeps semantic/resource layers separate')
        if idx<6:
            sat=[a for a in w['attempts'] if a['status']=='sat'];ck(len(sat)==1,wp,'one actual final SAT witness')
            actual=job['independent_sqlite_replay']
            ck(sat[0]['witness']=={'T':[[6]]}==actual['witness'] and actual['original_contract_raw']==[[1]] and actual['relations']==[[[None]],[[6]]],wp,'external raw SQL original-predicate oracle and complete values')
        if idx>=12:
            ck(not w.get('pair_work_started',False) and w['attempts']==[] and w['fallback']['status']=='FORBIDDEN_UNVERIFIED_OR_REJECTED_CONTRACT',wp,'typed stop has no query work or fallback')
        jobs.append({'index':idx,'case_id':job['case'],'arm':job['arm'],'worker_path':str(wp),'worker_sha256':record(wp),'worker_entry':str(actual_worker),'exit_code':job['exit_code'],'decision':w['final_decision'],'pair_work_status':w['pair_work_status'],'no_stop':True})
    ck(len(jobs)==24 and sorted(j['index'] for j in jobs)==list(range(24)),label,'24 exact registered jobs')
    versions[label]={'manifest_path':str(base/'FREEZE_MANIFEST.json'),'manifest_sha256':record(base/'FREEZE_MANIFEST.json'),'manifest_files_verified':len(manifest['files']),'receipt_path':str(base/'independent_run_01/SUPERVISION.json'),'receipt_sha256':record(base/'independent_run_01/SUPERVISION.json'),'external_runner_path':str(runner),'external_runner_sha256':record(runner),'actual_lock_path':str(lockpath),'actual_lock_sha256':record(lockpath),'locked_files_verified_by_this_audit':len(lock['files']),'programs':program_rows,'counts':{'registered':24,'actual_sql_decisions':12,'typed_contract_stops':12,'resource_stops':0,'not_run':0,'exit_codes':dict(Counter(j['exit_code'] for j in jobs)),'decisions':dict(Counter(j['decision'] for j in jobs))},'source_unchanged_after_recorded':receipt['source_unchanged_after'],'jobs':jobs}

external_fix_lock=read(R/'statusfix_review/AUDITOR_RUNTIME_LOCK.json')
old_nonprogram={p:s for p,s in local_main_lock['files'].items() if p not in local_main_lock['runtime_programs']}
new_nonprogram={p:s for p,s in external_fix_lock['files'].items() if p not in external_fix_lock['runtime_programs']}
ck(old_nonprogram==new_nonprogram,'independent lock','same 848 nonprogram dependencies; only five programs replaced by six exact frozen programs')
reg=read(T/'experiments/V5_AGGREGATOR_CLASSIFICATION_REGRESSION_02.json')
aggregate=T/'experiments/BUILD_FINAL_V5_EXECUTION_CUT.py';cut=T/'experiments/FINAL_V5_EXECUTION_CUT.json';selector=T/'experiments/V5_SLOT_SELECTION_FINAL.json'
ck(record(aggregate)==reg['aggregator_sha256']=='83a23fc07b0185f39bd106be2a4c1d893c5c18a4a99592012ca6ed098275fe32','current exporter','same hash as current 16-fixture receipt')
record(cut);record(selector);record(T/'science_review/PAIR_WORK_STATUS_FIX_INDEPENDENT_REVIEW.json');record(T/'science_review/MAIN_ENTRY_REPAIR_EXECUTED_REVIEW.json')
for p in [R/'PAIR_REGRESSION_RECOUNT.json',R/'STATUSFIX_REGRESSION_RECOUNT.json',R/'statusfix_review/INDEPENDENT_LOGGING_RECEIPT.json']:record(p)
result={'utc':datetime.now(timezone.utc).isoformat(),'status':'EXTERNAL_EXECUTED_WORKER_REGRESSION_IDENTITY_MATCHED' if not errors else 'IDENTITY_FINDINGS_REMAIN','reviewer':'Different AI agent, offline read/hash/receipt comparison; no new target/native/SQLite execution','versions':versions,'shared_nonprogram_files':len(old_nonprogram),'statusfix_local_future_lock_status':local_fix_lock['status'],'current_handoff_objects':{'exporter':{'path':str(aggregate),'sha256':record(aggregate),'matching_regression_path':str(T/'experiments/V5_AGGREGATOR_CLASSIFICATION_REGRESSION_02.json'),'matching_regression_sha256':record(T/'experiments/V5_AGGREGATOR_CLASSIFICATION_REGRESSION_02.json'),'count':16},'final_cut':{'path':str(cut),'sha256':record(cut)},'selector':{'path':str(selector),'sha256':record(selector)},'local_independent_review':{'path':str(T/'science_review/PAIR_WORK_STATUS_FIX_INDEPENDENT_REVIEW.json'),'sha256':record(T/'science_review/PAIR_WORK_STATUS_FIX_INDEPENDENT_REVIEW.json')}},'interpretation':['External v5 actual argv executes our original worker with the unchanged 853-file lock. External statusfix argv executes an exact-byte frozen worker copy under an auditor-owned 854-file lock.','All our frozen five v5 and six statusfix program bytes match. Supervisor bytes were included in the source inventory but neither supervisor was the external child entry point.','Each round is 24 registered jobs: 12 SQL decisions plus 12 expected typed stops, not 24 SQL equivalence proofs. The four-case external suite differs from our 28-case main suite.','This adds actual limited statusfix-worker evidence beyond our earlier pure-helper/static cutoff; it does not rewrite that historical review or claim our pending release lock was executed.','No prior e574/781 narrow-reference result is inherited: actual current reference in both tested versions is fdcee3a919930013945c571e64b7d4b478186c93ceee4546ff520879e99680e0.','External handoff current-exporter mismatch describes its earlier cutoff. Current local regression_02 binds 83a23fc exactly and our separate full frozen-cut receipt review is complete; external acceptance of those exact objects still requires that reviewer to inspect them.','External coordinator exit0 is recorded in FINAL_REVIEW_STATUS.json (sessions18584/57840); this audit can verify that recorded provenance and per-child wait4 reports, not replay platform session history.','New supervisor process coverage, hard-stop/cleanup/disk-failure race coverage, performance/generic SQL correctness and paper scientific acceptance are not established by these 48 worker controls.'],'findings':errors,'raw_evidence_sha256':evidence,'audit_script_sha256':sha(__file__)}
if OUT.exists():raise SystemExit('Refusing to overwrite existing identity review')
OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'status':result['status'],'findings':errors,'versions':{k:v['counts'] for k,v in versions.items()},'shared_nonprogram_files':len(old_nonprogram),'path':str(OUT),'sha256':sha(OUT)},ensure_ascii=False,indent=2))
