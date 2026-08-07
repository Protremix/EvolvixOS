"""
Dependency Graph API endpoints.

Provides REST access to the dependency graph tracker.
"""

import os
import hashlib
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.api.deps import get_current_active_user
from app.models.user import User

router = APIRouter(prefix="/dep-graph", tags=["dependency-graph"])


class BuildGraphRequest(BaseModel):
    project_path: str = Field(..., description="Root path of the project to analyze")
    ignore_dirs: list[str] = Field(default_factory=list, description="Directories to ignore")


class AnalyzeFileRequest(BaseModel):
    file_path: str = Field(..., description="File path to analyze impact for")
    max_depth: int = Field(10, description="Max traversal depth")


# In-memory graph cache keyed by hash of project path
_graph_cache: dict[str, dict] = {}


def _cache_key(project_path: str) -> str:
    return hashlib.md5(project_path.encode()).hexdigest()[:12]


@router.post("/build")
async def build_graph(
    request: BuildGraphRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Build a dependency graph for a project."""
    from app.services.dependency_graph import DependencyGraphBuilder

    if not os.path.exists(request.project_path):
        raise HTTPException(status_code=400, detail=f"Path not found: {request.project_path}")

    ignore = set(request.ignore_dirs) if request.ignore_dirs else None
    builder = DependencyGraphBuilder(request.project_path, ignore_dirs=ignore)
    graph = builder.build()

    result = graph.to_dict()
    key = _cache_key(request.project_path)
    result["cache_key"] = key
    result["project_path"] = request.project_path
    _graph_cache[key] = result
    return result


@router.get("/stats")
async def get_graph_stats(
    project_path: str = Query(..., description="Project path"),
    current_user: User = Depends(get_current_active_user),
):
    """Get dependency graph statistics for a project."""
    key = _cache_key(project_path)
    if key not in _graph_cache:
        raise HTTPException(status_code=404, detail="Graph not built. Call /build first.")
    return _graph_cache[key].get("stats", {})


@router.get("/cycles")
async def get_cycles(
    project_path: str = Query(..., description="Project path"),
    current_user: User = Depends(get_current_active_user),
):
    """Get detected circular dependencies for a project."""
    key = _cache_key(project_path)
    if key not in _graph_cache:
        raise HTTPException(status_code=404, detail="Graph not built. Call /build first.")
    return {"cycles": _graph_cache[key].get("cycles", [])}


@router.post("/impact")
async def impact_analysis(
    request: AnalyzeFileRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Analyze the impact of changing a file."""
    from app.services.dependency_graph import DependencyGraph, DependencyNode

    for key, graph_data in _graph_cache.items():
        graph = DependencyGraph()
        for node_data in graph_data.get("nodes", []):
            node = DependencyNode(
                file_path=node_data["file_path"],
                module_name=node_data["module_name"],
                language=node_data["language"],
                imports=node_data.get("imports", []),
                imported_by=node_data.get("imported_by", []),
                line_count=node_data.get("line_count", 0),
                is_entry_point=node_data.get("is_entry_point", False),
            )
            graph.add_node(node)
            for dep in node.imported_by:
                graph.add_edge(dep, node.file_path)

        if request.file_path in graph.nodes:
            return graph.get_impact(request.file_path, request.max_depth)

    raise HTTPException(status_code=404, detail=f"File not found in any cached graph: {request.file_path}")


@router.get("/dependencies")
async def get_dependencies(
    project_path: str = Query(..., description="Project path"),
    file_path: str = Query("", description="Specific file to get deps for"),
    current_user: User = Depends(get_current_active_user),
):
    """Get dependencies for a file or all files in the project."""
    key = _cache_key(project_path)
    if key not in _graph_cache:
        raise HTTPException(status_code=404, detail="Graph not built. Call /build first.")

    graph_data = _graph_cache[key]
    nodes = graph_data.get("nodes", [])

    if file_path:
        node = next((n for n in nodes if n["file_path"] == file_path), None)
        if not node:
            raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
        return {
            "file": file_path,
            "imports": node.get("imports", []),
            "imported_by": node.get("imported_by", []),
        }
    else:
        return {
            "dependencies": [
                {"file": n["file_path"], "imports": n.get("imports", []), "imported_by": n.get("imported_by", [])}
                for n in nodes
            ]
        }


@router.delete("/cache")
async def clear_cache(
    project_path: str = Query(..., description="Project path"),
    current_user: User = Depends(get_current_active_user),
):
    """Clear the cached graph for a project."""
    key = _cache_key(project_path)
    if key in _graph_cache:
        del _graph_cache[key]
        return {"cleared": True}
    raise HTTPException(status_code=404, detail="No cached graph found for this project")
