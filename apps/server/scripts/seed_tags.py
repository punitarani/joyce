"""
Seed tags for Joyce memory system.

Creates predefined tags with categories and synonyms for organizing memories.
"""

import asyncio
import sys
import traceback
from pathlib import Path

# Add parent directory to path so we can import joyce modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from joyce.db.client import SessionMaker
from joyce.db.schema.tag import Tag

# Predefined tags organized by category
TAGS = [
    # Wellness
    ("mood", "wellness", ["emotion", "feeling", "vibe"]),
    ("symptom", "wellness", ["pain", "discomfort", "issue"]),
    ("activity", "wellness", ["exercise", "workout", "movement"]),
    ("sleep", "wellness", ["rest", "bedtime", "wake"]),
    ("nutrition", "wellness", ["food", "diet", "meal", "drink"]),
    ("medication", "wellness", ["drug", "supplement", "pill"]),
    ("hydration", "wellness", ["water", "fluids", "drinks"]),
    ("stress", "wellness", ["anxiety", "pressure", "overwhelmed", "tension"]),
    # Lifestyle
    ("goal", "lifestyle", ["target", "aspiration", "resolution"]),
    ("routine", "lifestyle", ["habit", "schedule", "practice"]),
    ("task", "lifestyle", ["to-do", "action item", "reminder"]),
    ("achievement", "lifestyle", ["milestone", "progress", "win"]),
    ("challenge", "lifestyle", ["difficulty", "obstacle", "struggle"]),
    ("celebration", "lifestyle", ["party", "birthday", "event", "holiday"]),
    # Personal Context
    ("identity", "personal", ["bio", "name", "self", "profile"]),
    ("preference", "personal", ["likes", "dislikes", "favorite"]),
    ("relationship", "personal", ["friend", "family", "partner"]),
    ("work", "personal", ["job", "career", "study", "school"]),
    ("location", "personal", ["place", "city", "environment", "travel"]),
    ("weather", "personal", ["hot", "cold", "sunny", "rainy", "temperature"]),
    # Temporal
    ("day", "temporal", ["today", "daily log", "entry"]),
    ("week", "temporal", ["weekly summary", "reflection"]),
    ("month", "temporal", ["monthly summary", "trend"]),
    ("time-sensitive", "temporal", ["deadline", "urgent", "priority"]),
    # System
    ("conversation", "system", ["chat", "dialogue", "talk"]),
    ("note", "system", ["log", "entry", "record"]),
    ("question", "system", ["query", "ask", "request"]),
    ("feedback", "system", ["input", "correction", "opinion"]),
]


async def seed_tags():
    """Seed the database with predefined tags."""
    print("🏷️  Seeding Joyce tags...")

    try:
        async with SessionMaker() as session:
            created_count = 0
            updated_count = 0

            for tag_id, category, synonyms in TAGS:
                # Check if tag already exists
                existing_tag = await session.get(Tag, tag_id)

                if existing_tag:
                    # Update existing tag
                    existing_tag.category = category
                    existing_tag.synonyms = synonyms
                    session.add(existing_tag)
                    updated_count += 1
                    print(f"  ↻ Updated tag: {tag_id}")
                else:
                    # Create new tag
                    new_tag = Tag(
                        tag_id=tag_id,
                        name=tag_id.replace("-", " ").title(),
                        category=category,
                        synonyms=synonyms,
                    )
                    session.add(new_tag)
                    created_count += 1
                    print(f"  ✅ Created tag: {tag_id}")

            await session.commit()

        print(f"\n🎉 Tag seeding completed!")
        print(f"  • Created: {created_count} tags")
        print(f"  • Updated: {updated_count} tags")
        print(f"  • Total: {len(TAGS)} tags processed")
        return True

    except Exception as e:
        print(f"❌ Failed to seed tags: {e}")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(seed_tags())
    sys.exit(0 if success else 1)
