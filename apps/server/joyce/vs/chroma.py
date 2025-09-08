from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import chromadb

from joyce.env import env

# Default instance (lazy initialization)
chroma_store = None


# Global instance for dependency injection
def create_chroma_store() -> ChromaStore:
    """Factory function for creating ChromaStore instances."""
    return ChromaStore(collection_name="memories")


def get_chroma_store() -> ChromaStore:
    """Get or create the default ChromaDB store instance."""
    global chroma_store  # noqa: PLW0603
    if chroma_store is None:
        chroma_store = create_chroma_store()
    return chroma_store


class ChromaStore:
    """Async-friendly ChromaDB wrapper for vector storage."""

    def __init__(self, collection_name: str = "memories"):
        """Initialize ChromaDB client with cloud configuration."""
        # Create cloud client
        self._client = chromadb.CloudClient(
            api_key=env.CHROMA_API_KEY,
            tenant=env.CHROMA_TENANT,
            database=env.CHROMA_DATABASE,
        )
        self._collection_name = collection_name

        # Initialize collection with metadata for user scoping
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "Joyce user memories"},
        )

    async def add_vectors(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
        documents: Optional[List[str]] = None,
    ) -> None:
        """Add vectors to the collection."""

        def _add():
            self._collection.add(
                ids=ids, embeddings=embeddings, metadatas=metadatas, documents=documents
            )

        await asyncio.to_thread(_add)

    async def query(
        self,
        embedding: List[float],
        n_results: int = 8,
        where: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Query vectors with optional filtering."""

        def _query():
            return self._collection.query(
                query_embeddings=[embedding], n_results=n_results, where=where
            )

        response = await asyncio.to_thread(_query)

        # Normalize response to list of hits
        hits = []
        ids = response.get("ids", [[]])[0]
        distances = response.get("distances", [[]])[0]
        metadatas = response.get("metadatas", [[]])[0]
        documents = (
            response.get("documents", [[]])[0]
            if "documents" in response
            else [None] * len(ids)
        )

        for i, hit_id in enumerate(ids):
            hits.append(
                {
                    "id": hit_id,
                    "distance": distances[i] if i < len(distances) else None,
                    "metadata": metadatas[i] if i < len(metadatas) else {},
                    "document": documents[i] if i < len(documents) else None,
                }
            )

        return hits

    async def delete(self, ids: List[str]) -> None:
        """Delete vectors by IDs."""

        def _delete():
            self._collection.delete(ids=ids)

        await asyncio.to_thread(_delete)

    async def update_vectors(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
        documents: Optional[List[str]] = None,
    ) -> None:
        """Update existing vectors."""

        def _update():
            self._collection.update(
                ids=ids, embeddings=embeddings, metadatas=metadatas, documents=documents
            )

        await asyncio.to_thread(_update)

    @staticmethod
    def create_metadata(
        user_id: str,
        memory_id: str,
        memory_type: str,
        tags: Optional[List[str]] = None,
        created_at: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create standardized metadata for vector storage."""
        if created_at is None:
            created_at = datetime.now(timezone.utc).isoformat()

        metadata = {
            "user_id": user_id,
            "memory_id": memory_id,
            "type": memory_type,
            "tags": ",".join(tags) if tags else "",
            "created_at": created_at,
        }

        # Merge additional data if provided
        if data:
            metadata.update(data)

        return metadata

    @staticmethod
    def distance_to_similarity(distance: float) -> float:
        """Convert ChromaDB distance to similarity score (0-1)."""
        # ChromaDB uses L2 distance by default
        # Convert to similarity where higher = better
        return max(0.0, 1.0 / (1.0 + distance))
