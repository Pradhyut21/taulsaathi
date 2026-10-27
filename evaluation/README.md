# Evaluation status and recording protocol

Later actual speech-service checks are documented separately in `../validation/LIVE-RESULTS.md`. They use generated Kannada audio and simulated noise, not human-speaker or held-out validation. `run_live.py` supports explicit future audio checks; the fixture harness below remains offline.

`fixtures.json` contains 20 authored text examples for the bounded parser. No audio is included, no live API was tested by this harness, and the Kannada examples have not been reviewed by a native speaker. This is a regression check, not a speech benchmark. `audio_manifest.csv` intentionally contains only a header: there are no fabricated recordings, participants, consent records, or measured speech scores.

From the app directory:

```powershell
python evaluation/evaluate.py
python evaluation/evaluate.py --output evaluation/text-results.json
```

The command uses Python's standard library and does not contact Gnani or consume credits. It checks seven supported receipts against their full expected fields and computed amounts, and checks that thirteen problematic examples remain blocked. It exits with status 1 if any fixture fails. Report its output as “authored text regressions passed,” with raw counts. Do not present it as Kannada ASR accuracy, noisy-audio robustness, native-language quality, or user task completion.

An additional 30-case adversarial set is stored separately in `adversarial-fixtures.json`. Run it with:

```powershell
python evaluation/evaluate.py --fixtures evaluation/adversarial-fixtures.json --output evaluation/adversarial-results.json
```

Read `ADVERSARIAL-FINDINGS.md` for the two false-ready paths found and fixed. `adversarial-results.json` is a saved text-regression result, with acoustic and live-Gnani evaluation explicitly marked false.

## Real recording protocol

1. Start with a small pilot in Kannada + English mixing, then aim for at least 60 original short utterances from at least six speakers if users, time and available credits permit. Ask a native Kannada speaker to review prompts, number forms, field labels and readbacks. A prototype this small cannot establish accuracy for the general population.
2. Obtain permission for evaluation recordings. Obtain separate permission before including a person's voice in the public contest video. Use anonymous speaker IDs and fictional names, if names are needed at all. Record the permissions in the manifest; do not assume they exist.
3. Ask people to describe transactions naturally, including gross/tare, net-only, decimals, rates, repeated values, negation, corrections and missing information. Do not let every participant read the same handful of examples. Have a person check each final intended record against the recording and scale/transaction scenario. Store the final intent separately from the literal transcript.
4. Split by speaker into development and held-out evaluation groups before refining the parser. Keep every original recording and all its derived variants in the same split. A noisy copy of a development recording cannot become an independent test example.
5. Record clean speech and real local environmental noise as separate conditions. Keep original WAVs. If creating seeded noise/8 kHz variants, label them `simulated_noise` or `simulated_telephony`, and preserve the transformation settings. Claim real telephony performance only after testing real consented phone-channel recordings, labelled `real_telephony`.
6. Freeze the held-out set. Run Prisma once per clip where practical and cache its transcript and timing. Track actual credit consumption from the console before scaling the collection. Avoid automatic retries after lost API responses. Use the same transcript for the unvalidated baseline and the validated application to isolate the contribution of repair and confirmation.
7. Evaluate the initial extraction and the final user-confirmed record separately. If a confirmation turn is allowed, use the same rule and turn limit for all examples. Record questions per completed record, retries, cancellations and end-to-end completion time.

`path` in the manifest should identify a real recording once collected, relative to the app directory or as an absolute local path. `condition` distinguishes `clean`, `real_environment_noise`, `simulated_noise`, `simulated_telephony`, and `real_telephony`; `split` identifies development or held-out evaluation. Blank fields mean unknown. A claimed permission should be explicitly recorded as `yes`. `gold_final_intent` can distinguish a valid receipt from `cancel` or `clarification_required`.

## Metrics to report once recordings exist

| Metric | Definition |
|---|---|
| Complete record accuracy | Correct material, all required input values and computed payable amount, divided by evaluable records. |
| Critical field accuracy | Exact gross/tare/net/rate/amount correctness, reported separately; do not use fuzzy numeric matching. |
| Incorrect ready-to-confirm records | Count of examples made ready despite an unresolved material error or cancellation intent. |
| Correction success | Final corrected intended value replaces the earlier value, among recordings containing a correction. |
| Review burden | Clarification questions, manual corrections, retries and cancellations per completed record. |
| Task completion time | Recording start to correct saved receipt, with median and p95 where the sample count supports it. |
| ASR WER/CER | Secondary diagnostic on human transcripts with documented normalization; preserve number differences and negation. |

Always include numerators, denominators and condition/speaker splits. Report before and after confirmation separately. A correct subtotal does not prove the weights or rate were heard correctly; a persistent wrong number can remain arithmetically consistent. Do not publish target percentages as achieved results.
