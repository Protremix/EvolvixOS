"""
AST-Aware Diff API endpoints.

Provides REST access to semantic code diffing.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.deps import get_current_active_user
from app.models.user import User

router = APIRouter(prefix="/ast-diff", tags=["ast-diff"])


class DiffRequest(BaseModel):
    old_code: str = Field(..., description="Old version of source code")
    new_code: str = Field(..., description="New version of source code")
    language: str = Field("python", description="Language: python, javascript, typescript")


class FileDiffRequest(BaseModel):
    old_file: str = Field(..., description="Path to old file")
    new_file: str = Field(..., description="Path to new file")
    language: str = Field("python", description="Language")


@router.post("/compare")
async def compare_code(
    request: DiffRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Generate a semantic AST diff between two code versions."""
    from app.services.ast_diff import ASTDiffEngine
    engine = ASTDiffEngine()
    return engine.diff(request.old_code, request.new_code, request.language)


@router.post("/compare-files")
async def compare_files(
    request: FileDiffRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Compare two files on disk."""
    import os
    if not os.path.exists(request.old_file):
        raise HTTPException(status_code=400, detail=f"Old file not found: {request.old_file}")
    if not os.path.exists(request.new_file):
        raise HTTPException(status_code=400, detail=f"New file not found: {request.new_file}")

    with open(request.old_file, "r") as f:
        old_code = f.read()
    with open(request.new_file, "r") as f:
        new_code = f.read()

    from app.services.ast_diff import ASTDiffEngine
    engine = ASTDiffEngine()
    result = engine.diff(old_code, new_code, request.language)
    result["old_file"] = request.old_file
    result["new_file"] = request.new_file
    return result


@router.get("/info")
async def diff_info(
    current_user: User = Depends(get_current_active_user),
):
    """Get info about the AST diff engine."""
    return {
        "engine": "ast_diff",
        "description": "Semantic code diffing using Abstract Syntax Tree analysis",
        "supported_languages": ["python (full AST)", "javascript (line-level)", "typescript (line-level)"],
        "change_types": ["added", "removed", "modified", "renamed", "signature_changed"],
        "features": [
            "function/class detection",
            "import tracking",
            "signature comparison",
            "body change detection",
            "rename detection (similarity > 60%)",
            "method-level comparison within classes",
            "breaking change detection",
        ],
    }
