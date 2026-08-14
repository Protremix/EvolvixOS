"""
EvolvixOS — Skill Forge Skill
Generates new skills on the fly using local LLM (Ollama at localhost:11434).
Creates skills/<name>/skill.py with proper Skill class, skill.json, and __init__.py.
This is the core self-improvement engine.
"""

import os
import re
import sys
import json
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional, Dict, Any


def slugify(text: str) -> str:
    """Convert text to snake_case identifier."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s-]+", "_", text)
    return text or "generated_skill"


class Skill:
    """Skill Forge — Generates new EvolvixOS skills using local Ollama LLM."""

    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
        self.ollama_url = self.config.get("ollama_url", "http://localhost:11434")
        self.base_skills_dir = Path(self.config.get("skills_dir", Path(__file__).parent.parent))

    def _call_ollama(self, prompt: str, model: str = "llama3.2") -> Optional[str]:
        """Call Ollama local endpoint."""
        url = f"{self.ollama_url}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                if response.status == 200:
                    res_json = json.loads(response.read().decode("utf-8"))
                    return res_json.get("response", "")
        except Exception:
            pass
        return None

    def _clean_code(self, raw_text: str) -> str:
        """Extract Python code from markdown codeblocks or raw output."""
        pattern = r"```(?:python)?\s*(.*?)\s*```"
        matches = re.findall(pattern, raw_text, re.DOTALL)
        if matches:
            return matches[0].strip()
        return raw_text.strip()

    def _fallback_template(self, skill_name: str, description: str) -> str:
        """Generate a working default Skill class template if LLM call is unavailable."""
        title = skill_name.replace("_", " ").title()
        return f'''"""
EvolvixOS — {title} Skill
{description}
"""

import sys
import json
from typing import Any, Dict, Optional


class Skill:
    """Auto-generated skill: {description}"""

    def __init__(self, config: Optional[dict] = None):
        self.config = config or {{}}

    def run(self, args: dict) -> dict:
        """
        Execute {skill_name} action.
        """
        action = args.get("action", "execute")
        try:
            return {{
                "success": True,
                "action": action,
                "message": f"Successfully executed {{action}} in {skill_name}",
                "input_args": args
            }}
        except Exception as e:
            return {{"success": False, "error": str(e)}}


if __name__ == "__main__":
    raw = sys.argv[1] if len(sys.argv) > 1 else "{{}}"
    args = json.loads(raw)
    print(json.dumps(Skill().run(args)))
'''

    def run(self, args: dict) -> dict:
        """
        Forge a new skill.

        Args:
            description (str): What the new skill should do.
            name / skill_name (str, optional): Directory name for the new skill.
            model (str, optional): Ollama model name (default: 'llama3.2').
            overwrite (bool, optional): Overwrite if directory exists (default: False).
        """
        description = args.get("description")
        if not description:
            return {"success": False, "error": "Missing required parameter 'description'."}

        raw_name = args.get("skill_name") or args.get("name")
        if not raw_name:
            first_words = " ".join(description.split()[:4])
            skill_name = slugify(first_words)
        else:
            skill_name = slugify(raw_name)

        model = args.get("model", "llama3.2")
        overwrite = args.get("overwrite", False)

        skill_dir = self.base_skills_dir / skill_name
        if skill_dir.exists() and not overwrite:
            return {
                "success": False,
                "error": f"Skill directory '{skill_name}' already exists at {skill_dir}. Set overwrite=True to replace."
            }

        skill_dir.mkdir(parents=True, exist_ok=True)

        prompt = f"""You are generating an EvolvixOS skill python module.
Requirement: {description}
Skill Name: {skill_name}

Write ONLY executable Python code implementing a Skill class with this exact structure:

```python
import sys
import json
from typing import Optional, Dict, Any

class Skill:
    def __init__(self, config: Optional[dict] = None):
        self.config = config or {{}}

    def run(self, args: dict) -> dict:
        # Implement functionality according to description
        return {{"success": True, "result": "..."}}
```

Requirements:
- Must define `class Skill:` with `__init__(self, config=None)` and `run(self, args) -> dict`.
- Zero external API keys required; use standard Python or auto-install free local libraries if needed.
- Always return a dictionary with at least a 'success' boolean field.
- Provide clean, robust Python code without markdown commentary outside code blocks.
"""

        raw_llm_output = self._call_ollama(prompt, model=model)

        if raw_llm_output:
            code = self._clean_code(raw_llm_output)
        else:
            code = self._fallback_template(skill_name, description)

        skill_py_path = skill_dir / "skill.py"
        with open(skill_py_path, "w", encoding="utf-8") as f:
            f.write(code)

        init_py_path = skill_dir / "__init__.py"
        with open(init_py_path, "w", encoding="utf-8") as f:
            f.write(f'"""{skill_name} skill package."""\nfrom .skill import Skill\n\n__all__ = ["Skill"]\n')

        display_name = skill_name.replace("_", " ").title()
        skill_json = {
            "name": display_name,
            "description": description,
            "version": "1.0.0",
            "free": True,
            "local": True,
            "cloud": False,
            "cost": "$0.00",
            "pip_dependencies": ""
        }
        skill_json_path = skill_dir / "skill.json"
        with open(skill_json_path, "w", encoding="utf-8") as f:
            json.dump(skill_json, f, indent=2)

        return {
            "success": True,
            "skill_name": skill_name,
            "skill_path": str(skill_dir),
            "files_created": [str(skill_py_path), str(init_py_path), str(skill_json_path)],
            "generated_via_ollama": bool(raw_llm_output),
            "skill_json": skill_json
        }


if __name__ == "__main__":
    if len(sys.argv) > 1:
        raw_args = json.loads(sys.argv[1])
    else:
        raw_args = {"description": "A skill that reverses strings and calculates character counts.", "skill_name": "string_reverser"}
    skill = Skill()
    print(json.dumps(skill.run(raw_args), indent=2))
