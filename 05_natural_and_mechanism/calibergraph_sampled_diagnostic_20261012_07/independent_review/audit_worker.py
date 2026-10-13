"""Independent saved-data SQLite audit. No baseline, generator, solver or data edits."""
from pathlib import Path
import sys
P = Path(__file__).resolve().parent
SOURCE = P.parent
sys.path.insert(0, str(SOURCE))
from guard import Guard, check_contender
mode, lockfd, pipefd, lifefd, threshold, directory = sys.argv[1:]
OUT = Path(directory)
guard = Guard(int(lockfd), int(pipefd), int(lifefd), int(threshold))
assert mode == 'audit'

import hashlib
import json
import math
import sqlite3
import traceback
from collections import Counter

R = {'status': 'STARTED', 'baseline_calls': 0, 'generator_calls': 0,
     'solver_calls': 0, 'saved_candidate_replays': [], 'sqlite_version': sqlite3.sqlite_version}

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def canonical(value): return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()
def ascii_fold(value): return value.translate(str.maketrans('ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'))
def quote(value): return '"' + value.replace('"', '""') + '"'
def rows(db, query): return [list(row) for row in db.execute(query)]
def checkpoint(): (OUT/'AUDIT_RESULT.json').write_text(json.dumps(R, ensure_ascii=False, indent=2)+'\n')

def main():
    lockpath = SOURCE.parent/'calibergraph_launch_protocol_v2_20261012_05/runtime/owned.lock'
    R['contender_blocked'] = check_contender(lockpath)
    original = json.loads((SOURCE/'science/RESULT.json').read_text())
    freeze = json.loads((SOURCE/'FREEZE.json').read_text())
    # Read and hash only; no imports from frozen external dependencies.
    mismatch = [item['path'] for item in freeze['files'] if sha(item['path']) != item['sha256']]
    assert not mismatch, mismatch
    R['freeze_file_verification'] = {'files': len(freeze['files']), 'all_match': True, 'freeze_sha256': sha(SOURCE/'FREEZE.json')}
    input_paths = {Path(x['path']).name:Path(x['path']) for x in freeze['files'] if Path(x['path']).name.startswith('case1172.')}
    goldpath, predpath, ddlpath = [input_paths[n] for n in ('case1172.gold.sql','case1172.predicted.sql','case1172.full-schema.sql')]
    queries = [goldpath.read_text(), predpath.read_text()]
    ddl = ddlpath.read_text()
    R['input_sha256'] = {p.name:sha(p) for p in (goldpath,predpath,ddlpath)}
    R['source_result_sha256'] = sha(SOURCE/'science/RESULT.json')
    R['source_error_sha256'] = sha(SOURCE/'science/error.txt')
    R['source_status_preserved'] = original['status']
    assert len(original['generated_candidates']) == 9
    R['candidate_denominator'] = {'loaded_snapshots':9, 'empty_snapshots':1, 'nonempty_snapshots':8}

    def fresh():
        db=sqlite3.connect(':memory:')
        db.execute('PRAGMA foreign_keys=ON')
        assert db.execute('PRAGMA foreign_keys').fetchone()==(1,)
        db.executescript(ddl) # byte-identical full DDL: all 3 tables, no narrowing
        return db

    expected_columns = {
        'Patient': ['ID','SEX','Birthday','Description','First Date','Admission','Diagnosis'],
        'Examination': ['ID','Examination Date','aCL IgG','aCL IgM','ANA','ANA Pattern','aCL IgA','Diagnosis','KCT','RVVT','LAC','Symptoms','Thrombosis'],
        'Laboratory': ['ID','Date','GOT','GPT','LDH','ALP','TP','ALB','UA','UN','CRE','T-BIL','T-CHO','TG','CPK','GLU','WBC','RBC','HGB','HCT','PLT','PT','APTT','FG','PIC','TAT','TAT2','U-PRO','IGG','IGA','IGM','CRP','RA','RF','C3','C4','RNP','SM','SC170','SSA','SSB','CENTROMEA','DNA','DNA-II']}
    db=fresh()
    try:
        schema={}
        assert rows(db,"SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")==[['Examination'],['Laboratory'],['Patient']]
        for name, expected in expected_columns.items():
            info=rows(db,'PRAGMA table_info('+quote(name)+')')
            assert [c[1] for c in info]==expected
            expected_nn={'Patient':['ID'],'Laboratory':['ID','Date'],'Examination':[]}[name]
            assert [c[1] for c in info if c[3]]==expected_nn
            expected_pk={'Patient':['ID'],'Laboratory':['ID','Date'],'Examination':[]}[name]
            assert [c[1] for c in sorted(info,key=lambda c:c[5]) if c[5]]==expected_pk
            defaults={c[1]:c[4] for c in info if c[4] is not None}
            assert defaults=={'Patient':{'ID':'0'},'Laboratory':{'ID':'0','Date':"'0000-00-00'"},'Examination':{}}[name]
            fks=rows(db,'PRAGMA foreign_key_list('+quote(name)+')')
            assert fks==([] if name=='Patient' else [[0,0,'Patient','ID','ID','CASCADE','CASCADE','NONE']])
            schema[name]={'columns':info,'foreign_keys':fks,'indexes':rows(db,'PRAGMA index_list('+quote(name)+')')}
        R['full_schema_metadata']=schema
        R['constraint_scope']='All original full-DDL tables/columns/defaults/PK/NOT NULL/FK actions instantiated unchanged; SQLite affinity semantics, no invented date/type CHECK constraints.'
    finally: db.close()

    def replay(data, index=None):
        folded={ascii_fold(name):name for name in data}
        assert len(folded)==len(data)==3
        assert set(folded)=={ascii_fold(x) for x in expected_columns}
        db=fresh()
        try:
            counts={}
            for name in ('Patient','Examination','Laboratory'):
                table=data[folded[ascii_fold(name)]]
                cols=table['columns']; values=table['rows']
                lowered=list(map(ascii_fold,cols))
                assert len(lowered)==len(set(lowered))
                assert set(lowered)==set(map(ascii_fold,expected_columns[name]))
                assert all(len(row)==len(cols) for row in values)
                assert all(v is None or type(v) in (str,int,float) for row in values for v in row)
                assert all(type(v) is not float or math.isfinite(v) for row in values for v in row)
                # SQL uses original case-insensitive identifiers; row values/order unchanged.
                stmt='INSERT INTO '+quote(name)+' ('+','.join(map(quote,cols))+') VALUES ('+','.join('?' for _ in cols)+')'
                db.executemany(stmt,values)
                counts[name]=len(values)
                assert db.execute('SELECT count(*) FROM '+quote(name)).fetchone()[0]==len(values)
            db.commit()
            fk=rows(db,'PRAGMA foreign_key_check'); integrity=rows(db,'PRAGMA integrity_check')
            assert not fk and integrity==[['ok']]
            outputs=[rows(db,q) for q in queries]
            # Diagnostic SELECTs only: explain multiplicity without changing stored data.
            joined=rows(db,"SELECT P.ID,L.Date,L.`T-BIL`,P.SEX,typeof(L.`T-BIL`) FROM Patient P JOIN Laboratory L ON P.ID=L.ID ORDER BY P.ID,L.Date")
            boundary=rows(db,"SELECT DISTINCT P.ID FROM Patient P JOIN Laboratory L ON P.ID=L.ID WHERE P.SEX='M' AND L.`T-BIL`=2.0 ORDER BY P.ID")
            greater=rows(db,"SELECT DISTINCT P.ID FROM Patient P JOIN Laboratory L ON P.ID=L.ID WHERE P.SEX='M' AND L.`T-BIL`>2.0 ORDER BY P.ID")
            ge=rows(db,"SELECT DISTINCT P.ID FROM Patient P JOIN Laboratory L ON P.ID=L.ID WHERE P.SEX='M' AND L.`T-BIL`>=2.0 ORDER BY P.ID")
            eq_ids=[r[0] for r in boundary]; gt_ids=[r[0] for r in greater]
            assert set(r[0] for r in ge)==set(eq_ids)|set(gt_ids)
            assert outputs==[[[len(ge)]],[[len(greater)]]]
            rec={'candidate':index,'saved_database_sha256':canonical(data),'row_counts':counts,
                 'foreign_key_check':fk,'integrity_check':integrity,'original_query_outputs':outputs,
                 'different':outputs[0]!=outputs[1], 'male_boundary_ids':eq_ids,'male_gt2_ids':gt_ids,
                 'boundary_ids_also_gt2':sorted(set(eq_ids)&set(gt_ids)),
                 'boundary_only_ids':sorted(set(eq_ids)-set(gt_ids)), 'joined_diagnostic_rows':joined,
                 'all_fullDDL_inserts_accepted':True}
            return rec
        finally: db.close()

    control=replay(original['known_control']['database'])
    assert control['original_query_outputs']==[[[1]],[[0]]] and control['different']
    R['control']={'kind':'OUR_SAVED_CONSTRUCTED_CONTROL_NOT_AUTHOR_WITNESS','supplied_to_generator':False,**control}
    checkpoint()
    for i,c in enumerate(original['generated_candidates']):
        rec=replay(c['database'],i)
        official=c['official_outputs']
        assert [o['side'] for o in official]==[0,1]
        rec['recorded_official_outputs_match']=rec['original_query_outputs']==[o['rows'] for o in official]
        assert rec['recorded_official_outputs_match']
        R['saved_candidate_replays'].append(rec);checkpoint()
    # Verify saved counters/stages rather than invoke any scientific implementation.
    stages=[json.loads(x) for x in (SOURCE/'science/STAGES.jsonl').read_text().splitlines()]
    counts=Counter((x['phase'],x['state']) for x in stages)
    assert counts['OFFICIAL_DISPROVE','START']==counts['OFFICIAL_DISPROVE','END']==original['disprove_calls']==1
    assert counts['GENERATION','END']==original['generation_calls']==2
    assert counts['Z3_CHECK','END']==original['solver_check_calls']==4
    assert counts['CANDIDATE_LOAD','PASS']==9 and counts['DIFFERENCE_CHECK','END']==9
    assert all(not x['different'] for x in stages if x['phase']=='DIFFERENCE_CHECK')
    assert all(not g['timed_out'] and g['unsupported'] is None for g in original['generations'])
    R['stage_audit']={'disprove':1,'generation_directions':2,'z3_check_calls':4,'candidate_loads':9,'comparisons':9,'parse_passes':counts['ORIGINAL_SQL_PARSE','PASS'],'lowering_passes':counts['QUERY_LOWERING','PASS'],'generation_timed_out':False,'unsupported_reported':False,'baseline_verdict':original['baseline_verdict'],'postbaseline_replay_error':original['error']}
    telemetry_audit={}
    for name in ('synthetic_memory','synthetic_deadline','synthetic_silence','science'):
        receipt=json.loads((SOURCE/name/'RECEIPT.json').read_text())
        ev=[json.loads(x) for x in (SOURCE/name/'telemetry.jsonl').read_text().splitlines()]
        samples=[x for x in ev if x['kind']=='rss']
        assert len(samples)==receipt['samples']
        assert max(x['rss'] for x in samples)==receipt['observed_peak_RSS_bytes']
        gap=max(b['t']-a['t'] for a,b in zip(samples,samples[1:]))
        assert gap==receipt['max_observed_sample_gap_s']
        assert receipt['reaped']
        telemetry_audit[name]={'receipt_matches_telemetry':True,**receipt}
    R['telemetry_audit']=telemetry_audit
    R['notes']=['This audit replayed saved data only; no modified data, no added baseline attempt, no new independent test set.','ru_maxrss observations are historical peaks at sample instants; no claim of hard cap or complete whole-host accounting.','Current hashes prove current file consistency, not cryptographic attestation of all historical execution.']
    assert sha(SOURCE/'science/RESULT.json')==R['source_result_sha256']
    assert sha(SOURCE/'science/error.txt')==R['source_error_sha256']
    R['status']='COMPLETED_SAVED_DATA_AUDIT'

try:
    main()
except BaseException as exc:
    R['status']='AUDIT_ERROR_NO_RETRY'
    R['error']={'type':type(exc).__name__,'message':str(exc)}
    (OUT/'error.txt').write_text(traceback.format_exc())
    raise
finally:
    checkpoint()
    guard.finish()
