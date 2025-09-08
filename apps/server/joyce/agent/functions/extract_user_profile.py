"""
Functions for extracting and updating user profile information from conversation.

This module provides LLM-based extraction of core user profile fields
(first_name, last_name, birth_date, email, preferred_name, gender, location, bio)
from natural conversation during onboarding.
"""

from __future__ import annotations

import json
from datetime import datetime

from livekit.agents import ChatContext, function_tool
from livekit.agents.llm import FunctionToolCall
from livekit.plugins import openai

from joyce.agent.user import get_user_profile
from joyce.db.schema.user_profile import UserProfile
from joyce.services.user import update_user_profile

# Prompt focused on extracting core user profile information
USER_PROFILE_EXTRACTION_PROMPT = """
You are an Expert User Profile Curator for Joyce.

Goal: From conversation context, extract core user profile information and update the user's profile.
Focus ONLY on the core static profile fields that define who the user is.

CORE FIELDS TO EXTRACT:
- first_name: User's given/first name
- last_name: User's family/last name
- preferred_name: What they like to be called (if different from first_name)
- email: Email address
- gender: Gender identity (keep it simple: male, female, non-binary, other)
- birth_date: Birth date in YYYY-MM-DD format
- location: JSON object with home, current, timezone if mentioned
- bio: 2-4 sentence static biographical summary (NOT mood/temporary states)

CRITICAL RULES:
- NEVER extract or update phone number - this is explicitly forbidden
- Only extract information that is clearly stated or strongly implied
- For bio: focus on static, lasting information about the person (profession, interests, background)
- For bio: do NOT include temporary moods, current activities, or conversational context
- For location: structure as {{"home": "City, State", "current": "City, State", "timezone": "America/Los_Angeles"}}
- Only call the update tool when new profile information is clearly provided
- If no clear profile information is mentioned, do not call any tool

Available tool:
- update_user_profile_data(field_updates)

Context provided:
- Current time/date: {time} on {date}
- Current user profile: {user_profile}

Instructions:
- Think step-by-step about what profile information is mentioned
- Only extract information that is explicitly stated or clearly implied
- Combine with existing profile data, don't overwrite with null/empty values
- If no profile updates are warranted, do not call any tool
""".strip()


@function_tool()
async def update_user_profile_data(
    first_name: str | None = None,
    last_name: str | None = None,
    preferred_name: str | None = None,
    email: str | None = None,
    gender: str | None = None,
    birth_date: str | None = None,  # YYYY-MM-DD format
    location_home: str | None = None,  # City, State format
    location_current: str | None = None,  # City, State format
    location_timezone: str | None = None,  # America/Los_Angeles format
    bio: str | None = None,
) -> str:
    """
    Update user profile with extracted information.

    Args:
        first_name: User's first name
        last_name: User's last name
        preferred_name: User's preferred name/nickname
        email: User's email address
        gender: User's gender (male, female, non-binary, other)
        birth_date: Birth date in YYYY-MM-DD format
        location_home: Home location as "City, State"
        location_current: Current location as "City, State"
        location_timezone: Timezone as "America/Los_Angeles"
        bio: Brief bio (2-4 sentences of static information)

    Examples:
    ```json
    {
      "first_name": "Sarah",
      "last_name": "Johnson",
      "preferred_name": "Sarah",
      "email": "sarah@email.com",
      "gender": "female",
      "birth_date": "1990-05-15",
      "location_home": "Seattle, WA",
      "bio": "Software engineer with a passion for AI. Loves hiking and cooking."
    }
    ```
    """
    return "update_user_profile_data enqueued"


def _format_user_profile_simple(profile: UserProfile | None) -> str:
    """Format user profile for LLM context."""
    if profile is None:
        return "No profile found"

    parts: list[str] = []
    if profile.first_name:
        parts.append(f"first_name: {profile.first_name}")
    if profile.last_name:
        parts.append(f"last_name: {profile.last_name}")
    if profile.preferred_name:
        parts.append(f"preferred_name: {profile.preferred_name}")
    if profile.email:
        parts.append(f"email: {profile.email}")
    if profile.gender:
        parts.append(f"gender: {profile.gender}")
    if profile.birth_date:
        parts.append(f"birth_date: {profile.birth_date}")
    if profile.location:
        parts.append(f"location: {json.dumps(profile.location)}")
    if profile.bio:
        parts.append(f"bio: {profile.bio}")

    return "Current profile: {" + ", ".join(parts) + "}"


async def extract_and_update_user_profile(
    user_id: str,
    new_message: str,
    ctx: ChatContext,
) -> None:
    """
    Analyze user message and extract/update core user profile information.

    This function:
    - Loads the user's current profile
    - Analyzes recent conversation for profile information
    - Calls LLM to extract structured profile data
    - Updates the user_profile table with new information
    """
    tools = [update_user_profile_data]

    # Load user profile
    user_profile = await get_user_profile(user_id)

    current_time = datetime.now(
        user_profile.timezone if user_profile else None
    ).strftime("%I:%M %p")
    current_date = datetime.now(
        user_profile.timezone if user_profile else None
    ).strftime("%d %b %Y")

    prompt = USER_PROFILE_EXTRACTION_PROMPT.format(
        time=current_time,
        date=current_date,
        user_profile=_format_user_profile_simple(user_profile),
    )

    # Recent conversation context
    chat_items = ctx.items
    user_messages = [
        item for item in chat_items if item.type == "message" and item.role == "user"
    ]
    last_user_messages = user_messages[-3:]  # Last 3 messages for context
    last_user_messages_str = "Recent conversation:\n\n" + "\n\n".join(
        [f"{item.role}: {item.content}" for item in last_user_messages]
    )
    user_message_str = f"Latest message: {new_message}"

    # Create chat context with the extraction prompt
    chat_ctx = ChatContext()
    chat_ctx.add_message(role="system", content=prompt)
    chat_ctx.add_message(role="user", content=last_user_messages_str)
    chat_ctx.add_message(role="user", content=user_message_str)

    # Use a fast LLM with tool calls
    llm = openai.LLM(
        model="gpt-4.1", parallel_tool_calls=False, _strict_tool_schema=False
    )

    async with llm.chat(chat_ctx=chat_ctx, tools=tools, tool_choice="auto") as stream:
        tool_calls: list[FunctionToolCall] = []

        async for chunk in stream:
            if chunk.delta and chunk.delta.tool_calls:
                tool_calls.extend(chunk.delta.tool_calls)

    # Apply tool calls to update profile
    for call in tool_calls:
        if call.name == "update_user_profile_data":
            args = json.loads(call.arguments) or {}

            # Parse birth_date if provided
            birth_date = None
            if args.get("birth_date"):
                try:
                    birth_date = datetime.strptime(
                        args["birth_date"], "%Y-%m-%d"
                    ).date()
                except ValueError:
                    # Skip invalid date format
                    pass

            # Build location object if any location data provided
            location = None
            if any(
                args.get(k)
                for k in ["location_home", "location_current", "location_timezone"]
            ):
                # Start with existing location or empty dict
                location = (
                    user_profile.location.copy()
                    if user_profile and user_profile.location
                    else {}
                )

                if args.get("location_home"):
                    location["home"] = args["location_home"]
                if args.get("location_current"):
                    location["current"] = args["location_current"]
                if args.get("location_timezone"):
                    location["timezone"] = args["location_timezone"]

            # Update profile with extracted data
            await update_user_profile(
                user_id=user_id,
                first_name=args.get("first_name"),
                last_name=args.get("last_name"),
                preferred_name=args.get("preferred_name"),
                email=args.get("email"),
                gender=args.get("gender"),
                birth_date=birth_date,
                location=location,
                bio=args.get("bio"),
            )
