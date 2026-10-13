import json
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

import httpx

from pdf_to_yaml_agent.ollama_client import OllamaClient, OllamaError
from pdf_to_yaml_agent.config import (
    DEFAULT_TEXT_MODEL,
    DEFAULT_VISION_MODEL,
    OLLAMA_CONTEXT_WINDOW,
    VISION_MAX_OUTPUT_TOKENS,
    text_model,
    vision_model,
)


class OllamaClientTests(unittest.IsolatedAsyncioTestCase):
    async def test_visual_chat_streams_json_with_image_and_thinking(self) -> None:
        requests: list[dict] = []

        def handler(request: httpx.Request) -> httpx.Response:
            payload = json.loads(request.content)
            requests.append(payload)
            events = [
                {"message": {"thinking": "Inspecting visible labels. ", "content": "{\"boards\":"}},
                {"message": {"thinking": "", "content": "[]}"}, "done": True},
            ]
            return httpx.Response(
                200,
                text="\n".join(json.dumps(event) for event in events),
                headers={"content-type": "application/x-ndjson"},
            )

        thinking: list[str] = []

        async def record_thinking(message: str) -> None:
            thinking.append(message)

        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / "crop.png"
            image.write_bytes(b"image-data")
            client = OllamaClient(
                "http://ollama.test",
                transport=httpx.MockTransport(handler),
            )
            result = await client.chat_json(
                "qwen3-vl:30b",
                "inspect",
                images=[image],
                thinking_callback=record_thinking,
                max_output_tokens=8192,
            )

        self.assertEqual({"boards": []}, result)
        self.assertEqual("qwen3-vl:30b", requests[0]["model"])
        self.assertEqual("json", requests[0]["format"])
        self.assertFalse(requests[0]["think"])
        self.assertEqual(65_536, requests[0]["options"]["num_ctx"])
        self.assertEqual(8192, requests[0]["options"]["num_predict"])
        self.assertEqual(1.1, requests[0]["options"]["repeat_penalty"])
        self.assertTrue(requests[0]["messages"][0]["images"])
        self.assertEqual(["Inspecting visible labels."], thinking)

    async def test_model_check_reports_missing_required_model(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"models": [{"name": "qwen3:32b"}]})

        client = OllamaClient(
            "http://ollama.test",
            transport=httpx.MockTransport(handler),
        )

        with self.assertRaisesRegex(OllamaError, "qwen3-vl:30b"):
            await client.ensure_models(["qwen3:32b", "qwen3-vl:30b"])

    async def test_uses_thinking_as_json_when_content_is_empty(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            event = {
                "message": {
                    "thinking": '{"elements": []}',
                    "content": "",
                },
                "done": True,
            }
            return httpx.Response(
                200,
                text=json.dumps(event),
                headers={"content-type": "application/x-ndjson"},
            )

        client = OllamaClient(
            "http://ollama.test",
            transport=httpx.MockTransport(handler),
        )

        result = await client.chat_json("qwen3-vl:30b", "inspect")

        self.assertEqual({"elements": []}, result)

    async def test_retries_once_when_model_returns_truncated_json(self) -> None:
        requests: list[dict] = []

        def handler(request: httpx.Request) -> httpx.Response:
            payload = json.loads(request.content)
            requests.append(payload)
            content = (
                '{"elements": [{"id": "truncated"}'
                if len(requests) == 1
                else '{"elements": [{"id": "complete"}]}'
            )
            return httpx.Response(
                200,
                text=json.dumps({"message": {"content": content}, "done": True}),
                headers={"content-type": "application/x-ndjson"},
            )

        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / "crop.png"
            image.write_bytes(b"image-data")
            client = OllamaClient(
                "http://ollama.test",
                transport=httpx.MockTransport(handler),
            )

            result = await client.chat_json(
                "qwen3-vl:30b",
                "inspect",
                images=[image],
                max_output_tokens=8192,
            )

        self.assertEqual({"elements": [{"id": "complete"}]}, result)
        self.assertEqual(2, len(requests))
        self.assertEqual(16_384, requests[1]["options"]["num_predict"])
        self.assertTrue(requests[1]["messages"][0]["images"])
        self.assertIn("上一次响应不是合法JSON", requests[1]["messages"][0]["content"])
        self.assertIn("不得省略", requests[1]["messages"][0]["content"])

    def test_pdf_agent_uses_shared_model_environment_and_code_defaults(self) -> None:
        with patch.dict(
            "os.environ",
            {"OLLAMA_MODEL": "shared-text", "VISION_MODEL": "shared-vision"},
            clear=True,
        ):
            self.assertEqual("shared-text", text_model())
            self.assertEqual("shared-vision", vision_model())

        with patch.dict("os.environ", {}, clear=True):
            self.assertEqual("qwen3:32b", DEFAULT_TEXT_MODEL)
            self.assertEqual("qwen3-vl:30b", DEFAULT_VISION_MODEL)
            self.assertEqual(65_536, OLLAMA_CONTEXT_WINDOW)
            self.assertEqual(16_384, VISION_MAX_OUTPUT_TOKENS)
            self.assertEqual(DEFAULT_TEXT_MODEL, text_model())
            self.assertEqual(DEFAULT_VISION_MODEL, vision_model())