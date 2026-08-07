import json
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.event import Event
from app.schemas.event import EventCreate
from app.core.events import event_publisher


class EventService:
    def create(self, db: Session, event_create: EventCreate, user_id: str | UUID | None = None) -> Event:
        event = Event(
            type=event_create.type,
            payload=event_create.payload,
            user_id=user_id,
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        # Publish to Redis for real-time subscribers
        event_publisher.publish(event_create.type, event_create.payload)
        return event

    def get_all(self, db: Session, skip: int = 0, limit: int = 100, event_type: str | None = None) -> list[Event]:
        query = db.query(Event)
        if event_type:
            query = query.filter(Event.type == event_type)
        return query.order_by(Event.created_at.desc()).offset(skip).limit(limit).all()


event_service = EventService()
