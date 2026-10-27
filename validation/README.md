# Published validation evidence

All transactions are fictional. The audio here is generated speech, with separately declared simulated-noise variants. There are no human participants or undisclosed consent records.

- `live-ui-clear-transcription.json`: actual Prisma response for the paper transaction.
- `live-ui-confirmed-receipt.json`: actual operator-confirmed ₹460 receipt with source and readback evidence.
- `live-ui-readback.wav`: actual returned 13.6-second Timbre audio.
- `live-ui-capture.json`: agent capture observations.
- `live-synthetic-benchmark.json`: four development STT responses, including the initial parser failures.
- `cached-parser-reanalysis.json`: unchanged transcript reanalysis after the explicit split-unit and decimal fix.
- `acoustic-clips/`: generated decimal/correction audio and simulated 10 dB white-noise variants, with manifest metadata.
- `agent-walkthrough.json`: scripted local workflow results, not customer feedback.
- `LIVE-RESULTS.md`: exact conclusions and limits.

Machine-local paths in published JSON metadata were replaced by portable repository paths or `LOCAL_PATH_REDACTED/<filename>`. Transcripts, source hashes, request IDs, computed fields and outcomes were preserved. These development clips helped refine the parser and are not a held-out accuracy benchmark. Provider credit debit was not measured.
