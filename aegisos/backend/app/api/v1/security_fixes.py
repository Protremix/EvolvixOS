"""API for Phase 50 Security Fixes."""

from fastapi import APIRouter, Depends
from app.api.deps import get_current_active_user
from app.models.user import User
from app.core.circuit_breaker import get_circuit_breaker_registry
from app.core.auth_rate_limit import get_auth_rate_limiter
from app.core.jwt_config import get_token_config
from app.core.bounded_store import BoundedDict, BoundedList
from app.core.secret_manager import get_secret_manager
from app.core.pagination import PaginationParams, paginate

router = APIRouter(prefix="/security", tags=["security-fixes"])


@router.get("/circuit-breakers")
async def list_circuit_breakers(current_user: User = Depends(get_current_active_user)):
    return get_circuit_breaker_registry().list_states()

@router.post("/circuit-breakers/{name}/reset")
async def reset_circuit_breaker(name: str, current_user: User = Depends(get_current_active_user)):
    breaker = get_circuit_breaker_registry().get(name)
    if breaker:
        breaker.reset()
        return {"reset": True, "name": name}
    return {"error": "Circuit breaker not found"}

@router.get("/auth-rate-limit/stats")
async def auth_rate_limit_stats(current_user: User = Depends(get_current_active_user)):
    return get_auth_rate_limiter().get_stats()

@router.get("/jwt-config")
async def jwt_config(current_user: User = Depends(get_current_active_user)):
    return get_token_config()

@router.get("/secret-manager/config")
async def secret_manager_config(current_user: User = Depends(get_current_active_user)):
    return get_secret_manager().get_config()

@router.get("/pagination/demo")
async def pagination_demo(current_user: User = Depends(get_current_active_user)):
    items = list(range(1, 1001))
    result = paginate(items, page=1, page_size=20)
    return result.to_dict()

@router.get("/summary")
async def security_summary(current_user: User = Depends(get_current_active_user)):
    """Summary of all Phase 50 security fixes."""
    return {
        "fixes": [
            {
                "id": "FIX-01",
                "title": "Circuit Breaker Pattern",
                "severity": "high",
                "status": "fixed",
                "file": "app/core/circuit_breaker.py",
                "description": "CircuitBreaker with closed/open/half-open states for external API calls",
                "details": "Registry tracks all breakers, auto-recovery after timeout",
            },
            {
                "id": "FIX-02",
                "title": "Auth Rate Limiting",
                "severity": "medium",
                "status": "fixed",
                "file": "app/core/auth_rate_limit.py",
                "description": "Per-IP (5/min) and per-address (10/hr) rate limiting on auth endpoints",
                "details": "Prevents brute force attacks on login/register",
            },
            {
                "id": "FIX-03",
                "title": "JWT Token Expiry",
                "severity": "medium",
                "status": "fixed",
                "file": "app/core/jwt_config.py",
                "description": "Access token reduced from 7 days to 1 hour with 7-day refresh token",
                "details": "Shorter exposure window for compromised tokens",
            },
            {
                "id": "FIX-04",
                "title": "Pagination Utility",
                "severity": "medium",
                "status": "fixed",
                "file": "app/core/pagination.py",
                "description": "Standardized pagination with PaginationParams and PaginatedResponse",
                "details": "Prevents large response payloads, max 500 items per page",
            },
            {
                "id": "FIX-05",
                "title": "Bounded Memory Stores",
                "severity": "medium",
                "status": "fixed",
                "file": "app/core/bounded_store.py",
                "description": "BoundedDict (max_size + TTL) and BoundedList (ring buffer) utilities",
                "details": "Prevents unbounded memory growth in in-memory stores",
            },
            {
                "id": "FIX-06",
                "title": "Secret Manager",
                "severity": "medium",
                "status": "fixed",
                "file": "app/core/secret_manager.py",
                "description": "Secret access wrapper that prevents logging of secret values",
                "details": "Access logging, leak detection, never caches values",
            },
        ],
        "total_fixes": 6,
        "critical_fixed": 0,
        "high_fixed": 1,
        "medium_fixed": 5,
        "remaining_open": 7,
        "security_improvement": "All high and medium findings resolved",
    }
