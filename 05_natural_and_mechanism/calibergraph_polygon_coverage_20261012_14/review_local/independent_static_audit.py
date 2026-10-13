"""Independent frozen-package audit. No Polygon imports, solver, or SELECT execution."""
from pathlib import Path
import collections
import hashlib
import json
import sqlite3

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
SOURCE = ROOT / 'calibergraph_coverage_boundary_20261012_09'
PILOT = ROOT / 'calibergraph_polygon_pilot_20261012_13'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def quote(name):
    return '"' + name.replace('"', '""') + '"'

def dump(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

cases = json.loads((SOURCE / 'CANDIDATES.json').read_text())
assert len(cases) == 10
assert len({c['case_id'] for c in cases}) == 10
rows = []
for c in cases:
    verified = {}
    for name, spec in c['files'].items():
        p = SOURCE / spec['local_path']
        actual = sha(p)
        assert actual == spec['sha256'], (c['case_id'], name)
        verified[name] = {'path': str(p.relative_to(ROOT)), 'sha256': actual}
    row = {'case_id': c['case_id'], 'source_files': verified,
           'role': c['role'], 'independent_final_test': False,
           'prior_science_case': c['index'] in ('319', '750'),
           'sqlite_explain': {}, 'tables': []}
    db = sqlite3.connect(':memory:')
    db.execute('PRAGMA foreign_keys=ON')
    ddl = (SOURCE / c['files']['full-schema.sql']['local_path']).read_text()
    db.executescript(ddl)
    # Catalog access via PRAGMA only; never execute a data SELECT.
    tables = sorted(t[1] for t in db.execute('PRAGMA table_list').fetchall()
                    if t[0] == 'main' and t[2] == 'table' and not t[1].startswith('sqlite_'))
    assert len(tables) == c['source_table_count']
    for name in tables:
        cols = [dict(zip(('cid','name','type','notnull','default','pk'), r))
                for r in db.execute('PRAGMA table_info(' + quote(name) + ')').fetchall()]
        fks = [dict(zip(('id','seq','table','from','to','on_update','on_delete','match'), r))
               for r in db.execute('PRAGMA foreign_key_list(' + quote(name) + ')').fetchall()]
        indexes = []
        for r in db.execute('PRAGMA index_list(' + quote(name) + ')').fetchall():
            entry = dict(zip(('seq','name','unique','origin','partial'), r))
            entry['columns'] = [dict(zip(('seqno','cid','name'), v)) for v in
                                db.execute('PRAGMA index_info(' + quote(entry['name']) + ')').fetchall()]
            indexes.append(entry)
        row['tables'].append({'table': name, 'columns': cols, 'foreign_keys': fks, 'indexes': indexes})
    for name in ('gold.sql', 'predicted.sql'):
        sql = (SOURCE / c['files'][name]['local_path']).read_text()
        try:
            opcodes = db.execute('EXPLAIN ' + sql).fetchall()
            row['sqlite_explain'][name] = {'status': 'COMPILES', 'opcode_count': len(opcodes)}
        except sqlite3.Error as exc:
            row['sqlite_explain'][name] = {'status': 'INVALID_INPUT', 'error': str(exc)}
    db.close()
    row['table_count'] = len(row['tables'])
    row['column_count'] = sum(len(t['columns']) for t in row['tables'])
    row['declared_type_counts'] = dict(sorted(collections.Counter(
        col['type'] for t in row['tables'] for col in t['columns']).items()))
    row['outside_exact_pilot_type_contract'] = [
        {'table':t['table'], 'column':col['name'], 'declared_type':col['type']}
        for t in row['tables'] for col in t['columns'] if col['type'] not in ('INTEGER','TEXT')]
    row['new_scientific_solver_calls'] = 0
    row['data_query_executions'] = 0
    rows.append(row)

notes = {
 'thrombosis_prediction__1172': {
    'primary_class': 'FULL_C_TYPE_MAPPING_NOT_CLOSED',
    'implementation_findings': ['COUNT(DISTINCT) and joins are implemented; no blanket unsupported-SQL claim.',
       'REAL T-BIL and DATE full-schema fields are outside exact pilot contract. REAL semantics must not be replaced by integer generation without a new declared contract.']},
 'thrombosis_prediction__1261': {
    'primary_class': 'FULL_C_TYPE_MAPPING_NOT_CLOSED',
    'implementation_findings': ['COUNT(DISTINCT) and joins are implemented.',
       'RF is TEXT, yet SQL compares RF < 20. Hash-integer ordering is not SQLite TEXT-affinity comparison; semantic admission remains unclosed independently of unrelated REAL/DATE fields.']},
 'debit_card_specializing__1490': {
    'primary_class': 'IMPLEMENTATION_UNSUPPORTED',
    'implementation_findings': ['IIF has no matching encoder dispatch (IF exists and is different spelling); native parser contains no IIF rewrite.',
       'CAST dispatch returns the input, with no SQLite REAL/FLOAT cast semantics. This is a semantic mismatch, not proof that parsing itself must fail.',
       'REAL Consumption, REAL Price and DATE transactions_1k.Date also block full-schema typed admission.']},
 'european_football_2__1073': {
    'primary_class': 'IMPLEMENTATION_UNSUPPORTED',
    'implementation_findings': ['SUBSTR and STRFTIME have no encoder dispatch; BETWEEN on string hashes is not SQLite lexicographic string comparison.',
       'REAL betting columns remain in full C even when SQL does not reference them. INT/VARCHAR are not keys in the frozen worker mapping; alias expansion would be a new adapter contract.']},
 'california_schools__45': {
    'primary_class': 'FULL_C_TYPE_MAPPING_NOT_CLOSED',
    'implementation_findings': ['JOIN, projection, GROUP BY and AVG appear in the fixed implementation; this is not classified as implementation-unsupported.',
       'All full-schema tables and columns must remain; unreferenced FRPM REAL fields and schools REAL/DATE fields prevent exact frozen type mapping. N=1 itself is not a reason to reject this case.']},
 'debit_card_specializing__1526': {
    'primary_class': 'IMPLEMENTATION_UNSUPPORTED',
    'implementation_findings': ['IIF and SUBSTRING have no encoder dispatch; CAST is a passthrough.',
       'Scalar subqueries do have visit_Query, but SQLite scalar-subquery and date-literal semantics are not thereby proven faithful; do not claim all subqueries unsupported.',
       'Full-schema REAL/DATE fields independently block exact pilot type mapping.']},
 'california_schools__26': {
    'primary_class': 'INVALID_INPUT',
    'implementation_findings': ['Predicted SQL aliases frpm as T1 and asks T1.Street; that field is absent. EXPLAIN independently confirms the original input error.',
       'Full-schema REAL/DATE fields are additional barriers; no query repair is authorized.']},
 'student_club__1390': {
    'primary_class': 'INVALID_INPUT',
    'implementation_findings': ['Predicted SQL aliases expense as T2 and asks T2.link_to_event; that field is absent. EXPLAIN independently confirms the original input error.',
       'REAL budget/expense fields and CAST semantics are additional barriers; no query repair is authorized.']},
}
for row in rows:
    if row['prior_science_case']:
        row['primary_class'] = 'PRIOR_PILOT_ONLY_NO_RERUN'
        continue
    row.update(notes[row['case_id']])
    row['semantic_and_full_C_admitted'] = False
    assert row['outside_exact_pilot_type_contract']
    if row['primary_class'] == 'INVALID_INPUT':
        assert row['sqlite_explain']['predicted.sql']['status'] == 'INVALID_INPUT'
    else:
        assert all(v['status'] == 'COMPILES' for v in row['sqlite_explain'].values())

paths = list((PILOT / 'runtime_local').rglob('*.py'))
paths += [PILOT / n for n in ('slot_worker.py', 'replay.py', 'SOURCE.json', 'FREEZE.json',
                               'INDEPENDENT_REVIEW.json', 'RESULT.zh.md')]
bindings = [{'path': str(p.relative_to(ROOT)), 'sha256': sha(p)} for p in sorted(paths)]
dump('STATIC_AUDIT.json', {
 'scope': 'Independent static source audit: in-memory original DDL, PRAGMA, EXPLAIN only; no Polygon imports or execution.',
 'sqlite_version': sqlite3.sqlite_version,
 'candidate_manifest': {'path': str((SOURCE/'CANDIDATES.json').relative_to(ROOT)), 'sha256': sha(SOURCE/'CANDIDATES.json')},
 'source_files_hash_verified': 40,
 'runtime_and_contract_source_bindings': bindings,
 'reviewer_script_sha256': sha(Path(__file__)),
 'new_admitted_cases': [],
 'remaining_eight_primary_counts': dict(collections.Counter(r['primary_class'] for r in rows if not r['prior_science_case'])),
 'new_solver_calls': 0, 'data_query_executions': 0, 'process_rss_queries': 0,
 'no_unrelated_project_operations': True,
 'cases': rows,
 'limitations': ['No new runtime parse/encode outcome is asserted.',
    'No unsupported item is a theorem about arbitrary Polygon versions or all possible adapters.',
    'Existing pilot results are source-bound references here, not newly replayed by this static audit.',
    'A static gate failure is not UNSAT, timeout, SQL equivalence, counterexample, novelty, or method superiority.']})
print(json.dumps({'counts': collections.Counter(r['primary_class'] for r in rows),
                  'cases': [{'id':r['case_id'],'tables':r['table_count'],'columns':r['column_count'],
                             'types':r['declared_type_counts'],'explain':r['sqlite_explain']} for r in rows]},
                 ensure_ascii=False, indent=2))
