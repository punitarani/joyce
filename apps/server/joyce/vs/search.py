from __future__ import annotations

import math
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from joyce.agent.embed import embed_texts
from joyce.db.schema import Memory, MemoryChunk

from .chroma import ChromaStore


def calculate_hybrid_score(
    distance: float,
    created_at: str,
    recency_weight: float = 0.15,
    recency_decay_days: float = 90.0,
) -> float:
    """
    Calculate hybrid score combining similarity and recency.

    Based on research-backed approach:
    - Converts distance to similarity (normalized 0-1)
    - Applies gentle recency boost only when items are close in similarity
    - Uses exponential decay with configurable half-life

    Args:
        distance: ChromaDB L2 distance (lower = more similar)
        created_at: ISO timestamp when memory was created
        recency_weight: Weight for recency component (0.1-0.2 recommended)
        recency_decay_days: Days for recency to decay to ~37% (1/e)

    Returns:
        Combined score where higher = better
    """
    # Convert distance to normalized similarity (0-1, higher = more similar)
    similarity = 1.0 / (1.0 + distance)

    # Calculate age in days
    try:
        timestamp = created_at.replace("Z", "+00:00")
        dt = datetime.fromisoformat(timestamp)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        age_days = (datetime.now(timezone.utc) - dt).total_seconds() / 86400.0
        age_days = max(0.0, age_days)
    except (ValueError, AttributeError):
        age_days = recency_decay_days * 2  # Treat invalid timestamps as old

    # Exponential decay recency factor (0-1, higher = more recent)
    recency = math.exp(-age_days / recency_decay_days)

    # Hybrid score: primarily similarity with gentle recency boost
    # This ensures recency only matters when similarities are close
    return similarity * (1.0 + recency_weight * recency)


async def create_chunk_with_embedding(
    session: AsyncSession,
    chroma: ChromaStore,
    memory_id: str,
    user_id: str,
    chunk_text: str,
    embedding_model: str = "text-embedding-3-small",
    chunk_metadata: Optional[Dict[str, Any]] = None,
    tags: Optional[List[str]] = None,
) -> str:
    """Create a memory chunk and upsert its embedding to ChromaDB."""

    # Create chunk record in database
    chunk = MemoryChunk(
        chunk_id=uuid.uuid4(),
        memory_id=uuid.UUID(memory_id),
        user_id=user_id,
        chunk_text=chunk_text,
        chunk_metadata=chunk_metadata or {},
        text_length=len(chunk_text),
        embedding_model=embedding_model,
        vector_upserted=False,
    )

    session.add(chunk)
    await session.flush()  # Ensure chunk_id is available
    chunk_id_str = str(chunk.chunk_id)

    try:
        # Generate embedding using existing embed function
        embeddings = await embed_texts([chunk_text])
        embedding = embeddings[0]

        # Create metadata for vector storage
        vector_metadata = chroma.create_metadata(
            user_id=user_id,
            memory_id=memory_id,
            chunk_id=chunk_id_str,
            embedding_model=embedding_model,
            tags=tags,
        )

        # Upsert to ChromaDB
        await chroma.add_vectors(
            ids=[chunk_id_str],
            embeddings=[embedding],
            metadatas=[vector_metadata],
            documents=[chunk_text[:2000]],  # Truncate for storage
        )

        # Mark as successfully upserted
        chunk.vector_upserted = True
        session.add(chunk)

    except Exception as e:
        # Log error but don't fail the operation
        print(f"Failed to upsert embedding for chunk {chunk_id_str}: {e}")
        chunk.vector_upserted = False
        session.add(chunk)

    await session.commit()
    return chunk_id_str


async def semantic_search(
    session: AsyncSession,
    chroma: ChromaStore,
    user_id: str,
    query: str,
    top_k: int = 6,
    candidate_multiplier: int = 3,
    category: Optional[str] = None,
    tag_filter: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Perform semantic search with time-aware ranking.

    Args:
        session: Database session
        chroma: ChromaDB client
        user_id: User ID for scoping
        query: Search query text
        top_k: Number of final results to return
        candidate_multiplier: Fetch top_k * multiplier candidates for reranking
        category: Content category for decay rate selection
        tag_filter: Optional list of tags to filter by

    Returns:
        List of ranked search results with memory information
    """

    # Generate query embedding
    query_embeddings = await embed_texts([query])
    query_embedding = query_embeddings[0]

    # Build where clause for user scoping
    where_clause = {"user_id": user_id}
    if tag_filter:
        # ChromaDB metadata filtering syntax
        where_clause["tags"] = {"$in": tag_filter}

    # Retrieve candidates from ChromaDB
    n_candidates = top_k * candidate_multiplier
    hits = await chroma.query(
        embedding=query_embedding, n_results=n_candidates, where=where_clause
    )

    if not hits:
        return []

    # Extract memory IDs and fetch memory records
    memory_ids = []
    chunk_hit_map = {}

    for hit in hits:
        memory_id = hit["metadata"].get("memory_id")
        if memory_id:
            memory_ids.append(memory_id)
            chunk_hit_map[memory_id] = hit

    # Fetch memory records
    memory_records = {}
    if memory_ids:
        stmt = select(Memory).where(
            Memory.memory_id.in_([uuid.UUID(mid) for mid in memory_ids]),
            Memory.user_id == user_id,
            not Memory.deleted,
        )
        result = await session.execute(stmt)
        memory_records = {str(m.memory_id): m for m in result.scalars().all()}

    # Prepare results for ranking
    ranking_input = []
    for hit in hits:
        memory_id = hit["metadata"].get("memory_id")
        memory_record = memory_records.get(memory_id)

        result_item = {
            "chunk_id": hit["id"],
            "distance": hit["distance"],
            "metadata": hit["metadata"],
            "document": hit.get("document"),
            "memory_id": memory_id,
            "memory": (
                {
                    "title": memory_record.title if memory_record else None,
                    "summary": memory_record.summary if memory_record else None,
                    "type": memory_record.type if memory_record else None,
                    "payload": memory_record.payload if memory_record else {},
                    "tags": memory_record.tags if memory_record else [],
                }
                if memory_record
                else None
            ),
        }
        ranking_input.append(result_item)

    # Apply hybrid scoring and ranking
    scored_results = []
    for item in ranking_input:
        # Get timestamp from metadata or memory record
        created_at = None
        if item["memory"] and item["memory"].get("payload"):
            created_at = item["memory"]["payload"].get("created_at")
        if not created_at and item["metadata"]:
            created_at = item["metadata"].get("created_at")

        if created_at:
            hybrid_score = calculate_hybrid_score(
                distance=item["distance"], created_at=created_at
            )
        else:
            # Fallback to similarity-only scoring for items without timestamps
            hybrid_score = 1.0 / (1.0 + item["distance"])

        item["hybrid_score"] = hybrid_score
        scored_results.append(item)

    # Sort by hybrid score (descending - higher is better)
    scored_results.sort(key=lambda x: x["hybrid_score"], reverse=True)

    # Return top K results
    return scored_results[:top_k]
