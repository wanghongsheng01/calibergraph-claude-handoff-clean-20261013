"""Fail-closed text inventory for these two frozen DDLs; no SQL/research imports."""
from pathlib import Path
import hashlib, json, re

P = Path(__file__).resolve().parent
ROOT = P.parent
PREV = ROOT / 'calibergraph_coverage_boundary_20261012_09'
def split_fields(body):
    # These fixed schemas have no comma-bearing quoted literals; reject rather
    # than generalize this source-text extractor to arbitrary SQL.
    if "'" in body: raise ValueError('Unadmitted quoted literal in DDL')
    fields=[]; start=0; depth=0
    for i,ch in enumerate(body):
        depth += (ch=='(')-(ch==')')
        if ch==',' and depth==0: fields.append(body[start:i].strip()); start=i+1
    fields.append(body[start:].strip()); assert depth==0
    return fields
def names(s): return [x.strip().strip('`"') for x in s.split(',')]
def inventory(sql):
    tables=[]
    for part in re.split(r';\s*\n',sql):
        m=re.fullmatch(r'CREATE TABLE\s+[`"]?(\w+)[`"]?\s*\((.*)\)\s*;?',part.strip(),re.S|re.I)
        assert m,part[:80]
        table={'table':m[1],'columns':[],'primary_key':[],'foreign_keys':[]}
        for text in split_fields(m[2]):
            if re.match(r'PRIMARY KEY',text,re.I):
                table['primary_key']=names(re.search(r'\((.*?)\)',text)[1]); continue
            if re.match(r'FOREIGN KEY',text,re.I):
                f=re.fullmatch(r'foreign key\s*\((.*?)\)\s*references\s+[`"]?(\w+)[`"]?\s*\((.*?)\)(.*)',text,re.I|re.S)
                assert f,text
                table['foreign_keys'].append({'columns':names(f[1]),'target_table':f[2],'target_columns':names(f[3]),'actions':f[4].strip()})
                continue
            c=re.fullmatch(r'[`"]?(\w+)[`"]?\s+(INTEGER|TEXT)(.*)',text,re.I|re.S)
            assert c,text
            rest=' '.join(c[3].upper().split())
            assert rest in ['', 'DEFAULT NULL', 'NOT NULL', 'NOT NULL PRIMARY KEY'],rest
            table['columns'].append({'name':c[1],'source_type':c[2].upper(),'explicit_not_null':'NOT NULL' in rest,'default_null':'DEFAULT NULL' in rest})
            if 'PRIMARY KEY' in rest: table['primary_key'].append(c[1])
        tables.append(table)
    return tables

out=P/'admission_local'; out.mkdir(exist_ok=False)
records=json.loads((PREV/'CANDIDATES.json').read_text()); summaries=[]
for record in records:
    if record['case_id'] not in {'superhero__750','toxicology__319'}: continue
    src=PREV/record['files']['full-schema.sql']['local_path']
    assert hashlib.sha256(src.read_bytes()).hexdigest()==record['files']['full-schema.sql']['sha256']
    tables=inventory(src.read_text()); by_name={t['table']:t for t in tables}
    constraints=[]
    for t in tables:
        columns={c['name'] for c in t['columns']}
        assert set(t['primary_key']) <= columns
        if t['primary_key']: constraints.append({'primary':[t['table']+'.'+c for c in t['primary_key']]})
        constraints.extend({'not_null':t['table']+'.'+c['name']} for c in t['columns'] if c['explicit_not_null'])
        for f in t['foreign_keys']:
            assert len(f['columns'])==len(f['target_columns'])==1
            assert set(f['columns'])<=columns
            assert f['target_table'] in by_name
            assert set(f['target_columns'])<=set(by_name[f['target_table']]['primary_key'])
            constraints.append({'eq':[t['table']+'.'+f['columns'][0],f['target_table']+'.'+f['target_columns'][0]]})
    content={'case_id':record['case_id'],'source_ddl_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'tables':tables,'proposed_polygon_constraint_entries':constraints,'status':'STATIC_MAPPING_INVENTORY_NOT_EXECUTABLE_ADAPTER','bound':{'live_rows_per_table':'0..1','no_forced_nonempty_tables':True},'update_delete_actions':'Retained in source and inventory; must exist on original replay DDL, do not affect validity of a static instance without UPDATE/DELETE','unresolved':['SQLite type affinities versus symbolic integer domain','Range-safe and equality-preserving model concretization','Complete runnable pinned source/dependencies','Owned process-tree RSS and kill/reap protection']}
    file=out/(record['case_id']+'.json'); file.write_text(json.dumps(content,indent=2)+'\n')
    summaries.append({'case_id':record['case_id'],'tables':len(tables),'columns':sum(len(t['columns']) for t in tables),'primary_key_declarations':sum(bool(t['primary_key']) for t in tables),'primary_key_columns':sum(len(t['primary_key']) for t in tables),'explicit_not_null_columns':sum(c['explicit_not_null'] for t in tables for c in t['columns']),'single_column_foreign_keys':sum(len(t['foreign_keys']) for t in tables),'table_column_counts':{t['table']:len(t['columns']) for t in tables},'local_inventory_path':str(file.relative_to(P)),'local_inventory_sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'all_source_declarations_recognized_by_restricted_text_extractor':True,'SQL_executions':0,'polygon_adapter_executed':False})
(P/'C_MAPPING_SUMMARY.json').write_text(json.dumps(summaries,indent=2)+'\n')
print(json.dumps(summaries,indent=2))
