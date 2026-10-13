"""Bounded owned fixtures, no scientific input, no descendants."""
import resource
import signal
import sys
import time

mode = sys.argv[1]
if mode == 'ignore_term':
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    print('READY', flush=True)
    time.sleep(4)
elif mode == 'hang':
    print('READY', flush=True)
    time.sleep(4)
elif mode == 'normal':
    print('OK', flush=True)
elif mode == 'eof':
    pass
elif mode == 'unknown':
    print('unknown', flush=True)
elif mode == 'self_report':
    print(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss, flush=True)
else:
    raise ValueError(mode)
