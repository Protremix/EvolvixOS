"""API for Documentation & Deployment Manifests — Phase 51."""

from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_current_active_user
from app.models.user import User
from app.services.deployment_docs import get_deployment_docs_service

router = APIRouter(prefix="/docs", tags=["deployment-docs"])


class CreateDocRequest(BaseModel):
    title: str
    category: str
    description: str
    content: str = ""
    tags: list = []


class CreateManifestRequest(BaseModel):
    name: str
    type: str
    component: str
    filename: str
    content: str
    description: str = ""
    env_vars: list = []
    dependencies: list = []
    port: int = 0
    health_check: str = ""


class CreateFAQRequest(BaseModel):
    question: str
    answer: str
    category: str = "general"


class CreateRunbookRequest(BaseModel):
    name: str
    scenario: str
    steps: list
    rollback_steps: list = []
    severity: str = "medium"
    estimated_time: str = ""


@router.get("/dashboard")
async def get_dashboard(current_user: User = Depends(get_current_active_user)):
    return get_deployment_docs_service().get_dashboard()

# === Docs ===

@router.get("/")
async def list_docs(category: Optional[str] = None, status: Optional[str] = None,
                     limit: int = 50, current_user: User = Depends(get_current_active_user)):
    return [d.to_dict() for d in get_deployment_docs_service().list_docs(category, status, limit)]

@router.get("/search")
async def search_docs(q: str, limit: int = 20, current_user: User = Depends(get_current_active_user)):
    return [d.to_dict() for d in get_deployment_docs_service().search_docs(q, limit)]

@router.get("/{doc_id}")
async def get_doc(doc_id: str, current_user: User = Depends(get_current_active_user)):
    d = get_deployment_docs_service().get_doc(doc_id)
    return d.to_dict() if d else {"error": "Doc not found"}

@router.post("/")
async def create_doc(req: CreateDocRequest, current_user: User = Depends(get_current_active_user)):
    return get_deployment_docs_service().create_doc(
        req.title, req.category, req.description, req.content, req.tags
    ).to_dict()

@router.patch("/{doc_id}")
async def update_doc(doc_id: str, req: dict, current_user: User = Depends(get_current_active_user)):
    d = get_deployment_docs_service().update_doc(doc_id, **req)
    return d.to_dict() if d else {"error": "Doc not found"}

@router.delete("/{doc_id}")
async def delete_doc(doc_id: str, current_user: User = Depends(get_current_active_user)):
    return {"deleted": get_deployment_docs_service().delete_doc(doc_id)}

# === Manifests ===

@router.get("/manifests")
async def list_manifests(type: Optional[str] = None, component: Optional[str] = None,
                          current_user: User = Depends(get_current_active_user)):
    return [m.to_dict() for m in get_deployment_docs_service().list_manifests(type, component)]

@router.get("/manifests/{manifest_id}")
async def get_manifest(manifest_id: str, current_user: User = Depends(get_current_active_user)):
    m = get_deployment_docs_service().get_manifest(manifest_id)
    return m.to_dict() if m else {"error": "Manifest not found"}

@router.post("/manifests")
async def create_manifest(req: CreateManifestRequest, current_user: User = Depends(get_current_active_user)):
    return get_deployment_docs_service().create_manifest(
        req.name, req.type, req.component, req.filename, req.content,
        description=req.description, env_vars=req.env_vars,
        dependencies=req.dependencies, port=req.port, health_check=req.health_check,
    ).to_dict()

# === FAQs ===

@router.get("/faqs")
async def list_faqs(category: Optional[str] = None, limit: int = 50,
                     current_user: User = Depends(get_current_active_user)):
    return [f.to_dict() for f in get_deployment_docs_service().list_faqs(category, limit)]

@router.get("/faqs/search")
async def search_faqs(q: str, limit: int = 20, current_user: User = Depends(get_current_active_user)):
    return [f.to_dict() for f in get_deployment_docs_service().search_faqs(q, limit)]

@router.post("/faqs")
async def create_faq(req: CreateFAQRequest, current_user: User = Depends(get_current_active_user)):
    return get_deployment_docs_service().create_faq(req.question, req.answer, req.category).to_dict()

@router.post("/faqs/{faq_id}/helpful")
async def mark_helpful(faq_id: str, current_user: User = Depends(get_current_active_user)):
    f = get_deployment_docs_service().mark_faq_helpful(faq_id)
    return f.to_dict() if f else {"error": "FAQ not found"}

# === Runbooks ===

@router.get("/runbooks")
async def list_runbooks(severity: Optional[str] = None, current_user: User = Depends(get_current_active_user)):
    return [r.to_dict() for r in get_deployment_docs_service().list_runbooks(severity)]

@router.get("/runbooks/{runbook_id}")
async def get_runbook(runbook_id: str, current_user: User = Depends(get_current_active_user)):
    r = get_deployment_docs_service().get_runbook(runbook_id)
    return r.to_dict() if r else {"error": "Runbook not found"}

@router.post("/runbooks")
async def create_runbook(req: CreateRunbookRequest, current_user: User = Depends(get_current_active_user)):
    return get_deployment_docs_service().create_runbook(
        req.name, req.scenario, req.steps, req.rollback_steps,
        req.severity, req.estimated_time,
    ).to_dict()
