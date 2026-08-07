"""Tests for Activity Log — Post-MVP Phase 7."""

import pytest
from datetime import datetime, timedelta
from app.services.activity_log import (
    ActivityLog, ActivityEntry, get_activity_log, log_activity,
)


class TestActivityLog:
    def test_log_entry(self):
        log = ActivityLog()
        entry = log.log(action="user.login", user_id="u1", entity_type="user")
        assert entry.id is not None
        assert entry.action == "user.login"
        assert entry.user_id == "u1"
        assert len(log._entries) == 1

    def test_get_entry(self):
        log = ActivityLog()
        entry = log.log(action="project.created", entity_id="p1")
        retrieved = log.get(entry.id)
        assert retrieved is not None
        assert retrieved.action == "project.created"

    def test_get_nonexistent(self):
        log = ActivityLog()
        assert log.get("nonexistent") is None

    def test_list_no_filters(self):
        log = ActivityLog()
        for i in range(5):
            log.log(action=f"action.{i}")
        entries = log.list()
        assert len(entries) == 5
        # Newest first
        assert entries[0].action == "action.4"

    def test_filter_by_action(self):
        log = ActivityLog()
        log.log(action="user.login", user_id="u1")
        log.log(action="project.created", user_id="u1")
        entries = log.list(action="user.login")
        assert len(entries) == 1
        assert entries[0].action == "user.login"

    def test_filter_by_user(self):
        log = ActivityLog()
        log.log(action="test", user_id="u1")
        log.log(action="test", user_id="u2")
        entries = log.list(user_id="u1")
        assert all(e.user_id == "u1" for e in entries)

    def test_filter_by_entity_type(self):
        log = ActivityLog()
        log.log(action="test", entity_type="project")
        log.log(action="test", entity_type="task")
        entries = log.list(entity_type="project")
        assert all(e.entity_type == "project" for e in entries)

    def test_filter_by_entity_id(self):
        log = ActivityLog()
        log.log(action="test", entity_type="project", entity_id="p1")
        log.log(action="test", entity_type="project", entity_id="p2")
        entries = log.list(entity_id="p1")
        assert len(entries) == 1

    def test_filter_by_severity(self):
        log = ActivityLog()
        log.log(action="ok", severity="info")
        log.log(action="bad", severity="error")
        entries = log.list(severity="error")
        assert len(entries) == 1
        assert entries[0].action == "bad"

    def test_filter_by_date_range(self):
        log = ActivityLog()
        old = (datetime.utcnow() - timedelta(days=10)).isoformat()
        entry = log.log(action="old")
        entry.timestamp = old
        entry2 = log.log(action="recent")
        entries = log.list(since=(datetime.utcnow() - timedelta(days=1)).isoformat())
        assert all(e.action == "recent" for e in entries)

    def test_limit_and_offset(self):
        log = ActivityLog()
        for i in range(10):
            log.log(action=f"action.{i}")
        entries = log.list(limit=3, offset=2)
        assert len(entries) == 3

    def test_search(self):
        log = ActivityLog()
        log.log(action="project.created", entity_name="My Awesome Project")
        log.log(action="user.login", user_email="test@example.com")
        results = log.search("Awesome")
        assert len(results) == 1
        assert "Awesome" in results[0].entity_name

    def test_search_no_results(self):
        log = ActivityLog()
        log.log(action="test")
        results = log.search("nonexistent_xyz")
        assert len(results) == 0

    def test_get_stats(self):
        log = ActivityLog()
        log.log(action="user.login", entity_type="user")
        log.log(action="project.created", entity_type="project")
        log.log(action="user.login", entity_type="user", severity="error")
        stats = log.get_stats()
        assert stats["total_entries"] == 3
        assert stats["actions"]["user.login"] == 2
        assert stats["entities"]["user"] == 2
        assert stats["severities"]["error"] == 1

    def test_get_user_activity(self):
        log = ActivityLog()
        log.log(action="a1", user_id="u1")
        log.log(action="a2", user_id="u2")
        log.log(action="a3", user_id="u1")
        activity = log.get_user_activity("u1")
        assert all(e.user_id == "u1" for e in activity)
        assert len(activity) == 2

    def test_get_recent_errors(self):
        log = ActivityLog()
        log.log(action="ok", severity="info")
        log.log(action="err1", severity="error")
        log.log(action="err2", severity="error")
        errors = log.get_recent_errors()
        assert len(errors) == 2
        assert all(e.severity == "error" for e in errors)

    def test_max_entries_ring_buffer(self):
        log = ActivityLog(max_entries=3)
        for i in range(5):
            log.log(action=f"action.{i}")
        assert len(log._entries) == 3
        # First 2 entries should be gone
        assert log._entries[0].action == "action.2"

    def test_cleanup_old(self):
        log = ActivityLog()
        old_entry = log.log(action="old")
        old_entry.timestamp = (datetime.utcnow() - timedelta(days=100)).isoformat()
        log.log(action="new")
        removed = log.cleanup_old(max_age_days=30)
        assert removed == 1
        assert len(log._entries) == 1

    def test_cleanup_no_old_entries(self):
        log = ActivityLog()
        log.log(action="recent")
        removed = log.cleanup_old(max_age_days=90)
        assert removed == 0

    def test_log_activity_convenience(self):
        log = get_activity_log()
        initial = len(log._entries)
        log_activity(action="test.convenience", user_id="u1")
        assert len(log._entries) > initial

    def test_entry_to_dict(self):
        entry = ActivityEntry(action="test", user_id="u1", entity_type="project")
        d = entry.to_dict()
        assert d["action"] == "test"
        assert d["user_id"] == "u1"
        assert d["entity_type"] == "project"


class TestActivityLogAPI:
    def test_list_api(self, client, test_user):
        resp = client.get("/api/v1/activity-log/", headers=test_user["headers"])
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_search_api(self, client, test_user):
        # Log an entry first
        client.post("/api/v1/activity-log/", json={
            "action": "test.searchable",
            "entity_name": "Searchable Project",
        }, headers=test_user["headers"])
        resp = client.get("/api/v1/activity-log/search?q=Searchable", headers=test_user["headers"])
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_search_empty_query(self, client, test_user):
        resp = client.get("/api/v1/activity-log/search?q=", headers=test_user["headers"])
        assert resp.status_code == 400

    def test_stats_api(self, client, test_user):
        resp = client.get("/api/v1/activity-log/stats", headers=test_user["headers"])
        assert resp.status_code == 200
        assert "total_entries" in resp.json()

    def test_create_entry_api(self, client, test_user):
        resp = client.post("/api/v1/activity-log/", json={
            "action": "test.manual",
            "entity_type": "test",
        }, headers=test_user["headers"])
        assert resp.status_code == 201
        assert resp.json()["action"] == "test.manual"

    def test_filter_by_action_api(self, client, test_user):
        client.post("/api/v1/activity-log/", json={"action": "test.filter_action"}, headers=test_user["headers"])
        resp = client.get("/api/v1/activity-log/?action=test.filter_action", headers=test_user["headers"])
        assert resp.status_code == 200
        assert all(e["action"] == "test.filter_action" for e in resp.json())

    def test_recent_errors_api(self, client, test_user):
        client.post("/api/v1/activity-log/", json={
            "action": "test.error", "severity": "error",
        }, headers=test_user["headers"])
        resp = client.get("/api/v1/activity-log/errors/recent", headers=test_user["headers"])
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_cleanup_api(self, client, test_user):
        resp = client.post("/api/v1/activity-log/cleanup?max_age_days=365", headers=test_user["headers"])
        assert resp.status_code == 200
        assert "removed" in resp.json()
