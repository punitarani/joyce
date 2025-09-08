"""
Universal vector search data models for Joyce.

Provides standardized data structures for vector search operations
that work across different vector stores (ChromaDB, Pinecone, etc.)
and follow common vector search patterns.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class VectorSearchDocument(BaseModel):
    """
    Universal document model for vector search operations.

    This model represents a single document/chunk with its vector representation
    and associated metadata, following standard vector search patterns.
    """

    id: str = Field(description="Unique identifier for the document")
    text: str = Field(description="Original text content of the document")
    embedding: Optional[List[float]] = Field(
        default=None, description="Vector representation of the text"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata for filtering and context",
    )
    score: Optional[float] = Field(
        default=None, description="Similarity score (higher is more similar, 0-1 range)"
    )
    distance: Optional[float] = Field(
        default=None, description="Distance from query vector (lower is more similar)"
    )

    @classmethod
    def from_chroma_result(
        cls,
        id: str,
        document: Optional[str],
        metadata: Optional[Dict[str, Any]],
        embedding: Optional[List[float]] = None,
        distance: Optional[float] = None,
    ) -> VectorSearchDocument:
        """Create from ChromaDB query result."""
        score = None
        if distance is not None:
            # Convert distance to similarity score (0-1, higher is better)
            score = 1.0 / (1.0 + distance)

        return cls(
            id=id,
            text=document or "",
            embedding=embedding,
            metadata=metadata or {},
            score=score,
            distance=distance,
        )


class VectorSearchQuery(BaseModel):
    """Query parameters for vector search operations."""

    text: Optional[str] = Field(default=None, description="Query text")
    embedding: Optional[List[float]] = Field(
        default=None, description="Query embedding"
    )
    top_k: int = Field(default=5, description="Number of results to return")
    filters: Dict[str, Any] = Field(
        default_factory=dict, description="Metadata filters to apply"
    )
    include_embeddings: bool = Field(
        default=False, description="Whether to include embeddings in results"
    )


class VectorSearchResponse(BaseModel):
    """Response from vector search operations."""

    query: VectorSearchQuery
    documents: List[VectorSearchDocument]
    total_found: int = Field(description="Total number of documents found")

    def to_rag_context(self, max_length: int = 2000) -> str:
        """
        Convert search results to RAG context string.

        This method formats the search results into a concise context string
        suitable for passing to an LLM for retrieval-augmented generation.
        """
        if not self.documents:
            return "No relevant information found."

        context_parts = []
        current_length = 0

        for i, doc in enumerate(self.documents):
            # Create a formatted entry
            score_info = f" (score: {doc.score:.3f})" if doc.score else ""
            entry = f"[{i + 1}] {doc.text.strip()}{score_info}"

            # Check if adding this entry would exceed max_length
            if current_length + len(entry) > max_length and context_parts:
                context_parts.append(f"... ({len(self.documents) - i} more results)")
                break

            context_parts.append(entry)
            current_length += len(entry) + 2  # +2 for newlines

        return "\n\n".join(context_parts)
