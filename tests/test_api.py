"""API Endpoint Tests"""
import sys, os, json, urllib.request, pytest

def check_server(url, timeout=2):
    """Check if server is reachable."""
    try:
        urllib.request.urlopen(url, timeout=timeout)
        return True
    except Exception:
        return False

HAS_API = check_server("http://127.0.0.1:8000/health")
HAS_OLLAMA = check_server("http://127.0.0.1:11434/api/tags")


class TestPublicChat:
    def test_chat_returns_response(self):
        if not HAS_API:
            pytest.skip("API server not available")
        url = "http://127.0.0.1:8000/api/v1/ai/chat"
        payload = json.dumps({"message": "Say hello"}).encode()
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        resp = urllib.request.urlopen(req, timeout=30)
        data = json.loads(resp.read())
        assert "response" in data
        assert data["response"]
        assert "model" in data

    def test_chat_rejects_empty_message(self):
        if not HAS_API:
            pytest.skip("API server not available")
        url = "http://127.0.0.1:8000/api/v1/ai/chat"
        payload = json.dumps({"message": ""}).encode()
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        try:
            urllib.request.urlopen(req, timeout=10)
            assert False
        except urllib.error.HTTPError as e:
            assert e.code == 400

class TestHealthEndpoint:
    def test_health_returns_200(self):
        if not HAS_API:
            pytest.skip("API server not available")
        resp = urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=5)
        assert resp.status == 200
        data = json.loads(resp.read())
        assert data["status"] == "healthy"
        assert data["service"] == "EvolvixOS"

class TestOllamaService:
    def test_ollama_responds(self):
        if not HAS_OLLAMA:
            pytest.skip("Ollama not available")
        resp = urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=5)
        assert resp.status == 200
        data = json.loads(resp.read())
        assert "models" in data
        assert len(data["models"]) >= 10

    def test_qwen_models_available(self):
        if not HAS_OLLAMA:
            pytest.skip("Ollama not available")
        resp = urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=5)
        data = json.loads(resp.read())
        names = [m["name"] for m in data["models"]]
        assert "qwen2.5:14b" in names
        assert "qwen2.5:7b" in names
        assert "qwen2.5:3b" in names

class TestMonitoring:
    def test_monitoring_script_exists(self):
        # This checks if the monitoring script exists in the repo
        script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "monitoring", "inference_alert.sh")
        if not os.path.exists(script_path):
            pytest.skip("Monitoring script not in repo (server-only file)")
        assert os.access(script_path, os.X_OK)

    def test_cron_job_configured(self):
        import subprocess
        result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
        if result.returncode != 0:
            pytest.skip("crontab not available")
        assert "inference_alert.sh" in result.stdout

    def test_prometheus_running(self):
        import subprocess
        result = subprocess.run(["docker", "ps", "--format", "{{.Names}}"], capture_output=True, text=True)
        if result.returncode != 0:
            pytest.skip("docker not available")
        assert "evolvixos-prometheus" in result.stdout
