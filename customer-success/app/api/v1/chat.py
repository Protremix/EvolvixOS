"""Module 1: AI Live Support Chat."""
from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Optional
import time
import asyncio
import json

from app.models import database

router = APIRouter(prefix="/chat", tags=["live-support"])

class ChatMessage(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    agent_type: Optional[str] = None
    context: Optional[dict] = None
    user_id: Optional[str] = None
    channel: Optional[str] = "web"

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    agent: str
    agent_type: str
    escalation_needed: bool = False
    timestamp: str

@router.post("/message")
async def send_message(req: Request, msg: ChatMessage):
    """Send a message to AI live support."""
    engine = req.app.state.ai_engine
    conv_service = req.app.state.conversations
    
    conv_id = msg.conversation_id or conv_service.create_conversation(
        user_id=msg.user_id or "anonymous",
        channel=msg.channel or "web",
        agent_type=msg.agent_type or "general",
    )
    
    # Store user message
    conv_service.add_message(conv_id, "user", msg.message)
    
    # Classify intent and route agent
    intent = engine.classify_intent(msg.message)
    agent_type = msg.agent_type or intent["agent_type"]
    
    # Get knowledge context
    knowledge = req.app.state.knowledge
    kb_context = knowledge.search(msg.message)
    
    # Get AI response
    result = await engine.chat(
        message=msg.message,
        conversation_id=conv_id,
        agent_type=agent_type,
        context=msg.context,
        knowledge_context=kb_context,
    )
    
    # Store AI response
    conv_service.add_message(conv_id, "assistant", result["response"])
    
    # Auto-create ticket if escalation needed
    if result.get("escalation_needed"):
        ticket_service = req.app.state.tickets
        ticket = ticket_service.create_ticket(
            conversation_id=conv_id,
            title=f"Escalation: {msg.message[:80]}",
            type=intent["ticket_type"],
            priority="high",
            description=msg.message,
            user_id=msg.user_id or "anonymous",
        )
        result["ticket_id"] = ticket["id"]
    
    return result

@router.get("/conversations/{conv_id}")
async def get_conversation(conv_id: str, req: Request):
    """Get conversation history."""
    conv = req.app.state.conversations.get_conversation(conv_id)
    if not conv:
        return {"error": "Conversation not found"}
    messages = req.app.state.conversations.get_messages(conv_id)
    return {"conversation": conv, "messages": messages}

@router.get("/conversations")
async def list_conversations(req: Request, limit: int = 50, offset: int = 0):
    """List all conversations."""
    convs = req.app.state.conversations.list_conversations(limit=limit, offset=offset)
    return {"conversations": convs, "total": len(convs)}

@router.delete("/conversations/{conv_id}")
async def delete_conversation(conv_id: str, req: Request):
    """Delete a conversation."""
    req.app.state.ai_engine.clear_history(conv_id)
    req.app.state.conversations.delete_conversation(conv_id)
    return {"deleted": True}

@router.websocket("/ws")
async def chat_websocket(websocket: WebSocket, req: Request):
    """WebSocket for real-time chat."""
    await websocket.accept()
    conv_id = None
    try:
        while True:
            data = await websocket.receive_text()
            msg_data = json.loads(data)
            
            engine = req.app.state.ai_engine
            conv_service = req.app.state.conversations
            
            if not conv_id:
                conv_id = conv_service.create_conversation(
                    user_id=msg_data.get("user_id", "anonymous"),
                    channel="websocket",
                    agent_type=msg_data.get("agent_type", "general"),
                )
            
            conv_service.add_message(conv_id, "user", msg_data["message"])
            
            intent = engine.classify_intent(msg_data["message"])
            kb_context = req.app.state.knowledge.search(msg_data["message"])
            
            result = await engine.chat(
                message=msg_data["message"],
                conversation_id=conv_id,
                agent_type=intent["agent_type"],
                knowledge_context=kb_context,
            )
            
            conv_service.add_message(conv_id, "assistant", result["response"])
            
            await websocket.send_text(json.dumps({
                "response": result["response"],
                "conversation_id": conv_id,
                "agent": result["agent"],
                "agent_type": result["agent_type"],
                "escalation_needed": result.get("escalation_needed", False),
                "timestamp": result.get("timestamp"),
            }))
    except WebSocketDisconnect:
        pass

@router.get("/agents")
async def list_agents():
    """List available AI agents."""
    return {
        "agents": [
            {"type": "general", "name": "General Support", "description": "General customer support"},
            {"type": "technical", "name": "Technical Support", "description": "Node, API, SDK, debugging"},
            {"type": "blockchain", "name": "Blockchain Support", "description": "Validators, consensus, node health"},
            {"type": "merchant", "name": "Merchant Support", "description": "Onboarding, payments, settlements"},
            {"type": "developer", "name": "Developer Support", "description": "Smart contracts, webhooks, code"},
        ]
    }
