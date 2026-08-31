"""
Kimi (Moonshot) — Cloud LLM Provider (complex reasoning)
"""
from __future__ import annotations
import json
import os
import time
import urllib.request
import logging
from v10.providers.base import LLMProvider, LLMResponse

logger = logging.getLogger("evolvixos.v10.providers.kimi")

KIMI_URL = "https://api.moonshot.ai/v1/chat/completions"

class KimiProvider(LLMProvider):
    name = "kimi"
    is_local = False
    supports_tools = True
    supports_vision = False
    supports_streaming = False
    max_context = 32768
    latency_tier = "medium"

    models_by_task = {
        "chat": "moonshot-v1-32k",
        "code": "moonshot-v1-32k",
        "reasoning": "moonshot-v1-32k",
    }
    default_model = "moonshot-v1-32k"

    def __init__(self):
        self._api_key = os.environ.get("KIMI_API_KEY", "")

    def is_available(self) -> bool:
        return bool(self._api_key)

    def chat(self, messages, tools=None, stream=False, temperature=0.7, max_tokens=4096, model=None) -> LLMResponse:
        if not self._api_key:
            raise RuntimeError("Kimi API key not configured")

        body = json.dumps({
            "model": model or self.default_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }).encode()

        req = urllib.request.Request(KIMI_URL, data=body, headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._api_key}",
            "User-Agent": "EvolvixOS/10.0"
        })

        start = time.monotonic()
        resp = urllib.request.urlopen(req, timeout=60)
        result = json.loads(resp.read())
        latency = (time.monotonic() - start) * 1000
        resp.close()

        msg = result.get("choices", [{}])[0].get("message", {})
        return LLMResponse(
            content=msg.get("content", ""),
            provider=self.name,
            model=model or self.default_model,
            tool_calls=msg.get("tool_calls", []),
            usage=result.get("usage", {}),
            latency_ms=latency,
            raw=result
        )
