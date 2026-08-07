"""
AI CTO Agent for EvolvixOS.

Handles strategic technology decisions, architecture reviews,
and strategic planning for the Verdis ecosystem.
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


class AICTOAgent(BaseAgent):
    """
    Permanent Chief Technology Officer for the Verdis ecosystem.

    Responsibilities:
    - Strategic technology decisions for Substrate/BABE/GRANDPA blockchain, EvolvixOS AI platform, and infrastructure.
    - Architecture review for scalability, security, maintainability, performance, developer experience.
    - GO/NO-GO verdicts with scores (1-10) per dimension.
    - Risk identification by severity (Critical, High, Medium, Low).
    - Recommendations for technologies, patterns, and practices aligned with the Verdis Ecosystem Constitution.
    """

    name: str = "cto_agent"
    description: str = (
        "Permanent Chief Technology Officer for the Verdis ecosystem, handling "
        "strategic technology decisions, architecture review, and strategic planning."
    )
    handled_task_types: set[TaskType] = {
        TaskType.ARCHITECTURE_REVIEW,
        TaskType.TECHNOLOGY_DECISION,
        TaskType.STRATEGIC_PLANNING,
    }

    @property
    def system_prompt(self) -> str:
        """Return system prompt for AI CTO Agent."""
        return """You are the permanent Chief Technology Officer (CTO) for the Verdis ecosystem.

Your mission is to make strategic technology decisions, evaluate architectural proposals, and drive long-term technical strategy across:
1. Verdis Blockchain Core: Built on Substrate with BABE block production and GRANDPA finality consensus.
2. EvolvixOS AI Platform: Distributed AI agent operating system and orchestration core.
3. Ecosystem Infrastructure: Decentralized storage, networking, telemetry, and developer toolchain.

All your decisions, reviews, and recommendations MUST adhere strictly to the Verdis Ecosystem Constitution principles:
- Absolute commitment to decentralization, security, and cryptographic verifiability.
- High throughput, bounded latency, and deterministic resource allocation.
- Sustainable architecture with zero hidden technical debt or unmonitored attack vectors.
- Superior developer experience without compromising safety or architectural integrity.

When evaluating tasks:
- **Architecture Review**: Evaluate scalability, security, maintainability, performance, and developer experience. Assign dimension scores (1-10), list findings categorised by severity (Critical, High, Medium, Low), render a clear GO or NO-GO verdict, and provide actionable recommendations.
- **Technology Decision**: Compare options against ecosystem requirements, risk profiles, maturity, and maintainability. Render a verdict with strategic justification.
- **Strategic Planning**: Formulate multi-phase technical roadmaps, risk mitigation strategies, and architectural governance guidelines.

Your output MUST be valid JSON (or wrapped in ```json ... ```) with the following structure:
{
  "summary": "Executive summary of the analysis or decision",
  "scores": {
    "scalability": 8.5,
    "security": 9.0,
    "maintainability": 8.0,
    "performance": 8.5,
    "developer_experience": 8.0
  },
  "overall_score": 8.4,
  "findings": [
    {
      "severity": "Critical | High | Medium | Low",
      "description": "Detailed description of the finding or risk"
    }
  ],
  "recommendations": [
    "Actionable recommendation 1",
    "Actionable recommendation 2"
  ],
  "verdict": "GO"
}

Note:
- "verdict" MUST be either "GO" or "NO-GO".
- "overall_score" MUST be a float between 1.0 and 10.0.
- "findings" MUST be a list of objects containing "severity" and "description".
- "recommendations" MUST be a list of strings.
"""

    def preprocess(self, task: AgentTask) -> str:
        """Transform task data into a user prompt for the LLM."""
        task_data = json.dumps(task.data, indent=2, default=str)
        return (
            f"Task Type: {task.type.value}\n"
            f"Task ID: {task.id}\n\n"
            f"Task Payload:\n{task_data}\n\n"
            "Please perform a CTO-level strategic evaluation based on the instructions above. "
            "Return valid JSON containing summary, scores, findings, recommendations, and verdict."
        )

    def postprocess(self, content: str, task: AgentTask) -> AgentResult:
        """
        Transform LLM response into an AgentResult.

        Extracts score, findings, recommendations, verdict, and structured data.
        """
        structured_data: dict[str, Any] = {}
        score: Optional[float] = None
        findings: list[dict[str, Any]] = []
        recommendations: list[str] = []
        verdict: str = "NO-GO"

        # Attempt JSON parsing
        try:
            structured_data = json.loads(content)
        except json.JSONDecodeError:
            json_match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", content)
            if json_match:
                try:
                    structured_data = json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    pass

            if not structured_data:
                start = content.find("{")
                end = content.rfind("}") + 1
                if start != -1 and end > start:
                    try:
                        structured_data = json.loads(content[start:end])
                    except json.JSONDecodeError:
                        pass

        if structured_data:
            # Score extraction
            raw_score = structured_data.get("overall_score")
            if raw_score is not None:
                try:
                    score = float(raw_score)
                except (ValueError, TypeError):
                    score = None
            elif isinstance(structured_data.get("scores"), dict):
                scores_dict = structured_data["scores"]
                valid_vals = []
                for v in scores_dict.values():
                    try:
                        valid_vals.append(float(v))
                    except (ValueError, TypeError):
                        pass
                if valid_vals:
                    score = round(sum(valid_vals) / len(valid_vals), 2)

            # Findings extraction
            raw_findings = structured_data.get("findings", [])
            if isinstance(raw_findings, list):
                for f in raw_findings:
                    if isinstance(f, dict):
                        findings.append({
                            "severity": str(f.get("severity", "Medium")).strip(),
                            "description": str(f.get("description", "")).strip(),
                        })
                    elif isinstance(f, str):
                        findings.append({
                            "severity": "Medium",
                            "description": f.strip(),
                        })

            # Recommendations extraction
            raw_recs = structured_data.get("recommendations", [])
            if isinstance(raw_recs, list):
                recommendations = [str(r).strip() for r in raw_recs if str(r).strip()]

            # Verdict extraction
            raw_verdict = str(structured_data.get("verdict", "")).upper()
            if "GO" in raw_verdict and "NO-GO" not in raw_verdict:
                verdict = "GO"
            elif "NO-GO" in raw_verdict:
                verdict = "NO-GO"
            else:
                verdict = raw_verdict if raw_verdict in ("GO", "NO-GO") else "NO-GO"

            structured_data["verdict"] = verdict

        else:
            # Fallback parsing
            structured_data = {"summary": content, "verdict": "NO-GO"}

            verdict_match = re.search(r"verdict[\"'\s:]+([A-Z\-]+)", content, re.IGNORECASE)
            if verdict_match:
                v_str = verdict_match.group(1).upper()
                if "GO" in v_str and "NO-GO" not in v_str:
                    verdict = "GO"
                else:
                    verdict = "NO-GO"
            structured_data["verdict"] = verdict

            score_match = re.search(r"overall_score[\"'\s:]+([0-9]+(?:\.[0-9]+)?)", content, re.IGNORECASE)
            if score_match:
                try:
                    score = float(score_match.group(1))
                except ValueError:
                    score = None

        return AgentResult(
            task_id=task.id,
            agent_name=self.name,
            status=AgentStatus.COMPLETED,
            content=content,
            structured_data=structured_data,
            recommendations=recommendations,
            score=score,
            findings=findings,
        )
