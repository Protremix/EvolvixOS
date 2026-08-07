"""
Pipeline Run Comparison — Post-MVP Phase 7

Compares two pipeline runs side-by-side:
- Stage-by-stage diff (status, duration, agent, retries)
- Summary comparison (total duration, stages passed/failed)
- Duration delta (faster/slower per stage)
- Error diff (errors that appeared/disappeared)
"""

from typing import Optional
from dataclasses import dataclass, field, asdict
from app.core.logging import get_logger

logger = get_logger("service.pipeline_comparison")


@dataclass
class StageDiff:
    """Diff for a single stage between two runs."""
    stage: str
    agent: str
    run_a_status: str = ""
    run_b_status: str = ""
    status_changed: bool = False
    run_a_duration_ms: int = 0
    run_b_duration_ms: int = 0
    duration_delta_ms: int = 0  # positive = B is slower
    run_a_retries: int = 0
    run_b_retries: int = 0
    retries_changed: bool = False
    run_a_error: Optional[str] = None
    run_b_error: Optional[str] = None
    error_changed: bool = False
    only_in_a: bool = False
    only_in_b: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class PipelineComparison:
    """Full comparison between two pipeline runs."""
    run_a_id: str
    run_b_id: str
    run_a_title: str = ""
    run_b_title: str = ""
    run_a_status: str = ""
    run_b_status: str = ""
    run_a_total_duration_ms: int = 0
    run_b_total_duration_ms: int = 0
    total_duration_delta_ms: int = 0
    run_a_stages_passed: int = 0
    run_b_stages_passed: int = 0
    run_a_stages_failed: int = 0
    run_b_stages_failed: int = 0
    stages: list[StageDiff] = field(default_factory=list)
    improvements: list[str] = field(default_factory=list)
    regressions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "run_a_id": self.run_a_id,
            "run_b_id": self.run_b_id,
            "run_a_title": self.run_a_title,
            "run_b_title": self.run_b_title,
            "run_a_status": self.run_a_status,
            "run_b_status": self.run_b_status,
            "run_a_total_duration_ms": self.run_a_total_duration_ms,
            "run_b_total_duration_ms": self.run_b_total_duration_ms,
            "total_duration_delta_ms": self.total_duration_delta_ms,
            "run_a_stages_passed": self.run_a_stages_passed,
            "run_b_stages_passed": self.run_b_stages_passed,
            "run_a_stages_failed": self.run_a_stages_failed,
            "run_b_stages_failed": self.run_b_stages_failed,
            "stages": [s.to_dict() for s in self.stages],
            "improvements": self.improvements,
            "regressions": self.regressions,
        }


def compare_pipeline_runs(run_a, run_b) -> PipelineComparison:
    """
    Compare two pipeline runs side by side.
    Returns a PipelineComparison with stage-by-stage diffs.
    """
    comparison = PipelineComparison(
        run_a_id=run_a.id,
        run_b_id=run_b.id,
        run_a_title=getattr(run_a, "title", ""),
        run_b_title=getattr(run_b, "title", ""),
        run_a_status=run_a.status,
        run_b_status=run_b.status,
        run_a_total_duration_ms=getattr(run_a, "total_duration_ms", 0) or 0,
        run_b_total_duration_ms=getattr(run_b, "total_duration_ms", 0) or 0,
    )

    comparison.total_duration_delta_ms = comparison.run_b_total_duration_ms - comparison.run_a_total_duration_ms

    # Build stage maps
    stages_a = {s.stage: s for s in run_a.stages}
    stages_b = {s.stage: s for s in run_b.stages}
    all_stages = sorted(set(stages_a.keys()) | set(stages_b.keys()))

    for stage_name in all_stages:
        sa = stages_a.get(stage_name)
        sb = stages_b.get(stage_name)

        diff = StageDiff(stage=stage_name, agent=(sa or sb).agent or "unknown")

        if sa and not sb:
            diff.only_in_a = True
            diff.run_a_status = sa.status
            diff.run_a_duration_ms = sa.duration_ms or 0
            diff.run_a_retries = sa.retry_count or 0
            diff.run_a_error = sa.error
        elif sb and not sa:
            diff.only_in_b = True
            diff.run_b_status = sb.status
            diff.run_b_duration_ms = sb.duration_ms or 0
            diff.run_b_retries = sb.retry_count or 0
            diff.run_b_error = sb.error
        else:
            diff.run_a_status = sa.status
            diff.run_b_status = sb.status
            diff.status_changed = sa.status != sb.status
            diff.run_a_duration_ms = sa.duration_ms or 0
            diff.run_b_duration_ms = sb.duration_ms or 0
            diff.duration_delta_ms = diff.run_b_duration_ms - diff.run_a_duration_ms
            diff.run_a_retries = sa.retry_count or 0
            diff.run_b_retries = sb.retry_count or 0
            diff.retries_changed = diff.run_a_retries != diff.run_b_retries
            diff.run_a_error = sa.error
            diff.run_b_error = sb.error
            diff.error_changed = bool(sa.error) != bool(sb.error) or (sa.error or "") != (sb.error or "")

            # Track improvements and regressions
            if sa.status == "failed" and sb.status == "passed":
                comparison.improvements.append(f"Stage '{stage_name}' now passes (was failed)")
            elif sa.status == "passed" and sb.status == "failed":
                comparison.regressions.append(f"Stage '{stage_name}' now fails (was passing)")
            elif sa.status == "passed" and sb.status == "passed":
                if diff.duration_delta_ms < 0:
                    comparison.improvements.append(
                        f"Stage '{stage_name}' faster by {abs(diff.duration_delta_ms)}ms"
                    )
                elif diff.duration_delta_ms > 0:
                    comparison.regressions.append(
                        f"Stage '{stage_name}' slower by {diff.duration_delta_ms}ms"
                    )
            if diff.retries_changed and diff.run_b_retries < diff.run_a_retries:
                comparison.improvements.append(
                    f"Stage '{stage_name}' retries reduced ({diff.run_a_retries} → {diff.run_b_retries})"
                )
            elif diff.retries_changed and diff.run_b_retries > diff.run_a_retries:
                comparison.regressions.append(
                    f"Stage '{stage_name}' retries increased ({diff.run_a_retries} → {diff.run_b_retries})"
                )

        comparison.stages.append(diff)

    # Count passed/failed
    comparison.run_a_stages_passed = sum(1 for s in run_a.stages if s.status == "passed")
    comparison.run_b_stages_passed = sum(1 for s in run_b.stages if s.status == "passed")
    comparison.run_a_stages_failed = sum(1 for s in run_a.stages if s.status == "failed")
    comparison.run_b_stages_failed = sum(1 for s in run_b.stages if s.status == "failed")

    # Overall improvements/regressions
    if comparison.run_b_stages_passed > comparison.run_a_stages_passed:
        comparison.improvements.append(
            f"More stages passed ({comparison.run_a_stages_passed} → {comparison.run_b_stages_passed})"
        )
    if comparison.run_b_stages_failed < comparison.run_a_stages_failed:
        comparison.improvements.append(
            f"Fewer stages failed ({comparison.run_a_stages_failed} → {comparison.run_b_stages_failed})"
        )
    if comparison.total_duration_delta_ms < 0:
        comparison.improvements.append(
            f"Overall faster by {abs(comparison.total_duration_delta_ms)}ms"
        )
    elif comparison.total_duration_delta_ms > 0:
        comparison.regressions.append(
            f"Overall slower by {comparison.total_duration_delta_ms}ms"
        )

    logger.info(
        "pipelines_compared",
        run_a=run_a.id, run_b=run_b.id,
        improvements=len(comparison.improvements),
        regressions=len(comparison.regressions),
    )

    return comparison
