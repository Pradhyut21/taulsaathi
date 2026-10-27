"""Additional authored adversarial text cases, not an acoustic benchmark."""

import json
import sys
import unittest
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_ROOT))
import domain

FIXTURES = json.loads((APP_ROOT / "evaluation" / "adversarial-fixtures.json").read_text(encoding="utf-8"))


class AdversarialReceiptTests(unittest.TestCase):
    pass


def make_case_test(case):
    def test(self):
        draft = domain.create_draft(case["text"], case["language"], "synthetic")
        for key, expected in case["expected"].items():
            self.assertEqual(draft[key], expected, f"{case['id']}: {key}; issues={draft['issues']}")
        if not case["expected"]["can_confirm"]:
            with self.assertRaises(ValueError):
                domain.confirm(draft, draft["revision"], True)
    return test


for fixture in FIXTURES["cases"]:
    setattr(AdversarialReceiptTests, "test_" + fixture["id"], make_case_test(fixture))


if __name__ == "__main__":
    unittest.main()
