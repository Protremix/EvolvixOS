"""
Pipeline Scheduler — Post-MVP Phase 5

Schedules pipeline runs on a recurring basis:
- Cron-like expressions (daily, weekly, monthly)
- Template-based scheduling (use a template for each scheduled run)
- Next-run computation
- Enable/disable without deleting

The scheduler is in-memory for MVP. Production would use
a persistent job store (e.g., APScheduler with SQLAlchemy).
"""

from typing import Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from app.core.logging import get_logger

logger = get_logger("service.pipeline_scheduler")


@dataclass
class ScheduledPipeline:
    """A scheduled recurring pipeline."""
    id: str = field(default_factory=lambda: f"sched-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}")
    name: str = ""
    template_id: str = ""
    title: str = ""
    description: str = ""
    schedule: str = "daily"  # daily, weekly, monthly
    time: str = "09:00"  # HH:MM in UTC
    day_of_week: int = 0  # 0=Monday for weekly
    day_of_month: int = 1  # for monthly
    enabled: bool = True
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    last_run: Optional[str] = None
    next_run: Optional[str] = None
    run_count: int = 0
    max_runs: Optional[int] = None  # None = unlimited

    def to_dict(self) -> dict:
        return asdict(self)


def _compute_next_run(sched: ScheduledPipeline) -> Optional[str]:
    """Compute the next run time for a schedule."""
    if not sched.enabled:
        return None

    now = datetime.utcnow()

    if sched.max_runs and sched.run_count >= sched.max_runs:
        return None

    try:
        hour, minute = map(int, sched.time.split(":"))
    except (ValueError, AttributeError):
        hour, minute = 9, 0

    if sched.schedule == "daily":
        # Next occurrence of time today (or tomorrow if already passed)
        target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if target <= now:
            target += timedelta(days=1)
        return target.isoformat()

    elif sched.schedule == "weekly":
        # Next occurrence of day_of_week at time
        target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        days_ahead = sched.day_of_week - target.weekday()
        if days_ahead < 0:
            days_ahead += 7
        if days_ahead == 0 and target <= now:
            days_ahead = 7
        target += timedelta(days=days_ahead)
        return target.isoformat()

    elif sched.schedule == "monthly":
        # Next occurrence of day_of_month at time
        target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if sched.day_of_month <= target.day:
            # Move to next month
            if target.month == 12:
                target = target.replace(year=target.year + 1, month=1, day=min(sched.day_of_month, 28))
            else:
                target = target.replace(month=target.month + 1, day=min(sched.day_of_month, 28))
        else:
            target = target.replace(day=sched.day_of_month)
        return target.isoformat()

    return None


class PipelineScheduler:
    """Manages scheduled pipeline runs."""

    def __init__(self):
        self._schedules: dict[str, ScheduledPipeline] = {}
        self._on_trigger: Optional[Callable] = None

    def set_trigger_callback(self, callback: Callable):
        """Set a callback called when a schedule fires.
        Callback receives (scheduled_pipeline) and should create+execute a pipeline."""
        self._on_trigger = callback

    def create_schedule(self, sched: ScheduledPipeline) -> ScheduledPipeline:
        """Create a new scheduled pipeline."""
        sched.next_run = _compute_next_run(sched)
        self._schedules[sched.id] = sched
        logger.info("schedule_created", schedule_id=sched.id, name=sched.name)
        return sched

    def update_schedule(self, schedule_id: str, updates: dict) -> Optional[ScheduledPipeline]:
        """Update a scheduled pipeline."""
        sched = self._schedules.get(schedule_id)
        if not sched:
            return None
        for k, v in updates.items():
            if hasattr(sched, k):
                setattr(sched, k, v)
        sched.next_run = _compute_next_run(sched)
        logger.info("schedule_updated", schedule_id=schedule_id)
        return sched

    def delete_schedule(self, schedule_id: str) -> bool:
        """Delete a scheduled pipeline."""
        if schedule_id in self._schedules:
            del self._schedules[schedule_id]
            return True
        return False

    def enable_schedule(self, schedule_id: str) -> Optional[ScheduledPipeline]:
        """Enable a schedule."""
        return self.update_schedule(schedule_id, {"enabled": True})

    def disable_schedule(self, schedule_id: str) -> Optional[ScheduledPipeline]:
        """Disable a schedule."""
        return self.update_schedule(schedule_id, {"enabled": False})

    def list_schedules(self, enabled_only: bool = False) -> list[ScheduledPipeline]:
        """List all schedules."""
        schedules = list(self._schedules.values())
        if enabled_only:
            schedules = [s for s in schedules if s.enabled]
        return sorted(schedules, key=lambda s: s.next_run or "")

    def get_schedule(self, schedule_id: str) -> Optional[ScheduledPipeline]:
        """Get a schedule by ID."""
        return self._schedules.get(schedule_id)

    def check_and_trigger(self) -> list[ScheduledPipeline]:
        """
        Check all schedules and trigger any that are due.
        Returns list of triggered schedules.
        """
        now = datetime.utcnow()
        triggered = []

        for sched in self._schedules.values():
            if not sched.enabled:
                continue
            if sched.max_runs and sched.run_count >= sched.max_runs:
                continue

            next_run = _parse_iso(sched.next_run)
            if next_run and next_run <= now:
                triggered.append(sched)
                sched.run_count += 1
                sched.last_run = now.isoformat()

                if self._on_trigger:
                    try:
                        self._on_trigger(sched)
                    except Exception as e:
                        logger.error("schedule_trigger_failed", schedule_id=sched.id, error=str(e))

                # Compute next run
                sched.next_run = _compute_next_run(sched)

        if triggered:
            logger.info("schedules_triggered", count=len(triggered))

        return triggered

    def get_upcoming(self, limit: int = 5) -> list[ScheduledPipeline]:
        """Get upcoming scheduled runs, sorted by next_run."""
        schedules = [s for s in self._schedules.values() if s.enabled and s.next_run]
        schedules.sort(key=lambda s: s.next_run)
        return schedules[:limit]


def _parse_iso(dt_str: Optional[str]) -> Optional[datetime]:
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str)
    except (ValueError, TypeError):
        return None


# Singleton
_scheduler: Optional[PipelineScheduler] = None


def get_scheduler() -> PipelineScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = PipelineScheduler()
    return _scheduler
