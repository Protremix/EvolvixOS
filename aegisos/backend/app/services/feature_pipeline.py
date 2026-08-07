"""
Feature Delivery Pipeline — Post-MVP Phase 1

Implements the full 10-stage autonomous software delivery pipeline:
1. PRD Generation (CTO Agent)
2. Architecture Design (Architect Agent)
3. Task Decomposition (Planner Agent)
4. Implementation (Distributed Executor)
5. QA Testing (QA Agent + Test Generator)
6. Security Review (Security Agent)
7. Performance Review (CTO Agent)
8. Documentation (Documentation Agent)
9. Code Review (Reviewer Agent)
10. Release (CTO Agent — final approval)

Each stage runs sequentially, passing context from previous stages.
Stages can fail and trigger retry loops.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
from app.core.logging import get_logger

logger = get_logger("service.feature_pipeline")


class PipelineStage(str, Enum):
    """10-stage feature delivery pipeline."""
    PRD = "prd_generation"
    ARCHITECTURE = "architecture_design"
    DECOMPOSITION = "task_decomposition"
    IMPLEMENTATION = "implementation"
    QA_TESTING = "qa_testing"
    SECURITY_REVIEW = "security_review"
    PERFORMANCE_REVIEW = "performance_review"
    DOCUMENTATION = "documentation"
    CODE_REVIEW = "code_review"
    RELEASE = "release"


class StageStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"


class StageResult(BaseModel):
    """Result of a single pipeline stage."""
    stage: str
    status: StageStatus = StageStatus.PENDING
    agent: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_ms: int = 0
    output: dict = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    retry_count: int = 0


class FeatureRequest(BaseModel):
    """Input to the feature delivery pipeline."""
    title: str = Field(..., description="Feature title")
    description: str = Field(..., description="Feature description")
    project_type: str = Field("generic", description="Project adapter type")
    priority: str = Field("medium", description="low, medium, high, critical")
    constraints: list[str] = Field(default_factory=list, description="Technical constraints")
    acceptance_criteria: list[str] = Field(default_factory=list, description="Acceptance criteria")


class FeaturePipelineRun(BaseModel):
    """A complete pipeline execution."""
    id: str
    feature: FeatureRequest
    stages: list[StageResult] = Field(default_factory=list)
    status: str = "pending"
    current_stage: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    completed_at: Optional[str] = None
    total_duration_ms: int = 0
    summary: str = ""


# Stage definitions: which agent, what task type, what context to pass
STAGE_DEFS = [
    {
        "stage": PipelineStage.PRD,
        "agent": "cto_agent",
        "task_type": "strategic_planning",
        "name": "PRD Generation",
        "description": "Generate product requirements document from feature request",
        "max_retries": 1,
    },
    {
        "stage": PipelineStage.ARCHITECTURE,
        "agent": "architect_agent",
        "task_type": "system_design",
        "name": "Architecture Design",
        "description": "Design system architecture and technology stack",
        "max_retries": 1,
    },
    {
        "stage": PipelineStage.DECOMPOSITION,
        "agent": "planner_agent",
        "task_type": "task_decomposition",
        "name": "Task Decomposition",
        "description": "Break down architecture into implementable tasks",
        "max_retries": 1,
    },
    {
        "stage": PipelineStage.IMPLEMENTATION,
        "agent": "executor",
        "task_type": "code_generation",
        "name": "Implementation",
        "description": "Execute implementation tasks (distributed executor)",
        "max_retries": 2,
    },
    {
        "stage": PipelineStage.QA_TESTING,
        "agent": "qa_agent",
        "task_type": "test_generation",
        "name": "QA Testing",
        "description": "Generate and run tests against implementation",
        "max_retries": 2,
    },
    {
        "stage": PipelineStage.SECURITY_REVIEW,
        "agent": "security_agent",
        "task_type": "security_review",
        "name": "Security Review",
        "description": "SAST analysis and threat modeling",
        "max_retries": 1,
    },
    {
        "stage": PipelineStage.PERFORMANCE_REVIEW,
        "agent": "cto_agent",
        "task_type": "architecture_review",
        "name": "Performance Review",
        "description": "Performance and scalability review",
        "max_retries": 1,
    },
    {
        "stage": PipelineStage.DOCUMENTATION,
        "agent": "documentation_agent",
        "task_type": "doc_generation",
        "name": "Documentation",
        "description": "Generate technical docs and API docs",
        "max_retries": 1,
    },
    {
        "stage": PipelineStage.CODE_REVIEW,
        "agent": "reviewer_agent",
        "task_type": "code_review",
        "name": "Code Review",
        "description": "Final code review and quality gate",
        "max_retries": 2,
    },
    {
        "stage": PipelineStage.RELEASE,
        "agent": "cto_agent",
        "task_type": "strategic_planning",
        "name": "Release",
        "description": "Final approval and release decision",
        "max_retries": 0,
    },
]


def get_stage_def(stage: PipelineStage) -> dict:
    """Get the definition for a pipeline stage."""
    for s in STAGE_DEFS:
        if s["stage"] == stage:
            return s
    return None


def create_pipeline_run(feature: FeatureRequest, pipeline_id: str = None) -> FeaturePipelineRun:
    """Create a new pipeline run with all stages initialized as pending."""
    import uuid
    run_id = pipeline_id or str(uuid.uuid4())

    stages = []
    for sdef in STAGE_DEFS:
        stages.append(StageResult(
            stage=sdef["stage"].value,
            status=StageStatus.PENDING,
            agent=sdef["agent"],
        ))

    return FeaturePipelineRun(
        id=run_id,
        feature=feature,
        stages=stages,
        status="pending",
    )


def get_stage_context(run: FeaturePipelineRun, stage: PipelineStage) -> dict:
    """Build context from previous stages for the current stage."""
    context = {
        "feature": run.feature.model_dump(),
        "stage": stage.value,
    }

    # Collect outputs from completed stages
    stage_order = [s["stage"] for s in STAGE_DEFS]
    stage_idx = stage_order.index(stage)

    for i, prev_stage in enumerate(stage_order[:stage_idx]):
        for s in run.stages:
            if s.stage == prev_stage.value and s.status == StageStatus.PASSED:
                context[f"previous_{prev_stage.value}"] = s.output

    return context


def update_stage_result(run: FeaturePipelineRun, stage: PipelineStage,
                        status: StageStatus, output: dict = None,
                        warnings: list[str] = None, duration_ms: int = 0) -> None:
    """Update the result of a stage in the pipeline run."""
    for s in run.stages:
        if s.stage == stage.value:
            s.status = status
            s.started_at = s.started_at or datetime.utcnow().isoformat()
            s.completed_at = datetime.utcnow().isoformat() if status in (StageStatus.PASSED, StageStatus.FAILED, StageStatus.SKIPPED) else s.completed_at
            s.duration_ms = duration_ms or s.duration_ms
            if output is not None:
                s.output = output
            if warnings is not None:
                s.warnings.extend(warnings)
            break

    run.current_stage = stage.value if status == StageStatus.RUNNING else run.current_stage


def get_pipeline_progress(run: FeaturePipelineRun) -> dict:
    """Get a progress summary of the pipeline run."""
    total_stages = len(run.stages)
    completed = sum(1 for s in run.stages if s.status == StageStatus.PASSED)
    failed = sum(1 for s in run.stages if s.status == StageStatus.FAILED)
    running = sum(1 for s in run.stages if s.status == StageStatus.RUNNING)
    pending = sum(1 for s in run.stages if s.status == StageStatus.PENDING)

    return {
        "total": total_stages,
        "completed": completed,
        "failed": failed,
        "running": running,
        "pending": pending,
        "progress_pct": round((completed / total_stages) * 100, 1) if total_stages > 0 else 0,
        "current_stage": run.current_stage,
        "status": run.status,
    }


def should_retry(run: FeaturePipelineRun, stage: PipelineStage) -> bool:
    """Check if a failed stage should be retried."""
    sdef = get_stage_def(stage)
    if not sdef or sdef["max_retries"] == 0:
        return False

    for s in run.stages:
        if s.stage == stage.value:
            return s.retry_count < sdef["max_retries"]
    return False


def get_pipeline_summary(run: FeaturePipelineRun) -> str:
    """Generate a human-readable summary of the pipeline run."""
    progress = get_pipeline_progress(run)
    lines = [
        f"Pipeline: {run.feature.title}",
        f"Status: {run.status} ({progress['completed']}/{progress['total']} stages complete)",
        f"Progress: {progress['progress_pct']}%",
    ]

    for s in run.stages:
        status_icon = {
            StageStatus.PASSED: "✓",
            StageStatus.FAILED: "✗",
            StageStatus.RUNNING: "→",
            StageStatus.PENDING: "○",
            StageStatus.SKIPPED: "—",
            StageStatus.RETRYING: "↻",
        }.get(s.status, "?")
        lines.append(f"  {status_icon} {s.stage} ({s.agent})")

    return "\n".join(lines)
