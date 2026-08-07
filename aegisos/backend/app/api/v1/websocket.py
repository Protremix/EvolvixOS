"""
WebSocket endpoint for real-time agent/task/executor updates.
Replaces polling with push-based real-time updates.
"""

import asyncio
import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from jose import jwt, JWTError

from app.core.config import settings
from app.core.websocket_manager import ws_manager
from app.ai.workflow_engine import AIWorkflowEngine

logger = logging.getLogger("evolvixos")

router = APIRouter()


async def authenticate_ws(websocket: WebSocket) -> bool:
    """Authenticate WebSocket connection via token query param."""
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001, reason="Missing token")
        return False
    try:
        jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return True
    except JWTError:
        await websocket.close(code=4003, reason="Invalid token")
        return False


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint for real-time updates.

    Client connects with: ws://host/api/v1/ws?token=<jwt>
    Receives events: agent_status, task_update, executor_status, agent_result
    Can send: {"action": "subscribe", "channel": "agents|tasks|executor|all"}
    """
    authenticated = await authenticate_ws(websocket)
    if not authenticated:
        return

    await ws_manager.connect(websocket)

    # Send initial state
    try:
        engine = AIWorkflowEngine()
        agents = [{"name": a.name, "display_name": a.display_name, "status": "active", "model": "GPT-4o"} for a in engine.list_agents()]
        await ws_manager.send_personal(websocket, "initial_state", {
            "agents": agents,
            "agent_count": len(agents),
        })
    except Exception as e:
        logger.warning("ws_initial_state_failed", extra={"error": str(e)})

    # Wire real-time monitor to push events via WebSocket
    from app.services.realtime_monitor import get_realtime_monitor
    import asyncio

    monitor = get_realtime_monitor()

    def monitor_callback(event_type: str, event_data: dict):
        """Push monitor events to this WebSocket."""
        try:
            asyncio.create_task(ws_manager.send_personal(websocket, event_type, event_data))
        except Exception:
            pass

    monitor.add_subscriber(monitor_callback)

    try:
        while True:
            # Keep connection alive; listen for client messages
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                action = msg.get("action")
                if action == "ping":
                    await ws_manager.send_personal(websocket, "pong", {"timestamp": asyncio.get_event_loop().time()})
                elif action == "status":
                    await ws_manager.send_personal(websocket, "status", {
                        "connections": ws_manager.connection_count,
                    })
            except json.JSONDecodeError:
                await ws_manager.send_personal(websocket, "error", {"message": "Invalid JSON"})
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.warning("ws_error", extra={"error": str(e)})
        ws_manager.disconnect(websocket)


@router.get("/ws/status")
async def ws_status():
    """Get WebSocket connection status (REST endpoint)."""
    return {
        "active_connections": ws_manager.connection_count,
        "status": "running" if ws_manager.connection_count > 0 else "idle",
    }
