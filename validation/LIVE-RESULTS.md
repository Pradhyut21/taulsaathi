# Live results and exact claim limits

**Both Gnani speech services and the complete local receipt flow have now succeeded on generated Kannada audio.** The earlier access-failure report is historical, before the client-identification fix.

## Actual UI flow

A 6.24-second fictional Kannada transaction was generated with Timbre, then uploaded through the app to Prisma. The returned transcript was used unchanged as the draft source. It yielded paper, gross25kg, tare2kg, rate₹20/kg, net23kg and amount₹460.00. No field corrections were needed for that clip. The app requested an actual Timbre readback, played/decoded13.6seconds, and confirmed/exported revision1.

The single STT operation measured491ms inside the adapter. This is one observation, not a latency benchmark, guarantee or the vendor's streaming-latency figure. The generated input/readback are not human speech.

Evidence: `live-ui-clear-transcription.json`, `live-ui-confirmed-receipt.json`, `live-ui-capture.json`, and `live-integration-summary.json`. The receipt includes source audio hash, request details, raw transcript, current-revision readback metadata and the reviewed field digest. Those do not authenticate a person, weighing instrument or payment.

## Four development clips

| Input | Actual API response | Initial parser | After the explicit parser repair, using the unchanged cached response |
|---|---|---|---|
| Generated Kannada decimal transaction | Transcript returned | Blocked splitunit/decimal phrase | 12kg net × ₹14/kg = ₹168.00 |
| Same decimal audio with simulated10dB white noise | Transcript returned | Blocked splitunit/decimal phrase | 12kg net × ₹14/kg = ₹168.00 |
| Generated Kannada15→50 correction | Transcript returned | Blocked | Still blocked; both rates retained, awaiting explicit operator review |
| Same correction audio with simulated10dB white noise | Transcript returned | Blocked | Still blocked; both rates retained, awaiting explicit operator review |

The original API report and parser source hash are preserved in `live-synthetic-benchmark.json`. `cached-parser-reanalysis.json` records the new source hash and the unchanged responses. **These samples were used to refine the parser; they are not held-out tests.** The noise is seeded Gaussian white noise, not an actual workshop or telephone channel.

## Software and usability checks

The offline suite passes110tests, and the original authored fixture sets pass50cases. Nine additional agent workflow tasks passed over local HTTP. Real browser captures show the live transcription, readback, confirmation and receipt export. This is agent testing, not feedback from a scrap buyer or seller. A later participant session can use `../docs/USER-FEEDBACK-KIT.md`.

## Claims supported now

- “Uses actual Gnani Prisma and Timbre API calls for a Kannada receipt workflow.”
- “Keeps conflicts and unsupported speech visible; edits invalidate confirmation.”
- “Includes raw evidence, hashes and reproducible small synthetic development cases.”

Claims of natural Kannada accuracy, all-language coverage, real telephony performance, field adoption, time savings, guaranteed safety, uniqueness or winning probability remain unsupported. Provider credit debit was not measured. No public post, registration or submission was performed.
