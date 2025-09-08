from __future__ import annotations

import asyncio
from datetime import datetime

from livekit.agents import Agent, ChatContext
from livekit.agents.llm import ChatMessage, FunctionToolCall
from zoneinfo import ZoneInfo

from joyce.agent.prompts import JOYCE_BASE_INSTRUCTIONS, USER_INSTRUCTIONS
from joyce.db.schema.user_profile import UserProfile

from .functions import extract_and_store_entities
from .onboarding import OnboardingAgent
from .tools import (
    add_user_entity,
    delete_user_entity,
    get_user_entities,
    get_user_profile,
    goodbye_and_end_call,
    search_memory,
    store_memory,
    update_user_entity,
)
from .user import UserData


class JoyceAgent(Agent):
    def __init__(self, userdata: UserData):
        self.userdata = userdata

        self.stored_entities: list[FunctionToolCall] = []

        # Task registry for fire-and-forget background tasks
        self._background_tasks: set = set()

        super().__init__(
            instructions=self.get_instructions(user_profile=userdata.user_profile),
            tools=[
                get_user_profile,
                get_user_entities,
                update_user_entity,
                goodbye_and_end_call,
                search_memory,
                store_memory,
                add_user_entity,
                delete_user_entity,
            ],
        )

    async def on_enter(self):
        # Ensure session userdata is available for function tools
        self.session.userdata = self.userdata

        user_profile = await self.userdata.get_user_profile()
        if user_profile and not user_profile.is_onboarding_complete:
            return "Let's finish onboarding!", OnboardingAgent(userdata=self.userdata)

        await self.session.generate_reply(
            instructions="Greet the user like a friend and ask how they are doing."
        )
        return None

    async def on_user_turn_completed(
        self, ctx: ChatContext, new_message: ChatMessage
    ) -> None:
        """
        Extract and store memories in fire-and-forget pattern.

        This follows best practices by:
        1. Only handling background memory storage
        2. Using fire-and-forget async task pattern
        3. Not injecting any context (tools handle retrieval on-demand)
        """
        if not new_message.text_content:
            return

        # Fire-and-forget memory storage task
        task = asyncio.create_task(
            extract_and_store_entities(
                user_id=self.userdata.user_id,
                new_message=new_message,
                stored_entities=self.stored_entities,
                ctx=ctx,
            )
        )

        # Add to task registry with cleanup callback (prevents garbage collection)
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)

    def get_instructions(self, user_profile: UserProfile | None) -> str:
        parts = [JOYCE_BASE_INSTRUCTIONS]

        user_timezone = ZoneInfo("US/Pacific")
        if user_profile is not None:
            user_timezone = user_profile.location.get("timezone")
            user_timezone = ZoneInfo(user_timezone)

            user_prompt = USER_INSTRUCTIONS.format(
                user_home=user_profile.location.get("home"),
                user_current=user_profile.location.get("current"),
                user_timezone=user_profile.location.get("timezone"),
                user_bio=user_profile.bio or "",
                user_context=user_profile.attributes.get("context", "") or "",
                user_attributes="",  # Removed attributes column
            )
            parts.append(user_prompt)

        return "\n\n".join(parts).format(
            time=datetime.now(user_timezone).strftime("%H:%M"),
            date=datetime.now(user_timezone).strftime("%Y-%m-%d"),
        )
