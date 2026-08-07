"""
AI QA Agent for EvolvixOS.

Handles test generation, quality gates evaluation, and coverage analysis
for the Verdis ecosystem across Rust/Substrate, Python/FastAPI, and TypeScript stacks.
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

logger = get_logger(__name__)


QA_SYSTEM_PROMPT = """You are the Quality Assurance (QA) Lead for the Verdis ecosystem.
Your primary responsibility is driving engineering excellence, continuous testing, software quality, and release readiness across all codebases in Verdis (Rust/Substrate, Python/FastAPI, and TypeScript/Node/React).

Your core responsibilities:
- Test Generation: Generate comprehensive unit tests, integration tests, end-to-end tests, property-based tests, and edge case scenario tests tailored to the target programming language and framework.
- Quality Gates Definition & Verification: Evaluate and enforce quality gates including build success, test pass rates, target code coverage (> 80%), zero critical/high security findings, linter checks (clippy/ruff/eslint), and formatting adherence (cargo fmt/black/prettier).
- Coverage Analysis & Gap Identification: Analyze test coverage reports, pinpoint uncovered logic branches, edge cases, error conditions, and recommend specific targeted test cases to eliminate coverage gaps.

Ecosystem Stack Standard Commands & Tooling:
- Rust / Substrate: `cargo test`, `cargo clippy`, `cargo fmt --check`, `cargo build --release`
- Python / FastAPI: `pytest`, `ruff`, `mypy`, `black`
- TypeScript / Web: `jest`, `eslint`, `tsc`

Output Structure Requirement:
You MUST format your final response as a valid JSON object strictly structured as follows:
{
  "summary": "High-level summary of the QA review / test generation / coverage analysis.",
  "test_cases": [
    {
      "name": "test_name_or_function",
      "description": "Explanation of what this test verifies, including edge cases tested",
      "test_code": "// Optional actual test implementation code string"
    }
  ],
  "quality_gates": [
    {
      "name": "Build Check",
      "status": "pass",
      "details": "cargo build --release succeeded without errors"
    },
    {
      "name": "Code Coverage (>80%)",
      "status": "pass",
      "details": "Current coverage is 85%"
    },
    {
      "name": "Security Check",
      "status": "pass",
      "details": "0 critical/high findings"
    },
    {
      "name": "Linter Check",
      "status": "pass",
      "details": "cargo clippy / ruff passed clean"
    },
    {
      "name": "Formatting Check",
      "status": "pass",
      "details": "cargo fmt / black compliant"
    }
  ],
  "coverage_gaps": [
    "Uncovered error path in user authentication fallback",
    "Missing edge case tests for integer overflow in token transfers"
  ],
  "recommendations": [
    "Add property-based tests using proptest / hypothesis",
    "Increase integration test coverage for RPC endpoints"
  ]
}
Ensure the JSON output is clean, valid, and contains these fields.
"""


class AIQAAgent(BaseAgent):
    """
    AI QA Agent responsible for test generation, quality gate evaluation,
    and coverage analysis across the Verdis ecosystem.
    """

    name: str = "qa_agent"
    description: str = "Quality Assurance Lead agent for test generation, quality gates, and coverage analysis."
    handled_task_types: set[TaskType] = {
        TaskType.TEST_GENERATION,
        TaskType.QUALITY_GATE,
        TaskType.COVERAGE_ANALYSIS,
        TaskType.CODE_GENERATION,
        TaskType.IMPLEMENTATION,
    }

    @property
    def system_prompt(self) -> str:
        """Returns the system prompt for the AI QA Agent."""
        return QA_SYSTEM_PROMPT

    def preprocess(self, task: AgentTask) -> str:
        """
        Preprocess task data into a formatted prompt for the LLM.
        """
        task_data = task.data or {}
        task_type_str = task.type.value if hasattr(task.type, "value") else str(task.type)

        prompt_parts = [
            f"Task Type: {task_type_str}",
            f"Title/Context: {task_data.get('title', task_data.get('name', 'QA Task'))}",
        ]

        if "description" in task_data:
            prompt_parts.append(f"Description: {task_data['description']}")

        if "language" in task_data or "stack" in task_data:
            prompt_parts.append(f"Technology Stack: {task_data.get('language', task_data.get('stack'))}")

        if "code" in task_data:
            language = task_data.get("language", "")
            prompt_parts.append(f"Source Code:\n```{language}\n{task_data['code']}\n```")

        if "existing_tests" in task_data:
            prompt_parts.append(f"Existing Tests:\n{task_data['existing_tests']}")

        if "coverage_report" in task_data:
            prompt_parts.append(f"Coverage Report:\n{json.dumps(task_data['coverage_report'], indent=2) if isinstance(task_data['coverage_report'], dict) else task_data['coverage_report']}")

        other_data = {
            k: v for k, v in task_data.items()
            if k not in ("title", "name", "description", "language", "stack", "code", "existing_tests", "coverage_report")
        }
        if other_data:
            prompt_parts.append(f"Additional Context:\n{json.dumps(other_data, indent=2, default=str)}")

        prompt_parts.append("\nPerform the QA analysis/test generation and output your response in the required JSON format.")
        return "\n\n".join(prompt_parts)

    def postprocess(self, content: str, task: AgentTask) -> AgentResult:
        """
        Extract structured test cases, quality gates, coverage gaps, and recommendations from LLM output.
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

        raw_test_cases = structured.get("test_cases", [])
        test_cases = []
        if isinstance(raw_test_cases, list):
            for item in raw_test_cases:
                if isinstance(item, dict):
                    tc = {
                        "name": item.get("name", "unnamed_test"),
                        "description": item.get("description", ""),
                    }
                    if "test_code" in item:
                        tc["test_code"] = item["test_code"]
                    test_cases.append(tc)

        raw_quality_gates = structured.get("quality_gates", [])
        quality_gates = []
        if isinstance(raw_quality_gates, list):
            for item in raw_quality_gates:
                if isinstance(item, dict):
                    quality_gates.append({
                        "name": item.get("name", "unnamed_gate"),
                        "status": item.get("status", "fail"),
                        "details": item.get("details", ""),
                    })

        raw_coverage_gaps = structured.get("coverage_gaps", [])
        coverage_gaps = raw_coverage_gaps if isinstance(raw_coverage_gaps, list) else []

        raw_recommendations = structured.get("recommendations", [])
        recommendations = raw_recommendations if isinstance(raw_recommendations, list) else []

        updated_structured = {
            "summary": structured.get("summary", ""),
            "test_cases": test_cases,
            "quality_gates": quality_gates,
            "coverage_gaps": coverage_gaps,
            "recommendations": recommendations,
        }
        for k, v in structured.items():
            if k not in updated_structured:
                updated_structured[k] = v

        result.structured_data = updated_structured
        result.recommendations = recommendations

        return result
