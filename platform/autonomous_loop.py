"""
EvolvixOS Autonomous Task Loop
AutoGPT-style plan → delegate → verify → reflect cycle.
Works entirely locally via V10 ModelRouter. No external paid APIs.
"""
import json
import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class TaskStatus(Enum):
    PENDING = "pending"
    PLANNING = "planning"
    EXECUTING = "executing"
    VERIFYING = "verifying"
    REFLECTING = "reflecting"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class TaskStep:
    """A single step in an autonomous task plan."""
    id: int
    description: str
    agent: str = "auto"
    status: str = "pending"
    result: str = ""
    attempts: int = 0
    max_attempts: int = 3


@dataclass 
class AutonomousTask:
    """A full autonomous task with plan, steps, and reflection."""
    id: str
    goal: str
    context: str = ""
    status: str = "pending"
    steps: List[TaskStep] = field(default_factory=list)
    current_step: int = 0
    max_rounds: int = 10
    current_round: int = 0
    reflections: List[str] = field(default_factory=list)
    final_result: str = ""
    created_date: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_date: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    error: str = ""


class AutonomousLoop:
    """Autonomous plan→execute→verify→reflect loop using local models."""

    def __init__(self):
        self.tasks: Dict[str, AutonomousTask] = {}
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"auto-{self._counter:04d}"

    def _get_llm(self):
        """Get V10 ModelRouter for local LLM calls."""
        try:
            import sys
            sys.path.insert(0, "/opt/evolvixos")
            from v10_model_router import ModelRouter
            return ModelRouter()
        except Exception:
            # Fallback to direct Ollama
            return None

    def _ollama_generate(self, system_prompt: str, user_prompt: str, max_tokens: int = 2000) -> str:
        """Synchronous Ollama call (runs in thread)."""
        import urllib.request
        data = json.dumps({
            "model": "qwen2.5:7b",
            "system": system_prompt,
            "prompt": user_prompt,
            "stream": False,
            "options": {"num_predict": max_tokens}
        }).encode()
        req = urllib.request.Request("http://localhost:11434/api/generate", data=data)
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())
            return result.get("response", "")

    async def _llm_generate(self, system_prompt: str, user_prompt: str, max_tokens: int = 2000) -> str:
        """Generate text using Ollama via thread pool (non-blocking)."""
        try:
            return await asyncio.to_thread(self._ollama_generate, system_prompt, user_prompt, max_tokens)
        except Exception as e:
            return f"[ERROR: LLM unavailable: {e}]"

    def _parse_json_response(self, text: str) -> Any:
        """Extract JSON from LLM response (handles markdown code blocks)."""
        # Try direct parse
        try:
            return json.loads(text)
        except:
            pass
        # Try extracting from code block
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            if end > start:
                try:
                    return json.loads(text[start:end].strip())
                except:
                    pass
        if "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            if end > start:
                try:
                    return json.loads(text[start:end].strip())
                except:
                    pass
        # Try finding JSON-like structure
        for i, c in enumerate(text):
            if c == "{":
                for j in range(len(text), i, -1):
                    if text[j-1] == "}":
                        try:
                            return json.loads(text[i:j])
                        except:
                            continue
        return None

    async def start(self, goal: str, context: str = "", max_rounds: int = 10) -> dict:
        """Start a new autonomous task — returns immediately, runs in background."""
        task_id = self._next_id()
        task = AutonomousTask(
            id=task_id,
            goal=goal,
            context=context,
            max_rounds=max_rounds,
            status="planning"
        )
        self.tasks[task_id] = task
        # Run in background
        asyncio.create_task(self._run(task))
        # Return immediately with task info
        return self._task_to_dict(task)

    async def start_sync(self, goal: str, context: str = "", max_rounds: int = 10) -> dict:
        """Start a task and wait for completion (for testing)."""
        task_id = self._next_id()
        task = AutonomousTask(
            id=task_id,
            goal=goal,
            context=context,
            max_rounds=max_rounds,
            status="planning"
        )
        self.tasks[task_id] = task
        return await self._run(task)

    async def _run(self, task: AutonomousTask) -> dict:
        """Main autonomous loop: plan → execute → verify → reflect → repeat."""
        while task.current_round < task.max_rounds and task.status not in ("completed", "failed"):
            task.current_round += 1
            task.updated_date = datetime.utcnow().isoformat()

            # PHASE 1: PLAN (or replan after reflection)
            if not task.steps or all(s.status == "completed" for s in task.steps):
                plan = await self._plan(task)
                if plan:
                    task.steps = plan
                    task.current_step = 0

            # PHASE 2: EXECUTE next pending step
            pending = [s for s in task.steps if s.status == "pending"]
            if not pending:
                # All steps done — verify goal
                task.status = "verifying"
                result = await self._verify(task)
                if result.get("achieved"):
                    task.final_result = result.get("summary", "Goal achieved")
                    task.status = "completed"
                else:
                    # Reflect and replan
                    reflection = await self._reflect(task, result)
                    task.reflections.append(reflection)
                    if task.current_round >= task.max_rounds:
                        task.status = "failed"
                        task.error = "Max rounds reached"
                    else:
                        task.status = "reflecting"
                        # Replan in next iteration
                continue

            step = pending[0]
            step.status = "executing"
            step.attempts += 1
            task.status = "executing"
            task.updated_date = datetime.utcnow().isoformat()

            # Execute step
            result = await self._execute_step(task, step)
            step.result = result

            if result.startswith("[ERROR"):
                if step.attempts < step.max_attempts:
                    step.status = "pending"  # Retry
                else:
                    step.status = "failed"
            else:
                step.status = "completed"

            task.current_step = task.steps.index(step) + 1

        if task.status not in ("completed", "failed"):
            task.status = "failed"
            task.error = "Loop ended without completion"

        return self._task_to_dict(task)

    async def _plan(self, task: AutonomousTask) -> List[TaskStep]:
        """Generate a plan of steps to achieve the goal."""
        system = """You are an autonomous task planner. Decompose the given goal into concrete, actionable steps.
Return a JSON array of step objects with "description" and "agent" fields.
Agent can be: "reasoner", "coder", "researcher", "analyst", or "auto".
Keep plans focused and practical (3-7 steps). Return ONLY valid JSON."""

        user = f"""Goal: {task.goal}
Context: {task.context or "None"}
Round: {task.current_round}
Previous reflections: {json.dumps(task.reflections[-3:]) if task.reflections else "None"}

Create a step-by-step plan. Return JSON array:
[{{"description": "...", "agent": "reasoner"}}, ...]"""

        response = await self._llm_generate(system, user, max_tokens=1500)
        plan_data = self._parse_json_response(response)

        if not isinstance(plan_data, list):
            # Fallback: single step
            plan_data = [{"description": task.goal, "agent": "auto"}]

        steps = []
        for i, step_data in enumerate(plan_data[:10]):
            steps.append(TaskStep(
                id=i + 1,
                description=step_data.get("description", str(step_data)),
                agent=step_data.get("agent", "auto"),
            ))
        return steps

    async def _execute_step(self, task: AutonomousTask, step: TaskStep) -> str:
        """Execute a single step using the appropriate agent."""
        system = f"""You are an autonomous agent executing step {step.id} of a larger task.
Your role: {step.agent}
Task goal: {task.goal}
Context: {task.context or "None"}

Completed steps so far:
{self._format_completed_steps(task)}

Execute this step fully and return the result."""

        user = f"Step to execute: {step.description}\n\nProvide a detailed, actionable result."

        return await self._llm_generate(system, user, max_tokens=2000)

    async def _verify(self, task: AutonomousTask) -> dict:
        """Verify whether the goal has been achieved."""
        system = """You are a task verifier. Evaluate whether the goal has been achieved 
based on the completed steps. Return JSON:
{"achieved": true/false, "summary": "brief summary", "gaps": ["gap1", ...]}"""

        user = f"""Goal: {task.goal}
Context: {task.context or "None"}

Completed steps:
{self._format_completed_steps(task)}

Has the goal been achieved? Return JSON."""

        response = await self._llm_generate(system, user, max_tokens=500)
        result = self._parse_json_response(response)
        if not isinstance(result, dict):
            return {"achieved": False, "summary": "Could not verify", "gaps": ["Verification failed"]}
        return result

    async def _reflect(self, task: AutonomousTask, verify_result: dict) -> str:
        """Reflect on what went wrong and how to improve."""
        system = """You are a reflection agent. Analyze why the goal was not achieved 
and suggest specific adjustments. Be concise and actionable."""

        user = f"""Goal: {task.goal}
Gaps identified: {json.dumps(verify_result.get("gaps", []))}
Completed steps: {self._format_completed_steps(task)}

What should change in the next round?"""

        return await self._llm_generate(system, user, max_tokens=500)

    def _format_completed_steps(self, task: AutonomousTask) -> str:
        lines = []
        for s in task.steps:
            if s.status == "completed":
                lines.append(f"  Step {s.id}: {s.description} → {s.result[:200]}...")
        return "\n".join(lines) if lines else "  None yet"

    def _task_to_dict(self, task: AutonomousTask) -> dict:
        return {
            "id": task.id,
            "goal": task.goal,
            "context": task.context,
            "status": task.status,
            "current_round": task.current_round,
            "max_rounds": task.max_rounds,
            "steps": [
                {
                    "id": s.id,
                    "description": s.description,
                    "agent": s.agent,
                    "status": s.status,
                    "result": s.result[:500] if s.result else "",
                    "attempts": s.attempts,
                }
                for s in task.steps
            ],
            "reflections": task.reflections,
            "final_result": task.final_result,
            "error": task.error,
            "created_date": task.created_date,
            "updated_date": task.updated_date,
        }

    def get_task(self, task_id: str) -> Optional[dict]:
        task = self.tasks.get(task_id)
        return self._task_to_dict(task) if task else None

    def list_tasks(self) -> List[dict]:
        return [self._task_to_dict(t) for t in self.tasks.values()]


# Singleton
autonomous_loop = AutonomousLoop()
