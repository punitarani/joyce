from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from livekit.agents import RunContext, function_tool

from joyce.agent.functions import format_user_profile
from joyce.agent.user import UserData
from joyce.services.user import update_user_profile

from .utils import get_user_id_from_context


@function_tool()
async def update_user_profile_info(
    context: RunContext[UserData],
    first_name: str | None = None,
    last_name: str | None = None,
    preferred_name: str | None = None,
    email: str | None = None,
    gender: str | None = None,
    birth_date: str | None = None,  # YYYY-MM-DD format
    location: Dict[str, Any] | None = None,
    bio: str | None = None,
) -> str:
    """
    Update user profile with core information.

    Args:
        first_name: User's first name
        last_name: User's last name
        preferred_name: User's preferred name/nickname
        email: User's email address
        gender: User's gender (male, female, non-binary, other)
        birth_date: Birth date in YYYY-MM-DD format
        location: Location object with home, current, timezone keys
        bio: Brief bio (2-4 sentences of static information about the user)

    Examples:
    For basic name and email:
    ```json
    {
      "first_name": "Sarah",
      "last_name": "Johnson",
      "email": "sarah@email.com"
    }
    ```

    For location information:
    ```json
    {
      "location": {
        "home": "Seattle, WA",
        "current": "Portland, OR",
        "timezone": "America/Los_Angeles"
      }
    }
    ```

    For bio (static information only):
    ```json
    {
      "bio": "Software engineer with 5 years experience. Passionate about AI and machine learning. Enjoys hiking and photography."
    }
    ```
    """
    user_id = get_user_id_from_context(context)

    # Parse birth_date if provided
    birth_date_obj = None
    if birth_date:
        try:
            birth_date_obj = datetime.strptime(birth_date, "%Y-%m-%d").date()
        except ValueError:
            return f"Invalid birth_date format. Please use YYYY-MM-DD format."

    # Update profile with provided data
    updated_profile = await update_user_profile(
        user_id=user_id,
        first_name=first_name,
        last_name=last_name,
        preferred_name=preferred_name,
        email=email,
        gender=gender,
        birth_date=birth_date_obj,
        location=location,
        bio=bio,
    )

    if updated_profile:
        return f"Successfully updated profile information:\n{format_user_profile(updated_profile)}"
    return "No profile updates were made. Please provide at least one field to update."
