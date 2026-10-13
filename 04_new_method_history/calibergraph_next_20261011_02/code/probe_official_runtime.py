"""Read-only metadata/hash probe. Does not import/load/execute target code.

Run with python3 -B -I -S. Writes only the explicitly requested new output.
This is availability evidence, not an import/ABI/solver smoke-test PASS.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse, hashlib, json, resource, time

OLD = Path('/Users/loctek/Documents/Codex/2026-10-09/task-7/calibergraph_revision_20261009/today_20261011')
INPUT = Path('/Users/loctek/Documents/Codex/2026-10-11/task-3/calibergraph_next_20261011_01/data/development.jsonl')

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(262144),b''):
            h.update(b)
    return h.hexdigest()

def main():
    start=time.monotonic()
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args()
    lock_path=OLD/'runtime_v3/runtime_paths.json'
    lock=json.loads(lock_path.read_text())
    roots={k:lock[k] for k in ('source_root','binding_root','support_root')}
    roots.update({f'dependency_{i}':p for i,p in enumerate(lock['dependency_roots'])})
    rels=('__main__.py','environment.py','constants.py','utils.py','scope.py',
          'parsers/sql_parser.py','parsers/constraint_parser.py','visitors/visitor.py',
          'verifiers/verifier.py','formulas/tables/base_table.py','parallel/cli_within_bound.py')
    selected=[Path(lock['source_root'])/r for r in rels]
    selected += [Path(lock['native_path']),Path(lock['binding_root'])/'z3/__init__.py',
                 Path(lock['binding_root'])/'z3/z3core.py',Path(lock['binding_root'])/'z3/z3.py']
    records=[]
    for p in selected:
        if time.monotonic()-start>20:
            raise RuntimeError('static probe exceeded 20 second cooperative budget')
        exists=p.is_file()
        actual=digest(p) if exists else None
        records.append({'path':str(p),'exists':exists,'bytes':p.stat().st_size if exists else None,
                        'sha256':actual,'locked_sha256':lock['files'].get(str(p)),
                        'matches_locked_hash':actual==lock['files'].get(str(p)) if exists else False})
    cases=[json.loads(line) for line in INPUT.read_text().splitlines()]
    result={'status':'STATIC_AVAILABILITY_ONLY','created_utc':datetime.now(timezone.utc).isoformat(),
       'target_imported':False,'native_loaded':False,'parser_called':False,'solver_called':False,
       'runtime_lock':{'path':str(lock_path),'sha256':digest(lock_path),'prior_status':lock['status'],
                       'expected_native_version':lock['expected_native_version'],
                       'source_commit':lock['source_commit'],'original_native_pin':lock['original_native_pin']},
       'roots':[{'kind':k,'path':p,'is_directory':Path(p).is_dir()} for k,p in roots.items()],
       'selected_entry_files':records,
       'input':{'path':str(INPUT),'sha256':digest(INPUT),'pairs':len(cases),'query_slots':sum(len(c['source_record']['pair']) for c in cases)},
       'observed_constraint_operators':sorted({op for c in cases for clause in (c['source_record']['constraint'] or []) for op in clause}),
       'source_call_sequence':['Environment','create_database(full schema, exact positive row count per table)',
                               'add_constraints(full original constraint JSON)','save_checkpoints','analyze(original SQL1, original SQL2)'],
       'limits':['This is not a fresh import/ABI/runtime/semantic validation.','No target dependencies installed or modified.',
                 'The original runtime native pin was unknown; current reconstructed native identity is retained honestly.',
                 'Official current IC semantics differ from ordinary SQL nullable FK/CHECK and same-row column comparisons.'],
       'usage':{'wall_seconds':time.monotonic()-start,'cpu_user_seconds':resource.getrusage(resource.RUSAGE_SELF).ru_utime,
                'cpu_system_seconds':resource.getrusage(resource.RUSAGE_SELF).ru_stime,
                'peak_rss_bytes_macos':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}}
    result['all_selected_paths_match']=all(x['matches_locked_hash'] for x in records) and all(x['is_directory'] for x in result['roots'])
    with args.out.open('x') as f:
        json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({'status':result['status'],'all_selected_paths_match':result['all_selected_paths_match'],
                      'entry_files':len(records),'roots':len(roots),'input':result['input'],'usage':result['usage']},ensure_ascii=False))

if __name__=='__main__':
    main()
