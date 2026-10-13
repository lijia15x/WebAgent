import base64
import json
import os
import re
from pathlib import Path
from typing import Awaitable, Callable, Sequence

import httpx


ThinkingCallback = Callable[[str], Awaitable[None]]


class OllamaError(RuntimeError):
    pass


class OllamaClient:
    def __init__(
        self,
        base_url: str | None = None,
        timeout: float = 900.0,
        context_window: int = 65_536,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")).rstrip("/")
        self.timeout = timeout
        self.context_window = context_window
        self.transport = transport

    async def ensure_models(self, models: Sequence[str]) -> None:
        try:
            async with httpx.AsyncClient(
                timeout=30.0, trust_env=False, transport=self.transport
            ) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise OllamaError(f"Cannot reach Ollama at {self.base_url}: {exc}") from exc
        available = {item.get("name") for item in response.json().get("models", [])}
        missing = [model for model in models if model not in available]
        if missing:
            raise OllamaError(
                "Required Ollama model(s) are unavailable: " + ", ".join(missing)
            )

    async def chat_json(
        self,
        model: str,
        prompt: str,
        images: Sequence[Path] = (),
        thinking_callback: ThinkingCallback | None = None,
        max_output_tokens: int | None = None,
        think: bool = False,
    ) -> dict | list:
        encoded_images = [
            base64.b64encode(path.read_bytes()).decode("ascii") for path in images
        ]
        last_json_error: json.JSONDecodeError | None = None
        for attempt in range(2):
            request_prompt = prompt
            output_tokens = max_output_tokens
            if attempt:
                request_prompt += (
                    "\n\n上一次响应不是合法JSON，可能在末尾被截断。请重新检查原始输入，"
                    "只返回一个完整、紧凑、语法合法且所有数组和对象均正确闭合的JSON。"
                    "不得省略原请求要求的任何事实、字段或数组项。"
                    "不要输出解释、Markdown代码块或重复内容。"
                )
                if output_tokens is not None:
                    output_tokens = min(output_tokens * 2, self.context_window)
                if thinking_callback is not None:
                    await thinking_callback("模型返回的JSON不完整，正在自动重试")

            message: dict[str, object] = {"role": "user", "content": request_prompt}
            if encoded_images:
                message["images"] = encoded_images
            payload = {
                "model": model,
                "messages": [message],
                "stream": True,
                "format": "json",
                "think": think,
                "options": {
                    "temperature": 0,
                    "num_ctx": self.context_window,
                    "repeat_penalty": 1.1,
                    "repeat_last_n": 256,
                },
            }
            if output_tokens is not None:
                payload["options"]["num_predict"] = output_tokens
            content_parts: list[str] = []
            thinking_parts: list[str] = []
            thinking_buffer = ""
            try:
                async with httpx.AsyncClient(
                    timeout=httpx.Timeout(self.timeout),
                    trust_env=False,
                    transport=self.transport,
                ) as client:
                    async with client.stream(
                        "POST", f"{self.base_url}/api/chat", json=payload
                    ) as response:
                        response.raise_for_status()
                        async for line in response.aiter_lines():
                            if not line:
                                continue
                            event = json.loads(line)
                            if event.get("error"):
                                raise OllamaError(str(event["error"]))
                            response_message = event.get("message") or {}
                            content_parts.append(response_message.get("content") or "")
                            thinking_delta = response_message.get("thinking") or ""
                            thinking_parts.append(thinking_delta)
                            thinking_buffer += thinking_delta
                            if thinking_callback is not None:
                                thinking_buffer = await self._emit_thinking(
                                    thinking_buffer, thinking_callback
                                )
            except (httpx.HTTPError, json.JSONDecodeError) as exc:
                raise OllamaError(f"Ollama request failed for {model}: {exc}") from exc

            if thinking_callback is not None and thinking_buffer.strip():
                await thinking_callback(self._clean_thinking(thinking_buffer))
            content = "".join(content_parts).strip()
            if not content:
                content = "".join(thinking_parts).strip()
            fenced = re.fullmatch(
                r"```(?:json)?\s*\n?(.*?)\n?```", content, re.DOTALL | re.IGNORECASE
            )
            if fenced:
                content = fenced.group(1).strip()
            try:
                result = json.loads(content)
            except json.JSONDecodeError as exc:
                last_json_error = exc
                continue
            if not isinstance(result, (dict, list)):
                raise OllamaError(f"{model} returned a non-object JSON response")
            return result

        raise OllamaError(f"{model} returned invalid JSON after retry: {last_json_error}")

    async def _emit_thinking(
        self,
        buffer: str,
        callback: ThinkingCallback,
    ) -> str:
        while True:
            boundary = re.search(r"(?:[.!?。！？](?:\s|$)|\n)", buffer)
            if boundary is None and len(buffer) < 180:
                return buffer
            end = boundary.end() if boundary is not None else 180
            message = self._clean_thinking(buffer[:end])
            buffer = buffer[end:]
            if len(message) >= 12:
                await callback(message)

    @staticmethod
    def _clean_thinking(message: str) -> str:
        cleaned = re.sub(r"[`#*_>]", "", message)
        cleaned = re.sub(r"\s+", " ", cleaned).strip(" -:\n\t")
        return cleaned[:177] + "..." if len(cleaned) > 180 else cleaned