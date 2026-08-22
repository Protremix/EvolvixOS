# EvolvixOS Test Report
**Date:** 2026-08-22 20:25:44 UTC
**Server:** 2.28.52.223 (Hetzner Cloud, Nuremberg)
**Python:** 3.14.4, pytest 9.1.1

## Summary
- **Total tests:** 52
- **Passed:** 52
- **Failed:** 0
- **Pass rate:** 100%
- **Duration:** 2.44s

## Test Categories

### 1. V10 Model Routing (16 tests)
- Task classification (simple/chat, code, reasoning)
- Provider selection (Ollama for simple, Groq for complex)
- Per-task model selection (7b chat, 14b code, 3b simple)
- Model parameter acceptance (Ollama, Groq, Gemini, Kimi)
- Fallback chain availability

### 2. Security (17 tests)
- XSS prevention (7 payload variants)
- SSRF protection (5 blocked URLs)
- User enumeration prevention
- Command injection detection (5 dangerous commands)

### 3. Model Providers (8 tests)
- Ollama provider (availability, default model, models_by_task, chat)
- Groq provider (availability, model param, chat response)
- Telegram bot (gemini-flash-latest verified)

### 4. API Endpoints (11 tests)
- Public chat (response, empty message rejection)
- Health endpoint (200, healthy status)
- Ollama service (responds, all qwen models available)
- Monitoring (script exists, executable, cron configured, Prometheus running)

## Patches Verified
1. V10 Ollama per-task models (chat() accepts model param, router passes decision.model)
2. Telegram gemini-2.0-flash-exp → gemini-flash-latest
3. Public chat fallback chain (14b → 7b → 3b)
4. Container LLMClient: OpenAI → Ollama fallback (172.18.0.1:11434)
5. Container LLMRegistry: Groq as primary (with User-Agent header fix)

## Latency Results
- Groq (primary): 203-380ms
- Ollama local (warm): 0.39-1.14s
- Fallback (OpenAI→Ollama): 1.14s (was 9.9s, 8.7x faster)
