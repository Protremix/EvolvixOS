"""
Unit tests for EvolvixOS Phase 3 AI Agents: AISecurityAgent and AIQAAgent.
"""

import json
from unittest.mock import MagicMock

import pytest

from app.ai.agents.base_agent import AgentTask, TaskType
from app.ai.agents.security_agent import AISecurityAgent
from app.ai.agents.qa_agent import AIQAAgent


class TestAISecurityAgent:
    """Tests for AISecurityAgent."""

    def test_security_agent_attributes(self):
        agent = AISecurityAgent()
        assert agent.name == "security_agent"
        assert TaskType.SECURITY_REVIEW in agent.handled_task_types
        assert TaskType.THREAT_MODELING in agent.handled_task_types
        assert TaskType.VULNERABILITY_SCAN in agent.handled_task_types
        assert len(agent.handled_task_types) == 3  # SECURITY_REVIEW, THREAT_MODELING, VULNERABILITY_SCAN

    def test_security_agent_system_prompt(self):
        agent = AISecurityAgent()
        prompt = agent.system_prompt
        assert "Chief Security Officer" in prompt
        assert "STRIDE" in prompt
        assert "Critical" in prompt
        assert "reentrancy" in prompt.lower()
        assert "owasp" in prompt.lower()

    def test_security_agent_temperature(self):
        agent = AISecurityAgent()
        assert agent.get_temperature(TaskType.SECURITY_REVIEW) == 0.1
        assert agent.get_temperature(TaskType.THREAT_MODELING) == 0.1
        assert agent.get_temperature(TaskType.VULNERABILITY_SCAN) == 0.1

    def test_security_agent_preprocess(self):
        agent = AISecurityAgent()
        task = AgentTask(
            type=TaskType.SECURITY_REVIEW,
            data={
                "title": "Smart Contract Audit",
                "code": "pub fn transfer() {}",
                "language": "rust",
            },
        )
        prompt = agent.preprocess(task)
        assert "Task Type: security_review" in prompt
        assert "Smart Contract Audit" in prompt
        assert "pub fn transfer() {}" in prompt

    def test_security_agent_postprocess(self):
        agent = AISecurityAgent()
        task = AgentTask(type=TaskType.SECURITY_REVIEW, data={})
        sample_output = json.dumps({
            "summary": "Found 1 high severity vulnerability",
            "risk_score": 8.0,
            "threat_model": {
                "stride_analysis": {
                    "tampering": ["Data tampering via unverified state update"]
                }
            },
            "findings": [
                {
                    "severity": "High",
                    "title": "Unchecked State Update",
                    "description": "State can be overwritten without permission check",
                    "recommendation": "Add access control modifier"
                }
            ],
            "recommendations": ["Implement RBAC"]
        })

        result = agent.postprocess(sample_output, task)
        assert result.score == 8.0
        assert len(result.findings) == 1
        assert result.findings[0]["severity"] == "High"
        assert result.findings[0]["title"] == "Unchecked State Update"
        assert "tampering" in result.structured_data["threat_model"]["stride_analysis"]
        assert result.recommendations == ["Implement RBAC"]


class TestAIQAAgent:
    """Tests for AIQAAgent."""

    def test_qa_agent_attributes(self):
        agent = AIQAAgent()
        assert agent.name == "qa_agent"
        assert TaskType.TEST_GENERATION in agent.handled_task_types
        assert TaskType.QUALITY_GATE in agent.handled_task_types
        assert TaskType.COVERAGE_ANALYSIS in agent.handled_task_types
        assert len(agent.handled_task_types) == 5  # TEST_GENERATION, QUALITY_GATE, COVERAGE_ANALYSIS, CODE_GENERATION, IMPLEMENTATION

    def test_qa_agent_system_prompt(self):
        agent = AIQAAgent()
        prompt = agent.system_prompt
        assert "Quality Assurance" in prompt
        assert "cargo test" in prompt
        assert "pytest" in prompt
        assert "jest" in prompt
        assert "80%" in prompt

    def test_qa_agent_preprocess(self):
        agent = AIQAAgent()
        task = AgentTask(
            type=TaskType.TEST_GENERATION,
            data={
                "title": "Auth Service Unit Tests",
                "code": "def authenticate(user, password): pass",
                "language": "python",
            },
        )
        prompt = agent.preprocess(task)
        assert "Task Type: test_generation" in prompt
        assert "Auth Service Unit Tests" in prompt
        assert "def authenticate" in prompt

    def test_qa_agent_postprocess(self):
        agent = AIQAAgent()
        task = AgentTask(type=TaskType.QUALITY_GATE, data={})
        sample_output = json.dumps({
            "summary": "Quality gate assessment passed",
            "test_cases": [
                {
                    "name": "test_auth_success",
                    "description": "Validates successful auth flow",
                    "test_code": "def test_auth_success(): assert True"
                }
            ],
            "quality_gates": [
                {"name": "Build Check", "status": "pass", "details": "Clean build"},
                {"name": "Coverage Check", "status": "pass", "details": "85% coverage"}
            ],
            "coverage_gaps": ["Error handler branch not covered"],
            "recommendations": ["Add error handling tests"]
        })

        result = agent.postprocess(sample_output, task)
        assert len(result.structured_data["test_cases"]) == 1
        assert result.structured_data["test_cases"][0]["name"] == "test_auth_success"
        assert len(result.structured_data["quality_gates"]) == 2
        assert result.structured_data["quality_gates"][0]["status"] == "pass"
        assert result.structured_data["coverage_gaps"] == ["Error handler branch not covered"]
        assert result.recommendations == ["Add error handling tests"]
