"""Original public SQL replay feasibility; NOT a semantic-equivalence oracle."""
from collections import Counter
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import resource
import sqlite3
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(os.environ['CALIBERGRAPH_RUN_OUT'])


def quote(s):
    return '"' + s.replace('"', '""') + '"'


def splitref(x):
    return x['value'].split('__', 1)


def validate(schema, constraints, rows):
    checks = []
    for table, cols in schema.items():
        for row in rows[table]:
            assert set(row) == set(cols), ('ROW_SCHEMA_MISMATCH', table)
            for col, typ in cols.items():
                assert ((typ == 'INT' and type(row[col]) is int) or
                        (typ in ('VARCHAR', 'DATE') and isinstance(row[col], str)))
    for c in constraints or []:
        assert len(c) == 1
        op, terms = next(iter(c.items()))
        if op == 'primary':
            refs = [splitref(x) for x in terms]
            table = refs[0][0]
            assert all(t == table for t, _ in refs)
            values = [tuple(r[col] for _, col in refs) for r in rows[table]]
            assert len(values) == len(set(values)) and all(None not in v for v in values)
        elif op == 'foreign':
            (st, sc), (dt, dc) = map(splitref, terms)
            assert all(r[sc] in {v[dc] for v in rows[dt]} for r in rows[st])
        elif op in ('gte', 'neq'):
            table, col = splitref(terms[0])
            other = terms[1]
            for row in rows[table]:
                if isinstance(other, dict):
                    t2, c2 = splitref(other)
                    assert t2 == table
                    value = row[c2]
                else:
                    value = other
                assert (row[col] >= value) if op == 'gte' else (row[col] != value)
        else:
            raise ValueError('UNSUPPORTED_FULL_CONSTRAINT: ' + op)
        checks.append({'constraint': c, 'status': 'PASS_ON_THIS_FIXTURE_ONLY'})
    return checks


def main():
    start = time.monotonic()
    protocol = json.loads((ROOT/'protocols/natural_replay.json').read_text())
    cases = [json.loads(line) for line in (ROOT/'data/development.jsonl').open()]
    fixtures = json.loads((ROOT/'protocols/natural_fixtures.json').read_text())
    assert len(cases) == 6 and {c['id'] for c in cases} == set(fixtures)
    contract_path = Path(protocol['legacy_contract_path'])
    spec = importlib.util.spec_from_file_location('frozen_legacy_contract', contract_path)
    legacy = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = legacy
    spec.loader.exec_module(legacy)
    records = []
    for case in cases:
        src = case['source_record']
        item = {'id': case['id'], 'source_group_id': case['source_group_id'],
                'source_sql_unchanged': [], 'legacy_full_contract': None,
                'natural_defect_label': 'UNKNOWN', 'fixtures': []}
        try:
            legacy.prepare(src['constraint'], src['schema'])
            item['legacy_full_contract'] = {'status': 'ACCEPTED_PREPARE_ONLY'}
        except legacy.UnverifiedContract as e:
            item['legacy_full_contract'] = {'status': 'REJECTED', 'reason': str(e)}
        for sql, expected in zip(src['pair'], case['original_sql_sha256']):
            actual = hashlib.sha256(sql.encode()).hexdigest()
            assert actual == expected
            item['source_sql_unchanged'].append(actual)
        for name, rows in [('empty', {t: [] for t in src['schema']}), ('tiny_synthetic', fixtures[case['id']])]:
            result = {'fixture': name, 'rows': rows, 'constraint_status': 'NOT_CHECKED', 'queries': []}
            try:
                result['constraint_checks'] = validate(src['schema'], src['constraint'], rows)
                result['constraint_status'] = 'PASS_ON_THIS_NO_NULL_FIXTURE'
                conn = sqlite3.connect(':memory:')
                conn.set_progress_handler(lambda: int(time.monotonic()-start > 10), 1000)
                for table, cols in src['schema'].items():
                    ddl = 'CREATE TABLE '+quote(table)+' ('+', '.join(quote(c)+' '+t for c,t in cols.items())+')'
                    conn.execute(ddl)
                    for row in rows[table]:
                        conn.execute('INSERT INTO '+quote(table)+' VALUES ('+','.join('?' for _ in cols)+')', [row[c] for c in cols])
                conn.execute('PRAGMA query_only=ON')
                for qi, sql in enumerate(src['pair']):
                    tick = time.monotonic()
                    try:
                        cur = conn.execute(sql)
                        values = cur.fetchall()
                        result['queries'].append({'query_index': qi, 'status': 'RETURNED', 'rows': values,
                                                   'column_names': [d[0] for d in cur.description],
                                                   'seconds': time.monotonic()-tick})
                    except sqlite3.Error as e:
                        result['queries'].append({'query_index': qi, 'status': 'SQLITE_ERROR', 'error': str(e),
                                                   'seconds': time.monotonic()-tick})
                conn.close()
                if all(q['status'] == 'RETURNED' for q in result['queries']):
                    a,b = result['queries']
                    result['sqlite_bag_equal_on_this_fixture'] = Counter(map(tuple,a['rows'])) == Counter(map(tuple,b['rows']))
                    result['comparison_scope'] = 'SQLite bag comparison only; not upstream dialect truth, no equivalence conclusion'
            except Exception as e:
                result['constraint_status'] = 'FAILED_OR_UNSUPPORTED'
                result['error'] = str(e)
            item['fixtures'].append(result)
        records.append(item)
    usage = resource.getrusage(resource.RUSAGE_SELF)
    result = {'protocol_id': protocol['id'], 'sqlite_version': sqlite3.sqlite_version,
              'pair_denominator': len(cases), 'query_slots_per_fixture': 12, 'fixture_denominator': 12,
              'query_attempt_denominator': 24, 'results': records,
              'scope': 'All original SQL and full source schema/constraints preserved. Separate literal constraint checker on fixed no-NULL fixtures. SQLite is a replay feasibility control, not a replacement verifier.',
              'worker_usage': {'wall_seconds': time.monotonic()-start, 'cpu_user_seconds': usage.ru_utime,
                               'cpu_system_seconds': usage.ru_stime, 'maxrss_bytes_macos': usage.ru_maxrss}}
    (OUT/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'pairs': len(cases), 'contract_statuses': Counter(x['legacy_full_contract']['status'] for x in records),
                      'query_statuses': Counter(q['status'] for x in records for f in x['fixtures'] for q in f['queries']),
                      'usage': result['worker_usage']}))


if __name__ == '__main__':
    main()
