import os,sys,time,signal,ctypes,subprocess,json,resource
from pathlib import Path
START=time.monotonic()
ACTIVE=None
HERE=Path(__file__).resolve().parent
OUT=HERE/'runs'/'full_scan_all_01_supervision.json'
def emergency(*unused):
 if ACTIVE is not None:
  try: os.kill(ACTIVE,signal.SIGKILL)
  except ProcessLookupError: pass
 os._exit(124)
signal.signal(signal.SIGALRM,emergency)
signal.setitimer(signal.ITIMER_REAL,65)
class Info(ctypes.Structure):
 _fields_=[(n,ctypes.c_uint64) for n in ('virtual_size','resident_size','total_user','total_system','threads_user','threads_system')]+[(n,ctypes.c_int32) for n in ('policy','faults','pageins','cow_faults','messages_sent','messages_received','syscalls_mach','syscalls_unix','csw','threadnum','numrunning','priority')]
probe=ctypes.CDLL(None).proc_pidinfo
probe.argtypes=[ctypes.c_int,ctypes.c_int,ctypes.c_uint64,ctypes.c_void_p,ctypes.c_int]
probe.restype=ctypes.c_int
assert ctypes.sizeof(Info)==96
OUT.parent.mkdir(exist_ok=True)
assert not OUT.exists()
lock=HERE.parent/'runtime_v2'/'runtime_paths.json'
cmd=[sys.executable,'-B','-I','-S',str(HERE/'scan_eligibility_all.py'),'--runtime-lock',str(lock),'--expected-lock-sha256','ed5a8d080c97f07b0484dd44c4956e067e6c1d36bd36beb4eb7ca0c69b64fa0b','--out-dir',str(HERE/'runs'/'full_scan_all_01')]
record={'command':cmd,'status':'STARTING','rss_limit_bytes':1073741824,'wall_limit_seconds':61,'sampled_peak_rss_bytes':0,'sampled_max_threads':0}
OUT.write_text(json.dumps(record,indent=2)+'\n')
with (OUT.parent/'full_scan_all_01.stdout').open('xb') as stdout,(OUT.parent/'full_scan_all_01.stderr').open('xb') as stderr:
 child=subprocess.Popen(cmd,cwd=HERE,env={'PATH':'/usr/bin:/bin','OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1'},stdin=subprocess.DEVNULL,stdout=stdout,stderr=stderr)
 ACTIVE=child.pid
 while child.poll() is None:
  info=Info();count=probe(child.pid,4,0,ctypes.byref(info),ctypes.sizeof(info))
  if count!=ctypes.sizeof(info):
   if child.poll() is None:record['stop_reason']='RSS_UNAVAILABLE';child.kill()
   break
  record['sampled_peak_rss_bytes']=max(record['sampled_peak_rss_bytes'],info.resident_size)
  record['sampled_max_threads']=max(record['sampled_max_threads'],info.threadnum)
  if info.resident_size>=1073741824 or time.monotonic()-START>=61:
   record['stop_reason']='RSS_OR_WALL';child.kill();break
  time.sleep(0.1)
 record.update(exit_code=child.wait(timeout=1),status='EXITED',wall_seconds=time.monotonic()-START)
 ACTIVE=None
OUT.write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record),flush=True)
