"""Text-fixture checks for bounded parsing and revision safety.

These examples are authored test strings. They do not evaluate acoustic quality,
Gnani accuracy, real Kannada usage, or native-speaker comprehension.
"""

import sys
import unittest
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import domain


VALID = "paper gross fifty kg tare two kg rate thirty rupees per kg"


class NumberGrammarTests(unittest.TestCase):
    def test_explicit_supported_numbers(self):
        cases = {
            "೦": "0", "೫೨.೫": "52.5", "fifty-five": "55", "twenty one": "21",
            "half": "0.5", "one and a half": "1.5", "two and a half": "2.5",
            "ಐವತ್ತು": "50", "ಎರಡು": "2", "ಇಪ್ಪತ್ತೈದು": "25", "ಅರ್ಧ": "0.5",
            "ಒಂದೂವರೆ": "1.5", "ಎರಡೂವರೆ": "2.5", "0.125": "0.125",
        }
        for text, value in cases.items():
            with self.subTest(text=text):
                self.assertEqual(domain.parse_number(text), Decimal(value))

    def test_unsupported_compounds_never_guess(self):
        for text in ("one hundred", "a few", "approximately fifty", "fifty or sixty",
                     "50,000", "-5", "NaN", "Infinity", "0.0001", "100001", ""):
            with self.subTest(text=text):
                self.assertIsNone(domain.parse_number(text))


class ReceiptParsingTests(unittest.TestCase):
    def test_english_gross_tare_and_exact_decimal_arithmetic(self):
        draft = domain.create_draft(VALID, "en-IN")
        self.assertEqual(draft["fields"], {
            "material": "paper", "gross_kg": "50", "tare_kg": "2",
            "net_kg": None, "rate_inr_per_kg": "30",
        })
        self.assertEqual(draft["computed"], {"net_kg": "48", "total_inr": "1440.00"})
        self.assertEqual(draft["issues"], [])
        self.assertTrue(draft["can_confirm"])

    def test_kannada_digits_and_labels_are_preserved_as_evidence(self):
        text = "ಕಾಗದ ಒಟ್ಟು ತೂಕ ೫೨.೫ ಕೆಜಿ ಚೀಲದ ತೂಕ ೨.೫ ಕೆಜಿ ದರ ೩೪ ರೂಪಾಯಿ ಪ್ರತಿ ಕೆಜಿ"
        draft = domain.create_draft(text)
        self.assertTrue(draft["can_confirm"], draft["issues"])
        self.assertEqual(draft["computed"], {"net_kg": "50", "total_inr": "1700.00"})
        self.assertEqual(draft["transcript"], text)
        for item in draft["evidence"]:
            self.assertEqual(item["raw"], text[item["start"]:item["end"]])

    def test_supported_kannada_words_and_english_labels(self):
        draft = domain.create_draft("ಕಾಗದ gross ಐವತ್ತು kg tare ಎರಡು kg rate ಮೂವತ್ತು per kg")
        self.assertTrue(draft["can_confirm"], draft["issues"])
        self.assertEqual(draft["computed"]["total_inr"], "1440.00")

    def test_decimal_net_only_and_round_half_up(self):
        draft = domain.create_draft("copper net 0.5 kg rate 0.01 rupees per kg", "en-IN")
        self.assertTrue(draft["can_confirm"], draft["issues"])
        self.assertEqual(draft["computed"]["total_inr"], "0.01")
        other = domain.create_draft("plastic net 0.1 kg rate 0.2 per kg")
        self.assertEqual(other["computed"]["total_inr"], "0.02")

    def test_equal_repetition_can_remain_a_single_value(self):
        draft = domain.create_draft("paper net fifty kg net fifty kg rate thirty per kg")
        self.assertTrue(draft["can_confirm"], draft["issues"])
        self.assertEqual(draft["fields"]["net_kg"], "50")

    def test_conflicting_repetition_stays_blocked_after_third_value(self):
        for repeated in ("net fifty kg net fifteen kg", "net fifty kg net fifteen kg net fifty kg"):
            with self.subTest(repeated=repeated):
                draft = domain.create_draft("paper " + repeated + " rate thirty per kg")
                self.assertFalse(draft["can_confirm"])
                self.assertIsNone(draft["fields"]["net_kg"])

    def test_missing_labels_units_or_values_block(self):
        for text in (
            "paper fifty kg thirty rupees per kg",
            "paper net fifty rate thirty per kg",
            "paper net fifty kg rate thirty",
            "paper gross fifty kg rate thirty per kg",
            "paper tare two kg rate thirty per kg",
            "paper gross fifty kg net forty eight kg rate thirty per kg",
            "paper net one hundred kg rate thirty per kg",
        ):
            with self.subTest(text=text):
                self.assertFalse(domain.create_draft(text)["can_confirm"])

    def test_conflicting_net_gross_and_tare_block(self):
        draft = domain.create_draft(VALID + " net forty kg")
        self.assertFalse(draft["can_confirm"])
        self.assertTrue(any("differs" in issue for issue in draft["issues"]))

    def test_invalid_arithmetic_and_zero_rate_block(self):
        for text in (
            "paper gross two kg tare fifty kg rate thirty per kg",
            "paper gross two kg tare two kg rate thirty per kg",
            "paper net zero kg rate thirty per kg",
            "paper net fifty kg rate zero per kg",
        ):
            with self.subTest(text=text):
                self.assertFalse(domain.create_draft(text)["can_confirm"])

    def test_multiple_materials_and_unknown_materials_block(self):
        for material in ("paper and copper", "steel", "unknown material"):
            with self.subTest(material=material):
                self.assertFalse(domain.create_draft(material + " net fifty kg rate thirty per kg")["can_confirm"])

    def test_wrong_units_cannot_be_silently_converted(self):
        for text in (
            "paper net fifty grams rate thirty per kg",
            "paper net fifty kg rate thirty per gram",
            "paper net fifty kg rate thirty dollars per kg",
            "paper net fifty tonnes rate thirty per kg",
        ):
            with self.subTest(text=text):
                self.assertFalse(domain.create_draft(text)["can_confirm"])

    def test_negation_correction_and_unassigned_digits_block(self):
        for suffix in (
            "; no, not that", "; sorry correction", "; ಐವತ್ತು ಅಲ್ಲ", "; ಬದಲು", "; 25",
            "; fifteen", "; ೨೫", "; total 1700 rupees",
        ):
            with self.subTest(suffix=suffix):
                self.assertFalse(domain.create_draft(VALID + suffix)["can_confirm"])

    def test_cancellation_or_negative_contractions_block_even_after_separator(self):
        for suffix in (
            "; cancel this receipt", ", don't confirm", "; do not save", "; ರದ್ದು", "; ಬೇಡ",
        ):
            with self.subTest(suffix=suffix):
                self.assertFalse(domain.create_draft(VALID + suffix)["can_confirm"], suffix)

    def test_unassigned_fraction_words_block(self):
        for suffix in ("; half kg", "; ಅರ್ಧ ಕೆಜಿ"):
            with self.subTest(suffix=suffix):
                self.assertFalse(domain.create_draft(VALID + suffix)["can_confirm"], suffix)

    def test_contradictory_units_outside_field_span_block(self):
        draft = domain.create_draft(VALID + "; weights actually in grams")
        self.assertFalse(draft["can_confirm"])

    def test_readback_includes_the_gross_and_tare_inputs_used_for_net(self):
        expected = {
            "en-IN": ("Gross weight five two point five", "Tare weight two point five",
                      "Net weight five zero", "Rate three four", "Total one seven zero zero point zero zero"),
            "kn-IN": ("ಒಟ್ಟು ತೂಕ ಐದು ಎರಡು ದಶಮಾಂಶ ಐದು", "ಚೀಲದ ತೂಕ ಎರಡು ದಶಮಾಂಶ ಐದು",
                      "ನಿವ್ವಳ ತೂಕ ಐದು ಸೊನ್ನೆ", "ಪ್ರತಿ ಕಿಲೋಗ್ರಾಂಗೆ ಮೂರು ನಾಲ್ಕು",
                      "ಒಟ್ಟು ಒಂದು ಏಳು ಸೊನ್ನೆ ಸೊನ್ನೆ ದಶಮಾಂಶ ಸೊನ್ನೆ ಸೊನ್ನೆ"),
        }
        for language, phrases in expected.items():
            with self.subTest(language=language):
                draft = domain.create_draft("paper gross 52.5 kg tare 2.5 kg rate 34 per kg", language)
                for phrase in phrases:
                    self.assertIn(phrase, draft["readback_text"])


class RevisionSafetyTests(unittest.TestCase):
    def test_confirmation_requires_boolean_true_and_clean_draft(self):
        draft = domain.create_draft(VALID)
        for value in (False, "true", 1, None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                domain.confirm(draft, 1, value)
        dirty = domain.create_draft(VALID + "; fifteen")
        with self.assertRaises(ValueError):
            domain.confirm(dirty, 1, True)

    def test_stale_edit_review_and_confirmation_are_rejected(self):
        draft = domain.create_draft(VALID)
        updated = domain.revise(draft, 1, "rate_inr_per_kg", "35", "Checked current rate")
        self.assertEqual(draft["revision"], 1)
        self.assertEqual(draft["fields"]["rate_inr_per_kg"], "30")
        with self.assertRaises(ValueError):
            domain.confirm(updated, 1, True)
        with self.assertRaises(ValueError):
            domain.revise(updated, 1, "tare_kg", "3", "Checked bag weight")
        with self.assertRaises(ValueError):
            domain.resolve_review(updated, 1, "Checked source transcript")

    def test_revised_receipt_must_be_confirmed_again_and_changes_digest(self):
        confirmed = domain.confirm(domain.create_draft(VALID), 1, True)
        updated = domain.revise(confirmed, 1, "rate_inr_per_kg", "35", "Checked current rate")
        self.assertEqual(updated["status"], "draft")
        self.assertEqual(updated["computed"]["total_inr"], "1680.00")
        self.assertNotIn("digest", updated)
        reconfirmed = domain.confirm(updated, 2, True)
        self.assertNotEqual(confirmed["digest"], reconfirmed["digest"])
        self.assertEqual(confirmed["computed"]["total_inr"], "1440.00")

    def test_reviewing_confirmed_draft_invalidates_old_digest(self):
        confirmed = domain.confirm(domain.create_draft(VALID), 1, True)
        reviewed = domain.resolve_review(confirmed, 1, "Checked source transcript")
        self.assertEqual(reviewed["status"], "draft")
        self.assertEqual(reviewed["revision"], 2)
        self.assertNotIn("digest", reviewed)

    def test_confirmation_is_idempotent(self):
        confirmed = domain.confirm(domain.create_draft(VALID), 1, True)
        again = domain.confirm(confirmed, 1, True)
        self.assertEqual(again, confirmed)
        self.assertIsNot(again, confirmed)
        self.assertEqual(sum(event["action"] == "confirmed" for event in again["history"]), 1)

    def test_edit_does_not_clear_unresolved_parse_warnings(self):
        draft = domain.create_draft(VALID + "; not fifty")
        updated = domain.revise(draft, 1, "gross_kg", "50", "Checked scale display")
        self.assertFalse(updated["can_confirm"])
        self.assertTrue(updated["parse_issues"])
        reviewed = domain.resolve_review(updated, 2, "Checked full transcript and corrected intended fields")
        self.assertTrue(reviewed["can_confirm"], reviewed["issues"])
        self.assertFalse(updated["can_confirm"])

    def test_arithmetic_warning_cannot_be_cleared_with_review_only(self):
        draft = domain.create_draft(VALID + " net forty kg")
        reviewed = domain.resolve_review(draft, 1, "Checked source transcript")
        self.assertFalse(reviewed["can_confirm"])
        self.assertTrue(any("differs" in issue for issue in reviewed["issues"]))

    def test_invalid_manual_values_rejected(self):
        draft = domain.create_draft(VALID)
        for value in ("-1", "NaN", "Infinity", "100001", "0.0001", True):
            with self.subTest(value=value), self.assertRaises(ValueError):
                domain.revise(draft, 1, "gross_kg", value, "Checked scale display")
        with self.assertRaises(ValueError):
            domain.revise(draft, 1, "material", "unknown", "Checked material")


if __name__ == "__main__":
    unittest.main()
