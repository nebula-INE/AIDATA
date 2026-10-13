import json
import tempfile
import unittest
from pathlib import Path

from scripts.audit_dataset import find_duplicates, jaccard, load_records, normalize, token_set


class DuplicateAuditTests(unittest.TestCase):
    def test_normalize_ignores_case_punctuation_and_extra_spaces(self):
        self.assertEqual(normalize("Hello,   WORLD!"), normalize("hello world"))

    def test_jaccard_handles_empty_sets(self):
        self.assertEqual(jaccard(set(), set()), 1.0)
        self.assertEqual(jaccard({"a"}, {"b"}), 0.0)

    def test_exact_duplicate_prompts_are_reported(self):
        records = [
            {"id": "one", "prompt": "Write a safe parser!"},
            {"id": "two", "prompt": " write A safe parser "},
        ]
        exact, near = find_duplicates(records)
        self.assertEqual(len(exact), 1)
        self.assertEqual(near, [])

    def test_near_duplicate_candidate_is_reported(self):
        records = [
            {"id": "one", "prompt": "Implement a robust parser for duration strings safely"},
            {"id": "two", "prompt": "Implement a robust parser for duration strings carefully"},
        ]
        exact, near = find_duplicates(records, threshold=0.7)
        self.assertEqual(exact, [])
        self.assertEqual(len(near), 1)

    def test_short_prompts_do_not_create_near_duplicate_noise(self):
        records = [
            {"id": "one", "prompt": "fix bug now"},
            {"id": "two", "prompt": "fix bug today"},
        ]
        exact, near = find_duplicates(records, threshold=0.5)
        self.assertEqual(exact, [])
        self.assertEqual(near, [])

    def test_load_records_reads_jsonl_without_executing_content(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "items.jsonl"
            path.write_text(json.dumps({"id": "x", "prompt": "print('not executed')"}) + "\n",
                            encoding="utf-8")
            records = load_records([str(path)])
        self.assertEqual(records[0]["prompt"], "print('not executed')")


if __name__ == "__main__":
    unittest.main()
