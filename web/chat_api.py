"""
EvolvixOS — Lightweight Chat API
Connects the web chat interface to Ollama for local, zero-token AI.

No auth, no database — just a simple proxy to Ollama with session management.
Runs on port 5001 alongside the main API.

Endpoints:
  GET  /api/v1/health       — health check
  GET  /api/v1/status       — system status
  POST /api/v1/chat         — chat (non-streaming)
  POST /api/v1/chat/stream  — chat (SSE streaming)
"""

import json
import time
import uuid
import os
from collections import defaultdict
from typing import Dict, List

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
import httpx

app = FastAPI(title="EvolvixOS Chat", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
MODEL = os.environ.get("EVOLVIX_MODEL", "qwen2.5:1.5b")
SYSTEM_PROMPT = os.environ.get(
    "EVOLVIX_SYSTEM_PROMPT",
    "You are EvolvixOS, an autonomous AI engineering assistant. You are helpful, concise, and knowledgeable about software engineering, AI/ML, and DevOps. You run 100% locally with zero paid tokens. Answer in the user's language.",
)

# In-memory session store: session_id -> list of messages
sessions: Dict[str, List[dict]] = defaultdict(list)
MAX_HISTORY = 20


@app.get("/api/v1/health")
async def health():
    """Health check."""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            res = await client.get(f"{OLLAMA_URL}/api/tags")
            models = res.json().get("models", []) if res.status_code == 200 else []
        return {
            "status": "ok",
            "service": "evolvixos-chat",
            "model": MODEL,
            "models_available": [m["name"] for m in models],
            "timestamp": time.time(),
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "offline", "error": str(e), "model": MODEL},
        )


@app.get("/api/v1/status")
async def status():
    """System status with skills info."""
    # List of EvolvixOS skills (static for now)
    skills = [
        "code_generator", "code_debugger", "code_analyzer", "security_scanner",
        "research_agent", "web_scraper", "data_analyzer", "math_solver",
        "text_summarizer", "translator", "image_generator", "video_creator",
        "movie_pipeline", "voice_interaction", "deploy_manager",
        "github_discovery", "self_improvement", "document_processor",
        "chart_generator", "ocr_scanner", "email_sender", "voip_caller",
        "life_manager", "device_connector", "api_manager",
    ]
    return {
        "name": "EvolvixOS",
        "model": MODEL,
        "skills": skills,
        "skill_count": len(skills),
        "mode": "100% local, zero tokens",
        "version": "0.4",
    }


@app.post("/api/v1/chat")
async def chat(request: Request):
    """Non-streaming chat endpoint."""
    data = await request.json()
    message = data.get("message", "").strip()
    session_id = data.get("session_id")

    if not message:
        return JSONResponse(status_code=400, content={"response": "No message provided."})

    # Get or create session
    if not session_id:
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
    history = sessions[session_id]

    # Build messages for Ollama
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in history[-MAX_HISTORY:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": message})

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            res = await client.post(
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model": MODEL,
                    "messages": messages,
                    "stream": False,
                    "options": {"temperature": 0.7, "top_p": 0.9},
                },
            )
            result = res.json()
            response_text = result.get("message", {}).get("content", "No response from model.")

        # Save to session
        sessions[session_id].append({"role": "user", "content": message})
        sessions[session_id].append({"role": "assistant", "content": response_text})

        return {
            "response": response_text,
            "session_id": session_id,
            "model": MODEL,
        }
    except httpx.TimeoutException:
        return JSONResponse(status_code=504, content={"response": "Model timed out. Try a simpler query.", "session_id": session_id})
    except Exception as e:
        return JSONResponse(status_code=500, content={"response": f"Error: {e}", "session_id": session_id})


@app.post("/api/v1/chat/stream")
async def chat_stream(request: Request):
    """Streaming chat endpoint (Server-Sent Events)."""
    data = await request.json()
    message = data.get("message", "").strip()
    session_id = data.get("session_id")

    if not message:
        return JSONResponse(status_code=400, content={"response": "No message provided."})

    if not session_id:
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
    history = sessions[session_id]

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in history[-MAX_HISTORY]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": message})

    async def generate():
        full_response = ""
        try:
            # Send session_id first
            yield f"data: {json.dumps({'session_id': session_id})}\n\n"

            async with httpx.AsyncClient(timeout=180) as client:
                async with client.stream(
                    "POST",
                    f"{OLLAMA_URL}/api/chat",
                    json={
                        "model": MODEL,
                        "messages": messages,
                        "stream": True,
                        "options": {"temperature": 0.7, "top_p": 0.9},
                    },
                ) as res:
                    async for line in res.aiter_lines():
                        if not line.strip():
                            continue
                        try:
                            chunk = json.loads(line)
                            text = chunk.get("message", {}).get("content", "")
                            if text:
                                full_response += text
                                yield f"data: {json.dumps({'text': text})}\n\n"
                            if chunk.get("done", False):
                                break
                        except json.JSONDecodeError:
                            continue

            # Save to session
            sessions[session_id].append({"role": "user", "content": message})
            sessions[session_id].append({"role": "assistant", "content": full_response})

            yield f"data: {json.dumps({'done': True, 'session_id': session_id})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.get("/")
async def root():
    return {"service": "EvolvixOS Chat API", "version": "1.0.0", "endpoints": ["/api/v1/chat", "/api/v1/chat/stream"]}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001)
