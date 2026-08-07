"""
Pipeline Execution Engine — Post-MVP Phase 2

Connects the Feature Delivery Pipeline to the AI Workflow Engine.
Executes each pipeline stage by routing to the appropriate AI agent,
passing context from previous stages, handling retries, and tracking
results.

This is the "live" execution layer on top of the pipeline data model.
"""

import json
import time
import uuid
from datetime import datetime
from typing import Optional

from app.core.logging import get_logger
from app.services.pipeline_events import (
    emit_pipeline_started, emit_stage_started,
    emit_stage_passed, emit_stage_failed,
    emit_pipeline_completed, emit_pipeline_cancelled,
)
from app.services.feature_pipeline import (
    FeaturePipelineRun, PipelineStage, StageStatus,
    STAGE_DEFS, get_stage_def, get_stage_context,
    update_stage_result, should_retry, get_pipeline_progress,
)

logger = get_logger("service.pipeline_executor")


# In-memory store for active executions (production would use Redis/DB)
_active_runs: dict[str, FeaturePipelineRun] = {}


class PipelineExecutor:
    """Executes feature delivery pipeline stages through AI agents."""

    def __init__(self, workflow_engine=None):
        """
        Args:
            workflow_engine: AIWorkflowEngine instance. If None, tries to
                            import and use the global engine.
        """
        self._engine = workflow_engine
        self._runs = _active_runs

    def _get_engine(self):
        """Lazily get the workflow engine."""
        if self._engine:
            return self._engine
        try:
            from app.ai.workflow_engine import AIWorkflowEngine
            # Try to get from app state or create a new one
            # In production this would be injected via DI
            self._engine = AIWorkflowEngine()
            self._register_default_agents()
            return self._engine
        except Exception as e:
            logger.warning("workflow_engine_unavailable", error=str(e))
            return None

    def _register_default_agents(self):
        """Register default AI agents if not already registered."""
        try:
            from app.ai.agents.cto_agent import CTOAgent
            from app.ai.agents.architect_agent import ArchitectAgent
            from app.ai.agents.planner_agent import PlannerAgent
            from app.ai.agents.security_agent import SecurityAgent
            from app.ai.agents.qa_agent import QAAgent
            from app.ai.agents.reviewer_agent import ReviewerAgent
            from app.ai.agents.documentation_agent import DocumentationAgent

            agents = [
                CTOAgent, ArchitectAgent, PlannerAgent,
                SecurityAgent, QAAgent, ReviewerAgent, DocumentationAgent,
            ]
            for AgentClass in agents:
                try:
                    agent = AgentClass()
                    self._engine.register_agent(agent)
                except Exception as e:
                    logger.warning("agent_registration_failed",
                                    agent=AgentClass.__name__, error=str(e))
        except Exception as e:
            logger.warning("default_agents_registration_failed", error=str(e))

    def execute_pipeline(self, run: FeaturePipelineRun,
                         start_stage: Optional[str] = None) -> FeaturePipelineRun:
        """
        Execute the full pipeline or resume from a specific stage.

        Args:
            run: The pipeline run to execute
            start_stage: Stage to resume from (None = start from beginning
                         or first pending stage)

        Returns:
            Updated FeaturePipelineRun
        """
        self._runs[run.id] = run
        run.status = "running"

        logger.info("pipeline_execution_started",
                    pipeline_id=run.id, feature=run.feature.title)
        emit_pipeline_started(run.id, run.feature.title)

        # Determine starting stage
        stage_order = [s["stage"] for s in STAGE_DEFS]
        start_idx = 0
        if start_stage:
            for i, s in enumerate(stage_order):
                if s.value == start_stage:
                    start_idx = i
                    break

        # Skip already completed stages
        for i in range(start_idx, len(STAGE_DEFS)):
            sdef = STAGE_DEFS[i]
            stage = sdef["stage"]

            # Skip if already passed
            existing = next((s for s in run.stages if s.stage == stage.value
                           and s.status == StageStatus.PASSED), None)
            if existing:
                continue

            # Execute this stage
            success = self._execute_stage(run, stage)

            if not success:
                run.status = "failed"
                logger.error("pipeline_stage_failed",
                             pipeline_id=run.id, stage=stage.value)
                break

        if run.status != "failed":
            run.status = "completed"
            run.completed_at = datetime.utcnow().isoformat()
            completed_count = sum(1 for s in run.stages if s.status == StageStatus.PASSED)
            emit_pipeline_completed(run.id, run.total_duration_ms, completed_count, len(run.stages))

        # Calculate total duration
        total_ms = sum(s.duration_ms for s in run.stages)
        run.total_duration_ms = total_ms

        # Generate summary
        from app.services.feature_pipeline import get_pipeline_summary
        run.summary = get_pipeline_summary(run)

        logger.info("pipeline_execution_completed",
                    pipeline_id=run.id, status=run.status,
                    duration_ms=total_ms)

        return run

    def _execute_stage(self, run: FeaturePipelineRun,
                       stage: PipelineStage) -> bool:
        """Execute a single pipeline stage with retry logic."""
        sdef = get_stage_def(stage)
        if not sdef:
            logger.error("stage_definition_not_found", stage=stage.value)
            return False

        max_retries = sdef["max_retries"]
        max_attempts = max_retries + 1

        for attempt in range(max_attempts):
            update_stage_result(run, stage, StageStatus.RUNNING)
            emit_stage_started(run.id, stage.value, sdef["agent"], attempt + 1)
            logger.info("stage_started",
                        pipeline_id=run.id, stage=stage.value,
                        attempt=attempt + 1, max=max_attempts)

            start_time = time.time()

            try:
                # Build context from previous stages
                context = get_stage_context(run, stage)

                # Add stage-specific instructions
                context["stage_name"] = sdef["name"]
                context["stage_description"] = sdef["description"]
                context["attempt"] = attempt + 1

                # Execute via workflow engine
                result = self._run_agent(sdef, context)

                elapsed_ms = int((time.time() - start_time) * 1000)

                if result and result.status.value == "completed":
                    # Stage passed
                    output = {
                        "content": result.content[:2000] if result.content else "",
                        "score": result.score,
                        "recommendations": result.recommendations[:5] if result.recommendations else [],
                        "findings": result.findings[:5] if result.findings else [],
                        "tokens_used": result.tokens_used,
                        "structured_data": result.structured_data if result.structured_data else {},
                    }
                    warnings = [f for f in result.findings
                               if isinstance(f, dict) and f.get("severity") == "warning"]
                    if not warnings and isinstance(result.findings, list):
                        warnings = [str(f) for f in result.findings
                                   if "warning" in str(f).lower()][:3]

                    update_stage_result(
                        run, stage, StageStatus.PASSED,
                        output=output,
                        warnings=warnings[:5],
                        duration_ms=elapsed_ms,
                    )

                    emit_stage_passed(run.id, stage.value, elapsed_ms,
                                     tokens=result.tokens_used, score=result.score)
                    logger.info("stage_passed",
                                pipeline_id=run.id, stage=stage.value,
                                duration_ms=elapsed_ms,
                                tokens=result.tokens_used,
                                attempt=attempt + 1)
                    return True

                else:
                    # Stage failed
                    error_msg = result.content if result else "No result returned"
                    update_stage_result(
                        run, stage, StageStatus.FAILED,
                        output={"error": error_msg[:500]},
                        duration_ms=elapsed_ms,
                    )

                    logger.warning("stage_failed",
                                    pipeline_id=run.id, stage=stage.value,
                                    attempt=attempt + 1, max=max_attempts,
                                    error=error_msg[:200])

                    if attempt < max_retries:
                        # Update retry count and retry
                        for s in run.stages:
                            if s.stage == stage.value:
                                s.retry_count = attempt + 1
                                s.status = StageStatus.RETRYING
                                break
                        continue
                    else:
                        return False

            except Exception as e:
                elapsed_ms = int((time.time() - start_time) * 1000)
                logger.error("stage_execution_error",
                              pipeline_id=run.id, stage=stage.value,
                              error=str(e), attempt=attempt + 1)
                update_stage_result(
                    run, stage, StageStatus.FAILED,
                    output={"error": str(e)[:500]},
                    duration_ms=elapsed_ms,
                )
                if attempt < max_retries:
                    for s in run.stages:
                        if s.stage == stage.value:
                            s.retry_count = attempt + 1
                            s.status = StageStatus.RETRYING
                            break
                    continue
                return False

        return False

    def _run_agent(self, stage_def: dict, context: dict):
        """Run the agent for a stage definition."""
        engine = self._get_engine()
        if not engine:
            # Fallback: return a mock result if no engine available
            logger.warning("no_workflow_engine_mock_result",
                          stage=stage_def["stage"].value)
            from app.ai.agents.base_agent import AgentResult, AgentStatus
            return AgentResult(
                task_id=str(uuid.uuid4()),
                agent_name=stage_def["agent"],
                status=AgentStatus.COMPLETED,
                content=f"Stage '{stage_def['name']}' executed (no LLM — engine unavailable). "
                       f"Feature: {context.get('feature', {}).get('title', 'unknown')}. "
                       f"Stage output: {stage_def['description']}.",
                tokens_used=0,
                latency_ms=0.0,
            )

        try:
            from app.ai.agents.base_agent import TaskType
            task_type = TaskType(stage_def["task_type"])
            result = engine.execute_task(task_type, context)
            return result
        except Exception as e:
            logger.error("agent_execution_failed",
                        agent=stage_def["agent"],
                        error=str(e))
            from app.ai.agents.base_agent import AgentResult, AgentStatus
            return AgentResult(
                task_id=str(uuid.uuid4()),
                agent_name=stage_def["agent"],
                status=AgentStatus.FAILED,
                content=f"Agent execution error: {str(e)}",
                tokens_used=0,
                latency_ms=0.0,
            )

    def get_run(self, run_id: str) -> Optional[FeaturePipelineRun]:
        """Get a pipeline run by ID."""
        return self._runs.get(run_id)

    def list_active_runs(self) -> list[FeaturePipelineRun]:
        """List all active pipeline runs."""
        return [r for r in self._runs.values() if r.status == "running"]

    def cancel_run(self, run_id: str) -> bool:
        """Cancel a running pipeline."""
        run = self._runs.get(run_id)
        if run and run.status == "running":
            run.status = "cancelled"
            emit_pipeline_cancelled(run_id)
            for s in run.stages:
                if s.status == StageStatus.RUNNING:
                    s.status = StageStatus.FAILED
                    s.output = {"error": "Pipeline cancelled"}
            logger.info("pipeline_cancelled", pipeline_id=run_id)
            return True
        return False


# Singleton executor
_executor: Optional[PipelineExecutor] = None


def get_executor() -> PipelineExecutor:
    """Get the singleton pipeline executor."""
    global _executor
    if _executor is None:
        _executor = PipelineExecutor()
    return _executor
