"""Offline live-runner tests: all speech/configuration entry points mocked."""

import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
import urllib.error
import wave
from pathlib import Path
from unittest.mock import patch

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))
spec = importlib.util.spec_from_file_location("taulsaathi_live_runner", PROJECT / "evaluation" / "run_live.py")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)

TRANSCRIPT = "paper, gross 25 kg, tare 2 kg, rate 20 rupees per kg"


def wav_bytes():
    result = io.BytesIO()
    with wave.open(result, "wb") as recording:
        recording.setnchannels(1)
        recording.setsampwidth(2)
        recording.setframerate(16000)
        recording.writeframes(b"\x00\x00" * 1600)
    return result.getvalue()


class LiveRunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp = self.enterContext(tempfile.TemporaryDirectory())
        self.root = Path(self.temp)
        self.audio = wav_bytes()
        self.wav = self.root / "fictional.wav"
        self.wav.write_bytes(self.audio)
        self.config = self.enterContext(patch.object(runner.gnani, "configuration_status", return_value={"configured": True}))
        self.stt = self.enterContext(patch.object(runner.gnani, "transcribe_wav", return_value={"text": TRANSCRIPT, "model": "prisma-v2.5", "language": "en-IN", "elapsed_ms": 123}))
        self.tts = self.enterContext(patch.object(runner.gnani, "synthesize", return_value=(self.audio, "audio/wav")))

    def case(self, **overrides):
        result = {"id": "fixture", "wav_path": self.wav, "language": "en-IN", "audio_provenance": "unknown", "scenario_provenance": "fictional",
                  "gold": {"fields": {"material": "paper", "gross_kg": "25", "tare_kg": "2", "rate_inr_per_kg": "20"},
                           "computed": {"net_kg": "23", "total_inr": "460"}, "must_block": False}}
        result.update(overrides)
        return result

    def test_missing_key_makes_zero_calls_and_does_not_open_audio(self):
        self.config.return_value = {"configured": False}
        with patch.object(runner, "audio_metadata") as metadata:
            report = runner.run_cases([self.case()], self.root)
        self.assertEqual(report["status"], "not_configured")
        self.assertEqual(report["api_calls"], {"stt": 0, "tts": 0, "total": 0})
        metadata.assert_not_called()
        self.stt.assert_not_called()
        self.tts.assert_not_called()

    def test_success_preserves_actual_transcript_hash_latency_and_field_checks(self):
        report = runner.run_cases([self.case()], self.root)
        clip = report["clips"][0]
        self.assertEqual(report["status"], "complete")
        self.assertEqual(clip["stt"]["raw_transcript"], TRANSCRIPT)
        self.assertEqual(clip["stt"]["adapter_elapsed_ms"], 123)
        self.assertEqual(clip["input"]["sha256"], runner.hashlib.sha256(self.audio).hexdigest())
        self.assertEqual(clip["input"]["duration_seconds"], 0.1)
        self.assertEqual(clip["audio_provenance"], "unknown")
        self.assertTrue(clip["evaluation"]["all_match"])
        self.assertEqual(report["summary"]["gold_checks_compared"], 7)
        self.stt.assert_called_once_with(self.audio, "en-IN")
        self.tts.assert_not_called()

    def test_mismatches_are_retained_and_never_invented_as_successful_gold(self):
        self.stt.return_value["text"] = TRANSCRIPT.replace("rate 20", "rate 50")
        clip = runner.run_cases([self.case()], self.root)["clips"][0]
        self.assertFalse(clip["evaluation"]["all_match"])
        check = next(c for c in clip["evaluation"]["checks"] if c["field"] == "fields.rate_inr_per_kg")
        self.assertEqual(check, {"field": "fields.rate_inr_per_kg", "expected": "20", "actual": "50", "match": False})

    def test_initial_run_cannot_exceed_five_clips(self):
        cases = [self.case(id=f"clip-{i}") for i in range(9)]
        report = runner.run_cases(cases, self.root)
        self.assertEqual(self.stt.call_count, 5)
        self.assertEqual(len(report["clips"]), 5)
        self.assertEqual(report["api_calls"]["total"], 5)
        for limit in (0, 6, True):
            with self.subTest(limit=limit), self.assertRaises(ValueError):
                runner.run_cases(cases, self.root, limit=limit)

    def test_access_error_stops_without_retry_and_omits_error_payload(self):
        self.stt.side_effect = runner.gnani.GnaniError("upstream_http_error", "SECRET THAT MUST NOT APPEAR", 403)
        report = runner.run_cases([self.case(id="one"), self.case(id="two")], self.root)
        self.assertEqual(self.stt.call_count, 1)
        self.assertEqual(report["api_calls"]["total"], 1)
        self.assertEqual(report["clips"][0]["stt"]["http_status"], 403)
        self.assertEqual(report["stopped_early"], "access_or_rate_limit_error")
        self.assertNotIn("SECRET", json.dumps(report))

    def test_unrecorded_unknown_scenario_and_invalid_wav_do_not_call_api(self):
        self.wav.write_bytes(b"invalid WAV")
        for changes in ({}, {"audio_provenance": "unrecorded"}, {"scenario_provenance": "unknown"}):
            with self.subTest(changes=changes):
                report = runner.run_cases([self.case(**changes)], self.root)
                self.assertEqual(report["clips"][0]["status"], "input_error")
                self.assertEqual(report["api_calls"]["total"], 0)
        self.stt.assert_not_called()

    def test_empty_asr_result_retains_real_call_and_raw_transcript(self):
        self.stt.return_value["text"] = ""
        report = runner.run_cases([self.case()], self.root)
        self.assertEqual(report["api_calls"]["stt"], 1)
        self.assertEqual(report["clips"][0]["stt"]["raw_transcript"], "")
        self.assertEqual(report["clips"][0]["status"], "parse_error")

    def test_tts_requires_explicit_flag_and_audio_is_not_saved_by_default(self):
        report = runner.run_cases([self.case()], self.root, tts=True)
        self.assertEqual(report["api_calls"], {"stt": 1, "tts": 1, "total": 2})
        self.assertEqual(report["clips"][0]["tts"]["input_status"], "unconfirmed_machine_draft")
        self.assertNotIn("saved_audio_filename", report["clips"][0]["tts"])
        self.assertEqual(list(self.root.glob("tts-*.wav")), [])
        with self.assertRaises(ValueError):
            runner.run_cases([self.case()], self.root, save_tts_audio=True)

    def test_tts_audio_only_saved_on_explicit_request(self):
        report = runner.run_cases([self.case()], self.root, tts=True, save_tts_audio=True)
        output = self.root / report["clips"][0]["tts"]["saved_audio_filename"]
        self.assertEqual(output.read_bytes(), self.audio)

    def test_blocking_draft_skips_optional_tts(self):
        self.stt.return_value["text"] = "paper, gross 25 kg, tare 2 kg, rate 20"
        report = runner.run_cases([self.case()], self.root, tts=True)
        self.assertEqual(report["clips"][0]["tts"]["status"], "skipped")
        self.assertEqual(report["api_calls"]["tts"], 0)
        self.tts.assert_not_called()

    def test_manifest_is_fictional_unrecorded_and_has_five_scripts(self):
        cases = runner.load_cases(PROJECT / "evaluation" / "live-prompts.json")
        self.assertEqual(len(cases), 5)
        self.assertEqual({c["language"] for c in cases}, {"kn-IN", "en-IN"})
        self.assertTrue(all(c["audio_provenance"] == "unrecorded" for c in cases))

    def test_local_backend_uses_no_environment_configuration_or_direct_adapter(self):
        with patch.object(runner.LocalBackend, "configured", return_value=True), patch.object(runner.LocalBackend, "transcribe", return_value={"text": TRANSCRIPT, "model": "prisma-v2.5", "elapsed_ms": 321, "transcription_id": "verified-token"}) as transcribe, patch.object(runner.LocalBackend, "readback", return_value=(self.audio, "audio/wav")) as readback:
            report = runner.run_cases([self.case()], self.root, tts=True, base_url="http://127.0.0.1:8765")
        self.config.assert_not_called()
        self.stt.assert_not_called()
        self.tts.assert_not_called()
        transcribe.assert_called_once_with(self.audio, "en-IN")
        readback.assert_called_once_with(TRANSCRIPT, "en-IN", "verified-token")
        self.assertEqual(report["transport"], "local_backend")
        self.assertEqual(report["api_calls"]["total"], 2)

    def backend_error_report(self, payload, content_type="application/json"):
        error = urllib.error.HTTPError("http://127.0.0.1:8765/api/transcribe", 502, "unsafe message",
                                       {"Content-Type": content_type}, io.BytesIO(json.dumps(payload).encode()))
        cases = [self.case(id=f"clip-{index}") for index in range(3)]
        with patch.object(runner.LocalBackend, "configured", return_value=True), patch.object(runner.urllib.request.OpenerDirector, "open", side_effect=error) as opener:
            report = runner.run_cases(cases, self.root, base_url="http://127.0.0.1:8765")
        self.assertEqual(opener.call_count, 1)
        self.assertEqual(report["api_calls"], {"stt": 1, "tts": 0, "total": 1})
        self.assertEqual(len(report["clips"]), 1)
        self.config.assert_not_called()
        self.stt.assert_not_called()
        return report

    def test_old_backend_sanitized_502_stops_batch_after_one_speech_attempt(self):
        for payload in ({"error": "PRIVATE MESSAGE", "code": "upstream_http_error"}, {"error": "PRIVATE MESSAGE"}):
            with self.subTest(payload=payload):
                report = self.backend_error_report(payload)
                self.assertEqual(report["stopped_early"], "backend_upstream_error")
                self.assertEqual(report["clips"][0]["stt"]["http_status"], 502)
                self.assertNotIn("upstream_http_status", report["clips"][0]["stt"])
                self.assertNotIn("PRIVATE", json.dumps(report))

    def test_new_backend_upstream_403_stops_and_records_only_numeric_status(self):
        report = self.backend_error_report({"error": "PRIVATE KEY TEXT", "code": "upstream_http_error", "upstream_status": 403})
        self.assertEqual(report["stopped_early"], "access_or_rate_limit_error")
        metadata = report["clips"][0]["stt"]
        self.assertEqual(metadata["code"], "upstream_http_error")
        self.assertEqual(metadata["http_status"], 502)
        self.assertEqual(metadata["upstream_http_status"], 403)
        self.assertNotIn("PRIVATE", json.dumps(report))

    def test_backend_does_not_expose_arbitrary_codes_or_coerce_status_strings(self):
        report = self.backend_error_report({"error": "PRIVATE KEY", "code": "PRIVATE KEY", "upstream_status": "403"})
        self.assertEqual(report["clips"][0]["stt"]["code"], "backend_http_error")
        self.assertNotIn("upstream_http_status", report["clips"][0]["stt"])
        self.assertNotIn("PRIVATE", json.dumps(report))

    def test_backend_oversized_error_json_is_not_parsed_or_logged(self):
        report = self.backend_error_report({"code": "upstream_http_error", "upstream_status": 403, "error": "PRIVATE" * 2000})
        self.assertEqual(report["clips"][0]["stt"]["code"], "backend_http_error")
        self.assertNotIn("upstream_http_status", report["clips"][0]["stt"])
        self.assertNotIn("PRIVATE", json.dumps(report))

    def test_backend_rejects_non_loopback_urls_before_configuration(self):
        for url in ("https://example.com", "http://127.0.0.1.evil:8765", "http://user:secret@localhost:8765", "http://localhost:8765/path", "http://localhost:8765?query=1", "http://localhost:99999"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                runner.LocalBackend(url)
        self.config.assert_not_called()

    def test_cli_writes_machine_report_without_recording_audio(self):
        stdout = io.StringIO()
        output = self.root / "results"
        with contextlib.redirect_stdout(stdout):
            code = runner.main(["--wav", str(self.wav), "--language", "en-IN", "--scenario-provenance", "fictional", "--output-dir", str(output), "--limit", "1"])
        report = json.loads(stdout.getvalue())
        self.assertEqual(code, 0)
        self.assertEqual(json.loads((output / report["report_filename"]).read_text(encoding="utf-8")), report)
        self.assertEqual(list(output.glob("*.wav")), [])

    def test_cli_kannada_console_json_is_safe_on_cp1252_and_file_stays_utf8(self):
        self.stt.return_value["text"] = "ಕಾಗದ, ಒಟ್ಟು ಇಪ್ಪತ್ತೈದು ಕೆಜಿ, ಚೀಲ ಎರಡು ಕೆಜಿ, ದರ ಇಪ್ಪತ್ತು ರೂಪಾಯಿ ಪ್ರತಿ ಕೆಜಿ"
        buffer = io.BytesIO()
        console = io.TextIOWrapper(buffer, encoding="cp1252", errors="strict")
        output = self.root / "kannada-results"
        with contextlib.redirect_stdout(console):
            code = runner.main(["--wav", str(self.wav), "--language", "kn-IN", "--scenario-provenance", "fictional", "--output-dir", str(output)])
        console.flush()
        console_json = buffer.getvalue().decode("ascii")
        report = json.loads(console_json)
        self.assertEqual(code, 0)
        self.assertIn("\\u0c", console_json)
        saved = (output / report["report_filename"]).read_text(encoding="utf-8")
        self.assertIn("ಕಾಗದ", saved)
        self.assertEqual(json.loads(saved), report)


if __name__ == "__main__":
    unittest.main()
