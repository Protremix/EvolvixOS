"""Module 4: AI Knowledge Assistant."""
from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import Optional
import time

from app.models import database

router = APIRouter(prefix="/knowledge", tags=["knowledge"])

def _get_kb_service(req: Request):
    if hasattr(req.app.state, 'knowledge') and req.app.state.knowledge:
        return req.app.state.knowledge
    from app.services.knowledge_service import KnowledgeService
    return KnowledgeService()

class SearchQuery(BaseModel):
    query: str
    limit: int = 10
    category: Optional[str] = None

class CreateEntry(BaseModel):
    title: str
    content: str
    category: str = "general"
    source: str = "manual"
    tags: list[str] = []
    verified: bool = False

@router.post("/search")
async def search_knowledge(req: Request, query: SearchQuery):
    service = _get_kb_service(req)
    results = service.search(query.query, category=query.category, limit=query.limit)
    return {"results": results, "total": len(results), "query": query.query}

@router.get("/search")
async def search_get(req: Request, q: str, category: Optional[str] = None, limit: int = 10):
    service = _get_kb_service(req)
    results = service.search(q, category=category, limit=limit)
    return {"results": results, "total": len(results)}

@router.post("/entries")
async def create_entry(req: Request, entry: CreateEntry):
    service = _get_kb_service(req)
    return service.create_entry(entry.title, entry.content, entry.category,
                                entry.source, entry.tags, entry.verified)

@router.get("/entries")
async def list_entries(req: Request, category: Optional[str] = None, limit: int = 50, offset: int = 0):
    service = _get_kb_service(req)
    entries = service.list_entries(category=category, limit=limit, offset=offset)
    return {"entries": entries, "total": len(entries)}

@router.get("/entries/{entry_id}")
async def get_entry(entry_id: str, req: Request):
    service = _get_kb_service(req)
    entry = service.get_entry(entry_id)
    if not entry:
        return {"error": "Entry not found"}
    return entry

@router.get("/categories/list")
async def list_categories():
    return {"categories": ["documentation", "api_reference", "developer_docs", "whitepaper",
                           "runbook", "security", "faq", "architecture", "release_notes", "roadmap"]}

@router.get("/stats")
async def knowledge_stats(req: Request):
    service = _get_kb_service(req)
    return service.get_stats()
