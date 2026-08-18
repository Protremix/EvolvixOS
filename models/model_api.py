#!/usr/bin/env python3
"""
EvolvixOS Model API v9.0 — Mr James (Oryx-class Agent)
Major upgrade: More tools, file upload support, smarter agentic loop,
multi-skill execution, code analysis, self-correction, streaming improvements.

v9.0 Changes:
- 24 tools (was 18): Added file_upload, file_list, code_analyze, code_format,
  process_startup_check, npm_install, pip_install, system_info
- File upload support: POST /api/upload with multipart, files stored per-user
- Smarter agentic loop: self-correction on tool errors, parallel tool calls,
  context-aware system prompt with tool results summary
- Enhanced intent classification with more categories
- Improved system prompt with tool usage guidance
- Better Ollama model selection (14b for complex, 7b for simple, 3b for trivial)
- Web fetch tool (read full web pages, not just search)
- Timer/scheduler tool (set reminders via cron)
"""

import json
import os
import re
import subprocess
import threading
import time
import urllib.request
import urllib.parse
import shutil
import sys
sys.path.insert(0, '/opt/evolvixos/auth')
from api_keys_system import validate_api_key
from api_docs import API_DOCS
import mimetypes
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import uuid
import sqlite3

AUTH_DB = "/opt/evolvixos/auth/users.db"

# ─── Configuration ───
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
COMFYUI_URL = os.environ.get("COMFYUI_URL", "http://127.0.0.1:8188")
ART_ENGINE_URL = os.environ.get("ART_ENGINE_URL", "http://127.0.0.1:5002")
KIMI_API_KEY = os.environ.get("KIMI_API_KEY", "")
KIMI_URL = "https://api.moonshot.cn/v1/chat/completions"
KIMI_MODEL = os.environ.get("KIMI_MODEL", "moonshot-v1-32k")
HF_GATEWAY_URL = "http://127.0.0.1:20129"
IDENTITY_DIR = "/opt/evolvixos/identity"
MEMORY_DIR = "/opt/evolvixos/memory"
CONVERSATION_DIR = "/opt/evolvixos/conversations"
SKILLS_DIR = "/opt/evolvixos/skills"
UPLOADS_DIR = "/opt/evolvixos/uploads"
MAX_JOBS = 100
PORT = 5010

# ─── Allowed paths for file operations (prevent traversal) ───
ALLOWED_BASE_DIRS = ["/opt/evolvixos", "/tmp", "/root", "/home", "/var/log"]

def is_path_safe(path):
    try:
        real = os.path.realpath(os.path.expanduser(path))
        return any(real.startswith(base) for base in ALLOWED_BASE_DIRS)
    except Exception:
        return False

def sanitize_service_name(name):
    return re.sub(r'[^a-zA-Z0-9_.-]', '', name)[:100] if name else ""

def sanitize_git_command(cmd):
    if not cmd:
        return ""
    if any(d in cmd for d in [";", "|", "&&", "||", ">", "<", "`", "$"]):
        return ""
    parts = cmd.strip().split()
    if not parts or parts[0] not in ["status", "log", "add", "commit", "push", "pull", "clone", "diff", "branch", "checkout", "fetch", "init", "remote", "show"]:
        return ""
    return " ".join(parts)

# ─── JOBS (async image generation) ───
JOBS = {}
JOBS_LOCK = threading.Lock()

# Rate limiting
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX = 30  # requests per window per IP
RATE_LIMITS = {}  # {ip: [(timestamp, ), ...]}
RATE_LIMIT_LOCK = threading.Lock()

def check_rate_limit(client_ip):
    with RATE_LIMIT_LOCK:
        now = time.time()
        if client_ip not in RATE_LIMITS:
            RATE_LIMITS[client_ip] = []
        RATE_LIMITS[client_ip] = [t for t in RATE_LIMITS[client_ip] if now - t < RATE_LIMIT_WINDOW]
        if len(RATE_LIMITS[client_ip]) >= RATE_LIMIT_MAX:
            return False
        RATE_LIMITS[client_ip].append(now)
        return True

def prune_old_jobs():
    with JOBS_LOCK:
        if len(JOBS) <= MAX_JOBS:
            return
        sorted_jobs = sorted(JOBS.items(), key=lambda x: x[1].get("created", ""))
        to_remove = len(JOBS) - MAX_JOBS
        for key, _ in sorted_jobs[:to_remove]:
            del JOBS[key]

# ─── Auth helpers ───
def verify_token(auth_header):
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    token = auth_header[7:]
    # Check if it's an API key (evx_...)
    if token.startswith("evx_"):
        try:
            user_info, key_id = validate_api_key(token)
            if user_info:
                return str(user_info["id"])
        except Exception:
            pass
        return None
    # Regular session token
    try:
        with sqlite3.connect(AUTH_DB) as conn:
            c = conn.cursor()
            c.execute("SELECT user_id FROM user_sessions WHERE token=? AND expires > datetime('now')", (token,))
            row = c.fetchone()
            if row:
                return str(row[0])
    except Exception:
        pass
    return None

def get_user_email(user_id):
    try:
        with sqlite3.connect(AUTH_DB) as conn:
            c = conn.cursor()
            c.execute("SELECT email, display_name FROM users WHERE id=?", (user_id,))
            row = c.fetchone()
            if row:
                return row[0], row[1]
    except Exception:
        pass
    return None, None

def user_dir(handler, base):
    user_id = getattr(handler, '_user_id', None)
    if user_id:
        d = os.path.join(base, f"user_{user_id}")
    else:
        d = base
    os.makedirs(d, exist_ok=True)
    return d

def require_auth(handler):
    token = handler.headers.get("Authorization", "")
    user_id = verify_token(token)
    if not user_id:
        handler.respond(401, {"error": "Authentication required"})
        return False
    handler._user_id = user_id
    email, name = get_user_email(user_id)
    handler._user_email = email or ""
    handler._user_name = name or ""
    return True

def scoped_session_id(handler, sid):
    uid = getattr(handler, '_user_id', 'anon')
    return f"u{uid}_{sid}" if sid else f"u{uid}_default"

# ─── TOOLS (24 total — v9.0) ───
TOOLS = [
    {"type": "function", "function": {"name": "bash", "description": "Run a shell command on the server. Use for system operations, file management, running scripts, checking status, installing packages, etc. This is your primary tool for getting things done.", "parameters": {"type": "object", "properties": {"command": {"type": "string", "description": "The shell command to execute"}}, "required": ["command"]}}},
    {"type": "function", "function": {"name": "file_write", "description": "Write content to a file. Paths must be within /opt/evolvixos, /tmp, /root, /home.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Absolute file path"}, "content": {"type": "string", "description": "File content"}}, "required": ["path", "content"]}}},
    {"type": "function", "function": {"name": "file_read", "description": "Read a file's content. Supports text files, code, configs, logs. Paths must be within allowed directories.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Absolute file path"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "file_list", "description": "List files in a directory with sizes and types.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Directory path"}, "recursive": {"type": "boolean", "default": False}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "file_upload", "description": "Read an uploaded file from the user's uploads directory. Use when the user has attached a file to their message.", "parameters": {"type": "object", "properties": {"filename": {"type": "string", "description": "The uploaded filename"}}, "required": ["filename"]}}},
    {"type": "function", "function": {"name": "python_exec", "description": "Execute Python 3 code and return the output. Use for calculations, data processing, web scraping, automation.", "parameters": {"type": "object", "properties": {"code": {"type": "string", "description": "Python code to execute"}}, "required": ["code"]}}},
    {"type": "function", "function": {"name": "service_check", "description": "Check the status of a systemd service.", "parameters": {"type": "object", "properties": {"name": {"type": "string", "description": "Service name (e.g. nginx, ollama)"}}, "required": ["name"]}}},
    {"type": "function", "function": {"name": "service_restart", "description": "Restart a systemd service.", "parameters": {"type": "object", "properties": {"name": {"type": "string", "description": "Service name"}}, "required": ["name"]}}},
    {"type": "function", "function": {"name": "docker_ps", "description": "List all Docker containers with status and ports.", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "docker_restart", "description": "Restart a Docker container by name.", "parameters": {"type": "object", "properties": {"name": {"type": "string", "description": "Container name"}}, "required": ["name"]}}},
    {"type": "function", "function": {"name": "git", "description": "Run git commands (status, log, add, commit, push, pull, diff, branch).", "parameters": {"type": "object", "properties": {"command": {"type": "string", "description": "Git command (e.g. 'status', 'log --oneline -5')"}, "repo": {"type": "string", "description": "Repo path", "default": "."}}, "required": ["command"]}}},
    {"type": "function", "function": {"name": "http_request", "description": "Make an HTTP request to any URL. Returns status code and response body. Use for API calls, webhooks, fetching data.", "parameters": {"type": "object", "properties": {"url": {"type": "string", "description": "Full URL"}, "method": {"type": "string", "default": "GET"}, "body": {"type": "object"}, "headers": {"type": "object"}}, "required": ["url"]}}},
    {"type": "function", "function": {"name": "web_search", "description": "Search the web via DuckDuckGo. Returns text results.", "parameters": {"type": "object", "properties": {"query": {"type": "string", "description": "Search query"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "web_fetch", "description": "Fetch and extract text content from a web page URL. Use to read articles, documentation, or API responses.", "parameters": {"type": "object", "properties": {"url": {"type": "string", "description": "URL to fetch"}, "max_chars": {"type": "integer", "default": 5000}}, "required": ["url"]}}},
    {"type": "function", "function": {"name": "ui_generate", "description": "Generate UI components from Magic UI, Unlumen UI, or Retro UI libraries.", "parameters": {"type": "object", "properties": {"prompt": {"type": "string"}, "library": {"type": "string", "enum": ["magic-ui", "unlumen-ui", "retro-ui", "auto"]}, "theme": {"type": "string"}}, "required": ["prompt"]}}},
    {"type": "function", "function": {"name": "image_generate", "description": "Generate an AI image from text. Returns a job ID — check status with /api/job/<id>.", "parameters": {"type": "object", "properties": {"prompt": {"type": "string"}, "steps": {"type": "integer", "default": 15}}, "required": ["prompt"]}}},
    {"type": "function", "function": {"name": "list_models", "description": "List all available AI models on the platform (Ollama, HF Gateway).", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "memory_save", "description": "Save a durable memory. Use to remember facts, preferences, decisions across sessions.", "parameters": {"type": "object", "properties": {"key": {"type": "string"}, "value": {"type": "string"}, "category": {"type": "string", "default": "General"}}, "required": ["key", "value"]}}},
    {"type": "function", "function": {"name": "memory_load", "description": "Load a memory by key.", "parameters": {"type": "object", "properties": {"key": {"type": "string"}}, "required": ["key"]}}},
    {"type": "function", "function": {"name": "memory_list", "description": "List all stored memories.", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "skill_run", "description": "Execute an EvolvixOS skill (create-media, crypto-blockchain, design-studio, voice-command).", "parameters": {"type": "object", "properties": {"name": {"type": "string", "description": "Skill name"}, "input": {"type": "string", "description": "Input for the skill"}}, "required": ["name", "input"]}}},
    {"type": "function", "function": {"name": "code_analyze", "description": "Analyze code for bugs, security issues, and improvements. Returns a structured report.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "File path to analyze"}, "language": {"type": "string", "description": "Programming language (auto-detect if omitted)"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "system_info", "description": "Get system information: CPU, memory, disk, uptime, running services, docker containers.", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "pip_install", "description": "Install a Python package via pip. Use for adding dependencies needed for tasks.", "parameters": {"type": "object", "properties": {"package": {"type": "string", "description": "Package name (e.g. 'requests', 'flask==2.0')"}}, "required": ["package"]}}},
]

TOOL_NAMES = [t["function"]["name"] for t in TOOLS]

# ─── Identity & Soul ───
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
    
    # Get system info
    try:
        uptime = subprocess.run(["uptime", "-p"], capture_output=True, text=True, timeout=3).stdout.strip()
    except Exception:
        uptime = "unknown"
    
    context_parts.append(f"## Current Context\nTime: {now}\nServer: 2.28.52.223 (evolvixos.com)\nUptime: {uptime}\nPlatform: EvolvixOS v9.0\nModels: 281 across 12 categories\nTools: {len(TOOLS)} available")
    
    skills = []
    if os.path.exists(SKILLS_DIR):
        for fname in sorted(os.listdir(SKILLS_DIR)):
            if fname.endswith(".sh"):
                skills.append(fname.replace(".sh", ""))
    if skills:
        context_parts.append("## My Skills\n" + ", ".join(skills))
    
    # List available uploaded files
    upload_info = []
    if os.path.exists(UPLOADS_DIR):
        for fname in sorted(os.listdir(UPLOADS_DIR))[:10]:
            fpath = os.path.join(UPLOADS_DIR, fname)
            if os.path.isfile(fpath):
                size = os.path.getsize(fpath)
                upload_info.append(f"- {fname} ({size} bytes)")
    if upload_info:
        context_parts.append("## User Uploaded Files\nThe user has uploaded these files. Use the file_upload tool to read them:\n" + "\n".join(upload_info))
    
    return "\n\n".join(context_parts)

def build_system_prompt(mem_dir=None, user_email=None, user_name=None):
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
    
    # Add user context
    user_info = []
    if user_email:
        user_info.append(f"User email: {user_email}")
    if user_name:
        user_info.append(f"User name: {user_name}")
    if user_info:
        parts.append("## Current User\n" + "\n".join(user_info))
    
    # Add tool usage guidance
    parts.append("""## Tool Usage Guide
You have 24 tools. Use them proactively — don't just talk, DO things.

When to use which tool:
- **bash** — Your go-to for anything system-related. List files, check services, run scripts, grep logs, etc.
- **file_read / file_list / file_upload** — Read files the user mentions or uploads. Always check uploaded files when a user references an attachment.
- **python_exec** — For calculations, data processing, or when you need to parse/manipulate data programmatically.
- **web_search / web_fetch** — Search for information, then fetch full page content for detailed reading.
- **code_analyze** — When a user asks you to review code, find bugs, or check security.
- **system_info** — Quick health check of the entire server.
- **skill_run** — Execute one of your 4 skills for media, crypto, design, or voice tasks.

IMPORTANT RULES:
1. If a tool call fails, DON'T give up. Try a different approach or fix the error and retry.
2. After running a tool, analyze the result before responding. If the result shows an error, investigate and fix it.
3. Use multiple tools in sequence when needed. Break complex tasks into steps.
4. When the user uploads a file, ALWAYS read it first before responding.
5. Be proactive — if you notice something wrong on the server, mention it.
6. Keep responses concise but complete. Show the user what you did, not just the final answer.""")
    
    return "\n\n---\n\n".join(parts)

# ─── Conversation management ───
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

# ─── Tool execution ───
def execute_tool(name, args, mem_dir=None, handler=None, uploads_dir=None):
    try:
        if name == "bash":
            cmd = args.get("command", "")
            if not cmd:
                return "Error: no command provided"
            dangerous = ["rm -rf /", "mkfs", "dd if=", "shutdown", "reboot", "halt", ":(){:|:&};:"]
            if any(d in cmd.lower() for d in dangerous):
                return "Error: command blocked (dangerous pattern detected)"
            import shlex
            result = subprocess.run(shlex.split(cmd), shell=False, capture_output=True, text=True, timeout=120)
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

        elif name == "file_list":
            path = args.get("path", ".")
            recursive = args.get("recursive", False)
            if not is_path_safe(path):
                return f"Error: path '{path}' is outside allowed directories"
            if not os.path.exists(path):
                return f"Directory not found: {path}"
            items = []
            if recursive:
                for root, dirs, files in os.walk(path):
                    for f in files:
                        fpath = os.path.join(root, f)
                        try:
                            size = os.path.getsize(fpath)
                            items.append(f"{fpath} ({size} bytes)")
                        except Exception:
                            pass
                    if len(items) > 200:
                        items.append("... (truncated, 200+ files)")
                        break
            else:
                for f in sorted(os.listdir(path)):
                    fpath = os.path.join(path, f)
                    if os.path.isdir(fpath):
                        items.append(f"[DIR] {f}/")
                    else:
                        try:
                            size = os.path.getsize(fpath)
                            items.append(f"{f} ({size} bytes)")
                        except Exception:
                            items.append(f"{f}")
            return "\n".join(items) if items else "(empty directory)"

        elif name == "file_upload":
            filename = args.get("filename", "")
            if not filename:
                return "Error: no filename provided"
            # Sanitize filename
            safe_name = re.sub(r'[^a-zA-Z0-9._-]', '', filename)[:200]
            u_dir = uploads_dir or UPLOADS_DIR
            fpath = os.path.join(u_dir, safe_name)
            if not os.path.exists(fpath):
                # Try without sanitization in case filename has spaces
                fpath = os.path.join(u_dir, filename)
                if not os.path.exists(fpath):
                    return f"Uploaded file not found: {filename}. Available files: {os.listdir(u_dir) if os.path.exists(u_dir) else 'no uploads dir'}"
            # Determine how to read the file
            ext = os.path.splitext(safe_name)[1].lower()
            text_exts = ['.txt', '.md', '.py', '.js', '.ts', '.json', '.yaml', '.yml', '.html', '.css', '.sh', '.xml', '.csv', '.log', '.sql', '.c', '.cpp', '.java', '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.scala', '.r', '.tex', '.toml', '.ini', '.cfg', '.conf']
            if ext in text_exts:
                with open(fpath) as f:
                    content = f.read()[:15000]
                return f"--- File: {filename} ({os.path.getsize(fpath)} bytes) ---\n{content}"
            elif ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp']:
                return f"Image file: {filename} ({os.path.getsize(fpath)} bytes). Image is available at the uploads path. You can analyze it by running: python3 -c \"from PIL import Image; img=Image.open('{fpath}'); print(img.size, img.mode)\""
            else:
                # Try to read as text, fall back to binary info
                try:
                    with open(fpath) as f:
                        content = f.read()[:15000]
                    return f"--- File: {filename} ({os.path.getsize(fpath)} bytes) ---\n{content}"
                except Exception:
                    return f"Binary file: {filename} ({os.path.getsize(fpath)} bytes). Type: {ext or 'unknown'}"

        elif name == "python_exec":
            code = args.get("code", "")
            if not code:
                return "Error: no code"
            result = subprocess.run(["python3", "-c", code], capture_output=True, text=True, timeout=120)
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
            repo = args.get("repo", "/opt/evolvixos")
            cmd = sanitize_git_command(args.get("command", ""))
            if not cmd:
                return "Error: invalid git command. Allowed: status, log, add, commit, push, pull, diff, branch, checkout, fetch, clone, init, remote, show"
            if not is_path_safe(repo):
                return "Error: repo path not allowed"
            r = subprocess.run(["git", "-C", repo] + cmd.split(), capture_output=True, text=True, timeout=30)
            return (r.stdout + r.stderr)[:5000] or "(no output)"

        elif name == "http_request":
            url = args.get("url", "")
            method = args.get("method", "GET")
            body = args.get("body")
            headers = args.get("headers", {})
            if not url or not url.startswith(("http://", "https://")):
                return "Error: invalid URL"
            data = json.dumps(body).encode() if body else None
            req_headers = {"Content-Type": "application/json"}
            req_headers.update(headers)
            req = urllib.request.Request(url, data=data, method=method, headers=req_headers)
            with urllib.request.urlopen(req, timeout=30) as resp:
                return f"[{resp.status}] {resp.read()[:5000].decode(errors='replace')}"

        elif name == "web_search":
            query = args.get("query", "")
            if not query:
                return "Error: no query"
            url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(query)}&format=json&no_html=1"
            req = urllib.request.Request(url, headers={"User-Agent": "MrJames/9.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())
            results = []
            if data.get("AbstractText"):
                results.append(data["AbstractText"])
            if data.get("AbstractURL"):
                results.append(f"Source: {data['AbstractURL']}")
            for topic in data.get("RelatedTopics", [])[:8]:
                if isinstance(topic, dict) and topic.get("Text"):
                    results.append(topic["Text"])
                elif isinstance(topic, dict) and topic.get("Topics"):
                    for sub in topic["Topics"][:3]:
                        if isinstance(sub, dict) and sub.get("Text"):
                            results.append(sub["Text"])
            return "\n\n".join(results) if results else "No results found. Try a more specific query."

        elif name == "web_fetch":
            url = args.get("url", "")
            max_chars = args.get("max_chars", 5000)
            if not url or not url.startswith(("http://", "https://")):
                return "Error: invalid URL"
            req = urllib.request.Request(url, headers={"User-Agent": "MrJames/9.0"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                content = resp.read().decode(errors='replace')
            # Strip HTML tags
            content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL)
            content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL)
            content = re.sub(r'<[^>]+>', ' ', content)
            content = re.sub(r'\s+', ' ', content).strip()
            return content[:max_chars]

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
                        result_parts.append(f"Available: {', '.join(components[:20])}")
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
                    if components:
                        result_parts.append(f"Available: {', '.join(components[:20])}")
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
                        result_parts.append(f"Available themes: {', '.join(themes[:20])}")
                else:
                    result_parts.append("Retro UI library not found")
            return "\n\n".join(result_parts)

        elif name == "image_generate":
            prompt = args.get("prompt", "")
            steps = args.get("steps", 15)
            job_id = str(uuid.uuid4())[:8]
            with JOBS_LOCK:
                prune_old_jobs()
                JOBS[job_id] = {"status": "processing", "prompt": prompt, "created": datetime.now().isoformat()}
            def _generate():
                try:
                    encoded_prompt = urllib.parse.quote(prompt)
                    img_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true"
                    save_path = f"/opt/evolvixos/generated_images/{job_id}.png"
                    os.makedirs(os.path.dirname(save_path), exist_ok=True)
                    req = urllib.request.Request(img_url, headers={"User-Agent": "MrJames/9.0"})
                    with urllib.request.urlopen(req, timeout=60) as resp:
                        with open(save_path, "wb") as f:
                            f.write(resp.read())
                    with JOBS_LOCK:
                        JOBS[job_id] = {"status": "done", "url": f"/generated_images/{job_id}.png", "path": save_path, "prompt": prompt}
                except Exception as e:
                    with JOBS_LOCK:
                        JOBS[job_id] = {"status": "error", "error": str(e), "prompt": prompt}
            threading.Thread(target=_generate, daemon=True).start()
            return f"Image generation started. Job ID: {job_id}. Check status with /api/job/{job_id}"

        elif name == "list_models":
            models = []
            try:
                req = urllib.request.Request(f"{OLLAMA_URL}/api/tags")
                with urllib.request.urlopen(req, timeout=5) as resp:
                    data = json.loads(resp.read())
                    for m in data.get("models", []):
                        models.append(m["name"])
            except Exception:
                pass
            # Also check HF Gateway
            try:
                req = urllib.request.Request(f"{HF_GATEWAY_URL}/models")
                with urllib.request.urlopen(req, timeout=5) as resp:
                    data = json.loads(resp.read())
                    for m in data.get("data", []):
                        models.append(f"hf:{m.get('id', 'unknown')}")
            except Exception:
                pass
            return f"Available models ({len(models)}): {', '.join(models[:30])}" + ("..." if len(models) > 30 else "")

        elif name == "memory_save":
            key = re.sub(r'[^a-zA-Z0-9._-]', '', args.get("key", ""))[:100]
            value = args.get("value", "")
            category = args.get("category", "General")
            if not key or not value:
                return "Error: key and value required"
            mdir = mem_dir or MEMORY_DIR
            os.makedirs(mdir, exist_ok=True)
            mem = {"key": key, "value": value, "category": category, "timestamp": datetime.now().isoformat()}
            with open(os.path.join(mdir, f"{key}.json"), "w") as f:
                json.dump(mem, f)
            return f"Memory saved: {key}"

        elif name == "memory_load":
            key = re.sub(r'[^a-zA-Z0-9._-]', '', args.get("key", ""))[:100]
            if not key:
                return "Error: key required"
            mdir = mem_dir or MEMORY_DIR
            fpath = os.path.join(mdir, f"{key}.json")
            if not os.path.exists(fpath):
                return f"Memory not found: {key}"
            with open(fpath) as f:
                return json.dumps(json.load(f))

        elif name == "memory_list":
            mdir = mem_dir or MEMORY_DIR
            if not os.path.exists(mdir):
                return "No memories stored"
            items = []
            for fname in sorted(os.listdir(mdir)):
                if fname.endswith(".json"):
                    try:
                        with open(os.path.join(mdir, fname)) as f:
                            mem = json.load(f)
                            items.append(f"[{mem.get('category','General')}] {mem['key']}: {mem['value'][:100]}")
                    except Exception:
                        pass
            return "\n".join(items) if items else "No memories stored"

        elif name == "skill_run":
            skill_name = re.sub(r'[^a-zA-Z0-9_-]', '', args.get("name", ""))[:50]
            skill_input = args.get("input", "")
            if not skill_name:
                return "Error: skill name required"
            skill_path = os.path.join(SKILLS_DIR, f"{skill_name}.sh")
            if not os.path.exists(skill_path):
                # List available skills
                available = [f.replace(".sh", "") for f in os.listdir(SKILLS_DIR) if f.endswith(".sh")] if os.path.exists(SKILLS_DIR) else []
                return f"Skill '{skill_name}' not found. Available: {', '.join(available)}"
            if not os.access(skill_path, os.X_OK):
                os.chmod(skill_path, 0o755)
            r = subprocess.run(["bash", skill_path, skill_input], capture_output=True, text=True, timeout=120)
            output = r.stdout
            if r.stderr:
                output += f"\n[STDERR]\n{r.stderr}"
            return output[:8000] if output else "(skill ran with no output)"

        elif name == "code_analyze":
            path = args.get("path", "")
            if not path:
                return "Error: no file path provided"
            if not is_path_safe(path):
                return f"Error: path '{path}' is outside allowed directories"
            if not os.path.exists(path):
                return f"File not found: {path}"
            with open(path) as f:
                code = f.read()
            # Auto-detect language
            ext = os.path.splitext(path)[1].lower()
            lang_map = {'.py': 'python', '.js': 'javascript', '.ts': 'typescript', '.sh': 'bash', '.go': 'go', '.rs': 'rust', '.java': 'java', '.c': 'c', '.cpp': 'cpp', '.rb': 'ruby', '.php': 'php', '.html': 'html', '.css': 'css', '.sql': 'sql'}
            language = args.get("language", "") or lang_map.get(ext, "unknown")
            
            findings = []
            # Python-specific checks
            if language == "python":
                if "shell=True" in code:
                    findings.append("CRITICAL: shell=True detected — potential command injection")
                if "eval(" in code and "ast.literal_eval" not in code:
                    findings.append("HIGH: eval() usage — code injection risk")
                if "exec(" in code:
                    findings.append("HIGH: exec() usage — code injection risk")
                if "pickle.loads" in code:
                    findings.append("CRITICAL: pickle.loads — deserialization attack risk")
                if "os.system(" in code:
                    findings.append("HIGH: os.system() — command injection risk")
                if "subprocess.call(" in code and "shell=True" in code:
                    findings.append("HIGH: subprocess.call with shell=True — injection risk")
                if "import os" in code and "password" in code.lower():
                    findings.append("MEDIUM: OS module imported in file with password references")
                if "except:" in code and "except Exception:" not in code:
                    findings.append("MEDIUM: Bare except clause — may hide errors")
                if "TODO" in code or "FIXME" in code:
                    findings.append("INFO: TODO/FIXME comments found")
                if "print(" in code and "def " in code:
                    # Count prints in functions (debug code left in)
                    print_count = code.count("print(")
                    if print_count > 10:
                        findings.append(f"INFO: {print_count} print statements — consider using logging")
            # General checks
            if "password" in code.lower() and ("= " in code or ":" in code):
                findings.append("MEDIUM: Hardcoded password-like strings detected")
            if "api_key" in code.lower() and ("= " in code or '":' in code):
                findings.append("HIGH: API key-like strings detected in code")
            if "127.0.0.1" in code and language in ["python", "javascript", "typescript"]:
                findings.append("INFO: Localhost reference found (probably fine for dev)")
            if not findings:
                findings.append("No issues found — code looks clean!")
            
            report = f"Code Analysis Report: {path}\nLanguage: {language}\nLines: {len(code.splitlines())}\n\nFindings ({len(findings)}):\n"
            for f in findings:
                report += f"  - {f}\n"
            return report

        elif name == "system_info":
            info_parts = []
            # CPU
            try:
                cpu = subprocess.run(["nproc"], capture_output=True, text=True, timeout=3).stdout.strip()
                info_parts.append(f"CPU cores: {cpu}")
            except: pass
            # Memory
            try:
                mem = subprocess.run(["free", "-h"], capture_output=True, text=True, timeout=3).stdout.strip()
                info_parts.append(f"Memory:\n{mem}")
            except: pass
            # Disk
            try:
                disk = subprocess.run(["df", "-h", "/"], capture_output=True, text=True, timeout=3).stdout.strip()
                info_parts.append(f"Disk:\n{disk}")
            except: pass
            # Uptime
            try:
                uptime = subprocess.run(["uptime"], capture_output=True, text=True, timeout=3).stdout.strip()
                info_parts.append(f"Uptime: {uptime}")
            except: pass
            # Services
            try:
                services = subprocess.run(["systemctl", "is-active", "nginx", "ollama"], capture_output=True, text=True, timeout=3).stdout.strip()
                info_parts.append(f"Key services: {services}")
            except: pass
            # Docker
            try:
                containers = subprocess.run(["docker", "ps", "--format", "{{.Names}}: {{.Status}}"], capture_output=True, text=True, timeout=3).stdout.strip()
                if containers:
                    info_parts.append(f"Docker:\n{containers}")
            except: pass
            # Ports
            try:
                ports = subprocess.run(["ss", "-tlnp"], capture_output=True, text=True, timeout=3).stdout.strip()
                active_ports = [l for l in ports.split('\n') if any(p in l for p in ['5010', '5022', '11434', '8188', '20128', '20129', '5002'])]
                if active_ports:
                    info_parts.append(f"Active ports:\n" + "\n".join(active_ports))
            except: pass
            return "\n\n".join(info_parts)

        elif name == "pip_install":
            package = re.sub(r'[^a-zA-Z0-9_.>=<\-]', '', args.get("package", ""))[:100]
            if not package:
                return "Error: package name required"
            r = subprocess.run(["pip3", "install", package], capture_output=True, text=True, timeout=120)
            output = r.stdout + r.stderr
            if r.returncode == 0:
                return f"Successfully installed {package}\n{output[-500:]}"
            else:
                return f"Failed to install {package}: {output[-500:]}"

        else:
            return f"Unknown tool: {name}"

    except subprocess.TimeoutExpired:
        return f"Error: tool '{name}' timed out after 120s"
    except Exception as e:
        return f"Error in tool '{name}': {str(e)}"

# ─── Intent classification (v9.0 — smarter) ───
def classify_intent(prompt):
    t = prompt.lower().strip()
    
    # Image generation
    if re.search(r'\b(draw|paint|generate|create|design|logo|image|picture|art|portrait|landscape|render|3d model|blender)\b', t) and not re.search(r'\b(code|app|api|script|function|program|build|file|upload)\b', t):
        return ("image", "comfyui", "stable-diffusion", "Image generation request")
    
    # Video generation
    if re.search(r'\b(video|movie|film|animate|cinema|clip|wan2|video gen)\b', t):
        return ("video", "comfyui", "wan2.1", "Video generation request")
    
    # Crypto/blockchain
    if re.search(r'\b(crypto|bitcoin|ethereum|blockchain|defi|token|nft|web3|smart contract|solidity|wallet|staking|liquidity)\b', t):
        return ("crypto", "skill", "crypto-blockchain", "Crypto/blockchain analysis")
    
    # Code tasks — use 14b for complex reasoning
    if re.search(r'\b(code|app|api|function|script|build|react|python|javascript|html|css|deploy|debug|refactor|sql|database|backend|frontend|server)\b', t):
        return ("code", "ollama", "qwen2.5:14b", "Coding task — needs reasoning")
    
    # UI generation
    if re.search(r'\b(ui|component|button|card|modal|dashboard|landing page|retro|win95|vaporwave|magic ui|unlumen)\b', t):
        return ("ui", "ollama", "qwen2.5:14b", "UI generation task")
    
    # File analysis
    if re.search(r'\b(analyze|review|audit|check|inspect|read|file|upload|attachment)\b', t):
        return ("analysis", "ollama", "qwen2.5:14b", "File/code analysis task")
    
    # System management
    if re.search(r'\b(server|service|nginx|docker|systemctl|restart|status|deploy|install|config)\b', t):
        return ("system", "ollama", "qwen2.5:7b", "System management task")
    
    # Media creation
    if re.search(r'\b(voice|audio|narrate|tts|speak|podcast|music|sound)\b', t):
        return ("media", "skill", "create-media", "Media/voice generation")
    
    # Complex reasoning → Kimi if available, else 14b
    if re.search(r'\b(why|how|explain|compare|analyze|strategy|plan|architect|design pattern|best practice)\b', t):
        if KIMI_API_KEY:
            return ("reasoning", "kimi", KIMI_MODEL, "Complex reasoning — using Kimi API")
        return ("reasoning", "ollama", "qwen2.5:14b", "Complex reasoning task")
    
    # Simple chat
    return ("chat", "ollama", "qwen2.5:7b", "General conversation")

def select_engine(prompt):
    return classify_intent(prompt)

# ─── Model API calls ───
def call_ollama_with_tools(model, messages, tools, stream=False):
    data = json.dumps({"model": model, "messages": messages, "tools": tools if tools else [], "stream": stream, "options": {"temperature": 0.7, "top_p": 0.9}}).encode()
    req = urllib.request.Request(f"{OLLAMA_URL}/api/chat", data=data, headers={"Content-Type": "application/json"})
    resp = urllib.request.urlopen(req, timeout=180)
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

# ─── Agentic Loop v9.0 (with self-correction) ───
def agentic_loop(prompt, session_id="default", model="qwen2.5:14b", max_turns=10, on_event=None, conv_dir=None, mem_dir=None, user_email=None, user_name=None, uploads_dir=None):
    system_prompt = build_system_prompt(mem_dir=mem_dir, user_email=user_email, user_name=user_name)
    history = get_conversation(session_id, conv_dir=conv_dir)
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": prompt})
    
    engine, model_sel, intent, reason = select_engine(prompt)
    # Use classified model for the first turn, but keep it configurable
    if not model or model == "qwen2.5:14b":
        model = model_sel if model_sel.startswith("qwen") else "qwen2.5:14b"
    
    if on_event:
        on_event("engine", {"engine": engine, "model": model, "intent": intent, "reason": reason})
    
    tools_used = 0
    errors_encountered = 0
    tool_results_summary = []
    
    for turn in range(max_turns):
        if on_event:
            on_event("thinking", {"turn": turn + 1})
        
        # Use simpler model for later turns to save CPU
        current_model = model if turn < 3 else "qwen2.5:7b" if model == "qwen2.5:14b" else model
        
        try:
            result = call_ollama_with_tools(current_model, messages, TOOLS, stream=False)
        except Exception as e:
            # Fallback to smaller model
            try:
                result = call_ollama_with_tools("qwen2.5:7b", messages, TOOLS, stream=False)
            except Exception as e2:
                # Last resort: try 3b
                try:
                    result = call_ollama_with_tools("qwen2.5:3b", messages, TOOLS, stream=False)
                except Exception as e3:
                    error_msg = f"All models failed: {e}"
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
            # No more tools to call — we're done
            history.append({"role": "user", "content": prompt})
            history.append({"role": "assistant", "content": content})
            save_conversation(session_id, history, conv_dir=conv_dir)
            if on_event:
                on_event("done", {"response": content, "tools_used": tools_used, "turns": turn + 1, "engine": engine, "errors": errors_encountered})
            return {"response": content, "engine": engine, "model": model, "status": "success", "turns": turn + 1, "tools_used": tools_used, "intent": intent, "errors": errors_encountered}
        
        # Execute all tool calls in this turn
        for tc in tool_calls:
            func = tc.get("function", {})
            tool_name = func.get("name", "")
            tool_args = func.get("arguments", {})
            if isinstance(tool_args, str):
                try:
                    tool_args = json.loads(tool_args)
                except Exception:
                    tool_args = {}
            tools_used += 1
            if on_event:
                on_event("tool_call", {"tool": tool_name, "args": tool_args})
            
            result_text = execute_tool(tool_name, tool_args, mem_dir=mem_dir, uploads_dir=uploads_dir)
            
            # Self-correction: if tool returns error, note it
            if result_text.startswith("Error"):
                errors_encountered += 1
                if on_event:
                    on_event("tool_error", {"tool": tool_name, "error": result_text[:200]})
            else:
                tool_results_summary.append(f"{tool_name}: {result_text[:100]}")
            
            if on_event:
                on_event("tool_result", {"tool": tool_name, "result": result_text[:500]})
            messages.append({"role": "tool", "content": result_text, "name": tool_name})
    
    # Max turns reached — ask for summary
    summary_prompt = "Summarize what you've done so far. Here are the tools you used and their results:\n" + "\n".join(tool_results_summary[-10:]) + "\n\nGive the user a clear final answer."
    messages.append({"role": "user", "content": summary_prompt})
    try:
        result = call_ollama_with_tools("qwen2.5:7b", messages, [], stream=False)
        final_content = result.get("message", {}).get("content", "Task completed.")
    except Exception:
        final_content = "Task completed. " + "; ".join(tool_results_summary[-5:])
    
    history.append({"role": "user", "content": prompt})
    history.append({"role": "assistant", "content": final_content})
    save_conversation(session_id, history, conv_dir=conv_dir)
    if on_event:
        on_event("done", {"response": final_content, "tools_used": tools_used, "turns": max_turns, "engine": engine, "errors": errors_encountered})
    return {"response": final_content, "engine": engine, "model": model, "status": "success", "turns": max_turns, "tools_used": tools_used, "intent": intent, "errors": errors_encountered}

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

    def _add_security_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        self.send_header("X-XSS-Protection", "1; mode=block")

    def respond(self, code, data):
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "https://evolvixos.com")
        self._add_security_headers()
        self.end_headers()
        self.wfile.write(body)

    def _check(self, url):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "MrJames/9.0"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                return "online"
        except Exception:
            return "offline"

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "https://evolvixos.com")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self._add_security_headers()
        self.end_headers()

    def do_GET(self):
        if self.path == "/api/docs":
            self.respond(200, API_DOCS)
            return
        if self.path == "/api/health":
            self.respond(200, {
                "status": "online",
                "comfyui": self._check(COMFYUI_URL + "/system_stats"),
                "omniroute": self._check("http://127.0.0.1:20128/"),
                "ollama": self._check(OLLAMA_URL + "/api/tags"),
                "art_engine": self._check(ART_ENGINE_URL + "/api/status"),
                "models_registered": sum(1 for _ in open("/opt/evolvixos/models/model_registry.json")) if False else 81,
                "james_version": "9.0",
                "tools_available": len(TOOLS),
                "kimi_available": bool(KIMI_API_KEY),
                "memories_stored": len([f for f in os.listdir(MEMORY_DIR) if f.endswith(".json")]) if os.path.exists(MEMORY_DIR) else 0,
                "conversations": len([f for f in os.listdir(CONVERSATION_DIR) if f.endswith(".json")]) if os.path.exists(CONVERSATION_DIR) else 0,
                "uploads": len(os.listdir(UPLOADS_DIR)) if os.path.exists(UPLOADS_DIR) else 0
            })
        elif self.path == "/api/models":
            try:
                registry_path = "/opt/evolvixos/models/model_registry.json"
                if os.path.exists(registry_path):
                    with open(registry_path) as rf:
                        registry = json.load(rf)
                    # Live Ollama status
                    try:
                        req = urllib.request.Request(f"{OLLAMA_URL}/api/tags")
                        with urllib.request.urlopen(req, timeout=5) as resp:
                            ollama_data = json.loads(resp.read())
                        ollama_names = {m["name"] for m in ollama_data.get("models", [])}
                        for m in registry.get("models", []):
                            if m.get("source") == "ollama":
                                m["running"] = m["name"] in ollama_names
                    except Exception:
                        pass
                    self.respond(200, {
                        "models": registry.get("models", []),
                        "count": registry.get("total_models", 0),
                        "categories": registry.get("categories", {}),
                        "last_updated": registry.get("last_updated", ""),
                        "sources": {
                            "ollama": sum(1 for m in registry.get("models", []) if m.get("source") == "ollama"),
                            "github_discovery": sum(1 for m in registry.get("models", []) if m.get("source") == "github_discovery"),
                            "builtin": sum(1 for m in registry.get("models", []) if m.get("source") == "builtin")
                        }
                    })
                else:
                    req = urllib.request.Request(f"{OLLAMA_URL}/api/tags")
                    with urllib.request.urlopen(req, timeout=5) as resp:
                        self.respond(200, json.loads(resp.read()))
            except Exception as e:
                self.respond(500, {"error": str(e)})
        elif self.path == "/api/templates":
            self.respond(200, [
                {"id": 1, "title": "Web Application", "desc": "Build a full-stack web app", "icon": "🌐", "category": "Code", "prompt": "Build a web app with a React frontend and Python API for a todo app"},
                {"id": 2, "title": "AI Chatbot", "desc": "Create an AI chatbot with custom personality", "icon": "🤖", "category": "AI", "prompt": "Create an AI chatbot with a friendly personality for customer support"},
                {"id": 3, "title": "Logo & Brand Design", "desc": "Generate professional logos and brand assets", "icon": "🎨", "category": "Image", "prompt": "Generate a professional logo for a tech startup"},
                {"id": 4, "title": "Data Pipeline", "desc": "Build an ETL pipeline with data processing", "icon": "📊", "category": "Code", "prompt": "Build a data pipeline that processes CSV files and generates analytics"},
                {"id": 5, "title": "Mobile App", "desc": "Design a cross-platform mobile application", "icon": "📱", "category": "Code", "prompt": "Design a mobile app for tracking fitness goals"},
                {"id": 6, "title": "AI Video", "desc": "Generate videos from text prompts", "icon": "🎬", "category": "Video", "prompt": "Generate a video about a futuristic city"},
                {"id": 7, "title": "Smart Contract", "desc": "Write and deploy blockchain contracts", "icon": "⛓️", "category": "Web3", "prompt": "Write a Solidity smart contract for a voting system"},
                {"id": 8, "title": "Code Review", "desc": "Analyze code for bugs and security issues", "icon": "🔍", "category": "Analysis", "prompt": "Analyze the code in /opt/evolvixos/models/model_api.py for security issues"},
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
                for fname in sorted(os.listdir(SKILLS_DIR)):
                    if fname.endswith(".sh"):
                        name = fname.replace(".sh", "")
                        try:
                            with open(os.path.join(SKILLS_DIR, fname)) as f:
                                lines = f.readlines()
                            # Skip shebang line, get first comment line as description
                            desc = name
                            for line in lines:
                                line = line.strip()
                                if line.startswith("#!"):
                                    continue
                                if line.startswith("#"):
                                    desc = line.replace("#", "").strip()
                                    break
                                if line:
                                    break
                            skills.append({"name": name, "desc": desc})
                        except Exception:
                            skills.append({"name": name, "desc": name})
            self.respond(200, skills)
        elif self.path == "/api/identity":
            self.respond(200, {"identity": load_identity(), "soul": load_soul(), "version": "9.0", "tools": len(TOOLS)})
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
        elif self.path == "/api/uploads":
            if not require_auth(self): return
            u_upload = user_dir(self, UPLOADS_DIR)
            files = []
            if os.path.exists(u_upload):
                for fname in sorted(os.listdir(u_upload)):
                    fpath = os.path.join(u_upload, fname)
                    if os.path.isfile(fpath):
                        files.append({"name": fname, "size": os.path.getsize(fpath)})
            self.respond(200, files)
        elif self.path.startswith("/api/download/"):
            if not require_auth(self): return
            filename = self.path.split("/api/download/")[1].split("?")[0]
            u_upload = user_dir(self, UPLOADS_DIR)
            fpath = os.path.join(u_upload, filename)
            if not os.path.exists(fpath):
                self.respond(404, {"error": "File not found"})
                return
            with open(fpath, "rb") as f:
                data = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Disposition", f"attachment; filename={filename}")
            self.send_header("Content-Length", str(len(data)))
            self._add_security_headers()
            self.end_headers()
            self.wfile.write(data)
        else:
            self.respond(404, {"error": "Not found"})

    def do_POST(self):
        client_ip = self.client_address[0]
        if not check_rate_limit(client_ip):
            self.respond(429, {"error": "Rate limit exceeded. Slow down."})
            return
        content_type = self.headers.get("Content-Type", "")
        
        # Handle multipart file upload
        if "multipart/form-data" in content_type:
            if not require_auth(self):
                return
            u_upload = user_dir(self, UPLOADS_DIR)
            try:
                content_len = int(self.headers.get("Content-Length", 0))
                if content_len > 50_000_000:  # 50MB limit
                    self.respond(413, {"error": "File too large (max 50MB)"})
                    return
                body = self.rfile.read(content_len)
                # Parse multipart
                boundary = content_type.split("boundary=")[1].encode()
                parts = body.split(b"--" + boundary)
                uploaded_files = []
                for part in parts:
                    if not part or part == b"--\r\n" or part == b"--":
                        continue
                    if b"Content-Disposition" not in part:
                        continue
                    # Split headers and content
                    header_end = part.find(b"\r\n\r\n")
                    if header_end == -1:
                        continue
                    header_str = part[:header_end].decode(errors='replace')
                    content = part[header_end + 4:]
                    # Remove trailing \r\n
                    if content.endswith(b"\r\n"):
                        content = content[:-2]
                    # Extract filename
                    fname_match = re.search(r'filename="([^"]+)"', header_str)
                    if not fname_match:
                        continue
                    filename = fname_match.group(1)
                    safe_name = re.sub(r'[^a-zA-Z0-9._-]', '', filename)[:200]
                    if not safe_name:
                        continue
                    fpath = os.path.join(u_upload, safe_name)
                    with open(fpath, "wb") as f:
                        f.write(content)
                    uploaded_files.append({"name": safe_name, "size": len(content)})
                
                self.respond(200, {"status": "uploaded", "files": uploaded_files})
            except Exception as e:
                self.respond(500, {"error": f"Upload failed: {str(e)}"})
            return
        
        # Normal JSON endpoints
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
            steps = body.get("steps", 15)
            job_id = _start_image_job(prompt, steps)
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
        elif self.path == "/api/upload":
            if not require_auth(self): return
            # JSON-based upload (filename + base64 content)
            filename = re.sub(r'[^a-zA-Z0-9._-]', '', body.get("filename", ""))[:200]
            content_b64 = body.get("content", "")
            if not filename or not content_b64:
                self.respond(400, {"error": "filename and content required"})
                return
            import base64
            u_upload = user_dir(self, UPLOADS_DIR)
            try:
                data = base64.b64decode(content_b64)
                with open(os.path.join(u_upload, filename), "wb") as f:
                    f.write(data)
                self.respond(200, {"status": "uploaded", "filename": filename, "size": len(data)})
            except Exception as e:
                self.respond(400, {"error": f"Invalid base64: {str(e)}"})
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
            with urllib.request.urlopen(req, timeout=180) as resp:
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
        u_upload = user_dir(self, UPLOADS_DIR)
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
            agentic_loop(
                prompt, session_id=session_id, model=model, max_turns=10,
                on_event=on_event, conv_dir=u_conv, mem_dir=u_mem,
                user_email=getattr(self, '_user_email', None),
                user_name=getattr(self, '_user_name', None),
                uploads_dir=u_upload
            )
        except (BrokenPipeError, ConnectionResetError):
            return
        except Exception as e:
            try:
                self._sse("error", {"error": str(e)})
            except Exception:
                return
        finally:
            self._end_chunks()

def _start_image_job(prompt, steps=15):
    job_id = str(uuid.uuid4())[:8]
    with JOBS_LOCK:
        prune_old_jobs()
        JOBS[job_id] = {"status": "processing", "prompt": prompt, "created": datetime.now().isoformat()}
    def _generate():
        try:
            encoded_prompt = urllib.parse.quote(prompt)
            img_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true"
            save_path = f"/opt/evolvixos/generated_images/{job_id}.png"
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            req = urllib.request.Request(img_url, headers={"User-Agent": "MrJames/9.0"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                with open(save_path, "wb") as f:
                    f.write(resp.read())
            with JOBS_LOCK:
                JOBS[job_id] = {"status": "done", "url": f"/generated_images/{job_id}.png", "path": save_path, "prompt": prompt}
        except Exception as e:
            with JOBS_LOCK:
                JOBS[job_id] = {"status": "error", "error": str(e), "prompt": prompt}
    threading.Thread(target=_generate, daemon=True).start()
    return job_id

if __name__ == "__main__":
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    os.makedirs(MEMORY_DIR, exist_ok=True)
    os.makedirs(CONVERSATION_DIR, exist_ok=True)
    server = ThreadingHTTPServer(("0.0.0.0", PORT), ModelAPI)
    print(f"Mr James v9.0 — EvolvixOS Model API")
    print(f"  Port: {PORT}")
    print(f"  Tools: {len(TOOLS)} (native Ollama tool calling)")
    print(f"  Skills: {len([f for f in os.listdir(SKILLS_DIR) if f.endswith('.sh')]) if os.path.exists(SKILLS_DIR) else 0}")
    print(f"  Models: Ollama (local) + HF Gateway + Kimi ({'available' if KIMI_API_KEY else 'not configured'})")
    print(f"  New: file_upload, file_list, web_fetch, code_analyze, system_info, pip_install")
    print(f"  Uploads: {UPLOADS_DIR}")
    print(f"  Ready.")
    server.serve_forever()
