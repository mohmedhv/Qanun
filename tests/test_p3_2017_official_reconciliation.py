"""Checks documentary status of the 2017 official amendments without claiming a second reviewer."""
import json
import unittest
from pathlib import Path


DATA = Path(__file__).resolve().parents[1] / "data/interim/amendments.json"

class OfficialReconciliationTests(unittest.TestCase):
    def test_three_complete_2017_wordings_are_preserved(self):
        data = json.loads(DATA.read_text(encoding="utf-8"))
        for article in ("141", "144", "145"):
            row = next(r for r in data if r["modifying_text_id"] == "loi-17-11" and r["target_article"] == article)
            self.assertTrue(row["official_full_wording_checked"])
            self.assertFalse(row["partial"])
            self.assertFalse(row["needs_review"])
            self.assertIn("En cas de récidive", row["new_content"])
            self.assertEqual(row["independent_check_status"], "pending")

    def test_reconstructed_wordings_keep_source_excerpt_and_human_review_state(self):
        data = json.loads(DATA.read_text(encoding="utf-8"))
        self.assertEqual(len(data), 79)
        self.assertEqual(sum(bool(r.get("needs_review")) for r in data), 0)
        self.assertEqual(sum(bool(r.get("official_full_wording_checked")) for r in data), 19)
        reconstructed = [r for r in data if r.get("official_full_wording_checked") and r.get("partial")]
        self.assertEqual(len(reconstructed), 16)
        self.assertTrue(all(r.get("independent_check_status") == "pending" for r in reconstructed))
        self.assertTrue(all(r.get("independent_check_status", "pending") == "pending" for r in data))

if __name__ == "__main__":
    unittest.main()
