"""
EvolvixOS Model Registry Builder
Merges Ollama models + GitHub Discovery tools into a unified registry.
Updates /api/models to return all available models/tools.
"""
import sqlite3
import json
import os
import urllib.request

DISCOVERY_DB = "/opt/evolvixos/learner/discovery.db"
OLLAMA_URL = "http://127.0.0.1:11434"
REGISTRY_PATH = "/opt/evolvixos/models/model_registry.json"

# Category mapping: discovery categories -> EvolvixOS categories
CATEGORY_MAP = {
    "image_generation": "image_generation",
    "llm_text": "llm_text",
    "local_engines": "local_engines",
    "rag_agents": "rag_agents",
    "speech_voice": "speech_voice",
    "video_generation": "video_generation",
    "vision_multimodal": "vision_multimodal",
    "ai_coding": "ai_coding",
    "music_audio": "music_audio",
    "three_d": "three_d",
    "image_control": "image_control",
    "frameworks": "frameworks"
}

def build_registry():
    registry = {
        "version": "1.0",
        "last_updated": None,
        "total_models": 0,
        "categories": {},
        "models": []
    }
    
    # 1. Add Ollama models
    try:
        req = urllib.request.Request(f"{OLLAMA_URL}/api/tags")
        with urllib.request.urlopen(req, timeout=10) as resp:
            ollama_data = json.loads(resp.read())
        for m in ollama_data.get("models", []):
            name = m["name"]
            size = m.get("size", 0)
            # Determine category from model name
            cat = "llm_text"
            if "embed" in name:
                cat = "rag_agents"
            elif "moondream" in name or "vl" in name or "vision" in name:
                cat = "vision_multimodal"
            
            registry["models"].append({
                "name": name,
                "full_name": f"ollama/{name}",
                "description": f"Local model via Ollama ({name})",
                "category": cat,
                "source": "ollama",
                "engine": "ollama",
                "size": size,
                "status": "available",
                "stars": 0,
                "url": "",
                "installable": False,
                "running": True
            })
    except Exception as e:
        print(f"Warning: Could not fetch Ollama models: {e}")
    
    # 2. Add discovered GitHub tools
    try:
        conn = sqlite3.connect(DISCOVERY_DB)
        c = conn.cursor()
        c.execute("SELECT name, full_name, description, category, url, stars, language, topics FROM discovered_tools ORDER BY stars DESC")
        for row in c.fetchall():
            name, full_name, desc, cat, url, stars, lang, topics = row
            mapped_cat = CATEGORY_MAP.get(cat, cat)
            registry["models"].append({
                "name": name,
                "full_name": full_name,
                "description": desc or name,
                "category": mapped_cat,
                "source": "github_discovery",
                "engine": "discovered",
                "size": 0,
                "status": "discovered",
                "stars": stars or 0,
                "url": url or f"https://github.com/{full_name}",
                "language": lang or "",
                "topics": topics or "",
                "installable": True,
                "running": False
            })
        conn.close()
    except Exception as e:
        print(f"Warning: Could not read discovery DB: {e}")
    
    # 3. Add built-in EvolvixOS services
    builtin = [
        {"name": "Mr James Agent", "full_name": "evolvixos/mr-james", "description": "Autonomous AI agent with 24 tools, intent-based routing, self-correction", "category": "rag_agents", "engine": "evolvixos", "stars": 0, "running": True},
        {"name": "ComfyUI", "full_name": "evolvixos/comfyui", "description": "Image generation pipeline with custom nodes", "category": "image_generation", "engine": "comfyui", "stars": 0, "running": True},
        {"name": "OmniRoute Gateway", "full_name": "evolvixos/omniroute", "description": "AI gateway for 340+ model providers", "category": "frameworks", "engine": "omniroute", "stars": 0, "running": True},
        {"name": "Art Engine", "full_name": "evolvixos/art-engine", "description": "Local art generation engine", "category": "image_generation", "engine": "art_engine", "stars": 0, "running": True},
        {"name": "Kimi API", "full_name": "evolvixos/kimi", "description": "Complex reasoning fallback (GPT/Claude-level quality)", "category": "llm_text", "engine": "kimi", "stars": 0, "running": True},
        {"name": "Piper TTS", "full_name": "evolvixos/piper", "description": "Neural TTS for AI voiceovers", "category": "speech_voice", "engine": "piper", "stars": 0, "running": True},
        {"name": "Whisper STT", "full_name": "evolvixos/whisper", "description": "Speech-to-text transcription", "category": "speech_voice", "engine": "whisper", "stars": 0, "running": True},
        {"name": "FFmpeg", "full_name": "evolvixos/ffmpeg", "description": "Video processing and 4K media production", "category": "video_generation", "engine": "ffmpeg", "stars": 0, "running": True},
        {"name": "CoinGecko API", "full_name": "evolvixos/coingecko", "description": "Crypto market data and token analysis", "category": "frameworks", "engine": "coingecko", "stars": 0, "running": True},
        {"name": "DeFiLlama API", "full_name": "evolvixos/defillama", "description": "DeFi protocol analytics and TVL tracking", "category": "frameworks", "engine": "defillama", "stars": 0, "running": True},
    ]
    for b in builtin:
        registry["models"].append({
            "name": b["name"],
            "full_name": b["full_name"],
            "description": b["description"],
            "category": b["category"],
            "source": "builtin",
            "engine": b["engine"],
            "size": 0,
            "status": "running",
            "stars": b["stars"],
            "url": "",
            "installable": False,
            "running": b["running"]
        })
    
    # 4. Build category summary
    from collections import Counter
    cats = Counter(m["category"] for m in registry["models"])
    registry["categories"] = dict(sorted(cats.items()))
    registry["total_models"] = len(registry["models"])
    
    from datetime import datetime
    registry["last_updated"] = datetime.utcnow().isoformat() + "Z"
    
    # Save registry
    with open(REGISTRY_PATH, "w") as f:
        json.dump(registry, f, indent=2)
    
    print(f"Registry built: {registry['total_models']} models across {len(cats)} categories")
    for cat, count in sorted(cats.items()):
        print(f"  {cat}: {count}")
    
    return registry

if __name__ == "__main__":
    build_registry()
