"""Module 10: Human Escalation."""
from fastapi import APIRouter, Request, Query
from pydantic import BaseModel
from typing import Optional
import time

router = APIRouter(prefix="/escalation", tags=["escalation"])

class CreateEscalation(BaseModel):
    conversation_id: str
    ticket_id: Optional[str] = None
    reason: str
    department: str = "general"
    priority: str = "high"
    user_id: str = "anonymous"

ESCALATION_REASONS = {
    "legal": {"department": "Legal", "priority": "critical", "sla_hours": 24},
    "financial": {"department": "Finance", "priority": "high", "sla_hours": 4},
    "security": {"department": "Security", "priority": "critical", "sla_hours": 1},
    "identity_verification": {"department": "Compliance", "priority": "high", "sla_hours": 8},
    "refunds": {"department": "Finance", "priority": "high", "sla_hours": 4},
    "critical_infrastructure": {"department": "Engineering", "priority": "critical", "sla_hours": 1},
    "enterprise_contracts": {"department": "Enterprise", "priority": "high", "sla_hours": 48},
    "user_request": {"department": "General Support", "priority": "medium", "sla_hours": 24},
}

@router.post("/")
async def create_escalation(req: Request, esc: CreateEscalation):
    """Create a human escalation with full context transfer."""
    conv_service = req.app.state.conversations
    
    # Get full conversation history
    conversation = conv_service.get_conversation(esc.conversation_id)
    messages = conv_service.get_messages(esc.conversation_id) if conversation else []
    
    # Get ticket if exists
    ticket = None
    if esc.ticket_id:
        ticket = req.app.state.tickets.get_ticket(esc.ticket_id)
    
    # Determine escalation routing
    reason_key = esc.reason.lower().replace(" ", "_")
    routing = ESCALATION_REASONS.get(reason_key, ESCALATION_REASONS["user_request"])
    
    record = database.insert("escalations", {
        "conversation_id": esc.conversation_id,
        "ticket_id": esc.ticket_id,
        "reason": esc.reason,
        "department": routing["department"],
        "priority": routing["priority"],
        "user_id": esc.user_id,
        "sla_hours": routing["sla_hours"],
        "status": "pending_transfer",
        "context": {
            "conversation": conversation,
            "messages": messages,
            "ticket": ticket,
            "ai_reasoning": f"Escalated due to {esc.reason}",
            "suggested_solution": "See AI conversation history for context",
        },
    })
    
    # Update ticket status
    if esc.ticket_id:
        req.app.state.tickets.update_ticket(esc.ticket_id, {
            "status": "escalated",
            "department": routing["department"],
        })
    
    return record

@router.get("/")
async def list_escalations(req: Request, status: Optional[str] = None, limit: int = 50):
    escalations = database.list_records("escalations",
        filter_fn=lambda r: (not status or r.get("status") == status),
        limit=limit)
    return {"escalations": escalations, "total": len(escalations)}

@router.get("/{escalation_id}")
async def get_escalation(escalation_id: str, req: Request):
    esc = database.get("escalations", escalation_id)
    if not esc:
        return {"error": "Escalation not found"}
    return esc

@router.patch("/{escalation_id}")
async def update_escalation(escalation_id: str, req: Request, status: str, assigned_to: Optional[str] = None):
    data = {"status": status}
    if assigned_to:
        data["assigned_to"] = assigned_to
    if status == "accepted":
        data["accepted_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    return database.update("escalations", escalation_id, data) or {"error": "Not found"}

@router.get("/reasons/list")
async def list_reasons():
    return {"reasons": list(ESCALATION_REASONS.keys()), "details": ESCALATION_REASONS}
