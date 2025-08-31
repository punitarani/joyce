"""
Tag model for reusable categorization of memories.

Tags provide a flexible way to categorize and organize memories
with support for hierarchical naming and synonym management.
"""

from __future__ import annotations

from sqlalchemy import JSON, TIMESTAMP, Column, String, func

from .base import Base


class Tag(Base):
    """Reusable tags for categorizing memories."""

    __tablename__ = "tags"

    tag_id = Column(String, primary_key=True)  # e.g., "pref:coffee", "fact:work"
    name = Column(String, nullable=False)
    category = Column(String, nullable=True)
    synonyms = Column(JSON, default=list)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
