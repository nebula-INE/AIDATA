import csv
import json
import tempfile
import unittest
from pathlib import Path

from scripts.evaluate_responses import AXES, prepare, summarize


class EvaluationHarnessTests(unittest.TestCase):
    def test_prepare_joins_predictions_and_flags_missing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evaluation = root / "eval.jsonl"
            predictions = root / "predictions.jsonl"
            output = root / "review.csv"
            evaluation.write_text(
                json.dumps({"id": "eval.one", "language": "ja", "task_type": "reasoning",
                            "prompt": "prompt", "target": "answer", "tags": ["negation"]}) + "\n" +
                json.dumps({"id": "eval.two", "language": "en", "task_type": "coding",
                            "prompt": "second prompt", "target": "second", "tags": ["coding"]}) + "\n",
                encoding="utf-8",
            )
            predictions.write_text(
                json.dumps({"id": "eval.one", "prediction": "model answer", "model": "baseline",
                            "model_version": "v1"}) + "\n",
                encoding="utf-8",
            )
            self.assertEqual(prepare(str(evaluation), str(predictions), str(output)), 0)
            with output.open(encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["prediction"], "model answer")
            self.assertEqual(rows[0]["prompt"], "prompt")
            self.assertEqual(rows[1]["notes"], "MISSING PREDICTION")
            self.assertEqual(rows[0]["score_meaning"], "")


    def test_prepare_rejects_malformed_prediction_fields_without_crashing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evaluation = root / "eval.jsonl"
            predictions = root / "predictions.jsonl"
            output = root / "review.csv"
            evaluation.write_text(
                json.dumps({"id": "eval.one", "language": "ja", "task_type": "coding",
                            "prompt": "prompt", "target": "answer"}) + "\n",
                encoding="utf-8",
            )
            predictions.write_text(
                json.dumps({"id": ["not", "hashable"], "prediction": "answer", "model": "m"}) + "\n" +
                json.dumps({"id": "eval.one", "prediction": 7, "model": "m"}) + "\n" +
                json.dumps({"id": "eval.one", "prediction": "answer", "model": " "}) + "\n",
                encoding="utf-8",
            )
            self.assertEqual(prepare(str(evaluation), str(predictions), str(output)), 1)
            self.assertFalse(output.exists())

    def test_prepare_rejects_malformed_evaluation_display_fields(self):
        malformed_records = [
            {"id": "eval.one", "tags": "not-a-list"},
            {"id": "eval.one", "tags": ["valid", 7]},
            {"id": "eval.one", "prompt": ["not", "text"]},
            {"id": "eval.one", "target": None},
        ]
        for record in malformed_records:
            with self.subTest(record=record), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                evaluation = root / "eval.jsonl"
                predictions = root / "predictions.jsonl"
                output = root / "review.csv"
                evaluation.write_text(json.dumps(record) + "\n", encoding="utf-8")
                predictions.write_text(
                    json.dumps({"id": "eval.one", "prediction": "answer", "model": "m"}) + "\n",
                    encoding="utf-8",
                )
                self.assertEqual(prepare(str(evaluation), str(predictions), str(output)), 1)
                self.assertFalse(output.exists())

    def test_summarize_uses_denominator_of_scored_axes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "scores.csv"
            fields = ["id", "model", "language", "task_type", "tags", *[f"score_{a}" for a in AXES]]
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader()
                row = {"id": "x", "model": "m", "language": "ja", "task_type": "reasoning", "tags": "scope"}
                row.update({f"score_{a}": "2" if a == "meaning" else "N/A" for a in AXES})
                writer.writerow(row)
            report = Path(directory) / "report.md"
            self.assertEqual(summarize(str(path), str(report)), 0)
            content = report.read_text(encoding="utf-8")
            self.assertIn("100.0%", content)
            self.assertIn("Axis ratings", content)

    def test_invalid_scores_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "scores.csv"
            fields = ["id", "model", "language", "task_type", "tags", *[f"score_{a}" for a in AXES]]
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader()
                row = {"id": "x", "model": "m", "language": "ja", "task_type": "reasoning", "tags": ""}
                row.update({f"score_{a}": "3" for a in AXES})
                writer.writerow(row)
            self.assertEqual(summarize(str(path), None), 1)


    def test_summarize_rejects_unscored_worksheet(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "scores.csv"
            fields = ["id", "model", "language", "task_type", "tags", *[f"score_{a}" for a in AXES]]
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader()
                row = {"id": "x", "model": "m", "language": "ja", "task_type": "reasoning", "tags": ""}
                row.update({f"score_{a}": "" for a in AXES})
                writer.writerow(row)
            self.assertEqual(summarize(str(path), None), 1)

    def test_summarize_separates_prompt_template_versions(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "scores.csv"
            fields = [
                "id", "model", "model_version", "prompt_template_version",
                "decoding_settings", "run_date", "language", "task_type", "tags",
                *[f"score_{a}" for a in AXES],
            ]
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader()
                for identifier, template in (("x", "system-v1"), ("x", "system-v2")):
                    row = {
                        "id": identifier, "model": "m", "model_version": "v1",
                        "prompt_template_version": template, "decoding_settings": '{"temperature": 0}',
                        "run_date": "2026-10-17", "language": "ja", "task_type": "reasoning", "tags": "",
                    }
                    row.update({f"score_{a}": "2" if a == "meaning" else "N/A" for a in AXES})
                    writer.writerow(row)
            report = Path(directory) / "report.md"
            self.assertEqual(summarize(str(path), str(report)), 0)
            content = report.read_text(encoding="utf-8")
            self.assertIn("[prompt=system-v1]", content)
            self.assertIn("[prompt=system-v2]", content)


    def test_summarize_rejects_duplicate_item_run_reviewer_rows(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "scores.csv"
            fields = [
                "id", "model", "model_version", "prompt_template_version",
                "decoding_settings", "run_date", "reviewer", "language", "task_type", "tags",
                *[f"score_{a}" for a in AXES],
            ]
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader()
                for _ in range(2):
                    row = {
                        "id": "x", "model": "m", "model_version": "v1",
                        "prompt_template_version": "system-v1", "decoding_settings": '{"temperature": 0}',
                        "run_date": "2026-10-17", "reviewer": "reviewer-a",
                        "language": "ja", "task_type": "reasoning", "tags": "",
                    }
                    row.update({f"score_{a}": "2" if a == "meaning" else "N/A" for a in AXES})
                    writer.writerow(row)
            self.assertEqual(summarize(str(path), None), 1)

    def test_summarize_allows_independent_reviewers_for_same_item(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "scores.csv"
            fields = [
                "id", "model", "model_version", "prompt_template_version",
                "decoding_settings", "run_date", "reviewer", "language", "task_type", "tags",
                *[f"score_{a}" for a in AXES],
            ]
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader()
                for reviewer, score in (("reviewer-a", "2"), ("reviewer-b", "1")):
                    row = {
                        "id": "x", "model": "m", "model_version": "v1",
                        "prompt_template_version": "system-v1", "decoding_settings": '{"temperature": 0}',
                        "run_date": "2026-10-17", "reviewer": reviewer,
                        "language": "ja", "task_type": "reasoning", "tags": "",
                    }
                    row.update({f"score_{a}": score if a == "meaning" else "N/A" for a in AXES})
                    writer.writerow(row)
            report = Path(directory) / "report.md"
            self.assertEqual(summarize(str(path), str(report)), 0)
            self.assertIn("1.5", report.read_text(encoding="utf-8"))

    def test_summarize_reports_inter_rater_disagreement_per_axis(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "scores.csv"
            fields = [
                "id", "model", "model_version", "prompt_template_version",
                "decoding_settings", "run_date", "reviewer", "language", "task_type", "tags",
                *[f"score_{a}" for a in AXES],
            ]
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader()
                for reviewer, meaning_score in (("reviewer-a", "2"), ("reviewer-b", "1"),
                                                ("reviewer-c", "N/A")):
                    row = {
                        "id": "x", "model": "m", "model_version": "v1",
                        "prompt_template_version": "system-v1", "decoding_settings": "{}",
                        "run_date": "2026-10-17", "reviewer": reviewer,
                        "language": "ja", "task_type": "reasoning", "tags": "",
                    }
                    row.update({f"score_{a}": meaning_score if a == "meaning" else "N/A" for a in AXES})
                    writer.writerow(row)
            report = Path(directory) / "report.md"
            self.assertEqual(summarize(str(path), str(report)), 0)
            content = report.read_text(encoding="utf-8")
            self.assertIn("## Inter-rater disagreement", content)
            self.assertIn("| m (v1) [prompt=system-v1] @ 2026-10-17 | meaning | 1 | 1 | 100.0% | 1 |", content)

    def test_summarize_reports_model_item_coverage_and_pairwise_overlap(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "scores.csv"
            fields = [
                "id", "model", "model_version", "prompt_template_version",
                "decoding_settings", "run_date", "reviewer", "language", "task_type", "tags",
                *[f"score_{a}" for a in AXES],
            ]
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader()
                for identifier, model in (("x", "model-a"), ("y", "model-a"),
                                          ("x", "model-b"), ("z", "model-b")):
                    row = {
                        "id": identifier, "model": model, "model_version": "v1",
                        "prompt_template_version": "system-v1", "decoding_settings": '{"temperature": 0}',
                        "run_date": "2026-10-17", "reviewer": "reviewer-a",
                        "language": "ja", "task_type": "reasoning", "tags": "",
                    }
                    row.update({f"score_{a}": "2" if a == "meaning" else "N/A" for a in AXES})
                    writer.writerow(row)
            report = Path(directory) / "report.md"
            self.assertEqual(summarize(str(path), str(report)), 0)
            content = report.read_text(encoding="utf-8")
            self.assertIn("## Item coverage", content)
            self.assertIn("| model-a (v1) [prompt=system-v1] [decoding={\"temperature\": 0}] @ 2026-10-17 | 2 | 2 | 100.0% |", content)
            self.assertIn("## Pairwise scored-item overlap", content)
            self.assertIn("| model-a (v1) [prompt=system-v1] [decoding={\"temperature\": 0}] @ 2026-10-17 | model-b (v1) [prompt=system-v1] [decoding={\"temperature\": 0}] @ 2026-10-17 | 1 | 3 | 33.3% |", content)

    def test_summarize_rejects_malformed_csv_row_width(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "scores.csv"
            fields = ["id", "model", "language", "task_type", "tags", *[f"score_{a}" for a in AXES]]
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.writer(handle)
                writer.writerow(fields)
                writer.writerow(["x", "m", "ja", "coding", "", "2", "N/A", "N/A", "N/A", "N/A", "N/A", "unexpected"])
            self.assertEqual(summarize(str(path), None), 1)

    def test_summarize_rejects_duplicate_csv_headers(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "scores.csv"
            fields = ["id", "model", "language", "task_type", "tags", *[f"score_{a}" for a in AXES]]
            fields[1] = "id"
            path.write_text(",".join(fields) + "\n" + ",".join(["x"] * len(fields)) + "\n", encoding="utf-8")
            self.assertEqual(summarize(str(path), None), 1)

    def test_summarize_rejects_blank_identity_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "scores.csv"
            fields = ["id", "model", "language", "task_type", "tags", *[f"score_{a}" for a in AXES]]
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader()
                row = {"id": " ", "model": "", "language": "ja", "task_type": "coding", "tags": ""}
                row.update({f"score_{a}": "2" if a == "meaning" else "N/A" for a in AXES})
                writer.writerow(row)
            self.assertEqual(summarize(str(path), None), 1)


    def test_summarize_reports_paired_per_item_model_comparison(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "scores.csv"
            fields = [
                "id", "model", "model_version", "prompt_template_version",
                "decoding_settings", "run_date", "reviewer", "language", "task_type", "tags",
                *[f"score_{a}" for a in AXES],
            ]
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader()
                for identifier, model, score in (
                    ("shared", "model-a", "2"),
                    ("shared", "model-b", "1"),
                    ("only-a", "model-a", "2"),
                    ("only-b", "model-b", "0"),
                ):
                    row = {
                        "id": identifier, "model": model, "model_version": "v1",
                        "prompt_template_version": "system-v1", "decoding_settings": "{}",
                        "run_date": "2026-10-17", "reviewer": "reviewer-a",
                        "language": "ja", "task_type": "reasoning", "tags": "",
                    }
                    row.update({f"score_{a}": score if a == "meaning" else "N/A" for a in AXES})
                    writer.writerow(row)
            report = Path(directory) / "report.md"
            self.assertEqual(summarize(str(path), str(report)), 0)
            content = report.read_text(encoding="utf-8")
            self.assertIn("## Paired model comparison", content)
            self.assertIn(
                "| model-a (v1) [prompt=system-v1] @ 2026-10-17 | "
                "model-b (v1) [prompt=system-v1] @ 2026-10-17 | meaning | 1 | "
                "2.000 | 1.000 | -1.000 | 1 | 0 | 0 |",
                content,
            )


if __name__ == "__main__":
    unittest.main()
