import csv
import json
import tempfile
import unittest
from pathlib import Path

from scripts.blind_review import blind, restore


class BlindReviewTests(unittest.TestCase):
    def test_blind_then_restore_preserves_scores_and_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, blinded, manifest, restored = (
                root / "source.csv", root / "blind.csv",
                root / "manifest.json", root / "restored.csv",
            )
            fields = ["id", "model", "model_version", "prompt_template_version",
                      "decoding_settings", "run_date", "score_meaning", "notes"]
            rows = [
                {"id": "item-1", "model": "provider-a", "model_version": "v1",
                 "prompt_template_version": "p1", "decoding_settings": '{"temperature": 0}',
                 "run_date": "2026-10-17", "score_meaning": "2", "notes": "good"},
                {"id": "item-2", "model": "provider-a", "model_version": "v1",
                 "prompt_template_version": "p1", "decoding_settings": '{"temperature": 0}',
                 "run_date": "2026-10-17", "score_meaning": "1", "notes": "partial"},
                {"id": "item-1", "model": "provider-b", "model_version": "v2",
                 "prompt_template_version": "p1", "decoding_settings": '{"temperature": 0}',
                 "run_date": "2026-10-17", "score_meaning": "2", "notes": ""},
            ]
            with source.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader()
                writer.writerows(rows)

            self.assertEqual(blind(str(source), str(blinded), str(manifest)), 0)
            with blinded.open(encoding="utf-8-sig", newline="") as handle:
                blind_rows = list(csv.DictReader(handle))
            self.assertEqual(blind_rows[0]["model"], "model-001")
            self.assertEqual(blind_rows[1]["model"], "model-001")
            self.assertEqual(blind_rows[2]["model"], "model-002")
            self.assertEqual(blind_rows[0]["model_version"], "")
            blind_text = blinded.read_text(encoding="utf-8-sig")
            self.assertNotIn("provider-a", blind_text)
            self.assertNotIn("provider-b", blind_text)

            # Simulate reviewer scoring on the anonymized worksheet.
            blind_rows[0]["score_meaning"] = "0"
            with blinded.open("w", encoding="utf-8-sig", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=blind_rows[0].keys())
                writer.writeheader()
                writer.writerows(blind_rows)
            self.assertEqual(restore(str(blinded), str(manifest), str(restored)), 0)
            with restored.open(encoding="utf-8-sig", newline="") as handle:
                result = list(csv.DictReader(handle))
            self.assertEqual(result[0]["model"], "provider-a")
            self.assertEqual(result[0]["model_version"], "v1")
            self.assertEqual(result[0]["score_meaning"], "0")
            self.assertEqual(result[0]["notes"], "good")

    def test_blind_rejects_path_collisions_without_overwriting_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.csv"
            source.write_text("id,model\nx,provider-a\n", encoding="utf-8")
            original = source.read_text(encoding="utf-8")
            manifest = root / "manifest.json"
            self.assertEqual(blind(str(source), str(source), str(manifest)), 1)
            self.assertEqual(source.read_text(encoding="utf-8"), original)
            self.assertFalse(manifest.exists())

    def test_restore_rejects_path_collisions_without_overwriting_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "blind.csv"
            source.write_text("id,model\nx,model-001\n", encoding="utf-8")
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({
                "manifest_version": 1,
                "models": {"model-001": {"model": "provider-a", "model_version": "v1",
                    "prompt_template_version": "", "decoding_settings": "", "run_date": ""}},
            }), encoding="utf-8")
            original = manifest.read_text(encoding="utf-8")
            self.assertEqual(restore(str(source), str(manifest), str(manifest)), 1)
            self.assertEqual(manifest.read_text(encoding="utf-8"), original)

    def test_restore_rejects_unknown_blind_label(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, manifest, output = root / "input.csv", root / "manifest.json", root / "out.csv"
            source.write_text("id,model\nx,model-999\n", encoding="utf-8")
            manifest.write_text(json.dumps({
                "manifest_version": 1,
                "models": {"model-001": {"model": "m", "model_version": "v1",
                    "prompt_template_version": "", "decoding_settings": "", "run_date": ""}},
            }), encoding="utf-8")
            self.assertEqual(restore(str(source), str(manifest), str(output)), 1)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
