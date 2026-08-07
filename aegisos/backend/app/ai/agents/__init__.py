"""EvolvixOS AI Agents — Phase 3 + Phase 4."""

from app.ai.agents.base_agent import (
    BaseAgent, AgentTask, AgentResult, AgentStatus, TaskType,
)

# Phase 3 agents
try:
    from app.ai.agents.cto_agent import AICTOAgent
except ImportError:
    AICTOAgent = None

try:
    from app.ai.agents.architect_agent import AIArchitectAgent
except ImportError:
    AIArchitectAgent = None

try:
    from app.ai.agents.security_agent import AISecurityAgent
except ImportError:
    AISecurityAgent = None

try:
    from app.ai.agents.qa_agent import AIQAAgent
except ImportError:
    AIQAAgent = None

try:
    from app.ai.agents.memory_agent import AIMemoryAgent
except ImportError:
    AIMemoryAgent = None

# Phase 4 agents
try:
    from app.ai.agents.planner_agent import AIPlannerAgent
except ImportError:
    AIPlannerAgent = None

try:
    from app.ai.agents.reviewer_agent import AIReviewerAgent
except ImportError:
    AIReviewerAgent = None

try:
    from app.ai.agents.documentation_agent import AIDocumentationAgent
except ImportError:
    AIDocumentationAgent = None

try:
    from app.ai.agents.test_generator_agent import AITestGeneratorAgent
except ImportError:
    AITestGeneratorAgent = None

try:
    from app.ai.agents.ci_healer_agent import AICIHealerAgent
except ImportError:
    AICIHealerAgent = None

__all__ = [
    "BaseAgent", "AgentTask", "AgentResult", "AgentStatus", "TaskType",
    "AICTOAgent", "AIArchitectAgent", "AISecurityAgent",
    "AIQAAgent", "AIMemoryAgent",
    "AIPlannerAgent", "AIReviewerAgent", "AIDocumentationAgent",
    "AITestGeneratorAgent", "AICIHealerAgent",
]
