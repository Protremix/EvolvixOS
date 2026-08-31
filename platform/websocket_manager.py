
"""
WebSocket Real-Time Manager — Self-Hosted.
Provides entity change streaming and agent chat streaming.
"""
import os
import json
import asyncio
from typing import Dict, Set, Any
from datetime import datetime, timezone
from fastapi import WebSocket, WebSocketDisconnect


class ConnectionManager:
    """Manage WebSocket connections for real-time updates."""
    
    def __init__(self):
        # Entity subscriptions: {entity_name: {connection_id: websocket}}
        self.entity_subscriptions: Dict[str, Dict[str, WebSocket]] = {}
        # Agent chat subscriptions: {conversation_id: {connection_id: websocket}}
        self.chat_subscriptions: Dict[str, Dict[str, WebSocket]] = {}
        # All connections
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, connection_id: str):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections[connection_id] = websocket
    
    def disconnect(self, connection_id: str):
        """Remove a connection from all subscriptions."""
        self.active_connections.pop(connection_id, None)
        for entity_name in list(self.entity_subscriptions.keys()):
            self.entity_subscriptions[entity_name].pop(connection_id, None)
            if not self.entity_subscriptions[entity_name]:
                del self.entity_subscriptions[entity_name]
        for conv_id in list(self.chat_subscriptions.keys()):
            self.chat_subscriptions[conv_id].pop(connection_id, None)
            if not self.chat_subscriptions[conv_id]:
                del self.chat_subscriptions[conv_id]
    
    def subscribe_entity(self, entity_name: str, connection_id: str):
        """Subscribe a connection to entity change events."""
        if entity_name not in self.entity_subscriptions:
            self.entity_subscriptions[entity_name] = {}
        self.entity_subscriptions[entity_name][connection_id] = self.active_connections.get(connection_id)
    
    def subscribe_chat(self, conversation_id: str, connection_id: str):
        """Subscribe a connection to agent chat events."""
        if conversation_id not in self.chat_subscriptions:
            self.chat_subscriptions[conversation_id] = {}
        self.chat_subscriptions[conversation_id][connection_id] = self.active_connections.get(connection_id)
    
    async def broadcast_entity_event(self, entity_name: str, event_type: str, record: dict):
        """Broadcast an entity change event to all subscribers."""
        if entity_name not in self.entity_subscriptions:
            return
        
        event = {
            "type": "entity_change",
            "entity_name": entity_name,
            "event_type": event_type,
            "record": record,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        dead = []
        for conn_id, ws in self.entity_subscriptions[entity_name].items():
            if ws is None:
                dead.append(conn_id)
                continue
            try:
                await ws.send_json(event)
            except:
                dead.append(conn_id)
        
        for conn_id in dead:
            self.entity_subscriptions[entity_name].pop(conn_id, None)
    
    async def stream_agent_response(self, conversation_id: str, token: str, is_final: bool = False):
        """Stream an agent response token to chat subscribers."""
        if conversation_id not in self.chat_subscriptions:
            return
        
        event = {
            "type": "agent_response",
            "conversation_id": conversation_id,
            "token": token,
            "is_final": is_final,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        dead = []
        for conn_id, ws in self.chat_subscriptions[conversation_id].items():
            if ws is None:
                dead.append(conn_id)
                continue
            try:
                await ws.send_json(event)
            except:
                dead.append(conn_id)
        
        for conn_id in dead:
            self.chat_subscriptions[conversation_id].pop(conn_id, None)


# Global instance
ws_manager = ConnectionManager()


class DeclarativeRLS:
    """Declarative Row-Level Security — Self-Hosted.
    
    Evaluates RLS rules from entity schemas against user context.
    Rules are JSON expressions evaluated per query.
    """
    
    @staticmethod
    def evaluate_rls(rls_rules: dict, user: dict, record: dict = None, action: str = "read") -> bool:
        """
        Evaluate RLS rules for a given action.
        
        Args:
            rls_rules: RLS definition from entity schema
            user: User context {id, role, email}
            record: Record being accessed (for read/update/delete)
            action: read, create, update, delete
            
        Returns:
            True if access is allowed, False otherwise
        """
        if not rls_rules:
            return True  # No rules = public access
        
        action_rule = rls_rules.get(action)
        if not action_rule:
            return True  # No rule for this action = allowed
        
        # Admin bypass
        if user and user.get("role") == "admin":
            return True
        
        # Evaluate conditions
        if isinstance(action_rule, dict):
            # Check $or conditions (Self-Hosted)
            if "$or" in action_rule:
                for condition in action_rule["$or"]:
                    if DeclarativeRLS._eval_condition(condition, user, record):
                        return True
                return False
            
            # Check user_condition
            if "user_condition" in action_rule:
                return DeclarativeRLS._eval_condition(action_rule["user_condition"], user, record)
            
            # Direct condition
            return DeclarativeRLS._eval_condition(action_rule, user, record)
        
        return True
    
    @staticmethod
    def _eval_condition(condition: dict, user: dict, record: dict) -> bool:
        """Evaluate a single RLS condition."""
        if not user:
            return False
        
        # role condition
        if "role" in condition:
            return user.get("role") == condition["role"]
        
        # user.id match (created_by)
        if "created_by" in condition:
            template = condition["created_by"]
            if template == "{{user.id}}":
                return record and record.get("created_by") == user.get("id")
        
        # Generic template evaluation
        for key, val in condition.items():
            if isinstance(val, str) and val.startswith("{{user."):
                field = val[7:-2]  # Extract field name from {{user.field}}
                if str(user.get(field)) != str(record.get(key) if record else None):
                    return False
        
        return True
