"""Module 3: AI Ticket System."""
from fastapi import APIRouter, Request, Query
from pydantic import BaseModel
from typing import Optional
import time

from app.models import database

router = APIRouter(prefix="/tickets", tags=["tickets"])

class CreateTicket(BaseModel):
    title: str
    type: str = "technical"
    priority: str = "medium"
    description: str
    user_id: str = "anonymous"
    conversation_id: Optional[str] = None
    department: Optional[str] = None
    metadata: Optional[dict] = None

class UpdateTicket(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[str] = None
    department: Optional[str] = None
    resolution: Optional[str] = None
    metadata: Optional[dict] = None

TICKET_TYPES = ["technical", "wallet", "blockchain", "node", "validator", 
                "developer", "merchant", "billing", "security", "bug_report",
                "feature_request", "enterprise"]
PRIORITIES = ["low", "medium", "high", "critical"]
STATUSES = ["open", "in_progress", "waiting_customer", "resolved", "closed", "escalated"]

def _get_ticket_service(req: Request):
    """Get ticket service from app state, or create a default one."""
    if hasattr(req.app.state, 'tickets') and req.app.state.tickets:
        return req.app.state.tickets
    from app.services.ticket_service import TicketService
    return TicketService()

@router.post("/")
async def create_ticket(req: Request, ticket: CreateTicket):
    """Create a support ticket."""
    service = _get_ticket_service(req)
    
    # Auto-assign department based on type
    if not ticket.department:
        dept_map = {
            "technical": "Engineering", "wallet": "Mobile", "blockchain": "Blockchain",
            "node": "Infrastructure", "validator": "Blockchain",
            "developer": "Developer Relations", "merchant": "Merchant Success",
            "billing": "Finance", "security": "Security",
            "bug_report": "Engineering", "feature_request": "Product",
            "enterprise": "Enterprise",
        }
        ticket.department = dept_map.get(ticket.type, "General Support")
    
    # Check for duplicates
    dup = service.check_duplicate(ticket.title, ticket.description)
    if dup:
        return {
            "duplicate": True,
            "existing_ticket": dup,
            "message": "Similar ticket already exists",
        }
    
    created = service.create_ticket(
        conversation_id=ticket.conversation_id,
        title=ticket.title,
        type=ticket.type,
        priority=ticket.priority,
        description=ticket.description,
        user_id=ticket.user_id,
        department=ticket.department,
        metadata=ticket.metadata or {},
    )
    return created

@router.get("/")
async def list_tickets(req: Request, status: Optional[str] = None, type: Optional[str] = None,
    priority: Optional[str] = None, department: Optional[str] = None,
    assigned_to: Optional[str] = None, limit: int = 50, offset: int = 0):
    """List tickets with filters."""
    service = _get_ticket_service(req)
    filters = {}
    if status: filters["status"] = status
    if type: filters["type"] = type
    if priority: filters["priority"] = priority
    if department: filters["department"] = department
    if assigned_to: filters["assigned_to"] = assigned_to
    
    tickets = service.list_tickets(filters=filters, limit=limit, offset=offset)
    total = service.count_tickets(filters)
    return {"tickets": tickets, "total": total, "limit": limit, "offset": offset}

@router.get("/stats/dashboard")
async def ticket_stats(req: Request):
    """Get ticket statistics."""
    service = _get_ticket_service(req)
    return service.get_stats()

@router.get("/{ticket_id}")
async def get_ticket(ticket_id: str, req: Request):
    """Get ticket details."""
    service = _get_ticket_service(req)
    ticket = service.get_ticket(ticket_id)
    if not ticket:
        return {"error": "Ticket not found"}
    events = service.get_ticket_events(ticket_id)
    return {"ticket": ticket, "events": events}

@router.patch("/{ticket_id}")
async def update_ticket(ticket_id: str, update: UpdateTicket, req: Request):
    """Update a ticket."""
    service = _get_ticket_service(req)
    data = {k: v for k, v in update.model_dump().items() if v is not None}
    if data.get("status"):
        service.add_event(ticket_id, "status_change", data["status"])
    if data.get("assigned_to"):
        service.add_event(ticket_id, "assigned", data["assigned_to"])
    updated = service.update_ticket(ticket_id, data)
    if not updated:
        return {"error": "Ticket not found"}
    return updated

@router.post("/{ticket_id}/merge")
async def merge_tickets(ticket_id: str, target_id: str = "", req: Request = None):
    """Merge two tickets."""
    service = _get_ticket_service(req)
    result = service.merge_tickets(ticket_id, target_id)
    return result

@router.get("/types/list")
async def list_types():
    return {"types": TICKET_TYPES}

@router.get("/priorities/list")
async def list_priorities():
    return {"priorities": PRIORITIES}

@router.get("/statuses/list")
async def list_statuses():
    return {"statuses": STATUSES}
