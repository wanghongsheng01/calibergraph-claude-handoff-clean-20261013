"""Read-only input audit; stdlib SQLite only; no author imports or subprocesses."""
import hashlib
import json
from pathlib import Path
import sqlite3

HERE = Path(__file__).resolve().parent
RUN = HERE.parent
ROOT = RUN.parent
SRC = ROOT / 'calibergraph_coverage_boundary_20261012_09/sources_local/thrombosis_prediction__1172'
OLD = ROOT / 'calibergraph_polygon_adapter_20261012_15'
def read(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def q(s): return '"' + s.replace('"', '""') + '"'
source_sha = {
    'gold.sql': '40340161f8fdb34f6c1a5c0b06a6856f2acf70e81e26e3592f949ff9a2e1c1bb',
    'predicted.sql': '6a9c0f524cf75c75a3d79af59984b9b8b82992a490dd9f8cbf67af8173f82545',
    'full-schema.sql': 'c4073e59ae5daffad317c7c8938f9839afb68e4fe99ca826480027dea88e58e4',
}
freeze = read(RUN / 'FREEZE.json')
assert freeze['solver_execution_authorized'] is True
assert read(OLD / 'FREEZE.json')['solver_execution_authorized'] is False
assert read(RUN / 'ATTEMPT_STARTED.json')['freeze_sha256'] == sha(RUN / 'FREEZE.json')
assert read(RUN / 'ATTEMPT_STARTED.json')['no_retries'] is True
assert (freeze['batch_wall_s'], freeze['per_solver_wall_s'], freeze['per_z3_internal_MiB'], freeze['bound']) == (60, 3, 512, 1)
for rel, digest in freeze['files_sha256'].items(): assert sha(RUN / rel) == digest, rel
preservation = read(RUN / 'OLD_PRESERVATION.json')
for item in preservation['checks']: assert sha(ROOT / item['path']) == item['sha256'], item['path']
for name, digest in source_sha.items(): assert sha(SRC / name) == digest
ddl = (SRC / 'full-schema.sql').read_text()
def fresh():
    db = sqlite3.connect(':memory:')
    db.execute('PRAGMA foreign_keys=ON')
    assert db.execute('PRAGMA foreign_keys').fetchone() == (1,)
    db.executescript(ddl)
    return db
db = fresh()
tables = [r[0] for r in db.execute("SELECT name FROM sqlite_schema WHERE type='table' ORDER BY name")]
assert tables == ['Examination', 'Laboratory', 'Patient']
info = {t: db.execute('PRAGMA table_info(' + q(t) + ')').fetchall() for t in tables}
assert {t: len(cols) for t, cols in info.items()} == {'Examination': 13, 'Laboratory': 44, 'Patient': 7}
pk = {t: [c[1] for c in sorted(cols, key=lambda c: c[5]) if c[5]] for t, cols in info.items() if any(c[5] for c in cols)}
nn = sorted((t, c[1]) for t, cols in info.items() for c in cols if c[3])
fk = {t: db.execute('PRAGMA foreign_key_list(' + q(t) + ')').fetchall() for t in tables}
assert pk == {'Laboratory': ['ID', 'Date'], 'Patient': ['ID']}
assert nn == [('Laboratory', 'Date'), ('Laboratory', 'ID'), ('Patient', 'ID')]
assert fk['Patient'] == []
for t in ['Examination', 'Laboratory']:
    assert len(fk[t]) == 1 and fk[t][0][2:] == ('Patient', 'ID', 'ID', 'CASCADE', 'CASCADE', 'NONE')
signature = db.execute("SELECT name,sql FROM sqlite_schema WHERE type='table' ORDER BY name").fetchall()
db.close()

def validate_and_lift(a):
    # Independent implementation of the declared finite observation classes.
    assert set(a) == {t.lower() for t in tables}
    rows = {}
    for t in tables:
        tab = a[t.lower()]
        names = [c[1].lower() for c in info[t]]
        assert len(tab) in (1, 2) and len(tab[0]) == len(set(tab[0]))
        assert set(tab[0]) == set(names)
        rows[t] = dict(zip(tab[0], tab[1])) if len(tab) == 2 else None
        if rows[t] is None: continue
        assert len(tab[1]) == len(names)
        for c in info[t]:
            v = rows[t][c[1].lower()]
            assert not ((c[3] or c[5]) and v is None)
            assert v is None or type(v) is (str if (t, c[1]) == ('Patient', 'SEX') else int)
    for t in ['Examination', 'Laboratory']:
        if rows[t] is not None and rows[t]['id'] is not None:
            assert rows['Patient'] is not None and rows[t]['id'] == rows['Patient']['id']
    out = {}
    for t in tables:
        out[t] = [[c[1] for c in info[t]]]
        if rows[t] is None: continue
        line = []
        for c in info[t]:
            v = rows[t][c[1].lower()]
            if v is None: line.append(None)
            elif c[1] == 'ID': line.append(1)
            elif (t, c[1]) == ('Patient', 'SEX'): line.append('M' if v == 'M' else 'X')
            elif (t, c[1]) == ('Laboratory', 'T-BIL'): line.append({-1: 0.0, 0: 2.0, 1: 3.0}[(v > 2) - (v < 2)])
            else: line.append(0)
        out[t].append(line)
    return out

batch = read(RUN / 'science_run_01/BATCH_RESULT.json')
assert batch['wall_budget_s'] == 60 and batch['elapsed_s'] < 60
assert [(r['case'], r['mode']) for r in batch['records']] == [tuple(s) for s in freeze['slots']]
assert batch['science_attempts'] == len(batch['records']) == 2
guard = batch['guard']
assert guard['all_reaped'] and guard['handle_count'] == 5 and not guard['cleanup_errors'] and guard['reason'] is None
spawn = [e for e in guard['events'] if e['kind'] == 'spawn']
waits = [e for e in guard['events'] if e['kind'] == 'wait']
assert len(spawn) == len(guard['returncodes']) == 5
for e in spawn:
    matches = [w for w in waits if w['pid_for_logging_only'] == e['pid_for_logging_only']]
    assert matches and all(w['returncode'] == guard['returncodes'][e['index']] for w in matches)
ua_pids = {e['pid_for_logging_only'] for e in spawn[:3]}
assert all(any(w['pid_for_logging_only'] == p and w['monotonic'] < spawn[3]['monotonic'] for w in waits) for p in ua_pids)
records = []
for record in batch['records']:
    mode = record['mode']
    slot = RUN / 'science_run_01' / ('thrombosis_prediction__1172_' + mode)
    result, a, concrete = [read(slot / n) for n in ['RESULT.json', 'abstract_witness.json', 'witness.json']]
    assert read(slot / 'CONTROLLER.json') == record
    assert a == result['raw_return'][1] == result['raw_return'][4]['cex']
    lifted = validate_and_lift(a)
    # Canonical JSON checks types as well as values (2.0 must not silently equal 2).
    assert json.dumps(lifted, sort_keys=True) == json.dumps(concrete, sort_keys=True)
    db = fresh()
    for t in ['Patient', 'Examination', 'Laboratory']:
        tab = concrete[t]
        assert tab[0] == [c[1] for c in info[t]] and len(tab) in (1, 2)
        db.executemany('INSERT INTO '+q(t)+' ('+','.join(map(q, tab[0]))+') VALUES ('+','.join('?' for _ in tab[0])+')', tab[1:])
    db.commit()
    assert db.execute('PRAGMA foreign_key_check').fetchall() == []
    assert db.execute('PRAGMA integrity_check').fetchall() == [('ok',)]
    assert db.execute("SELECT name,sql FROM sqlite_schema WHERE type='table' ORDER BY name").fetchall() == signature
    outputs = [db.execute((SRC / n).read_text()).fetchall() for n in ['gold.sql', 'predicted.sql']]
    assert outputs == [[(1,)], [(0,)]]
    counts = {t: db.execute('SELECT count(*) FROM '+q(t)).fetchone()[0] for t in tables}
    assert all(n <= 1 for n in counts.values())
    db.close()
    assert result['status'] == record['status'] == 'VALIDATED_NEQ'
    calls = result['solver_calls']
    assert len(calls) == len(record['native_launches']) == (2 if mode == 'UA' else 1)
    assert all(c['state'] == 'SAT' and c['elapsed_s'] < 3 for c in calls)
    assert all(x['args'][1:] == ['--in', '-T:3', '-memory:512'] for x in record['native_launches'])
    assert record['worker_returncode'] == 0 and record['all_slot_handles_reaped']
    assert not result['protocol_events']
    assert all(v is not None and v >= 0 for v in result['stages_seconds'].values())
    records.append({'mode': mode, 'status': result['status'], 'outputs': outputs, 'row_counts': counts, 'fixed_lift_exact': True,
                    'abstract_C_valid_before_lift': True, 'original_C_valid': True, 'solver_calls': calls,
                    'stages_seconds': result['stages_seconds'], 'wall_elapsed_s': record['wall_elapsed_s']})
report = {'passed': True, 'sqlite_version': sqlite3.sqlite_version, 'review_solver_calls': 0,
          'frozen_files_checked': len(freeze['files_sha256']), 'preserved_files_checked': len(preservation['checks']),
          'source_sha256': source_sha, 'tables': 3, 'columns': 64, 'PK_declarations': pk, 'explicit_NN': nn,
          'FK_declarations': fk, 'constraint_declaration_total': 7, 'old_gate': False, 'new_gate': True,
          'denominator_slots': 2, 'validated_NEQ': 2, 'unknown_or_failed_slots': 0, 'native_solver_checks': 3,
          'batch_elapsed_s': batch['elapsed_s'], 'owned_handles_reaped': 5, 'returncodes': guard['returncodes'],
          'slot_seriality_verified': True, 'aggregate_RSS_verified': False, 'records': records,
          'reviewed_input_sha256': {str(p.relative_to(ROOT)): sha(p) for p in [RUN/'FREEZE.json', RUN/'ATTEMPT_STARTED.json', *sorted((RUN/'science_run_01').rglob('*'))] if p.is_file()}}
(HERE / 'independent_replay.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
print(json.dumps({k: report[k] for k in ['passed', 'tables', 'columns', 'constraint_declaration_total', 'validated_NEQ', 'denominator_slots', 'native_solver_checks', 'owned_handles_reaped', 'batch_elapsed_s']}))
