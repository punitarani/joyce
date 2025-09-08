"""
Test script to validate the memory system is working correctly.

Usage:
    python scripts/test_memory.py
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path so we can import joyce modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from joyce.agent.memory import recall_memories, store_memory
from joyce.db.utils import get_user


async def test_memory_system():
    """Test the memory storage and retrieval system."""
    print("🧠 Testing Joyce Memory System...")

    try:
        # Get user ID
        user_id = get_user()
        print(f"✅ User ID: {user_id}")

        # Test 1: Store a test memory
        print("\n📝 Test 1: Storing a test memory...")
        memory_id = await store_memory(
            memory_type="test",
            payload={
                "message": "This is a test memory",
                "test_data": {"value": 42, "status": "active"},
            },
            title="Test Memory",
            summary="A test memory to validate the system is working",
            tags=["test", "validation"],
        )

        if memory_id:
            print(f"✅ Memory stored successfully with ID: {memory_id}")
        else:
            print("❌ Failed to store memory")
            return False

        # Test 2: Recall the memory
        print("\n🔍 Test 2: Recalling test memories...")
        memories = await recall_memories(query="test memory validation", top_k=3)

        if memories:
            print(f"✅ Found {len(memories)} memories:")
            for i, memory in enumerate(memories, 1):
                memory_data = memory.get("memory", {}) if memory.get("memory") else {}
                title = (
                    memory_data.get("title", "Untitled") if memory_data else "No Data"
                )
                summary = memory_data.get("summary", "") if memory_data else ""
                print(f"  {i}. {title} - {summary}")
                # Debug: print the structure
                print(
                    f"     Debug - Memory structure: {list(memory.keys()) if isinstance(memory, dict) else type(memory)}"
                )
                if isinstance(memory, dict) and "memory" in memory:
                    print(f"     Debug - Memory field content: {memory['memory']}")
                    print(f"     Debug - Memory field type: {type(memory['memory'])}")
        else:
            print("❌ No memories found")
            return False

        # Test 3: Store a food intake memory (like the agent would)
        print("\n🍎 Test 3: Storing food intake memory...")
        food_memory_id = await store_memory(
            memory_type="food_intake",
            payload={
                "food_item": "apple",
                "quantity": "1 medium",
                "time": "afternoon snack",
                "meal_type": "snack",
            },
            title="Food: apple",
            summary="Consumed apple at afternoon snack",
            tags=["nutrition", "food"],
        )

        if food_memory_id:
            print(f"✅ Food memory stored with ID: {food_memory_id}")
        else:
            print("❌ Failed to store food memory")
            return False

        # Test 4: Search for food memories
        print("\n🔍 Test 4: Searching for food memories...")
        food_memories = await recall_memories(
            query="apple food snack", memory_type="food_intake", top_k=5
        )

        if food_memories:
            print(f"✅ Found {len(food_memories)} food memories:")
            for i, memory in enumerate(food_memories, 1):
                memory_data = memory.get("memory", {}) if memory.get("memory") else {}
                payload = memory_data.get("payload", {}) if memory_data else {}
                food_item = (
                    payload.get("food_item", "Unknown") if payload else "No Data"
                )
                summary = memory_data.get("summary", "") if memory_data else ""
                print(f"  {i}. {food_item} - {summary}")
                # Debug
                print(
                    f"     Debug - Memory field: {memory['memory'] if 'memory' in memory else 'Missing'}"
                )
        else:
            print("❌ No food memories found")

        print("\n🎉 Memory system test completed successfully!")
        return True

    except Exception as e:
        print(f"❌ Memory system test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_memory_system())
    sys.exit(0 if success else 1)
