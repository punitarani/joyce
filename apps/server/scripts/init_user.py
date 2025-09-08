"""
Initialize user profile in the database.

Creates the required user profile record for the current user.
Does NOT create auth.users record as that's managed by Supabase.

Usage:
    python scripts/init_user.py
    # or
    uv run python scripts/init_user.py
"""

import asyncio
import sys
from datetime import date
from pathlib import Path

# Add parent directory to path so we can import joyce modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.dialects.postgresql import insert

from joyce.db.client import SessionMaker
from joyce.db.schema.user_profile import UserProfile
from joyce.db.utils import get_user


async def init_user() -> None:
    """Initialize user profile for the current user."""
    try:
        user_id = get_user()
        print(f"Initializing user profile for user_id: {user_id}")

        async with SessionMaker() as session:
            # Create user profile with UPSERT behavior
            stmt = insert(UserProfile).values(
                user_id=user_id,
                first_name="Punit",
                last_name="Arani",
                email="punitsai36@gmail.com",
                phone="+16235232095",
                gender="male",
                birth_date=date(2001, 12, 10),
                bio="I am Punit Arani. I am a new user getting started with Joyce.",
                attributes={},
                location={
                    "home": "San Francisco, CA",
                    "current": "San Francisco, CA",
                    "from": "Bangalore, India",
                    "timezone": "US/Pacific",
                },
            )

            # On conflict, update the version to show it was re-initialized
            stmt = stmt.on_conflict_do_update(
                index_elements=["user_id"],
                set_={
                    "version": stmt.excluded.version,
                    "last_updated_at": stmt.excluded.last_updated_at,
                },
            )

            await session.execute(stmt)
            await session.commit()

        print(f"✅ User profile initialized successfully for {user_id}")

    except Exception as e:
        print(f"❌ Failed to initialize user profile: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(init_user())
