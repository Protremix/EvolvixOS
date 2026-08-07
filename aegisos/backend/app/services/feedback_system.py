"""
Developer Feedback System — Phase 24

Collects and manages developer feedback for the Verdis/EvolvixOS ecosystem.
"""

from typing import Optional
from datetime import datetime
from dataclasses import dataclass, field, asdict
from collections import defaultdict
import threading
from app.core.logging import get_logger

logger = get_logger("service.feedback")


@dataclass
class Feedback:
    id: str = field(default_factory=lambda: f"fb-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}")
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    category: str = ""  # bug, feature_request, documentation, experience, other
    rating: int = 0  # 1-5 stars
    title: str = ""
    description: str = ""
    user: str = "anonymous"
    page: str = ""  # which page/feature the feedback is about
    status: str = "open"  # open, acknowledged, resolved, dismissed
    response: str = ""  # admin response
    responded_at: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


class FeedbackSystem:
    """Manages developer feedback collection and tracking."""

    def __init__(self, max_feedback: int = 5000):
        self._feedback: dict[str, Feedback] = {}
        self._max = max_feedback
        self._lock = threading.Lock()
        self._category_stats: dict[str, dict] = defaultdict(lambda: {
            "count": 0, "avg_rating": 0.0, "ratings_sum": 0
        })

    def submit(self, category: str, rating: int, title: str,
               description: str = "", user: str = "anonymous", page: str = "") -> Feedback:
        with self._lock:
            if not 1 <= rating <= 5:
                raise ValueError("Rating must be 1-5")
            
            fb = Feedback(
                category=category, rating=rating, title=title,
                description=description, user=user, page=page,
            )
            self._feedback[fb.id] = fb

            # Update category stats
            stats = self._category_stats[category]
            stats["count"] += 1
            stats["ratings_sum"] += rating
            stats["avg_rating"] = round(stats["ratings_sum"] / stats["count"], 2)

            if len(self._feedback) > self._max:
                oldest = min(self._feedback.keys(), key=lambda k: self._feedback[k].timestamp)
                del self._feedback[oldest]

        logger.info("feedback_submitted", id=fb.id, category=category, rating=rating)
        return fb

    def get(self, feedback_id: str) -> Optional[Feedback]:
        return self._feedback.get(feedback_id)

    def list_feedback(self, category: str = None, status: str = None, limit: int = 50) -> list[Feedback]:
        feedback = list(self._feedback.values())
        if category:
            feedback = [f for f in feedback if f.category == category]
        if status:
            feedback = [f for f in feedback if f.status == status]
        feedback.sort(key=lambda f: f.timestamp, reverse=True)
        return feedback[:limit]

    def respond(self, feedback_id: str, response: str, status: str = "resolved") -> bool:
        fb = self._feedback.get(feedback_id)
        if not fb:
            return False
        fb.response = response
        fb.status = status
        fb.responded_at = datetime.utcnow().isoformat()
        return True

    def acknowledge(self, feedback_id: str) -> bool:
        fb = self._feedback.get(feedback_id)
        if not fb:
            return False
        fb.status = "acknowledged"
        return True

    def dismiss(self, feedback_id: str) -> bool:
        fb = self._feedback.get(feedback_id)
        if not fb:
            return False
        fb.status = "dismissed"
        return True

    def get_stats(self) -> dict:
        feedback = list(self._feedback.values())
        if not feedback:
            return {"total": 0, "avg_rating": 0, "categories": {}, "open": 0, "resolved": 0}
        
        ratings = [f.rating for f in feedback]
        return {
            "total": len(feedback),
            "avg_rating": round(sum(ratings) / len(ratings), 2),
            "categories": {k: dict(v) for k, v in self._category_stats.items()},
            "open": sum(1 for f in feedback if f.status == "open"),
            "acknowledged": sum(1 for f in feedback if f.status == "acknowledged"),
            "resolved": sum(1 for f in feedback if f.status == "resolved"),
            "dismissed": sum(1 for f in feedback if f.status == "dismissed"),
        }

    def clear(self):
        with self._lock:
            self._feedback.clear()
            self._category_stats.clear()


_service: Optional[FeedbackSystem] = None

def get_feedback_system() -> FeedbackSystem:
    global _service
    if _service is None:
        _service = FeedbackSystem()
    return _service
