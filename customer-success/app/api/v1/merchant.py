"""Module 5: Merchant Support."""
from fastapi import APIRouter, Request, Query
from pydantic import BaseModel
from typing import Optional
import time

router = APIRouter(prefix="/merchant", tags=["merchant-support"])

class MerchantOnboarding(BaseModel):
    business_name: str
    contact_email: str
    phone: str
    business_type: str
    website: Optional[str] = None
    description: Optional[str] = None

@router.post("/onboarding")
async def start_onboarding(req: Request, merchant: MerchantOnboarding):
    """Start merchant onboarding process."""
    record = database.insert("merchant_tickets", {
        "type": "onboarding",
        "business_name": merchant.business_name,
        "contact_email": merchant.contact_email,
        "phone": merchant.phone,
        "business_type": merchant.business_type,
        "website": merchant.website,
        "description": merchant.description,
        "status": "pending_verification",
        "step": 1,
        "total_steps": 5,
    })
    return record

@router.get("/onboarding/{merchant_id}")
async def get_onboarding(merchant_id: str, req: Request):
    return database.get("merchant_tickets", merchant_id) or {"error": "Not found"}

@router.post("/onboarding/{merchant_id}/advance")
async def advance_onboarding(merchant_id: str, req: Request):
    merchant = database.get("merchant_tickets", merchant_id)
    if not merchant:
        return {"error": "Not found"}
    if merchant["step"] < merchant["total_steps"]:
        return database.update("merchant_tickets", merchant_id, {
            "step": merchant["step"] + 1,
            "status": f"step_{merchant['step'] + 1}",
        })
    return database.update("merchant_tickets", merchant_id, {"status": "completed"})

@router.get("/tickets")
async def list_merchant_tickets(req: Request, status: Optional[str] = None, limit: int = 50):
    tickets = database.list_records("merchant_tickets",
        filter_fn=lambda r: r.get("status") == status if status else True,
        limit=limit)
    return {"tickets": tickets, "total": len(tickets)}

@router.post("/qr/troubleshoot")
async def qr_troubleshoot(req: Request, issue: str, merchant_id: str):
    """QR code troubleshooting with AI."""
    engine = req.app.state.ai_engine
    result = await engine.chat(
        message=f"QR code issue for merchant {merchant_id}: {issue}",
        agent_type="merchant",
    )
    return {"diagnosis": result["response"], "merchant_id": merchant_id}

@router.post("/analytics/explain")
async def explain_analytics(req: Request, metric: str, merchant_id: str):
    """Explain merchant analytics with AI."""
    engine = req.app.state.ai_engine
    result = await engine.chat(
        message=f"Explain the {metric} metric for merchant {merchant_id} in simple terms.",
        agent_type="merchant",
    )
    return {"explanation": result["response"]}
