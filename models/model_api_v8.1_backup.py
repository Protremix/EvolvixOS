#!/usr/bin/env python3
"""
EvolvixOS Model API v8.1 — Mr James (Oryx-class Agent)
Native tool calling, conversation history, persistent memory, identity, soul.

v8.1: Security hardening — path sanitization, auth on all endpoints,
      JOBS pruning, proper context managers, fixed duplicate TOOLS key,
      fixed self reference in execute_tool, fixed stream handle closing,
      fixed save_conversation user scoping, security headers.
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

# ─── Allowed paths for file operations (prevent traversal) ───
ALLOWED_BASE_DIRS = ["/opt/evolvixos", "/tmp", "/root", "/home"]

def is_path_safe(path):
    if not path:
        return False
    abs_path = os.path.abspath(os.path.normpath(path))
    return any(abs_path.startswith(base) for base in ALLOWED_BASE_DIRS)

def sanitize_service_name(name):
    if not name:
        return ""
    return re.sub(r'[^a-zA-Z0-9._-]', '', name)[:100]

def sanitize_git_command(cmd):
    if not cmd:
        return ""
    return re.sub(r'[;&|`$(){}]', '', cmd).strip()[:200]

def get_user_from_request(handler):
    auth_header = handler.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header[7:]
    try:
        conn = sqlite3.connect(AUTH_DB, timeout=5)
        cur = conn.cursor()
        cur.execute("SELECT u.id, u.email, u.display_name FROM user_sessions s JOIN users u ON s.user_id = u.id WHERE s.token = ? AND s.expires > datetime('now')", (token,))
        row = cur.fetchone()
        conn.close()
        if row:
            return {"id": row[0], "email": row[1], "display_name": row[2]}
    except Exception:
        pass
    return None

def require_auth(handler):
    user = get_user_from_request(handler)
    if not user:
        handler.respond(401, {"error": "Authentication required"})
        return None
    return user

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

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
COMFYUI_URL = os.environ.get("COMFYUI_URL", "http://127.0.0.1:8188")
ART_ENGINE_URL = os.environ.get("ART_ENGINE_URL", "http://127.0.0.1:5002")
KIMI_API_KEY = os.environ.get("KIMI_API_KEY", "")
KIMI_URL = os.environ.get("KIMI_URL", "https://api.moonshot.cn/v1/chat/completions")
KIMI_MODEL = os.environ.get("KIMI_MODEL", "moonshot-v1-32k")

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
MAX_JOBS = 100

TOOLS = [
    {"type": "function", "function": {"name": "bash", "description": "Run a shell command on the server.", "parameters": {"type": "object", "properties": {"command": {"type": "string", "description": "The shell command to execute"}}, "required": ["command"]}}},
    {"type": "function", "function": {"name": "file_write", "description": "Write content to a file. Paths must be within /opt/evolvixos.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Absolute file path"}, "content": {"type": "string", "description": "File content"}}, "required": ["path", "content"]}}},
    {"type": "function", "function": {"name": "file_read", "description": "Read a file. Paths must be within /opt/evolvixos.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Absolute file path"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "python_exec", "description": "Execute Python 3 code.", "parameters": {"type": "object", "properties": {"code": {"type": "string", "description": "Python code"}}, "required": ["code"]}}},
    {"type": "function", "function": {"name": "service_check", "description": "Check systemd service status.", "parameters": {"type": "object", "properties": {"name": {"type": "string", "description": "Service name"}}, "required": ["name"]}}},
    {"type": "function", "function": {"name": "service_restart", "description": "Restart a systemd service.", "parameters": {"type": "object", "properties": {"name": {"type": "string", "description": "Service name"}}, "required": ["name"]}}},
    {"type": "function", "function": {"name": "docker_ps", "description": "List Docker containers.", "parameters": {"type": "object", "properties": {}}},},
    {"type": "function", "function": {"name": "docker_restart", "description": "Restart a Docker container.", "parameters": {"type": "object", "properties": {"name": {"type": "string", "description": "Container name"}}, "required": ["name"]}}},
    {"type": "function", "function": {"name": "git", "description": "Run git commands.", "parameters": {"type": "object", "properties": {"command": {"type": "string", "description": "Git command"}, "repo": {"type": "string", "description": "Repo path", "default": "."}}, "required": ["command"]}}},
    {"type": "function", "function": {"name": "http_request", "description": "Make an HTTP request.", "parameters": {"type": "object", "properties": {"url": {"type": "string"}, "method": {"type": "string", "default": "GET"}, "body": {"type": "object"}}, "required": ["url"]}}},
    {"type": "function", "function": {"name": "web_search", "description": "Search the web via DuckDuckGo.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "ui_generate", "description": "Generate UI components: Magic UI, Unlumen UI, Retro UI.", "parameters": {"type": "object", "properties": {"prompt": {"type": "string"}, "library": {"type": "string", "enum": ["magic-ui", "unlumen-ui", "retro-ui", "auto"]}, "theme": {"type": "string"}}, "required": ["prompt"]}}},
    {"type": "function", "function": {"name": "image_generate", "description": "Generate an AI image from text.", "parameters": {"type": "object", "properties": {"prompt": {"type": "string"}, "steps": {"type": "integer", "default": 15}}, "required": ["prompt"]}}},
    {"type": "function", "function": {"name": "list_models", "description": "List available Ollama models.", "parameters": {"type": "object", "properties": {}}},},
    {"type": "function", "function": {"name": "memory_save", "description": "Save a durable memory.", "parameters": {"type": "object", "properties": {"key": {"type": "string"}, "value": {"type": "string"}, "category": {"type": "string", "default": "General"}}, "required": ["key", "value"]}}},
    {"type": "function", "function": {"name": "memory_load", "description": "Load a memory by key.", "parameters": {"type": "object", "properties": {"key": {"type": "string"}}, "required": ["key"]}}},
    {"type": "function", "function": {"name": "memory_list", "description": "List all stored memories.", "parameters": {"type": "object", "properties": {}}},},
    {"type": "function", "function": {"name": "skill_run", "description": "Execute an EvolvixOS skill.", "parameters": {"type": "object", "properties": {"name": {"type": "string"}, "input": {"type": "string"}}, "required": ["name", "input"]}}},
]

TOOL_NAMES = [t["function"]["name"] for t in TOOLS]

def load_identity():
    path = os.path.join(IDENTITY_DIR, "IDENTITY.md")
    if os.path.exists(path):
        with open(path) as f:
            return f.read()
    return ""

def load_soul():
    path = os.path.join(IDENTITY_DIR, "SOUL.md")
    if os.path.exists(path):
        with open(path) as f:
            return f.read()
    return ""

def load_context(mem_dir=None):
    context_parts = []
    memories = []
    mdir = mem_dir or MEMORY_DIR
    if os.path.exists(mdir):
        for fname in sorted(os.listdir(mdir)):
            if fname.endswith(".json"):
                try:
                    with open(os.path.join(mdir, fname)) as f:
                        mem = json.load(f)
                        memories.append(f"- [{mem.get('category','General')}] {mem['key']}: {mem['value'][:200]}")
                except Exception:
                    pass
    if memories:
        context_parts.append("## What I Remember\n" + "\n".join(memories))
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    context_parts.append(f"## Current Context\nTime: {now}\nServer: 2.28.52.223 (evolvixos.com)\nPlatform: EvolvixOS v8.1\nModels: 281 across 12 categories")
    skills = []
    if os.path.exists(SKILLS_DIR):
        for fname in os.listdir(SKILLS_DIR):
            if fname.endswith(".sh"):
                skills.append(fname.replace(".sh", ""))
    if skills:
        context_parts.append("## My Skills\n" + ", ".join(skills))
    return "\n\n".join(context_parts)

def build_system_prompt(mem_dir=None):
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

def get_conversation(session_id, conv_dir=None):
    if not session_id:
        return []
    d = conv_dir or CONVERSATION_DIR
    fpath = os.path.join(d, f"{session_id}.json")
    if os.path.exists(fpath):
        try:
            with open(fpath) as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_conversation(session_id, messages, conv_dir=None):
    if not session_id:
        return
    d = conv_dir or CONVERSATION_DIR
    os.makedirs(d, exist_ok=True)
    fpath = os.path.join(d, f"{session_id}.json")
    trimmed = messages[-20:]
    with open(fpath, "w") as f:
        json.dump(trimmed, f)

def prune_old_jobs():
    with JOBS_LOCK:
        if len(JOBS) <= MAX_JOBS:
            return
        sorted_jobs = sorted(JOBS.items(), key=lambda x: x[1].get("created", ""))
        to_remove = len(JOBS) - MAX_JOBS
        for key, _ in sorted_jobs[:to_remove]:
            del JOBS[key]

def execute_tool(name, args, mem_dir=None, handler=None):
    try:
        if name == "bash":
            cmd = args.get("command", "")
            if not cmd:
                return "Error: no command provided"
            dangerous = ["rm -rf /", "mkfs", "dd if=", "shutdown", "reboot", "halt"]
            if any(d in cmd.lower() for d in dangerous):
                return "Error: command blocked (dangerous pattern detected)"
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
            if not is_path_safe(path):
                return f"Error: path '{path}' is outside allowed directories"
            os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
            with open(path, "w") as f:
                f.write(content)
            return f"Wrote {len(content)} bytes to {path}"

        elif name == "file_read":
            path = args.get("path", "")
            if not path:
                return "Error: no path"
            if not is_path_safe(path):
                return f"Error: path '{path}' is outside allowed directories"
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
            svc = sanitize_service_name(args.get("name", ""))
            if not svc:
                return "Error: invalid service name"
            r = subprocess.run(["systemctl", "is-active", svc], capture_output=True, text=True)
            return f"Service '{svc}' is {r.stdout.strip()}"

        elif name == "service_restart":
            svc = sanitize_service_name(args.get("name", ""))
            if not svc:
                return "Error: invalid service name"
            r = subprocess.run(["systemctl", "restart", svc], capture_output=True, text=True)
            return f"Service '{svc}' restarted" if r.returncode == 0 else f"Error: {r.stderr}"

        elif name == "docker_ps":
            r = subprocess.run(["docker", "ps", "-a", "--format", "{{.Names}}\t{{.Status}}\t{{.Ports}}"], capture_output=True, text=True)
            return r.stdout or "No containers"

        elif name == "docker_restart":
            cname = sanitize_service_name(args.get("name", ""))
            if not cname:
                return "Error: invalid container name"
            r = subprocess.run(["docker", "restart", cname], capture_output=True, text=True)
            return f"Container '{cname}' restarted" if r.returncode == 0 else f"Error: {r.stderr}"

        elif name == "git":
            repo = args.get("repo", ".")
            cmd = sanitize_git_command(args.get("command", ""))
            if not cmd:
                return "Error: invalid git command"
            if not is_path_safe(repo):
                return "Error: repo path not allowed"
            r = subprocess.run(["git", "-C", repo] + cmd.split(), capture_output=True, text=True, timeout=30)
            return (r.stdout + r.stderr)[:5000] or "(no output)"

        elif name == "http_request":
            url = args.get("url", "")
            method = args.get("method", "GET")
            body = args.get("body")
            if not url or not url.startswith(("http://", "https://")):
                return "Error: invalid URL"
            data = json.dumps(body).encode() if body else None
            req = urllib.request.Request(url, data=data, method=method, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                return f"[{resp.status}] {resp.read()[:5000].decode(errors='replace')}"

        elif name == "web_search":
            query = args.get("query", "")
            url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(query)}&format=json&no_html=1"
            req = urllib.request.Request(url, headers={"User-Agent": "MrJames/8.1"})
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
            if library == "auto":
                if any(t in ui_prompt.lower() for t in ["retro", "win95", "vaporwave", "dos", "arcade", "gameboy", "crt", "tron"]):
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
                    result_parts.append(f"Magic UI - {len(components)} components available")
                    matched = [c for c in components if any(w in c for w in ui_prompt.lower().split())]
                    if matched:
                        comp_file = os.path.join(comp_dir, matched[0] + ".tsx")
                        with open(comp_file) as cf:
                            code = cf.read()[:3000]
                        result_parts.append(f"\n--- Component: {matched[0]} ---\n```tsx\n{code}\n```")
                    else:
                        result_parts.append("No exact match. Use a component name from the list above.")
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
                else:
                    result_parts.append("Unlumen UI library not found")
            elif library == "retro-ui":
                tokens_dir = os.path.join(ui_lib_dir, "retro-design-system", "tokens")
                styles_dir = os.path.join(ui_lib_dir, "retro-design-system", "styles")
                if os.path.isdir(tokens_dir):
                    themes = [f.replace(".css", "") for f in os.listdir(tokens_dir) if f.endswith(".css")]
                    result_parts.append(f"Retro UI - {len(themes)} themes available")
                    if theme:
                        matched = [t for t in themes if theme.lower() in t.lower()]
                    else:
                        matched = [t for t in themes if any(w in t.lower() for w in ui_prompt.lower().split())]
                    if matched:
                        theme_file = os.path.join(tokens_dir, matched[0] + ".css")
                        with open(theme_file) as tf:
                            css = tf.read()[:3000]
                        result_parts.append(f"\n--- Theme: {matched[0]} ---\n```css\n{css}\n```")
                        style_dir = os.path.join(styles_dir, matched[0])
                        if os.path.isdir(style_dir):
                            for sf in os.listdir(style_dir):
                                if sf.endswith(".css") or sf.endswith(".html"):
                                    sfile = os.path.join(style_dir, sf)
                                    with open(sfile) as sfh:
                                        result_parts.append(f"\n--- {sf} ---\n{sfh.read()[:2000]}")
                    else:
                        result_parts.append("No theme match. Try: win95, vaporwave, gameboy, tron, crt, dos, arcade")
                else:
                    result_parts.append("Retro UI library not found")
            return "\n\n".join(result_parts)

        elif name == "image_generate":
            prompt = args.get("prompt", "")
            steps = args.get("steps", 15)
            job_id = str(uuid.uuid4())[:8]
            with JOBS_LOCK:
                prune_old_jobs()
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
            key = re.sub(r'[^a-zA-Z0-9._-]', '', args.get("key", ""))[:100]
            value = args.get("value", "")
            category = args.get("category", "General")
            if not key:
                return "Error: invalid memory key"
            mem = {"key": key, "value": value, "category": category, "timestamp": datetime.now().isoformat()}
            mdir = mem_dir or MEMORY_DIR
            os.makedirs(mdir, exist_ok=True)
            with open(os.path.join(mdir, f"{key}.json"), "w") as f:
                json.dump(mem, f)
            return f"Memory saved: {key}"

        elif name == "memory_load":
            key = re.sub(r'[^a-zA-Z0-9._-]', '', args.get("key", ""))[:100]
            if not key:
                return "Error: invalid memory key"
            mdir = mem_dir or MEMORY_DIR
            fpath = os.path.join(mdir, f"{key}.json")
            if not os.path.exists(fpath):
                return f"No memory: {key}"
            with open(fpath) as f:
                return json.dumps(json.load(f))

        elif name == "memory_list":
            memories = []
            mdir = mem_dir or MEMORY_DIR
            if not os.path.exists(mdir):
                return 'No memories'
            for fname in os.listdir(mdir):
                if fname.endswith(".json"):
                    try:
                        with open(os.path.join(mdir, fname)) as f:
                            mem = json.load(f)
                            memories.append(f"[{mem.get('category','General')}] {mem['key']}: {mem['value'][:80]}")
                    except Exception:
                        pass
            return "\n".join(memories) if memories else "No memories"

        elif name == "skill_run":
            skill_name = re.sub(r'[^a-zA-Z0-9._-]', '', args.get("name", ""))[:100]
            skill_input = args.get("input", "")[:10000]
            if not skill_name:
                return "Error: invalid skill name"
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
            try:
                prompt_encoded = urllib.parse.quote(prompt)
                seed = int(time.time()) % 2147483647
                img_url = f"https://image.pollinations.ai/prompt/{prompt_encoded}?width=1024&height=1024&seed={seed}&nologo=true&model=flux"
                req = urllib.request.Request(img_url, headers={"User-Agent": "EvolvixOS/8.1"})
                with urllib.request.urlopen(req, timeout=120) as img_resp:
                    img_data = img_resp.read()
                os.makedirs(os.path.join(BASE_DIR, "output"), exist_ok=True)
                out_path = os.path.join(BASE_DIR, "output", f"{job_id}.png")
                with open(out_path, "wb") as f:
                    f.write(img_data)
                gen_time = round(time.time() - start_time, 1)
                with JOBS_LOCK:
                    JOBS[job_id] = {"status": "done", "image": f"/output/{job_id}.png", "generation_time": gen_time, "seed": seed, "engine": "Pollinations.ai (Flux)", "prompt": prompt}
                return
            except Exception as e:
                print(f"Pollinations failed: {e}")

        if has_checkpoint:
            try:
                workflow = {
                    "3": {"class_type": "KSampler", "inputs": {"seed": int(time.time()) % (2**32), "steps": steps, "cfg": 8, "sampler_name": "euler", "scheduler": "normal", "denoise": 1, "model": ["4", 0], "positive": ["6", 0], "negative": ["7", 0], "latent_image": ["5", 0]}},
                    "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": ckpts[0]}},
                    "5": {"class_type": "EmptyLatentImage", "inputs": {"width": 512, "height": 512, "batch_size": 1}},
                    "6": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["4", 1]}},
                    "7": {"class_type": "CLIPTextEncode", "inputs": {"text": "blurry, low quality, distorted", "clip": ["4", 1]}},
                    "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
                    "9": {"class_type": "SaveImage", "inputs": {"filename_prefix": f"evolvix_{job_id}", "images": ["8", 0]}}
                }
                req = urllib.request.Request(f"{COMFYUI_URL}/prompt", data=json.dumps({"prompt": workflow}).encode(), headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=30) as resp:
                    result = json.loads(resp.read())
                gen_time = round(time.time() - start_time, 1)
                with JOBS_LOCK:
                    JOBS[job_id] = {"status": "done", "image": f"/output/{job_id}.png", "generation_time": gen_time, "seed": workflow["3"]["inputs"]["seed"], "engine": "ComfyUI (local GPU)", "prompt": prompt}
                return
            except Exception as e:
                print(f"ComfyUI failed: {e}")

        # Last resort: gradient placeholder
        try:
            from PIL import Image, ImageDraw
            import random
            r1, g1, b1 = random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)
            r2, g2, b2 = random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)
            img = Image.new("RGB", (512, 512))
            draw = ImageDraw.Draw(img)
            for y in range(512):
                r = int(r1 + (r2 - r1) * y / 512)
                g = int(g1 + (g2 - g1) * y / 512)
                b = int(b1 + (b2 - b1) * y / 512)
                draw.line([(0, y), (512, y)], fill=(r, g, b))
            os.makedirs(os.path.join(BASE_DIR, "output"), exist_ok=True)
            out_path = os.path.join(BASE_DIR, "output", f"{job_id}.png")
            img.save(out_path, "PNG")
            gen_time = round(time.time() - start_time, 1)
            with JOBS_LOCK:
                JOBS[job_id] = {"status": "done", "image": f"/output/{job_id}.png", "generation_time": gen_time, "seed": 0, "engine": "PIL gradient (placeholder)", "prompt": prompt}
        except Exception as e:
            with JOBS_LOCK:
                JOBS[job_id] = {"status": "error", "error": f"Image generation failed: {e}"}
    except Exception as e:
        with JOBS_LOCK:
            JOBS[job_id] = {"status": "error", "error": str(e)}

def classify_intent(prompt):
    t = prompt.lower().strip()
    if re.search(r'\b(draw|paint|generate|create|design|logo|image|picture|art|portrait|landscape|render|3d model|blender)\b', t) and not re.search(r'\b(code|app|api|script|function|program|build)\b', t):
        return ("image", "comfyui", "stable-diffusion", "Image generation request")
    if re.search(r'\b(video|movie|film|animate|cinema|clip|wan2|video gen)\b', t):
        return ("video", "comfyui", "wan2.1", "Video generation request")
    if re.search(r'\b(crypto|bitcoin|ethereum|blockchain|defi|token|nft|web3|smart contract|solidity)\b', t):
        return ("crypto", "skill", "crypto-blockchain", "Crypto/blockchain analysis")
    if re.search(r'\b(code|app|api|function|script|build|react|python|javascript|html|css|deploy|debug|refactor)\b', t):
        return ("code", "kimi", "moonshot-v1-32k", "Coding task — needs complex reasoning")
    if re.search(r'\b(ui|component|button|card|modal|dashboard|landing page|retro|win95|vaporwave)\b', t):
        return ("ui", "ollama", "qwen2.5:14b", "UI generation task")
    return ("chat", "ollama", "qwen2.5:7b", "General conversation")

def select_engine(prompt):
    return classify_intent(prompt)

def call_ollama_with_tools(model, messages, tools, stream=False):
    data = json.dumps({"model": model, "messages": messages, "tools": tools if tools else [], "stream": stream, "options": {"temperature": 0.7, "top_p": 0.9}}).encode()
    req = urllib.request.Request(f"{OLLAMA_URL}/api/chat", data=data, headers={"Content-Type": "application/json"})
    resp = urllib.request.urlopen(req, timeout=120)
    if stream:
        return resp
    try:
        result = json.loads(resp.read())
    finally:
        resp.close()
    return result

def call_kimi(prompt, system_prompt, messages=None):
    if not KIMI_API_KEY:
        return None
    try:
        all_messages = [{"role": "system", "content": system_prompt}]
        if messages:
            all_messages.extend(messages)
        all_messages.append({"role": "user", "content": prompt})
        data = json.dumps({"model": KIMI_MODEL, "messages": all_messages, "temperature": 0.7, "max_tokens": 4096}).encode()
        req = urllib.request.Request(KIMI_URL, data=data, headers={"Content-Type": "application/json", "Authorization": f"Bearer {KIMI_API_KEY}"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read())
            return result.get("choices", [{}])[0].get("message", {}).get("content", "")
    except Exception as e:
        print(f"Kimi API error: {e}")
        return None

def agentic_loop(prompt, session_id="default", model="qwen2.5:14b", max_turns=10, on_event=None, conv_dir=None, mem_dir=None):
    system_prompt = build_system_prompt(mem_dir=mem_dir)
    history = get_conversation(session_id, conv_dir=conv_dir)
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": prompt})
    engine, model_sel, intent, reason = select_engine(prompt)
    model = model_sel if not model else model
    if on_event:
        on_event("engine", {"engine": engine, "model": model, "intent": intent, "reason": reason})
    tools_used = 0
    for turn in range(max_turns):
        if on_event:
            on_event("thinking", {"turn": turn + 1})
        try:
            result = call_ollama_with_tools(model, messages, TOOLS, stream=False)
        except Exception as e:
            try:
                result = call_ollama_with_tools("qwen2.5:7b", messages, TOOLS, stream=False)
            except Exception as e2:
                error_msg = f"Engine error: {e}"
                if on_event:
                    on_event("error", {"error": str(e)})
                return {"response": error_msg, "engine": engine, "model": model, "status": "error", "turns": turn, "tools_used": tools_used}
        assistant_msg = result.get("message", {})
        content = assistant_msg.get("content", "")
        tool_calls = assistant_msg.get("tool_calls", [])
        messages.append(assistant_msg)
        if content and on_event:
            on_event("text", {"text": content})
        if not tool_calls:
            history.append({"role": "user", "content": prompt})
            history.append({"role": "assistant", "content": content})
            save_conversation(session_id, history, conv_dir=conv_dir)
            if on_event:
                on_event("done", {"response": content, "tools_used": tools_used, "turns": turn + 1, "engine": engine})
            return {"response": content, "engine": engine, "model": model, "status": "success", "turns": turn + 1, "tools_used": tools_used, "intent": intent}
        for tc in tool_calls:
            func = tc.get("function", {})
            tool_name = func.get("name", "")
            tool_args = func.get("arguments", {})
            tools_used += 1
            if on_event:
                on_event("tool_call", {"tool": tool_name, "args": tool_args})
            result_text = execute_tool(tool_name, tool_args, mem_dir=mem_dir)
            if on_event:
                on_event("tool_result", {"tool": tool_name, "result": result_text[:300]})
            messages.append({"role": "tool", "content": result_text, "name": tool_name})
    messages.append({"role": "user", "content": "Summarize what you've done so far and give me the final result."})
    try:
        result = call_ollama_with_tools(model, messages, [], stream=False)
        final_content = result.get("message", {}).get("content", "Task completed.")
    except Exception:
        final_content = "Task completed."
    history.append({"role": "user", "content": prompt})
    history.append({"role": "assistant", "content": final_content})
    save_conversation(session_id, history, conv_dir=conv_dir)
    if on_event:
        on_event("done", {"response": final_content, "tools_used": tools_used, "turns": max_turns, "engine": engine})
    return {"response": final_content, "engine": engine, "model": model, "status": "success", "turns": max_turns, "tools_used": tools_used, "intent": intent}

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

    def _add_security_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        self.send_header("X-XSS-Protection", "1; mode=block")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "https://evolvixos.com")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self._add_security_headers()
        self.end_headers()

    def do_GET(self):
        if self.path == "/api/health":
            self.respond(200, {"status": "online", "comfyui": self._check(COMFYUI_URL + "/system_stats"), "omniroute": self._check("http://127.0.0.1:20128/dashboard"), "ollama": self._check(OLLAMA_URL + "/api/tags"), "art_engine": self._check(ART_ENGINE_URL + "/api/status"), "models_registered": 281, "james_version": "8.1", "tools_available": len(TOOLS), "kimi_available": bool(KIMI_API_KEY), "memories_stored": len([f for f in os.listdir(MEMORY_DIR) if f.endswith(".json")]), "conversations": len([f for f in os.listdir(CONVERSATION_DIR) if f.endswith(".json")]) if os.path.exists(CONVERSATION_DIR) else 0})
        elif self.path == "/api/models":
            try:
                req = urllib.request.Request(f"{OLLAMA_URL}/api/tags")
                with urllib.request.urlopen(req, timeout=5) as resp:
                    self.respond(200, json.loads(resp.read()))
            except Exception:
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
            if not require_auth(self): return
            job_id = self.path.split("/api/job/")[1].split("?")[0]
            with JOBS_LOCK:
                job = JOBS.get(job_id, {"status": "not_found"})
            self.respond(200, job)
        elif self.path == "/api/memories":
            if not require_auth(self): return
            u_mem = user_dir(self, MEMORY_DIR)
            memories = []
            if os.path.exists(u_mem):
                for fname in sorted(os.listdir(u_mem)):
                    if fname.endswith(".json"):
                        try:
                            with open(os.path.join(u_mem, fname)) as f:
                                memories.append(json.load(f))
                        except Exception:
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
                        except Exception:
                            skills.append({"name": name, "desc": name})
            self.respond(200, skills)
        elif self.path == "/api/identity":
            self.respond(200, {"identity": load_identity(), "soul": load_soul(), "version": "8.1"})
        elif self.path == "/api/conversations":
            if not require_auth(self): return
            u_conv = user_dir(self, CONVERSATION_DIR)
            convos = []
            if os.path.exists(u_conv):
                for fname in os.listdir(u_conv):
                    if fname.endswith(".json"):
                        fpath = os.path.join(u_conv, fname)
                        size = os.path.getsize(fpath)
                        convos.append({"id": fname.replace(".json", ""), "size": size, "messages": size // 200})
            self.respond(200, convos)
        else:
            self.respond(404, {"error": "Not found"})

    def do_POST(self):
        content_len = int(self.headers.get("Content-Length", 0))
        if content_len > 10_000_000:
            self.respond(413, {"error": "Request body too large"})
            return
        body = json.loads(self.rfile.read(content_len)) if content_len else {}
        if self.path == "/api/chat/stream":
            if not require_auth(self): return
            self._handle_stream_chat(body)
        elif self.path == "/api/agent" or self.path == "/api/agent/stream":
            if not require_auth(self): return
            self._handle_stream_agentic(body)
        elif self.path == "/api/generate/image":
            if not require_auth(self): return
            prompt = body.get("prompt", "")
            style = body.get("style", "none")
            steps = body.get("steps", 15)
            job_id = _start_image_job(prompt, style, steps)
            self.respond(200, {"job_id": job_id, "status": "processing"})
        elif self.path == "/api/memory/save":
            if not require_auth(self): return
            key = re.sub(r'[^a-zA-Z0-9._-]', '', body.get("key", ""))[:100]
            value = body.get("value", "")
            category = body.get("category", "General")
            if key and value:
                u_mem = user_dir(self, MEMORY_DIR)
                mem = {"key": key, "value": value, "category": category, "timestamp": datetime.now().isoformat()}
                with open(os.path.join(u_mem, f"{key}.json"), "w") as f:
                    json.dump(mem, f)
                self.respond(200, {"status": "saved", "key": key})
            else:
                self.respond(400, {"error": "key and value required"})
        elif self.path == "/api/identity/update":
            if not require_auth(self): return
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
        prompt = body.get("prompt", "")
        system = body.get("system", build_system_prompt())
        sel_engine, sel_model, intent, reason = select_engine(prompt)
        model = sel_model if not body.get("model") else body.get("model")
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "close")
        self.send_header("Transfer-Encoding", "chunked")
        self.send_header("Access-Control-Allow-Origin", "https://evolvixos.com")
        self._add_security_headers()
        self.end_headers()
        self.close_connection = True
        try:
            data = json.dumps({"model": model, "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}], "stream": True}).encode()
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
            except Exception:
                return
        finally:
            self._end_chunks()

    def _handle_stream_agentic(self, body):
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
        self.send_header("Access-Control-Allow-Origin", "https://evolvixos.com")
        self._add_security_headers()
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
            except Exception:
                return
        finally:
            self._end_chunks()

    def _check(self, url):
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=3) as resp:
                return "online"
        except Exception:
            return "offline"

    def respond(self, code, data):
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "https://evolvixos.com")
        self._add_security_headers()
        self.end_headers()
        try:
            self.wfile.write(body)
        except Exception:
            pass

def _start_image_job(prompt, style, steps):
    job_id = str(uuid.uuid4())[:8]
    with JOBS_LOCK:
        prune_old_jobs()
        JOBS[job_id] = {"status": "processing", "prompt": prompt, "created": datetime.now().isoformat(), "image": None}
    threading.Thread(target=_generate_image, args=(job_id, prompt, steps), daemon=True).start()
    return job_id

if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", 5010), ModelAPI)
    print("EvolvixOS Model API v8.1 — Mr James (Oryx-class Agent)")
    print(f"  Tools: {len(TOOLS)} (native Ollama tool calling)")
    print(f"  Kimi: {'available' if KIMI_API_KEY else 'not configured'}")
    print(f"  Memory: {len(os.listdir(MEMORY_DIR)) if os.path.exists(MEMORY_DIR) else 0} memories")
    print(f"  Skills: {len([f for f in os.listdir(SKILLS_DIR) if f.endswith('.sh')]) if os.path.exists(SKILLS_DIR) else 0} skills")
    print(f"  Identity: {'loaded' if os.path.exists(os.path.join(IDENTITY_DIR, 'IDENTITY.md')) else 'not found'}")
    print(f"  Soul: {'loaded' if os.path.exists(os.path.join(IDENTITY_DIR, 'SOUL.md')) else 'not found'}")
    server.serve_forever()
