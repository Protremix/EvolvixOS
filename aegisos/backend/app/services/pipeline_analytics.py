"""
Pipeline Analytics — Post-MVP Phase 5

Computes metrics from pipeline runs:
- Success/failure rates
- Average duration per stage and per pipeline
- Agent performance (success rate, avg duration, retry count)
- Stage bottleneck detection
- Throughput (pipelines per day/week)
- Trend analysis (last 7 days vs previous 7 days)

All metrics are computed on-demand from the in-memory pipeline store.
Production would use a time-series database.
"""

from typing import Optional
from datetime import datetime, timedelta
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from app.core.logging import get_logger

logger = get_logger("service.pipeline_analytics")


@dataclass
class StageMetrics:
    """Metrics for a single pipeline stage."""
    stage: str
    agent: str
    total_runs: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    avg_duration_ms: float = 0.0
    max_duration_ms: int = 0
    min_duration_ms: int = 0
    total_retries: int = 0
    success_rate: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class AgentMetrics:
    """Metrics for an AI agent across all stages it handles."""
    agent: str
    total_tasks: int = 0
    passed: int = 0
    failed: int = 0
    avg_duration_ms: float = 0.0
    total_retries: int = 0
    stages: list[str] = field(default_factory=list)
    success_rate: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class PipelineSummary:
    """Overall pipeline metrics summary."""
    total_pipelines: int = 0
    completed: int = 0
    failed: int = 0
    cancelled: int = 0
    running: int = 0
    pending: int = 0
    success_rate: float = 0.0
    avg_duration_ms: float = 0.0
    avg_stages_passed: float = 0.0
    total_retries: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ThroughputData:
    """Pipeline throughput over time."""
    period: str  # "daily" or "weekly"
    data: list[dict] = field(default_factory=list)  # [{date, total, completed, failed}]

    def to_dict(self) -> dict:
        return asdict(self)


def _parse_datetime(dt_str: Optional[str]) -> Optional[datetime]:
    """Parse ISO datetime string."""
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str)
    except (ValueError, TypeError):
        return None


def compute_pipeline_summary(runs: list) -> PipelineSummary:
    """Compute overall pipeline metrics from a list of pipeline runs."""
    summary = PipelineSummary(total_pipelines=len(runs))

    durations = []
    stages_passed = []
    total_retries = 0

    for run in runs:
        status = getattr(run, "status", "pending")
        if status == "completed":
            summary.completed += 1
            if run.total_duration_ms:
                durations.append(run.total_duration_ms)
            stages_passed.append(sum(1 for s in run.stages if s.status == "passed"))
        elif status == "failed":
            summary.failed += 1
        elif status == "cancelled":
            summary.cancelled += 1
        elif status == "running":
            summary.running += 1
        elif status == "pending":
            summary.pending += 1

        for stage in run.stages:
            if stage.retry_count:
                total_retries += stage.retry_count

    if summary.completed + summary.failed > 0:
        summary.success_rate = round(
            summary.completed / (summary.completed + summary.failed) * 100, 1
        )

    if durations:
        summary.avg_duration_ms = round(sum(durations) / len(durations), 1)

    if stages_passed:
        summary.avg_stages_passed = round(sum(stages_passed) / len(stages_passed), 1)

    summary.total_retries = total_retries

    return summary


def compute_stage_metrics(runs: list) -> list[StageMetrics]:
    """Compute per-stage metrics from pipeline runs."""
    stage_data = defaultdict(lambda: {
        "durations": [], "retries": 0, "passed": 0, "failed": 0,
        "skipped": 0, "total": 0, "agent": "",
    })

    for run in runs:
        for stage in run.stages:
            key = stage.stage
            stage_data[key]["total"] += 1
            stage_data[key]["agent"] = stage.agent or "unknown"

            if stage.status == "passed":
                stage_data[key]["passed"] += 1
                if stage.duration_ms:
                    stage_data[key]["durations"].append(stage.duration_ms)
            elif stage.status == "failed":
                stage_data[key]["failed"] += 1
            elif stage.status == "skipped":
                stage_data[key]["skipped"] += 1

            if stage.retry_count:
                stage_data[key]["retries"] += stage.retry_count

    metrics = []
    for stage_name, data in stage_data.items():
        durations = data["durations"]
        m = StageMetrics(
            stage=stage_name,
            agent=data["agent"],
            total_runs=data["total"],
            passed=data["passed"],
            failed=data["failed"],
            skipped=data["skipped"],
            avg_duration_ms=round(sum(durations) / len(durations), 1) if durations else 0,
            max_duration_ms=max(durations) if durations else 0,
            min_duration_ms=min(durations) if durations else 0,
            total_retries=data["retries"],
            success_rate=round(data["passed"] / data["total"] * 100, 1) if data["total"] > 0 else 0,
        )
        metrics.append(m)

    return metrics


def compute_agent_metrics(runs: list) -> list[AgentMetrics]:
    """Compute per-agent metrics from pipeline runs."""
    agent_data = defaultdict(lambda: {
        "durations": [], "retries": 0, "passed": 0, "failed": 0,
        "total": 0, "stages": set(),
    })

    for run in runs:
        for stage in run.stages:
            agent = stage.agent or "unknown"
            agent_data[agent]["total"] += 1
            agent_data[agent]["stages"].add(stage.stage)

            if stage.status == "passed":
                agent_data[agent]["passed"] += 1
                if stage.duration_ms:
                    agent_data[agent]["durations"].append(stage.duration_ms)
            elif stage.status == "failed":
                agent_data[agent]["failed"] += 1

            if stage.retry_count:
                agent_data[agent]["retries"] += stage.retry_count

    metrics = []
    for agent, data in agent_data.items():
        durations = data["durations"]
        m = AgentMetrics(
            agent=agent,
            total_tasks=data["total"],
            passed=data["passed"],
            failed=data["failed"],
            avg_duration_ms=round(sum(durations) / len(durations), 1) if durations else 0,
            total_retries=data["retries"],
            stages=sorted(data["stages"]),
            success_rate=round(data["passed"] / data["total"] * 100, 1) if data["total"] > 0 else 0,
        )
        metrics.append(m)

    return metrics


def compute_throughput(runs: list, period: str = "daily", days: int = 7) -> ThroughputData:
    """Compute pipeline throughput over time."""
    now = datetime.utcnow()
    buckets = {}

    if period == "weekly":
        for i in range(weeks_back(days)):
            week_start = now - timedelta(weeks=i + 1)
            key = week_start.strftime("%Y-W%U")
            buckets[key] = {"date": key, "total": 0, "completed": 0, "failed": 0}
    else:
        for i in range(days):
            day = now - timedelta(days=i)
            key = day.strftime("%Y-%m-%d")
            buckets[key] = {"date": key, "total": 0, "completed": 0, "failed": 0}

    for run in runs:
        created = _parse_datetime(getattr(run, "created_at", None))
        if not created:
            continue

        if period == "weekly":
            key = created.strftime("%Y-W%U")
        else:
            key = created.strftime("%Y-%m-%d")

        if key in buckets:
            buckets[key]["total"] += 1
            if run.status == "completed":
                buckets[key]["completed"] += 1
            elif run.status == "failed":
                buckets[key]["failed"] += 1

    # Sort by date ascending
    sorted_data = sorted(buckets.values(), key=lambda x: x["date"])

    return ThroughputData(period=period, data=sorted_data)


def weeks_back(days: int) -> int:
    return (days + 6) // 7


def detect_bottlenecks(runs: list, threshold_pct: float = 1.5) -> list[dict]:
    """
    Detect stages that are bottlenecks — stages whose avg duration
    is significantly longer than the overall average.

    threshold_pct: a stage is a bottleneck if its avg duration is
    threshold_pct times the overall average (default 1.5x).
    """
    stage_metrics = compute_stage_metrics(runs)
    if not stage_metrics:
        return []

    durations = [m.avg_duration_ms for m in stage_metrics if m.avg_duration_ms > 0]
    if not durations:
        return []

    avg = sum(durations) / len(durations)

    bottlenecks = []
    for m in stage_metrics:
        if m.avg_duration_ms > avg * threshold_pct:
            bottlenecks.append({
                "stage": m.stage,
                "agent": m.agent,
                "avg_duration_ms": m.avg_duration_ms,
                "overall_avg_ms": round(avg, 1),
                "ratio": round(m.avg_duration_ms / avg, 2) if avg > 0 else 0,
                "success_rate": m.success_rate,
            })

    return sorted(bottlenecks, key=lambda x: x["avg_duration_ms"], reverse=True)


def get_trends(runs: list, days: int = 7) -> dict:
    """
    Compare recent period vs previous period.
    Returns trend indicators (up/down/stable) for key metrics.
    """
    now = datetime.utcnow()
    recent_cutoff = now - timedelta(days=days)
    previous_cutoff = now - timedelta(days=days * 2)

    recent_runs = []
    previous_runs = []

    for run in runs:
        created = _parse_datetime(getattr(run, "created_at", None))
        if not created:
            continue
        if created >= recent_cutoff:
            recent_runs.append(run)
        elif created >= previous_cutoff:
            previous_runs.append(run)

    recent = compute_pipeline_summary(recent_runs)
    previous = compute_pipeline_summary(previous_runs)

    def trend(current, prev):
        if prev == 0:
            return "stable" if current == 0 else "up"
        pct = ((current - prev) / prev) * 100
        if abs(pct) < 5:
            return "stable"
        return "up" if pct > 0 else "down"

    return {
        "recent": recent.to_dict(),
        "previous": previous.to_dict(),
        "trends": {
            "success_rate": trend(recent.success_rate, previous.success_rate),
            "avg_duration": trend(recent.avg_duration_ms, previous.avg_duration_ms),
            "total_pipelines": trend(recent.total_pipelines, previous.total_pipelines),
            "retries": trend(recent.total_retries, previous.total_retries),
        },
    }


def get_full_analytics(runs: list) -> dict:
    """Get all analytics in one response."""
    return {
        "summary": compute_pipeline_summary(runs).to_dict(),
        "stages": [m.to_dict() for m in compute_stage_metrics(runs)],
        "agents": [m.to_dict() for m in compute_agent_metrics(runs)],
        "throughput": compute_throughput(runs, "daily", 7).to_dict(),
        "bottlenecks": detect_bottlenecks(runs),
        "trends": get_trends(runs, 7),
    }
