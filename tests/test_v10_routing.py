"""V10 Model Routing Tests"""
import sys, os, json, urllib.request, pytest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def server_available(url, timeout=2):
    try:
        urllib.request.urlopen(url, timeout=timeout)
        return True
    except Exception:
        return False

# Skip entire module if v10 modules or Ollama server not available
try:
    if os.path.exists("/opt/evolvixos/.env"):
        for line in open("/opt/evolvixos/.env"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                v = v.strip().strip("'").strip('"')
                if k not in os.environ: os.environ[k] = v
    from v10.router.model_router import ModelRouter
    from v10.providers.base import LLMRegistry, PrivacyMode
    from v10.providers.ollama import OllamaProvider
    from v10.providers.groq import GroqProvider
    # Also verify Ollama server is reachable
    HAS_OLLAMA = server_available("http://127.0.0.1:11434/api/tags")
    HAS_V10 = True
except Exception:
    HAS_V10 = False
    HAS_OLLAMA = False

pytestmark = pytest.mark.skipif(not (HAS_V10 and HAS_OLLAMA), reason="V10 modules or Ollama server not available")


@pytest.fixture
def registry():
    reg = LLMRegistry()
    reg.set_privacy_mode(PrivacyMode.HYBRID)
    reg.register(OllamaProvider())
    reg.register(GroqProvider())
    return reg

@pytest.fixture
def router(registry):
    return ModelRouter(registry)

class TestTaskClassification:
    def test_simple_chat(self, router):
        d = router.route("hello")
        assert d.task_type == "chat"
        assert d.complexity == "simple"

    def test_code_task(self, router):
        d = router.route("write a python function to sort a list")
        assert d.task_type == "code"

    def test_reasoning_task(self, router):
        d = router.route("explain how to design a distributed system with microservices")
        assert d.task_type == "reasoning"
        assert d.complexity == "complex"

class TestProviderSelection:
    def test_simple_routes_to_local(self, router):
        d = router.route("hello")
        assert d.provider == "ollama"

    def test_complex_routes_to_cloud(self, router):
        d = router.route("explain how to design a distributed system with microservices")
        assert d.provider == "groq"

class TestPerTaskModelSelection:
    def test_simple_uses_7b(self, router):
        d = router.route("hello")
        assert d.model == "qwen2.5:7b"

    def test_code_uses_14b(self, router):
        d = router.route("write a python function")
        assert d.model == "qwen2.5:14b"

    def test_simple_short_uses_chat_model(self, router):
        d = router.route("hi")
        assert d.task_type == "chat"
        assert d.model == "qwen2.5:7b"

class TestModelParameter:
    def test_ollama_chat_accepts_model(self):
        assert "model" in OllamaProvider().chat.__code__.co_varnames

    def test_groq_chat_accepts_model(self):
        assert "model" in GroqProvider().chat.__code__.co_varnames

    def test_gemini_chat_accepts_model(self):
        from v10.providers.gemini import GeminiProvider
        assert "model" in GeminiProvider().chat.__code__.co_varnames

    def test_kimi_chat_accepts_model(self):
        from v10.providers.kimi import KimiProvider
        assert "model" in KimiProvider().chat.__code__.co_varnames

class TestFallbackChain:
    def test_ollama_available(self):
        assert OllamaProvider().is_available()

    def test_groq_available(self):
        assert GroqProvider().is_available()

    def test_ollama_models_by_task(self):
        p = OllamaProvider()
        assert "chat" in p.models_by_task
        assert "code" in p.models_by_task
        assert "simple" in p.models_by_task
        assert p.models_by_task["chat"] == "qwen2.5:7b"
        assert p.models_by_task["code"] == "qwen2.5:14b"
        assert p.models_by_task["simple"] == "qwen2.5:3b"
