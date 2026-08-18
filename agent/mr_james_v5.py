#!/usr/bin/env python3
"""
Mr James v5.0 — Universal AI Agent with Auto-Engine Selection
=============================================================
Automatically detects user intent and routes to the best AI engine:
- Text reasoning → OmniRoute (340+ models) / Ollama (local)
- Video generation → ComfyUI (Wan2.1/2.2, LTX, HunyuanVideo, etc.)
- Image generation → ComfyUI (FLUX, SDXL, SD, Qwen-Image)
- Audio/TTS → Piper (CPU) / CosyVoice / XTTS (GPU)
- Animation → ComfyUI (LivePortrait, SadTalker, AnimateDiff, etc.)
- Code/Build → Direct execution (Python, Bash, Docker)
- Crypto → CoinGecko / DeFiLlama APIs
"""

import json
import os
import re
import subprocess
import urllib.request
import urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler

# ═══════════════════════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════════════════════

OMNIROUTE_URL = "http://localhost:20128"
OLLAMA_URL = "http://localhost:11434"
COMFYUI_URL = "http://localhost:8188"
MODEL_API_URL = "http://localhost:5010"
KIMI_API_KEY = os.environ.get("KIMI_API_KEY", "")
KIMI_URL = "https://api.moonshot.ai/v1/chat/completions"

# Load model registry
try:
    with open("/opt/evolvixos/models/registry/manifest.json") as f:
        MANIFEST = json.load(f)
except:
    MANIFEST = {"models": {}}

# Load tool registries (integrated from GitHub Discovery Engine)
TOOL_REGISTRIES = {}
for reg_name, reg_path in [
    ("ai_tools", "/opt/evolvixos/models/free_ai_tools_registry.json"),
    ("freellm", "/opt/evolvixos/models/freellm_registry.json"),
    ("image_gen", "/opt/evolvixos/models/image_gen_api.json"),
    ("apis", "/opt/evolvixos/models/api_directory.json"),
    ("learn", "/opt/evolvixos/models/learning_hub.json"),
]:
    try:
        with open(reg_path) as f:
            TOOL_REGISTRIES[reg_name] = json.load(f)
    except:
        TOOL_REGISTRIES[reg_name] = {}

# Free LLM API providers for routing (loaded from registry)
FREE_LLM_PROVIDERS = []
if TOOL_REGISTRIES.get("freellm", {}).get("providers"):
    for p in TOOL_REGISTRIES["freellm"]["providers"]:
        if p.get("base_url") and p.get("tier") == "permanent_free":
            FREE_LLM_PROVIDERS.append({
                "name": p["name"],
                "base_url": p["base_url"],
                "key_url": p.get("key_url", ""),
                "models": p.get("models", []),
                "free_models": p.get("free_models", 0),
                "credit_card": p.get("credit_card", "No"),
                "modalities": p.get("modalities", [])
            })

# ═══════════════════════════════════════════════════════════════════════════════
# Auto-Engine Selection — The Brain
# ═══════════════════════════════════════════════════════════════════════════════

class EngineSelector:
    """Analyzes user prompt and picks the best AI engine for the task."""

    @staticmethod
    def detect(prompt):
        """Returns dict with type, engine, reason, and routing info."""
        p = prompt.lower().strip()

        # --- VISION / IMAGE UNDERSTANDING ---
        if re.search(r'\b(describe.+image|what.+in.+image|analyze.+image|what.+in.+photo|look at|see in|vision|identify.+image|describe.+photo)\b', p):
            if re.search(r'\b(light|small|fast|quick)\b', p):
                return {"type": "vision", "subtype": "lightweight",
                    "engine": "Moondream", "engine_id": "moondream",
                    "reason": "Lightweight vision task -> Moondream (small, fast VLM)",
                    "route": "ollama"}
            if re.search(r'\b(detect|segment|mask|bounding box)\b', p):
                return {"type": "vision", "subtype": "detection",
                    "engine": "Florence-2", "engine_id": "florence-2",
                    "reason": "Detection task -> Florence-2 (best for object detection)",
                    "route": "comfyui", "vram": "8GB"}
            return {"type": "vision", "subtype": "general",
                "engine": "Qwen2-VL", "engine_id": "qwen2-vl",
                "reason": "Vision/multimodal -> Qwen2-VL (best open-source VLM)",
                "route": "comfyui", "vram": "16GB"}

        # --- 3D GENERATION ---
        if re.search(r'\b(3d|3.d model|mesh|point cloud|3d asset|three.?d|create.+model)\b', p) and not re.search(r'\b(llm|language|text|chat|reason)\b', p):
            if re.search(r'\b(fast|quick|real.?time)\b', p):
                return {"type": "3d", "subtype": "fast",
                    "engine": "TripoSR", "engine_id": "triposr",
                    "reason": "Fast 3D -> TripoSR (fastest single-image to 3D)",
                    "route": "comfyui", "vram": "8GB"}
            if re.search(r'\b(high.?quality|detailed|best|professional)\b', p):
                return {"type": "3d", "subtype": "quality",
                    "engine": "Hunyuan3D-2.1", "engine_id": "hunyuan3d-2.1",
                    "reason": "High quality 3D -> Hunyuan3D 2.1 (best quality 3D generation)",
                    "route": "comfyui", "vram": "12GB"}
            return {"type": "3d", "subtype": "general",
                "engine": "TRELLIS", "engine_id": "trellis",
                "reason": "3D generation -> TRELLIS (versatile, good balance)",
                "route": "comfyui", "vram": "10GB"}

        # --- RAG / KNOWLEDGE BASE ---
        if re.search(r'\b(rag|knowledge base|vector db|embeddings|search.+documents|qa.+documents|retrieve)\b', p):
            return {"type": "rag", "subtype": "knowledge",
                "engine": "LangChain + Chroma", "engine_id": "langchain",
                "reason": "RAG/knowledge -> LangChain + Chroma (best open-source RAG stack)",
                "route": "tools"}

        # --- VIDEO EDITING ---
        if re.search(r'\b(edit.+video|cut|merge.+video|trim|concat|transcode|convert.+format|compress.+video)\b', p):
            if re.search(r'\b(complex|professional|advanced|cinematic)\b', p):
                return {"type": "video_edit", "subtype": "pro",
                    "engine": "FFmpeg + Blender", "engine_id": "ffmpeg",
                    "reason": "Pro video editing -> FFmpeg + Blender pipeline",
                    "route": "tools"}
            return {"type": "video_edit", "subtype": "basic",
                "engine": "FFmpeg", "engine_id": "ffmpeg",
                "reason": "Video editing -> FFmpeg (handles all video operations)",
                "route": "tools"}

        # --- AI CODING ---
        if re.search(r'\b(code|build|deploy|server|docker|api|function|script|program|app|python|javascript|bash|sql|refactor|debug|fix.+code)\b', p):
            if re.search(r'\b(complex|architecture|design|refactor|optimi[sz]e)\b', p):
                return {"type": "code", "subtype": "complex",
                    "engine": "Kimi-K3", "engine_id": "kimi-k3",
                    "reason": "Complex code -> Kimi K3 (GPT/Claude-level reasoning)",
                    "route": "kimi"}
            if re.search(r'\b(autonomous|hands.?free|agent)\b', p):
                return {"type": "code", "subtype": "autonomous",
                    "engine": "OpenHands", "engine_id": "openhands",
                    "reason": "Autonomous coding -> OpenHands (self-correcting code agent)",
                    "route": "tools"}
            return {"type": "code", "subtype": "simple",
                "engine": "Qwen2.5-14B", "engine_id": "qwen2.5:14b",
                "reason": "Code task -> Qwen 2.5 14B (local, fast, zero-cost)",
                "route": "ollama"}

        # --- VIDEO GENERATION ---
        if re.search(r'\b(video|movie|film|clip|cinema|scene|render.+video)\b', p) and not re.search(r'\b(talking|head|portrait|face|lip|dance|body)\b', p):
            if re.search(r'\b(from image|image to|using image|based on.+image)\b', p):
                return {
                    "type": "video", "subtype": "i2v",
                    "engine": "Wan2.2-I2V-A14B", "engine_id": "wan2.2-i2v-a14b",
                    "reason": "Image-to-Video detected → Wan2.2 I2V (best quality)",
                    "route": "comfyui", "vram": "20GB"
                }
            if re.search(r'\b(fast|quick|real.?time|instant|speed|lite)\b', p):
                return {
                    "type": "video", "subtype": "t2v",
                    "engine": "LTX-Video", "engine_id": "ltx-video",
                    "reason": "Speed requested → LTX-Video (real-time generation)",
                    "route": "comfyui", "vram": "8GB"
                }
            if re.search(r'\b(high.?quality|4k|8k|cinematic|detailed|professional|best)\b', p):
                return {
                    "type": "video", "subtype": "t2v",
                    "engine": "Wan2.2-T2V-A14B", "engine_id": "wan2.2-t2v-a14b",
                    "reason": "High quality requested → Wan2.2 T2V A14B (newest, best)",
                    "route": "comfyui", "vram": "20GB"
                }
            if re.search(r'\b(short|gif|loop|simple|basic)\b', p):
                return {
                    "type": "video", "subtype": "t2v",
                    "engine": "Wan2.1-T2V-1.3B", "engine_id": "wan2.1-t2v-1.3b",
                    "reason": "Light task → Wan2.1 1.3B (fast & efficient)",
                    "route": "comfyui", "vram": "8GB"
                }
            # Default video
            return {
                "type": "video", "subtype": "t2v",
                "engine": "Wan2.1-T2V-1.3B", "engine_id": "wan2.1-t2v-1.3b",
                "reason": "Text-to-Video → Wan2.1 T2V 1.3B (balanced quality & speed)",
                "route": "comfyui", "vram": "8GB"
            }

        # --- TALKING HEAD / PORTRAIT ---
        if re.search(r'\b(talking|head|portrait|face|lip.?sync|speak|narrat.+face|say.+words|mouth)\b', p):
            if re.search(r'\b(high.?quality|realistic|detailed|professional)\b', p):
                return {
                    "type": "animation", "subtype": "talking_head",
                    "engine": "Hallo2", "engine_id": "hallo2",
                    "reason": "High quality talking head → Hallo2 (best quality portrait animation)",
                    "route": "comfyui", "vram": "12GB"
                }
            if re.search(r'\b(full.?body|body|gesture|hands)\b', p):
                return {
                    "type": "animation", "subtype": "full_body",
                    "engine": "OmniHuman", "engine_id": "omnihuman",
                    "reason": "Full body animation → OmniHuman (ByteDance, full body)",
                    "route": "comfyui", "vram": "16GB"
                }
            return {
                "type": "animation", "subtype": "talking_head",
                "engine": "LivePortrait", "engine_id": "liveportrait",
                "reason": "Portrait animation → LivePortrait (fastest, best for talking heads)",
                "route": "comfyui", "vram": "6GB"
            }

        # --- DANCE / BODY ANIMATION ---
        if re.search(r'\b(dance|dancing|body movement|gesture animat|motion.+transfer|pose.+animat)\b', p):
            return {
                "type": "animation", "subtype": "dance",
                "engine": "Animate-Anyone", "engine_id": "animate-anyone",
                "reason": "Body/dance animation → Animate Anyone (best for dance & movement)",
                "route": "comfyui", "vram": "10GB"
            }

        # --- IMAGE GENERATION ---
        if re.search(r'\b(image|picture|photo|draw|paint|art|illustration|generate.+image|create.+image)\b', p) and not re.search(r'\b(video|movie|film)\b', p):
            if re.search(r'\b(text|words|letters|sign|banner|poster|typography|caption)\b', p):
                return {
                    "type": "image", "subtype": "t2i",
                    "engine": "FLUX", "engine_id": "flux",
                    "reason": "Text in image detected → FLUX (best at rendering text in images)",
                    "route": "comfyui", "vram": "20GB"
                }
            if re.search(r'\b(my face|same person|identity|consistent person|same character)\b', p):
                return {
                    "type": "image", "subtype": "t2i_identity",
                    "engine": "SDXL + InstantID", "engine_id": "sdxl",
                    "reason": "Identity preservation → SDXL + InstantID",
                    "route": "comfyui", "vram": "10GB"
                }
            if re.search(r'\b(best|highest|quality|detailed|professional|4k|8k|hdr|photoreal)\b', p):
                return {
                    "type": "image", "subtype": "t2i",
                    "engine": "FLUX", "engine_id": "flux",
                    "reason": "Best quality → FLUX (12B model, top-tier)",
                    "route": "comfyui", "vram": "20GB"
                }
            if re.search(r'\b(fast|quick|simple|basic|draft)\b', p):
                return {
                    "type": "image", "subtype": "t2i",
                    "engine": "Stable-Diffusion", "engine_id": "stable-diffusion",
                    "reason": "Fast generation → Stable Diffusion 1.5 (lightweight, 4GB VRAM)",
                    "route": "comfyui", "vram": "4GB"
                }
            # Default image
            return {
                "type": "image", "subtype": "t2i",
                "engine": "SDXL", "engine_id": "sdxl",
                "reason": "Standard image generation → SDXL (fast & detailed, good balance)",
                "route": "comfyui", "vram": "10GB"
            }

        # --- IMAGE CONTROL ---
        if re.search(r'\b(control|pose|style transfer|ip.adapter|openpose|transform.+image)\b', p):
            if re.search(r'\b(pose|body position|skeleton)\b', p):
                return {
                    "type": "image_control", "subtype": "pose",
                    "engine": "ControlNet-OpenPose", "engine_id": "openpose",
                    "reason": "Pose control → ControlNet OpenPose",
                    "route": "comfyui", "vram": "4GB"
                }
            if re.search(r'\b(style|transfer.+style|reference.+style)\b', p):
                return {
                    "type": "image_control", "subtype": "style",
                    "engine": "IP-Adapter", "engine_id": "ip-adapter",
                    "reason": "Style transfer → IP-Adapter",
                    "route": "comfyui", "vram": "4GB"
                }
            return {
                "type": "image_control", "subtype": "control",
                "engine": "ControlNet", "engine_id": "controlnet",
                "reason": "Image control → ControlNet (general)",
                "route": "comfyui", "vram": "4GB"
            }

        # --- VOICE / TTS ---
        if re.search(r'\b(voice|speech|narration|narrate|read.+aloud|say.+text|text.?to.?speech|tts|read.+text)\b', p):
            if re.search(r'\b(clone|my voice|copy voice|same voice|replicate voice)\b', p):
                return {
                    "type": "audio", "subtype": "tts_clone",
                    "engine": "CosyVoice", "engine_id": "cosyvoice",
                    "reason": "Voice cloning → CosyVoice (best for voice cloning)",
                    "route": "audio", "vram": "6GB"
                }
            if re.search(r'\b(french|spanish|german|chinese|japanese|korean|arabic|hindi|portuguese|multilingual)\b', p):
                return {
                    "type": "audio", "subtype": "tts_multi",
                    "engine": "XTTS-v2", "engine_id": "xtts",
                    "reason": "Multilingual → XTTS v2 (17+ languages)",
                    "route": "audio", "vram": "4GB"
                }
            if re.search(r'\b(natural|realistic|expressive|emotional)\b', p):
                return {
                    "type": "audio", "subtype": "tts",
                    "engine": "Fish-Speech", "engine_id": "fish-speech",
                    "reason": "Natural voice → Fish Speech (most natural TTS)",
                    "route": "audio", "vram": "4GB"
                }
            # Default TTS — Piper works on CPU right now
            return {
                "type": "audio", "subtype": "tts",
                "engine": "Piper", "engine_id": "piper",
                "reason": "Text-to-speech → Piper (fast, runs on CPU, available now)",
                "route": "audio", "vram": "0"
            }

        # --- SPEECH TO TEXT ---
        if re.search(r'\b(transcribe|speech.?to.?text|convert audio|subtitle|caption|whisper)\b', p):
            return {
                "type": "audio", "subtype": "stt",
                "engine": "Whisper", "engine_id": "whisper",
                "reason": "Speech-to-text → Whisper (OpenAI, best in class, runs on CPU)",
                "route": "audio", "vram": "0"
            }

        # --- MUSIC ---
        if re.search(r'\b(music|song|melody|beat|instrumental|soundtrack|background music|compose)\b', p):
            if re.search(r'\b(sound effect|sfx|ambient|noise|foley)\b', p):
                return {
                    "type": "audio", "subtype": "sfx",
                    "engine": "AudioCraft", "engine_id": "audiocraft",
                    "reason": "Sound effects → AudioCraft",
                    "route": "audio", "vram": "6GB"
                }
            return {
                "type": "audio", "subtype": "music",
                "engine": "MusicGen", "engine_id": "musicgen",
                "reason": "Music generation → MusicGen (full track generation)",
                "route": "audio", "vram": "6GB"
            }

        # --- CRYPTO ---
        if re.search(r'\b(crypto|bitcoin|ethereum|btc|eth|token|defi|blockchain|wallet|nft|trading|market.?cap|tvl)\b', p):
            return {
                "type": "crypto", "subtype": "analysis",
                "engine": "CoinGecko + DeFiLlama", "engine_id": "crypto",
                "reason": "Crypto analysis → CoinGecko market data + DeFiLlama TVL tracking",
                "route": "tools"
            }

        # --- CODE / BUILD ---
        if re.search(r'\b(code|build|deploy|server|docker|api|function|script|program|app|python|javascript|bash|sql)\b', p):
            if re.search(r'\b(complex|architecture|design|refactor|optimi[sz]e)\b', p):
                return {
                    "type": "code", "subtype": "complex",
                    "engine": "Kimi-K3", "engine_id": "kimi-k3",
                    "reason": "Complex code task → Kimi K3 (GPT/Claude-level reasoning)",
                    "route": "kimi"
                }
            return {
                "type": "code", "subtype": "simple",
                "engine": "Qwen2.5-14B", "engine_id": "qwen2.5:14b",
                "reason": "Code task → Qwen 2.5 14B (local, fast, zero-cost)",
                "route": "ollama"
            }

        # --- TOOL DISCOVERY ---
        if re.search(r'\b(find.+tool|search.+tool|what.+tools|available.+tool|list.+tool|recommend.+tool|best.+tool|ai tool|dev tool|coding tool|cli tool|ide|which.+api)\b', p):
            return {
                "type": "tool_discovery", "subtype": "search",
                "engine": "AI Tools Registry", "engine_id": "ai-tools",
                "reason": "Tool discovery query -> Search 85+ curated AI dev tools",
                "route": "tool_registry"
            }

        # --- API DISCOVERY ---
        if re.search(r'\b(find.+api|search.+api|what.+api|available.+api|list.+api|recommend.+api|best.+api|free.+api|api.+for|which.+service)\b', p):
            return {
                "type": "api_discovery", "subtype": "search",
                "engine": "API Directory", "engine_id": "api-directory",
                "reason": "API discovery query -> Search 35K+ indexed APIs",
                "route": "tool_registry"
            }

        # --- FREE LLM API ROUTING ---
        if re.search(r'\b(free.+llm|free.+api|free.+model|no.+cost.+api|zero.+cost|cheapest.+api|free.+gpt|free.+claude|free.+gemini)\b', p):
            return {
                "type": "freellm", "subtype": "routing",
                "engine": "Free LLM APIs", "engine_id": "freellm",
                "reason": "Free LLM request -> Route to 31+ free LLM API providers (442 models)",
                "route": "freellm"
            }

        # --- LEARNING / EDUCATION ---
        if re.search(r'\b(learn|tutorial|course|guide|how.+to.+build|teach|study|module|lesson|beginner)\b', p):
            return {
                "type": "learning", "subtype": "education",
                "engine": "Learning Hub", "engine_id": "learn",
                "reason": "Learning query -> Learning Hub with 15 modules on full-stack dev",
                "route": "tool_registry"
            }

        # --- IMAGE GEN API DEPLOYMENT ---
        if re.search(r'\b(deploy.+image|image.+api.+deploy|cloudflare.+worker|image.+gen.+setup|stable.+diffusion.+api)\b', p):
            return {
                "type": "image_gen_deploy", "subtype": "guide",
                "engine": "Image Gen API", "engine_id": "image-gen",
                "reason": "Image generation API deployment -> Free CF Worker (100K calls/day)",
                "route": "tool_registry"
            }

        # --- CHAT / REASONING (default) ---
        if re.search(r'\b(why|how|what|explain|analyze|compare|think|reason|summarize|write|essay|article)\b', p) or len(p) > 100:
            return {
                "type": "chat", "subtype": "reasoning",
                "engine": "auto", "engine_id": "auto",
                "reason": "Reasoning/question → OmniRoute auto-selects best available model (340+ models)",
                "route": "omniroute"
            }

        # Simple chat — use local Qwen for speed
        return {
            "type": "chat", "subtype": "simple",
            "engine": "Qwen2.5-14B", "engine_id": "qwen2.5:14b",
            "reason": "Simple chat → Qwen 2.5 14B (local, instant, free)",
            "route": "ollama"
        }


# ═══════════════════════════════════════════════════════════════════════════════
# Engine Routers — Route to the selected engine
# ═══════════════════════════════════════════════════════════════════════════════

class EngineRouter:
    """Routes requests to the selected AI engine."""

    @staticmethod
    def route(intent, prompt, context=None):
        route = intent["route"]

        if route == "omniroute":
            return EngineRouter._omniroute(prompt, context)
        elif route == "ollama":
            return EngineRouter._ollama(intent["engine_id"], prompt, context)
        elif route == "kimi":
            return EngineRouter._kimi(prompt, context)
        elif route == "comfyui":
            return EngineRouter._comfyui(intent, prompt)
        elif route == "audio":
            return EngineRouter._audio(intent, prompt)
        elif route == "tools":
            return EngineRouter._tools(intent, prompt)
        elif route == "tool_registry":
            return EngineRouter._tool_registry(intent, prompt)
        elif route == "freellm":
            return EngineRouter._freellm(intent, prompt)
        else:
            return EngineRouter._omniroute(prompt, context)

    @staticmethod
    def _omniroute(prompt, context=None):
        messages = context or [{"role": "user", "content": prompt}]
        body = json.dumps({"model": "auto", "messages": messages, "max_tokens": 2000}).encode()
        req = urllib.request.Request(
            f"{OMNIROUTE_URL}/v1/chat/completions",
            data=body,
            headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read())
                return {
                    "engine": "OmniRoute (auto)",
                    "model": data.get("model", "auto"),
                    "response": data.get("choices", [{}])[0].get("message", {}).get("content", ""),
                    "usage": data.get("usage", {}),
                    "status": "ok"
                }
        except Exception as e:
            # Fallback to Ollama
            return EngineRouter._ollama("qwen2.5:14b", prompt, context)

    @staticmethod
    def _ollama(model, prompt, context=None):
        messages = context or [{"role": "user", "content": prompt}]
        body = json.dumps({"model": model, "messages": messages, "stream": False}).encode()
        req = urllib.request.Request(
            f"{OLLAMA_URL}/api/chat",
            data=body,
            headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read())
                return {
                    "engine": f"Ollama ({model})",
                    "model": model,
                    "response": data.get("message", {}).get("content", ""),
                    "status": "ok"
                }
        except Exception as e:
            return {"engine": f"Ollama ({model})", "error": str(e), "status": "error"}

    @staticmethod
    def _kimi(prompt, context=None):
        if not KIMI_API_KEY:
            # Fallback to OmniRoute
            return EngineRouter._omniroute(prompt, context)

        messages = context or [{"role": "user", "content": prompt}]
        body = json.dumps({
            "model": "k2.7-code-highspeed",
            "messages": messages,
            "max_tokens": 4000,
            "temperature": 0.7
        }).encode()
        req = urllib.request.Request(
            KIMI_URL,
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {KIMI_API_KEY}"
            }
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read())
                return {
                    "engine": "Kimi K3",
                    "model": "k2.7-code-highspeed",
                    "response": data.get("choices", [{}])[0].get("message", {}).get("content", ""),
                    "status": "ok"
                }
        except Exception as e:
            return {"engine": "Kimi K3", "error": str(e), "status": "error"}

    @staticmethod
    def _comfyui(intent, prompt):
        # Build workflow based on type
        if intent["type"] == "video":
            workflow = EngineRouter._build_video_workflow(intent["engine_id"], prompt)
        elif intent["type"] == "image":
            workflow = EngineRouter._build_image_workflow(intent["engine_id"], prompt)
        else:
            workflow = EngineRouter._build_video_workflow(intent["engine_id"], prompt)

        body = json.dumps({"prompt": workflow}).encode()
        req = urllib.request.Request(
            f"{COMFYUI_URL}/prompt",
            data=body,
            headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=600) as resp:
                data = json.loads(resp.read())
                return {
                    "engine": intent["engine"],
                    "prompt_id": data.get("prompt_id", ""),
                    "status": "queued",
                    "message": f"Generation queued on {intent['engine']}. Check ComfyUI for progress."
                }
        except Exception as e:
            return {
                "engine": intent["engine"],
                "error": str(e),
                "status": "pending_gpu",
                "message": f"{intent['engine']} requires the GPU server (GEX44 pending delivery). Once provisioned, this will work automatically."
            }

    @staticmethod
    def _audio(intent, prompt):
        engine_id = intent["engine_id"]

        if engine_id == "whisper":
            # Whisper STT — runs on CPU
            return {
                "engine": "Whisper",
                "status": "ready",
                "message": "Whisper is ready for speech-to-text. Upload an audio file to transcribe."
            }

        if engine_id == "piper":
            # Piper TTS — runs on CPU
            # Extract the text to speak (after colon or quotes)
            text_match = re.search(r'(?:narrat(?:e|ion)[:\s]+|say[:\s]+|read[:\s]+|text[:\s]+|voice[:\s]+)["\']?(.+?)["\']?$', prompt, re.IGNORECASE)
            text = text_match.group(1) if text_match else prompt

            output_file = f"/tmp/tts_{os.getpid()}.wav"
            try:
                proc = subprocess.run(
                    ["piper", "-m", "/opt/piper-voices/en_US-amy-medium.onnx", "-f", output_file],
                    input=text.encode(), timeout=30, capture_output=True
                )
                if proc.returncode == 0:
                    return {"engine": "Piper", "status": "ok", "output": output_file, "text": text}
                else:
                    return {"engine": "Piper", "error": "Piper model not downloaded yet", "status": "error"}
            except Exception as e:
                return {"engine": "Piper", "error": str(e), "status": "error"}

        # Other audio engines need GPU
        return {
            "engine": intent["engine"],
            "status": "pending_gpu",
            "message": f"{intent['engine']} requires the GPU server. Pending GEX44 delivery."
        }

    @staticmethod
    def _tools(intent, prompt):
        return {
            "engine": intent["engine"],
            "status": "ready",
            "message": f"Route to tool engine for: {prompt[:100]}"
        }

    @staticmethod
    def _tool_registry(intent, prompt):
        """Search integrated tool registries for relevant tools/APIs."""
        reg_id = intent.get("engine_id", "ai-tools")
        p = prompt.lower()

        if reg_id == "ai-tools":
            reg = TOOL_REGISTRIES.get("ai_tools", {})
            tools = reg.get("tools", [])
            if not tools:
                return {"engine": "AI Tools Registry", "status": "error", "message": "Registry not loaded"}

            # Score tools by relevance
            scored = []
            for t in tools:
                score = 0
                searchable = (t.get("name", "") + " " + t.get("shortDescription", "") + " " +
                             " ".join(t.get("tags", [])) + " " + t.get("category", "") +
                             " " + " ".join(t.get("models", []))).lower()
                for word in p.split():
                    if len(word) > 3 and word in searchable:
                        score += 1
                if t.get("featured"):
                    score += 0.5
                if t.get("pricing", {}).get("type") in ("free", "open-source"):
                    score += 0.3
                scored.append((score, t))

            scored.sort(key=lambda x: -x[0])
            top = [t for s, t in scored if s > 0][:10]
            if not top:
                # Return featured tools
                top = [t for t in tools if t.get("featured")][:10]

            return {
                "engine": "AI Tools Registry",
                "status": "ok",
                "total_tools": reg.get("total_tools", len(tools)),
                "results": top,
                "message": f"Found {len(top)} relevant tools from {len(tools)} total"
            }

        elif reg_id == "api-directory":
            reg = TOOL_REGISTRIES.get("apis", {})
            categories = reg.get("categories", [])
            total = reg.get("total_apis", 0)

            # Find relevant categories
            relevant = []
            for cat in categories:
                cat_name = cat.get("name", "").lower()
                cat_desc = cat.get("description", "").lower()
                score = 0
                for word in p.split():
                    if len(word) > 3 and (word in cat_name or word in cat_desc):
                        score += 1
                if score > 0:
                    relevant.append((score, cat))

            relevant.sort(key=lambda x: -x[0])
            top_cats = [c for s, c in relevant][:5]

            return {
                "engine": "API Directory",
                "status": "ok",
                "total_apis": total,
                "relevant_categories": top_cats,
                "message": f"Found {len(top_cats)} relevant API categories from {len(categories)} total ({total} APIs indexed)"
            }

        elif reg_id == "learn":
            reg = TOOL_REGISTRIES.get("learn", {})
            modules = reg.get("modules", [])

            # Find relevant modules
            relevant = []
            for m in modules:
                m_title = m.get("title", "").lower()
                m_desc = m.get("description", "").lower()
                score = 0
                for word in p.split():
                    if len(word) > 3 and (word in m_title or word in m_desc):
                        score += 1
                relevant.append((score, m))

            relevant.sort(key=lambda x: -x[0])
            top = [m for s, m in relevant if s > 0][:5]
            if not top:
                top = modules[:5]

            return {
                "engine": "Learning Hub",
                "status": "ok",
                "total_modules": reg.get("total_modules", len(modules)),
                "results": top,
                "message": f"Found {len(top)} relevant learning modules"
            }

        elif reg_id == "image-gen":
            reg = TOOL_REGISTRIES.get("image_gen", {})
            return {
                "engine": "Image Gen API",
                "status": "ok",
                "models": reg.get("models", []),
                "deployment_steps": reg.get("deployment_steps", []),
                "usage": reg.get("usage_examples", {}),
                "message": "Free image generation API: 100K calls/day via Cloudflare Workers AI"
            }

        return {"engine": intent["engine"], "status": "error", "message": "Unknown registry"}

    @staticmethod
    def _freellm(intent, prompt):
        """Route to free LLM API providers as alternative to paid services."""
        providers = FREE_LLM_PROVIDERS
        if not providers:
            # Fallback to Ollama
            return EngineRouter._ollama("qwen2.5:14b", prompt)

        # Pick best provider based on prompt needs
        p = prompt.lower()
        selected = None

        # Check for specific needs
        if re.search(r'\b(vision|image|multimodal|see)\b', p):
            for prov in providers:
                if "vision" in str(prov.get("modalities", [])).lower():
                    selected = prov
                    break

        if not selected and re.search(r'\b(fast|quick|real.?time|low.?latency|speed)\b', p):
            for prov in providers:
                if "groq" in prov["name"].lower() or "cerebras" in prov["name"].lower():
                    selected = prov
                    break

        if not selected and re.search(r'\b(code|coding|program|debug|refactor)\b', p):
            for prov in providers:
                if any("coder" in m.lower() or "code" in m.lower() for m in prov.get("models", [])):
                    selected = prov
                    break

        if not selected:
            # Pick first available provider with most free models
            selected = max(providers, key=lambda x: x.get("free_models", 0) if isinstance(x.get("free_models"), int) else 0)

        return {
            "engine": f"Free LLM API ({selected['name']})",
            "status": "info",
            "provider": selected,
            "available_providers": len(providers),
            "message": f"Route to {selected['name']} - {selected.get('free_models', '?')} free models. Get API key at {selected.get('key_url', 'N/A')}. Base URL: {selected.get('base_url', 'N/A')}",
            "suggestion": "curl " + selected.get("base_url", "") + "/v1/chat/completions -H 'Authorization: Bearer YOUR_KEY' -H 'Content-Type: application/json' -d '{\"model\":\"auto\",\"messages\":[{\"role\":\"user\",\"content\":\"' + prompt[:200] + '\"}]}'"
        }

    @staticmethod
    def _build_video_workflow(model_id, prompt):
        import random
        return {
            "3": {"class_type": "KSampler", "inputs": {
                "seed": random.randint(0, 2**32),
                "steps": 20, "cfg": 7.5, "sampler_name": "euler",
                "scheduler": "normal", "denoise": 1.0,
                "model": ["4", 0], "positive": ["6", 0],
                "negative": ["7", 0], "latent_image": ["5", 0]
            }},
            "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": f"{model_id}/model.safetensors"}},
            "5": {"class_type": "EmptyLatentVideo", "inputs": {"width": 512, "height": 512, "length": 16, "batch_size": 1}},
            "6": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["4", 1]}},
            "7": {"class_type": "CLIPTextEncode", "inputs": {"text": "blurry, low quality, distorted, watermark", "clip": ["4", 1]}}
        }

    @staticmethod
    def _build_image_workflow(model_id, prompt):
        import random
        return {
            "3": {"class_type": "KSampler", "inputs": {
                "seed": random.randint(0, 2**32),
                "steps": 25, "cfg": 8.0, "sampler_name": "euler",
                "scheduler": "normal", "denoise": 1.0,
                "model": ["4", 0], "positive": ["6", 0],
                "negative": ["7", 0], "latent_image": ["5", 0]
            }},
            "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": f"{model_id}/model.safetensors"}},
            "5": {"class_type": "EmptyLatentImage", "inputs": {"width": 1024, "height": 1024, "batch_size": 1}},
            "6": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["4", 1]}},
            "7": {"class_type": "CLIPTextEncode", "inputs": {"text": "blurry, low quality, distorted, watermark", "clip": ["4", 1]}}
        }


# ═══════════════════════════════════════════════════════════════════════════════
# HTTP Server
# ═══════════════════════════════════════════════════════════════════════════════

class MrJamesServer(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_GET(self):
        if self.path == "/" or self.path == "/health":
            self.respond(200, {
                "service": "Mr James v5.0",
                "status": "online",
                "engine": "auto-select",
                "models": sum(len(v.get("models", {})) for v in MANIFEST.get("models", {}).values()),
                "routing": "intent-based auto-selection",
                "capabilities": [
                    "video_generation", "image_generation", "image_control",
                    "animation", "audio_tts", "audio_stt", "music",
                    "vision", "3d", "rag", "video_edit", "coding",
                    "chat", "code", "crypto", "comfyui", "omniroute",
                    "tool_discovery", "api_discovery", "freellm_routing",
                    "learning_hub", "image_gen_deploy"
                ],
                "registries": {
                    "ai_tools": TOOL_REGISTRIES.get("ai_tools", {}).get("total_tools", 0),
                    "freellm_providers": len(FREE_LLM_PROVIDERS),
                    "freellm_models": TOOL_REGISTRIES.get("freellm", {}).get("total_free_models", 0),
                    "apis": TOOL_REGISTRIES.get("apis", {}).get("total_apis", 0),
                    "learn_modules": TOOL_REGISTRIES.get("learn", {}).get("total_modules", 0),
                    "image_gen_models": len(TOOL_REGISTRIES.get("image_gen", {}).get("models", []))
                }
            })
        elif self.path == "/models":
            self.respond(200, MANIFEST)
        elif self.path == "/registries":
            self.respond(200, {
                "ai_tools": {
                    "total": TOOL_REGISTRIES.get("ai_tools", {}).get("total_tools", 0),
                    "categories": TOOL_REGISTRIES.get("ai_tools", {}).get("total_categories", 0)
                },
                "freellm": {
                    "providers": len(FREE_LLM_PROVIDERS),
                    "total_models": TOOL_REGISTRIES.get("freellm", {}).get("total_free_models", 0)
                },
                "apis": {
                    "total": TOOL_REGISTRIES.get("apis", {}).get("total_apis", 0)
                },
                "learn": {
                    "modules": TOOL_REGISTRIES.get("learn", {}).get("total_modules", 0)
                },
                "image_gen": {
                    "models": len(TOOL_REGISTRIES.get("image_gen", {}).get("models", []))
                }
            })
        elif self.path == "/search-tools":
            content_len = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(content_len)) if content_len else {}
            query = body.get("query", "")
            category = body.get("category", "all")
            reg = TOOL_REGISTRIES.get("ai_tools", {})
            tools = reg.get("tools", [])
            if category != "all":
                tools = [t for t in tools if t.get("category") == category]
            if query:
                q = query.lower()
                scored = []
                for t in tools:
                    score = 0
                    searchable = (t.get("name", "") + " " + t.get("shortDescription", "") + " " + " ".join(t.get("tags", []))).lower()
                    for word in q.split():
                        if word in searchable:
                            score += 1
                    if score > 0:
                        scored.append((score, t))
                scored.sort(key=lambda x: -x[0])
                tools = [t for s, t in scored]
            self.respond(200, {"results": tools[:20], "total": len(tools), "query": query})
        elif self.path == "/free-llm-providers":
            self.respond(200, {"providers": FREE_LLM_PROVIDERS, "total": len(FREE_LLM_PROVIDERS)})
        elif self.path == "/engines":
            # List all available engines
            engines = []
            for cat, info in MANIFEST.get("models", {}).items():
                for mid, minfo in info.get("models", {}).items():
                    engines.append({
                        "id": mid, "name": mid, "category": cat,
                        "type": minfo.get("type", ""), "status": minfo.get("status", ""),
                        "vram": minfo.get("vram", "")
                    })
            self.respond(200, {"engines": engines})
        else:
            self.respond(404, {"error": "Not found"})

    def do_POST(self):
        content_len = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(content_len)) if content_len else {}

        if self.path == "/chat" or self.path == "/agent/chat":
            prompt = body.get("message", body.get("prompt", ""))
            context = body.get("context", body.get("messages", None))

            if not prompt:
                self.respond(400, {"error": "No message provided"})
                return

            # Auto-select engine
            intent = EngineSelector.detect(prompt)

            # Route to engine
            result = EngineRouter.route(intent, prompt, context)

            self.respond(200, {
                "intent": intent,
                "result": result,
                "response": result.get("response", result.get("message", "")),
                "engine_used": result.get("engine", intent["engine"]),
                "status": result.get("status", "ok")
            })

        elif self.path == "/detect":
            # Just detect intent without executing
            prompt = body.get("message", body.get("prompt", ""))
            intent = EngineSelector.detect(prompt)
            self.respond(200, {"intent": intent})

        elif self.path == "/generate":
            # Direct generation with specified type
            gen_type = body.get("type", "auto")
            prompt = body.get("prompt", "")

            if gen_type == "auto":
                intent = EngineSelector.detect(prompt)
            else:
                intent = {"type": gen_type, "engine": body.get("engine", "auto"), "route": gen_type, "reason": "User-specified"}

            result = EngineRouter.route(intent, prompt, body.get("context"))
            self.respond(200, {"intent": intent, "result": result})

        else:
            self.respond(404, {"error": "Not found"})

    def respond(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self._cors()
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 5003), MrJamesServer)
    print("Mr James v5.0 running on port 5003")
    print("Auto-engine selection: ON")
    print(f"Models registered: {sum(len(v.get('models', {})) for v in MANIFEST.get('models', {}).values())}")
    server.serve_forever()
