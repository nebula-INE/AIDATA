#!/usr/bin/env python3
"""Report exact and near-duplicate prompts in AIDATA JSONL files.

This tool is deliberately advisory by default: similarity is a review signal,
not proof that two examples are redundant. It never executes dataset content.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


def normalize(text: str) -> str:
    """Lowercase text and collapse punctuation/whitespace for exact comparison."""
    return " ".join(re.findall(r"[a-z0-9]+|[^\W\d_]+", text.casefold()))


def token_set(text: str) -> set[str]:
    return set(normalize(text).split())


def jaccard(left: set[str], right: set[str]) -> float:
    union = left | right
    return len(left & right) / len(union) if union else 1.0


def load_records(paths: list[str]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for filename in paths:
        path = Path(filename)
        with path.open(encoding="utf-8") as stream:
            for line_number, line in enumerate(stream, 1):
                if not line.strip() or line.lstrip().startswith("#"):
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as exc:
                    print(f"{path}:{line_number}: invalid JSON: {exc}", file=sys.stderr)
                    continue
                if isinstance(record, dict) and isinstance(record.get("prompt"), str):
                    records.append({
                        "id": str(record.get("id", f"{path}:{line_number}")),
                        "file": str(path),
                        "line": line_number,
                        "prompt": record["prompt"],
                    })
    return records


def find_duplicates(
    records: list[dict[str, Any]], threshold: float = 0.82
) -> tuple[list[tuple[dict[str, Any], dict[str, Any]]],
           list[tuple[dict[str, Any], dict[str, Any], float]]]:
    exact_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        key = normalize(record["prompt"])
        if key:
            exact_groups[key].append(record)

    exact_pairs: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for group in exact_groups.values():
        for index, first in enumerate(group):
            for second in group[index + 1:]:
                exact_pairs.append((first, second))

    near_pairs: list[tuple[dict[str, Any], dict[str, Any], float]] = []
    tokenized = [(record, token_set(record["prompt"])) for record in records]
    for index, (first, first_tokens) in enumerate(tokenized):
        # Very short prompts have unstable similarity scores; exact matches above
        # are still reported, but short prompts are omitted from near-match checks.
        if len(first_tokens) < 5:
            continue
        for second, second_tokens in tokenized[index + 1:]:
            if len(second_tokens) < 5 or first["id"] == second["id"]:
                continue
            score = jaccard(first_tokens, second_tokens)
            if threshold <= score < 1.0:
                near_pairs.append((first, second, score))
    return exact_pairs, near_pairs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", help="JSONL files to inspect")
    parser.add_argument("--threshold", type=float, default=0.82,
                        help="Jaccard threshold for near-duplicate prompts (default: 0.82)")
    parser.add_argument("--fail-on-exact", action="store_true",
                        help="return non-zero when normalized exact duplicates are found")
    args = parser.parse_args(argv)
    if not 0.0 < args.threshold <= 1.0:
        parser.error("--threshold must be in (0, 1]")

    records = load_records(args.files)
    exact, near = find_duplicates(records, args.threshold)
    print(f"Scanned {len(records)} prompt(s).")
    if exact:
        print(f"\nExact normalized prompt duplicates: {len(exact)}")
        for first, second in exact:
            print(f"  {first['id']} ({first['file']}:{first['line']}) == "
                  f"{second['id']} ({second['file']}:{second['line']})")
    else:
        print("Exact normalized prompt duplicates: 0")

    if near:
        print(f"\nNear-duplicate candidates (threshold={args.threshold:.2f}): {len(near)}")
        for first, second, score in sorted(near, key=lambda item: item[2], reverse=True):
            print(f"  {score:.3f}  {first['id']} <-> {second['id']}")
    else:
        print("Near-duplicate candidates: 0")
    print("Review candidates manually; similarity alone does not establish redundancy.")
    return 1 if args.fail_on_exact and exact else 0


if __name__ == "__main__":
    raise SystemExit(main())
