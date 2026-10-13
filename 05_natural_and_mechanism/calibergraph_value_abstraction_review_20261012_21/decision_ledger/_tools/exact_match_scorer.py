#!/usr/bin/env python3
"""Deterministically score complete JSONL predictions with scalar exact match."""
import argparse
import csv
import json
import math
import os
from pathlib import Path


def unique_object(pairs):
    value = {}
    for key, child in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON key: {key}")
        value[key] = child
    return value


def scalar(value):
    if isinstance(value, (dict, list)) or value is None or (isinstance(value, float) and not math.isfinite(value)):
        raise ValueError("exact-match values must be finite JSON scalars")
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def rows(path):
    result = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line, object_pairs_hook=unique_object)
        if not isinstance(value, dict):
            raise ValueError(f"{path}: line {number} is not an object")
        result.append(value)
    if not result:
        raise ValueError(f"{path}: no rows")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--gold", required=True)
    parser.add_argument("--identity-field", required=True)
    parser.add_argument("--gold-value-field", required=True)
    parser.add_argument("--method-field", action="append", required=True, help="METHOD_ID=PREDICTION_COLUMN")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    predictions_path, gold_path, out = Path(args.predictions), Path(args.gold), Path(args.out)
    if out.exists():
        raise SystemExit(f"Refusing to overwrite: {out}")
    methods = []
    for raw in args.method_field:
        if "=" not in raw:
            raise SystemExit("--method-field requires METHOD_ID=PREDICTION_COLUMN")
        method, field = raw.split("=", 1)
        if not method or not field:
            raise SystemExit("method and prediction column must be nonempty")
        methods.append((method, field))
    if len({method for method, _ in methods}) != len(methods) or len({field for _, field in methods}) != len(methods):
        raise SystemExit("method IDs and prediction columns must be unique")
    expected_prediction_fields = {args.identity_field} | {field for _, field in methods}
    if args.identity_field in {field for _, field in methods} or args.identity_field == args.gold_value_field:
        raise SystemExit("identity, gold, and prediction fields must be distinct")

    predictions = {}
    for row in rows(predictions_path):
        if set(row) != expected_prediction_fields:
            raise SystemExit("prediction rows must contain exactly identity and registered method fields")
        item = row.get(args.identity_field)
        if not isinstance(item, str) or not item or item in predictions:
            raise SystemExit("prediction identities must be unique nonempty strings")
        for _, field in methods:
            scalar(row[field])
        predictions[item] = row
    gold = {}
    for row in rows(gold_path):
        if set(row) != {args.identity_field, args.gold_value_field}:
            raise SystemExit("gold rows must contain exactly identity and gold fields")
        item = row.get(args.identity_field)
        if not isinstance(item, str) or not item or item in gold:
            raise SystemExit("gold identities must be unique nonempty strings")
        scalar(row[args.gold_value_field])
        gold[item] = row[args.gold_value_field]
    if set(predictions) != set(gold):
        raise SystemExit("prediction and gold identities must match exactly")

    out.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(out, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow([args.identity_field, "method", "score"])
        for item in sorted(predictions):
            for method, field in methods:
                writer.writerow([item, method, int(scalar(predictions[item][field]) == scalar(gold[item]))])
        handle.flush()
        os.fsync(handle.fileno())


if __name__ == "__main__":
    main()
