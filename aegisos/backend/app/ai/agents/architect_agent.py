"""
AI Architect Agent for EvolvixOS.

Handles system design, Architecture Decision Record (ADR) generation,
and technology selection for the Verdis ecosystem.
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


class AIArchitectAgent(BaseAgent):
    """
    Chief Blockchain Architect for Verdis.

    Responsibilities:
    - Designs system architecture for Substrate pallets, runtime, consensus, and networking.
    - Generates Architecture Decision Records (ADRs) with required 9 fields.
    - Selects technologies based on maturity, community support, security, performance, compatibility.
    - Outputs structured results containing design_summary, components, data_flow, adr, trade_offs, and risks.
    """

    name: str = "architect_agent"
    description: str = (
        "Chief Blockchain Architect for Verdis, specializing in Substrate pallets, "
        "runtime architecture, ADR generation, and technology selection."
    )
    handled_task_types: set[TaskType] = {
        TaskType.SYSTEM_DESIGN,
        TaskType.ADR_GENERATION,
        TaskType.TECHNOLOGY_SELECTION,
        TaskType.REFACTORING,
    }

    @property
    def system_prompt(self) -> str:
        """Return system prompt for AI Architect Agent."""
        return """You are the Chief Blockchain Architect for the Verdis ecosystem.

Your role is to design resilient, performant, and secure system architectures with a focus on:
1. Substrate Runtime & Pallet Design: Custom frame pallets, storage layouts, origin dispatchables, extrinsic weight calculations, and state transitions.
2. Consensus & Networking: BABE slot allocation, GRANDPA finality gadget, libp2p networking, state sync, and RPC interface design.
3. EvolvixOS System Integration: High-performance inter-process communication, secure sandbox boundaries, state serialization, and AI agent execution environments.
4. Technology Selection: Rigorous evaluation of libraries, frameworks, database systems, and protocols based on maturity, community support, security, performance, and compatibility.

When generating Architecture Decision Records (ADRs), you MUST provide a complete record containing ALL of the following 9 fields:
1. "decision": Clear statement of the architecture decision made.
2. "context": The problem statement, background, driver, and constraints.
3. "alternatives": Alternative approaches considered with brief descriptions.
4. "trade_offs": Technical and operational trade-offs evaluated.
5. "risks": Architectural risks identified along with potential impacts.
6. "consequences": Direct positive and negative impacts of adopting this decision.
7. "reasoning": In-depth architectural justification for why this decision was chosen over alternatives.
8. "approval": Stakeholder review status and approval governance process.
9. "future_review_criteria": Triggers, metrics, or timelines for re-evaluating this decision in the future.

Your response MUST be formatted as valid JSON (or enclosed in ```json ... ```) with this structure:
{
  "design_summary": "High-level architectural summary",
  "components": [
    {
      "name": "Component Name",
      "description": "Component role and responsibility",
      "interactions": ["Interaction 1", "Interaction 2"]
    }
  ],
  "data_flow": [
    "Step 1 of data flow",
    "Step 2 of data flow"
  ],
  "trade_offs": [
    "Trade-off description 1",
    "Trade-off description 2"
  ],
  "risks": [
    {
      "severity": "High",
      "description": "Description of risk"
    }
  ],
  "adr": {
    "decision": "Full decision statement",
    "context": "Context and background",
    "alternatives": ["Alternative 1", "Alternative 2"],
    "trade_offs": ["Trade-off 1", "Trade-off 2"],
    "risks": ["Risk 1", "Risk 2"],
    "consequences": ["Consequence 1", "Consequence 2"],
    "reasoning": "Reasoning and rationale",
    "approval": "Status / Approved by CTO & Architecture Board",
    "future_review_criteria": "Review upon next major version or performance bottleneck"
  }
}

Note:
- "components" MUST be a list of dicts or strings.
- "trade_offs" MUST be a list of strings.
- "risks" MUST be a list of dicts (or strings describing risks).
- "adr" MUST be present (especially for ADR_GENERATION tasks) and contain all 9 fields: decision, context, alternatives, trade_offs, risks, consequences, reasoning, approval, future_review_criteria.
"""

    def preprocess(self, task: AgentTask) -> str:
        """Transform task data into an architectural evaluation prompt."""
        task_data = json.dumps(task.data, indent=2, default=str)
        return (
            f"Task Type: {task.type.value}\n"
            f"Task ID: {task.id}\n\n"
            f"Task Payload:\n{task_data}\n\n"
            "Please perform a complete architectural analysis and design based on the system instructions. "
            "Return valid JSON containing design_summary, components, data_flow, trade_offs, risks, and adr."
        )

    def postprocess(self, content: str, task: AgentTask) -> AgentResult:
        """
        Transform LLM response into an AgentResult.

        Extracts adr (with all 9 fields), components, trade_offs, risks, and structured data.
        """
        structured_data: dict[str, Any] = {}
        adr: Optional[dict[str, Any]] = None
        components: list[Any] = []
        trade_offs: list[str] = []
        risks: list[Any] = []

        # Parse JSON from content
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
            # Extract components
            raw_comp = structured_data.get("components", [])
            if isinstance(raw_comp, list):
                components = raw_comp

            # Extract trade_offs
            raw_to = structured_data.get("trade_offs", [])
            if isinstance(raw_to, list):
                trade_offs = [str(item) for item in raw_to]

            # Extract risks
            raw_risks = structured_data.get("risks", [])
            if isinstance(raw_risks, list):
                risks = raw_risks

            # Extract ADR dict if present
            raw_adr = structured_data.get("adr")
            if isinstance(raw_adr, dict):
                adr_fields = [
                    "decision",
                    "context",
                    "alternatives",
                    "trade_offs",
                    "risks",
                    "consequences",
                    "reasoning",
                    "approval",
                    "future_review_criteria",
                ]
                adr = {}
                for field in adr_fields:
                    adr[field] = raw_adr.get(field, f"N/A ({field} not provided)")
                structured_data["adr"] = adr

        else:
            # Fallback structure
            structured_data = {
                "design_summary": content,
                "components": components,
                "trade_offs": trade_offs,
                "risks": risks,
                "adr": adr,
            }

        findings = risks if isinstance(risks, list) else []
        recommendations = structured_data.get("recommendations", [])
        if not isinstance(recommendations, list):
            recommendations = []

        return AgentResult(
            task_id=task.id,
            agent_name=self.name,
            status=AgentStatus.COMPLETED,
            content=content,
            structured_data=structured_data,
            recommendations=recommendations,
            findings=findings,
        )
