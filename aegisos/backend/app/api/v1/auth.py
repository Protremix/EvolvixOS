from fastapi import APIRouter, Depends, HTTPException, status, Form, Request, Body
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.db.session import get_db
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, Token
from app.services.user_service import user_service
from app.services.password_reset import password_reset

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(request: Request, user_create: UserCreate, db: Session = Depends(get_db)):
    try:
        user = user_service.create(db, user_create)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return user


@router.post("/login", response_model=Token)
def login(
    request: Request,
    credentials: dict = Body(...),
    db: Session = Depends(get_db),
):
    email = credentials.get("email", "")
    password = credentials.get("password", "")
    # Check account lockout
    if password_reset.is_locked(email):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Account locked due to too many failed attempts. Try again later.",
        )

    user = user_service.authenticate(db, email, password)
    if not user:
        attempt_result = password_reset.record_login_attempt(email, success=False)
        if attempt_result["locked"]:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=attempt_result["reason"],
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
        )

    password_reset.record_login_attempt(email, success=True)
    access_token = create_access_token(str(user.id), user.role.value)
    refresh_token = create_refresh_token(str(user.id))
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.post("/refresh", response_model=Token)
def refresh_token_endpoint(
    request: Request,
    refresh_token: str = Body(..., embed=True),
    db: Session = Depends(get_db),
):
    try:
        payload = decode_token(refresh_token)
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user = user_service.get_by_id(db, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    access_token = create_access_token(str(user.id), user.role.value)
    new_refresh = create_refresh_token(str(user.id))
    return {"access_token": access_token, "refresh_token": new_refresh, "token_type": "bearer"}


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    return {"detail": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
