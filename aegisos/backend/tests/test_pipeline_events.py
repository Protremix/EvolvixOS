"""Tests for Pipeline Event System — Post-MVP Phase 3."""

import pytest
import asyncio
from app.services.pipeline_events import (
    PipelineEvent, PipelineEventBus, get_event_bus,
    emit_pipeline_started, emit_stage_started, emit_stage_passed,
    emit_stage_failed, emit_pipeline_completed, emit_pipeline_cancelled,
    emit_pipeline_failed,
)


@pytest.fixture
def fresh_bus():
    """Get a fresh event bus for testing."""
    return PipelineEventBus(max_log_size=100)


class TestPipelineEvent:
    """Test the PipelineEvent dataclass."""

    def test_event_creation(self):
        event = PipelineEvent(
            event_type="pipeline.started",
            pipeline_id="test-123",
            message="Pipeline started",
        )
        assert event.event_type == "pipeline.started"
        assert event.pipeline_id == "test-123"
        assert event.timestamp is not None

    def test_event_to_dict(self):
        event = PipelineEvent(
            event_type="pipeline.stage_passed",
            pipeline_id="test-123",
            stage="prd_generation",
            status="passed",
            data={"duration_ms": 1500},
        )
        d = event.to_dict()
        assert d["event_type"] == "pipeline.stage_passed"
        assert d["pipeline_id"] == "test-123"
        assert d["data"]["duration_ms"] == 1500

    def test_event_to_json(self):
        event = PipelineEvent(event_type="test", pipeline_id="p1")
        j = event.to_json()
        assert isinstance(j, str)
        assert '"event_type": "test"' in j

    def test_event_auto_id(self):
        e1 = PipelineEvent()
        e2 = PipelineEvent()
        assert e1.event_id != e2.event_id


class TestPipelineEventBus:
    """Test the event bus functionality."""

    def test_singleton(self):
        bus1 = get_event_bus()
        bus2 = get_event_bus()
        assert bus1 is bus2

    def test_emit_and_log(self, fresh_bus):
        event = PipelineEvent(
            event_type="test.event",
            pipeline_id="p1",
            message="Test",
        )
        fresh_bus.emit(event)
        assert fresh_bus.total_events == 1

    def test_pipeline_events_tracking(self, fresh_bus):
        for i in range(3):
            fresh_bus.emit(PipelineEvent(
                event_type="test.event",
                pipeline_id="p1",
                message=f"Event {i}",
            ))
        events = fresh_bus.get_pipeline_events("p1")
        assert len(events) == 3

    def test_multiple_pipelines(self, fresh_bus):
        fresh_bus.emit(PipelineEvent(event_type="test", pipeline_id="p1"))
        fresh_bus.emit(PipelineEvent(event_type="test", pipeline_id="p2"))
        fresh_bus.emit(PipelineEvent(event_type="test", pipeline_id="p1"))
        assert len(fresh_bus.get_pipeline_events("p1")) == 2
        assert len(fresh_bus.get_pipeline_events("p2")) == 1

    def test_clear_pipeline_events(self, fresh_bus):
        fresh_bus.emit(PipelineEvent(event_type="test", pipeline_id="p1"))
        fresh_bus.emit(PipelineEvent(event_type="test", pipeline_id="p1"))
        fresh_bus.clear_pipeline_events("p1")
        assert len(fresh_bus.get_pipeline_events("p1")) == 0

    def test_sync_listener(self, fresh_bus):
        received = []
        listener = lambda e: received.append(e)
        fresh_bus.subscribe(listener)
        fresh_bus.emit(PipelineEvent(event_type="test", pipeline_id="p1"))
        assert len(received) == 1
        assert received[0].event_type == "test"

    def test_unsubscribe(self, fresh_bus):
        received = []
        listener = lambda e: received.append(e)
        fresh_bus.subscribe(listener)
        fresh_bus.emit(PipelineEvent(event_type="test", pipeline_id="p1"))
        fresh_bus.unsubscribe(listener)
        fresh_bus.emit(PipelineEvent(event_type="test", pipeline_id="p1"))
        assert len(received) == 1

    def test_max_log_size(self):
        bus = PipelineEventBus(max_log_size=5)
        for i in range(10):
            bus.emit(PipelineEvent(event_type="test", pipeline_id="p1"))
        assert bus.total_events == 5  # capped at 5

    def test_get_recent_events(self, fresh_bus):
        for i in range(10):
            fresh_bus.emit(PipelineEvent(
                event_type="test",
                pipeline_id=f"p{i}",
                message=f"Event {i}",
            ))
        recent = fresh_bus.get_recent_events(limit=3)
        assert len(recent) == 3
        # Should be the last 3
        assert recent[2]["pipeline_id"] == "p9"

    def test_listener_error_handled(self, fresh_bus):
        """Listener errors should not crash the bus."""
        def bad_listener(e):
            raise RuntimeError("Listener error")
        fresh_bus.subscribe(bad_listener)
        # Should not raise
        fresh_bus.emit(PipelineEvent(event_type="test", pipeline_id="p1"))

    def test_async_listener(self, fresh_bus):
        """Test async listener registration."""
        received = []
        async def async_listener(e):
            received.append(e)
        fresh_bus.subscribe_async(async_listener)
        fresh_bus.emit(PipelineEvent(event_type="test", pipeline_id="p1"))
        # Async listeners only fire if there's a running loop
        # In sync context, they just get registered


class TestEventEmitters:
    """Test the helper emit functions."""

    def test_emit_pipeline_started(self, fresh_bus):
        import app.services.pipeline_events as pe
        old_bus = pe._event_bus
        pe._event_bus = fresh_bus
        try:
            emit_pipeline_started("p1", "Add OAuth2")
            events = fresh_bus.get_pipeline_events("p1")
            assert len(events) == 1
            assert events[0]["event_type"] == "pipeline.started"
            assert "Add OAuth2" in events[0]["message"]
        finally:
            pe._event_bus = old_bus

    def test_emit_stage_started(self, fresh_bus):
        import app.services.pipeline_events as pe
        old_bus = pe._event_bus
        pe._event_bus = fresh_bus
        try:
            emit_stage_started("p1", "prd_generation", "cto_agent", 1)
            events = fresh_bus.get_pipeline_events("p1")
            assert len(events) == 1
            assert events[0]["event_type"] == "pipeline.stage_started"
            assert events[0]["stage"] == "prd_generation"
            assert events[0]["data"]["agent"] == "cto_agent"
        finally:
            pe._event_bus = old_bus

    def test_emit_stage_passed(self, fresh_bus):
        import app.services.pipeline_events as pe
        old_bus = pe._event_bus
        pe._event_bus = fresh_bus
        try:
            emit_stage_passed("p1", "qa_testing", 1500, tokens=800, score=8.5)
            events = fresh_bus.get_pipeline_events("p1")
            assert len(events) == 1
            assert events[0]["event_type"] == "pipeline.stage_passed"
            assert events[0]["data"]["duration_ms"] == 1500
            assert events[0]["data"]["score"] == 8.5
        finally:
            pe._event_bus = old_bus

    def test_emit_stage_failed(self, fresh_bus):
        import app.services.pipeline_events as pe
        old_bus = pe._event_bus
        pe._event_bus = fresh_bus
        try:
            emit_stage_failed("p1", "implementation", "Compile error", 2, True)
            events = fresh_bus.get_pipeline_events("p1")
            assert len(events) == 1
            assert events[0]["event_type"] == "pipeline.stage_failed"
            assert events[0]["data"]["will_retry"] is True
        finally:
            pe._event_bus = old_bus

    def test_emit_pipeline_completed(self, fresh_bus):
        import app.services.pipeline_events as pe
        old_bus = pe._event_bus
        pe._event_bus = fresh_bus
        try:
            emit_pipeline_completed("p1", 5000, 10, 10)
            events = fresh_bus.get_pipeline_events("p1")
            assert len(events) == 1
            assert events[0]["event_type"] == "pipeline.completed"
            assert events[0]["data"]["stages_completed"] == 10
        finally:
            pe._event_bus = old_bus

    def test_emit_pipeline_failed(self, fresh_bus):
        import app.services.pipeline_events as pe
        old_bus = pe._event_bus
        pe._event_bus = fresh_bus
        try:
            emit_pipeline_failed("p1", "security_review", "Critical vulnerability found")
            events = fresh_bus.get_pipeline_events("p1")
            assert len(events) == 1
            assert events[0]["event_type"] == "pipeline.failed"
            assert events[0]["stage"] == "security_review"
        finally:
            pe._event_bus = old_bus

    def test_emit_pipeline_cancelled(self, fresh_bus):
        import app.services.pipeline_events as pe
        old_bus = pe._event_bus
        pe._event_bus = fresh_bus
        try:
            emit_pipeline_cancelled("p1")
            events = fresh_bus.get_pipeline_events("p1")
            assert len(events) == 1
            assert events[0]["event_type"] == "pipeline.cancelled"
        finally:
            pe._event_bus = old_bus

    def test_full_pipeline_event_sequence(self, fresh_bus):
        """Test a complete pipeline event sequence."""
        import app.services.pipeline_events as pe
        old_bus = pe._event_bus
        pe._event_bus = fresh_bus
        try:
            emit_pipeline_started("p1", "Add dark mode")
            emit_stage_started("p1", "prd_generation", "cto_agent", 1)
            emit_stage_passed("p1", "prd_generation", 500)
            emit_stage_started("p1", "architecture_design", "architect_agent", 1)
            emit_stage_passed("p1", "architecture_design", 800)
            emit_pipeline_completed("p1", 1300, 2, 2)

            events = fresh_bus.get_pipeline_events("p1")
            assert len(events) == 6
            types = [e["event_type"] for e in events]
            assert types == [
                "pipeline.started",
                "pipeline.stage_started",
                "pipeline.stage_passed",
                "pipeline.stage_started",
                "pipeline.stage_passed",
                "pipeline.completed",
            ]
        finally:
            pe._event_bus = old_bus


class TestEventAPI:
    """Test the event API endpoints."""

    def test_get_pipeline_events_api(self, client, test_user):
        """Test getting events for a pipeline."""
        import app.services.pipeline_events as pe
        old_bus = pe._event_bus
        pe._event_bus = PipelineEventBus()
        try:
            emit_pipeline_started("test-p1", "Test feature")
            emit_stage_passed("test-p1", "prd_generation", 500)

            headers = test_user["headers"]
            resp = client.get("/api/v1/feature-pipeline/test-p1/events", headers=headers)
            assert resp.status_code == 200
            data = resp.json()
            assert data["count"] >= 2
        finally:
            pe._event_bus = old_bus

    def test_get_recent_events_api(self, client, test_user):
        """Test getting recent events."""
        import app.services.pipeline_events as pe
        old_bus = pe._event_bus
        pe._event_bus = PipelineEventBus()
        try:
            emit_pipeline_started("p1", "F1")
            emit_pipeline_started("p2", "F2")

            headers = test_user["headers"]
            resp = client.get("/api/v1/feature-pipeline/events/recent?limit=5", headers=headers)
            assert resp.status_code == 200
            data = resp.json()
            assert data["count"] >= 2
        finally:
            pe._event_bus = old_bus
