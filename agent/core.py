"""
EvolvixOS — Agent Core v0.3
The brain of the system. Uses Ollama locally. Zero external tokens, zero API calls.

The agent loop:
  1. PERCEIVE — receive user request or continue from plan
  2. THINK — use LLM to reason about what to do
  3. PLAN — break the task into steps
  4. ACT — execute a skill (research, coding, video, GitHub skills, etc.)
  5. OBSERVE — check the result
  6. REFLECT — was the result good? (optional)
  7. LOOP — continue until task is done

v0.3: Now discovers and uses skills auto-installed from GitHub.
"""

import json
import time
import traceback
import importlib
from pathlib import Path
from typing import Optional

import ollama
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

console = Console()


class AgentCore:
    """The main EvolvixOS agent brain. Fully local, zero tokens. Gets smarter from GitHub."""

    def __init__(self, config_path: str = "config/config.yaml"):
        self.config = self._load_config(config_path)
        self.llm_config = self.config["llm"]
        self.agent_config = self.config["agent"]
        self.skills_config = self.config.get("skills", {})

        # Initialize Ollama client (local, no external calls)
        self.ollama_client = ollama.Client(host=self.llm_config["host"])

        # Initialize memory
        from agent.memory import MemoryStore
        self.memory = MemoryStore(self.agent_config.get("memory_db", "./data/evolvix_memory.db"))

        # Initialize skills (lazy-loaded)
        self._skills = {}
        self._available_skills = self._discover_skills()

        # Load GitHub skill registry (what's been discovered/installed/learned)
        self._github_registry = self._load_github_registry()

        # System prompt — defines who Evolvix is
        self.system_prompt = self._build_system_prompt()

        # Conversation history
        self.conversation = []

    def _load_config(self, path: str) -> dict:
        with open(path, "r") as f:
            return yaml.safe_load(f)["config"]

    def _discover_skills(self) -> dict:
        """Find all available skills — both built-in and GitHub-installed."""
        skills = {}
        skills_dir = Path(__file__).parent.parent / "skills"

        # Built-in skills (have skill.py)
        for skill_dir in skills_dir.iterdir():
            if skill_dir.is_dir() and (skill_dir / "skill.py").exists():
                skill_name = skill_dir.name
                skill_config = self.skills_config.get(skill_name, {})
                if skill_config.get("enabled", True):
                    skills[skill_name] = {
                        "name": skill_name,
                        "path": str(skill_dir),
                        "config": skill_config,
                        "source": "builtin",
                    }

        # GitHub-installed skills (have evolvix_skill.py)
        for skill_dir in skills_dir.iterdir():
            if skill_dir.is_dir() and (skill_dir / "evolvix_skill.py").exists():
                skill_name = skill_dir.name
                if skill_name not in skills:  # Don't override builtins
                    skills[skill_name] = {
                        "name": skill_name,
                        "path": str(skill_dir),
                        "config": {},
                        "source": "github",
                    }

        return skills

    def _load_github_registry(self) -> dict:
        """Load the GitHub skill discovery registry."""
        registry_path = Path(self.config.get("skills", {}).get("github_discovery", {}).get("cache_dir", "./data/github_cache")) / "skill_registry.json"
        if registry_path.exists():
            with open(registry_path) as f:
                return json.load(f)
        return {"discovered": {}, "installed": {}, "learned": {}}

    def _build_system_prompt(self) -> str:
        """Build the system prompt that defines Evolvix's identity and capabilities."""

        # Built-in skills
        builtin_skills = [
            f"  - {name} ({info['source']}): {info.get('config', {}).get('description', 'AI skill')}"
            for name, info in self._available_skills.items()
            if info["source"] == "builtin"
        ]

        # GitHub-installed skills
        github_skills = []
        for name, info in self._available_skills.items():
            if info["source"] == "github":
                repo_info = self._github_registry.get("installed", {}).get(
                    name.replace("github_", ""), {}
                )
                desc = repo_info.get("description", "GitHub-installed skill")
                caps = repo_info.get("analysis", {}).get("capabilities", [])
                caps_str = f" (capabilities: {', '.join(caps)})" if caps else ""
                github_skills.append(f"  - {name} (github): {desc}{caps_str}")

        # Learned knowledge (from GitHub skills)
        learned_skills = []
        for repo, info in self._github_registry.get("learned", {}).items():
            learned_skills.append(f"  - {repo}: {info.get('knowledge', '')[:200]}...")

        skill_list = "\n".join(builtin_skills + github_skills)

        github_section = ""
        if github_skills:
            github_section = f"\n\nGitHub-installed skills ({len(github_skills)}):\n" + "\n".join(github_skills)
        if learned_skills:
            github_section += f"\n\nLearned skill knowledge ({len(learned_skills)}):\n" + "\n".join(learned_skills[:10])

        return f"""You are Evolvix, an autonomous AI agent that is part of EvolvixOS v0.3.

You are a 100% local, open-source AI system. You do not use any external APIs, tokens, or paid services. Everything runs locally.

You continuously learn by discovering and installing open-source AI tools from GitHub. You get smarter every day.

Your capabilities (skills you can use):
{skill_list if skill_list else "  (Skills will be loaded as they are activated)"}
{github_section}

You also have a GitHub discovery skill that can:
  - Search GitHub for new AI tools and skills
  - Install them locally (zero tokens)
  - Learn how to use each one
  - Use them in your workflow

When you receive a task, you must:
1. THINK: Reason about what needs to be done. Break complex tasks into steps.
2. ACT: Call a skill to execute. Use this format:
   <skill name="skill_name">{{"action": "do_something", "args": {{...}}}}</skill>
3. OBSERVE: Review the result of the skill execution.
4. CONTINUE: If the task is not complete, think and act again.
5. COMPLETE: When done, provide a final summary.

Rules:
- You are fully autonomous. Make decisions and act.
- If a skill fails, try to recover or use an alternative approach.
- Always explain your reasoning before acting.
- Be efficient — don't repeat work.
- If you don't have a needed skill, search GitHub for one using the github_discovery skill.
- You learn and grow. Every new tool on GitHub makes you smarter.

You are self-hosted, free, and independent. You belong to no corporation.
You learn from the entire open-source community. You are always getting smarter."""

    def _call_llm(self, messages: list, model: Optional[str] = None) -> str:
        """Call the local LLM via Ollama. Zero tokens, zero external calls."""
        model = model or self.llm_config["primary_model"]
        try:
            response = self.ollama_client.chat(
                model=model,
                messages=messages,
                options={
                    "temperature": self.llm_config.get("temperature", 0.7),
                    "num_ctx": self.llm_config.get("num_ctx", 32768),
                },
            )
            return response["message"]["content"]
        except Exception as e:
            console.print(f"[red]LLM error: {e}[/red]")
            return f"[ERROR: LLM call failed: {e}]"

    def _parse_skill_call(self, text: str) -> Optional[dict]:
        """Extract a skill call from the LLM's response."""
        import re
        pattern = r'<skill\s+name="([\w_]+)">(.*?)</skill>'
        match = re.search(pattern, text, re.DOTALL)
        if match:
            skill_name = match.group(1)
            try:
                args = json.loads(match.group(2))
            except json.JSONDecodeError:
                args = {"raw": match.group(2)}
            return {"skill": skill_name, "args": args}
        return None

    def _execute_skill(self, skill_name: str, args: dict) -> str:
        """Load and execute a skill — built-in or GitHub-installed."""
        if skill_name not in self._available_skills:
            # Check if it's a GitHub skill
            github_name = f"github_{skill_name}" if not skill_name.startswith("github_") else skill_name
            if github_name in self._available_skills:
                skill_name = github_name
            else:
                return f"Skill '{skill_name}' not found. Available: {', '.join(self._available_skills.keys())}"

        # Lazy-load the skill module
        if skill_name not in self._skills:
            try:
                skill_info = self._available_skills[skill_name]
                skill_path = Path(skill_info["path"])

                # GitHub skills use evolvix_skill.py, builtins use skill.py
                if (skill_path / "evolvix_skill.py").exists() and skill_info["source"] == "github":
                    # Import from evolvix_skill.py in the skill directory
                    import sys
                    sys.path.insert(0, str(skill_path))
                    from evolvix_skill import Skill as GitHubSkill
                    self._skills[skill_name] = GitHubSkill(config=skill_info.get("config", {}))
                    sys.path.pop(0)
                else:
                    # Built-in skill
                    module = importlib.import_module(f"skills.{skill_name}.skill")
                    skill_config = skill_info.get("config", {})
                    self._skills[skill_name] = module.Skill(config=skill_config)

            except Exception as e:
                return f"Failed to load skill '{skill_name}': {e}\n{traceback.format_exc()}"

        # Execute
        try:
            console.print(f"[cyan]⚡ Executing skill: {skill_name}[/cyan]")
            result = self._skills[skill_name].run(args)
            return result
        except Exception as e:
            return f"Skill '{skill_name}' failed: {e}\n{traceback.format_exc()}"

    def refresh_skills(self):
        """Re-scan for new skills (including newly installed GitHub skills)."""
        self._available_skills = self._discover_skills()
        self._github_registry = self._load_github_registry()
        self.system_prompt = self._build_system_prompt()
        console.print(f"[green]✅ Refreshed: {len(self._available_skills)} skills available[/green]")

    def discover_github_skills(self, min_stars: int = 50):
        """Search GitHub for new AI skills and install them."""
        from skills.github_discovery.skill import GitHubSkillDiscovery
        discovery = GitHubSkillDiscovery(config=self.skills_config.get("github_discovery", {}))

        console.print("[bold cyan]🔍 Discovering new skills from GitHub...[/bold cyan]")
        discovery.discover_all(min_stars=min_stars)

        # Auto-install top skills
        console.print("[bold cyan]📦 Installing top skills...[/bold cyan]")
        discovery.install_all_discovered(min_stars=100, max_install=20)

        # Auto-learn installed skills
        if self.agent_config.get("auto_learn_from_github", True):
            console.print("[bold cyan]🧠 Learning new skills...[/bold cyan]")
            discovery.learn_all_installed()

        # Refresh agent's skill list
        self.refresh_skills()

        console.print(f"[green]✅ EvolvixOS is now smarter. {len(self._available_skills)} skills total.[/green]")

    def run(self, user_request: str):
        """Main agent loop. Runs until the task is complete or max steps reached."""
        console.print(Panel(
            f"[bold green]EvolvixOS Agent v0.3[/bold green]\n"
            f"Model: {self.llm_config['primary_model']}\n"
            f"Built-in skills: {sum(1 for s in self._available_skills.values() if s['source'] == 'builtin')}\n"
            f"GitHub skills: {sum(1 for s in self._available_skills.values() if s['source'] == 'github')}\n"
            f"Learned: {len(self._github_registry.get('learned', {}))}\n"
            f"Mode: 100% local, zero tokens",
            title="🧬 EvolvixOS",
            border_style="green"
        ))

        # Add user request to conversation
        self.conversation.append({"role": "user", "content": user_request})

        # Save to memory
        self.memory.add(
            content=user_request,
            memory_type="user_request",
        )

        for step in range(self.agent_config["max_steps"]):
            console.print(f"\n[bold yellow]--- Step {step + 1} ---[/bold yellow]")

            # Build messages with system prompt + conversation
            messages = [
                {"role": "system", "content": self.system_prompt},
                *self.conversation,
            ]

            # THINK
            console.print("[blue]🧠 Thinking...[/blue]")
            response = self._call_llm(messages)
            console.print(Markdown(response))

            # Check if agent wants to call a skill
            skill_call = self._parse_skill_call(response)

            if skill_call:
                # ACT
                result = self._execute_skill(skill_call["skill"], skill_call["args"])

                # OBSERVE
                console.print(f"[green]✅ Skill result:[/green]")
                console.print(result[:500] + "..." if len(result) > 500 else result)

                # Add to conversation for the agent to observe
                self.conversation.append({"role": "assistant", "content": response})
                self.conversation.append({
                    "role": "user",
                    "content": f"Skill '{skill_call['skill']}' returned:\n{result}\n\nContinue with the next step or provide your final answer."
                })

                # Self-reflection (optional)
                if self.agent_config.get("self_reflect", True):
                    reflect_msg = [
                        {"role": "system", "content": "You are reviewing your own work. Was the skill result good? Should you continue or adjust your approach? Be brief."},
                        {"role": "user", "content": f"Task: {user_request}\nLast action: {skill_call['skill']}\nResult: {result[:1000]}\n\nReflect briefly (1-2 sentences)."}
                    ]
                    reflection = self._call_llm(reflect_msg, model=self.llm_config.get("fast_model"))
                    console.print(f"[dim]💭 Reflection: {reflection}[/dim]")

            elif "COMPLETE" in response.upper() or "task is done" in response.lower():
                # Agent says it's done
                console.print("\n[bold green]✅ Task complete![/bold green]")

                # Save to memory
                self.memory.add(
                    content=f"Task: {user_request}\nResult: {response[:500]}",
                    memory_type="task_complete",
                )
                return response

            else:
                # No skill call and not complete — agent is thinking/reasoning
                self.conversation.append({"role": "assistant", "content": response})
                self.conversation.append({
                    "role": "user",
                    "content": "Continue. Use a skill if needed, or say COMPLETE if the task is done."
                })

        console.print("[yellow]⚠ Max steps reached. Stopping.[/yellow]")
        return "Task incomplete — max steps reached."

    def chat(self):
        """Interactive chat mode."""
        console.print(Panel(
            f"[bold green]EvolvixOS v0.3 Interactive Mode[/bold green]\n"
            f"Built-in skills: {sum(1 for s in self._available_skills.values() if s['source'] == 'builtin')}\n"
            f"GitHub skills: {sum(1 for s in self._available_skills.values() if s['source'] == 'github')}\n"
            f"Learned: {len(self._github_registry.get('learned', {}))}\n"
            f"Type your request. 'discover' = search GitHub for new skills. 'exit' to quit.\n"
            f"100% local • zero tokens • learns from all of GitHub",
            title="🧬 EvolvixOS",
            border_style="green"
        ))

        while True:
            try:
                user_input = console.input("\n[bold cyan]You:[/bold cyan] ")
                if user_input.lower().strip() in ["exit", "quit", "q"]:
                    console.print("[green]Goodbye. EvolvixOS shutting down.[/green]")
                    break
                if not user_input.strip():
                    continue

                # Special command: discover new GitHub skills
                if user_input.lower().strip() == "discover":
                    self.discover_github_skills()
                    continue

                # Special command: show skill catalog
                if user_input.lower().strip() == "catalog":
                    if "github_discovery" in self._available_skills:
                        from skills.github_discovery.skill import GitHubSkillDiscovery
                        discovery = GitHubSkillDiscovery(config=self.skills_config.get("github_discovery", {}))
                        discovery.get_skill_catalog()
                    continue

                # Special command: refresh skills
                if user_input.lower().strip() == "refresh":
                    self.refresh_skills()
                    continue

                self.conversation = []  # Fresh conversation
                self.run(user_input)
            except KeyboardInterrupt:
                console.print("\n[yellow]Interrupted. Type 'exit' to quit.[/yellow]")
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
                console.print(traceback.format_exc())
