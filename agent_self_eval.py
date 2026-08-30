"""
EvolvixOS Agent Self-Evaluation Module v1.0
Adapted from ECC Agent Self-Evaluation — MIT licensed (affaan-m/ECC)

5-axis rubric for evaluating agent task completion:
  1. Accuracy — Are facts/claims/outputs correct?
  2. Completeness — Did it cover everything requested?
  3. Clarity — Is the explanation understandable and well-structured?
  4. Actionability — Can the user act immediately?
  5. Conciseness — Minimum words/tokens needed?

Scoring: 1-5 per axis. Every score below 5 MUST cite specific evidence.
Integrates with instinct_system.py — low scores generate improvement instincts.
"""

import json
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone


@dataclass
class EvalAxis:
    name: str
    score: int  # 1-5
    evidence: str
    improvement: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "score": self.score,
            "evidence": self.evidence,
            "improvement": self.improvement,
        }


@dataclass
class TaskEvaluation:
    task_description: str
    axes: List[EvalAxis] = field(default_factory=list)
    overall_score: float = 0.0
    summary: str = ""
    timestamp: str = ""
    instinct_generated: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_description": self.task_description,
            "axes": [a.to_dict() for a in self.axes],
            "overall_score": self.overall_score,
            "summary": self.summary,
            "timestamp": self.timestamp,
            "instinct_generated": self.instinct_generated,
        }

    def to_scorecard(self) -> str:
        """Render a human-readable scorecard."""
        lines = [
            f"Self-Evaluation Scorecard ({self.timestamp})",
            f"Task: {self.task_description}",
            "",
            f"{'Axis':<20} {'Score':<8} {'Evidence'}",
            f"{'─'*20} {'─'*8} {'─'*40}",
        ]
        for axis in self.axes:
            score_bar = "★" * axis.score + "☆" * (5 - axis.score)
            lines.append(f"{axis.name:<20} {score_bar:<8} {axis.evidence}")
            if axis.improvement:
                lines.append(f"{'':>30} → {axis.improvement}")
        lines.append("")
        lines.append(f"Overall: {self.overall_score:.1f}/5.0")
        if self.summary:
            lines.append(f"Summary: {self.summary}")
        return "\n".join(lines)


# ─────────────────────────────────────────────
# Evaluation Axes
# ─────────────────────────────────────────────

AXIS_QUESTIONS = {
    "accuracy": "Are the facts, claims, and outputs correct?",
    "completeness": "Did it cover everything the user asked for?",
    "clarity": "Is the explanation understandable and well-structured?",
    "actionability": "Can the user act on the output immediately?",
    "conciseness": "Did it use the minimum words/tokens needed?",
}

AXIS_CATCHES = {
    "accuracy": "Hallucinations, wrong API names, incorrect syntax, false statements",
    "completeness": "Missed edge cases, unhandled error paths, forgotten requirements, skipped subtasks",
    "clarity": "Confusing explanations, jargon without definition, missing context, rambling",
    "actionability": "Vague suggestions, missing steps, 'you should X' without showing how, no verification path",
    "conciseness": "Redundancy, over-explanation, repeating the user's question verbatim, filler content",
}


def evaluate_task(
    task_description: str,
    task_output: str,
    tool_results: Optional[List[Dict]] = None,
    user_feedback: Optional[str] = None,
    project_id: str = "global",
    project_name: str = "",
) -> TaskEvaluation:
    """
    Evaluate a completed task on 5 axes.

    Args:
        task_description: What was asked
        task_output: What the agent produced
        tool_results: Verification data (test results, exit codes, etc.)
        user_feedback: Any corrections from the user
        project_id: For instinct creation
        project_name: For instinct creation

    Returns:
        TaskEvaluation with scores and evidence
    """
    evaluation = TaskEvaluation(
        task_description=task_description,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

    # Heuristic checks for each axis
    output_lower = task_output.lower()

    # 1. Accuracy — check for hedging words, uncertainty markers
    hedging = sum(1 for w in ["i think", "maybe", "possibly", "i believe", "likely", "might"]
                  if w in output_lower)
    has_verification = bool(tool_results and any(r.get("success") for r in tool_results))
    accuracy_score = 5 if has_verification and hedging == 0 else (4 if hedging <= 1 else 3)
    if hedging > 2:
        accuracy_score = 2
    accuracy_evidence = "Verified with tool results" if has_verification else f"{hedging} hedging markers found"
    accuracy_improvement = None
    if accuracy_score < 5:
        accuracy_improvement = "Verify claims with tool calls before stating them as facts"

    evaluation.axes.append(EvalAxis(
        "accuracy", accuracy_score, accuracy_evidence, accuracy_improvement
    ))

    # 2. Completeness — check if output addresses the task description keywords
    task_words = set(task_description.lower().split())
    output_words = set(output_lower.split())
    coverage = len(task_words & output_words) / max(len(task_words), 1)
    if coverage > 0.7:
        completeness_score = 5
    elif coverage > 0.5:
        completeness_score = 4
    elif coverage > 0.3:
        completeness_score = 3
    else:
        completeness_score = 2

    missing = task_words - output_words
    completeness_evidence = f"{coverage:.0%} of task keywords addressed"
    completeness_improvement = None
    if completeness_score < 5 and missing:
        completeness_improvement = f"Missing aspects: {', '.join(list(missing)[:5])}"

    evaluation.axes.append(EvalAxis(
        "completeness", completeness_score, completeness_evidence, completeness_improvement
    ))

    # 3. Clarity — check for structure (headers, lists, code blocks)
    has_structure = any(marker in task_output for marker in ["```", "##", "1.", "•", "- "])
    has_sections = task_output.count("\n\n") > 2
    clarity_score = 5 if has_structure and has_sections else (4 if has_structure or has_sections else 3)
    clarity_evidence = "Well-structured with sections and code blocks" if has_structure and has_sections else "Some structure present" if has_structure else "No clear structure"
    clarity_improvement = None if clarity_score >= 4 else "Add headers, code blocks, and clear sections"

    evaluation.axes.append(EvalAxis(
        "clarity", clarity_score, clarity_evidence, clarity_improvement
    ))

    # 4. Actionability — check for vague phrases
    vague = sum(1 for w in ["you should", "consider", "you might want to", "it would be good"]
                if w in output_lower)
    has_code = "```" in task_output or "def " in task_output or "$ " in task_output
    actionable_score = 5 if has_code and vague == 0 else (4 if vague <= 1 else 2)
    actionable_evidence = f"{'Includes' if has_code else 'No'} concrete code/commands, {vague} vague suggestions"
    actionable_improvement = None if actionable_score >= 4 else "Replace vague suggestions with concrete steps and code"

    evaluation.axes.append(EvalAxis(
        "actionability", actionable_score, actionable_evidence, actionable_improvement
    ))

    # 5. Conciseness — check output length
    output_len = len(task_output)
    if output_len < 200:
        conciseness_score = 5
    elif output_len < 1000:
        conciseness_score = 5 if "redundant" not in output_lower else 3
    elif output_len < 3000:
        conciseness_score = 4
    elif output_len < 5000:
        conciseness_score = 3
    else:
        conciseness_score = 2

    # Check for repetition
    sentences = task_output.split(". ")
    if len(sentences) > 1:
        unique_starts = len(set(s[:30] for s in sentences))
        if unique_starts / len(sentences) < 0.7:
            conciseness_score = max(2, conciseness_score - 1)

    conciseness_evidence = f"{output_len} chars, {'concise' if output_len < 1000 else 'verbose'}"
    conciseness_improvement = None if conciseness_score >= 4 else "Remove redundant explanations"

    evaluation.axes.append(EvalAxis(
        "conciseness", conciseness_score, conciseness_evidence, conciseness_improvement
    ))

    # Calculate overall score
    evaluation.overall_score = sum(a.score for a in evaluation.axes) / len(evaluation.axes)

    # Generate summary
    weakest = min(evaluation.axes, key=lambda a: a.score)
    strongest = max(evaluation.axes, key=lambda a: a.score)
    evaluation.summary = (
        f"Strongest: {strongest.name} ({strongest.score}/5). "
        f"Weakest: {weakest.name} ({weakest.score}/5). "
    )
    if user_feedback:
        evaluation.summary += f"User feedback received: {user_feedback[:100]}"

    # Generate instinct for weak areas
    if evaluation.overall_score < 4.0:
        try:
            from instinct_system import add_instinct
            for axis in evaluation.axes:
                if axis.score <= 3 and axis.improvement:
                    add_instinct(
                        trigger=f"when completing tasks similar to: {task_description[:100]}",
                        action=axis.improvement,
                        domain="self-improvement",
                        confidence=0.4,
                        evidence={"axis": axis.name, "score": axis.score, "task": task_description[:200]},
                        project_id=project_id,
                        project_name=project_name,
                    )
                    evaluation.instinct_generated = True
        except Exception:
            pass  # Don't fail evaluation if instinct system isn't available

    return evaluation


def quick_eval(task: str, output: str) -> str:
    """Quick one-line evaluation for inline use."""
    evaluation = evaluate_task(task, output)
    return f"[{evaluation.overall_score:.1f}/5.0] — {evaluation.summary}"
