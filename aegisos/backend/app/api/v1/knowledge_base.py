"""
API endpoints for Knowledge Base — Post-MVP Phase 6.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.deps import get_current_active_user
from app.models.user import User
from app.services.knowledge_base import KnowledgeEntry, PatternRecord, get_knowledge_base

router = APIRouter(prefix="/knowledge-base", tags=["knowledge-base"])


# --- Knowledge Entry endpoints ---

@router.get("/")
async def list_entries(
    category: Optional[str] = None,
    source: Optional[str] = None,
    project_type: Optional[str] = None,
    tag: Optional[str] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
):
    """List knowledge entries with optional filters."""
    kb = get_knowledge_base()
    entries = kb.list_entries(category=category, source=source, project_type=project_type, tag=tag, limit=limit)
    return [e.to_dict() for e in entries]


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_entry(
    entry: KnowledgeEntry,
    current_user: User = Depends(get_current_active_user),
):
    """Create a new knowledge entry."""
    kb = get_knowledge_base()
    result = kb.add_entry(entry)
    return result.to_dict()


@router.get("/search")
async def search_entries(
    q: str = "",
    limit: int = 10,
    current_user: User = Depends(get_current_active_user),
):
    """Search knowledge entries with relevance scoring."""
    if not q:
        raise HTTPException(status_code=400, detail="Query parameter 'q' is required")
    kb = get_knowledge_base()
    return kb.search(q, limit)


@router.get("/stats")
async def get_stats(
    current_user: User = Depends(get_current_active_user),
):
    """Get knowledge base statistics."""
    return get_knowledge_base().get_stats()


@router.get("/{entry_id}")
async def get_entry(
    entry_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """Get a specific knowledge entry."""
    entry = get_knowledge_base().get_entry(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry.to_dict()


@router.patch("/{entry_id}")
async def update_entry(
    entry_id: str,
    updates: dict,
    current_user: User = Depends(get_current_active_user),
):
    """Update a knowledge entry."""
    result = get_knowledge_base().update_entry(entry_id, updates)
    if not result:
        raise HTTPException(status_code=404, detail="Entry not found")
    return result.to_dict()


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_entry(
    entry_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """Delete a knowledge entry."""
    if not get_knowledge_base().delete_entry(entry_id):
        raise HTTPException(status_code=404, detail="Entry not found")


# --- Pattern endpoints ---

@router.get("/patterns/list")
async def list_patterns(
    pattern_type: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
):
    """List detected patterns."""
    kb = get_knowledge_base()
    patterns = kb.list_patterns(pattern_type=pattern_type)
    return [p.to_dict() for p in patterns]


@router.delete("/patterns/{pattern_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pattern(
    pattern_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """Delete a pattern."""
    if not get_knowledge_base().delete_pattern(pattern_id):
        raise HTTPException(status_code=404, detail="Pattern not found")


@router.post("/patterns/extract")
async def extract_patterns(
    current_user: User = Depends(get_current_active_user),
):
    """Extract patterns from all pipeline runs."""
    from app.api.v1.feature_pipeline import _pipeline_runs
    kb = get_knowledge_base()
    runs = list(_pipeline_runs.values())
    patterns = kb.extract_patterns_from_runs(runs)
    return [p.to_dict() for p in patterns]


@router.post("/lessons/{pipeline_id}")
async def extract_lessons(
    pipeline_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """Extract lessons from a specific pipeline run."""
    from app.api.v1.feature_pipeline import _pipeline_runs
    run = _pipeline_runs.get(pipeline_id)
    if not run:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    kb = get_knowledge_base()
    lessons = kb.extract_lessons_from_run(run)
    return [l.to_dict() for l in lessons]
