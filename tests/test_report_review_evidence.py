import csv
import json
import tempfile
import unittest
from pathlib import Path

from scripts.report_review_evidence import (
    build_summary, load_dataset_records, load_fixture_report, load_review_rows,
)


class ReviewEvidenceReportTests(unittest.TestCase):
    def _write_review(self, path: Path, rows: list[dict[str, str]]) -> None:
        fields = [
            "id", "reviewer", "decision", "evidence_kind", "evidence_reference",
            "verification_commit", "verification_result",
        ]
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

    def test_summary_separates_review_and_fixture_counts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            review = root / "review.csv"
            self._write_review(review, [
                {"id": "a", "decision": "accept", "evidence_kind": "manual_reasoning", "verification_result": "not_applicable"},
                {"id": "b", "decision": "", "evidence_kind": "", "verification_result": ""},
            ])
            rows = load_review_rows(review)
            report = {
                "runner": "verify_fixed_fixtures.py",
                "results": [
                    {"fixture_id": "dataset-validator", "status": "passed"},
                    {"fixture_id": "review-workflow", "status": "failed"},
                    {"fixture_id": "coverage-report", "status": "timeout"},
                ],
            }
            summary = build_summary(rows, report)
            self.assertIn("Review rows: 2", summary)
            self.assertIn("Completed decisions: 1", summary)
            self.assertIn("Pending decisions: 1", summary)
            self.assertIn("- passed: 1", summary)
            self.assertIn("- failed: 1", summary)
            self.assertIn("- timeout: 1", summary)
            self.assertIn("does not infer that a fixture validates", summary)
            self.assertIn("does not establish semantic correctness", summary)

    def test_dataset_coverage_matches_ids_and_reports_unknown_ids(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dataset = root / "data.jsonl"
            dataset.write_text(
                '\n'.join([
                    json.dumps({"id": "a", "split": "train"}),
                    json.dumps({"id": "b", "split": "validation"}),
                    json.dumps({"id": "heldout", "split": "eval"}),
                ]) + '\n',
                encoding="utf-8",
            )
            review = root / "review.csv"
            self._write_review(review, [
                {"id": "a", "decision": "accept"},
                {"id": "b", "decision": ""},
                {"id": "not-in-data", "decision": "retire"},
            ])
            records = load_dataset_records([dataset])
            summary = build_summary(load_review_rows(review), dataset_records=records)
            self.assertIn("Dataset records in scope: 2", summary)
            self.assertIn("Dataset records with a completed decision: 1", summary)
            self.assertIn("Dataset records still without a completed decision: 1", summary)
            self.assertIn("Review CSV IDs absent from the dataset inputs: 1", summary)
            self.assertIn("- train: 1/1", summary)
            self.assertIn("- validation: 0/1", summary)
            self.assertIn("- not-in-data", summary)
            self.assertNotIn("heldout", summary)

    def test_dataset_eval_can_be_included_explicitly(self):
        with tempfile.TemporaryDirectory() as directory:
            dataset = Path(directory) / "data.jsonl"
            dataset.write_text(json.dumps({"id": "eval-id", "split": "eval"}) + '\n', encoding="utf-8")
            self.assertEqual(load_dataset_records([dataset]), [])
            self.assertEqual(load_dataset_records([dataset], include_eval=True), [
                {"id": "eval-id", "split": "eval"}
            ])

    def test_dataset_duplicate_ids_are_rejected_even_when_eval_is_filtered(self):
        with tempfile.TemporaryDirectory() as directory:
            dataset = Path(directory) / "data.jsonl"
            dataset.write_text(
                json.dumps({"id": "same", "split": "eval"}) + '\n' +
                json.dumps({"id": "same", "split": "train"}) + '\n',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "duplicate dataset id"):
                load_dataset_records([dataset])

    def test_unrecognized_decisions_are_visible_and_not_counted_as_pending(self):
        summary = build_summary([
            {"id": "a", "decision": "accept"},
            {"id": "b", "decision": "maybe"},
            {"id": "c", "decision": ""},
        ])
        self.assertIn("Completed decisions: 1", summary)
        self.assertIn("Pending decisions: 1", summary)
        self.assertIn("Invalid/unrecognized decisions: 1", summary)
        self.assertIn("- maybe: 1", summary)

    def test_rejects_duplicate_review_ids(self):
        with tempfile.TemporaryDirectory() as directory:
            review = Path(directory) / "review.csv"
            row = {"id": "same", "decision": "accept"}
            self._write_review(review, [row, row])
            with self.assertRaisesRegex(ValueError, "duplicate id"):
                load_review_rows(review)

    def test_rejects_malformed_fixture_report(self):
        with tempfile.TemporaryDirectory() as directory:
            report_path = Path(directory) / "report.json"
            report_path.write_text(json.dumps({"results": [{"fixture_id": "x", "status": "unknown"}]}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unsupported status"):
                load_fixture_report(report_path)


if __name__ == "__main__":
    unittest.main()
