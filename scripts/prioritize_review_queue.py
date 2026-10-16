#!/usr/bin/env python3
"""Prioritize dataset records needing human review or stronger evidence.

This tool only reads JSONL and review CSV inputs. It never edits records or
changes quality.status. Priority is a workflow heuristic, not a correctness
judgment.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

FIELDS = (
    "priority", "reason", "id", "source_file", "split", "task_type",
    "language", "quality_status", "review_decision", "reviewer",
    "evidence_kind", "evidence_reference", "verification_result",
)


def read_records(paths: list[str]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
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
                errors.append(f"{path}:{line_number}: expected JSON object")
                continue
            identifier = item.get("id")
            if not isinstance(identifier, str) or not identifier:
                errors.append(f"{path}:{line_number}: missing id")
                continue
            if identifier in seen:
                errors.append(f"{path}:{line_number}: duplicate id {identifier}")
                continue
            seen.add(identifier)
            item["_source_file"] = filename
            records.append(item)
    if errors:
        raise ValueError("\n".join(errors))
    return records


def read_reviews(path: str | None) -> dict[str, dict[str, str]]:
    if not path:
        return {}
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if "id" not in (reader.fieldnames or []):
            raise ValueError("review CSV must include an id column")
        reviews: dict[str, dict[str, str]] = {}
        for line_number, row in enumerate(reader, 2):
            identifier = (row.get("id") or "").strip()
            if not identifier:
                continue
            if identifier in reviews:
                raise ValueError(f"review CSV row {line_number}: duplicate id {identifier}")
            reviews[identifier] = row
        return reviews


def prioritize(records: list[dict[str, Any]], reviews: dict[str, dict[str, str]]) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    for record in records:
        identifier = record["id"]
        quality = record.get("quality") if isinstance(record.get("quality"), dict) else {}
        review = reviews.get(identifier, {})
        status = str(quality.get("status", "unknown"))
        decision = (review.get("decision") or "").strip()
        reviewer = (review.get("reviewer") or "").strip()
        evidence_kind = (review.get("evidence_kind") or "").strip()
        evidence_reference = (review.get("evidence_reference") or "").strip()
        verification = (review.get("verification_result") or "").strip()
        reasons: list[str] = []

        if decision not in {"accept", "revise", "retire"}:
            priority = "P0"
            reasons.append("human_review_missing")
        elif decision in {"revise", "retire"}:
            priority = "P0"
            reasons.append(f"review_decision_{decision}")
        elif not reviewer:
            priority = "P0"
            reasons.append("reviewer_missing")
        elif verification == "failed":
            priority = "P0"
            reasons.append("verification_failed")
        else:
            priority = "P3"

        if decision == "accept" and (not evidence_kind or not evidence_reference):
            priority = min(priority, "P1")
            reasons.append("evidence_metadata_incomplete")
        if decision == "accept" and verification in {"", "not_run"}:
            priority = min(priority, "P1")
            reasons.append("verification_not_run")
        if status == "draft":
            if priority > "P1":
                priority = "P1"
            reasons.append("quality_status_draft")
        elif status == "unknown":
            priority = min(priority, "P1")
            reasons.append("quality_status_unknown")
        if status == "verified" and (decision != "accept" or verification == "failed"):
            priority = "P0"
            reasons.append("status_review_consistency_check")
        if status == "reviewed" and decision != "accept":
            priority = min(priority, "P1")
            reasons.append("review_status_consistency_check")
        if (
            status == "reviewed" and decision == "accept" and reviewer
            and evidence_kind and evidence_reference
            and verification in {"passed", "not_applicable"}
            and priority == "P3"
        ):
            priority = "P2"
        if (
            status == "verified" and decision == "accept" and reviewer
            and evidence_kind and evidence_reference and verification == "passed"
            and priority == "P3"
        ):
            reasons.append("recorded_verification_evidence_present")

        output.append({
            "priority": priority,
            "reason": ";".join(dict.fromkeys(reasons)) or "review_recorded_evidence_present",
            "id": identifier,
            "source_file": str(record.get("_source_file", "")),
            "split": str(record.get("split", "")),
            "task_type": str(record.get("task_type", "")),
            "language": str(record.get("language", "")),
            "quality_status": status,
            "review_decision": decision,
            "reviewer": reviewer,
            "evidence_kind": evidence_kind,
            "evidence_reference": evidence_reference,
            "verification_result": verification,
        })
    order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    return sorted(output, key=lambda row: (order[row["priority"]], row["split"] == "eval", row["id"]))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", help="JSONL dataset files")
    parser.add_argument("--review-csv", help="optional CSV exported by review_dataset.py")
    parser.add_argument("--output", required=True, help="output CSV path")
    args = parser.parse_args(argv)
    try:
        records = read_records(args.inputs)
        reviews = read_reviews(args.review_csv)
        rows = prioritize(records, reviews)
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        counts = Counter(row["priority"] for row in rows)
        print(f"Records prioritized: {len(rows)}")
        for priority in ("P0", "P1", "P2", "P3"):
            print(f"{priority}: {counts[priority]}")
        print(f"Output: {output}")
        print("Priority is a workflow heuristic; no record or quality status was changed.")
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
