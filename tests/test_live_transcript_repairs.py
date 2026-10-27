"""Bounded repairs from synthetic development ASR, never human speech scores."""

import sys
import unittest
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import domain

# Exact raw transcripts from the saved synthetic development run. Clean/noisy
# variants returned the same text; this is not a new independent speech sample.
DECIMAL_RAW = "ಕಾಗದ ಒಟ್ಟು ತೂಕ ಹನ್ನೆರಡು ಪಾಯಿಂಟ್ ಐದು ಕೆ ಜಿ ಚೀಲದ ತೂಕ ಅರ್ಧ ಕೆ ಜಿ ದರ ಹದಿನಾಲ್ಕು ರೂಪಾಯಿ ಪ್ರತಿ ಕೆ ಜಿ"
CORRECTION_RAW = "ಕಬ್ಬಿಣ ಒಟ್ಟು ತೂಕ ಇಪ್ಪತ್ತೈದು ಕೆ ಜಿ ಚೀಲದ ತೂಕ ಎರಡು ಕೆ ಜಿ ದರ ಹದಿನೈದು ರೂಪಾಯಿ ಪ್ರತಿ ಕೆ ಜಿ ಅಲ್ಲ ದರ ಐವತ್ತು ರೂಪಾಯಿ ಪ್ರತಿ ಕೆ ಜಿ"


class LiveTranscriptRepairTests(unittest.TestCase):
    def test_cached_synthetic_decimal_transcript_preserves_source_evidence(self):
        draft = domain.create_draft(DECIMAL_RAW, "kn-IN", "gnani")
        self.assertTrue(draft["can_confirm"], draft["issues"])
        self.assertEqual(draft["computed"], {"net_kg": "12", "total_inr": "168.00"})
        self.assertEqual(draft["fields"]["gross_kg"], "12.5")
        self.assertEqual(draft["transcript"], DECIMAL_RAW)
        for item in draft["evidence"]:
            self.assertEqual(item["raw"], DECIMAL_RAW[item["start"]:item["end"]])
        self.assertTrue(any("ಪಾಯಿಂಟ್" in item["raw"] for item in draft["evidence"]))
        self.assertTrue(any("ಕೆ ಜಿ" in item["raw"] for item in draft["evidence"]))

    def test_split_unit_clear_record(self):
        draft = domain.create_draft("ಕಾಗದ ಒಟ್ಟು ತೂಕ ಇಪ್ಪತ್ತೈದು ಕೆ ಜಿ ಚೀಲದ ತೂಕ ಎರಡು ಕೆ ಜಿ ದರ ಇಪ್ಪತ್ತು ರೂಪಾಯಿ ಪ್ರತಿ ಕೆ ಜಿ")
        self.assertTrue(draft["can_confirm"], draft["issues"])
        self.assertEqual(draft["computed"], {"net_kg": "23", "total_inr": "460.00"})

    def test_cached_correction_keeps_both_values_and_requires_explicit_review(self):
        draft = domain.create_draft(CORRECTION_RAW, "kn-IN", "gnani")
        self.assertFalse(draft["can_confirm"])
        self.assertEqual([e["value"] for e in draft["evidence"] if e["field"] == "rate_inr_per_kg"], ["15", "50"])
        self.assertIsNone(draft["fields"]["rate_inr_per_kg"])
        self.assertEqual(draft["computed"], {"net_kg": "23", "total_inr": None})
        with self.assertRaises(ValueError):
            domain.confirm(draft, 1, True)
        revised = domain.revise(draft, 1, "rate_inr_per_kg", "50", "Checked final intended rate")
        self.assertFalse(revised["can_confirm"])
        reviewed = domain.resolve_review(revised, 2, "Reviewed both rate values and selected the final intended rate")
        self.assertTrue(reviewed["can_confirm"], reviewed["issues"])
        self.assertEqual(reviewed["computed"]["total_inr"], "1150.00")

    def test_explicit_spoken_decimal_forms(self):
        cases = {
            "twelve point five": "12.5", "ಹನ್ನೆರಡು ಪಾಯಿಂಟ್ ಐದು": "12.5",
            "ಹನ್ನೆರಡು ದಶಮಾಂಶ ಐದು": "12.5", "zero point zero five": "0.05",
            "ಸೊನ್ನೆ ಪಾಯಿಂಟ್ ಸೊನ್ನೆ ಐದು": "0.05", "12 point 05": "12.05",
            "೧೨ ಪಾಯಿಂಟ್ ೦ ಐದು": "12.05", "twenty-one point five": "21.5",
            "one point zero zero one": "1.001", "12 point 5 zero 5": "12.505",
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(domain.parse_number(text), Decimal(expected))

    def test_fraction_requires_one_to_three_individual_digits(self):
        for text in ("one point fifteen", "one point twenty five", "ಒಂದು ಪಾಯಿಂಟ್ ಹದಿನೈದು",
                     "one point half", "half point five", "one and a half point five",
                     "one point zero zero zero one", "one point 0001", "one point",
                     "one point five point five", "one point +5", "one point - five"):
            with self.subTest(text=text):
                self.assertIsNone(domain.parse_number(text))

    def test_decimal_support_cannot_hide_negative_or_subtraction_signs(self):
        for text in ("- twelve point five", "− twelve point five", "fifty - five point five",
                     "- twenty-one point five", "fifty--five point five", "100000 point one"):
            with self.subTest(text=text):
                self.assertIsNone(domain.parse_number(text))

    def test_decimal_rate_still_requires_explicit_rate_unit(self):
        draft = domain.create_draft("paper net twelve point five kg rate fourteen point five")
        self.assertFalse(draft["can_confirm"])

    def test_split_alias_does_not_accept_a_different_unit(self):
        draft = domain.create_draft("ಕಾಗದ net twelve point five ಕೆ ಗೆ rate fourteen per kg")
        self.assertFalse(draft["can_confirm"])


if __name__ == "__main__":
    unittest.main()
