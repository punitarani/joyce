"""
Core onboarding functions for Joyce - handles evaluation criteria and logic.

This module provides reusable functions for onboarding evaluation that can be
used by both OnboardingAgent and function tools to ensure consistency.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict

from livekit.agents.llm import ChatContext
from livekit.plugins import openai
from sqlalchemy import select, update

from joyce.db.client import SessionMaker
from joyce.db.schema import UserProfile
from joyce.services.user.user_entities import list_entities
from joyce.types import OnboardingStatus

logger = logging.getLogger(__name__)

# Core onboarding evaluation criteria and prompts
ONBOARDING_EVALUATION_CRITERIA = {
    "required_collections": [
        "identity",
        "social",
        "professional",
        "health",
        "lifestyle",
        "pursuits",
        "resources",
        "milestones",
        "misc",
    ],
    "minimum_requirements": {
        "identity_present": True,
        "context_signals": 1,  # At least one meaningful context signal
    },
}

ONBOARDING_EVALUATION_PROMPT = """
You are a careful, privacy-aware judge for onboarding completeness for an AI wellness assistant (Joyce).

Goal: Decide if we have enough high-level, non-sensitive information to start personalized but safe support.

Mark ready only if:
- Identity present (first_name or preferred_name)
- AND at least one meaningful context signal (goals, preferences, relationships, location, or a misc note)

Never require sensitive data (SSN, precise address, detailed medical history).
Be generous: good enough is OK if identity + one context item exist.

Respond with strict JSON only: {
  "is_ready": boolean,
  "confidence": number,
  "missing_critical": string[],
  "recommendations": string[],
  "reasoning": string
}
""".strip()


async def collect_user_onboarding_data(user_id: str) -> Dict[str, Any]:
    """
    Collect comprehensive user data for onboarding evaluation.

    Args:
        user_id: User UUID

    Returns:
        Dictionary containing profile and entity data structured for evaluation
    """
    try:
        # Get user profile
        async with SessionMaker() as session:
            profile_result = await session.execute(
                select(UserProfile).filter(UserProfile.user_id == user_id)
            )
            profile = profile_result.scalars().first()

        # Collect entities across all collections
        entity_data = {}
        for collection in ONBOARDING_EVALUATION_CRITERIA["required_collections"]:
            entities = await list_entities(
                user_id=user_id,
                collection=collection,
                include_archived=False,
                limit=50,
            )
            entity_data[collection] = [
                {
                    "id": e.id,
                    "type": e.type,
                    "slug": e.slug,
                    "data": e.data,
                    "created_at": e.created_at.isoformat() if e.created_at else None,
                }
                for e in entities
            ]

        # Structure profile data
        return {
            "basic_info": {
                "first_name": getattr(profile, "first_name", None),
                "last_name": getattr(profile, "last_name", None),
                "preferred_name": getattr(profile, "preferred_name", None),
                "display_name": getattr(profile, "display_name", None),
                "email": getattr(profile, "email", None),
                "phone": getattr(profile, "phone", None),
                "bio": getattr(profile, "bio", None),
            },
            "location": getattr(profile, "location", None) or {},
            "entities": entity_data,
        }

    except Exception as e:
        logger.error("Error collecting onboarding data for user %s: %s", user_id, e)
        return {
            "basic_info": {},
            "location": {},
            "entities": {
                collection: []
                for collection in ONBOARDING_EVALUATION_CRITERIA["required_collections"]
            },
            "error": str(e),
        }


async def evaluate_onboarding_readiness(
    user_id: str, profile_data: Dict[str, Any] | None = None
) -> Dict[str, Any]:
    """
    Evaluate if user's onboarding is complete enough to proceed.

    Args:
        user_id: User UUID
        profile_data: Optional pre-collected profile data (if None, will collect)

    Returns:
        Dictionary with evaluation results including is_ready, confidence, recommendations
    """
    try:
        # Collect data if not provided
        if profile_data is None:
            profile_data = await collect_user_onboarding_data(user_id)

        # Call LLM for evaluation
        llm = openai.LLM(
            model="gpt-4.1", parallel_tool_calls=True, _strict_tool_schema=True
        )
        chat_ctx = ChatContext()
        chat_ctx.add_message(role="system", content=ONBOARDING_EVALUATION_PROMPT)
        chat_ctx.add_message(role="user", content=json.dumps(profile_data))

        response = ""
        async with llm.chat(chat_ctx=chat_ctx) as stream:
            async for chunk in stream:
                if chunk.delta and chunk.delta.content:
                    response += chunk.delta.content

        try:
            assessment = json.loads(response.strip())
        except Exception:
            # Conservative fallback if LLM response can't be parsed
            return {
                "is_ready": False,
                "confidence": 0.0,
                "missing_critical": ["llm_response_unparseable"],
                "recommendations": [
                    "Confirm your preferred or first name",
                    "Share one high-level goal or preference",
                ],
                "reasoning": "Could not parse judge response; defaulting to safe not-ready.",
            }

        # Apply guardrails and normalization
        return normalize_onboarding_assessment(assessment, profile_data)

    except Exception as e:
        logger.error(
            "Error evaluating onboarding readiness for user %s: %s", user_id, e
        )
        return {
            "is_ready": False,
            "confidence": 0.0,
            "missing_critical": ["evaluation_error"],
            "recommendations": ["Try again shortly"],
            "reasoning": f"Evaluation error: {e}",
        }


def normalize_onboarding_assessment(
    assessment: Dict[str, Any], profile_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Apply guardrails and normalize assessment results.

    Args:
        assessment: Raw LLM assessment results
        profile_data: User profile data used for evaluation

    Returns:
        Normalized and validated assessment
    """
    # Check minimum requirements
    is_identity_present = bool(
        profile_data.get("basic_info", {}).get("first_name")
        or profile_data.get("basic_info", {}).get("preferred_name")
    )

    entity_data = profile_data.get("entities", {})
    has_any_context = any(len(entity_data.get(c, [])) > 0 for c in entity_data)

    # Override to not ready if minimum requirements not met
    if not is_identity_present or not has_any_context:
        assessment["is_ready"] = False
        assessment["confidence"] = min(float(assessment.get("confidence", 0.0)), 0.4)

        missing = []
        if not is_identity_present:
            missing.append("identity_name")
        if not has_any_context:
            missing.append("any_context_entity")

        assessment.setdefault("missing_critical", [])
        assessment["missing_critical"] = list(
            {*assessment["missing_critical"], *missing}
        )

    # Bound confidence to valid range
    try:
        assessment["confidence"] = max(
            0.0, min(1.0, float(assessment.get("confidence", 0.0)))
        )
    except (ValueError, TypeError):
        assessment["confidence"] = 0.0

    # Ensure required keys exist with defaults
    assessment.setdefault("is_ready", False)
    assessment.setdefault("missing_critical", [])
    assessment.setdefault("recommendations", [])
    assessment.setdefault("reasoning", "")

    return assessment


async def mark_user_onboarding_complete(user_id: str) -> bool:
    """
    Mark user's onboarding as completed in the database.

    Args:
        user_id: User UUID

    Returns:
        True if successful, False otherwise
    """
    try:
        async with SessionMaker() as session:
            await session.execute(
                update(UserProfile)
                .where(UserProfile.user_id == user_id)
                .values(status=OnboardingStatus.COMPLETED.value)
            )
            await session.commit()

        logger.info("Marked onboarding complete for user %s", user_id)
        return True

    except Exception as e:
        logger.error("Error marking onboarding complete for user %s: %s", user_id, e)
        return False


def get_onboarding_evaluation_criteria() -> Dict[str, Any]:
    """
    Get the standardized onboarding evaluation criteria.

    Returns:
        Dictionary containing evaluation criteria and requirements
    """
    return ONBOARDING_EVALUATION_CRITERIA.copy()


def get_onboarding_evaluation_prompt() -> str:
    """
    Get the standardized LLM prompt for onboarding evaluation.

    Returns:
        Prompt string for LLM evaluation
    """
    return ONBOARDING_EVALUATION_PROMPT
