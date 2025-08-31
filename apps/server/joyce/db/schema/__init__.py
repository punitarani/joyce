"""
Joyce Database Schema Module

Contains all SQLAlchemy models organized by table, each in its own file.
All models inherit from the shared Base class for consistent metadata handling.
"""

from __future__ import annotations

from .base import Base
from .memory import Memory
from .memory_chunk import MemoryChunk
from .memory_tag import MemoryTag
from .tag import Tag
from .user_profile import UserProfile

__all__ = [
    "Base",
    "Memory",
    "MemoryChunk",
    "MemoryTag",
    "Tag",
    "UserProfile",
]
