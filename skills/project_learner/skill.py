"""
EvolvixOS — Project Learner Skill
Eats any codebase, understands it, and answers questions about it.
100% local using Ollama. Zero tokens, zero external APIs.

When you feed Evolvix a project:
  1. It scans the directory structure
  2. Reads and indexes all source files
  3. Detects the tech stack (languages, frameworks, databases)
  4. Generates a project summary using local LLM
  5. Can then answer any question about the project with deep context
"""

import os
import json
import time
import hashlib
from pathlib import Path
from typing import Optional
from rich.console import Console
import ollama

console = Console()

# File extensions to analyze (skip binaries, media, deps)
ANALYZE_EXTENSIONS = {
    # Code
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".kt", ".go", ".rs", ".c", ".cpp", ".h", ".hpp",
    ".cs", ".rb", ".php", ".swift", ".dart", ".scala", ".lua", ".pl", ".r", ".jl",
    # Web
    ".html", ".css", ".scss", ".sass", ".less", ".vue", ".svelte", ".astro",
    # Data
    ".json", ".yaml", ".yml", ".toml", ".ini", ".env.example", ".cfg",
    ".sql", ".graphql", ".gql", ".proto",
    # Docs
    ".md", ".txt", ".rst", ".adoc",
    # Config
    ".dockerfile", ".sh", ".bash", ".zsh", ".bat", ".ps1",
    ".gitignore", ".dockerignore", ".editorconfig",
    "Dockerfile", "Makefile", "CMakeLists.txt", "requirements.txt", "package.json",
    "go.mod", "Cargo.toml", "pom.xml", "build.gradle", "Gemfile",
}

# Directories to skip
SKIP_DIRS = {
    "node_modules", ".git", "__pycache__", ".venv", "venv", "env",
    ".idea", ".vscode", "dist", "build", ".next", ".nuxt", "target",
    "vendor", "bower_components", ".pytest_cache", ".mypy_cache",
    "coverage", ".cache", "tmp", "logs",
}

# Tech stack detection patterns
TECH_PATTERNS = {
    "Python": ["requirements.txt", "setup.py", "pyproject.toml", "Pipfile", "manage.py", "app.py", "main.py"],
    "Django": ["manage.py", "settings.py", "wsgi.py", "asgi.py"],
    "Flask": ["app.py", "wsgi.py", "flask"],
    "FastAPI": ["main.py", "fastapi", "uvicorn"],
    "Node.js": ["package.json", "server.js", "index.js"],
    "Express": ["express", "package.json"],
    "Next.js": ["next.config", "package.json"],
    "React": ["package.json", ".jsx", ".tsx", "react"],
    "Vue.js": ["vue.config", ".vue", "package.json"],
    "TypeScript": ["tsconfig.json", ".ts", ".tsx"],
    "Rust": ["Cargo.toml", "main.rs", "lib.rs"],
    "Go": ["go.mod", "main.go"],
    "Java": ["pom.xml", "build.gradle", ".java"],
    "Spring Boot": ["spring", "application.properties", "application.yml"],
    "Kotlin": ["build.gradle.kts", ".kt"],
    "Docker": ["Dockerfile", "docker-compose.yml", "docker-compose.yaml"],
    "PostgreSQL": ["postgresql", "psql", "pg_"],
    "MongoDB": ["mongodb", "mongoose", "pymongo"],
    "Redis": ["redis", "redis-py", "ioredis"],
    "Kubernetes": ["k8s", "deployment.yaml", "kubernetes", "kustomization.yaml"],
    "GraphQL": ["graphql", "gql", "schema.graphql", "Apollo"],
    "AWS": ["aws", "boto3", "serverless.yml", "sam.yaml"],
    "Terraform": ["terraform", ".tf"],
    "Flutter": ["pubspec.yaml", ".dart"],
    "Swift/iOS": ["Package.swift", ".swift", "xcodeproj"],
    "C++": ["CMakeLists.txt", ".cpp", ".hpp"],
    "Unity": ["UnityEngine", ".unity", "Assembly-CSharp"],
    "Godot": ["gdscript", ".gd", "project.godot"],
}


class ProjectLearner:
    """Learns and understands any project. Fully local, zero tokens."""

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.projects = {}  # name → project data
        self.ollama_host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        self.ollama = ollama.Client(host=self.ollama_host)
        self.primary_model = os.environ.get("EVOLVIX_MODEL", "deepseek-r1:7b")
        self.coder_model = os.environ.get("EVOLVIX_CODER_MODEL", "qwen2.5-coder:7b")
        self.max_file_size = self.config.get("max_file_size", 50000)  # chars per file
        self.max_files = self.config.get("max_files", 500)  # max files to index
        self.db_dir = Path(self.config.get("db_dir", "./data/projects"))
        self.db_dir.mkdir(parents=True, exist_ok=True)

    
    def run(self, args: dict) -> str:
        """Standard EvolvixOS skill interface."""
        import json
        action = args.get("action", "load")
        
        if action == "load":
            result = self.load_project(args.get("path", "."), args.get("name"))
            return json.dumps(result, indent=2)
        elif action == "ask":
            return self.ask(args.get("project", ""), args.get("question", ""))
        elif action == "represent":
            return self.get_representation_prompt(args.get("project", ""))
        else:
            return f"Unknown action: {action}. Use: load, ask, represent"

def _should_analyze(self, filepath: Path) -> bool:
        """Check if a file should be analyzed."""
        name = filepath.name
        ext = filepath.suffix.lower()

        # Check by name
        if name in SKIP_DIRS:
            return False
        if name in ANALYZE_EXTENSIONS or name in {"Dockerfile", "Makefile", "CMakeLists.txt", "requirements.txt", "package.json", "go.mod", "Cargo.toml", "pom.xml", "build.gradle", "Gemfile"}:
            return True
        # Check by extension
        if ext in ANALYZE_EXTENSIONS:
            return True
        return False

    def _detect_tech_stack(self, root: Path, files: list) -> list:
        """Detect what technologies the project uses."""
        detected = set()
        file_names = {f["name"] for f in files}
        file_exts = {Path(f["name"]).suffix.lower() for f in files}
        all_content = " ".join(f.get("content", "")[:500] for f in files[:50]).lower()

        for tech, markers in TECH_PATTERNS.items():
            for marker in markers:
                if marker in file_names or marker in file_exts:
                    detected.add(tech)
                    break
                # Check file contents for framework imports
                if marker.startswith(".") == False and len(marker) > 3 and marker.lower() in all_content:
                    if tech in {"Django", "Flask", "FastAPI", "Express", "Next.js", "React", "Vue.js", "Spring Boot", "GraphQL"}:
                        detected.add(tech)
                        break

        return sorted(detected)

    def _scan_directory(self, root: Path) -> list:
        """Scan a directory and return file list with contents."""
        files = []
        count = 0

        for item in root.rglob("*"):
            # Skip directories in skip list
            if any(part in SKIP_DIRS for part in item.parts):
                continue

            if item.is_file() and self._should_analyze(item):
                try:
                    size = item.stat().st_size
                    if size > self.max_file_size:
                        content = item.read_text(encoding="utf-8", errors="ignore")[:self.max_file_size]
                        content += "\n... [truncated]"
                    else:
                        content = item.read_text(encoding="utf-8", errors="ignore")

                    rel_path = str(item.relative_to(root))
                    files.append({
                        "path": rel_path,
                        "name": item.name,
                        "ext": item.suffix.lower(),
                        "size": size,
                        "content": content,
                    })
                    count += 1

                    if count >= self.max_files:
                        console.print(f"[yellow]⚠ Max files ({self.max_files}) reached. Scanning first {count} files.[/yellow]")
                        break
                except Exception as e:
                    continue

        return files

    def _generate_project_summary(self, files: list, tech_stack: list) -> str:
        """Use local LLM to understand and summarize the project. Zero tokens."""
        # Build context from key files
        key_files_content = []
        # Prioritize: README, main entry points, config files
        priority_names = {"readme.md", "main.py", "app.py", "index.js", "server.js", "main.go", "main.rs", "package.json", "requirements.txt", "dockerfile", "cargo.toml", "go.mod"}

        key_files = []
        for f in files:
            if f["name"].lower() in priority_names:
                key_files.append(f)
        # Add some regular source files too
        key_files.extend([f for f in files if f not in key_files][:20])

        # Build context (limited to avoid overflowing context window)
        context_parts = []
        total_chars = 0
        for f in key_files[:30]:
            chunk = f"=== {f['path']} ===\n{f['content'][:2000]}\n\n"
            if total_chars + len(chunk) > 30000:
                break
            context_parts.append(chunk)
            total_chars += len(chunk)

        context = "\n".join(context_parts)

        prompt = f"""Analyze this codebase and provide a comprehensive summary.

Tech stack detected: {', '.join(tech_stack) if tech_stack else 'unknown'}

Key files from the project:

{context}

Provide a detailed analysis:
1. What this project does (purpose and main functionality)
2. Architecture (how it's structured, main components)
3. Key entry points (where execution starts)
4. Dependencies and integrations
5. How to run it (if visible from config files)
6. Notable patterns or issues

Be specific and reference actual file paths and code you see."""

        try:
            response = self.ollama.chat(
                model=self.coder_model,
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0.2, "num_ctx": 32768},
            )
            return response["message"]["content"]
        except Exception as e:
            return f"Summary generation failed: {e}. Basic info: {len(files)} files, tech: {tech_stack}"

    def load_project(self, path: str, name: Optional[str] = None) -> dict:
        """Load and analyze a project. Returns project data."""
        root = Path(path).resolve()
        if not root.exists():
            raise FileNotFoundError(f"Path not found: {root}")

        name = name or root.name
        console.print(f"[cyan]📂 Loading project: {name} from {root}[/cyan]")

        # Step 1: Scan files
        console.print("  [blue]Scanning files...[/blue]")
        files = self._scan_directory(root)
        console.print(f"  [green]Found {len(files)} analyzable files[/green]")

        # Step 2: Detect tech stack
        console.print("  [blue]Detecting tech stack...[/blue]")
        tech_stack = self._detect_tech_stack(root, files)
        console.print(f"  [green]Tech: {', '.join(tech_stack) if tech_stack else 'unknown'}[/green]")

        # Step 3: Build file index (path → content summary)
        file_index = {}
        for f in files:
            file_index[f["path"]] = {
                "name": f["name"],
                "ext": f["ext"],
                "size": f["size"],
                "preview": f["content"][:500],
            }

        # Step 4: Generate deep summary with LLM
        console.print("  [blue]Analyzing project with local LLM (zero tokens)...[/blue]")
        summary = self._generate_project_summary(files, tech_stack)
        console.print("  [green]✅ Project understood[/green]")

        # Step 5: Extract key files
        key_files = [f["path"] for f in files if f["name"].lower() in {"readme.md", "main.py", "app.py", "index.js", "server.js", "package.json", "requirements.txt", "dockerfile", "go.mod", "cargo.toml"}]

        # Build project data
        project_data = {
            "name": name,
            "path": str(root),
            "description": summary,
            "tech_stack": tech_stack,
            "file_count": len(files),
            "key_files": key_files,
            "file_index": file_index,
            "loaded_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

        # Store files content for Q&A
        self.projects[name] = project_data
        self.projects[name]["_files"] = files  # Internal, for Q&A context

        # Save to disk for persistence
        db_file = self.db_dir / f"{name}.json"
        with open(db_file, "w") as f:
            save_data = {k: v for k, v in project_data.items() if k != "_files"}
            json.dump(save_data, f, indent=2, ensure_ascii=False)

        console.print(f"[green]✅ Project '{name}' loaded and understood[/green]")
        return project_data

    def ask(self, project_name: str, question: str) -> str:
        """Answer a question about a loaded project. Zero tokens."""
        if project_name not in self.projects:
            # Try to reload from disk
            db_file = self.db_dir / f"{project_name}.json"
            if db_file.exists():
                with open(db_file) as f:
                    self.projects[project_name] = json.load(f)
            else:
                return f"Project '{project_name}' not found. Load it first."

        project = self.projects[project_name]

        # Find relevant files based on the question
        relevant_files = self._find_relevant_files(project, question)

        # Build context from relevant files
        context_parts = []
        total_chars = 0
        for f in relevant_files[:15]:
            content = f.get("content", "")
            chunk = f"=== {f.get('path', f.get('name', 'unknown'))} ===\n{content[:3000]}\n\n"
            if total_chars + len(chunk) > 25000:
                break
            context_parts.append(chunk)
            total_chars += len(chunk)

        context = "\n".join(context_parts)
        summary = project.get("description", "")

        prompt = f"""You are EvolvixOS, representing the project '{project_name}'.

Project summary:
{summary}

Relevant source files:

{context}

Question: {question}

Answer the question as an expert who deeply understands this codebase.
Reference specific files and code when relevant. If you don't know, say so.
Be clear and specific."""

        try:
            response = self.ollama.chat(
                model=self.coder_model,
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0.2, "num_ctx": 32768},
            )
            return response["message"]["content"]
        except Exception as e:
            return f"Failed to answer: {e}"

    def _find_relevant_files(self, project: dict, question: str) -> list:
        """Find files most relevant to a question. Local keyword matching."""
        files = project.get("_files", [])
        if not files:
            # Rebuild from index
            for path, info in project.get("file_index", {}).items():
                files.append({"path": path, "name": info["name"], "content": info.get("preview", "")})

        question_words = set(question.lower().split())
        scored = []

        for f in files:
            score = 0
            path_lower = f.get("path", "").lower()
            content_lower = f.get("content", "")[:2000].lower()

            # Score by path name matches
            for word in question_words:
                if len(word) > 2 and word in path_lower:
                    score += 3
                if len(word) > 2 and word in content_lower:
                    score += 1

            # Prioritize key files
            if f.get("name", "").lower() in {"readme.md", "main.py", "app.py", "index.js", "package.json"}:
                score += 5

            if score > 0:
                scored.append((score, f))

        scored.sort(key=lambda x: -x[0])
        return [f for _, f in scored]

    def get_representation_prompt(self, project_name: str) -> str:
        """Get a system prompt that makes Evolvix represent a project."""
        if project_name not in self.projects:
            return ""

        project = self.projects[project_name]
        return f"""You are EvolvixOS, the AI representative for the project '{project_name}'.

You have deep knowledge of this project:
- Tech stack: {', '.join(project.get('tech_stack', []))}
- {project.get('file_count', 0)} files analyzed
- Project description: {project.get('description', 'N/A')[:2000]}

When asked about this project, answer as someone who built it and knows it inside out.
Be enthusiastic but accurate. Reference specific files and components.
If asked something outside the project scope, you can still help but note it's outside the project context.
"""


# Skill interface compatibility
Skill = ProjectLearner
