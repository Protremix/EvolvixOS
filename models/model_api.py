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
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
KIMI_URL = "https://api.moonshot.cn/v1/chat/completions"
KIMI_MODEL = os.environ.get("KIMI_MODEL", "moonshot-v1-32k")
HF_GATEWAY_URL = "http://127.0.0.1:20129"
IDENTITY_DIR = "/opt/evolvixos/identity"
MEMORY_DIR = "/opt/evolvixos/memory"
CONVERSATION_DIR = "/opt/evolvixos/conversations"
SKILLS_DIR = "/opt/evolvixos/skills"
from tim_integration import TIMIntegration
from mbti_profiles import _PROFILES as MBTI_PROFILES
from tencentcloud_manager import TencentCloudManager
tc_manager = TencentCloudManager()
TC_ENABLED = tc_manager.is_configured()
import tim_integration as tim_module
UPLOADS_DIR = "/opt/evolvixos/uploads"
MEMORY_PROXY_URL = "http://127.0.0.1:8096/claude-code/default"
MEMORY_PROXY_KEY = "sk-mem-JLj8ptfAdUISkCrOEdOmYqQ3SmejWZod"
MEMORY_CORE_URL = "http://127.0.0.1:8420"
MEMORY_HUB_URL = "http://127.0.0.1:8125"
KNOWLEDGE_API_URL = "http://127.0.0.1:8424/v3"
CUBE_API_URL = "http://127.0.0.1:3000"
CUBE_TEMPLATE_ID = "base"
SANDBOX_ENABLED = False  # Set to True when KVM is available
tim_client = TIMIntegration()
TIM_ENABLED = tim_client.is_configured()
MAX_JOBS = 100
PORT = 5010

# ─── Allowed paths for file operations (prevent traversal) ───
ALLOWED_BASE_DIRS = ["/opt/evolvixos", "/tmp", "/root", "/home", "/var/log"]

# ─── v10 Architecture: Unified Router + Providers + Security ───
sys.path.insert(0, '/opt/evolvixos')
from v10.providers.base import (
    LLMProvider, LLMRegistry, LLMResponse,
    PrivacyMode, RoutingDecision, init_registry, get_registry
)
from v10.router.model_router import ModelRouter, init_router, get_router
from v10.security.tool_security import (
    Permission, ToolSpec, register_tool, get_tool_spec,
    check_permission, validate_command, validate_url, validate_python_code,
    log_audit, get_audit_log, check_tool_rate, init_default_tools, validate_path
)

# Initialize v10 architecture (HYBRID mode by default)
V10_PRIVACY_MODE = os.environ.get("EVOLVIX_PRIVACY_MODE", "HYBRID")
_v10_router = None
_v10_registry = None

def _init_v10():
    global _v10_router, _v10_registry
    if _v10_registry is None:
        _v10_registry = init_registry(V10_PRIVACY_MODE)
        _v10_router = ModelRouter(_v10_registry)
        init_default_tools()

_init_v10()

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
    {"type": "function", "function": {"name": "file_upload", "description": "Read and understand an uploaded file. Supports text files (code, config, docs), images (analyzed with Gemini Vision - OCR, charts, UI, screenshots), PDFs, and more. Use when the user has attached a file or asks about a file.", "parameters": {"type": "object", "properties": {"file_path": {"type": "string", "description": "The uploaded filename (e.g. test_code.py)"}, "prompt": {"type": "string", "description": "Optional instruction for image analysis (e.g. Read all text, Describe the UI)"}}, "required": ["file_path"]}}},
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
    {"type": "function", "function": {"name": "search_ai_tools", "description": "Search the EvolvixOS AI Tools Registry (85+ curated dev tools: IDEs, CLIs, LLM APIs, agents, RAG, vector DBs, hosting, evaluation). Returns matching tools with pricing, models, features.", "parameters": {"type": "object", "properties": {"query": {"type": "string", "description": "Search query (e.g. 'free coding IDE', 'vector database', 'agent framework')"}, "category": {"type": "string", "enum": ["all", "llm-api", "ide", "cli", "local-model", "rag", "agent", "speech", "image", "video", "vector-db", "hosting", "evaluation", "embedding", "browser", "chat-platform"], "default": "all"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "search_apis", "description": "Search the EvolvixOS API Directory (35,000+ APIs across 33 categories). Find free or low-cost APIs for any use case.", "parameters": {"type": "object", "properties": {"query": {"type": "string", "description": "Search query (e.g. payment API, weather API, authentication)"}, "category": {"type": "string", "description": "Category filter (optional)"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "gemini_vision", "description": "Analyze an image using Google Gemini vision. Supports image understanding, OCR, chart reading, screenshot analysis, and multimodal queries.", "parameters": {"type": "object", "properties": {"image_path": {"type": "string", "description": "Path to image file on server or URL"}, "prompt": {"type": "string", "description": "Question or instruction about the image"}}, "required": ["image_path", "prompt"]}}},
    {"type": "function", "function": {"name": "gemini_tts", "description": "Convert text to speech using Google Gemini TTS. Returns audio file path.", "parameters": {"type": "object", "properties": {"text": {"type": "string", "description": "Text to convert to speech"}, "voice": {"type": "string", "description": "Voice style", "default": "neutral"}}, "required": ["text"]}}},
    {"type": "function", "function": {"name": "free_llm_providers", "description": "List free LLM API providers (31+ providers, 442+ free models). Returns providers with base URLs, free tier limits, and API key links. Use when user needs free AI model access.", "parameters": {"type": "object", "properties": {"filter": {"type": "string", "enum": ["all", "no-credit-card", "vision", "fast", "coding"], "default": "all", "description": "Filter providers by feature"}}}}},
    {"type": "function", "function": {"name": "search_learn", "description": "Search the EvolvixOS Learning Hub (15 modules on full-stack development, AI integration, prompt engineering). Returns relevant learning modules.", "parameters": {"type": "object", "properties": {"query": {"type": "string", "description": "Search query (e.g. 'how to build an app', 'prompt engineering', 'API integration')"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "image_gen_api_info", "description": "Get deployment info for the Free Image Generation API (100K calls/day via Cloudflare Workers AI, Stable Diffusion XL). Returns models, setup steps, and code examples.", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "smart_api_call", "description": "Make an HTTP request to any API URL. Use after finding an API with search_apis. Supports GET/POST with headers and body. Automatically adds common headers. Returns status code and response body.", "parameters": {"type": "object", "properties": {"url": {"type": "string", "description": "Full API URL to call"}, "method": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE"], "default": "GET"}, "headers": {"type": "object", "description": "HTTP headers (e.g. {Authorization: Bearer KEY})"}, "body": {"type": "object", "description": "JSON body for POST/PUT requests"}, "timeout": {"type": "integer", "default": 30, "description": "Timeout in seconds"}}, "required": ["url"]}}},
    {"type": "function", "function": {"name": "call_free_llm", "description": "Call a free LLM API provider for complex reasoning that local Qwen models cant handle. Supports Groq (fast, 276 tokens/s), Google Gemini (vision+multimodal), NVIDIA NIM (125 models), Cerebras (ultra-fast), ModelScope (55 models). Requires API key from the provider. Returns the LLM response. Use for: complex reasoning, long context, vision tasks, coding, when Qwen is too slow.", "parameters": {"type": "object", "properties": {"prompt": {"type": "string", "description": "The prompt/question to send to the LLM"}, "provider": {"type": "string", "enum": ["auto", "groq", "gemini", "nvidia", "cerebras", "modelscope", "cloudflare"], "default": "auto", "description": "Which provider to use. auto picks the best for the task."}, "system_prompt": {"type": "string", "description": "Optional system prompt to set context/behavior"}, "model": {"type": "string", "description": "Specific model name (optional, auto-selects if omitted)"}}, "required": ["prompt"]}}},
    {"type": "function", "function": {"name": "team_memory_search", "description": "Search the TencentDB team memory hub for past conversations, decisions, skills, and knowledge from previous agent sessions. Use to recall context without repeating work.", "parameters": {"type": "object", "properties": {"query": {"type": "string", "description": "What to search for in team memory"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "team_memory_save", "description": "Save important context to the TencentDB team memory hub for future sessions. Use for decisions, key findings, project context, or reusable workflows.", "parameters": {"type": "object", "properties": {"content": {"type": "string", "description": "What to remember"}, "category": {"type": "string", "description": "Category: decision, finding, context, skill"}}, "required": ["content"]}}},
    {"type": "function", "function": {"name": "sandbox_exec", "description": "Execute Python code or shell commands in a secure isolated MicroVM sandbox (CubeSandbox). Hardware-isolated with its own kernel and filesystem. Use for: running untrusted code, testing scripts, executing dangerous commands safely, or isolating workloads.", "parameters": {"type": "object", "properties": {"language": {"type": "string", "enum": ["python", "shell"], "default": "python", "description": "Language to execute"}, "code": {"type": "string", "description": "Code to execute in the sandbox"}}, "required": ["code", "language"]}}},
    {"type": "function", "function": {"name": "tim_send_message", "description": "Send a real-time message to a user via Tencent IM (TIMSDK). Messages appear in the EvolvixOS in-app chat. Requires TIM credentials to be configured.", "parameters": {"type": "object", "properties": {"to_user": {"type": "string", "description": "Recipient user ID"}, "content": {"type": "string", "description": "Message content"}, "msg_type": {"type": "string", "enum": ["text", "custom"], "default": "text", "description": "Message type"}}, "required": ["to_user", "content"]}}},
    {"type": "function", "function": {"name": "tim_create_group", "description": "Create a chat group/channel in Tencent IM for community discussions. Requires TIM credentials.", "parameters": {"type": "object", "properties": {"group_name": {"type": "string", "description": "Name of the group to create"}, "group_type": {"type": "string", "enum": ["Public", "Private", "ChatRoom", "Community"], "default": "Public", "description": "Type of group"}}, "required": ["group_name"]}}},
    {"type": "function", "function": {"name": "tim_send_group_message", "description": "Send a message to a Tencent IM group/channel. Requires TIM credentials and group ID.", "parameters": {"type": "object", "properties": {"group_id": {"type": "string", "description": "The group ID"}, "content": {"type": "string", "description": "Message content"}}, "required": ["group_id", "content"]}}},
    {"type": "function", "function": {"name": "tim_import_user", "description": "Import/register a user account in Tencent IM so they can use the in-app chat. Requires TIM credentials.", "parameters": {"type": "object", "properties": {"user_id": {"type": "string", "description": "Unique user ID to register"}, "nickname": {"type": "string", "description": "Display name for the user"}}, "required": ["user_id"]}}},
    {"type": "function", "function": {"name": "search_subagents", "description": "Search the Octop subagent library (217 AI agent templates across 16 categories: engineering, marketing, security, design, finance, etc.). Returns matching templates with descriptions and paths.", "parameters": {"type": "object", "properties": {"query": {"type": "string", "description": "Search query (skill name, category, or keyword)"}, "category": {"type": "string", "description": "Filter by category: academic, design, engineering, finance, game-development, gis, marketing, paid-media, product, project-management, sales, security, spatial-computing, specialized, support, testing"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "set_persona", "description": "Switch Mr James personality using an MBTI profile (16 types available). Changes response style, communication approach, and behavior patterns.", "parameters": {"type": "object", "properties": {"mbti_type": {"type": "string", "enum": ["INTJ", "INTP", "ENTJ", "ENTP", "INFJ", "INFP", "ENFJ", "ENFP", "ISTJ", "ISTP", "ESTJ", "ESTP", "ISFJ", "ISFP", "ESFJ", "ESFP"], "description": "MBTI personality type"}, "custom_prompt": {"type": "string", "description": "Optional custom system prompt override"}}, "required": ["mbti_type"]}}},
    {"type": "function", "function": {"name": "tencent_cloud", "description": "Manage Tencent Cloud resources via the official SDK. Supports 10 services: CVM (servers), CDB (databases), VPC (networking), SSL (certificates), DNSPod (DNS), CDN, Billing (costs), CAM (users), Hunyuan (Tencent LLM), and AIArt (image generation). Requires TENCENTCLOUD_SECRET_ID and TENCENTCLOUD_SECRET_KEY.", "parameters": {"type": "object", "properties": {"service": {"type": "string", "enum": ["cvm", "cdb", "vpc", "ssl", "dnspod", "cdn", "billing", "cam", "hunyuan", "aiart"], "description": "Tencent Cloud service name"}, "action": {"type": "string", "description": "Action to perform (e.g., describe_instances, start_instances, chat, text_to_image)"}, "params": {"type": "object", "description": "Parameters for the action"}, "region": {"type": "string", "description": "Tencent Cloud region (default: ap-frankfurt)"}}, "required": ["service", "action"]}}},
    {"type": "function", "function": {"name": "api_auto_route", "description": "Smart API auto-router. Given a task description, searches the 35K+ API directory AND the 85+ AI tools registry to find the best API or tool for the job. Returns ranked matches with URLs, descriptions, and setup instructions. Use when the user needs to accomplish something that an external API could help with.", "parameters": {"type": "object", "properties": {"task": {"type": "string", "description": "Natural language description of what the user wants to accomplish (e.g. 'scrape youtube comments', 'send email notifications', 'analyze sentiment', 'generate QR codes')"}, "prefer_free": {"type": "boolean", "default": True, "description": "Prefer free/open-source APIs over paid ones"}}, "required": ["task"]}}},
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
    
    context_parts.append(f"## Current Context\nTime: {now}\nServer: 2.28.52.223 (evolvixos.com)\nUptime: {uptime}\nPlatform: EvolvixOS v9.0\nModels: 81 across 8 categories\nTools: {len(TOOLS)} available (32 tools: 24 core + 8 API intelligence)")
    
    skills = []
    if os.path.exists(SKILLS_DIR):
        for fname in sorted(os.listdir(SKILLS_DIR)):
            if fname.endswith(".sh"):
                skills.append(fname.replace(".sh", ""))
    if skills:
        context_parts.append("## My Skills\n" + ", ".join(skills))
    
    return "\n\n".join(context_parts)

def build_system_prompt(mem_dir=None, user_email=None, user_name=None, uploads_dir=None):
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
You have 32 tools. Use them proactively — don't just talk, DO things.

### Core Tools (24)
- **bash** — Your go-to for anything system-related. List files, check services, run scripts, grep logs, etc.
- **file_read / file_list / file_upload** — Read files the user mentions or uploads. Always check uploaded files when a user references an attachment.
- **python_exec** — For calculations, data processing, or when you need to parse/manipulate data programmatically.
- **web_search / web_fetch** — Search for information, then fetch full page content for detailed reading.
- **code_analyze** — When a user asks you to review code, find bugs, or check security.
- **system_info** — Quick health check of the entire server.
- **skill_run** — Execute one of your 4 skills for media, crypto, design, or voice tasks.
- **http_request** — Make direct HTTP calls to any URL.

### API Intelligence Tools (8) — YOUR SUPERPOWER
You have access to a massive knowledge base of external APIs and tools:
- **search_ai_tools** — Search 85+ curated AI dev tools (IDEs, CLIs, agents, RAG, vector DBs). Use when looking for a specific tool type.
- **search_apis** — Search 35,000+ APIs across 33 categories. Use when the user needs an API for a specific task.
- **free_llm_providers** — List 31 free LLM API providers with 442 free models. Use when the user needs free AI model access.
- **search_learn** — Search 19 learning modules on full-stack development. Use for educational queries.
- **image_gen_api_info** — Get deployment info for free image generation API (100K calls/day).
- **api_auto_route** — THE SMART ONE: Given a task description, auto-searches ALL registries and finds the best API/tool. Always use this first when a user describes a task that an external API could help with.
- **smart_api_call** — Actually CALL any API URL you discover. Use after finding an API with search_apis or api_auto_route.
- **call_free_llm** — Call a free external LLM (Groq/Gemini/NVIDIA/Cerebras) for complex reasoning that local Qwen cant handle. Auto-selects the best provider. Use for hard reasoning, vision, long context.

### How to use your API intelligence
1. When a user asks to accomplish something (e.g. "scrape youtube", "send emails", "analyze sentiment"), FIRST use api_auto_route to find the best API.
2. Then use smart_api_call to test the API, or tell the user the setup steps.
3. When a task needs complex reasoning and Qwen is struggling, use call_free_llm to delegate to a free external model.
4. When the user asks about free AI models, use free_llm_providers to show them options with 442+ free models.
5. Be PROACTIVE — if you detect a task that an API could help with, suggest it without being asked.

IMPORTANT RULES:
1. If a tool call fails, DON'T give up. Try a different approach or fix the error and retry.
2. After running a tool, analyze the result before responding. If the result shows an error, investigate and fix it.
3. Use multiple tools in sequence when needed. Break complex tasks into steps.
4. CRITICAL: When the user uploads a file, you MUST use the file_upload tool with file_path parameter to read it. NOT code_analyze, NOT file_read — use file_upload. Images are analyzed with Gemini Vision (OCR, charts, UI, screenshots). PDFs get text extracted. Text/code files are read directly. The file_upload tool is the ONLY way to read uploaded files.
5. Be proactive — if you notice something wrong on the server, mention it.
6. Keep responses concise but complete. Show the user what you did, not just the final answer.
7. ALWAYS use api_auto_route when a user describes a task that could be solved by an external API. You have 35K+ APIs at your disposal.
8. When you find an API, try calling it with smart_api_call to verify it works before recommending it.""")

    # List available uploaded files
    upload_info = []
    check_dir = uploads_dir or UPLOADS_DIR
    if os.path.exists(check_dir):
        for fname in sorted(os.listdir(check_dir))[:20]:
            fpath = os.path.join(check_dir, fname)
            if os.path.isfile(fpath):
                size = os.path.getsize(fpath)
                upload_info.append(f"- {fname} ({size} bytes)")
    if upload_info:
        parts.append("## User Uploaded Files\nIMPORTANT: These files exist in your uploads directory. To read them, you MUST call the file_upload tool with the file_path parameter set to the filename. Do NOT use code_analyze or any other tool.\nFiles:\n" + "\n".join(upload_info))
    
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
            # v10 security: validate command
            ok, result_msg = validate_command(cmd)
            if not ok:
                log_audit("system", "bash", "execute", cmd[:200], "blocked", 0)
                return f"Error: {result_msg}"
            import shlex
            start = time.time()
            result = subprocess.run(shlex.split(cmd), shell=False, capture_output=True, text=True, timeout=120)
            duration = (time.time() - start) * 1000
            output = result.stdout
            if result.stderr:
                output += f"\n[STDERR]\n{result.stderr}"
            if result.returncode != 0:
                output += f"\n[EXIT: {result.returncode}]"
            log_audit("system", "bash", "execute", cmd[:200], "success" if result.returncode == 0 else "error", duration)
            return output[:8000] if output else "(no output)"

        elif name == "file_write":
            path = args.get("path", "")
            content = args.get("content", "")
            if not path:
                return "Error: no path"
            # v10 security: validate path
            ok, result_msg = validate_path(path, ALLOWED_BASE_DIRS)
            if not ok:
                log_audit("system", "file_write", "write", path[:200], "blocked", 0)
                return f"Error: {result_msg}"
            log_audit("system", "file_write", "write", path[:200], "success", 0)
            os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
            with open(path, "w") as f:
                f.write(content)
            return f"Wrote {len(content)} bytes to {path}"

        elif name == "file_read":
            path = args.get("path", "")
            if not path:
                return "Error: no path"
            # v10 security: validate path
            ok, result_msg = validate_path(path, ALLOWED_BASE_DIRS)
            if not ok:
                log_audit("system", "file_read", "read", path[:200], "blocked", 0)
                return f"Error: {result_msg}"
            if not os.path.exists(path):
                return f"File not found: {path}"
            log_audit("system", "file_read", "read", path[:200], "success", 0)
            with open(path) as f:
                return f.read()[:15000]

        elif name == "file_list":
            path = args.get("path", ".")
            recursive = args.get("recursive", False)
            # v10 security: validate path
            ok, result_msg = validate_path(path, ALLOWED_BASE_DIRS)
            if not ok:
                log_audit("system", "file_list", "read", path[:200], "blocked", 0)
                return f"Error: {result_msg}"
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
            filename = args.get("file_path", "") or args.get("filename", "")
            prompt = args.get("prompt", "")
            if not filename:
                return "Error: no filename provided. Use file_path parameter."
            safe_name = re.sub(r'[^a-zA-Z0-9._-]', '', filename)[:200]
            u_dir = uploads_dir or UPLOADS_DIR
            fpath = os.path.join(u_dir, safe_name)
            if not os.path.exists(fpath):
                fpath = os.path.join(u_dir, filename)
                if not os.path.exists(fpath):
                    avail = os.listdir(u_dir) if os.path.exists(u_dir) else []
                    return f"File not found: {filename}. Available: {avail}"
            ext = os.path.splitext(safe_name)[1].lower()
            text_exts = ['.txt', '.md', '.py', '.js', '.ts', '.json', '.yaml', '.yml', '.html', '.css', '.sh', '.xml', '.csv', '.log', '.sql', '.c', '.cpp', '.java', '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.scala', '.r', '.tex', '.toml', '.ini', '.cfg', '.conf', '.jsx', '.tsx', '.vue']
            if ext in text_exts:
                with open(fpath) as f:
                    content = f.read()[:20000]
                return f"--- File: {filename} ({os.path.getsize(fpath)} bytes) ---\n{content}"
            elif ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp']:
                if GOOGLE_API_KEY:
                    try:
                        import base64 as b64mod
                        with open(fpath, "rb") as img_f:
                            img_data = b64mod.b64encode(img_f.read()).decode()
                        mime = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".gif": "image/gif", ".webp": "image/webp", ".bmp": "image/bmp"}.get(ext, "image/png")
                        vision_prompt = prompt or "Analyze this image in detail. Describe what you see, any text (OCR), charts, diagrams, UI elements, or notable features."
                        gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={GOOGLE_API_KEY}"
                        # v10 security: validate URL (SSRF protection)
                        _ok, _msg = validate_url(gemini_url)
                        if not _ok:
                            return f"Error: SSRF blocked: {_msg}"
                        body = json.dumps({"contents": [{"parts": [{"text": vision_prompt}, {"inline_data": {"mime_type": mime, "data": img_data}}]}], "generationConfig": {"maxOutputTokens": 1000, "temperature": 0.4}}).encode()
                        req = urllib.request.Request(gemini_url, data=body, headers={"Content-Type": "application/json", "User-Agent": "EvolvixOS/9.2"})
                        with urllib.request.urlopen(req, timeout=60) as resp:
                            result = json.loads(resp.read())
                            text = result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "No analysis")
                            return f"--- Image: {filename} ({os.path.getsize(fpath)} bytes) ---\nGemini Vision Analysis:\n{text}"
                    except Exception as e:
                        return f"Image: {filename} ({os.path.getsize(fpath)} bytes). Vision error: {str(e)}"
                else:
                    return f"Image: {filename} ({os.path.getsize(fpath)} bytes). Gemini not configured. Path: {fpath}"
            elif ext == '.pdf':
                try:
                    import subprocess
                    # v10 fix: Use safe argument passing instead of string interpolation
                    pdf_code = 'import PyPDF2, sys; reader=PyPDF2.PdfReader(sys.argv[1]); print("\n".join([p.extract_text()[:5000] for p in reader.pages[:10]]))'
                    result = subprocess.run(['python3', '-c', pdf_code, fpath], capture_output=True, text=True, timeout=15)
                    if result.returncode == 0:
                        return f"--- PDF: {filename} ({os.path.getsize(fpath)} bytes) ---\n{result.stdout[:15000]}"
                    else:
                        return f"PDF: {filename} ({os.path.getsize(fpath)} bytes). PyPDF2 not available."
                except Exception as e:
                    return f"PDF: {filename} ({os.path.getsize(fpath)} bytes). Error: {str(e)}"
            else:
                try:
                    with open(fpath) as f:
                        content = f.read()[:20000]
                    return f"--- File: {filename} ({os.path.getsize(fpath)} bytes) ---\n{content}"
                except Exception:
                    return f"Binary file: {filename} ({os.path.getsize(fpath)} bytes). Type: {ext or 'unknown'}"

        elif name == "python_exec":
            code = args.get("code", "")
            if not code:
                return "Error: no code"
            # v10 security: validate Python code
            ok, result_msg = validate_python_code(code)
            if not ok:
                log_audit("system", "python_exec", "execute", code[:200], "blocked", 0)
                return f"Error: {result_msg}"
            start = time.time()
            result = subprocess.run(["python3", "-c", code], capture_output=True, text=True, timeout=120)
            duration = (time.time() - start) * 1000
            output = result.stdout
            if result.stderr:
                output += f"\n[STDERR]\n{result.stderr}"
            if result.returncode != 0:
                output += f"\n[EXIT: {result.returncode}]"
            log_audit("system", "python_exec", "execute", code[:200], "success" if result.returncode == 0 else "error", duration)
            return output[:8000] if output else "(no output)"

        elif name == "service_check":
            svc = sanitize_service_name(args.get("name", ""))
            if not svc:
                return "Error: invalid service name"
            # v10 security: audit log
            start = time.time()
            r = subprocess.run(["systemctl", "is-active", svc], capture_output=True, text=True)
            duration = (time.time() - start) * 1000
            log_audit("system", "service_check", "read", svc, "success", duration)
            return f"Service '{svc}' is {r.stdout.strip()}"

        elif name == "service_restart":
            # v10 security: admin permission required
            ok, msg = check_permission("service_restart", user_role="admin")
            if not ok:
                log_audit("system", "service_restart", "execute", str(args), "blocked", 0)
                return f"Error: {msg}"
            svc = sanitize_service_name(args.get("name", ""))
            if not svc:
                return "Error: invalid service name"
            start = time.time()
            r = subprocess.run(["systemctl", "restart", svc], capture_output=True, text=True)
            duration = (time.time() - start) * 1000
            log_audit("admin", "service_restart", "execute", svc, "success" if r.returncode == 0 else "error", duration)
            return f"Service '{svc}' restarted" if r.returncode == 0 else f"Error: {r.stderr}"

        elif name == "docker_ps":
            # v10 security: audit log
            start = time.time()
            r = subprocess.run(["docker", "ps", "-a", "--format", "{{.Names}}\t{{.Status}}\t{{.Ports}}"], capture_output=True, text=True)
            duration = (time.time() - start) * 1000
            log_audit("system", "docker_ps", "read", "list", "success", duration)
            return r.stdout or "No containers"

        elif name == "docker_restart":
            # v10 security: admin permission required
            ok, msg = check_permission("docker_restart", user_role="admin")
            if not ok:
                log_audit("system", "docker_restart", "execute", str(args), "blocked", 0)
                return f"Error: {msg}"
            cname = sanitize_service_name(args.get("name", ""))
            if not cname:
                return "Error: invalid container name"
            start = time.time()
            r = subprocess.run(["docker", "restart", cname], capture_output=True, text=True)
            duration = (time.time() - start) * 1000
            log_audit("admin", "docker_restart", "execute", cname, "success" if r.returncode == 0 else "error", duration)
            return f"Container '{cname}' restarted" if r.returncode == 0 else f"Error: {r.stderr}"

        elif name == "git":
            # v10 security: admin permission required
            ok, msg = check_permission("git", user_role="admin")
            if not ok:
                log_audit("system", "git", "execute", str(args), "blocked", 0)
                return f"Error: {msg}"
            repo = args.get("repo", "/opt/evolvixos")
            cmd = sanitize_git_command(args.get("command", ""))
            if not cmd:
                return "Error: invalid git command. Allowed: status, log, add, commit, push, pull, diff, branch, checkout, fetch, clone, init, remote, show"
            if not is_path_safe(repo):
                return "Error: repo path not allowed"
            start = time.time()
            r = subprocess.run(["git", "-C", repo] + cmd.split(), capture_output=True, text=True, timeout=30)
            duration = (time.time() - start) * 1000
            log_audit("admin", "git", "execute", cmd, "success" if r.returncode == 0 else "error", duration)
            return (r.stdout + r.stderr)[:5000] or "(no output)"

        elif name == "http_request":
            url = args.get("url", "")
            method = args.get("method", "GET")
            body = args.get("body")
            headers = args.get("headers", {})
            if not url or not url.startswith(("http://", "https://")):
                return "Error: invalid URL"
            # v10 security: SSRF protection
            ok, result_msg = validate_url(url)
            if not ok:
                log_audit("system", "http_request", "network", url[:200], "blocked", 0)
                return f"Error: {result_msg}"
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
            # v10 security: validate search URL
            ok, result_msg = validate_url(url)
            if not ok:
                log_audit("system", "web_search", "network", query[:200], "blocked", 0)
                return f"Error: {result_msg}"
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
            # v10 security: SSRF protection
            ok, result_msg = validate_url(url)
            if not ok:
                log_audit("system", "web_fetch", "network", url[:200], "blocked", 0)
                return f"Error: {result_msg}"
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
            # v10 security: audit skill execution
            start = time.time()
            r = subprocess.run(["bash", skill_path, skill_input], capture_output=True, text=True, timeout=120)
            duration = (time.time() - start) * 1000
            log_audit("system", "skill_exec", "execute", skill_name, "success" if r.returncode == 0 else "error", duration)
            output = r.stdout
            if r.stderr:
                output += f"\n[STDERR]\n{r.stderr}"
            return output[:8000] if output else "(skill ran with no output)"

        elif name == "code_analyze":
            path = args.get("path", "") or args.get("file_path", "") or args.get("filename", "")
            if not path:
                return "Error: no file path provided"
            # Check uploads dir as fallback
            u_dir = uploads_dir or UPLOADS_DIR
            if not os.path.exists(path):
                for candidate in [os.path.join(u_dir, path), os.path.join(u_dir, re.sub(r'[^a-zA-Z0-9._-]', '', path)[:200])]:
                    if os.path.exists(candidate):
                        path = candidate
                        break
            if not os.path.exists(path):
                avail = os.listdir(u_dir) if os.path.exists(u_dir) else []
                return f"File not found: {path}. Uploaded files: {avail}"
            if not is_path_safe(path):
                return f"Error: path '{path}' is outside allowed directories"
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
            # v10 security: admin permission required (installs system packages)
            ok, msg = check_permission("pip_install", user_role="admin")
            if not ok:
                log_audit("system", "pip_install", "execute", str(args), "blocked", 0)
                return f"Error: {msg}"
            package = re.sub(r'[^a-zA-Z0-9_.>=<\-]', '', args.get("package", ""))[:100]
            if not package:
                return "Error: package name required"
            start = time.time()
            r = subprocess.run(["pip3", "install", package], capture_output=True, text=True, timeout=120)
            duration = (time.time() - start) * 1000
            log_audit("admin", "pip_install", "execute", package, "success" if r.returncode == 0 else "error", duration)
            output = r.stdout + r.stderr
            if r.returncode == 0:
                return f"Successfully installed {package}\n{output[-500:]}"
            else:
                return f"Failed to install {package}: {output[-500:]}"

        elif name == "search_ai_tools":
            query = args.get("query", "").lower()
            category = args.get("category", "all")
            try:
                with open("/opt/evolvixos/models/free_ai_tools_registry.json") as f:
                    reg = json.load(f)
                tools = reg.get("tools", [])
                if category != "all":
                    tools = [t for t in tools if t.get("category") == category]
                if query:
                    scored = []
                    for t in tools:
                        score = 0
                        searchable = (t.get("name", "") + " " + t.get("shortDescription", "") + " " + " ".join(t.get("tags", [])) + " " + " ".join(t.get("models", []))).lower()
                        for word in query.split():
                            if len(word) > 2 and word in searchable:
                                score += 1
                        if t.get("featured"):
                            score += 0.5
                        if t.get("pricing", {}).get("type") in ("free", "open-source"):
                            score += 0.3
                        scored.append((score, t))
                    scored.sort(key=lambda x: -x[0])
                    tools = [t for s, t in scored if s > 0][:15]
                else:
                    tools = [t for t in tools if t.get("featured")][:15]

                result_parts = [f"AI Tools Registry: {len(tools)} matches (of {reg.get('total_tools', 0)} total, {reg.get('total_categories', 0)} categories)"]
                for t in tools:
                    pricing = t.get("pricing", {})
                    result_parts.append(f"\n---\n[{t.get('name', '?')}] ({t.get('category', '?')})\n  {t.get('shortDescription', '')}\n  Pricing: {pricing.get('type', '?')} | Free: {pricing.get('freeTier', 'N/A')[:80]}\n  Card required: {pricing.get('creditCardRequired', '?')} | OSS: {t.get('openSource', False)}\n  Models: {', '.join(t.get('models', [])[:5])}\n  Website: {t.get('website', '')}")
                return "\n".join(result_parts)
            except Exception as e:
                return f"Error searching AI tools: {e}"

        elif name == "gemini_vision":
            import base64 as b64mod
            image_path = args.get("image_path", "")
            prompt = args.get("prompt", "Describe this image")
            if not GOOGLE_API_KEY:
                return "Gemini API key not configured"
            try:
                if image_path.startswith("http"):
                    req_img = urllib.request.Request(image_path, headers={"User-Agent": "EvolvixOS/9.2"})
                    with urllib.request.urlopen(req_img, timeout=30) as img_resp:
                        img_data = b64mod.b64encode(img_resp.read()).decode()
                else:
                    with open(image_path, "rb") as f:
                        img_data = b64mod.b64encode(f.read()).decode()
                ext = image_path.split(".")[-1].lower() if "." in image_path else "png"
                mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "gif": "image/gif", "webp": "image/webp"}.get(ext, "image/png")
                gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={GOOGLE_API_KEY}"
                # v10 security: validate URL (SSRF protection)
                _ok, _msg = validate_url(gemini_url)
                if not _ok:
                    return f"Error: SSRF blocked: {_msg}"
                body = json.dumps({"contents": [{"parts": [{"text": prompt}, {"inline_data": {"mime_type": mime, "data": img_data}}]}], "generationConfig": {"maxOutputTokens": 500, "temperature": 0.7}}).encode()
                req = urllib.request.Request(gemini_url, data=body, headers={"Content-Type": "application/json", "User-Agent": "EvolvixOS/9.2"})
                with urllib.request.urlopen(req, timeout=30) as resp:
                    result = json.loads(resp.read())
                    text = result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "No response")
                    return text
            except Exception as e:
                return f"Gemini vision error: {str(e)}"
        
        elif name == "gemini_tts":
            text = args.get("text", "")
            voice = args.get("voice", "neutral")
            if not GOOGLE_API_KEY:
                return "Gemini API key not configured"
            if not text:
                return "No text provided"
            try:
                gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-tts:generateContent?key={GOOGLE_API_KEY}"
                body = json.dumps({"contents": [{"parts": [{"text": text}]}], "generationConfig": {"responseModalities": ["AUDIO"], "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}}}}).encode()
                req = urllib.request.Request(gemini_url, data=body, headers={"Content-Type": "application/json", "User-Agent": "EvolvixOS/9.2"})
                with urllib.request.urlopen(req, timeout=30) as resp:
                    result = json.loads(resp.read())
                    audio_parts = result.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                    import base64 as b64mod
                    for part in audio_parts:
                        if "inlineData" in part:
                            audio_data = b64mod.b64decode(part["inlineData"]["data"])
                            output_path = f"/tmp/tts_{int(time.time())}.wav"
                            with open(output_path, "wb") as f:
                                f.write(audio_data)
                            return f"TTS audio saved to {output_path} ({len(audio_data)} bytes)"
                    return "TTS completed but no audio found"
            except Exception as e:
                return f"Gemini TTS error: {str(e)}"
        
        elif name == "search_apis":
            query = args.get("query", "").lower()
            category = args.get("category", "")
            try:
                with open("/opt/evolvixos/models/openclaw_apis.json") as f:
                    reg = json.load(f)
                total = reg.get("total_apis", 0)
                cat_dict = reg.get("categories", {})
                if isinstance(cat_dict, dict):
                    cat_items = list(cat_dict.items())
                else:
                    cat_items = [(c.get("name", "?"), c.get("count", 0)) for c in cat_dict]
                result_parts = [f"API Directory: {total} APIs across {len(cat_items)} categories"]

                # Search the actual API list for individual API matches
                all_apis = reg.get("apis", [])
                if isinstance(all_apis, list):
                    api_matches = []
                    for api in all_apis:
                        if isinstance(api, dict):
                            score = 0
                            searchable = (api.get("name", "") + " " + api.get("description", "")).lower()
                            for word in query.split():
                                if len(word) > 2 and word in searchable:
                                    score += 1
                            if score > 0:
                                api_matches.append((score, api))
                    api_matches.sort(key=lambda x: -x[0])
                    for score, api in api_matches[:10]:
                        result_parts.append(f"\n---\n[{api.get('name','?')}] ({api.get('category','?')})\n  {api.get('description','')[:150]}\n  URL: {api.get('url','')}")

                if category:
                    for cat_name, cat_count in cat_items:
                        if category.lower() in cat_name.lower():
                            result_parts.append(f"\n---\n[{cat_name}] ({cat_count} APIs)")
                            return "\n".join(result_parts)
                else:
                    scored = []
                    for cat_name, cat_count in cat_items:
                        score = 0
                        for word in query.split():
                            if len(word) > 2 and word in cat_name.lower():
                                score += 1
                        if score > 0:
                            scored.append((score, cat_name, cat_count))
                    scored.sort(key=lambda x: -x[0])
                    for s, cat_name, cat_count in scored[:5]:
                        result_parts.append(f"\n  [{cat_name}] ({cat_count} APIs)")
                return "\n".join(result_parts)
            except Exception as e:
                return f"Error searching APIs: {e}"

        elif name == "free_llm_providers":
            filt = args.get("filter", "all")
            try:
                with open("/opt/evolvixos/models/freellm_registry.json") as f:
                    reg = json.load(f)
                providers = reg.get("providers", [])
                if filt == "no-credit-card":
                    providers = [p for p in providers if p.get("credit_card", "").lower() in ("no", "no ")]
                elif filt == "vision":
                    providers = [p for p in providers if "vision" in str(p.get("modalities", [])).lower()]
                elif filt == "fast":
                    providers = [p for p in providers if any(w in p.get("name", "").lower() for w in ["groq", "cerebras", "cloudflare"])]
                elif filt == "coding":
                    providers = [p for p in providers if any("code" in m.lower() for m in p.get("models", []))]

                result_parts = [f"Free LLM Providers: {len(providers)} matching (of {reg.get('total_providers', 0)} total, {reg.get('total_free_models', 0)} free models)"]
                for p in providers[:15]:
                    result_parts.append(f"\n---\n[{p.get('name', '?')}] ({p.get('free_models', '?')} free models)\n  Tier: {p.get('tier', '?')}\n  Card: {p.get('credit_card', '?')}\n  Context: {p.get('max_context', 'N/A')}\n  Modalities: {', '.join(p.get('modalities', [])[:5])}\n  Base URL: {p.get('base_url', 'N/A')}\n  Get key: {p.get('key_url', 'N/A')}")
                return "\n".join(result_parts)
            except Exception as e:
                return f"Error listing free LLM providers: {e}"

        elif name == "search_learn":
            query = args.get("query", "").lower()
            try:
                with open("/opt/evolvixos/models/lovable_course_full.json") as f:
                    reg = json.load(f)
                modules = reg.get("modules", reg.get("course_modules", []))
                scored = []
                for m in modules:
                    score = 0
                    m_text = (m.get("title", "") + " " + m.get("description", "")).lower()
                    for word in query.split():
                        if len(word) > 2 and word in m_text:
                            score += 1
                    scored.append((score, m))
                scored.sort(key=lambda x: -x[0])
                relevant = [m for s, m in scored if s > 0][:5]
                if not relevant:
                    relevant = modules[:5]

                result_parts = [f"Learning Hub: {len(relevant)} relevant modules (of {reg.get('total_modules', 0)} total)"]
                for m in relevant:
                    result_parts.append(f"\n---\n[Module {m.get('id', '?')}] {m.get('title', '?')}\n  {m.get('description', '')}\n  Topics: {', '.join(m.get('topics', [])[:5])}\n  Difficulty: {m.get('difficulty', 'N/A')}")
                return "\n".join(result_parts)
            except Exception as e:
                return f"Error searching learning hub: {e}"

        elif name == "image_gen_api_info":
            try:
                with open("/opt/evolvixos/models/image_gen_api.json") as f:
                    reg = json.load(f)
                result_parts = [f"Free Image Generation API ({reg.get('title', '')})"]
                result_parts.append(f"\nModels ({len(reg.get('models', []))} available):")
                for m in reg.get("models", []):
                    result_parts.append(f"  - {m}")
                result_parts.append(f"\nDeployment Steps:")
                for s in reg.get("deployment_steps", []):
                    result_parts.append(f"  {s.get('step', '?')}. {s.get('title', '')}: {s.get('desc', '')}")
                result_parts.append(f"\nPricing: {reg.get('pricing', {}).get('freeTier', '100K/day free')}")
                result_parts.append(f"\ncURL example:\n{reg.get('usage_examples', {}).get('curl', 'N/A')}")
                return "\n".join(result_parts)
            except Exception as e:
                return f"Error getting image gen API info: {e}"

        elif name == "smart_api_call":
            url = args.get("url", "")
            method = args.get("method", "GET").upper()
            headers = args.get("headers", {})
            body = args.get("body", {})
            timeout = min(args.get("timeout", 30), 60)
            if not url or not url.startswith("http"):
                return "Error: valid URL required (must start with http:// or https://)"
            # v10 security: SSRF protection
            ok, result_msg = validate_url(url)
            if not ok:
                log_audit("system", "smart_api_call", "network", url[:200], "blocked", 0)
                return f"Error: {result_msg}"
            try:
                if method == "GET":
                    req = urllib.request.Request(url, headers=headers or None)
                else:
                    data = json.dumps(body).encode() if body else None
                    req = urllib.request.Request(url, data=data, method=method, headers={**{"Content-Type": "application/json"}, **headers})
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    status = resp.getcode()
                    content_type = resp.headers.get("Content-Type", "")
                    raw = resp.read()
                    if "json" in content_type:
                        try:
                            parsed = json.loads(raw)
                            return json.dumps(parsed, indent=2)[:8000]
                        except Exception:
                            pass
                    return f"[{status}] {content_type}\n{raw.decode('utf-8', errors='replace')[:8000]}"
            except urllib.error.HTTPError as e:
                body_text = ""
                try:
                    body_text = e.read().decode('utf-8', errors='replace')[:2000]
                except Exception:
                    pass
                return f"HTTP {e.code} {e.reason}\n{body_text}"
            except Exception as e:
                return f"API call error: {e}"

        elif name == "call_free_llm":
            prompt_text = args.get("prompt", "")
            provider = args.get("provider", "auto")
            sys_prompt = args.get("system_prompt", "")
            model_override = args.get("model", "")
            if not prompt_text:
                return "Error: prompt is required"
            # v10 security: validate provider URL before calling
            provider_urls = {
                "groq": "https://api.groq.com/openai/v1/chat/completions",
                "gemini": "https://generativelanguage.googleapis.com/v1beta/models",
                "kimi": "https://api.moonshot.ai/v1/chat/completions",
            }
            prov_lower = provider.lower() if provider != "auto" else ""
            if prov_lower in provider_urls:
                ok, result_msg = validate_url(provider_urls[prov_lower])
                if not ok:
                    log_audit("system", "call_free_llm", "network", provider, "blocked", 0)
                    return f"Error: {result_msg}"

            # Load free LLM providers
            try:
                with open("/opt/evolvixos/models/freellm_registry.json") as f:
                    fl_reg = json.load(f)
                all_providers = fl_reg.get("providers", [])
            except Exception:
                return "Error: Could not load free LLM registry"

            # Check if Kimi API key is available (already configured in the env)
            kimi_key = os.environ.get("KIMI_API_KEY", "")
            if kimi_key and provider == "auto":
                # Kimi is already configured - use it as a fallback option
                pass

            # Provider configurations with env var keys
            provider_configs = {
                "groq": {
                    "name_match": ["groq"],
                    "base_url": "https://api.groq.com/openai/v1/chat/completions",
                    "key_env": "GROQ_API_KEY",
                    "default_model": "openai/gpt-oss-20b",
                    "speed": "fast"
                },
                "gemini": {
                    "name_match": ["gemini", "google"],
                    "base_url": "https://generativelanguage.googleapis.com/v1beta/models",
                    "key_env": "GEMINI_API_KEY",
                    "default_model": "gemini-2.0-flash",
                    "speed": "medium"
                },
                "nvidia": {
                    "name_match": ["nvidia"],
                    "base_url": "https://integrate.api.nvidia.com/v1/chat/completions",
                    "key_env": "NVIDIA_API_KEY",
                    "default_model": "meta/llama-3.1-405b-instruct",
                    "speed": "medium"
                },
                "cerebras": {
                    "name_match": ["cerebras"],
                    "base_url": "https://api.cerebras.ai/v1/chat/completions",
                    "key_env": "CEREBRAS_API_KEY",
                    "default_model": "llama-3.1-8b-instruct",
                    "speed": "ultra-fast"
                },
                "modelscope": {
                    "name_match": ["modelscope"],
                    "base_url": "https://api-inference.modelscope.cn/v1/chat/completions",
                    "key_env": "MODELSCOPE_API_KEY",
                    "default_model": "Qwen/Qwen2.5-72B-Instruct",
                    "speed": "medium"
                },
                "cloudflare": {
                    "name_match": ["cloudflare"],
                    "base_url": "https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/",
                    "key_env": "CLOUDFLARE_API_KEY",
                    "default_model": "@cf/meta/llama-3.1-8b-instruct",
                    "speed": "fast"
                },
                "kimi": {
                    "name_match": ["kimi", "moonshot"],
                    "base_url": "https://api.moonshot.ai/v1/chat/completions",
                    "key_env": "KIMI_API_KEY",
                    "default_model": "moonshot-v1-32k",
                    "speed": "medium"
                }
            }

            # Auto-select best provider
            if provider == "auto":
                # Check which keys are available
                available = []
                for p_name, p_config in provider_configs.items():
                    key = os.environ.get(p_config["key_env"], "")
                    if key:
                        available.append((p_name, p_config))

                if not available:
                    # No API keys configured
                    keys_needed = [p["key_env"] for p in provider_configs.values()]
                    return ("No free LLM API keys configured. Set one of these env vars and restart:\n"
                            + "\n".join(f"  - {k} (get from provider)" for k in keys_needed[:4])
                            + "\n\nEasiest: Groq (free, 276 tok/s, no credit card) at https://console.groq.com/keys\n"
                            + "Or Gemini (free, vision+multimodal) at https://aistudio.google.com/app/apikey")

                # Pick fastest available for simple, most capable for complex
                if len(prompt_text) > 2000:
                    # Long context - prefer nvidia or modelscope
                    for p_name, p_config in available:
                        if p_name in ("nvidia", "modelscope"):
                            provider = p_name
                            break
                else:
                    # Short prompt - prefer fastest
                    for p_name, p_config in available:
                        if p_name in ("cerebras", "groq"):
                            provider = p_name
                            break
                    if provider == "auto":
                        provider = available[0][0]

            # Get provider config
            p_config = provider_configs.get(provider)
            if not p_config:
                return f"Unknown provider: {provider}. Available: {list(provider_configs.keys())}"

            api_key = os.environ.get(p_config["key_env"], "")
            if not api_key:
                key_url = ""
                for p in all_providers:
                    if any(m in p.get("name", "").lower() for m in p_config["name_match"]):
                        key_url = p.get("key_url", "")
                        break
                return f"No API key for {provider}. Set env var {p_config['key_env']}.\nGet key at: {key_url or 'see provider website'}"

            model = model_override or p_config["default_model"]

            # Make the API call (OpenAI-compatible format for most)
            try:
                messages = []
                if sys_prompt:
                    messages.append({"role": "system", "content": sys_prompt})
                messages.append({"role": "user", "content": prompt_text})

                body = json.dumps({
                    "model": model,
                    "messages": messages,
                    "max_tokens": 4096,
                    "temperature": 0.7
                }).encode()

                if p_config.get("format") == "gemini":
                    model = p_config.get("default_model", "gemini-3.6-flash")
                    gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
                    gemini_body = json.dumps({
                        "contents": [{"parts": [{"text": task}]}],
                        "generationConfig": {"maxOutputTokens": 500, "temperature": 0.7}
                    }).encode()
                    req = urllib.request.Request(gemini_url, data=gemini_body, headers={"Content-Type": "application/json", "User-Agent": "EvolvixOS/9.2"})
                else:
                    req = urllib.request.Request(
                        p_config["base_url"],
                        data=body,
                        headers={
                            "Content-Type": "application/json",
                            "Authorization": f"Bearer {api_key}",
                            "User-Agent": "EvolvixOS/9.2"
                        }
                    )
                with urllib.request.urlopen(req, timeout=60) as resp:
                    result = json.loads(resp.read())
                    response_text = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                    usage = result.get("usage", {})
                    return f"[{provider} | {model}]\n{response_text}\n\n---\nTokens: {usage.get('total_tokens', '?')}"
            except urllib.error.HTTPError as e:
                err_body = ""
                try:
                    err_body = e.read().decode('utf-8', errors='replace')[:500]
                except Exception:
                    pass
                return f"Free LLM error ({provider}, HTTP {e.code}): {err_body}"
            except Exception as e:
                return f"Free LLM call failed ({provider}): {e}"

        elif name == "api_auto_route":
            task = args.get("task", "").lower()
            prefer_free = args.get("prefer_free", True)
            if not task:
                return "Error: task description is required"

            # Search both registries simultaneously
            results = []

            # 1. Search API directory (35K+ APIs)
            try:
                with open("/opt/evolvixos/models/openclaw_apis.json") as f:
                    api_reg = json.load(f)
                all_apis = api_reg.get("apis", {})
                total_apis = api_reg.get("total_apis", 0)

                if isinstance(all_apis, dict):
                    for cat_name, api_list in all_apis.items():
                        for api in api_list:
                            if isinstance(api, dict):
                                score = 0
                                searchable = (api.get("name", "") + " " + api.get("description", "") + " " + api.get("category", "")).lower()
                                for word in task.split():
                                    if len(word) > 2 and word in searchable:
                                        score += 1
                                if score > 0:
                                    results.append({
                                        "source": "api_directory",
                                        "name": api.get("name", ""),
                                        "url": api.get("url", ""),
                                        "description": api.get("description", "")[:200],
                                        "category": api.get("category", ""),
                                        "score": score,
                                        "type": api.get("type", "api")
                                    })
            except Exception:
                pass

            # 2. Search AI Tools registry (85+ tools)
            try:
                with open("/opt/evolvixos/models/free_ai_tools_registry.json") as f:
                    tools_reg = json.load(f)
                for t in tools_reg.get("tools", []):
                    score = 0
                    searchable = (t.get("name", "") + " " + t.get("shortDescription", "") + " " + " ".join(t.get("tags", [])) + " " + " ".join(t.get("models", []))).lower()
                    for word in task.split():
                        if len(word) > 2 and word in searchable:
                            score += 1
                    if score > 0:
                        pricing = t.get("pricing", {})
                        is_free = pricing.get("type") in ("free", "open-source")
                        if prefer_free and is_free:
                            score += 2
                        results.append({
                            "source": "ai_tools",
                            "name": t.get("name", ""),
                            "url": t.get("website", ""),
                            "description": t.get("shortDescription", ""),
                            "category": t.get("category", ""),
                            "pricing": pricing.get("type", "?"),
                            "free_tier": pricing.get("freeTier", "")[:100],
                            "score": score,
                            "type": "tool"
                        })
            except Exception:
                pass

            # Sort by score
            results.sort(key=lambda x: -x["score"])
            top = results[:15]

            if not top:
                return f"No APIs or tools found for: '{task}'. Try a different description or check the API directory manually."

            # Format results
            result_parts = [f"Smart API Router: Found {len(top)} matches for '{task}' (searched {total_apis} APIs + 85 AI tools)"]
            for i, r in enumerate(top):
                source_tag = r["source"].replace("api_directory", "API").replace("ai_tools", "TOOL")
                result_parts.append(
                    f"\n{i+1}. [{source_tag}] {r['name']}\n"
                    f"   URL: {r['url']}\n"
                    f"   {r['description'][:150]}\n"
                    f"   Category: {r.get('category', '?')} | Pricing: {r.get('pricing', '?')}"
                )

            # Add smart suggestion
            best = top[0]
            result_parts.append(
                f"\n---\nRECOMMENDED: {best['name']}\n"
                f"This is the best match for your task. Use smart_api_call to make a test request to the API URL above, "
                f"or visit the website to get setup instructions."
            )

            return "\n".join(result_parts)

        elif name == "team_memory_search":
            query = args.get("query", "")
            if not query:
                return "Error: no query"
            try:
                headers = {"Content-Type": "application/json", "Authorization": "Bearer local", "x-tdai-service-id": "default"}
                # Search both conversations (L0) and atomic memories (L1)
                search_body = json.dumps({"team_id": "default", "agent_id": "mr-james", "user_id": "default", "query": query, "limit": 5}).encode()
                req = urllib.request.Request(MEMORY_CORE_URL + "/v3/conversation/search", data=search_body, headers=headers)
                results = []
                try:
                    with urllib.request.urlopen(req, timeout=15) as resp:
                        conv_result = json.loads(resp.read())
                        if conv_result.get("code") == 0 and conv_result.get("data"):
                            results.append("Conversations: " + json.dumps(conv_result["data"])[:1500])
                except Exception as e:
                    results.append(f"Conv search: {str(e)[:100]}")
                # Also search atomic memories
                req2 = urllib.request.Request(MEMORY_CORE_URL + "/v3/atomic/search", data=search_body, headers=headers)
                try:
                    with urllib.request.urlopen(req2, timeout=15) as resp:
                        atom_result = json.loads(resp.read())
                        if atom_result.get("code") == 0 and atom_result.get("data"):
                            results.append("Memories: " + json.dumps(atom_result["data"])[:1500])
                except Exception as e:
                    results.append(f"Atomic search: {str(e)[:100]}")
                return "\n".join(results) if results else "No memories found for: " + query
            except Exception as e:
                return f"Memory search error: {str(e)}"

        elif name == "team_memory_save":
            content = args.get("content", "")
            category = args.get("category", "context")
            if not content:
                return "Error: no content"
            try:
                headers = {"Content-Type": "application/json", "Authorization": "Bearer local", "x-tdai-service-id": "default"}
                body = json.dumps({
                    "team_id": "default",
                    "agent_id": "mr-james",
                    "user_id": "default",
                    "session_id": "evolvix-session",
                    "messages": [
                        {"role": "user", "content": f"[SAVE] Category={category}: {content}"}
                    ]
                }).encode()
                req = urllib.request.Request(MEMORY_CORE_URL + "/v3/conversation/add", data=body, headers=headers)
                with urllib.request.urlopen(req, timeout=15) as resp:
                    result = json.loads(resp.read())
                return f"Saved to team memory: code={result.get('code', '?')}"
            except Exception as e:
                return f"Memory save error: {str(e)}"

        elif name == "sandbox_exec":
            code_str = args.get("code", "")
            language = args.get("language", "python")
            if not code_str:
                return "Error: no code provided"
            if not SANDBOX_ENABLED:
                # Fallback: run in Docker container for isolation
                try:
                    import subprocess
                    import tempfile
                    with tempfile.NamedTemporaryFile(mode="w", suffix=".py" if language == "python" else ".sh", delete=False) as f:
                        f.write(code_str)
                        temp_path = f.name
                    if language == "python":
                        result = subprocess.run(
                            ["docker", "run", "--rm", "--network=none", "--memory=512m", "--cpus=1",
                             "-v", temp_path + ":/tmp/code.py:ro", "evolvix-sandbox:latest",
                             "python", "/tmp/code.py"],
                            capture_output=True, text=True, timeout=30
                        )
                    else:
                        result = subprocess.run(
                            ["docker", "run", "--rm", "--network=none", "--memory=512m", "--cpus=1",
                             "-v", temp_path + ":/tmp/code.sh:ro", "evolvix-sandbox:latest",
                             "bash", "/tmp/code.sh"],
                            capture_output=True, text=True, timeout=30
                        )
                    os.unlink(temp_path)
                    output = result.stdout[-3000:] if result.stdout else ""
                    if result.stderr:
                        output += "\nSTDERR: " + result.stderr[-1000:]
                    return output if output else "Code executed successfully (no output)"
                except subprocess.TimeoutExpired:
                    return "Sandbox error: code execution timed out (30s limit)"
                except Exception as e:
                    return f"Sandbox fallback error: {str(e)}"
            else:
                # Use CubeSandbox MicroVM
                try:
                    from cubesandbox import Sandbox
                    with Sandbox(api_url=CUBE_API_URL, template=CUBE_TEMPLATE_ID) as sb:
                        if language == "python":
                            result = sb.run_code(code_str)
                        else:
                            result = sb.commands.run(code_str)
                        return result.text[-3000:] if hasattr(result, "text") else str(result)[:3000]
                except Exception as e:
                    return f"Sandbox error: {str(e)}"

        elif name == "tim_send_message":
            to_user = args.get("to_user", "")
            content = args.get("content", "")
            msg_type = args.get("msg_type", "text")
            if not to_user or not content:
                return "Error: to_user and content required"
            if not TIM_ENABLED:
                return "TIM not configured. Set TIM_SDK_APP_ID and TIM_SECRET_KEY env vars on the server."
            result = tim_client.send_message(to_user, content, msg_type)
            return json.dumps(result, indent=2)[:2000]

        elif name == "tim_create_group":
            group_name = args.get("group_name", "")
            group_type = args.get("group_type", "Public")
            if not group_name:
                return "Error: group_name required"
            if not TIM_ENABLED:
                return "TIM not configured. Set TIM_SDK_APP_ID and TIM_SECRET_KEY env vars on the server."
            result = tim_client.create_group(group_name, group_type)
            return json.dumps(result, indent=2)[:2000]

        elif name == "tim_send_group_message":
            group_id = args.get("group_id", "")
            content = args.get("content", "")
            if not group_id or not content:
                return "Error: group_id and content required"
            if not TIM_ENABLED:
                return "TIM not configured. Set TIM_SDK_APP_ID and TIM_SECRET_KEY env vars on the server."
            result = tim_client.send_group_message(group_id, content)
            return json.dumps(result, indent=2)[:2000]

        elif name == "tim_import_user":
            user_id = args.get("user_id", "")
            nickname = args.get("nickname", "")
            if not user_id:
                return "Error: user_id required"
            if not TIM_ENABLED:
                return "TIM not configured. Set TIM_SDK_APP_ID and TIM_SECRET_KEY env vars on the server."
            result = tim_client.import_account(user_id, nickname)
            return json.dumps(result, indent=2)[:2000]

        elif name == "search_subagents":
            query = args.get("query", "").lower()
            category = args.get("category", "")
            try:
                import json as _json
                index_path = "/opt/evolvixos/knowledge/subagents/index.json"
                if not os.path.exists(index_path):
                    return "Subagent library not indexed. Run indexing first."
                with open(index_path) as f:
                    idx = _json.load(f)
                results = []
                for item in idx:
                    if category and item.get("category") != category:
                        continue
                    name = item.get("name", "").lower()
                    desc = item.get("description", "").lower()
                    if query in name or query in desc or query in item.get("path", "").lower():
                        results.append(item)
                if not results:
                    return f"No subagent templates found for: {query}"
                out = f"Found {len(results)} subagent templates:\n"
                for r in results[:15]:
                    out += f"\n[{r['category']}] {r['name']}: {r['description']}\n  Path: {r['path']}\n"
                return out[:3000]
            except Exception as e:
                return f"Search error: {str(e)}"

        elif name == "set_persona":
            mbti_type = args.get("mbti_type", "INTJ").upper()
            custom_prompt = args.get("custom_prompt", "")
            try:
                if mbti_type in MBTI_PROFILES:
                    profile = MBTI_PROFILES[mbti_type]
                    persona_info = f"Persona set to {mbti_type} ({profile.name_en}): {profile.summary_en}\n"
                    persona_info += f"Answer style: {profile.behavior.answer_style}\n"
                    persona_info += f"Casual chat: {profile.behavior.casual_chat}\n"
                    persona_info += f"Conflict: {profile.behavior.conflict}\n"
                    persona_info += f"Creativity: {profile.behavior.creativity}\n"
                    persona_info += f"Emotion: {profile.behavior.emotion}\n"
                    persona_info += f"Planning: {profile.behavior.planning}\n"
                    if custom_prompt:
                        persona_info += f"\nCustom prompt: {custom_prompt}"
                    # Store in env for this session
                    os.environ["MR_JAMES_PERSONA"] = mbti_type
                    return persona_info
                else:
                    return f"Unknown MBTI type: {mbti_type}. Available: {', '.join(MBTI_PROFILES.keys())}"
            except Exception as e:
                return f"Persona error: {str(e)}"

        elif name == "tencent_cloud":
            service = args.get("service", "")
            action = args.get("action", "")
            params = args.get("params", {})
            region = args.get("region", "ap-frankfurt")
            if not service or not action:
                return "Error: service and action required"
            if not TC_ENABLED:
                return "Tencent Cloud not configured. Set TENCENTCLOUD_SECRET_ID and TENCENTCLOUD_SECRET_KEY env vars on the server."
            # Try Go binary first (faster), fall back to Python SDK
            try:
                import subprocess as _sp
                tccli = "/usr/local/bin/tccli"
                if os.path.exists(tccli):
                    cmd = [tccli, "--service", service, "--action", action, "--region", region, "--params", json.dumps(params)]
                    result = _sp.run(cmd, capture_output=True, text=True, timeout=15)
                    if result.returncode == 0 and result.stdout:
                        return result.stdout[:3000]
                    # Fall through to Python SDK on error
                    if result.returncode != 0 and "required" not in result.stderr:
                        return json.dumps({"error": result.stderr.strip()[:500]})
            except Exception as go_err:
                pass  # Fall back to Python SDK
            try:
                result = None
                if service == "cvm":
                    if action == "describe_instances":
                        result = tc_manager.cvm_describe_instances(region)
                    elif action == "describe_zones":
                        result = tc_manager.cvm_describe_zones(region)
                    elif action == "run_instances":
                        result = tc_manager.cvm_run_instances(params.get("zone",""), params.get("instance_type",""), params.get("image_id"), params.get("instance_name","evolvixos-instance"), region)
                    elif action == "start_instances":
                        result = tc_manager.cvm_start_instances(params.get("instance_ids",[]), region)
                    elif action == "stop_instances":
                        result = tc_manager.cvm_stop_instances(params.get("instance_ids",[]), region)
                    elif action == "reboot_instances":
                        result = tc_manager.cvm_reboot_instances(params.get("instance_ids",[]), region)
                elif service == "cdb":
                    if action == "describe_instances":
                        result = tc_manager.cdb_describe_instances(region)
                elif service == "vpc":
                    if action == "describe_vpcs":
                        result = tc_manager.vpc_describe_vpcs(region)
                    elif action == "describe_security_groups":
                        result = tc_manager.vpc_describe_security_groups(region)
                elif service == "ssl":
                    if action == "describe_certificates":
                        result = tc_manager.ssl_describe_certificates(params.get("limit",100))
                elif service == "dnspod":
                    if action == "describe_record_list":
                        result = tc_manager.dnspod_describe_record_list(params.get("domain",""), params.get("subdomain"))
                    elif action == "describe_domain_list":
                        result = tc_manager.dnspod_describe_domain_list()
                elif service == "cdn":
                    if action == "describe_domains":
                        result = tc_manager.cdn_describe_domains()
                elif service == "billing":
                    if action == "describe_bill_summary":
                        result = tc_manager.billing_describe_bill_summary(params.get("start_month",""), params.get("end_month",""))
                    elif action == "describe_account_balance":
                        result = tc_manager.billing_describe_account_balance()
                elif service == "cam":
                    if action == "list_users":
                        result = tc_manager.cam_list_users()
                elif service == "hunyuan":
                    if action == "chat":
                        result = tc_manager.hunyuan_chat(params.get("messages",[]), params.get("model","hunyuan-pro"))
                elif service == "aiart":
                    if action == "text_to_image":
                        result = tc_manager.aiart_text_to_image(params.get("prompt",""), params.get("styles"), params.get("result_config"))
                if result is not None:
                    return json.dumps(result, indent=2)[:3000]
                return f"Unknown action: {service}/{action}. Available: " + json.dumps(tc_manager.list_services())
            except Exception as e:
                return f"Tencent Cloud error: {str(e)}"

        else:
            return f"Unknown tool: {name}"

    except subprocess.TimeoutExpired:
        return f"Error: tool '{name}' timed out after 120s"
    except Exception as e:
        return f"Error in tool '{name}': {str(e)}"

# ─── Intent classification (v9.0 — smarter) ───
def classify_intent(prompt):
    """Delegate to v10 unified router. Returns (task_type, engine, model, reason)."""
    _init_v10()
    decision = _v10_router.route(prompt)
    # Map v10 provider name to old engine name
    provider = _v10_registry.get(decision.provider)
    engine = "ollama" if provider and provider.is_local else decision.provider
    return (decision.task_type, engine, decision.model, decision.reason)

def select_engine(prompt):
    """Delegate to v10 unified router."""
    return classify_intent(prompt)

# ─── Model API calls ───
def _normalize_messages_for_ollama(messages):
    """Ollama expects tool_calls[].function.arguments as a native object,
    but Groq/OpenAI-format providers return it as a JSON string. When
    cross-provider fallback echoes those messages back into Ollama, the
    Go JSON parser rejects the stringified arguments with a 400 error.
    This normalizes any string arguments to parsed objects, and drops
    None content (Ollama expects a string, not null)."""
    fixed = []
    for m in messages:
        m = dict(m)
        if m.get("content") is None:
            m["content"] = ""
        tcs = m.get("tool_calls")
        if tcs:
            new_tcs = []
            for tc in tcs:
                tc = dict(tc)
                func = dict(tc.get("function", {}))
                args = func.get("arguments")
                if isinstance(args, str):
                    try:
                        func["arguments"] = json.loads(args)
                    except Exception:
                        func["arguments"] = {}
                tc["function"] = func
                new_tcs.append(tc)
            m["tool_calls"] = new_tcs
        fixed.append(m)
    return fixed

def call_ollama_with_tools(model, messages, tools, stream=False):
    """Delegate to v10 OllamaProvider."""
    _init_v10()
    messages = _normalize_messages_for_ollama(messages)
    provider = _v10_registry.get("ollama")
    if provider and provider.is_available():
        try:
            resp = provider.chat(messages, tools=tools, stream=stream)
            if stream:
                # Return raw response object for streaming
                data = json.dumps({"model": model, "messages": messages, "tools": tools if tools else [], "stream": True, "options": {"temperature": 0.7, "top_p": 0.9}}).encode()
                req = urllib.request.Request(f"{OLLAMA_URL}/api/chat", data=data, headers={"Content-Type": "application/json"})
                return urllib.request.urlopen(req, timeout=180)
            return {"message": {"role": "assistant", "content": resp.content, "tool_calls": resp.tool_calls}}
        except Exception as e:
            print(f"v10 Ollama error: {e}, falling back to direct")
    # Fallback to direct call
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

def call_groq_with_tools(model, messages, tools, stream=False):
    """Delegate to v10 GroqProvider."""
    _init_v10()
    provider = _v10_registry.get("groq")
    if provider and provider.is_available():
        try:
            resp = provider.chat(messages, tools=tools, stream=stream)
            if stream:
                return None  # Streaming handled by caller
            # Convert to old format expected by agentic_loop: {"message": {...}}
            return {"message": {"role": "assistant", "content": resp.content, "tool_calls": resp.tool_calls}, "usage": resp.usage}
        except Exception as e:
            print(f"v10 Groq error: {e}")
    return None

def call_kimi(prompt, system_prompt, messages=None):
    """Delegate to v10 KimiProvider."""
    _init_v10()
    provider = _v10_registry.get("kimi")
    if provider and provider.is_available():
        try:
            all_messages = []
            if system_prompt:
                all_messages.append({"role": "system", "content": system_prompt})
            if messages:
                all_messages.extend(messages)
            all_messages.append({"role": "user", "content": prompt})
            resp = provider.chat(all_messages)
            return resp.content
        except Exception as e:
            print(f"v10 Kimi error: {e}")
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
    system_prompt = build_system_prompt(mem_dir=mem_dir, user_email=user_email, user_name=user_name, uploads_dir=uploads_dir)
    history = get_conversation(session_id, conv_dir=conv_dir)
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": prompt})
    
    intent, engine, model_sel, reason = select_engine(prompt)
    # Use classified model for the first turn, but keep it configurable
    if engine == "groq":
        model = model_sel if model_sel else "openai/gpt-oss-20b"
    elif not model or model == "qwen2.5:14b":
        model = model_sel if model_sel.startswith("qwen") else "qwen2.5:14b"
    
    if on_event:
        on_event("engine", {"engine": engine, "model": model, "intent": intent, "reason": reason})
    
    tools_used = 0
    errors_encountered = 0
    tool_results_summary = []
    
    last_tool_name = None
    last_tool_args = None
    repeat_count = 0
    
    for turn in range(max_turns):
        if on_event:
            on_event("thinking", {"turn": turn + 1})
        
        # Use simpler model for later turns to save CPU
        current_model = model if turn < 3 else "qwen2.5:7b" if model == "qwen2.5:14b" else model
        
        try:
            # After 3 turns, remove tools to force a text response
            active_tools = TOOLS if turn < 3 else []
            if engine == "groq":
                result = call_groq_with_tools(model, messages, active_tools, stream=False)
                if result is None:
                    result = call_ollama_with_tools("qwen2.5:14b", messages, active_tools, stream=False)
            else:
                result = call_ollama_with_tools(current_model, messages, active_tools, stream=False)
        except Exception as e:
            # Fallback to smaller model
            try:
                result = call_ollama_with_tools("qwen2.5:7b", messages, TOOLS, stream=False)
            except Exception as e2:
                # Last resort: try 3b
                try:
                    result = call_ollama_with_tools("qwen2.5:3b", messages, TOOLS, stream=False)
                except Exception as e3:
                    # Last resort: try free LLM API if available
                    groq_key = os.environ.get("GROQ_API_KEY", "")
                    if groq_key:
                        try:
                            fl_body = json.dumps({
                                "model": "openai/gpt-oss-20b",
                                "messages": messages,
                                "max_tokens": 4096,
                                "temperature": 0.7
                            }).encode()
                            # v10 security: validate URL (SSRF protection)
                            _groq_url = "https://api.groq.com/openai/v1/chat/completions"
                            _ok, _msg = validate_url(_groq_url)
                            if not _ok:
                                raise Exception(f"SSRF blocked: {_msg}")
                            fl_req = urllib.request.Request(
                                _groq_url,
                                data=fl_body,
                                headers={"Content-Type": "application/json", "Authorization": f"Bearer {groq_key}", "User-Agent": "EvolvixOS/9.2"}
                            )
                            with urllib.request.urlopen(fl_req, timeout=60) as fl_resp:
                                fl_result = json.loads(fl_resp.read())
                                fl_content = fl_result.get("choices", [{}])[0].get("message", {}).get("content", "")
                                if fl_content:
                                    messages.append({"role": "assistant", "content": fl_content})
                                    if on_event:
                                        on_event("text", {"text": fl_content})
                                    history.append({"role": "user", "content": prompt})
                                    history.append({"role": "assistant", "content": fl_content})
                                    save_conversation(session_id, history, conv_dir=conv_dir)
                                    on_event("done", {"response": fl_content, "tools_used": tools_used, "turns": turn + 1, "engine": "groq-fallback", "errors": errors_encountered})
                                    return {"response": fl_content, "engine": "groq-fallback", "model": "gpt-oss-20b", "status": "success", "turns": turn + 1, "tools_used": tools_used, "intent": intent, "errors": errors_encountered}
                        except Exception:
                            pass
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
            _tc_id = tc.get("id") or f"call_{tools_used}"
            _truncated = result_text[:2000] if len(result_text) > 2000 else result_text
            if len(result_text) > 2000:
                _truncated += "\n... (truncated, full result: " + str(len(result_text)) + " chars)"
            messages.append({"role": "tool", "content": _truncated, "name": tool_name, "tool_call_id": _tc_id})
    
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
        if self.path == "/api/tim/status":
            status = {"configured": TIM_ENABLED, "sdk_app_id": tim_client.sdk_app_id if TIM_ENABLED else ""}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(status).encode())
            return

        if self.path == "/api/health":
            self.respond(200, {
                "status": "online",
                "comfyui": self._check(COMFYUI_URL + "/system_stats"),
                "omniroute": self._check("http://127.0.0.1:20128/"),
                "ollama": self._check(OLLAMA_URL + "/api/tags"),
                "art_engine": self._check(ART_ENGINE_URL + "/api/status"),
                "models_registered": sum(1 for _ in open("/opt/evolvixos/models/model_registry.json")) if False else 81,
                "james_version": "10.0",
                "tools_available": len(TOOLS),
                "v10_enabled": True,
                "v10_privacy_mode": V10_PRIVACY_MODE,
                "v10_providers": _v10_registry.list_available() if _v10_registry else [],
                "v10_provider_details": _v10_registry.list_providers() if _v10_registry else [],
                "kimi_available": bool(KIMI_API_KEY),
                "memories_stored": len([f for f in os.listdir(MEMORY_DIR) if f.endswith(".json")]) if os.path.exists(MEMORY_DIR) else 0,
                "conversations": len([f for f in os.listdir(CONVERSATION_DIR) if f.endswith(".json")]) if os.path.exists(CONVERSATION_DIR) else 0,
                "uploads": len(os.listdir(UPLOADS_DIR)) if os.path.exists(UPLOADS_DIR) else 0,
                "capabilities": [
                    "video_generation", "image_generation", "image_control",
                    "animation", "audio_tts", "audio_stt", "music",
                    "vision", "3d", "rag", "video_edit", "coding",
                    "chat", "code", "crypto", "comfyui", "omniroute",
                    "tool_discovery", "api_discovery", "freellm_routing",
                    "learning_hub", "image_gen_deploy",
                    "smart_api_call", "free_llm_fallback", "api_auto_route"
                ],
                "groq_available": bool(os.environ.get("GROQ_API_KEY", "")),
                "gemini_available": bool(GOOGLE_API_KEY),
                "kimi_available": bool(KIMI_API_KEY),
                "registries": {
                    "ai_tools": 85,
                    "freellm_providers": 31,
                    "freellm_models": 442,
                    "apis": 35192,
                    "learn_modules": 19,
                    "image_gen_models": 6,
                    "total_searchable": 35277
                }
            })
        elif self.path == "/api/models":
            # Public endpoint — model registry is public data
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
        elif self.path == "/api/openclaw" or self.path.startswith("/api/openclaw?"):
            import urllib.parse as up
            qs = up.parse_qs(up.urlparse(self.path).query)
            cat_filter = qs.get("category", [None])[0]
            search_q = qs.get("q", [None])[0]
            limit = int(qs.get("limit", ["50"])[0])
            offset = int(qs.get("offset", ["0"])[0])
            try:
                with open("/opt/evolvixos/models/openclaw_apis.json") as f:
                    reg = json.load(f)
                apis = reg.get("apis", [])
                if cat_filter and cat_filter != "all":
                    apis = [a for a in apis if a["category"].lower() == cat_filter.lower()]
                if search_q:
                    q = search_q.lower()
                    apis = [a for a in apis if q in a["name"].lower() or q in a["description"].lower() or q in a["category"].lower()]
                total = len(apis)
                cats = {}
                for a in reg.get("apis", []):
                    cats[a["category"]] = cats.get(a["category"], 0) + 1
                paginated = apis[offset:offset + limit]
                self.respond(200, {
                    "total": total, "limit": limit, "offset": offset,
                    "categories": cats,
                    "source": "openclaw-api-list",
                    "source_url": "https://github.com/cporter202/openclaw-api-list",
                    "apis": paginated
                })
            except Exception as e:
                self.respond(500, {"error": str(e)})
        elif self.path == "/api/openclaw/categories":
            try:
                with open("/opt/evolvixos/models/openclaw_apis.json") as f:
                    reg = json.load(f)
                self.respond(200, {
                    "total_apis": reg.get("total_apis", 0),
                    "categories": reg.get("categories", {}),
                    "last_updated": reg.get("last_updated", ""),
                    "source": "openclaw-api-list"
                })
            except Exception as e:
                self.respond(500, {"error": str(e)})
        elif self.path == "/api/image-gen":
            try:
                with open("/opt/evolvixos/models/image_gen_api.json", "r") as f:
                    self.respond(200, json.load(f))
            except Exception as e:
                self.respond(500, {"error": str(e)})
        elif self.path == "/api/ai-tools":
            try:
                with open("/opt/evolvixos/models/free_ai_tools_registry.json", "r") as f:
                    self.respond(200, json.load(f))
            except Exception as e:
                self.respond(500, {"error": str(e)})
        elif self.path.startswith("/api/ai-tools/"):
            sub = self.path.split("/api/ai-tools/")[1].split("?")[0]
            try:
                with open("/opt/evolvixos/models/free_ai_tools_registry.json", "r") as f:
                    reg = json.load(f)
                if sub == "categories":
                    self.respond(200, {"categories": reg["categories"], "total": reg["total_categories"]})
                elif sub == "stacks":
                    self.respond(200, {"stacks": reg["stacks"], "total": reg["total_stacks"]})
                elif sub.startswith("category/"):
                    cat_id = sub.split("category/")[1]
                    tools = [t for t in reg["tools"] if t.get("category") == cat_id]
                    self.respond(200, {"category": cat_id, "tools": tools, "total": len(tools)})
                elif sub.startswith("tool/"):
                    tool_id = sub.split("tool/")[1]
                    tool = next((t for t in reg["tools"] if t["id"] == tool_id), None)
                    if tool:
                        self.respond(200, tool)
                    else:
                        self.respond(404, {"error": "Tool not found"})
                else:
                    self.respond(404, {"error": f"Unknown endpoint: {sub}"})
            except Exception as e:
                self.respond(500, {"error": str(e)})
        elif self.path == "/api/freellm":
            try:
                with open("/opt/evolvixos/models/freellm_registry.json", "r") as f:
                    self.respond(200, json.load(f))
            except Exception as e:
                self.respond(500, {"error": str(e)})
        elif self.path.startswith("/api/freellm/"):
            sub = self.path.split("/api/freellm/")[1].split("?")[0]
            try:
                with open("/opt/evolvixos/models/freellm_registry.json", "r") as f:
                    reg = json.load(f)
                if sub == "providers":
                    self.respond(200, {"providers": reg["providers"], "total": reg["total_providers"]})
                elif sub == "models":
                    self.respond(200, {"models": reg["best_models"], "total": reg["total_models"]})
                elif sub == "local":
                    self.respond(200, {"local_tools": reg["local_tools"], "total": reg["local_tools_count"]})
                else:
                    self.respond(404, {"error": f"Unknown endpoint: {sub}"})
            except Exception as e:
                self.respond(500, {"error": str(e)})
        elif self.path == "/api/learn":
            try:
                with open("/opt/evolvixos/models/lovable_course.json", "r") as f:
                    self.respond(200, json.load(f))
            except Exception as e:
                self.respond(500, {"error": str(e)})
        elif self.path.startswith("/api/learn/"):
            module_id = self.path.split("/api/learn/")[1].split("?")[0]
            course_dir = "/opt/evolvixos/lovable-for-beginners"
            # Try different filename patterns
            for pattern in [f"{module_id}.md", f"module-{module_id}.md", f"supplement-{module_id}.md"]:
                filepath = os.path.join(course_dir, pattern)
                if os.path.exists(filepath):
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()
                    title_m = re.match(r"#\s+(.+)", content)
                    title = title_m.group(1) if title_m else module_id
                    num_m = re.search(r"module-(\d+)", pattern)
                    module_num = int(num_m.group(1)) if num_m else 0
                    goals = []
                    goals_m = re.search(r"## Learning goals.*?\n(.*?)(?=\n##|\Z)", content, re.DOTALL)
                    if goals_m:
                        goals = re.findall(r"-\s+(.+)", goals_m.group(1))
                    sections = re.findall(r"^##\s+(.+)", content, re.MULTILINE)
                    word_count = len(content.split())
                    self.respond(200, {
                        "module_id": module_id,
                        "title": title,
                        "module_num": module_num,
                        "content": content,
                        "goals": goals,
                        "sections": sections,
                        "word_count": word_count,
                        "read_time": max(1, word_count // 200),
                        "source": "https://github.com/cporter202/lovable-for-beginners"
                    })
                    return
            self.respond(404, {"error": f"Module '{module_id}' not found"})
        elif self.path == "/api/templates":
            _templates = [
                {"id": 1, "title": "Web Application", "desc": "Build a full-stack web app", "icon": "🌐", "category": "Code", "prompt": "Build a web app with a React frontend and Python API for a todo app"},
                {"id": 2, "title": "AI Chatbot", "desc": "Create an AI chatbot with custom personality", "icon": "🤖", "category": "AI", "prompt": "Create an AI chatbot with a friendly personality for customer support"},
                {"id": 3, "title": "Logo & Brand Design", "desc": "Generate professional logos and brand assets", "icon": "🎨", "category": "Image", "prompt": "Generate a professional logo for a tech startup"},
                {"id": 4, "title": "Data Pipeline", "desc": "Build an ETL pipeline with data processing", "icon": "📊", "category": "Code", "prompt": "Build a data pipeline that processes CSV files and generates analytics"},
                {"id": 5, "title": "Mobile App", "desc": "Design a cross-platform mobile application", "icon": "📱", "category": "Code", "prompt": "Design a mobile app for tracking fitness goals"},
                {"id": 6, "title": "AI Video", "desc": "Generate videos from text prompts", "icon": "🎬", "category": "Video", "prompt": "Generate a video about a futuristic city"},
                {"id": 7, "title": "Smart Contract", "desc": "Write and deploy blockchain contracts", "icon": "⛓️", "category": "Web3", "prompt": "Write a Solidity smart contract for a voting system"},
                {"id": 8, "title": "Code Review", "desc": "Analyze code for bugs and security issues", "icon": "🔍", "category": "Analysis", "prompt": "Analyze the code in /opt/evolvixos/models/model_api.py for security issues"},
            ]
            _cats = sorted(set(t["category"] for t in _templates))
            self.respond(200, {"templates": _templates, "categories": _cats})
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
        if content_len > 50_000_000:
            self.respond(413, {"error": "Request body too large (max 50MB)"})
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
        system = body.get("system", build_system_prompt(uploads_dir=user_dir(self, UPLOADS_DIR)))
        # v10: Route through unified ModelRouter
        _init_v10()
        decision = _v10_router.route(prompt)
        model = body.get("model") or decision.model
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "close")
        self.send_header("Transfer-Encoding", "chunked")
        self.send_header("Access-Control-Allow-Origin", "https://evolvixos.com")
        self._add_security_headers()
        self.end_headers()
        self.close_connection = True

        # v10: Log routing decision
        log_audit("system", "stream_chat", "route", prompt[:200], "success", 0)

        # v10: Select provider based on routing decision
        provider = _v10_registry.get(decision.provider)
        use_ollama = provider and provider.is_local

        try:
            if use_ollama:
                # Stream from Ollama directly (Ollama supports streaming natively)
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
            else:
                # Cloud provider: use non-streaming, emit as SSE
                messages = [{"role": "system", "content": system}, {"role": "user", "content": prompt}]
                resp = provider.chat(messages, tools=None, stream=False)
                if resp.content:
                    self._sse("text", {"text": resp.content, "done": False})
                self._sse("text", {"text": "", "done": True})
        except (BrokenPipeError, ConnectionResetError):
            return
        except Exception as e:
            # v10: Fallback to Ollama if cloud provider fails
            try:
                ollama_provider = _v10_registry.get("ollama")
                if ollama_provider and ollama_provider.is_available():
                    data = json.dumps({"model": "qwen2.5:14b", "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}], "stream": True}).encode()
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
                else:
                    self._sse("error", {"error": str(e)})
            except Exception:
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
    print(f"Mr James v10.0 — EvolvixOS Model API (v10 Hardened)")
    print(f"  Port: {PORT}")
    print(f"  Privacy Mode: {V10_PRIVACY_MODE}")
    print(f"  Tools: {len(TOOLS)} (with v10 security: permissions, audit, SSRF protection)")
    print(f"  Providers: {_v10_registry.list_available() if _v10_registry else []}")
    print(f"  Skills: {len([f for f in os.listdir(SKILLS_DIR) if f.endswith('.sh')]) if os.path.exists(SKILLS_DIR) else 0}")
    print(f"  Models: Ollama (local) + Groq + Gemini + Kimi (triple-brain routing)")
    print(f"  Security: v10 framework active (permissions, audit log, SSRF guard, rate limits)")
    print(f"  Uploads: {UPLOADS_DIR}")
    print(f"  Ready.")
    server.serve_forever()
