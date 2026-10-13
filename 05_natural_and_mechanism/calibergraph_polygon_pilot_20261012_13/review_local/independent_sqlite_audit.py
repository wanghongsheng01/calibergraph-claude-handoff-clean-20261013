"""Read frozen inputs/results; independently validate SQLite witnesses. No solver/process calls."""
import collections
import hashlib
import json
from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parents[1]


def quote(name):
    return '"' + name.replace('"', '""') + '"'


def audit_case(case):
    source = ROOT / 'inputs_local' / case
    inventory = json.loads((ROOT / 'inputs_local' / (case + '.json')).read_text())
    ddl = (source / 'full-schema.sql').read_text()
    assert hashlib.sha256((source / 'full-schema.sql').read_bytes()).hexdigest() == inventory['source_ddl_sha256']
    conn = sqlite3.connect(':memory:')
    conn.execute('PRAGMA foreign_keys=ON')
    conn.executescript(ddl)
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_schema WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
    assert tables == {t['table'] for t in inventory['tables']}
    derived_constraints = []
    details = []
    for table in inventory['tables']:
        name = table['table']
        columns = list(conn.execute('PRAGMA table_info(' + quote(name) + ')'))
        assert [(r[1], r[2], bool(r[3]), r[4] == 'NULL') for r in columns] == [
            (c['name'], c['source_type'], c['explicit_not_null'], c['default_null']) for c in table['columns']]
        pk = [r[1] for r in sorted(columns, key=lambda r: r[5]) if r[5]]
        assert pk == table['primary_key']
        if pk:
            derived_constraints.append({'primary': [name + '.' + c for c in pk]})
        derived_constraints.extend({'not_null': name + '.' + r[1]} for r in columns if r[3])
        foreign_keys = list(conn.execute('PRAGMA foreign_key_list(' + quote(name) + ')'))
        expected_fks = {(f['columns'][0], f['target_table'], f['target_columns'][0],
                         'CASCADE' if 'ON UPDATE CASCADE' in f['actions'] else 'NO ACTION',
                         'CASCADE' if 'ON DELETE CASCADE' in f['actions'] else 'NO ACTION') for f in table['foreign_keys']}
        assert {(r[3], r[2], r[4], r[5], r[6]) for r in foreign_keys} == expected_fks
        assert len({r[0] for r in foreign_keys}) == len(foreign_keys), 'unexpected composite FK'
        derived_constraints.extend({'eq': [name + '.' + r[3], r[2] + '.' + r[4]]} for r in foreign_keys)
        details.append({'table': name, 'columns': len(columns), 'primary_key': pk, 'foreign_keys': len(foreign_keys)})
    canonical = lambda x: collections.Counter(json.dumps(r, sort_keys=True) for r in x)
    assert canonical(derived_constraints) == canonical(inventory['proposed_polygon_constraint_entries'])
    conn.close()
    return {'case': case, 'source_ddl_sha256_verified': True, 'complete_column_and_constraint_inventory': True,
            'tables': details, 'column_count': sum(t['columns'] for t in details), 'constraint_entries': len(derived_constraints)}


def replay_witness(case, mode):
    slot = ROOT / 'science_run_01' / (case + '_' + mode)
    result = json.loads((slot / 'RESULT.json').read_text())
    record = {'case': case, 'mode': mode, 'reported_status': result['status'],
              'solver_calls': result['solver_calls'], 'protocol_events': result['protocol_events']}
    witness_path = slot / 'witness.json'
    if not witness_path.exists():
        record['witness_present'] = False
        return record
    source = ROOT / 'inputs_local' / case
    witness = json.loads(witness_path.read_text())
    conn = sqlite3.connect(':memory:')
    try:
        conn.execute('PRAGMA foreign_keys=ON')
        conn.executescript((source / 'full-schema.sql').read_text())
        actual_tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_schema WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
        assert set(witness) == actual_tables
        conn.execute('BEGIN')
        conn.execute('PRAGMA defer_foreign_keys=ON')
        row_counts = {}
        storage_types = {}
        for table, rows in witness.items():
            header = rows[0]
            expected_columns = [r[1] for r in conn.execute('PRAGMA table_info(' + quote(table) + ')')]
            assert len(header) == len(set(header)) and set(header) == set(expected_columns)
            assert 0 <= len(rows) - 1 <= 1
            for row in rows[1:]:
                assert len(row) == len(header)
                assert all(type(v) in (int, str, type(None)) for v in row)
                assert all(type(v) is not int or -(2**63) <= v < 2**63 for v in row)
                conn.execute('INSERT INTO ' + quote(table) + '(' + ','.join(map(quote, header)) + ') VALUES (' + ','.join('?' for _ in row) + ')', row)
            row_counts[table] = len(rows) - 1
            storage_types[table] = list(conn.execute('SELECT ' + ','.join('typeof(' + quote(c) + ')' for c in header) + ' FROM ' + quote(table)))
        foreign_key_check = list(conn.execute('PRAGMA foreign_key_check'))
        assert not foreign_key_check
        conn.commit()
        assert conn.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
        gold = list(conn.execute((source / 'gold.sql').read_text()))
        predicted = list(conn.execute((source / 'predicted.sql').read_text()))
        record.update(witness_present=True, witness_sha256=hashlib.sha256(witness_path.read_bytes()).hexdigest(),
                      full_C_valid=True, bound_N1_verified=True, foreign_key_check=foreign_key_check,
                      row_counts=row_counts, storage_types=storage_types, gold=gold, predicted=predicted,
                      different=collections.Counter(gold) != collections.Counter(predicted),
                      original_ddl_and_sql_unchanged=True)
    except Exception as error:
        record.update(witness_present=True, independent_replay_error=repr(error))
    finally:
        conn.close()
    return record


if __name__ == '__main__':
    frozen = json.loads((ROOT / 'FREEZE.json').read_text())
    mismatches = [p for p, h in frozen['files_sha256'].items() if hashlib.sha256((ROOT / p).read_bytes()).hexdigest() != h]
    assert not mismatches
    output = {'reviewer': 'independent execution/semantic review agent', 'sqlite_version': sqlite3.sqlite_version,
              'frozen_hash_count': len(frozen['files_sha256']), 'hash_mismatches': mismatches,
              'inventory_audits': [audit_case(case) for case in dict.fromkeys(s[0] for s in frozen['slots'])]}
    if (ROOT / 'science_run_01' / 'BATCH_RESULT.json').exists():
        output['slots'] = [replay_witness(*slot) for slot in frozen['slots']]
    (ROOT / 'review_local' / 'SQLITE_AUDIT.json').write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(output, ensure_ascii=False, indent=2))
