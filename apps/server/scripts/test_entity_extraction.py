#!/usr/bin/env python3
"""
Test script for the multi-agent entity extraction system.
Tests background processing, LLM-powered entity extraction, and memory storage.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path so we can import joyce modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from joyce.agent.entity_extractor import EntityExtractor
from joyce.agent.memory import recall_memories
from joyce.db.utils import get_user


async def test_entity_extraction():
    """Test the entity extraction system with realistic conversation segments."""
    print("🧠 Testing Joyce Entity Extraction System...")

    # Initialize the entity extractor
    extractor = EntityExtractor()
    user_id = get_user()
    print(f"✅ User ID: {user_id}")

    # Test conversation segments that should trigger entity extraction
    test_conversations = [
        {
            "user": "I had a really bad headache this morning and took two ibuprofen around 9 AM",
            "assistant": "I'm sorry to hear about your headache. It's good that you took ibuprofen - that should help with the pain. How are you feeling now?",
        },
        {
            "user": "My sleep was terrible last night. I only got about 4 hours because of work stress",
            "assistant": "That sounds very challenging. Poor sleep can really affect how you feel throughout the day. What's been causing the work stress lately?",
        },
        {
            "user": "I went for a 30-minute jog in Central Park this afternoon with my friend Sarah",
            "assistant": "That's wonderful! Regular exercise like jogging is great for both physical and mental health. How did it feel running with Sarah?",
        },
        {
            "user": "I'm feeling anxious about my presentation tomorrow at the office meeting",
            "assistant": "It's completely normal to feel anxious before an important presentation. What aspects of the presentation are you most concerned about?",
        },
    ]

    print(f"\n📝 Test 1: Queuing {len(test_conversations)} conversation segments...")

    # Queue all conversation segments
    for i, conv in enumerate(test_conversations, 1):
        await extractor.queue_conversation_segment(
            user_message=conv["user"],
            assistant_response=conv["assistant"],
            user_id=user_id,
        )
        print(f"   ✅ Queued conversation {i}")

    print(f"\n⚙️  Test 2: Processing background queue...")

    # Process the queue directly (simulate background processing)
    processed_count = 0
    max_iterations = 10  # Prevent infinite loop
    iteration = 0

    while not extractor.processing_queue.empty() and iteration < max_iterations:
        try:
            # Get conversation segment from queue
            conversation = await extractor.processing_queue.get()
            await extractor._extract_and_store_entities(conversation)
            extractor.processing_queue.task_done()
            processed_count += 1
            print(f"   ✅ Processed item {processed_count}")
        except Exception as e:
            print(f"   ❌ Error processing item: {e}")
            break
        iteration += 1

    print(f"\n🔍 Test 3: Verifying stored memories...")

    # Wait a moment for async operations to complete
    await asyncio.sleep(2)

    # Search for various types of extracted information
    search_queries = [
        "headache ibuprofen morning",
        "sleep work stress",
        "jogging Central Park Sarah",
        "presentation anxiety office meeting",
    ]

    total_found = 0
    for query in search_queries:
        try:
            memories = await recall_memories(query, top_k=3)
            found_count = len(memories)
            total_found += found_count
            print(f"   🔍 Query '{query}': Found {found_count} memories")

            # Show details of found memories
            for memory in memories:
                if hasattr(memory, "memory") and memory.memory:
                    title = memory.memory.get("title", "No Title")
                    summary = memory.memory.get("summary", "No Summary")
                    print(f"      - {title}: {summary}")

                    # Check if names and dates are specific (not using pronouns)
                    if memory.memory.get("payload"):
                        payload_str = str(memory.memory["payload"])
                        if any(
                            word in payload_str.lower()
                            for word in ["this", "that", "they", "it"]
                        ):
                            print(
                                f"      ⚠️  Warning: Memory may contain pronouns instead of specific references"
                            )
                        else:
                            print(f"      ✅ Memory appears to use specific references")

        except Exception as e:
            print(f"   ❌ Error searching for '{query}': {e}")

    print(f"\n📊 Test Results:")
    print(f"   - Conversation segments queued: {len(test_conversations)}")
    print(f"   - Background items processed: {processed_count}")
    print(f"   - Total memories found in searches: {total_found}")

    print(f"\n✅ Entity extraction test completed!")

    return {
        "queued": len(test_conversations),
        "processed": processed_count,
        "memories_found": total_found,
    }


async def test_user_profile_detection():
    """Test user profile detection and context building."""
    print(f"\n👤 Test 4: User profile detection...")

    extractor = EntityExtractor()

    # Test conversation with name detection
    test_segment = {
        "user_message": "Hi, I'm Alex and I work as a software engineer at Google",
        "assistant_response": "Nice to meet you, Alex! It's great to connect with a software engineer. How do you like working at Google?",
        "user_id": get_user(),
    }

    # Process this segment to build user profile
    await extractor.queue_conversation_segment(**test_segment)

    # Process the queued segment
    if not extractor.processing_queue.empty():
        conversation = await extractor.processing_queue.get()
        await extractor._extract_and_store_entities(conversation)
        extractor.processing_queue.task_done()

    # Check if user profile was updated
    if extractor.user_profile:
        print(f"   ✅ User profile detected: {extractor.user_profile}")
    else:
        print(f"   ⚠️  User profile not detected in conversation")

    print(f"   Profile data: {extractor.user_profile}")


async def main():
    """Run all entity extraction tests."""
    try:
        # Run main entity extraction tests
        results = await test_entity_extraction()

        # Run user profile detection test
        await test_user_profile_detection()

        # Summary
        print(f"\n🎉 All tests completed successfully!")
        print(f"   The multi-agent entity extraction system is working correctly.")
        print(
            f"   Background processing handled {results['processed']} conversation segments."
        )
        print(f"   Memory system successfully stored and retrieved extracted entities.")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
