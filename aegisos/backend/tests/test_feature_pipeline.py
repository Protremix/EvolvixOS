"""Tests for the Feature Delivery Pipeline — Post-MVP Phase 1."""

import pytest
from app.services.feature_pipeline import (
    FeatureRequest, FeaturePipelineRun, create_pipeline_run,
    get_pipeline_progress, get_pipeline_summary, get_stage_context,
    update_stage_result, should_retry, PipelineStage, StageStatus,
    STAGE_DEFS, get_stage_def,
)


class TestPipelineStages:
    """Test pipeline stage definitions."""

    def test_all_10_stages_defined(self):
        assert len(STAGE_DEFS) == 10

    def test_stage_order(self):
        stages = [s["stage"] for s in STAGE_DEFS]
        assert stages[0] == PipelineStage.PRD
        assert stages[1] == PipelineStage.ARCHITECTURE
        assert stages[2] == PipelineStage.DECOMPOSITION
        assert stages[3] == PipelineStage.IMPLEMENTATION
        assert stages[4] == PipelineStage.QA_TESTING
        assert stages[5] == PipelineStage.SECURITY_REVIEW
        assert stages[6] == PipelineStage.PERFORMANCE_REVIEW
        assert stages[7] == PipelineStage.DOCUMENTATION
        assert stages[8] == PipelineStage.CODE_REVIEW
        assert stages[9] == PipelineStage.RELEASE

    def test_stage_has_agent(self):
        for s in STAGE_DEFS:
            assert s["agent"], f"Stage {s['stage']} has no agent"

    def test_stage_has_task_type(self):
        for s in STAGE_DEFS:
            assert s["task_type"], f"Stage {s['stage']} has no task type"

    def test_stage_has_max_retries(self):
        for s in STAGE_DEFS:
            assert s["max_retries"] >= 0

    def test_get_stage_def(self):
        sdef = get_stage_def(PipelineStage.QA_TESTING)
        assert sdef is not None
        assert sdef["name"] == "QA Testing"
        assert sdef["agent"] == "qa_agent"

    def test_get_stage_def_not_found(self):
        # Should handle gracefully
        from app.services.feature_pipeline import get_stage_def
        # PipelineStage is an enum, all values have defs
        sdef = get_stage_def(PipelineStage.RELEASE)
        assert sdef["name"] == "Release"
        assert sdef["max_retries"] == 0  # No retries for final release

    def test_implementation_has_highest_retries(self):
        impl = get_stage_def(PipelineStage.IMPLEMENTATION)
        qa = get_stage_def(PipelineStage.QA_TESTING)
        review = get_stage_def(PipelineStage.CODE_REVIEW)
        # These complex stages should allow retries
        assert impl["max_retries"] >= 1
        assert qa["max_retries"] >= 1
        assert review["max_retries"] >= 1


class TestPipelineRun:
    """Test pipeline run creation and management."""

    def test_create_pipeline_run(self):
        feature = FeatureRequest(
            title="Add user avatars",
            description="Allow users to upload and crop profile avatars",
            project_type="web_backend",
            priority="medium",
        )
        run = create_pipeline_run(feature)
        assert run.id is not None
        assert run.feature.title == "Add user avatars"
        assert len(run.stages) == 10
        assert run.status == "pending"
        assert run.current_stage is None

    def test_all_stages_pending_initially(self):
        feature = FeatureRequest(title="Test", description="Test feature")
        run = create_pipeline_run(feature)
        for s in run.stages:
            assert s.status == StageStatus.PENDING

    def test_stages_have_correct_agents(self):
        feature = FeatureRequest(title="Test", description="Test")
        run = create_pipeline_run(feature)
        agents = [s.agent for s in run.stages]
        assert "cto_agent" in agents
        assert "architect_agent" in agents
        assert "planner_agent" in agents
        assert "security_agent" in agents
        assert "qa_agent" in agents
        assert "documentation_agent" in agents
        assert "reviewer_agent" in agents

    def test_pipeline_id_custom(self):
        feature = FeatureRequest(title="Test", description="Test")
        run = create_pipeline_run(feature, pipeline_id="custom-id-123")
        assert run.id == "custom-id-123"

    def test_feature_constraints(self):
        feature = FeatureRequest(
            title="Test",
            description="Test",
            constraints=["Must use Rust", "No external deps"],
        )
        run = create_pipeline_run(feature)
        assert len(run.feature.constraints) == 2
        assert "Must use Rust" in run.feature.constraints

    def test_feature_acceptance_criteria(self):
        feature = FeatureRequest(
            title="Test",
            description="Test",
            acceptance_criteria=["Works on mobile", "Handles offline"],
        )
        run = create_pipeline_run(feature)
        assert len(run.feature.acceptance_criteria) == 2


class TestStageUpdates:
    """Test stage status updates."""

    def test_update_stage_to_running(self):
        feature = FeatureRequest(title="Test", description="Test")
        run = create_pipeline_run(feature)
        update_stage_result(run, PipelineStage.PRD, StageStatus.RUNNING)
        assert run.stages[0].status == StageStatus.RUNNING
        assert run.current_stage == PipelineStage.PRD.value

    def test_update_stage_to_passed(self):
        feature = FeatureRequest(title="Test", description="Test")
        run = create_pipeline_run(feature)
        update_stage_result(
            run, PipelineStage.PRD, StageStatus.PASSED,
            output={"prd": "doc content"},
            duration_ms=1500,
        )
        assert run.stages[0].status == StageStatus.PASSED
        assert run.stages[0].output["prd"] == "doc content"
        assert run.stages[0].duration_ms == 1500
        assert run.stages[0].completed_at is not None

    def test_update_stage_with_warnings(self):
        feature = FeatureRequest(title="Test", description="Test")
        run = create_pipeline_run(feature)
        update_stage_result(
            run, PipelineStage.SECURITY_REVIEW, StageStatus.PASSED,
            warnings=["Minor XSS risk in template"],
        )
        assert len(run.stages[5].warnings) == 1
        assert "XSS" in run.stages[5].warnings[0]

    def test_update_stage_failed(self):
        feature = FeatureRequest(title="Test", description="Test")
        run = create_pipeline_run(feature)
        update_stage_result(run, PipelineStage.QA_TESTING, StageStatus.FAILED)
        assert run.stages[4].status == StageStatus.FAILED
        assert run.stages[4].completed_at is not None


class TestStageContext:
    """Test context passing between stages."""

    def test_context_includes_feature(self):
        feature = FeatureRequest(title="Test Feature", description="Test")
        run = create_pipeline_run(feature)
        ctx = get_stage_context(run, PipelineStage.ARCHITECTURE)
        assert ctx["feature"]["title"] == "Test Feature"
        assert ctx["stage"] == "architecture_design"

    def test_context_includes_previous_outputs(self):
        feature = FeatureRequest(title="Test", description="Test")
        run = create_pipeline_run(feature)
        # Complete PRD stage
        update_stage_result(
            run, PipelineStage.PRD, StageStatus.PASSED,
            output={"prd_doc": "Product requirements..."},
        )
        # Get context for architecture stage
        ctx = get_stage_context(run, PipelineStage.ARCHITECTURE)
        assert "previous_prd_generation" in ctx
        assert ctx["previous_prd_generation"]["prd_doc"] == "Product requirements..."

    def test_context_excludes_failed_stages(self):
        feature = FeatureRequest(title="Test", description="Test")
        run = create_pipeline_run(feature)
        # PRD passed
        update_stage_result(run, PipelineStage.PRD, StageStatus.PASSED, output={"prd": "doc"})
        # Architecture failed
        update_stage_result(run, PipelineStage.ARCHITECTURE, StageStatus.FAILED, output={"error": "fail"})
        # Get context for decomposition
        ctx = get_stage_context(run, PipelineStage.DECOMPOSITION)
        assert "previous_prd_generation" in ctx
        assert "previous_architecture_design" not in ctx


class TestPipelineProgress:
    """Test progress tracking."""

    def test_initial_progress(self):
        feature = FeatureRequest(title="Test", description="Test")
        run = create_pipeline_run(feature)
        progress = get_pipeline_progress(run)
        assert progress["total"] == 10
        assert progress["completed"] == 0
        assert progress["pending"] == 10
        assert progress["progress_pct"] == 0.0

    def test_progress_after_stages(self):
        feature = FeatureRequest(title="Test", description="Test")
        run = create_pipeline_run(feature)
        update_stage_result(run, PipelineStage.PRD, StageStatus.PASSED)
        update_stage_result(run, PipelineStage.ARCHITECTURE, StageStatus.PASSED)
        progress = get_pipeline_progress(run)
        assert progress["completed"] == 2
        assert progress["progress_pct"] == 20.0

    def test_progress_with_failure(self):
        feature = FeatureRequest(title="Test", description="Test")
        run = create_pipeline_run(feature)
        update_stage_result(run, PipelineStage.PRD, StageStatus.PASSED)
        update_stage_result(run, PipelineStage.ARCHITECTURE, StageStatus.FAILED)
        progress = get_pipeline_progress(run)
        assert progress["completed"] == 1
        assert progress["failed"] == 1

    def test_progress_with_running(self):
        feature = FeatureRequest(title="Test", description="Test")
        run = create_pipeline_run(feature)
        update_stage_result(run, PipelineStage.PRD, StageStatus.RUNNING)
        progress = get_pipeline_progress(run)
        assert progress["running"] == 1
        assert progress["pending"] == 9


class TestRetryLogic:
    """Test stage retry logic."""

    def test_should_retry_within_limit(self):
        feature = FeatureRequest(title="Test", description="Test")
        run = create_pipeline_run(feature)
        update_stage_result(run, PipelineStage.QA_TESTING, StageStatus.FAILED)
        assert should_retry(run, PipelineStage.QA_TESTING) is True

    def test_should_not_retry_exhausted(self):
        feature = FeatureRequest(title="Test", description="Test")
        run = create_pipeline_run(feature)
        # QA allows 2 retries
        update_stage_result(run, PipelineStage.QA_TESTING, StageStatus.FAILED)
        run.stages[4].retry_count = 2
        assert should_retry(run, PipelineStage.QA_TESTING) is False

    def test_should_not_retry_release(self):
        feature = FeatureRequest(title="Test", description="Test")
        run = create_pipeline_run(feature)
        update_stage_result(run, PipelineStage.RELEASE, StageStatus.FAILED)
        assert should_retry(run, PipelineStage.RELEASE) is False  # max_retries=0


class TestPipelineSummary:
    """Test summary generation."""

    def test_summary_includes_title(self):
        feature = FeatureRequest(title="Add dark mode", description="Test")
        run = create_pipeline_run(feature)
        summary = get_pipeline_summary(run)
        assert "Add dark mode" in summary

    def test_summary_includes_stages(self):
        feature = FeatureRequest(title="Test", description="Test")
        run = create_pipeline_run(feature)
        summary = get_pipeline_summary(run)
        assert "prd_generation" in summary
        assert "release" in summary

    def test_summary_with_completed_stages(self):
        feature = FeatureRequest(title="Test", description="Test")
        run = create_pipeline_run(feature)
        update_stage_result(run, PipelineStage.PRD, StageStatus.PASSED)
        summary = get_pipeline_summary(run)
        assert "✓" in summary


class TestPipelineAPI:
    """Test API endpoints."""

    def test_create_pipeline_api(self, client, test_user):
        headers = test_user["headers"]
        resp = client.post("/api/v1/feature-pipeline/", json={
            "title": "Add OAuth2 login",
            "description": "Implement Google OAuth2 authentication",
            "project_type": "web_backend",
            "priority": "high",
            "constraints": ["Must support Google and GitHub"],
            "acceptance_criteria": ["User can login with Google", "Token refresh works"],
        }, headers=headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["feature"]["title"] == "Add OAuth2 login"
        assert len(data["stages"]) == 10
        assert data["status"] == "pending"

    def test_list_pipelines_api(self, client, test_user):
        headers = test_user["headers"]
        client.post("/api/v1/feature-pipeline/", json={
            "title": "Feature 1", "description": "Test",
        }, headers=headers)
        client.post("/api/v1/feature-pipeline/", json={
            "title": "Feature 2", "description": "Test",
        }, headers=headers)
        resp = client.get("/api/v1/feature-pipeline/", headers=headers)
        assert resp.status_code == 200
        assert len(resp.json()) >= 2

    def test_get_pipeline_api(self, client, test_user):
        headers = test_user["headers"]
        create_resp = client.post("/api/v1/feature-pipeline/", json={
            "title": "Test", "description": "Test",
        }, headers=headers)
        pipeline_id = create_resp.json()["id"]
        resp = client.get(f"/api/v1/feature-pipeline/{pipeline_id}", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == pipeline_id

    def test_get_pipeline_not_found(self, client, test_user):
        headers = test_user["headers"]
        resp = client.get("/api/v1/feature-pipeline/nonexistent", headers=headers)
        assert resp.status_code == 404

    def test_get_progress_api(self, client, test_user):
        headers = test_user["headers"]
        create_resp = client.post("/api/v1/feature-pipeline/", json={
            "title": "Test", "description": "Test",
        }, headers=headers)
        pipeline_id = create_resp.json()["id"]
        resp = client.get(f"/api/v1/feature-pipeline/{pipeline_id}/progress", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 10
        assert data["pending"] == 10
        assert data["progress_pct"] == 0.0

    def test_get_summary_api(self, client, test_user):
        headers = test_user["headers"]
        create_resp = client.post("/api/v1/feature-pipeline/", json={
            "title": "Add caching", "description": "Redis cache for API",
        }, headers=headers)
        pipeline_id = create_resp.json()["id"]
        resp = client.get(f"/api/v1/feature-pipeline/{pipeline_id}/summary", headers=headers)
        assert resp.status_code == 200
        assert "Add caching" in resp.json()["summary"]

    def test_get_stages_info_api(self, client, test_user):
        headers = test_user["headers"]
        resp = client.get("/api/v1/feature-pipeline/stages/info", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 10
        assert data[0]["stage"] == "prd_generation"
        assert data[0]["order"] == 0
        assert data[9]["stage"] == "release"
        assert data[9]["order"] == 9

    def test_retry_stage_api(self, client, test_user):
        headers = test_user["headers"]
        create_resp = client.post("/api/v1/feature-pipeline/", json={
            "title": "Test", "description": "Test",
        }, headers=headers)
        pipeline_id = create_resp.json()["id"]
        resp = client.post(
            f"/api/v1/feature-pipeline/{pipeline_id}/stages/qa_testing/retry",
            headers=headers,
        )
        assert resp.status_code == 200

    def test_retry_exhausted(self, client, test_user):
        headers = test_user["headers"]
        create_resp = client.post("/api/v1/feature-pipeline/", json={
            "title": "Test", "description": "Test",
        }, headers=headers)
        pipeline_id = create_resp.json()["id"]
        # Exhaust retries for release (max_retries=0)
        resp = client.post(
            f"/api/v1/feature-pipeline/{pipeline_id}/stages/release/retry",
            headers=headers,
        )
        assert resp.status_code == 400

    def test_delete_pipeline_api(self, client, test_user):
        headers = test_user["headers"]
        create_resp = client.post("/api/v1/feature-pipeline/", json={
            "title": "Test", "description": "Test",
        }, headers=headers)
        pipeline_id = create_resp.json()["id"]
        resp = client.delete(f"/api/v1/feature-pipeline/{pipeline_id}", headers=headers)
        assert resp.status_code == 204
        # Verify it's gone
        resp = client.get(f"/api/v1/feature-pipeline/{pipeline_id}", headers=headers)
        assert resp.status_code == 404

    def test_unauthorized_access(self, client):
        resp = client.get("/api/v1/feature-pipeline/")
        assert resp.status_code == 401

    def test_create_invalid_request(self, client, test_user):
        headers = test_user["headers"]
        # Missing required title
        resp = client.post("/api/v1/feature-pipeline/", json={
            "description": "Test",
        }, headers=headers)
        assert resp.status_code == 422
