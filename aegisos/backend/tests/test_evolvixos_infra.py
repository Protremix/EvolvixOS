"""Tests for EvolvixOS Infrastructure."""

import pytest
from app.services.evolvixos_infra import (
    EvolvixOSInfraService, get_evolvixos_infra_service, ServiceStatus, ComponentType,
)


class TestComponents:
    def test_list(self):
        s = EvolvixOSInfraService()
        comps = s.list_components()
        assert len(comps) >= 7

    def test_get(self):
        s = EvolvixOSInfraService()
        comps = s.list_components()[:1]
        c = s.get_component(comps[0].id)
        assert c is not None

    def test_update_status(self):
        s = EvolvixOSInfraService()
        comps = s.list_components()[:1]
        c = s.update_component_status(comps[0].id, ServiceStatus.LIVE.value)
        assert c.status == ServiceStatus.LIVE.value

    def test_backend_has_env_vars(self):
        s = EvolvixOSInfraService()
        for c in s.list_components():
            if c.type == ComponentType.BACKEND.value:
                assert len(c.environment_vars) > 0
                assert any("VERDIS" in v for v in c.environment_vars)

    def test_frontend_has_env_vars(self):
        s = EvolvixOSInfraService()
        for c in s.list_components():
            if c.type == ComponentType.FRONTEND.value:
                assert any("VITE_API_URL" in v for v in c.environment_vars)


class TestDNS:
    def test_list(self):
        s = EvolvixOSInfraService()
        dns = s.list_dns()
        assert len(dns) >= 6

    def test_has_main_domain(self):
        s = EvolvixOSInfraService()
        dns = s.list_dns()
        assert any(d.full_domain == "evolvixos.com" for d in dns)

    def test_has_api_subdomain(self):
        s = EvolvixOSInfraService()
        dns = s.list_dns()
        assert any(d.full_domain == "api.evolvixos.com" for d in dns)

    def test_set_ip(self):
        s = EvolvixOSInfraService()
        s.set_server_ip("1.2.3.4")
        for d in s.list_dns():
            assert d.target == "1.2.3.4"


class TestSteps:
    def test_list(self):
        s = EvolvixOSInfraService()
        steps = s.list_steps()
        assert len(steps) >= 16

    def test_ordered(self):
        s = EvolvixOSInfraService()
        steps = s.list_steps()
        orders = [st.order for st in steps]
        assert orders == sorted(orders)

    def test_update_status(self):
        s = EvolvixOSInfraService()
        steps = s.list_steps()[:1]
        st = s.update_step_status(steps[0].id, ServiceStatus.LIVE.value)
        assert st.status == ServiceStatus.LIVE.value

    def test_progress(self):
        s = EvolvixOSInfraService()
        p = s.get_progress()
        assert "total" in p
        assert "domain" in p
        assert p["domain"] == "evolvixos.com"


class TestScripts:
    def test_get_scripts(self):
        s = EvolvixOSInfraService()
        scripts = s.get_deployment_scripts()
        assert "evolvixos_deploy.sh" in scripts
        assert "evolvixos_setup_dns.sh" in scripts
        assert "evolvixos-nginx.conf" in scripts
        assert "evolvixos-docker-compose.yml" in scripts

    def test_nginx_has_domain(self):
        s = EvolvixOSInfraService()
        scripts = s.get_deployment_scripts()
        assert "evolvixos.com" in scripts["evolvixos-nginx.conf"]

    def test_docker_compose_has_services(self):
        s = EvolvixOSInfraService()
        scripts = s.get_deployment_scripts()
        compose = scripts["evolvixos-docker-compose.yml"]
        assert "postgres" in compose
        assert "backend" in compose
        assert "frontend" in compose
        assert "redis" in compose

    def test_deploy_has_git_clone(self):
        s = EvolvixOSInfraService()
        scripts = s.get_deployment_scripts()
        assert "git clone" in scripts["evolvixos_deploy.sh"]


class TestDashboard:
    def test_dashboard(self):
        s = EvolvixOSInfraService()
        dash = s.get_dashboard()
        assert "domain" in dash
        assert "components" in dash
        assert "dns_records" in dash
        assert "steps" in dash
        assert "progress" in dash
        assert "verdis_connection" in dash
        assert dash["domain"] == "evolvixos.com"


class TestAPI:
    def test_dashboard(self, client, test_user):
        resp = client.get("/api/v1/evolvixos-infra/dashboard", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_components(self, client, test_user):
        resp = client.get("/api/v1/evolvixos-infra/components", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_dns(self, client, test_user):
        resp = client.get("/api/v1/evolvixos-infra/dns", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_steps(self, client, test_user):
        resp = client.get("/api/v1/evolvixos-infra/steps", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_scripts(self, client, test_user):
        resp = client.get("/api/v1/evolvixos-infra/scripts", headers=test_user["headers"])
        assert resp.status_code == 200
        assert "evolvixos_deploy.sh" in resp.json()

    def test_progress(self, client, test_user):
        resp = client.get("/api/v1/evolvixos-infra/progress", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_set_ip(self, client, test_user):
        resp = client.post("/api/v1/evolvixos-infra/set-ip", json={"ip": "5.6.7.8"}, headers=test_user["headers"])
        assert resp.status_code == 200

    def test_singleton(self):
        assert get_evolvixos_infra_service() is get_evolvixos_infra_service()
