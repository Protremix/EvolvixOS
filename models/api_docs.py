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
        "learn": {
            "method": "GET",
            "path": "/api/learn",
            "description": "Get the course index with all 15 modules, 4 supplements, and metadata across 3 learning phases.",
            "example": "curl https://evolvixos.com/api/learn",
            "auth_required": False
        },
        "learn_module": {
            "method": "GET",
            "path": "/api/learn/{module_id}",
            "description": "Get full content of a specific course module (e.g., 01-welcome-to-lovable).",
            "params": {"module_id": "Module slug from the course index"},
            "example": "curl https://evolvixos.com/api/learn/01-welcome-to-lovable",
            "auth_required": False
        },
        "openclaw": {
            "method": "GET",
            "path": "/api/openclaw",
            "description": "Browse 35,000+ APIs and AI tools from OpenClaw + API Mega List + AI Agent Tools directories. Filter by category, search by name/description.",
            "params": {
                "q": "Search query (optional)",
                "category": "Filter by category (optional)",
                "limit": "Results per page (default 50, max 500)",
                "offset": "Pagination offset (default 0)"
            },
            "example": "curl https://evolvixos.com/api/openclaw?q=youtube&limit=10",
            "auth_required": False
        },
        "openclaw_categories": {
            "method": "GET",
            "path": "/api/openclaw/categories",
            "description": "Get summary of all API categories and counts across OpenClaw + API Mega List (35,192 APIs/tools, 32 categories).",
            "example": "curl https://evolvixos.com/api/openclaw/categories",
            "auth_required": False
        },
        "models": {
            "method": "GET",
            "path": "/api/models",
            "description": "List all available AI models (81 registered)"
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
    "models_available": "81 models across 8 categories (LLM, image gen, video gen, speech, music, vision, coding, RAG, 3D, local engines, frameworks)",
    "tools_available": 24,
    "code_example": {
        "python": "import requests\\n\\nAPI_KEY = 'evx_your_key_here'\\nBASE = 'https://evolvixos.com'\\n\\nresp = requests.post(f'{BASE}/api/agent',\\n    headers={'Authorization': f'Bearer {API_KEY}'},\\n    json={'prompt': 'Hello!', 'session_id': 'test'},\\n    stream=True)\\n\\nfor line in resp.iter_lines():\\n    print(line.decode())",
        "curl": "curl -N -X POST https://evolvixos.com/api/agent -H 'Authorization: Bearer evx_your_key' -H 'Content-Type: application/json' -d '{\"prompt\":\"Hello\"}'"
    }
}
