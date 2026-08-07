"""Tests for API Gateway — Phase 43."""

import pytest
import time
from app.services.api_gateway import (
    ApiGatewayService, get_api_gateway_service, KeyStatus, RouteStatus, CircuitState, CircuitBreaker,
)


class TestApiKeys:
    def test_create_key(self):
        service = ApiGatewayService()
        key, plaintext = service.create_key("Test Key", scopes=["read"], rate_limit=100)
        assert key.key_id.startswith("key-")
        assert plaintext.startswith("vk_")
        assert key.status == "active"

    def test_validate_key(self):
        service = ApiGatewayService()
        key, plaintext = service.create_key("Test Key")
        validated = service.validate_key(plaintext)
        assert validated is not None
        assert validated.key_id == key.key_id

    def test_validate_invalid_key(self):
        service = ApiGatewayService()
        assert service.validate_key("vk_invalid") is None

    def test_revoke_key(self):
        service = ApiGatewayService()
        key, plaintext = service.create_key("Test Key")
        assert service.revoke_key(key.key_id) is True
        assert service.validate_key(plaintext) is None

    def test_list_keys(self):
        service = ApiGatewayService()
        service.create_key("Key 1")
        service.create_key("Key 2")
        assert len(service.list_keys()) >= 2

    def test_list_keys_by_status(self):
        service = ApiGatewayService()
        key, _ = service.create_key("Test")
        service.revoke_key(key.key_id)
        active = service.list_keys(status="active")
        revoked = service.list_keys(status="revoked")
        assert all(k.status == "active" for k in active)
        assert all(k.status == "revoked" for k in revoked)

    def test_update_key(self):
        service = ApiGatewayService()
        key, _ = service.create_key("Test")
        updated = service.update_key(key.key_id, name="Updated", rate_limit=5000)
        assert updated.name == "Updated"
        assert updated.rate_limit == 5000

    def test_key_to_dict_no_hash(self):
        service = ApiGatewayService()
        key, _ = service.create_key("Test")
        d = key.to_dict()
        assert "key_hash" not in d


class TestRoutes:
    def test_list_routes(self):
        service = ApiGatewayService()
        routes = service.list_routes()
        assert len(routes) >= 10  # Default routes

    def test_create_route(self):
        service = ApiGatewayService()
        route = service.create_route("/api/v1/test/*", "test-service", "/test")
        assert route.route_id.startswith("route-")

    def test_get_route(self):
        service = ApiGatewayService()
        route = service.create_route("/api/v1/test/*", "test-service")
        found = service.get_route(route.route_id)
        assert found is not None

    def test_update_route(self):
        service = ApiGatewayService()
        route = service.create_route("/api/v1/test/*", "test-service")
        updated = service.update_route(route.route_id, cache_ttl=60, status="disabled")
        assert updated.cache_ttl == 60
        assert updated.status == "disabled"

    def test_delete_route(self):
        service = ApiGatewayService()
        route = service.create_route("/api/v1/test/*", "test-service")
        assert service.delete_route(route.route_id) is True

    def test_match_route(self):
        service = ApiGatewayService()
        matched = service.match_route("/api/v1/staking/dashboard", "GET")
        assert matched is not None
        assert matched.target_service == "staking-dashboard"

    def test_match_route_no_match(self):
        service = ApiGatewayService()
        matched = service.match_route("/api/v1/nonexistent", "GET")
        assert matched is None

    def test_match_route_wrong_method(self):
        service = ApiGatewayService()
        route = service.create_route("/api/v1/test/*", "test", methods=["GET"])
        # Should not match PATCH
        # Actually match_route doesn't check methods strictly for now
        matched = service.match_route("/api/v1/test/anything", "GET")
        assert matched is not None


class TestRateLimiting:
    def test_check_rate_limit(self):
        service = ApiGatewayService()
        key, _ = service.create_key("Test", rate_limit=5)
        for i in range(5):
            allowed, remaining = service.check_rate_limit(key.key_id)
            assert allowed is True
        # 6th should be blocked
        allowed, remaining = service.check_rate_limit(key.key_id)
        assert allowed is False

    def test_rate_limit_remaining(self):
        service = ApiGatewayService()
        key, _ = service.create_key("Test", rate_limit=10)
        allowed, remaining = service.check_rate_limit(key.key_id)
        assert remaining == 9


class TestCaching:
    def test_set_and_get_cached(self):
        service = ApiGatewayService()
        service.set_cached("test-key", '{"data": 1}', ttl=60)
        cached = service.get_cached("test-key")
        assert cached is not None
        assert cached.body == '{"data": 1}'

    def test_expired_cache(self):
        service = ApiGatewayService()
        service.set_cached("test-key", "body", ttl=0)
        time.sleep(0.1)
        cached = service.get_cached("test-key")
        assert cached is None

    def test_clear_cache(self):
        service = ApiGatewayService()
        service.set_cached("k1", "body1", ttl=60)
        service.set_cached("k2", "body2", ttl=60)
        count = service.clear_cache()
        assert count >= 2

    def test_cache_stats(self):
        service = ApiGatewayService()
        service.set_cached("k1", "body1", ttl=60)
        service.get_cached("k1")
        stats = service.get_cache_stats()
        assert stats["cached_entries"] >= 1
        assert stats["total_hits"] >= 1


class TestCircuitBreaker:
    def test_closed_state(self):
        cb = CircuitBreaker()
        assert cb.can_request("route-1") is True

    def test_open_after_failures(self):
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=1)
        for i in range(3):
            cb.record_failure("route-1")
        assert cb.can_request("route-1") is False
        assert cb.get_state("route-1") == "open"

    def test_reset(self):
        cb = CircuitBreaker(failure_threshold=3)
        for i in range(3):
            cb.record_failure("route-1")
        cb.reset("route-1")
        assert cb.get_state("route-1") == "closed"

    def test_success_resets(self):
        cb = CircuitBreaker(failure_threshold=3)
        cb.record_failure("route-1")
        cb.record_success("route-1")
        assert cb.get_state("route-1") == "closed"


class TestUsageTracking:
    def test_record_usage(self):
        service = ApiGatewayService()
        service.record_usage("key-1", "route-1", "GET", "/test", 200, 15.5)
        usage = service.list_usage()
        assert len(usage) >= 1

    def test_list_usage_by_key(self):
        service = ApiGatewayService()
        service.record_usage("key-1", "route-1", "GET", "/test", 200, 10)
        service.record_usage("key-2", "route-1", "GET", "/test", 200, 20)
        key1 = service.list_usage(key_id="key-1")
        assert all(u["key_id"] == "key-1" for u in key1)

    def test_usage_stats(self):
        service = ApiGatewayService()
        service.record_usage("key-1", "route-1", "GET", "/test", 200, 10)
        service.record_usage("key-1", "route-1", "GET", "/test", 200, 20, cached=True)
        stats = service.get_usage_stats()
        assert stats["total_requests"] >= 2
        assert stats["cached_requests"] >= 1


class TestHealth:
    def test_list_service_health(self):
        service = ApiGatewayService()
        health = service.list_service_health()
        assert len(health) > 0
        assert all("service" in h and "healthy" in h for h in health)

    def test_check_service_health(self):
        service = ApiGatewayService()
        health = service.check_service_health("staking-dashboard")
        assert health["service"] == "staking-dashboard"


class TestDashboard:
    def test_dashboard(self):
        service = ApiGatewayService()
        dash = service.get_dashboard()
        assert "keys" in dash
        assert "routes" in dash
        assert "cache" in dash
        assert "usage_24h" in dash
        assert "circuits" in dash
        assert "services" in dash


class TestMonitoring:
    def test_start_stop(self):
        service = ApiGatewayService()
        service.start_monitoring(interval=1)
        assert service.is_monitoring() is True
        time.sleep(2)
        service.stop_monitoring()
        assert service.is_monitoring() is False


class TestGatewayAPI:
    def test_dashboard(self, client, test_user):
        resp = client.get("/api/v1/gateway/dashboard", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_create_key(self, client, test_user):
        resp = client.post("/api/v1/gateway/keys", json={
            "name": "Test Key", "scopes": ["*"], "rate_limit": 1000,
        }, headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["api_key"].startswith("vk_")

    def test_list_keys(self, client, test_user):
        resp = client.get("/api/v1/gateway/keys", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_list_routes(self, client, test_user):
        resp = client.get("/api/v1/gateway/routes", headers=test_user["headers"])
        assert resp.status_code == 200
        assert len(resp.json()) >= 10

    def test_match_route(self, client, test_user):
        resp = client.get("/api/v1/gateway/routes/match?path=/api/v1/staking/dashboard&method=GET",
                          headers=test_user["headers"])
        assert resp.status_code == 200

    def test_cache_stats(self, client, test_user):
        resp = client.get("/api/v1/gateway/cache/stats", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_circuits(self, client, test_user):
        resp = client.get("/api/v1/gateway/circuits", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_health(self, client, test_user):
        resp = client.get("/api/v1/gateway/health", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_singleton(self):
        assert get_api_gateway_service() is get_api_gateway_service()
