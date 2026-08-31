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

# Condensed system prompt for Groq (keeps total tokens under 8000 TPM limit)
CONDENSED_SYSTEM = """You are Mr James, an AI builder assistant for EvolvixOS.
You help users build apps, write code, generate images, analyze data, and manage servers.
You have tools available - use them when needed to complete tasks.
Be helpful, concise, and proactive. Show results clearly."""

# Essential tools only (keeps payload small for Groq free tier 8000 TPM limit)
ESSENTIAL_TOOL_NAMES = {
    "bash", "file_write", "file_read", "file_list", "file_upload",
    "python_exec", "web_search", "web_fetch", "image_generate",
    "ui_generate", "memory_save", "memory_load", "memory_list",
    "skill_run", "code_analyze", "service_check", "system_info",
    "git", "list_models", "http_request"
}

class GroqProvider(LLMProvider):
    name = "groq"
    is_local = False
    supports_tools = True
    supports_vision = False
    supports_streaming = True
    max_context = 128000
    latency_tier = "ultra-fast"

    models_by_task = {
        "chat": "openai/gpt-oss-20b",
        "code": "openai/gpt-oss-20b",
        "reasoning": "openai/gpt-oss-20b",
        "simple": "openai/gpt-oss-20b",
    }
    default_model = "openai/gpt-oss-20b"

    def __init__(self):
        self._api_key = os.environ.get("GROQ_API_KEY", "")

    def is_available(self) -> bool:
        return bool(self._api_key)

    def _filter_tools(self, tools):
        """Filter to essential tools only to stay under Groq's 8000 TPM limit."""
        if not tools:
            return None
        filtered = [t for t in tools if t.get("function", {}).get("name", "") in ESSENTIAL_TOOL_NAMES]
        return filtered if filtered else None

    def chat(self, messages, tools=None, stream=False, temperature=0.7, max_tokens=4096, model=None) -> LLMResponse:
        if not self._api_key:
            raise RuntimeError("Groq API key not configured")

        # Condense system prompt to save tokens (Groq free tier: 8000 TPM)
        condensed_messages = []
        for msg in messages:
            if msg.get("role") == "system":
                # Replace long system prompt with condensed version
                if len(msg.get("content", "")) > 500:
                    condensed_messages.append({"role": "system", "content": CONDENSED_SYSTEM})
                else:
                    condensed_messages.append(msg)
            else:
                condensed_messages.append(msg)

        # Filter tools to essential set only
        filtered_tools = self._filter_tools(tools)

        body = json.dumps({
            "model": model or self.default_model,
            "messages": condensed_messages,
            "tools": filtered_tools,
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
            model=model or self.default_model,
            tool_calls=msg.get("tool_calls", []),
            usage=result.get("usage", {}),
            latency_ms=latency,
            raw=result
        )
