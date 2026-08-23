"""
GLM (Z.ai) — Cloud LLM Provider
================================
OpenAI-compatible API at https://api.z.ai/api/paas/v4/

Free models:
  - glm-4.5-flash  (free, coding + reasoning)
  - glm-4.7-flash  (free, general purpose)

Paid models:
  - glm-5.3       (flagship coding, requires Coding Plan)
  - glm-5.2       (coding + agentic)
  - glm-4.5       (reasoning + coding)

GLM-5.3 is Z.ai's latest flagship (Aug 14, 2026) — frontier coding
with emergent cyber capabilities. 1M context window.
"""
from __future__ import annotations
import json
import os
import time
import urllib.request
import logging
from v10.providers.base import LLMProvider, LLMResponse

logger = logging.getLogger("evolvixos.v10.providers.glm")

ZAI_URL = "https://api.z.ai/api/paas/v4/chat/completions"

SYSTEM_PROMPT = """You are Mr James, an AI builder assistant for EvolvixOS.
You help users build apps, write code, generate images, analyze data, and manage servers.
You have tools available — use them when needed. Be helpful, concise, and proactive."""

class GLMProvider(LLMProvider):
    name = "glm"
    is_local = False
    supports_tools = True
    supports_vision = False
    supports_streaming = True
    max_context = 128000
    latency_tier = "fast"

    # Model selection by task — default to free flash model
    models_by_task = {
        "chat": "glm-4.5-flash",       # Free — general chat
        "code": "glm-4.5-flash",       # Free — coding
        "reasoning": "glm-4.5-flash",  # Free — reasoning
        "simple": "glm-4.5-flash",    # Free — quick responses
        "complex": "glm-4.5-flash",   # Free — complex (5.3 needs paid plan)
    }
    default_model = "glm-4.5-flash"

    def __init__(self):
        self._api_key = os.environ.get("ZAI_API_KEY", "") or os.environ.get("GLM_API_KEY", "")

    def is_available(self) -> bool:
        return bool(self._api_key)

    def chat(self, messages, tools=None, stream=False, temperature=0.7, max_tokens=4096, model=None) -> LLMResponse:
        if not self._api_key:
            raise RuntimeError("Z.ai API key not configured. Set ZAI_API_KEY or GLM_API_KEY env var.")

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

        req = urllib.request.Request(ZAI_URL, data=body, headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._api_key}",
            "Accept-Language": "en-US,en",
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
                model=_model,
                tool_calls=msg.get("tool_calls", []),
                usage=result.get("usage", {}),
                latency_ms=latency,
                raw=result
            )
        except urllib.error.HTTPError as e:
            error_body = e.read().decode() if e.fp else ""
            logger.error(f"GLM API error {e.code}: {error_body[:500]}")
            # If paid model fails (401/403/429), fall back to free flash
            if _model != "glm-4.5-flash" and e.code in (401, 402, 403, 429):
                logger.info("GLM: Falling back from %s to glm-4.5-flash (free)", _model)
                return self.chat(messages, tools, stream, temperature, max_tokens, "glm-4.5-flash")
            raise RuntimeError(f"GLM API error {e.code}: {error_body[:200]}")
