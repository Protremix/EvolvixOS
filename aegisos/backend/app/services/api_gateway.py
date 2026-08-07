"""
API Gateway — Phase 43

Unified entry point with route management, API key authentication,
rate limiting, caching, usage tracking, circuit breaker, and health checks.
"""

import secrets
import time
import threading
import hashlib
import json
from typing import Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict, deque
from app.core.logging import get_logger

logger = get_logger("service.api_gateway")


class KeyStatus(str, Enum):
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"


class RouteStatus(str, Enum):
    ACTIVE = "active"
    DISABLED = "disabled"
    MAINTENANCE = "maintenance"


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class ApiKey:
    key_id: str
    key_hash: str  # Store hash, not plaintext
    name: str
    scopes: list = field(default_factory=list)  # e.g. ["staking:read", "governance:write"]
    rate_limit: int = 1000  # requests per minute
    status: str = KeyStatus.ACTIVE.value
    created: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    expires: str = ""
    last_used: str = ""
    total_requests: int = 0
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = asdict(self)
        d.pop("key_hash", None)  # Never expose hash
        return d


@dataclass
class Route:
    route_id: str
    path: str  # e.g. /api/v1/staking/*
    target_service: str = ""  # e.g. staking-dashboard
    target_path: str = ""  # e.g. /staking
    methods: list = field(default_factory=lambda: ["GET", "POST", "PUT", "DELETE"])
    strip_prefix: str = ""  # Strip from incoming path
    add_headers: dict = field(default_factory=dict)
    cache_ttl: int = 0  # seconds, 0 = no cache
    auth_required: bool = True
    allowed_scopes: list = field(default_factory=list)
    status: str = RouteStatus.ACTIVE.value
    created: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    request_count: int = 0
    error_count: int = 0
    avg_latency_ms: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class CachedResponse:
    key: str
    body: str
    status_code: int = 200
    headers: dict = field(default_factory=dict)
    cached_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    expires_at: str = ""
    hit_count: int = 0

    def is_expired(self) -> bool:
        if not self.expires_at:
            return True
        return datetime.utcnow() > datetime.fromisoformat(self.expires_at.replace("Z", ""))


@dataclass
class UsageRecord:
    key_id: str
    route_id: str
    method: str
    path: str
    status_code: int
    latency_ms: float
    cached: bool = False
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class CircuitBreaker:
    """Circuit breaker for route health."""
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self._failures: dict[str, int] = defaultdict(int)
        self._states: dict[str, str] = defaultdict(lambda: CircuitState.CLOSED.value)
        self._last_failure: dict[str, str] = {}
        self._lock = threading.Lock()

    def record_success(self, route_id: str):
        with self._lock:
            self._failures[route_id] = 0
            self._states[route_id] = CircuitState.CLOSED.value

    def record_failure(self, route_id: str):
        with self._lock:
            self._failures[route_id] += 1
            self._last_failure[route_id] = datetime.utcnow().isoformat()
            if self._failures[route_id] >= self.failure_threshold:
                self._states[route_id] = CircuitState.OPEN.value

    def can_request(self, route_id: str) -> bool:
        with self._lock:
            state = self._states[route_id]
            if state == CircuitState.CLOSED.value:
                return True
            if state == CircuitState.OPEN.value:
                # Check if recovery timeout has passed
                last = self._last_failure.get(route_id, "")
                if last:
                    last_time = datetime.fromisoformat(last.replace("Z", ""))
                    if datetime.utcnow() - last_time > timedelta(seconds=self.recovery_timeout):
                        self._states[route_id] = CircuitState.HALF_OPEN.value
                        return True
                return False
            if state == CircuitState.HALF_OPEN.value:
                return True
            return True

    def get_state(self, route_id: str) -> str:
        return self._states.get(route_id, CircuitState.CLOSED.value)

    def reset(self, route_id: str):
        with self._lock:
            self._failures[route_id] = 0
            self._states[route_id] = CircuitState.CLOSED.value


class ApiGatewayService:
    """API Gateway with routing, auth, rate limiting, caching, and monitoring."""

    def __init__(self, max_cache: int = 500, max_usage: int = 10000):
        self._keys: dict[str, ApiKey] = {}  # key_id -> ApiKey
        self._key_lookup: dict[str, str] = {}  # key_hash -> key_id
        self._routes: dict[str, Route] = {}
        self._cache: dict[str, CachedResponse] = {}
        self._usage: deque = deque(maxlen=max_usage)
        self._rate_tracker: dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))  # key_id -> timestamps
        self._circuit = CircuitBreaker()
        self._lock = threading.Lock()
        self._max_cache = max_cache
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._init_default_routes()
        self._init_default_keys()

    def _init_default_routes(self):
        """Initialize default routes for all EvolvixOS services."""
        routes = [
            ("route-staking", "/api/v1/staking/*", "staking-dashboard", "/staking"),
            ("route-notifications", "/api/v1/notifications/*", "notification-center", "/notifications"),
            ("route-cross-chain", "/api/v1/cross-chain/*", "cross-chain-analytics", "/cross-chain"),
            ("route-identity", "/api/v1/identity/*", "identity-service", "/identity"),
            ("route-governance", "/api/v1/governance/*", "governance-service", "/governance"),
            ("route-tokenomics", "/api/v1/tokenomics/*", "tokenomics-service", "/tokenomics"),
            ("route-validators", "/api/v1/validators/*", "validator-service", "/validators"),
            ("route-bridge", "/api/v1/bridge/*", "bridge-service", "/bridge"),
            ("route-plugins", "/api/v1/plugins/*", "plugin-marketplace", "/plugins"),
            ("route-analytics", "/api/v1/analytics/*", "on-chain-analytics", "/analytics"),
            ("route-deployment", "/api/v1/deployment/*", "deployment-service", "/deployment"),
            ("route-contracts", "/api/v1/contracts/*", "smart-contracts", "/contracts"),
        ]
        for rid, path, target, target_path in routes:
            self._routes[rid] = Route(
                route_id=rid, path=path,
                target_service=target, target_path=target_path,
                cache_ttl=30 if "analytics" in target or "cross" in target else 0,
                auth_required=True,
            )

    def _init_default_keys(self):
        """Initialize with a default API key."""
        plaintext = "vk_verdis_default_0000000000000000000000000000000000000000"
        self.create_key("Default Key", scopes=["*"], rate_limit=10000)

    # === API Keys ===

    def create_key(self, name: str, scopes: list = None, rate_limit: int = 1000,
                   expires_days: int = 0, metadata: dict = None) -> tuple[ApiKey, str]:
        """Create a new API key. Returns (key_info, plaintext_key)."""
        plaintext = f"vk_{secrets.token_hex(24)}"
        key_hash = hashlib.sha256(plaintext.encode()).hexdigest()
        key_id = f"key-{secrets.token_hex(8)}"

        expires = ""
        if expires_days > 0:
            expires = (datetime.utcnow() + timedelta(days=expires_days)).isoformat()

        key = ApiKey(
            key_id=key_id, key_hash=key_hash, name=name,
            scopes=scopes or ["*"], rate_limit=rate_limit,
            expires=expires, metadata=metadata or {},
        )

        with self._lock:
            self._keys[key_id] = key
            self._key_lookup[key_hash] = key_id

        logger.info("api_key_created", key_id=key_id, name=name)
        return key, plaintext

    def revoke_key(self, key_id: str) -> bool:
        key = self._keys.get(key_id)
        if not key:
            return False
        key.status = KeyStatus.REVOKED.value
        # Remove from lookup
        self._key_lookup.pop(key.key_hash, None)
        return True

    def validate_key(self, plaintext: str) -> Optional[ApiKey]:
        """Validate an API key and return the key info if valid."""
        key_hash = hashlib.sha256(plaintext.encode()).hexdigest()
        key_id = self._key_lookup.get(key_hash)
        if not key_id:
            return None

        key = self._keys.get(key_id)
        if not key:
            return None
        if key.status != KeyStatus.ACTIVE.value:
            return None
        if key.expires and datetime.utcnow() > datetime.fromisoformat(key.expires.replace("Z", "")):
            key.status = KeyStatus.EXPIRED.value
            return None

        key.last_used = datetime.utcnow().isoformat()
        key.total_requests += 1
        return key

    def list_keys(self, status: str = None) -> list[ApiKey]:
        keys = list(self._keys.values())
        if status:
            keys = [k for k in keys if k.status == status]
        return keys

    def get_key(self, key_id: str) -> Optional[ApiKey]:
        return self._keys.get(key_id)

    def update_key(self, key_id: str, **kwargs) -> Optional[ApiKey]:
        key = self._keys.get(key_id)
        if not key:
            return None
        if "scopes" in kwargs:
            key.scopes = kwargs["scopes"]
        if "rate_limit" in kwargs:
            key.rate_limit = kwargs["rate_limit"]
        if "name" in kwargs:
            key.name = kwargs["name"]
        return key

    # === Routes ===

    def create_route(self, path: str, target_service: str, target_path: str = "",
                     methods: list = None, cache_ttl: int = 0,
                     auth_required: bool = True, allowed_scopes: list = None) -> Route:
        route_id = f"route-{secrets.token_hex(8)}"
        route = Route(
            route_id=route_id, path=path,
            methods=methods or ["GET", "POST", "PUT", "DELETE"],
            target_service=target_service, target_path=target_path,
            cache_ttl=cache_ttl, auth_required=auth_required,
            allowed_scopes=allowed_scopes or [],
        )
        self._routes[route_id] = route
        return route

    def list_routes(self, status: str = None, target_service: str = None) -> list[Route]:
        routes = list(self._routes.values())
        if status:
            routes = [r for r in routes if r.status == status]
        if target_service:
            routes = [r for r in routes if r.target_service == target_service]
        return routes

    def get_route(self, route_id: str) -> Optional[Route]:
        return self._routes.get(route_id)

    def update_route(self, route_id: str, **kwargs) -> Optional[Route]:
        route = self._routes.get(route_id)
        if not route:
            return None
        for k, v in kwargs.items():
            if hasattr(route, k):
                setattr(route, k, v)
        return route

    def delete_route(self, route_id: str) -> bool:
        return self._routes.pop(route_id, None) is not None

    def match_route(self, path: str, method: str) -> Optional[Route]:
        """Match a request path and method to a route."""
        for route in self._routes.values():
            if route.status != RouteStatus.ACTIVE.value:
                continue
            if method not in route.methods:
                continue
            # Simple wildcard matching: /api/v1/staking/* matches /api/v1/staking/anything
            pattern = route.path.replace("*", "")
            if path.startswith(pattern) or path == route.path.replace("/*", ""):
                return route
        return None

    # === Rate Limiting ===

    def check_rate_limit(self, key_id: str, limit: int = None) -> tuple[bool, int]:
        """Check if key is within rate limit. Returns (allowed, remaining)."""
        key = self._keys.get(key_id)
        if not key:
            return False, 0

        limit = limit or key.rate_limit
        now = time.time()
        window = 60  # 1 minute window

        with self._lock:
            # Clean old entries
            timestamps = self._rate_tracker[key_id]
            while timestamps and timestamps[0] < now - window:
                timestamps.popleft()

            if len(timestamps) >= limit:
                return False, 0

            timestamps.append(now)
            remaining = limit - len(timestamps)
            return True, remaining

    # === Caching ===

    def get_cached(self, cache_key: str) -> Optional[CachedResponse]:
        cached = self._cache.get(cache_key)
        if not cached:
            return None
        if cached.is_expired():
            del self._cache[cache_key]
            return None
        cached.hit_count += 1
        return cached

    def set_cached(self, cache_key: str, body: str, status_code: int = 200,
                   headers: dict = None, ttl: int = 30) -> CachedResponse:
        # Evict if cache is full
        if len(self._cache) >= self._max_cache:
            oldest = min(self._cache.keys(), key=lambda k: self._cache[k].cached_at)
            del self._cache[oldest]

        cached = CachedResponse(
            key=cache_key, body=body, status_code=status_code,
            headers=headers or {},
            expires_at=(datetime.utcnow() + timedelta(seconds=ttl)).isoformat(),
        )
        self._cache[cache_key] = cached
        return cached

    def clear_cache(self, route_id: str = None) -> int:
        if route_id:
            to_remove = [k for k, v in self._cache.items() if route_id in k]
            for k in to_remove:
                del self._cache[k]
            return len(to_remove)
        count = len(self._cache)
        self._cache.clear()
        return count

    def get_cache_stats(self) -> dict:
        total_hits = sum(c.hit_count for c in self._cache.values())
        return {
            "cached_entries": len(self._cache),
            "total_hits": total_hits,
            "max_cache": self._max_cache,
            "hit_rate": round(total_hits / max(1, total_hits + len(self._usage)), 2),
        }

    # === Usage Tracking ===

    def record_usage(self, key_id: str, route_id: str, method: str, path: str,
                     status_code: int, latency_ms: float, cached: bool = False):
        record = UsageRecord(
            key_id=key_id, route_id=route_id, method=method, path=path,
            status_code=status_code, latency_ms=latency_ms, cached=cached,
        )
        self._usage.append(record)

        # Update route stats
        route = self._routes.get(route_id)
        if route:
            route.request_count += 1
            if status_code >= 400:
                route.error_count += 1
            # Running average latency
            route.avg_latency_ms = round((route.avg_latency_ms * (route.request_count - 1) + latency_ms) / route.request_count, 2)

    def list_usage(self, key_id: str = None, route_id: str = None, limit: int = 50) -> list[dict]:
        usage = list(self._usage)
        if key_id:
            usage = [u for u in usage if u.key_id == key_id]
        if route_id:
            usage = [u for u in usage if u.route_id == route_id]
        usage.reverse()
        return [asdict(u) for u in usage[:limit]]

    def get_usage_stats(self, hours: int = 24) -> dict:
        cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        recent = [u for u in self._usage if u.timestamp >= cutoff]
        by_route = defaultdict(int)
        by_key = defaultdict(int)
        by_status = defaultdict(int)
        cached_count = 0
        latencies = []

        for u in recent:
            by_route[u.route_id] += 1
            by_key[u.key_id] += 1
            by_status[u.status_code] += 1
            if u.cached:
                cached_count += 1
            latencies.append(u.latency_ms)

        return {
            "total_requests": len(recent),
            "cached_requests": cached_count,
            "cache_hit_rate": round(cached_count / max(1, len(recent)), 4),
            "avg_latency_ms": round(sum(latencies) / max(1, len(latencies)), 2),
            "p95_latency_ms": round(sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0, 2),
            "by_route": dict(by_route),
            "by_key": dict(by_key),
            "by_status": dict(by_status),
        }

    # === Circuit Breaker ===

    def get_circuit_state(self, route_id: str) -> str:
        return self._circuit.get_state(route_id)

    def reset_circuit(self, route_id: str) -> bool:
        self._circuit.reset(route_id)
        return True

    def list_circuits(self) -> list[dict]:
        return [
            {"route_id": rid, "state": self._circuit.get_state(rid), "failures": self._circuit._failures.get(rid, 0)}
            for rid in self._routes
        ]

    # === Health Checks ===

    def check_service_health(self, target_service: str) -> dict:
        """Check health of a target service (simulated)."""
        routes = [r for r in self._routes.values() if r.target_service == target_service]
        total = sum(r.request_count for r in routes)
        errors = sum(r.error_count for r in routes)
        error_rate = (errors / max(1, total)) * 100

        healthy = error_rate < 10
        return {
            "service": target_service,
            "healthy": healthy,
            "total_requests": total,
            "error_count": errors,
            "error_rate": round(error_rate, 2),
            "routes": len(routes),
            "avg_latency_ms": round(sum(r.avg_latency_ms for r in routes) / max(1, len(routes)), 2),
        }

    def list_service_health(self) -> list[dict]:
        services = set(r.target_service for r in self._routes.values())
        return [self.check_service_health(s) for s in sorted(services)]

    # === Dashboard ===

    def get_dashboard(self) -> dict:
        return {
            "keys": {"total": len(self._keys), "active": sum(1 for k in self._keys.values() if k.status == "active")},
            "routes": {"total": len(self._routes), "active": sum(1 for r in self._routes.values() if r.status == "active")},
            "cache": self.get_cache_stats(),
            "usage_24h": self.get_usage_stats(24),
            "circuits": self.list_circuits(),
            "services": self.list_service_health(),
            "monitoring": self._monitoring,
        }

    # === Monitoring ===

    def start_monitoring(self, interval: int = 60):
        if self._monitoring:
            return
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, args=(interval,), daemon=True)
        self._monitor_thread.start()
        logger.info("gateway_monitoring_started", interval=interval)

    def stop_monitoring(self):
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)

    def _monitor_loop(self, interval: int):
        while self._monitoring:
            try:
                # Check for expired keys
                now = datetime.utcnow()
                for key in self._keys.values():
                    if key.status == "active" and key.expires:
                        try:
                            exp = datetime.fromisoformat(key.expires.replace("Z", ""))
                            if now > exp:
                                key.status = "expired"
                                self._key_lookup.pop(key.key_hash, None)
                                logger.info("key_expired", key_id=key.key_id)
                        except Exception:
                            pass
                # Clean expired cache
                expired = [k for k, v in self._cache.items() if v.is_expired()]
                for k in expired:
                    del self._cache[k]
                if expired:
                    logger.info("cache_expired_cleaned", count=len(expired))
            except Exception as e:
                logger.error("monitor_error", error=str(e))
            time.sleep(interval)

    def is_monitoring(self) -> bool:
        return self._monitoring


_service: Optional[ApiGatewayService] = None

def get_api_gateway_service() -> ApiGatewayService:
    global _service
    if _service is None:
        _service = ApiGatewayService()
    return _service
