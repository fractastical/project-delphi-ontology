import csv
import unittest
import tempfile
import json
from unittest.mock import patch
from pathlib import Path
from review_context import IDENTITY, PARTICIPANTS, PAPER_ADDITIONS, build, SNAPSHOT


class ReviewTests(unittest.TestCase):
    def test_complete_unique_decisions(self):
        with Path(__file__).with_name("context_decisions.tsv").open() as f:
            rows = list(csv.DictReader(f, delimiter="\t"))
        self.assertEqual(len(rows), 200)
        self.assertEqual({(int(r["claim"]), int(r["evidence"])) for r in rows},
                         {(i, j) for i in range(40) for j in range(5)})
        self.assertTrue(all(r["conditions"] and r["organism"] for r in rows))

    def test_identity_and_catalyst_boundaries(self):
        self.assertIn("not GJA1", IDENTITY[20])
        self.assertIn("process", IDENTITY[36])
        self.assertIn("upstream", PARTICIPANTS[2, 3])
        self.assertNotIn((1, 0), PAPER_ADDITIONS)  # rat background, mouse study
        self.assertNotIn((0, 1), PAPER_ADDITIONS)  # background != HAEC experiment

    def test_wrong_snapshot_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw = Path(tmp) / "raw.json"
            raw.write_text("{}")
            with self.assertRaisesRegex(ValueError, "different snapshot"):
                build(raw, raw, raw, Path(tmp))

    def test_wrong_mapping_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw = Path(tmp) / "raw.json"
            mapped = Path(tmp) / "mapped.json"
            raw.write_text(json.dumps([{"type": "Activation", "subj": {"name": "A"},
                                        "obj": {"name": "B"}, "evidence": []}]))
            mapped.write_text("{}")
            with patch("review_context.sha", return_value=SNAPSHOT):
                with self.assertRaisesRegex(ValueError, "does not match"):
                    build(raw, mapped, raw, Path(tmp))


if __name__ == "__main__":
    unittest.main()
