"""
UserProfile model with dynamic JSONB context storage.

Stores user profile information including a first-person bio,
structured attributes, and dynamic context that changes over time
with automatic timestamp tracking.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import JSON, TIMESTAMP, Column, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID

from .auth import users
from .base import Base


class UserProfile(Base):
    """User profile with dynamic JSONB context storage."""

    __tablename__ = "user_profiles"

    profile_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey(users.c.id, ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    first_person_bio = Column(Text, nullable=False)  # "I am a software engineer..."
    attributes = Column(JSON, default=dict)  # communication_style, pronouns, etc.
    context = Column(JSON, default=dict)  # dynamic context with timestamps
    version = Column(String, default="1")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    last_updated_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    @classmethod
    def validate_bio(cls, bio: str) -> str:
        """Validate that bio starts with 'I ' for first-person context."""
        if not bio.strip().startswith("I "):
            raise ValueError("first_person_bio must start with 'I '")
        return bio.strip()

    @classmethod
    def create_context_entry(cls, value: str, timestamp: Optional[str] = None) -> dict:
        """Helper to create context entries with timestamps."""
        if timestamp is None:
            timestamp = datetime.now(timezone.utc).isoformat()

        return {"value": value, "ts": timestamp}

    @classmethod
    def update_context_key(cls, context: dict, key: str, value: str) -> dict:
        """Helper to update a single context key with timestamp."""
        context = context.copy() if context else {}
        context[key] = cls.create_context_entry(value)
        return context
