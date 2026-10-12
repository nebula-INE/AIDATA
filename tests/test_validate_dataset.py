import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_dataset import main, validate_record


def valid_record(**overrides):
    record = {
        "schema_version": "1.0",
        "id": "test.record.001",
        "task_type": "coding",
        "prompt": "Implement a pure function.",
        "target": "def answer():\n    return 42",
        "language": "python",
        "split": "train",
        "provenance": {"kind": "synthetic", "source": "unit test"},
        "license": "CC0-1.0",
        "quality": {"status": "draft", "notes": "Test fixture."},
        "tests": ["assert answer() == 42"],
        "tags": ["unit-test"],
    }
    record.update(overrides)
    return record


class ValidateRecordTests(unittest.TestCase):
    def test_valid_record_passes(self):
        self.assertEqual(validate_record(valid_record(), 1), [])

    def test_non_object_is_reported(self):
        self.assertIn("expected a JSON object", validate_record([], 1)[0])

    def test_unhashable_task_type_does_not_crash(self):
        errors = validate_record(valid_record(task_type=[]), 1)
        self.assertTrue(any("task_type" in error for error in errors))

    def test_unknown_top_level_field_is_rejected(self):
        record = valid_record()
        record["surprise"] = True
        self.assertTrue(any("unknown fields" in error for error in validate_record(record, 1)))

    def test_unknown_nested_field_is_rejected(self):
        record = valid_record()
        record["quality"]["extra"] = "value"
        self.assertTrue(any("unknown quality fields" in error for error in validate_record(record, 1)))

    def test_invalid_test_shape_is_rejected(self):
        self.assertTrue(any("tests must be a list" in error for error in validate_record(valid_record(tests="assert True"), 1)))

    def test_short_id_is_rejected(self):
        self.assertTrue(any("id" in error for error in validate_record(valid_record(id="ab"), 1)))


class ValidateDatasetCliTests(unittest.TestCase):
    def test_duplicate_ids_across_files_fail(self):
        record = json.dumps(valid_record())
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first.jsonl"
            second = Path(directory) / "second.jsonl"
            first.write_text(record + "\n", encoding="utf-8")
            second.write_text(record + "\n", encoding="utf-8")
            self.assertEqual(main(["validate_dataset.py", str(first), str(second)]), 1)

    def test_invalid_json_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "broken.jsonl"
            path.write_text("{not json}\n", encoding="utf-8")
            self.assertEqual(main(["validate_dataset.py", str(path)]), 1)

    def test_empty_argument_list_returns_usage_error(self):
        self.assertEqual(main(["validate_dataset.py"]), 2)


if __name__ == "__main__":
    unittest.main()
