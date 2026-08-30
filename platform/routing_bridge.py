"""
Updated model routing for EvolvixOS platform — based on OpenRouter τ²-Bench Airline benchmark
data (Aug 23, 2026). Models ranked by tool-calling accuracy and cost efficiency.

BENCHMARK-DRIVEN MODEL SELECTION:
  Builder/Agent tasks (need JSON tool-following):
    Primary:   qwen/qwen3.8-27b        (80.7%, $0.076/task) — best value tool caller
    Fallback1: google/gemini-3.7-flash  (80.6%, $0.077/task) — fast, accurate
    Fallback2: stepfun/step-3.7-flash   (77.3%, $0.020/task) — cheapest reliable
    Fallback3: z-ai/glm-5               (74.8%, $0.036/task) — legacy fallback

  Code tasks:
    Primary:   deepseek/deepseek-v4-flash-0731  (76.3%, $0.010/task) — best code+tools value
    Fallback1: nvidia/nemotron-3-ultra         (76.9%, $0.10/task)  — Mike's requirement
    Fallback2: openai/gpt-oss-120b             (63.0%, $0.012/task) — legacy fallback

  Simple chat:
    Primary:   google/gemma-4-31b              (76.5%, $0.016/task) — great for chat
    Fallback1: deepseek/deepseek-v4-flash (75.2%, $0.009/task) — cheapest
    Fallback2: openai/gpt-oss-20b              (51.5%, $0.021/task) — legacy (BAD, avoid)

  Complex/Reasoning:
    Primary:   google/gemini-3.7-flash          (80.6%, $0.077/task)
    Fallback1: z-ai/glm-5.2                     (75.3%, $0.040/task) — legacy fallback
"""

import os
import sys
import json
import asyncio
import urllib.request
import logging
from typing import Tuple

logger = logging.getLogger("evolvixos.platform.routing")

V10_PATH = os.path.join(os.path.dirname(__file__), "..", "v10")
if V10_PATH not in sys.path:
    sys.path.insert(0, os.path.abspath(V10_PATH))
EVOLVIXOS_ROOT = os.path.join(os.path.dirname(__file__), "..")
if EVOLVIXOS_ROOT not in sys.path:
    sys.path.insert(0, os.path.abspath(EVOLVIXOS_ROOT))

_registry = None
_router = None

# ─── Benchmark-driven model chains ───
BUILDER_MODELS = [
    "qwen/qwen3.8-27b",           # 80.7% tool accuracy, $0.076/task
    "google/gemini-3.7-flash",     # 80.6%, $0.077/task
    "moonshotai/kimi-k3",          # 2.8T multimodal, 1M ctx (NVIDIA free)
    "meta/muse-glimmer-30b",       # multimodal reasoning + tool-calling (NVIDIA free)
    "stepfun/step-3.7-flash",      # 77.3%, $0.020/task
    "z-ai/glm-5",                  # 74.8%, $0.036/task (legacy)
]
CODE_MODELS = [
    "deepseek/deepseek-v4-flash-0731", # 76.3%, $0.010/task (NVIDIA free)
    "deepseek/deepseek-v4-pro-0813",   # 1M ctx, MoE (NVIDIA free)
    "qwen/qwen3-coder-30b-a3b-instruct",  # 33B MoE, agentic coding (NVIDIA free)
    "nvidia/nemotron-3-ultra-550b-a55b",  # 76.9%, 1M ctx (NVIDIA free)
]
CHAT_MODELS = [
    "nvidia/nemotron-3.5-lightning", # 30B MoE, 3B active, fast (NVIDIA free)
    "google/gemma-4-31b-it",               # 76.5%, $0.016/task
    "deepseek/deepseek-v4-flash",   # 75.2%, $0.009/task
    "openai/gpt-oss-20b",               # 51.5%, $0.021/task (legacy, BAD)
]
REASONING_MODELS = [
    "google/gemini-3.7-flash",          # 80.6%, $0.077/task
    "z-ai/glm-5.2",                     # 75.3%, $0.040/task
]


def _get_router():
    global _registry, _router
    if _router is not None:
        return _registry, _router
    try:
        from v10.providers.base import LLMRegistry, PrivacyMode
        from v10.router.model_router import ModelRouter
        _registry = LLMRegistry()
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
        logger.warning(f"V10 routing unavailable: {e}")
        return None, None


def _select_chain(user_msg: str, model: str = "auto") -> list:
    """Select the model fallback chain based on task type."""
    if model != "auto":
        return [model]

    msg_lower = user_msg.lower()
    if any(w in msg_lower for w in ["build", "create", "make", "add", "entity", "crm", "app",
                                    "store", "shop", "dashboard", "blog", "inventory", "task",
                                    "project", "social", "note", "feedback", "contact", "order",
                                    "booking", "product", "page", "post", "workout"]):
        return BUILDER_MODELS
    elif any(w in msg_lower for w in ["code", "function", "api", "deploy", "python", "script",
                                      "backend", "endpoint", "debug", "refactor", "sql"]):
        return CODE_MODELS
    elif any(w in msg_lower for w in ["analyze", "reason", "think", "complex", "architect",
                                      "design", "plan", "strategy", "compare", "why", "how"]):
        return REASONING_MODELS
    else:
        return CHAT_MODELS


def _v10_route_and_chat_sync(messages: list, model: str = "auto", temperature: float = 0.7,
                              max_tokens: int = 4096, prefer_cloud: bool = False) -> Tuple[str, str, str]:
    registry, router = _get_router()
    if router is None:
        return None, None, None

    user_prompt = ""
    for m in reversed(messages):
        if m.get("role") == "user":
            user_prompt = m.get("content", "")
            break

    if model == "auto" and prefer_cloud and registry.can_use_cloud():
        # Use benchmark-driven model selection for builder/agent tasks
        model_chain = _select_chain(user_prompt, "auto")
        cloud_providers = registry.get_cloud_providers()

        for try_model in model_chain:
            # Try OpenRouter (our gateway to all cloud models)
            if "openrouter" in cloud_providers:
                provider = registry.get("openrouter")
                if provider:
                    try:
                        response = provider.chat(messages, model=try_model, temperature=temperature, max_tokens=max_tokens)
                        return response.content, "openrouter", try_model
                    except Exception as e:
                        logger.warning(f"prefer_cloud openrouter {try_model} failed: {e}")
                        continue

        # If OpenRouter failed, try other cloud providers
        for name in cloud_providers:
            if name == "openrouter":
                continue
            p = registry.get(name)
            if p:
                try:
                    response = p.chat(messages, temperature=temperature, max_tokens=max_tokens)
                    return response.content, name, response.model
                except Exception:
                    continue

    if model != "auto":
        try:
            if ":" in model and "/" not in model:
                provider = registry.get("ollama")
                if provider:
                    response = provider.chat(model, messages, temperature=temperature)
                    return response.content, "ollama", model
            else:
                provider = registry.get("openrouter")
                if provider:
                    response = provider.chat(messages, model=model, temperature=temperature, max_tokens=max_tokens)
                    return response.content, "openrouter", model
        except Exception as e:
            logger.warning(f"V10 direct model routing failed for {model}: {e}")

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
    Unified chat — V10 routing first, benchmark-driven fallback second.

    prefer_cloud=True uses benchmark-ranked models for tool-calling tasks.
    """
    try:
        result = await asyncio.to_thread(
            _v10_route_and_chat_sync, messages, model, temperature, max_tokens, prefer_cloud
        )
        if result[0]:
            registry, _ = _get_router()
            privacy = "HYBRID"
            if registry:
                privacy = registry.privacy_mode.value
            return {"content": result[0], "provider": result[1], "model": result[2], "privacy_mode": privacy}
    except Exception as e:
        logger.warning(f"V11 routing bridge error: {e}")

    # ── Fallback: inline routing (benchmark-driven) ──
    privacy_mode = os.environ.get("EVOLVIX_PRIVACY_MODE", "HYBRID").upper()

    if privacy_mode == "LOCAL":
        ollama_url = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
        local_model = os.environ.get("OLLAMA_DEFAULT_MODEL", "qwen2.5:7b")
        try:
            payload = json.dumps({"model": local_model, "messages": messages, "stream": False,
                                  "options": {"temperature": temperature}}).encode()
            req = urllib.request.Request(f"{ollama_url}/api/chat", data=payload, headers={"Content-Type": "application/json"})
            resp = urllib.request.urlopen(req, timeout=90)
            data = json.loads(resp.read())
            return {"content": data.get("message", {}).get("content", ""),
                    "provider": "ollama", "model": local_model, "privacy_mode": "LOCAL"}
        except Exception as e:
            return {"content": f"Error: LOCAL mode but Ollama unavailable: {e}",
                    "provider": "none", "model": "none", "privacy_mode": "LOCAL"}

    # HYBRID/CLOUD: benchmark-driven model selection
    user_msg = ""
    for m in reversed(messages):
        if m.get("role") == "user":
            user_msg = m.get("content", "")
            break

    model_chain = _select_chain(user_msg, model)

    or_key = os.environ.get("OPENROUTER_API_KEY", "")
    if or_key:
        for try_model in model_chain:
            try:
                or_payload = json.dumps({
                    "model": try_model, "messages": messages,
                    "stream": False, "temperature": temperature, "max_tokens": max_tokens
                }).encode()
                or_req = urllib.request.Request(
                    "https://openrouter.ai/api/v1/chat/completions",
                    data=or_payload,
                    headers={"Content-Type": "application/json", "Authorization": f"Bearer {or_key}",
                             "HTTP-Referer": "https://evolvixos.com", "X-Title": "EvolvixOS"}
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
            glm_payload = json.dumps({"model": "glm-4.5-flash", "messages": messages,
                "stream": False, "temperature": temperature, "max_tokens": max_tokens}).encode()
            glm_req = urllib.request.Request("https://api.z.ai/api/paas/v4/chat/completions",
                data=glm_payload, headers={"Content-Type": "application/json",
                "Authorization": f"Bearer {zai_key}", "Accept-Language": "en-US,en"})
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
