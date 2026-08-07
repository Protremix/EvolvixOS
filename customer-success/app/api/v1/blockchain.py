"""Module 7: Blockchain Support."""
from fastapi import APIRouter, Request
from typing import Optional
import httpx
import time

router = APIRouter(prefix="/blockchain", tags=["blockchain-support"])

@router.get("/health")
async def blockchain_health(req: Request):
    """Check blockchain node health."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            # Check EvolvixOS bridge
            resp = await client.get("http://localhost:3200/blockchain/api/health")
            bridge_health = resp.json() if resp.status_code == 200 else {"status": "error"}
    except Exception as e:
        bridge_health = {"status": "error", "message": str(e)}
    
    return {
        "bridge": bridge_health,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }

@router.post("/diagnostics")
async def run_diagnostics(req: Request, issue: str):
    """Run AI-powered blockchain diagnostics."""
    engine = req.app.state.ai_engine
    knowledge = req.app.state.knowledge
    kb = knowledge.search(issue)
    
    result = await engine.chat(
        message=f"Blockchain diagnostic request: {issue}",
        agent_type="blockchain",
        knowledge_context=kb,
    )
    return result

@router.post("/log-analysis")
async def analyze_logs(req: Request, logs: str):
    """Analyze blockchain logs with AI."""
    engine = req.app.state.ai_engine
    result = await engine.chat(
        message=f"Analyze these blockchain logs and identify issues:\n\n{logs[:5000]}",
        agent_type="blockchain",
    )
    return {"analysis": result["response"], "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")}

@router.get("/node-status")
async def node_status(req: Request):
    """Get node status summary."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post("http://localhost:3200/blockchain/rpc", json={
                "jsonrpc": "2.0", "method": "system_health", "params": [], "id": 1
            })
            rpc_health = resp.json() if resp.status_code == 200 else {"error": "RPC unavailable"}
            
            resp2 = await client.post("http://localhost:3200/blockchain/rpc", json={
                "jsonrpc": "2.0", "method": "system_networkPeers", "params": [], "id": 2
            })
            peers = resp2.json() if resp2.status_code == 200 else {"error": "peers unavailable"}
    except Exception as e:
        rpc_health = {"error": str(e)}
        peers = {"error": str(e)}
    
    return {
        "rpc_health": rpc_health,
        "peers": peers,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
