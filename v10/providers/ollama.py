"""
Ollama — Local LLM Provider (zero-cost, offline-capable)
"""
from __future__ import annotations
import json
import os
import urllib.request
import logging
from v10.providers.base import LLMProvider, LLMResponse

logger = logging.getLogger("evolvixos.v10.providers.ollama")

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")

class OllamaProvider(LLMProvider):
    name = "ollama"
    is_local = True
    supports_tools = True
    supports_vision = False
    supports_streaming = True
    max_context = 32768
    latency_tier = "slow"  # CPU inference

    # Task → model mapping
    models_by_task = {
        "chat": "qwen2.5:7b",
        "code": "qwen2.5:14b",
        "reasoning": "qwen2.5:14b",
        "simple": "qwen2.5:3b",
        "system": "qwen2.5:7b",
    }
    default_model = "qwen2.5:14b"

    def is_available(self) -> bool:
        try:
            req = urllib.request.Request(f"{OLLAMA_URL}/api/tags", headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status == 200
        except Exception:
            return False

    def chat(self, messages, tools=None, stream=False, temperature=0.7, max_tokens=4096, model=None) -> LLMResponse:
        model = model or self.default_model
        data = json.dumps({
            "model": model,
            "messages": messages,
            "tools": tools or [],
            "stream": stream,
            "options": {"temperature": temperature, "top_p": 0.9}
        }).encode()
        req = urllib.request.Request(f"{OLLAMA_URL}/api/chat", data=data,
                                     headers={"Content-Type": "application/json"})
        import time
        start = time.monotonic()
        resp = urllib.request.urlopen(req, timeout=180)
        result = json.loads(resp.read())
        latency = (time.monotonic() - start) * 1000
        resp.close()

        return LLMResponse(
            content=result.get("message", {}).get("content", ""),
            provider=self.name,
            model=model,
            tool_calls=result.get("message", {}).get("tool_calls", []),
            usage=result.get("prompt_eval_count", 0),
            latency_ms=latency,
            raw=result
        )
