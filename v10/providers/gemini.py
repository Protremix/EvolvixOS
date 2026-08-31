"""
Google Gemini — Cloud LLM Provider (vision, multimodal, 1M context)
"""
from __future__ import annotations
import json
import os
import time
import urllib.request
import logging
from v10.providers.base import LLMProvider, LLMResponse

logger = logging.getLogger("evolvixos.v10.providers.gemini")

class GeminiProvider(LLMProvider):
    name = "gemini"
    is_local = False
    supports_tools = True
    supports_vision = True
    supports_streaming = True
    max_context = 1000000
    latency_tier = "fast"

    models_by_task = {
        "chat": "gemini-3.6-flash",
        "code": "gemini-3.6-flash",
        "reasoning": "gemini-3.6-flash",
        "vision": "gemini-3.6-flash",
        "simple": "gemini-flash-latest",
    }
    default_model = "gemini-3.6-flash"

    def __init__(self):
        self._api_key = os.environ.get("GEMINI_API_KEY", "") or os.environ.get("GOOGLE_API_KEY", "")

    def is_available(self) -> bool:
        return bool(self._api_key)

    def chat(self, messages, tools=None, stream=False, temperature=0.7, max_tokens=4096, model=None) -> LLMResponse:
        if not self._api_key:
            raise RuntimeError("Gemini API key not configured")

        # Convert OpenAI-style messages to Gemini format
        contents = []
        system_text = ""
        for msg in messages:
            if msg["role"] == "system":
                system_text += msg["content"] + "\n"
            else:
                contents.append({
                    "role": "user" if msg["role"] == "user" else "model",
                    "parts": [{"text": msg["content"]}]
                })

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model or self.default_model}:generateContent?key={self._api_key}"
        body = json.dumps({
            "contents": contents,
            "systemInstruction": {"parts": [{"text": system_text}]} if system_text else None,
            "generationConfig": {"maxOutputTokens": max_tokens, "temperature": temperature},
        }).encode()

        req = urllib.request.Request(url, data=body, headers={
            "Content-Type": "application/json",
            "User-Agent": "EvolvixOS/10.0"
        })

        start = time.monotonic()
        resp = urllib.request.urlopen(req, timeout=60)
        result = json.loads(resp.read())
        latency = (time.monotonic() - start) * 1000
        resp.close()

        text = result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        return LLMResponse(
            content=text,
            provider=self.name,
            model=model or self.default_model,
            tool_calls=[],
            usage={},
            latency_ms=latency,
            raw=result
        )
