"""
EvolvixOS — Planner
Breaks complex tasks into steps. Uses local LLM, zero tokens.
"""

import json
import ollama
from rich.console import Console

console = Console()


class Planner:
    """Task decomposition and planning. Fully local."""

    def __init__(self, llm_config: dict):
        self.llm_config = llm_config
        self.ollama_client = ollama.Client(host=llm_config["host"])

    def plan(self, task: str, available_skills: list) -> list:
        """Break a task into a list of steps."""
        prompt = f"""You are a task planner for EvolvixOS, a local AI agent.

Break the following task into clear, actionable steps. Each step should use one of these available skills: {', '.join(available_skills)}.

Task: {task}

Respond with a JSON array of steps. Each step has:
- "step": step number
- "skill": which skill to use
- "action": what to do
- "description": brief explanation

Example:
[{{"step": 1, "skill": "research", "action": "search", "description": "Research the topic"}}, ...]

Respond with ONLY the JSON array, no other text."""

        response = self.ollama_client.chat(
            model=self.llm_config.get("fast_model", "llama3.2:3b"),
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.3, "num_ctx": 8192},
        )

        try:
            text = response["message"]["content"]
            # Extract JSON from response
            start = text.find("[")
            end = text.rfind("]") + 1
            if start >= 0 and end > start:
                return json.loads(text[start:end])
            return [{"step": 1, "skill": "unknown", "action": "do", "description": task}]
        except (json.JSONDecodeError, KeyError):
            console.print("[yellow]Planning failed, using single-step plan.[/yellow]")
            return [{"step": 1, "skill": "general", "action": "do", "description": task}]
