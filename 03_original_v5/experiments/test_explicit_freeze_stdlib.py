"""Tiny /tmp fixtures for the file copier only; no research target is loaded."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile

HERE = Path(__file__).resolve().parent


def main():
    spec = importlib.util.spec_from_file_location("freeze_fixture_only", HERE / "freeze_explicit_review_package.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    passed = []
    with tempfile.TemporaryDirectory(prefix="caliber-freeze-unit-") as temporary:
        root = Path(temporary).resolve()
        files = []
        for name, content in [("paper.pdf", b"%PDF-1.4\nSYNTHETIC COPY TEST ONLY"),
                              ("compile.json", b'{"synthetic_fixture":true}'),
                              ("review.json", b'{"synthetic_fixture":true}')]:
            path = root / name
            path.write_bytes(content)
            files.append({"source": str(path), "destination": "evidence/" + name,
                          "sha256": module.digest(path), "bytes": len(content)})
        plan = {"schema_version": 1, "status": "FINAL_READY", "root_confirmed_no_active_writers": True,
                "allowed_source_root": str(root), "scope": "SYNTHETIC_FILE_COPY_UNIT_TEST_NOT_A_PAPER_PACKAGE",
                "files": files, "final_manuscript": {"compiled_and_reviews_final": True,
                "pdf_source": str(root / "paper.pdf"), "compile_receipt_source": str(root / "compile.json"),
                "review_sources": [str(root / "review.json")]}}

        def write_plan(name, value):
            path = root / name
            path.write_text(json.dumps(value))
            return path, module.digest(path)

        def must_fail(name, function):
            try:
                function()
            except ValueError:
                passed.append(name)
            else:
                raise AssertionError("expected conservative rejection: " + name)

        path, expected = write_plan("plan.json", plan)
        result = module.snapshot(path, expected, root / "package")
        assert result["status"] == "COMPLETE_EXPLICIT_HASH_VERIFIED_SNAPSHOT"
        assert all(module.digest(root / "package" / f["destination"]) == f["sha256"] for f in files)
        passed.append("explicit_copy_and_destination_hashes")
        must_fail("never_overwrite_package", lambda: module.snapshot(path, expected, root / "package"))
        pending = copy.deepcopy(plan)
        pending["status"] = "WAIT_MANUSCRIPT"
        pp, ph = write_plan("pending.json", pending)
        assert module.snapshot(pp, ph, verify_only=True)["status"] == "EXPLICIT_SOURCE_HASHES_VERIFIED_NO_COPY"
        passed.append("verify_only_pending_without_copy")
        must_fail("pending_plan_cannot_copy", lambda: module.snapshot(pp, ph, root / "pending_package"))
        wrong = copy.deepcopy(plan)
        wrong["files"][0]["sha256"] = "0" * 64
        wp, wh = write_plan("wrong.json", wrong)
        must_fail("changed_source_aborts_preflight", lambda: module.snapshot(wp, wh, root / "wrong_package"))
        assert not (root / "wrong_package").exists()
        unsafe = copy.deepcopy(plan)
        unsafe["files"][0]["destination"] = "../escape"
        up, uh = write_plan("unsafe.json", unsafe)
        must_fail("destination_traversal_rejected", lambda: module.snapshot(up, uh, root / "unsafe_package"))
        link = root / "linked.pdf"
        link.symlink_to(root / "paper.pdf")
        linked = copy.deepcopy(plan)
        linked["files"][0]["source"] = str(link)
        lp, lh = write_plan("linked.json", linked)
        must_fail("source_symlink_rejected", lambda: module.snapshot(lp, lh, root / "linked_package"))
        original_digest = module.digest
        changed = False

        def mutate_after_destination_hash(file):
            nonlocal changed
            value = original_digest(file)
            if not changed and file == root / "race_package/evidence/paper.pdf":
                (root / "paper.pdf").write_bytes(b"SOURCE CHANGED DURING COPY")
                changed = True
            return value

        module.digest = mutate_after_destination_hash
        must_fail("source_change_during_copy_no_complete_manifest", lambda: module.snapshot(path, expected, root / "race_package"))
        assert changed
        assert (root / "race_package/_package_metadata/ABORTED.json").exists()
        assert not (root / "race_package/_package_metadata/MANIFEST.json").exists()
    receipt = {"status": "PASS_STDLIB_FILE_COPY_FIXTURES_ONLY", "passed": passed,
               "count": len(passed), "target_native_solver_execution": "NONE",
               "copied_real_experiment_or_manuscript_outputs": False,
               "tool_sha256": hashlib.sha256((HERE / "freeze_explicit_review_package.py").read_bytes()).hexdigest(),
               "test_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    output = HERE / "FREEZE_TOOL_STDLIB_FIXTURE_RECEIPT.json"
    with output.open("x") as stream:
        json.dump(receipt, stream, indent=2)
        stream.write("\n")
    print(json.dumps({"status": receipt["status"], "count": len(passed),
                      "receipt_sha256": hashlib.sha256(output.read_bytes()).hexdigest()}))


if __name__ == "__main__":
    main()
