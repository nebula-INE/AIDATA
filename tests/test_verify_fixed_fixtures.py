import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.verify_fixed_fixtures import (
    FIXTURES,
    build_command,
    classify_returncode,
    main,
    write_report,
)


class FixedFixtureRunnerTests(unittest.TestCase):
    def test_fixture_registry_contains_only_repository_test_patterns(self):
        self.assertTrue(FIXTURES)
        for fixture_id, pattern in FIXTURES.items():
            self.assertTrue(fixture_id)
            self.assertTrue(pattern.startswith("test_"))
            self.assertTrue(pattern.endswith(".py"))
            self.assertNotIn("/", pattern)
            self.assertNotIn("\\", pattern)

    def test_command_is_fixed_and_does_not_accept_arbitrary_selectors(self):
        command = build_command("dataset-validator")
        self.assertEqual(command[5:7], ["tests", "-p"])
        self.assertEqual(command[7], "test_validate_dataset.py")
        self.assertEqual(command[1:4], ["-m", "unittest", "discover"])
        with self.assertRaises(ValueError):
            build_command("../../some_untrusted_module")

    def test_return_code_classification(self):
        self.assertEqual(classify_returncode(0), "passed")
        self.assertEqual(classify_returncode(1), "failed")
        self.assertEqual(classify_returncode(-9), "failed")

    def test_report_is_valid_json_and_replaces_existing_file(self):
        with tempfile.TemporaryDirectory() as directory:
            report_path = Path(directory) / "nested" / "report.json"
            report_path.parent.mkdir()
            report_path.write_text('{"old": true}\n', encoding="utf-8")

            write_report(report_path, json.dumps({"status": "passed"}))

            self.assertEqual(json.loads(report_path.read_text(encoding="utf-8")), {"status": "passed"})
            self.assertEqual(
                sorted(path.name for path in report_path.parent.iterdir()),
                ["report.json"],
            )

    def test_cli_lists_allowlisted_ids(self):
        with patch("builtins.print") as output:
            self.assertEqual(main(["--list"]), 0)
        listed = output.call_args.args[0].splitlines()
        self.assertEqual(listed, sorted(FIXTURES))

    def test_cli_rejects_out_of_range_timeout(self):
        with self.assertRaises(SystemExit) as raised:
            main(["--fixture", "dataset-validator", "--timeout", "0"])
        self.assertEqual(raised.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
