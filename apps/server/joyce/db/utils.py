"""
Database utility functions.
"""

from __future__ import annotations

import os
import uuid

from joyce.env import env


def get_user() -> str:
    """
    Get the current user ID.

    In development mode, reads from USER_ID environment variable.
    In production, this would typically come from authentication context.

    Returns:
        str: User ID as string (UUID format)

    Raises:
        RuntimeError: If USER_ID is not set in development mode
        ValueError: If USER_ID is not a valid UUID format
    """
    if env.is_development:
        user_id = os.getenv("USER_ID")
        if not user_id:
            raise RuntimeError(
                "USER_ID environment variable must be set in development mode"
            )

        # Validate UUID format
        try:
            uuid.UUID(user_id)
        except ValueError as e:
            raise ValueError(f"USER_ID must be a valid UUID: {e}") from e

        return user_id
    # In production, this would come from authentication context
    # For now, raise an error to prevent accidental usage
    raise RuntimeError("User ID resolution not implemented for production mode")


def get_user_safe() -> str | None:
    """
    Get the current user ID safely without raising exceptions.

    Returns:
        Optional[str]: User ID if available and valid, None otherwise
    """
    try:
        return get_user()
    except (RuntimeError, ValueError):
        return None
