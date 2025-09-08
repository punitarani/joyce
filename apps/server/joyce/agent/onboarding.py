"""
OnboardingAgent for Joyce - handles new user profile collection through natural conversation.

This agent collects essential profile information in a conversational way,
maintains progress through onboarding steps, and seamlessly transitions to
the main Joyce agent when complete.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from livekit.agents import Agent, ChatContext
from livekit.agents.llm import ChatMessage, FunctionToolCall

from joyce.agent.functions import (
    extract_and_store_entities,
    extract_and_update_user_profile,
)
from joyce.agent.functions.onboarding import (
    collect_user_onboarding_data,
    evaluate_onboarding_readiness,
)
from joyce.agent.prompts import (
    ONBOARDING_BASE_INSTRUCTIONS,
)
from joyce.agent.tools import (
    add_user_entity,
    delete_user_entity,
    get_user_entities,
    get_user_entity_by_id,
    get_user_entity_by_slug,
    get_user_profile,
    goodbye_and_end_call,
    review_and_complete_onboarding,
    search_memory,
    store_memory,
    update_user_entity,
    update_user_profile_info,
)
from joyce.db.schema.user_profile import UserProfile

from .user import UserData

logger = logging.getLogger("agent.onboarding")


class OnboardingAgent(Agent):
    """
    Specialized agent for handling user onboarding through natural conversation.

    This agent:
    - Collects essential profile information conversationally
    - Tracks progress through structured onboarding steps
    - Infers information from natural conversation with confidence scores
    - Validates and confirms collected data
    - Seamlessly hands off to Joyce agent when complete
    """

    def __init__(self, userdata: UserData):
        self.userdata = userdata

        self.user_id = userdata.user_id
        self.user_profile = userdata.user_profile
        self.onboarding_context: Optional[Dict[str, Any]] = None

        # Background entity extraction state
        self.stored_entities: list[FunctionToolCall] = []
        self._background_tasks: set = set()

        # All data collection handled by function tools - no background tasks needed

        # Initialize base agent
        super().__init__(
            instructions=self.get_instructions(userdata.user_profile),
            tools=[
                get_user_profile,
                get_user_entities,
                get_user_entity_by_id,
                get_user_entity_by_slug,
                review_and_complete_onboarding,
                update_user_entity,
                add_user_entity,
                delete_user_entity,
                search_memory,
                store_memory,
                update_user_profile_info,
                goodbye_and_end_call,
            ],
        )

    async def on_enter(self) -> None:
        """Initialize onboarding session and greet the user."""
        # Ensure session userdata is available for function tools
        # (function tools access RunContext.userdata → session.userdata)
        self.session.userdata = self.userdata

        # Load or create onboarding context
        await self._initialize_onboarding_context()

        # Update instructions for onboarding
        await self.update_instructions(
            self.get_instructions(self.userdata.user_profile)
        )

        # Greet user based on onboarding status
        if self.user_profile and self.user_profile.is_onboarding_in_progress:
            await self.session.generate_reply(
                instructions="Welcome back! Continue onboarding where we left off. "
                "Ask what information they'd like to provide next."
            )
        else:
            await self.session.generate_reply(
                instructions="Start onboarding with a warm welcome. Introduce yourself as Joyce and "
                "express excitement about getting to know them."
            )

    async def on_user_turn_completed(
        self, ctx: ChatContext, new_message: ChatMessage
    ) -> None:
        """
        Extract and store entities and user profile data in fire-and-forget pattern.

        This follows best practices by:
        1. Only handling background entity and profile storage
        2. Using fire-and-forget async task pattern
        3. Not injecting any context (tools handle retrieval on-demand)
        """
        if not new_message.text_content:
            return

        # Fire-and-forget entity storage task
        entity_task = asyncio.create_task(
            extract_and_store_entities(
                user_id=self.user_id,
                new_message=new_message,
                stored_entities=self.stored_entities,
                ctx=ctx,
            )
        )

        # Fire-and-forget user profile extraction task
        profile_task = asyncio.create_task(
            extract_and_update_user_profile(
                user_id=self.user_id,
                new_message=new_message.text_content,
                ctx=ctx,
            )
        )

        # Add to task registry with cleanup callback (prevents garbage collection)
        self._background_tasks.add(entity_task)
        self._background_tasks.add(profile_task)
        entity_task.add_done_callback(self._background_tasks.discard)
        profile_task.add_done_callback(self._background_tasks.discard)

    async def _initialize_onboarding_context(self) -> None:
        """Initialize or load onboarding context for the user."""
        # Load existing profile if available
        if not self.user_profile:
            self.user_profile = await self.userdata.get_user_profile()

        # Create simple onboarding context
        self.onboarding_context = {
            "user_id": self.user_id,
            "conversation_history": [],
            "data_collected": {},
        }

    def get_instructions(self, user_profile: UserProfile | None) -> str:
        """Get base onboarding instructions."""
        current_time = datetime.now(
            user_profile.timezone if user_profile else timezone.utc
        ).strftime("%I:%M %p")
        current_date = datetime.now(
            user_profile.timezone if user_profile else timezone.utc
        ).strftime("%B %d, %Y")

        return ONBOARDING_BASE_INSTRUCTIONS.format(time=current_time, date=current_date)

    @property
    def is_onboarding_complete(self) -> bool:
        """Check if onboarding is complete for this user."""
        return bool(self.user_profile and self.user_profile.is_onboarding_complete)

    async def get_onboarding_assessment(self) -> Dict[str, Any]:
        """Get detailed onboarding readiness assessment using shared functions."""
        return await evaluate_onboarding_readiness(self.user_id)

    async def collect_current_data(self) -> Dict[str, Any]:
        """Collect current user data using shared functions."""
        return await collect_user_onboarding_data(self.user_id)
