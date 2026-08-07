from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.event import EventCreate, EventResponse
from app.services.event_service import event_service

router = APIRouter(prefix="/events", tags=["events"])


@router.get("/", response_model=list[EventResponse])
def list_events(skip: int = 0, limit: int = 100, type: str | None = None, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    return event_service.get_all(db, skip=skip, limit=limit, event_type=type)


@router.post("/", response_model=EventResponse, status_code=201)
def create_event(event_create: EventCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return event_service.create(db, event_create, user_id=user.id)
