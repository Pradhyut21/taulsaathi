# Verification performed

Initial checks began 22 October 2026; subsequent live results carry their exact UTC timestamps in the JSON reports. Python 3.13, Windows. The API client identification issue was fixed and actual STT/TTS calls now succeed on synthetic Kannada audio. Billed credit usage is unknown.

- 110 offline unit tests passed: domain/state, adversarial, observed-transcript repairs, mocked Gnani contracts, real-localhost HTTP workflow and mocked live-runner checks.
- 50 authored text regression fixtures passed across the original and adversarial sets. Fifteen supported records matched expected fields/arithmetic; 35 problematic cases remained blocked.
- JavaScript parsed successfully with `node --check static/app.js`.

- 16 browser scenario checks passed in Chrome 155 using the local app, including current-revision confirmation/export, correction invalidation, transcript/language mismatch, and synthetic-to-typed provenance. Desktop 1440×1600 and mobile 390px screenshots were visually checked; no overflow or uncaught JavaScript exception was observed. See `BROWSER-QA.md`.
- Nine further scripted agent workflow tasks passed over real local HTTP, including the corrected adversarial cases. See `../validation/agent-walkthrough.json`. No buyer/seller interview or human comprehension result is claimed.

Four actual STT operations on generated Kannada clean/noise development clips returned transcripts. Their initial parser failures and unchanged raw responses are preserved; cached reanalysis after the unit/decimal fix gives two correct decimal records and keeps both correction records blocked. This small same-provider synthetic loop is not a natural-speaker or held-out accuracy benchmark. See `../validation/`.

The complete browser flow also succeeded on one generated Kannada transaction: actual Prisma transcription, unchanged transcript parsed into 23 kg at ₹20/kg (₹460.00), actual 13.6-second Timbre readback, then revision-1 confirmation and JSON export. The matching returned audio and receipt provenance are in `../validation/live-ui-readback.wav` and `../validation/live-ui-confirmed-receipt.json`.

The offline checks do not measure Kannada ASR accuracy. The live development checks do not establish spontaneous speech coverage, human comprehension, real telephony robustness or field impact. Text fixture results remain explicitly labelled in `evaluation/text-results.json`.

To reproduce, run from the app directory:

```powershell
python -m unittest discover -s tests -v
python evaluation/evaluate.py
node --check static/app.js
```
