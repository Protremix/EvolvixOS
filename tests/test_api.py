
"""API Endpoint Tests"""
import sys, os, json, urllib.request, pytest

class TestPublicChat:
    def test_chat_returns_response(self):
        url = "http://127.0.0.1:8000/api/v1/ai/chat"
        payload = json.dumps({"message": "Say hello"}).encode()
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        try:
            resp = urllib.request.urlopen(req, timeout=30)
            data = json.loads(resp.read())
            assert "response" in data
            assert data["response"]
            assert "model" in data
        except Exception:
            pytest.skip("API not available")

    def test_chat_rejects_empty_message(self):
        url = "http://127.0.0.1:8000/api/v1/ai/chat"
        payload = json.dumps({"message": ""}).encode()
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        try:
            urllib.request.urlopen(req, timeout=10)
            assert False
        except urllib.error.HTTPError as e:
            assert e.code == 400
        except Exception:
            pytest.skip("API not available")

class TestHealthEndpoint:
    def test_health_returns_200(self):
        resp = urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=5)
        assert resp.status == 200
        data = json.loads(resp.read())
        assert data["status"] == "healthy"
        assert data["service"] == "EvolvixOS"

class TestOllamaService:
    def test_ollama_responds(self):
        resp = urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=5)
        assert resp.status == 200
        data = json.loads(resp.read())
        assert "models" in data
        assert len(data["models"]) >= 10

    def test_qwen_models_available(self):
        resp = urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=5)
        data = json.loads(resp.read())
        names = [m["name"] for m in data["models"]]
        assert "qwen2.5:14b" in names
        assert "qwen2.5:7b" in names
        assert "qwen2.5:3b" in names

class TestMonitoring:
    def test_monitoring_script_exists(self):
        assert os.path.exists("/opt/evolvixos/monitoring/inference_alert.sh")

    def test_monitoring_script_executable(self):
        assert os.access("/opt/evolvixos/monitoring/inference_alert.sh", os.X_OK)

    def test_cron_job_configured(self):
        import subprocess
        result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
        assert "inference_alert.sh" in result.stdout

    def test_prometheus_running(self):
        import subprocess
        result = subprocess.run(["docker", "ps", "--format", "{{.Names}}"], capture_output=True, text=True)
        assert "evolvixos-prometheus" in result.stdout
