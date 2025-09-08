from __future__ import annotations

from livekit.agents import RunContext, function_tool

from joyce.agent.functions import format_user_entities, format_user_entity
from joyce.agent.user import UserData
from joyce.services.user import (
    archive_entity,
    create_entity,
    get_entity_by_id,
    get_entity_by_slug,
    list_entities,
    update_entity_by_slug,
)
from joyce.types import UserEntityCollection, UserEntityType

from .utils import get_user_id_from_context


@function_tool()
async def add_user_entity(
    context: RunContext[UserData],
    collection: UserEntityCollection,
    entity_type: UserEntityType,
    slug: str,
    entity_data: object,
) -> str:
    """
    Create a new user entity (or upsert by slug).

    Args:
        collection: Entity collection bucket - one of: identity, social, professional, health, lifestyle, pursuits, resources, milestones, misc
        entity_type: Category within collection. Use UserEntityType enum
        slug: Human-readable identifier. Use "user/{entity_type}" for unique entities, "user/{entity_type}.{identifier}" for entities that can have multiple instances
        entity_data: JSON data describing the entity (Required)

    Entity Type Guidelines:
        - Unique entities (one per user): father, mother, spouse, birth_date, primary_job, blood_type
        - Multi-instance entities: goal, friend, skill, health_condition, hobby, achievement

    Examples:
    For unique entities (typically one per user):
    ```json
    {
      "collection": "social",
      "entity_type": "father",
      "slug": "user/father",
      "entity_data": {"first_name": "John", "last_name": "Smith", "birth_date": "1970-01-01"}
    }
    ```

    For entities that can have multiple instances:
    ```json
    {
      "collection": "pursuits",
      "entity_type": "goal",
      "slug": "user/goal.marathon-2025",
      "entity_data": {"title": "Run marathon", "target_date": "2025-10-01"}
    }
    ```

    ```json
    {
      "collection": "social",
      "entity_type": "friend",
      "slug": "user/friend.sarah-johnson",
      "entity_data": {"first_name": "Sarah", "last_name": "Johnson", "relationship_type": "close_friend"}
    }
    ```
    """
    user_id = get_user_id_from_context(context)

    entity = await create_entity(
        user_id=user_id,
        entity_type=entity_type,
        data=entity_data,
        slug=slug,
        collection=collection.value,
        allow_upsert=True,
    )
    return format_user_entity(entity)


@function_tool()
async def update_user_entity(
    context: RunContext[UserData],
    slug: str,
    entity_data: object,
) -> str:
    """
    Update an existing entity's data (merges with existing data).

    Always call `list_user_entities` or `get_user_entity_by_slug` to confirm the entity exists before updating.
    If the entity does not exist, call `add_user_entity` to create it.

    Args:
        slug: Human-readable identifier. Use "user/{entity_type}" for unique entities, "user/{entity_type}.{identifier}" for multiple instances
        entity_data: JSON data to fully replace existing entity data

    Entity Type Guidelines:
        - Unique entities (one per user): father, mother, spouse, birth_date, primary_job, blood_type
        - Multi-instance entities: goal, friend, skill, health_condition, hobby, achievement

    Examples:
    For unique entities:
    ```json
    {
      "slug": "user/father",
      "entity_data": {"first_name": "John", "last_name": "Smith", "age": 52, "location": "Seattle"}
    }
    ```

    For entities with multiple instances:
    ```json
    {
      "slug": "user/goal.marathon-2025",
      "entity_data": {"title": "Run Boston Marathon", "target_date": "2025-04-21", "training_status": "in_progress"}
    }
    ```
    """
    user_id = get_user_id_from_context(context)
    entity = await update_entity_by_slug(user_id=user_id, slug=slug, data=entity_data)
    return format_user_entity(entity)


@function_tool()
async def get_user_entities(
    context: RunContext[UserData],
) -> str:
    """
    List all non-archived entities for the current user.

    Example:
    ```json
    {}
    ```
    """
    user_id = get_user_id_from_context(context)
    entities = await list_entities(
        user_id=user_id, include_archived=False, limit=1000, offset=0
    )
    return format_user_entities(entities)


@function_tool()
async def get_user_entity_by_id(
    context: RunContext[UserData],
    entity_id: str,
) -> str:
    """
    Retrieve a single entity by its UUID.

    Args:
        entity_id: UUID of the entity to fetch

    Example:
    ```json
    {"entity_id": "f0b0a6f0-9c2f-4b2e-8a8a-3b9e6d7f1234"}
    ```
    """
    entity = await get_entity_by_id(entity_id=entity_id, include_archived=False)
    return format_user_entity(entity)


@function_tool()
async def get_user_entity_by_slug(
    context: RunContext[UserData],
    slug: str,
) -> str:
    """
    Retrieve a single entity by its slug identifier.

    Args:
        slug: Human-readable identifier. Use "user/{entity_type}" for unique entities, "user/{entity_type}.{identifier}" for multiple instances

    Entity Type Guidelines:
        - Unique entities (one per user): father, mother, spouse, birth_date, primary_job, blood_type
        - Multi-instance entities: goal, friend, skill, health_condition, hobby, achievement

    Examples:
    ```json
    {"slug": "user/father"}
    ```

    ```json
    {"slug": "user/goal.marathon-2025"}
    ```
    """
    user_id = get_user_id_from_context(context)
    entity = await get_entity_by_slug(user_id, slug)
    return format_user_entity(entity)


@function_tool()
async def delete_user_entity(
    context: RunContext[UserData],
    entity_id: str,
    reason: str | None = None,
) -> str:
    """
    Delete (archive) an entity.

    Args:
        entity_id: UUID of the entity to delete
        reason: Optional deletion reason

    Example:
    ```json
    {
      "entity_id": "f0b0a6f0-9c2f-4b2e-8a8a-3b9e6d7f1234",
      "reason": "No longer relevant"
    }
    ```
    """

    user_id = get_user_id_from_context(context)

    success = await archive_entity(user_id=user_id, entity_id=entity_id, reason=reason)
    return "Succesffully deleted entity" if success else "Failed to delete entity"
