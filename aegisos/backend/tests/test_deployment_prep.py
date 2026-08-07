"""Tests for Deployment Preparation — Phase 52."""

import pytest
from app.services.deployment_prep import (
    DeploymentPrepService, get_deployment_prep_service, ScriptType, ScriptStatus,
)


class TestScripts:
    def test_list_scripts(self):
        service = DeploymentPrepService()
        scripts = service.list_scripts()
        assert len(scripts) >= 8

    def test_filter_by_type(self):
        service = DeploymentPrepService()
        dns = service.list_scripts(type=ScriptType.DNS.value)
        assert all(s.type == ScriptType.DNS.value for s in dns)

    def test_get_script(self):
        service = DeploymentPrepService()
        scripts = service.list_scripts()[:1]
        s = service.get_script(scripts[0].id)
        assert s is not None

    def test_get_by_filename(self):
        service = DeploymentPrepService()
        s = service.get_script_by_filename("deploy.sh")
        assert s is not None
        assert s.name == "Deploy Verdis + EvolvixOS"

    def test_update_status(self):
        service = DeploymentPrepService()
        scripts = service.list_scripts()[:1]
        updated = service.update_script_status(scripts[0].id, ScriptStatus.COMPLETED.value)
        assert updated.status == ScriptStatus.COMPLETED.value
        assert updated.run_count == 1

    def test_generate_all(self):
        service = DeploymentPrepService()
        scripts = service.generate_all_scripts()
        assert "deploy.sh" in scripts
        assert "setup_dns.sh" in scripts
        assert "harden_server.sh" in scripts

    def test_script_has_content(self):
        service = DeploymentPrepService()
        s = service.get_script_by_filename("deploy.sh")
        assert len(s.content) > 100
        assert "docker" in s.content


class TestDNS:
    def test_list_dns(self):
        service = DeploymentPrepService()
        records = service.list_dns_records()
        assert len(records) >= 9

    def test_get_dns_record(self):
        service = DeploymentPrepService()
        records = service.list_dns_records()[:1]
        r = service.get_dns_record(records[0].id)
        assert r is not None

    def test_has_main_domain(self):
        service = DeploymentPrepService()
        records = service.list_dns_records()
        main = [r for r in records if r.name == "verdischain.com"]
        assert len(main) > 0
        assert main[0].type == "A"

    def test_has_subdomains(self):
        service = DeploymentPrepService()
        records = service.list_dns_records()
        names = [r.name for r in records]
        assert "api.verdischain.com" in names
        assert "explorer.verdischain.com" in names
        assert "faucet.verdischain.com" in names


class TestSSL:
    def test_list_ssl(self):
        service = DeploymentPrepService()
        configs = service.list_ssl_configs()
        assert len(configs) >= 6

    def test_get_ssl_config(self):
        service = DeploymentPrepService()
        configs = service.list_ssl_configs()[:1]
        c = service.get_ssl_config(configs[0].id)
        assert c is not None

    def test_lets_encrypt(self):
        service = DeploymentPrepService()
        configs = service.list_ssl_configs()
        assert all(c.issuer == "Let's Encrypt" for c in configs)

    def test_auto_renew(self):
        service = DeploymentPrepService()
        configs = service.list_ssl_configs()
        assert all(c.auto_renew for c in configs)


class TestSteps:
    def test_list_steps(self):
        service = DeploymentPrepService()
        steps = service.list_steps()
        assert len(steps) >= 16

    def test_ordered(self):
        service = DeploymentPrepService()
        steps = service.list_steps()
        orders = [s.order for s in steps]
        assert orders == sorted(orders)

    def test_get_step(self):
        service = DeploymentPrepService()
        steps = service.list_steps()[:1]
        s = service.get_step(steps[0].id)
        assert s is not None

    def test_update_step_status(self):
        service = DeploymentPrepService()
        steps = service.list_steps()[:1]
        updated = service.update_step_status(steps[0].id, ScriptStatus.COMPLETED.value)
        assert updated.status == ScriptStatus.COMPLETED.value

    def test_deployment_progress(self):
        service = DeploymentPrepService()
        progress = service.get_deployment_progress()
        assert "total" in progress
        assert "completed" in progress
        assert "percentage" in progress

    def test_has_dependencies(self):
        service = DeploymentPrepService()
        steps = service.list_steps()
        deploy_step = [s for s in steps if s.name == "Deploy Services"][0]
        assert len(deploy_step.depends_on) > 0


class TestDashboard:
    def test_dashboard(self):
        service = DeploymentPrepService()
        dash = service.get_dashboard()
        assert "stats" in dash
        assert "progress" in dash
        assert "scripts" in dash
        assert "dns_records" in dash
        assert "ssl_configs" in dash
        assert "steps" in dash

    def test_stats(self):
        service = DeploymentPrepService()
        dash = service.get_dashboard()
        assert dash["stats"]["total_scripts"] >= 8
        assert dash["stats"]["total_dns_records"] >= 9
        assert dash["stats"]["total_ssl_configs"] >= 6
        assert dash["stats"]["total_steps"] >= 16


class TestDeployAPI:
    def test_dashboard(self, client, test_user):
        resp = client.get("/api/v1/deploy/dashboard", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_list_scripts(self, client, test_user):
        resp = client.get("/api/v1/deploy/scripts", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_get_script(self, client, test_user):
        resp = client.get("/api/v1/deploy/scripts/filename/deploy.sh", headers=test_user["headers"])
        assert resp.status_code == 200
        assert "docker" in resp.json()["content"]

    def test_generate_all(self, client, test_user):
        resp = client.get("/api/v1/deploy/scripts/generate-all", headers=test_user["headers"])
        assert resp.status_code == 200
        assert "deploy.sh" in resp.json()

    def test_list_dns(self, client, test_user):
        resp = client.get("/api/v1/deploy/dns", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_list_ssl(self, client, test_user):
        resp = client.get("/api/v1/deploy/ssl", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_list_steps(self, client, test_user):
        resp = client.get("/api/v1/deploy/steps", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_progress(self, client, test_user):
        resp = client.get("/api/v1/deploy/progress", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_singleton(self):
        assert get_deployment_prep_service() is get_deployment_prep_service()
