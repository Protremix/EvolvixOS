from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.config import settings

limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])


async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={
            "error": {
                "code": 429,
                "message": "Rate limit exceeded",
                "detail": str(exc.detail),
            }
        },
    )
