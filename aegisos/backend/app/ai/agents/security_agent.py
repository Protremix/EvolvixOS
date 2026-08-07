"""
AI Security Agent for EvolvixOS.

Handles security review, threat modeling, and vulnerability scanning
for the Verdis ecosystem.
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


SECURITY_SYSTEM_PROMPT = """You are the Chief Security Officer (CSO) for the Verdis ecosystem.
Your primary responsibility is ensuring absolute security, resilience, and cryptographic integrity across all components of Verdis, including blockchain protocol code, smart contracts, Web3 bridges, consensus engines, backend API services, frontend Web apps, and cloud infrastructure.

When analyzing code, architecture, or system specifications, you perform thorough evaluations covering:
- Security Code Review: Input validation, authentication, authorization/access control, cryptography implementation, injection flaws (SQL, Command, NoSQL), Cross-Site Scripting (XSS), Cross-Site Request Forgery (CSRF), Server-Side Request Forgery (SSRF), dependency/supply chain risks, key management, secrets exposure.
- Threat Modeling: Using the STRIDE framework (Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege) to identify potential attack vectors, threat actors, and mitigation strategies.
- Vulnerability Scanning & Severity Classification:
  * Critical: Immediate risk of catastrophic compromise, severe financial loss, consensus halt, or full system takeover.
  * High: Serious security breach risk, unauthorized high-privileged access, key exposure, or significant data loss.
  * Medium: Moderate security impact, localized privilege escalation, partial access bypass, or conditional exploits.
  * Low: Minor security risk, best-practice violations, low-impact information disclosure.
  * Info: Informational security observations, hardening recommendations, defense-in-depth suggestions.
- Blockchain & Consensus Security: Reentrancy attacks, validator slashing risks, consensus manipulation, bridge exploit risks, oracle manipulation, front-running/MEV attacks, integer overflow/underflow, access control on state transitions, governance attacks.
- Web & API Security: OWASP Top 10 vulnerabilities, auth bypass, session management, broken object-level authorization (BOLA), rate limiting, CORS configuration, data leakage.

You MUST always format your final output as a valid JSON object matching the following structure:
{
  "summary": "High-level summary of the security review / threat model / vulnerability scan.",
  "risk_score": 7.5,
  "threat_model": {
    "stride_analysis": {
      "spoofing": ["..."],
      "tampering": ["..."],
      "repudiation": ["..."],
      "information_disclosure": ["..."],
      "denial_of_service": ["..."],
      "elevation_of_privilege": ["..."]
    },
    "attack_vectors": ["..."],
    "mitigations": ["..."]
  },
  "findings": [
    {
      "severity": "Critical",
      "title": "Short descriptive title of finding",
      "description": "Detailed explanation of vulnerability, root cause, and potential impact",
      "recommendation": "Concrete remediation guidance or fix code snippet"
    }
  ],
  "recommendations": [
    "General recommendation 1",
    "General recommendation 2"
  ]
}
Ensure the JSON response is valid and strictly adheres to this schema.
"""


class AISecurityAgent(BaseAgent):
    """
    AI Security Agent responsible for security reviews, threat modeling,
    and vulnerability scanning across the Verdis ecosystem.
    """

    name: str = "security_agent"
    description: str = "Chief Security Officer agent for security review, threat modeling, and vulnerability scanning."
    handled_task_types: set[TaskType] = {
        TaskType.SECURITY_REVIEW,
        TaskType.THREAT_MODELING,
        TaskType.VULNERABILITY_SCAN,
    }

    @property
    def system_prompt(self) -> str:
        """Returns the system prompt for the AI Security Agent."""
        return SECURITY_SYSTEM_PROMPT

    def preprocess(self, task: AgentTask) -> str:
        """
        Preprocess task data into a formatted prompt for the LLM.
        """
        task_data = task.data or {}
        task_type_str = task.type.value if hasattr(task.type, "value") else str(task.type)

        prompt_parts = [
            f"Task Type: {task_type_str}",
            f"Title/Context: {task_data.get('title', task_data.get('name', 'Security Analysis Task'))}",
        ]

        if "description" in task_data:
            prompt_parts.append(f"Description: {task_data['description']}")

        if "code" in task_data:
            language = task_data.get("language", "")
            prompt_parts.append(f"Code to Review ({language}):\n```{language}\n{task_data['code']}\n```")

        if "architecture" in task_data:
            prompt_parts.append(f"Architecture Description:\n{task_data['architecture']}")

        if "files" in task_data:
            prompt_parts.append(f"Files Content:\n{json.dumps(task_data['files'], indent=2)}")

        other_data = {
            k: v for k, v in task_data.items()
            if k not in ("title", "name", "description", "code", "language", "architecture", "files")
        }
        if other_data:
            prompt_parts.append(f"Additional Parameters:\n{json.dumps(other_data, indent=2, default=str)}")

        prompt_parts.append("\nPerform the security analysis and provide your structured findings in the required JSON format.")
        return "\n\n".join(prompt_parts)

    def postprocess(self, content: str, task: AgentTask) -> AgentResult:
        """
        Extract structured findings, risk score, and threat model from the LLM output.
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

        raw_findings = structured.get("findings", [])
        findings = []
        if isinstance(raw_findings, list):
            for item in raw_findings:
                if isinstance(item, dict):
                    findings.append({
                        "severity": item.get("severity", "Medium"),
                        "title": item.get("title", "Unspecified Finding"),
                        "description": item.get("description", ""),
                        "recommendation": item.get("recommendation", ""),
                    })

        raw_risk_score = structured.get("risk_score", 1.0)
        try:
            risk_score = float(raw_risk_score)
        except (ValueError, TypeError):
            risk_score = 1.0

        threat_model = structured.get("threat_model")
        if not isinstance(threat_model, dict):
            threat_model = {} if threat_model is not None else None

        recommendations = structured.get("recommendations", [])
        if not isinstance(recommendations, list):
            recommendations = []

        updated_structured = {
            "summary": structured.get("summary", ""),
            "risk_score": risk_score,
            "threat_model": threat_model if threat_model is not None else {},
            "findings": findings,
            "recommendations": recommendations,
        }
        for k, v in structured.items():
            if k not in updated_structured:
                updated_structured[k] = v

        result.structured_data = updated_structured
        result.findings = findings
        result.score = risk_score
        result.recommendations = recommendations

        return result
