#!/usr/bin/env python3
"""Audit normalized exact and near-duplicate prompts across train/eval splits.

Exact normalized prompt overlap is a hard failure by default. Near matches are
heuristic review candidates only; they do not prove semantic leakage.
"""
from __future__ import annotations

import argparse
import sys

try:
    from .audit_dataset import find_duplicates, load_records
except ImportError:  # Executed as a standalone script.
    from audit_dataset import find_duplicates, load_records


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train", nargs="+", required=True, help="Training JSONL files")
    parser.add_argument("--eval", nargs="+", required=True, help="Held-out evaluation JSONL files")
    parser.add_argument("--threshold", type=float, default=0.82,
                        help="Jaccard threshold for advisory near matches (default: 0.82)")
    parser.add_argument("--allow-exact", action="store_true",
                        help="Report exact overlap without failing (for investigation only)")
    args = parser.parse_args(argv)
    if not 0.0 < args.threshold <= 1.0:
        parser.error("--threshold must be in (0, 1]")

    train = load_records(args.train)
    evaluation = load_records(args.eval)
    if not train or not evaluation:
        print("Both train and eval inputs must contain readable prompt records.", file=sys.stderr)
        return 2

    for record in train:
        record["split"] = "train"
    for record in evaluation:
        record["split"] = "eval"

    exact, near = find_duplicates(train + evaluation, args.threshold)
    exact = [(a, b) for a, b in exact if a["split"] != b["split"]]
    near = [(a, b, score) for a, b, score in near if a["split"] != b["split"]]

    print(f"Train prompts: {len(train)}; eval prompts: {len(evaluation)}.")
    print(f"Cross-split exact normalized prompt overlaps: {len(exact)}")
    for a, b in exact:
        print(f"  {a['id']} ({a['file']}:{a['line']}) [{a['split']}] == "
              f"{b['id']} ({b['file']}:{b['line']}) [{b['split']}]")

    print(f"Cross-split near-duplicate candidates (threshold={args.threshold:.2f}): {len(near)}")
    for a, b, score in sorted(near, key=lambda item: item[2], reverse=True):
        print(f"  {score:.3f}  {a['id']} ({a['file']}:{a['line']}) [{a['split']}] <-> "
              f"{b['id']} ({b['file']}:{b['line']}) [{b['split']}]")
    print("Near matches are advisory only; manually review semantic similarity and answer leakage.")
    return 1 if exact and not args.allow_exact else 0


if __name__ == "__main__":
    raise SystemExit(main())
