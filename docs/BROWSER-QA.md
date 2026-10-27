# Browser verification

This records the initial offline browser pass. Later successful live API capture, audio, receipt and provenance are documented in `../validation/LIVE-RESULTS.md`; the no-key limit below describes this initial pass only.

Checked 22 October 2026 with local Chrome 155.0.8059.85, headless Chrome DevTools Protocol, Node 22.18.0 and the actual Python app on loopback port 8766. No browser packages or frontend dependencies were installed. An isolated profile was created under the workspace's `work/` directory. The owned test server and browser were stopped after verification.

The frontend uses local HTML/CSS/JavaScript, system font fallbacks and no external font/CDN calls. Browser JavaScript syntax check passed.

## Verified flows

Sixteen scenario checks passed against the real local server:

1. The initial page shows local mode and no configured Gnani key.
2. The synthetic Kannada scenario produces net weight 23 kg and amount ₹460.
3. Confirmation stays disabled until the current revision's review checkbox is checked.
4. Confirmed JSON export returns the expected record and amount.
5. Changing the textarea blocks the older record's export, print, confirmation and readback in the UI, and displays a new-draft instruction.
6. Restoring matching input clears the input-mismatch notice.
7. Changing the language also blocks the older record's actions.
8. An unapplied field correction blocks export in the UI.
9. Applying a rate correction changes the amount, invalidates confirmation and makes the server reject export until a new confirmation.
10. The contradictory-rate scenario creates blocking transcript warnings.
11. A field edit does not silently clear those warnings; an explicit whole-transcript review with a reason is required.
12. The corrected and reviewed conflicting scenario can then be confirmed.
13. Editing a synthetic example changes its provenance to typed input.
14. Live transcription and voice-readback buttons are disabled when no server key is configured.
15. The page has no horizontal overflow at an emulated 390 CSS-pixel mobile width.
16. No uncaught JavaScript exceptions occurred during the checked flows.

Visual inspection used actual screenshots at desktop 1440 × 1600 and mobile width 390 (full content height 2501 pixels). The empty state, confirmed Kannada record and English mobile draft were inspected with the image viewer; no clipping or horizontal overflow was observed. Final desktop preview: `../media/live-preview.png`.

## Findings corrected during QA

- Busy-button restoration originally flattened the button's label and icon structure; the original DOM children are now restored.
- Old record actions could remain available after changing the input conversation or language. The UI now blocks those actions, clears review/audio state and prompts for a new draft.
- The first test script used an insufficient wait for the correction request; the harness now waits for the new revision and completion of the request. The final run passed.

## Limits

No real Gnani call ran because no API key was available to this test session. Live ASR accuracy, native-speaker Kannada validation, TTS pronunciation, telephony performance, upload success with a real recording and upstream errors remain unverified. The existing checks validate the working local workflow, not real-world user adoption or speech accuracy.

Mobile verification was browser emulation, not a physical phone. Screen-reader and full keyboard-only testing, printed-paper layout and a multi-tab stale-edit race were not manually tested here. Server unit/integration tests are documented separately. The synthetic scenarios are illustrative; they are not recordings or real user testimonials.
