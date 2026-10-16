#!/usr/bin/env python3
"""Run only repository-owned, allowlisted test suites.

This tool never executes code, shell commands, paths, or test selectors from a
dataset record. It is a verification helper, not a security sandbox: only use
it in a disposable environment for trusted repository test code.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

# These patterns are maintained in source control. User input can only choose
# one of these keys; it cannot supply a path or arbitrary unittest selector.
FIXTURES: dict[str, str] = {
    "dataset-validator": "test_validate_dataset.py",
    "duplicate-audit": "test_audit_dataset.py",
    "eval-leakage": "test_check_eval_leakage.py",
    "coverage-report": "test_report_dataset_coverage.py",
    "review-workflow": "test_review_dataset.py",
    "response-evaluation": "test_evaluate_responses.py",
}


def build_command(fixture_id: str) -> list[str]:
    """Return a command only for a fixed, repository-owned test fixture."""
    try:
        pattern = FIXTURES[fixture_id]
    except KeyError as exc:
        raise ValueError(f"unknown fixture id: {fixture_id}") from exc
    return [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", pattern, "-v"]


def classify_returncode(returncode: int) -> str:
    return "passed" if returncode == 0 else "failed"


def run_fixture(fixture_id: str, timeout_seconds: int) -> dict[str, Any]:
    command = build_command(fixture_id)
    started = time.monotonic()
    # Avoid leaking most ambient configuration/secrets to child test processes.
    # Keep only variables needed to locate the runtime and basic platform paths.
    env = {
        key: value for key, value in os.environ.items()
        if key in {"PATH", "SYSTEMROOT", "WINDIR", "TMP", "TEMP", "TMPDIR"}
    }
    env["PYTHONIOENCODING"] = "utf-8"
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
            check=False,
        )
        return {
            "fixture_id": fixture_id,
            "status": classify_returncode(completed.returncode),
            "exit_code": completed.returncode,
            "timed_out": False,
            "duration_seconds": round(time.monotonic() - started, 3),
            "command": command,
            "output": completed.stdout,
        }
    except subprocess.TimeoutExpired as exc:
        output = exc.stdout or ""
        if isinstance(output, bytes):
            output = output.decode("utf-8", errors="replace")
        return {
            "fixture_id": fixture_id,
            "status": "timeout",
            "exit_code": None,
            "timed_out": True,
            "duration_seconds": round(time.monotonic() - started, 3),
            "command": command,
            "output": output,
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true", help="List available fixed fixture IDs")
    parser.add_argument("--fixture", action="append", choices=sorted(FIXTURES),
                        help="Allowlisted fixture ID; may be repeated")
    parser.add_argument("--timeout", type=int, default=60,
                        help="Per-fixture timeout in seconds (1-600; default: 60)")
    parser.add_argument("--report", type=Path, help="Write a JSON report to this path")
    args = parser.parse_args(argv)

    if args.list:
        print("\n".join(sorted(FIXTURES)))
        return 0
    if not args.fixture:
        parser.error("provide --fixture or --list")
    if not 1 <= args.timeout <= 600:
        parser.error("--timeout must be between 1 and 600 seconds")

    results = [run_fixture(fixture_id, args.timeout) for fixture_id in args.fixture]
    report = {
        "schema_version": "1.0",
        "runner": "verify_fixed_fixtures.py",
        "execution_scope": "repository-owned allowlisted unittest suites only",
        "results": results,
        "summary": {
            "total": len(results),
            "passed": sum(result["status"] == "passed" for result in results),
            "failed": sum(result["status"] == "failed" for result in results),
            "timeout": sum(result["status"] == "timeout" for result in results),
        },
        "limitations": [
            "This is not an OS-level security sandbox.",
            "It does not execute dataset-provided code.",
            "A passing test suite does not promote dataset quality.status automatically.",
        ],
    }
    serialized = json.dumps(report, ensure_ascii=False, indent=2)
    print(serialized)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(serialized + "\n", encoding="utf-8")
    return 0 if all(result["status"] == "passed" for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
