"""
AI Core API endpoints for EvolvixOS.

Provides HTTP endpoints to interact with AI agents:
- List registered agents
- Execute a single agent task
- Execute multi-step pipelines
- Retrieve agent results
"""

from typing import Any, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from structlog import get_logger

from app.api.deps import get_current_active_user
from app.core.websocket_manager import ws_manager
from app.models.user import User

# Distributed execution imports (lazy-loaded in endpoints)

logger = get_logger(__name__)

router = APIRouter(prefix="/ai", tags=["ai-core"])


# ============================================================
# Schemas
# ============================================================

class TaskRequest(BaseModel):
    """Request to execute an AI agent task."""
    task_type: str = Field(..., description="Type of task (e.g. architecture_review, security_review)")
    data: dict = Field(default_factory=dict, description="Task payload")
    agent_name: Optional[str] = Field(None, description="Specific agent to use (optional)")


class TaskResponse(BaseModel):
    """Response from an AI agent task."""
    task_id: str
    agent_name: str
    status: str
    content: str
    structured_data: Optional[dict] = None
    recommendations: list = Field(default_factory=list)
    score: Optional[float] = None
    findings: list = Field(default_factory=list)
    tokens_used: int = 0
    latency_ms: float = 0.0


class PipelineRequest(BaseModel):
    """Request to execute a multi-step agent pipeline."""
    name: str = Field(..., description="Pipeline name")
    steps: list[dict] = Field(..., description="List of steps with task_type and optional depends_on")


class PipelineResponse(BaseModel):
    """Response from a pipeline execution."""
    pipeline_id: str
    status: str
    results: dict


class AgentInfo(BaseModel):
    """Information about a registered agent."""
    name: str
    description: str
    task_types: list[str]
    display_name: str = ""
    status: str = "active"
    model: str = "GPT-4o"
    supported_types: list[str] = []
    tasks_completed: int = 0



class DispatchRequest(BaseModel):
    """Request to dispatch a task for concurrent execution."""
    task_type: str = Field(..., description="Type of task to execute")
    data: dict = Field(default_factory=dict, description="Task payload")
    timeout: Optional[int] = Field(None, description="Timeout in seconds")


class BatchDispatchRequest(BaseModel):
    """Request to dispatch multiple tasks concurrently."""
    tasks: list[dict] = Field(..., description="List of {task_type, data} objects")


class DispatchResponse(BaseModel):
    """Response from task dispatch."""
    task_id: str
    status: str


class ExecutorStatusResponse(BaseModel):
    """Distributed executor status."""
    max_workers: int
    pending: int
    completed: int
    running: int

# ============================================================
# Endpoints
# ============================================================

@router.get("/agents", response_model=list[AgentInfo])
async def list_agents(
    current_user: User = Depends(get_current_active_user),
):
    """List all registered AI agents."""
    from app.ai.workflow_engine import get_workflow_engine
    engine = get_workflow_engine()
    return engine.list_agents()


@router.post("/tasks", response_model=TaskResponse)
async def execute_task(
    request: TaskRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Execute a single AI agent task."""
    from app.ai.workflow_engine import get_workflow_engine
    from app.ai.agents.base_agent import TaskType

    # Validate task type
    try:
        task_type = TaskType(request.task_type)
    except ValueError:
        valid_types = [t.value for t in TaskType]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid task type '{request.task_type}'. Valid types: {valid_types}",
        )

    engine = get_workflow_engine()

    # Check if an agent can handle this task
    agent = engine.route_task(task_type)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No agent registered for task type '{request.task_type}'",
        )

    logger.info("ai_task_requested", task_type=request.task_type, user=current_user.email)

    result = engine.execute_task(task_type, request.data)

    # Broadcast task completion via WebSocket
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(ws_manager.broadcast("task_completed", {
                "task_id": result.task_id,
                "agent_name": result.agent_name,
                "task_type": request.task_type,
                "status": result.status.value,
            }))
    except RuntimeError:
        pass

    return TaskResponse(
        task_id=result.task_id,
        agent_name=result.agent_name,
        status=result.status.value,
        content=result.content,
        structured_data=result.structured_data,
        recommendations=result.recommendations,
        score=result.score,
        findings=result.findings,
        tokens_used=result.tokens_used,
        latency_ms=result.latency_ms,
    )


@router.post("/pipelines", response_model=PipelineResponse)
async def execute_pipeline(
    request: PipelineRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Execute a multi-step AI agent pipeline."""
    from app.ai.workflow_engine import get_workflow_engine

    engine = get_workflow_engine()

    logger.info("ai_pipeline_requested", name=request.name, steps=len(request.steps), user=current_user.email)

    result = engine.execute_pipeline(request.name, request.steps)

    return PipelineResponse(
        pipeline_id=result["pipeline_id"],
        status=result["status"],
        results=result["results"],
    )



# ============================================================
# Distributed Execution Endpoints
# ============================================================

@router.post("/dispatch", response_model=DispatchResponse)
async def dispatch_task(
    request: DispatchRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Dispatch a task for concurrent execution."""
    from app.ai.workflow_engine import get_workflow_engine
    from app.ai.distributed_executor import get_distributed_executor
    from app.ai.agents.base_agent import TaskType

    try:
        task_type = TaskType(request.task_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid task type: {request.task_type}",
        )

    engine = get_workflow_engine()
    executor = get_distributed_executor()

    task_id = executor.dispatch(engine, task_type, request.data, request.timeout)
    if not task_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No agent registered for task type '{request.task_type}'",
        )

    # Broadcast task dispatch via WebSocket
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(ws_manager.broadcast("task_dispatched", {
                "task_id": task_id,
                "task_type": request.task_type,
            }))
    except RuntimeError:
        pass

    return DispatchResponse(task_id=task_id, status="dispatched")


@router.post("/dispatch/batch", response_model=list[DispatchResponse])
async def dispatch_batch(
    request: BatchDispatchRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Dispatch multiple tasks for concurrent execution."""
    from app.ai.workflow_engine import get_workflow_engine
    from app.ai.distributed_executor import get_distributed_executor
    from app.ai.agents.base_agent import TaskType

    engine = get_workflow_engine()
    executor = get_distributed_executor()

    results = []
    for task_def in request.tasks:
        try:
            task_type = TaskType(task_def["task_type"])
            data = task_def.get("data", {})
            task_id = executor.dispatch(engine, task_type, data)
            if task_id:
                results.append(DispatchResponse(task_id=task_id, status="dispatched"))
        except (ValueError, KeyError) as e:
            results.append(DispatchResponse(task_id="", status=f"error: {str(e)}"))

    return results


@router.get("/dispatch/{task_id}/result", response_model=TaskResponse)
async def get_dispatch_result(
    task_id: str,
    timeout: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
):
    """Get the result of a dispatched task (blocks until complete)."""
    from app.ai.distributed_executor import get_distributed_executor

    executor = get_distributed_executor()
    result = executor.get_result(task_id, timeout)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task not found or still running: {task_id}",
        )

    return TaskResponse(
        task_id=result.task_id,
        agent_name=result.agent_name,
        status=result.status.value,
        content=result.content,
        structured_data=result.structured_data,
        recommendations=result.recommendations,
        score=result.score,
        findings=result.findings,
        tokens_used=result.tokens_used,
        latency_ms=result.latency_ms,
    )


@router.get("/executor/status", response_model=ExecutorStatusResponse)
async def executor_status(
    current_user: User = Depends(get_current_active_user),
):
    """Get the distributed executor status."""
    from app.ai.distributed_executor import get_distributed_executor

    executor = get_distributed_executor()
    return executor.get_status()


@router.get("/health")
async def ai_health(
    current_user: User = Depends(get_current_active_user),
):
    """Check AI Core health — agents registered, LLM client available."""
    from app.ai.workflow_engine import get_workflow_engine
    from app.ai.llm_client import get_llm_client

    engine = get_workflow_engine()
    agents = engine.list_agents()

    llm = get_llm_client()

    return {
        "status": "healthy" if agents else "degraded",
        "agents_registered": len(agents),
        "agents": [a["name"] for a in agents],
        "llm_model": llm.model,
        "llm_api_key_configured": bool(llm.api_key),
    }
