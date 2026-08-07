"""
Configuration and Secrets Management for EvolvixOS.

Provides secure configuration management with:
- Environment-based configuration (dev/staging/prod)
- Secrets encryption at rest using Fernet
- Project-level configuration storage
- API key management
"""

import json
import os
from datetime import datetime, datetime, UTC
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
from sqlalchemy import Column, String, Text, DateTime, Boolean, JSON
from sqlalchemy.orm import Session

from app.models.base import Base


class ConfigEntry(Base):
    """Configuration key-value store for projects and organizations."""
    __tablename__ = "config_entries"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    scope = Column(String(50), nullable=False, index=True)  # 'global', 'org', 'project'
    scope_id = Column(String(36), nullable=True, index=True)  # org_id or project_id
    key = Column(String(255), nullable=False, index=True)
    value = Column(JSON, nullable=True)
    is_secret = Column(Boolean, default=False, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))


class SecretStore(Base):
    """Encrypted secret storage."""
    __tablename__ = "secrets"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    scope = Column(String(50), nullable=False, index=True)  # 'global', 'org', 'project'
    scope_id = Column(String(36), nullable=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    encrypted_value = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))


class ConfigSchema(BaseModel):
    """Pydantic schema for configuration API."""
    key: str = Field(..., max_length=255)
    value: Any
    is_secret: bool = False
    description: Optional[str] = None


class SecretSchema(BaseModel):
    """Pydantic schema for secrets API."""
    name: str = Field(..., max_length=255)
    value: str  # Plaintext on input, encrypted at rest


class ConfigResponse(BaseModel):
    """Response schema for configuration."""
    id: str
    scope: str
    scope_id: Optional[str]
    key: str
    value: Any
    is_secret: bool
    description: Optional[str]
    updated_at: datetime


class SecretResponse(BaseModel):
    """Response schema for secrets (never returns the actual value)."""
    id: str
    scope: str
    scope_id: Optional[str]
    name: str
    created_at: datetime
    updated_at: datetime


class ConfigManager:
    """
    Configuration and secrets manager.
    Handles encrypted storage of secrets and plain config values.
    """

    def __init__(self, encryption_key: Optional[str] = None):
        """
        Initialize the config manager.

        Args:
            encryption_key: Fernet-compatible encryption key. If not provided,
                           reads from ENCRYPTION_KEY env var or generates one.
        """
        from cryptography.fernet import Fernet

        key = encryption_key or os.environ.get("ENCRYPTION_KEY")
        if key:
            self._fernet = Fernet(key.encode() if isinstance(key, str) else key)
        else:
            # Dev mode: generate ephemeral key (NOT for production)
            self._fernet = Fernet(Fernet.generate_key())

    def encrypt(self, plaintext: str) -> str:
        """Encrypt a plaintext string."""
        return self._fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt a ciphertext string."""
        return self._fernet.decrypt(ciphertext.encode()).decode()

    async def get_config(
        self,
        db: Session,
        key: str,
        scope: str = "global",
        scope_id: Optional[str] = None,
    ) -> Optional[Any]:
        """
        Get a configuration value.

        Args:
            db: Database session
            key: Configuration key
            scope: 'global', 'org', or 'project'
            scope_id: org_id or project_id (None for global)

        Returns:
            Configuration value, or None if not found.
        """
        entry = db.query(ConfigEntry).filter(
            ConfigEntry.scope == scope,
            ConfigEntry.scope_id == scope_id if scope_id else ConfigEntry.scope_id.is_(None),
            ConfigEntry.key == key,
        ).first()

        if not entry:
            return None

        if entry.is_secret:
            # Decrypt secret value
            secret = db.query(SecretStore).filter(
                SecretStore.scope == scope,
                SecretStore.scope_id == scope_id if scope_id else SecretStore.scope_id.is_(None),
                SecretStore.name == key,
            ).first()
            if secret:
                return self.decrypt(secret.encrypted_value)

        return entry.value

    async def set_config(
        self,
        db: Session,
        key: str,
        value: Any,
        scope: str = "global",
        scope_id: Optional[str] = None,
        is_secret: bool = False,
        description: Optional[str] = None,
    ) -> ConfigEntry:
        """
        Set a configuration value.

        Args:
            db: Database session
            key: Configuration key
            value: Configuration value
            scope: 'global', 'org', or 'project'
            scope_id: org_id or project_id
            is_secret: Whether this is a secret (encrypted at rest)
            description: Optional description

        Returns:
            The created/updated ConfigEntry.
        """
        # Check if entry exists
        entry = db.query(ConfigEntry).filter(
            ConfigEntry.scope == scope,
            ConfigEntry.scope_id == scope_id if scope_id else ConfigEntry.scope_id.is_(None),
            ConfigEntry.key == key,
        ).first()

        if entry:
            # Update existing
            entry.value = value
            entry.is_secret = is_secret
            entry.description = description
            entry.updated_at = datetime.now(UTC)
        else:
            # Create new
            entry = ConfigEntry(
                scope=scope,
                scope_id=scope_id,
                key=key,
                value=value,
                is_secret=is_secret,
                description=description,
            )
            db.add(entry)

        # If secret, also store encrypted version
        if is_secret and isinstance(value, str):
            secret = db.query(SecretStore).filter(
                SecretStore.scope == scope,
                SecretStore.scope_id == scope_id if scope_id else SecretStore.scope_id.is_(None),
                SecretStore.name == key,
            ).first()

            if secret:
                secret.encrypted_value = self.encrypt(value)
                secret.updated_at = datetime.now(UTC)
            else:
                secret = SecretStore(
                    scope=scope,
                    scope_id=scope_id,
                    name=key,
                    encrypted_value=self.encrypt(value),
                )
                db.add(secret)

        db.commit()
        db.refresh(entry)
        return entry

    async def delete_config(
        self,
        db: Session,
        key: str,
        scope: str = "global",
        scope_id: Optional[str] = None,
    ) -> bool:
        """
        Delete a configuration value.

        Returns:
            True if deleted, False if not found.
        """
        entry = db.query(ConfigEntry).filter(
            ConfigEntry.scope == scope,
            ConfigEntry.scope_id == scope_id if scope_id else ConfigEntry.scope_id.is_(None),
            ConfigEntry.key == key,
        ).first()

        if not entry:
            return False

        # Also delete secret if exists
        secret = db.query(SecretStore).filter(
            SecretStore.scope == scope,
            SecretStore.scope_id == scope_id if scope_id else SecretStore.scope_id.is_(None),
            SecretStore.name == key,
        ).first()

        if secret:
            db.delete(secret)

        db.delete(entry)
        db.commit()
        return True

    async def list_config(
        self,
        db: Session,
        scope: str = "global",
        scope_id: Optional[str] = None,
    ) -> list[ConfigEntry]:
        """
        List all configuration entries for a scope.

        Returns:
            List of ConfigEntry objects.
        """
        query = db.query(ConfigEntry).filter(ConfigEntry.scope == scope)

        if scope_id:
            query = query.filter(ConfigEntry.scope_id == scope_id)
        else:
            query = query.filter(ConfigEntry.scope_id.is_(None))

        return query.all()
