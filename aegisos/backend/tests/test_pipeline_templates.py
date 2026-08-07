"""Tests for Pipeline Templates — Post-MVP Phase 4."""

import pytest
from app.services.pipeline_templates import (
    list_templates, get_template, register_custom_template,
    delete_custom_template, apply_template, get_template_categories,
    PipelineTemplate, BUILTIN_TEMPLATES,
)


class TestBuiltinTemplates:
    """Test built-in templates."""

    def test_builtin_templates_exist(self):
        templates = list_templates()
        assert len(templates) >= 8  # 8 built-in templates

    def test_get_bugfix_template(self):
        t = get_template("bugfix")
        assert t is not None
        assert t.name == "Bug Fix"
        assert t.category == "bugfix"
        assert t.default_priority == "high"

    def test_get_new_feature_template(self):
        t = get_template("new_feature")
        assert t is not None
        assert t.name == "New Feature"
        assert t.category == "feature"

    def test_get_hotfix_template(self):
        t = get_template("hotfix")
        assert t is not None
        assert t.complexity == "critical"
        assert t.estimated_duration_hours == 1.0
        # Hotfix skips many stages
        assert "prd_generation" in t.skip_stages
        assert "task_decomposition" in t.skip_stages

    def test_get_security_patch_template(self):
        t = get_template("security_patch")
        assert t is not None
        assert t.default_priority == "critical"
        assert t.stage_overrides["security_review"]["max_retries"] == 3

    def test_get_nonexistent_template(self):
        t = get_template("nonexistent")
        assert t is None

    def test_all_templates_have_required_fields(self):
        for t in BUILTIN_TEMPLATES:
            assert t.id, f"Template missing id"
            assert t.name, f"Template {t.id} missing name"
            assert t.description, f"Template {t.id} missing description"
            assert t.category in ["general", "bugfix", "feature", "infra", "security"]
            assert t.default_priority in ["low", "medium", "high", "critical"]
            assert t.complexity in ["low", "medium", "high", "critical"]

    def test_template_categories(self):
        cats = get_template_categories()
        assert len(cats) >= 4  # bugfix, feature, infra, security
        cat_names = [c["name"] for c in cats]
        assert "bugfix" in cat_names
        assert "feature" in cat_names
        assert "security" in cat_names


class TestTemplateFiltering:
    """Test template filtering by category."""

    def test_filter_by_bugfix(self):
        templates = list_templates(category="bugfix")
        assert all(t.category == "bugfix" for t in templates)
        assert len(templates) >= 2  # bugfix + hotfix

    def test_filter_by_security(self):
        templates = list_templates(category="security")
        assert len(templates) == 1  # only security_patch
        assert templates[0].id == "security_patch"

    def test_filter_by_feature(self):
        templates = list_templates(category="feature")
        assert all(t.category == "feature" for t in templates)
        assert len(templates) >= 3  # new_feature, refactor, api_endpoint


class TestApplyTemplate:
    """Test applying templates to create feature requests."""

    def test_apply_bugfix(self):
        result = apply_template("bugfix", "login crash", "App crashes on login")
        assert result is not None
        assert result["title"] == "Fix: login crash"
        assert result["priority"] == "high"
        assert "Must not break existing functionality" in result["constraints"]
        assert len(result["acceptance_criteria"]) >= 3
        assert result["_template"]["id"] == "bugfix"
        assert "performance_review" in result["_template"]["skip_stages"]

    def test_apply_new_feature(self):
        result = apply_template("new_feature", "dark mode", "Add dark theme support")
        assert result is not None
        assert result["title"] == "Feat: dark mode"
        assert result["priority"] == "medium"
        assert result["project_type"] == "generic"

    def test_apply_security_patch(self):
        result = apply_template("security_patch", "SQL injection in search",
                                "Fix SQL injection vulnerability")
        assert result is not None
        assert result["title"] == "Security: SQL injection in search"
        assert result["priority"] == "critical"
        assert "Follow OWASP best practices" in result["constraints"]

    def test_apply_with_extra_constraints(self):
        result = apply_template(
            "new_feature", "test feature", "desc",
            extra_constraints=["Custom constraint 1", "Custom constraint 2"],
        )
        assert result is not None
        assert "Custom constraint 1" in result["constraints"]
        assert "Custom constraint 2" in result["constraints"]
        # Original constraints still present
        assert "Follow existing code patterns" in result["constraints"]

    def test_apply_with_extra_acceptance(self):
        result = apply_template(
            "new_feature", "test", "desc",
            extra_acceptance=["Custom acceptance"],
        )
        assert "Custom acceptance" in result["acceptance_criteria"]

    def test_apply_nonexistent_template(self):
        result = apply_template("nonexistent", "title", "desc")
        assert result is None

    def test_apply_preserves_title_without_prefix(self):
        """If title already has prefix, don't double-prefix."""
        result = apply_template("bugfix", "Fix: already prefixed", "desc")
        assert result["title"] == "Fix: already prefixed"  # not "Fix: Fix: already prefixed"

    def test_apply_infra_template(self):
        result = apply_template("infra_change", "deploy new cache", "Deploy Redis cluster")
        assert result is not None
        assert result["project_type"] == "infrastructure"
        assert "Zero downtime deployment" in result["constraints"]


class TestCustomTemplates:
    """Test custom template management."""

    def test_create_custom_template(self):
        custom = PipelineTemplate(
            id="custom_test",
            name="Custom Test Template",
            description="A custom template for testing",
            category="general",
            default_constraints=["Test constraint"],
        )
        register_custom_template(custom)
        
        retrieved = get_template("custom_test")
        assert retrieved is not None
        assert retrieved.name == "Custom Test Template"

    def test_delete_custom_template(self):
        custom = PipelineTemplate(
            id="delete_me",
            name="Delete Me",
            description="Template to delete",
        )
        register_custom_template(custom)
        assert get_template("delete_me") is not None
        
        deleted = delete_custom_template("delete_me")
        assert deleted is True
        assert get_template("delete_me") is None

    def test_cannot_delete_builtin(self):
        result = delete_custom_template("bugfix")
        assert result is False
        assert get_template("bugfix") is not None


class TestTemplateAPI:
    """Test the template API endpoints."""

    def test_list_templates_api(self, client, test_user):
        headers = test_user["headers"]
        resp = client.get("/api/v1/pipeline-templates/", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 8

    def test_get_template_api(self, client, test_user):
        headers = test_user["headers"]
        resp = client.get("/api/v1/pipeline-templates/bugfix", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == "bugfix"

    def test_get_template_not_found(self, client, test_user):
        headers = test_user["headers"]
        resp = client.get("/api/v1/pipeline-templates/nonexistent", headers=headers)
        assert resp.status_code == 404

    def test_list_categories_api(self, client, test_user):
        headers = test_user["headers"]
        resp = client.get("/api/v1/pipeline-templates/categories", headers=headers)
        assert resp.status_code == 200
        assert len(resp.json()) >= 4

    def test_filter_by_category_api(self, client, test_user):
        headers = test_user["headers"]
        resp = client.get("/api/v1/pipeline-templates/?category=security", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert all(t["category"] == "security" for t in data)

    def test_apply_template_api(self, client, test_user):
        headers = test_user["headers"]
        resp = client.post("/api/v1/pipeline-templates/bugfix/apply",
                          params={"title": "test bug", "description": "test desc"},
                          headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "Fix:" in data["title"]

    def test_create_pipeline_from_template_api(self, client, test_user):
        headers = test_user["headers"]
        resp = client.post("/api/v1/pipeline-templates/bugfix/create-pipeline",
                          params={"title": "auth bug", "description": "Login fails"},
                          headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["feature"]["title"] == "Fix: auth bug"
        assert data["status"] == "pending"

    def test_create_custom_template_api(self, client, test_user):
        headers = test_user["headers"]
        resp = client.post("/api/v1/pipeline-templates/", json={
            "id": "api_custom",
            "name": "API Custom",
            "description": "Custom template via API",
            "category": "general",
        }, headers=headers)
        assert resp.status_code == 201

    def test_duplicate_template_id_fails(self, client, test_user):
        headers = test_user["headers"]
        resp = client.post("/api/v1/pipeline-templates/", json={
            "id": "bugfix",  # already exists
            "name": "Duplicate",
            "description": "Should fail",
        }, headers=headers)
        assert resp.status_code == 400

    def test_delete_builtin_fails(self, client, test_user):
        headers = test_user["headers"]
        resp = client.delete("/api/v1/pipeline-templates/bugfix", headers=headers)
        assert resp.status_code == 400
