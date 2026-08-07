"""
Tests for the Test Generation Agent and CI Healer Agent.
"""

import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock

from app.ai.agents.test_generator_agent import AITestGeneratorAgent
from app.ai.agents.ci_healer_agent import AICIHealerAgent


class TestTestGeneratorAgent:
    """Test the automated test generation agent."""

    def test_agent_name(self):
        agent = AITestGeneratorAgent()
        assert agent.name == "test_generator"

    def test_system_prompt(self):
        agent = AITestGeneratorAgent()
        prompt = agent.system_prompt
        assert "test" in prompt.lower()
        assert "pytest" in prompt or "jest" in prompt

    def test_can_handle(self):
        agent = AITestGeneratorAgent()
        assert agent.can_handle("generate_tests")
        assert not agent.can_handle("review_code")

    def test_extract_code_python(self):
        agent = AITestGeneratorAgent()
        response = "Here's the test:\n```python\ndef test_add():\n    assert 1+1 == 2\n```"
        code = agent._extract_code(response)
        assert "def test_add" in code
        assert "assert" in code

    def test_extract_code_javascript(self):
        agent = AITestGeneratorAgent()
        response = '```javascript\ntest("adds", () => {\n  expect(1+1).toBe(2);\n});\n```'
        code = agent._extract_code(response)
        assert "expect" in code

    def test_extract_code_no_backticks(self):
        agent = AITestGeneratorAgent()
        response = "def test_basic():\n    assert True"
        code = agent._extract_code(response)
        assert "test_basic" in code

    @pytest.mark.asyncio
    async def test_generate_tests_mock(self):
        agent = AITestGeneratorAgent()
        agent.llm = AsyncMock()
        agent.llm.chat = AsyncMock(return_value="```python\ndef test_hello():\n    assert True\ndef test_world():\n    assert True\n```")

        result = await agent.generate_tests("def hello(): return 'world'", "python", "hello.py")
        assert result["test_file"] == "test_hello.py"
        assert result["test_count"] == 2
        assert "test_hello" in result["test_code"]

    @pytest.mark.asyncio
    async def test_generate_tests_javascript(self):
        agent = AITestGeneratorAgent()
        agent.llm = AsyncMock()
        agent.llm.chat = AsyncMock(return_value='```javascript\ntest("works", () => {});\ntest("also", () => {});\n```')

        result = await agent.generate_tests("function foo() {}", "javascript", "foo.ts")
        assert ".test." in result["test_file"]
        assert result["test_count"] == 2

    @pytest.mark.asyncio
    async def test_run_with_source_code(self):
        agent = AITestGeneratorAgent()
        agent.llm = AsyncMock()
        agent.llm.chat = AsyncMock(return_value="```python\ndef test_thing():\n    assert True\n```")

        result = await agent.run({"source_code": "def thing(): pass", "language": "python", "file_name": "thing.py"})
        assert result["test_file"] == "test_thing.py"
        assert result["test_count"] == 1

    @pytest.mark.asyncio
    async def test_run_no_code_no_path(self):
        agent = AITestGeneratorAgent()
        agent.llm = AsyncMock()
        agent.llm.chat = AsyncMock(return_value="```python\ndef test_x():\n    pass\n```")

        result = await agent.run({"source_code": "pass", "language": "python"})
        assert "test_code" in result


class TestCIHealerAgent:
    """Test the self-healing CI/CD agent."""

    def test_agent_name(self):
        agent = AICIHealerAgent()
        assert agent.name == "ci_healer"

    def test_system_prompt(self):
        agent = AICIHealerAgent()
        prompt = agent.system_prompt
        assert "JSON" in prompt
        assert "failure_type" in prompt

    def test_can_handle(self):
        agent = AICIHealerAgent()
        assert agent.can_handle("diagnose_ci")
        assert agent.can_handle("fix_ci")
        assert not agent.can_handle("generate_tests")

    def test_quick_diagnose_missing_module(self):
        agent = AICIHealerAgent()
        logs = "Traceback... ModuleNotFoundError: No module named 'fastapi'"
        result = agent._quick_diagnose(logs)
        assert result["failure_type"] == "import"
        assert "fastapi" in result["root_cause"]
        assert result["confidence"] >= 0.9

    def test_quick_diagnose_import_error(self):
        agent = AICIHealerAgent()
        logs = "ImportError: cannot import name 'Router' from 'fastapi'"
        result = agent._quick_diagnose(logs)
        assert result["failure_type"] == "import"
        assert "Router" in result["root_cause"]
        assert "fastapi" in result["root_cause"]

    def test_quick_diagnose_syntax_error(self):
        agent = AICIHealerAgent()
        logs = "SyntaxError: invalid syntax ( main.py , line 42)"
        result = agent._quick_diagnose(logs)
        assert result["failure_type"] == "syntax"
        assert result["confidence"] >= 0.9

    def test_quick_diagnose_test_failure(self):
        agent = AICIHealerAgent()
        logs = "AssertionError: expected 5 got 3"
        result = agent._quick_diagnose(logs)
        assert result["failure_type"] == "test"
        assert "5 got 3" in result["root_cause"]

    def test_quick_diagnose_command_not_found(self):
        agent = AICIHealerAgent()
        logs = "command not found: docker"
        result = agent._quick_diagnose(logs)
        assert result["failure_type"] == "config"
        assert "docker" in result["root_cause"]

    def test_quick_diagnose_typescript_error(self):
        agent = AICIHealerAgent()
        logs = "error TS2322: Type 'string' is not assignable to type 'number'"
        result = agent._quick_diagnose(logs)
        assert result["failure_type"] == "type"

    def test_quick_diagnose_unknown(self):
        agent = AICIHealerAgent()
        logs = "Some random error that doesn't match patterns"
        result = agent._quick_diagnose(logs)
        assert result is None

    def test_parse_diagnosis_valid_json(self):
        agent = AICIHealerAgent()
        text = '```json\n{"failure_type": "import", "root_cause": "missing", "affected_files": [], "suggested_fix": "install", "confidence": 0.9}\n```'
        result = agent._parse_diagnosis(text)
        assert result["failure_type"] == "import"
        assert result["confidence"] == 0.9

    def test_parse_diagnosis_invalid_json(self):
        agent = AICIHealerAgent()
        text = "This is not JSON at all"
        result = agent._parse_diagnosis(text)
        assert result["failure_type"] == "other"
        assert result["confidence"] < 0.5

    @pytest.mark.asyncio
    async def test_diagnose_quick_match(self):
        agent = AICIHealerAgent()
        logs = "ModuleNotFoundError: No module named 'requests'"
        result = await agent.diagnose(logs)
        assert result["failure_type"] == "import"
        assert "requests" in result["root_cause"]
        assert result["confidence"] >= 0.9

    @pytest.mark.asyncio
    async def test_diagnose_llm_fallback(self):
        agent = AICIHealerAgent()
        agent.llm = AsyncMock()
        agent.llm.chat = AsyncMock(return_value='```json\n{"failure_type": "other", "root_cause": "complex issue", "affected_files": ["main.py"], "suggested_fix": "refactor needed", "confidence": 0.6}\n```')

        logs = "Some complex error that doesn't match quick patterns"
        result = await agent.diagnose(logs)
        assert result["failure_type"] == "other"
        assert result["root_cause"] == "complex issue"
        assert agent.llm.chat.called

    @pytest.mark.asyncio
    async def test_generate_fix(self):
        agent = AICIHealerAgent()
        agent.llm = AsyncMock()
        agent.llm.chat = AsyncMock(return_value='```json\n{"patched_files": {"main.py": "fixed content"}, "fix_summary": "Added missing import"}\n```')

        diagnosis = {"failure_type": "import", "root_cause": "missing", "affected_files": ["main.py"]}
        result = await agent.generate_fix(diagnosis, {"main.py": "broken content"})
        assert "main.py" in result["patched_files"]
        assert result["fix_summary"] == "Added missing import"

    @pytest.mark.asyncio
    async def test_run_full_pipeline(self):
        agent = AICIHealerAgent()
        agent.llm = AsyncMock()
        agent.llm.chat = AsyncMock(return_value='```json\n{"patched_files": {"app.py": "fixed"}, "fix_summary": "Fixed"}\n```')

        result = await agent.run({
            "error_logs": "ModuleNotFoundError: No module named 'fastapi'",
            "generate_fix": True,
            "file_contents": {"app.py": "import fastapi"},
        })
        assert "diagnosis" in result
        assert result["diagnosis"]["failure_type"] == "import"
        assert "fix" in result
        assert result["fix"]["fix_summary"] == "Fixed"

    @pytest.mark.asyncio
    async def test_run_diagnosis_only(self):
        agent = AICIHealerAgent()
        result = await agent.run({
            "error_logs": "command not found: pytest",
            "generate_fix": False,
        })
        assert "diagnosis" in result
        assert "fix" not in result


class TestCodeOpsAPI:
    """Test code operations API endpoints."""

    def test_generate_tests_unauthorized(self, client):
        response = client.post("/api/v1/code-ops/generate-tests", json={"source_code": "pass"})
        assert response.status_code == 401

    def test_diagnose_ci_unauthorized(self, client):
        response = client.post("/api/v1/code-ops/diagnose-ci", json={"error_logs": "error"})
        assert response.status_code == 401

    def test_agent_info_unauthorized(self, client):
        response = client.get("/api/v1/code-ops/agents/test-generator")
        assert response.status_code == 401

    def test_test_generator_info_authorized(self, client, test_user):
        headers = test_user["headers"]
        response = client.get("/api/v1/code-ops/agents/test-generator", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["agent_type"] == "test_generator"
        assert "python" in data["supported_languages"]

    def test_ci_healer_info_authorized(self, client, test_user):
        headers = test_user["headers"]
        response = client.get("/api/v1/code-ops/agents/ci-healer", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["agent_type"] == "ci_healer"
        assert "quick_pattern_match" in data["features"]
