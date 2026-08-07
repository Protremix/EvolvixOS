"""
Secrets management API endpoints for EvolvixOS.

Provides CRUD for project/organization/global secrets with encryption at rest.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.services.config_manager import (
    ConfigManager,
    ConfigSchema,
    ConfigResponse,
    SecretSchema,
    SecretResponse,
)

router = APIRouter(prefix="/config", tags=["configuration"])

# Singleton config manager (initialized on first use)
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """Get or create the config manager singleton."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


@router.get("/", response_model=List[ConfigResponse])
async def list_config(
    scope: str = "global",
    scope_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all configuration entries for a scope."""
    manager = get_config_manager()
    entries = await manager.list_config(db, scope=scope, scope_id=scope_id)
    return [
        ConfigResponse(
            id=e.id,
            scope=e.scope,
            scope_id=e.scope_id,
            key=e.key,
            value="[REDACTED]" if e.is_secret else e.value,
            is_secret=e.is_secret,
            description=e.description,
            updated_at=e.updated_at,
        )
        for e in entries
    ]


@router.get("/{key}", response_model=ConfigResponse)
async def get_config(
    key: str,
    scope: str = "global",
    scope_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get a specific configuration value."""
    manager = get_config_manager()
    value = await manager.get_config(db, key=key, scope=scope, scope_id=scope_id)
    if value is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuration key '{key}' not found",
        )
    return ConfigResponse(
        id="",
        scope=scope,
        scope_id=scope_id,
        key=key,
        value=value,
        is_secret=False,
        description=None,
        updated_at=None,
    )


@router.post("/", response_model=ConfigResponse, status_code=status.HTTP_201_CREATED)
async def set_config(
    config: ConfigSchema,
    scope: str = "global",
    scope_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create or update a configuration value."""
    manager = get_config_manager()
    entry = await manager.set_config(
        db,
        key=config.key,
        value=config.value,
        scope=scope,
        scope_id=scope_id,
        is_secret=config.is_secret,
        description=config.description,
    )
    return ConfigResponse(
        id=entry.id,
        scope=entry.scope,
        scope_id=entry.scope_id,
        key=entry.key,
        value="[REDACTED]" if entry.is_secret else entry.value,
        is_secret=entry.is_secret,
        description=entry.description,
        updated_at=entry.updated_at,
    )


@router.post("/secrets", response_model=SecretResponse, status_code=status.HTTP_201_CREATED)
async def set_secret(
    secret: SecretSchema,
    scope: str = "global",
    scope_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create or update a secret (encrypted at rest, never returned in plaintext)."""
    manager = get_config_manager()
    entry = await manager.set_config(
        db,
        key=secret.name,
        value=secret.value,
        scope=scope,
        scope_id=scope_id,
        is_secret=True,
        description="Encrypted secret",
    )
    return SecretResponse(
        id=entry.id,
        scope=entry.scope,
        scope_id=entry.scope_id,
        name=entry.key,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
    )


@router.delete("/{key}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_config(
    key: str,
    scope: str = "global",
    scope_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a configuration value or secret."""
    manager = get_config_manager()
    deleted = await manager.delete_config(db, key=key, scope=scope, scope_id=scope_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuration key '{key}' not found",
        )
    return None
