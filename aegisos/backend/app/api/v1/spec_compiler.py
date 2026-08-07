"""
Spec-Driven Compiler API endpoints.

Provides REST access to spec compilation and code generation.
"""

import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.deps import get_current_active_user
from app.models.user import User

router = APIRouter(prefix="/spec-compiler", tags=["spec-compiler"])


class CompileSpecRequest(BaseModel):
    spec: dict = Field(..., description="OpenAPI or AsyncAPI spec as JSON object")
    spec_format: str = Field("openapi", description="Spec format: openapi or asyncapi")


class CompileStringRequest(BaseModel):
    spec_json: str = Field(..., description="OpenAPI or AsyncAPI spec as JSON string")
    spec_format: str = Field("openapi", description="Spec format: openapi or asyncapi")


@router.post("/compile")
async def compile_spec(
    request: CompileSpecRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Compile a spec into a code blueprint with generated code."""
    from app.services.spec_compiler import SpecCompiler
    compiler = SpecCompiler()
    try:
        return compiler.compile(request.spec, request.spec_format)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Compilation failed: {str(e)}")


@router.post("/compile-string")
async def compile_spec_string(
    request: CompileStringRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Compile a spec from a JSON string."""
    from app.services.spec_compiler import SpecCompiler
    try:
        spec = json.loads(request.spec_json)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")
    compiler = SpecCompiler()
    try:
        return compiler.compile(spec, request.spec_format)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Compilation failed: {str(e)}")


@router.get("/info")
async def compiler_info(
    current_user: User = Depends(get_current_active_user),
):
    """Get info about the spec compiler."""
    return {
        "engine": "spec_compiler",
        "description": "Compiles OpenAPI/AsyncAPI specs into code blueprints",
        "supported_formats": ["openapi", "asyncapi"],
        "output_types": ["pydantic_models", "fastapi_routes", "typescript_types"],
        "features": [
            "schema parsing (properties, required, $ref, allOf)",
            "endpoint parsing (paths, methods, parameters, request body, responses)",
            "field type mapping (string, integer, number, boolean, array, object, reference)",
            "validation constraints (minLength, maxLength, pattern, enum, min, max)",
            "Pydantic model generation",
            "FastAPI route generation",
            "TypeScript interface generation",
            "AsyncAPI channel parsing",
            "Inheritance (allOf) support",
        ],
    }


@router.post("/validate")
async def validate_spec(
    request: CompileSpecRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Validate a spec without generating code."""
    from app.services.spec_compiler import SpecCompiler
    compiler = SpecCompiler()
    try:
        result = compiler.compile(request.spec, request.spec_format)
        return {
            "valid": True,
            "stats": result["stats"],
            "models": len(result["models"]),
            "endpoints": len(result["endpoints"]),
        }
    except Exception as e:
        return {"valid": False, "error": str(e)}
