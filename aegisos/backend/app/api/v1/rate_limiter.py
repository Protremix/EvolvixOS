"""API for Rate Limiter — Post-MVP Phase 9."""

from fastapi import APIRouter, Depends
from app.api.deps import get_current_active_user
from app.models.user import User
from app.middleware.enhanced_rate_limit import get_rate_limiter

router = APIRouter(prefix="/rate-limiter", tags=["rate-limiter"])


@router.get("/stats")
async def get_stats(current_user: User = Depends(get_current_active_user)):
    """Get rate limiter statistics."""
    return get_rate_limiter().get_stats()


@router.post("/toggle")
async def toggle(
    enabled: bool = True,
    current_user: User = Depends(get_current_active_user),
):
    """Enable or disable rate limiting."""
    get_rate_limiter().set_enabled(enabled)
    return {"enabled": enabled}


@router.post("/cleanup")
async def cleanup(current_user: User = Depends(get_current_active_user)):
    """Clean up expired rate limit entries."""
    get_rate_limiter().cleanup_expired()
    return get_rate_limiter().get_stats()
