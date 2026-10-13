"""Independent adapter tests. Never import Polygon or run author's test suite."""
import copy
import hashlib
import itertools
import json
from pathlib import Path
import sqlite3
import sys

HERE = Path(__file__).resolve().parent
ADAPTER = HERE.parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(ADAPTER))
import case1172_adapter as a

c = a.load_contract(ADAPTER.parent / 'calibergraph_coverage_boundary_20261012_09/sources_local/thrombosis_prediction__1172')


def outputs(db):
    return [db.execute((c['source'] / s).read_text()).fetchall() for s in ['gold.sql', 'predicted.sql']]


passed = 0
for tbil, sex, key in itertools.product([None, float('-inf'), 1.9999999999999998, 2, 2.0000000000000004, float('inf'), float('nan'), '2', '2x', b'2'], [None, 'M', 'm', 'M\x00', b'M'], [-2**63, 0, 2**63-1]):
    db = a.fresh(c)
    db.execute('INSERT INTO Patient(ID,SEX) VALUES(?,?)', (key, sex))
    db.execute('INSERT INTO Laboratory(ID,Date,`T-BIL`) VALUES(?,?,?)', (key, b'invalid-date', tbil))
    db.execute('INSERT INTO Examination(ID) VALUES(NULL)')
    db.commit()
    projection = a.project_original(c, db)
    assert a.replay_lifted(c, projection)['outputs'] == outputs(db)
    db.close()
    passed += 1

rejected = []
def reject(name, data):
    try:
        a.lift_abstract(c, data)
    except ValueError:
        rejected.append(name)
    else:
        raise AssertionError(name)

x = copy.deepcopy(projection)
x['examination'][1][x['examination'][0].index('id')] = 9
reject('Examination dangling FK', x)
x = copy.deepcopy(projection)
x['patient'][1][x['patient'][0].index('id')] = None
reject('Patient NULL primary key', x)
x = copy.deepcopy(projection)
x['laboratory'][1][x['laboratory'][0].index('id')] = None
reject('Laboratory NULL ID', x)
x = copy.deepcopy(projection)
x['patient'][0][-1] = x['patient'][0][0]
reject('duplicate abstract column', x)

db = a.fresh(c)
db.execute("INSERT INTO Patient(ID,SEX) VALUES(1,'M')")
db.execute('CREATE TEMP TABLE Laboratory AS SELECT * FROM main.Laboratory')
db.execute('INSERT INTO temp.Laboratory(ID,Date,`T-BIL`) VALUES(99,0,2)')
db.commit()
shadow = {'original_outputs': outputs(db)}
try:
    a.validate_original(c, db)
except ValueError as exc:
    shadow.update(rejected=True, error=str(exc))
else:
    shadow.update(rejected=False, replay_outputs=a.replay_lifted(c, a.project_original(c, db))['outputs'])
db.close()

result = {'adapter_sha256': hashlib.sha256((ADAPTER / 'case1172_adapter.py').read_bytes()).hexdigest(), 'sqlite_version': sqlite3.sqlite_version, 'direct_adapter_cross_product_passes': passed, 'negative_cases_passed': rejected, 'temp_shadow_regression': shadow, 'solver_calls': 0, 'status': 'PASS' if shadow['rejected'] else 'FIX_REQUIRED_TEMP_SHADOW'}
(HERE / 'adapter_semantic_check.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result))
