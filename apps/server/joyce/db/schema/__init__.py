"""
Joyce Database Schema Module

Contains all SQLAlchemy models organized by table, each in its own file.
All models inherit from the shared Base class for consistent metadata handling.
"""

from __future__ import annotations

from .base import Base
from .memory import Memory
from .user_entities import UserEntity
from .user_profile import UserProfile

__all__ = [
    "Base",
    "Memory",
    "UserEntity",
    "UserProfile",
]
