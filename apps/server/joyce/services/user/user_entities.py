from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from sqlalchemy import and_, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import OperationalError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from joyce.db.client import SessionMaker
from joyce.db.schema import UserEntity, UserProfile
from joyce.utils import safify

logger = logging.getLogger(__name__)


def make_entity_slug(
    user_handle: str, entity_type: str, identifier: str, short_id: str | None = None
) -> str:
    """
    Generate entity slug following consistent patterns.

    Args:
        user_handle: User identifier (first name, username, etc.)
        entity_type: Type of entity (relationship, goal, health, etc.)
        identifier: Specific identifier (name, description, etc.)
        short_id: Optional short UUID suffix for uniqueness

    Returns:
        Formatted slug like "dave/father.john" or "dave/goal.marathon-5a3b2"

    Examples:
        make_entity_slug("dave", "father", "john") -> "dave/father.john"
        make_entity_slug("sarah", "goal", "marathon", "5a3b2") -> "sarah/goal.marathon-5a3b2"
        make_entity_slug("mike", "favorite-food", "pizza") -> "mike/favorite-food.pizza"
    """
    base_slug = f"{user_handle}/{entity_type}.{identifier}"
    if short_id:
        base_slug += f"-{short_id}"
    return safify(base_slug)


@retry(
    retry=retry_if_exception_type(OperationalError),
    stop=stop_after_attempt(3),
    wait=wait_fixed(1),
)
async def create_entity(
    user_id: str,
    entity_type: str,
    data: dict,
    slug: str | None = None,
    collection: str = "misc",
    allow_upsert: bool = False,
) -> UserEntity:
    """
    Create a new user entity with optional upsert behavior.

    Args:
        user_id: User UUID
        entity_type: Type of entity for categorization
        data: JSONB data with entity-specific data
        slug: Optional human-readable slug (auto-generated if None)
        collection: Entity collection (relationships, goals, health, etc.)
        allow_upsert: If True and slug exists, merge with existing entity

    Returns:
        Dictionary representation of created/updated entity

    Raises:
        IntegrityError: If slug exists and allow_upsert is False
    """
    async with SessionMaker() as session:
        user_profile_result = await session.execute(
            select(UserProfile).filter(UserProfile.user_id == user_id)
        )
        user_profile = user_profile_result.scalars().one()

        entity_id = uuid4()
        slug = slug or make_entity_slug(
            user_profile.display_name.split(" ")[0],
            entity_type,
            str(entity_id).split("-")[0],
        )

        # Ensure data has canonical ID for LLM convenience
        data = data.copy() if data else {}
        data["id"] = str(entity_id)
        data.setdefault("meta", {}).update(
            {
                "created_source": "llm_tool",
                "last_updated": datetime.now(timezone.utc).isoformat(),
            }
        )

        stmt = insert(UserEntity).values(
            id=entity_id,
            user_id=user_id,
            slug=slug,
            type=entity_type,
            collection=collection,
            data=data,
        )

        # Add ON CONFLICT logic if upsert is allowed
        if allow_upsert:
            stmt = stmt.on_conflict_do_update(
                constraint="uq_user_entities_user_slug",
                set_={
                    "type": stmt.excluded.type,
                    "collection": stmt.excluded.collection,
                    "data": stmt.excluded.data,
                    "updated_at": func.now(),
                    "archived_at": None,
                },
            )

        stmt = stmt.returning(UserEntity)

        result = await session.execute(stmt)
        entity = result.scalars().one()
        await session.commit()

        return entity


@retry(
    retry=retry_if_exception_type(OperationalError),
    stop=stop_after_attempt(3),
    wait=wait_fixed(1),
)
async def get_entity_by_id(
    entity_id: str,
    include_archived: bool = False,
) -> UserEntity | None:
    """
    Get a single entity by ID.

    Args:
        entity_id: Entity UUID
        include_archived: Whether to include archived entities
    """
    async with SessionMaker() as session:
        result = await session.execute(
            select(UserEntity).filter(UserEntity.id == entity_id)
        )
        return result.scalars().first()


@retry(
    retry=retry_if_exception_type(OperationalError),
    stop=stop_after_attempt(3),
    wait=wait_fixed(1),
)
async def get_entity_by_slug(
    user_id: str,
    slug: str,
    include_archived: bool = False,
) -> UserEntity | None:
    """
    Get a single entity by ID.

    Args:
        entity_id: Entity UUID
        include_archived: Whether to include archived entities
    """
    async with SessionMaker() as session:
        result = await session.execute(
            select(UserEntity).filter(
                UserEntity.user_id == user_id,
                UserEntity.slug == slug,
            )
        )
        return result.scalars().first()


@retry(
    retry=retry_if_exception_type(OperationalError),
    stop=stop_after_attempt(3),
    wait=wait_fixed(1),
)
async def list_entities(
    user_id: str,
    entity_type: str | None = None,
    collection: str | None = None,
    include_archived: bool = False,
    limit: int = 1000,
    offset: int = 0,
) -> list[UserEntity]:
    """
    List entities for a user with optional filtering.

    Args:
        user_id: User UUID
        entity_type: Optional filter by entity type
        collection: Optional filter by collection
        include_archived: Whether to include archived entities
        limit: Maximum number of entities to return
        offset: Number of entities to skip

    Returns:
        List of entity dictionaries ordered by updated_at desc
    """
    async with SessionMaker() as session:
        query = select(UserEntity).filter(UserEntity.user_id == user_id)

        if entity_type:
            query = query.filter(UserEntity.type == entity_type)

        if collection:
            query = query.filter(UserEntity.collection == collection)

        if not include_archived:
            query = query.filter(UserEntity.archived_at.is_(None))

        query = query.order_by(UserEntity.updated_at.desc()).limit(limit).offset(offset)

        result = await session.execute(query)
        return list(result.scalars().all())


@retry(
    retry=retry_if_exception_type(OperationalError),
    stop=stop_after_attempt(3),
    wait=wait_fixed(1),
)
async def update_entity_by_id(
    user_id: str,
    entity_id: str,
    data: dict[str, Any],
) -> Optional[UserEntity]:
    """
    Update entity by ID with new data.
    """
    async with SessionMaker() as session:
        # Get entity with row lock
        result = await session.execute(
            select(UserEntity)
            .filter(
                and_(
                    UserEntity.user_id == user_id,
                    UserEntity.id == entity_id,
                    UserEntity.archived_at.is_(None),
                )
            )
            .with_for_update()
        )
        entity = result.scalars().first()

        if not entity:
            return None

        # Update metadata
        meta = data.setdefault("meta", {})
        meta["last_updated"] = datetime.now(timezone.utc).isoformat()

        entity.data = data
        entity.updated_at = func.now()

        await session.commit()
        await session.refresh(entity)

        return entity


@retry(
    retry=retry_if_exception_type(OperationalError),
    stop=stop_after_attempt(3),
    wait=wait_fixed(1),
)
async def update_entity_by_slug(
    user_id: str,
    slug: str,
    data: dict[str, Any],
) -> Optional[UserEntity]:
    """
    Update entity by slug with new data.

    Args:
        user_id: User UUID
        slug: Entity slug to update
        data: New data to set for the entity

    Returns:
        Updated entity or None if not found

    Example:
        # Update relationship contact info
        await update_entity_by_slug(
            user_id="123",
            slug="dave/father.john",
            data={"phone": "+1-987-654-3210", "location": "Seattle"}
        )
    """
    async with SessionMaker() as session:
        # Get entity with row lock
        result = await session.execute(
            select(UserEntity)
            .filter(
                and_(
                    UserEntity.user_id == user_id,
                    UserEntity.slug == slug,
                    UserEntity.archived_at.is_(None),
                )
            )
            .with_for_update()
        )
        entity = result.scalars().first()

        if not entity:
            return None

        # Update metadata
        meta = data.setdefault("meta", {})
        meta["last_updated"] = datetime.now(timezone.utc).isoformat()

        entity.data = data
        entity.updated_at = func.now()

        await session.commit()
        await session.refresh(entity)

        return entity


@retry(
    retry=retry_if_exception_type(OperationalError),
    stop=stop_after_attempt(3),
    wait=wait_fixed(1),
)
async def archive_entity(
    user_id: str, entity_id: str, reason: str | None = None
) -> bool:
    """
    Soft delete entity by setting archived_at timestamp.

    Args:
        user_id: User UUID
        entity_id: Entity UUID to archive
        reason: Optional reason for archival (stored in metadata)

    Returns:
        True if entity was archived, False if not found
    """
    async with SessionMaker() as session:
        # Get entity with row lock
        result = await session.execute(
            select(UserEntity)
            .filter(
                and_(
                    UserEntity.user_id == user_id,
                    UserEntity.id == entity_id,
                    UserEntity.archived_at.is_(None),
                )
            )
            .with_for_update()
        )
        entity = result.scalars().first()

        if not entity:
            return False

        # Set archived timestamp and add reason to metadata
        entity.archived_at = func.now()

        if reason:
            meta = entity.data.setdefault("meta", {}) if entity.data else {}
            meta["archive_reason"] = reason
            meta["archived_by"] = "llm_tool"
            entity.data = entity.data or {}

        await session.commit()

        return True
