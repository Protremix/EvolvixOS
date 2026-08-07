"""Module 11: Learning Engine."""
from fastapi import APIRouter, Request, Query
from pydantic import BaseModel
from typing import Optional
import time
from app.models import database

router = APIRouter(prefix="/learning", tags=["learning"])

class StoreLearning(BaseModel):
    conversation_id: str
    issue_type: str
    resolution: str
    successful: bool = True
    tags: list[str] = []
    user_satisfied: Optional[bool] = None

class CreateSolution(BaseModel):
    title: str
    problem: str
    solution: str
    category: str = "general"
    tags: list[str] = []

@router.post("/store")
async def store_learning(req: Request, learning: StoreLearning):
    conv_msgs = database.list_records("messages",
        filter_fn=lambda r: r.get("conversation_id") == learning.conversation_id, limit=100)
    return database.insert("learning_entries", {
        "conversation_id": learning.conversation_id,
        "issue_type": learning.issue_type,
        "resolution": learning.resolution,
        "successful": learning.successful,
        "tags": learning.tags,
        "user_satisfied": learning.user_satisfied,
        "conversation_summary": {
            "messages": len(conv_msgs),
            "first_message": conv_msgs[0]["content"][:200] if conv_msgs else "",
            "last_message": conv_msgs[-1]["content"][:200] if conv_msgs else "",
        },
    })

@router.post("/solutions")
async def create_solution(req: Request, solution: CreateSolution):
    return database.insert("solutions", {
        "title": solution.title,
        "problem": solution.problem,
        "solution": solution.solution,
        "category": solution.category,
        "tags": solution.tags,
        "usage_count": 0,
        "success_rate": 100,
    })

@router.get("/solutions")
async def list_solutions(category: Optional[str] = None, limit: int = 50):
    solutions = database.list_records("solutions",
        filter_fn=lambda r: (not category or r.get("category") == category),
        limit=limit)
    return {"solutions": solutions, "total": len(solutions)}

@router.get("/solutions/search")
async def search_solutions(q: str, limit: int = 10):
    solutions = database.list_records("solutions", limit=100)
    q_lower = q.lower()
    scored = []
    for s in solutions:
        score = 0
        text = (s.get("title", "") + " " + s.get("problem", "") + " " + s.get("solution", "")).lower()
        for word in q_lower.split():
            if word in text:
                score += 1
        if score > 0:
            scored.append((score, s))
    scored.sort(key=lambda x: x[0], reverse=True)
    return {"results": [s for _, s in scored[:limit]], "total": len(scored)}

@router.get("/entries")
async def list_learning_entries(limit: int = 50):
    entries = database.list_records("learning_entries", limit=limit)
    return {"entries": entries, "total": len(entries)}

@router.get("/stats")
async def learning_stats():
    entries = database.list_records("learning_entries", limit=1000)
    solutions = database.list_records("solutions", limit=1000)
    successful = sum(1 for e in entries if e.get("successful"))
    return {
        "total_learnings": len(entries),
        "successful_resolutions": successful,
        "success_rate": round(successful / len(entries) * 100, 1) if entries else 0,
        "total_solutions": len(solutions),
    }
