"""
Global Search Service — Post-MVP Phase 10

Unified search across all EvolvixOS entities:
- Pipelines (title, description, status)
- Knowledge base entries (title, content, tags)
- Activity log entries (action, entity_name, user_email)
- Webhook subscriptions (url, description, event_types)
- System settings (key, description, category)
- AI agents (agent_name, description)
- Pipeline templates (name, description)
"""

from typing import Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
from app.core.logging import get_logger

logger = get_logger("service.global_search")


@dataclass
class SearchResult:
    """A single search result."""
    entity_type: str  # pipeline, knowledge, activity, webhook, setting, agent, template
    entity_id: str
    title: str
    description: str
    relevance: float
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


class GlobalSearchService:
    """Searches across all EvolvixOS entities."""

    def search(self, query: str, entity_types: Optional[list[str]] = None, limit: int = 50) -> list[SearchResult]:
        """
        Search across all entities.
        
        Args:
            query: Search query
            entity_types: Optional filter (pipeline, knowledge, activity, webhook, setting, agent, template)
            limit: Max results per entity type
        """
        results = []
        query_lower = query.lower()
        query_words = [w for w in query_lower.split() if len(w) > 1]

        # Search pipelines
        if not entity_types or "pipeline" in entity_types:
            results.extend(self._search_pipelines(query_lower, query_words, limit))

        # Search knowledge base
        if not entity_types or "knowledge" in entity_types:
            results.extend(self._search_knowledge(query_lower, query_words, limit))

        # Search activity log
        if not entity_types or "activity" in entity_types:
            results.extend(self._search_activity(query_lower, query_words, limit))

        # Search webhooks
        if not entity_types or "webhook" in entity_types:
            results.extend(self._search_webhooks(query_lower, query_words, limit))

        # Search system settings
        if not entity_types or "setting" in entity_types:
            results.extend(self._search_settings(query_lower, query_words, limit))

        # Search pipeline templates
        if not entity_types or "template" in entity_types:
            results.extend(self._search_templates(query_lower, query_words, limit))

        # Sort by relevance
        results.sort(key=lambda r: r.relevance, reverse=True)
        return results[:limit * 3]  # Allow more total, but capped

    def _search_pipelines(self, query: str, words: list[str], limit: int) -> list[SearchResult]:
        results = []
        try:
            from app.api.v1.feature_pipeline import _pipeline_runs
            for run in _pipeline_runs.values():
                title = getattr(run, "title", "") or ""
                status = run.status or ""
                text = f"{title} {status}".lower()
                relevance = self._score(text, query, words)
                if relevance > 0:
                    results.append(SearchResult(
                        entity_type="pipeline",
                        entity_id=run.id,
                        title=title,
                        description=f"Status: {status}",
                        relevance=relevance,
                        metadata={"status": status},
                    ))
        except Exception:
            pass
        return results[:limit]

    def _search_knowledge(self, query: str, words: list[str], limit: int) -> list[SearchResult]:
        results = []
        try:
            from app.services.knowledge_base import get_knowledge_base
            kb = get_knowledge_base()
            for entry in kb._entries.values():
                title = entry.title.lower()
                content = entry.content.lower()
                tags = " ".join(entry.tags).lower()
                text = f"{title} {content} {tags}"
                relevance = self._score(text, query, words)
                # Boost title matches
                if query in title:
                    relevance += 0.5
                if relevance > 0:
                    results.append(SearchResult(
                        entity_type="knowledge",
                        entity_id=entry.id,
                        title=entry.title,
                        description=entry.content[:100],
                        relevance=relevance,
                        metadata={"category": entry.category, "tags": entry.tags},
                    ))
        except Exception:
            pass
        return results[:limit]

    def _search_activity(self, query: str, words: list[str], limit: int) -> list[SearchResult]:
        results = []
        try:
            from app.services.activity_log import get_activity_log
            log = get_activity_log()
            for entry in log._entries:
                text = f"{entry.action} {entry.entity_name} {entry.user_email}".lower()
                relevance = self._score(text, query, words)
                if relevance > 0:
                    results.append(SearchResult(
                        entity_type="activity",
                        entity_id=entry.id,
                        title=entry.action,
                        description=f"{entry.entity_type}: {entry.entity_name}" if entry.entity_name else entry.action,
                        relevance=relevance,
                        metadata={"severity": entry.severity, "timestamp": entry.timestamp},
                    ))
        except Exception:
            pass
        return results[:limit]

    def _search_webhooks(self, query: str, words: list[str], limit: int) -> list[SearchResult]:
        results = []
        try:
            from app.services.webhook_subscriptions import get_webhook_manager
            mgr = get_webhook_manager()
            for sub in mgr._subscriptions.values():
                text = f"{sub.url} {sub.description} {' '.join(sub.event_types)}".lower()
                relevance = self._score(text, query, words)
                if relevance > 0:
                    results.append(SearchResult(
                        entity_type="webhook",
                        entity_id=sub.id,
                        title=sub.url,
                        description=sub.description or ", ".join(sub.event_types),
                        relevance=relevance,
                        metadata={"active": sub.active, "event_types": sub.event_types},
                    ))
        except Exception:
            pass
        return results[:limit]

    def _search_settings(self, query: str, words: list[str], limit: int) -> list[SearchResult]:
        results = []
        try:
            from app.services.system_settings import get_settings_manager
            mgr = get_settings_manager()
            for setting in mgr.list_all():
                text = f"{setting['key']} {setting['description']} {setting['category']}".lower()
                relevance = self._score(text, query, words)
                if relevance > 0:
                    results.append(SearchResult(
                        entity_type="setting",
                        entity_id=setting["key"],
                        title=setting["key"],
                        description=setting["description"],
                        relevance=relevance,
                        metadata={"category": setting["category"], "value": str(setting["value"])},
                    ))
        except Exception:
            pass
        return results[:limit]

    def _search_templates(self, query: str, words: list[str], limit: int) -> list[SearchResult]:
        results = []
        try:
            from app.services.pipeline_templates import list_templates
            templates = list_templates()
            for tmpl in templates:
                text = f"{tmpl.name} {tmpl.description} {tmpl.category}".lower()
                relevance = self._score(text, query, words)
                if relevance > 0:
                    results.append(SearchResult(
                        entity_type="template",
                        entity_id=tmpl.id,
                        title=tmpl.name,
                        description=tmpl.description,
                        relevance=relevance,
                        metadata={"category": tmpl.category},
                    ))
        except Exception:
            pass
        return results[:limit]

    def _score(self, text: str, query: str, words: list[str]) -> float:
        """Calculate relevance score."""
        score = 0.0
        if query in text:
            score += 1.0  # Exact phrase match
        for word in words:
            count = text.count(word)
            score += count * 0.3
        return round(score, 2)

    def get_searchable_types(self) -> list[dict]:
        """Get list of searchable entity types."""
        return [
            {"type": "pipeline", "label": "Pipelines", "description": "Feature delivery pipeline runs"},
            {"type": "knowledge", "label": "Knowledge Base", "description": "Best practices, lessons, patterns"},
            {"type": "activity", "label": "Activity Log", "description": "User and system actions"},
            {"type": "webhook", "label": "Webhooks", "description": "Webhook subscriptions"},
            {"type": "setting", "label": "Settings", "description": "System configuration"},
            {"type": "template", "label": "Templates", "description": "Pipeline templates"},
        ]


# Singleton
_search: Optional[GlobalSearchService] = None


def get_search_service() -> GlobalSearchService:
    global _search
    if _search is None:
        _search = GlobalSearchService()
    return _search
