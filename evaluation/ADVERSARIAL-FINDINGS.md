# Additional adversarial text validation

Thirty new authored cases were added after the initial twenty. They cover signed and dashed word numbers, alternative decimal syntax, unsupported currency/unit expressions, invisible token boundaries, unassigned symbols, mixed-script decimals, exact rounding, reordered inputs and Indic punctuation.

Two false-ready paths were found and fixed:

1. The parser replaced every ASCII hyphen with a space, so `net - fifty five kg` and `net fifty - five kg` could become positive 55 kg. Hyphens are now supported only in an attached English compound such as `fifty-five`; leading, trailing, spaced and repeated hyphens remain blocked.
2. The leftover check looked for word characters, which let isolated currency, arithmetic or cancellation symbols disappear after a valid record. Unassigned symbols now require review. A small set of prose punctuation remains allowed, including Indic danda. Currency symbols and `/ kg` inside recognized rate evidence still work.

No bad arithmetic was found in the additional supported cases. Independent expected amounts include 50.25 × 12.5 = ₹628.13 after half-up rounding, and (1.001 − 1) × 99999.999 = ₹100.00 after rounding.

`adversarial-results.json` records **30/30 passing text regressions**: eight supported records matched all expected fields and amounts, and 22 problematic cases stayed blocked. The full offline suite passed **79 tests** at this validation point. The initial twenty text fixtures were also rechecked.

These cases are not recordings. They do not measure Gnani speech accuracy, natural Kannada coverage, robustness to workshop or telephone audio, native-language quality, or feedback from actual buyers/sellers. The current bounded grammar deliberately sends unsupported phrasing for review rather than estimating confidence. Native-speaker and real-user validation remain necessary.
