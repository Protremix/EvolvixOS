#!/usr/bin/env python3
"""
EvolvixOS Model API v8.0 — Mr James (Oryx-class Agent)
Native tool calling, conversation history, persistent memory, identity, soul.
Same logic as a Base44 Superagent.
"""

import json
import os
import re
import subprocess
import threading
import time
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import uuid
import sqlite3

AUTH_DB = "/opt/evolvixos/auth/users.db"

def get_user_from_request(handler):
    auth_header = handler.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header[7:]
    try:
        conn = sqlite3.connect(AUTH_DB)
        cur = conn.cursor()
        cur.execute("SELECT u.id, u.email, u.display_name FROM user_sessions s JOIN users u ON s.user_id = u.id WHERE s.token = ? AND s.expires > datetime('now')", (token,))
        row = cur.fetchone()
        conn.close()
        if row:
            return {"id": row[0], "email": row[1], "display_name": row[2]}
    except:
        pass
    return None

def scoped_session_id(handler, raw_sid):
    user = get_user_from_request(handler)
    if user:
        return "user_" + str(user["id"]) + "_" + (raw_sid or "default")
    return raw_sid or "default"

def user_dir(handler, base_dir):
    user = get_user_from_request(handler)
    if user:
        d = os.path.join(base_dir, "user_" + str(user["id"]))
        os.makedirs(d, exist_ok=True)
        return d
    return base_dir


# ─── Config ───
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
COMFYUI_URL = os.environ.get("COMFYUI_URL", "http://127.0.0.1:8188")
ART_ENGINE_URL = os.environ.get("ART_ENGINE_URL", "http://127.0.0.1:5002")
# Kimi API - use official Moonshot API directly, fall back to free bridge
KIMI_API_KEY = os.environ.get("KIMI_API_KEY", "")
KIMI_URL = os.environ.get("KIMI_URL", "https://api.moonshot.cn/v1/chat/completions")
KIMI_MODEL = os.environ.get("KIMI_MODEL", "moonshot-v1-32k")
# Free bridge fallback (if official API fails)
KIMI_FREE_URL = "http://localhost:3000/v1/chat/completions"
KIMI_FREE_KEY = "waguri-evolvixos"
KIMI_FREE_MODEL = "k2d6"

# ─── Paths ───
BASE_DIR = "/opt/evolvixos"
IDENTITY_DIR = os.path.join(BASE_DIR, "identity")
MEMORY_DIR = os.path.join(BASE_DIR, "memory")
CONVERSATION_DIR = os.path.join(BASE_DIR, "conversations")
PROJECTS_DIR = os.path.join(BASE_DIR, "projects")
SKILLS_DIR = os.path.join(BASE_DIR, "skills")

for d in [IDENTITY_DIR, MEMORY_DIR, CONVERSATION_DIR, PROJECTS_DIR, SKILLS_DIR]:
    os.makedirs(d, exist_ok=True)

JOBS = {}
JOBS_LOCK = threading.Lock()

# ─── Tool Definitions (native Ollama format) ───
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "bash",
            "description": "Run a shell command on the server. Use for any system operation: listing files, checking services, running scripts, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The shell command to execute"}
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "file_write",
            "description": "Write content to a file on the server. Creates directories if needed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Absolute file path"},
                    "content": {"type": "string", "description": "File content to write"}
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "file_read",
            "description": "Read the contents of a file on the server.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Absolute file path"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "python_exec",
            "description": "Execute Python 3 code on the server. Use for data processing, calculations, automation scripts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Python code to execute"}
                },
                "required": ["code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "service_check",
            "description": "Check the status of a systemd service.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Service name (e.g. nginx, docker)"}
                },
                "required": ["name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "service_restart",
            "description": "Restart a systemd service. Use carefully.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Service name to restart"}
                },
                "required": ["name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "docker_ps",
            "description": "List all Docker containers and their status.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "docker_restart",
            "description": "Restart a specific Docker container.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Container name"}
                },
                "required": ["name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "git",
            "description": "Run git commands in a repository.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Git command (e.g. 'status', 'log --oneline -5', 'push')"},
                    "repo": {"type": "string", "description": "Repository path", "default": "."}
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "http_request",
            "description": "Make an HTTP request to any URL. Use for API calls, webhooks, fetching data.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to request"},
                    "method": {"type": "string", "description": "HTTP method", "default": "GET"},
                    "body": {"type": "object", "description": "JSON body for POST/PUT requests"}
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for information. Returns text results from DuckDuckGo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "ui_generate",
            "description": "Generate UI components using integrated libraries: Magic UI (150+ animated React components), Unlumen UI (59+ shadcn primitives), Retro UI (53 retro themes: Win95, Vaporwave, GameBoy, Tron). Returns component code + preview. Available styles: modern, retro, glassmorphism, brutalist, neumorphism, vaporwave.",
            "parameters": {"type": "object", "properties": {"prompt": {"type": "string", "description": "What UI to build"}, "library": {"type": "string", "enum": ["magic-ui", "unlumen-ui", "retro-ui", "auto"], "description": "Which library to use (auto = best match)"}, "theme": {"type": "string", "description": "For retro-ui: win95, vaporwave, gameboy, tron, crt, dos, arcade, etc."}}, "required": ["prompt"]},
            "name": "image_generate",
            "description": "Generate an AI image from a text prompt using Stable Diffusion / ComfyUI.",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "Image description/prompt"},
                    "steps": {"type": "integer", "description": "Sampling steps (default 15)", "default": 15}
                },
                "required": ["prompt"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_models",
            "description": "List all available Ollama models on the server.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "memory_save",
            "description": "Save a durable memory. Use for important facts, preferences, decisions, or context the user shares. These persist across sessions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Short unique key for this memory (e.g. 'user_name', 'server_config')"},
                    "value": {"type": "string", "description": "The memory content"},
                    "category": {"type": "string", "description": "Category (e.g. 'EvolvixOS', 'User', 'Project', 'Preference')", "default": "General"}
                },
                "required": ["key", "value"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "memory_load",
            "description": "Load a specific memory by key.",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Memory key to load"}
                },
                "required": ["key"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "memory_list",
            "description": "List all stored memories. Use to recall what you know about the user or projects.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "skill_run",
            "description": "Execute an EvolvixOS skill. Available skills: create-media (4K video/voiceover/images), crypto-blockchain (market analysis), design-studio (logos/brand/graphics), voice-command (Alexa-style assistant).",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Skill name: create-media, crypto-blockchain, design-studio, or voice-command"},
                    "input": {"type": "string", "description": "Input/prompt for the skill"}
                },
                "required": ["name", "input"]
            }
        }
    },
]

TOOL_NAMES = [t["function"]["name"] for t in TOOLS]


# ─── Load Identity & Soul ───
def load_identity():
    """Load Mr James's identity file."""
    path = os.path.join(IDENTITY_DIR, "IDENTITY.md")
    if os.path.exists(path):
        with open(path) as f:
            return f.read()
    return ""

def load_soul():
    """Load Mr James's soul file."""
    path = os.path.join(IDENTITY_DIR, "SOUL.md")
    if os.path.exists(path):
        with open(path) as f:
            return f.read()
    return ""

def load_context(mem_dir=None):
    """Load memories and system context — same as Oryx loading memory."""
    context_parts = []
    
    # Memories
    memories = []
    mdir = mem_dir or MEMORY_DIR
    if os.path.exists(mdir):
        for fname in sorted(os.listdir(mdir)):
            if fname.endswith(".json"):
                try:
                    with open(os.path.join(mdir, fname)) as f:
                        mem = json.load(f)
                        memories.append(f"- [{mem.get('category','General')}] {mem['key']}: {mem['value'][:200]}")
                except:
                    pass
    if memories:
        context_parts.append("## What I Remember\n" + "\n".join(memories))
    
    # System status
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    context_parts.append(f"## Current Context\nTime: {now}\nServer: 2.28.52.223 (evolvixos.com)\nPlatform: EvolvixOS v8.0\nModels: 281 across 12 categories")
    
    # Skills available
    skills = []
    if os.path.exists(SKILLS_DIR):
        for fname in os.listdir(SKILLS_DIR):
            if fname.endswith(".sh"):
                skills.append(fname.replace(".sh", ""))
    if skills:
        context_parts.append("## My Skills\n" + ", ".join(skills))
    
    return "\n\n".join(context_parts)


def build_system_prompt(mem_dir=None):
    """Build the full system prompt — identity + soul + context. Same structure as Oryx."""
    parts = []
    
    soul = load_soul()
    if soul:
        parts.append(soul)
    
    identity = load_identity()
    if identity:
        parts.append(identity)
    
    context = load_context(mem_dir=mem_dir)
    if context:
        parts.append(context)
    
    return "\n\n---\n\n".join(parts)


# ─── Conversation History ───
def get_conversation(session_id, conv_dir=None):
    """Load conversation history for a session."""
    if not session_id:
        return []
    d = conv_dir or CONVERSATION_DIR
    fpath = os.path.join(d, f"{session_id}.json")
    if os.path.exists(fpath):
        try:
            with open(fpath) as f:
                return json.load(f)
        except:
            return []
    return []

def save_conversation(session_id, messages, conv_dir=None):
    """Save conversation history."""
    if not session_id:
        return
    fpath = os.path.join(CONVERSATION_DIR, f"{session_id}.json")
    # Keep only last 20 messages to avoid memory bloat
    trimmed = messages[-20:]
    with open(fpath, "w") as f:
        json.dump(trimmed, f)


# ─── Tool Execution ───
def execute_tool(name, args, mem_dir=None):
    """Execute a tool by name with given arguments. Returns string result."""
    try:
        if name == "bash":
            cmd = args.get("command", "")
            if not cmd:
                return "Error: no command provided"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
            output = result.stdout
            if result.stderr:
                output += f"\n[STDERR]\n{result.stderr}"
            if result.returncode != 0:
                output += f"\n[EXIT: {result.returncode}]"
            return output[:8000] if output else "(no output)"

        elif name == "file_write":
            path = args.get("path", "")
            content = args.get("content", "")
            if not path:
                return "Error: no path"
            os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
            with open(path, "w") as f:
                f.write(content)
            return f"Wrote {len(content)} bytes to {path}"

        elif name == "file_read":
            path = args.get("path", "")
            if not path:
                return "Error: no path"
            if not os.path.exists(path):
                return f"File not found: {path}"
            with open(path) as f:
                return f.read()[:15000]

        elif name == "python_exec":
            code = args.get("code", "")
            if not code:
                return "Error: no code"
            result = subprocess.run(["python3", "-c", code], capture_output=True, text=True, timeout=60)
            output = result.stdout
            if result.stderr:
                output += f"\n[STDERR]\n{result.stderr}"
            if result.returncode != 0:
                output += f"\n[EXIT: {result.returncode}]"
            return output[:8000] if output else "(no output)"

        elif name == "service_check":
            svc = args.get("name", "")
            r = subprocess.run(f"systemctl is-active {svc}", shell=True, capture_output=True, text=True)
            return f"Service '{svc}' is {r.stdout.strip()}"

        elif name == "service_restart":
            svc = args.get("name", "")
            r = subprocess.run(f"systemctl restart {svc}", shell=True, capture_output=True, text=True)
            return f"Service '{svc}' restarted" if r.returncode == 0 else f"Error: {r.stderr}"

        elif name == "docker_ps":
            r = subprocess.run("docker ps -a --format '{{.Names}}\\t{{.Status}}\\t{{.Ports}}'", shell=True, capture_output=True, text=True)
            return r.stdout or "No containers"

        elif name == "docker_restart":
            cname = args.get("name", "")
            r = subprocess.run(f"docker restart {cname}", shell=True, capture_output=True, text=True)
            return f"Container '{cname}' restarted" if r.returncode == 0 else f"Error: {r.stderr}"

        elif name == "git":
            repo = args.get("repo", ".")
            cmd = args.get("command", "")
            r = subprocess.run(f"cd {repo} && git {cmd}", shell=True, capture_output=True, text=True, timeout=30)
            return (r.stdout + r.stderr)[:5000] or "(no output)"

        elif name == "http_request":
            url = args.get("url", "")
            method = args.get("method", "GET")
            body = args.get("body")
            data = json.dumps(body).encode() if body else None
            req = urllib.request.Request(url, data=data, method=method)
            req.add_header("Content-Type", "application/json")
            with urllib.request.urlopen(req, timeout=15) as resp:
                return resp.read().decode()[:5000]

        elif name == "web_search":
            query = args.get("query", "")
            url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(query)}&format=json&no_html=1"
            req = urllib.request.Request(url, headers={"User-Agent": "MrJames/7.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
            results = []
            if data.get("AbstractText"):
                results.append(data["AbstractText"])
            for topic in data.get("RelatedTopics", [])[:5]:
                if isinstance(topic, dict) and topic.get("Text"):
                    results.append(topic["Text"])
            return "\n\n".join(results) if results else "No results found"

        elif name == "ui_generate":
            library = args.get("library", "auto")
            theme = args.get("theme", "")
            ui_prompt = args.get("prompt", "")
                
            ui_lib_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ui-libraries")
                
            # Determine best library
            if library == "auto":
                if any(t in ui_prompt.lower() for t in ["retro", "win95", "windows 95", "vaporwave", "dos", "arcade", "gameboy", "crt", "tron"]):
                    library = "retro-ui"
                elif any(t in ui_prompt.lower() for t in ["animate", "beam", "particle", "gradient", "shiny", "glow"]):
                    library = "magic-ui"
                else:
                    library = "unlumen-ui"
                
            result_parts = []
                
            if library == "magic-ui":
                comp_dir = os.path.join(ui_lib_dir, "magicui", "apps", "www", "registry", "magicui")
                if os.path.isdir(comp_dir):
                    components = [f.replace(".tsx", "") for f in os.listdir(comp_dir) if f.endswith(".tsx")]
                    result_parts.append(f"Magic UI - {len(components)} components available at {comp_dir}")
                    result_parts.append(f"Components: {', '.join(sorted(components)[:20])}...")
                    # Find matching component
                    matched = [c for c in components if any(w in c for w in ui_prompt.lower().split())]
                    if matched:
                        comp_file = os.path.join(comp_dir, matched[0] + ".tsx")
                        with open(comp_file) as cf:
                            code = cf.read()[:3000]
                        result_parts.append(f"\n--- Component: {matched[0]} ---\n```tsx\n{code}\n```")
                    else:
                        result_parts.append(f"No exact match. Use a component name from the list above.")
                else:
                    result_parts.append("Magic UI library not found")
                
            elif library == "unlumen-ui":
                reg_dir = os.path.join(ui_lib_dir, "unlumen-ui", "__registry__")
                if os.path.isdir(reg_dir):
                    components = []
                    for root, dirs, files in os.walk(reg_dir):
                        for f in files:
                            if f.endswith(".tsx") or f.endswith(".ts"):
                                components.append(os.path.relpath(os.path.join(root, f), reg_dir))
                    result_parts.append(f"Unlumen UI - {len(components)} files in registry")
                    result_parts.append(f"Components: {', '.join(sorted(set(c.split('/')[0] for c in components))[:20])}...")
                else:
                    result_parts.append("Unlumen UI library not found")
                
            elif library == "retro-ui":
                tokens_dir = os.path.join(ui_lib_dir, "retro-design-system", "tokens")
                styles_dir = os.path.join(ui_lib_dir, "retro-design-system", "styles")
                if os.path.isdir(tokens_dir):
                    themes = [f.replace(".css", "") for f in os.listdir(tokens_dir) if f.endswith(".css")]
                    result_parts.append(f"Retro UI - {len(themes)} themes available")
                    result_parts.append(f"Themes: {', '.join(sorted(themes)[:15])}...")
                        
                    # Find matching theme
                    if theme:
                        matched = [t for t in themes if theme.lower() in t.lower()]
                    else:
                        matched = [t for t in themes if any(w in t.lower() for w in ui_prompt.lower().split())]
                        
                    if matched:
                        theme_file = os.path.join(tokens_dir, matched[0] + ".css")
                        with open(theme_file) as tf:
                            css = tf.read()[:3000]
                        result_parts.append(f"\n--- Theme: {matched[0]} ---\n```css\n{css}\n```")
                            
                        # Also check for style files
                        style_dir = os.path.join(styles_dir, matched[0])
                        if os.path.isdir(style_dir):
                            for sf in os.listdir(style_dir):
                                if sf.endswith(".css") or sf.endswith(".html"):
                                    sfile = os.path.join(style_dir, sf)
                                    with open(sfile) as sfh:
                                        result_parts.append(f"\n--- {sf} ---\n{sfh.read()[:2000]}")
                    else:
                        result_parts.append(f"No theme match. Try: win95, vaporwave, gameboy, tron, crt, dos, arcade")
                else:
                    result_parts.append("Retro UI library not found")
                
            self.respond(200, {"response": "\n\n".join(result_parts), "library": library, "status": "success"})

        elif name == "image_generate":
            prompt = args.get("prompt", "")
            steps = args.get("steps", 15)
            job_id = str(uuid.uuid4())[:8]
            with JOBS_LOCK:
                JOBS[job_id] = {"status": "processing", "prompt": prompt, "created": datetime.now().isoformat(), "image": None}
            threading.Thread(target=_generate_image, args=(job_id, prompt, steps), daemon=True).start()
            return f"Image generation started. Job ID: {job_id}"

        elif name == "list_models":
            req = urllib.request.Request(f"{OLLAMA_URL}/api/tags")
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read())
                models = [m["name"] for m in data.get("models", [])]
                return f"Available models: {', '.join(models)}"

        elif name == "memory_save":
            key = args.get("key", "")
            value = args.get("value", "")
            category = args.get("category", "General")
            mem = {"key": key, "value": value, "category": category, "timestamp": datetime.now().isoformat()}
            mdir = mem_dir or MEMORY_DIR
            with open(os.path.join(mdir, f"{key}.json"), "w") as f:
                json.dump(mem, f)
            return f"Memory saved: {key}"

        elif name == "memory_load":
            key = args.get("key", "")
            mdir = mem_dir or MEMORY_DIR
            fpath = os.path.join(mdir, f"{key}.json")
            if not os.path.exists(fpath):
                return f"No memory: {key}"
            with open(fpath) as f:
                return json.dumps(json.load(f))

        elif name == "memory_list":
            memories = []
            mdir = mem_dir or MEMORY_DIR
            if not os.path.exists(mdir): return 'No memories'
            for fname in os.listdir(mdir):
                if fname.endswith(".json"):
                    try:
                        with open(os.path.join(MEMORY_DIR, fname)) as f:
                            mem = json.load(f)
                            memories.append(f"[{mem.get('category','General')}] {mem['key']}: {mem['value'][:80]}")
                    except:
                        pass
            return "\n".join(memories) if memories else "No memories"

        elif name == "skill_run":
            skill_name = args.get("name", "")
            skill_input = args.get("input", "")
            skill_path = os.path.join(SKILLS_DIR, f"{skill_name}.sh")
            if not os.path.exists(skill_path):
                available = [f.replace(".sh", "") for f in os.listdir(SKILLS_DIR) if f.endswith(".sh")]
                return f"Skill not found: {skill_name}. Available: {', '.join(available)}"
            r = subprocess.run([skill_path, skill_input], capture_output=True, text=True, timeout=120)
            return (r.stdout + (f"\n[STDERR]\n{r.stderr}" if r.stderr else ""))[:8000] or "(no output)"

        else:
            return f"Unknown tool: {name}"

    except subprocess.TimeoutExpired:
        return "Error: command timed out (60s)"
    except Exception as e:
        return f"Error: {e}"


def _generate_image(job_id, prompt, steps):
    """
    Background image generation.
    Order of preference:
      1. ComfyUI/SDXL if a real checkpoint is installed (GPU box, once GEX44 arrives)
      2. Pollinations.ai — free, no-key, genuinely prompt-aware (Flux-based) hosted API
      3. Local PIL gradient-placeholder skill (design-studio.sh) as last resort
    Returns a URL that nginx actually serves (/output/...).
    """
    start_time = time.time()
    try:
        has_checkpoint = False
        ckpts = []
        try:
            info_req = urllib.request.Request(f"{COMFYUI_URL}/object_info/CheckpointLoaderSimple")
            with urllib.request.urlopen(info_req, timeout=5) as resp:
                info = json.loads(resp.read())
                ckpts = info.get("CheckpointLoaderSimple", {}).get("input", {}).get("required", {}).get("ckpt_name", [[]])[0]
                has_checkpoint = len(ckpts) > 0
        except Exception:
            has_checkpoint = False

        if not has_checkpoint:
            # Try Pollinations.ai — free, unauthenticated, actually follows the prompt
            try:
                import urllib.parse
                design_dir = os.path.join(BASE_DIR, "output", "design")
                os.makedirs(design_dir, exist_ok=True)
                enc_prompt = urllib.parse.quote(prompt)
                seed = int(time.time()) % 1000000
                poll_url = f"https://image.pollinations.ai/prompt/{enc_prompt}?width=1024&height=1024&nologo=true&seed={seed}"
                fname = f"pollinations_{seed}.png"
                fpath = os.path.join(design_dir, fname)
                poll_req = urllib.request.Request(poll_url, headers={"User-Agent": "EvolvixOS/1.0"})
                with urllib.request.urlopen(poll_req, timeout=45) as p_resp:
                    img_data = p_resp.read()
                if len(img_data) > 1000:
                    with open(fpath, "wb") as f:
                        f.write(img_data)
                    with JOBS_LOCK:
                        JOBS[job_id] = {"status": "done", "image": f"https://evolvixos.com/output/design/{fname}", "prompt": prompt, "generation_time": round(time.time()-start_time,1), "engine": "Flux/Pollinations (free)"}
                    return
            except Exception as e:
                print(f"Pollinations fallback error: {e}")

        if has_checkpoint:
            ckpt_name = ckpts[0]
            workflow = {
                "prompt": {
                    "3": {"class_type": "KSampler", "inputs": {
                        "seed": int(time.time()) % 1000000, "steps": steps, "cfg": 8,
                        "sampler_name": "euler", "scheduler": "normal", "denoise": 1,
                        "model": ["4", 0], "positive": ["7", 0], "negative": ["6", 0], "latent_image": ["5", 0],
                    }},
                    "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": ckpt_name}},
                    "5": {"class_type": "EmptyLatentImage", "inputs": {"width": 1024, "height": 1024, "batch_size": 1}},
                    "6": {"class_type": "CLIPTextEncode", "inputs": {"text": "blurry, low quality, distorted, watermark", "clip": ["4", 1]}},
                    "7": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["4", 1]}},
                    "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
                    "9": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": "james_gen"}},
                }
            }
            req = urllib.request.Request(f"{COMFYUI_URL}/prompt", data=json.dumps(workflow).encode(), headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read())
                prompt_id = result.get("prompt_id", "")
            for _ in range(60):
                time.sleep(3)
                try:
                    hist_req = urllib.request.Request(f"{COMFYUI_URL}/history/{prompt_id}")
                    with urllib.request.urlopen(hist_req, timeout=5) as h_resp:
                        hist = json.loads(h_resp.read())
                        if prompt_id in hist:
                            outputs = hist[prompt_id].get("outputs", {})
                            if "9" in outputs:
                                images = outputs["9"].get("images", [])
                                if images:
                                    img = images[0]
                                    img_url = f"{COMFYUI_URL}/view?filename={img['filename']}&subfolder={img.get('subfolder','')}&type={img.get('type','output')}"
                                    with JOBS_LOCK:
                                        JOBS[job_id] = {"status": "done", "image": img_url, "prompt": prompt, "generation_time": round(time.time()-start_time,1), "engine": "SDXL/ComfyUI"}
                                    return
                except Exception:
                    pass

        design_dir = os.path.join(BASE_DIR, "output", "design")
        os.makedirs(design_dir, exist_ok=True)
        before = set(os.listdir(design_dir)) if os.path.exists(design_dir) else set()

        skill_path = os.path.join(SKILLS_DIR, "design-studio.sh")
        r = subprocess.run([skill_path, prompt], capture_output=True, text=True, timeout=60)

        after = set(os.listdir(design_dir)) if os.path.exists(design_dir) else set()
        new_files = sorted(after - before)

        if not new_files:
            with JOBS_LOCK:
                JOBS[job_id] = {"status": "error", "error": f"Generator produced no output. {r.stderr[:300]}"}
            return

        fname = new_files[0]
        img_url = f"https://evolvixos.com/output/design/{fname}"
        with JOBS_LOCK:
            JOBS[job_id] = {
                "status": "done", "image": img_url, "prompt": prompt,
                "generation_time": round(time.time() - start_time, 1),
                "engine": "Local Design Engine (PIL, CPU)",
                "variants": [f"https://evolvixos.com/output/design/{f}" for f in new_files],
            }
    except Exception as e:
        with JOBS_LOCK:
            JOBS[job_id]["status"] = "error"
            JOBS[job_id]["error"] = str(e)


# ─── LLM Backend ───
def call_ollama_with_tools(model, messages, tools, stream=False):
    """Call Ollama with native tool calling support."""
    data = {"model": model, "messages": messages, "stream": stream}
    if tools:
        data["tools"] = tools
    
    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/chat",
        data=json.dumps(data).encode(),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        if stream:
            return resp  # Return the response for streaming
        else:
            return json.loads(resp.read())


def call_kimi(messages, max_tokens=4000):
    """Call Kimi API - tries official Moonshot API first, falls back to free bridge"""
    # Try official Moonshot API first
    if KIMI_API_KEY:
        try:
            data = json.dumps({
                "model": KIMI_MODEL,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": 0.7,
                "stream": False
            }).encode()
            req = urllib.request.Request(KIMI_URL, data=data, headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {KIMI_API_KEY}"
            })
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read())
                return result.get("choices", [{}])[0].get("message", {}).get("content", "")
        except Exception as e:
            print(f"Kimi official API failed: {e}", flush=True)
    
    # Fall back to free bridge
    try:
        data = json.dumps({
            "model": KIMI_FREE_MODEL,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.7,
            "stream": False
        }).encode()
        req = urllib.request.Request(KIMI_FREE_URL, data=data, headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {KIMI_FREE_KEY}"
        })
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())
            return result.get("choices", [{}])[0].get("message", {}).get("content", "")
    except Exception as e:
        print(f"Kimi free bridge failed: {e}", flush=True)
        raise RuntimeError(f"All Kimi endpoints failed: {e}")
# ─── Intent Classification Rules ───
INTENT_RULES = [
    # (intent, engine, model, keywords)
    ("image_gen",  "pollinations", "flux",      ["generate image", "create image", "draw", "make a picture", "render image", "image of", "picture of"]),
    ("video_gen",  "comfyui",      "wan2.1",    ["generate video", "create video", "make a video", "animate", "video of"]),
    ("three_d",    "comfyui",      "3d",        ["3d model", "create 3d", "generate 3d", "mesh", "render 3d"]),
    ("crypto",     "crypto_skill",  "crypto",    ["crypto", "bitcoin", "ethereum", "defi", "blockchain", "token", "wallet", "nft", "market cap", "coingecko"]),
    ("coding",     "ollama",       "qwen2.5:7b", ["write code", "write a function", "write a script", "debug", "fix code", "python", "javascript", "typescript", "react", "api endpoint", "sql", "algorithm", "implement", "refactor"]),
    ("vision",     "ollama",       "moondream:latest", ["analyze image", "describe image", "what is in this image", "read image", "ocr"]),
    ("complex",    "kimi",         "moonshot-v1-32k", ["architect", "design system", "design a", "compare", "analyze", "strategy", "write a comprehensive", "write a detailed", "create a complete", "build a full", "explain in detail", "step by step guide", "in-depth analysis", "research", "evaluate", "trade-offs", "pros and cons", "detailed analysis"]),
    ("chat",       "ollama",       "qwen2.5:7b",  []),  # fallback
]

def classify_intent(prompt):
    """Classify the user prompt into an intent. Returns (intent, engine, model)."""
    p = prompt.lower().strip()

    # Check rules in priority order
    for intent, engine, model, keywords in INTENT_RULES:
        if not keywords:
            continue  # skip fallback
        for kw in keywords:
            if kw in p:
                return intent, engine, model

    # Heuristics for fallback
    if len(prompt) > 800:
        return "complex", "kimi", "moonshot-v1-32k"
    if len(prompt) < 50 and "?" in prompt:
        return "chat", "ollama", "qwen2.5:3b"

    # Default: simple chat with fast model
    return "chat", "ollama", "qwen2.5:3b"

def select_engine(prompt, conversation=None):
    """Master engine selector. Returns (engine, model, intent, reason)."""
    intent, engine, model = classify_intent(prompt)

    # Override: if intent needs image/video/3d, but no GPU, use fallback
    if engine == "comfyui" and intent in ("video_gen", "three_d"):
        # No GPU yet — return graceful message instead of crash
        return engine, model, intent, "GPU_REQUIRED"

    # Override: if Kimi is not configured or key invalid, fall back to Ollama 14b
    if engine == "kimi":
        if not KIMI_API_KEY:
            return "ollama", "qwen2.5:14b", intent, "KIMI_UNAVAILABLE"
        # Quick health check - if Kimi was recently unreachable, use Ollama
        if not hasattr(select_engine, "_kimi_ok"):
            select_engine._kimi_ok = True
        if not select_engine._kimi_ok:
            return "ollama", "qwen2.5:14b", intent, "KIMI_RECENTLY_FAILED"

    # Override: if code task and deepseek not available, use qwen 7b
    if engine == "ollama" and model == "deepseek-r1:7b":  # kept for future GPU use
        # Check if model is loaded (quick check via cached list)
        if not hasattr(select_engine, "_available_models"):
            try:
                req = urllib.request.Request(f"{OLLAMA_URL}/api/tags")
                with urllib.request.urlopen(req, timeout=3) as resp:
                    select_engine._available_models = [m["name"] for m in json.loads(resp.read()).get("models", [])]
            except:
                select_engine._available_models = []
        if "deepseek-r1:7b" not in select_engine._available_models:
            return "ollama", "qwen2.5:7b", intent, "DEEPSEEK_UNAVAILABLE"

    return engine, model, intent, "OK"

def should_use_kimi(prompt, conversation):
    """Legacy compat — now uses classify_intent."""
    intent, engine, model = classify_intent(prompt)
    return engine == "kimi"


# ─── Agentic Loop (Same Logic as Oryx) ───
def agentic_loop(prompt, session_id=None, model="qwen2.5:14b", max_turns=10, on_event=None, conv_dir=None, mem_dir=None):
    """
    The main agentic loop — same logic as Oryx (Base44 Superagent).
    
    1. Load context (identity, soul, memory, conversation history)
    2. Build messages with system prompt + history + user message
    3. Send to Ollama with native tools
    4. If tool_calls returned, execute them and feed results back
    5. Continue until model returns content without tool_calls
    6. Save to conversation history
    7. Return response
    """
    # Build system prompt (same as Oryx loading IDENTITY + SOUL + memory)
    system_prompt = build_system_prompt(mem_dir=mem_dir)
    
    # Load conversation history
    history = get_conversation(session_id, conv_dir=conv_dir)
    
    # Build messages: system + history + new user message
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add conversation history (last 10 messages)
    for msg in history[-10:]:
        if msg.get("role") in ("user", "assistant") and msg.get("content"):
            messages.append({"role": msg["role"], "content": msg["content"]})
        # Skip tool messages from history (they're too large)
    
    # Add current user message
    messages.append({"role": "user", "content": prompt})
    
    # ─── Auto-Engine Selection (v8.0) ───
    sel_engine, sel_model, intent, reason = select_engine(prompt)
    tools_used = 0
    engine = f"{sel_engine} ({sel_model})"
    
    # If GPU required but not available, return graceful message
    if reason == "GPU_REQUIRED":
        gpu_msg = f"This task requires a GPU (intent: {intent}). The GEX44 GPU server is pending provisioning. Once active, this will work automatically."
        history.append({"role": "user", "content": prompt})
        history.append({"role": "assistant", "content": gpu_msg})
        save_conversation(session_id, history, conv_dir=conv_dir)
        if on_event:
            on_event("text", {"text": gpu_msg})
            on_event("done", {"response": gpu_msg, "engine": engine, "tools_used": 0, "turns": 0})
        return {"response": gpu_msg, "engine": engine, "model": sel_model, "status": "success", "turns": 0, "tools_used": 0, "intent": intent}
    
    # Use the auto-selected model (override the default)
    model = sel_model
    
    # If Kimi is selected, use it for the first turn (no tools), then switch to Ollama for tool execution
    if sel_engine == "kimi":
        if on_event:
            on_event("engine", {"engine": "Kimi", "model": sel_model, "intent": intent})
        try:
            kimi_response = call_kimi(messages, max_tokens=2000)
            # If Kimi doesn't suggest tool use, return its response directly
            if not any(kw in kimi_response.lower() for kw in ["use tool", "run command", "execute", "check server"]):
                history.append({"role": "user", "content": prompt})
                history.append({"role": "assistant", "content": kimi_response})
                save_conversation(session_id, history, conv_dir=conv_dir)
                if on_event:
                    on_event("text", {"text": kimi_response})
                    on_event("done", {"response": kimi_response, "engine": engine, "tools_used": 0, "turns": 1, "intent": intent})
                return {"response": kimi_response, "engine": engine, "model": sel_model, "status": "success", "turns": 1, "tools_used": 0, "intent": intent}
            # If Kimi suggests tools, continue with Ollama for tool execution
            messages.append({"role": "assistant", "content": kimi_response})
            model = "qwen2.5:7b"
            engine = f"Ollama ({model})"
        except Exception as e:
            if on_event:
                on_event("engine_fallback", {"from": "kimi", "to": "ollama", "reason": str(e)})
            model = "qwen2.5:7b"
            engine = f"Ollama ({model})"
    else:
        if on_event:
            on_event("engine", {"engine": sel_engine, "model": sel_model, "intent": intent})
    
    for turn in range(max_turns):
        if on_event:
            on_event("thinking", {"turn": turn + 1})
        
        # Call Ollama with native tools
        try:
            result = call_ollama_with_tools(model, messages, TOOLS, stream=False)
        except Exception as e:
            error_msg = f"Engine error: {e}"
            if on_event:
                on_event("error", {"error": str(e)})
            return {
                "response": error_msg, "engine": engine, "model": model,
                "status": "error", "turns": turn, "tools_used": tools_used,
            }
        
        assistant_msg = result.get("message", {})
        content = assistant_msg.get("content", "")
        tool_calls = assistant_msg.get("tool_calls", [])
        
        # Add assistant message to conversation
        messages.append(assistant_msg)
        
        # If there's text content, emit it
        if content and on_event:
            on_event("text", {"text": content})
        
        # If no tool calls, we're done — this is the final response
        if not tool_calls:
            # Save to conversation history
            history.append({"role": "user", "content": prompt})
            history.append({"role": "assistant", "content": content})
            save_conversation(session_id, history, conv_dir=conv_dir)
            
            if on_event:
                on_event("done", {
                    "response": content, "tools_used": tools_used,
                    "turns": turn + 1, "engine": engine
                })
            
            return {
                "response": content,
                "engine": engine,
                "model": model,
                "status": "success",
                "turns": turn + 1,
                "tools_used": tools_used,
                "intent": intent,
            }
        
        # Execute each tool call
        for tc in tool_calls:
            func = tc.get("function", {})
            tool_name = func.get("name", "")
            tool_args = func.get("arguments", {})
            tool_call_id = tc.get("id", "")
            
            tools_used += 1
            
            if on_event:
                on_event("tool_call", {"tool": tool_name, "args": tool_args})
            
            # Execute the tool
            result_text = execute_tool(tool_name, tool_args, mem_dir=mem_dir)
            
            if on_event:
                on_event("tool_result", {"tool": tool_name, "result": result_text[:300]})
            
            # Add tool result to conversation (Ollama format)
            messages.append({
                "role": "tool",
                "content": result_text,
                "name": tool_name,
            })
    
    # Max turns reached — ask for a final summary
    messages.append({
        "role": "user",
        "content": "Summarize what you've done so far and give me the final result."
    })
    
    try:
        result = call_ollama_with_tools(model, messages, [], stream=False)
        final_content = result.get("message", {}).get("content", "Task completed.")
    except:
        final_content = "Task completed."
    
    history.append({"role": "user", "content": prompt})
    history.append({"role": "assistant", "content": final_content})
    save_conversation(session_id, history)
    
    if on_event:
        on_event("done", {
            "response": final_content, "tools_used": tools_used,
            "turns": max_turns, "engine": engine
        })
    
    return {
        "response": final_content,
        "engine": engine,
        "model": model,
        "status": "success",
        "turns": max_turns,
        "tools_used": tools_used,
        "intent": intent,
    }


# ─── HTTP Server ───
class ModelAPI(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _write_chunk(self, data_bytes):
        try:
            self.wfile.write(("%x\r\n" % len(data_bytes)).encode())
            self.wfile.write(data_bytes)
            self.wfile.write(b"\r\n")
            self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            raise

    def _end_chunks(self):
        try:
            self.wfile.write(b"0\r\n\r\n")
            self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _sse(self, event, data):
        payload = f"event: {event}\ndata: {json.dumps(data)}\n\n"
        self._write_chunk(payload.encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        if self.path == "/api/health":
            self.respond(200, {
                "status": "online",
                "comfyui": self._check(COMFYUI_URL + "/system_stats"),
                "omniroute": self._check("http://127.0.0.1:20128/dashboard"),
                "ollama": self._check(OLLAMA_URL + "/api/tags"),
                "art_engine": self._check(ART_ENGINE_URL + "/api/status"),
                "models_registered": 281,
                "james_version": "8.0",
                "tools_available": len(TOOLS),
                "kimi_available": bool(KIMI_API_KEY),
                "memories_stored": len([f for f in os.listdir(MEMORY_DIR) if f.endswith(".json")]),
                "conversations": len([f for f in os.listdir(CONVERSATION_DIR) if f.endswith(".json")]) if os.path.exists(CONVERSATION_DIR) else 0,
            })

        elif self.path == "/api/models":
            try:
                req = urllib.request.Request(f"{OLLAMA_URL}/api/tags")
                with urllib.request.urlopen(req, timeout=5) as resp:
                    self.respond(200, json.loads(resp.read()))
            except:
                self.respond(200, {"models": []})

        elif self.path == "/api/templates":
            self.respond(200, [
                {"id": 1, "title": "Web Application", "desc": "Build a full-stack web app", "icon": "🌐", "category": "Code", "prompt": "Build a web app with a React frontend and Python API for a todo app"},
                {"id": 2, "title": "AI Chatbot", "desc": "Create an AI chatbot with custom personality", "icon": "🤖", "category": "AI", "prompt": "Create an AI chatbot with a friendly personality for customer support"},
                {"id": 3, "title": "Logo & Brand Design", "desc": "Generate professional logos and brand assets", "icon": "🎨", "category": "Image", "prompt": "Generate a professional logo for a tech startup"},
                {"id": 4, "title": "Data Pipeline", "desc": "Build an ETL pipeline with data processing", "icon": "📊", "category": "Code", "prompt": "Build a data pipeline that processes CSV files and generates analytics"},
                {"id": 5, "title": "Mobile App", "desc": "Design a cross-platform mobile application", "icon": "📱", "category": "Code", "prompt": "Design a mobile app for tracking fitness goals"},
                {"id": 6, "title": "AI Video", "desc": "Generate videos from text prompts", "icon": "🎬", "category": "Video", "prompt": "Generate a video about a futuristic city"},
                {"id": 7, "title": "Smart Contract", "desc": "Write and deploy blockchain contracts", "icon": "⛓️", "category": "Web3", "prompt": "Write a Solidity smart contract for a voting system"},
                {"id": 8, "title": "REST API", "desc": "Build a production REST API", "icon": "🔌", "category": "Code", "prompt": "Build a REST API with authentication, rate limiting, and OpenAPI docs"},
            ])

        elif self.path.startswith("/api/job/"):
            job_id = self.path.split("/api/job/")[1].split("?")[0]
            with JOBS_LOCK:
                job = JOBS.get(job_id, {"status": "not_found"})
            self.respond(200, job)

        elif self.path == "/api/memories":
            memories = []
            if os.path.exists(MEMORY_DIR):
                for fname in sorted(os.listdir(MEMORY_DIR)):
                    if fname.endswith(".json"):
                        try:
                            with open(os.path.join(MEMORY_DIR, fname)) as f:
                                memories.append(json.load(f))
                        except:
                            pass
            self.respond(200, memories)

        elif self.path == "/api/tools":
            self.respond(200, [{"name": t["function"]["name"], "desc": t["function"]["description"], "icon": "🔧"} for t in TOOLS])

        elif self.path == "/api/skills":
            skills = []
            if os.path.exists(SKILLS_DIR):
                for fname in os.listdir(SKILLS_DIR):
                    if fname.endswith(".sh"):
                        name = fname.replace(".sh", "")
                        try:
                            with open(os.path.join(SKILLS_DIR, fname)) as f:
                                first_line = f.readline().strip()
                                desc = first_line.replace("#", "").strip() if first_line.startswith("#") else name
                            skills.append({"name": name, "desc": desc})
                        except:
                            skills.append({"name": name, "desc": name})
            self.respond(200, skills)

        elif self.path == "/api/identity":
            self.respond(200, {
                "identity": load_identity(),
                "soul": load_soul(),
                "version": "7.0",
            })

        elif self.path == "/api/conversations":
            convos = []
            if os.path.exists(CONVERSATION_DIR):
                for fname in os.listdir(CONVERSATION_DIR):
                    if fname.endswith(".json"):
                        fpath = os.path.join(CONVERSATION_DIR, fname)
                        size = os.path.getsize(fpath)
                        convos.append({"id": fname.replace(".json", ""), "size": size, "messages": size // 200})
            self.respond(200, convos)

        else:
            self.respond(404, {"error": "Not found"})

    def do_POST(self):
        content_len = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(content_len)) if content_len > 0 else {}

        if self.path == "/api/generate/image":
            prompt = body.get("prompt", "")
            steps = body.get("steps", 15)
            job_id = _start_image_job(prompt, body.get("style", "none"), steps)
            self.respond(200, {"job_id": job_id, "status": "processing"})

        elif self.path == "/api/chat/stream":
            if not get_user_from_request(self):
                self.respond(401, {"error": "Authentication required"})
                return
            self._handle_stream_chat(body)

        elif self.path == "/api/agent/stream":
            if not get_user_from_request(self):
                self.respond(401, {"error": "Authentication required"})
                return
            self._handle_stream_agentic(body)

        elif self.path == "/api/chat":
            if not get_user_from_request(self):
                self.respond(401, {"error": "Authentication required"})
                return
            prompt = body.get("prompt", "")
            system = body.get("system", build_system_prompt())
            # Auto-engine selection for simple chat too
            sel_engine, sel_model, intent, reason = select_engine(prompt)
            model = sel_model if not body.get("model") else body.get("model")

            if sel_engine == "kimi" and reason == "OK":
                try:
                    kimi_resp = call_kimi([{"role": "system", "content": system}, {"role": "user", "content": prompt}])
                    self.respond(200, {"response": kimi_resp, "engine": f"Kimi ({sel_model})", "status": "success", "intent": intent})
                except Exception as e:
                    # Fallback to Ollama
                    model = "qwen2.5:7b"
                    sel_engine = "ollama"

            if sel_engine != "kimi" or reason != "OK":
                try:
                    req = urllib.request.Request(
                        f"{OLLAMA_URL}/api/chat",
                        data=json.dumps({"model": model, "messages": [
                            {"role": "system", "content": system},
                            {"role": "user", "content": prompt}
                        ], "stream": False}).encode(),
                        headers={"Content-Type": "application/json"}
                    )
                    timeout = 30 if model == "qwen2.5:3b" else 60 if model == "qwen2.5:7b" else 120
                    with urllib.request.urlopen(req, timeout=timeout) as resp:
                        data = json.loads(resp.read())
                        self.respond(200, {"response": data["message"]["content"], "engine": f"Ollama ({model})", "status": "success", "intent": intent})
                except Exception as e:
                    self.respond(200, {"response": f"Error: {e}", "status": "error"})

        elif self.path == "/api/agent":
            if not get_user_from_request(self):
                self.respond(401, {"error": "Authentication required"})
                return
            prompt = body.get("prompt", "")
            session_id = scoped_session_id(self, body.get("session_id", "default"))
            model = body.get("model", "qwen2.5:14b")
            u_conv = user_dir(self, CONVERSATION_DIR)
            u_mem = user_dir(self, MEMORY_DIR)
            result = agentic_loop(prompt, session_id=session_id, model=model, conv_dir=u_conv, mem_dir=u_mem)
            self.respond(200, result)

        elif self.path == "/api/memory/save":
            key = body.get("key", "")
            value = body.get("value", "")
            category = body.get("category", "General")
            if key and value:
                mem = {"key": key, "value": value, "category": category, "timestamp": datetime.now().isoformat()}
                with open(os.path.join(MEMORY_DIR, f"{key}.json"), "w") as f:
                    json.dump(mem, f)
                self.respond(200, {"status": "saved", "key": key})
            else:
                self.respond(400, {"error": "key and value required"})

        elif self.path == "/api/identity/update":
            identity = body.get("identity", "")
            soul = body.get("soul", "")
            if identity:
                with open(os.path.join(IDENTITY_DIR, "IDENTITY.md"), "w") as f:
                    f.write(identity)
            if soul:
                with open(os.path.join(IDENTITY_DIR, "SOUL.md"), "w") as f:
                    f.write(soul)
            self.respond(200, {"status": "updated"})

        else:
            self.respond(404, {"error": "Not found"})

    def _handle_stream_chat(self, body):
        """Simple streaming chat (no tools)."""
        prompt = body.get("prompt", "")
        system = body.get("system", build_system_prompt())
        # Auto-select model for streaming
        sel_engine, sel_model, intent, reason = select_engine(prompt)
        model = sel_model if not body.get("model") else body.get("model")

        # Emit engine selection event
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "close")
        self.send_header("Transfer-Encoding", "chunked")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.close_connection = True

        try:
            data = json.dumps({
                "model": model,
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
                "stream": True
            }).encode()
            req = urllib.request.Request(f"{OLLAMA_URL}/api/chat", data=data, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=120) as resp:
                for line in resp:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                        if chunk.get("message", {}).get("content"):
                            self._sse("text", {"text": chunk["message"]["content"], "done": False})
                        if chunk.get("done"):
                            self._sse("text", {"text": "", "done": True})
                    except json.JSONDecodeError:
                        continue
        except (BrokenPipeError, ConnectionResetError):
            return
        except Exception as e:
            try:
                self._sse("error", {"error": str(e)})
            except:
                return
        finally:
            self._end_chunks()

    def _handle_stream_agentic(self, body):
        """Streaming agentic chat with real-time tool-call visibility — same as Oryx."""
        prompt = body.get("prompt", "")
        session_id = scoped_session_id(self, body.get("session_id", "default"))
        model = body.get("model", "qwen2.5:14b")
        u_conv = user_dir(self, CONVERSATION_DIR)
        u_mem = user_dir(self, MEMORY_DIR)

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "close")
        self.send_header("Transfer-Encoding", "chunked")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.close_connection = True

        def on_event(event_type, data):
            try:
                self._sse(event_type, data)
            except (BrokenPipeError, ConnectionResetError):
                pass

        try:
            agentic_loop(prompt, session_id=session_id, model=model, max_turns=10, on_event=on_event, conv_dir=u_conv, mem_dir=u_mem)
        except (BrokenPipeError, ConnectionResetError):
            return
        except Exception as e:
            try:
                self._sse("error", {"error": str(e)})
            except:
                return
        finally:
            self._end_chunks()

    def _check(self, url):
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=3) as resp:
                return "online"
        except:
            return "offline"

    def respond(self, code, data):
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        try:
            self.wfile.write(body)
        except:
            pass


def _start_image_job(prompt, style, steps):
    job_id = str(uuid.uuid4())[:8]
    with JOBS_LOCK:
        JOBS[job_id] = {"status": "processing", "prompt": prompt, "created": datetime.now().isoformat(), "image": None}
    threading.Thread(target=_generate_image, args=(job_id, prompt, steps), daemon=True).start()
    return job_id


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", 5010), ModelAPI)
    print("EvolvixOS Model API v8.0 — Mr James (Oryx-class Agent)")
    print(f"  Tools: {len(TOOLS)} (native Ollama tool calling)")
    print(f"  Kimi: {'available' if KIMI_API_KEY else 'not configured'}")
    print(f"  Memory: {len(os.listdir(MEMORY_DIR)) if os.path.exists(MEMORY_DIR) else 0} memories")
    print(f"  Skills: {len([f for f in os.listdir(SKILLS_DIR) if f.endswith('.sh')]) if os.path.exists(SKILLS_DIR) else 0} skills")
    print(f"  Identity: {'loaded' if os.path.exists(os.path.join(IDENTITY_DIR, 'IDENTITY.md')) else 'not found'}")
    print(f"  Soul: {'loaded' if os.path.exists(os.path.join(IDENTITY_DIR, 'SOUL.md')) else 'not found'}")
    server.serve_forever()
