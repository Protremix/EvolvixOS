"""Vector store embedding model using pgvector for AI knowledge base."""

from typing import Optional
from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.types import GUID

try:
    from pgvector.sqlalchemy import Vector
    HAS_PGVECTOR = True
except ImportError:
    HAS_PGVECTOR = False
    Vector = None


class DocumentEmbedding(Base):
    """Document embedding for vector similarity search (AI Knowledge Base)."""
    __tablename__ = "document_embeddings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    project_id: Mapped[Optional[str]] = mapped_column(
        GUID(), ForeignKey("projects.id"), nullable=True
    )
    metadata_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    embedding: Mapped[Optional[list[float]]] = mapped_column(
        Vector(1536) if HAS_PGVECTOR else Text,
        nullable=True
    )
