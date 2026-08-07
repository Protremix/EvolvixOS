import json
import redis
from typing import Any
from app.core.config import settings

EVENT_TYPES = {
    "user_registered": "user.registered",
    "user_logged_in": "user.logged_in",
    "project_created": "project.created",
    "project_updated": "project.updated",
    "project_deleted": "project.deleted",
    "task_created": "task.created",
    "task_updated": "task.updated",
    "task_completed": "task.completed",
    "task_failed": "task.failed",
    "system_health": "system.health",
}


class EventPublisher:
    def __init__(self):
        self._redis = None

    @property
    def redis(self):
        if self._redis is None:
            self._redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
        return self._redis

    def publish(self, channel: str, message: dict[str, Any]) -> None:
        try:
            self.redis.publish(channel, json.dumps(message))
        except Exception as e:
            import structlog
            log = structlog.get_logger()
            log.error("event_publish_failed", channel=channel, error=str(e))

    def close(self):
        if self._redis:
            self._redis.close()


class EventBus:
    def __init__(self):
        self._redis = None

    @property
    def redis(self):
        if self._redis is None:
            self._redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
        return self._redis

    def subscribe(self, channel: str):
        pubsub = self.redis.pubsub()
        pubsub.subscribe(channel)
        for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    yield json.loads(message["data"])
                except json.JSONDecodeError:
                    continue

    def close(self):
        if self._redis:
            self._redis.close()


event_publisher = EventPublisher()
event_bus = EventBus()
