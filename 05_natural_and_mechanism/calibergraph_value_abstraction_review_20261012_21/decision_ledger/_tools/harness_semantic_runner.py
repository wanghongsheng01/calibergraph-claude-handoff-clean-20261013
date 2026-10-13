#!/usr/bin/env python3
"""Execute the five closed automatic-v1 harness semantics on a JSON fixture."""
import csv
import io
import json
import sys
from pathlib import Path

CONTRACTS = {
    "SANDBOX": "deny registered protected-gold paths and hashes to method execution",
    "PARSER": "reject malformed, duplicate-key, duplicate-column, missing, duplicate, and extra identities",
    "SCORER": "recompute exact-match accuracy from canonical prediction and protected-gold scalars",
    "MASK": "expose exactly the registered method-visible fields and no protected or oracle fields",
    "MISSINGNESS": "reject incomplete pairs and preserve the full registered denominator",
}


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def require_string_list(value, label):
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        raise ValueError(f"{label} must be a string list")
    return value


def run_case(fixture):
    kind = fixture.get("kind")
    case_id = fixture.get("case_id")
    contract = fixture.get("contract")
    payload = fixture.get("payload")
    if fixture.get("schema_version") != "1.0" or not isinstance(case_id, str) or kind not in CONTRACTS or contract != CONTRACTS[kind] or not isinstance(payload, dict):
        raise ValueError("fixture header/contract is invalid")
    if kind == "SANDBOX":
        protected_paths = set(require_string_list(payload.get("protected_paths"), "protected_paths"))
        protected_hashes = set(require_string_list(payload.get("protected_sha256"), "protected_sha256"))
        visible_paths = set(require_string_list(payload.get("method_visible_paths"), "method_visible_paths"))
        visible_hashes = set(require_string_list(payload.get("method_visible_sha256"), "method_visible_sha256"))
        passed = not (protected_paths & visible_paths or protected_hashes & visible_hashes)
    elif kind == "PARSER":
        registered = require_string_list(payload.get("registered_ids"), "registered_ids")
        valid_lines = require_string_list(payload.get("valid_jsonl"), "valid_jsonl")
        parsed = [json.loads(line, object_pairs_hook=unique_object) for line in valid_lines]
        valid_ids = [row.get("item_id") for row in parsed if isinstance(row, dict)]
        duplicate_json_rejected = False
        try:
            json.loads(payload.get("duplicate_json_object", ""), object_pairs_hook=unique_object)
        except Exception:
            duplicate_json_rejected = True
        header = next(csv.reader(io.StringIO(payload.get("duplicate_csv_header", ""))), [])
        duplicate_header_rejected = len(header) != len(set(header))
        missing = payload.get("missing_ids")
        duplicate = payload.get("duplicate_ids")
        extra = payload.get("extra_ids")
        passed = (
            valid_ids == registered and len(valid_ids) == len(set(valid_ids))
            and duplicate_json_rejected and duplicate_header_rejected
            and isinstance(missing, list) and set(missing) != set(registered)
            and isinstance(duplicate, list) and len(duplicate) != len(set(duplicate))
            and isinstance(extra, list) and set(extra) != set(registered)
        )
    elif kind == "SCORER":
        predictions, gold = payload.get("predictions"), payload.get("gold")
        expected = payload.get("expected_accuracy")
        if not isinstance(predictions, list) or not isinstance(gold, list) or len(predictions) != len(gold) or not predictions:
            raise ValueError("scorer fixture must contain complete pairs")
        score = sum(canonical(left) == canonical(right) for left, right in zip(predictions, gold)) / len(gold)
        passed = isinstance(expected, (int, float)) and not isinstance(expected, bool) and abs(score - expected) <= 1e-12
    elif kind == "MASK":
        visible = require_string_list(payload.get("registered_visible_fields"), "registered_visible_fields")
        protected = require_string_list(payload.get("protected_fields"), "protected_fields")
        oracle = require_string_list(payload.get("oracle_fields"), "oracle_fields")
        observed = require_string_list(payload.get("observed_fields"), "observed_fields")
        passed = set(observed) == set(visible) and not set(observed) & (set(protected) | set(oracle))
    else:
        registered = require_string_list(payload.get("registered_ids"), "registered_ids")
        by_method = payload.get("ids_by_method")
        passed = isinstance(by_method, dict) and bool(by_method)
        if passed:
            for ids in by_method.values():
                passed = passed and isinstance(ids, list) and len(ids) == len(set(ids)) and set(ids) == set(registered)
    if not passed:
        raise ValueError(f"{kind} semantic assertion failed")
    return {"schema_version": "1.0", "case_id": case_id, "kind": kind, "contract": contract, "result": "PASS"}


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: harness_semantic_runner.py INPUT_JSON OUTPUT_JSON")
    source, destination = map(Path, sys.argv[1:])
    fixture = json.loads(source.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
    result = run_case(fixture)
    with destination.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


if __name__ == "__main__":
    main()
