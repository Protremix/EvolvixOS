"""API for Plugin Marketplace — Phase 39."""

from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_current_active_user
from app.models.user import User
from app.services.plugin_marketplace import get_plugin_marketplace_service

router = APIRouter(prefix="/plugins", tags=["plugin-marketplace"])


class SubmitPluginRequest(BaseModel):
    name: str
    description: str
    author: str
    version: str
    category: str
    license: str = "free"
    price: float = 0.0
    tags: list[str] = []
    homepage: str = ""
    repository: str = ""
    documentation: str = ""
    min_version: str = "1.0.0"
    checksum: str = ""
    size_bytes: int = 0
    metadata: dict = {}


class ReviewRequest(BaseModel):
    reviewer: str
    rating: float
    comment: str = ""


class RegisterDeveloperRequest(BaseModel):
    address: str
    name: str
    bio: str = ""
    website: str = ""


class UpdatePluginRequest(BaseModel):
    description: Optional[str] = None
    version: Optional[str] = None
    tags: Optional[list[str]] = None
    homepage: Optional[str] = None
    documentation: Optional[str] = None


@router.get("/dashboard")
async def get_dashboard(current_user: User = Depends(get_current_active_user)):
    return get_plugin_marketplace_service().get_dashboard()

@router.get("/stats")
async def get_stats(current_user: User = Depends(get_current_active_user)):
    return get_plugin_marketplace_service().get_stats()

# === Plugins ===

@router.post("/")
async def submit_plugin(req: SubmitPluginRequest, current_user: User = Depends(get_current_active_user)):
    return get_plugin_marketplace_service().submit_plugin(
        req.name, req.description, req.author, req.version, req.category,
        req.license, req.price, req.tags, req.homepage, req.repository,
        req.documentation, req.min_version, req.checksum, req.size_bytes, req.metadata,
    ).to_dict()

@router.get("/")
async def list_plugins(status: Optional[str] = None, category: Optional[str] = None,
                        author: Optional[str] = None, search: Optional[str] = None,
                        sort_by: str = "downloads", limit: int = 50,
                        current_user: User = Depends(get_current_active_user)):
    return [p.to_dict() for p in get_plugin_marketplace_service().list_plugins(status, category, author, search, sort_by, limit)]

@router.get("/{plugin_id}")
async def get_plugin(plugin_id: str, current_user: User = Depends(get_current_active_user)):
    p = get_plugin_marketplace_service().get_plugin(plugin_id)
    return p.to_dict() if p else {"error": "Plugin not found"}

@router.get("/slug/{slug}")
async def get_by_slug(slug: str, current_user: User = Depends(get_current_active_user)):
    p = get_plugin_marketplace_service().get_plugin_by_slug(slug)
    return p.to_dict() if p else {"error": "Plugin not found"}

@router.patch("/{plugin_id}")
async def update_plugin(plugin_id: str, req: UpdatePluginRequest, current_user: User = Depends(get_current_active_user)):
    kwargs = {k: v for k, v in req.model_dump().items() if v is not None}
    p = get_plugin_marketplace_service().update_plugin(plugin_id, **kwargs)
    return p.to_dict() if p else {"error": "Plugin not found"}

@router.post("/{plugin_id}/approve")
async def approve_plugin(plugin_id: str, current_user: User = Depends(get_current_active_user)):
    p = get_plugin_marketplace_service().approve_plugin(plugin_id)
    return p.to_dict() if p else {"error": "Cannot approve"}

@router.post("/{plugin_id}/reject")
async def reject_plugin(plugin_id: str, reason: str = "", current_user: User = Depends(get_current_active_user)):
    p = get_plugin_marketplace_service().reject_plugin(plugin_id, reason)
    return p.to_dict() if p else {"error": "Cannot reject"}

@router.post("/{plugin_id}/suspend")
async def suspend_plugin(plugin_id: str, current_user: User = Depends(get_current_active_user)):
    p = get_plugin_marketplace_service().suspend_plugin(plugin_id)
    return p.to_dict() if p else {"error": "Cannot suspend"}

@router.post("/{plugin_id}/deprecate")
async def deprecate_plugin(plugin_id: str, current_user: User = Depends(get_current_active_user)):
    p = get_plugin_marketplace_service().deprecate_plugin(plugin_id)
    return p.to_dict() if p else {"error": "Cannot deprecate"}

# === Installation ===

@router.post("/{plugin_id}/install")
async def install_plugin(plugin_id: str, user_address: str, current_user: User = Depends(get_current_active_user)):
    p = get_plugin_marketplace_service().install_plugin(plugin_id, user_address)
    return p.to_dict() if p else {"error": "Cannot install"}

@router.post("/{plugin_id}/uninstall")
async def uninstall_plugin(plugin_id: str, user_address: str, current_user: User = Depends(get_current_active_user)):
    return {"uninstalled": get_plugin_marketplace_service().uninstall_plugin(plugin_id, user_address)}

@router.get("/installed/{user_address}")
async def get_installed(user_address: str, current_user: User = Depends(get_current_active_user)):
    return [p.to_dict() for p in get_plugin_marketplace_service().get_installed_plugins(user_address)]

# === Reviews ===

@router.post("/{plugin_id}/reviews")
async def add_review(plugin_id: str, req: ReviewRequest, current_user: User = Depends(get_current_active_user)):
    r = get_plugin_marketplace_service().add_review(plugin_id, req.reviewer, req.rating, req.comment)
    return r.to_dict() if r else {"error": "Cannot review"}

@router.get("/{plugin_id}/reviews")
async def get_reviews(plugin_id: str, limit: int = 20, current_user: User = Depends(get_current_active_user)):
    return [r.to_dict() for r in get_plugin_marketplace_service().get_reviews(plugin_id, limit)]

@router.post("/reviews/{review_id}/helpful")
async def mark_helpful(review_id: str, current_user: User = Depends(get_current_active_user)):
    return {"helpful": get_plugin_marketplace_service().mark_review_helpful(review_id)}

# === Developers ===

@router.post("/developers")
async def register_developer(req: RegisterDeveloperRequest, current_user: User = Depends(get_current_active_user)):
    return get_plugin_marketplace_service().register_developer(req.address, req.name, req.bio, req.website).to_dict()

@router.post("/developers/{address}/verify")
async def verify_developer(address: str, current_user: User = Depends(get_current_active_user)):
    return {"verified": get_plugin_marketplace_service().verify_developer(address)}

@router.get("/developers/{address}")
async def get_developer(address: str, current_user: User = Depends(get_current_active_user)):
    d = get_plugin_marketplace_service().get_developer(address)
    return d.to_dict() if d else {"error": "Developer not found"}

@router.get("/developers")
async def list_developers(verified_only: bool = False, current_user: User = Depends(get_current_active_user)):
    return [d.to_dict() for d in get_plugin_marketplace_service().list_developers(verified_only)]

# === Categories ===

@router.get("/categories/list")
async def list_categories():
    return get_plugin_marketplace_service().list_categories()
