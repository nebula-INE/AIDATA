import json
import tempfile
import unittest
from pathlib import Path

from scripts.audit_record_quality import inspect


class RecordQualityAuditTests(unittest.TestCase):
    def run_audit(self, records):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "records.jsonl"
            path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in records),
                            encoding="utf-8")
            return inspect([str(path)])

    def test_detects_generic_test_placeholders_and_empty_tests(self):
        report = self.run_audit([
            {"id": "a", "prompt": "Prompt A", "target": "Answer A",
             "tests": ["Review expected behavior against the stated assumptions; do not treat this synthetic record as verified."]},
            {"id": "b", "prompt": "Prompt B", "target": "Answer B", "tests": []},
        ])
        kinds = {item["kind"] for item in report["findings"]}
        self.assertIn("generic_test_placeholder", kinds)
        self.assertIn("no_tests_or_checks", kinds)

    def test_detects_duplicate_ids_and_prompts(self):
        report = self.run_audit([
            {"id": "same", "prompt": "Same prompt", "target": "A", "tests": ["assert A"]},
            {"id": "same", "prompt": "Same prompt", "target": "B", "tests": ["assert B"]},
        ])
        kinds = [item["kind"] for item in report["findings"]]
        self.assertIn("duplicate_id", kinds)
        self.assertIn("exact_prompt_duplicate", kinds)

    def test_detects_literal_backslash_n_in_prompt(self):
        report = self.run_audit([
            {"id": "escaped", "prompt": "first\\\\nsecond",
             "target": "Answer", "tests": ["assert answer"]},
        ])
        self.assertIn("literal_backslash_n_in_prompt", {item["kind"] for item in report["findings"]})

    def test_detects_missing_target_and_review_claim_without_reviewer(self):
        report = self.run_audit([
            {"id": "a", "prompt": "Prompt", "target": "", "tests": ["assert True"],
             "quality": {"status": "reviewed"}}
        ])
        kinds = {item["kind"] for item in report["findings"]}
        self.assertIn("missing_target", kinds)
        self.assertIn("reviewed_without_reviewer", kinds)


if __name__ == "__main__":
    unittest.main()
