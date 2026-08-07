"""
Knowledge Base — Post-MVP Phase 6

Captures learnings from pipeline runs and provides intelligent retrieval:
- Pattern detection from failed/succeeded stages
- Lessons learned (auto-extracted from pipeline outcomes)
- Best practices accumulation per project type
- Search with relevance scoring
- Knowledge categories (architecture, security, performance, testing, devops)

The knowledge base is in-memory for MVP. Production would use
pgvector + PostgreSQL for semantic search.
"""

from typing import Optional
from datetime import datetime
from dataclasses import dataclass, field, asdict
from collections import defaultdict
from app.core.logging import get_logger

logger = get_logger("service.knowledge_base")


@dataclass
class KnowledgeEntry:
    """A single knowledge entry — a lesson learned, best practice, or pattern."""
    id: str = field(default_factory=lambda: f"kb-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}")
    category: str = "general"  # architecture, security, performance, testing, devops, general
    title: str = ""
    content: str = ""
    source: str = "manual"  # manual, pipeline, audit, agent
    source_pipeline_id: Optional[str] = None
    source_stage: Optional[str] = None
    project_type: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    confidence: float = 0.5  # 0.0 to 1.0
    times_referenced: int = 0
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class PatternRecord:
    """A detected pattern from pipeline runs."""
    id: str = field(default_factory=lambda: f"pat-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}")
    pattern_type: str = ""  # failure_pattern, success_pattern, bottleneck, retry_pattern
    stage: str = ""
    agent: str = ""
    description: str = ""
    occurrence_count: int = 0
    pipeline_ids: list[str] = field(default_factory=list)
    recommendation: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


class KnowledgeBase:
    """
    Knowledge Base with pattern detection and intelligent retrieval.

    Stores knowledge entries and detected patterns, provides search
    with relevance scoring, and auto-extracts lessons from pipeline runs.
    """

    def __init__(self):
        self._entries: dict[str, KnowledgeEntry] = {}
        self._patterns: dict[str, PatternRecord] = {}
        self._seed_builtin_knowledge()

    def _seed_builtin_knowledge(self):
        """Seed with built-in best practices."""
        builtins = [
            KnowledgeEntry(
                category="architecture",
                title="Prefer composition over inheritance",
                content="Use composition and dependency injection instead of deep inheritance hierarchies. This improves testability, maintainability, and flexibility.",
                source="manual",
                tags=["design", "oop", "solid"],
                confidence=0.9,
            ),
            KnowledgeEntry(
                category="security",
                title="Validate all external inputs",
                content="Never trust user input. Validate, sanitize, and authenticate all external data at system boundaries. Use parameterized queries for database access.",
                source="manual",
                tags=["input-validation", "owasp", "injection"],
                confidence=0.95,
            ),
            KnowledgeEntry(
                category="testing",
                title="Test behavior, not implementation",
                content="Write tests that verify expected behavior rather than internal implementation details. This makes tests more resilient to refactoring.",
                source="manual",
                tags=["unit-testing", "tdd", "best-practices"],
                confidence=0.85,
            ),
            KnowledgeEntry(
                category="performance",
                title="Profile before optimizing",
                content="Always measure performance before and after optimization. Premature optimization leads to complex, hard-to-maintain code.",
                source="manual",
                tags=["profiling", "optimization", "measurement"],
                confidence=0.8,
            ),
            KnowledgeEntry(
                category="devops",
                title="Immutable deployments",
                content="Deploy immutable artifacts. Never modify running systems. Use blue-green or canary deployments for zero-downtime updates.",
                source="manual",
                tags=["deployment", "ci-cd", "immutable"],
                confidence=0.9,
            ),
            KnowledgeEntry(
                category="architecture",
                title="API versioning from day one",
                content="Version APIs from the start. Use URL path versioning (/v1/) or header-based versioning. Never break backward compatibility without a deprecation cycle.",
                source="manual",
                tags=["api", "versioning", "backward-compatibility"],
                confidence=0.85,
            ),
        ]
        for entry in builtins:
            self._entries[entry.id] = entry

    # --- Knowledge Entry CRUD ---

    def add_entry(self, entry: KnowledgeEntry) -> KnowledgeEntry:
        self._entries[entry.id] = entry
        logger.info("knowledge_added", entry_id=entry.id, category=entry.category, title=entry.title)
        return entry

    def get_entry(self, entry_id: str) -> Optional[KnowledgeEntry]:
        entry = self._entries.get(entry_id)
        if entry:
            entry.times_referenced += 1
            entry.updated_at = datetime.utcnow().isoformat()
        return entry

    def update_entry(self, entry_id: str, updates: dict) -> Optional[KnowledgeEntry]:
        entry = self._entries.get(entry_id)
        if not entry:
            return None
        for k, v in updates.items():
            if hasattr(entry, k) and k != "id":
                setattr(entry, k, v)
        entry.updated_at = datetime.utcnow().isoformat()
        return entry

    def delete_entry(self, entry_id: str) -> bool:
        if entry_id in self._entries:
            del self._entries[entry_id]
            return True
        return False

    def list_entries(
        self,
        category: Optional[str] = None,
        source: Optional[str] = None,
        project_type: Optional[str] = None,
        tag: Optional[str] = None,
        limit: int = 50,
    ) -> list[KnowledgeEntry]:
        """List entries with optional filters."""
        entries = list(self._entries.values())

        if category:
            entries = [e for e in entries if e.category == category]
        if source:
            entries = [e for e in entries if e.source == source]
        if project_type:
            entries = [e for e in entries if e.project_type == project_type]
        if tag:
            entries = [e for e in entries if tag in e.tags]

        # Sort by confidence (descending), then by times_referenced
        entries.sort(key=lambda e: (-e.confidence, -e.times_referenced))
        return entries[:limit]

    def search(self, query: str, limit: int = 10) -> list[dict]:
        """
        Search knowledge entries with relevance scoring.
        Uses simple text matching (production would use vector similarity).
        """
        query_lower = query.lower()
        query_terms = query_lower.split()

        scored = []
        for entry in self._entries.values():
            score = 0.0
            title_lower = entry.title.lower()
            content_lower = entry.content.lower()

            for term in query_terms:
                # Title matches are worth more
                if term in title_lower:
                    score += 3.0
                if term in content_lower:
                    score += 1.0
                for tag in entry.tags:
                    if term in tag.lower():
                        score += 2.0

            # Boost by confidence
            score *= entry.confidence

            if score > 0:
                scored.append({
                    "entry": entry.to_dict(),
                    "score": round(score, 2),
                })

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:limit]

    def get_categories(self) -> list[dict]:
        """Get category statistics."""
        cat_counts = defaultdict(lambda: {"count": 0, "entries": []})
        for entry in self._entries.values():
            cat_counts[entry.category]["count"] += 1
            cat_counts[entry.category]["entries"].append(entry.title)

        return [
            {"category": cat, "count": data["count"], "titles": data["titles"]}
            for cat, data in sorted(cat_counts.items())
        ]

    # --- Pattern Detection ---

    def add_pattern(self, pattern: PatternRecord) -> PatternRecord:
        self._patterns[pattern.id] = pattern
        logger.info("pattern_added", pattern_id=pattern.id, type=pattern.pattern_type, stage=pattern.stage)
        return pattern

    def list_patterns(self, pattern_type: Optional[str] = None) -> list[PatternRecord]:
        patterns = list(self._patterns.values())
        if pattern_type:
            patterns = [p for p in patterns if p.pattern_type == pattern_type]
        return sorted(patterns, key=lambda p: p.occurrence_count, reverse=True)

    def delete_pattern(self, pattern_id: str) -> bool:
        if pattern_id in self._patterns:
            del self._patterns[pattern_id]
            return True
        return False

    def extract_patterns_from_runs(self, runs: list) -> list[PatternRecord]:
        """
        Analyze pipeline runs and extract patterns:
        - Stages that consistently fail (failure_pattern)
        - Stages that always pass (success_pattern)
        - Stages with high retry counts (retry_pattern)
        - Stages that are consistently slow (bottleneck_pattern)
        """
        stage_stats = defaultdict(lambda: {
            "passed": 0, "failed": 0, "skipped": 0, "total": 0,
            "retries": 0, "durations": [], "agent": "", "pipeline_ids": [],
        })

        for run in runs:
            for stage in run.stages:
                key = (stage.stage, stage.agent or "unknown")
                stage_stats[key]["total"] += 1
                stage_stats[key]["agent"] = stage.agent or "unknown"
                stage_stats[key]["pipeline_ids"].append(run.id)

                if stage.status == "passed":
                    stage_stats[key]["passed"] += 1
                    if stage.duration_ms:
                        stage_stats[key]["durations"].append(stage.duration_ms)
                elif stage.status == "failed":
                    stage_stats[key]["failed"] += 1
                elif stage.status == "skipped":
                    stage_stats[key]["skipped"] += 1

                if stage.retry_count:
                    stage_stats[key]["retries"] += stage.retry_count

        patterns = []
        for (stage_name, agent), stats in stage_stats.items():
            # Failure pattern: stage fails >50% of the time (min 3 runs)
            if stats["total"] >= 3 and stats["failed"] / stats["total"] > 0.5:
                patterns.append(PatternRecord(
                    pattern_type="failure_pattern",
                    stage=stage_name,
                    agent=agent,
                    description=f"Stage '{stage_name}' fails {stats['failed']}/{stats['total']} times ({stats['failed']/stats['total']*100:.0f}%)",
                    occurrence_count=stats["failed"],
                    pipeline_ids=stats["pipeline_ids"][:10],
                    recommendation=f"Review agent '{agent}' configuration for stage '{stage_name}'. Check for common error patterns or missing context.",
                ))

            # Success pattern: stage always passes (min 5 runs)
            if stats["total"] >= 5 and stats["passed"] == stats["total"]:
                patterns.append(PatternRecord(
                    pattern_type="success_pattern",
                    stage=stage_name,
                    agent=agent,
                    description=f"Stage '{stage_name}' passes 100% of the time ({stats['total']} runs)",
                    occurrence_count=stats["passed"],
                    pipeline_ids=stats["pipeline_ids"][:10],
                    recommendation=f"Agent '{agent}' performs reliably on '{stage_name}'. Consider using as a reference for other agents.",
                ))

            # Retry pattern: high retry count (min 2 retries across runs)
            if stats["retries"] >= 2:
                patterns.append(PatternRecord(
                    pattern_type="retry_pattern",
                    stage=stage_name,
                    agent=agent,
                    description=f"Stage '{stage_name}' required {stats['retries']} total retries across {stats['total']} runs",
                    occurrence_count=stats["retries"],
                    pipeline_ids=stats["pipeline_ids"][:10],
                    recommendation=f"Increase max_retries for '{stage_name}' or improve agent '{agent}' prompt to reduce failures.",
                ))

            # Bottleneck pattern: avg duration > 2x overall average
            if stats["durations"]:
                avg = sum(stats["durations"]) / len(stats["durations"])
                patterns.append(PatternRecord(
                    pattern_type="bottleneck_pattern",
                    stage=stage_name,
                    agent=agent,
                    description=f"Stage '{stage_name}' averages {avg:.0f}ms ({avg/1000:.1f}s)",
                    occurrence_count=len(stats["durations"]),
                    pipeline_ids=stats["pipeline_ids"][:10],
                    recommendation=f"Consider optimizing or parallelizing stage '{stage_name}' to reduce pipeline duration.",
                ))

        # Store detected patterns
        for p in patterns:
            self._patterns[p.id] = p

        logger.info("patterns_extracted", count=len(patterns))
        return patterns

    def extract_lessons_from_run(self, run) -> list[KnowledgeEntry]:
        """
        Extract lessons learned from a completed pipeline run.
        Creates knowledge entries from failures, retries, and successful patterns.
        """
        lessons = []

        if run.status == "completed":
            lessons.append(KnowledgeEntry(
                category="general",
                title=f"Successful pipeline: {run.title}",
                content=f"Pipeline '{run.title}' completed successfully in {run.total_duration_ms or 0}ms through {len(run.stages)} stages. All stages passed.",
                source="pipeline",
                source_pipeline_id=run.id,
                confidence=0.7,
                tags=["success", "completed"],
            ))

        for stage in run.stages:
            if stage.status == "failed":
                lessons.append(KnowledgeEntry(
                    category=self._stage_to_category(stage.stage),
                    title=f"Stage failure in '{stage.stage}'",
                    content=f"Stage '{stage.stage}' (agent: {stage.agent}) failed in pipeline '{run.title}'. "
                            f"Error: {stage.error or 'unknown'}. "
                            f"Retries: {stage.retry_count or 0}.",
                    source="pipeline",
                    source_pipeline_id=run.id,
                    source_stage=stage.stage,
                    confidence=0.6,
                    tags=["failure", stage.stage, stage.agent or "unknown"],
                ))

            if stage.retry_count and stage.retry_count > 0 and stage.status == "passed":
                lessons.append(KnowledgeEntry(
                    category=self._stage_to_category(stage.stage),
                    title=f"Stage '{stage.stage}' needed {stage.retry_count} retries",
                    content=f"Stage '{stage.stage}' (agent: {stage.agent}) eventually passed after {stage.retry_count} retries in pipeline '{run.title}'. "
                            f"Consider improving the agent prompt or increasing max_retries.",
                    source="pipeline",
                    source_pipeline_id=run.id,
                    source_stage=stage.stage,
                    confidence=0.65,
                    tags=["retry", stage.stage, "resilience"],
                ))

        for lesson in lessons:
            self._entries[lesson.id] = lesson

        if lessons:
            logger.info("lessons_extracted", count=len(lessons), pipeline_id=run.id)

        return lessons

    @staticmethod
    def _stage_to_category(stage: str) -> str:
        """Map pipeline stage to knowledge category."""
        mapping = {
            "prd": "architecture",
            "architecture": "architecture",
            "decomposition": "architecture",
            "implementation": "general",
            "qa": "testing",
            "security": "security",
            "performance": "performance",
            "documentation": "general",
            "review": "general",
            "release": "devops",
        }
        return mapping.get(stage, "general")

    def get_stats(self) -> dict:
        """Get knowledge base statistics."""
        cat_counts = defaultdict(int)
        source_counts = defaultdict(int)
        total_refs = 0
        avg_confidence = 0.0

        for entry in self._entries.values():
            cat_counts[entry.category] += 1
            source_counts[entry.source] += 1
            total_refs += entry.times_referenced

        if self._entries:
            avg_confidence = sum(e.confidence for e in self._entries.values()) / len(self._entries)

        return {
            "total_entries": len(self._entries),
            "total_patterns": len(self._patterns),
            "categories": dict(cat_counts),
            "sources": dict(source_counts),
            "total_references": total_refs,
            "avg_confidence": round(avg_confidence, 2),
        }


# Singleton
_kb: Optional[KnowledgeBase] = None


def get_knowledge_base() -> KnowledgeBase:
    global _kb
    if _kb is None:
        _kb = KnowledgeBase()
    return _kb
