"""Tests for Community Engagement — Phase 53."""

import pytest
from app.services.community import (
    CommunityService, get_community_service, FeedbackType, FeedbackStatus,
    EventStatus, EventType, BadgeType,
)


class TestFeedback:
    def test_submit(self):
        s = CommunityService()
        f = s.submit_feedback("bug", "high", "Test Bug", "Test desc")
        assert f.id.startswith("fb-")
        assert f.status == "open"

    def test_list(self):
        s = CommunityService()
        items = s.list_feedback()
        assert len(items) > 0

    def test_filter_by_type(self):
        s = CommunityService()
        bugs = s.list_feedback(type="bug")
        assert all(f.type == "bug" for f in bugs)

    def test_filter_by_status(self):
        s = CommunityService()
        open_items = s.list_feedback(status="open")
        assert all(f.status == "open" for f in open_items)

    def test_get(self):
        s = CommunityService()
        items = s.list_feedback(limit=1)
        f = s.get_feedback(items[0].id)
        assert f is not None

    def test_update_status(self):
        s = CommunityService()
        items = s.list_feedback(limit=1)
        updated = s.update_feedback_status(items[0].id, "resolved", "Fixed")
        assert updated.status == "resolved"

    def test_vote(self):
        s = CommunityService()
        items = s.list_feedback(limit=1)
        before = items[0].votes
        voted = s.vote_feedback(items[0].id)
        assert voted.votes == before + 1

    def test_stats(self):
        s = CommunityService()
        stats = s.get_feedback_stats()
        assert "total" in stats
        assert stats["total"] > 0
        assert "by_type" in stats


class TestFeatureRequests:
    def test_create(self):
        s = CommunityService()
        r = s.create_feature_request("Test Feature", "Test desc")
        assert r.id.startswith("fr-")

    def test_list(self):
        s = CommunityService()
        items = s.list_feature_requests()
        assert len(items) > 0

    def test_vote(self):
        s = CommunityService()
        items = s.list_feature_requests(limit=1)
        before = items[0].votes
        voted = s.vote_feature_request(items[0].id, "0xvoter")
        assert voted.votes == before + 1

    def test_vote_twice_prevented(self):
        s = CommunityService()
        items = s.list_feature_requests(limit=1)
        s.vote_feature_request(items[0].id, "0xvoter2")
        before = s.get_feature_request(items[0].id).votes
        s.vote_feature_request(items[0].id, "0xvoter2")
        assert s.get_feature_request(items[0].id).votes == before

    def test_update_status(self):
        s = CommunityService()
        items = s.list_feature_requests(limit=1)
        updated = s.update_feature_status(items[0].id, "planned", "high")
        assert updated.status == "planned"
        assert updated.priority == "high"

    def test_add_comment(self):
        s = CommunityService()
        items = s.list_feature_requests(limit=1)
        r = s.add_comment(items[0].id, "user", "Great idea!")
        assert len(r.comments) > 0


class TestMembers:
    def test_register(self):
        s = CommunityService()
        m = s.register_member("0xnew123", "new@test.com", "NewUser")
        assert m.address == "0xnew123"

    def test_register_duplicate(self):
        s = CommunityService()
        m1 = s.register_member("0xdup", "dup@test.com", "Dup")
        m2 = s.register_member("0xdup", "dup@test.com", "Dup")
        assert m1.id == m2.id

    def test_get_member(self):
        s = CommunityService()
        s.register_member("0xget123", "get@test.com", "Getter")
        m = s.get_member("0xget123")
        assert m is not None

    def test_list_members(self):
        s = CommunityService()
        members = s.list_members()
        assert len(members) > 0

    def test_award_points(self):
        s = CommunityService()
        s.register_member("0xpts", "pts@test.com", "Pts")
        s._award_points("0xpts", 100, "test")
        m = s.get_member("0xpts")
        assert m.points == 100

    def test_award_badge(self):
        s = CommunityService()
        s.register_member("0xbadge", "badge@test.com", "Badge")
        m = s.award_badge("0xbadge", BadgeType.BUG_HUNTER.value)
        assert BadgeType.BUG_HUNTER.value in m.badges

    def test_leaderboard(self):
        s = CommunityService()
        board = s.get_leaderboard()
        assert len(board) > 0
        points = [m.points for m in board]
        assert points == sorted(points, reverse=True)


class TestEvents:
    def test_list(self):
        s = CommunityService()
        events = s.list_events()
        assert len(events) > 0

    def test_filter_by_status(self):
        s = CommunityService()
        upcoming = s.list_events(status="upcoming")
        assert all(e.status == "upcoming" for e in upcoming)

    def test_create(self):
        s = CommunityService()
        e = s.create_event("Test Event", "webinar", "Test desc")
        assert e.id.startswith("evt-")

    def test_register(self):
        s = CommunityService()
        events = s.list_events(status="upcoming", limit=1)
        e = s.register_for_event(events[0].id, "0xattendee")
        assert e.registered > 0

    def test_update_status(self):
        s = CommunityService()
        events = s.list_events(limit=1)
        updated = s.update_event_status(events[0].id, "cancelled")
        assert updated.status == "cancelled"


class TestBadges:
    def test_list(self):
        s = CommunityService()
        badges = s.list_badges()
        assert len(badges) >= 10

    def test_get(self):
        s = CommunityService()
        badges = s.list_badges()[:1]
        b = s.get_badge(badges[0].id)
        assert b is not None


class TestUsability:
    def test_list(self):
        s = CommunityService()
        metrics = s.list_usability()
        assert len(metrics) > 0

    def test_get_by_page(self):
        s = CommunityService()
        m = s.get_usability("dashboard")
        assert m is not None

    def test_update(self):
        s = CommunityService()
        m = s.update_usability("dashboard", visits=99999)
        assert m.visits == 99999

    def test_summary(self):
        s = CommunityService()
        summary = s.get_usability_summary()
        assert "total_pages" in summary
        assert "avg_satisfaction" in summary


class TestDashboard:
    def test_dashboard(self):
        s = CommunityService()
        dash = s.get_dashboard()
        assert "feedback_stats" in dash
        assert "feature_requests" in dash
        assert "total_members" in dash
        assert "usability" in dash


class TestCommunityAPI:
    def test_dashboard(self, client, test_user):
        resp = client.get("/api/v1/community/dashboard", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_list_feedback(self, client, test_user):
        resp = client.get("/api/v1/community/feedback", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_submit_feedback(self, client, test_user):
        resp = client.post("/api/v1/community/feedback", json={
            "type": "bug", "severity": "high", "title": "API Test", "description": "Test"
        }, headers=test_user["headers"])
        assert resp.status_code == 200

    def test_feedback_stats(self, client, test_user):
        resp = client.get("/api/v1/community/feedback/stats", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_list_features(self, client, test_user):
        resp = client.get("/api/v1/community/features", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_list_members(self, client, test_user):
        resp = client.get("/api/v1/community/members", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_leaderboard(self, client, test_user):
        resp = client.get("/api/v1/community/leaderboard", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_list_events(self, client, test_user):
        resp = client.get("/api/v1/community/events", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_list_badges(self, client, test_user):
        resp = client.get("/api/v1/community/badges", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_list_usability(self, client, test_user):
        resp = client.get("/api/v1/community/usability", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_usability_summary(self, client, test_user):
        resp = client.get("/api/v1/community/usability/summary", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_singleton(self):
        assert get_community_service() is get_community_service()
