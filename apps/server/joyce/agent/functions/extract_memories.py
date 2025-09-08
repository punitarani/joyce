from __future__ import annotations

from datetime import datetime

from livekit.agents import ChatContext, function_tool
from livekit.agents.llm import FunctionToolCall
from livekit.plugins import openai

from joyce.agent.prompts import ENTITY_EXTRACTION_PROMPT
from joyce.agent.user import get_user_profile
from joyce.db.schema.memory import BaseMemoryCreate, MemoryCreate
from joyce.vs.insert import insert_memories


async def extract_and_store_memories_func(memory: BaseMemoryCreate) -> BaseMemoryCreate:
    return BaseMemoryCreate(**memory.model_dump())


extract_and_store_memories_tool = function_tool(
    extract_and_store_memories_func,
    name="extract_entity",
    description="Call this function when user's message contains information to store in memory.",
)


async def extract_and_store_memories(
    user_id: str,
    new_message: str,
    stored_entities: list[BaseMemoryCreate],
    ctx: ChatContext,
) -> None:
    tools = [extract_and_store_memories_tool]

    # get user profile
    user_profile = await get_user_profile(user_id)

    current_time = datetime.now(user_profile.timezone).strftime("%I:%M %p")
    current_date = datetime.now(user_profile.timezone).strftime("%d %b %Y")

    extraction_prompt = ENTITY_EXTRACTION_PROMPT.format(
        user_bio=user_profile.bio, time=current_time, date=current_date
    )
    previous_extracted_entities_str = format_stored_memories(stored_entities)
    user_message_str = f"User's latest message: {new_message}"

    # Get the last few messages in reverse order
    chat_items = ctx.items
    user_messages = [
        item for item in chat_items if item.type == "message" and item.role == "user"
    ]
    last_user_messages = user_messages[-5:]
    last_user_messages_str = "Last 5 user messages:\n\n" + "\n\n\n".join(
        [f"{item.role}: {item.content}" for item in last_user_messages]
    )

    # Use fast LLM for entity extraction
    llm = openai.LLM(
        model="gpt-4.1", parallel_tool_calls=True, _strict_tool_schema=False
    )

    # Create chat context with the extraction prompt
    chat_ctx = ChatContext()
    chat_ctx.add_message(role="system", content=extraction_prompt)
    chat_ctx.add_message(role="user", content=last_user_messages_str)
    chat_ctx.add_message(role="assistant", content=previous_extracted_entities_str)
    chat_ctx.add_message(role="user", content=user_message_str)

    async with llm.chat(chat_ctx=chat_ctx, tools=tools, tool_choice="auto") as stream:
        tool_calls: list[FunctionToolCall] = []

        async for chunk in stream:
            if chunk.delta and chunk.delta.tool_calls:
                tool_calls.extend(chunk.delta.tool_calls)

        # Process extracted tool calls
        inserted_memories = await insert_memories(
            memories=[
                MemoryCreate.from_tool_call_arguments(
                    user_id=user_id, arguments=tool_call.arguments
                )
                for tool_call in tool_calls
            ]
        )

        stored_entities.extend(inserted_memories)


def format_stored_memories(stored_memories: list[BaseMemoryCreate]) -> str:
    formatted_memories = []
    for memory in stored_memories:
        memory_str = f"type: {memory.type}, text: {memory.text}, data: {memory.data}, tags: {memory.tags}"
        formatted_memories.append(memory_str)
    return "\n\t- " + "\n\t- ".join(formatted_memories)
