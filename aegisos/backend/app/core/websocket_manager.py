"""
WebSocket connection manager for real-time updates.
Subscribes to Redis pub/sub channels and broadcasts to connected WebSocket clients.
"""

import json
import asyncio
import logging
from typing import Dict, Set
from fastapi import WebSocket

logger = logging.getLogger("evolvixos")


class WebSocketManager:
    """Manages WebSocket connections and broadcasts events from Redis pub/sub."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self._redis_task: asyncio.Task | None = None
        self._loop: asyncio.AbstractEventLoop | None = None

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info("ws_connected", extra={"total": len(self.active_connections)})

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        logger.info("ws_disconnected", extra={"total": len(self.active_connections)})

    async def broadcast(self, event_type: str, data: dict):
        """Broadcast an event to all connected WebSocket clients."""
        message = json.dumps({"type": event_type, "data": data})
        dead = []
        for ws in self.active_connections:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

    async def send_personal(self, websocket: WebSocket, event_type: str, data: dict):
        """Send a message to a single WebSocket client."""
        message = json.dumps({"type": event_type, "data": data})
        try:
            await websocket.send_text(message)
        except Exception:
            self.disconnect(websocket)

    @property
    def connection_count(self) -> int:
        return len(self.active_connections)


# Singleton
ws_manager = WebSocketManager()
