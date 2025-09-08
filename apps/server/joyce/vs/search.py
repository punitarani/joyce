from __future__ import annotations

from typing import Any, Dict, List, Optional

from joyce.lm.embed import embed_texts
from joyce.vs import get_chroma_store
from joyce.vs.models import (
    VectorSearchDocument,
    VectorSearchQuery,
    VectorSearchResponse,
)
from joyce.vs.similarity import calculate_hybrid_score


async def search_memories(
    query: str,
    user_id: str,
    top_k: int = 5,
    filters: Optional[Dict[str, Any]] = None,
) -> VectorSearchResponse:
    """
    Primary memory search function using universal data models.

    This function provides a simplified, standardized interface for memory search
    that follows vector search best practices and returns data ready for RAG.

    Args:
        query: Search query text
        user_id: User ID for scoping
        top_k: Number of results to return
        filters: Optional metadata filters (e.g., {"type": "personal"})

    Returns:
        VectorSearchResponse with standardized document results
    """
    search_query = VectorSearchQuery(
        text=query,
        top_k=top_k,
        filters=filters or {},
    )

    # Simple vector search (no reranking) scoped by user
    chroma = get_chroma_store()
    query_embeddings = await embed_texts([query])
    query_embedding = query_embeddings[0]

    where_clause = {"user_id": user_id}
    raw_results = await chroma.query(
        embedding=query_embedding, n_results=top_k, where=where_clause
    )

    # Optional simple filtering by type/tags
    filtered_results = []
    for mem in raw_results or []:
        if not filters or "type" not in filters:
            filtered_results.append(mem)
            continue

        metadata = mem.get("metadata", {})
        memory_type = metadata.get("type")
        memory_tags = metadata.get("tags", "")
        required_type = filters.get("type")

        if isinstance(memory_tags, list):
            available_tags = [
                str(tag).strip() for tag in memory_tags if str(tag).strip()
            ]
        else:
            available_tags = [
                tag.strip() for tag in str(memory_tags).split(",") if tag.strip()
            ]

        if memory_type == required_type or required_type in available_tags:
            filtered_results.append(mem)

    documents: List[VectorSearchDocument] = []
    for mem in filtered_results:
        documents.append(
            VectorSearchDocument.from_chroma_result(
                id=mem.get("id"),
                document=mem.get("document"),
                metadata=mem.get("metadata"),
                distance=mem.get("distance"),
            )
        )

    return VectorSearchResponse(
        query=search_query,
        documents=documents,
        total_found=len(documents),
    )


async def search_memories_ranked(
    user_id: str,
    query: str,
    top_k: int = 6,
    filters: Optional[Dict[str, Any]] = None,
    candidate_multiplier: int = 3,
) -> List[VectorSearchDocument]:
    """
    Perform semantic search with time-aware ranking.

    Args:
        user_id: User ID for scoping
        query: Search query text
        top_k: Number of final results to return
        filters: Optional metadata filters (e.g., {"type": "personal"})
        candidate_multiplier: Fetch top_k * multiplier candidates for reranking
        tag_filter: Optional list of tags to filter by

    Returns:
        List of ranked search results with memory information
    """
    chroma = get_chroma_store()

    # Generate query embedding
    query_embeddings = await embed_texts([query])
    query_embedding = query_embeddings[0]

    # Build where clause for user scoping only
    # Note: Tag filtering is done post-query since ChromaDB doesn't support
    # complex string operations on comma-separated tag strings
    where_clause = {"user_id": user_id}

    # Retrieve candidates from ChromaDB
    n_candidates = top_k * candidate_multiplier
    memories = await chroma.query(
        embedding=query_embedding, n_results=n_candidates, where=where_clause
    )

    if not memories:
        return []

    # Filter candidates by provided filters (supports simple "type"/tags filtering)
    filtered_memories = []
    for memory in memories:
        metadata = memory.get("metadata", {})
        memory_type = metadata.get("type")
        memory_tags = metadata.get("tags", "")

        if filters and "type" in filters:
            required_type = filters.get("type")

            # Normalize available tags to a list of strings
            if isinstance(memory_tags, list):
                available_tags = [
                    str(tag).strip() for tag in memory_tags if str(tag).strip()
                ]
            else:
                available_tags = [
                    tag.strip() for tag in str(memory_tags).split(",") if tag.strip()
                ]

            # Keep if the required type matches either explicit type or tags
            if memory_type != required_type and required_type not in available_tags:
                continue

        filtered_memories.append(memory)

    # Prepare VectorSearchDocuments with hybrid scoring
    results: List[VectorSearchDocument] = []
    for mem in filtered_memories:
        metadata = mem.get("metadata") or {}
        distance = mem.get("distance")
        document = mem.get("document")

        created_at = metadata.get("created_at") if metadata else None
        if created_at is not None:
            score = calculate_hybrid_score(distance=distance, created_at=created_at)
        else:
            score = 1.0 / (1.0 + distance)

        doc = VectorSearchDocument.from_chroma_result(
            id=mem.get("id"),
            document=document,
            metadata=metadata,
            distance=distance,
        )
        # Overwrite score with hybrid score
        doc.score = score
        results.append(doc)

    # Sort by score (descending - higher is better)
    results.sort(key=lambda d: (d.score if d.score is not None else 0.0), reverse=True)

    # Return top K results
    return results[:top_k]
