import importlib.util
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError


SCRIPT = Path(__file__).parents[1] / "scripts" / "atlas_tts.py"
SPEC = importlib.util.spec_from_file_location("atlas_tts", SCRIPT)
atlas_tts = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(atlas_tts)


class FakeResponse:
    def __init__(self, body):
        self.body = body if isinstance(body, bytes) else json.dumps(body).encode()

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return self.body


class AtlasTtsTests(unittest.TestCase):
    def test_preview_does_not_open_network(self):
        calls = []

        def opener(*args, **kwargs):
            calls.append((args, kwargs))
            raise AssertionError("preview must not access the network")

        with tempfile.TemporaryDirectory() as directory, patch("os.getcwd", return_value=directory):
            with patch.object(Path, "cwd", return_value=Path(directory)), redirect_stdout(io.StringIO()):
                result = atlas_tts.run(["--text", "hello"], opener=opener)

        self.assertEqual("preview", result["mode"])
        self.assertFalse(result["billable_request_sent"])
        self.assertEqual([], calls)

    def test_submit_failure_is_not_retried(self):
        requests = []

        def opener(request, **_kwargs):
            requests.append(request)
            raise HTTPError(request.full_url, 503, "unavailable", {}, None)

        with tempfile.TemporaryDirectory() as directory:
            with patch.object(Path, "cwd", return_value=Path(directory)), patch.dict(
                os.environ, {"ATLASCLOUD_API_KEY": "test-key"}
            ), self.assertRaises(HTTPError):
                atlas_tts.run(["--text", "hello", "--execute"], opener=opener)

        self.assertEqual(1, len(requests))
        self.assertEqual("POST", requests[0].get_method())

    def test_completed_audio_download_omits_authorization(self):
        requests = []
        responses = [
            FakeResponse({"data": {"id": "pred-1"}}),
            FakeResponse({"data": {"status": "completed", "outputs": ["https://cdn.example/audio.mp3"]}}),
            FakeResponse(b"audio-data"),
        ]

        def opener(request, **_kwargs):
            requests.append(request)
            return responses.pop(0)

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "speech.mp3"
            with patch.object(Path, "cwd", return_value=Path(directory)), patch.dict(
                os.environ, {"ATLASCLOUD_API_KEY": "test-key"}
            ), redirect_stdout(io.StringIO()):
                result = atlas_tts.run(
                    ["--text", "hello", "--output", "speech.mp3", "--execute"],
                    opener=opener,
                    sleeper=lambda _seconds: None,
                )

            self.assertEqual(b"audio-data", output.read_bytes())
            self.assertEqual(len(b"audio-data"), result["bytes"])

        self.assertEqual(["POST", "GET", "GET"], [request.get_method() for request in requests])
        self.assertIn("Authorization", requests[0].headers)
        self.assertIn("Authorization", requests[1].headers)
        self.assertNotIn("Authorization", requests[2].headers)

    def test_retryable_poll_error_retries_only_get(self):
        requests = []
        responses = [
            FakeResponse({"data": {"id": "pred-1"}}),
            HTTPError("https://api.example/prediction", 503, "unavailable", {}, None),
            FakeResponse({"data": {"status": "completed", "outputs": ["https://cdn.example/audio.mp3"]}}),
            FakeResponse(b"audio-data"),
        ]

        def opener(request, **_kwargs):
            requests.append(request)
            response = responses.pop(0)
            if isinstance(response, Exception):
                raise response
            return response

        with tempfile.TemporaryDirectory() as directory:
            with patch.object(Path, "cwd", return_value=Path(directory)), patch.dict(
                os.environ, {"ATLASCLOUD_API_KEY": "test-key"}
            ), redirect_stdout(io.StringIO()):
                atlas_tts.run(
                    ["--text", "hello", "--execute", "--poll-interval", "0"],
                    opener=opener,
                    sleeper=lambda _seconds: None,
                )

        self.assertEqual(1, sum(request.get_method() == "POST" for request in requests))
        self.assertEqual(3, sum(request.get_method() == "GET" for request in requests))

    def test_output_must_be_new_and_inside_working_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            existing = root / "existing.mp3"
            existing.write_bytes(b"existing")
            with self.assertRaises(FileExistsError):
                atlas_tts.resolve_output(existing, root)
            with self.assertRaises(ValueError):
                atlas_tts.resolve_output(root.parent / "escape.mp3", root)


if __name__ == "__main__":
    unittest.main()
