# test_temporal_filtering.py
"""
Test script to verify temporal filtering and fact deduplication are working.
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000"

def send_message(message):
    """Send a message to the chatbot and get response."""
    response = requests.post(
        f"{BASE_URL}/chat",
        json={"message": message},
        headers={"Content-Type": "application/json"}
    )
    return response.json()

def get_shared_facts(topic):
    """Get shared facts about a topic."""
    response = requests.get(f"{BASE_URL}/debug/shared-facts?topic={topic}")
    return response.json()

def analyze_query(query):
    """Analyze how a query would be processed."""
    response = requests.get(f"{BASE_URL}/debug/analyze-query?query={query}")
    return response.json()

def test_temporal_filtering():
    """Test temporal filtering and deduplication."""
    print("🧪 Testing Temporal Filtering & Deduplication\n")
    
    # Test 1: Initial setup
    print("="*60)
    print("Test 1: Setup - Introduce yourself")
    print("="*60)
    
    response = send_message("Hi, my name is Jack and I work at Renault")
    print(f"Bot: {response['reply']}")
    
    time.sleep(2)
    
    # Test 2: First CEO query
    print("\n" + "="*60)
    print("Test 2: First CEO Query")
    print("="*60)
    
    response = send_message("What's the latest on our CEO's resignation?")
    print(f"Bot: {response['reply'][:300]}...")
    
    # Wait and check facts
    time.sleep(3)
    facts = get_shared_facts("Renault CEO resignation")
    print(f"\n📊 Facts stored: {facts['facts_count']}")
    if facts['facts']:
        print("Facts tracked:")
        for i, fact in enumerate(facts['facts'], 1):
            print(f"{i}. {fact['fact'][:80]}...")
            print(f"   Shared at: {fact['timestamp']}")
    
    time.sleep(2)
    
    # Test 3: Ask for updates (should not repeat)
    print("\n" + "="*60)
    print("Test 3: Ask for Updates (Should NOT Repeat)")
    print("="*60)
    
    # First analyze the query
    analysis = analyze_query("Are there any new updates on our CEO's resignation as of now?")
    print(f"\n🔍 Query Analysis:")
    print(f"  Query Type: {analysis['analysis']['query_type']}")
    print(f"  Temporal Requirement: {analysis['analysis']['temporal_requirement']}")
    print(f"  Search Constraints: {analysis['analysis']['search_constraints'][:3]}...")  # First 3
    print(f"  Enhanced Query: {analysis['analysis']['enhanced_query']}")
    
    response = send_message("Are there any new updates on our CEO's resignation as of now?")
    print(f"\nBot: {response['reply']}")
    
    # Check if response contains old facts
    old_facts = ["Luca de Meo", "July 15", "Kering", "Gucci", "five-year tenure"]
    repeated_facts = [fact for fact in old_facts if fact.lower() in response['reply'].lower()]
    
    if repeated_facts:
        print(f"\n❌ WARNING: Response repeated these facts: {repeated_facts}")
    else:
        print(f"\n✅ Good: Response did not repeat old facts")
    
    time.sleep(2)
    
    # Test 4: Different phrasing for updates
    print("\n" + "="*60)
    print("Test 4: Different Update Phrasing")
    print("="*60)
    
    response = send_message("Any NEW information about the CEO situation that you haven't told me yet?")
    print(f"Bot: {response['reply']}")
    
    # Test 5: Check conversation history
    print("\n" + "="*60)
    print("Test 5: Conversation History Check")
    print("="*60)
    
    history_response = requests.get(f"{BASE_URL}/debug/conversation-history?topic=Renault CEO resignation")
    history = history_response.json()
    
    print(f"Conversation turns: {history['history_count']}")
    for i, turn in enumerate(history['history'], 1):
        print(f"\nTurn {i}:")
        print(f"  Query: {turn['query']}")
        print(f"  Facts shared: {len(turn.get('facts_shared', []))}")
        print(f"  Timestamp: {turn['timestamp']}")

def test_specific_scenarios():
    """Test specific temporal scenarios."""
    print("\n\n🎯 Testing Specific Temporal Scenarios\n")
    
    # Scenario 1: Explicit temporal query
    print("Scenario 1: Explicit Temporal Query")
    print("-"*40)
    
    analysis = analyze_query("What happened with our CEO since yesterday?")
    print(f"Temporal constraints: {analysis['analysis']['search_constraints']}")
    
    # Scenario 2: Testing fact similarity
    print("\nScenario 2: Fact Similarity Detection")
    print("-"*40)
    
    # Send similar facts
    response1 = send_message("The CEO resigned on July 15")
    time.sleep(1)
    response2 = send_message("CEO resignation effective July 15")
    
    # Check if both were stored or deduplicated
    facts = get_shared_facts("CEO")
    print(f"Total facts stored: {facts['facts_count']} (should deduplicate similar facts)")

if __name__ == "__main__":
    print("⚠️  Make sure the app is running on http://localhost:5000")
    print("⚠️  This test assumes a fresh conversation (restart the app)")
    print("Starting test in 3 seconds...\n")
    time.sleep(3)
    
    try:
        # Run main temporal filtering tests
        test_temporal_filtering()
        
        # Run specific scenarios
        test_specific_scenarios()
        
        print("\n✅ Test completed!")
        print("\nKey things to verify:")
        print("1. ✅ Facts are tracked with timestamps")
        print("2. ✅ 'New updates' queries exclude previously shared facts")
        print("3. ✅ Search constraints include NOT operators")
        print("4. ✅ Similar facts are deduplicated")
        print("5. ✅ Temporal constraints (after:date) are added")
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the app. Make sure it's running!")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()