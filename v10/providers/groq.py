"""
Groq — Cloud LLM Provider (ultra-fast, tool-use optimized)
"""
from __future__ import annotations
import json
import os
import time
import urllib.request
import logging
from v10.providers.base import LLMProvider, LLMResponse

logger = logging.getLogger("evolvixos.v10.providers.groq")

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

class GroqProvider(LLMProvider):
    name = "groq"
    is_local = False
    supports_tools = True
    supports_vision = False
    supports_streaming = True
    max_context = 128000
    latency_tier = "ultra-fast"

    models_by_task = {
        "chat": "qwen/qwen3.6-27b",
        "code": "openai/gpt-oss-120b",
        "reasoning": "openai/gpt-oss-120b",
        "simple": "qwen/qwen3.6-27b",
    }
    default_model = "openai/gpt-oss-120b"

    def __init__(self):
        self._api_key = os.environ.get("GROQ_API_KEY", "")

    def is_available(self) -> bool:
        return bool(self._api_key)

    def chat(self, messages, tools=None, stream=False, temperature=0.7, max_tokens=4096) -> LLMResponse:
        if not self._api_key:
            raise RuntimeError("Groq API key not configured")

        body = json.dumps({
            "model": self.default_model,
            "messages": messages,
            "tools": tools if tools else None,
            "stream": stream,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }).encode()

        req = urllib.request.Request(GROQ_URL, data=body, headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._api_key}",
            "User-Agent": "EvolvixOS/10.0"
        })

        start = time.monotonic()
        resp = urllib.request.urlopen(req, timeout=120)
        result = json.loads(resp.read())
        latency = (time.monotonic() - start) * 1000
        resp.close()

        msg = result.get("choices", [{}])[0].get("message", {})
        return LLMResponse(
            content=msg.get("content", ""),
            provider=self.name,
            model=self.default_model,
            tool_calls=msg.get("tool_calls", []),
            usage=result.get("usage", {}),
            latency_ms=latency,
            raw=result
        )
