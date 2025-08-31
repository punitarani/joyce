"""
MemoryTag model for many-to-many relationships between memories and tags.

Junction table that enables flexible tagging of memories with support
for relevance scoring and tracking the source of tag assignments.
"""

from __future__ import annotations

from sqlalchemy import (
    TIMESTAMP,
    Column,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base


class MemoryTag(Base):
    """Junction table for memory-tag relationships."""

    __tablename__ = "memory_tags"

    memory_id = Column(
        UUID(as_uuid=True),
        ForeignKey("memories.memory_id", ondelete="CASCADE"),
        primary_key=True,
    )
    tag_id = Column(
        String, ForeignKey("tags.tag_id", ondelete="CASCADE"), primary_key=True
    )
    score = Column(Integer, default=1)  # relevance score
    source = Column(String, default="auto")  # "auto", "manual", "ai"
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationships
    memory = relationship("Memory", back_populates="memory_tags")
    tag = relationship("Tag")
