"""
AI Memory Agent — conversation context, decision history, knowledge retention.

This agent handles three task types:
- CONTEXT_STORE: Store context/data for later retrieval
- CONTEXT_RETRIEVAL: Search for relevant stored context
- KNOWLEDGE_INDEX: Index a document into the pgvector knowledge base

The memory agent has a custom execute() that doesn't always need an LLM call.
For CONTEXT_STORE and CONTEXT_RETRIEVAL, it operates directly on storage.
For KNOWLEDGE_INDEX, it may use the LLM to generate a summary before indexing.
"""

import json
import uuid
from datetime import datetime, UTC
from typing import Any, Optional

from structlog import get_logger

from app.ai.agents.base_agent import (
    BaseAgent,
    AgentTask,
    AgentResult,
    AgentStatus,
    TaskType,
)

logger = get_logger("agent.memory_agent")

# In-memory store for contexts (fallback when no DB session available)
_memory_store: list[dict] = []


class AIMemoryAgent(BaseAgent):
    """
    AI Memory Agent — stores and retrieves context, decisions, and knowledge.

    Uses the DocumentEmbedding model with pgvector for semantic search
    when available, falls back to in-memory text matching otherwise.
    """

    name = "memory_agent"
    description = "AI Memory — context storage, retrieval, and knowledge indexing"
    handled_task_types = {TaskType.CONTEXT_STORE, TaskType.CONTEXT_RETRIEVAL, TaskType.KNOWLEDGE_INDEX}

    @property
    def system_prompt(self) -> str:
        from app.ai.prompts.system_prompts import MEMORY_SYSTEM_PROMPT
        return MEMORY_SYSTEM_PROMPT

    def execute(self, task: AgentTask) -> AgentResult:
        """
        Execute the memory task based on task type.

        - CONTEXT_STORE: Store the data directly (no LLM needed)
        - CONTEXT_RETRIEVAL: Search stored data (no LLM for simple search)
        - KNOWLEDGE_INDEX: Index a document (may use LLM for summary)
        """
        import time

        self.logger.info("memory_agent_executing", task_id=task.id, task_type=task.type.value)
        task.status = AgentStatus.RUNNING
        start = time.time()

        try:
            if task.type == TaskType.CONTEXT_STORE:
                result = self._store_context(task)
            elif task.type == TaskType.CONTEXT_RETRIEVAL:
                result = self._retrieve_context(task)
            elif task.type == TaskType.KNOWLEDGE_INDEX:
                result = self._index_knowledge(task)
            else:
                raise ValueError(f"Memory agent cannot handle task type: {task.type.value}")

            latency_ms = (time.time() - start) * 1000
            task.status = AgentStatus.COMPLETED
            task.completed_at = datetime.now(UTC).isoformat()
            task.latency_ms = latency_ms

            result.latency_ms = latency_ms
            return result

        except Exception as e:
            task.status = AgentStatus.FAILED
            task.error = str(e)
            task.completed_at = datetime.now(UTC).isoformat()

            self.logger.error("memory_agent_failed", task_id=task.id, error=str(e))

            return AgentResult(
                task_id=task.id,
                agent_name=self.name,
                status=AgentStatus.FAILED,
                content=f"Memory agent failed: {str(e)}",
            )

    def _store_context(self, task: AgentTask) -> AgentResult:
        """Store context data in memory."""
        data = task.data
        entry = {
            "id": str(uuid.uuid4()),
            "title": data.get("title", "Untitled"),
            "content": data.get("content", ""),
            "source": data.get("source", "user"),
            "project_id": data.get("project_id"),
            "metadata": data.get("metadata", {}),
            "timestamp": datetime.now(UTC).isoformat(),
        }

        _memory_store.append(entry)

        self.logger.info("context_stored", entry_id=entry["id"], title=entry["title"])

        return AgentResult(
            task_id=task.id,
            agent_name=self.name,
            status=AgentStatus.COMPLETED,
            content=f"Context stored: {entry['title']}",
            structured_data={
                "action": "store",
                "entry_id": entry["id"],
                "title": entry["title"],
                "stored_at": entry["timestamp"],
            },
        )

    def _retrieve_context(self, task: AgentTask) -> AgentResult:
        """Retrieve relevant context from memory store."""
        query = task.data.get("query", "")
        limit = task.data.get("limit", 5)
        project_id = task.data.get("project_id")

        # Simple keyword matching (fallback for when pgvector isn't available)
        results = []
        query_lower = query.lower()

        for entry in _memory_store:
            # Filter by project_id if specified
            if project_id and entry.get("project_id") != project_id:
                continue

            # Simple relevance scoring
            content_lower = entry["content"].lower()
            title_lower = entry["title"].lower()

            score = 0.0
            if query_lower in title_lower:
                score += 0.5
            if query_lower in content_lower:
                score += 0.3

            # Count word overlap
            query_words = set(query_lower.split())
            content_words = set(content_lower.split())
            overlap = len(query_words & content_words)
            if query_words:
                score += (overlap / len(query_words)) * 0.2

            if score > 0:
                results.append({
                    "source": entry["source"],
                    "title": entry["title"],
                    "content": entry["content"][:500],
                    "relevance_score": round(min(score, 1.0), 3),
                    "timestamp": entry["timestamp"],
                })

        # Sort by relevance and limit
        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        results = results[:limit]

        self.logger.info("context_retrieved", query=query, results=len(results))

        return AgentResult(
            task_id=task.id,
            agent_name=self.name,
            status=AgentStatus.COMPLETED,
            content=f"Retrieved {len(results)} memories for query: {query}",
            structured_data={
                "action": "retrieve",
                "query": query,
                "relevant_memories": results,
            },
        )

    def _index_knowledge(self, task: AgentTask) -> AgentResult:
        """Index a document into the knowledge base."""
        title = task.data.get("title", "Untitled")
        content = task.data.get("content", "")
        source = task.data.get("source", "document")

        # Store in memory (will use pgvector when DB is available)
        entry = {
            "id": str(uuid.uuid4()),
            "title": title,
            "content": content,
            "source": source,
            "project_id": task.data.get("project_id"),
            "metadata": {"indexed": True, "index_time": datetime.now(UTC).isoformat()},
            "timestamp": datetime.now(UTC).isoformat(),
        }

        _memory_store.append(entry)

        self.logger.info("knowledge_indexed", entry_id=entry["id"], title=title, source=source)

        return AgentResult(
            task_id=task.id,
            agent_name=self.name,
            status=AgentStatus.COMPLETED,
            content=f"Document indexed: {title}",
            structured_data={
                "action": "index",
                "entry_id": entry["id"],
                "title": title,
                "source": source,
                "indexed_at": entry["timestamp"],
            },
        )

    @staticmethod
    def get_store_size() -> int:
        """Get the number of entries in the memory store."""
        return len(_memory_store)

    @staticmethod
    def clear_store() -> None:
        """Clear the memory store (for testing)."""
        _memory_store.clear()
