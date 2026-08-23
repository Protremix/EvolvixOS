"""
OpenRouter — Unified LLM Gateway Provider
==========================================
One API key → 300+ models from all major providers.
OpenAI-compatible endpoint.

Free models (no cost):
  - z-ai/glm-4.5-flash:free    (GLM coding)
  - google/gemini-flash:free   (Gemini vision)
  - groq/gpt-oss-20b           (ultra-fast chat)
  - meta-llama/llama-3.3-70b   (general purpose)
  - deepseek/deepseek-r1:free  (reasoning)
  - qwen/qwen3-coder-30b:free  (coding)

Cheap models:
  - z-ai/glm-5.2               ($1.40/$4.40 per 1M)
  - google/gemini-3.1-pro       (~$2.50/$7.50 per 1M)
  - moonshot/kimi-k2.5          ($0.60/$3.00 per 1M)
  - anthropic/claude-sonnet-5   ($3/$15 per 1M)
  - deepseek/deepseek-v4-flash  ($0.14/$0.28 per 1M)
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

    # Model selection by task — uses free models first, paid for complex
    models_by_task = {
        "chat": "groq/gpt-oss-20b",              # Free via Groq — ultra-fast
        "code": "z-ai/glm-4.5-flash:free",        # Free GLM — coding
        "reasoning": "deepseek/deepseek-r1:free",  # Free DeepSeek — reasoning
        "simple": "groq/gpt-oss-20b",             # Free — quick responses
        "vision": "google/gemini-flash:free",      # Free Gemini — vision
        "complex": "z-ai/glm-5.2",                 # Paid — flagship coding ($1.40/$4.40)
        "video": "groq/gpt-oss-20b",               # Free — routing only
        "image": "groq/gpt-oss-20b",              # Free — routing only
        "crypto": "groq/gpt-oss-20b",             # Free — routing only
    }
    default_model = "groq/gpt-oss-20b"

    def __init__(self):
        self._api_key = os.environ.get("OPENROUTER_API_KEY", "")

    def is_available(self) -> bool:
        return bool(self._api_key)

    def chat(self, messages, tools=None, stream=False, temperature=0.7, max_tokens=4096, model=None) -> LLMResponse:
        if not self._api_key:
            raise RuntimeError("OpenRouter API key not configured. Set OPENROUTER_API_KEY env var.")

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
            return LLMResponse(
                content=msg.get("content", ""),
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
            # If paid model fails, fall back to free
            if ":free" not in _model and e.code in (401, 402, 403, 429):
                free_model = _model.split("/")[0] + "/" + _model.split("/")[1].split(":")[0] + ":free"
                logger.info("OpenRouter: Falling back from %s to %s", _model, free_model)
                return self.chat(messages, tools, stream, temperature, max_tokens, free_model)
            raise RuntimeError(f"OpenRouter API error {e.code}: {error_body[:200]}")
