"""Original frozen SQL/DDL SQLite witnesses. Called only by the one-shot budgeted batch."""
from pathlib import Path
import collections,hashlib,json,sqlite3,time,traceback
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
SOURCE=ROOT/'calibergraph_coverage_boundary_20261012_09/sources_local'
q=lambda s:'"'+s.replace('"','""')+'"'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def school(key,score):
    return ({'CDSCode':key,'School':'S','AdmFName1':'Ricci','AdmLName1':'Ulrich','StatusType':'X','County':'X','District':'X','DOC':'X','DOCType':'X','LastUpdate':'2016-01-01'},
            {'cds':key,'rtype':'S','enroll12':0,'NumTstTakr':0,'AvgScrWrite':score})
def schools(scores):
    pairs=[school('K'+str(i+1),s) for i,s in enumerate(scores)]
    return {'schools':[a for a,b in pairs],'satscores':[b for a,b in pairs]}
def football(id,date):
    return {'League':[{'id':1,'country_id':None,'name':'Germany 1. Bundesliga'}],
            'Match':[{'id':id,'league_id':1,'date':date}]}
def debit(multi=False):
    d={'customers':[{'CustomerID':1}], 'gasstations':[{'GasStationID':1}],
       'transactions_1k':[{'TransactionID':1,'Date':'2012-08-25','CustomerID':1,'GasStationID':1,'Price':634.8}],
       'yearmonth':[{'CustomerID':1,'Date':'2012-01','Consumption':1.0}]}
    if multi:
        d['transactions_1k'].append({'TransactionID':2,'Date':'2012-08-24','CustomerID':1,'GasStationID':1,'Price':634.8})
        d['yearmonth']=[{'CustomerID':1,'Date':date,'Consumption':value} for date,value in [('2012-01',10.0),('2012-02',20.0),('2013-01',5.0)]]
    return d
CANDIDATES=[
 ('1073_invalid_date','european_football_2__1073',football(1,'2008-08-invalid'),'date parser versus prefix',[[1]],[[0]]),
 ('1073_nullable_pk','european_football_2__1073',football(None,'2008-08-01'),'COUNT nullable INT primary key versus COUNT(*)',[[0]],[[1]]),
 ('45_text_N1','california_schools__45',schools(['x']),'source-legal nonnumeric stored TEXT', [['S','x']],[['S',0.0]]),
 ('45_large_int_N1','california_schools__45',schools([9007199254740993]),'single integer versus AVG binary64', [['S',9007199254740993]],[['S',9007199254740992.0]]),
 ('45_group_N2','california_schools__45',schools([1,3]),'two distinct keys sharing group name', [['S',1],['S',3]],[['S',2.0]]),
 ('45_bag_N2','california_schools__45',schools([0,0]),'bag multiplicity with identical exact numeric values', [['S',0],['S',0]],[['S',0.0]]),
 ('1526_N1','debit_card_specializing__1526',debit(),'original date and missing-year scalar effects', [[1.0]],[[None]]),
 ('1526_sum_scalar','debit_card_specializing__1526',debit(True),'both transaction dates select same customer; monthly SUM versus scalar',[[25.0/30.0]],None),
]
def bag(rows):return collections.Counter(map(tuple,rows))

def run():
    started=time.monotonic();out={'format_version':1,'sqlite_version':sqlite3.sqlite_version,'cases':[]}
    source_freeze=json.loads((ROOT/'calibergraph_polygon_case1261_20261012_17/FIVE_CASE_SCREEN.json').read_text())
    fixed={r['case_id']:r['source_hashes'] for r in source_freeze['rows']}
    for name,case,values,phenomenon,want_gold,want_pred in CANDIDATES:
        t=time.monotonic();d=SOURCE/case
        record={'candidate_id':name,'case_id':case,'phenomenon':phenomenon,'source':{'directory':str(d),'files':{n:{'sha256':sha(d/n)} for n in ['gold.sql','predicted.sql','full-schema.sql']}},'expected_difference':True}
        db=None
        try:
            for n,v in record['source']['files'].items():assert v['sha256']==fixed[case][n],n
            db=sqlite3.connect(':memory:');db.execute('PRAGMA foreign_keys=ON');db.execute('PRAGMA threads=0')
            assert db.execute('PRAGMA foreign_keys').fetchone()==(1,)
            db.executescript((d/'full-schema.sql').read_text());db.execute('BEGIN');db.execute('PRAGMA defer_foreign_keys=ON')
            names=[r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
            assert set(values)<=set(names)
            metadata={};tables={}
            for table in names:
                info=db.execute('PRAGMA table_info('+q(table)+')').fetchall();cols=[r[1] for r in info]
                indexes=db.execute('PRAGMA index_list('+q(table)+')').fetchall()
                metadata[table]={'table_info':info,'foreign_key_list':db.execute('PRAGMA foreign_key_list('+q(table)+')').fetchall(),
                     'index_list':indexes,'unique_index_columns':{r[1]:db.execute('PRAGMA index_info('+q(r[1])+')').fetchall() for r in indexes if r[2]}}
                for partial in values.get(table,[]):
                    assert set(partial)<=set(cols),(table,set(partial)-set(cols))
                    row=[partial.get(c) for c in cols]
                    db.execute('INSERT INTO '+q(table)+' ('+','.join(map(q,cols))+') VALUES ('+','.join('?' for c in cols)+')',row)
                tables[table]={'columns':cols}
            fk=db.execute('PRAGMA foreign_key_check').fetchall();assert not fk,fk
            db.commit();integrity=db.execute('PRAGMA integrity_check').fetchall();assert integrity==[('ok',)],integrity
            nn_checks=[];unique_checks=[]
            for table in names:
                cols=tables[table]['columns'];stored=[list(r) for r in db.execute('SELECT '+','.join(map(q,cols))+' FROM '+q(table))]
                intended=[[partial.get(c) for c in cols] for partial in values.get(table,[])]
                assert bag(stored)==bag(intended),('storage modified witness',table,stored,intended)
                tables[table]['stored_rows']=stored
                tables[table]['stored_types']=[list(r) for r in db.execute('SELECT '+','.join('typeof('+q(c)+')' for c in cols)+' FROM '+q(table))]
                for col in metadata[table]['table_info']:
                    if col[3] or (col[5] and col[2].upper()=='INTEGER' and sum(bool(x[5]) for x in metadata[table]['table_info'])==1):
                        n=db.execute('SELECT COUNT(*) FROM '+q(table)+' WHERE '+q(col[1])+' IS NULL').fetchone()[0];assert n==0
                        nn_checks.append([table,col[1],n])
                for index,icols in metadata[table]['unique_index_columns'].items():
                    cs=[r[2] for r in icols];assert all(c is not None for c in cs)
                    query='SELECT COUNT(*) FROM '+q(table)+' WHERE '+' AND '.join(q(c)+' IS NOT NULL' for c in cs)+' GROUP BY '+','.join(map(q,cs))+' HAVING COUNT(*)>1'
                    violations=db.execute(query).fetchall();assert not violations;unique_checks.append([table,index,cs,violations])
            gold=[list(r) for r in db.execute((d/'gold.sql').read_text())];pred=[list(r) for r in db.execute((d/'predicted.sql').read_text())]
            different=bag(gold)!=bag(pred);assert different
            assert bag(gold)==bag(want_gold),(gold,want_gold)
            if want_pred is not None:assert bag(pred)==bag(want_pred),(pred,want_pred)
            else:assert pred in [[[0.5]],[[0.75]]],pred
            record.update(status='VALIDATED_NEQ',tables=tables,outputs={'gold':gold,'predicted':pred},different=different,
                active_rows={n:len(t['stored_rows']) for n,t in tables.items()},N=max(len(t['stored_rows']) for t in tables.values()),total_rows=sum(len(t['stored_rows']) for t in tables.values()),
                author_validation={'foreign_keys_enabled':True,'foreign_key_check':fk,'integrity_check':integrity,'nn_checks':nn_checks,'unique_checks':unique_checks,'full_schema_metadata':metadata,'all_source_tables_and_columns_preserved':True,'storage_matches_candidate':True})
        except Exception as error:
            record.update(status='FAILED',error=repr(error),traceback=traceback.format_exc())
        finally:
            if db:db.close()
            record['elapsed_s']=time.monotonic()-t;out['cases'].append(record)
            (HERE/'replays.json').write_text(json.dumps(out,indent=2)+'\n')
    out['elapsed_s']=time.monotonic()-started;out['status']='PASS' if all(c['status']=='VALIDATED_NEQ' for c in out['cases']) else 'HAS_FAILURES'
    (HERE/'replays.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({'replays':out['status'],'cases':[(c['candidate_id'],c['status']) for c in out['cases']]}))
if __name__=='__main__':run()
