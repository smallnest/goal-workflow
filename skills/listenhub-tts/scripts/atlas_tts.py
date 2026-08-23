#!/usr/bin/env python3
"""Generate short-form TTS with Atlas Cloud's xAI TTS model."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Callable, Sequence
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


BASE_URL = "https://api.atlascloud.ai/api/v1"
MODEL = "xai/tts-v1"
RETRYABLE_GET_STATUS = {429, 500, 502, 503, 504}
LANGUAGES = (
    "auto",
    "en",
    "zh",
    "ar-EG",
    "ar-SA",
    "ar-AE",
    "bn",
    "fr",
    "de",
    "hi",
    "id",
    "it",
    "ja",
    "ko",
    "pt-BR",
    "pt-PT",
    "ru",
    "es-MX",
    "es-ES",
    "tr",
    "vi",
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Preview or execute an Atlas Cloud xAI TTS request."
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--text", help="Text to synthesize (maximum 15,000 characters)")
    source.add_argument("--text-file", type=Path, help="UTF-8 text file to synthesize")
    parser.add_argument("--output", type=Path, default=Path("atlas-tts.mp3"))
    parser.add_argument("--language", choices=LANGUAGES, default="auto")
    parser.add_argument("--voice-id", default="eve")
    parser.add_argument("--codec", choices=("mp3", "wav", "pcm", "mulaw", "alaw"), default="mp3")
    parser.add_argument("--sample-rate", type=int, choices=(8000, 16000, 22050, 24000, 44100, 48000), default=24000)
    parser.add_argument("--bit-rate", type=int, choices=(32000, 64000, 96000, 128000, 192000), default=128000)
    parser.add_argument("--speed", type=float, default=1.0)
    parser.add_argument("--text-normalization", action="store_true")
    parser.add_argument("--optimize-streaming-latency", type=int, choices=(0, 1, 2), default=0)
    parser.add_argument("--poll-attempts", type=int, default=40)
    parser.add_argument("--poll-interval", type=float, default=3.0)
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Submit the billable request; without this flag the command only previews",
    )
    return parser.parse_args(argv)


def read_text(args: argparse.Namespace) -> str:
    text = args.text if args.text is not None else args.text_file.read_text(encoding="utf-8")
    if not text.strip():
        raise ValueError("text must not be empty")
    if len(text) > 15_000:
        raise ValueError("text exceeds the xai/tts-v1 limit of 15,000 characters")
    return text


def resolve_output(path: Path, root: Path | None = None) -> Path:
    root = (root or Path.cwd()).resolve()
    output = (root / path).resolve() if not path.is_absolute() else path.resolve()
    try:
        output.relative_to(root)
    except ValueError as exc:
        raise ValueError("output must stay inside the current working directory") from exc
    if output.exists():
        raise FileExistsError(f"refusing to overwrite existing file: {output}")
    return output


def build_payload(args: argparse.Namespace, text: str) -> dict[str, Any]:
    if not 0.7 <= args.speed <= 1.5:
        raise ValueError("speed must be between 0.7 and 1.5 for xai/tts-v1")
    if args.poll_attempts < 1 or args.poll_interval < 0:
        raise ValueError("poll attempts must be positive and poll interval non-negative")
    return {
        "model": MODEL,
        "text": text,
        "language": args.language,
        "voice_id": args.voice_id,
        "codec": args.codec,
        "sample_rate": args.sample_rate,
        "bit_rate": args.bit_rate,
        "speed": args.speed,
        "text_normalization": args.text_normalization,
        "optimize_streaming_latency": args.optimize_streaming_latency,
    }


def decode_response(response: Any) -> dict[str, Any]:
    data = json.loads(response.read().decode("utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError("Atlas Cloud returned a non-object response")
    envelope = data.get("data", data)
    if not isinstance(envelope, dict):
        raise RuntimeError("Atlas Cloud response is missing a data object")
    return envelope


def submit_once(
    payload: dict[str, Any],
    api_key: str,
    opener: Callable[..., Any],
) -> str:
    request = Request(
        f"{BASE_URL}/model/generateAudio",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "goal-workflow-atlas-tts/1.0",
        },
        method="POST",
    )
    with opener(request, timeout=50) as response:
        prediction_id = decode_response(response).get("id")
    if not isinstance(prediction_id, str) or not prediction_id:
        raise RuntimeError("Atlas Cloud response is missing the prediction id")
    return prediction_id


def poll_prediction(
    prediction_id: str,
    api_key: str,
    attempts: int,
    interval: float,
    opener: Callable[..., Any],
    sleeper: Callable[[float], None],
) -> list[str]:
    url = f"{BASE_URL}/model/prediction/{prediction_id}"
    for attempt in range(attempts):
        request = Request(
            url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "User-Agent": "goal-workflow-atlas-tts/1.0",
            },
            method="GET",
        )
        try:
            with opener(request, timeout=30) as response:
                result = decode_response(response)
        except HTTPError as exc:
            if exc.code not in RETRYABLE_GET_STATUS or attempt == attempts - 1:
                raise
            sleeper(min(interval * (2**attempt), 30.0))
            continue

        status = result.get("status")
        if status in ("completed", "succeeded"):
            outputs = result.get("outputs")
            if not isinstance(outputs, list) or not outputs or not all(
                isinstance(item, str) and item for item in outputs
            ):
                raise RuntimeError("completed prediction is missing outputs")
            return outputs
        if status == "failed":
            raise RuntimeError(f"Atlas Cloud TTS failed: {result.get('error', 'unknown error')}")
        if attempt < attempts - 1:
            sleeper(interval)
    raise TimeoutError("Atlas Cloud TTS did not complete within the polling limit")


def download_output(url: str, output: Path, opener: Callable[..., Any]) -> int:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError("Atlas Cloud output must be an HTTPS URL")
    request = Request(url, headers={"User-Agent": "goal-workflow-atlas-tts/1.0"}, method="GET")
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{output.name}.", dir=output.parent)
    try:
        with os.fdopen(fd, "wb") as file_handle:
            with opener(request, timeout=60) as response:
                file_handle.write(response.read())
            file_handle.flush()
            os.fsync(file_handle.fileno())
        size = os.path.getsize(temporary)
        if size == 0:
            raise RuntimeError("Atlas Cloud output download was empty")
        os.link(temporary, output)
        os.unlink(temporary)
        return size
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def run(
    argv: Sequence[str] | None = None,
    opener: Callable[..., Any] = urlopen,
    sleeper: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    args = parse_args(argv)
    text = read_text(args)
    output = resolve_output(args.output)
    payload = build_payload(args, text)

    if not args.execute:
        result = {
            "mode": "preview",
            "billable_request_sent": False,
            "endpoint": f"{BASE_URL}/model/generateAudio",
            "payload": payload,
            "output": str(output),
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return result

    api_key = os.environ.get("ATLASCLOUD_API_KEY")
    if not api_key:
        raise RuntimeError("ATLASCLOUD_API_KEY is required with --execute")

    prediction_id = submit_once(payload, api_key, opener)
    outputs = poll_prediction(
        prediction_id,
        api_key,
        args.poll_attempts,
        args.poll_interval,
        opener,
        sleeper,
    )
    size = download_output(outputs[0], output, opener)
    result = {
        "mode": "execute",
        "model": MODEL,
        "prediction_id": prediction_id,
        "output": str(output),
        "bytes": size,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


def main() -> int:
    try:
        run()
    except (HTTPError, OSError, RuntimeError, TimeoutError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
