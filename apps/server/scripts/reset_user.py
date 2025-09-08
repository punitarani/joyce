"""
Reset user data by deleting all entities owned by a user.

Cleans both database records (memories) and corresponding vectors
from ChromaDB collection.

Usage:
    python scripts/reset_user.py
    # or
    uv run python scripts/reset_user.py
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path so we can import joyce modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import delete, select

from joyce.db.client import SessionMaker
from joyce.db.schema.memory import Memory
from joyce.db.schema.user_entities import UserEntity
from joyce.db.utils import get_user
from joyce.vs import get_chroma_store


async def reset_user() -> None:
    """Reset all data for the current user."""
    try:
        user_id = get_user()
        print(f"🔄 Resetting all data for user_id: {user_id}")

        async with SessionMaker() as session:
            # First, get all memory IDs with embeddings for ChromaDB deletion
            chunk_result = await session.execute(
                select(Memory.id).where(
                    Memory.user_id == user_id, Memory.embedding.is_not(None)
                )
            )
            chunk_ids = [str(row[0]) for row in chunk_result.fetchall()]

            if chunk_ids:
                print(
                    "📋 Found %s vector chunks to delete from ChromaDB", len(chunk_ids)
                )

                # Delete vectors from ChromaDB
                chroma = get_chroma_store()
                await chroma.delete(chunk_ids)
                print("🗑️  Deleted %s vectors from ChromaDB", len(chunk_ids))

            # Delete database records
            memories_result = await session.execute(
                delete(Memory).where(Memory.user_id == user_id)
            )
            print("🧠 Deleted %s memories", memories_result.rowcount)

            # Delete user entities
            entities_result = await session.execute(
                delete(UserEntity).where(UserEntity.user_id == user_id)
            )
            print("📝 Deleted %s entities", entities_result.rowcount)

            await session.commit()

        print(f"✅ User data reset completed successfully for {user_id}")
        print("   - Database: %s memories", memories_result.rowcount)
        print("   - Database: %s entities", entities_result.rowcount)
        print("   - Vector store: %s embeddings", len(chunk_ids))

    except Exception as e:
        print(f"❌ Failed to reset user data: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(reset_user())
