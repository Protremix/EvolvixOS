"""
EvolvixOS — GitHub Skill Discovery Engine
Automatically searches GitHub for ALL open-source AI skills, tools, and frameworks.
Downloads them, wraps them as EvolvixOS skills, and learns how to use each one.

This is how EvolvixOS becomes smarter than any single AI:
  - It searches GitHub for the best open-source AI tools
  - Clones and installs them locally (zero tokens)
  - Wraps each one as a skill it can use
  - Learns what each tool does and when to use it
  - Gets continuously smarter as new tools appear on GitHub

Categories it discovers:
  - LLMs and inference engines
  - Agent frameworks
  - RAG systems
  - Code generators
  - Image/video/audio generators
  - Research tools
  - Data processing
  - ML/AI libraries
  - Automation tools
  - And anything new that appears
"""

import os
import json
import time
import subprocess
import re
import hashlib
from pathlib import Path
from typing import Optional, List, Dict
from rich.console import Console
from rich.table import Table
import requests

console = Console()


class GitHubSkillDiscovery:
    """Discovers, downloads, and learns from ALL open-source AI skills on GitHub."""

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.skills_dir = Path(self.config.get("skills_dir", "./skills"))
        self.skills_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir = Path(self.config.get("cache_dir", "./data/github_cache"))
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.registry_file = self.cache_dir / "skill_registry.json"
        self.github_token = os.environ.get("GITHUB_TOKEN", "")  # Optional, increases rate limit
        self.registry = self._load_registry()

        # Search topics — what we look for on GitHub
        self.search_topics = [
            # AI/ML frameworks
            "ai-agent", "llm-agent", "autonomous-agent", "ai-framework",
            "language-model", "llm-inference", "transformer",
            # Code generation
            "code-generation", "code-generator", "ai-coding", "copilot",
            "code-assistant", "auto-coder",
            # RAG and knowledge
            "rag", "retrieval-augmented", "knowledge-base", "vector-database",
            "semantic-search", "embedding",
            # Image/Video/Audio generation
            "text-to-image", "text-to-video", "text-to-speech",
            "stable-diffusion", "image-generation", "video-generation",
            "ai-music", "audio-generation", "voice-cloning",
            # Research tools
            "web-scraping", "research-tools", "search-engine",
            "data-extraction", "web-crawler",
            # Agent tools
            "tool-use", "function-calling", "agent-tools",
            "multi-agent", "agent-orchestration",
            # Automation
            "automation", "workflow-automation", "task-automation",
            # Data processing
            "data-processing", "data-pipeline", "etl",
            # NLP
            "nlp", "natural-language-processing", "text-analysis",
            "sentiment-analysis", "text-classification",
            # Computer vision
            "computer-vision", "object-detection", "image-processing",
            "ocr", "face-recognition",
            # Speech
            "speech-recognition", "speech-to-text", "voice-synthesis",
            # New/emerging
            "ai-tools", "machine-learning-tools", "openai-tools",
            "langchain", "autogen", "crewai",
        ]

    def _load_registry(self) -> dict:
        """Load the skill registry from disk."""
        if self.registry_file.exists():
            with open(self.registry_file) as f:
                return json.load(f)
        return {"discovered": {}, "installed": {}, "learned": {}}

    def _save_registry(self):
        """Save the skill registry."""
        with open(self.registry_file, "w") as f:
            json.dump(self.registry, f, indent=2)

    def _github_headers(self) -> dict:
        """Headers for GitHub API."""
        headers = {"Accept": "application/vnd.github.v3+json"}
        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"
        return headers

    def search_github(self, topic: str, sort: str = "stars", per_page: int = 30) -> List[dict]:
        """Search GitHub for repositories matching a topic. Uses GitHub API (free, no tokens needed for basic search)."""
        url = "https://api.github.com/search/repositories"
        params = {
            "q": f"topic:{topic} stars:>50 language:python",
            "sort": sort,
            "order": "desc",
            "per_page": per_page,
        }

        try:
            response = requests.get(url, params=params, headers=self._github_headers(), timeout=15)
            if response.status_code == 200:
                items = response.json().get("items", [])
                return [
                    {
                        "name": item["name"],
                        "full_name": item["full_name"],
                        "description": item.get("description", ""),
                        "url": item["html_url"],
                        "clone_url": item["clone_url"],
                        "stars": item["stargazers_count"],
                        "language": item.get("language", ""),
                        "topics": item.get("topics", []),
                        "license": item.get("license", {}).get("spdx_id", "Unknown") if item.get("license") else "Unknown",
                        "updated_at": item.get("updated_at", ""),
                        "default_branch": item.get("default_branch", "main"),
                    }
                    for item in items
                ]
            elif response.status_code == 403:
                console.print("[yellow]⚠ GitHub API rate limit reached. Waiting 30s...[/yellow]")
                time.sleep(30)
                return self.search_github(topic, sort, per_page)
            else:
                console.print(f"[red]GitHub API error: {response.status_code}[/red]")
                return []
        except Exception as e:
            console.print(f"[red]Search error: {e}[/red]")
            return []

    def discover_all(self, max_per_topic: int = 20, min_stars: int = 50) -> dict:
        """Search ALL topics on GitHub and catalog every open-source AI skill found."""
        console.print("[bold cyan]🔍 Scanning GitHub for ALL open-source AI skills...[/bold cyan]")
        console.print(f"   Searching {len(self.search_topics)} topic categories")
        console.print(f"   Min stars: {min_stars}")
        console.print()

        all_found = {}
        total = 0

        for i, topic in enumerate(self.search_topics):
            console.print(f"  [{i+1}/{len(self.search_topics)}] Searching: {topic}...", end=" ")

            results = self.search_github(topic, per_page=max_per_topic)
            filtered = [r for r in results if r["stars"] >= min_stars]

            # Add to registry
            for repo in filtered:
                key = repo["full_name"]
                if key not in self.registry["discovered"]:
                    self.registry["discovered"][key] = {
                        **repo,
                        "discovered_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "status": "discovered",
                        "category": topic,
                    }
                    all_found[key] = repo
                    total += 1

            console.print(f"{len(filtered)} repos found")
            time.sleep(1)  # Be nice to GitHub API

        self._save_registry()
        console.print(f"\n[green]✅ Discovered {total} new open-source AI skills on GitHub[/green]")
        console.print(f"   Total in registry: {len(self.registry['discovered'])}")

        return all_found

    def install_skill(self, repo_full_name: str) -> dict:
        """Download and install a skill from GitHub. Zero tokens — just git clone."""
        if repo_full_name not in self.registry["discovered"]:
            return {"error": f"Unknown repo: {repo_full_name}. Run discover_all() first."}

        repo_info = self.registry["discovered"][repo_full_name]
        skill_name = self._repo_to_skill_name(repo_full_name)
        skill_dir = self.skills_dir / skill_name

        console.print(f"[cyan]📥 Installing: {repo_full_name} → {skill_name}[/cyan]")

        # Clone the repo
        if skill_dir.exists():
            console.print(f"  [yellow]Already exists, pulling latest...[/yellow]")
            try:
                subprocess.run(["git", "pull"], cwd=skill_dir, capture_output=True, timeout=30)
            except Exception:
                pass
        else:
            try:
                subprocess.run(
                    ["git", "clone", "--depth", "1", repo_info["clone_url"], str(skill_dir)],
                    capture_output=True, timeout=120,
                )
            except subprocess.TimeoutExpired:
                return {"error": "Clone timed out (repo too large?)"}
            except Exception as e:
                return {"error": f"Clone failed: {e}"}

        # Analyze the repo
        analysis = self._analyze_repo(skill_dir, repo_info)

        # Create skill wrapper
        wrapper_path = skill_dir / "evolvix_skill.py"
        wrapper_code = self._generate_skill_wrapper(skill_name, repo_info, analysis)
        wrapper_path.write_text(wrapper_code)

        # Create __init__.py if not exists
        init_path = skill_dir / "__init__.py"
        if not init_path.exists():
            init_path.write_text(f"# {skill_name} — auto-installed from GitHub\n")

        # Install Python dependencies if requirements.txt exists
        req_path = skill_dir / "requirements.txt"
        if req_path.exists():
            console.print(f"  [blue]Installing dependencies...[/blue]")
            try:
                subprocess.run(
                    ["pip", "install", "-r", str(req_path), "--quiet"],
                    capture_output=True, timeout=120,
                )
                console.print(f"  [green]✅ Dependencies installed[/green]")
            except Exception as e:
                console.print(f"  [yellow]⚠ Some dependencies failed: {e}[/yellow]")

        # Update registry
        self.registry["installed"][repo_full_name] = {
            **repo_info,
            "installed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "skill_name": skill_name,
            "path": str(skill_dir),
            "analysis": analysis,
        }
        self._save_registry()

        console.print(f"[green]✅ {skill_name} installed and ready[/green]")
        return {"status": "installed", "skill_name": skill_name, "path": str(skill_dir), "analysis": analysis}

    def _repo_to_skill_name(self, full_name: str) -> str:
        """Convert repo name to a valid skill name."""
        name = full_name.split("/")[-1]
        name = re.sub(r"[^a-zA-Z0-9_]", "_", name).lower().strip("_")
        return f"github_{name}"

    def _analyze_repo(self, repo_dir: Path, repo_info: dict) -> dict:
        """Analyze a cloned repo to understand what it does. Local, zero tokens."""
        analysis = {
            "name": repo_info["name"],
            "description": repo_info.get("description", ""),
            "entry_points": [],
            "has_cli": False,
            "has_api": False,
            "has_web": False,
            "main_language": repo_info.get("language", "Python"),
            "dependencies": [],
            "usage_example": "",
            "capabilities": [],
        }

        # Find entry points
        for entry in ["main.py", "app.py", "run.py", "cli.py", "server.py", "__main__.py", "index.py"]:
            if (repo_dir / entry).exists():
                analysis["entry_points"].append(entry)

        # Check for CLI
        if (repo_dir / "setup.py").exists() or (repo_dir / "pyproject.toml").exists():
            content = ""
            for f in ["setup.py", "pyproject.toml"]:
                p = repo_dir / f
                if p.exists():
                    content += p.read_text(errors="ignore") + "\n"
            if "console_scripts" in content or "entry_points" in content or "[project.scripts]" in content:
                analysis["has_cli"] = True
                analysis["capabilities"].append("CLI")

        # Check for API/web
        for f in ["api.py", "server.py", "app.py", "wsgi.py", "asgi.py"]:
            if (repo_dir / f).exists():
                content = (repo_dir / f).read_text(errors="ignore")[:5000]
                if "flask" in content.lower() or "fastapi" in content.lower() or "uvicorn" in content.lower():
                    analysis["has_api"] = True
                    analysis["capabilities"].append("API Server")
                if "html" in content.lower() or "render_template" in content.lower():
                    analysis["has_web"] = True
                    analysis["capabilities"].append("Web UI")

        # Get dependencies
        req_path = repo_dir / "requirements.txt"
        if req_path.exists():
            deps = req_path.read_text(errors="ignore").splitlines()
            analysis["dependencies"] = [d.strip().split(">=")[0].split("==")[0].split("<")[0].strip() for d in deps if d.strip() and not d.startswith("#")]

        # Detect capabilities from README
        readme_path = None
        for name in ["README.md", "README.rst", "readme.md", "README.txt"]:
            if (repo_dir / name).exists():
                readme_path = repo_dir / name
                break

        if readme_path:
            readme = readme_path.read_text(errors="ignore")[:10000].lower()
            capability_map = {
                "image generation": "image_generation",
                "text-to-image": "image_generation",
                "stable diffusion": "image_generation",
                "video generation": "video_generation",
                "text-to-video": "video_generation",
                "speech": "speech",
                "tts": "text_to_speech",
                "voice": "voice",
                "whisper": "speech_to_text",
                "transcri": "speech_to_text",
                "code gen": "code_generation",
                "code completion": "code_generation",
                "rag": "retrieval",
                "embedding": "embeddings",
                "vector": "vector_search",
                "search": "search",
                "scraping": "web_scraping",
                "crawler": "web_crawling",
                "research": "research",
                "analyz": "analysis",
                "classifi": "classification",
                "sentiment": "sentiment",
                "translation": "translation",
                "summariz": "summarization",
                "ocr": "ocr",
                "object detection": "object_detection",
                "face": "face_recognition",
                "music": "music_generation",
                "audio": "audio_processing",
                "chat": "chat",
                "agent": "agent",
                "automation": "automation",
                "workflow": "workflow",
                "data pipeline": "data_pipeline",
                "etl": "data_pipeline",
            }
            for keyword, cap in capability_map.items():
                if keyword in readme and cap not in analysis["capabilities"]:
                    analysis["capabilities"].append(cap)

        return analysis

    def _generate_skill_wrapper(self, skill_name: str, repo_info: dict, analysis: dict) -> str:
        """Generate an EvolvixOS skill wrapper for a GitHub repo."""
        return f'''"""
EvolvixOS Skill — {skill_name}
Auto-installed from: {repo_info["full_name"]}
GitHub stars: {repo_info["stars"]}
License: {repo_info.get("license", "Unknown")}

What it does: {repo_info.get("description", "See README")}

Capabilities: {", ".join(analysis.get("capabilities", ["unknown"]))}
Entry points: {", ".join(analysis.get("entry_points", ["unknown"]))}

This wrapper lets EvolvixOS use this tool as a skill.
"""

import subprocess
import sys
from pathlib import Path
from rich.console import Console

console = Console()

SKILL_DIR = Path(__file__).parent
REPO_URL = "{repo_info["url"]}"
REPO_NAME = "{repo_info["full_name"]}"


class Skill:
    """Auto-generated EvolvixOS skill wrapper for {repo_info["name"]}."""

    def __init__(self, config=None):
        self.config = config or {{}}
        self.name = "{skill_name}"
        self.source = REPO_URL
        self.capabilities = {json.dumps(analysis.get("capabilities", []))}
        self.entry_points = {json.dumps(analysis.get("entry_points", []))}

    def run(self, args):
        """Execute this skill. The agent passes arguments here."""
        action = args.get("action", "info")

        if action == "info":
            return self._info()

        elif action == "run":
            return self._run_entrypoint(args)

        elif action == "exec":
            return self._exec_command(args)

        elif action == "python":
            return self._run_python(args)

        else:
            return self._info()

    def _info(self):
        """Return information about this skill."""
        return f"""Skill: {{self.name}}
Source: {{self.source}}
Capabilities: {{", ".join(self.capabilities) if self.capabilities else "unknown"}}
Entry points: {{", ".join(self.entry_points) if self.entry_points else "unknown"}}

Usage:
  action="run" — Run the main entry point
  action="exec" — Execute a shell command in the skill directory
  action="python" — Run a Python snippet using this skill's dependencies
"""

    def _run_entrypoint(self, args):
        """Run the repo's main entry point."""
        if not self.entry_points:
            return "No entry point found. Use action='exec' to run commands."

        entry = self.entry_points[0]
        entry_path = SKILL_DIR / entry

        if not entry_path.exists():
            return f"Entry point not found: {{entry}}"

        try:
            cmd = args.get("command", f"python3 {{{{entry}}}}")
            result = subprocess.run(
                cmd.split() + args.get("args", []),
                cwd=str(SKILL_DIR),
                capture_output=True, text=True, timeout=60
            )
            output = result.stdout
            if result.stderr:
                output += f"\\n[STDERR]: {{result.stderr}}"
            return output or "Executed (no output)"
        except Exception as e:
            return f"Execution error: {{e}}"

    def _exec_command(self, args):
        """Execute a shell command in the skill directory."""
        command = args.get("command", "")
        if not command:
            return "No command provided."

        try:
            result = subprocess.run(
                command, shell=True, cwd=str(SKILL_DIR),
                capture_output=True, text=True, timeout=60
            )
            output = result.stdout
            if result.stderr:
                output += f"\\n[STDERR]: {{result.stderr}}"
            return output or "Executed (no output)"
        except Exception as e:
            return f"Command error: {{e}}"

    def _run_python(self, args):
        """Run a Python snippet using this skill's installed dependencies."""
        code = args.get("code", "")
        if not code:
            return "No code provided."

        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_path = f.name

        try:
            result = subprocess.run(
                [sys.executable, temp_path],
                cwd=str(SKILL_DIR),
                capture_output=True, text=True, timeout=60,
                env={{**os.environ, "PYTHONPATH": str(SKILL_DIR)}}
            )
            os.unlink(temp_path)
            output = result.stdout
            if result.stderr:
                output += f"\\n[STDERR]: {{result.stderr}}"
            return output or "Executed (no output)"
        except Exception as e:
            os.unlink(temp_path) if os.path.exists(temp_path) else None
            return f"Python error: {{e}}"
'''

    def install_all_discovered(self, min_stars: int = 100, max_install: int = 50) -> dict:
        """Install ALL discovered skills above a star threshold. Zero tokens."""
        console.print(f"[bold cyan]📦 Installing all discovered skills (≥{min_stars} stars)...[/bold cyan]")

        candidates = [
            (name, info) for name, info in self.registry["discovered"].items()
            if info["stars"] >= min_stars and name not in self.registry["installed"]
        ]
        candidates.sort(key=lambda x: -x[1]["stars"])

        if max_install and len(candidates) > max_install:
            console.print(f"[yellow]⚠ {len(candidates)} candidates. Installing top {max_install}.[/yellow]")
            candidates = candidates[:max_install]

        installed = []
        failed = []

        for i, (name, info) in enumerate(candidates):
            console.print(f"\n[{i+1}/{len(candidates)}] {name} ⭐{info['stars']}")
            result = self.install_skill(name)
            if "error" in result:
                failed.append({"repo": name, "error": result["error"]})
            else:
                installed.append(result)

        console.print(f"\n[green]✅ Installed {len(installed)} skills[/green]")
        if failed:
            console.print(f"[yellow]⚠ {len(failed)} failed[/yellow]")

        return {"installed": len(installed), "failed": len(failed), "details": installed, "errors": failed}

    def learn_skill(self, repo_full_name: str) -> dict:
        """Learn how to use a skill by studying its code. Uses local LLM, zero tokens."""
        import ollama

        if repo_full_name not in self.registry["installed"]:
            return {"error": "Skill not installed. Run install_skill() first."}

        skill_info = self.registry["installed"][repo_full_name]
        skill_dir = Path(skill_info["path"])

        console.print(f"[cyan]🧠 Learning: {repo_full_name}[/cyan]")

        # Read key files
        context_parts = []
        total_chars = 0

        for f in skill_dir.rglob("*.py"):
            if "__pycache__" in str(f) or ".git" in str(f):
                continue
            try:
                content = f.read_text(errors="ignore")[:3000]
                chunk = f"=== {f.relative_to(skill_dir)} ===\n{content}\n\n"
                if total_chars + len(chunk) > 20000:
                    break
                context_parts.append(chunk)
                total_chars += len(chunk)

        # Also get README
        for name in ["README.md", "readme.md", "README.rst"]:
            readme = skill_dir / name
            if readme.exists():
                context_parts.insert(0, f"=== README ===\n{readme.read_text(errors='ignore')[:5000]}\n\n")
                break

        context = "\n".join(context_parts)

        # Ask local LLM to understand the tool
        ollama_host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        client = ollama.Client(host=ollama_host)

        prompt = f"""You are EvolvixOS learning a new tool from GitHub.

Tool: {repo_full_name}
Description: {skill_info.get('description', 'N/A')}
Capabilities: {skill_info.get('analysis', {}).get('capabilities', [])}

Source code:
{context}

Analyze this tool and explain:
1. What it does (be specific)
2. How to use it (exact commands or function calls)
3. What inputs it needs
4. What outputs it produces
5. When EvolvixOS should use this skill (give 3 example use cases)
6. Any limitations or requirements

Be practical and specific. This knowledge will be used to decide when to invoke this skill."""

        try:
            response = client.chat(
                model=os.environ.get("EVOLVIX_MODEL", "deepseek-r1:7b"),
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0.2, "num_ctx": 32768},
            )
            knowledge = response["message"]["content"]

            # Save learned knowledge
            self.registry["learned"][repo_full_name] = {
                "knowledge": knowledge,
                "learned_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "skill_name": skill_info["skill_name"],
            }
            self._save_registry()

            # Also save to agent memory
            knowledge_file = self.cache_dir / f"learned_{skill_info['skill_name']}.md"
            knowledge_file.write_text(knowledge)

            console.print(f"[green]✅ Learned how to use {repo_full_name}[/green]")
            return {"status": "learned", "knowledge": knowledge[:500]}

        except Exception as e:
            console.print(f"[red]Learning failed: {e}[/red]")
            return {"error": str(e)}

    def learn_all_installed(self) -> dict:
        """Learn how to use ALL installed skills. Zero tokens."""
        installed = [name for name in self.registry["installed"] if name not in self.registry["learned"]]

        console.print(f"[bold cyan]🧠 Learning {len(installed)} installed skills...[/bold cyan]")

        learned = 0
        for i, name in enumerate(installed):
            console.print(f"  [{i+1}/{len(installed)}] {name}")
            result = self.learn_skill(name)
            if "error" not in result:
                learned += 1

        console.print(f"[green]✅ Learned {learned}/{len(installed)} skills[/green]")
        return {"learned": learned, "total": len(installed)}

    def get_skill_catalog(self) -> str:
        """Get a formatted catalog of all discovered/installed/learned skills."""
        table = Table(title="🧬 EvolvixOS GitHub Skill Catalog")
        table.add_column("Repo", style="cyan")
        table.add_column("Stars", justify="right")
        table.add_column("Status", style="green")
        table.add_column("Capabilities", style="yellow")
        table.add_column("Category")

        for name, info in sorted(self.registry["discovered"].items(), key=lambda x: -x[1]["stars"]):
            status = "📦 Installed" if name in self.registry["installed"] else "👁 Discovered"
            if name in self.registry["learned"]:
                status = "🧠 Learned"
            caps = ", ".join(info.get("analysis", {}).get("capabilities", []))[:40] if name in self.registry["installed"] else ""
            table.add_row(
                name[:40],
                str(info["stars"]),
                status,
                caps,
                info.get("category", ""),
            )

        console.print(table)

        stats = {
            "discovered": len(self.registry["discovered"]),
            "installed": len(self.registry["installed"]),
            "learned": len(self.registry["learned"]),
        }
        return json.dumps(stats, indent=2)

    def update_all(self):
        """Update all installed skills from GitHub (git pull)."""
        console.print("[cyan]🔄 Updating all installed skills from GitHub...[/cyan]")
        updated = 0
        for name, info in self.registry["installed"].items():
            skill_dir = Path(info["path"])
            if skill_dir.exists():
                try:
                    subprocess.run(["git", "pull", "--quiet"], cwd=skill_dir, capture_output=True, timeout=30)
                    updated += 1
                except Exception:
                    pass
        console.print(f"[green]✅ Updated {updated} skills[/green]")
        return updated

    def run(self, args: dict) -> str:
        """Execute the skill discovery engine."""
        action = args.get("action", "discover")

        if action == "discover":
            results = self.discover_all(
                max_per_topic=args.get("max_per_topic", 20),
                min_stars=args.get("min_stars", 50),
            )
            return f"Discovered {len(results)} new skills. Total: {len(self.registry['discovered'])}"

        elif action == "install":
            repo = args.get("repo", "")
            if not repo:
                return "Error: provide 'repo' (full name like 'owner/repo')"
            result = self.install_skill(repo)
            return json.dumps(result, indent=2)

        elif action == "install_all":
            result = self.install_all_discovered(
                min_stars=args.get("min_stars", 100),
                max_install=args.get("max_install", 50),
            )
            return json.dumps({"installed": result["installed"], "failed": result["failed"]})

        elif action == "learn":
            repo = args.get("repo", "")
            if not repo:
                return "Error: provide 'repo'"
            result = self.learn_skill(repo)
            return json.dumps(result, indent=2)

        elif action == "learn_all":
            result = self.learn_all_installed()
            return json.dumps(result)

        elif action == "catalog":
            return self.get_skill_catalog()

        elif action == "update":
            count = self.update_all()
            return f"Updated {count} skills"

        elif action == "status":
            return json.dumps({
                "discovered": len(self.registry["discovered"]),
                "installed": len(self.registry["installed"]),
                "learned": len(self.registry["learned"]),
                "categories": len(self.search_topics),
            }, indent=2)

        else:
            return f"Unknown action: {action}. Use: discover, install, install_all, learn, learn_all, catalog, update, status"
