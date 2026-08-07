"""
EvolvixOS Worker — standalone distributed executor worker.

Runs as a separate process for containerized deployment.
Polls Redis for tasks, executes them using the workflow engine,
and reports results back.
"""

import json
import os
import signal
import sys
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional

from structlog import get_logger

logger = get_logger(__name__)

# Worker state
_worker_running = True
_tasks_executed = 0
_tasks_failed = 0
_start_time = time.time()


class WorkerHealthHandler(BaseHTTPRequestHandler):
    """HTTP handler for worker health checks."""

    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            status = {
                "status": "healthy" if _worker_running else "stopping",
                "worker_id": os.environ.get("WORKER_ID", "worker-0"),
                "tasks_executed": _tasks_executed,
                "tasks_failed": _tasks_failed,
                "uptime_seconds": int(time.time() - _start_time),
            }
            self.wfile.write(json.dumps(status).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # Suppress access logs


def init_workflow_engine():
    """Initialize the workflow engine with all 8 agents."""
    from app.ai.workflow_engine import get_workflow_engine
    engine = get_workflow_engine()
    # The get_workflow_engine already registers all agents
    return engine


def init_executor(max_workers: int = 4):
    """Initialize the distributed executor."""
    from app.ai.distributed_executor import DistributedExecutor
    return DistributedExecutor(max_workers=max_workers)


def poll_for_tasks(engine, executor, redis_client=None):
    """
    Poll for tasks from Redis (or in-memory fallback).
    
    In production, this polls a Redis list for task messages.
    In development without Redis, it can be used with direct dispatch.
    """
    global _tasks_executed, _tasks_failed

    if redis_client:
        try:
            # Pop task from Redis queue (non-blocking)
            task_data = redis_client.lpop("evolvixos:task_queue")
            if task_data:
                task_msg = json.loads(task_data)
                task_type_str = task_msg.get("task_type")
                task_data_payload = task_msg.get("data", {})

                from app.ai.agents.base_agent import TaskType
                try:
                    task_type = TaskType(task_type_str)
                except ValueError:
                    logger.error("invalid_task_type", task_type=task_type_str)
                    return

                # Dispatch task
                task_id = executor.dispatch(engine, task_type, task_data_payload)
                if task_id:
                    logger.info("task_dispatched", task_id=task_id, task_type=task_type_str)

                    # Wait for result (in worker mode, we can block)
                    result = executor.get_result(task_id, timeout=120)
                    if result and result.status.value == "completed":
                        _tasks_executed += 1
                        # Push result back to Redis
                        if redis_client:
                            redis_client.lpush(
                                f"evolvixos:results:{task_msg.get('request_id', 'unknown')}",
                                json.dumps({
                                    "task_id": task_id,
                                    "status": result.status.value,
                                    "content": result.content,
                                })
                            )
                    else:
                        _tasks_failed += 1
        except Exception as e:
            logger.error("task_poll_error", error=str(e))


def start_health_server(port: int = 8001):
    """Start the health check HTTP server in a background thread."""
    server = HTTPServer(("0.0.0.0", port), WorkerHealthHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    logger.info("health_server_started", port=port)
    return server


def signal_handler(signum, frame):
    """Handle shutdown signals."""
    global _worker_running
    logger.info("shutdown_signal_received", signal=signum)
    _worker_running = False


def run_worker(max_workers: int = 4, health_port: int = 8001, poll_interval: float = 1.0):
    """
    Run the EvolvixOS worker process.

    Args:
        max_workers: Max concurrent task executions
        health_port: Port for health check HTTP server
        poll_interval: Seconds between Redis polls
    """
    global _worker_running

    # Setup signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    logger.info(
        "worker_starting",
        max_workers=max_workers,
        health_port=health_port,
        worker_id=os.environ.get("WORKER_ID", "worker-0"),
    )

    # Initialize components
    engine = init_workflow_engine()
    executor = init_executor(max_workers)

    # Try to connect to Redis (optional)
    redis_client = None
    try:
        import redis
        redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        redis_client = redis.from_url(redis_url)
        redis_client.ping()
        logger.info("redis_connected", url=redis_url)
    except ImportError:
        logger.warn("redis_not_available", reason="redis package not installed")
    except Exception as e:
        logger.warn("redis_connection_failed", error=str(e))

    # Start health check server
    health_server = start_health_server(health_port)

    # Main polling loop
    logger.info("worker_ready", polling=redis_client is not None)

    while _worker_running:
        if redis_client:
            poll_for_tasks(engine, executor, redis_client)
        time.sleep(poll_interval)

    # Graceful shutdown
    logger.info("worker_shutting_down", tasks_executed=_tasks_executed, tasks_failed=_tasks_failed)
    health_server.shutdown()
    executor.shutdown(wait=True)
    logger.info("worker_stopped")


if __name__ == "__main__":
    max_workers = int(os.environ.get("WORKER_MAX_TASKS", "4"))
    health_port = int(os.environ.get("WORKER_HEALTH_PORT", "8001"))
    run_worker(max_workers=max_workers, health_port=health_port)
