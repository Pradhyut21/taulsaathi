"""Local research prototype. Run: python app.py; browse http://127.0.0.1:8765."""
from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import json
import threading
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import domain
import gnani

ROOT = Path(__file__).resolve().parent
EXAMPLES = [
    {"id":"kannada", "title":"Kannada + English · clear numbers", "language":"kn-IN",
     "transcript":"ಕಾಗದ, ಒಟ್ಟು ೨೫ ಕೆಜಿ, ಚೀಲ ೨ ಕೆಜಿ, ದರ ೨೦ ರೂಪಾಯಿ ಪ್ರತಿ ಕೆಜಿ"},
    {"id":"words", "title":"Kannada number words · bounded vocabulary", "language":"kn-IN",
     "transcript":"ಕಾಗದ, ಒಟ್ಟು ಇಪ್ಪತ್ತೈದು ಕೆಜಿ, ಚೀಲ ಎರಡು ಕೆಜಿ, ದರ ಇಪ್ಪತ್ತು ರೂಪಾಯಿ ಪ್ರತಿ ಕೆಜಿ"},
    {"id":"correction", "title":"Spoken correction · must review", "language":"kn-IN",
     "transcript":"ಕಬ್ಬಿಣ, gross 25 kg, tare 2 kg, rate 15 rupees per kg, rate 50 rupees per kg ಅಲ್ಲ 15 rupees per kg"},
    {"id":"missing", "title":"Missing unit · cannot confirm", "language":"en-IN",
     "transcript":"paper, gross 25 kg, tare 2 kg, rate 20"},
    {"id":"decimal", "title":"Decimal quantities · exact arithmetic", "language":"en-IN",
     "transcript":"paper, gross 12.5 kg, tare half kg, rate 14 rupees per kg"},
]


class Store:
    def __init__(self):
        self.lock = threading.RLock()
        self.drafts = {}
        self.transcripts = {}
        self.audio_cache = {}
        self.live_lock = threading.Lock()

    def get(self, identifier):
        if not isinstance(identifier, str) or identifier not in self.drafts:
            raise ValueError("Draft not found. Create a draft first.")
        return self.drafts[identifier]

    def insert(self, draft):
        if len(self.drafts) >= 100:
            raise ValueError("Local session is full. Export your records, then restart the app.")
        self.drafts[draft["id"]] = draft
        return draft


STORE = Store()


class Handler(BaseHTTPRequestHandler):
    server_version = "TaulSaathi/0.1"

    def log_message(self, format, *args):
        # Never log request bodies, API keys or transcripts.
        return

    def _send(self, status, content, content_type="application/json; charset=utf-8", download=None):
        if not isinstance(content, bytes):
            content = json.dumps(content, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; media-src 'self' blob:; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'")
        if download:
            self.send_header("Content-Disposition", f'attachment; filename="{download}"')
        self.end_headers()
        self.wfile.write(content)

    def _allowed_host(self):
        port = self.server.server_port
        return self.headers.get("Host") in (f"127.0.0.1:{port}", f"localhost:{port}")

    def do_GET(self):
        if not self._allowed_host():
            return self._send(403, {"error":"Open the app using its localhost address."})
        parsed = urlsplit(self.path)
        try:
            if parsed.path == "/api/status":
                status = gnani.configuration_status()
                return self._send(200, {**status, "gnani_configured":status["configured"],
                                        "languages":["kn-IN", "en-IN"], "storage":"session memory only"})
            if parsed.path == "/api/examples":
                return self._send(200, EXAMPLES)
            if parsed.path == "/api/receipt":
                identifier = parse_qs(parsed.query).get("id", [None])[0]
                with STORE.lock:
                    draft = STORE.get(identifier)
                    if draft["status"] != "confirmed":
                        raise ValueError("Confirm the current revision before exporting.")
                    export = {**draft, "notice":"Operator-confirmed record; no payment, identity, scale or market price verified.",
                              "software":"TaulSaathi research prototype 0.1"}
                return self._send(200, export, download=f"taulsaathi-{identifier[:8]}-r{draft['revision']}.json")
            static_paths = {"/":"index.html", "/index.html":"index.html", "/app.js":"app.js", "/style.css":"style.css"}
            if parsed.path in static_paths:
                file = ROOT / "static" / static_paths[parsed.path]
                types = {".html":"text/html; charset=utf-8", ".css":"text/css; charset=utf-8", ".js":"text/javascript; charset=utf-8"}
                return self._send(200, file.read_bytes(), types[file.suffix])
            return self._send(404, {"error":"Not found."})
        except ValueError as error:
            self._send(400, {"error":str(error)})
        except OSError:
            self._send(500, {"error":"A local app file could not be loaded."})

    def do_POST(self):
        port = self.server.server_port
        origin = self.headers.get("Origin")
        if not self._allowed_host() or (origin and origin not in (f"http://127.0.0.1:{port}", f"http://localhost:{port}")):
            return self._send(403, {"error":"Only the local app can perform this action."})
        if self.headers.get("Content-Type", "").split(";", 1)[0] != "application/json":
            return self._send(415, {"error":"Send application/json."})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 12 * 1024 * 1024:
                raise ValueError("Request is empty or too large.")
            data = json.loads(self.rfile.read(length))
            if not isinstance(data, dict):
                raise ValueError("Expected a JSON object.")
            route = urlsplit(self.path).path
            if route == "/api/draft":
                source = data.get("source", "typed")
                transcript, language = data.get("transcript"), data.get("language", "kn-IN")
                if source == "gnani":
                    with STORE.lock:
                        verified = STORE.transcripts.get(data.get("transcription_id"))
                    if not verified or verified["transcript"] != transcript or verified["language"] != language:
                        raise ValueError("Edited transcripts must be labelled typed. Re-transcribe for a live-source draft.")
                if source == "synthetic" and not any(e["transcript"] == transcript and e["language"] == language for e in EXAMPLES):
                    source = "typed"
                draft = domain.create_draft(transcript, language, source)
                if source == 'gnani':
                    draft['speech_evidence'] = {key: verified.get(key) for key in
                        ('model', 'request_id', 'elapsed_ms', 'audio_sha256', 'audio_bytes', 'processed_at_utc')}
                with STORE.lock:
                    STORE.insert(draft)
                return self._send(200, draft)
            if route in ("/api/revise", "/api/review", "/api/confirm"):
                with STORE.lock:
                    draft = STORE.get(data.get("id"))
                    revision = data.get("revision")
                    if isinstance(revision, bool) or not isinstance(revision, int):
                        raise ValueError("Supply the current revision number.")
                    if route == "/api/revise":
                        updated = domain.revise(draft, revision, data.get("field"), data.get("value"), data.get("reason"))
                    elif route == "/api/review":
                        updated = domain.resolve_review(draft, revision, data.get("reason"))
                    else:
                        updated = domain.confirm(draft, revision, data.get("reviewed"))
                    if route != '/api/confirm':
                        updated.pop('readback_evidence', None)
                    STORE.drafts[updated["id"]] = updated
                return self._send(200, updated)
            if route in ("/api/transcribe", "/api/readback"):
                if not STORE.live_lock.acquire(blocking=False):
                    return self._send(429, {"error":"A speech request is already running. Wait for it to finish."})
                try:
                    if route == "/api/transcribe":
                        language = data.get("language", "kn-IN")
                        if language not in ("kn-IN", "en-IN"):
                            raise ValueError("Choose Kannada or English.")
                        encoded = data.get("audio_base64")
                        if not isinstance(encoded, str):
                            raise ValueError("Choose a WAV recording first.")
                        try:
                            audio = base64.b64decode(encoded, validate=True)
                        except (binascii.Error, ValueError):
                            raise ValueError("Invalid audio encoding.") from None
                        result = gnani.transcribe_wav(audio, language)
                        identifier = uuid.uuid4().hex
                        response = {"transcript":result["text"].strip(), "model":result["model"], "elapsed_ms":result["elapsed_ms"],
                                    "language":language, "transcription_id":identifier,
                                    "request_id":result.get('request_id'), "audio_sha256":hashlib.sha256(audio).hexdigest(),
                                    "audio_bytes":len(audio), "processed_at_utc":datetime.now(timezone.utc).isoformat()}
                        with STORE.lock:
                            if len(STORE.transcripts) >= 100:
                                STORE.transcripts.pop(next(iter(STORE.transcripts)))
                            STORE.transcripts[identifier] = response
                        return self._send(200, response)
                    with STORE.lock:
                        draft = STORE.get(data.get("id"))
                        requested_revision = data.get("revision")
                        if isinstance(requested_revision, bool) or not isinstance(requested_revision, int):
                            raise ValueError("Supply the current revision number.")
                        if draft["revision"] != requested_revision:
                            raise ValueError("Readback request is stale. Use the current revision.")
                        if draft["issues"]:
                            raise ValueError("Resolve all issues before generating a readback.")
                        cache_key = (draft["id"], draft["revision"])
                        text, language = draft["readback_text"], draft["language"]
                        cached = STORE.audio_cache.get(cache_key)
                    if cached is None:
                        cached = gnani.synthesize(text, language)
                        with STORE.lock:
                            if STORE.get(draft["id"])["revision"] != requested_revision:
                                raise ValueError("Draft changed while audio was generated. Request the current readback.")
                            if len(STORE.audio_cache) >= 20:
                                STORE.audio_cache.pop(next(iter(STORE.audio_cache)))
                            STORE.audio_cache[cache_key] = cached
                    with STORE.lock:
                        if STORE.get(draft["id"])["revision"] != requested_revision:
                            raise ValueError("Draft changed. Request the current readback.")
                        STORE.get(draft['id'])['readback_evidence'] = {
                            'model':gnani.TTS_MODEL, 'voice':gnani.VOICES[language],
                            'generated_for_revision':requested_revision, 'audio_sha256':hashlib.sha256(cached[0]).hexdigest(),
                            'audio_bytes':len(cached[0])}
                        return self._send(200, cached[0], cached[1])
                finally:
                    STORE.live_lock.release()
            return self._send(404, {"error":"Not found."})
        except gnani.GnaniError as error:
            result = {"error":str(error), "code":error.code}
            if error.status is not None:
                result["upstream_status"] = error.status
            self._send(400 if error.code.startswith(("invalid", "not_")) else 502, result)
        except (ValueError, TypeError, KeyError) as error:
            message = str(error) if isinstance(error, ValueError) else "Invalid request fields."
            self._send(400, {"error":message})
        except Exception:
            self._send(500, {"error":"The local app could not complete this request."})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"TaulSaathi local prototype: http://127.0.0.1:{server.server_port}", flush=True)
    print("Drafts remain in session memory. Export confirmed records before closing. Ctrl+C stops.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
