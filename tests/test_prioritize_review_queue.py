import csv
import json
import tempfile
import unittest
from pathlib import Path

from scripts.prioritize_review_queue import prioritize, read_records, read_reviews


class PrioritizedReviewQueueTests(unittest.TestCase):
    def test_missing_review_is_p0_and_draft_is_never_promoted(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "data.jsonl"
            source.write_text(json.dumps({
                "id": "sample.one", "split": "train", "task_type": "coding",
                "language": "ja", "quality": {"status": "draft"},
                "prompt": "hidden prompt", "target": "hidden target",
            }) + "\n", encoding="utf-8")
            rows = prioritize(read_records([str(source)]), {})
            self.assertEqual(rows[0]["priority"], "P0")
            self.assertIn("human_review_missing", rows[0]["reason"])
            self.assertEqual(rows[0]["quality_status"], "draft")
            self.assertNotIn("prompt", rows[0])
            self.assertNotIn("target", rows[0])

    def test_reviewed_with_evidence_is_p2_and_verified_is_p3(self):
        base = {
            "id": "sample.one", "split": "train", "task_type": "coding",
            "language": "ja", "quality": {"status": "reviewed"},
        }
        review = {
            "decision": "accept", "reviewer": "reviewer-1",
            "evidence_kind": "manual_reasoning",
            "evidence_reference": "checked by hand",
            "verification_result": "not_applicable",
        }
        self.assertEqual(prioritize([base], {"sample.one": review})[0]["priority"], "P2")
        verified = {**base, "quality": {"status": "verified"}}
        passed_review = {**review, "verification_result": "passed"}
        self.assertEqual(prioritize([verified], {"sample.one": passed_review})[0]["priority"], "P3")

    def test_failed_verification_is_p0_even_if_status_says_verified(self):
        record = {
            "id": "sample.one", "quality": {"status": "verified"},
            "split": "train", "task_type": "testing", "language": "ja",
        }
        review = {
            "decision": "accept", "reviewer": "reviewer-1",
            "evidence_kind": "fixed_fixture_report", "evidence_reference": "report.json",
            "verification_result": "failed",
        }
        row = prioritize([record], {"sample.one": review})[0]
        self.assertEqual(row["priority"], "P0")
        self.assertIn("verification_failed", row["reason"])
        self.assertIn("status_review_consistency_check", row["reason"])

    def test_eval_records_are_excluded_unless_explicitly_requested(self):
        records = [
            {
                "id": "train.one", "split": "train", "task_type": "coding",
                "language": "ja", "quality": {"status": "draft"},
            },
            {
                "id": "eval.one", "split": "eval", "task_type": "coding",
                "language": "ja", "quality": {"status": "draft"},
            },
        ]
        default_rows = prioritize(records, {})
        self.assertEqual([row["id"] for row in default_rows], ["train.one"])
        explicit_rows = prioritize(records, {}, include_eval=True)
        self.assertEqual({row["id"] for row in explicit_rows}, {"train.one", "eval.one"})

    def test_duplicate_review_ids_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "review.csv"
            fields = ["id", "decision"]
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader()
                writer.writerow({"id": "same", "decision": "accept"})
                writer.writerow({"id": "same", "decision": "accept"})
            with self.assertRaisesRegex(ValueError, "duplicate id"):
                read_reviews(str(path))


if __name__ == "__main__":
    unittest.main()
