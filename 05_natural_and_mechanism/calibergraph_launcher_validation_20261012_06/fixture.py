"""Harmless owned-child engineering fixture. Never imports scientific libraries."""
import fcntl
import json
import os
import resource
import sys
import time

mode, lock_path, inherited_fd = sys.argv[1], sys.argv[2], int(sys.argv[3])
record = {"mode": mode, "pid": os.getpid(), "science_calls": 0,
          "python": sys.version, "kernel": os.uname().release}
record["inherited_lock_inode_matches"] = os.fstat(inherited_fd).st_ino == os.stat(lock_path).st_ino
with open(lock_path, "a") as contender:
    try:
        fcntl.flock(contender.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        record["independent_lock_contender_blocked"] = True
    else:
        record["independent_lock_contender_blocked"] = False
        raise RuntimeError("Owned lock did not exclude contender")

resource.setrlimit(resource.RLIMIT_CPU, (60, 60))
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
resource.setrlimit(resource.RLIMIT_FSIZE, (1024 * 1024, 1024 * 1024))
record["cpu_limit_readback_s"] = resource.getrlimit(resource.RLIMIT_CPU)
record["own_peak_rss_bytes_before"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
if mode == "memory_cap_probe":
    budget = 1024 ** 3
    record["requested_AS_bytes"] = budget
    record["AS_before"] = resource.getrlimit(resource.RLIMIT_AS)
    record["RSS_aliases_AS"] = resource.RLIMIT_RSS == resource.RLIMIT_AS
    try:
        resource.setrlimit(resource.RLIMIT_AS, (budget, budget))
    except (ValueError, OSError) as exc:
        record["memory_cap_setter"] = "REJECTED"
        record["exception"] = {"type": type(exc).__name__, "message": str(exc),
                               "errno": getattr(exc, "errno", None)}
    else:
        record["memory_cap_setter"] = "ACCEPTED_NOT_ENFORCEMENT_PROOF"
    record["AS_after"] = resource.getrlimit(resource.RLIMIT_AS)
    record["hard_RSS_cap_verified"] = False
    print(json.dumps(record), flush=True)
elif mode == "deadline_fixture":
    record["state"] = "WAITING_FOR_PARENT_DEADLINE"
    print(json.dumps(record), flush=True)
    time.sleep(10)  # no CPU workload; parent must terminate at 0.25 seconds
else:
    raise ValueError("Unknown fixture mode")
