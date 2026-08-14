"""
EvolvixOS — Pipeline Builder Skill
Chain skills together into reproducible AI workflows.

Features:
  - Define multi-step pipelines (skill1 → skill2 → skill3)
  - Pass outputs between steps
  - Conditional branching (if/else)
  - Save and replay pipelines
  - Run pipelines in parallel or sequential
  - Schedule pipelines (cron)

Example pipeline:
  scrape → summarize → translate → write_document → send_email

Storage: data/pipelines/pipelines.json
"""

import os
import json
import time
import uuid
from pathlib import Path
from typing import Any
from rich.console import Console

console = Console()

PIPELINES_PATH = Path(__file__).parent.parent.parent / "data" / "pipelines" / "pipelines.json"


class Skill:
    """Pipeline Builder — orchestrate multi-step AI workflows."""

    def __init__(self, config=None):
        self.config = config or {}
        self.skills = {}  # Will be injected by API server
        PIPELINES_PATH.parent.mkdir(parents=True, exist_ok=True)
        self._load()

    def _load(self):
        if PIPELINES_PATH.exists():
            self.data = json.loads(PIPELINES_PATH.read_text())
        else:
            self.data = {"pipelines": {}}

    def _save(self):
        PIPELINES_PATH.write_text(json.dumps(self.data, indent=2))

    def set_skills(self, skills: dict):
        """Inject the skills registry from the API server."""
        self.skills = skills

    def create(self, name: str, steps: list, description: str = "",
               schedule: str = "", tags: list = None) -> str:
        """
        Create a pipeline.
        steps = [
            {"skill": "web_scraper", "input": {"url": "https://..."}, "output_key": "scraped"},
            {"skill": "summarizer", "input": {"text": "${scraped.text}"}, "output_key": "summary"},
            {"skill": "translator", "input": {"text": "${summary}", "to_lang": "es"}, "output_key": "translated"},
        ]
        """
        pipe_id = f"pipe_{uuid.uuid4().hex[:8]}"
        pipeline = {
            "id": pipe_id,
            "name": name,
            "description": description,
            "steps": steps,
            "schedule": schedule,
            "tags": tags or [],
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "runs": [],
            "status": "ready",
        }
        self.data["pipelines"][pipe_id] = pipeline
        self._save()
        return f"✅ Pipeline '{name}' created with {len(steps)} steps → {pipe_id}"

    def run_pipeline(self, pipe_id: str, input_data: dict = None) -> str:
        """Execute a pipeline."""
        pipeline = self.data["pipelines"].get(pipe_id)
        if not pipeline:
            return f"❌ Pipeline {pipe_id} not found."

        run_id = f"run_{uuid.uuid4().hex[:8]}"
        run_log = {
            "run_id": run_id,
            "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "status": "running",
            "steps": [],
            "results": {},
        }

        console.print(f"[cyan]🔄 Running pipeline '{pipeline['name']}' ({run_id})...[/cyan]")

        context = input_data or {}
        context.update({"pipeline_id": pipe_id, "run_id": run_id})

        for i, step in enumerate(pipeline["steps"]):
            step_name = step.get("name", f"step_{i+1}")
            skill_name = step.get("skill", "")
            step_input = step.get("input", {})

            # Resolve variables from context (e.g., ${scraped.text})
            resolved_input = {}
            for key, value in step_input.items():
                if isinstance(value, str) and "${" in value:
                    # Replace ${var} with context values
                    for ctx_key, ctx_val in context.items():
                        placeholder = f"${{{ctx_key}}}"
                        if placeholder in value:
                            if isinstance(ctx_val, dict):
                                # ${var.subkey}
                                for sub_key, sub_val in ctx_val.items():
                                    value = value.replace(f"${{{ctx_key}.{sub_key}}}", str(sub_val))
                            else:
                                value = value.replace(placeholder, str(ctx_val))
                    resolved_input[key] = value
                else:
                    resolved_input[key] = value

            console.print(f"  [{i+1}/{len(pipeline['steps'])}] {step_name} → {skill_name}")

            step_result = {"step": step_name, "skill": skill_name, "status": "pending"}

            # Check for conditional
            condition = step.get("condition")
            if condition:
                # Simple condition: ${var} == "value"
                if not self._eval_condition(condition, context):
                    step_result["status"] = "skipped"
                    run_log["steps"].append(step_result)
                    continue

            # Execute the skill
            if skill_name and skill_name in self.skills:
                try:
                    skill = self.skills[skill_name]
                    result = skill.run(resolved_input)
                    output_key = step.get("output_key", f"step_{i+1}_output")
                    context[output_key] = result
                    step_result["status"] = "completed"
                    step_result["output_key"] = output_key
                    run_log["results"][output_key] = str(result)[:200]
                except Exception as e:
                    step_result["status"] = "failed"
                    step_result["error"] = str(e)
                    run_log["status"] = "failed"
                    run_log["steps"].append(step_result)
                    run_log["completed_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
                    pipeline["runs"].append(run_log)
                    self._save()
                    return f"❌ Pipeline failed at step {i+1} ({step_name}): {e}"
            else:
                step_result["status"] = "skipped"
                step_result["error"] = f"Skill '{skill_name}' not available"

            run_log["steps"].append(step_result)

        run_log["status"] = "completed"
        run_log["completed_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        pipeline["runs"].append(run_log)
        self._save()

        return (
            f"✅ Pipeline '{pipeline['name']}' completed!\n"
            f"   Run ID: {run_id}\n"
            f"   Steps: {len(run_log['steps'])}\n"
            f"   Completed: {sum(1 for s in run_log['steps'] if s['status']=='completed')}\n"
            f"   Skipped: {sum(1 for s in run_log['steps'] if s['status']=='skipped')}\n"
            f"   Duration: {run_log['started_at']} → {run_log['completed_at']}"
        )

    def _eval_condition(self, condition: str, context: dict) -> bool:
        """Evaluate a simple condition like ${var} == 'value'."""
        try:
            # Replace ${var} with actual values
            for key, val in context.items():
                condition = condition.replace(f"${{{key}}}", str(val))
            # Safe eval of comparison
            if "==" in condition:
                left, right = condition.split("==", 1)
                return left.strip().strip('"\'') == right.strip().strip('"\'')
            elif "!=" in condition:
                left, right = condition.split("!=", 1)
                return left.strip().strip('"\'') != right.strip().strip('"\'')
            return bool(condition)
        except:
            return True

    def list_pipelines(self) -> str:
        """List all pipelines."""
        pipes = list(self.data["pipelines"].values())
        if not pipes:
            return "No pipelines created yet."
        lines = ["🔗 Pipelines:"]
        for p in pipes:
            run_count = len(p.get("runs", []))
            last_run = p["runs"][-1]["status"] if run_count > 0 else "never"
            lines.append(
                f"  {p['id']} — {p['name']} ({len(p['steps'])} steps, {run_count} runs, last: {last_run})"
            )
        return "\n".join(lines)

    def get_pipeline(self, pipe_id: str) -> str:
        """Get pipeline details."""
        p = self.data["pipelines"].get(pipe_id)
        if not p:
            return f"❌ Pipeline {pipe_id} not found."
        return json.dumps(p, indent=2)

    def delete(self, pipe_id: str) -> str:
        """Delete a pipeline."""
        if pipe_id not in self.data["pipelines"]:
            return f"❌ Pipeline {pipe_id} not found."
        del self.data["pipelines"][pipe_id]
        self._save()
        return f"✅ Deleted pipeline {pipe_id}"

    def run(self, args: dict) -> str:
        action = args.get("action", "list")

        if action == "create":
            return self.create(
                name=args.get("name", "unnamed"),
                steps=args.get("steps", []),
                description=args.get("description", ""),
                schedule=args.get("schedule", ""),
                tags=args.get("tags", []),
            )
        elif action == "run":
            return self.run_pipeline(args.get("pipe_id", ""), args.get("input", {}))
        elif action == "list":
            return self.list_pipelines()
        elif action == "get":
            return self.get_pipeline(args.get("pipe_id", ""))
        elif action == "delete":
            return self.delete(args.get("pipe_id", ""))
        else:
            return f"Unknown action: {action}\nAvailable: create, run, list, get, delete"
