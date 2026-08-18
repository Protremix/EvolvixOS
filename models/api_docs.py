"""
EvolvixOS Public API Documentation
Accessible at https://evolvixos.com/api/docs
"""

API_DOCS = {
    "name": "EvolvixOS API",
    "version": "1.0",
    "base_url": "https://evolvixos.com",
    "description": "Integrate EvolvixOS AI capabilities into your own agent or platform.",
    "auth": {
        "type": "Bearer Token (API Key)",
        "header": "Authorization: Bearer evx_your_key_here",
        "get_key": "POST /auth/api-keys/generate (requires login session)"
    },
    "endpoints": {
        "chat": {
            "method": "POST",
            "path": "/api/agent",
            "description": "Send a prompt to Mr James AI agent. Returns SSE stream.",
            "params": {"prompt": "string (required)", "session_id": "string (optional)"},
            "example": {
                "request": {"prompt": "Write a Python function to reverse a string", "session_id": "my-app"},
                "response": "SSE stream: event: text\\ndata: {\"text\": \"...\"}\\nevent: done"
            }
        },
        "chat_stream": {
            "method": "POST", 
            "path": "/api/chat/stream",
            "description": "Simple chat without agentic tools. Faster response.",
            "params": {"prompt": "string", "session_id": "string"}
        },
        "models": {
            "method": "GET",
            "path": "/api/models",
            "description": "List all available AI models (281 registered)"
        },
        "tools": {
            "method": "GET",
            "path": "/api/tools",
            "description": "List all 24 available agent tools"
        },
        "image_generate": {
            "method": "POST",
            "path": "/api/generate/image",
            "description": "Generate an AI image from text prompt",
            "params": {"prompt": "string", "steps": "integer (default 15)"}
        },
        "memory_save": {
            "method": "POST",
            "path": "/api/memory/save",
            "description": "Save a memory for the authenticated user",
            "params": {"key": "string", "value": "string", "category": "string"}
        },
        "memories": {
            "method": "GET",
            "path": "/api/memories",
            "description": "List all stored memories"
        },
        "identity": {
            "method": "GET",
            "path": "/api/identity",
            "description": "Get the agent identity (name, personality, soul)"
        },
        "upload": {
            "method": "POST",
            "path": "/api/upload",
            "description": "Upload a file (multipart/form-data)",
            "params": {"file": "binary", "description": "string (optional)"}
        },
        "skills": {
            "method": "GET",
            "path": "/api/skills",
            "description": "List available skills (media, crypto, design, voice)"
        },
        "health": {
            "method": "GET",
            "path": "/api/health",
            "description": "Check API health and status (no auth required)"
        }
    },
    "rate_limit": "100 requests per minute per API key",
    "models_available": "281 models across 12 categories (LLM, image gen, video gen, speech, music, vision, coding, RAG, 3D, local engines, frameworks)",
    "tools_available": 24,
    "code_example": {
        "python": "import requests\\n\\nAPI_KEY = 'evx_your_key_here'\\nBASE = 'https://evolvixos.com'\\n\\nresp = requests.post(f'{BASE}/api/agent',\\n    headers={'Authorization': f'Bearer {API_KEY}'},\\n    json={'prompt': 'Hello!', 'session_id': 'test'},\\n    stream=True)\\n\\nfor line in resp.iter_lines():\\n    print(line.decode())",
        "curl": "curl -N -X POST https://evolvixos.com/api/agent -H 'Authorization: Bearer evx_your_key' -H 'Content-Type: application/json' -d '{\"prompt\":\"Hello\"}'"
    }
}
