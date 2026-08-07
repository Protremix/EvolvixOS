"""
Local Monitor Service — Phase 28

Monitors local development environment health, collects metrics,
and provides a dashboard view of all running services.
"""

import time
import psutil
import threading
from typing import Optional
from datetime import datetime
from dataclasses import dataclass, field, asdict
from collections import defaultdict, deque
from app.core.logging import get_logger

logger = get_logger("service.local_monitor")


@dataclass
class ServiceHealth:
    name: str
    status: str  # healthy, degraded, offline
    url: str = ""
    response_time_ms: float = 0
    last_check: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    details: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class MetricPoint:
    timestamp: str
    value: float


class LocalMonitor:
    """Monitors local development services and collects metrics."""

    def __init__(self, max_history: int = 1000):
        self._services: dict[str, ServiceHealth] = {}
        self._metrics: dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        self._lock = threading.Lock()
        self._monitoring = False
        self._thread: Optional[threading.Thread] = None

        # Define services to monitor
        self._service_configs = [
            {"name": "EvolvixOS Backend", "url": "http://localhost:8000/health"},
            {"name": "EvolvixOS Frontend", "url": "http://localhost:5173"},
            {"name": "Redis", "url": "http://localhost:6379"},
            {"name": "Verdis Node", "url": "http://localhost:9933"},
        ]

    def check_service(self, name: str, url: str) -> ServiceHealth:
        """Check a single service health."""
        import urllib.request
        start = time.time()
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=3) as resp:
                elapsed = (time.time() - start) * 1000
                health = ServiceHealth(
                    name=name, status="healthy", url=url,
                    response_time_ms=round(elapsed, 2),
                    details={"status_code": resp.status}
                )
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            health = ServiceHealth(
                name=name, status="offline", url=url,
                response_time_ms=round(elapsed, 2),
                details={"error": str(e)[:100]}
            )

        with self._lock:
            self._services[name] = health
        return health

    def check_all(self) -> list[ServiceHealth]:
        """Check all configured services."""
        return [self.check_service(s["name"], s["url"]) for s in self._service_configs]

    def get_system_metrics(self) -> dict:
        """Collect system metrics (CPU, memory, disk)."""
        try:
            cpu = psutil.cpu_percent(interval=0.5)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            metrics = {
                "cpu_percent": cpu,
                "memory_total_gb": round(memory.total / (1024**3), 2),
                "memory_used_gb": round(memory.used / (1024**3), 2),
                "memory_percent": memory.percent,
                "disk_total_gb": round(disk.total / (1024**3), 2),
                "disk_used_gb": round(disk.used / (1024**3), 2),
                "disk_percent": round(disk.used / disk.total * 100, 2),
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Record in history
            with self._lock:
                self._metrics["cpu"].append(MetricPoint(
                    timestamp=metrics["timestamp"], value=cpu
                ))
                self._metrics["memory"].append(MetricPoint(
                    timestamp=metrics["timestamp"], value=memory.percent
                ))

            return metrics
        except Exception as e:
            return {"error": str(e), "timestamp": datetime.utcnow().isoformat()}

    def get_all_health(self) -> dict:
        """Get health of all services + system metrics."""
        services = list(self._services.values())
        system = self.get_system_metrics()

        healthy = sum(1 for s in services if s.status == "healthy")
        offline = sum(1 for s in services if s.status == "offline")

        return {
            "services": [s.to_dict() for s in services],
            "system": system,
            "summary": {
                "total": len(services),
                "healthy": healthy,
                "offline": offline,
                "overall": "healthy" if offline == 0 else "degraded" if healthy > 0 else "offline",
            }
        }

    def get_metrics_history(self, metric_name: str = "cpu", limit: int = 100) -> list[dict]:
        """Get historical metric data points."""
        with self._lock:
            points = list(self._metrics.get(metric_name, []))
        return [{"timestamp": p.timestamp, "value": p.value} for p in points[-limit:]]

    def start_monitoring(self, interval: int = 30):
        """Start background monitoring."""
        if self._monitoring:
            return

        self._monitoring = True

        def _monitor():
            while self._monitoring:
                self.check_all()
                self.get_system_metrics()
                time.sleep(interval)

        self._thread = threading.Thread(target=_monitor, daemon=True)
        self._thread.start()
        logger.info("local_monitoring_started", interval=interval)

    def stop_monitoring(self):
        """Stop background monitoring."""
        self._monitoring = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("local_monitoring_stopped")


_service: Optional[LocalMonitor] = None

def get_local_monitor() -> LocalMonitor:
    global _service
    if _service is None:
        _service = LocalMonitor()
    return _service
