#!/usr/bin/env python3
"""Prepare blind-review worksheets and summarize manually scored model evaluations.

Prediction JSONL format: one object per line with id, prediction, model, model_version,
prompt_template_version, decoding_settings, and run_date. The first three are required.
The evaluation answer key is joined locally and is never sent to the model by this script.

Usage:
  python scripts/evaluate_responses.py prepare data/eval/japanese_language_understanding_eval.jsonl predictions.jsonl --output review.csv
  python scripts/evaluate_responses.py summarize review.csv --output report.md
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

AXES = (
    "meaning",
    "constraints",
    "ambiguity_calibration",
    "evidence_discipline",
    "context_tracking",
    "language_quality",
)
SCORE_COLUMNS = tuple(f"score_{axis}" for axis in AXES)
REQUIRED_PREDICTION_FIELDS = {"id", "prediction", "model"}


def read_jsonl(path: str) -> tuple[list[dict[str, Any]], list[str]]:
    records: list[dict[str, Any]] = []
    errors: list[str] = []
    try:
        lines = Path(path).read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        return [], [f"{path}: {exc}"]
    for number, line in enumerate(lines, 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"{path}:{number}: invalid JSON: {exc}")
            continue
        if not isinstance(item, dict):
            errors.append(f"{path}:{number}: expected JSON object")
            continue
        records.append(item)
    return records, errors


def prepare(eval_path: str, predictions_path: str, output_path: str) -> int:
    evaluation, errors = read_jsonl(eval_path)
    predictions, prediction_errors = read_jsonl(predictions_path)
    errors.extend(prediction_errors)
    eval_by_id: dict[str, dict[str, Any]] = {}
    for item in evaluation:
        identifier = item.get("id")
        if not isinstance(identifier, str) or not identifier.strip():
            errors.append(f"evaluation item has invalid id: {identifier!r}")
            continue
        if identifier in eval_by_id:
            errors.append(f"duplicate evaluation id: {identifier}")
            continue

        # Validate optional display fields before CSV serialization. Dataset records
        # are external inputs here; malformed types must produce actionable errors,
        # not TypeError from join() or surprising character-by-character tags.
        item_valid = True
        for field in ("language", "task_type", "prompt", "target"):
            if field in item and not isinstance(item[field], str):
                errors.append(f"evaluation field {field!r} must be a string for id: {identifier}")
                item_valid = False
        tags = item.get("tags", [])
        if not isinstance(tags, list) or any(not isinstance(tag, str) for tag in tags):
            errors.append(f"evaluation field 'tags' must be a list of strings for id: {identifier}")
            item_valid = False
        if item_valid:
            eval_by_id[identifier] = item

    predictions_by_id: dict[str, dict[str, Any]] = {}
    for item in predictions:
        missing = REQUIRED_PREDICTION_FIELDS - item.keys()
        if missing:
            errors.append(f"prediction missing fields {sorted(missing)}: {item.get('id', '<no id>')}")
            continue
        identifier = item["id"]
        if not isinstance(identifier, str) or not identifier:
            errors.append(f"prediction has invalid id: {identifier!r}")
            continue
        if not isinstance(item["prediction"], str):
            errors.append(f"prediction must be a string for id: {identifier}")
            continue
        if not isinstance(item["model"], str) or not item["model"].strip():
            errors.append(f"model must be a non-empty string for id: {identifier}")
            continue
        if identifier not in eval_by_id:
            errors.append(f"prediction id not in evaluation set: {identifier}")
        if identifier in predictions_by_id:
            errors.append(f"duplicate prediction id: {identifier}")
        predictions_by_id[identifier] = item

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    missing_predictions = sorted(set(eval_by_id) - set(predictions_by_id))
    extra_predictions = sorted(set(predictions_by_id) - set(eval_by_id))
    if extra_predictions:
        print(f"unexpected prediction IDs: {extra_predictions}", file=sys.stderr)
        return 1

    columns = [
        "id", "language", "task_type", "tags", "model", "model_version",
        "prompt_template_version", "decoding_settings", "run_date", "reviewer",
        "prompt", "meaning_reference", "prediction", *SCORE_COLUMNS, "notes",
    ]
    with Path(output_path).open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for identifier, item in eval_by_id.items():
            pred = predictions_by_id.get(identifier, {})
            writer.writerow({
                "id": identifier,
                "language": item.get("language", ""),
                "task_type": item.get("task_type", ""),
                "tags": "|".join(item.get("tags", [])),
                "model": pred.get("model", ""),
                "model_version": pred.get("model_version", ""),
                "prompt_template_version": pred.get("prompt_template_version", ""),
                "decoding_settings": json.dumps(pred.get("decoding_settings", {}), ensure_ascii=False, sort_keys=True),
                "run_date": pred.get("run_date", ""),
                "reviewer": "",
                "prompt": item.get("prompt", ""),
                "meaning_reference": item.get("target", ""),
                "prediction": pred.get("prediction", ""),
                **{column: "" for column in SCORE_COLUMNS},
                "notes": "MISSING PREDICTION" if identifier in missing_predictions else "",
            })
    print(f"Prepared {len(eval_by_id)} evaluation rows; {len(missing_predictions)} predictions missing.")
    print("Review answer keys and rubric before scoring; these synthetic draft keys are not independently validated.")
    return 0


def parse_score(value: str) -> float | None:
    value = value.strip().upper()
    if value in {"", "NA", "N/A"}:
        return None
    try:
        score = float(value)
    except ValueError as exc:
        raise ValueError(f"invalid score {value!r}; use 0, 1, 2, or N/A") from exc
    if score not in {0.0, 1.0, 2.0}:
        raise ValueError(f"invalid score {value!r}; use 0, 1, 2, or N/A")
    return score


def summarize(input_path: str, output_path: str | None) -> int:
    try:
        with Path(input_path).open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle, strict=True)
            headers = reader.fieldnames
            if not headers:
                print("CSV header row is missing.", file=sys.stderr)
                return 1
            duplicate_headers = sorted({name for name in headers if headers.count(name) > 1})
            if duplicate_headers:
                print(f"duplicate CSV columns: {duplicate_headers}", file=sys.stderr)
                return 1
            required = {"id", "model", "language", "task_type", "tags", *SCORE_COLUMNS}
            missing_columns = required - set(headers)
            if missing_columns:
                print(f"missing columns: {sorted(missing_columns)}", file=sys.stderr)
                return 1
            rows = list(reader)
    except (OSError, csv.Error) as exc:
        print(f"could not read evaluation CSV: {exc}", file=sys.stderr)
        return 1
    if not rows:
        print("No scored rows found.", file=sys.stderr)
        return 1

    parsed: list[dict[str, Any]] = []
    errors: list[str] = []
    for row_number, row in enumerate(rows, 2):
        if None in row:
            errors.append(f"row {row_number}: too many CSV fields")
            continue
        missing_values = [name for name, value in row.items() if value is None]
        if missing_values:
            errors.append(f"row {row_number}: missing CSV fields for columns {missing_values}")
            continue
        identifier = row.get("id", "")
        if not identifier.strip():
            errors.append(f"row {row_number}: id must be non-empty")
        if not row.get("model", "").strip():
            errors.append(f"row {row_number}: model must be non-empty")
        values: dict[str, float | None] = {}
        for column in SCORE_COLUMNS:
            try:
                values[column] = parse_score(row.get(column, ""))
            except ValueError as exc:
                errors.append(f"row {row_number}, {column}: {exc}")
        parsed.append({**row, "_scores": values})
    # A repeated item/run/reviewer row silently overweights that item in aggregates.
    # Keep separate prompt/model/decoding runs and independent reviewers distinct.
    seen_review_rows: set[tuple[str, ...]] = set()
    for row_number, row in enumerate(parsed, 2):
        identity = tuple(row.get(field, "").strip() for field in (
            "id", "model", "model_version", "prompt_template_version",
            "decoding_settings", "run_date", "reviewer",
        ))
        if identity in seen_review_rows:
            errors.append(
                f"row {row_number}: duplicate item/run/reviewer row for id {row.get('id', '')!r}; "
                "do not count the same review twice"
            )
        seen_review_rows.add(identity)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    total_ratings = sum(
        value is not None
        for row in parsed
        for value in row["_scores"].values()
    )
    if total_ratings == 0:
        print("No scored ratings found; score at least one applicable axis before summarizing.", file=sys.stderr)
        return 1

    def group_summary(group: list[dict[str, Any]]) -> dict[str, Any]:
        all_scores = [score for row in group for score in row["_scores"].values() if score is not None]
        axis_stats = {}
        for axis in AXES:
            vals = [row["_scores"][f"score_{axis}"] for row in group if row["_scores"][f"score_{axis}"] is not None]
            axis_stats[axis] = {
                "mean": round(sum(vals) / len(vals), 3) if vals else None,
                "scored": len(vals),
                "max_possible": 2 * len(vals),
                "normalized_percent": round(sum(vals) / (2 * len(vals)) * 100, 2) if vals else None,
            }
        return {
            "items": len(group),
            "items_with_any_score": sum(any(v is not None for v in r["_scores"].values()) for r in group),
            "axis_scores": axis_stats,
            "overall_mean": round(sum(all_scores) / len(all_scores), 3) if all_scores else None,
            "overall_normalized_percent": round(sum(all_scores) / (2 * len(all_scores)) * 100, 2) if all_scores else None,
            "total_axis_ratings": len(all_scores),
            "possible_points_for_rated_axes": 2 * len(all_scores),
        }

    by_model: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_language: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_task: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_tag: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in parsed:
        model_label = row.get("model") or "(unspecified)"
        model_version = row.get("model_version", "").strip()
        run_date = row.get("run_date", "").strip()
        prompt_template = row.get("prompt_template_version", "").strip()
        decoding_settings = row.get("decoding_settings", "").strip()
        if model_version:
            model_label += f" ({model_version})"
        if prompt_template:
            model_label += f" [prompt={prompt_template}]"
        if decoding_settings and decoding_settings != "{}":
            model_label += f" [decoding={decoding_settings}]"
        if run_date:
            model_label += f" @ {run_date}"
        by_model[model_label].append(row)
        by_language[row.get("language") or "(unspecified)"].append(row)
        by_task[row.get("task_type") or "(unspecified)"].append(row)
        for tag in filter(None, row.get("tags", "").split("|")):
            by_tag[tag].append(row)

    report: list[str] = [
        "# Model Evaluation Report", "",
        "> Manual rubric scores are judgments, not automatic correctness proofs. Report dataset revision, answer-key review, model version, prompt template, decoding settings, reviewer, and sample size alongside these results.", "",
        f"- Rows: {len(rows)}",
        f"- Rows with at least one score: {sum(any(v is not None for v in row['_scores'].values()) for row in parsed)}",
        "- Axes: " + ", ".join(AXES),
        "- Scale: 0 = incorrect/failed; 1 = partial; 2 = correct; N/A = not applicable. Missing scores are excluded, and denominators are shown.", "",
        "## By model", "",
        "| Model | Items | Axis ratings | Mean (0–2) | Normalized score |",
        "|---|---:|---:|---:|---:|",
    ]
    for name, group in sorted(by_model.items()):
        stats = group_summary(group)
        mean = stats["overall_mean"]
        pct = stats["overall_normalized_percent"]
        report.append(f"| {name} | {stats['items']} | {stats['total_axis_ratings']} | {mean if mean is not None else '—'} | {f'{pct}%' if pct is not None else '—'} |")

    for title, groups in (("Language", by_language), ("Task type", by_task), ("Tag", by_tag)):
        report.extend(["", f"## By {title.lower()}", "", "| Group | Items | Axis ratings | Mean (0–2) | Normalized score |", "|---|---:|---:|---:|---:|"])
        for name, group in sorted(groups.items()):
            stats = group_summary(group)
            mean = stats["overall_mean"]
            pct = stats["overall_normalized_percent"]
            report.append(f"| {name} | {stats['items']} | {stats['total_axis_ratings']} | {mean if mean is not None else '—'} | {f'{pct}%' if pct is not None else '—'} |")

    # Report both item coverage and the exact overlap used for model comparisons.
    # Reviewer duplicates are collapsed to item IDs for coverage purposes.
    report.extend([
        "", "## Item coverage", "",
        "Coverage counts unique evaluation IDs, not reviewer rows. A model with fewer scored items may have a misleading aggregate; compare models on shared scored IDs.",
        "", "| Model/run | Unique items | Items with any score | Scored-item coverage |",
        "|---|---:|---:|---:|",
    ])
    scored_item_ids: dict[str, set[str]] = {}
    for name, group in sorted(by_model.items()):
        item_ids = {row["id"] for row in group}
        scored_ids = {
            row["id"] for row in group
            if any(value is not None for value in row["_scores"].values())
        }
        scored_item_ids[name] = scored_ids
        coverage = 100 * len(scored_ids) / len(item_ids) if item_ids else 0
        report.append(f"| {name} | {len(item_ids)} | {len(scored_ids)} | {coverage:.1f}% |")

    report.extend([
        "", "## Pairwise scored-item overlap", "",
        "Jaccard = shared scored item IDs divided by the union of scored item IDs. This is a coverage diagnostic, not a significance test.",
        "", "| Model A | Model B | Shared scored items | Union of scored items | Jaccard overlap |",
        "|---|---|---:|---:|---:|",
    ])
    model_names = sorted(scored_item_ids)
    if len(model_names) < 2:
        report.append("| — | — | — | — | Need at least two model/run groups |")
    else:
        for index, name_a in enumerate(model_names):
            for name_b in model_names[index + 1:]:
                ids_a, ids_b = scored_item_ids[name_a], scored_item_ids[name_b]
                shared = ids_a & ids_b
                union = ids_a | ids_b
                jaccard = 100 * len(shared) / len(union) if union else 0
                report.append(
                    f"| {name_a} | {name_b} | {len(shared)} | {len(union)} | {jaccard:.1f}% |"
                )

    # Compare independent reviewers on the exact same item and model/run. N/A and
    # blank scores are excluded; only axes with at least two numeric ratings count.
    def run_key(row: dict[str, Any]) -> tuple[str, ...]:
        return tuple(row.get(field, "").strip() for field in (
            "model", "model_version", "prompt_template_version",
            "decoding_settings", "run_date",
        ))

    run_labels: dict[tuple[str, ...], str] = {}
    reviewer_scores: dict[tuple[tuple[str, ...], str, str], list[float]] = defaultdict(list)
    for row in parsed:
        key = run_key(row)
        label = row.get("model") or "(unspecified)"
        if row.get("model_version", "").strip():
            label += f" ({row['model_version'].strip()})"
        if row.get("prompt_template_version", "").strip():
            label += f" [prompt={row['prompt_template_version'].strip()}]"
        if row.get("decoding_settings", "").strip() and row["decoding_settings"].strip() != "{}":
            label += f" [decoding={row['decoding_settings'].strip()}]"
        if row.get("run_date", "").strip():
            label += f" @ {row['run_date'].strip()}"
        run_labels[key] = label
        for axis in AXES:
            score = row["_scores"][f"score_{axis}"]
            if score is not None:
                reviewer_scores[(key, row["id"], axis)].append(score)

    disagreement_stats: dict[tuple[tuple[str, ...], str], dict[str, int]] = defaultdict(
        lambda: {"comparable_items": 0, "disagreements": 0, "rating_pairs": 0}
    )
    for (key, _identifier, axis), values in reviewer_scores.items():
        if len(values) < 2:
            continue
        stats = disagreement_stats[(key, axis)]
        stats["comparable_items"] += 1
        pair_count = len(values) * (len(values) - 1) // 2
        stats["rating_pairs"] += pair_count
        if len(set(values)) > 1:
            stats["disagreements"] += 1

    report.extend([
        "", "## Inter-rater disagreement", "",
        "For each model/run and axis, compares numeric scores from independent reviewers on the same item. Blank and N/A ratings are excluded. Disagreement is a review signal, not proof that either reviewer is wrong; adjudicate before treating scores as settled.",
        "", "| Model/run | Axis | Items with 2+ ratings | Items with disagreement | Disagreement rate | Rating pairs |",
        "|---|---|---:|---:|---:|---:|",
    ])
    if not disagreement_stats:
        report.append("| — | — | 0 | 0 | — | 0 |")
    else:
        for (key, axis), stats in sorted(disagreement_stats.items(), key=lambda item: (run_labels[item[0][0]], item[0][1])):
            rate = 100 * stats["disagreements"] / stats["comparable_items"] if stats["comparable_items"] else 0
            report.append(
                f"| {run_labels[key]} | {axis} | {stats['comparable_items']} | "
                f"{stats['disagreements']} | {rate:.1f}% | {stats['rating_pairs']} |"
            )

    # Paired comparisons use only item/axis scores available for both model runs.
    # When multiple reviewers score one item, average their numeric ratings first so
    # reviewer count does not make that item count more than once in the comparison.
    item_axis_scores: dict[str, dict[tuple[str, str], list[float]]] = defaultdict(lambda: defaultdict(list))
    for name, group in by_model.items():
        for row in group:
            for axis in AXES:
                score = row["_scores"][f"score_{axis}"]
                if score is not None:
                    item_axis_scores[name][(row["id"], axis)].append(score)

    item_axis_means: dict[str, dict[tuple[str, str], float]] = {
        name: {key: sum(values) / len(values) for key, values in scores.items()}
        for name, scores in item_axis_scores.items()
    }
    report.extend([
        "", "## Paired model comparison", "",
        "For each pair of model/run groups, compares numeric scores only on the same item and axis scored for both. Multiple reviewers are averaged within an item before comparison. Delta is B minus A; positive favors B. This is descriptive, not a significance test.",
        "", "| Model A | Model B | Axis | Shared scored items | Mean A | Mean B | Delta (B−A) | A wins | Ties | B wins |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ])
    if len(model_names) < 2:
        report.append("| — | — | — | 0 | — | — | — | — | — | Need at least two model/run groups |")
    else:
        for index, name_a in enumerate(model_names):
            for name_b in model_names[index + 1:]:
                scores_a, scores_b = item_axis_means[name_a], item_axis_means[name_b]
                for axis in AXES:
                    shared = sorted(
                        identifier for identifier, shared_axis in scores_a
                        if shared_axis == axis and (identifier, axis) in scores_b
                    )
                    if not shared:
                        continue
                    values_a = [scores_a[(identifier, axis)] for identifier in shared]
                    values_b = [scores_b[(identifier, axis)] for identifier in shared]
                    wins_a = sum(a > b for a, b in zip(values_a, values_b))
                    ties = sum(a == b for a, b in zip(values_a, values_b))
                    wins_b = sum(a < b for a, b in zip(values_a, values_b))
                    mean_a = sum(values_a) / len(values_a)
                    mean_b = sum(values_b) / len(values_b)
                    report.append(
                        f"| {name_a} | {name_b} | {axis} | {len(shared)} | "
                        f"{mean_a:.3f} | {mean_b:.3f} | {mean_b - mean_a:+.3f} | "
                        f"{wins_a} | {ties} | {wins_b} |"
                    )

    report.extend(["", "## Per-axis results", "", "| Model | Axis | Scored | Mean (0–2) | Normalized score |", "|---|---|---:|---:|---:|"])
    for name, group in sorted(by_model.items()):
        stats = group_summary(group)
        for axis, values in stats["axis_scores"].items():
            pct = values["normalized_percent"]
            report.append(f"| {name} | {axis} | {values['scored']} | {values['mean'] if values['mean'] is not None else '—'} | {f'{pct}%' if pct is not None else '—'} |")
    report.extend(["", "## Limitations", "", "- Scores are not statistically representative unless the evaluation set was designed and sampled for that purpose.",
                   "- The script does not judge semantic correctness automatically; a qualified reviewer must score each response.",
                   "- Compare models only on the same frozen items and comparable inference settings. Review per-item regressions before claiming improvement.",
                   "- A high aggregate score can hide failures in a language, task family, or safety-critical constraint."])
    output = "\n".join(report) + "\n"
    if output_path:
        Path(output_path).write_text(output, encoding="utf-8")
    else:
        print(output)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare_parser = subparsers.add_parser("prepare", help="join held-out items with saved model predictions")
    prepare_parser.add_argument("evaluation")
    prepare_parser.add_argument("predictions")
    prepare_parser.add_argument("--output", required=True)
    summary_parser = subparsers.add_parser("summarize", help="summarize manually scored CSV")
    summary_parser.add_argument("scores")
    summary_parser.add_argument("--output")
    args = parser.parse_args()
    if args.command == "prepare":
        return prepare(args.evaluation, args.predictions, args.output)
    return summarize(args.scores, args.output)


if __name__ == "__main__":
    raise SystemExit(main())
