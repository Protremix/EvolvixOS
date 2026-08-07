"""
Agent Collaboration Service — Phase 18

Enables AI agents to work together on complex tasks:
- Collaboration Sessions: group agents for multi-step tasks
- Context Sharing: agents share results and context
- Dependency Chains: agent B uses agent A's output as input
- Collaboration Patterns: review-then-fix, audit-then-document, etc.
- Real-time status tracking
"""

from typing import Optional
from datetime import datetime
from dataclasses import dataclass, field, asdict
from collections import deque
import threading
from app.core.logging import get_logger

logger = get_logger("service.agent_collaboration")


@dataclass
class CollaborationStep:
    """A single step in a collaboration session."""
    id: str = field(default_factory=lambda: f"step-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}")
    agent_name: str = ""
    task_type: str = ""
    status: str = "pending"  # pending, running, completed, failed
    input_data: dict = field(default_factory=dict)
    output_data: dict = field(default_factory=dict)
    depends_on: list = field(default_factory=list)  # step IDs this step depends on
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    score: Optional[float] = None
    verdict: Optional[str] = None
    findings: list = field(default_factory=list)
    recommendations: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class CollaborationSession:
    """A collaboration session where multiple agents work together."""
    id: str = field(default_factory=lambda: f"collab-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}")
    name: str = ""
    pattern: str = ""  # review_then_fix, audit_then_document, parallel_review, sequential_pipeline
    project: str = ""
    description: str = ""
    steps: list[CollaborationStep] = field(default_factory=list)
    status: str = "pending"  # pending, running, completed, failed
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    completed_at: Optional[str] = None
    final_result: dict = field(default_factory=dict)
    agents_involved: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "pattern": self.pattern,
            "project": self.project,
            "description": self.description,
            "steps": [s.to_dict() for s in self.steps],
            "status": self.status,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "final_result": self.final_result,
            "agents_involved": self.agents_involved,
        }


# Pre-built collaboration patterns
COLLAB_PATTERNS = {
    "review_then_fix": {
        "name": "Review then Fix",
        "description": "Reviewer agent reviews code, then CI Healer fixes issues found",
        "agents": ["reviewer_agent", "ci_healer_agent"],
        "steps": [
            {"agent": "reviewer_agent", "task_type": "code_review", "depends_on": []},
            {"agent": "ci_healer_agent", "task_type": "ci_heal", "depends_on": ["step_1"]},
        ],
    },
    "audit_then_document": {
        "name": "Audit then Document",
        "description": "Security agent audits, then Documentation agent documents findings",
        "agents": ["security_agent", "documentation_agent"],
        "steps": [
            {"agent": "security_agent", "task_type": "security_review", "depends_on": []},
            {"agent": "documentation_agent", "task_type": "doc_generation", "depends_on": ["step_1"]},
        ],
    },
    "parallel_review": {
        "name": "Parallel Review",
        "description": "Multiple agents review in parallel: Security, QA, Architect",
        "agents": ["security_agent", "qa_agent", "architect_agent"],
        "steps": [
            {"agent": "security_agent", "task_type": "security_review", "depends_on": []},
            {"agent": "qa_agent", "task_type": "quality_gate", "depends_on": []},
            {"agent": "architect_agent", "task_type": "system_design", "depends_on": []},
        ],
    },
    "sequential_pipeline": {
        "name": "Sequential Pipeline",
        "description": "CTO → Architect → Planner → QA → Reviewer",
        "agents": ["cto_agent", "architect_agent", "planner_agent", "qa_agent", "reviewer_agent"],
        "steps": [
            {"agent": "cto_agent", "task_type": "architecture_review", "depends_on": []},
            {"agent": "architect_agent", "task_type": "system_design", "depends_on": ["step_1"]},
            {"agent": "planner_agent", "task_type": "task_decomposition", "depends_on": ["step_2"]},
            {"agent": "qa_agent", "task_type": "quality_gate", "depends_on": ["step_3"]},
            {"agent": "reviewer_agent", "task_type": "code_review", "depends_on": ["step_4"]},
        ],
    },
    "security_deep_dive": {
        "name": "Security Deep Dive",
        "description": "Security audit → CTO review of findings → CI Healer fixes",
        "agents": ["security_agent", "cto_agent", "ci_healer_agent"],
        "steps": [
            {"agent": "security_agent", "task_type": "security_review", "depends_on": []},
            {"agent": "cto_agent", "task_type": "architecture_review", "depends_on": ["step_1"]},
            {"agent": "ci_healer_agent", "task_type": "ci_heal", "depends_on": ["step_2"]},
        ],
    },
    "feature_lifecycle": {
        "name": "Feature Lifecycle",
        "description": "Planner → Architect → QA → Security → Documentation → Reviewer",
        "agents": ["planner_agent", "architect_agent", "qa_agent", "security_agent", "documentation_agent", "reviewer_agent"],
        "steps": [
            {"agent": "planner_agent", "task_type": "task_decomposition", "depends_on": []},
            {"agent": "architect_agent", "task_type": "system_design", "depends_on": ["step_1"]},
            {"agent": "qa_agent", "task_type": "test_generation", "depends_on": ["step_2"]},
            {"agent": "security_agent", "task_type": "security_review", "depends_on": ["step_2"]},
            {"agent": "documentation_agent", "task_type": "doc_generation", "depends_on": ["step_2"]},
            {"agent": "reviewer_agent", "task_type": "code_review", "depends_on": ["step_3", "step_4", "step_5"]},
        ],
    },
}


class AgentCollaborationService:
    """Manages agent collaboration sessions and patterns."""

    def __init__(self, max_sessions: int = 500):
        self._sessions: dict[str, CollaborationSession] = {}
        self._max_sessions = max_sessions
        self._lock = threading.Lock()
        self._event_listeners: list = []

    def list_patterns(self) -> list[dict]:
        """List all collaboration patterns."""
        return [
            {"key": k, "name": v["name"], "description": v["description"],
             "agents": v["agents"], "step_count": len(v["steps"])}
            for k, v in COLLAB_PATTERNS.items()
        ]

    def get_pattern(self, key: str) -> Optional[dict]:
        """Get a specific pattern."""
        return COLLAB_PATTERNS.get(key)

    def create_session(self, name: str, pattern: str, project: str = "",
                       description: str = "", custom_steps: list = None) -> CollaborationSession:
        """Create a collaboration session from a pattern or custom steps."""
        session = CollaborationSession(
            name=name, pattern=pattern,
            project=project, description=description,
        )

        if custom_steps:
            # Use custom steps
            for i, step in enumerate(custom_steps):
                session.steps.append(CollaborationStep(
                    agent_name=step.get("agent_name", ""),
                    task_type=step.get("task_type", ""),
                    depends_on=step.get("depends_on", []),
                    input_data=step.get("input_data", {}),
                ))
        else:
            # Use pattern — map "step_1", "step_2" placeholders to actual IDs
            pat = COLLAB_PATTERNS.get(pattern)
            if pat:
                # First pass: create steps
                step_id_map = {}  # "step_1" -> actual_id
                for i, step_def in enumerate(pat["steps"]):
                    step = CollaborationStep(
                        agent_name=step_def["agent"],
                        task_type=step_def["task_type"],
                        depends_on=[],  # will set after all IDs exist
                    )
                    session.steps.append(step)
                    step_id_map[f"step_{i+1}"] = step.id
                # Second pass: map dependencies
                for i, step_def in enumerate(pat["steps"]):
                    mapped_deps = [step_id_map.get(d, d) for d in step_def.get("depends_on", [])]
                    session.steps[i].depends_on = mapped_deps
                session.agents_involved = pat["agents"]

        with self._lock:
            self._sessions[session.id] = session
            if len(self._sessions) > self._max_sessions:
                # Remove oldest
                oldest_id = next(iter(self._sessions))
                del self._sessions[oldest_id]

        logger.info("collaboration_session_created", id=session.id, name=name, pattern=pattern)
        self._emit_event("collaboration.created", {"session_id": session.id, "name": name})
        return session

    def get_session(self, session_id: str) -> Optional[CollaborationSession]:
        return self._sessions.get(session_id)

    def list_sessions(self, status: str = None, limit: int = 50) -> list[CollaborationSession]:
        sessions = list(self._sessions.values())
        if status:
            sessions = [s for s in sessions if s.status == status]
        return sorted(sessions, key=lambda s: s.created_at, reverse=True)[:limit]

    def update_step(self, session_id: str, step_id: str, status: str,
                    output_data: dict = None, score: float = None,
                    verdict: str = None, findings: list = None,
                    recommendations: list = None) -> bool:
        """Update a step in a collaboration session."""
        session = self._sessions.get(session_id)
        if not session:
            return False

        for step in session.steps:
            if step.id == step_id:
                step.status = status
                if status == "running" and not step.started_at:
                    step.started_at = datetime.utcnow().isoformat()
                if status in ("completed", "failed"):
                    step.completed_at = datetime.utcnow().isoformat()
                if output_data:
                    step.output_data = output_data
                if score is not None:
                    step.score = score
                if verdict:
                    step.verdict = verdict
                if findings:
                    step.findings = findings
                if recommendations:
                    step.recommendations = recommendations

                self._emit_event("collaboration.step_updated", {
                    "session_id": session_id, "step_id": step_id,
                    "status": status, "agent": step.agent_name,
                })

                # Check if all steps complete
                all_done = all(s.status in ("completed", "failed") for s in session.steps)
                if all_done:
                    session.status = "completed"
                    session.completed_at = datetime.utcnow().isoformat()
                    session.final_result = self._compute_final_result(session)
                    self._emit_event("collaboration.completed", {
                        "session_id": session_id, "result": session.final_result,
                    })

                return True
        return False

    def _compute_final_result(self, session: CollaborationSession) -> dict:
        """Compute aggregate result from all steps."""
        scores = [s.score for s in session.steps if s.score is not None]
        all_findings = []
        all_recommendations = []
        for s in session.steps:
            all_findings.extend(s.findings)
            all_recommendations.extend(s.recommendations)

        return {
            "avg_score": round(sum(scores) / len(scores), 1) if scores else 0,
            "total_findings": len(all_findings),
            "total_recommendations": len(all_recommendations),
            "steps_completed": sum(1 for s in session.steps if s.status == "completed"),
            "steps_failed": sum(1 for s in session.steps if s.status == "failed"),
            "critical_findings": sum(1 for f in all_findings if isinstance(f, dict) and f.get("severity", "").lower() == "critical"),
            "high_findings": sum(1 for f in all_findings if isinstance(f, dict) and f.get("severity", "").lower() == "high"),
            "overall_verdict": "GO" if all(s.status == "completed" for s in session.steps) else "NO-GO",
        }

    def get_step_context(self, session_id: str, step_id: str) -> dict:
        """Get context from previous steps for a given step (dependency chain)."""
        session = self._sessions.get(session_id)
        if not session:
            return {}

        step = next((s for s in session.steps if s.id == step_id), None)
        if not step:
            return {}

        context = {}
        for dep_id in step.depends_on:
            dep_step = next((s for s in session.steps if s.id == dep_id), None)
            if dep_step and dep_step.status == "completed":
                context[dep_id] = {
                    "agent": dep_step.agent_name,
                    "output": dep_step.output_data,
                    "score": dep_step.score,
                    "findings": dep_step.findings,
                    "recommendations": dep_step.recommendations,
                }

        return context

    def simulate_session(self, session_id: str) -> dict:
        """Simulate a collaboration session with mock data (for testing/demo)."""
        from app.services.agent_simulation import get_simulation_service
        sim = get_simulation_service()

        session = self._sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}

        session.status = "running"
        results = []

        for step in session.steps:
            # Update step to running
            self.update_step(session_id, step.id, "running")

            # Run simulation
            sim_result = sim.run_agent_simulation(step.agent_name, step.task_type, step.input_data)

            # Update step with results
            self.update_step(
                session_id, step.id, "completed",
                output_data=sim_result.get("output", {}),
                score=sim_result.get("score"),
                verdict=sim_result.get("verdict"),
                findings=sim_result.get("findings", []),
                recommendations=sim_result.get("recommendations", []),
            )

            results.append({
                "step_id": step.id,
                "agent": step.agent_name,
                "status": "completed",
                "score": sim_result.get("score"),
                "verdict": sim_result.get("verdict"),
            })

        return {
            "session_id": session_id,
            "status": "completed",
            "steps": results,
            "final_result": session.final_result,
        }


    def execute_session_real(self, session_id: str, use_verdis_context: bool = True) -> dict:
        """
        Execute a collaboration session with REAL LLM calls.
        Each step calls the actual AI agent via the workflow engine.
        """
        from app.ai.workflow_engine import get_workflow_engine
        from app.services.verdis_agent_enhancer import get_verdis_enhancer
        from app.services.realtime_monitor import get_realtime_monitor
        from app.ai.agents.base_agent import TaskType
        import time

        session = self._sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}

        engine = get_workflow_engine()
        monitor = get_realtime_monitor()
        enhancer = get_verdis_enhancer()

        session.status = "running"
        monitor.emit("collaboration_started", "collaboration",
                      f"Real session '{session.name}' started",
                      {"session_id": session_id}, "success")

        results = []

        for step in session.steps:
            # Check dependencies are completed
            dep_context = self.get_step_context(session_id, step.id)
            if step.depends_on and not dep_context:
                self.update_step(session_id, step.id, "failed",
                    output_data={"error": "Dependencies not met"})
                monitor.emit("step_failed", step.agent_name,
                    f"Step {step.id} failed — dependencies not met",
                    {"session_id": session_id}, "error")
                results.append({"step_id": step.id, "status": "failed", "error": "deps_not_met"})
                continue

            # Mark step as running
            self.update_step(session_id, step.id, "running")
            monitor.emit("agent_started", step.agent_name,
                f"Agent {step.agent_name} executing {step.task_type}",
                {"session_id": session_id, "step_id": step.id}, "info")

            # Build task data with dependency context
            task_data = dict(step.input_data)
            if dep_context:
                task_data["previous_steps"] = dep_context

            # Inject Verdis context if enabled
            if use_verdis_context:
                task_data["verdis_context"] = enhancer.get_context().to_dict()

            start_time = time.time()

            try:
                # Route to the actual agent and execute
                task_type_enum = None
                try:
                    task_type_enum = TaskType(step.task_type)
                except ValueError:
                    # Unknown task type — use architecture_review as fallback
                    task_type_enum = TaskType.ARCHITECTURE_REVIEW

                result = engine.execute_task(task_type_enum, task_data)
                latency_ms = (time.time() - start_time) * 1000

                if result.status.value == "completed":
                    self.update_step(
                        session_id, step.id, "completed",
                        output_data=result.structured_data or {"content": result.content},
                        score=result.score,
                        verdict=result.structured_data.get("verdict") if result.structured_data else None,
                        findings=result.findings if result.findings else [],
                        recommendations=result.recommendations if result.recommendations else [],
                    )
                    monitor.emit("agent_completed", step.agent_name,
                        f"Agent {step.agent_name} completed ({result.score or 0}/10)",
                        {"session_id": session_id, "score": result.score,
                         "tokens": result.tokens_used, "latency_ms": latency_ms}, "success")

                    # Record metrics
                    monitor.record_metric("agent_latency_ms", latency_ms, "ms")
                    monitor.record_metric("agent_tokens", result.tokens_used, "tokens")

                    results.append({
                        "step_id": step.id,
                        "agent": step.agent_name,
                        "status": "completed",
                        "score": result.score,
                        "verdict": result.structured_data.get("verdict") if result.structured_data else None,
                        "tokens_used": result.tokens_used,
                        "latency_ms": latency_ms,
                        "findings_count": len(result.findings) if result.findings else 0,
                    })
                else:
                    self.update_step(session_id, step.id, "failed",
                        output_data={"error": result.content})
                    monitor.emit("agent_failed", step.agent_name,
                        f"Agent {step.agent_name} failed",
                        {"session_id": session_id}, "error")
                    results.append({
                        "step_id": step.id,
                        "agent": step.agent_name,
                        "status": "failed",
                        "error": result.content[:200],
                    })

            except Exception as e:
                latency_ms = (time.time() - start_time) * 1000
                self.update_step(session_id, step.id, "failed",
                    output_data={"error": str(e)})
                monitor.emit("agent_failed", step.agent_name,
                    f"Agent {step.agent_name} exception: {str(e)}",
                    {"session_id": session_id}, "error")
                results.append({
                    "step_id": step.id,
                    "agent": step.agent_name,
                    "status": "failed",
                    "error": str(e)[:200],
                })

        monitor.emit("collaboration_completed", "collaboration",
            f"Session '{session.name}' completed",
            {"session_id": session_id, "final_result": session.final_result}, "success")

        return {
            "session_id": session_id,
            "status": session.status,
            "steps": results,
            "final_result": session.final_result,
            "execution_mode": "real_llm",
        }

    def get_stats(self) -> dict:
        """Get collaboration statistics."""
        total = len(self._sessions)
        completed = sum(1 for s in self._sessions.values() if s.status == "completed")
        running = sum(1 for s in self._sessions.values() if s.status == "running")
        patterns_used = {}
        for s in self._sessions.values():
            patterns_used[s.pattern] = patterns_used.get(s.pattern, 0) + 1

        return {
            "total_sessions": total,
            "completed": completed,
            "running": running,
            "patterns_available": len(COLLAB_PATTERNS),
            "patterns_used": patterns_used,
        }

    def add_event_listener(self, callback):
        """Add a callback for collaboration events."""
        self._event_listeners.append(callback)

    def _emit_event(self, event_type: str, data: dict):
        """Emit an event to listeners."""
        for cb in self._event_listeners:
            try:
                cb(event_type, data)
            except Exception:
                pass


# Singleton
_service: Optional[AgentCollaborationService] = None


def get_collaboration_service() -> AgentCollaborationService:
    global _service
    if _service is None:
        _service = AgentCollaborationService()
    return _service
