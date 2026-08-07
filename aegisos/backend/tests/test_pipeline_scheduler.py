"""Tests for Pipeline Scheduler — Post-MVP Phase 5."""

import pytest
from datetime import datetime, timedelta
from app.services.pipeline_scheduler import (
    ScheduledPipeline, PipelineScheduler, get_scheduler,
    _compute_next_run, _parse_iso,
)


class TestNextRunComputation:
    def test_daily_schedule(self):
        sched = ScheduledPipeline(schedule="daily", time="09:00", enabled=True)
        next_run = _compute_next_run(sched)
        assert next_run is not None
        parsed = _parse_iso(next_run)
        assert parsed is not None
        assert parsed.hour == 9
        assert parsed.minute == 0
        assert parsed > datetime.utcnow()

    def test_daily_schedule_past_time(self):
        """If 09:00 has already passed today, next run is tomorrow."""
        past_time = (datetime.utcnow() - timedelta(hours=2)).strftime("%H:%M")
        sched = ScheduledPipeline(schedule="daily", time=past_time, enabled=True)
        next_run = _compute_next_run(sched)
        parsed = _parse_iso(next_run)
        assert parsed > datetime.utcnow()

    def test_weekly_schedule(self):
        sched = ScheduledPipeline(schedule="weekly", time="09:00", day_of_week=0, enabled=True)
        next_run = _compute_next_run(sched)
        parsed = _parse_iso(next_run)
        assert parsed is not None
        assert parsed > datetime.utcnow()
        # Should be a Monday
        assert parsed.weekday() == 0

    def test_monthly_schedule(self):
        sched = ScheduledPipeline(schedule="monthly", time="09:00", day_of_month=15, enabled=True)
        next_run = _compute_next_run(sched)
        parsed = _parse_iso(next_run)
        assert parsed is not None
        assert parsed > datetime.utcnow()

    def test_disabled_schedule_no_next_run(self):
        sched = ScheduledPipeline(schedule="daily", time="09:00", enabled=False)
        assert _compute_next_run(sched) is None

    def test_max_runs_reached(self):
        sched = ScheduledPipeline(schedule="daily", time="09:00", enabled=True, max_runs=3, run_count=3)
        assert _compute_next_run(sched) is None

    def test_invalid_time_format(self):
        sched = ScheduledPipeline(schedule="daily", time="invalid", enabled=True)
        next_run = _compute_next_run(sched)
        # Should fall back to 09:00
        parsed = _parse_iso(next_run)
        assert parsed.hour == 9


class TestSchedulerCRUD:
    def test_create_schedule(self):
        scheduler = PipelineScheduler()
        sched = ScheduledPipeline(name="Test", template_id="bugfix", title="test", schedule="daily")
        result = scheduler.create_schedule(sched)
        assert result.id is not None
        assert result.next_run is not None

    def test_get_schedule(self):
        scheduler = PipelineScheduler()
        sched = ScheduledPipeline(name="Test Get", template_id="bugfix", title="test")
        scheduler.create_schedule(sched)
        retrieved = scheduler.get_schedule(sched.id)
        assert retrieved is not None
        assert retrieved.name == "Test Get"

    def test_get_nonexistent(self):
        scheduler = PipelineScheduler()
        assert scheduler.get_schedule("nonexistent") is None

    def test_list_schedules(self):
        scheduler = PipelineScheduler()
        for i in range(3):
            scheduler.create_schedule(ScheduledPipeline(name=f"Test {i}"))
        schedules = scheduler.list_schedules()
        assert len(schedules) == 3

    def test_list_enabled_only(self):
        scheduler = PipelineScheduler()
        s1 = scheduler.create_schedule(ScheduledPipeline(name="Enabled", enabled=True))
        s2 = scheduler.create_schedule(ScheduledPipeline(name="Disabled", enabled=False))
        enabled = scheduler.list_schedules(enabled_only=True)
        assert len(enabled) == 1
        assert enabled[0].name == "Enabled"

    def test_update_schedule(self):
        scheduler = PipelineScheduler()
        sched = scheduler.create_schedule(ScheduledPipeline(name="Test", title="old"))
        updated = scheduler.update_schedule(sched.id, {"title": "new title"})
        assert updated.title == "new title"

    def test_delete_schedule(self):
        scheduler = PipelineScheduler()
        sched = scheduler.create_schedule(ScheduledPipeline(name="Delete Me"))
        assert scheduler.delete_schedule(sched.id) is True
        assert scheduler.get_schedule(sched.id) is None

    def test_delete_nonexistent(self):
        scheduler = PipelineScheduler()
        assert scheduler.delete_schedule("nonexistent") is False

    def test_enable_schedule(self):
        scheduler = PipelineScheduler()
        sched = scheduler.create_schedule(ScheduledPipeline(name="Test", enabled=False))
        enabled = scheduler.enable_schedule(sched.id)
        assert enabled.enabled is True
        assert enabled.next_run is not None

    def test_disable_schedule(self):
        scheduler = PipelineScheduler()
        sched = scheduler.create_schedule(ScheduledPipeline(name="Test", enabled=True))
        disabled = scheduler.disable_schedule(sched.id)
        assert disabled.enabled is False
        assert disabled.next_run is None

    def test_get_upcoming(self):
        scheduler = PipelineScheduler()
        for i in range(5):
            scheduler.create_schedule(ScheduledPipeline(name=f"Test {i}"))
        upcoming = scheduler.get_upcoming(limit=3)
        assert len(upcoming) == 3
        # Should be sorted by next_run
        assert upcoming[0].next_run <= upcoming[1].next_run


class TestSchedulerTrigger:
    def test_trigger_fires_callback(self):
        scheduler = PipelineScheduler()
        triggered = []
        
        def callback(sched):
            triggered.append(sched.name)
        
        scheduler.set_trigger_callback(callback)
        
        # Create a schedule with next_run in the past
        sched = ScheduledPipeline(name="Past Due", template_id="bugfix", title="test", schedule="daily")
        sched = scheduler.create_schedule(sched)
        # Manually set next_run to past
        sched.next_run = (datetime.utcnow() - timedelta(hours=1)).isoformat()
        
        result = scheduler.check_and_trigger()
        assert len(result) == 1
        assert len(triggered) == 1
        assert triggered[0] == "Past Due"
        # run_count should increment
        assert sched.run_count == 1
        # last_run should be set
        assert sched.last_run is not None
        # next_run should be recomputed (future)
        assert _parse_iso(sched.next_run) > datetime.utcnow()

    def test_disabled_not_triggered(self):
        scheduler = PipelineScheduler()
        sched = scheduler.create_schedule(ScheduledPipeline(name="Disabled", enabled=False))
        sched.next_run = (datetime.utcnow() - timedelta(hours=1)).isoformat()
        
        result = scheduler.check_and_trigger()
        assert len(result) == 0

    def test_max_runs_not_triggered(self):
        scheduler = PipelineScheduler()
        sched = scheduler.create_schedule(
            ScheduledPipeline(name="Maxed", enabled=True, max_runs=2, run_count=2)
        )
        sched.next_run = (datetime.utcnow() - timedelta(hours=1)).isoformat()
        
        result = scheduler.check_and_trigger()
        assert len(result) == 0

    def test_future_not_triggered(self):
        scheduler = PipelineScheduler()
        sched = scheduler.create_schedule(ScheduledPipeline(name="Future", enabled=True))
        # next_run is already in the future
        
        result = scheduler.check_and_trigger()
        assert len(result) == 0

    def test_callback_exception_handled(self):
        """If callback raises, schedule still updates."""
        scheduler = PipelineScheduler()
        
        def bad_callback(sched):
            raise ValueError("Boom!")
        
        scheduler.set_trigger_callback(bad_callback)
        
        sched = scheduler.create_schedule(ScheduledPipeline(name="Bad Callback", enabled=True))
        sched.next_run = (datetime.utcnow() - timedelta(hours=1)).isoformat()
        
        # Should not raise
        result = scheduler.check_and_trigger()
        assert len(result) == 1
        # Schedule should still be updated
        assert sched.run_count == 1


class TestSchedulerAPI:
    def test_list_schedules_api(self, client, test_user):
        headers = test_user["headers"]
        resp = client.get("/api/v1/pipeline-scheduler/", headers=headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_create_schedule_api(self, client, test_user):
        headers = test_user["headers"]
        resp = client.post("/api/v1/pipeline-scheduler/", json={
            "name": "Daily Bugfix Check",
            "template_id": "bugfix",
            "title": "automated scan",
            "description": "Daily bug scan",
            "schedule": "daily",
            "time": "09:00",
        }, headers=headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Daily Bugfix Check"
        assert data["next_run"] is not None

    def test_get_schedule_api(self, client, test_user):
        headers = test_user["headers"]
        # Create first
        create = client.post("/api/v1/pipeline-scheduler/", json={
            "name": "Get Test",
            "template_id": "bugfix",
            "title": "test",
        }, headers=headers)
        sched_id = create.json()["id"]
        
        resp = client.get(f"/api/v1/pipeline-scheduler/{sched_id}", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == sched_id

    def test_update_schedule_api(self, client, test_user):
        headers = test_user["headers"]
        create = client.post("/api/v1/pipeline-scheduler/", json={
            "name": "Update Test",
            "template_id": "bugfix",
            "title": "original",
        }, headers=headers)
        sched_id = create.json()["id"]
        
        resp = client.patch(f"/api/v1/pipeline-scheduler/{sched_id}", json={"title": "updated"}, headers=headers)
        assert resp.status_code == 200
        assert resp.json()["title"] == "updated"

    def test_delete_schedule_api(self, client, test_user):
        headers = test_user["headers"]
        create = client.post("/api/v1/pipeline-scheduler/", json={
            "name": "Delete Test",
            "template_id": "bugfix",
            "title": "test",
        }, headers=headers)
        sched_id = create.json()["id"]
        
        resp = client.delete(f"/api/v1/pipeline-scheduler/{sched_id}", headers=headers)
        assert resp.status_code == 204

    def test_enable_disable_api(self, client, test_user):
        headers = test_user["headers"]
        create = client.post("/api/v1/pipeline-scheduler/", json={
            "name": "Enable Test",
            "template_id": "bugfix",
            "title": "test",
            "enabled": True,
        }, headers=headers)
        sched_id = create.json()["id"]
        
        # Disable
        resp = client.post(f"/api/v1/pipeline-scheduler/{sched_id}/disable", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["enabled"] is False
        
        # Enable
        resp = client.post(f"/api/v1/pipeline-scheduler/{sched_id}/enable", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["enabled"] is True

    def test_check_trigger_api(self, client, test_user):
        headers = test_user["headers"]
        resp = client.post("/api/v1/pipeline-scheduler/check", headers=headers)
        assert resp.status_code == 200
        assert "triggered_count" in resp.json()

    def test_upcoming_api(self, client, test_user):
        headers = test_user["headers"]
        resp = client.get("/api/v1/pipeline-scheduler/upcoming/list", headers=headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_get_nonexistent_schedule(self, client, test_user):
        headers = test_user["headers"]
        resp = client.get("/api/v1/pipeline-scheduler/nonexistent", headers=headers)
        assert resp.status_code == 404
