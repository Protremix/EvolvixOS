"""Module 6: Developer Support."""
from fastapi import APIRouter, Request, Query
from typing import Optional
import time

router = APIRouter(prefix="/developer", tags=["developer-support"])

@router.post("/ask")
async def ask_question(req: Request, question: str, context: Optional[str] = None):
    """Ask a developer question to AI."""
    engine = req.app.state.ai_engine
    knowledge = req.app.state.knowledge
    kb = knowledge.search(question)
    result = await engine.chat(
        message=question,
        agent_type="developer",
        context={"channel": "developer_portal"} if context else None,
        knowledge_context=kb,
    )
    return result

@router.get("/docs/search")
async def search_docs(req: Request, q: str, limit: int = 10):
    """Search developer documentation."""
    service = req.app.state.knowledge
    results = service.search(q, category="developer_docs", limit=limit)
    return {"results": results, "total": len(results)}

@router.get("/api-reference")
async def api_reference(req: Request, endpoint: Optional[str] = None):
    """Get API reference."""
    # Return EvolvixOS API endpoints
    return {
        "base_url": "https://evolvixos.com/api/v1",
        "blockchain_rpc": "https://evolvixos.com/blockchain/rpc",
        "blockchain_api": "https://evolvixos.com/blockchain/api",
        "endpoints": {
            "auth": ["/auth/register", "/auth/login", "/auth/refresh", "/auth/verify"],
            "blockchain": ["/verdis/dashboard", "/verdis/chain-state", "/verdis/blocks/latest"],
            "dex": ["/verdis/dex/pools", "/verdis/dex/stats", "/verdis/dex/prices"],
            "identity": ["/identity/dids", "/identity/credentials", "/identity/verify"],
            "governance": ["/governance/proposals", "/governance/treasury", "/governance/council"],
            "notifications": ["/notifications/", "/notifications/webhook", "/notifications/stats"],
        },
        "websocket": "wss://evolvixos.com/ws",
    }

@router.post("/debug")
async def debug_assist(req: Request, error_message: str, code_snippet: Optional[str] = None):
    """Get AI debugging help."""
    engine = req.app.state.ai_engine
    msg = f"Error: {error_message}"
    if code_snippet:
        msg += f"\n\nCode:\n```\n{code_snippet}\n```"
    result = await engine.chat(message=msg, agent_type="technical")
    return result
