"""
LLM Provider Registry — manages provider registration, selection, and fallback.

Priority order: GPT-4o > Claude > Local
If the preferred provider fails, falls back to the next available.
"""

import os
from typing import Optional

from app.ai.llm_provider import LLMProvider, LLMResponse
from app.ai.providers.gpt4o_provider import GPT4oProvider
from app.ai.providers.claude_provider import ClaudeProvider
from app.ai.providers.local_provider import LocalLLMProvider


class LLMRegistry:
    """Registry for LLM providers with automatic fallback."""

    def __init__(self):
        self._providers: dict[str, LLMProvider] = {}
        self._priority = ["gpt4o", "claude", "local"]
        self._selected: Optional[str] = None
        self._register_defaults()

    def _register_defaults(self):
        """Register all default providers."""
        try:
            self.register("gpt4o", GPT4oProvider())
        except Exception:
            pass

        try:
            self.register("claude", ClaudeProvider())
        except Exception:
            pass

        try:
            self.register("local", LocalLLMProvider())
        except Exception:
            pass

    def register(self, name: str, provider: LLMProvider) -> None:
        """Register a new provider."""
        self._providers[name] = provider

    def get_provider(self, name: Optional[str] = None) -> Optional[LLMProvider]:
        """Get a specific provider by name, or the best available."""
        if name:
            return self._providers.get(name)
        return self.get_best_available()

    def get_best_available(self) -> Optional[LLMProvider]:
        """Get the best available provider based on priority."""
        # If a provider is manually selected and available, use it
        if self._selected and self._selected in self._providers:
            provider = self._providers[self._selected]
            if provider.is_available():
                return provider

        # Try providers in priority order
        for name in self._priority:
            provider = self._providers.get(name)
            if provider and provider.is_available():
                return provider

        return None

    def select_provider(self, name: str) -> bool:
        """Manually select a provider."""
        if name in self._providers:
            self._selected = name
            return True
        return False

    def list_providers(self) -> list[dict]:
        """List all registered providers with their status."""
        return [
            {
                "name": name,
                "model": provider.model_name(),
                "available": provider.is_available(),
                "priority": self._priority.index(name) if name in self._priority else 99,
            }
            for name, provider in self._providers.items()
        ]

    def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 4000,
    ) -> LLMResponse:
        """Send a chat request using the best available provider with fallback."""
        errors = []

        # Try providers in priority order
        providers_to_try = []
        if self._selected and self._selected in self._providers:
            providers_to_try.append(self._selected)
        for name in self._priority:
            if name not in providers_to_try:
                providers_to_try.append(name)

        for name in providers_to_try:
            provider = self._providers.get(name)
            if not provider or not provider.is_available():
                continue
            try:
                return provider.chat(system_prompt, user_prompt, temperature, max_tokens)
            except Exception as e:
                errors.append(f"{name}: {str(e)}")
                continue

        raise RuntimeError(f"All LLM providers failed: {'; '.join(errors)}")


# Global registry singleton
_registry: Optional[LLMRegistry] = None


def get_llm_registry() -> LLMRegistry:
    """Get or create the global LLM registry singleton."""
    global _registry
    if _registry is None:
        _registry = LLMRegistry()
    return _registry
