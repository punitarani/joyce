"""
MemoryChunk model for storing text chunks with embedding metadata.

Memory chunks represent smaller pieces of text extracted from memories,
optimized for vector embedding and semantic search operations.
"""

from __future__ import annotations

import uuid

from sqlalchemy import (
    JSON,
    TIMESTAMP,
    Boolean,
    Column,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .auth import users
from .base import Base


class MemoryChunk(Base):
    """Text chunks with embedding metadata."""

    __tablename__ = "memory_chunks"

    chunk_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    memory_id = Column(
        UUID(as_uuid=True),
        ForeignKey("memories.memory_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey(users.c.id, ondelete="CASCADE"),
        nullable=False,
        index=True,
    )  # denormalized for faster queries
    chunk_text = Column(Text, nullable=False)
    chunk_metadata = Column(JSON, default=dict)
    text_length = Column(Integer)
    embedding_model = Column(String, nullable=True)
    vector_upserted = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationships
    memory = relationship("Memory", back_populates="chunks")
