# Public snapshot verification

Checked 27 October 2026 using the copied public source tree.

- Full offline suite: **110 tests passed**.
- Authored parser fixtures: **20 + 30 cases passed**; no speech calls were made by these commands.
- Browser JavaScript: `node --check static/app.js` passed.
- Local Markdown file links resolved.
- Privacy/secret-pattern scan passed for the selected text files. Machine-local path metadata in two saved fixture reports was replaced with portable repository paths. Transcripts, evidence hashes and API outcomes were preserved.
- App, adapter, parser and browser source files match the working deliverable byte for byte.

The first full test run encountered one Windows localhost connection abort (`WinError 10053`) in the cross-origin/foreign-host denial test. The isolated 11-test HTTP group then passed, followed by a full 110-test pass. No source changes were made to produce that result. This records the transient failure rather than hiding it.

The earlier browser QA document describes the initial no-key session. Later successful generated-audio integration is documented in `../validation/LIVE-RESULTS.md` and the matching raw receipt and response files. Neither session is a human user study.
