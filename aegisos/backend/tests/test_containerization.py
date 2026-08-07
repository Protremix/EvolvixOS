"""
Tests for containerization — Docker configs, worker module, and environment.
"""

import json
import os
import time
import socket
import pytest
from http.client import HTTPConnection

from app.ai.worker import WorkerHealthHandler, _worker_running


# ============================================================
# Dockerfile Tests
# ============================================================

class TestDockerfiles:
    def test_dockerfile_api_exists(self):
        path = os.path.join(os.path.dirname(__file__), "..", "Dockerfile")
        assert os.path.exists(path), "Dockerfile not found"
        
        with open(path) as f:
            content = f.read()
        assert "python:3.11-slim" in content
        assert "uvicorn" in content
        assert "aegis" in content  # non-root user
        assert "HEALTHCHECK" in content
        assert "8000" in content

    def test_dockerfile_worker_exists(self):
        path = os.path.join(os.path.dirname(__file__), "..", "Dockerfile.worker")
        assert os.path.exists(path), "Dockerfile.worker not found"
        
        with open(path) as f:
            content = f.read()
        assert "python:3.11-slim" in content
        assert "app.ai.worker" in content
        assert "aegis" in content
        assert "HEALTHCHECK" in content
        assert "8001" in content


# ============================================================
# Docker Compose Tests
# ============================================================

class TestDockerCompose:
    def test_docker_compose_exists(self):
        path = os.path.join(os.path.dirname(__file__), "..", "docker-compose.yml")
        assert os.path.exists(path), "docker-compose.yml not found"

    def test_docker_compose_valid_yaml(self):
        try:
            import yaml
        except ImportError:
            pytest.skip("PyYAML not installed")
        
        path = os.path.join(os.path.dirname(__file__), "..", "docker-compose.yml")
        with open(path) as f:
            compose = yaml.safe_load(f)
        
        assert "services" in compose
        assert "postgres" in compose["services"]
        assert "redis" in compose["services"]
        assert "api" in compose["services"]
        assert "worker-1" in compose["services"]
        assert "worker-2" in compose["services"]
        assert "worker-3" in compose["services"]
        assert "nginx" in compose["services"]
        assert "volumes" in compose
        assert "networks" in compose

    def test_docker_compose_postgres_config(self):
        try:
            import yaml
        except ImportError:
            pytest.skip("PyYAML not installed")
        
        path = os.path.join(os.path.dirname(__file__), "..", "docker-compose.yml")
        with open(path) as f:
            compose = yaml.safe_load(f)
        
        pg = compose["services"]["postgres"]
        assert "pgvector" in pg["image"]
        assert pg["environment"]["POSTGRES_USER"] == "aegis"
        assert pg["environment"]["POSTGRES_DB"] == "evolvixos"

    def test_docker_compose_worker_config(self):
        try:
            import yaml
        except ImportError:
            pytest.skip("PyYAML not installed")
        
        path = os.path.join(os.path.dirname(__file__), "..", "docker-compose.yml")
        with open(path) as f:
            compose = yaml.safe_load(f)
        
        worker = compose["services"]["worker-1"]
        env = worker["environment"]
        # Handle both list and dict formats
        if isinstance(env, list):
            env_dict = {}
            for item in env:
                key, _, val = item.partition("=")
                env_dict[key] = val
            env = env_dict
        assert env.get("WORKER_ID") == "worker-1"
        assert "OPENAI_API_KEY_2" in env
        assert "REDIS_URL" in env


# ============================================================
# Environment Template Tests
# ============================================================

class TestEnvExample:
    def test_env_example_exists(self):
        path = os.path.join(os.path.dirname(__file__), "..", ".env.example")
        assert os.path.exists(path), ".env.example not found"

    def test_env_example_has_required_vars(self):
        path = os.path.join(os.path.dirname(__file__), "..", ".env.example")
        with open(path) as f:
            content = f.read()
        
        required_vars = [
            "DATABASE_URL",
            "REDIS_URL",
            "OPENAI_API_KEY_2",
            "ANTHROPIC_API_KEY",
            "SECRET_KEY",
        ]
        for var in required_vars:
            assert var in content, f"Missing {var} in .env.example"


# ============================================================
# Nginx Config Tests
# ============================================================

class TestNginxConfig:
    def test_nginx_config_exists(self):
        path = os.path.join(os.path.dirname(__file__), "..", "docker", "nginx.conf")
        assert os.path.exists(path), "nginx.conf not found"

    def test_nginx_config_content(self):
        path = os.path.join(os.path.dirname(__file__), "..", "docker", "nginx.conf")
        with open(path) as f:
            content = f.read()
        
        assert "upstream" in content
        assert "evolvixos_api" in content
        assert "proxy_pass" in content
        assert "80" in content


# ============================================================
# Worker Module Tests
# ============================================================

class TestWorkerModule:
    def test_worker_imports(self):
        from app.ai.worker import run_worker, WorkerHealthHandler
        assert callable(run_worker)
        assert WorkerHealthHandler is not None

    def test_worker_health_handler(self):
        """Test the worker health handler returns proper status."""
        import threading
        from http.server import HTTPServer

        # Start a test health server
        server = HTTPServer(("127.0.0.1", 18099), WorkerHealthHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        
        time.sleep(0.5)
        
        # Make request
        import urllib.request
        try:
            resp = urllib.request.urlopen("http://127.0.0.1:18099/health", timeout=5)
            data = json.loads(resp.read().decode())
            assert "status" in data
            assert "worker_id" in data
            assert "tasks_executed" in data
            assert "uptime_seconds" in data
        finally:
            server.shutdown()
            thread.join(timeout=2)

    def test_worker_health_404(self):
        """Test the worker health handler returns 404 for unknown paths."""
        import threading
        from http.server import HTTPServer
        import urllib.request

        server = HTTPServer(("127.0.0.1", 18098), WorkerHealthHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        
        time.sleep(0.5)
        
        try:
            urllib.request.urlopen("http://127.0.0.1:18098/unknown", timeout=5)
            assert False, "Should have raised HTTPError"
        except urllib.error.HTTPError as e:
            assert e.code == 404
        finally:
            server.shutdown()
            thread.join(timeout=2)
