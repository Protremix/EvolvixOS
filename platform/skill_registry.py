"""
EvolvixOS Agent Skills System
Adopted from awesome-llm-apps agent_skills format.

Each skill is a directory with:
- SKILL.md: YAML frontmatter + markdown instructions
- scripts/: Python scripts the skill can run
- references/: Optional reference files

Skills are discoverable, installable, and executable.
"""
import os
import json
import yaml
import importlib
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class AgentSkill:
    """A discoverable agent skill."""
    name: str
    description: str
    author: str = ""
    version: str = "1.0.0"
    license: str = "Apache-2.0"
    source: str = ""
    instructions: str = ""
    scripts: List[str] = None
    metadata: Dict = None


class SkillRegistry:
    """Registry for discovering and managing agent skills."""

    def __init__(self, skills_dir: str = None):
        self.skills_dir = skills_dir or "/opt/evolvixos/knowledge/skills"
        self.skills: Dict[str, AgentSkill] = {}
        self._discover()

    def _discover(self):
        """Discover all skills in the skills directory."""
        if not os.path.exists(self.skills_dir):
            return

        for name in os.listdir(self.skills_dir):
            skill_path = os.path.join(self.skills_dir, name)
            skill_md = os.path.join(skill_path, "SKILL.md")

            if os.path.isdir(skill_path) and os.path.exists(skill_md):
                skill = self._parse_skill_md(skill_md, name)
                if skill:
                    self.skills[name] = skill

    def _parse_skill_md(self, path: str, name: str) -> Optional[AgentSkill]:
        """Parse a SKILL.md file into an AgentSkill."""
        try:
            with open(path, "r") as f:
                content = f.read()

            # Split YAML frontmatter from markdown body
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    frontmatter = yaml.safe_load(parts[1])
                    body = parts[2].strip()
                else:
                    frontmatter = {}
                    body = content
            else:
                frontmatter = {}
                body = content

            # Find scripts
            scripts_dir = os.path.join(os.path.dirname(path), "scripts")
            scripts = []
            if os.path.exists(scripts_dir):
                scripts = [f for f in os.listdir(scripts_dir) if f.endswith(".py")]

            return AgentSkill(
                name=frontmatter.get("name", name),
                description=frontmatter.get("description", ""),
                author=frontmatter.get("metadata", {}).get("author", ""),
                version=frontmatter.get("metadata", {}).get("version", "1.0.0"),
                license=frontmatter.get("license", "Apache-2.0"),
                source=frontmatter.get("metadata", {}).get("source", ""),
                instructions=body,
                scripts=scripts,
                metadata=frontmatter.get("metadata", {})
            )
        except Exception as e:
            print(f"Error parsing skill {name}: {e}")
            return None

    def list_skills(self) -> List[dict]:
        """List all discovered skills."""
        return [
            {
                "name": s.name,
                "description": s.description[:200] if s.description else "",
                "author": s.author,
                "version": s.version,
                "scripts": s.scripts or [],
                "source": s.source
            }
            for s in self.skills.values()
        ]

    def get_skill(self, name: str) -> Optional[AgentSkill]:
        """Get a skill by name."""
        return self.skills.get(name)

    def run_skill(self, name: str, args: str = "") -> dict:
        """Run a skill's script."""
        skill = self.skills.get(name)
        if not skill:
            return {"error": f"Skill '{name}' not found"}

        skill_dir = os.path.join(self.skills_dir, name)
        scripts_dir = os.path.join(skill_dir, "scripts")

        if not skill.scripts:
            return {"error": "No scripts found for this skill"}

        # Run the first script (or a named one)
        script_name = skill.scripts[0]
        script_path = os.path.join(scripts_dir, script_name)

        if not os.path.exists(script_path):
            return {"error": f"Script {script_name} not found"}

        try:
            import subprocess
            result = subprocess.run(
                ["python3", script_path, args],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=skill_dir
            )
            return {
                "skill": name,
                "script": script_name,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"error": "Script timed out (60s limit)"}
        except Exception as e:
            return {"error": str(e)}

    def install_skill(self, source_dir: str, name: str = None) -> bool:
        """Install a skill from a source directory."""
        skill_name = name or os.path.basename(source_dir)
        dest = os.path.join(self.skills_dir, skill_name)

        if os.path.exists(dest):
            shutil.rmtree(dest)

        shutil.copytree(source_dir, dest)

        # Re-discover
        skill = self._parse_skill_md(os.path.join(dest, "SKILL.md"), skill_name)
        if skill:
            self.skills[skill_name] = skill
            return True
        return False


# Singleton
skill_registry = SkillRegistry()
