"""Exercise real localhost HTTP routes with in-memory state and mocked speech.

No credentials are read: all three Gnani entry points used by the server are
patched before any request. No request leaves the ephemeral local server.
"""

import base64
import hashlib
import json
import sys
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app

TRANSCRIPT = "paper, gross 25 kg, tare 2 kg, rate 20 rupees per kg"
WAV_RESPONSE = b"RIFF\x04\x00\x00\x00WAVE"


class AppWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), app.Handler)
        cls.server.daemon_threads = True
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"
        cls.worker = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.worker.start()
        cls.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.worker.join(timeout=3)

    def setUp(self):
        app.STORE = app.Store()
        self.stt = self.enterContext(patch.object(app.gnani, "transcribe_wav"))
        self.tts = self.enterContext(patch.object(app.gnani, "synthesize", return_value=(WAV_RESPONSE, "audio/wav")))
        self.enterContext(patch.object(app.gnani, "configuration_status", return_value={"configured": False, "live_verified": False}))

    def request(self, route, data=None, headers=None):
        body = json.dumps(data).encode("utf-8") if data is not None else None
        request_headers = {"Content-Type": "application/json"} if body is not None else {}
        request_headers.update(headers or {})
        request = urllib.request.Request(self.base + route, data=body, headers=request_headers)
        try:
            response = self.opener.open(request, timeout=4)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            content = response.read()
            content_type = response.headers.get("Content-Type", "")
            payload = json.loads(content) if content_type.startswith("application/json") else content
            return response.code, payload, response.headers

    def draft(self, **overrides):
        data = {"transcript": TRANSCRIPT, "language": "en-IN", "source": "typed"}
        data.update(overrides)
        status, draft, _ = self.request("/api/draft", data)
        self.assertEqual(status, 200, draft)
        return draft

    def test_draft_confirm_export_requires_explicit_review(self):
        draft = self.draft()
        self.assertEqual(draft["computed"], {"net_kg": "23", "total_inr": "460.00"})
        self.assertEqual(self.request("/api/receipt?id=" + draft["id"])[0], 400)
        status, _, _ = self.request("/api/confirm", {"id": draft["id"], "revision": 1, "reviewed": False})
        self.assertEqual(status, 400)
        status, confirmed, _ = self.request("/api/confirm", {"id": draft["id"], "revision": 1, "reviewed": True})
        self.assertEqual(status, 200, confirmed)
        self.assertEqual(confirmed["status"], "confirmed")
        self.assertEqual(len(confirmed["digest"]), 64)
        status, receipt, headers = self.request("/api/receipt?id=" + draft["id"])
        self.assertEqual(status, 200)
        self.assertEqual(receipt["digest"], confirmed["digest"])
        self.assertEqual(receipt["source"], "typed")
        self.assertIn("no payment", receipt["notice"])
        self.assertIn("attachment", headers["Content-Disposition"])
        self.stt.assert_not_called()
        self.tts.assert_not_called()

    def test_correction_invalidates_confirmation_and_blocks_stale_revision(self):
        draft = self.draft()
        self.request("/api/confirm", {"id": draft["id"], "revision": 1, "reviewed": True})
        status, revised, _ = self.request("/api/revise", {"id": draft["id"], "revision": 1, "field": "rate_inr_per_kg", "value": "22", "reason": "Operator checked the agreed rate."})
        self.assertEqual(status, 200, revised)
        self.assertEqual(revised["revision"], 2)
        self.assertEqual(revised["status"], "draft")
        self.assertNotIn("digest", revised)
        self.assertEqual(revised["computed"]["total_inr"], "506.00")
        self.assertEqual(self.request("/api/receipt?id=" + draft["id"])[0], 400)
        for route in ("/api/confirm", "/api/review", "/api/revise"):
            status, _, _ = self.request(route, {"id": draft["id"], "revision": 1, "reviewed": True, "reason": "Operator reviewed the old transcript.", "field": "tare_kg", "value": "1"})
            self.assertEqual(status, 400, route)
        status, confirmed, _ = self.request("/api/confirm", {"id": draft["id"], "revision": 2, "reviewed": True})
        self.assertEqual(status, 200, confirmed)

    def test_revision_bool_is_not_a_current_revision(self):
        draft = self.draft()
        for route in ("/api/confirm", "/api/review", "/api/revise", "/api/readback"):
            status, _, _ = self.request(route, {"id": draft["id"], "revision": True, "reviewed": True, "reason": "Operator verified the values.", "field": "tare_kg", "value": "1"})
            self.assertEqual(status, 400, route)
        self.tts.assert_not_called()

    def test_upstream_access_failure_exposes_only_safe_status(self):
        draft = self.draft()
        self.tts.side_effect = app.gnani.GnaniError('upstream_http_error', 'Gnani denied access.', 403)
        status, payload, _ = self.request('/api/readback', {'id': draft['id'], 'revision': 1})
        self.assertEqual(status, 502)
        self.assertEqual(payload, {'error': 'Gnani denied access.', 'code': 'upstream_http_error', 'upstream_status': 403})

    def test_export_preserves_speech_evidence_and_invalidates_old_readback(self):
        audio = b'fictional-contract-audio'
        self.stt.return_value = {'text': TRANSCRIPT, 'model': 'prisma-v2.5', 'elapsed_ms': 5, 'request_id': 'req_contract'}
        status, speech, _ = self.request('/api/transcribe', {'audio_base64': base64.b64encode(audio).decode(), 'language': 'en-IN'})
        self.assertEqual(status, 200)
        self.assertEqual(speech['audio_sha256'], hashlib.sha256(audio).hexdigest())
        draft = self.draft(source='gnani', transcription_id=speech['transcription_id'])
        self.assertEqual(draft['speech_evidence']['request_id'], 'req_contract')
        self.request('/api/readback', {'id': draft['id'], 'revision': 1})
        _, confirmed, _ = self.request('/api/confirm', {'id': draft['id'], 'revision': 1, 'reviewed': True})
        self.assertEqual(confirmed['readback_evidence']['generated_for_revision'], 1)
        self.assertEqual(confirmed['readback_evidence']['audio_sha256'], hashlib.sha256(WAV_RESPONSE).hexdigest())
        _, revised, _ = self.request('/api/revise', {'id': draft['id'], 'revision': 1, 'field': 'rate_inr_per_kg', 'value': '21', 'reason': 'Checked a new fictional rate.'})
        self.assertNotIn('readback_evidence', revised)
        self.assertEqual(revised['speech_evidence']['request_id'], 'req_contract')

    def test_cross_origin_and_foreign_host_actions_are_denied(self):
        for headers in ({"Origin": "https://example.com"}, {"Origin": "null"}, {"Host": "example.com"}, {"Host": "127.0.0.1:1"}):
            status, _, _ = self.request("/api/draft", {"transcript": TRANSCRIPT}, headers)
            self.assertEqual(status, 403, headers)
        self.assertEqual(self.request("/api/examples", headers={"Host": "attacker.example"})[0], 403)
        status, _, _ = self.request("/api/draft", {"transcript": TRANSCRIPT, "language": "en-IN"}, {"Origin": self.base})
        self.assertEqual(status, 200)
        self.stt.assert_not_called()
        self.tts.assert_not_called()

    def test_source_spoofing_is_rejected_or_relabelled(self):
        status, _, _ = self.request("/api/draft", {"transcript": TRANSCRIPT, "language": "en-IN", "source": "gnani", "transcription_id": "invented"})
        self.assertEqual(status, 400)
        draft = self.draft(source="synthetic")
        self.assertEqual(draft["source"], "typed")

    def test_live_transcription_provenance_requires_matching_text_and_language(self):
        self.stt.return_value = {"text": TRANSCRIPT, "model": "prisma-v2.5", "language": "en-IN", "elapsed_ms": 123}
        recorded = b"synthetic recording for a mocked transport"
        status, result, _ = self.request("/api/transcribe", {"language": "en-IN", "audio_base64": base64.b64encode(recorded).decode("ascii")})
        self.assertEqual(status, 200, result)
        self.stt.assert_called_once_with(recorded, "en-IN")
        draft = self.draft(source="gnani", transcription_id=result["transcription_id"])
        self.assertEqual(draft["source"], "gnani")
        for changes in ({"transcript": TRANSCRIPT + " changed"}, {"language": "kn-IN"}):
            data = {"transcript": TRANSCRIPT, "language": "en-IN", "source": "gnani", "transcription_id": result["transcription_id"]}
            data.update(changes)
            self.assertEqual(self.request("/api/draft", data)[0], 400)
        self.assertEqual(self.draft(transcript=TRANSCRIPT + " changed")["source"], "typed")

    def test_readback_caches_exact_revision_and_rejects_stale_request(self):
        draft = self.draft()
        data = {"id": draft["id"], "revision": 1}
        for _ in range(2):
            status, audio, headers = self.request("/api/readback", data)
            self.assertEqual(status, 200)
            self.assertEqual(audio, WAV_RESPONSE)
            self.assertEqual(headers["Content-Type"], "audio/wav")
        self.tts.assert_called_once_with(draft["readback_text"], "en-IN")
        status, revised, _ = self.request("/api/revise", {**data, "field": "tare_kg", "value": "1", "reason": "Tare was independently checked."})
        self.assertEqual(status, 200)
        self.assertEqual(self.request("/api/readback", data)[0], 400)
        self.assertEqual(self.tts.call_count, 1)
        self.assertEqual(self.request("/api/readback", {"id": draft["id"], "revision": revised["revision"]})[0], 200)
        self.assertEqual(self.tts.call_count, 2)
        self.tts.assert_called_with(revised["readback_text"], "en-IN")

    def test_readback_rejects_revision_changed_during_synthesis(self):
        draft = self.draft()
        entered, release = threading.Event(), threading.Event()
        result = []

        def delayed_synthesis(*args):
            entered.set()
            if not release.wait(3):
                raise RuntimeError("Test synchronization timed out")
            return WAV_RESPONSE, "audio/wav"

        self.tts.side_effect = delayed_synthesis
        worker = threading.Thread(target=lambda: result.append(self.request("/api/readback", {"id": draft["id"], "revision": 1})))
        worker.start()
        try:
            self.assertTrue(entered.wait(2), "Readback did not reach mocked synthesis")
            status, _, _ = self.request("/api/revise", {"id": draft["id"], "revision": 1, "field": "tare_kg", "value": "1", "reason": "Corrected during audio generation."})
            self.assertEqual(status, 200)
        finally:
            release.set()
            worker.join(timeout=4)
        self.assertFalse(worker.is_alive())
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], 400, "Audio generated for an obsolete revision must not be returned")

    def test_invalid_base64_does_not_consume_speech_credits(self):
        status, _, _ = self.request("/api/transcribe", {"language": "kn-IN", "audio_base64": "!invalid!"})
        self.assertEqual(status, 400)
        self.stt.assert_not_called()


if __name__ == "__main__":
    unittest.main()
