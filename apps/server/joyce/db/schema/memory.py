"""
Memory model for storing core memory records with user scoping.

The Memory table serves as the primary container for user memories,
supporting different types (preferences, facts, events) with structured
metadata and flexible tagging.
"""

from __future__ import annotations

import uuid

from sqlalchemy import (
    JSON,
    TIMESTAMP,
    Boolean,
    Column,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .auth import users
from .base import Base


class Memory(Base):
    """Core memory records with user scoping."""

    __tablename__ = "memories"

    memory_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey(users.c.id, ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    type = Column(String, nullable=False)  # e.g., "preference", "fact", "event"
    title = Column(String, nullable=True)
    summary = Column(Text, nullable=True)
    payload = Column(JSON, default=dict)  # structured data
    sensitive = Column(Boolean, default=False)
    tags = Column(JSON, default=list)  # convenience list of tag IDs
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    last_updated_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    deleted = Column(Boolean, default=False)

    # Relationships
    chunks = relationship(
        "MemoryChunk", back_populates="memory", cascade="all, delete-orphan"
    )
    memory_tags = relationship(
        "MemoryTag", back_populates="memory", cascade="all, delete-orphan"
    )
