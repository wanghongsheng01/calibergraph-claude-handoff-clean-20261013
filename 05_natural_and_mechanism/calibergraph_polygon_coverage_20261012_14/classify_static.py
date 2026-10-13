"""Hash-bound frozen-ten support inventory. SQLite DDL/PRAGMA/EXPLAIN only; no solver."""
from pathlib import Path
import collections, hashlib, json, sqlite3, time
P=Path(__file__).resolve().parent
ROOT=P.parent
SOURCE=ROOT/'calibergraph_coverage_boundary_20261012_09'
PILOT=ROOT/'calibergraph_polygon_pilot_20261012_13'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def quote(s):return '"'+s.replace('"','""')+'"'
def save(name,data):
    with (P/name).open('x') as f:json.dump(data,f,ensure_ascii=False,indent=2);f.write('\n')
notes={
 'thrombosis_prediction__1172':['Laboratory.T-BIL is REAL and used at the 2.0 boundary; source also contains DATE. Existing worker maps only INTEGER/TEXT. No silent REAL-to-int or DATE-to-text conversion admitted.','Historical ParSEval false EQ and independent legal witness remain prior development evidence, not a new Polygon result.'],
 'thrombosis_prediction__1261':['Laboratory.RF is TEXT compared to numeric 20: SQLite affinity/order is not numeric string-hash order. Complete DDL also contains REAL and DATE.','Earlier FK equivalence argument is separate static evidence, not a new solver result.'],
 'debit_card_specializing__1490':['Consumption is REAL, comparison literal is 46.73, queries use FLOAT/REAL CAST and division. Fixed encoder makes CAST an identity and cell is Int; SQLite floating semantics not admitted.','DDL has two REFERENCES declarations on yearmonth.CustomerID with implicit target PK, UNIQUE, AUTOINCREMENT and DATE; existing restricted full-C mapper is not complete for this schema.'],
 'european_football_2__1073':['Original pair uses SUBSTR versus strftime on date strings. No explicit substr/substring/strftime encoder branch in fixed complete source; parser normalization was not executed and is not assumed absent.','Full schema has additional types and UNIQUE constraints outside the old mapper. Date decoder clamps overflowing integers; do not claim exact source-domain mapping.'],
 'california_schools__45':['Complete schema includes REAL and DATE (including NOT NULL schools.LastUpdate), plus quoted column names. Cannot drop unreferenced frpm or coerce all source types into existing map.','N=1 is insufficient for the existing two-school group-merging countermodel; this limits interpretation but is NOT an independent reason to reject admission.'],
 'debit_card_specializing__1526':['REAL/DATE, CAST/division, scalar subqueries and SUBSTRING/IIF/LIKE need source-dialect semantics. LIKE has an implementation branch, so it is not categorically labelled absent.','Complete DDL has the same duplicate/implicit-target REFERENCES, UNIQUE, AUTOINCREMENT mapping obligations as #1490.'],
 'california_schools__26':['Predicted query refers to frpm.Street (also City/Zip/State); those columns are absent. Keep malformed pair in denominator, do not repair aliases or replace case.'],
 'student_club__1390':['Predicted query refers to expense.link_to_event, absent from original expense DDL. Keep malformed pair in denominator.','Nullable non-integer SQLite PRIMARY KEY columns add a separate semantic issue: Polygon primary encoder forces non-NULL; no mapping admission asserted.'],
 'superhero__750':['Reuse pilot13 two independently replayed full-C witnesses; no rerun. Negative weights are DDL-legal synthetic values, not real records.'],
 'toxicology__319':['Reuse pilot13 two bounded symbolic UNSAT results; original SQL bytes identical. No whole SQLite-domain proof and no rerun.']}
rows=[];checks=[];started=time.monotonic()
records=json.loads((SOURCE/'CANDIDATES.json').read_text());assert len(records)==10
for c in records:
    cid=c['case_id'];src=SOURCE/'sources_local'/cid
    for name,meta in c['files'].items():
        h=sha(src/name);assert h==meta['sha256'],(cid,name)
        checks.append({'path':str((src/name).relative_to(ROOT)),'sha256':h})
    db=sqlite3.connect(':memory:');db.execute('PRAGMA foreign_keys=ON')
    db.executescript((src/'full-schema.sql').read_text())
    tables=[]
    # sqlite_sequence is implementation metadata, not a declared source table.
    names=[r[1] for r in db.execute('PRAGMA table_list') if r[2]=='table' and not r[1].startswith('sqlite_')]
    for name in sorted(names):
        cols=[dict(zip(['cid','name','type','notnull','default','pk'],r)) for r in db.execute('PRAGMA table_info('+quote(name)+')')]
        fks=[dict(zip(['id','seq','table','from','to','on_update','on_delete','match'],r)) for r in db.execute('PRAGMA foreign_key_list('+quote(name)+')')]
        idx=[]
        for r in db.execute('PRAGMA index_list('+quote(name)+')'):
            idx.append({'name':r[1],'unique':r[2],'origin':r[3],'partial':r[4],'columns':[list(x) for x in db.execute('PRAGMA index_info('+quote(r[1])+')')]})
        tables.append({'table':name,'columns':cols,'foreign_keys':fks,'indexes':idx})
    compilation={}
    for name in ['gold.sql','predicted.sql']:
        try:
            opcodes=db.execute('EXPLAIN '+(src/name).read_text()).fetchall()
            compilation[name]={'status':'COMPILES','opcode_count':len(opcodes),'query_executed':False}
        except sqlite3.Error as e:compilation[name]={'status':'INVALID_INPUT','error':str(e),'query_executed':False}
    types=collections.Counter(col['type'].upper() for t in tables for col in t['columns'])
    invalid=any(x['status']=='INVALID_INPUT' for x in compilation.values())
    prev=cid in ['superhero__750','toxicology__319']
    category='PREVIOUSLY_EXECUTED' if prev else 'INVALID_INPUT' if invalid else 'TYPE_SEMANTICS_NOT_ADMITTED'
    assert prev or invalid or set(types)-{'INTEGER','TEXT'},cid
    row={'case_id':cid,'development_only':True,'category':category,'new_run':False,'new_UA':'NOT_RUN_'+category if not prev else 'NOT_RERUN_PREVIOUS_EVIDENCE','new_precise':'NOT_RUN_'+category if not prev else 'NOT_RERUN_PREVIOUS_EVIDENCE','reasons':notes[cid], 'source_commit':'88cfe245bcf249a5b0df561a6b09c116ff2a2896','source_files':c['files'],'compile_only':compilation,'type_counts':dict(types),'unsupported_by_existing_type_map':sorted(set(types)-{'INTEGER','TEXT'}),'table_count':len(tables),'column_count':sum(len(t['columns']) for t in tables),'full_C_inventory':tables,'full_C_mapping_admitted':prev,'no_source_query_or_DDL_rewrite':True,'new_solver_calls':0,'new_query_data_executions':0,'new_stage_seconds':None}
    row['secondary_static_tags']=['FULL_C_TYPE_MAPPING_NOT_ADMITTED'] if category=='TYPE_SEMANTICS_NOT_ADMITTED' else []
    if cid in ['debit_card_specializing__1490','european_football_2__1073','debit_card_specializing__1526']:row['secondary_static_tags'].append('ENCODER_SEMANTIC_GAP_OR_NO_EXPLICIT_OPERATOR_BRANCH_NOT_DYNAMICALLY_TESTED')
    if category=='INVALID_INPUT':row['secondary_static_tags']=['ORIGINAL_QUERY_MISSING_COLUMN']
    rows.append(row);db.close()
save('STATIC_CLASSIFICATION.json',{'sqlite_version':sqlite3.sqlite_version,'elapsed_static_s':time.monotonic()-started,'operation_scope':'In-memory original DDL, PRAGMA metadata and EXPLAIN; original query bodies never executed, no research package imports and no solver','rows':rows})
save('SOURCE_HASHES.json',{'frozen_candidate_list_sha256':sha(SOURCE/'CANDIDATES.json'),'selection_protocol_sha256':sha(SOURCE/'SELECTION_PROTOCOL.json'),'checks':checks})
save('PRE_RUN_DECISION.json',{'ordered_frozen_cases':[r['case_id'] for r in rows],'new_run_slots':[],'prior_cases_not_retried':['superhero__750','toxicology__319'],'static_categories':dict(collections.Counter(r['category'] for r in rows)),'decision':'NO_NEW_ADMITTED_CASES_CLOSE_WITHOUT_SCIENCE','no_new_samples':True,'admission_policy':'Reuse INTEGER/TEXT N=1 generation+original full-C replay admission only; do not silently broaden types, drop columns, repair SQL or count syntactic compilation as semantic admission.','approved_if_admitted':{'serial':True,'batch_science_wall_s':60,'per_solver_s':3,'per_native_z3_internal_MiB':512,'aggregate_RSS_limit':False,'no_science_retries':True,'unstarted_on_budget_exhaustion':'NOT_RUN'}})
print(json.dumps({'categories':dict(collections.Counter(r['category'] for r in rows)),'new_slots':0,'source_files_checked':len(checks)},ensure_ascii=False))
