import json
import tempfile
import unittest
from pathlib import Path

from scripts.report_dataset_coverage import read_records, summarize


class DatasetCoverageTests(unittest.TestCase):
    def test_counts_language_split_status_and_review_queue(self):
        records = [
            {"id": "a.one", "language": "ja", "split": "train", "task_type": "reasoning",
             "quality": {"status": "draft"}, "tags": ["vocabulary", "scope"]},
            {"id": "b.two", "language": "en", "split": "eval", "task_type": "coding",
             "quality": {"status": "verified"}, "tags": ["coding"]},
        ]
        report = summarize(records)
        self.assertEqual(report["record_count"], 2)
        self.assertEqual(report["language_counts"], {"en": 1, "ja": 1})
        self.assertEqual(report["split_counts"], {"eval": 1, "train": 1})
        self.assertEqual(report["draft_review_queue_count"], 1)

    def test_duplicate_ids_and_split_overlap_are_reported(self):
        records = [
            {"id": "same.id", "language": "ja", "split": "train", "task_type": "reasoning", "quality": {"status": "draft"}, "tags": []},
            {"id": "same.id", "language": "en", "split": "eval", "task_type": "reasoning", "quality": {"status": "draft"}, "tags": []},
        ]
        report = summarize(records)
        self.assertEqual(report["duplicate_ids"], ["same.id"])
        self.assertEqual(report["train_validation_eval_id_overlap"], ["same.id"])

    def test_reads_jsonl(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data.jsonl"
            path.write_text(json.dumps({"id": "entry.one", "language": "ja"}) + "\n", encoding="utf-8")
            records, errors = read_records([str(path)])
            self.assertEqual(errors, [])
            self.assertEqual(records[0]["id"], "entry.one")


if __name__ == "__main__":
    unittest.main()
