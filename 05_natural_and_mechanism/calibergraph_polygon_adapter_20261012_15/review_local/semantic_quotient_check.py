"""Independent original-SQL SQLite checks; no solver or Polygon imports."""
import itertools
import json
import math
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / 'calibergraph_coverage_boundary_20261012_09/sources_local/thrombosis_prediction__1172'
DDL = (SRC / 'full-schema.sql').read_text()
QUERIES = [(SRC / name).read_text() for name in ('gold.sql', 'predicted.sql')]
TABLES = ('Patient', 'Laboratory', 'Examination')


def db():
    c = sqlite3.connect(':memory:')
    c.execute('PRAGMA foreign_keys=ON')
    c.executescript(DDL)
    return c


def quote(s):
    return '"' + s.replace('"', '""') + '"'


def outputs(c):
    return [c.execute(q).fetchone()[0] for q in QUERIES]


def insert(c, table, values):
    c.execute(f'INSERT INTO {quote(table)} ({",".join(map(quote, values))}) VALUES ({",".join("?" for _ in values)})', list(values.values()))


def quotient(c):
    out = db()
    for table in TABLES:
        columns = [r[1] for r in c.execute(f'PRAGMA table_info({quote(table)})')]
        rows = c.execute(f'SELECT * FROM {quote(table)}').fetchall()
        assert len(rows) <= 1
        for row in rows:
            values = dict(zip(columns, (None if x is None else 0 for x in row)))
            values['ID'] = None if row[columns.index('ID')] is None else 1
            if table == 'Patient':
                sex, matches = c.execute("SELECT SEX, SEX = 'M' FROM Patient").fetchone()
                values['SEX'] = None if sex is None else 'M' if matches else 'X'
            if table == 'Laboratory':
                null, ge, gt = c.execute('SELECT `T-BIL` IS NULL, `T-BIL` >= 2.0, `T-BIL` > 2.0 FROM Laboratory').fetchone()
                values['T-BIL'] = None if null else 3.0 if gt else 2.0 if ge else 0.0
                values['Date'] = 0
            insert(out, table, values)
    assert not out.execute('PRAGMA foreign_key_check').fetchall()
    assert outputs(c) == outputs(out)
    for table in TABLES:
        cols = [r[1] for r in c.execute(f'PRAGMA table_info({quote(table)})')]
        null_sql = ','.join(f'{quote(col)} IS NULL' for col in cols)
        assert c.execute(f'SELECT {null_sql} FROM {quote(table)}').fetchall() == out.execute(f'SELECT {null_sql} FROM {quote(table)}').fetchall()
    out.close()


def main():
    values = [None, -math.inf, -9223372036854775808, -0.0, 0, math.nextafter(2.0, -math.inf), 2, 2.0, math.nextafter(2.0, math.inf), 9223372036854775807, math.inf, math.nan, '', '2', '2.0', ' 2 ', '2e0', '2x', 'NaN', 'Inf', '1e999', '0x2', b'', b'2', b'M']
    sexes = [None, 'M', 'X', 'm', 'M ', 'M\x00', '', 0, 2.0, b'M']
    keys = [-9223372036854775808, -1, 0, 1, 9223372036854775807]
    dates = [0, 2.5, '0000-00-00', '', b'', math.inf]
    count = 0
    truth = []
    for value in values:
        c = db()
        insert(c, 'Patient', {'ID': 1, 'SEX': 'M'})
        insert(c, 'Laboratory', {'ID': 1, 'Date': 0, 'T-BIL': value})
        storage, ge, gt, isnull = c.execute('SELECT typeof(`T-BIL`), `T-BIL` >= 2.0, `T-BIL` > 2.0, `T-BIL` IS NULL FROM Laboratory').fetchone()
        truth.append({'input_repr': repr(value), 'storage': storage, 'ge': ge, 'gt': gt, 'isnull': isnull})
        c.close()
    for key, sex, value, date in itertools.product(keys, sexes, values, dates):
        c = db()
        insert(c, 'Patient', {'ID': key, 'SEX': sex, 'Birthday': b'not-a-date', 'Diagnosis': 7})
        insert(c, 'Laboratory', {'ID': key, 'Date': date, 'T-BIL': value, 'GOT': b'x', 'CRP': 2})
        insert(c, 'Examination', {'ID': key, 'Examination Date': 'not-date', 'ANA': 'not-number'})
        quotient(c)
        c.close()
        count += 1
    occupancy = 0
    for patient, lab, examination, exam_null in itertools.product((False, True), repeat=4):
        if (lab or examination and not exam_null) and not patient:
            continue
        c = db()
        if patient:
            insert(c, 'Patient', {'ID': 1, 'SEX': 'M'})
        if lab:
            insert(c, 'Laboratory', {'ID': 1, 'Date': 0, 'T-BIL': 2})
        if examination:
            insert(c, 'Examination', {'ID': None if exam_null else 1})
        quotient(c)
        c.close()
        occupancy += 1
    # FK applies INTEGER parent affinity; legal coercible child values are renamed.
    fk_checks = []
    for parent, child in [(1, '01'), (1, '1.0'), (1, '1e0'), (1, 1.0), (0, -0.0), (-9223372036854775808, float(-9223372036854775808)), (9223372036854775807, '9223372036854775807')]:
        c = db()
        insert(c, 'Patient', {'ID': parent, 'SEX': 'M'})
        try:
            insert(c, 'Laboratory', {'ID': child, 'Date': 0, 'T-BIL': 2})
        except sqlite3.IntegrityError as exc:
            fk_checks.append({'parent': repr(parent), 'child': repr(child), 'source_rejected': str(exc)})
        else:
            quotient(c)
            fk_checks.append({'parent': repr(parent), 'child': repr(child), 'outputs': outputs(c)})
        c.close()
    result = {'sqlite_version': sqlite3.sqlite_version, 'original_ddl': str(SRC / 'full-schema.sql'), 'cross_product_cases': count, 'occupancy_cases': occupancy, 'fk_cases': fk_checks, 'tbil_storage_truth_table': truth, 'result': 'PASS', 'scope': 'Independent SQLite unit checks only; no solver, scientific run, or benchmark result. Universal claim relies on the accompanying argument, not enumeration.'}
    Path(__file__).with_suffix('.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('tbil_storage_truth_table', 'fk_cases')}))


if __name__ == '__main__':
    main()
