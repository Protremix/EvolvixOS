"""
EvolvixOS — Self-Improvement Engine v1.0
EvolvixOS writes new skills for itself when it encounters a task it can't do.

How it works:
1. When the agent can't find a skill for a task, it creates one
2. It writes the skill code using the local LLM (zero tokens)
3. It saves the skill to skills/self_generated/
4. It tests the skill
5. It registers the skill and can use it immediately
6. The skill can be shared with the community

This is how EvolvixOS becomes autonomous and self-evolving.
"""

import os
import json
import time
import importlib
import traceback
from pathlib import Path
from typing import Optional

import ollama
import yaml
from rich.console import Console
from rich.panel import Panel

console = Console()


class SelfImprover:
    """EvolvixOS self-improvement — writes its own skills."""

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.skills_dir = Path(self.config.get("skills_dir", "./skills"))
        self.self_gen_dir = self.skills_dir / "self_generated"
        self.self_gen_dir.mkdir(parents=True, exist_ok=True)
        self.registry_file = self.self_gen_dir / "registry.json"
        self.registry = self._load_registry()

        self.ollama_host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        self.coder_model = self.config.get("coder_model", "qwen2.5-coder:7b")

    def _load_registry(self) -> dict:
        if self.registry_file.exists():
            with open(self.registry_file) as f:
                return json.load(f)
        return {"skills": {}}

    def _save_registry(self):
        with open(self.registry_file, "w") as f:
            json.dump(self.registry, f, indent=2)

    def create_skill(self, task_description: str, skill_name: Optional[str] = None) -> dict:
        """Create a new skill to handle a task EvolvixOS can't currently do."""

        # Generate skill name
        if not skill_name:
            skill_name = self._generate_skill_name(task_description)

        console.print(f"[bold cyan]🧬 Self-generating skill: {skill_name}[/bold cyan]")
        console.print(f"   Task: {task_description}")

        # Generate the skill code using local LLM
        skill_code = self._generate_skill_code(task_description, skill_name)

        if not skill_code:
            return {"error": "Failed to generate skill code"}

        # Save the skill
        skill_dir = self.self_gen_dir / skill_name
        skill_dir.mkdir(parents=True, exist_ok=True)

        init_path = skill_dir / "__init__.py"
        init_path.write_text(f"# Self-generated skill: {skill_name}\n")

        skill_path = skill_dir / "skill.py"
        skill_path.write_text(skill_code)

        console.print(f"[green]✅ Skill code generated and saved[/green]")

        # Test the skill
        test_result = self._test_skill(skill_name, skill_dir)

        # Register the skill
        self.registry["skills"][skill_name] = {
            "name": skill_name,
            "task": task_description,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "path": str(skill_dir),
            "test_result": test_result,
            "iterations": 1,
            "status": "tested" if test_result.get("success") else "needs_fixing",
        }
        self._save_registry()

        if test_result.get("success"):
            console.print(f"[bold green]✅ Skill '{skill_name}' created and tested successfully![/bold green]")
        else:
            console.print(f"[yellow]⚠ Skill needs fixing. Attempting auto-fix...[/yellow]")
            fixed = self._auto_fix_skill(skill_name, task_description, test_result)
            if fixed:
                console.print(f"[green]✅ Auto-fixed successfully![/green]")
            else:
                console.print(f"[yellow]⚠ Auto-fix failed. Skill saved but needs manual review.[/yellow]")

        return {
            "skill_name": skill_name,
            "path": str(skill_dir),
            "test_result": test_result,
            "code": skill_code[:500],
        }

    def _generate_skill_name(self, description: str) -> str:
        """Generate a valid skill name from a task description."""
        import re
        # Take key words from description
        words = re.findall(r"[a-zA-Z]+", description.lower())
        words = [w for w in words if w not in {"the", "a", "an", "to", "for", "and", "or", "of", "in", "on", "at", "is", "it", "this", "that", "with", "from"}]
        name = "_".join(words[:3]) if len(words) >= 3 else "_".join(words) if words else "custom_skill"
        name = re.sub(r"[^a-zA-Z0-9_]", "", name)
        if not name:
            name = "custom_skill"
        return name

    def _generate_skill_code(self, task_description: str, skill_name: str) -> str:
        """Use the local LLM to write Python code for a new skill. Zero tokens."""

        client = ollama.Client(host=self.ollama_host)

        prompt = f"""You are EvolvixOS writing a new skill for itself.

Write a complete, working Python skill module that can: {task_description}

Requirements:
1. The skill must follow the EvolvixOS skill interface exactly
2. Everything must be 100% local — no external API calls, no tokens, no paid services
3. Use only free, open-source Python libraries
4. Include proper error handling
5. Include a docstring explaining what the skill does
6. The Skill class must have __init__(self, config=None) and run(self, args: dict) -> str

Skill template:
```python
\"\"\"EvolvixOS Skill — {skill_name}
Description of what this skill does.
\"\"\"
# Your imports here (only free, open-source libraries)

from rich.console import Console
console = Console()


class Skill:
    def __init__(self, config=None):
        self.config = config or {{}}
        self.name = "{skill_name}"

    def run(self, args: dict) -> str:
        action = args.get("action", "default")
        
        if action == "default":
            return self._default(args)
        # Add more actions as needed

    def _default(self, args):
        # Your implementation here
        return "Result"
```

Write ONLY the Python code. No markdown fences, no explanation. Just the code.
The code must be immediately runnable with no syntax errors."""

        try:
            response = client.chat(
                model=self.coder_model,
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0.2, "num_ctx": 16384},
            )
            code = response["message"]["content"]

            # Strip markdown code fences if present
            if "```python" in code:
                code = code.split("```python")[1].split("```")[0]
            elif "```" in code:
                code = code.split("```")[1].split("```")[0]

            return code.strip()
        except Exception as e:
            console.print(f"[red]Code generation failed: {e}[/red]")
            return ""

    def _test_skill(self, skill_name: str, skill_dir: Path) -> dict:
        """Test a self-generated skill."""
        console.print(f"[blue]🧪 Testing skill: {skill_name}[/blue]")

        try:
            import sys
            sys.path.insert(0, str(self.skills_dir.parent))

            # Try to import the module
            module_path = f"skills.self_generated.{skill_name}.skill"
            module = importlib.import_module(module_path)

            # Instantiate
            skill_instance = module.Skill(config={})

            # Run with default args
            result = skill_instance.run({"action": "default"})

            console.print(f"[green]✅ Test passed: {result[:200]}[/green]")
            return {"success": True, "result": result[:500]}

        except SyntaxError as e:
            console.print(f"[red]Syntax error: {e}[/red]")
            return {"success": False, "error": f"SyntaxError: {e}", "type": "syntax"}
        except ImportError as e:
            console.print(f"[red]Import error: {e}[/red]")
            return {"success": False, "error": f"ImportError: {e}", "type": "import"}
        except Exception as e:
            console.print(f"[red]Runtime error: {e}[/red]")
            return {"success": False, "error": str(e), "type": "runtime", "traceback": traceback.format_exc()}

    def _auto_fix_skill(self, skill_name: str, task_description: str, test_result: dict) -> bool:
        """Try to auto-fix a broken skill using the LLM."""
        skill_dir = self.self_gen_dir / skill_name
        skill_path = skill_dir / "skill.py"

        if not skill_path.exists():
            return False

        current_code = skill_path.read_text()
        error = test_result.get("error", "Unknown error")

        console.print(f"[blue]🔧 Auto-fixing: {error[:100]}[/blue]")

        client = ollama.Client(host=self.ollama_host)

        prompt = f"""You are EvolvixOS fixing a skill it wrote for itself.

The skill was supposed to: {task_description}

The current code has an error:
```
{error}
```

Current code:
```python
{current_code}
```

Fix the code. Return ONLY the corrected Python code. No explanation, no markdown fences.
The fixed code must be immediately runnable."""

        try:
            response = client.chat(
                model=self.coder_model,
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0.1, "num_ctx": 16384},
            )
            fixed_code = response["message"]["content"]

            if "```python" in fixed_code:
                fixed_code = fixed_code.split("```python")[1].split("```")[0]
            elif "```" in fixed_code:
                fixed_code = fixed_code.split("```")[1].split("```")[0]

            skill_path.write_text(fixed_code.strip())

            # Re-test
            new_test = self._test_skill(skill_name, skill_dir)
            self.registry["skills"][skill_name]["test_result"] = new_test
            self.registry["skills"][skill_name]["iterations"] += 1
            self.registry["skills"][skill_name]["status"] = "tested" if new_test.get("success") else "needs_fixing"
            self._save_registry()

            return new_test.get("success", False)

        except Exception as e:
            console.print(f"[red]Auto-fix failed: {e}[/red]")
            return False

    def list_self_generated_skills(self) -> str:
        """List all self-generated skills."""
        if not self.registry["skills"]:
            return "No self-generated skills yet."

        from rich.table import Table
        table = Table(title="🧬 Self-Generated Skills")
        table.add_column("Name", style="cyan")
        table.add_column("Task", style="yellow")
        table.add_column("Status", style="green")
        table.add_column("Iterations", justify="right")

        for name, info in self.registry["skills"].items():
            status = "✅ Working" if info["test_result"].get("success") else "⚠ Needs fixing"
            table.add_row(name, info["task"][:50], status, str(info["iterations"]))

        console.print(table)
        return json.dumps({k: v["task"] for k, v in self.registry["skills"].items()}, indent=2)

    def run(self, args: dict) -> str:
        """Execute the self-improvement engine."""
        action = args.get("action", "list")

        if action == "create":
            task = args.get("task", "")
            if not task:
                return "Error: provide 'task' describing what the skill should do"
            result = self.create_skill(task, args.get("name"))
            return json.dumps(result, indent=2)

        elif action == "list":
            return self.list_self_generated_skills()

        elif action == "fix":
            name = args.get("name", "")
            if name not in self.registry["skills"]:
                return f"Skill '{name}' not found"
            skill_info = self.registry["skills"][name]
            test_result = self._test_skill(name, self.self_gen_dir / name)
            if not test_result.get("success"):
                fixed = self._auto_fix_skill(name, skill_info["task"], test_result)
                return f"Fixed: {fixed}" if fixed else "Auto-fix failed"
            return "Skill already working"

        else:
            return f"Unknown action: {action}. Use: create, list, fix"
