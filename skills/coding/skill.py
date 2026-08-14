"""
EvolvixOS — Coding Skill
Code generation using local Ollama models (Qwen2.5-Coder). Zero tokens.
Can also execute code locally.
"""

import subprocess
import tempfile
import os
import json
from pathlib import Path
from rich.console import Console
import ollama

console = Console()


class Skill:
    """Coding skill — generates and optionally executes code locally."""

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.output_dir = Path(self.config.get("output_dir", "./output/code"))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.allow_execution = self.config.get("allow_execution", True)
        self.languages = self.config.get("languages", ["python", "javascript", "bash"])
        self.coder_model = "qwen2.5-coder:7b"
        self.ollama_host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        self.ollama = ollama.Client(host=self.ollama_host)

    def generate_code(self, description: str, language: str = "python") -> str:
        """Generate code using local Qwen2.5-Coder. Zero tokens."""
        prompt = f"""You are an expert {language} programmer. Generate clean, well-commented, production-ready code for the following request:

{description}

Requirements:
- Write complete, working code (no placeholders)
- Include error handling
- Add comments explaining key parts
- Use modern best practices
- Output ONLY the code in a markdown code block

Language: {language}"""

        response = self.ollama.chat(
            model=self.coder_model,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.2, "num_ctx": 8192},
        )

        code = response["message"]["content"]

        # Extract code from markdown block
        if "```" in code:
            start = code.find("```")
            # Skip language identifier
            lang_end = code.find("\n", start)
            content_start = lang_end + 1 if lang_end > start else start + 3
            end = code.find("```", content_start)
            if end > content_start:
                code = code[content_start:end].strip()

        # Save to file
        ext_map = {
            "python": ".py", "javascript": ".js", "bash": ".sh",
            "html": ".html", "css": ".css", "sql": ".sql",
        }
        ext = ext_map.get(language, ".txt")
        filename = self.output_dir / f"generated_{int(__import__('time').time())}{ext}"
        filename.write_text(code, encoding="utf-8")
        console.print(f"[green]💾 Code saved: {filename}[/green]")

        return code

    def execute_code(self, code: str, language: str = "python") -> str:
        """Execute code locally. No external services."""
        if not self.allow_execution:
            return "Code execution is disabled in config."

        ext_map = {
            "python": ".py", "javascript": ".js", "bash": ".sh",
        }
        ext = ext_map.get(language, ".txt")

        with tempfile.NamedTemporaryFile(mode="w", suffix=ext, delete=False) as f:
            f.write(code)
            temp_path = f.name

        try:
            if language == "python":
                result = subprocess.run(
                    ["python3", temp_path],
                    capture_output=True, text=True, timeout=30
                )
            elif language == "bash":
                result = subprocess.run(
                    ["bash", temp_path],
                    capture_output=True, text=True, timeout=30
                )
            elif language == "javascript":
                result = subprocess.run(
                    ["node", temp_path],
                    capture_output=True, text=True, timeout=30
                )
            else:
                os.unlink(temp_path)
                return f"Execution not supported for {language}"

            output = result.stdout
            if result.stderr:
                output += f"\n[STDERR]:\n{result.stderr}"

            os.unlink(temp_path)
            return output if output else "Code executed successfully (no output)."

        except subprocess.TimeoutExpired:
            os.unlink(temp_path)
            return "Execution timed out (30s limit)."
        except Exception as e:
            os.unlink(temp_path)
            return f"Execution error: {e}"

    def run(self, args: dict) -> str:
        """Execute the coding skill."""
        action = args.get("action", "generate")
        description = args.get("description", args.get("query", ""))
        language = args.get("language", "python")

        if action == "generate":
            if not description:
                return "Error: no description provided."
            code = self.generate_code(description, language)
            return f"Generated {language} code:\n\n```\n{code}\n```"

        elif action == "execute":
            code = args.get("code", "")
            if not code:
                return "Error: no code provided."
            result = self.execute_code(code, language)
            return f"Execution result:\n{result}"

        elif action == "generate_and_execute":
            if not description:
                return "Error: no description provided."
            code = self.generate_code(description, language)
            console.print(f"[cyan]▶ Executing generated code...[/cyan]")
            result = self.execute_code(code, language)
            return f"Generated {language} code:\n\n```\n{code}\n```\n\nExecution result:\n{result}"

        else:
            return f"Unknown action: {action}. Use 'generate', 'execute', or 'generate_and_execute'."
