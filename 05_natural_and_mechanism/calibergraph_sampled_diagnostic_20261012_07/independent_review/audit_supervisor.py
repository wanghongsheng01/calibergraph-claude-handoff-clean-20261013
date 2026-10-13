"""One-shot saved-data audit supervisor, adapted from frozen supervisor.run; never runs baseline."""
from pathlib import Path
import fcntl, hashlib, json, os, selectors, subprocess, sys, time
P=Path(__file__).resolve().parent
CONTROL=P.parent.parent/'calibergraph_launch_protocol_v2_20261012_05/runtime'
PYTHON='/opt/homebrew/bin/python3.12'
def exclusive(path, record):
    with path.open("x") as f:
        json.dump(record, f, indent=2)
        f.write("\n"); f.flush(); os.fsync(f.fileno())
    fd = os.open(path.parent, os.O_RDONLY)
    try: os.fsync(fd)
    finally: os.close(fd)

def run(mode, threshold, wall, lock_fd, outdir):
    outdir.mkdir(exist_ok=False)
    started = time.monotonic()
    read_fd, write_fd = os.pipe()
    life_read, life_write = os.pipe()
    sel = selectors.DefaultSelector()
    os.set_blocking(read_fd, False)
    sel.register(read_fd, selectors.EVENT_READ)
    child = None; buffer = b""; events = []; reason = None; last_sample = started
    record = {"mode": mode, "wall_budget_s": wall, "threshold_bytes": threshold,
              "sampling_interval_s": 0.05, "telemetry_silence_stop_s": 2,
              "hard_RSS_limit": False, "possible_overshoot": True}
    def consume():
        nonlocal buffer, last_sample, reason
        try: data = os.read(read_fd, 65536)
        except BlockingIOError: return
        buffer += data
        while b"\n" in buffer:
            line, buffer = buffer.split(b"\n", 1)
            event = json.loads(line); events.append(event)
            if event["kind"] == "rss": last_sample = time.monotonic()
            if event["kind"] == "memory_stop": reason = "MEMORY_SAMPLED_STOP"
    with (outdir / "stdout.txt").open("wb") as stdout, (outdir / "stderr.txt").open("wb") as stderr:
        try:
            child = subprocess.Popen([PYTHON, "-I", "-S", "-B", str(P / "audit_worker.py"), mode,
                                      str(lock_fd), str(write_fd), str(life_read), str(threshold), str(outdir)],
                                     pass_fds=(lock_fd, write_fd, life_read), stdout=stdout, stderr=stderr,
                                     env={"PATH": "/usr/bin:/bin", "LANG": "C", "LC_ALL": "C", "TZ": "UTC",
                                          "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1",
                                          "MKL_NUM_THREADS": "1", "VECLIB_MAXIMUM_THREADS": "1"})
            os.close(write_fd); write_fd = None
            os.close(life_read); life_read = None
            record["pid_for_logging_only"] = child.pid
            while True:
                for _, _ in sel.select(timeout=0.025): consume()
                if child.poll() is not None:
                    consume(); break
                now = time.monotonic()
                if reason is not None: break
                if now - started >= wall: reason = "WALL_STOP"; break
                if now - last_sample >= 2: reason = "TELEMETRY_LOST_STOP"; break
            if child.poll() is None:
                child.kill()  # only this live owned child; fast stop after detection
            child.wait(timeout=2)
            consume()
        except Exception as error:
            record["supervisor_error"] = {"type": type(error).__name__, "message": str(error)}
            reason = reason or "SUPERVISOR_ERROR"
        finally:
            try:
                if child is not None and child.poll() is None:
                    child.kill(); child.wait(timeout=2)
            except Exception as error:
                record["cleanup_error"] = {"type": type(error).__name__, "message": str(error)}
            finally:
                record["reaped"] = child is not None and child.returncode is not None
                record["returncode"] = child.returncode if child is not None else None
                record["elapsed_s"] = time.monotonic() - started
                record["stop_reason"] = reason
                rss = [e for e in events if e["kind"] == "rss"]
                record["observed_peak_RSS_bytes"] = max((e["rss"] for e in rss), default=None)
                record["max_observed_sample_gap_s"] = max((b["t"] - a["t"] for a,b in zip(rss,rss[1:])), default=None)
                record["samples"] = len(rss)
                (outdir / "telemetry.jsonl").write_text("".join(json.dumps(e)+"\n" for e in events))
                (outdir / "RECEIPT.json").write_text(json.dumps(record, indent=2)+"\n")
                for fd in (write_fd, life_read, life_write, read_fd):
                    if fd is not None: os.close(fd)
                sel.close()
    return record
def main():
    with (CONTROL/'owned.lock').open('a') as lock:
        fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        exclusive(P/'REVIEW_ONCE.json',{'kind':'saved_data_sqlite_audit_only','baseline_calls':0,'worker_sha256':hashlib.sha256((P/'audit_worker.py').read_bytes()).hexdigest(),'supervisor_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'guard_sha256':hashlib.sha256((P.parent/'guard.py').read_bytes()).hexdigest()})
        result=run('audit',1024**3,60,lock.fileno(),P/'run')
        print(json.dumps(result))
        if not result['reaped'] or result['returncode']!=0 or result['stop_reason'] is not None:raise SystemExit('Audit failed or resource-stopped; no automatic retry')
if __name__=='__main__':main()
