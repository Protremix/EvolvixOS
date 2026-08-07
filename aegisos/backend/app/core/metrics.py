"""
Prometheus metrics collection for EvolvixOS.

Exposes metrics at /metrics endpoint for Prometheus scraping.
"""

import time
from typing import Callable

from fastapi import FastAPI, Request, Response
from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    generate_latest,
    CONTENT_TYPE_LATEST,
)

# ============================================================
# Metrics Definitions
# ============================================================

# HTTP metrics
http_requests_total = Counter(
    "evolvixos_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

http_request_duration_seconds = Histogram(
    "evolvixos_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

http_requests_in_progress = Gauge(
    "evolvixos_http_requests_in_progress",
    "HTTP requests currently in progress",
)

# Database metrics
db_connections_active = Gauge(
    "evolvixos_db_connections_active",
    "Active database connections",
)

db_query_duration_seconds = Histogram(
    "evolvixos_db_query_duration_seconds",
    "Database query duration in seconds",
    buckets=[0.001, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0],
)

# Redis metrics
redis_operations_total = Counter(
    "evolvixos_redis_operations_total",
    "Total Redis operations",
    ["operation"],
)

# Business metrics
users_total = Gauge("evolvixos_users_total", "Total registered users")
organizations_total = Gauge("evolvixos_organizations_total", "Total organizations")
projects_total = Gauge("evolvixos_projects_total", "Total projects")
active_sessions = Gauge("evolvixos_active_sessions", "Active user sessions")

# Event bus metrics
events_published_total = Counter(
    "evolvixos_events_published_total",
    "Total events published",
    ["channel"],
)

events_processed_total = Counter(
    "evolvixos_events_processed_total",
    "Total events processed",
    ["channel", "status"],
)


def setup_metrics(app: FastAPI) -> None:
    """
    Set up Prometheus metrics middleware and endpoint.

    Args:
        app: FastAPI application instance.
    """

    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next: Callable) -> Response:
        """Middleware to collect HTTP metrics."""
        method = request.method
        # Normalize endpoint (remove path params)
        endpoint = request.url.path

        http_requests_in_progress.inc()
        start_time = time.time()

        try:
            response = await call_next(request)
            duration = time.time() - start_time
            status = str(response.status_code)

            http_requests_total.labels(method=method, endpoint=endpoint, status=status).inc()
            http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)

            return response
        except Exception as e:
            duration = time.time() - start_time
            http_requests_total.labels(method=method, endpoint=endpoint, status="500").inc()
            http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)
            raise
        finally:
            http_requests_in_progress.dec()

    @app.get("/metrics", include_in_schema=False)
    async def metrics() -> Response:
        """Prometheus metrics endpoint."""
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
