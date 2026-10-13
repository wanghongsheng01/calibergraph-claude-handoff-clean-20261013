"""Frozen #1261, N<=1 observation quotient. No solver, generic SQL repair or dropped C."""
from pathlib import Path
import hashlib
import sqlite3

SOURCE_SHA = {'gold.sql':'8ca50bee79653ca58e24c34a734ac718d0b09446486caadef8c513f64c638e82',
 'predicted.sql':'c977e9d8fac35d63504c9cf9f2d84145a195974c58fde06640c4254b3c677028',
 'full-schema.sql':'c4073e59ae5daffad317c7c8938f9839afb68e4fe99ca826480027dea88e58e4'}
def q(name):return '"'+name.replace('"','""')+'"'

def load_contract(source, bound=1):
    if type(bound) is not int or bound != 1:raise ValueError('Only frozen N=1 is proved')
    source=Path(source)
    for name,digest in SOURCE_SHA.items():
        if hashlib.sha256((source/name).read_bytes()).hexdigest()!=digest:raise ValueError('Source drift: '+name)
    db=sqlite3.connect(':memory:');db.executescript((source/'full-schema.sql').read_text())
    tables=[];schema=[];constraints=[]
    for name in ['Examination','Patient','Laboratory']:
        cols=db.execute('PRAGMA table_info('+q(name)+')').fetchall()
        table={'table':name,'columns':[{'name':c[1],'source_type':c[2],'explicit_not_null':bool(c[3]),'default':c[4],'pk_order':c[5]} for c in cols]}
        tables.append(table)
        schema.append({'TableName':name,'PKeys':[],'FKeys':[],'Others':[{'Name':c[1],'Type':'int'} for c in cols]})
        pk=sorted([c for c in cols if c[5]],key=lambda c:c[5])
        if pk:constraints.append({'primary':[name+'.'+c[1] for c in pk]})
        constraints.extend({'not_null':name+'.'+c[1]} for c in cols if c[3])
        for f in db.execute('PRAGMA foreign_key_list('+q(name)+')'):
            assert f[3:5]==('ID','ID') and f[2]=='Patient'
            constraints.append({'eq':[name+'.ID','Patient.ID']})
    ddl_signature=db.execute("SELECT name,sql FROM sqlite_schema WHERE type='table' ORDER BY name").fetchall()
    db.close()
    assert [len(t['columns']) for t in tables]==[13,7,44] and len(constraints)==7
    return {'source':source,'tables':tables,'schema':schema,'constraints':constraints,'ddl_signature':ddl_signature,'bound':1}

def fresh(c):
    db=sqlite3.connect(':memory:');db.execute('PRAGMA foreign_keys=ON')
    db.executescript((c['source']/'full-schema.sql').read_text());return db

def validate_original(c,db):
    # Unqualified original SQL must resolve only to the frozen main schema.
    if db.execute('SELECT 1 FROM temp.sqlite_schema LIMIT 1').fetchone():raise ValueError('TEMP objects may shadow original source')
    if any(row[1] not in ('main','temp') for row in db.execute('PRAGMA database_list')):raise ValueError('Attached schemas outside contract')
    signature=db.execute("SELECT name,sql FROM sqlite_schema WHERE type='table' ORDER BY name").fetchall()
    if signature!=c['ddl_signature']:raise ValueError('Original DDL signature mismatch')
    if db.execute('PRAGMA foreign_key_check').fetchall():raise ValueError('Invalid original FK')
    if db.execute('PRAGMA integrity_check').fetchall()!=[('ok',)]:raise ValueError('Invalid original C')
    for t in c['tables']:
        if db.execute('SELECT count(*) FROM '+q(t['table'])).fetchone()[0]>1:raise ValueError('N=1 exceeded')

def project_original(c,db):
    """Use SQLite stored-value comparisons, covering REAL affinity, TEXT/BLOB and NULL."""
    validate_original(c,db);answer={}
    for t in c['tables']:
        expr=[]
        for col in t['columns']:
            name=col['name'];x=q(name)
            if name=='ID':v='1'
            elif t['table']=='Laboratory' and name=='RF':v='CASE WHEN '+x+' < 20 THEN 0 ELSE 20 END'
            elif t['table']=='Examination' and name=='Thrombosis':v='CASE WHEN '+x+' = 0 THEN 0 ELSE 1 END'
            else:v='0'
            expr.append('CASE WHEN '+x+' IS NULL THEN NULL ELSE '+v+' END')
        rows=db.execute('SELECT '+','.join(expr)+' FROM '+q(t['table'])).fetchall()
        answer[t['table'].lower()]=[[c['name'].lower() for c in t['columns']],*[list(r) for r in rows]]
    return answer

def validate_abstract(c,data):
    """Validate BEFORE lifting: never turn a malformed/FK-invalid model into a valid one."""
    expected={t['table'].lower():t for t in c['tables']}
    if set(data)!=set(expected):raise ValueError('All three source tables required')
    rows={}
    for name,t in expected.items():
        tab=data[name];header=tab[0] if tab else []
        cols=[col['name'].lower() for col in t['columns']]
        if len(header)!=len(set(header)) or set(header)!=set(cols) or len(tab) not in (1,2):raise ValueError('Columns/bound mismatch')
        if len(tab)==1:rows[name]=None;continue
        if len(tab[1])!=len(header):raise ValueError('Row width')
        row=dict(zip(header,tab[1]));rows[name]=row
        for col in t['columns']:
            key=col['name'].lower();v=row[key]
            if v is None:
                if col['explicit_not_null'] or col['pk_order']:raise ValueError('Invalid abstract NN/PK')
            elif type(v) is not int:raise ValueError('Abstract cell must be Int/NULL')
    parent=rows['patient']
    for name in ['examination','laboratory']:
        row=rows[name]
        if row is not None and row['id'] is not None:
            if parent is None or row['id']!=parent['id']:raise ValueError('Invalid abstract FK')
    return rows

def lift_abstract(c,data):
    rows=validate_abstract(c,data);answer={}
    for t in c['tables']:
        name=t['table'].lower();row=rows[name];values=[]
        for col in t['columns']:
            key=col['name'].lower();v=None if row is None else row[key]
            if v is None:values.append(None)
            elif key=='id':values.append(1)
            elif name=='laboratory' and key=='rf':values.append('0' if v<20 else 'z')
            elif name=='examination' and key=='thrombosis':values.append(0 if v==0 else 1)
            else:values.append(0)
        answer[t['table']]=[[col['name'] for col in t['columns']],*([values] if row is not None else [])]
    return answer

def replay_lifted(c,data):
    concrete=lift_abstract(c,data);db=fresh(c)
    try:
        db.execute('BEGIN');db.execute('PRAGMA defer_foreign_keys=ON')
        for table,tab in concrete.items():
            db.executemany('INSERT INTO '+q(table)+' ('+','.join(map(q,tab[0]))+') VALUES ('+','.join('?' for _ in tab[0])+')',tab[1:])
        validate_original(c,db);db.commit()
        outputs=[db.execute((c['source']/name).read_text()).fetchall() for name in ['gold.sql','predicted.sql']]
        return {'concrete':concrete,'outputs':outputs,'different':outputs[0]!=outputs[1],'full_C_valid':True}
    finally:db.close()
