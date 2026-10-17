import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from scripts.check_eval_leakage import main


class EvalLeakageAuditTests(unittest.TestCase):
    def _write(self, directory: str, name: str, prompt: str, record_id: str) -> str:
        path = Path(directory) / name
        path.write_text(json.dumps({"id": record_id, "prompt": prompt}) + "\n", encoding="utf-8")
        return str(path)

    def test_exact_cross_split_overlap_fails_and_reports_both_records(self):
        with tempfile.TemporaryDirectory() as directory:
            train = self._write(directory, "train.jsonl", "Implement a safe parser!", "train-1")
            evaluation = self._write(directory, "eval.jsonl", " implement A safe parser ", "eval-1")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = main(["--train", train, "--eval", evaluation])
        self.assertEqual(code, 1)
        self.assertIn("Cross-split exact normalized prompt overlaps: 1", output.getvalue())
        self.assertIn("train-1", output.getvalue())
        self.assertIn("eval-1", output.getvalue())

    def test_near_match_is_advisory_not_a_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            train = self._write(directory, "train.jsonl",
                                "Implement a robust parser for duration strings safely", "train-1")
            evaluation = self._write(directory, "eval.jsonl",
                                     "Implement a robust parser for duration strings carefully", "eval-1")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = main(["--train", train, "--eval", evaluation, "--threshold", "0.7"])
        self.assertEqual(code, 0)
        self.assertIn("Cross-split near-duplicate candidates", output.getvalue())

    def test_same_split_duplicates_are_not_reported_as_cross_split_leakage(self):
        with tempfile.TemporaryDirectory() as directory:
            train_a = self._write(directory, "train-a.jsonl", "Implement a safe parser", "train-1")
            train_b = self._write(directory, "train-b.jsonl", "Implement a safe parser", "train-2")
            evaluation = self._write(directory, "eval.jsonl", "Write a different task about maps", "eval-1")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = main(["--train", train_a, train_b, "--eval", evaluation])
        self.assertEqual(code, 0)
        self.assertIn("Cross-split exact normalized prompt overlaps: 0", output.getvalue())


if __name__ == "__main__":
    unittest.main()
