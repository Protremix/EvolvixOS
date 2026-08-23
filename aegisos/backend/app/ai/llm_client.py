"""
LLM client for AI agents — wraps OpenAI GPT-4o API calls.

Provides a unified interface for all AI agents to make LLM calls
with proper error handling, retry logic, and token management.
"""

import json
import os
import time
from typing import Any, Optional
from dataclasses import dataclass

import httpx
from structlog import get_logger

logger = get_logger(__name__)


@dataclass
class LLMResponse:
    """Response from an LLM call."""
    content: str
    model: str
    tokens_used: int
    latency_ms: float


class LLMClient:
    """
    Client for making GPT-4o API calls.
    Handles authentication, retries, and response parsing.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o",
        max_retries: int = 3,
        timeout: int = 120,
    ):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY_2") or os.environ.get("OPENAI_API_KEY", "")
        if not self.api_key:
            logger.warning("No OpenAI API key found — LLM calls will fail")
        elif not self._validate_api_key(self.api_key):
            logger.warning("OpenAI API key format appears invalid — expected sk-... prefix")
        self.model = model
        self.max_retries = max_retries if (self.api_key and self._validate_api_key(self.api_key)) else 1
        self.timeout = timeout
        self._base_url = "https://api.openai.com/v1/chat/completions"
        # Persistent clients — avoid connection setup overhead per call
        self._ollama_client = httpx.Client(timeout=30)
        self._openai_client = httpx.Client(timeout=timeout)

    @staticmethod
    def _validate_api_key(key: str) -> bool:
        """Validate that the API key has the expected OpenAI format."""
        if not key or len(key) < 20:
            return False
        # OpenAI keys start with sk- and are at least 51 chars
        if not key.startswith("sk-"):
            return False
        return True

    def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 4000,
    ) -> LLMResponse:
        """Make a chat completion call. Tries OpenAI first, falls back to local Ollama."""
        if self.api_key and self.api_key != "placeholder" and self._validate_api_key(self.api_key):
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            last_error = None
            for attempt in range(self.max_retries):
                try:
                    start = time.time()
                    response = self._openai_client.post(self._base_url, headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"}, json=payload)
                        response.raise_for_status()
                        data = response.json()
                        latency_ms = (time.time() - start) * 1000
                        content = data["choices"][0]["message"]["content"]
                        tokens = data.get("usage", {}).get("total_tokens", 0)
                        logger.info("llm_call_success", model=self.model, tokens=tokens, latency_ms=round(latency_ms, 2), attempt=attempt + 1)
                        return LLMResponse(content=content, model=self.model, tokens_used=tokens, latency_ms=latency_ms)
                except httpx.HTTPStatusError as e:
                    last_error = e
                    logger.error("llm_call_http_error", status_code=e.response.status_code, attempt=attempt + 1)
                    if e.response.status_code == 429: time.sleep(2 ** attempt)
                    elif e.response.status_code >= 500: time.sleep(2 ** attempt)
                    else: break
                except Exception as e:
                    last_error = e
                    logger.error("llm_call_error", error=str(e), attempt=attempt + 1)
                    time.sleep(2 ** attempt)
            logger.warning(f"OpenAI failed after retries, falling back to Ollama: {last_error}")
        return self._chat_ollama(system_prompt, user_prompt, temperature, max_tokens)

    def _chat_ollama(self, system_prompt: str, user_prompt: str, temperature: float = 0.3, max_tokens: int = 4000) -> LLMResponse:
        """Fallback: Use local Ollama when cloud providers are unavailable."""
        ollama_url = os.environ.get("OLLAMA_URL", "http://172.18.0.1:11434")
        ollama_model = os.environ.get("FALLBACK_LLM_MODEL", "qwen2.5:7b")  # 7b is 3x faster than 14b
        payload = {"model": ollama_model, "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}], "stream": False, "keep_alive": "30m", "options": {"temperature": temperature, "top_p": 0.9}}
        start = time.time()
        response = self._ollama_client.post(f"{ollama_url}/api/chat", headers={"Content-Type": "application/json"}, json=payload)
            response.raise_for_status()
            data = response.json()
            latency_ms = (time.time() - start) * 1000
            content = data.get("message", {}).get("content", "No response from model.")
            tokens = data.get("eval_count", 0)
            logger.info("llm_fallback_ollama_success", model=ollama_model, tokens=tokens, latency_ms=round(latency_ms, 2))
            return LLMResponse(content=content, model=ollama_model, tokens_used=tokens, latency_ms=latency_ms)

    def chat_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 4000,
    ) -> dict:
        """
        Make a chat completion call and parse JSON response.

        Returns:
            Parsed JSON dict from the LLM response.
        """
        response = self.chat(system_prompt, user_prompt, temperature, max_tokens)

        # Try to extract JSON from the response
        content = response.content.strip()

        # Handle markdown code blocks
        if content.startswith("```"):
            lines = content.split("\n")
            # Remove first and last lines (code block markers)
            lines = lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
            content = "\n".join(lines)

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Try to find JSON in the content
            start = content.find("{")
            end = content.rfind("}") + 1
            if start != -1 and end > start:
                return json.loads(content[start:end])
            raise


# Global LLM client instance
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Get or create the global LLM client singleton."""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
