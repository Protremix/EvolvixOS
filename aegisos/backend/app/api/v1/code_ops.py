"""
Code Operations API endpoints.

Provides REST access to test generation and CI/CD healing capabilities.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.deps import get_current_active_user
from app.models.user import User

router = APIRouter(prefix="/code-ops", tags=["code-operations"])


class GenerateTestsRequest(BaseModel):
    source_code: str = Field("", description="Source code to generate tests for")
    file_path: str = Field("", description="Path to source file (alternative to source_code)")
    language: str = Field("python", description="Language: python or javascript")
    file_name: str = Field("", description="File name for naming the test file")


class DiagnoseCIRequest(BaseModel):
    error_logs: str = Field(..., description="Error logs from failed CI run")
    repo_context: str = Field("", description="Repository context info")
    generate_fix: bool = Field(False, description="Also generate a fix")
    file_contents: dict = Field(default_factory=dict, description="Contents of affected files")


@router.post("/generate-tests")
async def generate_tests(
    request: GenerateTestsRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Generate a test suite for source code."""
    from app.ai.agents.test_generator_agent import AITestGeneratorAgent
    agent = AITestGeneratorAgent()

    if request.file_path and not request.source_code:
        result = await agent.generate_tests_for_file(request.file_path)
    else:
        result = await agent.generate_tests(
            request.source_code, request.language, request.file_name
        )
    return result


@router.post("/diagnose-ci")
async def diagnose_ci(
    request: DiagnoseCIRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Diagnose a CI/CD failure from error logs."""
    from app.ai.agents.ci_healer_agent import AICIHealerAgent
    agent = AICIHealerAgent()

    task_input = {
        "error_logs": request.error_logs,
        "repo_context": request.repo_context,
        "generate_fix": request.generate_fix,
        "file_contents": request.file_contents,
    }
    result = await agent.run(task_input)
    return result


@router.get("/agents/test-generator")
async def test_generator_info(
    current_user: User = Depends(get_current_active_user),
):
    """Get info about the test generator agent."""
    return {
        "agent_type": "test_generator",
        "description": "Generates high-coverage test suites from source code",
        "supported_languages": ["python", "javascript", "typescript"],
        "task_types": ["generate_tests"],
    }


@router.get("/agents/ci-healer")
async def ci_healer_info(
    current_user: User = Depends(get_current_active_user),
):
    """Get info about the CI healer agent."""
    return {
        "agent_type": "ci_healer",
        "description": "Diagnoses and auto-fixes CI/CD pipeline failures",
        "failure_types": ["import", "syntax", "test", "type", "config", "other"],
        "task_types": ["diagnose_ci", "fix_ci"],
        "features": ["quick_pattern_match", "llm_diagnosis", "auto_fix_generation"],
    }
