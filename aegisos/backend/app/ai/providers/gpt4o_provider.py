"""
GPT-4o LLM Provider — wraps OpenAI API for chat completions.
"""

import json
import os
import time
import urllib.request
from typing import Optional

from app.ai.llm_provider import LLMProvider, LLMResponse


class GPT4oProvider(LLMProvider):
    """GPT-4o provider using the OpenAI API."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o"):
        self._api_key = api_key if api_key is not None else os.environ.get("OPENAI_API_KEY_2", os.environ.get("OPENAI_API_KEY", ""))
        self._model = model
        self._api_url = "https://api.openai.com/v1/chat/completions"

    def name(self) -> str:
        return "gpt4o"

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
            raise RuntimeError("GPT-4o API key not configured")

        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        start = time.time()
        req_data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self._api_url,
            data=req_data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._api_key}",
            },
        )

        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode("utf-8"))

        latency = (time.time() - start) * 1000

        return LLMResponse(
            content=result["choices"][0]["message"]["content"],
            tokens_used=result.get("usage", {}).get("total_tokens", 0),
            model=self._model,
            latency_ms=latency,
            finish_reason=result["choices"][0].get("finish_reason", "stop"),
            provider="gpt4o",
        )
