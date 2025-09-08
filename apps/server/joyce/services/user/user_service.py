from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy import select, update
from supabase_auth import User

from joyce.db import SessionMaker
from joyce.db.schema import UserProfile
from joyce.db.schema.auth import users
from joyce.services.supabase import supabase_client


class UserAlreadyExistsError(Exception):
    def __init__(self, user_id: str) -> None:
        self.user_id = user_id
        super().__init__(f"User profile already exists for user {user_id}")


class UserService:
    def __init__(self, user_id: str) -> None:
        self.user_id = user_id

    @classmethod
    async def init_user_profile(
        cls,
        user_id: str,
        first_name: str,
        last_name: str,
        dob: date,
        email: str,
        phone: str,
    ) -> UserService:
        async with SessionMaker() as session:
            # Check if the user profile already exists
            result = await session.execute(
                select(UserProfile).filter(UserProfile.user_id == user_id)
            )
            profile = result.scalars().first()
            if profile:
                raise UserAlreadyExistsError(user_id)

            # Create the user profile
            profile = UserProfile(
                user_id=user_id,
                first_name=first_name,
                last_name=last_name,
                dob=dob,
                email=email,
                phone=phone,
            )
            session.add(profile)
            await session.commit()

        return UserService(user_id)

    @classmethod
    async def get_or_create(cls, phone_number: str) -> UserService:
        # Remove spaces and non-numeric characters
        clean_phone_number = "".join(filter(str.isdigit, phone_number))

        # Create a user profile for the caller if it doesn't exist
        async with SessionMaker() as session:
            stmt = select(users.c.id).where(users.c.phone == clean_phone_number)

            result = await session.execute(stmt)
            existing_user_id = result.scalar_one_or_none()
            if existing_user_id:
                return str(existing_user_id)

            # If we create user and fail before user profile, we need to delete the user
            user: User | None = None
            try:
                # Create a new user for the caller
                user_response = supabase_client.auth.admin.create_user(
                    {
                        "phone": phone_number,
                        "phone_confirm": True,
                    }
                )
                user: User = user_response.user

                # Create a user profile for the caller with the user id and phone number
                user_profile = UserProfile(
                    user_id=user.id,
                    phone=phone_number,
                )
                session.add(user_profile)
                await session.commit()

                return user.id
            except Exception as e:
                if user:
                    await supabase_client.auth.admin.delete_user(user.id)
                raise e

    async def get_user_profile(self) -> UserProfile:
        async with SessionMaker() as session:
            result = await session.execute(
                select(UserProfile).filter(UserProfile.user_id == self.user_id)
            )
            return result.scalars().one()


async def update_user_profile(
    user_id: str,
    **updates: Any,
) -> UserProfile | None:
    """
    Update user profile with provided fields. Only updates non-None values.

    Args:
        user_id: User UUID
        **updates: Keyword arguments for fields to update (first_name, last_name,
                  preferred_name, email, gender, birth_date, location, bio)

    Returns:
        Updated UserProfile or None if user not found
    """
    async with SessionMaker() as session:
        # Build update values dict, only including non-None values
        update_values = {k: v for k, v in updates.items() if v is not None}

        # Only proceed if there are values to update
        if not update_values:
            return None

        # Update the profile
        await session.execute(
            update(UserProfile)
            .where(UserProfile.user_id == user_id)
            .values(**update_values)
        )
        await session.commit()

        # Return updated profile
        result = await session.execute(
            select(UserProfile).filter(UserProfile.user_id == user_id)
        )
        return result.scalars().first()
