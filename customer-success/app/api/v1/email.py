"""Module 2: AI Email Agent."""
from fastapi import APIRouter, Request, Query
from pydantic import BaseModel
from typing import Optional
import time

router = APIRouter(prefix="/email", tags=["email-agent"])

class EmailConfig(BaseModel):
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    imap_host: str = "imap.gmail.com"
    imap_port: int = 993
    email_address: str
    email_password: str
    provider: str = "gmail"

class ProcessEmail(BaseModel):
    from_email: str
    subject: str
    body: str
    to_email: str = "support@evolvixos.com"

@router.post("/process")
async def process_email(req: Request, email: ProcessEmail):
    """Process an incoming email through AI."""
    engine = req.app.state.ai_engine
    ticket_service = req.app.state.tickets
    
    # Classify the email
    intent = engine.classify_intent(email.subject + " " + email.body)
    
    # Generate AI response
    result = await engine.chat(
        message=f"Email from: {email.from_email}\nSubject: {email.subject}\nBody: {email.body}",
        agent_type=intent["agent_type"],
        context={"channel": "email", "from": email.from_email},
    )
    
    # Auto-create ticket
    ticket = ticket_service.create_ticket(
        title=f"[Email] {email.subject[:80]}",
        type=intent["ticket_type"],
        priority=intent["priority"],
        description=f"From: {email.from_email}\nSubject: {email.subject}\n\n{email.body}",
        user_id=email.from_email,
        department="Email Support",
    )
    
    return {
        "classification": intent,
        "ai_response": result["response"],
        "ticket_id": ticket["id"],
        "auto_reply_suggested": True,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }

@router.post("/draft-reply")
async def draft_reply(req: Request, email: ProcessEmail, tone: str = "professional"):
    """Draft an email reply using AI."""
    engine = req.app.state.ai_engine
    result = await engine.chat(
        message=f"Draft a {tone} reply to this email:\nFrom: {email.from_email}\nSubject: {email.subject}\nBody: {email.body}",
        agent_type="general",
    )
    return {"draft": result["response"], "tone": tone}

@router.get("/threads")
async def list_threads(req: Request, limit: int = 50, offset: int = 0):
    """List email threads."""
    threads = database.list_records("email_threads", limit=limit, offset=offset)
    return {"threads": threads, "total": len(threads)}

@router.get("/threads/{thread_id}")
async def get_thread(thread_id: str, req: Request):
    """Get email thread."""
    thread = database.get("email_threads", thread_id)
    messages = database.list_records("email_messages", 
        filter_fn=lambda r: r.get("thread_id") == thread_id)
    return {"thread": thread, "messages": messages}

@router.post("/classify")
async def classify_email(req: Request, email: ProcessEmail):
    """Classify an email without generating a response."""
    engine = req.app.state.ai_engine
    intent = engine.classify_intent(email.subject + " " + email.body)
    return {
        "classification": intent,
        "suggested_department": intent.get("ticket_type", "general"),
        "suggested_priority": intent.get("priority", "medium"),
    }
