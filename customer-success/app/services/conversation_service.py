"""Conversation management service."""
import time
import uuid
from app.models import database

class ConversationService:
    def create_conversation(self, user_id: str, channel: str = "web", agent_type: str = "general") -> str:
        conv_id = str(uuid.uuid4())
        database.insert("conversations", {
            "id": conv_id,
            "user_id": user_id,
            "channel": channel,
            "agent_type": agent_type,
            "status": "active",
            "message_count": 0,
        })
        return conv_id
    
    def add_message(self, conv_id: str, role: str, content: str) -> dict:
        database.update("conversations", conv_id, {
            "message_count": (database.get("conversations", conv_id) or {}).get("message_count", 0) + 1,
            "last_message_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        })
        return database.insert("messages", {
            "conversation_id": conv_id,
            "role": role,
            "content": content,
        })
    
    def get_conversation(self, conv_id: str):
        return database.get("conversations", conv_id)
    
    def get_messages(self, conv_id: str) -> list:
        return database.list_records("messages",
            filter_fn=lambda r: r.get("conversation_id") == conv_id, limit=500)
    
    def list_conversations(self, limit=50, offset=0) -> list:
        return database.list_records("conversations", limit=limit, offset=offset)
    
    def delete_conversation(self, conv_id: str):
        database.delete("conversations", conv_id)
        # Also delete messages
        msgs = database.list_records("messages",
            filter_fn=lambda r: r.get("conversation_id") == conv_id, limit=1000)
        for m in msgs:
            database.delete("messages", m["id"])
