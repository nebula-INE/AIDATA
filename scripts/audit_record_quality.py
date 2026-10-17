#!/usr/bin/env python3
"""Advisory content-quality audit for JSONL dataset records; never executes data."""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

GENERIC_TESTS = (
    "review expected behavior against the stated assumptions",
    "not independently human-reviewed",
    "synthetic record as verified",
    "check factual correctness",
)
LITERAL_NEWLINE = re.compile(r"\\n")


def inspect(paths: list[str]) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    seen_ids: dict[str, tuple[str, int]] = {}
    prompt_groups: dict[str, list[tuple[str, int, str]]] = defaultdict(list)
    count = 0
    for filename in paths:
        path = Path(filename)
        try:
            stream = path.open(encoding="utf-8")
        except OSError as exc:
            findings.append({"kind": "file_error", "file": filename, "detail": str(exc)})
            continue
        with stream:
            for line_no, line in enumerate(stream, 1):
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as exc:
                    findings.append({"kind": "invalid_json", "file": filename, "line": line_no, "detail": str(exc)})
                    continue
                if not isinstance(record, dict):
                    findings.append({"kind": "non_object_record", "file": filename, "line": line_no})
                    continue
                count += 1
                rid = str(record.get("id", "")).strip()
                if not rid:
                    findings.append({"kind": "missing_id", "file": filename, "line": line_no})
                elif rid in seen_ids:
                    old_file, old_line = seen_ids[rid]
                    findings.append({"kind": "duplicate_id", "id": rid, "file": filename, "line": line_no,
                                     "also_at": f"{old_file}:{old_line}"})
                else:
                    seen_ids[rid] = (filename, line_no)
                prompt = record.get("prompt", "")
                target = record.get("target", "")
                if isinstance(prompt, str):
                    normalized = " ".join(prompt.casefold().split())
                    if normalized:
                        prompt_groups[normalized].append((filename, line_no, rid))
                    if LITERAL_NEWLINE.search(prompt):
                        findings.append({"kind": "literal_backslash_n_in_prompt", "id": rid,
                                         "file": filename, "line": line_no})
                if not isinstance(target, str) or not target.strip():
                    findings.append({"kind": "missing_target", "id": rid, "file": filename, "line": line_no})
                tests = record.get("tests", [])
                if not isinstance(tests, list) or not tests:
                    findings.append({"kind": "no_tests_or_checks", "id": rid, "file": filename, "line": line_no})
                elif any(isinstance(item, str) and any(marker in item.casefold() for marker in GENERIC_TESTS)
                         for item in tests):
                    findings.append({"kind": "generic_test_placeholder", "id": rid,
                                     "file": filename, "line": line_no})
                quality = record.get("quality")
                if isinstance(quality, dict) and quality.get("status") == "reviewed" and not quality.get("reviewer"):
                    findings.append({"kind": "reviewed_without_reviewer", "id": rid,
                                     "file": filename, "line": line_no})
    for group in prompt_groups.values():
        if len(group) > 1:
            for filename, line_no, rid in group[1:]:
                first = group[0]
                findings.append({"kind": "exact_prompt_duplicate", "id": rid, "file": filename, "line": line_no,
                                 "also_at": f"{first[0]}:{first[1]}", "also_id": first[2]})
    return {"records_scanned": count, "findings": findings}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", help="JSONL files to inspect")
    parser.add_argument("--fail-on", action="append", default=[],
                        help="finding kind that should return exit code 1; repeatable (default: advisory only)")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args()
    report = inspect(args.files)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"Scanned {report['records_scanned']} record(s); {len(report['findings'])} finding(s).")
        counts: dict[str, int] = defaultdict(int)
        for item in report["findings"]:
            counts[item["kind"]] += 1
        for kind, total in sorted(counts.items()):
            print(f"  {kind}: {total}")
        for item in report["findings"]:
            where = f"{item.get('file', '?')}:{item.get('line', '?')}"
            print(f"  [{item['kind']}] {where} id={item.get('id', '-')}"
                  + (f" also_at={item['also_at']}" if item.get("also_at") else ""))
    return 1 if any(item["kind"] in args.fail_on for item in report["findings"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
