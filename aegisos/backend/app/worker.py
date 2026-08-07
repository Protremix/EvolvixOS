"""EvolvixOS Celery Worker Module"""
import os
from celery import Celery

celery_app = Celery(
    "evolvixos",
    broker=os.getenv("REDIS_URL", "redis://redis:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://redis:6379/0"),
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

@celery_app.task(name="evolvixos.ping")
def ping():
    return "pong"
