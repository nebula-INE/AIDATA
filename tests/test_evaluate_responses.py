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
                            "prompt": "prompt", "target": "answer"}) + "\\n",
                encoding="utf-8",
            )
            predictions.write_text(
                json.dumps({"id": ["not", "hashable"], "prediction": "answer", "model": "m"}) + "\\n" +
                json.dumps({"id": "eval.one", "prediction": 7, "model": "m"}) + "\\n" +
                json.dumps({"id": "eval.one", "prediction": "answer", "model": " "}) + "\\n",
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


if __name__ == "__main__":
    unittest.main()
