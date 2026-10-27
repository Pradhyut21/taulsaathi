"""Run authored text regressions. No audio or network is used.

Usage from the app directory: python evaluation/evaluate.py
Optional: python evaluation/evaluate.py --output evaluation/text-results.json
"""

import argparse
import json
import sys
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_ROOT))
import domain


def evaluate(fixtures_path):
    fixtures = json.loads(fixtures_path.read_text(encoding="utf-8"))
    results = []
    for case in fixtures["cases"]:
        draft = domain.create_draft(case["text"], case["language"], source="synthetic")
        expected = case["expected"]
        problems = []
        for key, value in expected.items():
            if draft.get(key) != value:
                problems.append({"field": key, "expected": value, "actual": draft.get(key)})
        results.append({
            "id": case["id"],
            "category": case["category"],
            "passed": not problems,
            "expected_confirmable": expected["can_confirm"],
            "actual_confirmable": draft["can_confirm"],
            "mismatches": problems,
        })
    positive = [r for r in results if r["expected_confirmable"]]
    blocking = [r for r in results if not r["expected_confirmable"]]
    return {
        "evaluation_kind": "authored_text_regression",
        "audio_evaluated": False,
        "live_gnani_evaluated": False,
        "native_speaker_reviewed": fixtures["native_speaker_reviewed"],
        "notice": "Passing these authored strings does not measure speech accuracy, noisy audio robustness, natural Kannada coverage, or user task success.",
        "fixtures": str(fixtures_path),
        "counts": {
            "total": len(results),
            "passed": sum(r["passed"] for r in results),
            "supported_receipts": len(positive),
            "supported_receipts_matching_all_expected_fields": sum(r["passed"] for r in positive),
            "blocking_cases": len(blocking),
            "blocking_cases_held_for_review": sum(not r["actual_confirmable"] for r in blocking),
            "blocking_cases_incorrectly_ready_to_confirm": sum(r["actual_confirmable"] for r in blocking),
        },
        "results": results,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", type=Path, default=Path(__file__).with_name("fixtures.json"))
    parser.add_argument("--output", type=Path, help="Optional JSON report path; no report file is written by default.")
    args = parser.parse_args()
    summary = evaluate(args.fixtures.resolve())
    rendered = json.dumps(summary, ensure_ascii=False, indent=2)
    print(rendered)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    return 0 if summary["counts"]["passed"] == summary["counts"]["total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
