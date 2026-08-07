"""
Community Engagement & UX Optimization — Phase 53

User feedback, feature requests, community rewards, events,
and usability tracking for the Verdis/EvolvixOS ecosystem.
"""

import secrets
import random
import time
import threading
from typing import Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict, deque
from app.core.logging import get_logger

logger = get_logger("service.community")


class FeedbackType(str, Enum):
    BUG = "bug"
    FEATURE = "feature_request"
    IMPROVEMENT = "improvement"
    PRAISE = "praise"
    QUESTION = "question"


class FeedbackStatus(str, Enum):
    OPEN = "open"
    TRIAGED = "triaged"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    DUPLICATE = "duplicate"


class FeedbackSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class EventStatus(str, Enum):
    UPCOMING = "upcoming"
    LIVE = "live"
    ENDED = "ended"
    CANCELLED = "cancelled"


class EventType(str, Enum):
    WEBINAR = "webinar"
    AMA = "ama"
    HACKATHON = "hackathon"
    WORKSHOP = "workshop"
    COMMUNITY_CALL = "community_call"
    BOUNTY = "bounty"


class BadgeType(str, Enum):
    EARLY_ADOPTER = "early_adopter"
    BUG_HUNTER = "bug_hunter"
    FEATURE_VOTER = "feature_voter"
    COMMUNITY_MEMBER = "community_member"
    EVENT_PARTICIPANT = "event_participant"
    CONTRIBUTOR = "contributor"
    MENTOR = "mentor"
    GREEN_VALIDATOR = "green_validator"
    TRANSLATOR = "translator"
    DOCS_CONTRIBUTOR = "docs_contributor"


@dataclass
class Feedback:
    id: str
    type: str
    severity: str
    title: str
    description: str
    category: str = "general"
    page: str = ""
    user_email: str = ""
    user_address: str = ""
    rating: int = 0  # 1-5
    status: str = FeedbackStatus.OPEN.value
    votes: int = 0
    tags: list = field(default_factory=list)
    assigned_to: str = ""
    resolution: str = ""
    created: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class FeatureRequest:
    id: str
    title: str
    description: str
    category: str = "general"
    requested_by: str = ""
    status: str = "submitted"  # submitted, under_review, planned, in_progress, shipped, declined
    votes: int = 0
    voters: list = field(default_factory=list)
    priority: str = "medium"  # low, medium, high, critical
    estimated_effort: str = ""  # S, M, L, XL
    target_phase: str = ""
    tags: list = field(default_factory=list)
    comments: list = field(default_factory=list)
    created: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class CommunityMember:
    id: str
    address: str
    email: str = ""
    username: str = ""
    joined: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    points: int = 0
    level: int = 1
    badges: list = field(default_factory=list)
    feedback_count: int = 0
    feature_votes: int = 0
    event_attendance: int = 0
    contributions: int = 0
    last_active: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class CommunityEvent:
    id: str
    name: str
    type: str
    description: str
    start_time: str = ""
    end_time: str = ""
    status: str = EventStatus.UPCOMING.value
    max_participants: int = 0
    registered: int = 0
    participants: list = field(default_factory=list)
    reward_points: int = 100
    recording_url: str = ""
    created: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class BadgeDefinition:
    id: str
    type: str
    name: str
    description: str
    icon: str = ""
    points: int = 100
    criteria: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class UsabilityMetric:
    id: str
    page: str
    visits: int = 0
    avg_duration: float = 0.0
    bounce_rate: float = 0.0
    error_rate: float = 0.0
    satisfaction: float = 0.0
    last_updated: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


class CommunityService:
    """Community engagement and UX optimization."""

    def __init__(self):
        self._feedback: dict[str, Feedback] = {}
        self._feature_requests: dict[str, FeatureRequest] = {}
        self._members: dict[str, CommunityMember] = {}
        self._events: dict[str, CommunityEvent] = {}
        self._badges: dict[str, BadgeDefinition] = {}
        self._usability: dict[str, UsabilityMetric] = {}
        self._lock = threading.Lock()
        self._init_badges()
        self._init_sample_data()

    def _init_badges(self):
        """Initialize badge definitions."""
        badges = [
            (BadgeType.EARLY_ADOPTER.value, "Early Adopter", "Joined during the first month", "🌱", 500, "Joined within first 30 days"),
            (BadgeType.BUG_HUNTER.value, "Bug Hunter", "Reported 5+ confirmed bugs", "🐛", 300, "5+ confirmed bug reports"),
            (BadgeType.FEATURE_VOTER.value, "Feature Voter", "Voted on 10+ feature requests", "🗳️", 200, "Voted on 10+ features"),
            (BadgeType.COMMUNITY_MEMBER.value, "Community Member", "Active community participant", "👥", 100, "Joined the community"),
            (BadgeType.EVENT_PARTICIPANT.value, "Event Participant", "Attended a community event", "📅", 150, "Attended at least 1 event"),
            (BadgeType.CONTRIBUTOR.value, "Contributor", "Made a code contribution", "💻", 500, "Merged a PR"),
            (BadgeType.MENTOR.value, "Mentor", "Helped onboard new members", "🧑‍🏫", 400, "Helped 3+ new members"),
            (BadgeType.GREEN_VALIDATOR.value, "Green Validator", "Operates a green validator node", "🌿", 1000, "Validator with green score >= 80"),
            (BadgeType.TRANSLATOR.value, "Translator", "Translated documentation", "🌍", 300, "Translated 10+ pages"),
            (BadgeType.DOCS_CONTRIBUTOR.value, "Docs Contributor", "Improved documentation", "📝", 250, "Improved 5+ doc pages"),
        ]
        for btype, name, desc, icon, points, criteria in badges:
            bid = f"bdg-{secrets.token_hex(8)}"
            self._badges[bid] = BadgeDefinition(
                id=bid, type=btype, name=name, description=desc,
                icon=icon, points=points, criteria=criteria,
            )

    def _init_sample_data(self):
        """Initialize sample data."""
        # Sample feedback
        feedback_samples = [
            (FeedbackType.FEATURE.value, FeedbackSeverity.MEDIUM.value, "Dark mode for explorer", "Would love a darker theme for Verdiscan", "explorer", "verdiscan", 5, ["ui", "theme"]),
            (FeedbackType.BUG.value, FeedbackSeverity.HIGH.value, "Wallet crashes on send", "App crashes when sending VRS on Android 14", "wallet", "android-wallet", 2, ["android", "crash"]),
            (FeedbackType.IMPROVEMENT.value, FeedbackSeverity.LOW.value, "Faster block sync", "Initial sync takes too long", "blockchain", "verdis-node", 4, ["performance", "sync"]),
            (FeedbackType.PRAISE.value, FeedbackSeverity.INFO.value, "Great staking UI", "The staking dashboard is really intuitive!", "staking", "staking-dashboard", 5, ["ui", "staking"]),
            (FeedbackType.QUESTION.value, FeedbackSeverity.INFO.value, "How to bridge tokens?", "Need help bridging from Ethereum to Verdis", "bridge", "bridge-ui", 3, ["bridge", "help"]),
            (FeedbackType.FEATURE.value, FeedbackSeverity.LOW.value, "Push notifications for governance", "Get notified when new proposals are created", "governance", "governance-ui", 4, ["governance", "notifications"]),
        ]
        for ftype, sev, title, desc, cat, page, rating, tags in feedback_samples:
            fid = f"fb-{secrets.token_hex(8)}"
            self._feedback[fid] = Feedback(
                id=fid, type=ftype, severity=sev, title=title,
                description=desc, category=cat, page=page,
                rating=rating, tags=tags,
                votes=secrets.token_hex(4).count("a"),
            )

        # Sample feature requests
        feature_samples = [
            ("Mobile staking", "Allow staking directly from the mobile wallet", "wallet", "high", "S", "Phase 53+"),
            ("Multi-language support", "Support Spanish, Portuguese, French in the UI", "accessibility", "medium", "L", ""),
            ("Gas estimation API", "Real-time gas price estimation for smart contracts", "developers", "high", "M", ""),
            ("Ledger hardware wallet", "Support Ledger devices for signing transactions", "wallet", "high", "XL", ""),
            ("On-chain governance discussion", "Discussion forum linked to governance proposals", "governance", "medium", "M", ""),
            ("Carbon offset calculator", "Calculate personal carbon offset from transactions", "eco", "low", "S", ""),
            ("Validator analytics API", "Public API for validator performance metrics", "developers", "medium", "M", ""),
            ("Notification preferences", "Granular notification settings per category", "ux", "low", "S", ""),
        ]
        for title, desc, cat, priority, effort, phase in feature_samples:
            fid = f"fr-{secrets.token_hex(8)}"
            votes = secrets.randbelow(50) + 5
            self._feature_requests[fid] = FeatureRequest(
                id=fid, title=title, description=desc, category=cat,
                priority=priority, estimated_effort=effort,
                target_phase=phase, votes=votes,
            )

        # Sample members
        member_samples = [
            ("0xalice1234", "alice@verdis.com", "Alice", 1250, 3),
            ("0xbob5678", "bob@verdis.com", "Bob", 800, 2),
            ("0xcharlie9", "charlie@verdis.com", "Charlie", 2100, 4),
            ("0xdiana0", "diana@verdis.com", "Diana", 450, 1),
            ("0xeve12345", "eve@verdis.com", "Eve", 1500, 3),
        ]
        for addr, email, username, points, level in member_samples:
            mid = f"mem-{secrets.token_hex(8)}"
            self._members[mid] = CommunityMember(
                id=mid, address=addr, email=email, username=username,
                points=points, level=level,
                badges=["community_member"] if points > 100 else [],
                feedback_count=secrets.randbelow(10),
                feature_votes=secrets.randbelow(20),
                event_attendance=secrets.randbelow(5),
            )

        # Sample events
        now = datetime.utcnow()
        event_samples = [
            ("Verdis Community Call #1", EventType.COMMUNITY_CALL.value, "Monthly community update and Q&A", now + timedelta(days=7), now + timedelta(days=7, hours=2), 200, 45, EventStatus.UPCOMING.value),
            ("Green Blockchain Workshop", EventType.WORKSHOP.value, "Learn about carbon-negative blockchain technology", now + timedelta(days=14), now + timedelta(days=14, hours=3), 100, 30, EventStatus.UPCOMING.value),
            ("Devs AMA with Rojs", EventType.AMA.value, "Ask me anything with the founder", now + timedelta(days=21), now + timedelta(days=21, hours=2), 500, 120, EventStatus.UPCOMING.value),
            ("Verdis Hackathon 2026", EventType.HACKATHON.value, "Build on Verdis — 100K VRS in prizes", now + timedelta(days=30), now + timedelta(days=33), 500, 80, EventStatus.UPCOMING.value),
            ("Smart Contract Workshop", EventType.WORKSHOP.value, "Hands-on Solidity on Verdis EVM", now - timedelta(days=7), now - timedelta(days=7, hours=2), 50, 35, EventStatus.ENDED.value),
        ]
        for name, etype, desc, start, end, max_p, reg, status in event_samples:
            eid = f"evt-{secrets.token_hex(8)}"
            self._events[eid] = CommunityEvent(
                id=eid, name=name, type=etype, description=desc,
                start_time=start.isoformat(), end_time=end.isoformat(),
                max_participants=max_p, registered=reg, status=status,
            )

        # Sample usability metrics
        pages = ["dashboard", "wallet", "staking", "governance", "explorer", "bridge", "nft", "identity", "faucet"]
        for page in pages:
            uid = f"us-{secrets.token_hex(8)}"
            self._usability[uid] = UsabilityMetric(
                id=uid, page=page,
                visits=random.randint(500, 10500),
                avg_duration=round(random.uniform(30, 600), 1),
                bounce_rate=round(random.uniform(10, 60), 1),
                error_rate=round(random.uniform(0, 5), 2),
                satisfaction=round(random.uniform(3.5, 5.0), 2),
            )

    # === Feedback ===

    def submit_feedback(self, type: str, severity: str, title: str,
                        description: str, **kwargs) -> Feedback:
        fid = f"fb-{secrets.token_hex(8)}"
        feedback = Feedback(
            id=fid, type=type, severity=severity, title=title,
            description=description, **kwargs,
        )
        self._feedback[fid] = feedback
        # Award points if user identified
        if feedback.user_address:
            self._award_points(feedback.user_address, 10, "feedback")
        return feedback

    def list_feedback(self, type: str = None, status: str = None,
                      severity: str = None, limit: int = 50) -> list[Feedback]:
        items = list(self._feedback.values())
        if type:
            items = [f for f in items if f.type == type]
        if status:
            items = [f for f in items if f.status == status]
        if severity:
            items = [f for f in items if f.severity == severity]
        items.sort(key=lambda f: f.created, reverse=True)
        return items[:limit]

    def get_feedback(self, feedback_id: str) -> Optional[Feedback]:
        return self._feedback.get(feedback_id)

    def update_feedback_status(self, feedback_id: str, status: str,
                                resolution: str = "") -> Optional[Feedback]:
        f = self._feedback.get(feedback_id)
        if not f:
            return None
        f.status = status
        if resolution:
            f.resolution = resolution
        f.updated = datetime.utcnow().isoformat()
        return f

    def vote_feedback(self, feedback_id: str) -> Optional[Feedback]:
        f = self._feedback.get(feedback_id)
        if f:
            f.votes += 1
            return f
        return None

    def get_feedback_stats(self) -> dict:
        items = list(self._feedback.values())
        type_counts = defaultdict(int)
        status_counts = defaultdict(int)
        sev_counts = defaultdict(int)
        total_rating = 0
        rated_count = 0
        for f in items:
            type_counts[f.type] += 1
            status_counts[f.status] += 1
            sev_counts[f.severity] += 1
            if f.rating > 0:
                total_rating += f.rating
                rated_count += 1
        return {
            "total": len(items),
            "by_type": dict(type_counts),
            "by_status": dict(status_counts),
            "by_severity": dict(sev_counts),
            "avg_rating": round(total_rating / max(1, rated_count), 2),
            "open": status_counts.get(FeedbackStatus.OPEN.value, 0),
            "resolved": status_counts.get(FeedbackStatus.RESOLVED.value, 0),
        }

    # === Feature Requests ===

    def create_feature_request(self, title: str, description: str,
                                **kwargs) -> FeatureRequest:
        fid = f"fr-{secrets.token_hex(8)}"
        req = FeatureRequest(id=fid, title=title, description=description, **kwargs)
        self._feature_requests[fid] = req
        return req

    def list_feature_requests(self, status: str = None, category: str = None,
                               limit: int = 50) -> list[FeatureRequest]:
        items = list(self._feature_requests.values())
        if status:
            items = [r for r in items if r.status == status]
        if category:
            items = [r for r in items if r.category == category]
        items.sort(key=lambda r: r.votes, reverse=True)
        return items[:limit]

    def get_feature_request(self, req_id: str) -> Optional[FeatureRequest]:
        return self._feature_requests.get(req_id)

    def vote_feature_request(self, req_id: str, voter: str = "") -> Optional[FeatureRequest]:
        r = self._feature_requests.get(req_id)
        if not r:
            return None
        if voter and voter in r.voters:
            return r  # Already voted
        r.votes += 1
        if voter:
            r.voters.append(voter)
            self._award_points(voter, 5, "feature_vote")
        return r

    def update_feature_status(self, req_id: str, status: str,
                               priority: str = "") -> Optional[FeatureRequest]:
        r = self._feature_requests.get(req_id)
        if not r:
            return None
        r.status = status
        if priority:
            r.priority = priority
        return r

    def add_comment(self, req_id: str, author: str, comment: str) -> Optional[FeatureRequest]:
        r = self._feature_requests.get(req_id)
        if not r:
            return None
        r.comments.append({
            "author": author,
            "text": comment,
            "timestamp": datetime.utcnow().isoformat(),
        })
        return r

    # === Community Members ===

    def register_member(self, address: str, email: str = "",
                         username: str = "") -> CommunityMember:
        # Check if already exists
        for m in self._members.values():
            if m.address == address:
                return m
        mid = f"mem-{secrets.token_hex(8)}"
        member = CommunityMember(
            id=mid, address=address, email=email, username=username,
            badges=[BadgeType.COMMUNITY_MEMBER.value],
        )
        self._members[mid] = member
        return member

    def get_member(self, address: str) -> Optional[CommunityMember]:
        for m in self._members.values():
            if m.address == address:
                return m
        return None

    def list_members(self, limit: int = 50) -> list[CommunityMember]:
        members = sorted(self._members.values(), key=lambda m: m.points, reverse=True)
        return members[:limit]

    def _award_points(self, address: str, points: int, reason: str = ""):
        member = self.get_member(address)
        if member:
            member.points += points
            member.last_active = datetime.utcnow().isoformat()
            # Level up every 500 points
            member.level = max(1, member.points // 500 + 1)

    def award_badge(self, address: str, badge_type: str) -> Optional[CommunityMember]:
        member = self.get_member(address)
        if not member:
            return None
        if badge_type not in member.badges:
            member.badges.append(badge_type)
            # Find badge points
            for b in self._badges.values():
                if b.type == badge_type:
                    member.points += b.points
                    break
        return member

    def get_leaderboard(self, limit: int = 20) -> list[CommunityMember]:
        return self.list_members(limit=limit)

    # === Events ===

    def create_event(self, name: str, type: str, description: str,
                     **kwargs) -> CommunityEvent:
        eid = f"evt-{secrets.token_hex(8)}"
        event = CommunityEvent(id=eid, name=name, type=type,
                                description=description, **kwargs)
        self._events[eid] = event
        return event

    def list_events(self, status: str = None, type: str = None,
                     limit: int = 50) -> list[CommunityEvent]:
        items = list(self._events.values())
        if status:
            items = [e for e in items if e.status == status]
        if type:
            items = [e for e in items if e.type == type]
        items.sort(key=lambda e: e.start_time)
        return items[:limit]

    def get_event(self, event_id: str) -> Optional[CommunityEvent]:
        return self._events.get(event_id)

    def register_for_event(self, event_id: str, address: str) -> Optional[CommunityEvent]:
        e = self._events.get(event_id)
        if not e:
            return None
        if e.max_participants > 0 and e.registered >= e.max_participants:
            return None
        if address not in e.participants:
            e.participants.append(address)
            e.registered += 1
            self._award_points(address, 50, "event_register")
        return e

    def update_event_status(self, event_id: str, status: str) -> Optional[CommunityEvent]:
        e = self._events.get(event_id)
        if not e:
            return None
        e.status = status
        return e

    # === Badges ===

    def list_badges(self) -> list[BadgeDefinition]:
        return list(self._badges.values())

    def get_badge(self, badge_id: str) -> Optional[BadgeDefinition]:
        return self._badges.get(badge_id)

    # === Usability ===

    def list_usability(self, limit: int = 50) -> list[UsabilityMetric]:
        return list(self._usability.values())[:limit]

    def get_usability(self, page: str) -> Optional[UsabilityMetric]:
        for u in self._usability.values():
            if u.page == page:
                return u
        return None

    def update_usability(self, page: str, **kwargs) -> UsabilityMetric:
        for uid, u in self._usability.items():
            if u.page == page:
                for k, v in kwargs.items():
                    if hasattr(u, k):
                        setattr(u, k, v)
                u.last_updated = datetime.utcnow().isoformat()
                return u
        # Create new
        uid = f"us-{secrets.token_hex(8)}"
        metric = UsabilityMetric(id=uid, page=page, **kwargs)
        self._usability[uid] = metric
        return metric

    def get_usability_summary(self) -> dict:
        metrics = list(self._usability.values())
        if not metrics:
            return {"message": "No data"}
        return {
            "total_pages": len(metrics),
            "total_visits": sum(m.visits for m in metrics),
            "avg_duration": round(sum(m.avg_duration for m in metrics) / len(metrics), 1),
            "avg_bounce_rate": round(sum(m.bounce_rate for m in metrics) / len(metrics), 1),
            "avg_error_rate": round(sum(m.error_rate for m in metrics) / len(metrics), 2),
            "avg_satisfaction": round(sum(m.satisfaction for m in metrics) / len(metrics), 2),
            "best_page": max(metrics, key=lambda m: m.satisfaction).page,
            "worst_page": min(metrics, key=lambda m: m.satisfaction).page,
        }

    # === Dashboard ===

    def get_dashboard(self) -> dict:
        return {
            "feedback_stats": self.get_feedback_stats(),
            "feature_requests": len(self._feature_requests),
            "total_members": len(self._members),
            "total_events": len(self._events),
            "upcoming_events": sum(1 for e in self._events.values() if e.status == EventStatus.UPCOMING.value),
            "total_badges": len(self._badges),
            "usability": self.get_usability_summary(),
            "top_members": [m.to_dict() for m in self.get_leaderboard(5)],
            "top_features": [r.to_dict() for r in self.list_feature_requests(limit=5)],
            "recent_feedback": [f.to_dict() for f in self.list_feedback(limit=5)],
        }


_service: Optional[CommunityService] = None

def get_community_service() -> CommunityService:
    global _service
    if _service is None:
        _service = CommunityService()
    return _service
