"""
User Entities table for flexible, structured user context storage.

This table stores semi-permanent user information like relationships, goals,
health conditions, and preferences as individual entities rather than a single
large JSONB blob. Each entity has a human-readable slug for LLM-friendly access.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import sqlalchemy as sa
from sqlalchemy import Column, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB, TEXT, TIMESTAMP, UUID

from .auth import users
from .base import Base


class UserEntity(Base):
    """
    Individual user entity with flexible JSONB data storage.

    Stores semi-permanent user information (relationships, goals, health, preferences)
    as individual rows with human-readable slugs and flexible JSONB bodies.
    """

    __tablename__ = "user_entities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey(users.c.id, ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Human-readable identifier unique per user (e.g., "dave/father.john", "dave/goal.marathon2025")
    slug = Column(TEXT, nullable=False, index=True)

    # Collection/category for organization (relationships, goals, health, metrics, events, favorites, preferences, misc)
    collection = Column(TEXT, nullable=False, default="misc", index=True)

    # Entity type for categorization (e.g., "father", "weight_loss_goal", "preferred_food")
    type = Column(TEXT, nullable=False, index=True)

    data = Column(JSONB, nullable=False, default=dict)

    created_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    archived_at = Column(TIMESTAMP(timezone=True), nullable=True)

    # Unique constraint and indexes
    __table_args__ = (
        # Unique slug per user
        sa.UniqueConstraint("user_id", "slug", name="uq_user_entities_user_slug"),
        # Composite indexes for common queries
        sa.Index(
            "ix_user_entities_user_type_archived", "user_id", "type", "archived_at"
        ),
        sa.Index(
            "ix_user_entities_user_collection_archived",
            "user_id",
            "collection",
            "archived_at",
        ),
        # GIN index for JSONB data searches
        sa.Index(
            "ix_user_entities_data_gin",
            "data",
            postgresql_using="gin",
            postgresql_ops={"data": "jsonb_path_ops"},
        ),
    )

    def serialize(self) -> dict:
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "slug": self.slug,
            "collection": self.collection,
            "type": self.type,
            "data": self.data,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "archived_at": self.archived_at.isoformat() if self.archived_at else None,
        }

    @property
    def is_archived(self) -> bool:
        """Check if entity is archived (soft deleted)."""
        return self.archived_at is not None

    @property
    def age_days(self) -> int:
        """Get age of entity in days."""
        if not self.created_at:
            return 0
        return (datetime.now(timezone.utc) - self.created_at.replace(tzinfo=None)).days

    def get_data_value(self, key: str, default=None):
        """Get a value from the JSONB data."""
        if not self.data or not isinstance(self.data, dict):
            return default
        return self.data.get(key, default)

    def set_data_value(self, key: str, value):
        """Set a value in the JSONB data."""
        if self.data is None or not isinstance(self.data, dict):
            self.data = {}
        self.data[key] = value

    def get_meta(self) -> dict:
        """Get metadata from data.meta field."""
        return self.get_data_value("meta", {})

    def set_meta(self, meta: dict):
        """Set metadata in data.meta field."""
        self.set_data_value("meta", meta)

    def add_provenance(self, source: str, confidence: float = 1.0):
        """Add provenance information to entity metadata."""
        meta = self.get_meta()
        meta.update(
            {
                "source": source,
                "confidence": confidence,
                "last_updated": datetime.now(timezone.utc).isoformat(),
            }
        )
        self.set_meta(meta)
