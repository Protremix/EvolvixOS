"""
EvolvixOS v10 — Unified LLM Provider Abstraction
=================================================
Single interface for all LLM providers. No more ad-hoc per-provider functions.
BaseAgent depends on LLMProvider interface, never on concrete providers.

Privacy modes:
  LOCAL  — only local models (Ollama). Cloud calls are FORBIDDEN.
  HYBRID — simple → local, coding → coding model, complex → cloud, vision → vision model
  CLOUD  — use configured cloud providers (Groq, Gemini, Kimi, etc.)
"""

from __future__ import annotations
import abc
import enum
import json
import os
import time
import logging
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger("evolvixos.v10.providers")


# ─── Privacy Modes ────────────────────────────────────────────────────────────

class PrivacyMode(enum.Enum):
    LOCAL = "LOCAL"
    HYBRID = "HYBRID"
    CLOUD = "CLOUD"

    @classmethod
    def from_str(cls, s: str) -> "PrivacyMode":
        try:
            return cls[s.upper()]
        except KeyError:
            raise ValueError(f"Invalid privacy mode: {s!r}. Must be LOCAL, HYBRID, or CLOUD.")


# ─── Routing Decision ────────────────────────────────────────────────────────

@dataclass
class RoutingDecision:
    """Structured routing decision — single source of truth for why a provider was chosen."""
    task_type: str           # chat, code, reasoning, vision, image, video, system, etc.
    complexity: str           # simple, medium, complex
    privacy_mode: str        # LOCAL, HYBRID, CLOUD
    provider: str            # ollama, groq, gemini, kimi, etc.
    model: str               # specific model name
    reason: str              # human-readable explanation
    available_providers: list = field(default_factory=list)  # what was available at decision time

    def to_dict(self) -> dict:
        return {
            "task_type": self.task_type,
            "complexity": self.complexity,
            "privacy_mode": self.privacy_mode,
            "provider": self.provider,
            "model": self.model,
            "reason": self.reason,
            "available_providers": self.available_providers,
        }


# ─── LLM Response ────────────────────────────────────────────────────────────

@dataclass
class LLMResponse:
    """Unified response from any provider."""
    content: str
    provider: str
    model: str
    tool_calls: list = field(default_factory=list)
    usage: dict = field(default_factory=dict)
    latency_ms: float = 0.0
    raw: Any = None


# ─── Base Provider Interface ──────────────────────────────────────────────────

class LLMProvider(abc.ABC):
    """Abstract base for all LLM providers. No concrete provider dependencies."""

    name: str = "base"
    is_local: bool = False
    supports_tools: bool = False
    supports_vision: bool = False
    supports_streaming: bool = False
    max_context: int = 4096
    latency_tier: str = "medium"  # ultra-fast, fast, medium, slow

    @abc.abstractmethod
    def is_available(self) -> bool:
        """Check if this provider is configured and reachable."""
        ...

    @abc.abstractmethod
    def chat(self, messages: list, tools: list = None, stream: bool = False,
             temperature: float = 0.7, max_tokens: int = 4096) -> LLMResponse:
        """Send a chat completion request. Returns unified LLMResponse."""
        ...

    def health_check(self) -> dict:
        """Return health status dict."""
        return {"provider": self.name, "available": self.is_available(), "local": self.is_local}


# ─── Provider Registry ────────────────────────────────────────────────────────

class LLMRegistry:
    """Central registry for all providers. Single source of truth."""

    def __init__(self):
        self._providers: dict[str, LLMProvider] = {}
        self._privacy_mode: PrivacyMode = PrivacyMode.HYBRID
        self._default_local: Optional[str] = None
        self._default_cloud: Optional[str] = None
        self._auto_register()

    def _auto_register(self):
        """Auto-register all available providers."""
        for mod_name, cls_name in [
            ("v10.providers.ollama", "OllamaProvider"),
            ("v10.providers.openrouter", "OpenRouterProvider"),
            ("v10.providers.groq", "GroqProvider"),
            ("v10.providers.gemini", "GeminiProvider"),
            ("v10.providers.kimi", "KimiProvider"),
            ("v10.providers.glm", "GLMProvider"),
            ("v10.providers.nvidia", "NvidiaProvider"),
        ]:
            try:
                mod = __import__(mod_name, fromlist=[cls_name])
                cls = getattr(mod, cls_name)
                provider = cls()
                if provider.is_available():
                    self.register(provider)
            except Exception as e:
                logger.debug(f"Could not auto-register {cls_name}: {e}")

    def register(self, provider: LLMProvider):
        self._providers[provider.name] = provider
        logger.info(f"Registered provider: {provider.name} (local={provider.is_local})")
        if provider.is_local and not self._default_local:
            self._default_local = provider.name
        elif not provider.is_local and not self._default_cloud:
            self._default_cloud = provider.name

    def get(self, name: str) -> Optional[LLMProvider]:
        return self._providers.get(name)

    def list_providers(self) -> list[dict]:
        return [
            {"name": p.name, "local": p.is_local, "available": p.is_available(),
             "tools": p.supports_tools, "vision": p.supports_vision,
             "context": p.max_context, "latency": p.latency_tier}
            for p in self._providers.values()
        ]

    def list_available(self) -> list[str]:
        return [name for name, p in self._providers.items() if p.is_available()]

    def set_privacy_mode(self, mode: PrivacyMode):
        self._privacy_mode = mode
        logger.info(f"Privacy mode set to: {mode.value}")

    @property
    def privacy_mode(self) -> PrivacyMode:
        return self._privacy_mode

    def get_local_providers(self) -> list[str]:
        return [name for name, p in self._providers.items() if p.is_local and p.is_available()]

    def get_cloud_providers(self) -> list[str]:
        return [name for name, p in self._providers.items() if not p.is_local and p.is_available()]

    def can_use_cloud(self) -> bool:
        """In LOCAL mode, cloud is FORBIDDEN. In HYBRID/CLOUD, cloud is allowed."""
        return self._privacy_mode != PrivacyMode.LOCAL

    def select_for_task(self, task_type: str, complexity: str = "medium",
                        needs_vision: bool = False, needs_tools: bool = False) -> RoutingDecision:
        """Select the best provider for a task, respecting privacy mode."""
        available = self.list_available()
        local_available = self.get_local_providers()
        cloud_available = self.get_cloud_providers()

        # ── LOCAL mode: ONLY local providers, NEVER cloud ──
        if self._privacy_mode == PrivacyMode.LOCAL:
            if not local_available:
                return RoutingDecision(
                    task_type=task_type, complexity=complexity,
                    privacy_mode="LOCAL", provider="none", model="none",
                    reason="LOCAL mode but no local providers available",
                    available_providers=available)
            # Pick best local provider
            provider_name = local_available[0]
            p = self._providers[provider_name]
            return RoutingDecision(
                task_type=task_type, complexity=complexity,
                privacy_mode="LOCAL", provider=provider_name,
                model=self._get_model_for_task(p, task_type),
                reason=f"LOCAL mode: using {provider_name} (cloud forbidden)",
                available_providers=available)

        # ── HYBRID mode: simple → local, complex → cloud ──
        if self._privacy_mode == PrivacyMode.HYBRID:
            if complexity == "simple" and local_available:
                provider_name = local_available[0]
                p = self._providers[provider_name]
                return RoutingDecision(
                    task_type=task_type, complexity=complexity,
                    privacy_mode="HYBRID", provider=provider_name,
                    model=self._get_model_for_task(p, task_type),
                    reason=f"HYBRID: simple task → local ({provider_name})",
                    available_providers=available)

            if needs_vision:
                # Find vision-capable provider
                for name in cloud_available + local_available:
                    p = self._providers[name]
                    if p.supports_vision:
                        return RoutingDecision(
                            task_type=task_type, complexity=complexity,
                            privacy_mode="HYBRID", provider=name,
                            model=self._get_model_for_task(p, task_type),
                            reason=f"HYBRID: vision task → {name} (vision-capable)",
                            available_providers=available)

            # ── Agent/reasoning tasks → NVIDIA Nemotron if available ──
            if task_type in ("reasoning", "agent", "code") and "nvidia" in cloud_available:
                provider_name = "nvidia"
                p = self._providers[provider_name]
                return RoutingDecision(
                    task_type=task_type, complexity=complexity,
                    privacy_mode="HYBRID", provider=provider_name,
                    model=self._get_model_for_task(p, task_type),
                    reason=f"HYBRID: {task_type} task → NVIDIA Nemotron (agent-optimized)",
                    available_providers=available)

            if complexity == "complex" and cloud_available:
                # Prefer NVIDIA for complex tasks if available
                if "nvidia" in cloud_available:
                    provider_name = "nvidia"
                else:
                    provider_name = cloud_available[0]
                p = self._providers[provider_name]
                return RoutingDecision(
                    task_type=task_type, complexity=complexity,
                    privacy_mode="HYBRID", provider=provider_name,
                    model=self._get_model_for_task(p, task_type),
                    reason=f"HYBRID: complex task → cloud ({provider_name})",
                    available_providers=available)

            # Fallback to local if available, then cloud
            if local_available:
                provider_name = local_available[0]
                p = self._providers[provider_name]
                return RoutingDecision(
                    task_type=task_type, complexity=complexity,
                    privacy_mode="HYBRID", provider=provider_name,
                    model=self._get_model_for_task(p, task_type),
                    reason=f"HYBRID: fallback → local ({provider_name})",
                    available_providers=available)
            if cloud_available:
                provider_name = cloud_available[0]
                p = self._providers[provider_name]
                return RoutingDecision(
                    task_type=task_type, complexity=complexity,
                    privacy_mode="HYBRID", provider=provider_name,
                    model=self._get_model_for_task(p, task_type),
                    reason=f"HYBRID: no local available → cloud ({provider_name})",
                    available_providers=available)

        # ── CLOUD mode: use cloud providers ──
        if self._privacy_mode == PrivacyMode.CLOUD:
            if not cloud_available and not local_available:
                return RoutingDecision(
                    task_type=task_type, complexity=complexity,
                    privacy_mode="CLOUD", provider="none", model="none",
                    reason="CLOUD mode but no providers available",
                    available_providers=available)
            # Prefer cloud, fallback to local
            pool = cloud_available if cloud_available else local_available
            provider_name = pool[0]
            p = self._providers[provider_name]
            return RoutingDecision(
                task_type=task_type, complexity=complexity,
                privacy_mode="CLOUD", provider=provider_name,
                model=self._get_model_for_task(p, task_type),
                reason=f"CLOUD mode: using {provider_name}",
                available_providers=available)

        # Nothing available
        return RoutingDecision(
            task_type=task_type, complexity=complexity,
            privacy_mode=self._privacy_mode.value, provider="none", model="none",
            reason="No providers available",
            available_providers=available)

    def _get_model_for_task(self, provider: LLMProvider, task_type: str) -> str:
        """Get the default model for a task type from a provider."""
        # Provider-specific model selection can be overridden
        if hasattr(provider, 'models_by_task') and task_type in provider.models_by_task:
            return provider.models_by_task[task_type]
        return getattr(provider, 'default_model', provider.name)


# ─── Global Registry Instance ─────────────────────────────────────────────────

_registry: Optional[LLMRegistry] = None

def get_registry() -> LLMRegistry:
    global _registry
    if _registry is None:
        _registry = LLMRegistry()
    return _registry

def init_registry(mode: str = "HYBRID") -> LLMRegistry:
    """Initialize the global registry with all configured providers."""
    global _registry
    _registry = LLMRegistry()
    _registry.set_privacy_mode(PrivacyMode.from_str(mode))

    # Register local providers
    from v10.providers.ollama import OllamaProvider
    ollama = OllamaProvider()
    if ollama.is_available():
        _registry.register(ollama)

    # Register cloud providers (only if not LOCAL mode)
    if mode.upper() != "LOCAL":
        from v10.providers.groq import GroqProvider
        groq = GroqProvider()
        if groq.is_available():
            _registry.register(groq)

        from v10.providers.gemini import GeminiProvider
        gemini = GeminiProvider()
        if gemini.is_available():
            _registry.register(gemini)

        from v10.providers.kimi import KimiProvider
        kimi = KimiProvider()
        if kimi.is_available():
            _registry.register(kimi)

    return _registry
