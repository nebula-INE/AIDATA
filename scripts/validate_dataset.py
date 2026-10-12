#!/usr/bin/env python3
"""Validate AIDATA JSONL records using only the Python standard library.

Usage:
  python scripts/validate_dataset.py data/seeds/*.jsonl
  python scripts/validate_dataset.py data/seeds/*.jsonl data/eval/*.jsonl
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

TASK_TYPES = {
    "reasoning", "math", "coding", "debugging", "testing",
    "code_review", "refactoring", "planning", "knowledge_qa",
}
SPLITS = {"train", "validation", "eval"}
PROVENANCE_KINDS = {"synthetic", "human_authored", "licensed_public", "internal_test"}
QUALITY_STATUSES = {"draft", "reviewed", "verified"}
TOP_LEVEL_FIELDS = {
    "schema_version", "id", "task_type", "prompt", "target", "language",
    "split", "provenance", "license", "quality", "tests", "tags",
}
PROVENANCE_FIELDS = {"kind", "source", "source_url", "retrieved_at"}
QUALITY_FIELDS = {"status", "reviewer", "verification", "notes"}
ID_PATTERN = re.compile(r"[a-z0-9][a-z0-9._-]+")


def validate_record(record: object, line_number: int) -> list[str]:
    errors: list[str] = []
    prefix = f"line {line_number}"
    if not isinstance(record, dict):
        return [f"{prefix}: expected a JSON object"]

    required = {
        "schema_version", "id", "task_type", "prompt", "target", "language",
        "split", "provenance", "license", "quality",
    }
    missing = required - record.keys()
    if missing:
        errors.append(f"{prefix}: missing fields: {', '.join(sorted(missing))}")
    extra = record.keys() - TOP_LEVEL_FIELDS
    if extra:
        errors.append(f"{prefix}: unknown fields: {', '.join(sorted(extra))}")

    if record.get("schema_version") != "1.0":
        errors.append(f"{prefix}: schema_version must be '1.0'")

    identifier = record.get("id")
    if not isinstance(identifier, str) or not ID_PATTERN.fullmatch(identifier):
        errors.append(f"{prefix}: id must be a stable lowercase identifier")

    for key in ("prompt", "target", "language", "license"):
        value = record.get(key)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{prefix}: {key} must be a non-empty string")
    if isinstance(record.get("language"), str) and len(record["language"]) < 2:
        errors.append(f"{prefix}: language must contain at least 2 characters")

    task_type = record.get("task_type")
    if not isinstance(task_type, str) or task_type not in TASK_TYPES:
        errors.append(f"{prefix}: unsupported task_type {task_type!r}")
    split = record.get("split")
    if not isinstance(split, str) or split not in SPLITS:
        errors.append(f"{prefix}: unsupported split {split!r}")

    provenance = record.get("provenance")
    if not isinstance(provenance, dict):
        errors.append(f"{prefix}: provenance must be an object")
    else:
        extra_provenance = provenance.keys() - PROVENANCE_FIELDS
        if extra_provenance:
            errors.append(f"{prefix}: unknown provenance fields: {', '.join(sorted(extra_provenance))}")
        kind = provenance.get("kind")
        if not isinstance(kind, str) or kind not in PROVENANCE_KINDS:
            errors.append(f"{prefix}: invalid provenance.kind")
        source = provenance.get("source")
        if not isinstance(source, str) or not source.strip():
            errors.append(f"{prefix}: provenance.source must be non-empty")
        source_url = provenance.get("source_url")
        if source_url is not None and not isinstance(source_url, str):
            errors.append(f"{prefix}: provenance.source_url must be a string")
        retrieved_at = provenance.get("retrieved_at")
        if retrieved_at is not None and (
            not isinstance(retrieved_at, str)
            or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", retrieved_at)
        ):
            errors.append(f"{prefix}: provenance.retrieved_at must use YYYY-MM-DD")

    quality = record.get("quality")
    if not isinstance(quality, dict):
        errors.append(f"{prefix}: quality must be an object")
    else:
        extra_quality = quality.keys() - QUALITY_FIELDS
        if extra_quality:
            errors.append(f"{prefix}: unknown quality fields: {', '.join(sorted(extra_quality))}")
        status = quality.get("status")
        if not isinstance(status, str) or status not in QUALITY_STATUSES:
            errors.append(f"{prefix}: invalid quality.status")
        for key in ("reviewer", "verification", "notes"):
            value = quality.get(key)
            if value is not None and not isinstance(value, str):
                errors.append(f"{prefix}: quality.{key} must be a string")

    for key in ("tests", "tags"):
        value = record.get(key)
        if key in record and (
            not isinstance(value, list)
            or not all(isinstance(item, str) for item in value)
        ):
            errors.append(f"{prefix}: {key} must be a list of strings")
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
                record: Any = json.loads(line)
            except json.JSONDecodeError as exc:
                print(f"{path}:{line_number}: invalid JSON: {exc}", file=sys.stderr)
                failures += 1
                continue
            for error in validate_record(record, line_number):
                print(f"{path}:{error}", file=sys.stderr)
                failures += 1
            if isinstance(record, dict) and isinstance(record.get("id"), str):
                identifier = record["id"]
                previous = seen_ids.get(identifier)
                if previous:
                    print(
                        f"{path}:{line_number}: duplicate id {identifier!r} "
                        f"(first seen in {previous})",
                        file=sys.stderr,
                    )
                    failures += 1
                else:
                    seen_ids[identifier] = f"{path}:{line_number}"

    if failures:
        print(f"FAILED: {failures} issue(s), {count} record(s) scanned.")
        return 1
    print(f"OK: {count} record(s) validated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
