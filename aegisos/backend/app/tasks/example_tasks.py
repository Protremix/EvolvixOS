import time
from app.core.celery_app import celery_app


@celery_app.task(name="example_tasks.ping")
def ping():
    return "pong"


@celery_app.task(name="example_tasks.process_event")
def process_event(event_type: str, payload: dict):
    """Simulates async event processing."""
    return {
        "status": "processed",
        "event_type": event_type,
        "payload": payload,
        "processed_at": time.time(),
    }


@celery_app.task(name="example_tasks.health_check")
def health_check():
    """Checks Database and Redis connectivity."""
    db_status = "ok"
    redis_status = "ok"

    # Check DB
    try:
        from app.db.session import engine
        with engine.connect() as conn:
            conn.execute("SELECT 1")
    except Exception as e:
        db_status = f"error: {str(e)}"

    # Check Redis
    try:
        import redis
        from app.core.config import settings
        r = redis.Redis.from_url(settings.CELERY_BROKER_URL)
        r.ping()
    except Exception as e:
        redis_status = f"error: {str(e)}"

    return {
        "status": "healthy" if db_status == "ok" and redis_status == "ok" else "degraded",
        "db": db_status,
        "redis": redis_status,
    }
