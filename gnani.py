"""Small server-side Gnani REST adapter, using Python's standard library only.

Contract verified 2026-10-22 at docs.gnani.ai/api/STT/speech-to-text and
docs.gnani.ai/api/TTS/tts-inference. No API calls happen at import time.
Set GNANI_API_KEY in the process environment before making an explicit live call.
"""

from __future__ import annotations

import io
import json
import os
import socket
import time
import urllib.error
import urllib.request
import uuid
import wave

BASE_URL = "https://api.vachana.ai"
STT_MODEL = "prisma-v2.5"
TTS_MODEL = "timbre-v2.5"
DEFAULT_LANGUAGE = "kn-IN"
TIMEOUT_SECONDS = 25
MAX_AUDIO_SECONDS = 30  # App limit conserves credits; upstream REST permits 60 s.
MAX_AUDIO_BYTES = 8 * 1024 * 1024
MAX_RESPONSE_BYTES = 16 * 1024 * 1024
MAX_TEXT_CHARS = 1500
USER_AGENT = "TaulSaathi/0.1 (Gnani API integration; Python urllib)"

# These voices belong to Timbre v2.5, not v3.0.
VOICES = {
    "bn-IN": "Kirra",
    "en-IN": "Kaveri",
    "gu-IN": "Falak",
    "hi-IN": "Nalini",
    "kn-IN": "Saanvi",
    "ml-IN": "Reshma",
    "mr-IN": "Zahira",
    "pa-IN": "Mehuli",
    "ta-IN": "Asmita",
    "te-IN": "Suhana",
}


class GnaniError(RuntimeError):
    """A safe, user-facing error with no upstream response or secret content."""

    def __init__(self, code: str, message: str, status: int | None = None):
        super().__init__(message)
        self.code = code
        self.status = status


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Never forward the API-key header to a redirected destination.
        return None


_OPENER = urllib.request.build_opener(_NoRedirect())


def configuration_status() -> dict:
    """Report configuration only. This does not verify the key or spend credits."""
    return {
        "configured": bool(os.environ.get("GNANI_API_KEY", "").strip()),
        "stt_model": STT_MODEL,
        "tts_model": TTS_MODEL,
        "default_language": DEFAULT_LANGUAGE,
        "languages": sorted(VOICES),
        "max_audio_seconds": MAX_AUDIO_SECONDS,
        "live_verified": False,
    }


def _api_key() -> str:
    key = os.environ.get("GNANI_API_KEY", "").strip()
    if not key:
        raise GnaniError("not_configured", "Set GNANI_API_KEY on the local server to use live speech.")
    if any(char in key for char in "\r\n"):
        raise GnaniError("invalid_configuration", "The API key configuration is invalid.")
    return key


def _validate_language(language: str) -> str:
    if not isinstance(language, str) or language not in VOICES:
        raise GnaniError("invalid_language", "Choose a supported speech language.")
    return language


def _request(path: str, body: bytes, content_type: str, max_bytes: int) -> tuple[bytes, str]:
    request = urllib.request.Request(
        BASE_URL + path,
        data=body,
        method="POST",
        headers={"X-API-Key-ID": _api_key(), "Content-Type": content_type,
                 "User-Agent": USER_AGENT, "Accept": "application/json, audio/wav"},
    )
    try:
        with _OPENER.open(request, timeout=TIMEOUT_SECONDS) as response:
            content = response.read(max_bytes + 1)
            response_type = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
    except urllib.error.HTTPError as error:
        status = error.code
        error.close()
        if status in (401, 403):
            message = "Gnani denied access. Check the API key, account access and available credits."
        elif status == 429:
            message = "Gnani is rate limiting requests. Wait before trying again."
        elif status >= 500:
            message = "Gnani is temporarily unavailable. Try again later."
        else:
            message = "Gnani rejected the speech request. Check the audio or language settings."
        raise GnaniError("upstream_http_error", message, status) from None
    except (TimeoutError, socket.timeout):
        raise GnaniError("upstream_timeout", "The speech request timed out. Try again later.") from None
    except (urllib.error.URLError, OSError):
        raise GnaniError("upstream_connection_error", "Could not reach Gnani. Check the connection and try again.") from None
    # No automatic retry: a lost response may already have consumed credits.
    if len(content) > max_bytes:
        raise GnaniError("upstream_response_too_large", "The speech response exceeded the local size limit.")
    return content, response_type


def transcribe_wav(audio: bytes, language: str = DEFAULT_LANGUAGE) -> dict:
    """Transcribe a 30 s-or-shorter WAV through Prisma; return normalized metadata.

    This is an explicit live network action and can consume programme credits.
    Returned text is raw spoken-form output; transaction validation is separate.
    """
    language = _validate_language(language)
    if not isinstance(audio, bytes) or not audio or len(audio) > MAX_AUDIO_BYTES:
        raise GnaniError("invalid_audio", "Upload a WAV recording smaller than 8 MiB.")
    try:
        with wave.open(io.BytesIO(audio), "rb") as recording:
            duration = recording.getnframes() / recording.getframerate()
            if recording.getnframes() <= 0 or duration > MAX_AUDIO_SECONDS:
                raise GnaniError("invalid_audio", "Record between a moment and 30 seconds of speech.")
            # Detect truncated containers before spending credits on an upload.
            expected_size = recording.getnframes() * recording.getnchannels() * recording.getsampwidth()
            if len(recording.readframes(recording.getnframes())) != expected_size:
                raise GnaniError("invalid_audio", "The WAV recording is incomplete.")
    except (wave.Error, EOFError, ZeroDivisionError, ValueError):
        raise GnaniError("invalid_audio", "The recording must be a valid uncompressed WAV file.") from None

    boundary = "taulsaathi-" + uuid.uuid4().hex
    parts = []
    for name, value in (("language_code", language), ("format", "verbatim")):
        parts.append(
            f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode("utf-8")
        )
    parts.append(
        f'--{boundary}\r\nContent-Disposition: form-data; name="audio_file"; filename="speech.wav"\r\n'
        'Content-Type: audio/wav\r\n\r\n'.encode("utf-8") + audio + b"\r\n"
    )
    parts.append(f"--{boundary}--\r\n".encode("ascii"))
    started = time.perf_counter()
    raw, response_type = _request(
        "/stt/v3", b"".join(parts), f"multipart/form-data; boundary={boundary}", 512 * 1024
    )
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise GnaniError("invalid_upstream_response", "Gnani returned an unreadable transcription response.") from None
    if (
        response_type != "application/json"
        or not isinstance(payload, dict)
        or payload.get("success") is not True
        or not isinstance(payload.get("transcript"), str)
    ):
        raise GnaniError("invalid_upstream_response", "Gnani did not return a successful transcription.")
    return {
        "text": payload["transcript"],
        "request_id": payload.get("request_id") if isinstance(payload.get("request_id"), str) else None,
        "model": STT_MODEL,
        "language": language,
        "elapsed_ms": round((time.perf_counter() - started) * 1000),
    }


def synthesize(text: str, language: str = DEFAULT_LANGUAGE) -> tuple[bytes, str]:
    """Synthesize reviewed confirmation text as WAV through Timbre v2.5."""
    language = _validate_language(language)
    if not isinstance(text, str) or not text.strip() or len(text) > MAX_TEXT_CHARS:
        raise GnaniError("invalid_text", "Provide 1 to 1,500 characters of confirmation text.")
    body = json.dumps(
        {
            "text": text.strip(),
            "voice": VOICES[language],
            "model": TTS_MODEL,
            "language": language,
            "speed": 1.0,
            "audio_config": {
                "sample_rate": 24000,
                "num_channels": 1,
                "sample_width": 2,
                "encoding": "linear_pcm",
                "container": "wav",
            },
        },
        ensure_ascii=False,
    ).encode("utf-8")
    audio, response_type = _request("/api/v1/tts/inference", body, "application/json", MAX_RESPONSE_BYTES)
    if response_type not in ("audio/wav", "audio/x-wav", "audio/wave") or not (
        len(audio) >= 12 and audio[:4] == b"RIFF" and audio[8:12] == b"WAVE"
    ):
        raise GnaniError("invalid_upstream_response", "Gnani did not return WAV audio.")
    # The observed REST service can leave a streaming length sentinel in RIFF.
    # Canonicalize only returned PCM; uploads still reject truncated containers.
    try:
        with wave.open(io.BytesIO(audio), "rb") as recording:
            params = recording.getparams()
            frame_size = params.nchannels * params.sampwidth
            declared_bytes = params.nframes * frame_size
            pcm = recording.readframes(params.nframes)
        if not pcm or len(pcm) % frame_size:
            raise ValueError("Incomplete PCM frames")
        streaming_lengths = {0xFFFFFFFF, 0xFFFFFFFE, 0x7FFFFFFF, 0x7FFFFFFE}
        if len(pcm) != declared_bytes and declared_bytes not in streaming_lengths:
            raise ValueError("Truncated PCM")
        normalized = io.BytesIO()
        with wave.open(normalized, "wb") as recording:
            recording.setnchannels(params.nchannels)
            recording.setsampwidth(params.sampwidth)
            recording.setframerate(params.framerate)
            recording.writeframes(pcm)
        audio = normalized.getvalue()
    except (wave.Error, EOFError, ValueError, ZeroDivisionError):
        raise GnaniError("invalid_upstream_response", "Gnani returned an incomplete or unsupported WAV container.") from None
    return audio, "audio/wav"
