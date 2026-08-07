"""Tests for Phase 50 Security Fixes."""

import pytest
import time
from app.core.circuit_breaker import CircuitBreaker, CircuitState, get_circuit_breaker_registry, with_circuit_breaker
from app.core.auth_rate_limit import AuthRateLimiter, get_auth_rate_limiter
from app.core.jwt_config import ACCESS_TOKEN_EXPIRE_HOURS, REFRESH_TOKEN_EXPIRE_DAYS, get_token_config
from app.core.bounded_store import BoundedDict, BoundedList
from app.core.secret_manager import SecretManager, get_secret_manager
from app.core.pagination import PaginationParams, paginate, PaginatedResponse


class TestCircuitBreaker:
    def test_initial_state(self):
        cb = CircuitBreaker("test")
        assert cb.state == CircuitState.CLOSED.value

    def test_opens_after_threshold(self):
        cb = CircuitBreaker("test", failure_threshold=3)
        for _ in range(3):
            cb.record_failure()
        assert cb.state == CircuitState.OPEN.value

    def test_rejects_when_open(self):
        cb = CircuitBreaker("test", failure_threshold=2)
        cb.record_failure()
        cb.record_failure()
        assert cb.can_execute() is False

    def test_half_open_after_timeout(self):
        cb = CircuitBreaker("test", failure_threshold=2, recovery_timeout=1)
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.OPEN.value
        time.sleep(1.5)
        assert cb.state == CircuitState.HALF_OPEN.value

    def test_closes_on_success_in_half_open(self):
        cb = CircuitBreaker("test", failure_threshold=1, recovery_timeout=1, half_open_max_calls=2)
        cb.record_failure()
        time.sleep(1.5)
        assert cb.state == CircuitState.HALF_OPEN.value
        cb.record_success()
        cb.record_success()
        assert cb.state == CircuitState.CLOSED.value

    def test_opens_on_failure_in_half_open(self):
        cb = CircuitBreaker("test", failure_threshold=1, recovery_timeout=1)
        cb.record_failure()
        time.sleep(1.5)
        assert cb.state == CircuitState.HALF_OPEN.value
        cb.record_failure()
        assert cb.state == CircuitState.OPEN.value

    def test_record_success_resets_failures(self):
        cb = CircuitBreaker("test", failure_threshold=3)
        cb.record_failure()
        cb.record_failure()
        cb.record_success()
        assert cb.state == CircuitState.CLOSED.value

    def test_reset(self):
        cb = CircuitBreaker("test", failure_threshold=2)
        cb.record_failure()
        cb.record_failure()
        cb.reset()
        assert cb.state == CircuitState.CLOSED.value

    def test_registry(self):
        registry = get_circuit_breaker_registry()
        cb = registry.get_or_create("test_service")
        assert cb is not None
        same = registry.get_or_create("test_service")
        assert cb is same

    def test_decorator(self):
        @with_circuit_breaker("decorated_test", failure_threshold=2)
        def test_func():
            return "success"

        result = test_func()
        assert result == "success"

    def test_decorator_opens_circuit(self):
        @with_circuit_breaker("failing_test", failure_threshold=2)
        def failing_func():
            raise Exception("fail")

        for _ in range(2):
            with pytest.raises(Exception):
                failing_func()

        # Now circuit should be open
        with pytest.raises(Exception, match="Circuit breaker"):
            failing_func()

    def test_stats(self):
        cb = CircuitBreaker("stats_test")
        cb.record_success()
        cb.record_failure()
        stats = cb.stats
        assert stats.total_calls == 2
        assert stats.successful == 1
        assert stats.failed == 1


class TestAuthRateLimiter:
    def test_allows_initial_attempts(self):
        limiter = AuthRateLimiter()
        can, msg = limiter.can_attempt("127.0.0.1")
        assert can is True

    def test_blocks_after_limit(self):
        limiter = AuthRateLimiter()
        limiter.ip_limit_per_minute = 3
        for _ in range(3):
            limiter.record_attempt("127.0.0.1")
        can, msg = limiter.can_attempt("127.0.0.1")
        assert can is False
        assert "IP" in msg

    def test_blocks_by_address(self):
        limiter = AuthRateLimiter()
        limiter.address_limit_per_hour = 2
        for _ in range(2):
            limiter.record_attempt("10.0.0.1", "0xaddress")
        can, msg = limiter.can_attempt("10.0.0.1", "0xaddress")
        assert can is False

    def test_different_ips_independent(self):
        limiter = AuthRateLimiter()
        limiter.ip_limit_per_minute = 1
        limiter.record_attempt("1.1.1.1")
        can1, _ = limiter.can_attempt("1.1.1.1")
        can2, _ = limiter.can_attempt("2.2.2.2")
        assert can1 is False
        assert can2 is True

    def test_stats(self):
        limiter = AuthRateLimiter()
        limiter.record_attempt("1.1.1.1")
        limiter.record_attempt("1.1.1.2", "0xaddr")
        stats = limiter.get_stats()
        assert stats["tracked_ips"] >= 2
        assert stats["tracked_addresses"] >= 1


class TestJWTConfig:
    def test_access_token_shorter(self):
        assert ACCESS_TOKEN_EXPIRE_HOURS == 1  # Was 168 (7 days)

    def test_refresh_token_days(self):
        assert REFRESH_TOKEN_EXPIRE_DAYS == 7

    def test_config(self):
        config = get_token_config()
        assert config["access_token_expiry_hours"] == 1
        assert config["previous_expiry_hours"] == 168
        assert "improvement" in config


class TestBoundedDict:
    def test_set_get(self):
        d = BoundedDict(max_size=100)
        d.set("key1", "value1")
        assert d.get("key1") == "value1"

    def test_max_size_eviction(self):
        d = BoundedDict(max_size=3)
        d.set("a", 1)
        d.set("b", 2)
        d.set("c", 3)
        d.set("d", 4)
        assert d.get("a") is None  # Evicted
        assert d.get("d") == 4

    def test_ttl_expiration(self):
        d = BoundedDict(max_size=100, ttl_seconds=1)
        d.set("key", "value")
        assert d.get("key") == "value"
        time.sleep(1.5)
        assert d.get("key") is None

    def test_delete(self):
        d = BoundedDict(max_size=100)
        d.set("key", "value")
        assert d.delete("key") is True
        assert d.get("key") is None

    def test_stats(self):
        d = BoundedDict(max_size=100)
        d.set("a", 1)
        stats = d.stats()
        assert stats["size"] == 1
        assert stats["max_size"] == 100


class TestBoundedList:
    def test_append_list(self):
        lst = BoundedList(max_size=5)
        for i in range(3):
            lst.append(i)
        assert lst.list_all() == [0, 1, 2]

    def test_max_size(self):
        lst = BoundedList(max_size=3)
        for i in range(5):
            lst.append(i)
        assert len(lst.list_all()) == 3
        assert lst.list_all() == [2, 3, 4]

    def test_stats(self):
        lst = BoundedList(max_size=5)
        lst.append(1)
        stats = lst.stats()
        assert stats["size"] == 1
        assert stats["total_added"] == 1


class TestPagination:
    def test_pagination_params(self):
        p = PaginationParams(page=2, page_size=10)
        assert p.offset == 10
        assert p.limit == 10

    def test_first_page(self):
        p = PaginationParams(page=1, page_size=10)
        assert p.offset == 0

    def test_max_page_size(self):
        p = PaginationParams(page=1, page_size=1000)
        assert p.page_size == 500  # Capped at max

    def test_paginate(self):
        items = list(range(100))
        result = paginate(items, page=1, page_size=10)
        assert len(result.items) == 10
        assert result.total == 100
        assert result.has_more is True

    def test_last_page(self):
        items = list(range(25))
        result = paginate(items, page=3, page_size=10)
        assert len(result.items) == 5
        assert result.has_more is False

    def test_empty(self):
        result = paginate([], page=1, page_size=10)
        assert result.total == 0
        assert result.has_more is False


class TestSecretManager:
    def test_get_set(self):
        import os
        os.environ["TEST_SECRET_KEY"] = "test_value"
        mgr = SecretManager()
        assert mgr.get("TEST_SECRET_KEY") == "test_value"
        del os.environ["TEST_SECRET_KEY"]

    def test_get_default(self):
        mgr = SecretManager()
        assert mgr.get("NONEXISTENT", "default") == "default"

    def test_is_set(self):
        import os
        os.environ["TEST_EXISTS"] = "yes"
        mgr = SecretManager()
        assert mgr.is_set("TEST_EXISTS") is True
        del os.environ["TEST_EXISTS"]

    def test_config(self):
        mgr = SecretManager()
        config = mgr.get_config()
        assert "sensitive_keys" in config
        assert "access_count" in config


class TestSecurityFixesAPI:
    def test_circuit_breakers(self, client, test_user):
        resp = client.get("/api/v1/security/circuit-breakers", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_auth_rate_limit_stats(self, client, test_user):
        resp = client.get("/api/v1/security/auth-rate-limit/stats", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_jwt_config(self, client, test_user):
        resp = client.get("/api/v1/security/jwt-config", headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["access_token_expiry_hours"] == 1

    def test_secret_manager(self, client, test_user):
        resp = client.get("/api/v1/security/secret-manager/config", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_pagination_demo(self, client, test_user):
        resp = client.get("/api/v1/security/pagination/demo", headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["total"] == 1000

    def test_summary(self, client, test_user):
        resp = client.get("/api/v1/security/summary", headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["total_fixes"] == 6
        assert resp.json()["high_fixed"] == 1
        assert resp.json()["medium_fixed"] == 5
