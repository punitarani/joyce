"""
UserProfile model for core user information.

Stores essential user profile information with structured attributes.
Semi-permanent contextual data (relationships, goals, health, preferences)
is now stored in the user_entities table for better performance and flexibility.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, ForeignKey, func
from sqlalchemy.dialects.postgresql import (
    DATE,
    JSONB,
    TEXT,
    TIMESTAMP,
    UUID,
)
from zoneinfo import ZoneInfo

from joyce.types import OnboardingStatus

from .auth import users
from .base import Base


class UserProfile(Base):
    """Core user profile information without contextual data."""

    __tablename__ = "user_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey(users.c.id, ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    first_name = Column(TEXT, nullable=True)
    last_name = Column(TEXT, nullable=True)
    preferred_name = Column(TEXT, nullable=True)
    email = Column(TEXT, nullable=True)
    phone = Column(TEXT, nullable=True)
    gender = Column(TEXT, nullable=True)
    birth_date = Column(DATE, nullable=True)
    bio = Column(TEXT, nullable=True)
    location = Column(JSONB, default=dict)
    attributes = Column(JSONB, default=dict)
    status = Column(TEXT, default=OnboardingStatus.NOT_STARTED.value)
    version = Column(TEXT, default="1")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    last_updated_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def serialize(self) -> dict:
        birth_date_iso = self.birth_date.isoformat() if self.birth_date else None
        created_at_iso = self.created_at.isoformat() if self.created_at else None
        last_updated_at_iso = (
            self.last_updated_at.isoformat() if self.last_updated_at else None
        )

        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "first_name": self.first_name,
            "last_name": self.last_name,
            "preferred_name": self.preferred_name,
            "email": self.email,
            "phone": self.phone,
            "gender": self.gender,
            "birth_date": birth_date_iso,
            "bio": self.bio,
            "location": self.location,
            "attributes": self.attributes,
            "status": self.status,
            "version": self.version,
            "created_at": created_at_iso,
            "last_updated_at": last_updated_at_iso,
        }

    @property
    def timezone(self) -> ZoneInfo:
        if self.location and isinstance(self.location, dict):
            user_timezone = self.location.get("timezone")
            if user_timezone:
                return ZoneInfo(user_timezone)
        return ZoneInfo("UTC")

    @property
    def full_name(self) -> str:
        first = self.first_name or ""
        last = self.last_name or ""
        return f"{first} {last}".strip() or "Unknown User"

    @property
    def age(self) -> Optional[int]:
        if not self.birth_date:
            return None
        today = datetime.now(self.timezone).date()
        age = today.year - self.birth_date.year
        if today < self.birth_date.replace(year=today.year):
            age -= 1
        return max(0, age)

    @property
    def display_name(self) -> str:
        if self.preferred_name:
            return self.preferred_name
        if self.first_name:
            return self.first_name
        return "User"

    @property
    def is_onboarding_complete(self) -> bool:
        return self.status == OnboardingStatus.COMPLETED.value

    @property
    def is_onboarding_in_progress(self) -> bool:
        return self.status == OnboardingStatus.IN_PROGRESS.value

    @property
    def required_fields_complete(self) -> bool:
        required_fields = [self.first_name, self.last_name, self.email, self.phone]
        return all(field is not None and field != "" for field in required_fields)
