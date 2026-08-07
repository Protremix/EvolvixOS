"""
Local LLM Provider — supports OpenAI-compatible local model servers
(Ollama, vLLM, LM Studio, etc.).
"""

import json
import os
import time
import urllib.request
from typing import Optional

from app.ai.llm_provider import LLMProvider, LLMResponse


class LocalLLMProvider(LLMProvider):
    """Local LLM provider for OpenAI-compatible servers."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self._base_url = base_url or os.environ.get("LOCAL_LLM_URL", "http://localhost:11434/v1")
        self._model = model or os.environ.get("LOCAL_LLM_MODEL", "llama3")
        self._api_url = f"{self._base_url}/chat/completions"

    def name(self) -> str:
        return "local"

    def model_name(self) -> str:
        return self._model

    def is_available(self) -> bool:
        """Check if the local LLM server is reachable."""
        if not self._base_url:
            return False
        try:
            health_url = self._base_url.replace("/v1", "/api/health") if "ollama" in self._base_url else f"{self._base_url}/models"
            req = urllib.request.Request(health_url)
            urllib.request.urlopen(req, timeout=5)
            return True
        except Exception:
            return False

    def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 4000,
    ) -> LLMResponse:
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
            headers={"Content-Type": "application/json"},
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
            provider="local",
        )
