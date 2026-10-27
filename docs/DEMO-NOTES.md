# TaulSaathi demo

The 60-second, 1920×1080 video combines captures from the working local app with English explanations. It is an edited agent walkthrough, not a continuous recording or a user study.

At 0–11 seconds, the app uses a real Gnani Prisma request on generated Kannada audio describing a fictional paper transaction. The unchanged transcript produces gross 25 kg, tare 2 kg, net 23 kg and ₹20/kg: ₹460. At 42–55.6 seconds, the actual returned 13.6-second Timbre readback plays over the matching paper record. The final record was confirmed and exported with speech and readback provenance.

The middle sequence separately uses a **typed synthetic** iron example to demonstrate conflicting rates, explicit field correction, whole-transcript review, exact-revision confirmation, and invalidation after a new edit. Its ₹345 and ₹368 totals belong to that separate example.

## Files

- `../media/TaulSaathi-demo.mp4`: final 60-second video.
- `../media/live-preview.png`: actual app with the successful live speech badge and confirmed ₹460 record.
- `TaulSaathi-demo-source.zip`: editable HyperFrames project, compositions, media and source documentation; no credentials, browser profile or runtime caches.
- `TaulSaathi-demo-contact-sheet-1.jpg` and `TaulSaathi-demo-contact-sheet-2.jpg`: reviewed scene frames.
- `validation/live-ui-clear-transcription.json`: actual Prisma response, request ID and source-audio hash.
- `validation/live-ui-confirmed-receipt.json`: actual confirmed receipt, including `speech_evidence` and `readback_evidence`.
- `validation/live-ui-readback.wav`: actual returned 24 kHz PCM readback.
- `validation/live-ui-capture.json`: capture observations and provenance.

## Validation and limits

The HyperFrames check passed the 60-second composition: no runtime, layout, contrast or craft errors. One timeline-density warning is retained because all nine explanation groups intentionally share one caption track. Scene and phone-width review sheets were inspected before rendering. Five decoded MP4 frames at 2, 14.5, 33, 49.5 and 58.5 seconds were inspected afterward. FFprobe verified H.264 1920×1080, 30 fps, AAC audio and exactly 60.000 seconds. The final file is 3,551,928 bytes. Audio peak measured −1.1 dBFS; no native-speaker listening was performed.

The upload input is generated Kannada speech and a fictional transaction. It does not establish accuracy on spontaneous human speech, dialects, real phone calls, real shops or noisy field recordings. Native-speaker listening, human-speaker tests and target-user validation remain pending. No testimonials or field-impact results are implied. No payment was executed. No contest entry, public post or external publication was made by this video workflow.

The audio was checked for a valid WAV stream and timing; it was not assessed by a native Kannada listener. There is no added music or narration. The actual readback is the only soundtrack.

To edit the source project, open its folder with HyperFrames. The project pins CLI 0.8.185. Run `npx --yes hyperframes@0.8.185 check`, preview it with `npx --yes hyperframes@0.8.185 preview --background`, then render with `npx --yes hyperframes@0.8.185 render --quality delivery --fps 30 --output demo.mp4`.
