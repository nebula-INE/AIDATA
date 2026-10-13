#!/usr/bin/env python3
"""Export a human review queue and validate completed review logs.

This tool never edits source JSONL or promotes quality.status automatically.
A human must inspect the prompt and target, record a decision, and make any
approved dataset edits separately.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

FIELDS = (
    "id", "source_file", "language", "task_type", "split", "tags",
    "prompt", "target", "reviewer", "review_date", "decision",
    "answer_cardinality", "expected_behavior", "interpretation",
    "constraint_checklist", "evidence_calibration", "language_quality",
    "rationale",
)
DECISIONS = {"accept", "revise", "retire"}
CARDINALITIES = {"single", "multiple", "context_dependent", "clarification_needed"}
BEHAVIORS = {"answer", "list_alternatives", "state_uncertainty", "ask_clarification"}


def read_jsonl(paths: list[str]) -> tuple[list[dict[str, Any]], list[str]]:
    records: list[dict[str, Any]] = []
    errors: list[str] = []
    for filename in paths:
        path = Path(filename)
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            errors.append(f"{path}: {exc}")
            continue
        for line_number, line in enumerate(lines, 1):
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"{path}:{line_number}: invalid JSON: {exc}")
                continue
            if not isinstance(item, dict):
                errors.append(f"{path}:{line_number}: expected a JSON object")
                continue
            item["_source_file"] = str(path)
            records.append(item)
    return records, errors


def export_queue(input_paths: list[str], output_path: str) -> int:
    records, errors = read_jsonl(input_paths)
    ids: set[str] = set()
    for record in records:
        identifier = record.get("id")
        if not isinstance(identifier, str) or not identifier:
            errors.append(f"record in {record.get('_source_file')} has missing/invalid id")
        elif identifier in ids:
            errors.append(f"duplicate record id across review queue: {identifier}")
        else:
            ids.add(identifier)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        for record in records:
            quality = record.get("quality") or {}
            writer.writerow({
                "id": record.get("id", ""),
                "source_file": record.get("_source_file", ""),
                "language": record.get("language", ""),
                "task_type": record.get("task_type", ""),
                "split": record.get("split", ""),
                "tags": "|".join(record.get("tags", [])) if isinstance(record.get("tags", []), list) else "",
                "prompt": record.get("prompt", ""),
                "target": record.get("target", ""),
                "reviewer": "",
                "review_date": "",
                "decision": "",
                "answer_cardinality": "",
                "expected_behavior": "",
                "interpretation": "",
                "constraint_checklist": "",
                "evidence_calibration": "",
                "language_quality": "",
                "rationale": f"Current status: {quality.get('status', 'missing')}. Review independently; do not accept solely because the record parses.",
            })
    print(f"Exported {len(records)} records to {output}. Review decisions are blank by design.")
    return 0


def validate_log(input_path: str, output_path: str | None) -> int:
    path = Path(input_path)
    try:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            headers = set(reader.fieldnames or [])
            missing_headers = set(FIELDS) - headers
            if missing_headers:
                print(f"missing columns: {sorted(missing_headers)}", file=sys.stderr)
                return 1
            rows = list(reader)
    except OSError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    errors: list[str] = []
    seen: set[str] = set()
    decisions: dict[str, int] = {}
    for row_number, row in enumerate(rows, 2):
        identifier = (row.get("id") or "").strip()
        if not identifier:
            errors.append(f"row {row_number}: id is required")
        elif identifier in seen:
            errors.append(f"row {row_number}: duplicate review id {identifier}")
        seen.add(identifier)
        for field in ("reviewer", "review_date", "decision", "rationale", "interpretation",
                      "answer_cardinality", "expected_behavior", "constraint_checklist",
                      "evidence_calibration", "language_quality"):
            if not (row.get(field) or "").strip():
                errors.append(f"row {row_number}: {field} is required for a completed review")
        decision = (row.get("decision") or "").strip()
        if decision and decision not in DECISIONS:
            errors.append(f"row {row_number}: decision must be one of {sorted(DECISIONS)}")
        elif decision:
            decisions[decision] = decisions.get(decision, 0) + 1
        cardinality = (row.get("answer_cardinality") or "").strip()
        if cardinality and cardinality not in CARDINALITIES:
            errors.append(f"row {row_number}: answer_cardinality must be one of {sorted(CARDINALITIES)}")
        behavior = (row.get("expected_behavior") or "").strip()
        if behavior and behavior not in BEHAVIORS:
            errors.append(f"row {row_number}: expected_behavior must be one of {sorted(BEHAVIORS)}")
        review_date = (row.get("review_date") or "").strip()
        if review_date:
            try:
                date.fromisoformat(review_date)
            except ValueError:
                errors.append(f"row {row_number}: review_date must use YYYY-MM-DD")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    summary = [
        "# Human Review Log Summary", "",
        f"- Reviewed rows: {len(rows)}",
        f"- Accept: {decisions.get('accept', 0)}",
        f"- Revise: {decisions.get('revise', 0)}",
        f"- Retire: {decisions.get('retire', 0)}", "",
        "This summary validates completed review metadata only; it does not verify reviewer competence or prove semantic correctness.",
    ]
    content = "\n".join(summary) + "\n"
    if output_path:
        Path(output_path).write_text(content, encoding="utf-8")
    else:
        print(content)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    export_parser = subparsers.add_parser("export", help="export records into a human-review CSV")
    export_parser.add_argument("files", nargs="+")
    export_parser.add_argument("--output", required=True)
    validate_parser = subparsers.add_parser("validate", help="validate a completed review CSV")
    validate_parser.add_argument("review_csv")
    validate_parser.add_argument("--output", help="write a Markdown summary")
    args = parser.parse_args(argv)
    if args.command == "export":
        return export_queue(args.files, args.output)
    return validate_log(args.review_csv, args.output)


if __name__ == "__main__":
    raise SystemExit(main())
