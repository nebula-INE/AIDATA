import csv
import json
import tempfile
import unittest
from pathlib import Path

from scripts.review_dataset import FIELDS, export_queue, validate_log


class DatasetReviewWorkflowTests(unittest.TestCase):
    def test_export_creates_blank_review_decisions_without_promoting_records(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "data.jsonl"
            output = root / "review.csv"
            source.write_text(json.dumps({
                "id": "review.one", "language": "ja", "task_type": "reasoning",
                "split": "train", "prompt": "prompt", "target": "target",
                "tags": ["scope"], "quality": {"status": "draft"},
            }, ensure_ascii=False) + "\n", encoding="utf-8")
            self.assertEqual(export_queue([str(source)], str(output)), 0)
            with output.open(encoding="utf-8-sig", newline="") as handle:
                row = next(csv.DictReader(handle))
            self.assertEqual(set(row), set(FIELDS))
            self.assertEqual(row["decision"], "")
            self.assertIn("draft", row["rationale"])

    def test_validate_accepts_completed_review_and_writes_summary(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            review = root / "review.csv"
            with review.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=FIELDS)
                writer.writeheader()
                row = {field: "reviewed" for field in FIELDS}
                row.update({
                    "id": "review.one", "reviewer": "reviewer-1",
                    "review_date": "2026-10-14", "decision": "accept",
                    "answer_cardinality": "single", "expected_behavior": "answer",
                    "rationale": "Target is accurate and complete.",
                })
                writer.writerow(row)
            summary = root / "summary.md"
            self.assertEqual(validate_log(str(review), str(summary)), 0)
            self.assertIn("Accept: 1", summary.read_text(encoding="utf-8"))

    def test_validate_rejects_incomplete_or_invalid_reviews(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            review = root / "review.csv"
            with review.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=FIELDS)
                writer.writeheader()
                row = {field: "" for field in FIELDS}
                row.update({"id": "review.one", "decision": "maybe", "review_date": "not-a-date"})
                writer.writerow(row)
            self.assertEqual(validate_log(str(review), None), 1)


if __name__ == "__main__":
    unittest.main()
