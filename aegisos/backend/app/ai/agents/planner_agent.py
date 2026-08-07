"""
AI Planner Agent for EvolvixOS.

Handles sprint planning, task decomposition, dependency analysis,
and project management for the Verdis ecosystem and EvolvixOS platform.
"""

import json
import re
from typing import Any, Optional

from structlog import get_logger

from app.ai.agents.base_agent import (
    AgentResult,
    AgentStatus,
    AgentTask,
    BaseAgent,
    TaskType,
)
from app.ai.prompts.system_prompts import PLANNER_SYSTEM_PROMPT

logger = get_logger(__name__)


class AIPlannerAgent(BaseAgent):
    """
    Project Planner for the Verdis ecosystem and EvolvixOS platform.

    Responsibilities:
    - SPRINT_PLANNING: Plan 2-week sprint cycles with capacity-based task assignment.
    - TASK_DECOMPOSITION: Decompose large features into actionable tasks (max 4h each) with MoSCoW priorities.
    - DEPENDENCY_ANALYSIS: Map task dependencies, identify critical path, and spot blockers/risks.
    """

    name: str = "planner_agent"
    description: str = (
        "Project Planner for Verdis ecosystem and EvolvixOS platform, specializing in "
        "sprint planning, task decomposition, dependency analysis, and risk management."
    )
    handled_task_types: set[TaskType] = {
        TaskType.SPRINT_PLANNING,
        TaskType.TASK_DECOMPOSITION,
        TaskType.DEPENDENCY_ANALYSIS,
    }

    @property
    def system_prompt(self) -> str:
        """Return system prompt for AI Planner Agent."""
        return PLANNER_SYSTEM_PROMPT

    def preprocess(self, task: AgentTask) -> str:
        """Transform task data into a project planning prompt."""
        task_data = json.dumps(task.data, indent=2, default=str)
        return (
            f"Task Type: {task.type.value}\n"
            f"Task ID: {task.id}\n\n"
            f"Task Payload:\n{task_data}\n\n"
            "Please perform project planning based on the system instructions. "
            "Decompose features into tasks (max 4 hours each), analyze dependencies and critical path, "
            "plan sprints (2-week cycles), assign MoSCoW priorities, and identify risks/blockers. "
            "Return valid JSON with keys: summary, tasks, dependencies, critical_path, sprint_plan, risks, blockers."
        )

    def postprocess(self, content: str, task: AgentTask) -> AgentResult:
        """
        Transform LLM response into an AgentResult.

        Extracts:
        - tasks: list of dicts with id, title, description, estimate_hours, priority, dependencies
        - dependencies: list of pairs [task_id_1, task_id_2]
        - critical_path: list of task ids
        - sprint_plan: dict with sprint_number, tasks, capacity, duration_days
        - risks: list of risks
        - blockers: list of blockers
        """
        structured_data: dict[str, Any] = {}
        raw_json: Optional[dict[str, Any]] = None

        # Attempt JSON parsing
        try:
            raw_json = json.loads(content)
        except json.JSONDecodeError:
            json_match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", content)
            if json_match:
                try:
                    raw_json = json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    pass

            if not raw_json:
                start = content.find("{")
                end = content.rfind("}") + 1
                if start != -1 and end > start:
                    try:
                        raw_json = json.loads(content[start:end])
                    except json.JSONDecodeError:
                        pass

        if not isinstance(raw_json, dict):
            raw_json = {}

        # 1. Process tasks
        raw_tasks = raw_json.get("tasks", [])
        tasks: list[dict[str, Any]] = []
        if isinstance(raw_tasks, list):
            for idx, item in enumerate(raw_tasks):
                if isinstance(item, dict):
                    t_id = str(item.get("id") or item.get("task_id") or f"TASK-{idx + 1:03d}")
                    t_title = str(item.get("title") or item.get("name") or f"Task {idx + 1}")
                    t_desc = str(item.get("description") or "")

                    try:
                        t_est = float(item.get("estimate_hours", item.get("estimate", 4.0)))
                    except (ValueError, TypeError):
                        t_est = 4.0

                    raw_prio = str(item.get("priority", "Must")).capitalize()
                    if raw_prio in ("Must", "Should", "Could", "Won't"):
                        t_prio = raw_prio
                    elif "must" in raw_prio.lower():
                        t_prio = "Must"
                    elif "should" in raw_prio.lower():
                        t_prio = "Should"
                    elif "could" in raw_prio.lower():
                        t_prio = "Could"
                    elif "won" in raw_prio.lower():
                        t_prio = "Won't"
                    else:
                        t_prio = "Must"

                    t_deps = item.get("dependencies", [])
                    if not isinstance(t_deps, list):
                        t_deps = [str(t_deps)] if t_deps else []
                    else:
                        t_deps = [str(d) for d in t_deps]

                    t_status = str(item.get("status", "pending")).lower()
                    if t_status not in ("pending", "in_progress", "completed", "failed"):
                        t_status = "pending"

                    tasks.append({
                        "id": t_id,
                        "title": t_title,
                        "description": t_desc,
                        "estimate_hours": t_est,
                        "priority": t_prio,
                        "status": t_status,
                        "dependencies": t_deps,
                    })

        # 2. Process dependencies
        raw_deps = raw_json.get("dependencies", [])
        dependencies: list[list[str]] = []
        if isinstance(raw_deps, list):
            for dep in raw_deps:
                if isinstance(dep, (list, tuple)) and len(dep) >= 2:
                    dependencies.append([str(dep[0]), str(dep[1])])
                elif isinstance(dep, dict) and "from" in dep and "to" in dep:
                    dependencies.append([str(dep["from"]), str(dep["to"])])
                elif isinstance(dep, dict) and "source" in dep and "target" in dep:
                    dependencies.append([str(dep["source"]), str(dep["target"])])

        # If explicit dependency list is empty, derive from tasks' dependencies
        if not dependencies and tasks:
            for t in tasks:
                t_id = t["id"]
                for dep_id in t.get("dependencies", []):
                    dependencies.append([str(dep_id), str(t_id)])

        # 3. Process critical path
        raw_cp = raw_json.get("critical_path", [])
        critical_path: list[str] = []
        if isinstance(raw_cp, list):
            critical_path = [str(item) for item in raw_cp]

        # 4. Process sprint plan
        raw_sp = raw_json.get("sprint_plan", {})
        if isinstance(raw_sp, dict):
            sp_num = raw_sp.get("sprint_number", raw_sp.get("sprint", 1))
            try:
                sp_num = int(sp_num)
            except (ValueError, TypeError):
                sp_num = 1

            sp_tasks = raw_sp.get("tasks", [t["id"] for t in tasks])
            if not isinstance(sp_tasks, list):
                sp_tasks = []
            else:
                sp_tasks = [str(st) for st in sp_tasks]

            try:
                sp_cap = float(raw_sp.get("capacity", 80))
            except (ValueError, TypeError):
                sp_cap = 80.0

            try:
                sp_dur = int(raw_sp.get("duration_days", 14))
            except (ValueError, TypeError):
                sp_dur = 14

            sprint_plan = {
                "sprint_number": sp_num,
                "tasks": sp_tasks,
                "capacity": sp_cap,
                "duration_days": sp_dur,
            }
        else:
            sprint_plan = {
                "sprint_number": 1,
                "tasks": [t["id"] for t in tasks],
                "capacity": 80.0,
                "duration_days": 14,
            }

        # 5. Process risks
        raw_risks = raw_json.get("risks", [])
        risks: list[Any] = raw_risks if isinstance(raw_risks, list) else [str(raw_risks)]

        # 6. Process blockers
        raw_blockers = raw_json.get("blockers", [])
        blockers: list[Any] = raw_blockers if isinstance(raw_blockers, list) else [str(raw_blockers)]

        # Construct structured_data dict
        structured_data = {
            "summary": str(raw_json.get("summary", content)),
            "tasks": tasks,
            "dependencies": dependencies,
            "critical_path": critical_path,
            "sprint_plan": sprint_plan,
            "risks": risks,
            "blockers": blockers,
        }

        # Build findings and recommendations
        findings = []
        for r in risks:
            if isinstance(r, dict):
                findings.append(r)
            else:
                findings.append({"severity": "Medium", "description": str(r)})
        for b in blockers:
            if isinstance(b, dict):
                findings.append(b)
            else:
                findings.append({"severity": "High", "description": f"Blocker: {str(b)}"})

        recommendations = raw_json.get("recommendations", [])
        if not isinstance(recommendations, list):
            recommendations = []
        if not recommendations:
            recommendations = [f"Resolve blocker: {b}" for b in blockers if isinstance(b, str)]

        return AgentResult(
            task_id=task.id,
            agent_name=self.name,
            status=AgentStatus.COMPLETED,
            content=content,
            structured_data=structured_data,
            recommendations=recommendations,
            findings=findings,
        )
