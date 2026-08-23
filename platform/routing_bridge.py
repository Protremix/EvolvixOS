"""
Unified LLM routing bridge — makes the platform layer use V10's LLMRegistry/ModelRouter.

This eliminates the duplicate routing system and enforces privacy mode (LOCAL/HYBRID/CLOUD).
"""
import os
import sys
import json
import asyncio
import urllib.request
import logging
from typing import Optional, Tuple

logger = logging.getLogger("evolvixos.platform.routing")

# Ensure v10 is importable
V10_PATH = os.path.join(os.path.dirname(__file__), "..", "v10")
if V10_PATH not in sys.path:
    sys.path.insert(0, os.path.abspath(V10_PATH))
EVOLVIXOS_ROOT = os.path.join(os.path.dirname(__file__), "..")
if EVOLVIXOS_ROOT not in sys.path:
    sys.path.insert(0, os.path.abspath(EVOLVIXOS_ROOT))

_registry = None
_router = None

def _get_router():
    """Lazy-init the V10 LLMRegistry + ModelRouter singleton."""
    global _registry, _router
    if _router is not None:
        return _registry, _router
    try:
        from v10.providers.base import LLMRegistry, PrivacyMode
        from v10.router.model_router import ModelRouter

        _registry = LLMRegistry()

        # Apply privacy mode from env
        mode_str = os.environ.get("EVOLVIX_PRIVACY_MODE", "HYBRID").upper()
        try:
            mode = PrivacyMode.from_str(mode_str)
        except ValueError:
            mode = PrivacyMode.HYBRID
        _registry.set_privacy_mode(mode)
        logger.info(f"V10 routing initialized — privacy_mode={mode.value}, providers={len(_registry.list_providers())}")

        _router = ModelRouter(_registry)
        return _registry, _router
    except Exception as e:
        logger.warning(f"V10 routing unavailable, will use fallback: {e}")
        return None, None


def _v10_route_and_chat_sync(messages: list, model: str = "auto", temperature: float = 0.7,
                              max_tokens: int = 4096, prefer_cloud: bool = False) -> Tuple[str, str, str]:
    """
    Use V10 ModelRouter to route and execute.
    Returns (response_text, provider_used, model_used).
    """
    registry, router = _get_router()
    if router is None:
        return None, None, None

    # Extract the user prompt for classification
    user_prompt = ""
    for m in reversed(messages):
        if m.get("role") == "user":
            user_prompt = m.get("content", "")
            break

    # If model is "auto" and prefer_cloud, skip V10's simple→local routing
    if model == "auto" and prefer_cloud:
        # Check privacy mode — if LOCAL, we can't use cloud
        if registry.can_use_cloud():
            cloud_providers = registry.get_cloud_providers()
            if cloud_providers:
                # Use OpenRouter (best for structured JSON) or first cloud provider
                preferred = "openrouter" if "openrouter" in cloud_providers else cloud_providers[0]
                provider = registry.get(preferred)
                if provider:
                    try:
                        response = provider.chat(messages, temperature=temperature, max_tokens=max_tokens)
                        return response.content, preferred, response.model
                    except Exception as e:
                        logger.warning(f"prefer_cloud {preferred} failed: {e}")
                        # Try next cloud provider
                        for name in cloud_providers:
                            if name == preferred:
                                continue
                            p = registry.get(name)
                            if p:
                                try:
                                    response = p.chat(messages, temperature=temperature, max_tokens=max_tokens)
                                    return response.content, name, response.model
                                except Exception:
                                    continue
        # If LOCAL mode or all cloud failed, fall through to normal V10 routing

    # If model is specified directly, use that provider
    if model != "auto":
        try:
            if ":" in model and "/" not in model:
                # Local Ollama model
                provider = registry.get("ollama")
                if provider:
                    response = provider.chat(model, messages, temperature=temperature)
                    return response.content, "ollama", model
            else:
                # Cloud model — try OpenRouter
                provider = registry.get("openrouter")
                if provider:
                    response = provider.chat(messages, model=model, temperature=temperature, max_tokens=max_tokens)
                    return response.content, "openrouter", model
        except Exception as e:
            logger.warning(f"V10 direct model routing failed for {model}: {e}")

    # Normal V10 auto-routing
    if model == "auto":
        try:
            response, decision = router.execute(user_prompt, messages, temperature=temperature)
            return response.content, decision.provider, decision.model
        except Exception as e:
            logger.warning(f"V10 auto-routing failed: {e}")

    return None, None, None


async def unified_chat(messages: list, model: str = "auto", temperature: float = 0.7,
                       max_tokens: int = 4096, prefer_cloud: bool = False) -> dict:
    """
    Unified chat function that tries V10 routing first, falls back to inline routing.

    Args:
        prefer_cloud: If True, skip V10's simple→local routing and use cloud providers
                      directly. Used by the platform builder which needs cloud models
                      for structured JSON tool-following.

    Returns: {"content": str, "provider": str, "model": str, "privacy_mode": str}
    """
    # ── Try V10 routing first ──
    try:
        result = await asyncio.to_thread(
            _v10_route_and_chat_sync, messages, model, temperature, max_tokens, prefer_cloud
        )
        if result[0]:
            registry, _ = _get_router()
            privacy = "HYBRID"
            if registry:
                from v10.providers.base import PrivacyMode
                privacy = registry.privacy_mode.value
            return {"content": result[0], "provider": result[1], "model": result[2], "privacy_mode": privacy}
    except Exception as e:
        logger.warning(f"V11 routing bridge error: {e}")

    # ── Fallback: inline routing (legacy, but respects privacy mode) ──
    privacy_mode = os.environ.get("EVOLVIX_PRIVACY_MODE", "HYBRID").upper()

    # In LOCAL mode, ONLY use Ollama — never cloud
    if privacy_mode == "LOCAL":
        ollama_url = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
        local_model = os.environ.get("OLLAMA_DEFAULT_MODEL", "qwen2.5:7b")
        try:
            payload = json.dumps({
                "model": local_model,
                "messages": messages,
                "stream": False,
                "options": {"temperature": temperature}
            }).encode()
            req = urllib.request.Request(
                f"{ollama_url}/api/chat", data=payload,
                headers={"Content-Type": "application/json"}
            )
            resp = urllib.request.urlopen(req, timeout=90)
            data = json.loads(resp.read())
            return {
                "content": data.get("message", {}).get("content", ""),
                "provider": "ollama", "model": local_model, "privacy_mode": "LOCAL"
            }
        except Exception as e:
            return {"content": f"Error: LOCAL mode but Ollama unavailable: {e}",
                    "provider": "none", "model": "none", "privacy_mode": "LOCAL"}

    # HYBRID/CLOUD: use OpenRouter → GLM → Ollama fallback chain
    selected_model = model
    if selected_model == "auto":
        user_msg = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                user_msg = m.get("content", "").lower()
                break
        if any(w in user_msg for w in ["build", "create", "make", "add", "entity", "crm", "app"]):
            selected_model = "z-ai/glm-5"
        elif any(w in user_msg for w in ["code", "function", "api", "deploy", "python"]):
            selected_model = "openai/gpt-oss-120b"
        elif any(w in user_msg for w in ["analyze", "reason", "think", "complex", "architect"]):
            selected_model = "z-ai/glm-5.2"
        else:
            selected_model = "openai/gpt-oss-20b"

    or_key = os.environ.get("OPENROUTER_API_KEY", "")
    if or_key:
        fallback_chain = list(dict.fromkeys([selected_model, "z-ai/glm-5", "openai/gpt-oss-20b", "z-ai/glm-5.2:free"]))
        for try_model in fallback_chain:
            try:
                or_payload = json.dumps({
                    "model": try_model, "messages": messages,
                    "stream": False, "temperature": temperature, "max_tokens": max_tokens
                }).encode()
                or_req = urllib.request.Request(
                    "https://openrouter.ai/api/v1/chat/completions",
                    data=or_payload,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {or_key}",
                        "HTTP-Referer": "https://evolvixos.com",
                        "X-Title": "EvolvixOS"
                    }
                )
                or_resp = urllib.request.urlopen(or_req, timeout=60)
                or_data = json.loads(or_resp.read())
                or_resp.close()
                or_msg = or_data.get("choices", [{}])[0].get("message", {})
                content = or_msg.get("content") or or_msg.get("reasoning", "") or ""
                if content and len(content) > 5:
                    return {"content": content, "provider": "openrouter", "model": try_model, "privacy_mode": privacy_mode}
            except Exception:
                continue

    # GLM direct fallback
    zai_key = os.environ.get("ZAI_API_KEY", "")
    if zai_key:
        try:
            glm_payload = json.dumps({
                "model": "glm-4.5-flash", "messages": messages,
                "stream": False, "temperature": temperature, "max_tokens": max_tokens
            }).encode()
            glm_req = urllib.request.Request(
                "https://api.z.ai/api/paas/v4/chat/completions",
                data=glm_payload,
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {zai_key}", "Accept-Language": "en-US,en"}
            )
            glm_resp = urllib.request.urlopen(glm_req, timeout=60)
            glm_data = json.loads(glm_resp.read())
            glm_resp.close()
            content = glm_data.get("choices", [{}])[0].get("message", {}).get("content", "")
            if content:
                return {"content": content, "provider": "zai", "model": "glm-4.5-flash", "privacy_mode": privacy_mode}
        except Exception:
            pass

    # Ollama final fallback
    ollama_url = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
    local_model = os.environ.get("OLLAMA_DEFAULT_MODEL", "qwen2.5:7b")
    try:
        payload = json.dumps({"model": local_model, "messages": messages, "stream": False,
                              "options": {"temperature": temperature}}).encode()
        req = urllib.request.Request(f"{ollama_url}/api/chat", data=payload, headers={"Content-Type": "application/json"})
        resp = urllib.request.urlopen(req, timeout=90)
        data = json.loads(resp.read())
        return {"content": data.get("message", {}).get("content", ""),
                "provider": "ollama", "model": local_model, "privacy_mode": privacy_mode}
    except Exception as e:
        return {"content": f"Error: All LLM providers failed. Last error: {e}",
                "provider": "none", "model": "none", "privacy_mode": privacy_mode}
