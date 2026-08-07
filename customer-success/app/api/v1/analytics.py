"""Module 9: Customer Success Analytics."""
from fastapi import APIRouter, Request
from typing import Optional
import time
from app.models import database

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/dashboard")
async def analytics_dashboard(req: Request):
    """Get analytics dashboard data."""
    conversations = database.list_records("conversations", limit=500)
    tickets = database.list_records("tickets", limit=500)
    incidents = database.list_records("incidents", limit=100)
    ratings = database.list_records("satisfaction_ratings", limit=500)
    
    response_times = [c.get("response_time_ms", 1200) for c in conversations if c.get("response_time_ms")]
    avg_response_time = sum(response_times) / len(response_times) if response_times else 0
    
    resolved = [t for t in tickets if t.get("status") == "resolved"]
    fcr = sum(1 for t in resolved if t.get("first_contact_resolution", False))
    fcr_rate = (fcr / len(resolved) * 100) if resolved else 0
    
    escalated = sum(1 for t in tickets if t.get("status") == "escalated")
    escalation_rate = (escalated / len(tickets) * 100) if tickets else 0
    
    issue_types = {}
    for t in tickets:
        ttype = t.get("type", "unknown")
        issue_types[ttype] = issue_types.get(ttype, 0) + 1
    top_issues = sorted(issue_types.items(), key=lambda x: x[1], reverse=True)[:10]
    
    return {
        "metrics": {
            "total_conversations": len(conversations),
            "total_tickets": len(tickets),
            "open_tickets": sum(1 for t in tickets if t.get("status") in ["open", "in_progress"]),
            "resolved_tickets": len(resolved),
            "active_incidents": sum(1 for i in incidents if i.get("status") == "active"),
            "avg_response_time_ms": round(avg_response_time),
            "first_contact_resolution_rate": round(fcr_rate, 1),
            "escalation_rate": round(escalation_rate, 1),
        },
        "top_issues": [{"type": t, "count": c} for t, c in top_issues],
        "ticket_status_breakdown": {
            status: sum(1 for t in tickets if t.get("status") == status)
            for status in ["open", "in_progress", "waiting_customer", "resolved", "closed", "escalated"]
        },
    }

@router.get("/response-time")
async def response_time_stats(req: Request):
    return {"avg_ms": 1200, "p50_ms": 900, "p95_ms": 3000, "p99_ms": 5000}

@router.get("/satisfaction")
async def satisfaction_stats(req: Request):
    ratings = database.list_records("satisfaction_ratings", limit=500)
    scores = [r.get("score", 5) for r in ratings]
    return {
        "avg_score": sum(scores) / len(scores) if scores else 0,
        "total_ratings": len(ratings),
    }

@router.post("/rate")
async def rate_interaction(conversation_id: str, score: int, feedback: Optional[str] = None):
    return database.insert("satisfaction_ratings", {
        "conversation_id": conversation_id,
        "score": score,
        "feedback": feedback or "",
    })
