"""Independent saved-result verification; run only by the budget controller.

No Polygon imports, parser calls, SMT translations or solver calls. The Python
reference below implements only the deliberately fixed COUNT test SQL grammar.
"""
from pathlib import Path
import collections
import hashlib
import itertools
import json
import re
import sqlite3

H = Path(__file__).resolve().parents[1]


def bag(rows):
    return collections.Counter(tuple((type(v).__name__, v) for v in r) for r in rows)


def reference(sql, rows, deleted):
    m = re.fullmatch(r'SELECT (g, )?COUNT\((\*|x|DISTINCT x)\)(?: FILTER \(WHERE (1|0|NULL|x)\))? FROM t( GROUP BY g)?', sql)
    assert m, sql
    grouped, arg, filt, suffix = m.groups()
    assert bool(grouped) == bool(suffix)
    live = [r for r, d in zip(rows, deleted) if not d]
    groups = {}
    if grouped:
        for x, g in live:
            groups.setdefault(g, []).append([x, g])
    else:
        groups[None] = live
    result = []
    for g, members in groups.items():
        eligible = [r for r in members if filt is None or filt == '1' or (filt == 'x' and r[0] is not None and r[0] != 0)]
        if arg == '*':
            n = len(eligible)
        elif arg == 'x':
            n = sum(r[0] is not None for r in eligible)
        else:
            n = len({r[0] for r in eligible if r[0] is not None})
        result.append([g, n] if grouped else [n])
    return result


def sqlite_reference(case):
    rows, deleted = case['rows'], case['deleted']
    assert len(rows) == len(deleted)
    assert all(type(d) is bool for d in deleted)
    assert all(len(r) == 2 and all(v is None or type(v) is int for v in r) for r in rows)
    db = sqlite3.connect(':memory:')
    try:
        db.execute('PRAGMA threads=0')
        db.execute('CREATE TABLE t(x INTEGER, g INTEGER)')
        db.executemany('INSERT INTO t(x,g) VALUES (?,?)', [r for r, d in zip(rows, deleted) if not d])
        return [list(r) for r in db.execute(case['sql'])]
    finally:
        db.close()


def run():
    path = H / 'PARSER_RESULTS_V2.json'
    saved = json.loads(path.read_text())
    assert set(saved['versions']) == {'original', 'p1', 'p2', 'p3'}
    assert saved['watchdog_adapter']['real_threads_started'] == 0
    assert saved['watchdog_adapter']['unresolved_exports'] == 0
    expected_matrix = {}
    for n in (0, 1, 2):
        for ds in itertools.product((False, True), repeat=n):
            for filt in ('absent', '1', '0', 'NULL'):
                ident = f'b{n}_{list(ds)}_{filt}'
                sql = 'SELECT COUNT(*)' + ('' if filt == 'absent' else f' FILTER (WHERE {filt})') + ' FROM t'
                expected_matrix[ident] = (sql, [[None, 0]] * n, list(ds))
    pipeline_ids = {'empty', 'null_row', 'duplicates', 'count_x_null', 'count_distinct', 'filter_null_column', 'group_empty', 'group_duplicates', 'group_null_keys', 'group_false', 'group_filter_null', 'group_filter_values', 'group_deleted', 'group_count_x'}
    group_failures = {'group_false', 'group_filter_null', 'group_filter_values', 'group_deleted'}
    checks = []
    originals = {}
    for ver, version in saved['versions'].items():
        assert set(version) == {'matrix', 'pipeline'}
        for kind, cases in version.items():
            expected_ids = set(expected_matrix) if kind == 'matrix' else pipeline_ids
            assert len(cases) == len(expected_ids)
            assert {c['id'] for c in cases} == expected_ids
            for c in cases:
                key = kind, c['id']
                identity = (c['sql'], c['rows'], c['deleted'])
                if kind == 'matrix':
                    assert identity == expected_matrix[c['id']]
                if ver == 'original':
                    originals[key] = identity
                else:
                    assert identity == originals[key], ('case changed across versions', key)
                sq = sqlite_reference(c)
                py = reference(*identity)
                assert bag(sq) == bag(py), ('independent oracle mismatch', ver, key)
                if c['status'] != 'ERROR':
                    assert bag(c['sqlite']) == bag(sq)
                    matches = bag(c['actual']) == bag(sq)
                    assert c['matches'] is matches
                    assert c['status'] == ('PASS' if matches else 'MISMATCH')
                    assert c['parser_json'] is not None and c['parsed_ast']
                    if kind == 'pipeline':
                        grouped = 'GROUP BY' in c['sql']
                        assert c['all_real_operator_formulas_satisfied'] is True
                        assert c['operator_formula_count'] == (2 if grouped else 1)
                        assert c['operators'] == (['FGroupBy', 'FProject'] if grouped else ['FProject'])
                else:
                    assert c.get('error')
                if ver == 'p3':
                    assert c['status'] == 'PASS', (ver, key, c)
                elif ver in ('p1', 'p2'):
                    failures = (group_failures | {'filter_null_column'}) if ver == 'p1' else {'filter_null_column', 'group_filter_values', 'group_deleted'}
                    assert c['status'] == ('MISMATCH' if kind == 'pipeline' and c['id'] in failures else 'PASS'), (ver, key, c)
                elif kind == 'matrix':
                    n = len(c['rows'])
                    filtered = 'FILTER' in c['sql']
                    expected_status = 'ERROR' if filtered and n >= 2 else ('MISMATCH' if not filtered and any(not d for d in c['deleted']) else 'PASS')
                    assert c['status'] == expected_status, (ver, key, c)
                else:
                    expected_status = 'ERROR' if c['id'] == 'filter_null_column' else ('MISMATCH' if c['id'] in group_failures | {'null_row', 'duplicates'} else 'PASS')
                    assert c['status'] == expected_status, (ver, key, c)
                if kind == 'pipeline' and c['id'] in {'filter_null_column', 'group_filter_values', 'group_deleted'} and c['status'] != 'ERROR':
                    expected_ast = "filter_clause=Attribute(name='x')" if ver == 'p3' else "filter_clause=Literal(value='x')"
                    assert expected_ast in c['parsed_ast'], (ver, key, c['parsed_ast'])
                checks.append({'version': ver, 'kind': kind, 'id': c['id'], 'sqlite': sq, 'python_reference': py, 'saved_status': c['status']})
    return {'status': 'PASS', 'source_result_sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'sqlite_version': sqlite3.sqlite_version, 'checks': checks, 'count': len(checks), 'scope': 'Independent fresh SQLite and Python COUNT reference for saved cases; operator formula execution is reviewed from author code and records, not independently re-executed here.', 'target_imports': 0, 'solver_calls': 0}


if __name__ == '__main__':
    result = {'status': 'INTERRUPTED'}
    try:
        result = run()
    except Exception as exc:
        result = {'status': 'FAIL', 'error': repr(exc)}
        raise
    finally:
        with (H / 'review_local' / 'VERIFY_RESULTS_V2.json').open('x') as output:
            json.dump(result, output, indent=2, ensure_ascii=False)
            output.write('\n')
