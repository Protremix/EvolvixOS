"""
OpenRouter — Unified LLM Gateway Provider
==========================================
One API key → 422+ models from all major providers.
OpenAI-compatible endpoint at https://openrouter.ai/api/v1/

Free models (verified working):
  - z-ai/glm-5.2:free        (GLM flagship, rate-limited)
  - google/gemma-4-31b-it:free (Gemma, rate-limited)

Cheapest paid models (verified working):
  - z-ai/glm-5               ($0.60/$1.92 per 1M — best value)
  - z-ai/glm-5.2             ($0.97/$3.04 per 1M — flagship)
  - z-ai/glm-4.7-flash        ($0.06/$0.40 per 1M — cheapest, reasoning)
  - openai/gpt-oss-20b       ($0.10/$0.10 per 1M — fast chat)
  - openai/gpt-oss-120b      ($0.10/$0.10 per 1M — bigger model)
"""
from __future__ import annotations
import json
import os
import time
import urllib.request
import logging
from v10.providers.base import LLMProvider, LLMResponse

logger = logging.getLogger("evolvixos.v10.providers.openrouter")

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

SYSTEM_PROMPT = """You are Mr James, an AI builder assistant for EvolvixOS.
You help users build apps, write code, generate images, analyze data, and manage servers.
Be helpful, concise, and proactive."""

class OpenRouterProvider(LLMProvider):
    name = "openrouter"
    is_local = False
    supports_tools = True
    supports_vision = True
    supports_streaming = True
    max_context = 128000
    latency_tier = "fast"

    # Verified model IDs from OpenRouter API
    models_by_task = {
        "chat": "openai/gpt-oss-20b",         # $0.10/$0.10 — fast chat
        "code": "z-ai/glm-5",                  # $0.60/$1.92 — coding
        "reasoning": "z-ai/glm-5",              # $0.60/$1.92 — reasoning
        "simple": "openai/gpt-oss-20b",         # $0.10/$0.10 — quick
        "vision": "z-ai/glm-5",                 # GLM supports vision
        "complex": "z-ai/glm-5.2",             # $0.97/$3.04 — flagship
        "video": "openai/gpt-oss-20b",         # routing only
        "image": "openai/gpt-oss-20b",          # routing only
        "crypto": "openai/gpt-oss-20b",        # routing only
    }
    default_model = "openai/gpt-oss-20b"

    def __init__(self):
        self._api_key = os.environ.get("OPENROUTER_API_KEY", "")

    def is_available(self) -> bool:
        return bool(self._api_key)

    def chat(self, messages, tools=None, stream=False, temperature=0.7, max_tokens=4096, model=None) -> LLMResponse:
        if not self._api_key:
            raise RuntimeError("OpenRouter API key not configured.")

        _model = model or self.default_model

        # Condense long system prompts
        condensed = []
        for msg in messages:
            if msg.get("role") == "system" and len(msg.get("content", "")) > 500:
                condensed.append({"role": "system", "content": SYSTEM_PROMPT})
            else:
                condensed.append(msg)

        body_dict = {
            "model": _model,
            "messages": condensed,
            "stream": stream,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if tools:
            body_dict["tools"] = tools

        body = json.dumps(body_dict).encode()

        req = urllib.request.Request(OPENROUTER_URL, data=body, headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._api_key}",
            "HTTP-Referer": "https://evolvixos.com",
            "X-Title": "EvolvixOS",
        })

        start = time.monotonic()
        try:
            resp = urllib.request.urlopen(req, timeout=120)
            result = json.loads(resp.read())
            latency = (time.monotonic() - start) * 1000
            resp.close()

            msg = result.get("choices", [{}])[0].get("message", {})
            # Handle reasoning models (GLM 4.7, DeepSeek R1) where content is null
            content = msg.get("content") or msg.get("reasoning", "") or ""
            return LLMResponse(
                content=content,
                provider=self.name,
                model=result.get("model", _model),
                tool_calls=msg.get("tool_calls", []),
                usage=result.get("usage", {}),
                latency_ms=latency,
                raw=result
            )
        except urllib.error.HTTPError as e:
            error_body = e.read().decode() if e.fp else ""
            logger.error(f"OpenRouter API error {e.code}: {error_body[:500]}")
            # If 429 on paid model, try free variant
            if ":free" not in _model and e.code == 429:
                free_model = _model + ":free"
                logger.info("OpenRouter: Falling back from %s to %s", _model, free_model)
                try:
                    return self.chat(messages, tools, stream, temperature, max_tokens, free_model)
                except Exception:
                    pass
            raise RuntimeError(f"OpenRouter API error {e.code}: {error_body[:200]}")
