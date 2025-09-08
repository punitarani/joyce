from __future__ import annotations

import asyncio

from livekit.agents import RunContext, function_tool

from joyce.agent.user import UserData
from joyce.db.schema.memory import MemoryCreate
from joyce.types import MemoryTag, MemoryType
from joyce.vs import insert_memories, search_memories, search_memories_ranked

from .utils import get_user_id_from_context


@function_tool()
async def search_memory(
    context: RunContext[UserData],
    query: str,
    limit: int = 10,
    memory_type: MemoryType | None = None,
) -> str:
    """
    Search user memories using semantic similarity.

    Args:
        query: Natural language search query
        limit: Maximum number of results to return (default 10)
        memory_type: Optional filter - one of: happenings, reflections, observations

    Example:
    ```json
    {
      "query": "What are my dietary restrictions?",
      "limit": 5,
      "memory_type": "reflections"
    }
    ```
    """

    # Send a verbal status update to the user after a short delay
    async def _speak_status_update(delay: float = 0.5):
        await asyncio.sleep(delay)
        await context.session.generate_reply(
            instructions=f"""
            You are searching the knowledge base for \"{query}\" but it is taking a little while.
            Update the user on your progress, but be very brief.
        """
        )

    status_update_task = asyncio.create_task(_speak_status_update(0.5))

    try:
        user_id = get_user_id_from_context(context)

        # Handle empty query by using a default search term
        if not query or query.strip() == "":
            query = "user information memories"

        # Build filters
        filters = {}
        if memory_type:
            filters["type"] = memory_type.value

        memories = await search_memories(
            query=query,
            user_id=user_id,
            top_k=limit,
            filters=filters,
        )

        # Cancel status update if search completed before timeout
        status_update_task.cancel()

        if memories == "No relevant information found.":
            return f"I couldn't find any relevant memories for: {query}"

        return memories.to_rag_context(max_length=8000)

    except Exception:
        status_update_task.cancel()
        return "I had trouble searching your memories. Please try again."


@function_tool()
async def search_memory_ranked(
    context: RunContext[UserData],
    query: str,
    limit: int = 10,
    memory_type: MemoryType | None = None,
) -> str:
    """
    Search user memories with time-aware ranking (recent memories prioritized).

    Args:
        query: Natural language search query
        limit: Maximum number of results to return (default 10)
        memory_type: Optional filter - one of: happenings, reflections, observations

    Example:
    ```json
    {
      "query": "recent health updates",
      "limit": 5,
      "memory_type": "happenings"
    }
    ```
    """

    # Send a verbal status update to the user after a short delay
    async def _speak_status_update(delay: float = 0.5):
        await asyncio.sleep(delay)
        await context.session.generate_reply(
            instructions=f"""
            You are searching the knowledge base for \"{query}\" but it is taking a little while.
            Update the user on your progress, but be very brief.
        """
        )

    status_update_task = asyncio.create_task(_speak_status_update(0.5))

    try:
        user_id = get_user_id_from_context(context)

        # Handle empty query by using a default search term
        if not query or query.strip() == "":
            query = "user information memories"

        # Build filters
        filters = {}
        if memory_type:
            filters["type"] = memory_type.value

        memories = await search_memories_ranked(
            query=query,
            user_id=user_id,
            top_k=limit,
            filters=filters,
        )

        # Cancel status update if search completed before timeout
        status_update_task.cancel()

        if memories == "No relevant information found.":
            return f"I couldn't find any relevant memories for: {query}"

        return memories.to_rag_context(max_length=8000)

    except Exception:
        status_update_task.cancel()
        return "I had trouble searching your memories. Please try again."


@function_tool()
async def store_memory(
    context: RunContext[UserData],
    memory_text: str,
    memory_data: object,
    memory_type: MemoryType = MemoryType.REFLECTIONS,
    tags: list[MemoryTag] | None = None,
) -> str:
    """
    Store a user memory.

    Args:
        memory_text: The memory content to store
        memory_data: Optional structured data associated with the memory
        memory_type: Type of memory - one of: happenings, reflections, observations (default: reflections)
        tags: Optional tags from the MemoryTag enum

    Example:
    ```json
    {
      "memory_text": "I prefer oat milk in coffee",
      "memory_type": "reflections",
      "memory_data": {"preference_strength": "strong"},
      "tags": ["eating", "content"]
    }
    ```
    """
    try:
        user_id = get_user_id_from_context(context)

        # Create memory object
        memory = MemoryCreate(
            user_id=user_id,
            type=memory_type.value,
            text=memory_text,
            data=memory_data,
            tags=tags or [],
        )

        await insert_memories([memory])
        return "Memory stored successfully."

    except Exception:
        return "Failed to store memory."


__all__ = [
    "search_memory",
    "store_memory",
]
