"""
NVIDIA NIM Provider — Full model catalog integration via build.nvidia.com
Uses OpenAI-compatible API at integrate.api.nvidia.com for LLM tasks
Uses ai.api.nvidia.com for image/video/speech generation

Models registered: 24 across 6 categories
- Reasoning/Agent: Nemotron 3 Ultra 550B, Nemotron 3 Super 120B, Nemotron 3.5 Lightning 30B
- Coding: DeepSeek V4 Pro, DeepSeek V4 Flash, Poolside Laguna XS
- Multimodal/Vision: Llama 3.2 90B Vision, Muse Glimmer 30B, Nemotron 3 Nano Omni, Kimi K3
- Embedding: Nemotron 3 Embed 1B
- Safety: Nemotron 3.5 Content Safety
- Translation: Riva Translate v2 (37 languages)
"""
from __future__ import annotations
import json
import os
import time
import base64
import urllib.request
import urllib.error
import logging
from v10.providers.base import LLMProvider, LLMResponse

logger = logging.getLogger("evolvixos.v10.providers.nvidia")

# API endpoints
NVIDIA_CHAT_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
NVIDIA_EMBED_URL = "https://integrate.api.nvidia.com/v1/embeddings"
NVIDIA_IMAGE_URL = "https://ai.api.nvidia.com/v1/genai/black-forest-labs/flux.1-dev"
NVIDIA_VIDEO_URL = "https://ai.api.nvidia.com/v1/genai/wan-ai/wan2.2"
NVIDIA_TTS_URL = "https://ai.api.nvidia.com/v1/genai/nvidia/magpie-tts-multilingual"


class NvidiaProvider(LLMProvider):
    name = "nvidia"
    is_local = False
    supports_tools = True
    supports_vision = True
    supports_streaming = False
    max_context = 1_048_576  # 1M context for Nemotron 3 Ultra
    latency_tier = "medium"

    # ─── LLM Models by task ───
    models_by_task = {
        # Primary reasoning/agent
        "chat": "nvidia/nemotron-3-ultra-550b-a55b",
        "reasoning": "nvidia/nemotron-3-ultra-550b-a55b",
        "agent": "nvidia/nemotron-3-ultra-550b-a55b",
        "complex": "nvidia/nemotron-3-ultra-550b-a55b",

        # Fast/efficient
        "simple": "nvidia/nemotron-3.5-lightning-30b-a3b",
        "fast": "nvidia/nemotron-3.5-lightning-30b-a3b",
        "medium": "nvidia/nemotron-3-super-120b-a12b",

        # Coding
        "code": "deepseek-ai/deepseek-v4-pro-0813",
        "code_fast": "deepseek-ai/deepseek-v4-flash-0731",
        "code_agent": "poolside/laguna-xs-2.1",

        # Vision/Multimodal
        "vision": "meta/llama-3.2-90b-vision-instruct",
        "vision_fast": "meta/llama-3.2-11b-vision-instruct",
        "multimodal": "meta/muse-glimmer-30b",
        "omni": "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",

        # Long-context multimodal
        "long_context": "moonshotai/kimi-k3",
        "long_code": "moonshotai/kimi-k3",

        # Safety
        "safety": "nvidia/nemotron-3.5-content-safety",

        # Embedding
        "embed": "nvidia/nemotron-3-embed-1b",

        # Translation
        "translate": "nvidia/riva-translate-4b-instruct-v2",

        # Creative
        "creative": "writer/palmyra-creative-122b",

        # MiniMax multimodal
        "multimodal_alt": "minimaxai/minimax-m3",
    }

    default_model = "nvidia/nemotron-3-ultra-550b-a55b"
    fast_model = "nvidia/nemotron-3.5-lightning-30b-a3b"
    code_model = "deepseek-ai/deepseek-v4-pro-0813"
    code_fast_model = "deepseek-ai/deepseek-v4-flash-0731"
    vision_model = "meta/llama-3.2-90b-vision-instruct"
    multimodal_model = "meta/muse-glimmer-30b"
    omni_model = "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning"
    long_context_model = "moonshotai/kimi-k3"
    translate_model = "nvidia/riva-translate-4b-instruct-v2"
    embed_model = "nvidia/nemotron-3-embed-1b"
    safety_model = "nvidia/nemotron-3.5-content-safety"
    creative_model = "writer/palmyra-creative-122b"

    def __init__(self):
        self._api_key = os.environ.get("NVIDIA_API_KEY", "")

    def is_available(self) -> bool:
        return bool(self._api_key)

    def chat(self, messages, tools=None, stream=False, temperature=0.7, max_tokens=8192, model=None) -> LLMResponse:
        if not self._api_key:
            raise RuntimeError("NVIDIA API key not configured. Set NVIDIA_API_KEY env var.")

        use_model = model or self.default_model

        body_dict = {
            "model": use_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
            "chat_template_kwargs": {"enable_thinking": False, "force_nonempty_content": True},
        }
        if tools:
            body_dict["tools"] = tools
            body_dict["tool_choice"] = "auto"

        body = json.dumps(body_dict).encode()

        req = urllib.request.Request(NVIDIA_CHAT_URL, data=body, headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._api_key}",
            "Accept": "application/json",
        })

        start = time.monotonic()
        try:
            resp = urllib.request.urlopen(req, timeout=180)
            result = json.loads(resp.read())
            resp.close()
        except urllib.error.HTTPError as e:
            err_body = e.read().decode() if e.fp else ""
            logger.error(f"NVIDIA API error {e.code}: {err_body[:500]}")
            raise RuntimeError(f"NVIDIA API error {e.code}: {err_body[:200]}")
        except Exception as e:
            logger.error(f"NVIDIA request failed: {e}")
            raise

        latency = (time.monotonic() - start) * 1000
        msg = result.get("choices", [{}])[0].get("message", {})

        return LLMResponse(
            content=msg.get("content", ""),
            provider=self.name,
            model=use_model,
            tool_calls=msg.get("tool_calls", []),
            usage=result.get("usage", {}),
            latency_ms=latency,
            raw=result
        )

    def embed(self, texts, input_type="query") -> list:
        """Generate embeddings using Nemotron 3 Embed 1B"""
        if not self._api_key:
            raise RuntimeError("NVIDIA API key not configured.")

        body = json.dumps({
            "model": self.embed_model,
            "input": texts if isinstance(texts, list) else [texts],
            "input_type": input_type,
        }).encode()

        req = urllib.request.Request(NVIDIA_EMBED_URL, data=body, headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._api_key}",
        })

        try:
            resp = urllib.request.urlopen(req, timeout=60)
            result = json.loads(resp.read())
            return [d["embedding"] for d in result.get("data", [])]
        except Exception as e:
            logger.error(f"NVIDIA embed failed: {e}")
            raise

    def translate(self, text, source_lang="en", target_lang="es") -> str:
        """Translate text using Riva Translate v2 (37 languages)"""
        prompt = f"Translate the following text from {source_lang} to {target_lang}. Provide only the translation:\n\n{text}"
        messages = [{"role": "user", "content": prompt}]

        body = json.dumps({
            "model": self.translate_model,
            "messages": messages,
            "max_tokens": 2048,
            "stream": False,
        }).encode()

        req = urllib.request.Request(NVIDIA_CHAT_URL, data=body, headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._api_key}",
        })

        try:
            resp = urllib.request.urlopen(req, timeout=120)
            result = json.loads(resp.read())
            return result.get("choices", [{}])[0].get("message", {}).get("content", "")
        except Exception as e:
            logger.error(f"NVIDIA translate failed: {e}")
            raise

    def generate_image(self, prompt, seed=42, width=1024, height=1024, cfg_scale=7.5) -> str:
        """Generate image using FLUX.1-dev. Returns image URL."""
        if not self._api_key:
            raise RuntimeError("NVIDIA API key not configured.")

        body = json.dumps({
            "prompt": prompt,
            "seed": seed,
            "cfg_scale": cfg_scale,
            "width": width,
            "height": height,
        }).encode()

        req = urllib.request.Request(NVIDIA_IMAGE_URL, data=body, headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._api_key}",
            "Accept": "application/json",
        })

        try:
            resp = urllib.request.urlopen(req, timeout=120)
            result = json.loads(resp.read())
            artifacts = result.get("artifacts", [])
            if artifacts:
                return artifacts[0].get("url", "")
            raise RuntimeError("No image generated")
        except Exception as e:
            logger.error(f"NVIDIA image gen failed: {e}")
            raise

    def generate_video(self, prompt, image_url=None, seed=42, num_frames=81, fps=24) -> dict:
        """Generate video using Wan2.2 T2V or I2V. Returns video URL + metadata."""
        if not self._api_key:
            raise RuntimeError("NVIDIA API key not configured.")

        body_dict = {
            "prompt": prompt,
            "seed": seed,
            "cfg_scale": 7.5,
            "width": 1024,
            "height": 576,
            "num_frames": num_frames,
            "fps": fps,
        }
        if image_url:
            body_dict["image_url"] = image_url

        body = json.dumps(body_dict).encode()

        req = urllib.request.Request(NVIDIA_VIDEO_URL, data=body, headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._api_key}",
            "Accept": "application/json",
        })

        try:
            resp = urllib.request.urlopen(req, timeout=300)
            result = json.loads(resp.read())
            artifacts = result.get("artifacts", [])
            if artifacts:
                return {
                    "url": artifacts[0].get("url", ""),
                    "duration": num_frames / fps,
                    "model": "wan2.2",
                    "type": "i2v" if image_url else "t2v",
                }
            raise RuntimeError("No video generated")
        except Exception as e:
            logger.error(f"NVIDIA video gen failed: {e}")
            raise

    def text_to_speech(self, text, language="en", voice="default") -> str:
        """Generate speech using NVIDIA Magpie TTS Multilingual. Returns audio URL."""
        if not self._api_key:
            raise RuntimeError("NVIDIA API key not configured.")

        body = json.dumps({
            "text": text,
            "language": language,
            "voice": voice,
        }).encode()

        req = urllib.request.Request(NVIDIA_TTS_URL, data=body, headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._api_key}",
            "Accept": "application/json",
        })

        try:
            resp = urllib.request.urlopen(req, timeout=120)
            result = json.loads(resp.read())
            return result.get("audio_url", result.get("url", ""))
        except Exception as e:
            logger.error(f"NVIDIA TTS failed: {e}")
            raise

    def get_available_models(self) -> dict:
        """Return all registered models grouped by category"""
        return {
            "reasoning_agent": [
                {"id": "nvidia/nemotron-3-ultra-550b-a55b", "name": "Nemotron 3 Ultra 550B", "context": "1M", "active_params": "55B"},
                {"id": "nvidia/nemotron-3-super-120b-a12b", "name": "Nemotron 3 Super 120B", "context": "256K", "active_params": "12B"},
                {"id": "nvidia/nemotron-3.5-lightning-30b-a3b", "name": "Nemotron 3.5 Lightning 30B", "context": "256K", "active_params": "3B"},
            ],
            "coding": [
                {"id": "deepseek-ai/deepseek-v4-pro-0813", "name": "DeepSeek V4 Pro", "context": "1M", "active_params": "MoE"},
                {"id": "deepseek-ai/deepseek-v4-flash-0731", "name": "DeepSeek V4 Flash", "context": "1M", "active_params": "13B active"},
                {"id": "poolside/laguna-xs-2.1", "name": "Poolside Laguna XS", "context": "128K", "active_params": "33B MoE"},
            ],
            "multimodal_vision": [
                {"id": "meta/llama-3.2-90b-vision-instruct", "name": "Llama 3.2 90B Vision", "context": "128K"},
                {"id": "meta/llama-3.2-11b-vision-instruct", "name": "Llama 3.2 11B Vision", "context": "128K"},
                {"id": "meta/muse-glimmer-30b", "name": "Muse Glimmer 30B", "context": "256K"},
                {"id": "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning", "name": "Nemotron 3 Nano Omni 30B", "context": "128K"},
                {"id": "moonshotai/kimi-k3", "name": "Kimi K3 2.8T", "context": "1M"},
                {"id": "minimaxai/minimax-m3", "name": "MiniMax M3", "context": "256K"},
            ],
            "embedding": [
                {"id": "nvidia/nemotron-3-embed-1b", "name": "Nemotron 3 Embed 1B", "dims": 2048},
            ],
            "safety": [
                {"id": "nvidia/nemotron-3.5-content-safety", "name": "Nemotron 3.5 Content Safety"},
            ],
            "translation": [
                {"id": "nvidia/riva-translate-4b-instruct-v2", "name": "Riva Translate v2", "languages": 37},
            ],
            "creative": [
                {"id": "writer/palmyra-creative-122b", "name": "Palmyra Creative 122B"},
            ],
            "image_generation": [
                {"id": "black-forest-labs/flux.1-dev", "name": "FLUX.1-dev", "max": "2048x2048"},
            ],
            "video_generation": [
                {"id": "wan-ai/wan2.2", "name": "Wan2.2 T2V/I2V", "max": "1024x576"},
            ],
            "speech": [
                {"id": "nvidia/magpie-tts-multilingual", "name": "Magpie TTS Multilingual", "languages": 25},
                {"id": "nvidia/magpie-tts-zeroshot", "name": "Magpie TTS Zero-shot"},
                {"id": "nvidia/nemotron-voicechat", "name": "Nemotron Voicechat", "type": "voice-to-voice"},
            ],
        }
