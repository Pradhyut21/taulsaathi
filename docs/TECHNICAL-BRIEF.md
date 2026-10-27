# TaulSaathi
### Checked Kannada + English voice receipts for a small scrap transaction

Technical submission narrative · 23 October 2026 · Two-page draft

**A correctly calculated amount can still use a misheard rate.** TaulSaathi turns a short weighing conversation into an inspectable draft, exposes critical numbers, and requires confirmation of the exact current revision before export. Its contribution is a small, auditable completion workflow around Gnani speech.

## Page 1 — Problem, contribution and implementation

**User and task.** A scrap buyer and seller need a record of one material, its net weight, the agreed rupee-per-kilogram rate and the amount due. For gross 12.5 kg, bag/tare 0.5 kg and ₹14/kg, the correct result is 12 kg and ₹168.00. If speech recognition instead returns a plausible ₹40 rate, arithmetic alone cannot discover the mistake. The product hypothesis is that visible evidence, spoken review and explicit correction make this task easier to check. Actual user benefit remains to be established.

**Prior art is acknowledged.** Scrap POS, gross/tare slips, digital transaction records and voice ledgers already exist: examples include [Kabadiwalla Connect](https://www.kabadiwallaconnect.in/), [WeighDATA](https://weighdata.in/) and [VoiceKhata](https://voicekhata.com/). Selective confirmation is established speech research, including [Komatani and Kawahara, 2000](https://www.isca-archive.org/icslp_2000/komatani00_icslp.html). TaulSaathi claims a concrete implementation and a testable workflow, without claiming the first voice receipt, an empty market, an exclusive invention or knowledge of other contest entries.

**Engineering contribution.** The implemented combination has five parts:

1. A bounded Kannada/English parser proposes typed fields with source phrases and offsets. Unknowns stay visible. Units, conflicting values, unsupported words/symbols, negation and correction cues can block confirmation.
2. `Decimal` arithmetic derives net = gross − tare and amount = net × rate, with explicit two-decimal half-up rounding. Missing tare is not assumed zero; a stated net must agree with supplied gross and tare.
3. Corrections are explicit operator edits with reasons. Transcript warnings require a separate recorded review action; structural arithmetic errors remain blocking. The prototype does not automatically understand arbitrary spoken self-corrections.
4. Each change creates a new revision and invalidates the prior confirmation and digest. Confirmation names that revision. Readback requests also reject stale revisions, including an edit during an in-flight synthesis request.
5. The server binds a live transcript label to its returned text, language and server-issued token. Edited text is labelled typed. Per-revision audio caching reduces repeated readback generation within the session.

**Gnani's role.** Prisma v2.5 supplies hosted speech-to-text; Timbre v2.5 supplies optional Kannada readback using voice Saanvi, with Kaveri for English. Critical gross/tare/net/rate/amount values are spoken when applicable. Numeric values are spelled digit by digit; comprehension and pronunciation still need native-speaker evaluation. The current app accepts short WAV uploads rather than requiring a real-time conversational stack. [Gnani STT documentation](https://docs.gnani.ai/api/STT/speech-to-text), [TTS documentation](https://docs.gnani.ai/api/TTS/tts-inference).

**Integration findings.** Default Python-client requests returned HTTP 403 with Cloudflare 1010. Keyless probes isolated this from API-key authentication; the truthful `TaulSaathi/0.1 (Gnani API integration; Python urllib)` identifier reached normal authentication, and authenticated STT/TTS then succeeded on synthetic inputs. [Cloudflare documents 1010 as client-signature blocking](https://developers.cloudflare.com/support/troubleshooting/http-status-codes/cloudflare-1xxx-errors/error-1010/). A returned TTS WAV declared 2,147,483,647 frames despite approximately 9.6 seconds of PCM. The adapter now canonicalizes recognized streaming-length sentinels without changing PCM, while rejecting ordinary truncated containers. Regression tests cover both paths; these are integration fixes, not new model capabilities.

**Implementation scope.** Python standard library plus buildless HTML/CSS/JavaScript; no new ASR training, LLM, GPU or third-party runtime package. The loopback server keeps drafts in session memory and exports confirmed JSON. Scope is six materials, kilograms, INR/kg, selected Kannada/English number forms, and net-only or gross-minus-tare records. Arbitrary Kannada sentences/compounds, grams/tonnes conversion, multiple line items, tax invoices and payments are outside the prototype.

---

## Page 2 — Evidence, limits and participant disclosure

**What the tests establish.** All 110 offline tests pass, exercising parser behavior, exact arithmetic, warning persistence, correction history, current-revision confirmation/export, live-transcript provenance, stale readback rejection and mocked API contracts. Fifty authored text fixtures comprise 15 supported records with expected fields/amounts and 35 cases that should stay blocked. Additional adversarial testing found and fixed two false-ready paths: a minus in a word-number phrase could be lost, and leftover money/math/cancel symbols could disappear. Inputs and outcomes are preserved in `taulsaathi/VERIFICATION.md` and the saved JSON reports; test strings are not an acoustic benchmark.

**How to interpret live evidence.** The complete browser flow succeeded on one generated Kannada transaction: actual Prisma transcription, unchanged transcript parsed to 23 kg × ₹20/kg = ₹460.00, actual 13.6-second Timbre readback, then current-revision confirmation and export. Four further clean/simulated-noise development clips informed parser repairs; raw responses and before/after outcomes are preserved. These TTS-generated fictional inputs demonstrate integration on those inputs. They do not establish spontaneous human Kannada, field code mixing, workshop noise, real telephony or unseen-speaker performance. Earlier access failures remain historical evidence. The small synthetic check supports no population accuracy claim.

**Why final records matter alongside WER.** A transcript may differ in harmless wording yet preserve the task, or contain just one wrong number that changes the amount substantially. [SLURP](https://aclanthology.org/2020.emnlp-main.588/) motivates semantic/entity evaluation; [MASSIVE](https://arxiv.org/abs/2204.08582) provides multilingual intent/slot and exact-match evaluation patterns. For original recordings, report exact critical-field accuracy, complete-record correctness, wrong-ready-to-confirm cases, correction success, review burden and completion time. Report draft and post-review results separately. WER/CER remain useful diagnostics when a human-verified verbatim reference exists.

| Defensible wording | Wording unsupported by current evidence |
|---|---|
| “A bounded Kannada/English prototype with Gnani speech integration and operator-reviewed receipt drafts.” | “Understands every Kannada conversation” or “automatically resolves every correction.” |
| “All cases in the named authored text sets passed on this version; counts and inputs are published.” | “100% Kannada speech accuracy,” “zero errors,” or a universal reliability guarantee. |
| “The current revision must be reviewed again after an edit.” | “A tamper-proof receipt,” “verified identities,” or authenticated agreement by two people. |
| “Hosted Gnani inference was tested on the specifically documented input provenance.” | “Real-user/noisy-telephone performance” inferred from synthesized speech. |
| “The product hypothesis awaits genuine buyer/seller feedback.” | Invented users, testimonials, time savings, adoption, revenue, reach, rankings or award probability. |
| “Uses Gnani models through the documented hosted API.” | “Fully offline,” verified India-only data residency, or customer-controlled hosting without deployment evidence. |

**Practical limits.** A plausible wrong number can satisfy every rule. Operator review is an override with an audit trail, not proof that speech was understood. The digest identifies a field snapshot inside this app; it is not a digital signature, immutable ledger or proof of payment, weighing accuracy, fair pricing or identity. The app does not verify the buyer's or seller's comprehension. Records disappear when the local session ends unless exported.

**Participant and assistance disclosure — complete with true details only.**

| Required fact | Participant to complete |
|---|---|
| Entrant name(s), college/course and eligibility | ____________________ |
| Solo entry or eligible teammate | ____________________ |
| Each person's actual implementation, review and testing contributions | ____________________ |
| Repository/version and reproducible validation report | ____________________ |
| Real user sessions and native-speaker review actually completed | ____________________ |

The code and research artifacts in this workspace were developed with AI coding and research assistance. List that assistance accurately and distinguish generated implementation from work the participant personally wrote, reviewed, tested and can explain. Gnani's foundation models were not trained by the entrant. Referenced research repositories are prior art and potential tools; their existence is not evidence that their code or datasets were used in this prototype.
