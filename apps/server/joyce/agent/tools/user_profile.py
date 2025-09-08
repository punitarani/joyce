from __future__ import annotations

from livekit.agents import RunContext, function_tool

from joyce.agent.functions import format_user_profile
from joyce.agent.user import UserData

from .utils import get_user_profile_from_context


@function_tool()
async def get_user_profile(context: RunContext[UserData]) -> str:
    """
    Get the current user's profile information.

    Example:
    ```json
    {}
    ```
    """
    user_profile = await get_user_profile_from_context(context)
    return format_user_profile(user_profile)
