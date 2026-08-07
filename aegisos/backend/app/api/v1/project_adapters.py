"""
Project Adapter API endpoints — MVP Feature #13

Provides endpoints for listing, registering, and querying project type adapters,
validating project configs, and retrieving quality gate commands.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from app.api.deps import get_current_active_user
from app.models.user import User
from app.services.project_adapter import (
    list_adapters, get_adapter, register_adapter,
    get_adapter_summary, validate_project_config,
    get_quality_gate_commands, ProjectTypeConfig,
)

router = APIRouter(prefix="/project-adapters", tags=["project-adapters"])


class AdapterResponse(BaseModel):
    """Response model for a project adapter."""
    type_id: str
    display_name: str
    description: str
    icon: str
    default_language: str
    supported_languages: list[str]
    task_types: list[str]
    quality_gates: list[str]
    security_checks: list[str]
    monitoring_metrics: list[str]
    file_structure: dict[str, str]


class AdapterListResponse(BaseModel):
    """List of all registered adapters."""
    adapters: list[AdapterResponse]
    total: int


class RegisterAdapterRequest(BaseModel):
    """Request to register a custom adapter."""
    type_id: str = Field(..., min_length=1, max_length=100)
    display_name: str = Field(..., min_length=1, max_length=200)
    description: str = Field("", max_length=1000)
    icon: str = Field("📦", max_length=10)
    default_language: str = Field("python")
    supported_languages: list[str] = Field(default_factory=lambda: ["python"])
    file_structure: dict[str, str] = Field(default_factory=dict)
    agent_overrides: dict[str, str] = Field(default_factory=dict)
    task_types: list[str] = Field(default_factory=lambda: ["code_review", "test_generation"])
    quality_gates: list[str] = Field(default_factory=lambda: ["lint", "test", "build"])
    ci_template: dict = Field(default_factory=dict)
    monitoring_metrics: list[str] = Field(default_factory=lambda: ["cpu", "memory"])
    security_checks: list[str] = Field(default_factory=lambda: ["dependency_scan"])


class ValidateConfigRequest(BaseModel):
    """Request to validate a project config."""
    project_type: str
    config: dict


class ValidateConfigResponse(BaseModel):
    """Validation result."""
    valid: bool
    warnings: list[str]
    adapter_type: str


class QualityGateResponse(BaseModel):
    """Quality gate commands for a project type."""
    project_type: str
    commands: dict[str, str]


@router.get("/", response_model=AdapterListResponse)
async def list_all_adapters(
    current_user: User = Depends(get_current_active_user),
):
    """List all registered project type adapters."""
    adapters = [get_adapter_summary(a) for a in list_adapters()]
    return AdapterListResponse(adapters=adapters, total=len(adapters))


@router.get("/{type_id}", response_model=AdapterResponse)
async def get_adapter_by_type(
    type_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """Get details for a specific project type adapter."""
    adapter = get_adapter(type_id)
    if adapter.type_id != type_id:
        raise HTTPException(status_code=404, detail=f"Adapter '{type_id}' not found")
    return get_adapter_summary(adapter)


@router.post("/", response_model=AdapterResponse, status_code=status.HTTP_201_CREATED)
async def register_custom_adapter(
    request: RegisterAdapterRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Register a custom project type adapter."""
    adapter = ProjectTypeConfig(**request.model_dump())
    register_adapter(adapter)
    return get_adapter_summary(adapter)


@router.post("/validate", response_model=ValidateConfigResponse)
async def validate_config(
    request: ValidateConfigRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Validate a project config against its adapter."""
    adapter = get_adapter(request.project_type)
    warnings = validate_project_config(request.project_type, request.config)
    return ValidateConfigResponse(
        valid=len(warnings) == 0,
        warnings=warnings,
        adapter_type=adapter.type_id,
    )


@router.get("/{type_id}/quality-gates", response_model=QualityGateResponse)
async def get_quality_gates(
    type_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """Get quality gate commands for a project type."""
    commands = get_quality_gate_commands(type_id)
    return QualityGateResponse(project_type=type_id, commands=commands)
