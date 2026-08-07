"""
API endpoints for Pipeline Templates and Notifications.
Post-MVP Phase 4.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_active_user
from app.models.user import User
from app.services.pipeline_templates import (
    list_templates, get_template, register_custom_template,
    delete_custom_template, apply_template, get_template_categories,
    PipelineTemplate,
)
from app.services.pipeline_notifications import get_notification_manager
from app.services.feature_pipeline import (
    FeatureRequest, create_pipeline_run,
)

router = APIRouter(prefix="/pipeline-templates", tags=["pipeline-templates"])


# --- Template endpoints ---

@router.get("/", response_model=list[dict])
async def list_all_templates(
    category: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
):
    """List all available pipeline templates."""
    templates = list_templates(category=category)
    return [t.model_dump() for t in templates]


@router.get("/categories")
async def list_categories(
    current_user: User = Depends(get_current_active_user),
):
    """List all template categories with counts."""
    return get_template_categories()


@router.get("/{template_id}")
async def get_template_by_id(
    template_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """Get a specific template by ID."""
    template = get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template.model_dump()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_custom_template(
    template: PipelineTemplate,
    current_user: User = Depends(get_current_active_user),
):
    """Register a custom pipeline template."""
    if get_template(template.id):
        raise HTTPException(status_code=400, detail="Template ID already exists")
    register_custom_template(template)
    return template.model_dump()


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_custom_template(
    template_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """Delete a custom template (built-in templates cannot be deleted)."""
    if not delete_custom_template(template_id):
        raise HTTPException(status_code=400, detail="Cannot delete template (not found or built-in)")


@router.post("/{template_id}/apply", response_model=dict)
async def apply_template_to_feature(
    template_id: str,
    title: str = "",
    description: str = "",
    extra_constraints: Optional[list[str]] = None,
    extra_acceptance: Optional[list[str]] = None,
    current_user: User = Depends(get_current_active_user),
):
    """Apply a template to create a FeatureRequest dict."""
    result = apply_template(
        template_id, title, description,
        extra_constraints=extra_constraints or [],
        extra_acceptance=extra_acceptance or [],
    )
    if not result:
        raise HTTPException(status_code=404, detail="Template not found")
    return result


@router.post("/{template_id}/create-pipeline")
async def create_pipeline_from_template(
    template_id: str,
    title: str,
    description: str,
    current_user: User = Depends(get_current_active_user),
):
    """Apply a template and immediately create a pipeline run."""
    result = apply_template(template_id, title, description)
    if not result:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Remove template metadata from FeatureRequest
    template_meta = result.pop("_template", {})
    
    feature = FeatureRequest(**result)
    run = create_pipeline_run(feature)
    
    # Store template metadata in run
    run.summary = f"Template: {template_meta.get('name', template_id)}"
    
    # Import the pipeline store and save
    from app.api.v1.feature_pipeline import _pipeline_runs
    _pipeline_runs[run.id] = run
    
    # Return same format as pipeline run endpoint
    from app.api.v1.feature_pipeline import run_to_response
    return run_to_response(run)


# --- Notification endpoints ---

notif_router = APIRouter(prefix="/notifications", tags=["notifications"])


@notif_router.get("/")
async def get_notifications(
    unread_only: bool = False,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
):
    """Get pipeline notifications."""
    mgr = get_notification_manager()
    return {
        "notifications": mgr.get_notifications(unread_only=unread_only, limit=limit),
        "unread_count": mgr.unread_count,
        "total_count": mgr.total_count,
    }


@notif_router.get("/unread-count")
async def get_unread_count(
    current_user: User = Depends(get_current_active_user),
):
    """Get just the unread notification count."""
    mgr = get_notification_manager()
    return {"unread_count": mgr.unread_count}


@notif_router.post("/{notif_id}/read")
async def mark_notification_read(
    notif_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """Mark a notification as read."""
    mgr = get_notification_manager()
    success = mgr.mark_read(notif_id)
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"status": "read"}


@notif_router.post("/read-all")
async def mark_all_read(
    current_user: User = Depends(get_current_active_user),
):
    """Mark all notifications as read."""
    mgr = get_notification_manager()
    count = mgr.mark_all_read()
    return {"marked_read": count}


@notif_router.delete("/")
async def clear_notifications(
    current_user: User = Depends(get_current_active_user),
):
    """Clear all notifications."""
    mgr = get_notification_manager()
    mgr.clear_notifications()
    return {"status": "cleared"}


@notif_router.post("/webhook/configure")
async def configure_webhook(
    url: str = "",
    current_user: User = Depends(get_current_active_user),
):
    """Configure a webhook URL for external notifications."""
    mgr = get_notification_manager()
    if url:
        mgr.configure_webhook(url)
        return {"status": "configured", "url": url}
    return {"status": "no_url_provided"}
