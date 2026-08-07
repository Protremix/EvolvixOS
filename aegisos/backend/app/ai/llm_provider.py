"""
LLM Provider abstraction layer for EvolvixOS.

Supports multiple LLM providers (GPT-4o, Claude, local models) with
automatic fallback and provider selection.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, UTC


@dataclass
class LLMResponse:
    """Standardized response from any LLM provider."""
    content: str
    tokens_used: int
    model: str
    latency_ms: float
    finish_reason: str = "stop"
    provider: str = ""


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 4000,
    ) -> LLMResponse:
        """Send a chat completion request."""
        pass

    @abstractmethod
    def name(self) -> str:
        """Return the provider name."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this provider is available (API key set, server reachable)."""
        pass

    @abstractmethod
    def model_name(self) -> str:
        """Return the model name."""
        pass
