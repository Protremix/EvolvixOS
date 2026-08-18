# Architecture

## Overview

EvolvixOS runs entirely on a single server with 16 systemd services, 4 Docker containers, and Nginx as the reverse proxy.

```
                    ┌─────────────────┐
                    │   evolvixos.com  │
                    │     (Nginx)      │
                    └────┬───────┬─────┘
                         │       │
              ┌──────────┘       └──────────┐
              ↓                              ↓
    ┌─────────────────┐          ┌─────────────────┐
    │   Model API      │          │   Auth API       │
    │    :5010         │          │    :5000         │
    │                  │          │                  │
    │  81 models       │          │  JWT + OTP       │
    │  44 tools        │          │  API keys       │
    │  Triple-brain    │          │  Rate limiting  │
    │  routing         │          │                  │
    └──┬────┬────┬─────┘          └─────────────────┘
       │    │    │
       ↓    ↓    ↓
  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐
  │Groq  │ │Gemini│ │Kimi  │ │Ollama│
  │467/s │ │1M ctx│ │32K   │ │Local │
  └──────┘ └──────┘ └──────┘ └──────┘
```

## Core Services

### Model API (`:5010`)
- Handles agent streaming/non-streaming requests
- Routes to best AI engine (Groq → Gemini → Kimi → Ollama)
- Executes 44 tools
- Serves model registry and API directory

### Auth API (`:5000`)
- User registration/login with OTP
- JWT token management
- Per-user API keys (SHA-256 hashed)
- Rate limiting (30/min IP, 100/min API key)

### Dashboard (`:8080`)
- Landing page, Studio, Models browser, API directory
- Learning Hub, Developer Portal
- Served via Nginx on evolvixos.com

## Docker Containers

| Container | Port | Purpose |
|-----------|------|---------|
| tdai-memory-core | 8420 | Core memory service |
| tdai-memory-hub | 8125 | Memory hub |
| tdai-proxy | 8096 | Proxy (Groq-powered) |
| evolvix-sandbox | — | CubeSandbox (Docker mode) |

## Systemd Services (16)

1. `evolvix-model-api` — Model API on :5010
2. `evolvix-auth-api` — Auth API on :5000
3. `evolvix-dashboard` — Dashboard server
4. `evolvix-nginx` — Nginx reverse proxy
5. `evolvix-ollama` — Local LLM (Ollama)
6. `evolvix-discovery` — GitHub Discovery Engine
7. `evolvix-memory` — TencentDB Agent Memory
8-16. Supporting services

## Server Specs

| Component | Value |
|-----------|-------|
| Provider | Hetzner Cloud (Nuremberg) |
| CPU | 16 vCPU |
| RAM | 30GB |
| Disk | 600GB |
| OS | Ubuntu 22.04 |
| Python | 3.14 |
| Go | 1.23.4 |
| SSL | Let's Encrypt (Nov 2026) |
