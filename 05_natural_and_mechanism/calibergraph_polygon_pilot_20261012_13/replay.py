"""Original frozen SQLite DDL and SQL; no model repairs or witness search."""
import collections
import sqlite3


def replay(case_dir, inventory, database):
    db=sqlite3.connect(':memory:')
    try:
        db.execute('PRAGMA foreign_keys=ON')
        db.executescript((case_dir/'full-schema.sql').read_text())
        db.execute('BEGIN')
        db.execute('PRAGMA defer_foreign_keys=ON')
        expected={t['table']:t for t in inventory['tables']}
        if set(database)!=set(expected):
            raise ValueError('missing or extra source table')
        types={}
        for table, spec in expected.items():
            rows=database[table];header=rows[0]
            if len(header)!=len(set(header)) or set(header)!={c['name'] for c in spec['columns']}:
                raise ValueError('source column coverage mismatch')
            if len(rows)-1>1: raise ValueError('N=1 bound exceeded')
            for row in rows[1:]:
                if len(row)!=len(header):raise ValueError('row width mismatch')
                for value in row:
                    if type(value) not in (int,str,type(None)):raise ValueError('unadmitted concrete value type')
                    if type(value) is int and not -2**63<=value<2**63:raise ValueError('SQLite integer overflow; no clipping')
                cols=','.join('"'+c.replace('"','""')+'"' for c in header)
                db.execute('INSERT INTO "'+table+'" ('+cols+') VALUES ('+','.join('?' for _ in row)+')',row)
            types[table]=db.execute('SELECT '+','.join('typeof("'+c+'")' for c in header)+' FROM "'+table+'"').fetchall()
        violations=db.execute('PRAGMA foreign_key_check').fetchall()
        if violations:raise ValueError('foreign key violations: '+repr(violations))
        db.commit()
        gold=db.execute((case_dir/'gold.sql').read_text()).fetchall()
        predicted=db.execute((case_dir/'predicted.sql').read_text()).fetchall()
        return {'full_C_valid':True,'foreign_key_check':violations,'gold':gold,'predicted':predicted,
                'different':collections.Counter(gold)!=collections.Counter(predicted),
                'storage_types':types,'source_schema_executed_unchanged':True}
    finally:db.close()
