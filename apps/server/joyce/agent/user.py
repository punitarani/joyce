from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.exc import OperationalError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_fixed,
)

from joyce.db.client import SessionMaker
from joyce.db.schema.user_profile import UserProfile


@dataclass
class UserData:
    user_id: str
    user_profile: UserProfile | None = None

    async def get_user_profile(self) -> UserProfile | None:
        if self.user_profile:
            return self.user_profile

        return await get_user_profile(self.user_id)


@retry(
    retry=retry_if_exception_type(OperationalError),
    stop=stop_after_attempt(3),
    wait=wait_fixed(wait=1),
)
async def get_user_profile(user_id: str) -> UserProfile | None:
    async with SessionMaker() as session:
        result = await session.execute(
            select(UserProfile).filter(UserProfile.user_id == user_id)
        )

        return result.scalars().first()
