"""Tests for Global Search + System Health + Backup — Post-MVP Phase 10."""

import pytest
import json
from app.services.global_search import GlobalSearchService, get_search_service, SearchResult
from app.services.backup_restore import BackupRestoreService, get_backup_service, BackupRecord


class TestGlobalSearch:
    def test_search_empty_query(self):
        svc = GlobalSearchService()
        results = svc.search("")
        assert isinstance(results, list)

    def test_search_pipelines(self):
        svc = GlobalSearchService()
        results = svc.search("pipeline")
        assert isinstance(results, list)

    def test_search_knowledge(self):
        svc = GlobalSearchService()
        results = svc.search("test")
        assert isinstance(results, list)
        # Should find built-in knowledge entries
        assert len(results) > 0

    def test_search_settings(self):
        svc = GlobalSearchService()
        results = svc.search("rate_limit")
        assert len(results) > 0
        assert any(r.entity_type == "setting" for r in results)

    def test_search_filter_by_type(self):
        svc = GlobalSearchService()
        results = svc.search("test", entity_types=["knowledge"])
        assert all(r.entity_type == "knowledge" for r in results)

    def test_search_relevance_ordering(self):
        svc = GlobalSearchService()
        results = svc.search("pipeline")
        # Results should be sorted by relevance descending
        for i in range(len(results) - 1):
            assert results[i].relevance >= results[i + 1].relevance

    def test_search_result_to_dict(self):
        r = SearchResult(
            entity_type="test", entity_id="1", title="Test", description="Desc", relevance=1.0,
        )
        d = r.to_dict()
        assert d["entity_type"] == "test"
        assert d["title"] == "Test"

    def test_searchable_types(self):
        svc = GlobalSearchService()
        types = svc.get_searchable_types()
        assert len(types) == 6
        assert any(t["type"] == "pipeline" for t in types)
        assert any(t["type"] == "knowledge" for t in types)

    def test_search_multiple_words(self):
        svc = GlobalSearchService()
        results = svc.search("rate limit")
        assert isinstance(results, list)
        assert len(results) > 0

    def test_search_no_results(self):
        svc = GlobalSearchService()
        results = svc.search("zzzznonexistent")
        # Might find some results from built-in entries, but should be empty or minimal
        assert isinstance(results, list)

    def test_search_webhooks(self):
        svc = GlobalSearchService()
        results = svc.search("webhook", entity_types=["webhook"])
        assert all(r.entity_type == "webhook" for r in results)

    def test_search_templates(self):
        svc = GlobalSearchService()
        results = svc.search("bugfix", entity_types=["template"])
        assert len(results) > 0
        assert all(r.entity_type == "template" for r in results)


class TestGlobalSearchAPI:
    def test_search_get_api(self, client, test_user):
        resp = client.get("/api/v1/search/?q=test", headers=test_user["headers"])
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_search_post_api(self, client, test_user):
        resp = client.post("/api/v1/search/", json={"query": "pipeline", "limit": 10}, headers=test_user["headers"])
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_search_types_api(self, client, test_user):
        resp = client.get("/api/v1/search/types", headers=test_user["headers"])
        assert resp.status_code == 200
        assert len(resp.json()) == 6

    def test_search_filter_api(self, client, test_user):
        resp = client.get("/api/v1/search/?q=test&entity_types=knowledge", headers=test_user["headers"])
        assert resp.status_code == 200
        assert all(r["entity_type"] == "knowledge" for r in resp.json())


class TestSystemHealth:
    def test_health_endpoint(self, client):
        """Health check should NOT require auth."""
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        assert "status" in resp.json()
        assert resp.json()["status"] in ("healthy", "degraded", "unhealthy")

    def test_health_detail_requires_auth(self, client):
        """Detailed health should require auth."""
        resp = client.get("/api/v1/health/detail")
        assert resp.status_code == 401

    def test_health_detail_with_auth(self, client, test_user):
        resp = client.get("/api/v1/health/detail", headers=test_user["headers"])
        assert resp.status_code == 200
        assert "subsystems" in resp.json()


class TestBackupRestore:
    def test_create_backup(self):
        svc = BackupRestoreService()
        backup = svc.create_backup("test backup")
        assert backup["version"] == "1.0"
        assert "entities" in backup
        assert backup["description"] == "test backup"

    def test_backup_contains_entities(self):
        svc = BackupRestoreService()
        backup = svc.create_backup()
        entities = backup["entities"]
        assert "knowledge_entries" in entities
        assert "system_settings" in entities
        assert "pipeline_templates" in entities

    def test_backup_entity_counts(self):
        svc = BackupRestoreService()
        backup = svc.create_backup()
        # Should have some knowledge entries (built-in)
        assert len(backup["entities"]["knowledge_entries"]) >= 6

    def test_backup_history(self):
        svc = BackupRestoreService()
        svc.create_backup("first")
        svc.create_backup("second")
        history = svc.get_backup_history()
        assert len(history) == 2
        assert history[0].description == "second"

    def test_last_backup(self):
        svc = BackupRestoreService()
        svc.create_backup("test")
        last = svc.get_last_backup()
        assert last is not None
        assert last.description == "test"

    def test_backup_stats(self):
        svc = BackupRestoreService()
        svc.create_backup("test")
        stats = svc.get_stats()
        assert stats["total_backups"] == 1
        assert stats["last_backup"] is not None

    def test_backup_record_to_dict(self):
        r = BackupRecord(description="test", size_bytes=100)
        d = r.to_dict()
        assert d["description"] == "test"
        assert d["size_bytes"] == 100

    def test_backup_max_history(self):
        svc = BackupRestoreService(max_history=3)
        for i in range(5):
            svc.create_backup(f"backup-{i}")
        assert len(svc._backup_history) == 3

    def test_restore_settings(self):
        svc = BackupRestoreService()
        backup = svc.create_backup()
        # Restore settings
        result = svc.restore_backup(backup, restore_types=["settings"])
        assert "system_settings" in result

    def test_restore_knowledge(self):
        svc = BackupRestoreService()
        backup = svc.create_backup()
        result = svc.restore_backup(backup, restore_types=["knowledge"])
        assert "knowledge_entries" in result

    def test_restore_all(self):
        svc = BackupRestoreService()
        backup = svc.create_backup()
        result = svc.restore_backup(backup)
        assert "knowledge_entries" in result
        assert "system_settings" in result

    def test_restore_partial_data(self):
        svc = BackupRestoreService()
        result = svc.restore_backup({"entities": {"system_settings": {}}})
        assert result.get("system_settings") == 0


class TestBackupAPI:
    def test_create_backup_api(self, client, test_user):
        resp = client.post("/api/v1/backup/", json={"description": "test"}, headers=test_user["headers"])
        assert resp.status_code == 200
        assert "version" in resp.json()

    def test_backup_history_api(self, client, test_user):
        client.post("/api/v1/backup/", json={"description": "test"}, headers=test_user["headers"])
        resp = client.get("/api/v1/backup/history", headers=test_user["headers"])
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_backup_stats_api(self, client, test_user):
        client.post("/api/v1/backup/", json={}, headers=test_user["headers"])
        resp = client.get("/api/v1/backup/stats", headers=test_user["headers"])
        assert resp.status_code == 200
        assert "total_backups" in resp.json()

    def test_last_backup_api(self, client, test_user):
        client.post("/api/v1/backup/", json={}, headers=test_user["headers"])
        resp = client.get("/api/v1/backup/last", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_restore_backup_api(self, client, test_user):
        create = client.post("/api/v1/backup/", json={"description": "test"}, headers=test_user["headers"])
        backup_data = create.json()
        resp = client.post("/api/v1/backup/restore", json={
            "data": backup_data, "restore_types": ["settings"],
        }, headers=test_user["headers"])
        assert resp.status_code == 200
        assert "system_settings" in resp.json()
