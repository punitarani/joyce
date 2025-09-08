from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from chromadb.errors import InternalError
from sqlalchemy import insert
from sqlalchemy.exc import OperationalError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from joyce.db.client import SessionMaker
from joyce.db.schema.memory import Memory, MemoryCreate, MemoryWithEmbeddingCreate
from joyce.lm.embed import embed_texts

from .chroma import get_chroma_store


@retry(
    retry=retry_if_exception_type((OperationalError, InternalError)),
    stop=stop_after_attempt(3),
    wait=wait_fixed(wait=1),
)
async def insert_memories(memories: List[MemoryCreate]) -> list[Memory]:
    """
    Insert memories into the database and the vector store.
    """
    if not memories:
        return []

    chroma = get_chroma_store()

    embeddings = await embed_texts([memory.text for memory in memories])

    memories_with_embeddings = [
        MemoryWithEmbeddingCreate(
            user_id=memory.user_id,
            type=memory.type,
            text=memory.text,
            data=memory.data,
            tags=memory.tags,
            deleted=memory.deleted,
            embedding=embedding,
        )
        for memory, embedding in zip(memories, embeddings)
    ]

    inserted_memories = []
    async with SessionMaker() as session:
        stmt = (
            insert(Memory)
            .values([memory.serialize() for memory in memories_with_embeddings])
            .returning(Memory)
        )
        result = await session.execute(stmt)
        inserted_memories = result.scalars().all()
        await session.commit()

    # Create metadata ensuring it's never empty for ChromaDB
    metadatas = []
    for memory in inserted_memories:
        metadata = {
            **(memory.data or {}),
            "user_id": str(memory.user_id),
            "memory_id": str(memory.id),
            "type": memory.type,
            "tags": ",".join(memory.tags) if memory.tags else "",
            "created_at": (
                memory.created_at.isoformat()
                if memory.created_at
                else datetime.now(timezone.utc).isoformat()
            ),
        }
        metadatas.append(metadata)

    await chroma.add_vectors(
        ids=[str(memory.id) for memory in inserted_memories],
        embeddings=[memory.embedding for memory in inserted_memories],
        metadatas=metadatas,
        documents=[memory.text for memory in inserted_memories],
    )

    return list(inserted_memories)
