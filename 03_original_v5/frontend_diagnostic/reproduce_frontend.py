import time,signal,resource
START=time.monotonic()
signal.signal(signal.SIGALRM,signal.SIG_DFL);signal.setitimer(signal.ITIMER_REAL,20)
resource.setrlimit(resource.RLIMIT_CPU,(14,15));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
import sys,json,sqlite3,hashlib,importlib.util,os
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('frozen_common',HERE/'common_frozen.py');h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
lock_path=HERE.parent/'runtime_v2/runtime_paths.json';lock=h.verify_lock(lock_path,'ed5a8d080c97f07b0484dd44c4956e067e6c1d36bd36beb4eb7ca0c69b64fa0b')
report={'status':'STARTED','scope':'Two static-review-generated adversarial frontend cases; not natural defects; no solver.check or official analyze invoked','cases':[],'helper_sha256':h.sha(HERE/'common_frozen.py'),'program_sha256':h.sha(Path(__file__))}
def checkpoint(phase):report['phase']=phase;h.save(HERE/'RESULT.json',report)
library,z3,constants,Environment,kernel=h.load_runtime(lock,checkpoint,report)
env=Environment(timer=False,generate_code=False,show_counterexample=False,dialect=constants.DIALECT.MYSQL)
for identifier,other in [('V$X','V_DOLLAR_X'),('A.B','A____B')]:
 schema={'F':{'K':'INT',identifier:'INT',other:'INT'},'D':{'K':'INT'}}
 pair=[f'SELECT SUM(F.`{identifier}`) FROM F JOIN D ON F.K=D.K',f'SELECT SUM(F.{other}) FROM F JOIN D ON F.K=D.K']
 row={'id':identifier,'schema':schema,'pair':pair,'database':{'F':[[1,2,7]],'D':[[1]]},'parsed_asts':[],'plans':[]}
 row['sqlite']=h.replay(schema,pair,row['database'])
 for sql in pair:
  try:
   ast=env.parse_sql_query(sql);row['parsed_asts'].append(ast)
   from dataclasses import asdict
   plan=kernel.recognize(ast,schema,identifier_encoding='verieql_double_underscore');row['plans'].append(asdict(plan))
  except Exception as exc:row.setdefault('errors',[]).append({'type':type(exc).__name__,'reason':str(exc)})
 row['same_plan']=len(row['plans'])==2 and row['plans'][0]==row['plans'][1]
 row['same_ast']=len(row['parsed_asts'])==2 and row['parsed_asts'][0]==row['parsed_asts'][1]
 report['cases'].append(row);checkpoint('CASE_RECORDED')
env.__exit__(None,None,None)
report['status']='COMPLETE';report['wall_seconds']=time.monotonic()-START;report['cpu_seconds']=h.cpu_seconds();report['peak_rss_bytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
checkpoint('COMPLETE');print(json.dumps(report,ensure_ascii=False),flush=True);os._exit(0)
