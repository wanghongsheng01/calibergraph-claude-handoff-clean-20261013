"""One-shot engineering validation only. No route to launch a scientific worker."""
from pathlib import Path
import datetime
import fcntl
import hashlib
import json
import os
import subprocess
import sys
import time

P = Path(__file__).resolve().parent
CONTROL = P.parent / "calibergraph_launch_protocol_v2_20261012_05/runtime"
PYTHON = "/opt/homebrew/bin/python3.12"


def durable_exclusive(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    fd = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def run_owned_fixture(mode, budget, lock_fd):
    started = time.monotonic()
    result = {"mode": mode, "deadline_s": budget, "science_calls": 0}
    child = None
    with (P / (mode + ".stdout.jsonl")).open("wb") as out, (P / (mode + ".stderr.txt")).open("wb") as err:
        try:
            child = subprocess.Popen(
                [PYTHON, "-I", "-S", "-B", str(P / "fixture.py"), mode,
                 str(CONTROL / "owned.lock"), str(lock_fd)],
                pass_fds=(lock_fd,), stdout=out, stderr=err,
                env={"PATH": "/usr/bin:/bin", "LANG": "C", "LC_ALL": "C",
                     "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1"})
            result["pid_for_logging_only"] = child.pid
            try:
                child.wait(timeout=max(0, budget - (time.monotonic() - started)))
                result["deadline_triggered"] = False
            except subprocess.TimeoutExpired:
                result["deadline_triggered"] = True
                child.terminate()
                try:
                    child.wait(timeout=0.5)
                except subprocess.TimeoutExpired:
                    result["kill_escalation"] = True
                    child.kill()
                    child.wait(timeout=2)
        finally:
            # Only the still-owned direct child can be signalled; never a stored PID.
            if child is not None and child.poll() is None:
                child.kill()
                child.wait(timeout=2)
            result["reaped"] = child is not None and child.returncode is not None
            result["returncode"] = child.returncode if child is not None else None
            result["elapsed_s"] = time.monotonic() - started
            (P / (mode + ".receipt.json")).write_text(json.dumps(result, indent=2) + "\n")
    return result


def main():
    assert sys.platform == "darwin"
    CONTROL.mkdir(exist_ok=True)
    with (CONTROL / "owned.lock").open("a") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        # No scientific attempt marker is created. This fixture batch is separately one-shot.
        marker = P / "ENGINEERING_ONCE.json"
        durable_exclusive(marker, {"kind": "engineering_only", "science_calls": 0,
                                  "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                                  "fixture_sha256": hashlib.sha256((P / "fixture.py").read_bytes()).hexdigest()})
        try:
            durable_exclusive(marker, {"invalid_second_attempt": True})
        except FileExistsError:
            marker_exclusion = True
        else:
            raise AssertionError("One-shot marker failed")
        cap = run_owned_fixture("memory_cap_probe", 3, lock.fileno())
        assert cap["reaped"] and cap["returncode"] == 0
        probe = json.loads((P / "memory_cap_probe.stdout.jsonl").read_text())
        assert probe["inherited_lock_inode_matches"] and probe["independent_lock_contender_blocked"]
        timeout = run_owned_fixture("deadline_fixture", 0.25, lock.fileno())
        assert timeout["reaped"] and timeout["deadline_triggered"] and timeout["returncode"] < 0
        fixture = json.loads((P / "deadline_fixture.stdout.jsonl").read_text())
        assert fixture["state"] == "WAITING_FOR_PARENT_DEADLINE"
        report = {"status": "ENGINEERING_VALIDATION_COMPLETE_SCIENCE_BLOCKED",
                  "scientific_launches": 0, "fixture_children": 2, "max_concurrent_fixture_children": 1,
                  "exclusive_marker_collision_rejected": marker_exclusion,
                  "inherited_lock_and_contender_validated": True,
                  "cpu_limit_set_and_readback": probe["cpu_limit_readback_s"],
                  "cpu_exhaustion_not_tested": True, "deadline_and_reap_validated": True,
                  "memory_probe": probe, "receipts": [cap, timeout],
                  "memory_blocker": "1 GiB worker-wide hard memory enforcement not established",
                  "not_validated": ["parent crash/orphan termination", "scientific imports and no-descendant path",
                                    "hard memory enforcement", "actual 60-second scientific execution"],
                  "no_permission_escalation": True, "no_system_process_listing": True}
        (P / "VALIDATION.json").write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report))


if __name__ == "__main__":
    main()
