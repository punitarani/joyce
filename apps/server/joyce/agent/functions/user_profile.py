from __future__ import annotations

import json

from joyce.db.schema import UserProfile

USER_PROFILE_PROMPT = """
Here is the user's profile information:
First name: {first_name}
Last name: {last_name}
Preferred name: {preferred_name}

Gender: {gender}
Birth date: {birth_date}

Email: {email}
Phone: {phone}

Location:
{location}

Attributes:
{attributes}

User's onboarding status: {status}
""".strip()


def format_user_profile(user_profile: UserProfile | None) -> str:
    if user_profile is None:
        return "User profile not found or not loaded"

    return USER_PROFILE_PROMPT.format(
        first_name=user_profile.first_name,
        last_name=user_profile.last_name,
        preferred_name=user_profile.preferred_name or user_profile.first_name,
        email=user_profile.email,
        phone=user_profile.phone,
        gender=user_profile.gender,
        birth_date=(
            user_profile.birth_date.isoformat()
            if user_profile.birth_date
            else "Not provided"
        ),
        location=(
            json.dumps(user_profile.location, indent=2)
            if user_profile.location
            else "No location information provided"
        ),
        attributes=(
            json.dumps(user_profile.attributes, indent=2)
            if user_profile.attributes
            else "None"
        ),
        status=user_profile.status,
    )
