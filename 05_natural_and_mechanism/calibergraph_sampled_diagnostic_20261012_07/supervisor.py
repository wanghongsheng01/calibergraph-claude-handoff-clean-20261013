"""One owned worker, persistent markers, sampled stop; no system process listing."""
from pathlib import Path
import fcntl
import hashlib
import json
import os
import selectors
import subprocess
import sys
import time

P = Path(__file__).resolve().parent
CONTROL = P.parent / "calibergraph_launch_protocol_v2_20261012_05/runtime"
PYTHON = "/opt/homebrew/bin/python3.12"


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
            child = subprocess.Popen([PYTHON, "-I", "-S", "-B", str(P / "worker.py"), mode,
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
    action = sys.argv[1]
    with (CONTROL / "owned.lock").open("a") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        if action == "validate":
            marker = P / "VALIDATION_ONCE.json"
            exclusive(marker, {"kind": "synthetic_only", "scientific_launches": 0})
            try: exclusive(marker, {})
            except FileExistsError: pass
            else: raise AssertionError("Marker collision must fail")
            records = [run("synthetic_memory", 64*1024**2, 5, lock.fileno(), P/"synthetic_memory"),
                       run("synthetic_deadline", 1024**3, 0.3, lock.fileno(), P/"synthetic_deadline"),
                       run("synthetic_silence", 1024**3, 4, lock.fileno(), P/"synthetic_silence")]
            assert all(r["reaped"] for r in records)
            assert records[0]["stop_reason"] == "MEMORY_SAMPLED_STOP"
            assert records[0]["observed_peak_RSS_bytes"] > 64*1024**2
            assert records[1]["stop_reason"] == "WALL_STOP"
            assert records[2]["stop_reason"] == "TELEMETRY_LOST_STOP"
            for mode in ("synthetic_memory", "synthetic_deadline", "synthetic_silence"):
                assert json.loads((P/mode/"LOCK_CHECK.json").read_text())["contender_blocked"]
            verdict = {"pass": True, "records": records, "scientific_launches": 0,
                       "memory_test_threshold_bytes":64*1024**2, "science_threshold_bytes":1024**3,
                       "test_does_not_prove_hard_cap":True}
            (P/"VALIDATION.json").write_text(json.dumps(verdict,indent=2)+"\n")
            print(json.dumps(verdict))
        elif action == "science":
            assert json.loads((P/"VALIDATION.json").read_text())["pass"]
            freeze = json.loads((P/"FREEZE.json").read_text())
            for item in freeze["files"]:
                assert hashlib.sha256(Path(item["path"]).read_bytes()).hexdigest() == item["sha256"], item["path"]
            exclusive(CONTROL/"ATTEMPT_STARTED.json", {"run":P.name,"freeze_sha256":hashlib.sha256((P/"FREEZE.json").read_bytes()).hexdigest()})
            result = run("science", 1024**3, 60, lock.fileno(), P/"science")
            print(json.dumps(result))
        else: raise ValueError("Unknown action")


if __name__ == "__main__": main()
