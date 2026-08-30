"""
EvolvixOS Agentic Engineering Module v1.0
Adapted from ECC Agentic Engineering + Agent Harness Construction — MIT licensed (affaan-m/ECC)

Structured workflow for agentic task execution:
  1. Plan → Test → Implement → Review → Verify → Remember → Improve
  2. Task decomposition (15-minute unit rule)
  3. Model routing by task complexity
  4. Context budgeting
  5. Tool/action space design patterns

Integrates with EvolvixOS V10 ModelRouter for model selection.
"""

import json
import time
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime, timezone
from enum import Enum


class TaskPhase(Enum):
    PLAN = "plan"
    TEST = "test"
    IMPLEMENT = "implement"
    REVIEW = "review"
    VERIFY = "verify"
    REMEMBER = "remember"
    IMPROVE = "improve"


class Complexity(Enum):
    LOW = "low"      # Haiku/simple — classification, boilerplate, narrow edits
    MEDIUM = "medium" # Standard — implementation, refactors
    HIGH = "high"    # Heavy — architecture, root-cause, multi-file


@dataclass
class TaskUnit:
    """A decomposed task unit (15-minute rule)."""
    id: str
    description: str
    phase: TaskPhase
    complexity: Complexity = Complexity.MEDIUM
    estimated_minutes: int = 15
    done_condition: str = ""
    dominant_risk: str = ""
    verification: str = ""
    status: str = "pending"  # pending | in_progress | done | failed
    result: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "phase": self.phase.value,
            "complexity": self.complexity.value,
            "estimated_minutes": self.estimated_minutes,
            "done_condition": self.done_condition,
            "dominant_risk": self.dominant_risk,
            "verification": self.verification,
            "status": self.status,
            "result": self.result,
        }


@dataclass
class AgenticWorkflow:
    """A complete agentic engineering workflow."""
    task: str
    units: List[TaskUnit] = field(default_factory=list)
    current_unit: int = 0
    started: str = ""
    completed: str = ""
    model_routing: Dict[str, str] = field(default_factory=dict)
    context_budget: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task": self.task,
            "units": [u.to_dict() for u in self.units],
            "current_unit": self.current_unit,
            "started": self.started,
            "completed": self.completed,
            "model_routing": self.model_routing,
            "context_budget": self.context_budget,
        }


# ─────────────────────────────────────────────
# Task Decomposition
# ─────────────────────────────────────────────

def decompose_task(task: str) -> AgenticWorkflow:
    """
    Decompose a task into 15-minute verifiable units.
    Each unit should:
      - Be independently verifiable
      - Have a single dominant risk
      - Have a clear done condition
    """
    workflow = AgenticWorkflow(
        task=task,
        started=datetime.now(timezone.utc).isoformat(),
    )

    # Standard plan→test→implement→review→verify→remember cycle
    phases = [
        (TaskPhase.PLAN, "Analyze requirements, identify risks, define approach", Complexity.HIGH, 10),
        (TaskPhase.TEST, "Define or update tests that validate the requirement", Complexity.MEDIUM, 10),
        (TaskPhase.IMPLEMENT, "Implement the solution to pass the tests", Complexity.MEDIUM, 15),
        (TaskPhase.REVIEW, "Review implementation from fresh context for edge cases", Complexity.HIGH, 10),
        (TaskPhase.VERIFY, "Run tests and verify all done conditions are met", Complexity.LOW, 5),
        (TaskPhase.REMEMBER, "Extract and save learned patterns as instincts", Complexity.LOW, 5),
    ]

    for i, (phase, desc, complexity, est_min) in enumerate(phases):
        unit = TaskUnit(
            id=f"unit-{i+1}",
            description=f"{phase.value.upper()}: {desc} — {task[:80]}",
            phase=phase,
            complexity=complexity,
            estimated_minutes=est_min,
            done_condition=_get_done_condition(phase),
            dominant_risk=_get_risk(phase, task),
            verification=_get_verification(phase),
        )
        workflow.units.append(unit)

    # Model routing by complexity
    workflow.model_routing = {
        Complexity.LOW.value: "qwen2.5:3b",        # Simple tasks → small model
        Complexity.MEDIUM.value: "qwen2.5:7b",     # Standard → medium model
        Complexity.HIGH.value: "qwen2.5:14b",       # Complex → large model
    }

    # Context budget
    workflow.context_budget = {
        "system_prompt": 2000,      # Keep minimal and invariant
        "task_context": 5000,       # Task-specific info
        "tool_results": 8000,       # Accumulated tool outputs
        "skills_loaded": 3000,      # On-demand skill content
        "total_budget": 18000,      # Total context window target
    }

    return workflow


def _get_done_condition(phase: TaskPhase) -> str:
    conditions = {
        TaskPhase.PLAN: "Plan documented with approach, risks, and done conditions",
        TaskPhase.TEST: "Tests defined that validate the requirement",
        TaskPhase.IMPLEMENT: "Code written and passes defined tests",
        TaskPhase.REVIEW: "Edge cases checked, security verified, no obvious gaps",
        TaskPhase.VERIFY: "All tests pass, done conditions met, no regressions",
        TaskPhase.REMEMBER: "Patterns extracted and saved as instincts",
    }
    return conditions.get(phase, "Done")


def _get_risk(phase: TaskPhase, task: str) -> str:
    risks = {
        TaskPhase.PLAN: "Misunderstanding requirements",
        TaskPhase.TEST: "Tests don't cover edge cases",
        TaskPhase.IMPLEMENT: "Breaking existing functionality",
        TaskPhase.REVIEW: "Missing security or error handling",
        TaskPhase.VERIFY: "False positive on tests",
        TaskPhase.REMEMBER: "Capturing noise instead of signal",
    }
    return risks.get(phase, "Unknown")


def _get_verification(phase: TaskPhase) -> str:
    verifications = {
        TaskPhase.PLAN: "User confirms plan matches intent",
        TaskPhase.TEST: "Tests exist and are runnable",
        TaskPhase.IMPLEMENT: "Tests pass, code runs without errors",
        TaskPhase.REVIEW: "No new security issues, edge cases handled",
        TaskPhase.VERIFY: "Exit code 0, all tests green",
        TaskPhase.REMEMBER: "Instincts saved with evidence",
    }
    return verifications.get(phase, "Verified")


# ─────────────────────────────────────────────
# Model Routing by Complexity
# ─────────────────────────────────────────────

def route_by_complexity(
    task_description: str,
    available_models: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Route model selection based on task complexity.
    Adapted from ECC's agentic engineering model routing.

    Args:
        task_description: What needs to be done
        available_models: Optional custom model mapping

    Returns:
        Routing decision with model, reason, and estimated cost
    """
    models = available_models or {
        Complexity.LOW.value: "qwen2.5:3b",
        Complexity.MEDIUM.value: "qwen2.5:7b",
        Complexity.HIGH.value: "qwen2.5:14b",
    }

    text = task_description.lower()

    # Complexity heuristics
    complexity = Complexity.MEDIUM

    # LOW: classification, boilerplate, narrow edits, simple lookups
    low_indicators = ["classify", "label", "format", "rename", "fix typo",
                      "update import", "change string", "add comment",
                      "list", "show", "get", "read", "check if"]
    if any(ind in text for ind in low_indicators):
        complexity = Complexity.LOW

    # HIGH: architecture, root-cause, multi-file, security, refactoring
    high_indicators = ["architect", "design", "refactor", "migrate", "root cause",
                       "security", "audit", "multiple files", "system-wide",
                       "performance", "optimize", "concurrent", "race condition"]
    if any(ind in text for ind in high_indicators):
        complexity = Complexity.HIGH

    # File count heuristic
    file_count = text.count("file") + text.count("files")
    if file_count > 3:
        complexity = Complexity.HIGH
    elif file_count > 1 and complexity == Complexity.LOW:
        complexity = Complexity.MEDIUM

    model = models.get(complexity.value, models.get(Complexity.MEDIUM.value, "qwen2.5:7b"))

    # Cost estimates (tokens/sec for local models)
    cost_estimates = {
        Complexity.LOW.value: {"tokens_per_sec": 800, "avg_tokens": 500},
        Complexity.MEDIUM.value: {"tokens_per_sec": 400, "avg_tokens": 1500},
        Complexity.HIGH.value: {"tokens_per_sec": 150, "avg_tokens": 3000},
    }
    est = cost_estimates.get(complexity.value, cost_estimates[Complexity.MEDIUM.value])

    return {
        "complexity": complexity.value,
        "model": model,
        "reason": f"Task contains {complexity.value} complexity indicators",
        "estimated_time_sec": est["avg_tokens"] / est["tokens_per_sec"],
        "estimated_tokens": est["avg_tokens"],
    }


# ─────────────────────────────────────────────
# Tool/Action Space Design (from Agent Harness Construction)
# ─────────────────────────────────────────────

def validate_tool_design(
    name: str,
    description: str,
    input_schema: Dict[str, Any],
    output_format: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Validate a tool design against agent harness best practices.
    Based on ECC Agent Harness Construction patterns.

    Checks:
      1. Stable, explicit tool names
      2. Schema-first, narrow inputs
      3. Deterministic output shapes
      4. No catch-all tools
      5. Observation format includes status, summary, next_actions
    """
    issues = []
    score = 100

    # 1. Tool name quality
    if len(name) < 3:
        issues.append("Tool name too short — use descriptive, stable names")
        score -= 10
    if " " in name or name != name.lower():
        issues.append("Tool name should be lowercase with no spaces")
        score -= 5
    if name in ("do", "run", "execute", "handle", "process"):
        issues.append("Tool name is too generic — be specific about what it does")
        score -= 15

    # 2. Input schema
    if not input_schema:
        issues.append("No input schema — tools need schema-first inputs")
        score -= 20
    if input_schema.get("type") == "string":
        issues.append("Catch-all string input — use structured schema with named fields")
        score -= 15

    # 3. Output format
    required_output_fields = ["status", "summary"]
    for field_name in required_output_fields:
        if field_name not in output_format:
            issues.append(f"Missing '{field_name}' in output format — every tool response needs it")
            score -= 10

    recommended_fields = ["next_actions", "artifacts"]
    for field_name in recommended_fields:
        if field_name not in output_format:
            issues.append(f"Recommended: add '{field_name}' to output for better agent recovery")
            score -= 5

    # 4. Error recovery contract
    if "error" not in output_format and "error_type" not in output_format:
        issues.append("No error type in output — agents need error classification for recovery")
        score -= 10

    return {
        "score": max(0, score),
        "issues": issues,
        "passed": score >= 70,
        "recommendations": [
            "Keep system prompt minimal and invariant",
            "Move large guidance into skills loaded on demand",
            "Prefer references to files over inlining long documents",
            "Include root cause hints in error outputs",
            "Include safe retry instructions in error outputs",
        ] if score < 100 else [],
    }


# ─────────────────────────────────────────────
# Context Budgeting
# ─────────────────────────────────────────────

def budget_context(
    system_prompt_tokens: int = 0,
    task_context_tokens: int = 0,
    tool_results_tokens: int = 0,
    skills_loaded_tokens: int = 0,
    max_budget: int = 18000,
) -> Dict[str, Any]:
    """
    Manage context budget to avoid overload.
    Based on ECC context budgeting patterns.

    Rules:
      1. System prompt: minimal and invariant (<2000)
      2. Task context: focused on current task (<5000)
      3. Tool results: compacted at phase boundaries (<8000)
      4. Skills: loaded on demand (<3000)
      5. Compact at phase boundaries, not arbitrary token thresholds
    """
    total = system_prompt_tokens + task_context_tokens + tool_results_tokens + skills_loaded_tokens
    utilization = total / max_budget

    recommendations = []

    if system_prompt_tokens > 2000:
        recommendations.append("System prompt exceeds 2000 tokens — move guidance to skills")

    if tool_results_tokens > 8000:
        recommendations.append("Tool results exceed 8000 tokens — compact at phase boundary")

    if skills_loaded_tokens > 3000:
        recommendations.append("Skills exceed 3000 tokens — load only what's needed for current phase")

    if utilization > 0.85:
        recommendations.append(f"Context at {utilization:.0%} — compact before next phase")
    elif utilization > 0.70:
        recommendations.append(f"Context at {utilization:.0%} — approaching limit, plan compaction")

    # Determine what to compact
    compact_target = None
    if tool_results_tokens > 4000:
        compact_target = "tool_results"
    elif skills_loaded_tokens > 2000:
        compact_target = "skills_loaded"

    return {
        "total_tokens": total,
        "budget": max_budget,
        "utilization": round(utilization, 3),
        "breakdown": {
            "system_prompt": system_prompt_tokens,
            "task_context": task_context_tokens,
            "tool_results": tool_results_tokens,
            "skills_loaded": skills_loaded_tokens,
        },
        "recommendations": recommendations,
        "compact_target": compact_target,
        "should_compact": utilization > 0.85,
    }


# ─────────────────────────────────────────────
# Eval-First Loop
# ─────────────────────────────────────────────

def eval_first_loop(
    task: str,
    run_baseline: Optional[Callable] = None,
    run_implementation: Optional[Callable] = None,
    run_eval: Optional[Callable] = None,
) -> Dict[str, Any]:
    """
    Execute the eval-first loop:
    1. Define capability eval and regression eval
    2. Run baseline and capture failure signatures
    3. Execute implementation
    4. Re-run evals and compare deltas

    If callbacks aren't provided, returns the plan for manual execution.
    """
    plan = {
        "task": task,
        "phases": [
            {"name": "define_evals", "action": "Define capability eval + regression eval"},
            {"name": "baseline", "action": "Run baseline evals, capture failures"},
            {"name": "implement", "action": "Execute the implementation"},
            {"name": "re_eval", "action": "Re-run evals, compare deltas"},
            {"name": "decision", "action": "If regressions: fix. If improvements: ship."},
        ],
    }

    results = {"plan": plan, "baseline": None, "implementation": None, "eval": None}

    if run_baseline:
        results["baseline"] = run_baseline()
    if run_implementation:
        results["implementation"] = run_implementation()
    if run_eval:
        results["eval"] = run_eval()
        # Compare deltas
        if results["baseline"] and results["eval"]:
            baseline_pass = results["baseline"].get("passed", 0)
            eval_pass = results["eval"].get("passed", 0)
            results["delta"] = eval_pass - baseline_pass
            results["improved"] = results["delta"] > 0
            results["regressed"] = results["delta"] < 0

    return results
