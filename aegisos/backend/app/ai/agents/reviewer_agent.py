"""
AI Reviewer Agent for EvolvixOS Phase 4.

Handles code review and PR review for the Verdis ecosystem across
Rust/Substrate, Python, and TypeScript stacks.
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
from app.ai.prompts.system_prompts import REVIEWER_SYSTEM_PROMPT

logger = get_logger(__name__)


class AIReviewerAgent(BaseAgent):
    """
    AI Reviewer Agent responsible for code reviews and PR reviews across
    the Verdis ecosystem (Rust/Substrate, Python, TypeScript).
    """

    name: str = "reviewer_agent"
    description: str = (
        "Senior Code Reviewer agent for code and PR reviews across the Verdis ecosystem."
    )
    handled_task_types: set[TaskType] = {
        TaskType.CODE_REVIEW,
        TaskType.PR_REVIEW,
    }

    @property
    def system_prompt(self) -> str:
        """Returns the system prompt for the AI Reviewer Agent."""
        return REVIEWER_SYSTEM_PROMPT

    def preprocess(self, task: AgentTask) -> str:
        """
        Transform task data into a formatted user prompt for LLM evaluation.
        """
        task_data = task.data or {}
        task_type_str = task.type.value if hasattr(task.type, "value") else str(task.type)

        prompt_parts = [
            f"Task Type: {task_type_str}",
            f"Title/Context: {task_data.get('title', task_data.get('name', 'Code/PR Review Task'))}",
        ]

        if "description" in task_data:
            prompt_parts.append(f"Description:\n{task_data['description']}")

        if "file_path" in task_data:
            prompt_parts.append(f"File Path: {task_data['file_path']}")

        if "language" in task_data:
            prompt_parts.append(f"Language: {task_data['language']}")

        # PR Review specific fields
        if task.type == TaskType.PR_REVIEW or task_type_str == "pr_review":
            prompt_parts.append("--- Pull Request Context ---")

            if "additions" in task_data or "deletions" in task_data:
                additions = task_data.get("additions", 0)
                deletions = task_data.get("deletions", 0)
                prompt_parts.append(f"Diff Changes: +{additions} / -{deletions}")

            if "diff_size" in task_data:
                prompt_parts.append(f"Diff Size: {task_data['diff_size']}")

            if "diff" in task_data:
                prompt_parts.append(f"DIFF:\n```diff\n{task_data['diff']}\n```")

            if "commit_messages" in task_data:
                commits = task_data['commit_messages']
                if isinstance(commits, list):
                    commits_str = "\n".join(f"- {c}" for c in commits)
                else:
                    commits_str = str(commits)
                prompt_parts.append(f"Commit Messages:\n{commits_str}")

            if "breaking_changes" in task_data:
                prompt_parts.append(f"Breaking Changes: {task_data['breaking_changes']}")

            if "migration_needs" in task_data:
                prompt_parts.append(f"Migration Needs: {task_data['migration_needs']}")

            if "rollback_plan" in task_data:
                prompt_parts.append(f"Rollback Plan: {task_data['rollback_plan']}")

        # Source code content
        if "code" in task_data:
            language = task_data.get("language", "")
            prompt_parts.append(f"Source Code ({language}):\n```{language}\n{task_data['code']}\n```")

        # Multi-file content
        if "files" in task_data:
            files = task_data["files"]
            if isinstance(files, dict):
                for filepath, content in files.items():
                    prompt_parts.append(f"File: {filepath}\n```\n{content}\n```")
            elif isinstance(files, list):
                prompt_parts.append(f"Files:\n{json.dumps(files, indent=2)}")

        other_data = {
            k: v for k, v in task_data.items()
            if k not in (
                "title", "name", "description", "code", "language", "files", "file_path",
                "diff", "diff_size", "additions", "deletions", "commit_messages", "breaking_changes",
                "migration_needs", "rollback_plan"
            )
        }
        if other_data:
            prompt_parts.append(f"Additional Parameters:\n{json.dumps(other_data, indent=2, default=str)}")

        prompt_parts.append(
            "\nPerform the code/PR review according to your system prompt instructions. "
            "Output your response strictly in valid JSON format matching the schema."
        )
        return "\n\n".join(prompt_parts)

    def postprocess(self, content: str, task: AgentTask) -> AgentResult:
        """
        Transform LLM response into an AgentResult, extracting:
        - score (float, overall)
        - findings (list of dicts with severity, file, line, title, description, suggestion)
        - verdict (GO/REQUEST_CHANGES/REJECT)
        - scores (dict per dimension)
        - approval (bool)
        """
        result = super().postprocess(content, task)

        structured = result.structured_data or {}

        if not structured and content:
            match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", content)
            if match:
                try:
                    structured = json.loads(match.group(1))
                except json.JSONDecodeError:
                    pass
            if not structured:
                start = content.find("{")
                end = content.rfind("}") + 1
                if start != -1 and end > start:
                    try:
                        structured = json.loads(content[start:end])
                    except json.JSONDecodeError:
                        pass

        if not isinstance(structured, dict):
            structured = {}

        # 1. Extract scores (dict per dimension)
        raw_scores = structured.get("scores", {})
        scores: dict[str, float] = {}
        if isinstance(raw_scores, dict):
            for k, v in raw_scores.items():
                try:
                    scores[str(k)] = float(v)
                except (ValueError, TypeError):
                    pass

        # 2. Extract overall score (float)
        score: Optional[float] = None
        raw_score = structured.get("score")
        if raw_score is None:
            raw_score = structured.get("overall_score")

        if raw_score is not None:
            try:
                score = float(raw_score)
            except (ValueError, TypeError):
                score = None

        if score is None and scores:
            score = round(sum(scores.values()) / len(scores), 2)

        # 3. Extract findings
        raw_findings = structured.get("findings", [])
        findings: list[dict[str, Any]] = []
        if isinstance(raw_findings, list):
            for item in raw_findings:
                if isinstance(item, dict):
                    line_val = item.get("line")
                    if line_val is not None:
                        try:
                            line_val = int(line_val)
                        except (ValueError, TypeError):
                            pass
                    findings.append({
                        "severity": str(item.get("severity", "Medium")),
                        "file": str(item.get("file", "")),
                        "line": line_val,
                        "title": str(item.get("title", "")),
                        "description": str(item.get("description", "")),
                        "suggestion": str(item.get("suggestion", "")),
                    })

        # 4. Extract verdict (GO/REQUEST_CHANGES/REJECT)
        raw_verdict = str(structured.get("verdict", "")).strip().upper()
        if raw_verdict in ("GO", "REQUEST_CHANGES", "REJECT"):
            verdict = raw_verdict
        elif "REQUEST_CHANGES" in raw_verdict or "REQUEST CHANGES" in raw_verdict:
            verdict = "REQUEST_CHANGES"
        elif "REJECT" in raw_verdict:
            verdict = "REJECT"
        elif "GO" in raw_verdict:
            verdict = "GO"
        else:
            verdict = "REQUEST_CHANGES" if findings else "GO"

        # 5. Extract approval (bool)
        raw_approval = structured.get("approval")
        if isinstance(raw_approval, bool):
            approval = raw_approval
        else:
            approval = (verdict == "GO")

        # 6. Extract recommendations
        raw_recs = structured.get("recommendations", [])
        recommendations = [str(r) for r in raw_recs] if isinstance(raw_recs, list) else []

        updated_structured = {
            "summary": structured.get("summary", ""),
            "scores": scores,
            "score": score,
            "verdict": verdict,
            "approval": approval,
            "findings": findings,
            "recommendations": recommendations,
        }
        for k, v in structured.items():
            if k not in updated_structured:
                updated_structured[k] = v

        result.structured_data = updated_structured
        result.score = score
        result.findings = findings
        result.recommendations = recommendations

        return result
