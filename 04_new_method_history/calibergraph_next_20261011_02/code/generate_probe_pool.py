"""Offline artificial 2-row probe pool, fixed without SQL/solver observations.

Run: python3 -B -I -S code/generate_probe_pool.py
Outputs are exclusive-create. The separate checker reads original C directly.
"""
from copy import deepcopy
from datetime import date, timedelta, datetime, timezone
from pathlib import Path
import hashlib
import json
import resource
import signal
import time

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parent / 'calibergraph_next_20261011_01/data/development.jsonl'
MAX_PER_GROUP = 12

def enc(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()

def sha(value):
    return hashlib.sha256(value).hexdigest()

def ref(term):
    if not isinstance(term, dict) or set(term) != {'value'} or not isinstance(term['value'], str):
        raise ValueError('INVALID_COLUMN_REFERENCE')
    parts = term['value'].split('__', 1)
    if len(parts) != 2:
        raise ValueError('INVALID_COLUMN_REFERENCE')
    return tuple(parts)

def write_new(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as f:
        f.write(raw)

def jwrite(path, value):
    write_new(path, json.dumps(value, ensure_ascii=False, indent=2).encode() + b'\n')

def check_contract(schema, constraints, rows):
    """Independent explicit finite checker: does not reuse generator masks.

    OperationalIC for these frozen five operators, not ordinary nullable SQL IC.
    This function reads every original C clause; unsupported operators fail closed.
    """
    start = time.monotonic()
    checks = []
    errors = []
    try:
        if set(rows) != set(schema):
            raise ValueError('TABLE_SET_MISMATCH')
        for table, cols in schema.items():
            if len(rows[table]) != 2:
                raise ValueError('NOT_EXACTLY_TWO_ROWS:' + table)
            for row in rows[table]:
                if set(row) != set(cols):
                    raise ValueError('COLUMN_SET_MISMATCH:' + table)
                for col, typ in cols.items():
                    v = row[col]
                    if typ not in ('INT', 'VARCHAR', 'DATE'):
                        raise ValueError('UNSUPPORTED_ORIGINAL_TYPE:' + typ)
                    if v is None:
                        continue
                    if typ == 'INT' and type(v) is not int:
                        raise ValueError('INT_TYPE_MISMATCH')
                    if typ in ('VARCHAR', 'DATE') and type(v) is not str:
                        raise ValueError('STRING_TYPE_MISMATCH')
                    if typ == 'DATE' and date.fromisoformat(v).isoformat() != v:
                        raise ValueError('DATE_LEXICAL_MISMATCH')
        checks.append({'kind': 'exact_shape_and_original_types', 'pass': True})
    except (KeyError, TypeError, ValueError) as e:
        errors.append(str(e))
        checks.append({'kind': 'exact_shape_and_original_types', 'pass': False, 'reason': str(e)})
    def values(term):
        table, col = ref(term)
        if table not in schema or col not in schema[table]:
            raise ValueError('UNKNOWN_ORIGINAL_COLUMN')
        return [r[col] for r in rows[table]]
    if constraints is not None and not isinstance(constraints, list):
        errors.append('CONSTRAINT_NOT_LIST_OR_NULL')
        constraints = []
    for ci, c in enumerate(constraints or []):
        try:
            if not isinstance(c, dict) or len(c) != 1:
                raise ValueError('INVALID_CLAUSE')
            op, terms = next(iter(c.items()))
            if op == 'primary':
                refs = [ref(t) for t in terms]
                if not refs or len({t for t, _ in refs}) != 1:
                    raise ValueError('INVALID_PRIMARY')
                table = refs[0][0]
                keys = [tuple(row[col] for _, col in refs) for row in rows[table]]
                ok = all(None not in key for key in keys) and len(set(keys)) == len(keys)
            elif op == 'foreign':
                if len(terms) != 2:
                    raise ValueError('ONLY_SINGLE_COLUMN_FOREIGN_SUPPORTED')
                source_values, target_values = values(terms[0]), values(terms[1])
                ok = all(v is not None and v in target_values for v in source_values)
            elif op == 'not_null':
                ok = all(v is not None for v in values(terms))
            elif op in ('gte', 'neq'):
                if len(terms) != 2:
                    raise ValueError('INVALID_BINARY_CONSTRAINT')
                left = values(terms[0])
                right = values(terms[1]) if isinstance(terms[1], dict) else [terms[1]]
                # Column-column comparisons are Cartesian, not same-row.
                pairs = [(a, b) for a in left for b in right]
                ok = all(a is not None and b is not None and (a >= b if op == 'gte' else a != b) for a, b in pairs)
            else:
                raise ValueError('UNSUPPORTED_FULL_CONSTRAINT:' + op)
            checks.append({'constraint_index': ci, 'operator': op, 'pass': bool(ok)})
            if not ok:
                errors.append('CONSTRAINT_FALSE:' + str(ci))
        except (KeyError, TypeError, ValueError) as e:
            checks.append({'constraint_index': ci, 'pass': False, 'reason': str(e)})
            errors.append('CONSTRAINT_CHECK_ERROR:' + str(ci) + ':' + str(e))
    return {'status': 'PASS' if not errors else 'REJECTED', 'checks': checks, 'errors': errors,
            'seconds': time.monotonic() - start, 'interpretation': 'OFFICIAL_OPERATIONAL_IC_FINITE_INSTANCE_ONLY'}

def make_base(schema, constraints):
    """Generation uses schema/C only; never receives SQL strings or outputs."""
    rows = {t: [{}, {}] for t in sorted(schema)}
    keys, foreign_cols, nonnull = set(), set(), set()
    ordinal = 0
    for table in sorted(schema):
        for col in sorted(schema[table]):
            ordinal += 1
            typ = schema[table][col]
            for ri in range(2):
                if typ == 'INT':
                    v = ordinal * 100 + ri + 1
                elif typ == 'VARCHAR':
                    v = f'{table}_{col}_{ri + 1:02d}'
                elif typ == 'DATE':
                    v = (date(2000, 1, 1) + timedelta(days=ordinal * 3 + ri)).isoformat()
                else:
                    raise ValueError('UNSUPPORTED_ORIGINAL_TYPE:' + typ)
                rows[table][ri][col] = v
    for c in constraints or []:
        op, terms = next(iter(c.items()))
        if op == 'primary':
            keys.update(ref(t) for t in terms)
        elif op == 'foreign':
            foreign_cols.update(ref(t) for t in terms)
        elif op == 'not_null':
            nonnull.add(ref(terms))
        elif op == 'gte':
            table, col = ref(terms[0])
            nonnull.add((table, col))
            if isinstance(terms[1], dict):
                raise ValueError('GENERATOR_UNSUPPORTED_COLUMN_COLUMN_GTE')
            for ri in range(2):
                rows[table][ri][col] = max(rows[table][ri][col], terms[1] + ri)
        elif op != 'neq':
            raise ValueError('GENERATOR_UNSUPPORTED_ORIGINAL_C:' + op)
    # Existing six schemas have one-level single-column FKs. No repairs after check.
    for c in constraints or []:
        if 'foreign' in c:
            (st, sc), (dt, dc) = [ref(t) for t in c['foreign']]
            for ri in range(2):
                rows[st][ri][sc] = rows[dt][ri][dc]
    return rows, keys, foreign_cols, nonnull

def descriptors(schema, keys, foreign_cols, nonnull):
    result = [{'kind': 'base', 'mutation': None}]
    for table in sorted(schema):
        for col in sorted(schema[table]):
            p = (table, col)
            if p not in keys | foreign_cols | nonnull:
                result.append({'kind': 'null_all', 'mutation': {'table': table, 'column': col, 'row_indexes': [0, 1]}})
                result.append({'kind': 'null_single', 'mutation': {'table': table, 'column': col, 'row_indexes': [0]}})
            if p not in keys:
                result.append({'kind': 'duplicate_nonkey', 'mutation': {'table': table, 'column': col, 'target_row_index': 1, 'source_row_index': 0}})
    return result

def main():
    started = time.monotonic()
    signal.alarm(1)
    raw = SOURCE.read_bytes()
    source_sha = sha(raw)
    copied = ROOT / 'data/development_v2.jsonl'
    write_new(copied, raw)
    cases = [json.loads(line) for line in raw.splitlines()]
    pool, ledger, groups = [], [], []
    checker_seconds = 0.0
    for case in cases:
        src = case['source_record']
        schema, constraints = src['schema'], src['constraint']
        base, keys, foreign_cols, nonnull = make_base(schema, constraints)
        planned = descriptors(schema, keys, foreign_cols, nonnull)
        selected = planned[:MAX_PER_GROUP]
        accepted = 0
        for index, desc in enumerate(planned, 1):
            pid = f'{case["id"]}_probe_{index:02d}'
            if index > MAX_PER_GROUP:
                ledger.append({'id': pid, 'case_id': case['id'], **desc, 'status': 'NOT_SELECTED_FIXED_CAP', 'replacement': False})
                continue
            rows = deepcopy(base)
            m = desc['mutation']
            if desc['kind'] in ('null_all', 'null_single'):
                for ri in m['row_indexes']:
                    rows[m['table']][ri][m['column']] = None
            elif desc['kind'] == 'duplicate_nonkey':
                rows[m['table']][m['target_row_index']][m['column']] = rows[m['table']][m['source_row_index']][m['column']]
            check = check_contract(schema, constraints, rows)
            checker_seconds += check['seconds']
            item = {'id': pid, 'case_id': case['id'], 'source_group_id': case['source_group_id'],
                    'candidate_index': index, **desc, 'rows': rows,
                    'schema_sha256': sha(enc(schema)), 'constraint_sha256': sha(enc(constraints)),
                    'source_development_sha256': source_sha, 'rows_sha256': sha(enc(rows)),
                    'data_origin': 'ARTIFICIAL_DETERMINISTIC_PROBE_NOT_NATURAL_DATA',
                    'ic_check': check, 'eligible_for_shared_probe': check['status'] == 'PASS'}
            pool.append(item)
            accepted += int(item['eligible_for_shared_probe'])
            ledger.append({'id': pid, 'case_id': case['id'], **desc, 'status': 'ACCEPTED' if item['eligible_for_shared_probe'] else 'REJECTED_FULL_C', 'errors': check['errors'], 'rows_sha256': item['rows_sha256'], 'replacement': False})
        groups.append({'case_id': case['id'], 'source_group_id': case['source_group_id'], 'planned': len(planned), 'selected': len(selected), 'accepted': accepted, 'rejected': len(selected)-accepted, 'truncated': len(planned)-len(selected)})
    path = ROOT / 'data/probe_pool.jsonl'
    write_new(path, b''.join(enc(r) + b'\n' for r in pool))
    jwrite(ROOT / 'data/probe_generation_ledger.json', ledger)
    manifest = {'status': 'FROZEN_ARTIFICIAL_POOL_NOT_EXECUTED', 'created_utc': datetime.now(timezone.utc).isoformat(),
        'source': {'path': str(SOURCE), 'sha256': source_sha, 'bytes': len(raw)},
        'copy': {'path': str(copied), 'sha256': sha(copied.read_bytes()), 'byte_identical': copied.read_bytes() == raw},
        'pool': {'path': str(path), 'sha256': sha(path.read_bytes()), 'candidates': len(pool), 'groups': groups},
        'rule': {'rows_per_original_table': 2, 'maximum_candidates_per_group': MAX_PER_GROUP, 'order': 'base then original table and column lexicographic order; per column null_all, null_single(row0), duplicate_nonkey(row1<-row0) when structurally eligible; take first12 before C check; never replace failures', 'null_columns': 'exclude every primary-key member, every FK participating column, not_null columns, and gte LHS columns', 'duplicate_columns': 'every non-primary-key column, including legal FK source or gte columns; separate full-C checker decides admission; no replacement', 'value_rule': 'INT ordinal*100+row+1; VARCHAR table_column_row; DATE 2000-01-01+3*ordinal+row; FK uses corresponding target row; gte scalar lower-bound adjustment; no SQL-derived constants'},
        'contract': 'Original full schema/C retained. Separate finite checker: PK nonNULL tuple unique; single-column FK nonNULL membership; gte nonNULL; column-column neq Cartesian and nonNULL; exact2rows/all tables; original INT/VARCHAR/DATE types.',
        'comparison': 'All methods must receive this same immutable candidate set; generic NULL-first strong baseline, candidate query-aware ranking, and pure-fallback ablation are downstream order/strategy choices. This pool was not selected by pair outputs.',
        'exposure': 'All six development groups are author-exposed, including previous49k applicability scans and01 development/replay; development_v2 filename does not create an unseen test. Reserve was not opened.',
        'novelty': 'Known XData-style preprobe plus VeriEQL fallback engineering combination; no claimed scientific increment and no result-based selection.',
        'prohibited_claims': ['natural databases', 'natural defect gold', 'test accuracy', 'automatic promotion', 'gain established before comparative experiment'],
        'usage': {'generation_wall_seconds': time.monotonic()-started, 'checker_total_seconds': checker_seconds, 'peak_rss_bytes_macos': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss, 'processes': 1, 'alarm_seconds': 1},
        'executed': {'sql': False, 'solver': False, 'parser': False, 'query_output_inspection': False},
        'code_sha256': sha(Path(__file__).read_bytes()), 'science_status': 'HOLD'}
    jwrite(ROOT / 'governance/probe_pool_manifest.json', manifest)
    print(json.dumps({'status': manifest['status'], 'groups': groups, 'candidates': len(pool), 'checker_seconds': checker_seconds, 'usage': manifest['usage'], 'source_copy_identical': manifest['copy']['byte_identical']}))

if __name__ == '__main__':
    main()
