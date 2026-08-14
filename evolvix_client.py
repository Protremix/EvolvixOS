"""
EvolvixOS — Client SDK v2.1
One file. Drop into any project. Connect to all of EvolvixOS. Zero cost.

Usage:
    from evolvix_client import EvolvixClient

    evolvix = EvolvixClient("http://localhost:5001")

    # === Core ===
    status = evolvix.status()
    response = evolvix.chat("Write a web scraper in Python")
    for chunk in evolvix.chat_stream("Tell me about quantum computing"):
        print(chunk, end="")

    # === Research ===
    report = evolvix.research("AI breakthroughs 2026", depth=5)

    # === Coding ===
    code = evolvix.code("Build a REST API in Flask", language="python")
    result = evolvix.code_execute("Print fibonacci sequence", language="python")
    fixed = evolvix.code_debug(code_string, error_message, language="python")

    # === Video ===
    video_job = evolvix.video("A cat playing piano", duration=5)
    status = evolvix.get_video_status(video_job["job_id"])

    # === Image ===
    image = evolvix.image("A futuristic city at sunset", size="1024x1024")

    # === Audio ===
    audio_bytes = evolvix.text_to_speech("Hello, I am Evolvix")
    evolvix.save_speech("Hello world", "output.wav")
    music = evolvix.music("Epic orchestral battle music", duration=30)
    text = evolvix.speech_to_text("recording.wav")

    # === Movie ===
    movie_job = evolvix.movie("A day in the life of a robot", style="cinematic")
    status = evolvix.get_movie_status(movie_job["job_id"])

    # === Deploy ===
    result = evolvix.deploy("/path/to/project", server="user@host", destination="/opt/app")

    # === GitHub Discovery ===
    discovered = evolvix.discover("AI agent frameworks", topic="ai-agent")
    installed = evolvix.discover_install("https://github.com/some/tool")
    learned = evolvix.discover_learned()

    # === Self-Improvement ===
    new_skill = evolvix.improve("scrape Twitter trends")
    skills = evolvix.improve_skills()

    # === Project Learner ===
    evolvix.load_project("/path/to/codebase", name="MyApp")
    answer = evolvix.ask_project("MyApp", "How does auth work?")
    projects = evolvix.list_projects()
    evolvix.represent("MyApp")
    evolvix.stop_representing()

    # === Memory ===
    memories = evolvix.search_memory("quantum computing")

    # === Docs ===
    docs = evolvix.docs()
"""

import requests
import json
from typing import Optional, Any


class EvolvixClient:
    """
    Client for the EvolvixOS Unified API.
    One client. All capabilities. Zero cost.
    """

    def __init__(self, base_url: str = "http://localhost:5001"):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    # ===================================================================
    # CORE
    # ===================================================================

    def status(self) -> dict:
        """Get full system status including all loaded skills."""
        return self.session.get(f"{self.base_url}/api/v1/status").json()

    def health(self) -> dict:
        """Health check."""
        return self.session.get(f"{self.base_url}/api/v1/health").json()

    def chat(self, message: str, project: str = None, voice: bool = False) -> dict:
        """Chat with the agent. It automatically selects the right skill."""
        payload = {"message": message, "voice": voice}
        if project:
            payload["project"] = project
        return self.session.post(f"{self.base_url}/api/v1/chat", json=payload).json()

    def chat_stream(self, message: str):
        """Stream chat response (generator yielding text chunks)."""
        response = self.session.post(
            f"{self.base_url}/api/v1/chat/stream",
            json={"message": message},
            stream=True,
        )
        for line in response.iter_lines():
            if line:
                line_str = line.decode("utf-8")
                if line_str.startswith("data: "):
                    data = json.loads(line_str[6:])
                    if "text" in data:
                        yield data["text"]
                    elif "error" in data:
                        raise Exception(data["error"])

    # ===================================================================
    # RESEARCH
    # ===================================================================

    def research(self, query: str, depth: int = 5, max_words: int = 5000) -> dict:
        """Deep web research → comprehensive report."""
        return self.session.post(f"{self.base_url}/api/v1/research", json={
            "query": query, "depth": depth, "max_words": max_words
        }).json()

    # ===================================================================
    # CODING
    # ===================================================================

    def code(self, prompt: str, language: str = "python") -> dict:
        """Generate code from natural language."""
        return self.session.post(f"{self.base_url}/api/v1/code", json={
            "prompt": prompt, "language": language
        }).json()

    def code_execute(self, prompt: str, language: str = "python") -> dict:
        """Generate and execute code."""
        return self.session.post(f"{self.base_url}/api/v1/code/execute", json={
            "prompt": prompt, "language": language
        }).json()

    def code_debug(self, code: str, error: str = "", language: str = "python") -> dict:
        """Debug existing code."""
        return self.session.post(f"{self.base_url}/api/v1/code/debug", json={
            "code": code, "error": error, "language": language
        }).json()

    # ===================================================================
    # VIDEO
    # ===================================================================

    def video(self, prompt: str, duration: int = 5, resolution: str = "720p", fps: int = 24) -> dict:
        """Text-to-video generation (async)."""
        return self.session.post(f"{self.base_url}/api/v1/video", json={
            "prompt": prompt, "duration": duration, "resolution": resolution, "fps": fps
        }).json()

    def get_video_status(self, job_id: str) -> dict:
        """Check video generation status."""
        return self.session.get(f"{self.base_url}/api/v1/video/{job_id}").json()

    # ===================================================================
    # IMAGE
    # ===================================================================

    def image(self, prompt: str, size: str = "1024x1024") -> dict:
        """Text-to-image generation."""
        return self.session.post(f"{self.base_url}/api/v1/image", json={
            "prompt": prompt, "size": size
        }).json()

    # ===================================================================
    # AUDIO
    # ===================================================================

    def text_to_speech(self, text: str, voice: str = "af") -> bytes:
        """Convert text to speech. Returns audio bytes."""
        response = self.session.post(f"{self.base_url}/api/v1/audio/tts", json={
            "text": text, "voice": voice
        })
        return response.content

    def save_speech(self, text: str, output_file: str, voice: str = "af") -> str:
        """Convert text to speech and save to file."""
        audio_bytes = self.text_to_speech(text, voice)
        with open(output_file, "wb") as f:
            f.write(audio_bytes)
        return output_file

    def music(self, prompt: str, duration: int = 10) -> dict:
        """Text-to-music generation."""
        return self.session.post(f"{self.base_url}/api/v1/audio/music", json={
            "prompt": prompt, "duration": duration
        }).json()

    def speech_to_text(self, audio_file_path: str, language: str = None) -> str:
        """Send audio file, get transcribed text."""
        with open(audio_file_path, "rb") as f:
            files = {"audio": f}
            data = {}
            if language:
                data["language"] = language
            response = requests.post(
                f"{self.base_url}/api/v1/voice",
                files=files, data=data,
            )
            return response.json().get("text", "")

    # ===================================================================
    # MOVIE
    # ===================================================================

    def movie(self, prompt: str, style: str = "cinematic", voice: str = "af",
              music: str = "epic", resolution: str = "720p") -> dict:
        """Full movie creation pipeline (async)."""
        return self.session.post(f"{self.base_url}/api/v1/movie", json={
            "prompt": prompt, "style": style, "voice": voice,
            "music": music, "resolution": resolution
        }).json()

    def get_movie_status(self, job_id: str) -> dict:
        """Check movie creation status."""
        return self.session.get(f"{self.base_url}/api/v1/movie/{job_id}").json()

    # ===================================================================
    # DEPLOY
    # ===================================================================

    def deploy(self, path: str, server: str, user: str = "",
               destination: str = "/opt/app", ssh_key: str = None) -> dict:
        """Deploy a project to a server via SSH."""
        payload = {"path": path, "server": server, "user": user,
                    "destination": destination}
        if ssh_key:
            payload["ssh_key"] = ssh_key
        return self.session.post(f"{self.base_url}/api/v1/deploy", json=payload).json()

    # ===================================================================
    # GITHUB DISCOVERY
    # ===================================================================

    def discover(self, query: str = "", topic: str = "", limit: int = 20,
                 auto_learn: bool = True) -> dict:
        """Search GitHub for new AI tools to learn from."""
        return self.session.post(f"{self.base_url}/api/v1/discover", json={
            "query": query, "topic": topic, "limit": limit, "auto_learn": auto_learn
        }).json()

    def discover_install(self, repo_url: str) -> dict:
        """Install a specific GitHub repo as a skill."""
        return self.session.post(f"{self.base_url}/api/v1/discover/install", json={
            "repo": repo_url
        }).json()

    def discover_learned(self) -> dict:
        """List all skills learned from GitHub."""
        return self.session.get(f"{self.base_url}/api/v1/discover/learned").json()

    # ===================================================================
    # SELF-IMPROVEMENT
    # ===================================================================

    def improve(self, task: str) -> dict:
        """Trigger self-improvement — write a new skill for a task."""
        return self.session.post(f"{self.base_url}/api/v1/improve", json={
            "task": task
        }).json()

    def improve_skills(self) -> dict:
        """List all self-written skills."""
        return self.session.get(f"{self.base_url}/api/v1/improve/skills").json()

    # ===================================================================
    # PROJECT LEARNER
    # ===================================================================

    def load_project(self, path: str, name: Optional[str] = None) -> dict:
        """Load a codebase for Evolvix to study."""
        payload = {"path": path}
        if name:
            payload["name"] = name
        return self.session.post(f"{self.base_url}/api/v1/project/load", json=payload).json()

    def ask_project(self, project_name: str, question: str) -> dict:
        """Ask a question about a loaded project."""
        return self.session.post(f"{self.base_url}/api/v1/project/ask", json={
            "project": project_name, "question": question
        }).json()

    def list_projects(self) -> dict:
        """List all loaded projects."""
        return self.session.get(f"{self.base_url}/api/v1/project/list").json()

    def represent(self, project_name: str) -> dict:
        """Make Evolvix represent a project (act as its AI ambassador)."""
        return self.session.post(f"{self.base_url}/api/v1/project/represent", json={
            "project": project_name
        }).json()

    def stop_representing(self) -> dict:
        """Stop representing a project."""
        return self.session.delete(f"{self.base_url}/api/v1/project/represent").json()

    # ===================================================================
    # MEMORY
    # ===================================================================

    def search_memory(self, query: str) -> dict:
        """Search agent's memory."""
        return self.session.get(f"{self.base_url}/api/v1/memory",
                                params={"q": query}).json()

    # ===================================================================
    # v0.4 NEW SKILLS
    # ===================================================================

    def run_skill(self, skill_name: str, **kwargs) -> dict:
        """Run ANY skill directly by name."""
        return self.session.post(f"{self.base_url}/api/v1/skill/{skill_name}",
                                  json=kwargs).json()

    def scrape(self, url: str, extract: str = "all") -> dict:
        """Scrape a website — extract text, links, images, tables."""
        return self.session.post(f"{self.base_url}/api/v1/scrape", json={
            "url": url, "extract": extract
        }).json()

    def analyze_data(self, file: str, fmt: str = "csv") -> dict:
        """Analyze a data file (CSV, JSON, Excel) — stats, structure."""
        return self.session.post(f"{self.base_url}/api/v1/data/analyze", json={
            "file": file, "format": fmt
        }).json()

    def data_chart(self, file: str, chart_type: str = "bar",
                   x: str = "", y: str = "", title: str = "", fmt: str = "csv") -> dict:
        """Create a chart from data."""
        return self.session.post(f"{self.base_url}/api/v1/data/chart", json={
            "file": file, "chart_type": chart_type, "x": x, "y": y,
            "title": title, "format": fmt
        }).json()

    def read_document(self, file: str) -> dict:
        """Read any document (PDF, Word, Excel, PowerPoint, TXT)."""
        return self.session.post(f"{self.base_url}/api/v1/doc/read", json={
            "file": file
        }).json()

    def write_document(self, text: str, filename: str = "", fmt: str = "docx") -> dict:
        """Write a document (PDF, Word, Excel)."""
        action = f"write_{fmt}"
        return self.session.post(f"{self.base_url}/api/v1/doc/write", json={
            "action": action, "text": text, "filename": filename
        }).json()

    def convert_document(self, file: str, to_format: str = "pdf") -> dict:
        """Convert document to another format."""
        return self.session.post(f"{self.base_url}/api/v1/doc/convert", json={
            "file": file, "to_format": to_format
        }).json()

    def translate(self, text: str, from_lang: str = "en", to_lang: str = "es") -> dict:
        """Translate text between 30+ languages (offline)."""
        return self.session.post(f"{self.base_url}/api/v1/translate", json={
            "text": text, "from_lang": from_lang, "to_lang": to_lang
        }).json()

    def translate_languages(self) -> dict:
        """List available translation languages."""
        return self.session.get(f"{self.base_url}/api/v1/translate/languages").json()

    def ocr(self, image: str, lang: str = "eng") -> dict:
        """Extract text from an image (OCR)."""
        return self.session.post(f"{self.base_url}/api/v1/ocr", json={
            "image": image, "lang": lang
        }).json()

    def edit_image(self, image: str, action: str = "resize", **kwargs) -> dict:
        """Edit an image (resize, crop, rotate, filter, watermark, convert, compress)."""
        payload = {"image": image, "action": action, **kwargs}
        return self.session.post(f"{self.base_url}/api/v1/image/edit", json=payload).json()

    def process_audio(self, file: str, action: str = "trim", **kwargs) -> dict:
        """Process audio (trim, merge, convert, speed, volume, fade, normalize)."""
        payload = {"file": file, "action": action, **kwargs}
        return self.session.post(f"{self.base_url}/api/v1/audio/process", json=payload).json()

    def edit_video(self, file: str, action: str = "trim", **kwargs) -> dict:
        """Edit video (trim, merge, convert, add_text, extract_audio, resize, speed)."""
        payload = {"file": file, "action": action, **kwargs}
        return self.session.post(f"{self.base_url}/api/v1/video/edit", json=payload).json()

    def analyze_code(self, path: str, action: str = "analyze") -> dict:
        """Analyze code (complexity, quality, structure, imports, dead code, TODOs)."""
        return self.session.post(f"{self.base_url}/api/v1/analyze/code", json={
            "path": path, "action": action
        }).json()

    def analyze_security(self, path: str) -> dict:
        """Security analysis of code (vulnerabilities, secrets)."""
        return self.session.post(f"{self.base_url}/api/v1/analyze/security", json={
            "path": path
        }).json()

    def summarize(self, text: str, style: str = "concise", ratio: float = 0.3) -> dict:
        """Summarize text using local LLM."""
        return self.session.post(f"{self.base_url}/api/v1/summarize", json={
            "text": text, "style": style, "ratio": ratio
        }).json()

    def summarize_file(self, file: str) -> dict:
        """Summarize a file (TXT, MD, PDF)."""
        return self.session.post(f"{self.base_url}/api/v1/summarize/file", json={
            "file": file
        }).json()

    def convert_file(self, file: str, to_format: str = "md") -> dict:
        """Convert any file to another format."""
        return self.session.post(f"{self.base_url}/api/v1/convert", json={
            "file": file, "to_format": to_format
        }).json()

    def scan_security(self, path: str) -> dict:
        """Scan code for security vulnerabilities."""
        return self.session.post(f"{self.base_url}/api/v1/scan/security", json={
            "path": path
        }).json()

    def scan_secrets(self, path: str) -> dict:
        """Scan code for hardcoded secrets (API keys, passwords, tokens)."""
        return self.session.post(f"{self.base_url}/api/v1/scan/secrets", json={
            "path": path
        }).json()

    def math_solve(self, equation: str, variable: str = "x") -> dict:
        """Solve a math equation."""
        return self.session.post(f"{self.base_url}/api/v1/math/solve", json={
            "equation": equation, "variable": variable
        }).json()

    def create_chart(self, chart_type: str = "bar", data: list = None,
                     labels: list = None, title: str = "",
                     xlabel: str = "", ylabel: str = "") -> dict:
        """Create a chart (bar, line, pie, scatter, histogram, heatmap, timeline)."""
        return self.session.post(f"{self.base_url}/api/v1/chart", json={
            "chart_type": chart_type, "data": data or [], "labels": labels or [],
            "title": title, "xlabel": xlabel, "ylabel": ylabel
        }).json()

    def schedule(self, command: str, when: str, repeat: bool = False) -> dict:
        """Schedule a task for a specific time."""
        return self.session.post(f"{self.base_url}/api/v1/schedule", json={
            "command": command, "when": when, "repeat": repeat
        }).json()

    def list_scheduled(self) -> dict:
        """List all scheduled jobs."""
        return self.session.get(f"{self.base_url}/api/v1/schedule/list").json()

    def system_status(self) -> dict:
        """Get system overview (CPU, RAM, disk, processes)."""
        return self.session.get(f"{self.base_url}/api/v1/system").json()

    def system_processes(self, sort_by: str = "cpu", limit: int = 20) -> dict:
        """List system processes."""
        return self.session.get(f"{self.base_url}/api/v1/system/processes",
                                params={"sort_by": sort_by, "limit": limit}).json()

    def send_email(self, to: str, subject: str, body: str,
                   html: bool = False, attachments: list = None) -> dict:
        """Send an email via SMTP."""
        payload = {"to": to, "subject": subject, "body": body, "html": html}
        if attachments:
            payload["attachments"] = attachments
        return self.session.post(f"{self.base_url}/api/v1/email/send", json=payload).json()

    def db_query(self, db: str, sql: str, params: list = None) -> dict:
        """Query a SQLite database."""
        return self.session.post(f"{self.base_url}/api/v1/db/query", json={
            "db": db, "sql": sql, "params": params or []
        }).json()

    def db_execute(self, db: str, sql: str, params: list = None) -> dict:
        """Execute SQL on a database (INSERT, UPDATE, DELETE, CREATE)."""
        return self.session.post(f"{self.base_url}/api/v1/db/execute", json={
            "db": db, "sql": sql, "params": params or []
        }).json()

    def build_markdown(self, action: str = "generate", **kwargs) -> dict:
        """Generate markdown documents (READMEs, reports, changelogs, API docs)."""
        payload = {"action": action, **kwargs}
        return self.session.post(f"{self.base_url}/api/v1/markdown", json=payload).json()

    def browser_navigate(self, url: str) -> dict:
        """Navigate browser to a URL."""
        return self.session.post(f"{self.base_url}/api/v1/browser/navigate", json={
            "url": url
        }).json()

    def browser_screenshot(self, filename: str = "") -> dict:
        """Take a screenshot of the current browser page."""
        return self.session.post(f"{self.base_url}/api/v1/browser/screenshot", json={
            "filename": filename
        }).json()

    def browser_extract(self, selector: str = "") -> dict:
        """Extract text from the current browser page."""
        return self.session.post(f"{self.base_url}/api/v1/browser/extract", json={
            "selector": selector
        }).json()

    # ===================================================================
    # HETZNER SERVER MANAGEMENT
    # ===================================================================

    def hetzner_servers(self) -> dict:
        """List all Hetzner servers."""
        return self.session.get(f"{self.base_url}/api/v1/hetzner/servers").json()

    def hetzner_create_server(self, name: str, server_type: str = "cpx42",
                               location: str = "hel1", image: str = "ubuntu-22.04") -> dict:
        """Create a new Hetzner server."""
        return self.session.post(f"{self.base_url}/api/v1/hetzner/servers", json={
            "name": name, "server_type": server_type, "image": image, "location": location
        }).json()

    def hetzner_get_server(self, server_id: int) -> dict:
        """Get details for a specific server."""
        return self.session.get(f"{self.base_url}/api/v1/hetzner/servers/{server_id}").json()

    def hetzner_delete_server(self, server_id: int) -> dict:
        """Delete a server permanently."""
        return self.session.delete(f"{self.base_url}/api/v1/hetzner/servers/{server_id}").json()

    def hetzner_power_on(self, server_id: int) -> dict:
        """Power on a server."""
        return self.session.post(f"{self.base_url}/api/v1/hetzner/servers/{server_id}/power",
                                  json={"action": "power_on"}).json()

    def hetzner_power_off(self, server_id: int) -> dict:
        """Power off a server."""
        return self.session.post(f"{self.base_url}/api/v1/hetzner/servers/{server_id}/power",
                                  json={"action": "power_off"}).json()

    def hetzner_reboot(self, server_id: int) -> dict:
        """Reboot a server."""
        return self.session.post(f"{self.base_url}/api/v1/hetzner/servers/{server_id}/power",
                                  json={"action": "reboot"}).json()

    def hetzner_deploy_evolvixos(self, server_id: int = None, domain: str = "evolvixos.com",
                                  create_new: bool = False, name: str = "evolvixos-prod",
                                  server_type: str = "cpx42", location: str = "hel1") -> dict:
        """Deploy EvolvixOS to a Hetzner server (existing or create new one)."""
        payload = {"domain": domain}
        if create_new:
            payload["action"] = "create_new"
            payload["name"] = name
            payload["server_type"] = server_type
            payload["location"] = location
        else:
            payload["server_id"] = server_id
        return self.session.post(f"{self.base_url}/api/v1/hetzner/deploy", json=payload).json()

    def hetzner_ssh_keys(self) -> dict:
        """List SSH keys."""
        return self.session.get(f"{self.base_url}/api/v1/hetzner/ssh-keys").json()

    def hetzner_add_ssh_key(self, name: str, public_key: str) -> dict:
        """Add an SSH public key."""
        return self.session.post(f"{self.base_url}/api/v1/hetzner/ssh-keys", json={
            "name": name, "public_key": public_key
        }).json()

    def hetzner_locations(self) -> dict:
        """List available locations."""
        return self.session.get(f"{self.base_url}/api/v1/hetzner/locations").json()

    def hetzner_types(self) -> dict:
        """List available server types and pricing."""
        return self.session.get(f"{self.base_url}/api/v1/hetzner/types").json()

    def hetzner_estimate(self) -> dict:
        """Get EvolvixOS deployment cost estimate."""
        return self.session.get(f"{self.base_url}/api/v1/hetzner/estimate").json()

    def hetzner_firewalls(self) -> dict:
        """List firewalls."""
        return self.session.get(f"{self.base_url}/api/v1/hetzner/firewalls").json()

    def hetzner_create_firewall(self, name: str = "evolvixos-firewall") -> dict:
        """Create a firewall with SSH/HTTP/HTTPS rules."""
        return self.session.post(f"{self.base_url}/api/v1/hetzner/firewalls", json={
            "name": name
        }).json()

    def hetzner_metrics(self, server_id: int, metric_type: str = "cpu") -> dict:
        """Get server metrics (cpu, network, disk)."""
        return self.session.get(f"{self.base_url}/api/v1/hetzner/metrics/{server_id}",
                                 params={"type": metric_type}).json()

    # ===================================================================
    # MODEL REGISTRY
    # ===================================================================

    def registry_list_models(self) -> dict:
        """List all registered models."""
        return self.session.get(f"{self.base_url}/api/v1/registry/models").json()

    def registry_register_model(self, name: str, version: str, model_type: str = "llm",
                                size_mb: float = 0, metrics: dict = None, **kwargs) -> dict:
        """Register a new model version."""
        payload = {"name": name, "version": version, "type": model_type, "size_mb": size_mb}
        if metrics: payload["metrics"] = metrics
        payload.update(kwargs)
        return self.session.post(f"{self.base_url}/api/v1/registry/models", json=payload).json()

    def registry_deploy_model(self, name: str, version: str, endpoint: str = "") -> dict:
        """Deploy a model (mark as live)."""
        return self.session.post(f"{self.base_url}/api/v1/registry/models/deploy", json={
            "name": name, "version": version, "endpoint": endpoint
        }).json()

    def registry_compare_models(self, name1: str, v1: str, name2: str, v2: str) -> dict:
        """Compare two model versions."""
        return self.session.post(f"{self.base_url}/api/v1/registry/models/compare", json={
            "name1": name1, "version1": v1, "name2": name2, "version2": v2
        }).json()

    def registry_deployed(self) -> dict:
        """List deployed models."""
        return self.session.get(f"{self.base_url}/api/v1/registry/models/deployed").json()

    # ===================================================================
    # EXPERIMENT TRACKER
    # ===================================================================

    def log_experiment(self, name: str, parameters: dict = None, metrics: dict = None,
                       model: str = "", status: str = "running", **kwargs) -> dict:
        """Log a new experiment."""
        payload = {"name": name, "model": model, "status": status}
        if parameters: payload["parameters"] = parameters
        if metrics: payload["metrics"] = metrics
        payload.update(kwargs)
        return self.session.post(f"{self.base_url}/api/v1/experiments", json=payload).json()

    def list_experiments(self, status: str = None) -> dict:
        """List experiments, optionally filtered by status."""
        params = {}
        if status: params["status"] = status
        return self.session.get(f"{self.base_url}/api/v1/experiments", params=params).json()

    def get_experiment(self, exp_id: str) -> dict:
        """Get experiment details."""
        return self.session.get(f"{self.base_url}/api/v1/experiments/{exp_id}").json()

    def update_experiment(self, exp_id: str, metrics: dict = None, status: str = None) -> dict:
        """Update an experiment."""
        payload = {}
        if metrics: payload["metrics"] = metrics
        if status: payload["status"] = status
        return self.session.patch(f"{self.base_url}/api/v1/experiments/{exp_id}", json=payload).json()

    def compare_experiments(self, exp_id1: str, exp_id2: str) -> dict:
        """Compare two experiments."""
        return self.session.post(f"{self.base_url}/api/v1/experiments/compare", json={
            "exp_id1": exp_id1, "exp_id2": exp_id2
        }).json()

    def experiment_summary(self) -> dict:
        """Get experiment summary."""
        return self.session.get(f"{self.base_url}/api/v1/experiments/summary").json()

    # ===================================================================
    # PIPELINE BUILDER
    # ===================================================================

    def create_pipeline(self, name: str, steps: list, description: str = "", **kwargs) -> dict:
        """Create a multi-step pipeline."""
        payload = {"name": name, "steps": steps, "description": description}
        payload.update(kwargs)
        return self.session.post(f"{self.base_url}/api/v1/pipelines", json=payload).json()

    def list_pipelines(self) -> dict:
        """List all pipelines."""
        return self.session.get(f"{self.base_url}/api/v1/pipelines").json()

    def get_pipeline(self, pipe_id: str) -> dict:
        """Get pipeline details."""
        return self.session.get(f"{self.base_url}/api/v1/pipelines/{pipe_id}").json()

    def run_pipeline(self, pipe_id: str, input_data: dict = None) -> dict:
        """Execute a pipeline."""
        return self.session.post(f"{self.base_url}/api/v1/pipelines/{pipe_id}/run",
                                  json=input_data or {}).json()

    def delete_pipeline(self, pipe_id: str) -> dict:
        """Delete a pipeline."""
        return self.session.delete(f"{self.base_url}/api/v1/pipelines/{pipe_id}").json()

    # ===================================================================
    # MODEL SERVER
    # ===================================================================

    def models_available(self) -> dict:
        """List available Ollama models."""
        return self.session.get(f"{self.base_url}/api/v1/models/available").json()

    def pull_model(self, model: str) -> dict:
        """Pull a model from Ollama registry."""
        return self.session.post(f"{self.base_url}/api/v1/models/pull", json={"model": model}).json()

    def serve_model(self, model: str, endpoint: str = "") -> dict:
        """Start serving a model."""
        return self.session.post(f"{self.base_url}/api/v1/models/serve", json={
            "model": model, "endpoint": endpoint
        }).json()

    def predict(self, model: str, prompt: str, system: str = "", temperature: float = 0.7,
                max_tokens: int = 2048) -> dict:
        """Run inference on a model."""
        return self.session.post(f"{self.base_url}/api/v1/models/predict", json={
            "model": model, "prompt": prompt, "system": system,
            "temperature": temperature, "max_tokens": max_tokens
        }).json()

    def embed(self, model: str, text: str) -> dict:
        """Generate embeddings."""
        return self.session.post(f"{self.base_url}/api/v1/models/embed", json={
            "model": model, "text": text
        }).json()

    def benchmark_model(self, model: str, n_runs: int = 5) -> dict:
        """Benchmark a model."""
        return self.session.post(f"{self.base_url}/api/v1/models/benchmark", json={
            "model": model, "n_runs": n_runs
        }).json()

    def model_metrics(self) -> dict:
        """Get serving metrics."""
        return self.session.get(f"{self.base_url}/api/v1/models/metrics").json()

    # ===================================================================
    # EVALUATION FRAMEWORK
    # ===================================================================

    def evaluate_model(self, model: str, benchmarks: list = None) -> dict:
        """Run evaluation suite on a model."""
        payload = {"model": model}
        if benchmarks: payload["benchmarks"] = benchmarks
        return self.session.post(f"{self.base_url}/api/v1/evaluate", json=payload).json()

    def compare_evaluations(self, models: list, benchmark: str = "reasoning") -> dict:
        """Compare models on a benchmark."""
        return self.session.post(f"{self.base_url}/api/v1/evaluate/compare", json={
            "models": models, "benchmark": benchmark
        }).json()

    def evaluation_history(self) -> dict:
        """Get evaluation history."""
        return self.session.get(f"{self.base_url}/api/v1/evaluate/history").json()

    # ===================================================================
    # VOICE ASSISTANT
    # ===================================================================

    def voice_speak(self, text: str) -> dict:
        """Text-to-speech — speak text locally."""
        return self.session.post(f"{self.base_url}/api/v1/voice/speak", json={"text": text}).json()

    def voice_listen(self, duration: int = 5) -> dict:
        """Listen to microphone and transcribe."""
        return self.session.post(f"{self.base_url}/api/v1/voice/listen", json={"duration": duration}).json()

    def voice_converse(self, text: str, speak: bool = True) -> dict:
        """Full conversation: text → think → speak."""
        return self.session.post(f"{self.base_url}/api/v1/voice/converse", json={
            "text": text, "speak": speak
        }).json()

    def voice_status(self) -> dict:
        """Get voice assistant status."""
        return self.session.get(f"{self.base_url}/api/v1/voice/status").json()

    def voice_voices(self) -> dict:
        """List available voices."""
        return self.session.get(f"{self.base_url}/api/v1/voice/voices").json()

    def voice_set_settings(self, voice: str, rate: float = None, volume: float = None) -> dict:
        """Change voice settings."""
        payload = {"voice": voice}
        if rate is not None: payload["rate"] = rate
        if volume is not None: payload["volume"] = volume
        return self.session.post(f"{self.base_url}/api/v1/voice/settings", json=payload).json()

    # ===================================================================
    # DEVICE MANAGER
    # ===================================================================

    def register_device(self, name: str, device_type: str = "web",
                        os_name: str = "", capabilities: list = None) -> dict:
        """Register a new device."""
        payload = {"name": name, "type": device_type, "os": os_name}
        if capabilities: payload["capabilities"] = capabilities
        return self.session.post(f"{self.base_url}/api/v1/devices/register", json=payload).json()

    def list_devices(self, device_type: str = None) -> dict:
        """List all registered devices."""
        return self.session.get(f"{self.base_url}/api/v1/devices").json()

    def get_device(self, device_id: str) -> dict:
        """Get device details."""
        return self.session.get(f"{self.base_url}/api/v1/devices/{device_id}").json()

    def connect_device(self, device_id: str) -> dict:
        """Mark a device as online."""
        return self.session.post(f"{self.base_url}/api/v1/devices/{device_id}/connect").json()

    def send_to_device(self, device_id: str, message: str) -> dict:
        """Send a message to a device."""
        return self.session.post(f"{self.base_url}/api/v1/devices/{device_id}/send", json={
            "message": message
        }).json()

    def broadcast_to_devices(self, message: str) -> dict:
        """Broadcast a message to all online devices."""
        return self.session.post(f"{self.base_url}/api/v1/devices/broadcast", json={
            "message": message
        }).json()

    def device_connect_info(self) -> dict:
        """Get connection info for devices."""
        return self.session.get(f"{self.base_url}/api/v1/devices/connect_info").json()

    def device_stats(self) -> dict:
        """Get device statistics."""
        return self.session.get(f"{self.base_url}/api/v1/devices/stats").json()

    def delete_device(self, device_id: str) -> dict:
        """Delete a device."""
        return self.session.delete(f"{self.base_url}/api/v1/devices/{device_id}").json()

    # ===================================================================
    # DOCS
    # ===================================================================

    def docs(self) -> dict:
        """Get the full API documentation (OpenAPI spec)."""
        return self.session.get(f"{self.base_url}/api/v1/docs").json()


# === EXAMPLE USAGE ===
if __name__ == "__main__":
    evolvix = EvolvixClient("http://localhost:5001")

    print("🧬 EvolvixOS Client v2.1 — One API, All Capabilities, Zero Cost\n")

    try:
        status = evolvix.status()
        print(f"  Status: {status['status']}")
        print(f"  Skills: {status['skills_count']} loaded")
        print(f"  Models: {status['model']}")
        print(f"  Cost:   {status['cost']}")
        print(f"\n  Endpoints: {len(status['endpoints'])} categories")
        for cat, endpoints in status["endpoints"].items():
            print(f"    {cat}: {len(endpoints)} endpoints")
    except requests.ConnectionError:
        print("❌ EvolvixOS API not running. Start it: python api_server.py")
