"""Copy an explicit finalized hash list; no target imports or directory discovery.

A pending plan can be inspected with --verify-only. Actual copying additionally
requires a FINAL_READY root cut, compiled-PDF receipt and final review identities.
The existing output directory is never reused, even after an aborted snapshot.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re


def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def canonical_source(raw, allowed):
    path = Path(raw)
    if not path.is_absolute() or path != path.resolve() or not path.is_file():
        raise ValueError("noncanonical/missing/symlinked source: " + str(path))
    if not path.is_relative_to(allowed):
        raise ValueError("source outside explicit workspace root: " + str(path))
    return path


def validate_plan(plan, *, copying=False):
    if plan.get("schema_version") != 1 or not plan.get("files"):
        raise ValueError("nonempty schema_version=1 explicit plan required")
    allowed = Path(plan["allowed_source_root"])
    if not allowed.is_absolute() or allowed != allowed.resolve():
        raise ValueError("canonical allowed source root required")
    seen_sources, seen_destinations = set(), set()
    for item in plan["files"]:
        source = canonical_source(item["source"], allowed)
        relative = Path(item["destination"])
        if relative.is_absolute() or not relative.parts or any(part in {".", ".."} for part in relative.parts):
            raise ValueError("unsafe relative destination")
        if relative.parts[0] == "_package_metadata":
            raise ValueError("reserved metadata destination")
        if str(source) in seen_sources or relative.as_posix() in seen_destinations:
            raise ValueError("duplicate explicit source/destination")
        if not isinstance(item["sha256"], str) or re.fullmatch("[0-9a-f]{64}", item["sha256"]) is None:
            raise ValueError("invalid SHA256")
        if type(item["bytes"]) is not int or item["bytes"] < 0:
            raise ValueError("invalid byte count")
        if source.stat().st_size != item["bytes"] or digest(source) != item["sha256"]:
            raise ValueError("source changed relative to cut: " + str(source))
        seen_sources.add(str(source))
        seen_destinations.add(relative.as_posix())
    if copying:
        if plan.get("status") != "FINAL_READY" or plan.get("root_confirmed_no_active_writers") is not True:
            raise ValueError("root final cut and no-active-writers confirmation required")
        manuscript = plan.get("final_manuscript", {})
        if manuscript.get("compiled_and_reviews_final") is not True:
            raise ValueError("final manuscript compilation and reviews remain pending")
        required = [manuscript.get("pdf_source"), manuscript.get("compile_receipt_source")]
        reviews = manuscript.get("review_sources", [])
        if not reviews:
            raise ValueError("explicit final review identities required")
        required.extend(reviews)
        if any(not isinstance(raw, str) or raw not in seen_sources for raw in required):
            raise ValueError("final PDF/compile receipt/review omitted from exact source list")
        pdf = Path(manuscript["pdf_source"])
        with pdf.open("rb") as stream:
            if stream.read(5) != b"%PDF-":
                raise ValueError("registered final PDF is not a PDF")
    return allowed


def snapshot(plan_path, expected_sha, output=None, *, verify_only=False):
    plan_path = Path(plan_path)
    if plan_path != plan_path.resolve() or digest(plan_path) != expected_sha:
        raise ValueError("plan path/hash changed")
    raw_plan = plan_path.read_bytes()
    if hashlib.sha256(raw_plan).hexdigest() != expected_sha:
        raise ValueError("plan changed while reading")
    plan = json.loads(raw_plan)
    allowed = validate_plan(plan, copying=not verify_only)
    if verify_only:
        return {"status": "EXPLICIT_SOURCE_HASHES_VERIFIED_NO_COPY", "plan_status": plan.get("status"),
                "file_count": len(plan["files"]), "bytes": sum(f["bytes"] for f in plan["files"]),
                "plan_sha256": expected_sha}
    if output is None:
        raise ValueError("new output path required")
    output = Path(output)
    if not output.is_absolute() or output != output.resolve() or output.exists() or not output.is_relative_to(allowed):
        raise ValueError("new canonical output directory inside workspace required")
    if any(Path(item["source"]).is_relative_to(output) for item in plan["files"]):
        raise ValueError("output may not contain any source")
    output.mkdir(parents=True)
    metadata = output / "_package_metadata"
    metadata.mkdir()
    copied = []
    try:
        for item in plan["files"]:
            source = canonical_source(item["source"], allowed)
            destination = output / item["destination"]
            if not destination.resolve().is_relative_to(output):
                raise ValueError("destination escaped package")
            destination.parent.mkdir(parents=True, exist_ok=True)
            value = hashlib.sha256()
            byte_count = 0
            with source.open("rb") as reader, destination.open("xb") as writer:
                for block in iter(lambda: reader.read(1024 * 1024), b""):
                    writer.write(block)
                    value.update(block)
                    byte_count += len(block)
                writer.flush()
                os.fsync(writer.fileno())
            if byte_count != item["bytes"] or value.hexdigest() != item["sha256"] or digest(destination) != item["sha256"]:
                raise ValueError("source/destination changed during copying: " + str(source))
            copied.append(dict(item))
        # Detect source changes after an earlier file was copied. No COMPLETE
        # manifest is written if any registered byte differs at this last pass.
        validate_plan(plan, copying=True)
        if digest(plan_path) != expected_sha:
            raise ValueError("plan changed before finalization")
        for item in copied:
            if digest(output / item["destination"]) != item["sha256"]:
                raise ValueError("destination changed before finalization")
        with (metadata / "input_plan.json").open("xb") as stream:
            stream.write(raw_plan)
            stream.flush()
            os.fsync(stream.fileno())
        manifest = {"status": "COMPLETE_EXPLICIT_HASH_VERIFIED_SNAPSHOT", "scope": plan.get("scope"),
                    "input_plan_source": str(plan_path), "input_plan_sha256": expected_sha,
                    "file_count": len(copied), "total_source_bytes": sum(f["bytes"] for f in copied),
                    "files": copied, "source_recheck_after_copy": "PASS", "destination_recheck": "PASS",
                    "process_boundary": "Relies on root explicit final cut/no-active-writers assertion; no process probing performed.",
                    "scientific_boundary": "Copies evidence faithfully; returned execution or matching hashes do not imply scientific correctness."}
        target = metadata / "MANIFEST.json"
        temporary = metadata / "MANIFEST.pending"
        manifest_bytes = (json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode()
        manifest_sha = hashlib.sha256(manifest_bytes).hexdigest()
        with temporary.open("xb") as stream:
            stream.write(manifest_bytes)
            stream.flush()
            os.fsync(stream.fileno())
        if digest(temporary) != manifest_sha:
            raise ValueError("manifest temporary hash mismatch")
        with (metadata / "MANIFEST.sha256").open("x") as stream:
            stream.write(manifest_sha + "  MANIFEST.json\n")
            stream.flush()
            os.fsync(stream.fileno())
        result = {"status": manifest["status"], "output": str(output), "file_count": len(copied), "manifest_sha256": manifest_sha}
        temporary.replace(target)  # Final commit; no successful manifest before this point.
        return result

    except BaseException as exc:
        with (metadata / "ABORTED.json").open("x") as stream:
            json.dump({"status": "ABORTED_INCOMPLETE_DO_NOT_DELIVER", "error_type": type(exc).__name__,
                       "reason": str(exc), "copied_before_abort": len(copied)}, stream, indent=2)
            stream.write("\n")
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--expected-plan-sha256", required=True)
    parser.add_argument("--out-dir", type=Path)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    result = snapshot(args.plan, args.expected_plan_sha256, args.out_dir, verify_only=args.verify_only)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
