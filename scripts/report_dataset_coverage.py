#!/usr/bin/env python3
"""Summarize AIDATA dataset coverage without reading prompt or target text.

Usage:
  python scripts/report_dataset_coverage.py data/seeds/*.jsonl data/eval/*.jsonl
  python scripts/report_dataset_coverage.py --json report.json data/seeds/*.jsonl
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


def read_records(paths: list[str]) -> tuple[list[dict[str, Any]], list[str]]:
    records: list[dict[str, Any]] = []
    errors: list[str] = []
    for name in paths:
        path = Path(name)
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            errors.append(f"{path}: {exc}")
            continue
        for number, line in enumerate(lines, 1):
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"{path}:{number}: invalid JSON: {exc}")
                continue
            if not isinstance(record, dict):
                errors.append(f"{path}:{number}: record is not a JSON object")
                continue
            record["_source_file"] = str(path)
            records.append(record)
    return records, errors


def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    count = len(records)
    by_language = Counter(str(r.get("language", "missing")) for r in records)
    by_split = Counter(str(r.get("split", "missing")) for r in records)
    by_task = Counter(str(r.get("task_type", "missing")) for r in records)
    by_status = Counter(str((r.get("quality") or {}).get("status", "missing")) for r in records)
    by_tag = Counter(tag for r in records for tag in r.get("tags", []) if isinstance(tag, str))
    ids = Counter(str(r.get("id", "")) for r in records)
    duplicate_ids = sorted(identifier for identifier, n in ids.items() if identifier and n > 1)
    review_candidates = [
        {"id": r.get("id", ""), "language": r.get("language", ""),
         "task_type": r.get("task_type", ""), "file": r.get("_source_file", ""),
         "quality_status": (r.get("quality") or {}).get("status", "missing")}
        for r in records if (r.get("quality") or {}).get("status") == "draft"
    ]
    eval_records = [r for r in records if r.get("split") == "eval"]
    overlap = sorted(
        str(r.get("id", "")) for r in records
        if r.get("split") in {"train", "validation"} and r.get("id") in {e.get("id") for e in eval_records}
    )
    return {
        "record_count": count,
        "language_counts": dict(sorted(by_language.items())),
        "split_counts": dict(sorted(by_split.items())),
        "task_type_counts": dict(sorted(by_task.items())),
        "quality_status_counts": dict(sorted(by_status.items())),
        "top_tags": dict(by_tag.most_common(30)),
        "duplicate_ids": duplicate_ids,
        "train_validation_eval_id_overlap": overlap,
        "draft_review_queue_count": len(review_candidates),
        "draft_review_queue": review_candidates,
        "note": "Coverage counts describe dataset composition, not semantic quality or model performance."
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", help="JSONL files to summarize")
    parser.add_argument("--json", dest="json_path", help="also write machine-readable JSON report")
    args = parser.parse_args(argv)
    records, errors = read_records(args.files)
    for error in errors:
        print(error, file=sys.stderr)
    report = summarize(records)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.json_path:
        Path(args.json_path).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 1 if errors or report["duplicate_ids"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
