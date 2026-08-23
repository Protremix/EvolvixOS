"""
EvolvixOS v10 — Unified Model Router
=====================================
Single source of truth for routing decisions. Replaces all duplicated
classify_intent / select_engine / EngineSelector implementations.

Factors:
  - task_type: what the user is asking for
  - complexity: how hard the task is
  - model availability: which providers are up
  - context length: how much context the task needs
  - latency: speed requirements
  - privacy_mode: LOCAL / HYBRID / CLOUD
  - provider availability: health checks

Output: structured RoutingDecision with full audit trail.
"""

from __future__ import annotations
import re
import logging
from typing import Optional
from v10.providers.base import LLMRegistry, PrivacyMode, RoutingDecision

logger = logging.getLogger("evolvixos.v10.router")


class ModelRouter:
    """One router to rule them all. No duplicated routing logic."""

    def __init__(self, registry: LLMRegistry):
        self.registry = registry
        self._decision_log: list[RoutingDecision] = []

    def classify(self, prompt: str) -> tuple[str, str, bool, bool]:
        """
        Classify user prompt into (task_type, complexity, needs_vision, needs_tools).
        This is the ONLY classification logic — no duplicates elsewhere.
        """
        t = prompt.lower().strip()

        # ── Detect vision needs ──
        needs_vision = bool(re.search(
            r'\b(analyze.+image|what.+in.+image|describe.+image|'
            r'ocr|chart|diagram|screenshot|vision)\b', t))

        # ── Detect tool needs ──
        needs_tools = bool(re.search(
            r'\b(run|execute|install|deploy|build|create|write|'
            r'search|fetch|call|api|bash|python|code|script|file)\b', t))

        # ── Task type classification ──
        # Vision
        if needs_vision:
            return "vision", "medium", True, needs_tools

        # Image generation
        if re.search(r'\b(draw|paint|generate.+image|create.+image|logo|art|portrait)\b', t) \
           and not re.search(r'\b(code|api|script|function|build)\b', t):
            return "image", "medium", False, False

        # Video generation
        if re.search(r'\b(video|movie|film|animate|cinema|clip|wan2)\b', t):
            return "video", "complex", False, False

        # Crypto/blockchain
        if re.search(r'\b(crypto|bitcoin|ethereum|blockchain|defi|token|nft|web3|'
                      r'smart contract|solidity|wallet|staking)\b', t):
            return "crypto", "medium", False, True

        # Complex reasoning (check before code - some keywords overlap)
        if re.search(r'\b(why|how do|how to|explain|compare|strategy|plan|architect|'
                      r'design pattern|best practice|production)\b', t):
            return "reasoning", "complex", False, False

        # Code tasks
        if re.search(r'\b(code|app|api|function|script|build|react|python|javascript|'
                      r'html|css|deploy|debug|refactor|sql|database|backend|frontend)\b', t):
            # Determine complexity by prompt length and keywords
            if re.search(r'\b(architect|design|system|distributed|microservice|'
                         r'scalable|production|enterprise)\b', t):
                return "code", "complex", False, True
            return "code", "medium", False, True

        # File analysis
        if re.search(r'\b(analyze|review|audit|check|inspect|read|file|upload|attachment)\b', t):
            return "analysis", "medium", needs_vision, True

        # System management
        if re.search(r'\b(server|service|nginx|docker|systemctl|restart|status|'
                      r'install|config|deploy|run|ls\s|cat\s|ps\s|df\s)\b', t):
            return "system", "simple", False, True

        # Media creation
        if re.search(r'\b(voice|audio|narrate|tts|speak|podcast|music|sound)\b', t):
            return "media", "medium", False, False



        # Tool/API discovery
        if re.search(r'\b(find.+tool|search.+tool|what.+tools|available.+tool|'
                      r'find.+api|search.+api)\b', t):
            return "discovery", "simple", False, True

        # Learning
        if re.search(r'\b(learn|tutorial|course|guide|how to|teach me)\b', t):
            return "learning", "simple", False, False

        # Default: simple chat
        # Complexity by prompt length
        complexity = "simple" if len(t) < 100 else "medium"
        return "chat", complexity, False, False

    def route(self, prompt: str) -> RoutingDecision:
        """
        Route a prompt to the best provider.
        Returns a structured RoutingDecision — the single source of truth.
        """
        task_type, complexity, needs_vision, needs_tools = self.classify(prompt)
        decision = self.registry.select_for_task(
            task_type=task_type,
            complexity=complexity,
            needs_vision=needs_vision,
            needs_tools=needs_tools
        )

        # Log the decision for audit trail
        self._decision_log.append(decision)
        if len(self._decision_log) > 1000:
            self._decision_log = self._decision_log[-500:]

        logger.info(f"Route: {task_type}/{complexity} → {decision.provider}/{decision.model} "
                    f"({decision.privacy_mode}) — {decision.reason}")

        return decision

    def execute(self, prompt: str, messages: list, tools: list = None,
                temperature: float = 0.7) -> tuple:
        """
        Route and execute in one step.
        Returns (LLMResponse, RoutingDecision).
        """
        decision = self.route(prompt)
        if decision.provider == "none":
            from v10.providers.base import LLMResponse
            return LLMResponse(
                content="Error: No providers available for this request.",
                provider="none", model="none"), decision

        provider = self.registry.get(decision.provider)
        if not provider:
            from v10.providers.base import LLMResponse
            return LLMResponse(
                content=f"Error: Provider {decision.provider} not found.",
                provider="none", model="none"), decision

        # ── ENFORCE LOCAL MODE ──
        # In LOCAL mode, if somehow a cloud provider was selected, BLOCK it
        if self.registry.privacy_mode == PrivacyMode.LOCAL and not provider.is_local:
            logger.error(f"SECURITY: Blocked cloud provider {decision.provider} in LOCAL mode!")
            from v10.providers.base import LLMResponse
            return LLMResponse(
                content="Error: Cloud providers are forbidden in LOCAL privacy mode.",
                provider="blocked", model="none"), decision

        try:
            response = provider.chat(
                messages=messages,
                tools=tools,
                temperature=temperature,
            )
            return response, decision
        except Exception as e:
            logger.error(f"Provider {decision.provider} failed: {e}")
            # Fallback chain
            available = self.registry.list_available()
            for fallback_name in available:
                if fallback_name == decision.provider:
                    continue
                fallback = self.registry.get(fallback_name)
                # In LOCAL mode, don't fallback to cloud
                if self.registry.privacy_mode == PrivacyMode.LOCAL and not fallback.is_local:
                    continue
                try:
                    logger.info(f"Fallback to {fallback_name}")
                    response = fallback.chat(
                        messages=messages, tools=tools,
                        temperature=temperature)
                    return response, decision
                except Exception as e2:
                    logger.error(f"Fallback {fallback_name} also failed: {e2}")
                    continue

            from v10.providers.base import LLMResponse
            return LLMResponse(
                content=f"Error: All providers failed. Last error: {e}",
                provider="failed", model="none"), decision

    def get_decision_log(self, limit: int = 50) -> list[dict]:
        """Return recent routing decisions for audit."""
        return [d.to_dict() for d in self._decision_log[-limit:]]

    def get_stats(self) -> dict:
        """Return routing statistics."""
        from collections import Counter
        providers = Counter(d.provider for d in self._decision_log)
        task_types = Counter(d.task_type for d in self._decision_log)
        return {
            "total_decisions": len(self._decision_log),
            "by_provider": dict(providers),
            "by_task_type": dict(task_types),
            "privacy_mode": self.registry.privacy_mode.value,
            "available_providers": self.registry.list_available(),
        }


# ─── Global Router Instance ───────────────────────────────────────────────────

_router: Optional[ModelRouter] = None

def get_router() -> ModelRouter:
    global _router
    if _router is None:
        from v10.providers.base import get_registry
        _router = ModelRouter(get_registry())
    return _router

def init_router(mode: str = "HYBRID") -> ModelRouter:
    global _router
    from v10.providers.base import init_registry
    registry = init_registry(mode)
    _router = ModelRouter(registry)
    return _router
