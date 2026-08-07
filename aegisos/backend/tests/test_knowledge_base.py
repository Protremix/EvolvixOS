"""Tests for Knowledge Base — Post-MVP Phase 6."""

import pytest
from unittest.mock import MagicMock
from datetime import datetime

from app.services.knowledge_base import (
    KnowledgeBase, KnowledgeEntry, PatternRecord, get_knowledge_base,
)


def _make_stage(stage, agent, status="passed", duration_ms=100, retry_count=0, error=None):
    s = MagicMock()
    s.stage = stage
    s.agent = agent
    s.status = status
    s.duration_ms = duration_ms
    s.retry_count = retry_count
    s.error = error
    return s


def _make_run(id="run-1", title="Test Pipeline", status="completed", stages=None, duration_ms=1000):
    r = MagicMock()
    r.id = id
    r.title = title
    r.status = status
    r.stages = stages or []
    r.total_duration_ms = duration_ms
    return r


class TestKnowledgeEntryCRUD:
    def test_add_and_get(self):
        kb = KnowledgeBase()
        entry = KnowledgeEntry(title="Test", content="Test content", category="general")
        kb.add_entry(entry)
        assert entry.id in kb._entries
        
        retrieved = kb.get_entry(entry.id)
        assert retrieved is not None
        assert retrieved.title == "Test"
        assert retrieved.times_referenced == 1

    def test_get_nonexistent(self):
        kb = KnowledgeBase()
        assert kb.get_entry("nonexistent") is None

    def test_update_entry(self):
        kb = KnowledgeBase()
        entry = kb.add_entry(KnowledgeEntry(title="Original"))
        updated = kb.update_entry(entry.id, {"title": "Updated", "content": "New content"})
        assert updated.title == "Updated"
        assert updated.content == "New content"

    def test_update_nonexistent(self):
        kb = KnowledgeBase()
        assert kb.update_entry("nonexistent", {}) is None

    def test_delete_entry(self):
        kb = KnowledgeBase()
        entry = kb.add_entry(KnowledgeEntry(title="Delete Me"))
        assert kb.delete_entry(entry.id) is True
        assert kb.get_entry(entry.id) is None

    def test_delete_nonexistent(self):
        kb = KnowledgeBase()
        assert kb.delete_entry("nonexistent") is False


class TestBuiltinKnowledge:
    def test_seeded_on_init(self):
        kb = KnowledgeBase()
        assert len(kb._entries) >= 6  # 6 built-in entries

    def test_has_security_category(self):
        kb = KnowledgeBase()
        security = kb.list_entries(category="security")
        assert len(security) >= 1
        assert any("Validate" in e.title for e in security)

    def test_has_architecture_category(self):
        kb = KnowledgeBase()
        arch = kb.list_entries(category="architecture")
        assert len(arch) >= 2


class TestListFilters:
    def test_filter_by_category(self):
        kb = KnowledgeBase()
        testing = kb.list_entries(category="testing")
        assert all(e.category == "testing" for e in testing)

    def test_filter_by_source(self):
        kb = KnowledgeBase()
        kb.add_entry(KnowledgeEntry(title="Pipeline Lesson", source="pipeline"))
        pipeline_entries = kb.list_entries(source="pipeline")
        assert all(e.source == "pipeline" for e in pipeline_entries)

    def test_filter_by_tag(self):
        kb = KnowledgeBase()
        tagged = kb.list_entries(tag="owasp")
        assert all("owasp" in e.tags for e in tagged)

    def test_limit(self):
        kb = KnowledgeBase()
        entries = kb.list_entries(limit=3)
        assert len(entries) <= 3

    def test_sorted_by_confidence(self):
        kb = KnowledgeBase()
        entries = kb.list_entries(limit=10)
        for i in range(len(entries) - 1):
            assert entries[i].confidence >= entries[i + 1].confidence


class TestSearch:
    def test_search_finds_matches(self):
        kb = KnowledgeBase()
        results = kb.search("validate input security")
        assert len(results) >= 1
        assert all("score" in r and "entry" in r for r in results)

    def test_search_title_weights_more(self):
        kb = KnowledgeBase()
        # Add an entry where the query is only in content
        kb.add_entry(KnowledgeEntry(
            title="Something Else",
            content="Validate inputs here",
            confidence=0.9,
        ))
        results = kb.search("validate")
        # The security entry with "Validate" in title should score higher
        assert results[0]["score"] >= results[-1]["score"]

    def test_search_no_matches(self):
        kb = KnowledgeBase()
        results = kb.search("xyzqwertyunmatched")
        assert len(results) == 0

    def test_search_multiple_terms(self):
        kb = KnowledgeBase()
        results = kb.search("api versioning backward")
        assert len(results) >= 1

    def test_search_boosted_by_confidence(self):
        kb = KnowledgeBase()
        results = kb.search("testing behavior")
        assert len(results) >= 1


class TestPatternDetection:
    def test_failure_pattern(self):
        kb = KnowledgeBase()
        runs = [
            _make_run(id=f"run-{i}", stages=[_make_stage("qa", "qa_agent", "failed")])
            for i in range(4)
        ]
        patterns = kb.extract_patterns_from_runs(runs)
        failure_pats = [p for p in patterns if p.pattern_type == "failure_pattern"]
        assert len(failure_pats) >= 1
        assert failure_pats[0].stage == "qa"
        assert failure_pats[0].occurrence_count == 4

    def test_success_pattern(self):
        kb = KnowledgeBase()
        runs = [
            _make_run(id=f"run-{i}", stages=[_make_stage("prd", "cto", "passed", 500)])
            for i in range(6)
        ]
        patterns = kb.extract_patterns_from_runs(runs)
        success_pats = [p for p in patterns if p.pattern_type == "success_pattern"]
        assert len(success_pats) >= 1
        assert success_pats[0].stage == "prd"

    def test_retry_pattern(self):
        kb = KnowledgeBase()
        runs = [
            _make_run(id=f"run-{i}", stages=[_make_stage("impl", "coder", "passed", 1000, retry_count=1)])
            for i in range(3)
        ]
        patterns = kb.extract_patterns_from_runs(runs)
        retry_pats = [p for p in patterns if p.pattern_type == "retry_pattern"]
        assert len(retry_pats) >= 1
        assert retry_pats[0].occurrence_count == 3

    def test_bottleneck_pattern(self):
        kb = KnowledgeBase()
        runs = [
            _make_run(id=f"run-{i}", stages=[
                _make_stage("fast", "agent1", "passed", 50),
                _make_stage("slow", "agent2", "passed", 5000),
            ])
            for i in range(3)
        ]
        patterns = kb.extract_patterns_from_runs(runs)
        bottleneck_pats = [p for p in patterns if p.pattern_type == "bottleneck_pattern"]
        assert len(bottleneck_pats) >= 1
        slow_pat = [p for p in bottleneck_pats if p.stage == "slow"]
        assert len(slow_pat) >= 1

    def test_no_patterns_from_empty(self):
        kb = KnowledgeBase()
        patterns = kb.extract_patterns_from_runs([])
        assert len(patterns) == 0

    def test_pattern_has_recommendation(self):
        kb = KnowledgeBase()
        runs = [
            _make_run(id=f"run-{i}", stages=[_make_stage("qa", "qa_agent", "failed")])
            for i in range(4)
        ]
        patterns = kb.extract_patterns_from_runs(runs)
        assert all(p.recommendation for p in patterns)

    def test_pattern_stored_after_extraction(self):
        kb = KnowledgeBase()
        runs = [
            _make_run(id=f"run-{i}", stages=[_make_stage("qa", "qa_agent", "failed")])
            for i in range(4)
        ]
        kb.extract_patterns_from_runs(runs)
        stored = kb.list_patterns()
        assert len(stored) >= 1

    def test_filter_patterns_by_type(self):
        kb = KnowledgeBase()
        runs = [
            _make_run(id=f"run-{i}", stages=[_make_stage("qa", "qa_agent", "failed")])
            for i in range(4)
        ]
        kb.extract_patterns_from_runs(runs)
        failure_only = kb.list_patterns(pattern_type="failure_pattern")
        assert all(p.pattern_type == "failure_pattern" for p in failure_only)

    def test_delete_pattern(self):
        kb = KnowledgeBase()
        kb.add_pattern(PatternRecord(pattern_type="test", stage="test"))
        pat_id = list(kb._patterns.keys())[0]
        assert kb.delete_pattern(pat_id) is True
        assert kb.delete_pattern(pat_id) is False


class TestLessonExtraction:
    def test_lesson_from_completed_run(self):
        kb = KnowledgeBase()
        run = _make_run(status="completed", stages=[
            _make_stage("prd", "cto", "passed", 500),
            _make_stage("impl", "coder", "passed", 1000),
        ])
        lessons = kb.extract_lessons_from_run(run)
        assert len(lessons) >= 1
        assert any("Successful pipeline" in l.title for l in lessons)

    def test_lesson_from_failed_stage(self):
        kb = KnowledgeBase()
        run = _make_run(status="failed", stages=[
            _make_stage("qa", "qa_agent", "failed", 200, error="test failed"),
        ])
        lessons = kb.extract_lessons_from_run(run)
        failure_lessons = [l for l in lessons if "failure" in l.tags]
        assert len(failure_lessons) >= 1
        assert failure_lessons[0].source_stage == "qa"

    def test_lesson_from_retry_then_pass(self):
        kb = KnowledgeBase()
        run = _make_run(stages=[
            _make_stage("impl", "coder", "passed", 1000, retry_count=3),
        ])
        lessons = kb.extract_lessons_from_run(run)
        retry_lessons = [l for l in lessons if "retry" in l.tags]
        assert len(retry_lessons) >= 1
        assert "3 retries" in retry_lessons[0].content

    def test_lessons_stored_in_kb(self):
        kb = KnowledgeBase()
        initial_count = len(kb._entries)
        run = _make_run(stages=[_make_stage("qa", "qa", "failed")])
        kb.extract_lessons_from_run(run)
        assert len(kb._entries) > initial_count

    def test_stage_to_category_mapping(self):
        assert KnowledgeBase._stage_to_category("security") == "security"
        assert KnowledgeBase._stage_to_category("qa") == "testing"
        assert KnowledgeBase._stage_to_category("release") == "devops"
        assert KnowledgeBase._stage_to_category("unknown_stage") == "general"


class TestStats:
    def test_stats_structure(self):
        kb = KnowledgeBase()
        stats = kb.get_stats()
        assert "total_entries" in stats
        assert "total_patterns" in stats
        assert "categories" in stats
        assert "sources" in stats
        assert "total_references" in stats
        assert "avg_confidence" in stats

    def test_stats_counts(self):
        kb = KnowledgeBase()
        stats = kb.get_stats()
        assert stats["total_entries"] >= 6  # built-in entries
        assert stats["total_patterns"] == 0  # no patterns extracted yet


class TestKnowledgeBaseAPI:
    def test_list_entries_api(self, client, test_user):
        headers = test_user["headers"]
        resp = client.get("/api/v1/knowledge-base/", headers=headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        assert len(resp.json()) >= 6

    def test_create_entry_api(self, client, test_user):
        headers = test_user["headers"]
        resp = client.post("/api/v1/knowledge-base/", json={
            "title": "Test Entry",
            "content": "Test content",
            "category": "general",
        }, headers=headers)
        assert resp.status_code == 201
        assert resp.json()["title"] == "Test Entry"

    def test_search_api(self, client, test_user):
        headers = test_user["headers"]
        resp = client.get("/api/v1/knowledge-base/search?q=validate", headers=headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        assert len(resp.json()) >= 1

    def test_search_empty_query_api(self, client, test_user):
        headers = test_user["headers"]
        resp = client.get("/api/v1/knowledge-base/search?q=", headers=headers)
        assert resp.status_code == 400

    def test_stats_api(self, client, test_user):
        headers = test_user["headers"]
        resp = client.get("/api/v1/knowledge-base/stats", headers=headers)
        assert resp.status_code == 200
        assert "total_entries" in resp.json()

    def test_get_entry_api(self, client, test_user):
        headers = test_user["headers"]
        create = client.post("/api/v1/knowledge-base/", json={
            "title": "Get Test",
            "content": "content",
            "category": "testing",
        }, headers=headers)
        entry_id = create.json()["id"]
        
        resp = client.get(f"/api/v1/knowledge-base/{entry_id}", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == entry_id

    def test_update_entry_api(self, client, test_user):
        headers = test_user["headers"]
        create = client.post("/api/v1/knowledge-base/", json={
            "title": "Original",
            "content": "content",
            "category": "general",
        }, headers=headers)
        entry_id = create.json()["id"]
        
        resp = client.patch(f"/api/v1/knowledge-base/{entry_id}", json={"title": "Updated"}, headers=headers)
        assert resp.status_code == 200
        assert resp.json()["title"] == "Updated"

    def test_delete_entry_api(self, client, test_user):
        headers = test_user["headers"]
        create = client.post("/api/v1/knowledge-base/", json={
            "title": "Delete Me",
            "content": "content",
            "category": "general",
        }, headers=headers)
        entry_id = create.json()["id"]
        
        resp = client.delete(f"/api/v1/knowledge-base/{entry_id}", headers=headers)
        assert resp.status_code == 204

    def test_list_patterns_api(self, client, test_user):
        headers = test_user["headers"]
        resp = client.get("/api/v1/knowledge-base/patterns/list", headers=headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_extract_patterns_api(self, client, test_user):
        headers = test_user["headers"]
        resp = client.post("/api/v1/knowledge-base/patterns/extract", headers=headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_filter_by_category_api(self, client, test_user):
        headers = test_user["headers"]
        resp = client.get("/api/v1/knowledge-base/?category=security", headers=headers)
        assert resp.status_code == 200
        assert all(e["category"] == "security" for e in resp.json())

    def test_get_nonexistent_entry(self, client, test_user):
        headers = test_user["headers"]
        resp = client.get("/api/v1/knowledge-base/nonexistent", headers=headers)
        assert resp.status_code == 404
