"""
Self-Healing CI/CD Pipeline Agent.

Monitors CI/CD failures, ingests error logs, diagnoses root causes,
generates patches, and verifies fixes — autonomously resolving
broken pipelines.
"""

import json
import logging
import re
from typing import Any

from app.ai.agents.base_agent import (
    BaseAgent, AgentResult, AgentStatus, AgentTask, TaskType,
)
from app.ai.llm_client import LLMClient

logger = logging.getLogger("evolvixos")


class AICIHealerAgent(BaseAgent):
    """AI agent that diagnoses and fixes CI/CD failures."""

    name: str = "ci_healer"
    description: str = "Diagnoses and auto-fixes CI/CD pipeline failures"

    def __init__(self, llm_client: LLMClient = None):
        super().__init__(llm_client=llm_client)
        self.llm = llm_client or LLMClient()

    @property
    def system_prompt(self) -> str:
        return """You are a CI/CD pipeline healer. Given error logs from a failed CI run, diagnose the root cause and suggest a fix.

Analyze the error logs and identify:
1. The type of failure (import error, syntax error, test failure, type error, config issue, other)
2. The root cause in one sentence
3. Which files need to be changed
4. A specific code fix or action to resolve it
5. Confidence level (0.0-1.0)

Output JSON:
{
  "failure_type": "import|syntax|test|type|config|other",
  "root_cause": "one sentence description",
  "affected_files": ["file1.py", "file2.py"],
  "suggested_fix": "specific fix description or code",
  "confidence": 0.85
}"""

    def can_handle(self, task_type: str) -> bool:
        return task_type in ("diagnose_ci", "fix_ci")

    def _quick_diagnose(self, logs: str) -> dict | None:
        """Fast pattern matching for common CI failures."""
        logs_lower = logs.lower()

        # Missing import
        import_match = re.search(r"ModuleNotFoundError: No module named ['\"]([^'\"]+)['\"]", logs)
        if import_match:
            module = import_match.group(1)
            return {
                "failure_type": "import",
                "root_cause": f"Missing module '{module}'",
                "affected_files": [],
                "suggested_fix": f"pip install {module} or add to requirements.txt",
                "confidence": 0.9,
            }

        # Import error (Python)
        imp_match = re.search(r"ImportError: cannot import name ['\"]([^'\"]+)['\"] from ['\"]([^'\"]+)['\"]", logs)
        if imp_match:
            name, module = imp_match.group(1), imp_match.group(2)
            return {
                "failure_type": "import",
                "root_cause": f"Cannot import '{name}' from '{module}'",
                "affected_files": [module.replace(".", "/") + ".py"],
                "suggested_fix": f"Add or fix the '{name}' definition in {module}",
                "confidence": 0.85,
            }

        # Syntax error
        syntax_match = re.search(r"SyntaxError: (.+?) \( (.+?), line (\d+)", logs)
        if syntax_match:
            return {
                "failure_type": "syntax",
                "root_cause": syntax_match.group(1),
                "affected_files": [syntax_match.group(2)],
                "suggested_fix": f"Fix syntax error on line {syntax_match.group(3)}",
                "confidence": 0.9,
            }

        # TypeScript type error
        type_match = re.search(r"error TS\d+: (.+)", logs)
        if type_match:
            return {
                "failure_type": "type",
                "root_cause": type_match.group(1),
                "affected_files": [],
                "suggested_fix": "Fix TypeScript type error",
                "confidence": 0.8,
            }

        # Test assertion failure
        assert_match = re.search(r"AssertionError: (.+)", logs)
        if assert_match:
            return {
                "failure_type": "test",
                "root_cause": assert_match.group(1)[:200],
                "affected_files": [],
                "suggested_fix": "Fix the failing test assertion or the code it tests",
                "confidence": 0.75,
            }

        # Command not found
        cmd_match = re.search(r"command not found: (\S+)", logs_lower)
        if cmd_match:
            return {
                "failure_type": "config",
                "root_cause": f"Command '{cmd_match.group(1)}' not found",
                "affected_files": [],
                "suggested_fix": f"Install {cmd_match.group(1)} or add to PATH",
                "confidence": 0.85,
            }

        return None

    def _parse_diagnosis(self, text: str) -> dict:
        """Parse LLM diagnosis response into dict."""
        try:
            if "```json" in text:
                json_str = text.split("```json")[1].split("```")[0]
                return json.loads(json_str)
            elif "```" in text:
                json_str = text.split("```")[1].split("```")[0]
                return json.loads(json_str)
            return json.loads(text)
        except (json.JSONDecodeError, IndexError):
            return {
                "failure_type": "other",
                "root_cause": "Unable to determine root cause from logs",
                "affected_files": [],
                "suggested_fix": "Manual investigation required",
                "confidence": 0.3,
            }

    async def diagnose(self, error_logs: str, repo_context: str = "") -> dict:
        """Diagnose a CI/CD failure from error logs."""
        quick = self._quick_diagnose(error_logs)
        if quick and quick["confidence"] >= 0.8:
            return quick

        prompt = f"""Diagnose this CI/CD failure:

Error logs:
```
{error_logs[:4000]}
```

{f"Repository context: {repo_context}" if repo_context else ""}

Provide the diagnosis as JSON."""

        response = await self.llm.chat(
            system=self.system_prompt,
            user_message=prompt,
            temperature=0.1,
        )
        return self._parse_diagnosis(response)

    async def generate_fix(self, diagnosis: dict, file_contents: dict = None) -> dict:
        """Generate a code fix based on the diagnosis."""
        file_contents = file_contents or {}
        affected = diagnosis.get("affected_files", [])

        file_ctx = ""
        for fname in affected:
            if fname in file_contents:
                file_ctx += f"\n--- {fname} ---\n{file_contents[fname]}\n"

        prompt = f"""Fix this CI/CD failure:

Diagnosis:
- Type: {diagnosis.get("failure_type")}
- Root cause: {diagnosis.get("root_cause")}
- Suggested fix: {diagnosis.get("suggested_fix")}

Current file contents:
{file_ctx}

Generate corrected file contents. Output JSON:
```json
{{
  "patched_files": {{ "filename.py": "full corrected content" }},
  "fix_summary": "what was changed"
}}
```"""

        response = await self.llm.chat(
            system="You are a code fixer. Generate corrected file contents. Output valid JSON only.",
            user_message=prompt,
            temperature=0.1,
        )

        try:
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
                return json.loads(json_str)
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0]
                return json.loads(json_str)
            return json.loads(response)
        except (json.JSONDecodeError, IndexError):
            return {
                "patched_files": {},
                "fix_summary": f"Manual fix needed: {diagnosis.get('suggested_fix', 'unknown')}",
            }

    async def execute(self, task: AgentTask) -> AgentResult:
        """Execute CI healing task."""
        task_input = task.input_data if hasattr(task, 'input_data') else task.get("input_data", {})
        logs = task_input.get("error_logs", "")
        context = task_input.get("repo_context", "")
        should_fix = task_input.get("generate_fix", False)
        file_contents = task_input.get("file_contents", {})

        diagnosis = await self.diagnose(logs, context)
        result = {"diagnosis": diagnosis}

        if should_fix:
            fix = await self.generate_fix(diagnosis, file_contents)
            result["fix"] = fix

        return AgentResult(
            agent_name=self.name,
            status=AgentStatus.COMPLETED,
            content=json.dumps(result),
            structured_data=result,
        )

    async def run(self, task_input: dict) -> dict:
        """Convenience method to run without AgentTask wrapper."""
        logs = task_input.get("error_logs", "")
        context = task_input.get("repo_context", "")
        should_fix = task_input.get("generate_fix", False)
        file_contents = task_input.get("file_contents", {})

        diagnosis = await self.diagnose(logs, context)
        result = {"diagnosis": diagnosis}

        if should_fix:
            fix = await self.generate_fix(diagnosis, file_contents)
            result["fix"] = fix

        return result
