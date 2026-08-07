"""API for Webhook Subscriptions — Post-MVP Phase 9."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.deps import get_current_active_user
from app.models.user import User
from app.services.webhook_subscriptions import (
    get_webhook_manager, SUBSCRIBABLE_EVENTS,
)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


class CreateWebhookRequest(BaseModel):
    url: str
    event_types: list[str]
    secret: str = ""
    description: str = ""


class UpdateWebhookRequest(BaseModel):
    url: Optional[str] = None
    event_types: Optional[list[str]] = None
    secret: Optional[str] = None
    description: Optional[str] = None
    active: Optional[bool] = None


@router.get("/events")
async def list_subscribable_events(current_user: User = Depends(get_current_active_user)):
    """List all events that can be subscribed to."""
    return list(SUBSCRIBABLE_EVENTS)


@router.get("/")
async def list_subscriptions(
    active_only: bool = False,
    current_user: User = Depends(get_current_active_user),
):
    """List webhook subscriptions."""
    return [s.to_dict() for s in get_webhook_manager().list_subscriptions(active_only)]


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_subscription(
    req: CreateWebhookRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Create a new webhook subscription."""
    try:
        sub = get_webhook_manager().create_subscription(
            url=req.url, event_types=req.event_types,
            secret=req.secret, description=req.description,
        )
        return sub.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))



@router.get("/stats")
async def get_stats(current_user: User = Depends(get_current_active_user)):
    """Get webhook system statistics."""
    return get_webhook_manager().get_stats()

@router.get("/deliveries/recent")
async def get_recent_deliveries(
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
):
    """Get recent deliveries across all subscriptions."""
    return [d.to_dict() for d in get_webhook_manager().get_deliveries(None, limit)]

@router.get("/{sub_id}")
async def get_subscription(
    sub_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """Get a webhook subscription."""
    sub = get_webhook_manager().get_subscription(sub_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return sub.to_dict()


@router.patch("/{sub_id}")
async def update_subscription(
    sub_id: str,
    req: UpdateWebhookRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Update a webhook subscription."""
    try:
        updates = {k: v for k, v in req.model_dump().items() if v is not None}
        sub = get_webhook_manager().update_subscription(sub_id, **updates)
        if not sub:
            raise HTTPException(status_code=404, detail="Subscription not found")
        return sub.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.delete("/{sub_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subscription(
    sub_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """Delete a webhook subscription."""
    if not get_webhook_manager().delete_subscription(sub_id):
        raise HTTPException(status_code=404, detail="Subscription not found")


@router.post("/{sub_id}/test")
async def test_subscription(
    sub_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """Send a test event to a subscription."""
    try:
        delivery = get_webhook_manager().test_subscription(sub_id)
        return delivery.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{sub_id}/activate")
async def activate_subscription(
    sub_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """Activate a webhook subscription."""
    if not get_webhook_manager().activate(sub_id):
        raise HTTPException(status_code=404, detail="Subscription not found")
    return {"status": "active"}


@router.post("/{sub_id}/deactivate")
async def deactivate_subscription(
    sub_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """Deactivate a webhook subscription."""
    if not get_webhook_manager().deactivate(sub_id):
        raise HTTPException(status_code=404, detail="Subscription not found")
    return {"status": "inactive"}


@router.get("/{sub_id}/deliveries")
async def get_deliveries(
    sub_id: str,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
):
    """Get delivery history for a subscription."""
    return [d.to_dict() for d in get_webhook_manager().get_deliveries(sub_id, limit)]





