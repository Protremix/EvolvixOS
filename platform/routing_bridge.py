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



# ─── FreeToken Provider (edge-native MoE serving, activates with GPU) ───

FREETOKEN_URL = os.environ.get("FREETOKEN_URL", "http://127.0.0.1:8088")
FREETOKEN_AVAILABLE = False

def _check_freetoken():
    """Check if FreeToken engine is running locally (requires GPU)."""
    global FREETOKEN_AVAILABLE
    try:
        import urllib.request
        req = urllib.request.Request(FREETOKEN_URL + "/v1/models", method="GET")
        resp = urllib.request.urlopen(req, timeout=2)
        if resp.status == 200:
            FREETOKEN_AVAILABLE = True
            logger.info("FreeToken engine detected at " + FREETOKEN_URL)
            return True
    except Exception:
        pass
    FREETOKEN_AVAILABLE = False
    return False

def _freetoken_chat(messages, model="auto", temperature=0.7, max_tokens=4096):
    """Call FreeToken OpenAI-compatible API."""
    # Map model names to FreeToken-supported models
    model_map = {
        "auto": "deepseek-v4-flash",
        "deepseek/deepseek-v4-flash": "deepseek-v4-flash",
        "qwen/qwen3.8-27b": "qwen3.6-35b-a3b",
        "z-ai/glm-5": "glm-5.2",
        "code": "deepseek-v4-flash",
    }
    ft_model = model_map.get(model, "deepseek-v4-flash")
    
    payload = json.dumps({
        "model": ft_model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }).encode()
    
    req = urllib.request.Request(
        FREETOKEN_URL + "/v1/chat/completions",
        data=payload,
        method="POST",
        headers={"Content-Type": "application/json"}
    )
    
    resp = urllib.request.urlopen(req, timeout=120)
    data = json.loads(resp.read().decode())
    return {
        "content": data["choices"][0]["message"]["content"],
        "model": ft_model,
        "provider": "freetoken",
        "tokens": data.get("usage", {}).get("total_tokens", 0),
    }


# ─── NVIDIA build.nvidia.com API (free cloud inference) ───

NVIDIA_API_KEY = os.environ.get("NVIDIA_API_KEY", "")
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"

NVIDIA_MODELS = [
    "nvidia/nemotron-3.5-lightning-30b-a3b",
    "deepseek-ai/deepseek-v4-flash-0731",
    "moonshotai/kimi-k3",
    "meta/muse-glimmer-30b",
]

def _nvidia_chat(messages, model="auto", temperature=0.7, max_tokens=4096):
    if not NVIDIA_API_KEY:
        raise ValueError("NVIDIA_API_KEY not set")

    nvidia_model = model
    if model == "auto":
        nvidia_model = "nvidia/nemotron-3.5-lightning-30b-a3b"
    elif model.startswith("nvidia/") or model.startswith("deepseek") or model.startswith("moonshot") or model.startswith("meta/"):
        nvidia_model = model
    elif "deepseek" in model:
        nvidia_model = "deepseek-ai/deepseek-v4-flash-0731"
    elif "qwen" in model:
        nvidia_model = "nvidia/nemotron-3.5-lightning-30b-a3b"
    elif "code" in model:
        nvidia_model = "deepseek-ai/deepseek-v4-flash-0731"

    payload = json.dumps({
        "model": nvidia_model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }).encode()

    req = urllib.request.Request(
        NVIDIA_BASE_URL + "/chat/completions",
        data=payload,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + NVIDIA_API_KEY,
            "Accept": "application/json",
        }
    )

    resp = urllib.request.urlopen(req, timeout=30)
    data = json.loads(resp.read().decode())
    raw_content = data["choices"][0]["message"]["content"]

    # Strip thinking/reasoning tokens
    import re as _re
    raw_content = _re.sub(r"\boxed.*?\boxed", "", raw_content, flags=_re.DOTALL).strip()

    return {
        "content": raw_content,
        "model": nvidia_model,
        "provider": "nvidia",
        "tokens": data.get("usage", {}).get("total_tokens", 0),
    }



# ─── Groq API (free tier, fast inference) ───

GROQ_API_KEY_ENV = os.environ.get("GROQ_API_KEY", "")
GROQ_BASE_URL = "https://api.groq.com/openai/v1"

GROQ_MODELS = [
    "openai/gpt-oss-20b",
    "qwen/qwen3.6-27b",
    "groq/compound-mini",
]

def _groq_chat(messages, model="auto", temperature=0.7, max_tokens=4096):
    """Call Groq API (free tier)."""
    if not GROQ_API_KEY_ENV:
        raise ValueError("GROQ_API_KEY not set")
    
    groq_model = model
    if model == "auto":
        groq_model = "openai/gpt-oss-20b"
    elif "deepseek" in model:
        groq_model = "openai/gpt-oss-20b"
    elif "qwen" in model:
        groq_model = "qwen/qwen3.6-27b"
    
    payload = json.dumps({
        "model": groq_model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }).encode()
    
    req = urllib.request.Request(
        GROQ_BASE_URL + "/chat/completions",
        data=payload,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + GROQ_API_KEY_ENV,
            "User-Agent": "EvolvixOS/1.0",
        }
    )
    
    resp = urllib.request.urlopen(req, timeout=120)
    data = json.loads(resp.read().decode())
    return {
        "content": data["choices"][0]["message"]["content"],
        "model": groq_model,
        "provider": "groq",
        "tokens": data.get("usage", {}).get("total_tokens", 0),
    }

def _openrouter_chat(messages, model="auto", temperature=0.7, max_tokens=4096):
    """Call OpenRouter API directly — uses openrouter/auto for smart model selection."""
    or_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not or_key:
        raise ValueError("OPENROUTER_API_KEY not set")

    # Primary: openrouter/auto (smart routing — OpenRouter picks best model per task)
    # Fallback: specific models if auto fails
    if model == "auto":
        model_chain = [
            "openrouter/auto",                    # smart auto-routing (primary)
            "deepseek/deepseek-v4-flash-0731",     # fast, cheap, 1.3M ctx
            "qwen/qwen3.8-27b",                   # 1M ctx, strong all-rounder
            "openai/gpt-4o-mini",                 # reliable fallback
        ]
    else:
        model_chain = [model, "openrouter/auto"]

    for try_model in model_chain:
        try:
            payload = json.dumps({
                "model": try_model,
                "messages": messages,
                "stream": False,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }).encode()
            req = urllib.request.Request(
                "https://openrouter.ai/api/v1/chat/completions",
                data=payload,
                method="POST",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": "Bearer " + or_key,
                    "HTTP-Referer": "https://evolvixos.com",
                    "X-Title": "EvolvixOS",
                }
            )
            resp = urllib.request.urlopen(req, timeout=45)
            data = json.loads(resp.read().decode())
            resp.close()
            msg = data.get("choices", [{}])[0].get("message", {})
            content = msg.get("content") or msg.get("reasoning", "") or ""
            if content and len(content) > 5:
                return {
                    "content": content,
                    "model": data.get("model", try_model),
                    "provider": "openrouter",
                    "tokens": data.get("usage", {}).get("total_tokens", 0),
                    "cost": data.get("usage", {}).get("cost", 0),
                }
        except Exception as e:
            logger.warning("OpenRouter " + try_model + " failed: " + str(e))
            continue

    raise ValueError("All OpenRouter models failed")





async def unified_chat(messages: list, model: str = "auto", temperature: float = 0.7,
                       max_tokens: int = 4096, prefer_cloud: bool = False) -> dict:
    """
    Unified chat — free providers first (zero paid tokens), V10 as fallback.

    Provider priority:
      1. FreeToken (local GPU MoE) — if available
      2. NVIDIA API (free cloud) — for cloud-preferred tasks
      3. Groq (free cloud) — fast fallback
      4. OpenRouter (openrouter/auto — smart model selection, paid)
      5. V10 ModelRouter (legacy fallback)
      6. Ollama (local CPU) — always available
    """
    privacy_mode = os.environ.get("EVOLVIX_PRIVACY_MODE", "HYBRID").upper()

    # ── 1. FreeToken (local GPU MoE serving) ──
    if _check_freetoken():
        try:
            return _freetoken_chat(messages, model, temperature, max_tokens)
        except Exception as e:
            logger.warning("FreeToken failed: " + str(e))

    # ── 2. NVIDIA API (free cloud inference) ──
    if prefer_cloud or privacy_mode != "LOCAL":
        if NVIDIA_API_KEY:
            try:
                return _nvidia_chat(messages, model, temperature, max_tokens)
            except Exception as e:
                logger.warning("NVIDIA API failed: " + str(e))

    # ── 3. Groq (free cloud, fast) ──
    if prefer_cloud or privacy_mode != "LOCAL":
        if GROQ_API_KEY_ENV:
            try:
                return _groq_chat(messages, model, temperature, max_tokens)
            except Exception as e:
                logger.warning("Groq failed: " + str(e))

    # ── 4. OpenRouter (paid, high quality) ──
    if prefer_cloud or privacy_mode != "LOCAL":
        or_key = os.environ.get("OPENROUTER_API_KEY", "")
        if or_key:
            try:
                return _openrouter_chat(messages, model, temperature, max_tokens)
            except Exception as e:
                logger.warning("OpenRouter failed: " + str(e))

    # ── 5. V10 ModelRouter (legacy fallback) ──
    try:
        result = await asyncio.wait_for(
            asyncio.to_thread(_v10_route_and_chat_sync, messages, model, temperature, max_tokens, prefer_cloud),
            timeout=30
        )
        if result[0]:
            registry, _ = _get_router()
            privacy = "HYBRID"
            if registry:
                privacy = registry.privacy_mode.value
            return {"content": result[0], "provider": result[1], "model": result[2], "privacy_mode": privacy}
    except Exception as e:
        logger.warning(f"V10 routing bridge error: {e}")

    # ── 6. Ollama (local CPU, always available) ──
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
                or_resp = urllib.request.urlopen(or_req, timeout=30)
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
            glm_resp = urllib.request.urlopen(glm_req, timeout=30)
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
