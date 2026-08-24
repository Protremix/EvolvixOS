"""Real-time WebSocket handler for entity change notifications."""
import json
import asyncio
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime

class ConnectionManager:
    """Manages WebSocket connections per entity for real-time sync."""
    def __init__(self):
        self.connections = {}

    async def connect(self, websocket: WebSocket, entity_name: str = None):
        await websocket.accept()
        key = entity_name or "global"
        if key not in self.connections:
            self.connections[key] = set()
        self.connections[key].add(websocket)
        if "global" not in self.connections:
            self.connections["global"] = set()
        self.connections["global"].add(websocket)

    def disconnect(self, websocket: WebSocket, entity_name: str = None):
        key = entity_name or "global"
        if key in self.connections:
            self.connections[key].discard(websocket)
        if "global" in self.connections:
            self.connections["global"].discard(websocket)

    async def broadcast(self, entity_name: str, event: str, data: dict):
        message = json.dumps({
            "type": event, "entity": entity_name, "data": data,
            "timestamp": datetime.utcnow().isoformat()
        })
        targets = set()
        if entity_name in self.connections:
            targets |= self.connections[entity_name]
        if "global" in self.connections:
            targets |= self.connections["global"]
        dead = []
        for ws in targets:
            try:
                await ws.send_text(message)
            except:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws, entity_name)

ws_manager = ConnectionManager()
