"""
Simplified models for function tool parameters and responses.

- Request models inherit from `AgentTool` and only declare fields
- Common schema export is handled by `AgentTool.raw_schema`
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel

from joyce.types.agent_tool import AgentTool


class ProfileUpdateRequest(AgentTool):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    preferred_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    gender: Optional[str] = None
    birth_date: Optional[str] = None
    bio: Optional[str] = None
    step_completed: Optional[str] = None


class ContactValidationRequest(AgentTool):
    email: Optional[str] = None
    phone: Optional[str] = None


class GetUserProfileRequest(AgentTool):
    include_location: bool = True
    include_contact: bool = True
    include_attributes: bool = True


class FlexibleInfoRequest(AgentTool):
    entity_type: str
    category: Optional[str] = None
    data: Optional[str] = None
    tags: Optional[list[str]] = None


class MemorySearchRequest(AgentTool):
    query: str
    limit: int = 5
    memory_type: Optional[str] = None


class ContextRequest(AgentTool):
    object_type: str
    value: str
    collection: str = "misc"


class ContextUpdateRequest(AgentTool):
    object_id: str
    new_value: str
    new_type: Optional[str] = None


class ContextRemoveRequest(AgentTool):
    object_id: str
    reason: Optional[str] = None


class ContextSearchRequest(AgentTool):
    query: Optional[str] = None
    object_type: Optional[str] = None
    collection: Optional[str] = None


class ProfileContextRequest(AgentTool):
    profile_context_json: str
    operation_description: Optional[str] = None


class ReadinessFactors(BaseModel):
    identity_clarity: float
    personal_context: float
    communication_readiness: float
    wellness_context: float


class CompletenessAssessmentResponse(BaseModel):
    is_ready: bool
    confidence: float
    missing_critical: list[str]
    recommendations: list[str]
    reasoning: str
    profile_strength_score: float
    readiness_factors: ReadinessFactors


class ProfileAssessmentRequest(AgentTool):
    confidence_threshold: float = 0.7
    include_detailed_breakdown: bool = True


# === User Entity Models ===


class CreateEntityRequest(AgentTool):
    entity_type: str
    collection: str = "misc"
    data: Dict[str, Any]
    slug: str = ""
    allow_upsert: bool = False


class GetEntityRequest(AgentTool):
    entity_id: str = ""
    slug: str = ""
    include_archived: bool = False


class ListEntitiesRequest(AgentTool):
    entity_type: str = ""
    collection: str = ""
    include_archived: bool = False
    limit: int = 50
    offset: int = 0


class UpdateEntityRequest(AgentTool):
    entity_id: str
    patch: Dict[str, Any]
    update_metadata: bool = True


class ArchiveEntityRequest(AgentTool):
    entity_id: str
    reason: str = ""


class SearchEntitiesRequest(AgentTool):
    entity_type: str = ""
    collection: str = ""
    query: str = ""
    include_archived: bool = False
    limit: int = 20
