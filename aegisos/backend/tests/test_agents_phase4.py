"""
Tests for Phase 4 AI Agents: Planner, Reviewer, Documentation.
"""

import json
import pytest
from unittest.mock import patch, MagicMock

from app.ai.agents.base_agent import (
    BaseAgent,
    AgentTask,
    AgentResult,
    AgentStatus,
    TaskType,
)


# ============================================================
# AI Planner Agent Tests
# ============================================================

class TestAIPlannerAgent:
    """Tests for the AI Planner Agent."""

    def test_planner_agent_attributes(self):
        """Test planner agent attributes."""
        from app.ai.agents.planner_agent import AIPlannerAgent
        agent = AIPlannerAgent()
        assert agent.name == "planner_agent"
        assert agent.description is not None
        assert TaskType.SPRINT_PLANNING in agent.handled_task_types
        assert TaskType.TASK_DECOMPOSITION in agent.handled_task_types
        assert TaskType.DEPENDENCY_ANALYSIS in agent.handled_task_types

    def test_planner_agent_system_prompt(self):
        """Test planner agent system prompt."""
        from app.ai.agents.planner_agent import AIPlannerAgent
        agent = AIPlannerAgent()
        assert "planner" in agent.system_prompt.lower() or "planning" in agent.system_prompt.lower()
        assert "MoSCoW" in agent.system_prompt or "moscow" in agent.system_prompt.lower()

    def test_planner_agent_preprocess(self):
        """Test planner agent preprocess formatting."""
        from app.ai.agents.planner_agent import AIPlannerAgent
        agent = AIPlannerAgent()

        task = AgentTask(
            type=TaskType.TASK_DECOMPOSITION,
            data={"feature": "AMM DEX", "description": "Build native AMM DEX pallet", "estimated_effort": "2 weeks"},
        )
        result = agent.preprocess(task)
        assert "AMM DEX" in result
        assert "2 weeks" in result

    def test_planner_agent_preprocess_sprint(self):
        """Test planner agent sprint planning preprocessing."""
        from app.ai.agents.planner_agent import AIPlannerAgent
        agent = AIPlannerAgent()

        task = AgentTask(
            type=TaskType.SPRINT_PLANNING,
            data={"sprint_number": 3, "capacity_hours": 80, "duration_days": 14, "backlog": [{"T1": "Task 1"}]},
        )
        result = agent.preprocess(task)
        assert "3" in result
        assert "80" in result

    def test_planner_agent_can_handle(self):
        """Test planner agent can_handle."""
        from app.ai.agents.planner_agent import AIPlannerAgent
        agent = AIPlannerAgent()
        assert agent.can_handle(TaskType.SPRINT_PLANNING) is True
        assert agent.can_handle(TaskType.TASK_DECOMPOSITION) is True
        assert agent.can_handle(TaskType.DEPENDENCY_ANALYSIS) is True
        assert agent.can_handle(TaskType.CODE_REVIEW) is False


# ============================================================
# AI Reviewer Agent Tests
# ============================================================

class TestAIReviewerAgent:
    """Tests for the AI Reviewer Agent."""

    def test_reviewer_agent_attributes(self):
        """Test reviewer agent attributes."""
        from app.ai.agents.reviewer_agent import AIReviewerAgent
        agent = AIReviewerAgent()
        assert agent.name == "reviewer_agent"
        assert TaskType.CODE_REVIEW in agent.handled_task_types
        assert TaskType.PR_REVIEW in agent.handled_task_types

    def test_reviewer_agent_system_prompt(self):
        """Test reviewer agent system prompt."""
        from app.ai.agents.reviewer_agent import AIReviewerAgent
        agent = AIReviewerAgent()
        prompt = agent.system_prompt
        assert "review" in prompt.lower()
        assert "Rust" in prompt or "rust" in prompt.lower()
        assert "severity" in prompt.lower()

    def test_reviewer_agent_preprocess_code(self):
        """Test reviewer agent code review preprocessing."""
        from app.ai.agents.reviewer_agent import AIReviewerAgent
        agent = AIReviewerAgent()

        task = AgentTask(
            type=TaskType.CODE_REVIEW,
            data={"file_path": "pallets/amm-dex/lib.rs", "language": "rust", "code": "fn swap() {}"},
        )
        result = agent.preprocess(task)
        assert "amm-dex" in result
        assert "rust" in result.lower()
        assert "swap" in result

    def test_reviewer_agent_preprocess_pr(self):
        """Test reviewer agent PR review preprocessing."""
        from app.ai.agents.reviewer_agent import AIReviewerAgent
        agent = AIReviewerAgent()

        task = AgentTask(
            type=TaskType.PR_REVIEW,
            data={"title": "Add AMM DEX pallet", "additions": 500, "deletions": 50, "diff": "+fn new_function() {}"},
        )
        result = agent.preprocess(task)
        assert "Add AMM" in result
        assert "diff" in result.lower()
        assert "new_function" in result

    def test_reviewer_agent_postprocess(self):
        """Test reviewer agent postprocess extracts findings and score."""
        from app.ai.agents.reviewer_agent import AIReviewerAgent
        agent = AIReviewerAgent()

        task = AgentTask(type=TaskType.CODE_REVIEW, data={})
        mock_response = json.dumps({
            "scores": {"correctness": 8, "security": 7},
            "overall_score": 7.5,
            "findings": [{"severity": "Medium", "title": "Missing input validation"}],
            "verdict": "GO",
        })

        result = agent.postprocess(mock_response, task)
        assert result.score == 7.5
        assert len(result.findings) == 1
        assert result.findings[0]["severity"] == "Medium"


# ============================================================
# AI Documentation Agent Tests
# ============================================================

class TestAIDocumentationAgent:
    """Tests for the AI Documentation Agent."""

    def test_doc_agent_attributes(self):
        """Test documentation agent attributes."""
        from app.ai.agents.documentation_agent import AIDocumentationAgent
        agent = AIDocumentationAgent()
        assert agent.name == "documentation_agent"
        assert TaskType.DOC_GENERATION in agent.handled_task_types
        assert TaskType.API_DOC_GENERATION in agent.handled_task_types

    def test_doc_agent_system_prompt(self):
        """Test documentation agent system prompt."""
        from app.ai.agents.documentation_agent import AIDocumentationAgent
        agent = AIDocumentationAgent()
        prompt = agent.system_prompt
        assert "documentation" in prompt.lower()
        assert "Markdown" in prompt
        assert "English" in prompt

    def test_doc_agent_preprocess(self):
        """Test documentation agent preprocessing."""
        from app.ai.agents.documentation_agent import AIDocumentationAgent
        agent = AIDocumentationAgent()

        task = AgentTask(
            type=TaskType.DOC_GENERATION,
            data={"doc_type": "readme", "title": "Verdis Blockchain", "source_code": "fn main() {}"},
        )
        result = agent.preprocess(task)
        assert "readme" in result
        assert "Verdis Blockchain" in result
        assert "main()" in result

    def test_doc_agent_preprocess_api(self):
        """Test API documentation preprocessing."""
        from app.ai.agents.documentation_agent import AIDocumentationAgent
        agent = AIDocumentationAgent()

        task = AgentTask(
            type=TaskType.API_DOC_GENERATION,
            data={"api_name": "EvolvixOS API", "framework": "fastapi", "endpoints": [{"method": "GET", "path": "/health"}]},
        )
        result = agent.preprocess(task)
        assert "EvolvixOS API" in result
        assert "fastapi" in result
        assert "GET" in result
        assert "/health" in result

    def test_doc_agent_temperature(self):
        """Test documentation agent temperature."""
        from app.ai.agents.documentation_agent import AIDocumentationAgent
        agent = AIDocumentationAgent()
        assert agent.get_temperature(TaskType.DOC_GENERATION) == 0.4

    def test_doc_agent_max_tokens(self):
        """Test documentation agent max tokens."""
        from app.ai.agents.documentation_agent import AIDocumentationAgent
        agent = AIDocumentationAgent()
        assert agent.get_max_tokens(TaskType.DOC_GENERATION) == 6000


# ============================================================
# Full Agent Registration Test
# ============================================================

class TestFullAgentRegistration:
    """Test that all 8 agents register with the workflow engine."""

    def test_all_8_agents_register(self):
        """Test that all 8 agents can be registered."""
        from app.ai.workflow_engine import AIWorkflowEngine
        from app.ai.agents import (
            AICTOAgent, AIArchitectAgent, AISecurityAgent, AIQAAgent,
            AIMemoryAgent, AIPlannerAgent, AIReviewerAgent, AIDocumentationAgent,
        )

        engine = AIWorkflowEngine()
        for agent_cls in [AICTOAgent, AIArchitectAgent, AISecurityAgent, AIQAAgent,
                          AIMemoryAgent, AIPlannerAgent, AIReviewerAgent, AIDocumentationAgent]:
            agent = agent_cls()
            engine.register_agent(agent)

        agents = engine.list_agents()
        assert len(agents) == 8

    def test_all_task_types_routed(self):
        """Test that every TaskType has a registered agent."""
        from app.ai.workflow_engine import AIWorkflowEngine
        from app.ai.agents import (
            AICTOAgent, AIArchitectAgent, AISecurityAgent, AIQAAgent,
            AIMemoryAgent, AIPlannerAgent, AIReviewerAgent, AIDocumentationAgent,
        )

        engine = AIWorkflowEngine()
        for agent_cls in [AICTOAgent, AIArchitectAgent, AISecurityAgent, AIQAAgent,
                          AIMemoryAgent, AIPlannerAgent, AIReviewerAgent, AIDocumentationAgent]:
            engine.register_agent(agent_cls())

        for task_type in TaskType:
            agent = engine.route_task(task_type)
            assert agent is not None, f"No agent for {task_type.value}"
