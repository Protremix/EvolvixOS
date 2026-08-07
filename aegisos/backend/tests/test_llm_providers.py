"""
Tests for LLM Provider system — multi-provider support with fallback.
"""

import os
import pytest
from unittest.mock import patch, MagicMock

from app.ai.llm_provider import LLMProvider, LLMResponse
from app.ai.providers.gpt4o_provider import GPT4oProvider
from app.ai.providers.claude_provider import ClaudeProvider
from app.ai.providers.local_provider import LocalLLMProvider
from app.ai.llm_registry import LLMRegistry, get_llm_registry


# ============================================================
# LLMResponse Tests
# ============================================================

class TestLLMResponse:
    def test_llm_response_creation(self):
        resp = LLMResponse(
            content="Hello",
            tokens_used=10,
            model="gpt-4o",
            latency_ms=50.0,
        )
        assert resp.content == "Hello"
        assert resp.tokens_used == 10
        assert resp.model == "gpt-4o"
        assert resp.finish_reason == "stop"
        assert resp.provider == ""


# ============================================================
# GPT-4o Provider Tests
# ============================================================

class TestGPT4oProvider:
    def test_provider_name(self):
        provider = GPT4oProvider(api_key="test-key")
        assert provider.name() == "gpt4o"
        assert provider.model_name() == "gpt-4o"

    def test_is_available_with_key(self):
        provider = GPT4oProvider(api_key="test-key")
        assert provider.is_available() is True

    def test_is_available_without_key(self):
        provider = GPT4oProvider(api_key="")
        assert provider.is_available() is False

    def test_is_available_from_env(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY_2": "env-key"}):
            provider = GPT4oProvider()
            assert provider.is_available() is True

    def test_chat_without_key_raises(self):
        provider = GPT4oProvider(api_key="")
        with pytest.raises(RuntimeError, match="API key not configured"):
            provider.chat("system", "user")


# ============================================================
# Claude Provider Tests
# ============================================================

class TestClaudeProvider:
    def test_provider_name(self):
        provider = ClaudeProvider(api_key="test-key")
        assert provider.name() == "claude"
        assert "claude" in provider.model_name()

    def test_is_available_with_key(self):
        provider = ClaudeProvider(api_key="test-key")
        assert provider.is_available() is True

    def test_is_available_without_key(self):
        provider = ClaudeProvider(api_key="")
        assert provider.is_available() is False

    def test_chat_without_key_raises(self):
        provider = ClaudeProvider(api_key="")
        with pytest.raises(RuntimeError, match="API key not configured"):
            provider.chat("system", "user")


# ============================================================
# Local LLM Provider Tests
# ============================================================

class TestLocalLLMProvider:
    def test_provider_name(self):
        provider = LocalLLMProvider(base_url="http://localhost:11434/v1")
        assert provider.name() == "local"
        assert provider.model_name() == "llama3"

    def test_is_available_no_url(self):
        provider = LocalLLMProvider(base_url="")
        assert provider.is_available() is False

    def test_custom_model(self):
        provider = LocalLLMProvider(base_url="http://localhost:8080/v1", model="mistral")
        assert provider.model_name() == "mistral"


# ============================================================
# LLM Registry Tests
# ============================================================

class TestLLMRegistry:
    def test_registry_init(self):
        registry = LLMRegistry()
        providers = registry.list_providers()
        assert len(providers) >= 1  # At least GPT-4o should be registered

    def test_register_provider(self):
        registry = LLMRegistry()
        mock_provider = MagicMock(spec=LLMProvider)
        mock_provider.is_available.return_value = True
        registry.register("custom", mock_provider)
        assert "custom" in registry._providers

    def test_get_best_available(self):
        registry = LLMRegistry()
        registry._providers = {}  # Clear defaults
        registry.register("gpt4o", GPT4oProvider(api_key="test"))
        provider = registry.get_best_available()
        assert provider is not None
        assert provider.name() == "gpt4o"

    def test_fallback_to_claude(self):
        registry = LLMRegistry()
        registry._providers = {}
        registry.register("gpt4o", GPT4oProvider(api_key=""))  # Not available
        registry.register("claude", ClaudeProvider(api_key="test"))
        provider = registry.get_best_available()
        assert provider is not None
        assert provider.name() == "claude"

    def test_fallback_to_local(self):
        registry = LLMRegistry()
        registry._providers = {}
        registry.register("gpt4o", GPT4oProvider(api_key=""))
        registry.register("claude", ClaudeProvider(api_key=""))
        registry.register("local", LocalLLMProvider(base_url="http://localhost:11434/v1"))
        # Local won't be available in test env, but let's test the logic
        provider = registry.get_best_available()
        # None should be available in test env (local server not running)
        assert provider is None or provider.name() == "local"

    def test_select_provider(self):
        registry = LLMRegistry()
        registry._providers = {}
        registry.register("gpt4o", GPT4oProvider(api_key="test"))
        registry.register("claude", ClaudeProvider(api_key="test"))
        
        assert registry.select_provider("claude") is True
        provider = registry.get_best_available()
        assert provider.name() == "claude"

    def test_select_nonexistent_provider(self):
        registry = LLMRegistry()
        assert registry.select_provider("nonexistent") is False

    def test_list_providers(self):
        registry = LLMRegistry()
        registry._providers = {}
        registry.register("gpt4o", GPT4oProvider(api_key="test"))
        registry.register("claude", ClaudeProvider(api_key="test"))
        
        providers = registry.list_providers()
        assert len(providers) == 2
        assert any(p["name"] == "gpt4o" for p in providers)
        assert any(p["name"] == "claude" for p in providers)

    def test_chat_with_fallback(self):
        registry = LLMRegistry()
        registry._providers = {}
        
        # Create mock providers
        mock_gpt = MagicMock(spec=LLMProvider)
        mock_gpt.is_available.return_value = True
        mock_gpt.chat.return_value = LLMResponse(
            content="Response from GPT-4o",
            tokens_used=50,
            model="gpt-4o",
            latency_ms=100,
            provider="gpt4o",
        )
        registry.register("gpt4o", mock_gpt)
        
        result = registry.chat("system", "user")
        assert result.content == "Response from GPT-4o"
        mock_gpt.chat.assert_called_once()

    def test_chat_all_fail_raises(self):
        registry = LLMRegistry()
        registry._providers = {}
        
        mock_gpt = MagicMock(spec=LLMProvider)
        mock_gpt.is_available.return_value = True
        mock_gpt.chat.side_effect = RuntimeError("API error")
        registry.register("gpt4o", mock_gpt)
        
        with pytest.raises(RuntimeError, match="All LLM providers failed"):
            registry.chat("system", "user")

    def test_get_registry_singleton(self):
        r1 = get_llm_registry()
        r2 = get_llm_registry()
        assert r1 is r2
