"""
Claude LLM Provider — wraps Anthropic API for chat completions.
"""

import json
import os
import time
import urllib.request
from typing import Optional

from app.ai.llm_provider import LLMProvider, LLMResponse


class ClaudeProvider(LLMProvider):
    """Anthropic Claude provider using the Messages API."""

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-sonnet-4-20250514"):
        self._api_key = api_key if api_key is not None else os.environ.get("ANTHROPIC_API_KEY", "")
        self._model = model
        self._api_url = "https://api.anthropic.com/v1/messages"

    def name(self) -> str:
        return "claude"

    def model_name(self) -> str:
        return self._model

    def is_available(self) -> bool:
        return bool(self._api_key)

    def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 4000,
    ) -> LLMResponse:
        if not self.is_available():
            raise RuntimeError("Anthropic API key not configured")

        payload = {
            "model": self._model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": user_prompt},
            ],
        }

        start = time.time()
        req_data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self._api_url,
            data=req_data,
            headers={
                "Content-Type": "application/json",
                "x-api-key": self._api_key,
                "anthropic-version": "2023-06-01",
            },
        )

        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode("utf-8"))

        latency = (time.time() - start) * 1000

        content_parts = result.get("content", [])
        content = ""
        for part in content_parts:
            if part.get("type") == "text":
                content += part.get("text", "")

        input_tokens = result.get("usage", {}).get("input_tokens", 0)
        output_tokens = result.get("usage", {}).get("output_tokens", 0)

        return LLMResponse(
            content=content,
            tokens_used=input_tokens + output_tokens,
            model=self._model,
            latency_ms=latency,
            finish_reason=result.get("stop_reason", "stop"),
            provider="claude",
        )
