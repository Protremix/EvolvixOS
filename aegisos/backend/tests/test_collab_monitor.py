"""Tests for Agent Collaboration + Real-Time Monitoring — Phase 18."""

import pytest
from app.services.agent_collaboration import (
    AgentCollaborationService, CollaborationSession, CollaborationStep,
    COLLAB_PATTERNS, get_collaboration_service,
)
from app.services.realtime_monitor import (
    RealtimeMonitor, LiveEvent, get_realtime_monitor,
)


class TestCollaborationPatterns:
    def test_patterns_exist(self):
        assert len(COLLAB_PATTERNS) == 6
        assert "review_then_fix" in COLLAB_PATTERNS
        assert "audit_then_document" in COLLAB_PATTERNS
        assert "parallel_review" in COLLAB_PATTERNS
        assert "sequential_pipeline" in COLLAB_PATTERNS
        assert "security_deep_dive" in COLLAB_PATTERNS
        assert "feature_lifecycle" in COLLAB_PATTERNS

    def test_pattern_structure(self):
        for key, pat in COLLAB_PATTERNS.items():
            assert "name" in pat
            assert "description" in pat
            assert "agents" in pat
            assert "steps" in pat
            assert len(pat["agents"]) >= 2
            assert len(pat["steps"]) >= 2

    def test_parallel_review_has_no_deps(self):
        pat = COLLAB_PATTERNS["parallel_review"]
        for step in pat["steps"]:
            assert step["depends_on"] == []

    def test_sequential_pipeline_has_chained_deps(self):
        pat = COLLAB_PATTERNS["sequential_pipeline"]
        assert pat["steps"][1]["depends_on"] == ["step_1"]
        assert pat["steps"][2]["depends_on"] == ["step_2"]

    def test_feature_lifecycle_has_parallel_steps(self):
        pat = COLLAB_PATTERNS["feature_lifecycle"]
        # Steps 3,4,5 (QA, Security, Docs) all depend on step_2 (Architect)
        assert pat["steps"][2]["depends_on"] == ["step_2"]
        assert pat["steps"][3]["depends_on"] == ["step_2"]
        assert pat["steps"][4]["depends_on"] == ["step_2"]
        # Step 6 (Reviewer) depends on 3,4,5
        assert set(pat["steps"][5]["depends_on"]) == {"step_3", "step_4", "step_5"}


class TestCollaborationService:
    def test_list_patterns(self):
        svc = AgentCollaborationService()
        patterns = svc.list_patterns()
        assert len(patterns) == 6
        assert "key" in patterns[0]
        assert "name" in patterns[0]

    def test_get_pattern(self):
        svc = AgentCollaborationService()
        pat = svc.get_pattern("review_then_fix")
        assert pat is not None
        assert pat["name"] == "Review then Fix"

    def test_get_nonexistent_pattern(self):
        svc = AgentCollaborationService()
        assert svc.get_pattern("nonexistent") is None

    def test_create_session_from_pattern(self):
        svc = AgentCollaborationService()
        session = svc.create_session(
            name="Test Session", pattern="review_then_fix",
        )
        assert session.name == "Test Session"
        assert session.pattern == "review_then_fix"
        assert len(session.steps) == 2
        assert session.steps[0].agent_name == "reviewer_agent"
        assert session.steps[1].agent_name == "ci_healer_agent"
        assert session.status == "pending"

    def test_create_session_custom_steps(self):
        svc = AgentCollaborationService()
        session = svc.create_session(
            name="Custom", pattern="custom",
            custom_steps=[
                {"agent_name": "cto_agent", "task_type": "architecture_review", "depends_on": []},
                {"agent_name": "qa_agent", "task_type": "quality_gate", "depends_on": ["step_1"]},
            ],
        )
        assert len(session.steps) == 2
        assert session.steps[1].depends_on == ["step_1"]

    def test_get_session(self):
        svc = AgentCollaborationService()
        session = svc.create_session(name="Test", pattern="parallel_review")
        got = svc.get_session(session.id)
        assert got is not None
        assert got.name == "Test"

    def test_list_sessions(self):
        svc = AgentCollaborationService()
        svc.create_session(name="S1", pattern="review_then_fix")
        svc.create_session(name="S2", pattern="audit_then_document")
        sessions = svc.list_sessions()
        assert len(sessions) >= 2

    def test_list_sessions_by_status(self):
        svc = AgentCollaborationService()
        s = svc.create_session(name="Test", pattern="review_then_fix")
        pending = svc.list_sessions(status="pending")
        assert len(pending) >= 1

    def test_update_step(self):
        svc = AgentCollaborationService()
        session = svc.create_session(name="Test", pattern="review_then_fix")
        step_id = session.steps[0].id
        result = svc.update_step(
            session.id, step_id, "completed",
            output_data={"summary": "Done"},
            score=8.5, verdict="GO",
            findings=[{"severity": "Low", "description": "Minor issue"}],
            recommendations=["Fix minor issue"],
        )
        assert result is True
        updated = svc.get_session(session.id)
        assert updated.steps[0].status == "completed"
        assert updated.steps[0].score == 8.5
        assert updated.steps[0].verdict == "GO"

    def test_update_nonexistent_step(self):
        svc = AgentCollaborationService()
        assert svc.update_step("nonexistent", "nonexistent", "completed") is False

    def test_session_completes_when_all_steps_done(self):
        svc = AgentCollaborationService()
        session = svc.create_session(name="Test", pattern="review_then_fix")
        svc.update_step(session.id, session.steps[0].id, "completed", score=8.0, verdict="GO")
        svc.update_step(session.id, session.steps[1].id, "completed", score=9.0, verdict="GO")
        updated = svc.get_session(session.id)
        assert updated.status == "completed"
        assert updated.final_result["avg_score"] == 8.5
        assert updated.final_result["overall_verdict"] == "GO"

    def test_session_fails_if_step_fails(self):
        svc = AgentCollaborationService()
        session = svc.create_session(name="Test", pattern="review_then_fix")
        svc.update_step(session.id, session.steps[0].id, "completed", score=8.0, verdict="GO")
        svc.update_step(session.id, session.steps[1].id, "failed")
        updated = svc.get_session(session.id)
        assert updated.status == "completed"
        assert updated.final_result["overall_verdict"] == "NO-GO"

    def test_get_step_context(self):
        svc = AgentCollaborationService()
        session = svc.create_session(name="Test", pattern="review_then_fix")
        svc.update_step(session.id, session.steps[0].id, "completed",
                        output_data={"summary": "Review done"}, score=8.5)
        context = svc.get_step_context(session.id, session.steps[1].id)
        assert len(context) == 1
        dep_id = session.steps[0].id
        assert dep_id in context
        assert context[dep_id]["output"]["summary"] == "Review done"

    def test_simulate_session(self):
        svc = AgentCollaborationService()
        session = svc.create_session(name="Test Sim", pattern="review_then_fix")
        result = svc.simulate_session(session.id)
        assert result["status"] == "completed"
        assert len(result["steps"]) == 2
        assert "final_result" in result

    def test_get_stats(self):
        svc = AgentCollaborationService()
        svc.create_session(name="T1", pattern="review_then_fix")
        stats = svc.get_stats()
        assert "total_sessions" in stats
        assert "patterns_available" in stats
        assert stats["patterns_available"] == 6

    def test_singleton(self):
        assert get_collaboration_service() is get_collaboration_service()


class TestRealtimeMonitor:
    def test_emit_event(self):
        mon = RealtimeMonitor()
        event = mon.emit("agent_started", "cto_agent", "CTO started task", {"task": "review"})
        assert event.type == "agent_started"
        assert event.source == "cto_agent"
        assert event.severity == "info"

    def test_get_events(self):
        mon = RealtimeMonitor()
        mon.emit("agent_started", "cto", "Task 1")
        mon.emit("agent_completed", "cto", "Task 1 done", severity="success")
        events = mon.get_events(limit=10)
        assert len(events) == 2
        assert events[0]["type"] == "agent_completed"

    def test_filter_events_by_type(self):
        mon = RealtimeMonitor()
        mon.emit("agent_started", "cto", "T1")
        mon.emit("agent_completed", "cto", "T1", severity="success")
        started = mon.get_events(event_type="agent_started")
        assert len(started) == 1
        assert started[0]["type"] == "agent_started"

    def test_filter_events_by_source(self):
        mon = RealtimeMonitor()
        mon.emit("agent_started", "cto", "T1")
        mon.emit("agent_started", "security", "T2")
        cto_events = mon.get_events(source="cto")
        assert len(cto_events) == 1

    def test_system_stats(self):
        mon = RealtimeMonitor()
        mon.emit("agent_started", "cto", "Task")
        stats = mon.get_system_stats()
        assert "tasks_running" in stats
        assert "tasks_completed" in stats
        assert "events_buffered" in stats

    def test_live_feed(self):
        mon = RealtimeMonitor()
        mon.emit("agent_started", "cto", "Task")
        feed = mon.get_live_feed(limit=10)
        assert "events" in feed
        assert "stats" in feed
        assert len(feed["events"]) == 1

    def test_record_metric(self):
        mon = RealtimeMonitor()
        mon.record_metric("latency_ms", 150.5, "ms")
        metrics = mon.get_metrics()
        assert len(metrics) == 1
        assert metrics[0]["value"] == 150.5

    def test_filter_metrics_by_name(self):
        mon = RealtimeMonitor()
        mon.record_metric("latency_ms", 100)
        mon.record_metric("tokens", 500)
        latency = mon.get_metrics(name="latency_ms")
        assert len(latency) == 1

    def test_event_types(self):
        mon = RealtimeMonitor()
        types = mon.get_event_types()
        assert "agent_started" in types
        assert "collaboration_started" in types
        assert len(types) >= 15

    def test_subscriber(self):
        mon = RealtimeMonitor()
        received = []
        mon.add_subscriber(lambda et, data: received.append((et, data)))
        mon.emit("agent_started", "cto", "Task")
        assert len(received) == 1
        assert received[0][0] == "agent_started"

    def test_singleton(self):
        assert get_realtime_monitor() is get_realtime_monitor()


class TestCollabMonitorAPI:
    def test_list_patterns_api(self, client, test_user):
        resp = client.get("/api/v1/collab-monitor/patterns", headers=test_user["headers"])
        assert resp.status_code == 200
        assert len(resp.json()) == 6

    def test_get_pattern_api(self, client, test_user):
        resp = client.get("/api/v1/collab-monitor/patterns/review_then_fix", headers=test_user["headers"])
        assert resp.status_code == 200
        assert "Review then Fix" in resp.json()["name"]

    def test_create_session_api(self, client, test_user):
        resp = client.post("/api/v1/collab-monitor/sessions", json={
            "name": "API Test", "pattern": "parallel_review",
        }, headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["name"] == "API Test"
        assert len(resp.json()["steps"]) == 3

    def test_list_sessions_api(self, client, test_user):
        client.post("/api/v1/collab-monitor/sessions", json={
            "name": "Test", "pattern": "review_then_fix",
        }, headers=test_user["headers"])
        resp = client.get("/api/v1/collab-monitor/sessions", headers=test_user["headers"])
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_get_session_api(self, client, test_user):
        create = client.post("/api/v1/collab-monitor/sessions", json={
            "name": "Test", "pattern": "review_then_fix",
        }, headers=test_user["headers"])
        sid = create.json()["id"]
        resp = client.get(f"/api/v1/collab-monitor/sessions/{sid}", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_update_step_api(self, client, test_user):
        create = client.post("/api/v1/collab-monitor/sessions", json={
            "name": "Test", "pattern": "review_then_fix",
        }, headers=test_user["headers"])
        sid = create.json()["id"]
        step_id = create.json()["steps"][0]["id"]
        resp = client.put(f"/api/v1/collab-monitor/sessions/{sid}/steps/{step_id}", json={
            "status": "completed", "score": 8.5, "verdict": "GO",
        }, headers=test_user["headers"])
        assert resp.status_code == 200

    def test_simulate_session_api(self, client, test_user):
        create = client.post("/api/v1/collab-monitor/sessions", json={
            "name": "Sim Test", "pattern": "review_then_fix",
        }, headers=test_user["headers"])
        sid = create.json()["id"]
        resp = client.post(f"/api/v1/collab-monitor/sessions/{sid}/simulate", headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["status"] == "completed"

    def test_collab_stats_api(self, client, test_user):
        resp = client.get("/api/v1/collab-monitor/stats", headers=test_user["headers"])
        assert resp.status_code == 200
        assert "patterns_available" in resp.json()

    def test_get_events_api(self, client, test_user):
        resp = client.get("/api/v1/collab-monitor/events", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_emit_event_api(self, client, test_user):
        resp = client.post("/api/v1/collab-monitor/events", json={
            "type": "agent_started", "source": "cto_agent",
            "message": "Test event", "severity": "info",
        }, headers=test_user["headers"])
        assert resp.status_code == 200

    def test_live_feed_api(self, client, test_user):
        resp = client.get("/api/v1/collab-monitor/events/feed", headers=test_user["headers"])
        assert resp.status_code == 200
        assert "events" in resp.json()
        assert "stats" in resp.json()

    def test_event_types_api(self, client, test_user):
        resp = client.get("/api/v1/collab-monitor/events/types", headers=test_user["headers"])
        assert resp.status_code == 200
        assert len(resp.json()) >= 15

    def test_system_stats_api(self, client, test_user):
        resp = client.get("/api/v1/collab-monitor/system-stats", headers=test_user["headers"])
        assert resp.status_code == 200
        assert "tasks_running" in resp.json()

    def test_metrics_api(self, client, test_user):
        client.post("/api/v1/collab-monitor/metrics?name=latency_ms&value=150.5&unit=ms", headers=test_user["headers"])
        resp = client.get("/api/v1/collab-monitor/metrics", headers=test_user["headers"])
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_step_context_api(self, client, test_user):
        create = client.post("/api/v1/collab-monitor/sessions", json={
            "name": "Context Test", "pattern": "review_then_fix",
        }, headers=test_user["headers"])
        sid = create.json()["id"]
        step1_id = create.json()["steps"][0]["id"]
        step2_id = create.json()["steps"][1]["id"]
        client.put(f"/api/v1/collab-monitor/sessions/{sid}/steps/{step1_id}", json={
            "status": "completed", "score": 8.0, "verdict": "GO",
        }, headers=test_user["headers"])
        resp = client.get(f"/api/v1/collab-monitor/sessions/{sid}/steps/{step2_id}/context", headers=test_user["headers"])
        assert resp.status_code == 200
