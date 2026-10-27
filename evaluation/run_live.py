"""Run up to five explicit live speech checks; never retries or submits entries.

Examples (from the project directory):
  python evaluation/run_live.py --manifest evaluation/live-prompts.json --output-dir evaluation/live-results --limit 1
  python evaluation/run_live.py --wav work/sample.wav --language kn-IN --scenario-provenance fictional --audio-provenance human_read_fictional_prompt --output-dir evaluation/live-results

GNANI_API_KEY must already be set locally. Never pass a key as a CLI argument.
No API request occurs on import. All scenarios must use fictional transaction data.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import sys
import time
import urllib.error
import urllib.request
import uuid
import wave
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urlsplit

PROJECT = Path(__file__).resolve().parents[1]
if str(PROJECT) not in sys.path:
    sys.path.insert(0, str(PROJECT))

import domain
import gnani

LANGUAGES = ("kn-IN", "en-IN")
AUDIO_PROVENANCE = ("human_read_fictional_prompt", "tts_generated", "unknown", "unrecorded")
NUMERIC_KEYS = {"gross_kg", "tare_kg", "net_kg", "rate_inr_per_kg", "total_inr"}
SAFE_ERROR_CODES = {
    "upstream_http_error", "upstream_timeout", "upstream_connection_error",
    "upstream_response_too_large", "invalid_upstream_response", "not_configured",
    "invalid_configuration", "invalid_audio", "invalid_text", "invalid_language",
}


class LocalBackend:
    """Use the already-running loopback server; never accesses API credentials."""

    def __init__(self, base_url: str):
        parsed = urlsplit(base_url)
        try:
            valid = (parsed.scheme == "http" and parsed.hostname in ("127.0.0.1", "localhost")
                     and parsed.port is not None and 1 <= parsed.port <= 65535
                     and parsed.path in ("", "/") and not parsed.query and not parsed.fragment
                     and parsed.username is None and parsed.password is None)
        except ValueError:
            valid = False
        if not valid:
            raise ValueError("Backend URL must be http://127.0.0.1:PORT or http://localhost:PORT.")
        self.base_url = base_url.rstrip("/")
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), gnani._NoRedirect())

    def request(self, route, data=None):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8") if data is not None else None
        request = urllib.request.Request(self.base_url + route, data=body,
                                         headers={"Content-Type": "application/json"} if body is not None else {})
        try:
            with self.opener.open(request, timeout=35) as response:
                content = response.read(gnani.MAX_RESPONSE_BYTES + 1)
                mimetype = response.headers.get("Content-Type", "").split(";", 1)[0].strip()
            if len(content) > gnani.MAX_RESPONSE_BYTES:
                raise gnani.GnaniError("invalid_backend_response", "Local backend response is too large.")
            return json.loads(content) if mimetype == "application/json" else content, mimetype
        except urllib.error.HTTPError as error:
            status = error.code
            safe_code, upstream_status = "backend_http_error", None
            try:
                # Read only a small JSON error. Never retain or echo its message,
                # raw body, transcript, request headers or arbitrary error codes.
                if error.headers.get("Content-Type", "").split(";", 1)[0].strip().lower() == "application/json":
                    error_body = error.read(8193)
                    payload = json.loads(error_body) if len(error_body) <= 8192 else None
                    if isinstance(payload, dict):
                        if isinstance(payload.get("code"), str) and payload["code"] in SAFE_ERROR_CODES:
                            safe_code = payload["code"]
                        numeric_status = payload.get("upstream_status")
                        if isinstance(numeric_status, int) and not isinstance(numeric_status, bool) and 100 <= numeric_status <= 599:
                            upstream_status = numeric_status
            except (ValueError, OSError):
                pass
            finally:
                error.close()
            safe_error = gnani.GnaniError(safe_code, "Local backend rejected the speech operation.", status)
            safe_error.upstream_status = upstream_status
            raise safe_error from None
        except (urllib.error.URLError, OSError):
            raise gnani.GnaniError("backend_connection_error", "Local backend could not be reached.") from None
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise gnani.GnaniError("invalid_backend_response", "Local backend returned unreadable data.") from None

    def configured(self):
        payload, _ = self.request("/api/status")
        return bool(payload.get("gnani_configured")) if isinstance(payload, dict) else False

    def transcribe(self, audio: bytes, language: str):
        payload, _ = self.request("/api/transcribe", {"language": language, "audio_base64": base64.b64encode(audio).decode("ascii")})
        if not isinstance(payload, dict):
            raise gnani.GnaniError("invalid_backend_response", "Local backend did not return transcription data.")
        return {"text": payload["transcript"], "model": payload["model"], "elapsed_ms": payload["elapsed_ms"],
                "transcription_id": payload["transcription_id"]}

    def readback(self, transcript: str, language: str, transcription_id: str):
        draft, _ = self.request("/api/draft", {"transcript": transcript, "language": language,
                                               "source": "gnani", "transcription_id": transcription_id})
        return self.request("/api/readback", {"id": draft["id"], "revision": draft["revision"]})


def _error_metadata(error: gnani.GnaniError, started: float) -> dict:
    metadata = {"status": "error", "code": error.code, "http_status": error.status,
                "measured_elapsed_ms": round((time.perf_counter() - started) * 1000)}
    upstream_status = getattr(error, "upstream_status", None)
    if upstream_status is not None:
        metadata["upstream_http_status"] = upstream_status
    return metadata


def _stop_error_reason(error: gnani.GnaniError, backend: LocalBackend | None) -> str | None:
    if (error.code in ("not_configured", "invalid_configuration") or error.status in (401, 403, 429)
            or getattr(error, "upstream_status", None) in (401, 403, 429)):
        return "access_or_rate_limit_error"
    # Older local servers sanitize upstream auth failures into HTTP 502. Stop
    # conservatively instead of spending every remaining clip on that failure.
    if backend and (error.code == "upstream_http_error" or (error.status == 502 and error.code == "backend_http_error")):
        return "backend_upstream_error"
    return None


def _limit(value: str) -> int:
    number = int(value)
    if not 1 <= number <= 5:
        raise argparse.ArgumentTypeError("Choose 1 to 5 clips per explicit run.")
    return number


def load_cases(manifest: Path) -> list[dict]:
    payload = json.loads(manifest.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict) or not isinstance(payload.get("clips"), list):
        raise ValueError("Manifest must contain a clips list.")
    cases = []
    seen = set()
    for item in payload["clips"]:
        if not isinstance(item, dict):
            raise ValueError("Every clip must be an object.")
        identifier = item.get("id")
        if not isinstance(identifier, str) or not identifier or identifier in seen:
            raise ValueError("Each clip requires a unique nonempty id.")
        seen.add(identifier)
        if item.get("language") not in LANGUAGES:
            raise ValueError("Manifest language must be kn-IN or en-IN.")
        if item.get("scenario_provenance") != "fictional":
            raise ValueError("Only declared fictional transaction scenarios are accepted.")
        if item.get("audio_provenance") not in AUDIO_PROVENANCE:
            raise ValueError("Declare each clip's audio_provenance.")
        if not isinstance(item.get("wav"), str) or not item["wav"]:
            raise ValueError("Every clip needs an explicit local WAV path.")
        gold = item.get("gold")
        if gold is not None and not isinstance(gold, dict):
            raise ValueError("Gold must be an object when supplied.")
        cases.append({**item, "wav_path": (manifest.parent / item["wav"]).resolve()})
    if not cases:
        raise ValueError("The manifest is empty.")
    return cases


def audio_metadata(path: Path) -> tuple[bytes, dict]:
    if path.suffix.lower() != ".wav":
        raise ValueError("Select a local .wav file.")
    with path.open("rb") as file:
        audio = file.read(gnani.MAX_AUDIO_BYTES + 1)
    if not audio or len(audio) > gnani.MAX_AUDIO_BYTES:
        raise ValueError("WAV must be nonempty and smaller than 8 MiB.")
    try:
        with wave.open(io.BytesIO(audio), "rb") as recording:
            duration = recording.getnframes() / recording.getframerate()
            if not 0 < duration <= gnani.MAX_AUDIO_SECONDS:
                raise ValueError("Use a recording no longer than 30 seconds.")
            expected = recording.getnframes() * recording.getnchannels() * recording.getsampwidth()
            if len(recording.readframes(recording.getnframes())) != expected:
                raise ValueError("The WAV is truncated.")
            metadata = {
                "filename": path.name,
                "sha256": hashlib.sha256(audio).hexdigest(),
                "bytes": len(audio),
                "duration_seconds": round(duration, 6),
                "sample_rate": recording.getframerate(),
                "channels": recording.getnchannels(),
                "sample_width_bytes": recording.getsampwidth(),
            }
    except (wave.Error, EOFError, ZeroDivisionError) as error:
        raise ValueError("Input is not a complete uncompressed WAV.") from error
    return audio, metadata


def _same(key: str, actual, expected) -> bool:
    if actual is None or expected is None:
        return actual is expected
    if key in NUMERIC_KEYS:
        try:
            return Decimal(str(actual)) == Decimal(str(expected))
        except InvalidOperation:
            return False
    return actual == expected


def evaluate_gold(draft: dict, gold: dict | None) -> dict:
    if gold is None:
        return {"status": "not_scored", "reason": "No human-declared expected fields supplied."}
    checks = []
    for group in ("fields", "computed"):
        values = gold.get(group, {})
        if not isinstance(values, dict):
            raise ValueError("Gold fields and computed values must be objects.")
        for key, expected in values.items():
            if key not in draft[group]:
                raise ValueError("Gold contains an unsupported field.")
            actual = draft[group][key]
            checks.append({"field": f"{group}.{key}", "expected": expected, "actual": actual, "match": _same(key, actual, expected)})
    if "must_block" in gold:
        if not isinstance(gold["must_block"], bool):
            raise ValueError("Gold must_block must be true or false.")
        actual = bool(draft["issues"])
        checks.append({"field": "must_block", "expected": gold["must_block"], "actual": actual, "match": actual == gold["must_block"]})
    return {"status": "compared", "checks": checks, "all_match": all(check["match"] for check in checks) if checks else None}


def run_cases(cases: list[dict], output_dir: Path, limit: int = 5, tts: bool = False, save_tts_audio: bool = False, base_url: str | None = None) -> dict:
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 5:
        raise ValueError("Choose 1 to 5 clips per run.")
    if save_tts_audio and not tts:
        raise ValueError("Saving synthesized audio also requires --tts.")
    backend = LocalBackend(base_url) if base_url else None
    report = {
        "schema_version": 1,
        "run_id": uuid.uuid4().hex,
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "pending",
        "models": {"stt": gnani.STT_MODEL, "tts": gnani.TTS_MODEL},
        "limit": limit,
        "tts_enabled": tts,
        "transport": "local_backend" if backend else "direct_gnani_adapter",
        "api_calls": {"stt": 0, "tts": 0, "total": 0},
        "call_count_semantics": ("Requested speech operations; backend readback can be cached. Billed API calls/credits unknown."
                                  if backend else "Attempted adapter invocations; no automatic retries. Provider billing is unknown."),
        "notes": [
            "Fictional scenarios. Human-read scripts and TTS audio are separate provenance categories.",
            "Raw transcripts and measured results only; no WER without a verified verbatim reference.",
            "Parsed fields are unconfirmed hypotheses. This run does not confirm receipts or execute payments.",
            "Audio noise/accent conditions are declarations, not independently verified measurements.",
        ],
        "clips": [],
    }
    # Presence check only. The key is neither returned nor logged.
    try:
        configured = backend.configured() if backend else gnani.configuration_status()["configured"]
    except gnani.GnaniError as error:
        report.update(status="backend_error", error_code=error.code)
        return report
    if not configured:
        report["status"] = "not_configured"
        report["error"] = "The selected speech server is not configured. No speech calls made."
        return report

    for case in cases[:limit]:
        record = {
            "id": case["id"], "language": case["language"],
            "scenario_provenance": case["scenario_provenance"],
            "audio_provenance": case["audio_provenance"],
            "declared_condition": case.get("condition", "unspecified"),
            "status": "pending",
        }
        report["clips"].append(record)
        try:
            if case["scenario_provenance"] != "fictional":
                raise ValueError("Explicitly declare fictional scenario provenance before sending audio.")
            if case["audio_provenance"] == "unrecorded":
                raise ValueError("Record the fictional script and set its actual audio provenance first.")
            audio, metadata = audio_metadata(case["wav_path"])
            record["input"] = metadata
            # Validate gold locally before spending credits.
            evaluate_gold(domain.create_draft("preflight", case["language"], "typed"), case.get("gold"))
        except (OSError, ValueError) as error:
            record.update(status="input_error", error=str(error) if isinstance(error, ValueError) else "Local WAV could not be read.")
            continue

        started = time.perf_counter()
        report["api_calls"]["stt"] += 1
        try:
            result = backend.transcribe(audio, case["language"]) if backend else gnani.transcribe_wav(audio, case["language"])
            transcript = result["text"]
            if not isinstance(transcript, str):
                raise ValueError("Invalid normalized transcription response.")
            record["stt"] = {"status": "success", "raw_transcript": transcript, "model": result["model"],
                             "adapter_elapsed_ms": result["elapsed_ms"], "measured_elapsed_ms": round((time.perf_counter() - started) * 1000)}
        except gnani.GnaniError as error:
            record.update(status="stt_error", stt=_error_metadata(error, started))
            # Authentication/credit/rate-limit failures cannot improve by consuming more clips.
            stop_reason = _stop_error_reason(error, backend)
            if stop_reason:
                report["stopped_early"] = stop_reason
                break
            continue
        except Exception:
            record.update(status="stt_error", stt={"status": "error", "code": "unexpected_local_error",
                                                    "measured_elapsed_ms": round((time.perf_counter() - started) * 1000)})
            continue

        try:
            draft = domain.create_draft(transcript, case["language"], "gnani")
            record["parsed"] = {"fields": draft["fields"], "computed": draft["computed"], "issues": draft["issues"], "can_confirm": draft["can_confirm"]}
            record["evaluation"] = evaluate_gold(draft, case.get("gold"))
        except ValueError:
            record.update(status="parse_error", evaluation={"status": "not_scored", "reason": "Returned transcript could not form a valid draft."})
            continue
        record["status"] = "success"
        if tts:
            if draft["issues"]:
                record["tts"] = {"status": "skipped", "reason": "Blocking draft issues; review/correct fields before readback."}
                continue
            report["api_calls"]["tts"] += 1
            started = time.perf_counter()
            try:
                generated, mimetype = (backend.readback(transcript, case["language"], result["transcription_id"])
                                       if backend else gnani.synthesize(draft["readback_text"], case["language"]))
                record["tts"] = {"status": "success", "model": gnani.TTS_MODEL, "input_status": "unconfirmed_machine_draft",
                                 "input_text": draft["readback_text"], "mimetype": mimetype, "bytes": len(generated),
                                 "sha256": hashlib.sha256(generated).hexdigest(), "measured_elapsed_ms": round((time.perf_counter() - started) * 1000)}
                if save_tts_audio:
                    output_dir.mkdir(parents=True, exist_ok=True)
                    filename = f"tts-{report['run_id']}-{len(report['clips']):02d}.wav"
                    (output_dir / filename).write_bytes(generated)
                    record["tts"]["saved_audio_filename"] = filename
            except gnani.GnaniError as error:
                record["tts"] = _error_metadata(error, started)
                record["status"] = "tts_error"
                stop_reason = _stop_error_reason(error, backend)
                if stop_reason:
                    report["stopped_early"] = stop_reason
                    break
            except Exception:
                record["tts"] = {"status": "error", "code": "unexpected_local_error"}
                record["status"] = "tts_error"
    report["api_calls"]["total"] = report["api_calls"]["stt"] + report["api_calls"]["tts"]
    report["status"] = "complete" if report["clips"] and all(c["status"] == "success" for c in report["clips"]) else "partial"
    compared = [c["evaluation"] for c in report["clips"] if c.get("evaluation", {}).get("status") == "compared"]
    checks = [check for evaluation in compared for check in evaluation["checks"]]
    report["summary"] = {"clips_attempted": len(report["clips"]), "clips_with_stt_success": sum("raw_transcript" in c.get("stt", {}) for c in report["clips"]),
                         "gold_checks_compared": len(checks), "gold_checks_matching": sum(check["match"] for check in checks)}
    report["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    inputs = parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument("--manifest", type=Path)
    inputs.add_argument("--wav", type=Path)
    parser.add_argument("--language", choices=LANGUAGES, default="kn-IN", help="Language for --wav; manifests declare each language.")
    parser.add_argument("--audio-provenance", choices=AUDIO_PROVENANCE, default="unknown", help="Actual origin of --wav, never inferred.")
    parser.add_argument("--scenario-provenance", choices=("fictional", "unknown"), default="unknown", help="Explicitly declare fictional data for a single --wav.")
    parser.add_argument("--base-url", help="Use an already-configured local app at http://127.0.0.1:PORT; does not read local API credentials.")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--limit", type=_limit, default=5)
    parser.add_argument("--tts", action="store_true", help="Explicitly spend credits testing draft readback; default off.")
    parser.add_argument("--save-tts-audio", action="store_true", help="Also save generated WAVs; requires --tts.")
    args = parser.parse_args(argv)
    if args.save_tts_audio and not args.tts:
        parser.error("--save-tts-audio requires --tts")
    try:
        cases = load_cases(args.manifest.resolve()) if args.manifest else [{"id": "single-wav", "wav_path": args.wav.resolve(),
                 "language": args.language, "audio_provenance": args.audio_provenance, "scenario_provenance": args.scenario_provenance}]
        report = run_cases(cases, args.output_dir, args.limit, args.tts, args.save_tts_audio, args.base_url)
    except (OSError, ValueError, json.JSONDecodeError):
        print(json.dumps({"status": "input_error", "error": "Check the manifest schema and local input paths.", "api_calls": {"stt": 0, "tts": 0, "total": 0}}))
        return 2
    args.output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"live-results-{report['run_id']}.json"
    report["report_filename"] = filename
    serialized = json.dumps(report, ensure_ascii=False, indent=2)
    (args.output_dir / filename).write_text(serialized + "\n", encoding="utf-8")
    # Windows terminals may use cp1252. Keep the saved artifact in native UTF-8,
    # and escape only the console JSON so a successful run cannot crash here.
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return 0 if report["status"] == "complete" else 2 if report["status"] == "not_configured" else 1


if __name__ == "__main__":
    raise SystemExit(main())
