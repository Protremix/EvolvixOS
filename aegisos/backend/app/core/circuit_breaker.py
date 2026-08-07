"""
Circuit Breaker Pattern — Phase 50 Security Fix

Prevents cascading failures on external API calls.
States: closed → open (after N failures) → half-open (timeout) → closed (success)
"""

import time
import threading
from typing import Optional, Callable, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict
from app.core.logging import get_logger

logger = get_logger("core.circuit_breaker")


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitStats:
    total_calls: int = 0
    successful: int = 0
    failed: int = 0
    rejected: int = 0
    last_failure: str = ""
    last_success: str = ""
    state_changes: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


class CircuitBreaker:
    """Circuit breaker for a single service/endpoint."""

    def __init__(self, name: str, failure_threshold: int = 5,
                 recovery_timeout: int = 60, half_open_max_calls: int = 3):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        self._state = CircuitState.CLOSED.value
        self._failure_count = 0
        self._success_count = 0
        self._half_open_calls = 0
        self._last_failure_time: Optional[datetime] = None
        self._lock = threading.Lock()
        self.stats = CircuitStats()

    @property
    def state(self) -> str:
        if self._state == CircuitState.OPEN.value:
            if self._last_failure_time:
                elapsed = (datetime.utcnow() - self._last_failure_time).total_seconds()
                if elapsed >= self.recovery_timeout:
                    with self._lock:
                        self._state = CircuitState.HALF_OPEN.value
                        self._half_open_calls = 0
                        self.stats.state_changes.append({
                            "from": CircuitState.OPEN.value,
                            "to": CircuitState.HALF_OPEN.value,
                            "timestamp": datetime.utcnow().isoformat(),
                        })
        return self._state

    def can_execute(self) -> bool:
        current = self.state
        if current == CircuitState.CLOSED.value:
            return True
        if current == CircuitState.HALF_OPEN.value:
            return self._half_open_calls < self.half_open_max_calls
        return False

    def record_success(self):
        with self._lock:
            self.stats.total_calls += 1
            self.stats.successful += 1
            self.stats.last_success = datetime.utcnow().isoformat()

            if self._state == CircuitState.HALF_OPEN.value:
                self._success_count += 1
                if self._success_count >= self.half_open_max_calls:
                    self._state = CircuitState.CLOSED.value
                    self._failure_count = 0
                    self.stats.state_changes.append({
                        "from": CircuitState.HALF_OPEN.value,
                        "to": CircuitState.CLOSED.value,
                        "timestamp": datetime.utcnow().isoformat(),
                    })
            else:
                self._failure_count = 0

    def record_failure(self):
        with self._lock:
            self.stats.total_calls += 1
            self.stats.failed += 1
            self.stats.last_failure = datetime.utcnow().isoformat()
            self._last_failure_time = datetime.utcnow()

            if self._state == CircuitState.HALF_OPEN.value:
                self._state = CircuitState.OPEN.value
                self._half_open_calls = 0
                self.stats.state_changes.append({
                    "from": CircuitState.HALF_OPEN.value,
                    "to": CircuitState.OPEN.value,
                    "timestamp": datetime.utcnow().isoformat(),
                })
            else:
                self._failure_count += 1
                if self._failure_count >= self.failure_threshold:
                    self._state = CircuitState.OPEN.value
                    self.stats.state_changes.append({
                        "from": CircuitState.CLOSED.value,
                        "to": CircuitState.OPEN.value,
                        "timestamp": datetime.utcnow().isoformat(),
                    })

    def record_rejection(self):
        self.stats.total_calls += 1
        self.stats.rejected += 1

    def reset(self):
        with self._lock:
            self._state = CircuitState.CLOSED.value
            self._failure_count = 0
            self._success_count = 0
            self._half_open_calls = 0
            self._last_failure_time = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "state": self.state,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout,
            "failure_count": self._failure_count,
            "stats": self.stats.to_dict(),
        }


class CircuitBreakerRegistry:
    """Registry for all circuit breakers."""

    def __init__(self):
        self._breakers: dict[str, CircuitBreaker] = {}
        self._lock = threading.Lock()

    def get_or_create(self, name: str, failure_threshold: int = 5,
                      recovery_timeout: int = 60) -> CircuitBreaker:
        with self._lock:
            if name not in self._breakers:
                self._breakers[name] = CircuitBreaker(
                    name, failure_threshold, recovery_timeout
                )
            return self._breakers[name]

    def get(self, name: str) -> Optional[CircuitBreaker]:
        return self._breakers.get(name)

    def list_all(self) -> list[CircuitBreaker]:
        return list(self._breakers.values())

    def list_states(self) -> list[dict]:
        return [b.to_dict() for b in self._breakers.values()]

    def reset_all(self):
        for b in self._breakers.values():
            b.reset()


_registry: Optional[CircuitBreakerRegistry] = None

def get_circuit_breaker_registry() -> CircuitBreakerRegistry:
    global _registry
    if _registry is None:
        _registry = CircuitBreakerRegistry()
        # Pre-register external services
        _registry.get_or_create("verdis_rpc", failure_threshold=5, recovery_timeout=30)
        _registry.get_or_create("bridge_relayer", failure_threshold=3, recovery_timeout=60)
        _registry.get_or_create("external_api", failure_threshold=5, recovery_timeout=60)
        _registry.get_or_create("notification_service", failure_threshold=10, recovery_timeout=120)
    return _registry


def with_circuit_breaker(name: str, failure_threshold: int = 5,
                         recovery_timeout: int = 60) -> Callable:
    """Decorator to wrap a function with a circuit breaker."""
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs) -> Any:
            registry = get_circuit_breaker_registry()
            breaker = registry.get_or_create(name, failure_threshold, recovery_timeout)

            if not breaker.can_execute():
                breaker.record_rejection()
                raise Exception(f"Circuit breaker '{name}' is OPEN - calls rejected")

            try:
                result = func(*args, **kwargs)
                breaker.record_success()
                return result
            except Exception as e:
                breaker.record_failure()
                raise
        return wrapper
    return decorator
