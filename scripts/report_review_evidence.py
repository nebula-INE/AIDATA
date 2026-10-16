#!/usr/bin/env python3
"""Summarize review completion and fixed-fixture evidence without promoting data."""
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


def build_summary(rows: list[dict[str, str]], report: dict[str, Any] | None = None) -> str:
    decisions = Counter((row.get("decision") or "").strip() or "pending" for row in rows)
    evidence = Counter((row.get("evidence_kind") or "").strip() or "unspecified" for row in rows)
    verification = Counter((row.get("verification_result") or "").strip() or "unspecified" for row in rows)
    lines = [
        "# Review and Evidence Coverage",
        "",
        f"- Review rows: {len(rows)}",
        f"- Completed decisions: {sum(decisions[key] for key in ('accept', 'revise', 'retire'))}",
        f"- Pending decisions: {decisions['pending']}",
        "",
        "## Decisions",
        "",
    ]
    for key in ("accept", "revise", "retire", "pending"):
        lines.append(f"- {key}: {decisions[key]}")
    lines.extend(["", "## Evidence kinds", ""])
    for key, count in sorted(evidence.items()):
        lines.append(f"- {key}: {count}")
    lines.extend(["", "## Recorded verification results", ""])
    for key, count in sorted(verification.items()):
        lines.append(f"- {key}: {count}")
    if report is not None:
        results = report["results"]
        fixture_counts = Counter(result["status"] for result in results)
        lines.extend([
            "", "## Fixed-fixture report",
            "",
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
    parser.add_argument("--output", type=Path, help="write Markdown report (default: stdout)")
    args = parser.parse_args(argv)
    try:
        rows = load_review_rows(args.review_csv)
        fixture_report = load_fixture_report(args.fixture_report) if args.fixture_report else None
        content = build_summary(rows, fixture_report)
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
