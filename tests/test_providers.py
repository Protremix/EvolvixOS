"""Model Provider Tests"""
import sys, os, urllib.request, pytest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def server_available(url, timeout=2):
    try:
        urllib.request.urlopen(url, timeout=timeout)
        return True
    except Exception:
        return False

try:
    if os.path.exists("/opt/evolvixos/.env"):
        for line in open("/opt/evolvixos/.env"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                v = v.strip().strip("'").strip('"')
                if k not in os.environ: os.environ[k] = v
    from v10.providers.ollama import OllamaProvider
    from v10.providers.groq import GroqProvider
    HAS_OLLAMA = server_available("http://127.0.0.1:11434/api/tags")
    HAS_PROVIDERS = True
except Exception:
    HAS_PROVIDERS = False
    HAS_OLLAMA = False

pytestmark = pytest.mark.skipif(not (HAS_PROVIDERS and HAS_OLLAMA), reason="Providers or Ollama server not available")


class TestOllamaProvider:
    def test_is_available(self):
        assert OllamaProvider().is_available()

    def test_default_model(self):
        assert OllamaProvider().default_model == "qwen2.5:14b"

    def test_models_by_task(self):
        p = OllamaProvider()
        assert isinstance(p.models_by_task, dict)
        assert len(p.models_by_task) >= 4

    def test_chat_accepts_model_param(self):
        assert "model" in OllamaProvider().chat.__code__.co_varnames

    def test_chat_returns_response(self):
        r = OllamaProvider().chat(messages=[{"role":"user","content":"Say hello"}], max_tokens=10)
        assert r is not None
        assert r.content
        assert "qwen" in r.model.lower()
        assert r.latency_ms > 0

class TestGroqProvider:
    def test_is_available(self):
        assert GroqProvider().is_available()

    def test_chat_accepts_model_param(self):
        assert "model" in GroqProvider().chat.__code__.co_varnames

    def test_chat_returns_response(self):
        r = GroqProvider().chat(messages=[{"role":"user","content":"Say hello"}], max_tokens=200)
        assert r is not None
        assert r.content
        assert r.latency_ms > 0
        assert r.latency_ms < 5000

class TestTelegramBot:
    def test_gemini_model_updated(self):
        telegram_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "messaging", "telegram_bot.py")
        if not os.path.exists(telegram_path):
            pytest.skip("telegram_bot.py not found")
        with open(telegram_path) as f:
            content = f.read()
        assert "gemini-flash-latest" in content
        assert "gemini-2.0-flash-exp" not in content
