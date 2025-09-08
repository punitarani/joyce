from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import Any

from livekit.agents import ChatContext, function_tool
from livekit.agents.llm import FunctionToolCall
from livekit.plugins import openai

from joyce.agent.user import get_user_profile
from joyce.db.schema.user_profile import UserProfile
from joyce.services.user import (
    archive_entity,
    create_entity,
    list_entities,
    update_entity_by_slug,
)

# Prompt focused on extracting semi-permanent user entities (profile-defining facts)
KEY_ENTITY_EXTRACTION_PROMPT = """
You are an Expert Personal-Graph Curator.

Goal: From conversation context, decide whether to CREATE, UPDATE (via JSON Merge Patch), or ARCHIVE
user entities that represent semi-permanent facts about the person. Entities should be high-signal,
relatively stable facts that define the user (identity, relationships, goals, health conditions,
important dates, preferences, achievements, memberships, recurring events, education, work, etc.).

Critical rules:
- Prefer UPDATE over CREATE when the same real-world concept already exists (match by meaning, slug, or id).
- Use ARCHIVE only when the user explicitly indicates the entity is no longer valid/relevant.
- Use CREATE when new, non-duplicate facts appear. Provide rich, structured `data`.
- For UPDATE, provide a minimal JSON Merge Patch for `data`; omit unchanged fields.
- For CREATE, include `entity_type`, `collection`, and a well-structured `data` body. A slug may be provided if stable.
- For slug generation: Use simple "user/entity_type" for unique entities (e.g., father, mother, spouse, primary_job, birth_date). Add specific identifiers for entities that can have multiples (e.g., goals, friends, health_conditions, skills, etc.). Refer to entity type classification for guidance.
- Do not store transient, mood-like, or conversational ephemera (those belong to memories).
- Prefer concise, unambiguous, and verifiable fields. Include clear identifiers (names, dates, orgs, etc.).

Available tools to call:
- create_key_entity(entity_type, data, slug?, collection?, allow_upsert?)
- update_key_entity(entity_id, patch, update_metadata?)
- delete_key_entity(entity_id, reason?)  # Soft-delete (archive)

Context provided to you:
- Current time/date: {time} on {date}
- User profile: {user_profile}
- Existing entities (markdown table):\n{existing_entities}

Instructions:
- Think step-by-step. If an entity already exists, UPDATE it. If not, CREATE it.
- Only call tools when action is clearly justified by the user's latest message and recent turns.
- If no entity action is warranted, do not call any tool.
- You may issue multiple tool calls in parallel if necessary (e.g., create a relationship and a goal).
""".strip()


@function_tool()
async def create_key_entity(
    entity_type: str,
    collection: str,
    entity_data: object,
    slug: str | None = None,
    allow_upsert: bool = False,
) -> str:
    """
    Create a new user entity representing a semi-permanent fact.

    Args:
        entity_type: Category within collection, e.g. "father", "goal", "employer"
        collection: Collection bucket - one of: identity, social, professional, health, lifestyle, pursuits, resources, milestones, misc
        entity_data: Structured details for this entity
        slug: Optional stable identifier, auto-generated if omitted
        allow_upsert: If true and slug exists, update existing entity

    Examples:
    For unique entities (typically one per user):
    ```json
    {{
      "entity_type": "father",
      "entity_data": {{"first_name": "John", "last_name": "Smith"}},
      "collection": "social",
      "slug": "user/father"
    }}
    ```

    For entities that can have multiple instances:
    ```json
    {{
      "entity_type": "goal",
      "entity_data": {{"title": "Run marathon", "target_date": "2025-10-01"}},
      "collection": "pursuits",
      "slug": "user/goal.marathon-2025"
    }}
    ```
    """
    return "create_key_entity enqueued"


@function_tool()
async def update_key_entity(
    entity_id: str,
    patch: object,
    update_metadata: bool = True,
) -> str:
    """
    Update an existing entity's data using JSON merge patch.

    Args:
        entity_id: UUID of the entity to update
        patch: JSON merge patch for data - set field to null to remove
        update_metadata: If true, updates last_updated timestamp

    Example:
    ```json
    {{
      "entity_id": "f0b0a6f0-9c2f-4b2e-8a8a-3b9e6d7f1234",
      "patch": {{"age": 53, "location": "Portland"}}
    }}
    ```
    """
    return "update_key_entity enqueued"


@function_tool()
async def delete_key_entity(
    entity_id: str,
    reason: str | None = None,
) -> str:
    """
    Soft-delete (archive) an entity.

    Args:
        entity_id: UUID of the entity to archive
        reason: Optional reason for deletion

    Example:
    ```json
    {{
      "entity_id": "f0b0a6f0-9c2f-4b2e-8a8a-3b9e6d7f1234",
      "reason": "No longer relevant"
    }}
    ```
    """
    return "delete_key_entity enqueued"


# ---- Formatting helpers ----


def _format_user_profile(profile: UserProfile | None) -> str:
    if profile is None:
        return "{{}}"
    parts: list[str] = []
    if profile.first_name or profile.last_name:
        parts.append(f"name={profile.full_name}")
    if profile.preferred_name:
        parts.append(f"preferred_name={profile.preferred_name}")
    if profile.email:
        parts.append(f"email={profile.email}")
    if profile.phone:
        parts.append(f"phone={profile.phone}")
    if profile.gender:
        parts.append(f"gender={profile.gender}")
    if profile.birth_date:
        parts.append(f"birth_date={profile.birth_date}")
    if profile.location:
        parts.append(f"location={profile.location}")
    return "{{" + ", ".join(parts) + "}}"


def _format_entities_as_markdown_table(entities: list[Any]) -> str:
    if not entities:
        return "(none)"
    header = "| id | slug | collection | type | data |\n| --- | --- | --- | --- | --- |"
    rows: list[str] = []
    for e in entities:
        # e may be ORM or dict-like; use getattr then fallback to dict
        eid = getattr(e, "id", None) or (e.get("id") if isinstance(e, dict) else None)
        slug = getattr(e, "slug", None) or (
            e.get("slug") if isinstance(e, dict) else None
        )
        collection = getattr(e, "collection", None) or (
            e.get("collection") if isinstance(e, dict) else None
        )
        etype = getattr(e, "type", None) or (
            e.get("type") if isinstance(e, dict) else None
        )
        data = getattr(e, "data", None) or (
            e.get("data") if isinstance(e, dict) else None
        )

        def esc(val: Any) -> str:
            s = "" if val is None else str(val)
            return s.replace("|", "\\|")

        if isinstance(data, (dict, list)):
            try:
                data_str = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
            except Exception:
                data_str = str(data)
        else:
            data_str = str(data) if data is not None else ""

        row = f"| {esc(eid)} | {esc(slug)} | {esc(collection)} | {esc(etype)} | {esc(data_str)} |"
        rows.append(row)

    return header + "\n" + "\n".join(rows)


# ---- Orchestrator ----


async def extract_and_store_key_entities(
    user_id: str,
    new_message: str,
    stored_entities: list[dict],
    ctx: ChatContext,
) -> None:
    """
    Analyze recent user messages to create/update/archive key user entities.

    This function:
    - Loads the user's profile and current entities
    - Provides them to the LLM alongside recent messages
    - Allows multiple parallel tool calls per iteration (create/update/archive)
    - Applies the resulting operations concurrently using the services layer
    - Extends `stored_entities` with created/updated entities and removes archived ones
    """
    tools = [create_key_entity, update_key_entity, delete_key_entity]

    # Load user profile and current entities
    user_profile = await get_user_profile(user_id)
    user_entities = await list_entities(user_id)

    current_time = datetime.now(
        user_profile.timezone if user_profile else None
    ).strftime("%I:%M %p")
    current_date = datetime.now(
        user_profile.timezone if user_profile else None
    ).strftime("%d %b %Y")

    prompt = KEY_ENTITY_EXTRACTION_PROMPT.format(
        time=current_time,
        date=current_date,
        user_profile=_format_user_profile(user_profile),
        existing_entities=_format_entities_as_markdown_table(user_entities),
    )

    # Recent conversation context
    chat_items = ctx.items
    user_messages = [
        item for item in chat_items if item.type == "message" and item.role == "user"
    ]
    last_user_messages = user_messages[-5:]
    last_user_messages_str = "Last 5 user messages:\n\n" + "\n\n\n".join(
        [f"{item.role}: {item.content}" for item in last_user_messages]
    )
    user_message_str = f"User's latest message: {new_message}"

    # Create chat context with the extraction prompt
    chat_ctx = ChatContext()
    chat_ctx.add_message(role="system", content=prompt)
    chat_ctx.add_message(role="user", content=last_user_messages_str)
    if stored_entities:
        chat_ctx.add_message(
            role="assistant",
            content="Previously extracted entities this session (markdown table):\n"
            + _format_entities_as_markdown_table(stored_entities),
        )
    chat_ctx.add_message(role="user", content=user_message_str)

    # Use a fast LLM with parallel tool calls enabled
    llm = openai.LLM(
        model="gpt-4.1", parallel_tool_calls=True, _strict_tool_schema=False
    )

    async with llm.chat(chat_ctx=chat_ctx, tools=tools, tool_choice="auto") as stream:
        tool_calls: list[FunctionToolCall] = []

        async for chunk in stream:
            if chunk.delta and chunk.delta.tool_calls:
                tool_calls.extend(chunk.delta.tool_calls)

    # Apply tool calls concurrently
    tasks: list[asyncio.Task] = []
    results: list[Any] = []

    for call in tool_calls:
        name = call.name
        args = json.loads(call.arguments) or {}

        if name == "create_key_entity":
            tasks.append(
                asyncio.create_task(
                    create_entity(
                        user_id=user_id,
                        entity_type=args.get("entity_type"),
                        data=args.get("entity_data") or {},
                        slug=args.get("slug"),
                        collection=args.get("collection", "misc"),
                        allow_upsert=bool(args.get("allow_upsert", False)),
                    )
                )
            )
        elif name == "update_key_entity":
            tasks.append(
                asyncio.create_task(
                    update_entity_by_slug(
                        user_id=user_id,
                        slug=args.get("slug"),
                        data=args.get("patch") or {},
                    )
                )
            )
        elif name == "delete_key_entity":
            tasks.append(
                asyncio.create_task(
                    archive_entity(
                        user_id=user_id,
                        entity_id=args.get("entity_id"),
                        reason=args.get("reason"),
                    )
                )
            )

    if tasks:
        results = await asyncio.gather(*tasks, return_exceptions=False)

    # Update in-memory session cache (stored_entities) based on results
    # We iterate through tool_calls and results in order
    idx = 0
    for call in tool_calls:
        name = call.name
        if name == "create_key_entity":
            created = results[idx]
            stored_entities.append(
                {
                    "id": getattr(created, "id", None) or getattr(created, "id", None),
                    "slug": getattr(created, "slug", None),
                    "collection": getattr(created, "collection", None),
                    "type": getattr(created, "type", None),
                    "data": getattr(created, "data", None),
                }
            )
            idx += 1
        elif name == "update_key_entity":
            updated = results[idx]
            if updated is not None:
                # Replace matching item in stored_entities if present; else append
                updated_id = getattr(updated, "id", None)
                replaced = False
                for i, e in enumerate(stored_entities):
                    if e.get("id") == str(updated_id):
                        stored_entities[i] = {
                            "id": str(updated_id),
                            "slug": getattr(updated, "slug", None),
                            "collection": getattr(updated, "collection", None),
                            "type": getattr(updated, "type", None),
                            "data": getattr(updated, "data", None),
                        }
                        replaced = True
                        break
                if not replaced:
                    stored_entities.append(
                        {
                            "id": str(updated_id),
                            "slug": getattr(updated, "slug", None),
                            "collection": getattr(updated, "collection", None),
                            "type": getattr(updated, "type", None),
                            "data": getattr(updated, "data", None),
                        }
                    )
            idx += 1
        elif name == "delete_key_entity":
            archived_ok = results[idx]
            if archived_ok and call.arguments and call.arguments.get("entity_id"):
                target_id = call.arguments.get("entity_id")
                stored_entities[:] = [
                    e for e in stored_entities if e.get("id") != target_id
                ]
            idx += 1


async def extract_and_store_entities(
    user_id: str,
    new_message: Any,
    stored_entities: list[Any],
    ctx: ChatContext,
) -> None:
    """
    Compatibility wrapper used by agents. Accepts a ChatMessage or string for new_message
    and delegates to the key-entity extractor.
    """
    message_text: str
    if hasattr(new_message, "text_content") and new_message.text_content:
        message_text = new_message.text_content
    else:
        message_text = str(new_message)

    await extract_and_store_key_entities(
        user_id=user_id,
        new_message=message_text,
        stored_entities=stored_entities,
        ctx=ctx,
    )
