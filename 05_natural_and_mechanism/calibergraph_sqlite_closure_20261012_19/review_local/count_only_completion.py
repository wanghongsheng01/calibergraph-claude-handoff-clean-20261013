"""Complete only the previously blocked independent COUNT unit; no SQLite case rerun."""
from pathlib import Path
import json,runpy,time,traceback
HERE=Path(__file__).resolve().parent
started=time.monotonic();report={'status':'STARTED','prior_replays_not_rerun':True}
try:
    checks=runpy.run_path(str(HERE/'independent_validation.py'),run_name='independent_count_only_library')
    report['count_star']=checks['validate_count_ast']()
    report['status']='PASS'
except BaseException as error:
    report.update(status='FAILED',error=repr(error),traceback=traceback.format_exc());raise
finally:
    report['elapsed_s']=time.monotonic()-started
    with (HERE/'count_only_completion.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
    print(json.dumps({'independent_count_completion':report['status'],'elapsed_s':report['elapsed_s']}))
