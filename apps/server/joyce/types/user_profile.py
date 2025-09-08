from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class OnboardingStatus(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class UserLocation(BaseModel):
    home: str | None = None
    current: str | None = None
    timezone: str | None = None
