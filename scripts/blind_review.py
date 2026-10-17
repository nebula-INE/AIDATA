#!/usr/bin/env python3
"""Create anonymized review CSVs and restore model metadata after scoring.

The manifest contains model identities and must be kept away from reviewers.
This reduces direct identity bias but cannot prevent inference from response style.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

IDENTITY_FIELDS = (
    "model", "model_version", "prompt_template_version",
    "decoding_settings", "run_date",
)
MANIFEST_VERSION = 1


def read_csv(path: str) -> tuple[list[str], list[dict[str, str]]]:
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, strict=True)
        if not reader.fieldnames:
            raise ValueError("CSV header row is missing")
        if len(set(reader.fieldnames)) != len(reader.fieldnames):
            raise ValueError("duplicate CSV headers")
        rows = list(reader)
        if any(None in row or any(value is None for value in row.values()) for row in rows):
            raise ValueError("CSV contains a row with the wrong number of fields")
        return reader.fieldnames, rows


def write_csv(path: str, fields: list[str], rows: list[dict[str, str]]) -> None:
    with Path(path).open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)


def blind(input_path: str, output_path: str, manifest_path: str) -> int:
    try:
        fields, rows = read_csv(input_path)
        if "model" not in fields:
            raise ValueError("input CSV must include a 'model' column")
        missing = [field for field in IDENTITY_FIELDS if field not in fields]
        # Older worksheets may omit optional run metadata; add it so restoration
        # has a stable, explicit contract and does not infer values later.
        fields.extend(field for field in missing if field != "model")
        identities: dict[tuple[str, ...], str] = {}
        mapping: dict[str, dict[str, str]] = {}
        blind_rows: list[dict[str, str]] = []
        for row_number, row in enumerate(rows, 2):
            model = row.get("model", "").strip()
            if not model:
                raise ValueError(f"row {row_number}: model identity is blank")
            identity = tuple(row.get(field, "").strip() for field in IDENTITY_FIELDS)
            if identity not in identities:
                label = f"model-{len(identities) + 1:03d}"
                identities[identity] = label
                mapping[label] = dict(zip(IDENTITY_FIELDS, identity))
            label = identities[identity]
            item = {field: row.get(field, "") for field in fields}
            item["model"] = label
            for field in IDENTITY_FIELDS[1:]:
                item[field] = ""
            blind_rows.append(item)
        write_csv(output_path, fields, blind_rows)
        Path(manifest_path).write_text(
            json.dumps({"manifest_version": MANIFEST_VERSION, "models": mapping},
                       ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except (OSError, csv.Error, ValueError, json.JSONDecodeError) as exc:
        print(f"blind review failed: {exc}", file=sys.stderr)
        return 1
    print(f"Created anonymized worksheet with {len(rows)} rows and {len(mapping)} model/run labels.")
    print("Keep the manifest private until scoring is complete.")
    return 0


def restore(input_path: str, manifest_path: str, output_path: str) -> int:
    try:
        fields, rows = read_csv(input_path)
        if "model" not in fields:
            raise ValueError("scored CSV must include a 'model' column")
        manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
        if not isinstance(manifest, dict) or manifest.get("manifest_version") != MANIFEST_VERSION:
            raise ValueError("unsupported or invalid manifest version")
        models = manifest.get("models")
        if not isinstance(models, dict) or not models:
            raise ValueError("manifest must contain a non-empty 'models' mapping")
        for label, identity in models.items():
            if not isinstance(label, str) or not isinstance(identity, dict):
                raise ValueError("manifest model entries must map labels to objects")
            if any(not isinstance(identity.get(field, ""), str) for field in IDENTITY_FIELDS):
                raise ValueError(f"manifest identity fields must be strings for {label!r}")
        for field in IDENTITY_FIELDS[1:]:
            if field not in fields:
                fields.append(field)
        for row_number, row in enumerate(rows, 2):
            label = row.get("model", "")
            identity = models.get(label)
            if identity is None:
                raise ValueError(f"row {row_number}: unknown blind label {label!r}")
            for field in IDENTITY_FIELDS:
                row[field] = identity.get(field, "")
        write_csv(output_path, fields, rows)
    except (OSError, csv.Error, ValueError, json.JSONDecodeError) as exc:
        print(f"restore failed: {exc}", file=sys.stderr)
        return 1
    print(f"Restored model/run metadata for {len(rows)} scored rows.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    blind_parser = commands.add_parser("blind", help="anonymize a review worksheet")
    blind_parser.add_argument("input")
    blind_parser.add_argument("--output", required=True)
    blind_parser.add_argument("--manifest", required=True)
    restore_parser = commands.add_parser("restore", help="restore metadata after reviewers finish scoring")
    restore_parser.add_argument("input")
    restore_parser.add_argument("--manifest", required=True)
    restore_parser.add_argument("--output", required=True)
    args = parser.parse_args()
    if args.command == "blind":
        return blind(args.input, args.output, args.manifest)
    return restore(args.input, args.manifest, args.output)


if __name__ == "__main__":
    raise SystemExit(main())
