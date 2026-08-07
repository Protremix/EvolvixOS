from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "evolvixos",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.example_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_time_limit=300,
    task_soft_time_limit=300,
    worker_pool="prefork",
)
