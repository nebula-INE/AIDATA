#!/usr/bin/env python3
"""Summarize human review coverage and fixed-fixture evidence without promoting data."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

REVIEW_FIELDS = {
    "id", "reviewer", "decision", "evidence_kind", "evidence_reference",
    "verification_commit", "verification_result",
}
FIXTURE_STATUSES = {"passed", "failed", "timeout"}
COMPLETED_DECISIONS = {"accept", "revise", "retire"}


def load_review_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = REVIEW_FIELDS - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"review CSV missing columns: {sorted(missing)}")
        rows = list(reader)
    seen: set[str] = set()
    for number, row in enumerate(rows, 2):
        identifier = (row.get("id") or "").strip()
        if not identifier:
            raise ValueError(f"review CSV row {number}: id is required")
        if identifier in seen:
            raise ValueError(f"review CSV row {number}: duplicate id {identifier}")
        seen.add(identifier)
    return rows


def load_dataset_records(paths: list[Path], *, include_eval: bool = False) -> list[dict[str, str]]:
    """Load dataset IDs/splits, checking all rows before optional eval filtering."""
    records: list[dict[str, str]] = []
    seen: set[str] = set()
    errors: list[str] = []
    for path in paths:
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
            identifier = item.get("id")
            if not isinstance(identifier, str) or not identifier.strip():
                errors.append(f"{path}:{line_number}: missing/invalid id")
                continue
            if identifier in seen:
                errors.append(f"{path}:{line_number}: duplicate dataset id {identifier}")
                continue
            seen.add(identifier)
            split = item.get("split", "")
            if not isinstance(split, str):
                errors.append(f"{path}:{line_number}: split must be a string")
                continue
            if include_eval or split != "eval":
                records.append({"id": identifier, "split": split or "unspecified"})
    if errors:
        raise ValueError("\n".join(errors))
    return records


def load_fixture_report(path: Path) -> dict[str, Any]:
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read fixture report {path}: {exc}") from exc
    if not isinstance(report, dict) or not isinstance(report.get("results"), list):
        raise ValueError("fixture report must be an object containing a results array")
    for index, result in enumerate(report["results"]):
        if not isinstance(result, dict):
            raise ValueError(f"fixture report result {index} must be an object")
        if result.get("status") not in FIXTURE_STATUSES:
            raise ValueError(f"fixture report result {index} has unsupported status")
        if not isinstance(result.get("fixture_id"), str) or not result["fixture_id"]:
            raise ValueError(f"fixture report result {index} has no fixture_id")
    return report


def build_summary(
    rows: list[dict[str, str]],
    report: dict[str, Any] | None = None,
    dataset_records: list[dict[str, str]] | None = None,
) -> str:
    decisions = Counter((row.get("decision") or "").strip() or "pending" for row in rows)
    evidence = Counter((row.get("evidence_kind") or "").strip() or "unspecified" for row in rows)
    verification = Counter((row.get("verification_result") or "").strip() or "unspecified" for row in rows)
    known_decisions = COMPLETED_DECISIONS | {"pending"}
    invalid_decisions = {
        decision: count for decision, count in decisions.items()
        if decision not in known_decisions
    }
    lines = [
        "# Review and Evidence Coverage", "",
        f"- Review rows: {len(rows)}",
        f"- Completed decisions: {sum(decisions[key] for key in COMPLETED_DECISIONS)}",
        f"- Pending decisions: {decisions['pending']}",
        f"- Invalid/unrecognized decisions: {sum(invalid_decisions.values())}", "",
        "## Decisions", "",
    ]
    for key in ("accept", "revise", "retire", "pending"):
        lines.append(f"- {key}: {decisions[key]}")
    if invalid_decisions:
        lines.extend(["", "### Unrecognized decision values", ""])
        for decision, count in sorted(invalid_decisions.items()):
            lines.append(f"- {decision}: {count}")
    lines.extend(["", "## Evidence kinds", ""])
    for key, count in sorted(evidence.items()):
        lines.append(f"- {key}: {count}")
    lines.extend(["", "## Recorded verification results", ""])
    for key, count in sorted(verification.items()):
        lines.append(f"- {key}: {count}")

    if dataset_records is not None:
        dataset_ids = {record["id"] for record in dataset_records}
        rows_by_id = { (row.get("id") or "").strip(): row for row in rows }
        completed_ids = {
            identifier for identifier, row in rows_by_id.items()
            if (row.get("decision") or "").strip() in COMPLETED_DECISIONS
        }
        matched_ids = dataset_ids & set(rows_by_id)
        unknown_ids = set(rows_by_id) - dataset_ids
        unreviewed_ids = dataset_ids - completed_ids
        split_counts = Counter(record["split"] for record in dataset_records)
        reviewed_split_counts = Counter(
            record["split"] for record in dataset_records if record["id"] in completed_ids
        )
        lines.extend([
            "", "## Dataset review coverage", "",
            f"- Dataset records in scope: {len(dataset_records)}",
            f"- Dataset records with a review CSV row: {len(matched_ids)}",
            f"- Dataset records with a completed decision: {len(dataset_ids & completed_ids)}",
            f"- Dataset records still without a completed decision: {len(unreviewed_ids)}",
            f"- Review CSV IDs absent from the dataset inputs: {len(unknown_ids)}",
            "", "### Coverage by split", "",
        ])
        for split in sorted(split_counts):
            lines.append(
                f"- {split}: {reviewed_split_counts[split]}/{split_counts[split]} "
                "records have completed decisions"
            )
        if unknown_ids:
            lines.extend(["", "### Unknown review IDs", ""])
            lines.extend(f"- {identifier}" for identifier in sorted(unknown_ids))
        lines.extend([
            "",
            "Coverage counts treat accept/revise/retire as completed decisions; a row alone is not a completed review. Dataset IDs are validated before eval filtering. Eval records are excluded by default unless --include-eval is used.",
        ])

    if report is not None:
        results = report["results"]
        fixture_counts = Counter(result["status"] for result in results)
        lines.extend([
            "", "## Fixed-fixture report", "",
            f"- Report runner: {report.get('runner', 'unspecified')}",
            f"- Fixture results: {len(results)}",
        ])
        for key in ("passed", "failed", "timeout"):
            lines.append(f"- {key}: {fixture_counts[key]}")
        lines.extend([
            "",
            "Fixture report counts are shown separately from review-row counts. This tool does not infer that a fixture validates a particular dataset record, authenticate evidence references, or change any quality.status field.",
        ])
    else:
        lines.extend([
            "",
            "No fixed-fixture report supplied. Review-row evidence metadata is counted as recorded, not authenticated.",
        ])
    lines.extend([
        "",
        "This report measures workflow coverage only. It does not establish semantic correctness, reviewer competence, or model capability.",
        "",
    ])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("review_csv", type=Path)
    parser.add_argument("--fixture-report", type=Path)
    parser.add_argument(
        "--dataset", nargs="+", type=Path,
        help="JSONL dataset inputs to compare against the review CSV (eval excluded by default)",
    )
    parser.add_argument(
        "--include-eval", action="store_true",
        help="include split: eval records when --dataset is supplied",
    )
    parser.add_argument("--output", type=Path, help="write Markdown report (default: stdout)")
    args = parser.parse_args(argv)
    if args.include_eval and not args.dataset:
        parser.error("--include-eval requires --dataset")
    try:
        rows = load_review_rows(args.review_csv)
        fixture_report = load_fixture_report(args.fixture_report) if args.fixture_report else None
        dataset_records = (
            load_dataset_records(args.dataset, include_eval=args.include_eval)
            if args.dataset else None
        )
        content = build_summary(rows, fixture_report, dataset_records)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(content, encoding="utf-8")
        else:
            print(content, end="")
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
