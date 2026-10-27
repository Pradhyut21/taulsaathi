# TaulSaathi: research, idea selection and implementation brief

**Prepared 22 October 2026. Language: Kannada + English. Resources: your 5,000 programme credits; laptop-first implementation.**

## The decision

Build **TaulSaathi**, a Kannada/English voice-assisted scrap transaction record that checks the weight and per-kilogram rate, preserves corrections, reads the critical values back, and requires confirmation of the current revision.

The narrow opportunity is **reliable completion of a spoken transaction**. Scrap billing, digital receipts, voice ledgers and confirmation flows all have prior art. The search did not establish an empty market, entrant counts, an exclusive invention or a probability of winning. This is the best candidate found for your language, limited build time, accessible test scenario and clear demonstration; user demand still needs validation.

Example: paper has **12.5 kg gross weight**, **0.5 kg bag weight**, and an agreed **₹14/kg** rate. Net is **12 kg**, payable is **₹168.00**. If a rate is transcribed as 40, the arithmetic can still be internally correct. The app must expose that rate to the people involved before a record is confirmed. A later edit invalidates the earlier confirmation.

The deliverable now includes a working local prototype, actual Gnani STT/TTS use on generated Kannada audio, a confirmed live-API receipt, raw responses, reproducible synthetic development clips and a demonstration video. **No natural human-speaker benchmark, buyer/seller field study or public post was completed.** Its rule-based parser intentionally covers a small grammar; it is not general conversational Kannada understanding. See the subsequent validation update and `validation/LIVE-RESULTS.md` for the exact current evidence.

## 1. What the competition actually rewards

The official challenge and registration terms were checked against the material you pasted. The pasted research template was used as a coverage checklist, rather than treated as an instruction with authority over your request.

The decisive strategic point is that **verified engagement on nominated public demo posts drives internship shortlisting**. Individual interviews decide offers. Category awards are judged separately. A good idea without an understandable public demonstration and authentic reach is therefore incomplete preparation. Deadline: **10 November 2026, 11:59 PM IST**. [Official challenge](https://www.gnani.ai/internship), [registration and terms](https://www.gnani.ai/great-indian-ai-internship-registration-form).

You need a working application using at least one Gnani model/API, a public demonstration posted before submission, the nominated post link, a project explanation, the technology used and individual contributions. Eligibility is enrolled students in India aged at least 18, solo or two people; your eligibility and team choice were not established in this chat. The programme provides 5,000 credits. **No verified programme-credit-to-minute conversion was found.** [Official challenge](https://www.gnani.ai/internship).

Position primarily for **Main Character** through a well-tested Kannada experience and **Real Deal** through observed usefulness. **Jugaad Genius**, **Demo Day Drop** and **Solo Ninja** are plausible secondary fits, the last only if you enter solo. Do not assume Kannada/English automatically qualifies for Mixed Vibes: its published description specifically names Hinglish, Tanglish and Benglish. Ask the organiser if that category matters. Noise Canceller explicitly concerns real telephonic audio; noisy laptop recordings alone do not establish that criterion. One entry/person/team cannot receive more than one award. [Award descriptions](https://www.gnani.ai/internship).

Two practical discrepancies need attention: the registration terms refer to a participant workspace while the FAQ says the submission form arrives by email; use actual registration communications. The challenge names Timbre v2.5 while current docs also expose v3.0. This build uses v2.5. Evon is not necessary: the FAQ describes weights by request rather than a hosted API. Preserve time for integration instead of adding an unneeded GPU dependency. [Terms](https://www.gnani.ai/great-indian-ai-internship-registration-form), [voice/version catalogue](https://docs.gnani.ai/api/TTS/available-voices).

## 2. Ideas compared before choosing

Scores are analyst judgments, **not competitor counts or measured chances**. Each dimension is 1–5, where higher means easier or more promising: feasibility / user access / 60-second story / Gnani relevance / differentiation room / authentic reach. Accessible real users can change the decision.

| Candidate | Scores | Total /30 | Decision and evidence |
|---|---|---:|---|
| Checked scrap weight/rate receipt | 5/4/5/5/4/5 | 28 | Choose. Existing POS validates the workflow and challenges novelty; test whether spoken review adds value. |
| Worker-owned piecework receipt | 4/3/5/5/4/4 | 25 | Backup if you already know home-based workers. Voice earnings and employer ledgers already exist: [DhanRakh](https://dhanrakh.in/), [KaryaAI](https://karyaai.app/). |
| Small repair-shop job card | 5/4/5/5/1/4 | 24 | Strong delivery score, weak differentiation: [HeyFix](https://www.heyfix.in/), [GarageGuru](https://garageguru.ai/) and [Repairwala](https://github.com/Rahullkumr/repairwala) are near matches. |
| Pump operator log/handover | 4/2/4/5/4/3 | 22 | Useful second domain only with operator access. [Glific/Arghyam](https://glific.org/arghyam-x-glific-empowering-rural-india-with-safe-water/) already supports conversational meter reporting. |
| Sanitation shift handover | 4/2/4/5/4/3 | 22 | Municipal/worker access uncertain; [Safai Mitra](https://play.google.com/store/apps/details?id=com.mtpl.safaimitra) already covers shifts and field work. |
| General critical-number confirmation toolkit | 4/5/3/5/2/3 | 22 | Good reusable component inside TaulSaathi; weaker standalone human story and established confirmation research. |
| SHG repayment/meeting record | 3/2/4/5/2/4 | 20 | Multi-speaker/financial complexity; [SakhiSetu](https://github.com/aayushijohri/SakhiSetu) already describes voice bookkeeping and audio confirmation. |
| Dysarthric-speech enhancement | 1/1/4/3/2/4 | 15 | Specialized data and evaluation exceed this window; [Paraspeak](https://www.paraspeak.in/) is direct Indian prior art. |

Generic crop advisory, kirana ordering and tutoring are easy convergence points because the contest itself suggests them. That makes overlap plausible, not proven saturation. A more unusual domain still needs a real user problem.

## 3. Problem, target users and prior art

Start with a small scrap buyer and a seller/collector discussing one recyclable material. The job is to produce a record they can inspect, with explicit gross/tare or net weight and an agreed INR-per-kg rate. Do not assume workers have low literacy or require a new app; test the accessibility benefit individually.

The NITI Aayog–UNDP handbook contains material-recovery transaction registers with weight, material category, rate/kg, amount, payment mode and acknowledgements, grounding the schema in a documented workflow. It does not prove demand for AI. [Official handbook, reporting/data-monitoring section, printed pp. 98–99](https://www.niti.gov.in/sites/default/files/2023-02/Final_Handbook_PWM_10112021.pdf). Hand in Hand India's waste-picker guide includes measurement and practical numeracy training; this supports testing accessible records without generalizing about every user. [Publisher's guide](https://hihindia.org/wp-content/uploads/2019/10/A-Guide-to-Empower-Informal-Waste-Pickers-1.pdf).

| Product/project | What its own source describes | Implication for this idea |
|---|---|---|
| [INZOO Scrap POS](https://inzoo.in/pos-software-for-scrap-shop) | Weight×rate receipts, vendor ledgers and rate histories in scrap-specific search extraction; later page retrieval varied | Basic scrap billing is direct prior art. Recheck the live app before comparative claims. |
| [Kabadi Khata / Recyloop](https://play.google.com/store/apps/details?id=com.thechampusman.recyloop) | Category, weight, payment, collection records and consumer confirmation | Confirmation and transaction records are not new by themselves. |
| [Kabadiwalla Connect](https://www.kabadiwallaconnect.in/) | Informal-supply-chain digitalization, transaction tracking and traceability | A substantial adjacent operator; do not imply the sector lacks digital tools. |
| [WeighDATA](https://weighdata.in/) | Scale integration, gross/tare/net/rate slips, roles, traceability and scrap use | Hardware-integrated records can be better than speech. Use speech where hardware integration is unavailable or insufficient. |
| [ReVive student project](https://github.com/JiveshNage/ReVive) | Vernacular audio, collectors, weighing/sign-off workflows in its README | Student and hackathon competition exists too. README claims were not independently run. |
| [ScrapVanta](https://scrapvanta.in/faq.html), [Kabadigo](https://www.kabadigo.com/faq) | Visible/digital weighing, slips or confirmation/disagreement flows | Trust-oriented weighing workflows already exist. |
| [LekhaBook](https://lekhabook.in/), [VoiceKhata](https://voicekhata.com/) | Indian-language spoken ledger entries | “Voice accounting for Bharat” is too broad a differentiation claim. |

The remaining hypothesis is that **Kannada/English critical-number capture, explicit ambiguity, complete readback and revision-bound confirmation** improve completion for a small transaction. Targeted searches did not find a verified deployed exact match showing the whole combination. Absence from search results is not evidence of absence; competitors may add these features or already have undocumented versions.

## 4. Research papers and what to borrow

The papers inform engineering choices. None measures this prototype or establishes a Gnani accuracy claim.

| Primary paper | Authors/year | Relevant finding or method | Applied decision |
|---|---|---|---|
| [SLURP: A Spoken Language Understanding Resource Package](https://aclanthology.org/2020.emnlp-main.588/) | Emanuele Bastianelli, Andrea Vanzo, Pawel Swietojanski, Verena Rieser; 2020 | Spoken intent/entities and semantic evaluation | Measure the final fields and complete record, alongside transcript error. English assistant data does not validate Kannada scrap speech. |
| [MASSIVE](https://arxiv.org/abs/2204.08582) | Jack FitzGerald, Christopher Hench, Charith Peris et al.; 2022 preprint / ACL 2023 | Multilingual intent/slot dataset and exact-match evaluation | Use a small typed schema and explicit unknowns. Text localization is not noisy code-mixed audio evidence. |
| [IndicVoices](https://arxiv.org/abs/2403.01926) | Tahir Javed, Janki Atul Nawale, Eldho Ittan George et al.; 2024 | Spontaneous, diverse Indian-language speech collection | Record spontaneous task descriptions with consent and speaker-separated tests. Paper and current dataset releases have different sizes. |
| [IndicSUPERB](https://arxiv.org/abs/2208.11761) | Tahir Javed, Kaushal Santosh Bhogale, Abhigyan Raman, Anoop Kunchukuttan, Pratyush Kumar, Mitesh M. Khapra; 2022 / AAAI 2023 | Kathbath and multilingual speech-task evaluation | Kannada read speech is a useful control, but does not replace original domain recordings. |
| [Bengali-English and Hindi-English Code Mixed Speech Data with Disfluencies](https://aclanthology.org/2026.wildre-1.5/) | Anuran Mitra, Tapabrata Mondal, Anirvan Chakravarty, Sivaji Bandyopadhyay; 2026 | Explicit repetitions/restarts/filled pauses in synthetic code-mixed speech | Include self-corrections and pauses in tests. Synthetic Bengali/Hindi evidence does not establish natural Kannada performance. |
| [Generating effective confirmation and guidance using two-level confidence measures for dialogue systems](https://www.isca-archive.org/icslp_2000/komatani00_icslp.html) | Kazunori Komatani, Tatsuya Kawahara; 2000 | Concept-level acceptance/confirmation/rejection using recognizer alternatives | Ask useful field questions. The API here supplies no verified calibrated confidence, so expose rule-based warnings, not invented percentages. |

Open research questions worth testing: Can users notice a plausible wrong rate when it is read back? Which numeral forms survive ASR? Is one-field push-to-talk faster and more reliable than a full note? How often does asking for review reduce errors, and how much time does it add? Does denoising remove important consonants or correction cues? Is a printed number plus spoken readback better than either alone?

## 5. GitHub foundations and datasets

These are verified public repositories. Stars and last-push snapshots were retrieved on 22 October 2026; they change and do not prove quality or maintenance. The starter to use is the included small app, together with current Gnani REST docs. **No third-party repo code was copied into the prototype.**

| Repository | Stars snapshot | Stack/license | Use and activity limit |
|---|---:|---|---|
| [snakers4/silero-vad](https://github.com/snakers4/silero-vad) | 10,501 | Python, PyTorch/ONNX; MIT | Optional voice boundaries; recent push Oct 2026. Skip until needed, because pauses/corrections matter. |
| [rapidfuzz/RapidFuzz](https://github.com/rapidfuzz/RapidFuzz) | 4,176 | Python/C++; MIT | Suggest material aliases; recent Oct 2026 activity. Similarity is not confidence and must not silently alter money. |
| [iver56/audiomentations](https://github.com/iver56/audiomentations) | 2,323 | Python/NumPy; MIT | Reproducible noise transforms; last observed push Apr 2026. Label transforms as simulation. |
| [jitsi/jiwer](https://github.com/jitsi/jiwer) | 938 | Python; Apache-2.0 | WER/CER diagnostics; last observed push Sep 2026. Secondary to exact numeric fields. |
| [alexa/massive](https://github.com/alexa/massive) | 575 | Python; Apache-2.0 code, CC-BY-4.0 data | Slot/evaluation reference; last observed push 2022. Avoid adopting old training dependencies. |
| [AI4Bharat/IndicXlit](https://github.com/AI4Bharat/IndicXlit) | 145 | Python/Fairseq; MIT | Optional native/Roman aliases; last observed push 2023. Do not add without an observed script problem. |
| [pswietojanski/slurp](https://github.com/pswietojanski/slurp) | 112 | Python; text CC-BY-4.0, audio CC-BY-NC-4.0 | Semantic scoring reference; last observed push 2022. Audio has separate noncommercial terms. |
| [raj-sutariya/indic-num2words](https://github.com/raj-sutariya/indic-num2words) | 39 | Python; Apache-2.0 | Kannada number readback candidate; last observed push May 2025. Digits→words only; it does not parse spoken words. |

Also inspect the [current official Gnani Python client](https://github.com/Gnani-AI-Mintlify/gnani-vachana), but check examples for model-version drift. The older [Gnani API-service](https://github.com/Gnani-AI/API-service) uses a legacy endpoint/authentication contract and is a poor new-project scaffold. [LiveKit Agents](https://github.com/livekit/agents) and its [Gnani integration](https://docs.livekit.io/agents/models/stt/gnani/) become useful if real-time sessions are validated as necessary; they add infrastructure to a short-clip MVP.

Dataset choices:

- [IndicVoices](https://huggingface.co/datasets/ai4bharat/IndicVoices): current card CC-BY-4.0 and gated acceptance. It includes Kannada and spontaneous speech, but no gold scrap records. The current release differs from the 2024 paper; pin a version if used.
- [Kathbath/IndicSUPERB](https://github.com/AI4Bharat/IndicSUPERB): repository lists 65.8 hours for Kannada. README dataset/code labels and root license differ, so inspect the specific artifact's terms before redistribution. Read speech is a control, not the target task.
- MASSIVE and SLURP provide schemas/evaluation patterns with the licensing distinctions above. They do not cover this workflow.
- **Original recordings are the essential missing dataset.** Use fictional identities, no private calls, and explicit consent for any participant audio made public. Contest FAQ instructions on synthetic calls govern the public demo; privately validated workflow feedback can be reported without exposing a real transaction.

Communities and primary venues: [AI4Bharat](https://ai4bharat.iitm.ac.in/), [ACL Anthology](https://aclanthology.org/), [ISCA Archive](https://www.isca-archive.org/), official Gnani documentation and its contest-linked Discord. Use these for specific API/dataset questions. No outreach, messages or posts were sent during this task.

## 6. Refined architecture and actual implementation

```text
Short WAV → Python backend → Gnani Prisma final transcript
                             ↓
                bounded Kannada/English parser
                             ↓
       draft + source phrases + warnings + exact arithmetic
                             ↓
        operator corrects fields / reviews unclear speech
                             ↓
          Gnani Timbre reads critical current values
                             ↓
        explicit current-revision confirmation → export
```

The app uses Python's standard library and buildless HTML/CSS/JavaScript. No GPU, paid LLM, vector database, new ASR training or external runtime package is required. Keeping the first version small makes its numerical behavior inspectable. Later, a structured extractor can propose candidates behind the same validation rules; it should only be added if measured coverage improves.

Implemented scope: one of six material categories, kilograms, INR/kg, net or gross-minus-tare, Decimal arithmetic and two-decimal half-up amount rounding. Supported label and number vocabulary is deliberately bounded. Kannada digits and selected Kannada/English words work; unsupported compounds require review/manual correction. Speak in short clauses such as:

> ಕಾಗದ, ಒಟ್ಟು ೨೫ ಕೆಜಿ, ಚೀಲ ೨ ಕೆಜಿ, ದರ ೨೦ ರೂಪಾಯಿ ಪ್ರತಿ ಕೆಜಿ

This example yields 23 kg net and ₹460.00. The Kannada wording and digit-by-digit spoken number style still need your native-speaker review and a real TTS listen. It is an engineering draft, not validated production translation.

Warnings block confirmation when a unit is absent, fields conflict, net disagrees with gross-minus-tare, another number or instruction remains unassigned, or a correction/negation needs review. Corrections create revisions. Transcript warnings require a separate explicit review reason, and structural errors remain blocking. This review is an operator override, not automatic proof of understanding. A plausible wrong value can still pass every rule, so humans must check the numbers.

The local server keeps records in session memory and exports confirmed JSON; the browser can print the confirmed view. A digest binds the confirmed field snapshot, but does not authenticate a person or create tamper-proof storage. Edits remove confirmation and its digest. Readback requests reject stale revisions, including changes that happen while synthesis is in progress. TTS audio is cached per revision to avoid spending credits twice on the same generated readback.

API keys remain server-side. Raw audio is processed in memory, not saved by this app. Hosted Gnani processing still sends it to Gnani; **Indian-model provenance alone does not establish offline operation or a verified data-residency guarantee**. This loopback research server is not a public production deployment. [Python server documentation](https://docs.python.org/3.13/library/http.server.html).

Gnani contracts used:

| Component | Verified request | Important detail |
|---|---|---|
| Prisma STT | `POST https://api.vachana.ai/stt/v3`; multipart `audio_file`, `language_code=kn-IN`, `format=verbatim` | `X-API-Key-ID` header; JSON `success` and `transcript`. App permits WAV up to 30 seconds. STT service mapping is documented Prisma v2.5; it is not a locally pinned weight file. |
| Timbre TTS | `POST https://api.vachana.ai/api/v1/tts/inference`; JSON text/voice/model/language/audio config | `timbre-v2.5`, Kannada `Saanvi`, binary WAV response. Model and voice catalogues must match. |

[Official STT reference](https://docs.gnani.ai/api/STT/speech-to-text), [TTS reference](https://docs.gnani.ai/api/TTS/tts-inference), [voice catalogue](https://docs.gnani.ai/api/TTS/available-voices).

REST upload is the first implementation. Microphone capture, streaming, WhatsApp integration, persistent database, multi-user acknowledgements, automatic spoken corrections and natural human-speech accuracy evaluation are **not implemented**. Do not describe the current UI as completely hands-free. A future SQLite store and field-by-field voice correction are sensible extensions after the workflow is validated.

## 7. Validation, benchmarks and 5,000-credit plan

Before spending on a large test set, run one short Kannada STT request and one TTS readback. Compare dashboard usage before/after to learn the actual credit debit. A balance screenshot does not establish a price or conversion. Local transcript tests use no API credits, and the app does not retry inference automatically.

Suggested credit allocation, expressed as **budget shares rather than assumed minutes**: 5% integration calibration, 25% development recordings, 30% frozen evaluation, 20% corrections/readback checks, 20% reserve. Adjust using measured debits; stop optional work before exhausting the reserve. For planning, 60 original ten-second clips total ten audio minutes before variants/retries, but their credit cost is unknown.

First validation in 48 hours: seek feedback from two independent scrap buyers/collectors and two sellers. Observe how they currently record weight/rate, whether errors or disputes recur, and whether a calculator plus ordinary voice note is sufficient. Compare completion time and comprehension. Stop or narrow if they see no recurrent problem or readback adds friction without benefit. Access and user interviews remain your next actions; no such findings are claimed here.

For speech evaluation, aim initially for 60 original clips from at least six speakers, with development and held-out speakers separated. Include native Kannada numbers, English mixing, 12.5 vs 125, 15 vs 50, half a kilogram, corrections, missing units, overlapping talk and silence. Keep clean/noisy variants of each clip in the same split. Freeze the held-out set before tuning. A small test is preliminary evidence, never population-level reliability.

| Metric | Definition |
|---|---|
| Draft exact-record accuracy | Correct material, mass basis, weights, rate and derived amount before operator repair / all attempts |
| Final exact-record accuracy | Fully correct records after the stated repair allowance / all attempts; unresolved counts as incomplete |
| Wrong-confirmed rate | Confirmed records with any material field error / confirmed records; also report absolute count |
| Completion coverage | Confirmed records / all attempts, so rejecting everything cannot appear successful |
| Correction success | Correct intended final value on correction cases / all correction cases |
| Burden and time | Review/correction actions, cancellations, total task time, and API latency separately |
| WER/CER | Secondary transcript diagnostics with frozen normalization; never erase negation or value changes |

Compare the **same Prisma transcripts** with one-pass extraction versus validated review, reporting both improvement and added operator work. Added noise is simulated noise. An 8 kHz transform is simulated telephony. Real telephone-channel claims need an appropriate permitted real-channel test. Do not attribute Whisper research failures to Prisma.

The included unit tests and text fixtures measure code behavior only. Live STT quality, spoken readback quality, user comprehension and time saved remain unmeasured. The separate evaluation folder includes a recording manifest template so those results can be collected without inventing scores.

## 8. Market viability and differentiation

Potential payers are small aggregation centres, scrap buyers, cooperatives or an operator that needs accessible records. A collector may be a beneficiary without being the buyer. The main adoption alternatives are a calculator, notebook, voice note, existing POS and a scale-linked receipt. Willingness to pay, distribution access and workflow frequency remain unknown.

A subscription or per-centre deployment is a possible business model, not validated pricing. Do not charge a percentage of workers' proceeds without evidence that this serves them. There is no defensible market-size estimate for this narrow feature from the sources reviewed; broad waste-sector employment figures cannot be converted into software revenue. Calculate a bottom-up opportunity only after interviews: reachable centres × credible paid adoption × tested monthly price, less speech and support costs.

The durable contribution would be a consented domain test set, transparent failure handling, a revision-safe state machine and demonstrated comprehension/time benefit. The claim “no competitor exists” is unnecessary and unsupported. If a better existing tool solves the task for your testers, document that and narrow the feature further.

## 9. Build schedule, demonstration and submission pack

| Dates, IST | Concrete milestone |
|---|---|
| Oct 22–24 | Run this prototype, native-review Kannada text, calibrate Gnani debit, validate the task with users. Kill/narrow if the problem is weak. |
| Oct 25–28 | Improve only observed grammar gaps; add microphone/field correction only if useful. Preserve confirmation tests. |
| Oct 29–Nov 2 | Collect/freeze consented fictional-task recordings, compare baseline and review workflow, report all failures. |
| Nov 3–6 | Fix failure cases using development examples; record a genuine working 60-second demo and publish early enough for authentic feedback. |
| Nov 7–9 | Respond to relevant feedback, finalize explanation/repo/contributions, verify nominated links and organiser submission instructions. |
| Nov 10 | Submit with a practical buffer before the official 11:59 PM IST deadline; verify receipt of submission. |

Proposed 60-second video storyboard, **not an already-created video**:

1. 0–7s: Show fictional paper/bag weights and explain the confusing number.
2. 7–22s: Upload a short Kannada/English recording, show the real Prisma response and extracted fields.
3. 22–39s: Show a correction/ambiguity and the blocked confirmation. Resolve the intended rate; total updates.
4. 39–52s: Play the actual Timbre readback, visibly review the current values, then confirm/export.
5. 52–60s: State Gnani models, actual tested sample count/results if available, and the current limitation. End with a focused request for user feedback.

If you inject a wrong rate deliberately, label it an injected test case. Do not edit a demo to imply a model error or success that did not happen. Do not manufacture testimonials, benchmark numbers, likes, votes or endorsements. Publish useful findings to relevant communities without spam or engagement exchanges. Public posting and submission have not been performed.

Project explanation draft:

> TaulSaathi helps people inspect a scrap transaction in Kannada and English. Gnani Prisma transcribes a short fictional weighing note; typed validation keeps missing units, conflicting values and corrections visible. Exact arithmetic derives net weight and amount, and Gnani Timbre reads the critical current values back. An operator must review and confirm that revision before export. The current prototype supports a bounded vocabulary and manual correction; speech accuracy and field usefulness will be reported only after testing.

Use the paragraph in a submission only after replacing future/unverified parts with your actual completed work. Prepare to explain the parser's limits, Decimal arithmetic, revision binding, the difference between WER and task accuracy, and why hosted speech does not by itself prove data residency. Those are interview-ready engineering decisions.

## First three actions

1. Open the included app and reproduce the clear, conflicting-rate and missing-unit examples. Review the Kannada labels yourself.
2. Add your Gnani key locally and complete one real STT→review→TTS→confirm flow; inspect its credit debit.
3. Test the problem with reachable users before expanding features, then record a small frozen speech evaluation and an honest demo.

Additional evidence notes are in `evidence/`; runnable code and detailed launch instructions are in `taulsaathi/README.md`.

## Subsequent validation update

The participant requested execution of the pre-submission checks and demo. Initial requests were blocked by the API edge with the default Python client signature; adding a truthful TaulSaathi API-client User-Agent resolved the integration. Actual Kannada Timbre audio and Prisma transcripts now succeed. The historical access-failure report is retained alongside the successful evidence; exact credit debit remains unknown. See `VALIDATION-STATUS.md` and `validation/`.

Thirty additional authored text cases found two parser flaws (word-number signs and unassigned symbols), which were corrected and retested. Live development transcripts then revealed split Kannada units (`ಕೆ ಜಿ`) and explicit spoken decimals. These are now handled with source spans preserved, while conflicting rates remain blocked. The combined offline suite passes 110 tests; the original two text sets pass 50 fixtures. Nine further scripted HTTP workflow checks also pass.

Four actual STT checks used two generated Kannada scripts and two simulated 10 dB noise variants. All returned transcripts. Reanalysis of those unchanged development transcripts after the parser fix gives both decimal examples 12 kg / ₹168 and keeps both correction examples blocked with 15 and 50 evidence. This is not a held-out, human-speaker or real-telephony benchmark. The app also normalizes the observed streaming WAV length sentinel without changing PCM. A feedback kit, technical project brief, interview guide and labelled prototype video accompany the update. No buyer/seller interview, outreach, posting or submission was performed.
