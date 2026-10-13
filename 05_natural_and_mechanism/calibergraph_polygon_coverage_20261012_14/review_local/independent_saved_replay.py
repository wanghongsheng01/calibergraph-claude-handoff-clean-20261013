"""Replay saved pilot13 witnesses only; no solver, model repair, or new search."""
from pathlib import Path
import collections
import hashlib
import json
import sqlite3

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
PILOT = ROOT / 'calibergraph_polygon_pilot_20261012_13'
SOURCE = ROOT / 'calibergraph_coverage_boundary_20261012_09'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
quote = lambda s: '"' + s.replace('"', '""') + '"'
frozen = json.loads((PILOT / 'FREEZE.json').read_text())
assert all(sha(PILOT / p) == h for p,h in frozen['files_sha256'].items())
manifest = json.loads((SOURCE / 'CANDIDATES.json').read_text())
candidate = next(c for c in manifest if c['case_id'] == 'superhero__750')
source = PILOT / 'inputs_local' / candidate['case_id']
bindings = {}
for f in ('gold.sql', 'predicted.sql', 'full-schema.sql'):
    expected = candidate['files'][f]['sha256']
    source_path = SOURCE / candidate['files'][f]['local_path']
    pilot_path = source / f
    pilot_relative = str(pilot_path.relative_to(PILOT))
    assert sha(source_path) == sha(pilot_path) == frozen['files_sha256'][pilot_relative] == expected
    bindings[f] = {'frozen_candidate_sha256': expected, 'pilot_freeze_sha256': expected,
                   'source_path': str(source_path.relative_to(ROOT)),
                   'pilot_input_path': str(pilot_path.relative_to(ROOT))}

slots = []
for mode in ('UA', 'precise'):
    slot = PILOT / 'science_run_01' / ('superhero__750_' + mode)
    wp = slot / 'witness.json'
    rp = slot / 'RESULT.json'
    saved = json.loads(rp.read_text())
    witness = json.loads(wp.read_text())
    assert witness == saved['raw_return'][1]
    assert saved['status'] == 'VALIDATED_NEQ'
    db = sqlite3.connect(':memory:')
    db.execute('PRAGMA foreign_keys=ON')
    assert db.execute('PRAGMA foreign_keys').fetchone() == (1,)
    db.executescript((source / 'full-schema.sql').read_text())
    tables = {r[1] for r in db.execute('PRAGMA table_list') if
              r[0] == 'main' and r[2] == 'table' and not r[1].startswith('sqlite_')}
    assert tables == set(witness)
    columns = {t: db.execute('PRAGMA table_info(' + quote(t) + ')').fetchall() for t in tables}
    assert len(tables) == 10 and sum(map(len, columns.values())) == 31
    db.execute('BEGIN')
    db.execute('PRAGMA defer_foreign_keys=ON')
    counts = {}
    for table, rows in witness.items():
        header = rows[0]
        assert len(header) == len(set(header))
        assert set(header) == {r[1] for r in columns[table]}
        assert 0 <= len(rows)-1 <= 1
        counts[table] = len(rows)-1
        for row in rows[1:]:
            assert len(row) == len(header)
            assert all(type(v) in (int, str, type(None)) for v in row)
            assert all(type(v) is not int or -2**63 <= v < 2**63 for v in row)
            db.execute('INSERT INTO ' + quote(table) + '(' + ','.join(map(quote, header)) +
                       ') VALUES (' + ','.join('?' for _ in row) + ')', row)
    violations = db.execute('PRAGMA foreign_key_check').fetchall()
    assert violations == []
    db.commit()
    assert db.execute('PRAGMA integrity_check').fetchone() == ('ok',)
    gold = db.execute((source / 'gold.sql').read_text()).fetchall()
    pred = db.execute((source / 'predicted.sql').read_text()).fetchall()
    assert collections.Counter(gold) != collections.Counter(pred)
    assert [list(v) for v in gold] == saved['replay']['gold']
    assert [list(v) for v in pred] == saved['replay']['predicted']
    db.close()
    slots.append({'case': candidate['case_id'], 'mode': mode,
       'witness_sha256': sha(wp), 'result_sha256': sha(rp),
       'witness_path': str(wp.relative_to(ROOT)), 'result_path': str(rp.relative_to(ROOT)),
       'witness_equals_saved_raw_return': True, 'row_counts': counts,
       'full_original_DDL_executed': True, 'full_original_columns_kept': True,
       'foreign_keys_enabled': True, 'foreign_key_check': violations,
       'transaction_committed': True, 'integrity_check': 'ok',
       'gold': gold, 'predicted': pred, 'different': True,
       'matches_pilot_saved_replay': True, 'new_solver_calls': 0,
       'new_witnesses_generated': 0, 'original_query_replay_executions': 2})

record = {'reviewer': 'independent polygon14 coverage reviewer',
 'sqlite_version': sqlite3.sqlite_version,
 'candidate_manifest_sha256': sha(SOURCE / 'CANDIDATES.json'),
 'pilot_freeze_sha256': sha(PILOT / 'FREEZE.json'),
 'pilot_frozen_file_hashes_verified': len(frozen['files_sha256']),
 'source_commit_record_sha256': sha(PILOT / 'SOURCE.json'),
 'fixed_polygon_commit': json.loads((PILOT / 'SOURCE.json').read_text())['commit'],
 'source_bindings': bindings, 'slots': slots,
 'total_original_query_replay_executions': 4,
 'new_solver_calls': 0, 'new_witnesses_generated': 0,
 'reviewer_script_sha256': sha(Path(__file__)),
 'interpretation': 'Two historical synthetic full-DDL-valid counterexamples independently replayed; no new Polygon scientific attempts and no method superiority evidence.'}
(OUT / 'SAVED_WITNESS_REPLAY.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'sqlite_version': sqlite3.sqlite_version, 'freeze_hashes': len(frozen['files_sha256']),
                  'slots':[{k:r[k] for k in ('mode','gold','predicted','different')} for r in slots]}, indent=2))
