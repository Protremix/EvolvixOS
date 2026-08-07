"""
Pipeline Event System — Post-MVP Phase 3

Provides real-time event streaming for pipeline execution.
Integrates with the WebSocket manager for live progress updates
and maintains an event log for replay/audit.

Events emitted:
- pipeline.started
- pipeline.stage_started
- pipeline.stage_passed
- pipeline.stage_failed
- pipeline.stage_retrying
- pipeline.completed
- pipeline.failed
- pipeline.cancelled
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Callable, Optional
from collections import deque
from dataclasses import dataclass, field, asdict

from app.core.logging import get_logger

logger = get_logger("service.pipeline_events")


@dataclass
class PipelineEvent:
    """A single pipeline event."""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = ""
    pipeline_id: str = ""
    stage: str = ""
    status: str = ""
    message: str = ""
    data: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


class PipelineEventBus:
    """
    Event bus for pipeline execution events.
    
    - Maintains an in-memory event log (configurable max size)
    - Notifies registered listeners (sync and async)
    - Integrates with WebSocketManager for real-time broadcasting
    - Supports event replay for late-joining clients
    """

    def __init__(self, max_log_size: int = 1000):
        self._listeners: list[Callable] = []
        self._async_listeners: list[Callable] = []
        self._event_log: deque = deque(maxlen=max_log_size)
        self._pipeline_events: dict[str, list[PipelineEvent]] = {}
        self._max_log_size = max_log_size
        self._ws_manager = None  # Lazy-loaded

    def _get_ws_manager(self):
        """Lazily get the WebSocket manager."""
        if self._ws_manager is not None:
            return self._ws_manager
        try:
            from app.core.websocket_manager import ws_manager
            self._ws_manager = ws_manager
        except Exception:
            pass
        return self._ws_manager

    def subscribe(self, listener: Callable):
        """Subscribe a sync listener."""
        self._listeners.append(listener)

    def subscribe_async(self, listener: Callable):
        """Subscribe an async listener."""
        self._async_listeners.append(listener)

    def unsubscribe(self, listener: Callable):
        """Unsubscribe a listener."""
        if listener in self._listeners:
            self._listeners.remove(listener)
        if listener in self._async_listeners:
            self._async_listeners.remove(listener)

    def emit(self, event: PipelineEvent):
        """Emit a pipeline event to all listeners and log."""
        # Log event
        self._event_log.append(event)
        if event.pipeline_id not in self._pipeline_events:
            self._pipeline_events[event.pipeline_id] = []
        self._pipeline_events[event.pipeline_id].append(event)

        logger.info("pipeline_event",
                     event_type=event.event_type,
                     pipeline_id=event.pipeline_id,
                     stage=event.stage)

        # Notify sync listeners
        for listener in self._listeners:
            try:
                listener(event)
            except Exception as e:
                logger.warning("event_listener_error", error=str(e))

        # Notify async listeners (fire and forget if no loop running)
        for listener in self._async_listeners:
            try:
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(listener(event))
                except RuntimeError:
                    # No running loop — skip
                    pass
            except Exception as e:
                logger.warning("async_event_listener_error", error=str(e))

        # Broadcast via WebSocket
        ws = self._get_ws_manager()
        if ws and ws.connection_count > 0:
            try:
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(ws.broadcast(event.event_type, event.to_dict()))
                except RuntimeError:
                    pass
            except Exception as e:
                logger.warning("ws_broadcast_error", error=str(e))

    def get_pipeline_events(self, pipeline_id: str) -> list[dict]:
        """Get all events for a specific pipeline (for replay)."""
        events = self._pipeline_events.get(pipeline_id, [])
        return [e.to_dict() for e in events]

    def get_recent_events(self, limit: int = 50) -> list[dict]:
        """Get recent events across all pipelines."""
        recent = list(self._event_log)[-limit:]
        return [e.to_dict() for e in recent]

    def clear_pipeline_events(self, pipeline_id: str):
        """Clear events for a specific pipeline."""
        if pipeline_id in self._pipeline_events:
            del self._pipeline_events[pipeline_id]

    @property
    def total_events(self) -> int:
        return len(self._event_log)

    @property
    def active_pipelines(self) -> int:
        """Number of pipelines with events (proxy for active)."""
        return len(self._pipeline_events)


# Singleton event bus
_event_bus: Optional[PipelineEventBus] = None


def get_event_bus() -> PipelineEventBus:
    """Get the singleton pipeline event bus."""
    global _event_bus
    if _event_bus is None:
        _event_bus = PipelineEventBus()
    return _event_bus


# Helper functions for common event types
def emit_pipeline_started(pipeline_id: str, feature_title: str):
    """Emit a pipeline.started event."""
    bus = get_event_bus()
    bus.emit(PipelineEvent(
        event_type="pipeline.started",
        pipeline_id=pipeline_id,
        message=f"Pipeline started: {feature_title}",
        data={"feature_title": feature_title},
    ))


def emit_stage_started(pipeline_id: str, stage: str, agent: str, attempt: int):
    """Emit a pipeline.stage_started event."""
    bus = get_event_bus()
    bus.emit(PipelineEvent(
        event_type="pipeline.stage_started",
        pipeline_id=pipeline_id,
        stage=stage,
        status="running",
        message=f"Stage '{stage}' started (attempt {attempt}, agent: {agent})",
        data={"agent": agent, "attempt": attempt},
    ))


def emit_stage_passed(pipeline_id: str, stage: str, duration_ms: int,
                      tokens: int = 0, score: float = None):
    """Emit a pipeline.stage_passed event."""
    bus = get_event_bus()
    bus.emit(PipelineEvent(
        event_type="pipeline.stage_passed",
        pipeline_id=pipeline_id,
        stage=stage,
        status="passed",
        message=f"Stage '{stage}' passed in {duration_ms}ms",
        data={"duration_ms": duration_ms, "tokens_used": tokens, "score": score},
    ))


def emit_stage_failed(pipeline_id: str, stage: str, error: str,
                      attempt: int, will_retry: bool):
    """Emit a pipeline.stage_failed event."""
    bus = get_event_bus()
    bus.emit(PipelineEvent(
        event_type="pipeline.stage_failed",
        pipeline_id=pipeline_id,
        stage=stage,
        status="failed",
        message=f"Stage '{stage}' failed (attempt {attempt}): {error[:200]}",
        data={"error": error[:500], "attempt": attempt, "will_retry": will_retry},
    ))


def emit_pipeline_completed(pipeline_id: str, total_duration_ms: int,
                            stages_completed: int, stages_total: int):
    """Emit a pipeline.completed event."""
    bus = get_event_bus()
    bus.emit(PipelineEvent(
        event_type="pipeline.completed",
        pipeline_id=pipeline_id,
        status="completed",
        message=f"Pipeline completed: {stages_completed}/{stages_total} stages in {total_duration_ms}ms",
        data={"duration_ms": total_duration_ms, "stages_completed": stages_completed,
              "stages_total": stages_total},
    ))


def emit_pipeline_failed(pipeline_id: str, failed_stage: str, error: str):
    """Emit a pipeline.failed event."""
    bus = get_event_bus()
    bus.emit(PipelineEvent(
        event_type="pipeline.failed",
        pipeline_id=pipeline_id,
        stage=failed_stage,
        status="failed",
        message=f"Pipeline failed at stage '{failed_stage}': {error[:200]}",
        data={"failed_stage": failed_stage, "error": error[:500]},
    ))


def emit_pipeline_cancelled(pipeline_id: str):
    """Emit a pipeline.cancelled event."""
    bus = get_event_bus()
    bus.emit(PipelineEvent(
        event_type="pipeline.cancelled",
        pipeline_id=pipeline_id,
        status="cancelled",
        message="Pipeline cancelled by user",
    ))
