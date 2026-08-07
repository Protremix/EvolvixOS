"""
Security Hardening API for EvolvixOS.
Password reset flow, account lockout, token validation.
"""

import logging
from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from typing import Optional

from app.core.config import settings
from app.db.session import get_db
from app.services.password_reset import password_reset
from app.services.user_service import user_service

logger = logging.getLogger("evolvixos")
router = APIRouter(prefix="/security", tags=["Security Hardening"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login", auto_error=False)


async def get_user_id_optional(token: str = Depends(oauth2_scheme)) -> Optional[str]:
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None


class ResetRequest(BaseModel):
    email: EmailStr

class ResetPasswordBody(BaseModel):
    token: str
    new_password: str

class VerifyTokenBody(BaseModel):
    token: str


@router.post("/password-reset/request")
async def request_password_reset(reset: ResetRequest):
    result = password_reset.request_reset(reset.email)
    return result


@router.post("/password-reset/verify")
async def verify_reset_token(verify: VerifyTokenBody):
    result = password_reset.verify_token(verify.token)
    return result


@router.post("/password-reset/confirm")
async def confirm_password_reset(reset: ResetPasswordBody, db: Session = Depends(get_db)):
    if len(reset.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    verification = password_reset.verify_token(reset.token)
    if not verification["valid"]:
        raise HTTPException(status_code=400, detail=verification["reason"])

    email = verification["email"]

    user = user_service.get_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user_service.update_password(db, user, reset.new_password)
    password_reset.invalidate_token(reset.token)
    _redis_delete(email)

    logger.info(f"password_reset_completed: {email}")
    return {"success": True, "email": email, "message": "Password reset successful."}


def _redis_delete(email):
    from app.services.password_reset import _redis
    _redis.delete(f"attempts:{email}")
    _redis.delete(f"lockout:{email}")


@router.get("/account/lock-status/{email}")
async def get_account_lock_status(email: str):
    locked = password_reset.is_locked(email)
    return {
        "email": email,
        "locked": locked,
        "max_attempts": password_reset.MAX_LOGIN_ATTEMPTS,
        "lockout_duration_seconds": password_reset.LOCKOUT_DURATION,
    }


@router.get("/token/validate")
async def validate_token(user_id: str = Depends(get_user_id_optional)):
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing token")
    return {"valid": True, "user_id": user_id}


@router.post("/cleanup/tokens")
async def cleanup_expired_tokens():
    removed = password_reset.cleanup_expired_tokens()
    return {"removed": removed, "message": f"Cleaned up {removed} expired tokens"}
