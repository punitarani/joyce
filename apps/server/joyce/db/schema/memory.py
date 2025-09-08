"""
Memory model for storing core memory records with user scoping.

The Memory table serves as the primary container for user memories,
supporting different types (preferences, facts, events) with structured
data and flexible tagging.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field
from sqlalchemy import (
    Column,
    ForeignKey,
    func,
)
from sqlalchemy.dialects.postgresql import (
    ARRAY,
    BOOLEAN,
    FLOAT,
    JSONB,
    TEXT,
    TIMESTAMP,
    UUID,
)

from joyce.types import MemoryTag, MemoryType

from .auth import users
from .base import Base


class Memory(Base):
    """Core memory records with user scoping."""

    __tablename__ = "memories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey(users.c.id, ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    type = Column(TEXT, nullable=False)
    text = Column(TEXT, nullable=False)
    data = Column(JSONB, default=dict, nullable=False)
    tags = Column(ARRAY(TEXT), default=list, nullable=False)
    embedding = Column(ARRAY(FLOAT), nullable=True)
    deleted = Column(BOOLEAN, default=False, nullable=False)
    created_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )


class BaseMemoryCreate(BaseModel):
    """
    Base model for creating a memory.

    All the fields are required.
    Type, text, data, and tags are required.

    Type is a MemoryType enum and text is a string.
    Data is a dictionary of the relevant structured data.
    Tags is a list of MemoryTag enums.
    """

    type: MemoryType
    text: str
    data: Dict[str, Any] = Field(
        default_factory=dict,
        json_schema_extra={
            "type": "object",
            "additionalProperties": False,
            "properties": {},
        },
    )
    tags: list[MemoryTag]


class MemoryCreate(BaseMemoryCreate):
    user_id: str
    deleted: bool = False
    created_at: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @classmethod
    def from_tool_call_arguments(cls, user_id: str, arguments: str) -> MemoryCreate:
        parsed_args = json.loads(arguments)
        memory = parsed_args.get("memory", parsed_args)

        memory_type = memory.get("type")
        text = memory.get("text")
        data = memory.get("data") or {}
        tags = memory.get("tags") or []

        # Convert string type to MemoryType enum if needed
        if isinstance(memory_type, str):
            memory_type = MemoryType(memory_type)

        # Convert string tags to MemoryTag enums
        tags = [MemoryTag(tag) if isinstance(tag, str) else tag for tag in tags]

        return cls(user_id=user_id, type=memory_type, text=text, data=data, tags=tags)


class MemoryWithEmbeddingCreate(MemoryCreate):
    embedding: list[float]

    def serialize(self) -> dict:
        return {
            "user_id": self.user_id,
            "type": self.type.value,
            "text": self.text,
            "data": self.data,
            "tags": [tag.value for tag in self.tags or []],
            "embedding": self.embedding,
            "deleted": self.deleted,
            "created_at": self.created_at,
        }
