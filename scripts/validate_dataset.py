#!/usr/bin/env python3
"""Validate AIDATA JSONL records using only the Python standard library.

Usage:
  python scripts/validate_dataset.py data/seeds/reasoning_coding.jsonl
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

TASK_TYPES = {
    "reasoning", "math", "coding", "debugging", "testing",
    "code_review", "refactoring", "planning", "knowledge_qa",
}
SPLITS = {"train", "validation", "eval"}
PROVENANCE_KINDS = {"synthetic", "human_authored", "licensed_public", "internal_test"}
QUALITY_STATUSES = {"draft", "reviewed", "verified"}
REQUIRED = {
    "schema_version", "id", "task_type", "prompt", "target", "language",
    "split", "provenance", "license", "quality",
}


def validate_record(record: object, line_number: int) -> list[str]:
    errors: list[str] = []
    prefix = f"line {line_number}"
    if not isinstance(record, dict):
        return [f"{prefix}: expected a JSON object"]
    missing = REQUIRED - record.keys()
    if missing:
        errors.append(f"{prefix}: missing fields: {', '.join(sorted(missing))}")
        return errors
    if record["schema_version"] != "1.0":
        errors.append(f"{prefix}: schema_version must be '1.0'")
    identifier = record["id"]
    if not isinstance(identifier, str) or not re.fullmatch(r"[a-z0-9][a-z0-9._-]+", identifier):
        errors.append(f"{prefix}: id must be a stable lowercase identifier")
    for key in ("prompt", "target", "language", "license"):
        if not isinstance(record[key], str) or not record[key].strip():
            errors.append(f"{prefix}: {key} must be a non-empty string")
    if record["task_type"] not in TASK_TYPES:
        errors.append(f"{prefix}: unsupported task_type {record['task_type']!r}")
    if record["split"] not in SPLITS:
        errors.append(f"{prefix}: unsupported split {record['split']!r}")
    provenance = record["provenance"]
    if not isinstance(provenance, dict):
        errors.append(f"{prefix}: provenance must be an object")
    else:
        if provenance.get("kind") not in PROVENANCE_KINDS:
            errors.append(f"{prefix}: invalid provenance.kind")
        if not isinstance(provenance.get("source"), str) or not provenance["source"].strip():
            errors.append(f"{prefix}: provenance.source must be non-empty")
    quality = record["quality"]
    if not isinstance(quality, dict):
        errors.append(f"{prefix}: quality must be an object")
    elif quality.get("status") not in QUALITY_STATUSES:
        errors.append(f"{prefix}: invalid quality.status")
    if "tests" in record and (
        not isinstance(record["tests"], list)
        or not all(isinstance(test, str) for test in record["tests"])
    ):
        errors.append(f"{prefix}: tests must be a list of strings")
    if "tags" in record and (
        not isinstance(record["tags"], list)
        or not all(isinstance(tag, str) for tag in record["tags"])
    ):
        errors.append(f"{prefix}: tags must be a list of strings")
    return errors


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("Usage: python scripts/validate_dataset.py FILE.jsonl [...]", file=sys.stderr)
        return 2
    failures = 0
    seen_ids: dict[str, str] = {}
    count = 0
    for arg in argv[1:]:
        path = Path(arg)
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            print(f"{path}: {exc}", file=sys.stderr)
            failures += 1
            continue
        for line_number, line in enumerate(lines, start=1):
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            count += 1
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                print(f"{path}:{line_number}: invalid JSON: {exc}", file=sys.stderr)
                failures += 1
                continue
            for error in validate_record(record, line_number):
                print(f"{path}:{error}", file=sys.stderr)
                failures += 1
            if isinstance(record, dict) and isinstance(record.get("id"), str):
                previous = seen_ids.get(record["id"])
                if previous:
                    print(f"{path}:{line_number}: duplicate id {record['id']!r} (first seen in {previous})", file=sys.stderr)
                    failures += 1
                else:
                    seen_ids[record["id"]] = f"{path}:{line_number}"
    if failures:
        print(f"FAILED: {failures} issue(s), {count} record(s) scanned.")
        return 1
    print(f"OK: {count} record(s) validated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
