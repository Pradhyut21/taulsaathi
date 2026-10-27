"""Offline transport/contract checks. These tests never use a real API key."""

import io
import json
import os
import struct
import sys
import unittest
import urllib.error
import wave
from email.parser import BytesParser
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gnani


def wav(seconds=0.1):
    output = io.BytesIO()
    with wave.open(output, "wb") as recording:
        recording.setnchannels(1)
        recording.setsampwidth(2)
        recording.setframerate(16000)
        recording.writeframes(b"\x00\x00" * int(16000 * seconds))
    return output.getvalue()


class Response:
    def __init__(self, body, content_type):
        self.body = io.BytesIO(body)
        self.headers = {"Content-Type": content_type}

    def read(self, limit):
        return self.body.read(limit)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.body.close()


@patch.dict(os.environ, {"GNANI_API_KEY": "contract-test-secret"}, clear=True)
class GnaniContractTests(unittest.TestCase):
    def test_stt_uploads_documented_multipart_and_uses_transcript_field(self):
        audio = wav()
        response = Response(json.dumps({"success": True, "transcript": "ಇಪ್ಪತ್ತು ರೂಪಾಯಿ"}, ensure_ascii=False).encode(), "application/json; charset=utf-8")
        with patch.object(gnani._OPENER, "open", return_value=response) as open_mock:
            result = gnani.transcribe_wav(audio)
        request = open_mock.call_args.args[0]
        self.assertEqual(request.full_url, "https://api.vachana.ai/stt/v3")
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(request.get_header("X-api-key-id"), "contract-test-secret")
        self.assertEqual(request.get_header("User-agent"), gnani.USER_AGENT)
        self.assertIn("TaulSaathi/", request.get_header("User-agent"))
        self.assertEqual(open_mock.call_args.kwargs["timeout"], 25)
        message = BytesParser().parsebytes(("Content-Type: " + request.get_header("Content-type") + "\r\nMIME-Version: 1.0\r\n\r\n").encode() + request.data)
        fields = {part.get_param("name", header="content-disposition"): part.get_payload(decode=True) for part in message.get_payload()}
        self.assertEqual(fields, {"audio_file": audio, "language_code": b"kn-IN", "format": b"verbatim"})
        self.assertEqual(result["text"], "ಇಪ್ಪತ್ತು ರೂಪಾಯಿ")
        self.assertEqual(result["model"], "prisma-v2.5")
        self.assertEqual(result["language"], "kn-IN")
        self.assertGreaterEqual(result["elapsed_ms"], 0)

    def test_tts_requests_kannada_v25_voice_and_returns_binary_audio(self):
        audio = wav()
        with patch.object(gnani._OPENER, "open", return_value=Response(audio, "audio/wav")) as open_mock:
            self.assertEqual(gnani.synthesize("ಪರಿಶೀಲಿಸಿ"), (audio, "audio/wav"))
        request = open_mock.call_args.args[0]
        self.assertEqual(request.full_url, "https://api.vachana.ai/api/v1/tts/inference")
        payload = json.loads(request.data)
        self.assertEqual(payload["text"], "ಪರಿಶೀಲಿಸಿ")
        self.assertEqual(payload["language"], "kn-IN")
        self.assertEqual(payload["voice"], "Saanvi")
        self.assertEqual(payload["model"], "timbre-v2.5")
        self.assertEqual(payload["audio_config"]["container"], "wav")

    def test_english_uses_english_voice(self):
        with patch.object(gnani._OPENER, "open", return_value=Response(wav(), "audio/wav")) as open_mock:
            gnani.synthesize("Confirm the weight.", "en-IN")
        self.assertEqual(json.loads(open_mock.call_args.args[0].data)["voice"], "Kaveri")

    def test_tts_streaming_wav_header_is_normalized_without_changing_pcm(self):
        original = wav()
        streaming = bytearray(original)
        streaming[4:8] = struct.pack('<I', 0xFFFFFFFF)
        streaming[40:44] = struct.pack('<I', 0xFFFFFFFE)
        with patch.object(gnani._OPENER, 'open', return_value=Response(bytes(streaming), 'audio/wav')):
            normalized, _ = gnani.synthesize('ಪರಿಶೀಲಿಸಿ')
        with wave.open(io.BytesIO(normalized), 'rb') as recording:
            self.assertEqual(recording.getnframes(), 1600)
            self.assertEqual(recording.readframes(1600), original[44:])

    def test_tts_truncated_wav_without_streaming_sentinel_is_rejected(self):
        with patch.object(gnani._OPENER, 'open', return_value=Response(wav()[:-10], 'audio/wav')):
            with self.assertRaises(gnani.GnaniError) as error:
                gnani.synthesize('Check the rate.', 'en-IN')
        self.assertEqual(error.exception.code, 'invalid_upstream_response')

    def test_missing_key_never_opens_connection(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(gnani._OPENER, "open") as open_mock:
            with self.assertRaises(gnani.GnaniError) as caught:
                gnani.transcribe_wav(wav())
        self.assertEqual(caught.exception.code, "not_configured")
        open_mock.assert_not_called()

    def test_configuration_reports_no_secret_and_does_not_claim_verification(self):
        status = gnani.configuration_status()
        self.assertTrue(status["configured"])
        self.assertFalse(status["live_verified"])
        self.assertNotIn("contract-test-secret", json.dumps(status))

    def test_long_audio_is_rejected_before_network(self):
        with patch.object(gnani._OPENER, "open") as open_mock:
            with self.assertRaises(gnani.GnaniError) as caught:
                gnani.transcribe_wav(wav(30.01))
        self.assertEqual(caught.exception.code, "invalid_audio")
        open_mock.assert_not_called()

    def test_invalid_and_truncated_wav_are_rejected(self):
        with patch.object(gnani._OPENER, "open") as open_mock:
            for audio in (b"not WAV", wav()[:-10], wav(0)):
                with self.subTest(audio_size=len(audio)), self.assertRaises(gnani.GnaniError):
                    gnani.transcribe_wav(audio)
        open_mock.assert_not_called()

    def test_unsupported_language_is_rejected_before_network(self):
        with patch.object(gnani._OPENER, "open") as open_mock:
            with self.assertRaises(gnani.GnaniError) as caught:
                gnani.synthesize("hello", "xx-IN")
        self.assertEqual(caught.exception.code, "invalid_language")
        open_mock.assert_not_called()

    def test_upstream_http_error_is_sanitized_and_not_retried(self):
        error = urllib.error.HTTPError("https://api.vachana.ai/stt/v3", 403, "contract-test-secret", {}, io.BytesIO(b"private upstream payload"))
        with patch.object(gnani._OPENER, "open", side_effect=error) as open_mock:
            with self.assertRaises(gnani.GnaniError) as caught:
                gnani.transcribe_wav(wav())
        self.assertEqual(caught.exception.status, 403)
        self.assertNotIn("contract-test-secret", str(caught.exception))
        self.assertNotIn("private", str(caught.exception))
        self.assertEqual(open_mock.call_count, 1)

    def test_timeout_is_sanitized_and_not_retried(self):
        with patch.object(gnani._OPENER, "open", side_effect=TimeoutError("private secret")) as open_mock:
            with self.assertRaises(gnani.GnaniError) as caught:
                gnani.transcribe_wav(wav())
        self.assertEqual(caught.exception.code, "upstream_timeout")
        self.assertNotIn("private secret", str(caught.exception))
        self.assertEqual(open_mock.call_count, 1)

    def test_stt_rejects_legacy_or_failed_schemas(self):
        for payload in ({"text": "legacy"}, {"success": False, "transcript": "failed"}, {"success": True, "transcript": 42}):
            with self.subTest(payload=payload), patch.object(gnani._OPENER, "open", return_value=Response(json.dumps(payload).encode(), "application/json")):
                with self.assertRaises(gnani.GnaniError) as caught:
                    gnani.transcribe_wav(wav())
                self.assertEqual(caught.exception.code, "invalid_upstream_response")

    def test_tts_refuses_json_error_disguised_as_success(self):
        with patch.object(gnani._OPENER, "open", return_value=Response(b'{"error":"secret"}', "application/json")):
            with self.assertRaises(gnani.GnaniError) as caught:
                gnani.synthesize("Confirm")
        self.assertEqual(caught.exception.code, "invalid_upstream_response")
        self.assertNotIn("secret", str(caught.exception))

    def test_oversize_response_is_bounded(self):
        with patch.object(gnani._OPENER, "open", return_value=Response(b"x" * (512 * 1024 + 2), "application/json")):
            with self.assertRaises(gnani.GnaniError) as caught:
                gnani.transcribe_wav(wav())
        self.assertEqual(caught.exception.code, "upstream_response_too_large")

    def test_redirect_handler_does_not_forward_key(self):
        self.assertIsNone(gnani._NoRedirect().redirect_request(None, None, 302, "", {}, "https://another.example"))


if __name__ == "__main__":
    unittest.main()
