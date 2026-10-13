"""Replay the inline F1 fault injection without starting any process."""
from pathlib import Path
import json
import runpy
import subprocess
import tempfile


class FakeChild:
    pid = -1
    returncode = None

    def wait(self, timeout):
        raise RuntimeError("injected initial wait failure")

    def poll(self):
        return None

    def kill(self):
        raise OSError("injected cleanup kill failure")


class FakeSubprocess:
    TimeoutExpired = subprocess.TimeoutExpired

    @staticmethod
    def Popen(*args, **kwargs):
        return FakeChild()


def main():
    module = runpy.run_path(str(Path(__file__).with_name("validate_launcher_hardened.py")),
                            run_name="engineering_unit_only")
    function = module["run_owned_fixture"]
    namespace = function.__globals__
    namespace["subprocess"] = FakeSubprocess
    with tempfile.TemporaryDirectory(prefix="cg-owned-fault-") as directory:
        namespace["P"] = namespace["CONTROL"] = Path(directory)
        try:
            function("fault_injection", 0.25, 0)
        except RuntimeError as error:
            assert str(error) == "injected initial wait failure"
        else:
            raise AssertionError("Original failure should propagate")
        receipt = json.loads((Path(directory) / "fault_injection.receipt.json").read_text())
        assert receipt["cleanup_status"] == "REAP_UNCONFIRMED_NO_RETRY"
        assert receipt["cleanup_error"]["type"] == "OSError"
        assert receipt["reaped"] is False
        print(json.dumps({"pass": True, "real_children": 0, "receipt": receipt}))


if __name__ == "__main__":
    main()
