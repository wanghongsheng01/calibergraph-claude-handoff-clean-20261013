"""Independent post-author checks; run ONLY inside the parent's one-shot 60s batch.

No solver/parser/Environment, no subprocess, no network, no author validation import.
Original frozen SQLite instances are rebuilt from stored rows; COUNT uses real
ExpressionEncoder ASTs and an independent strict typed evaluator.
"""
from pathlib import Path
from collections import Counter
import difflib
import hashlib
import importlib.util
import itertools
import json
import math
import re
import sqlite3
import sys
import time
import traceback
import types

HERE = Path(__file__).resolve().parent
RUN = HERE.parent
ROOT = RUN.parent
EXPECTED_IDS = {
    '1073_invalid_date': 'european_football_2__1073',
    '1073_nullable_pk': 'european_football_2__1073',
    '45_text_N1': 'california_schools__45',
    '45_large_int_N1': 'california_schools__45',
    '45_group_N2': 'california_schools__45',
    '45_bag_N2': 'california_schools__45',
    '1526_N1': 'debit_card_specializing__1526',
    '1526_sum_scalar': 'debit_card_specializing__1526',
}
EXPECTED_SHAPE = {
    '1073_invalid_date': (1, 2), '1073_nullable_pk': (1, 2),
    '45_text_N1': (1, 2), '45_large_int_N1': (1, 2),
    '45_group_N2': (2, 4), '45_bag_N2': (2, 4),
    '1526_N1': (1, 4), '1526_sum_scalar': (3, 7),
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def quote(name):
    return '"' + name.replace('"', '""') + '"'


def decode(v):
    if isinstance(v, dict):
        if set(v) == {'__sqlite_blob_hex__'}:
            return bytes.fromhex(v['__sqlite_blob_hex__'])
        if set(v) == {'__sqlite_real__'} and v['__sqlite_real__'] in ('inf', '-inf'):
            return float(v['__sqlite_real__'])
        raise ValueError('Unrecognized cell tag')
    if v is None or type(v) in (int, str):
        return v
    if type(v) is float and not math.isnan(v):
        return v
    raise ValueError('Unsupported cell type (bool is not an SQLite value tag)')


def encode(v):
    if isinstance(v, bytes):
        return {'__sqlite_blob_hex__': v.hex()}
    if type(v) is float and not math.isfinite(v):
        return {'__sqlite_real__': 'inf' if v > 0 else '-inf'}
    return v


def scalar_key(v, storage=False):
    if v is None:
        return ('null',)
    if type(v) in (int, float):
        assert not (type(v) is float and math.isnan(v))
        # Python equality/hash exactly compares int with float; it does not cast
        # a large int to binary64 first. 9007199254740993 != 9007199254740992.0.
        return (type(v).__name__ if storage else 'number', v)
    if type(v) is str:
        return ('text', v)
    if type(v) is bytes:
        return ('blob', v)
    raise TypeError(type(v).__name__)


def bag(rows, storage=False):
    return Counter(tuple(scalar_key(v, storage) for v in row) for row in rows)


def validate_replays():
    source_list_path = ROOT / 'calibergraph_coverage_boundary_20261012_09/CANDIDATES.json'
    candidates = {x['case_id']: x for x in json.loads(source_list_path.read_text())}
    recorded = json.loads((RUN / 'replays.json').read_text())
    assert recorded['format_version'] == 1
    assert len(recorded['cases']) == len(EXPECTED_IDS)
    assert {x['candidate_id'] for x in recorded['cases']} == set(EXPECTED_IDS)
    rows = []
    for case in recorded['cases']:
        started = time.monotonic()
        cid = case['candidate_id']
        assert case['case_id'] == EXPECTED_IDS[cid]
        assert case['status'] == 'VALIDATED_NEQ'
        source = ROOT / 'calibergraph_coverage_boundary_20261012_09/sources_local' / case['case_id']
        reported_dir = Path(case['source']['directory'])
        if not reported_dir.is_absolute():
            reported_dir = ROOT / reported_dir
        assert reported_dir.resolve() == source.resolve()
        verified_hashes = {}
        for name in ('gold.sql', 'predicted.sql', 'full-schema.sql'):
            actual = sha(source / name)
            assert actual == candidates[case['case_id']]['files'][name]['sha256']
            assert actual == case['source']['files'][name]['sha256']
            verified_hashes[name] = actual
        db = sqlite3.connect(':memory:')
        try:
            db.execute('PRAGMA foreign_keys=ON')
            db.execute('PRAGMA threads=0')
            assert db.execute('PRAGMA foreign_keys').fetchone() == (1,)
            db.executescript((source / 'full-schema.sql').read_text())
            names = [r[0] for r in db.execute("SELECT name FROM main.sqlite_schema WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
            assert set(case['tables']) == set(names)
            db.execute('BEGIN')
            db.execute('PRAGMA defer_foreign_keys=ON')
            meta = {}
            intended = {}
            for table in names:
                info = db.execute('PRAGMA table_info(' + quote(table) + ')').fetchall()
                columns = [c[1] for c in info]
                data = case['tables'][table]
                assert data['columns'] == columns and len(columns) == len(set(columns))
                intended[table] = [[decode(v) for v in r] for r in data['stored_rows']]
                assert all(len(r) == len(columns) for r in intended[table])
                indexes = db.execute('PRAGMA index_list(' + quote(table) + ')').fetchall()
                meta[table] = {
                    'table_info': info,
                    'foreign_key_list': db.execute('PRAGMA foreign_key_list(' + quote(table) + ')').fetchall(),
                    'index_list': indexes,
                    'unique_indexes': {idx[1]: db.execute('PRAGMA index_info(' + quote(idx[1]) + ')').fetchall() for idx in indexes if idx[2]},
                }
                db.executemany('INSERT INTO ' + quote(table) + ' (' + ','.join(map(quote, columns)) + ') VALUES (' + ','.join('?' for _ in columns) + ')', intended[table])
            fk = db.execute('PRAGMA foreign_key_check').fetchall()
            assert not fk, fk
            db.commit()  # also enforces deferred source foreign keys
            integrity = db.execute('PRAGMA integrity_check').fetchall()
            assert integrity == [('ok',)], integrity
            constraints = []
            storage = {}
            for table in names:
                info = meta[table]['table_info']
                cols = [c[1] for c in info]
                stored = db.execute('SELECT ' + ','.join(map(quote, cols)) + ' FROM ' + quote(table)).fetchall()
                assert bag(stored, storage=True) == bag(intended[table], storage=True), ('storage changed', cid, table)
                types_rows = db.execute('SELECT ' + ','.join('typeof(' + quote(c) + ')' for c in cols) + ' FROM ' + quote(table)).fetchall()
                storage[table] = {'rows': [[encode(v) for v in r] for r in stored], 'types': types_rows}
                pk = [c for c in info if c[5]]
                for c in info:
                    # Do not strengthen nullable INT/TEXT PRIMARY KEY into NOT NULL.
                    ipk_alias = len(pk) == 1 and c[5] and c[2].upper() == 'INTEGER'
                    if c[3] or ipk_alias:
                        null_count = db.execute('SELECT COUNT(*) FROM ' + quote(table) + ' WHERE ' + quote(c[1]) + ' IS NULL').fetchone()[0]
                        assert null_count == 0
                        constraints.append({'table': table, 'column': c[1], 'check': 'declared NN or INTEGER PK alias', 'violations': 0})
                # Source DDL itself enforces PK and UNIQUE. Also query each declared
                # unique index with SQLite's NULL-distinct rule; include non-NULL
                # keys only instead of silently prohibiting nullable unique keys.
                for index, index_cols in meta[table]['unique_indexes'].items():
                    indexed = [r[2] for r in index_cols]
                    assert all(x is not None for x in indexed), 'Expression index unsupported in these frozen sources'
                    violations = db.execute('SELECT COUNT(*) FROM ' + quote(table) + ' WHERE ' + ' AND '.join(quote(c) + ' IS NOT NULL' for c in indexed) + ' GROUP BY ' + ','.join(map(quote, indexed)) + ' HAVING COUNT(*) > 1').fetchall()
                    assert not violations
                    constraints.append({'table': table, 'index': index, 'check': 'PK/UNIQUE non-NULL duplicate groups', 'violations': []})
            computed = {label: [list(r) for r in db.execute((source / filename).read_text()).fetchall()] for label, filename in [('gold', 'gold.sql'), ('predicted', 'predicted.sql')]}
            for label in computed:
                expected = [[decode(v) for v in r] for r in case['outputs'][label]]
                assert bag(computed[label]) == bag(expected), (cid, label, computed[label], expected)
            assert bag(computed['gold']) != bag(computed['predicted'])
            shape = {t: len(intended[t]) for t in names}
            assert (max(shape.values()), sum(shape.values())) == EXPECTED_SHAPE[cid]
            rows.append({'candidate_id': cid, 'case_id': case['case_id'], 'status': 'INDEPENDENTLY_REPLAYED_NEQ', 'source_hashes': verified_hashes, 'all_source_tables_columns_preserved': True, 'full_DDL_enforced': True, 'foreign_key_check': fk, 'integrity_check': integrity, 'explicit_constraint_checks': constraints, 'source_metadata': meta, 'stored_values_and_types': storage, 'outputs': computed, 'bag_different': True, 'N': max(shape.values()), 'total_source_rows': sum(shape.values()), 'row_counts': shape, 'elapsed_s': time.monotonic() - started})
        finally:
            db.close()
    return {'status': 'PASS', 'sqlite_version': sqlite3.sqlite_version, 'independent_source_catalog_sha256': sha(source_list_path), 'author_record_sha256': sha(RUN / 'replays.json'), 'cases': rows, 'method': 'Fresh original-DDL SQLite database for every candidate, no author validator functions; exact stored type/NULL preservation and numeric-aware unordered bags'}


def apply_unified_patch(original, patch):
    lines = original.splitlines(keepends=True)
    patch_lines = patch.splitlines(keepends=True)
    output = []
    position = 0
    i = 0
    hunks = 0
    removed = []
    added = []
    while i < len(patch_lines):
        line = patch_lines[i]
        if not line.startswith('@@ '):
            assert line.startswith(('--- ', '+++ ')) or not line.strip(), ('unexpected patch line', line)
            i += 1
            continue
        m = re.match(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@', line)
        assert m
        start = int(m.group(1)) - 1
        assert start >= position
        output.extend(lines[position:start])
        position = start
        i += 1
        hunks += 1
        while i < len(patch_lines) and not patch_lines[i].startswith('@@ '):
            line = patch_lines[i]
            if line.startswith(' '):
                assert lines[position] == line[1:]
                output.append(line[1:]); position += 1
            elif line.startswith('-') and not line.startswith('--- '):
                assert lines[position] == line[1:]
                removed.append(line[1:]); position += 1
            elif line.startswith('+') and not line.startswith('+++ '):
                output.append(line[1:]); added.append(line[1:])
            else:
                raise AssertionError(('Unsupported unified patch line', line))
            i += 1
    output.extend(lines[position:])
    assert hunks == 1 and len(removed) == len(added) == 1
    return ''.join(output), removed, added


def evaluate_typed(node, deleted):
    """Independent strict AST evaluation; bool arithmetic is rejected, not coerced."""
    name = type(node).__name__
    if name == 'Int':
        assert type(node.x) is int
        return 'Int', node.x
    if name == 'Bool':
        assert type(node.x) is bool
        return 'Bool', node.x
    if name == 'Deleted':
        return 'Bool', deleted[node.tuple_id]
    if name == 'Not':
        t, v = evaluate_typed(node.node, deleted)
        if t != 'Bool': raise TypeError('Not requires Bool')
        return 'Bool', not v
    if name in ('And', 'Or'):
        args = node.conjunct if name == 'And' else node.disjunct
        vals = [evaluate_typed(x, deleted) for x in args]
        if any(t != 'Bool' for t, v in vals): raise TypeError(name + ' requires Bool operands')
        return 'Bool', all(v for t, v in vals) if name == 'And' else any(v for t, v in vals)
    if name == 'If':
        a, b, c = [evaluate_typed(x, deleted) for x in (node.a, node.b, node.c)]
        if a[0] != 'Bool' or b[0] != c[0]: raise TypeError('If sort mismatch')
        return b if a[1] else c
    if name in ('Eq', 'Neq'):
        a, b = [evaluate_typed(x, deleted) for x in (node.a, node.b)]
        if a[0] != b[0]: raise TypeError(name + ' sort mismatch')
        return 'Bool', (a[1] == b[1]) if name == 'Eq' else (a[1] != b[1])
    if name == 'Plus':
        a, b = [evaluate_typed(x, deleted) for x in (node.a, node.b)]
        if a[0] != 'Int' or b[0] != 'Int': raise TypeError('Plus requires Int operands; got ' + a[0] + ',' + b[0])
        return 'Int', a[1] + b[1]
    raise TypeError('Unexpected AST node: ' + name)


def ast_tree(node):
    name = type(node).__name__
    if name in ('Int', 'Bool'): return {'node': name, 'value': node.x}
    if name == 'Deleted': return {'node': name, 'table_id': node.table_id, 'tuple_id': node.tuple_id}
    if name == 'Not': return {'node': name, 'child': ast_tree(node.node)}
    if name in ('And', 'Or'): return {'node': name, 'children': [ast_tree(x) for x in (node.conjunct if name == 'And' else node.disjunct)]}
    if name in ('Eq', 'Neq', 'Plus'): return {'node': name, 'left': ast_tree(node.a), 'right': ast_tree(node.b)}
    if name == 'If': return {'node': name, 'condition': ast_tree(node.a), 'then': ast_tree(node.b), 'else': ast_tree(node.c)}
    raise TypeError('Unexpected AST node for record: ' + name)


def validate_count_ast():
    runtime = ROOT / 'calibergraph_polygon_pilot_20261012_13/runtime_local'
    dependencies = ROOT / 'calibergraph_polygon_pilot_20261012_13/dependencies_local'
    source = runtime / 'polygon/visitors/expression_encoder.py'
    evidence = json.loads((ROOT / 'calibergraph_remaining_four_analysis_20261012_18/SOURCE_EVIDENCE.json').read_text())
    frozen_hash = next(x['sha256'] for x in evidence['source_files'] if x['path'].endswith('polygon/visitors/expression_encoder.py'))
    assert sha(source) == frozen_hash
    original = source.read_text()
    patch = (RUN / 'COUNT_STAR.patch').read_text()
    patched, removed, added = apply_unified_patch(original, patch)
    old_line = '                            indicators.append(Not(deleted))\n'
    new_line = '                        indicators.append(If(Not(deleted), Int(1), Int(0)))\n'
    assert original.count(old_line) == 1
    assert removed == [old_line] and added == [new_line]
    assert patched == original.replace(old_line, new_line, 1), 'Patch changed anything beyond the single intended statement'
    sys.path[:0] = [str(runtime), str(dependencies)]
    # This is the original file's actual class, not a reimplementation of its body.
    spec = importlib.util.spec_from_file_location('independent_original_expression_encoder', source)
    original_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(original_module)
    patched_module = types.ModuleType('independent_patched_expression_encoder')
    patched_module.__file__ = str(source) + ':single_statement_patch_in_memory'
    exec(compile(patched, patched_module.__file__, 'exec'), patched_module.__dict__)
    from polygon.ast.expressions.expression import Expression
    from polygon.ast.expressions.attribute import Attribute
    from polygon.ast.expressions.literal import Literal
    # No parser, Environment or SMTLIBv2 prover is instantiated. Only the real
    # encoder and its AST classes are imported and called for this focused unit.
    rows = []
    defect_counts = {'unfiltered_value_mismatch': 0, 'filtered_type_error': 0}
    modes = [('absent', None), ('true', True), ('false', False), ('null', None)]
    for name, module in [('original', original_module), ('patched', patched_module)]:
        for bound in (0, 1, 2):
            table = types.SimpleNamespace(table_id=901, bound=bound)
            for mask in itertools.product((False, True), repeat=bound):
                for filter_name, literal_value in modes:
                    clause = None if filter_name == 'absent' else Literal(literal_value)
                    exp = Expression('count', [False, Attribute('*')], filter_clause=clause)
                    encoder = module.ExpressionEncoder(table, types.SimpleNamespace())
                    val, null = encoder.expression_for_tuple(exp, 0)
                    expected = sum(not d for d in mask) if filter_name in ('absent', 'true') else 0
                    record = {'version': name, 'bound': bound, 'deleted': list(mask), 'filter': filter_name, 'expected_sql_count': expected, 'actual_AST': ast_tree(val), 'null_AST': ast_tree(null)}
                    assert evaluate_typed(null, mask) == ('Bool', False)
                    try:
                        sort, actual = evaluate_typed(val, mask)
                        assert sort == 'Int'
                        record.update(actual_count=actual, type_valid=True, matches_SQL_count=actual == expected)
                    except TypeError as exc:
                        record.update(type_valid=False, type_error=str(exc), matches_SQL_count=False)
                    if name == 'patched':
                        assert record['matches_SQL_count'], record
                    elif filter_name == 'absent':
                        assert record['type_valid'] and record['actual_count'] == 0
                        if expected != 0: defect_counts['unfiltered_value_mismatch'] += 1
                    elif bound == 2:
                        assert not record['type_valid'] and 'Plus requires Int' in record['type_error']
                        defect_counts['filtered_type_error'] += 1
                    else:
                        assert record['matches_SQL_count'], record
                    rows.append(record)
    assert defect_counts == {'unfiltered_value_mismatch': 4, 'filtered_type_error': 12}
    assert len(rows) == 56
    assert sha(source) == frozen_hash, 'Upstream source changed'
    return {'status': 'PASS', 'original_encoder_sha256': frozen_hash, 'patch_sha256': sha(RUN / 'COUNT_STAR.patch'), 'patched_text_sha256': hashlib.sha256(patched.encode()).hexdigest(), 'patch_exactly_one_statement': True, 'upstream_unchanged': True, 'real_ExpressionEncoder_AST': True, 'author_count_record_sha256': sha(RUN / 'count_star_results.json'), 'defects_reproduced_in_original': defect_counts, 'patched_cases_passed': 28, 'tests': rows, 'solver_calls': 0, 'parser_runs': 0, 'scope': 'Direct AST unit only, not an end-to-end proof of the original SQL parser path or full Polygon correctness'}


def main():
    started = time.monotonic()
    def audit(event, args):
        if event in ('subprocess.Popen', 'os.system', 'os.posix_spawn', 'os.spawn', 'socket.connect', 'socket.bind'):
            raise RuntimeError('Independent validator forbids native launch/network: ' + event)
    sys.addaudithook(audit)
    report = {'status': 'STARTED', 'reviewer_solver_calls': 0, 'reviewer_native_launches': 0, 'reviewer_network_requests': 0}
    try:
        report['replays'] = validate_replays()
        report['count_star'] = validate_count_ast()
        report['status'] = 'PASS'
    except BaseException as error:
        report.update(status='FAILED', error=repr(error), traceback=traceback.format_exc())
        raise
    finally:
        report['elapsed_s'] = time.monotonic() - started
        with (HERE / 'independent_validation.json').open('x') as out:
            json.dump(report, out, indent=2, ensure_ascii=False)
            out.write('\n')
        print(json.dumps({'independent_validation': report['status'], 'elapsed_s': report['elapsed_s']}))


if __name__ == '__main__':
    main()
