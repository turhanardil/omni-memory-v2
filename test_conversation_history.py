# test_conversation_history.py
"""
Test script to verify Azure Search conversation history is working properly.
Run this to check if data is being stored and retrieved correctly.
"""

import os
import time
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from conversation_tracker import ConversationTracker
import json

load_dotenv()

def test_azure_search_connection():
    """Test basic Azure Search connection."""
    print("🔍 Testing Azure Search Connection...")
    
    try:
        client = SearchClient(
            os.environ["AZURE_SEARCH_ENDPOINT"],
            "conversation-history",
            AzureKeyCredential(os.environ["AZURE_SEARCH_API_KEY"])
        )
        
        # Try a simple search
        results = client.search(
            search_text="*",
            top=1
        )
        
        # Force evaluation
        result_list = list(results)
        print("✅ Azure Search connection successful!")
        return True
        
    except Exception as e:
        print(f"❌ Azure Search connection failed: {e}")
        return False

def check_conversation_data(thread_id: str = "test_thread"):
    """Check what conversation data exists for a thread."""
    print(f"\n📊 Checking conversation data for thread: {thread_id}")
    
    try:
        tracker = ConversationTracker(thread_id)
        
        # Get all topics
        topics = tracker.get_all_topics()
        print(f"\n📌 Topics discussed: {len(topics)}")
        for topic in topics[:5]:  # Show first 5
            print(f"   - {topic}")
            last_time = tracker.get_last_discussion_time(topic)
            if last_time:
                print(f"     Last discussed: {last_time}")
        
        # Get user preferences
        prefs = tracker.get_user_preferences()
        print(f"\n⚙️  User preferences: {len(prefs)}")
        for key, value in list(prefs.items())[:5]:  # Show first 5
            print(f"   - {key}: {value}")
        
        # Check shared facts
        if topics:
            topic = topics[0]
            facts = tracker.get_shared_facts(topic)
            print(f"\n📝 Facts shared about '{topic}': {len(facts)}")
            for fact in facts[:3]:  # Show first 3
                print(f"   - {fact.fact[:100]}...")
        
        # Check conversation history
        if topics:
            history = tracker.get_conversation_history(topics[0], limit=3)
            print(f"\n💬 Conversation history for '{topics[0]}':")
            for turn in history:
                print(f"   Q: {turn['query'][:50]}...")
                print(f"   A: {turn['response'][:100]}...")
                print()
                
    except Exception as e:
        print(f"❌ Error checking conversation data: {e}")

def test_data_persistence():
    """Test that data persists across tracker instances."""
    print("\n🔄 Testing data persistence...")
    
    test_thread = f"persistence_test_thread_{int(time.time())}"  # Unique thread ID
    test_topic = "test_topic"
    test_fact = "This is a test fact for persistence checking."
    
    try:
        # Create first tracker and add data
        print("1️⃣ Creating first tracker and adding data...")
        tracker1 = ConversationTracker(test_thread)
        
        # Add a fact
        fact_id = tracker1.add_shared_fact(
            topic=test_topic,
            fact=test_fact,
            source="test"
        )
        
        # Add a conversation turn
        tracker1.add_conversation_turn(
            topic=test_topic,
            query="Test query",
            response="Test response",
            sources=["test_source"],
            fact_ids=[fact_id] if fact_id else []
        )
        
        # Update a preference
        tracker1.update_preference("test_pref", "test_value")
        
        print("✅ Data added to first tracker")
        
        # Wait a bit longer for Azure Search indexing
        print("\n⏳ Waiting for Azure Search indexing (3 seconds)...")
        time.sleep(3)
        
        # Create second tracker with same thread ID
        print("\n2️⃣ Creating second tracker with same thread ID...")
        tracker2 = ConversationTracker(test_thread)
        
        # Force refresh to ensure we get latest data
        tracker2.force_refresh()
        
        # Check if data is loaded
        topics = tracker2.get_all_topics()
        print(f"   Topics found: {len(topics)} (should be at least 1)")
        if topics:
            print(f"   Topics: {topics}")
        
        facts = tracker2.get_shared_facts(test_topic)
        print(f"   Facts found: {len(facts)} (should be at least 1)")
        if facts:
            print(f"   First fact: {facts[0].fact[:50]}...")
        
        prefs = tracker2.get_user_preferences()
        print(f"   Preferences found: {len(prefs)} (should be at least 1)")
        print(f"   Test preference value: {prefs.get('test_pref', 'NOT FOUND')}")
        
        # Check conversation history
        history = tracker2.get_conversation_history(test_topic)
        print(f"   Conversation history entries: {len(history)}")
        
        if topics and facts and prefs.get('test_pref') == 'test_value':
            print("\n✅ Data persistence test PASSED!")
            return True
        else:
            print("\n❌ Data persistence test FAILED!")
            print("   Debugging info:")
            print(f"   - Topics found: {topics}")
            print(f"   - Facts count: {len(facts)}")
            print(f"   - Preferences: {prefs}")
            return False
            
    except Exception as e:
        print(f"❌ Persistence test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def list_all_threads():
    """List all unique thread IDs in the system."""
    print("\n👥 Listing all threads in the system...")
    
    try:
        client = SearchClient(
            os.environ["AZURE_SEARCH_ENDPOINT"],
            "conversation-history",
            AzureKeyCredential(os.environ["AZURE_SEARCH_API_KEY"])
        )
        
        # Get all documents with thread_id
        results = client.search(
            search_text="*",
            select=["thread_id"],
            top=1000
        )
        
        threads = set()
        for result in results:
            if "thread_id" in result:
                threads.add(result["thread_id"])
        
        print(f"Found {len(threads)} unique threads:")
        for thread in sorted(list(threads))[:10]:  # Show first 10
            print(f"   - {thread}")
            
        return list(threads)
        
    except Exception as e:
        print(f"❌ Error listing threads: {e}")
        return []

def cleanup_test_threads():
    """Clean up test threads from previous runs."""
    print("\n🧹 Cleaning up old test threads...")
    
    try:
        client = SearchClient(
            os.environ["AZURE_SEARCH_ENDPOINT"],
            "conversation-history",
            AzureKeyCredential(os.environ["AZURE_SEARCH_API_KEY"])
        )
        
        # Find test threads
        results = client.search(
            search_text="*",
            filter="thread_id eq 'persistence_test_thread' or search.ismatch('persistence_test_thread*', 'thread_id')",
            select=["id"],
            top=1000
        )
        
        docs_to_delete = []
        for result in results:
            docs_to_delete.append({"id": result["id"]})
        
        if docs_to_delete:
            print(f"   Found {len(docs_to_delete)} test documents to clean up")
            # Note: Azure Search doesn't have a delete by query, so we'd need to delete individually
            # For now, just report what we found
        else:
            print("   No test documents found to clean up")
            
    except Exception as e:
        print(f"⚠️ Error during cleanup: {e}")

if __name__ == "__main__":
    print("🧪 Running Conversation History Tests\n")
    print("="*60)
    
    # Test 1: Azure Search Connection
    if test_azure_search_connection():
        
        # Test 2: Check existing data
        # You can change this to your actual thread ID
        check_conversation_data("127_0_0_1")
        
        # Test 3: Test persistence
        test_data_persistence()
        
        # Test 4: List all threads
        list_all_threads()
        
        # Optional: Cleanup old test data
        # cleanup_test_threads()
    
    print("\n" + "="*60)
    print("✅ Tests complete!")