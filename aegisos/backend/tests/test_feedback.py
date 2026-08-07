"""Tests for Developer Feedback System — Phase 24."""

import pytest
from app.services.feedback_system import FeedbackSystem, get_feedback_system


class TestFeedbackSystem:
    def test_submit_feedback(self):
        fs = FeedbackSystem()
        fb = fs.submit(category="bug", rating=4, title="Test bug", description="Something broke")
        assert fb.category == "bug"
        assert fb.rating == 4
        assert fb.status == "open"
        assert fb.id.startswith("fb-")

    def test_submit_invalid_rating(self):
        fs = FeedbackSystem()
        with pytest.raises(ValueError):
            fs.submit(category="bug", rating=0, title="Bad")
        with pytest.raises(ValueError):
            fs.submit(category="bug", rating=6, title="Bad")

    def test_get_feedback(self):
        fs = FeedbackSystem()
        fb = fs.submit(category="bug", rating=3, title="Get test")
        got = fs.get(fb.id)
        assert got is not None
        assert got.title == "Get test"

    def test_get_nonexistent(self):
        fs = FeedbackSystem()
        assert fs.get("nonexistent") is None

    def test_list_feedback(self):
        fs = FeedbackSystem()
        fs.submit(category="bug", rating=4, title="A")
        fs.submit(category="feature", rating=5, title="B")
        feedback = fs.list_feedback()
        assert len(feedback) == 2

    def test_list_by_category(self):
        fs = FeedbackSystem()
        fs.submit(category="bug", rating=4, title="A")
        fs.submit(category="feature", rating=5, title="B")
        bugs = fs.list_feedback(category="bug")
        assert len(bugs) == 1
        assert bugs[0].title == "A"

    def test_list_by_status(self):
        fs = FeedbackSystem()
        fb = fs.submit(category="bug", rating=3, title="A")
        fs.acknowledge(fb.id)
        open_fb = fs.list_feedback(status="open")
        ack_fb = fs.list_feedback(status="acknowledged")
        assert len(open_fb) == 0
        assert len(ack_fb) == 1

    def test_respond(self):
        fs = FeedbackSystem()
        fb = fs.submit(category="bug", rating=2, title="A")
        assert fs.respond(fb.id, "Fixed in v1.2") is True
        updated = fs.get(fb.id)
        assert updated.status == "resolved"
        assert updated.response == "Fixed in v1.2"
        assert updated.responded_at is not None

    def test_acknowledge(self):
        fs = FeedbackSystem()
        fb = fs.submit(category="bug", rating=3, title="A")
        assert fs.acknowledge(fb.id) is True
        assert fs.get(fb.id).status == "acknowledged"

    def test_dismiss(self):
        fs = FeedbackSystem()
        fb = fs.submit(category="spam", rating=1, title="A")
        assert fs.dismiss(fb.id) is True
        assert fs.get(fb.id).status == "dismissed"

    def test_get_stats(self):
        fs = FeedbackSystem()
        fs.submit(category="bug", rating=4, title="A")
        fs.submit(category="bug", rating=2, title="B")
        fs.submit(category="feature", rating=5, title="C")
        stats = fs.get_stats()
        assert stats["total"] == 3
        assert stats["avg_rating"] == round(11/3, 2)
        assert stats["open"] == 3
        assert "bug" in stats["categories"]
        assert stats["categories"]["bug"]["count"] == 2

    def test_get_stats_empty(self):
        fs = FeedbackSystem()
        stats = fs.get_stats()
        assert stats["total"] == 0

    def test_clear(self):
        fs = FeedbackSystem()
        fs.submit(category="bug", rating=3, title="A")
        fs.clear()
        assert len(fs.list_feedback()) == 0

    def test_singleton(self):
        assert get_feedback_system() is get_feedback_system()


class TestFeedbackAPI:
    def test_submit_api(self, client, test_user):
        resp = client.post("/api/v1/feedback", json={
            "category": "bug", "rating": 4, "title": "API bug",
        }, headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["category"] == "bug"

    def test_list_api(self, client, test_user):
        client.post("/api/v1/feedback", json={
            "category": "feature", "rating": 5, "title": "Great",
        }, headers=test_user["headers"])
        resp = client.get("/api/v1/feedback", headers=test_user["headers"])
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_stats_api(self, client, test_user):
        resp = client.get("/api/v1/feedback/stats", headers=test_user["headers"])
        assert resp.status_code == 200
        assert "total" in resp.json()

    def test_respond_api(self, client, test_user):
        create = client.post("/api/v1/feedback", json={
            "category": "bug", "rating": 2, "title": "Fix me",
        }, headers=test_user["headers"])
        fb_id = create.json()["id"]
        resp = client.post(f"/api/v1/feedback/{fb_id}/respond", json={
            "response": "Fixed!", "status": "resolved",
        }, headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["responded"] is True

    def test_acknowledge_api(self, client, test_user):
        create = client.post("/api/v1/feedback", json={
            "category": "bug", "rating": 3, "title": "Ack me",
        }, headers=test_user["headers"])
        fb_id = create.json()["id"]
        resp = client.post(f"/api/v1/feedback/{fb_id}/acknowledge", headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["acknowledged"] is True
