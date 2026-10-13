"""Strict original-SQL replay for two statically inspected INT-only source pairs.

Inert until called after registered official SAT generation. No SQL rewriting,
parser replacement, solver, generic VARCHAR decoder, or synthetic witness.
"""
from collections import Counter
from itertools import product
import hashlib
import json
import re
import time
import resource


class ReplayInconclusive(ValueError):
    pass


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
        separators=(',', ':'), allow_nan=False).encode()).hexdigest()


# Original source objects inspected as text only; hashes bind the whole pair/C/schema.
PROFILES = {
    'dev03_10': {
        'sql': ['d6f4e1268f13f698ca86b9079280ef9d56c18a1b8b815aacf0940f90a6303e26',
                'c450dc8464a1717929aa7810c6be75b98c150efb82d16bde5a6eaa5f0da88fb5'],
        'schema': '7edcbc89506aa5aeb305dd083d43bc6d75cd645e18372595f28d18c87b2e6732',
        'constraint': 'f1f94c490360d247884b782779dcbb626b50d779d3cf016228ff37206d724099',
        'minimum_sqlite': (3, 8, 3),
        'reason': 'INT-only CASE, equality join, DISTINCT and NOT IN; no arithmetic/string/date/order/collation.'},
    'dev03_15': {
        'sql': ['f63915350c6d64ab99bfd7af8702a072da34476f8839a98f9c209753821f8c39',
                'e8657124a5d7aea2a9e4648f69af0c916faefbb7eb429cefb979ebc36af306f7'],
        'schema': '226b6d3373dab280504982f2356d48b5492c49a5a1ce6bbaafeb160472292d59',
        'constraint': '5e0086dc628cbf2af39cb9be7d370d301fc4c18e7833c8a874a2c8011e7ec5ef',
        'minimum_sqlite': (3, 39, 0),
        'reason': 'INT-only outer joins, equality and row equality, IFNULL/COALESCE; RIGHT JOIN requires SQLite >=3.39.'},
}
REJECTIONS = {
    'dev03_07': 'DATE_SCHEMA_AND_DIVISION_ROUND_SEMANTICS_UNPROVEN',
    'dev03_04': 'DECIMAL_MULTIPLICATION_ROUND_DIALECT_SEMANTICS_UNPROVEN; VARCHAR_EQUALITY_DECODER_NOT_CERTIFIED',
}


def check_full_original_C(schema, constraints, db, exact_rows, budget):
    """Independent Python checker of supported complete operational C.

    Column-to-column comparisons use every Cartesian pair, as in the pinned
    official add_constraints, not ordinary rowwise SQL CHECK semantics.
    """
    if not isinstance(constraints, list):
        raise ReplayInconclusive('MISSING_OR_NULL_C')
    if set(db) != set(schema):
        raise ReplayInconclusive('FULL_TABLE_SET_MISMATCH')
    refs = {}
    for table, fields in schema.items():
        if len(db[table]) != exact_rows:
            raise ReplayInconclusive('EXACT_N_ROW_SHAPE_MISMATCH')
        for row in db[table]:
            if set(row) != set(fields):
                raise ReplayInconclusive('FULL_COLUMN_SET_MISMATCH')
            for col, typ in fields.items():
                value = row[col]
                if typ != 'INT' or (value is not None and
                    (type(value) is not int or not -2147483648 <= value <= 2147483647)):
                    raise ReplayInconclusive('INT_TYPE_OR_OFFICIAL_RANGE_MISMATCH')
        for col in fields:
            refs[table.upper() + '__' + col.upper()] = (table, col)
    def ref(expr):
        if not isinstance(expr, dict) or set(expr) != {'value'} or expr['value'] not in refs:
            raise ReplayInconclusive('UNSUPPORTED_COMPLETE_C_OPERAND')
        return refs[expr['value']]
    def values(expr):
        if type(expr) is int:
            return [expr]
        table, col = ref(expr)
        return [row[col] for row in db[table]]
    def clause(item):
        budget.check()
        if not isinstance(item, dict) or len(item) != 1:
            raise ReplayInconclusive('UNSUPPORTED_COMPLETE_C_CLAUSE')
        op, operands = next(iter(item.items()))
        if op == 'primary':
            refs_ = [ref(x) for x in operands]
            if not refs_ or len({t for t, c in refs_}) != 1:
                raise ReplayInconclusive('UNSUPPORTED_COMPLETE_PRIMARY')
            rows = [tuple(row[c] for t, c in refs_) for row in db[refs_[0][0]]]
            return all(None not in row for row in rows) and len(set(rows)) == len(rows)
        if op == 'foreign':
            if len(operands) != 2:
                raise ReplayInconclusive('FOREIGN_ARITY')
            a, b = map(values, operands)
            return all(x is not None and any(y is not None and x == y for y in b) for x in a)
        if op in ('eq', 'neq', 'lt', 'lte', 'gt', 'gte'):
            if len(operands) != 2:
                raise ReplayInconclusive('COMPARE_ARITY')
            left, right = operands
            # Preserve official literal-left swap (even its order quirk).
            if type(left) is int and isinstance(right, dict):
                left, right = right, left
            compare = {'eq': lambda a,b:a==b, 'neq': lambda a,b:a!=b,
                'lt':lambda a,b:a<b, 'lte':lambda a,b:a<=b,
                'gt':lambda a,b:a>b, 'gte':lambda a,b:a>=b}[op]
            return all(a is not None and b is not None and compare(a,b)
                       for a,b in product(values(left), values(right)))
        if op == 'not_null':
            return all(x is not None for x in values(operands))
        if op in ('and', 'or'):
            # Visit every clause even if an early truth value would short-circuit.
            results = [clause(x) for x in operands]
            return all(results) if op == 'and' else any(results)
        raise ReplayInconclusive('UNSUPPORTED_COMPLETE_C_OPERATOR_' + str(op))
    results = [clause(item) for item in constraints]
    if not all(results):
        raise ReplayInconclusive('INDEPENDENT_COMPLETE_ORIGINAL_C_FAILED')
    return {'status': 'COMPLETE_ORIGINAL_OPERATIONAL_C_TRUE',
        'original_clause_count': len(constraints), 'checked_clause_count': len(results),
        'semantics': 'Pinned official operational C, including Cartesian column comparisons; not business-completeness proof.'}


def replay_generated_witness(case, witness, env, protocol, budget):
    result = {'status': 'INCONCLUSIVE', 'full_C_status': 'NOT_CHECKED',
        'original_sql_unchanged': True, 'query_rewrites': 0,
        'scope': 'SQLite dialect replay of the identical original pair on one generated exact-N database.'}
    checkpoints = []
    def phase(name, action):
        budget.check()
        start = time.monotonic()
        before = resource.getrusage(resource.RUSAGE_SELF)
        row = {'name': name, 'status': 'STARTED'}
        checkpoints.append(row)
        try:
            answer = action()
            row['status'] = 'RETURNED'
            return answer
        finally:
            after = resource.getrusage(resource.RUSAGE_SELF)
            row.update(wall_seconds=time.monotonic()-start,
                cpu_seconds=after.ru_utime+after.ru_stime-before.ru_utime-before.ru_stime)
    connection = None
    try:
        profile = PROFILES.get(case['id'])
        if profile is None:
            raise ReplayInconclusive(REJECTIONS.get(case['id'], 'SOURCE_PAIR_NOT_STATICALLY_ADMITTED'))
        src = case['source_record']
        hashes = [hashlib.sha256(q.encode()).hexdigest() for q in src['pair']]
        if hashes != profile['sql'] or digest(src['schema']) != profile['schema'] or digest(src['constraint']) != profile['constraint']:
            raise ReplayInconclusive('REVIEWED_SOURCE_PROFILE_HASH_MISMATCH')
        db = witness['all_physical_raw_values']
        # Export already obtained NULL from the independent model NULL flag.
        # Never use the official formatter's 99999 sentinel or stringified output.
        c_result = phase('INDEPENDENT_FULL_C_CHECK', lambda: check_full_original_C(
            src['schema'], src['constraint'], db, protocol['exact_rows_per_table'], budget))
        result.update(full_C_status=c_result['status'], independent_full_C=c_result,
            concrete_database=db, original_sql_sha256=hashes, admission=profile['reason'])
        import sqlite3
        result['sqlite_version'] = sqlite3.sqlite_version
        if sqlite3.sqlite_version_info < profile['minimum_sqlite']:
            raise ReplayInconclusive('SQLITE_DIALECT_VERSION_TOO_OLD_FOR_UNCHANGED_ORIGINAL_SQL')
        connection = sqlite3.connect(':memory:', isolation_level=None)
        def quote(name):
            if not re.fullmatch(r'[A-Z][A-Z0-9_]*', name):
                raise ReplayInconclusive('UNREVIEWED_SCHEMA_IDENTIFIER')
            return '"' + name + '"'
        def load():
            for table, fields in src['schema'].items():
                budget.check()
                connection.execute('CREATE TABLE ' + quote(table) + '(' + ','.join(
                    quote(c) + ' INTEGER' for c in fields) + ')')
                connection.executemany('INSERT INTO ' + quote(table) + ' VALUES (' +
                    ','.join('?' for _ in fields) + ')',
                    [tuple(row[c] for c in fields) for row in db[table]])
        phase('SQLITE_LOAD_GENERATED_DATABASE', load)
        connection.execute('PRAGMA query_only=ON')
        allowed = {sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_FUNCTION,
                   getattr(sqlite3, 'SQLITE_RECURSIVE', 33)}
        connection.set_authorizer(lambda action,*args: sqlite3.SQLITE_OK if action in allowed else sqlite3.SQLITE_DENY)
        # CPython converts callback exceptions into OperationalError. Preserve
        # the original guard failure out of band, interrupt, then re-raise it.
        from official_generation_backend import BudgetStop
        guard_failure = []
        def progress():
            try:
                budget.check()
                return 0
            except BaseException as error:
                guard_failure.append(error)
                return 1
        connection.set_progress_handler(progress, 100)
        outputs = []
        for index, sql in enumerate(src['pair']):
            def execute(sql=sql):
                try:
                    cursor = connection.execute(sql)
                    rows = cursor.fetchall()
                except BaseException:
                    if guard_failure:
                        original = guard_failure[0]
                        if isinstance(original, BudgetStop):
                            raise original
                        raise BudgetStop('SQLITE_PROGRESS_GUARD_FAILURE: ' +
                            type(original).__name__ + ': ' + str(original)[:1000]) from original
                    raise
                if any(any(x is not None and type(x) is not int for x in row) for row in rows):
                    raise ReplayInconclusive('UNEXPECTED_REPLAY_OUTPUT_TYPE')
                return rows
            outputs.append(phase('SQLITE_ORIGINAL_QUERY_' + str(index), execute))
        bags = [Counter(tuple(row) for row in rows) for rows in outputs]
        result.update(status='REPLAY_CONFIRMED_DIFFERENCE' if bags[0] != bags[1] else 'REPLAY_DID_NOT_CONFIRM_DIFFERENCE',
            original_sql_results=outputs, comparison='bag multiplicities, exact INT/NULL equality',
            generated_official_model=True)
    except ReplayInconclusive as error:
        result['reason'] = str(error)
    except Exception as error:
        if type(error).__name__ in ('BudgetStop', 'SolverBudgetOverrun'):
            raise
        result.update(reason='REPLAY_ERROR', error_type=type(error).__name__, error=str(error)[:2000])
    finally:
        if connection is not None:
            connection.close()
        result['phase_costs'] = checkpoints
    return result
