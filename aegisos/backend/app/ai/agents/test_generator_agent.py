"""
Automated Test Generation Agent.

Analyzes source code files and generates high-coverage test suites.
Uses GPT-4o to understand function signatures, identify edge cases,
and produce pytest/jest test files.
"""

import logging
import os
from typing import Any

from app.ai.agents.base_agent import (
    BaseAgent, AgentResult, AgentStatus, AgentTask, TaskType,
)
from app.ai.llm_client import LLMClient

logger = logging.getLogger("evolvixos")


class AITestGeneratorAgent(BaseAgent):
    """AI agent that generates test suites from source code."""

    name: str = "test_generator"
    description: str = "Generates high-coverage test suites from source code analysis"

    def __init__(self, llm_client: LLMClient = None):
        super().__init__(llm_client=llm_client)
        self.llm = llm_client or LLMClient()

    @property
    def system_prompt(self) -> str:
        return """You are an expert test engineer. Given source code, generate comprehensive test suites.

Rules:
1. Generate pytest-compatible tests for Python, jest for JavaScript/TypeScript
2. Cover: happy path, edge cases, error handling, boundary conditions
3. Use descriptive test names that explain the scenario
4. Mock external dependencies (APIs, databases, file I/O)
5. Include type annotations where the source uses them
6. Aim for >90% code path coverage
7. Return ONLY valid test code, no explanations
8. Include necessary imports"""

    def can_handle(self, task_type: str) -> bool:
        return task_type in ("generate_tests",)

    def _extract_code(self, text: str) -> str:
        """Extract code block from LLM response."""
        if "```" in text:
            parts = text.split("```")
            if len(parts) >= 3:
                code = parts[1]
                if code.startswith(("python", "javascript", "typescript", "js", "ts", "")):
                    code = code.split("\n", 1)[1] if "\n" in code else code
                return code.strip()
        return text.strip()

    async def generate_tests(self, source_code: str, language: str = "python",
                             file_name: str = "") -> dict:
        """Generate a test suite for the given source code."""
        framework = "pytest" if language == "python" else "jest"

        prompt = f"""Generate a comprehensive {framework} test suite for this {language} code.

File: {file_name or "module.py"}

```{language}
{source_code}
```

Generate tests that cover all public functions/methods, edge cases, error handling, input validation, and empty/null inputs.

Return the complete test file content."""

        response = await self.llm.chat(
            system=self.system_prompt,
            user_message=prompt,
            temperature=0.2,
        )

        test_code = self._extract_code(response)

        if language == "python":
            test_count = test_code.count("def test_")
        else:
            test_count = test_code.count("it(") + test_code.count("test(")

        if file_name:
            if language == "python":
                base = file_name.replace(".py", "")
                test_file = f"test_{base}.py"
            else:
                base = file_name.replace(".ts", "").replace(".js", "").replace(".tsx", "").replace(".jsx", "")
                ext = "ts" if ".ts" in file_name else "js"
                test_file = f"{base}.test.{ext}"
        else:
            test_file = f"test_generated.{'py' if language == 'python' else 'test.js'}"

        return {
            "test_code": test_code,
            "test_file": test_file,
            "test_count": test_count,
            "coverage_notes": f"Generated {test_count} tests covering public API, edge cases, and error paths",
            "source_file": file_name,
        }

    async def generate_tests_for_file(self, file_path: str) -> dict:
        """Generate tests for a file on disk."""
        with open(file_path, "r") as f:
            source_code = f.read()
        language = "python" if file_path.endswith(".py") else "javascript"
        return await self.generate_tests(source_code, language, os.path.basename(file_path))

    async def execute(self, task: AgentTask) -> AgentResult:
        """Execute test generation task."""
        task_input = task.input_data if hasattr(task, 'input_data') else task.get("input_data", {})
        source_code = task_input.get("source_code", "")
        file_path = task_input.get("file_path", "")
        language = task_input.get("language", "python")
        file_name = task_input.get("file_name", "")

        if file_path and not source_code:
            result = await self.generate_tests_for_file(file_path)
        else:
            result = await self.generate_tests(source_code, language, file_name)

        return AgentResult(
            agent_name=self.name,
            status=AgentStatus.COMPLETED,
            content=result.get("test_code", ""),
            structured_data=result,
        )

    async def run(self, task_input: dict) -> dict:
        """Convenience method to run without AgentTask wrapper."""
        source_code = task_input.get("source_code", "")
        file_path = task_input.get("file_path", "")
        language = task_input.get("language", "python")
        file_name = task_input.get("file_name", "")

        if file_path and not source_code:
            return await self.generate_tests_for_file(file_path)
        return await self.generate_tests(source_code, language, file_name)
