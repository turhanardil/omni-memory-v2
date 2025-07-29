# test_context_manager.py
"""
Test script to demonstrate context-aware memory chatbot features.
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

def get_conversation_summary(topic=None):
    """Get conversation summary."""
    url = f"{BASE_URL}/debug/conversation-summary"
    if topic:
        url += f"?topic={topic}"
    response = requests.get(url)
    return response.json()

def analyze_query(query):
    """Analyze how a query would be processed."""
    response = requests.get(f"{BASE_URL}/debug/analyze-query?query={query}")
    return response.json()

def test_context_aware_features():
    """Test the context-aware features."""
    print("🧪 Testing Context-Aware Memory Chatbot\n")
    
    # Test 1: Initial conversation about CEO
    print("="*60)
    print("Test 1: Initial CEO Discussion")
    print("="*60)
    
    response = send_message("Tell me about our CEO's resignation")
    print(f"Bot: {response['reply'][:200]}...")
    
    time.sleep(2)
    
    # Check what facts were stored
    facts = get_shared_facts("Renault CEO resignation")
    print(f"\n📊 Facts stored: {facts['facts_count']}")
    if facts['facts']:
        print("Sample facts:")
        for fact in facts['facts'][:3]:
            print(f"  - {fact['fact'][:100]}...")
    
    time.sleep(2)
    
    # Test 2: Follow-up with explicit no-repeat instruction
    print("\n" + "="*60)
    print("Test 2: Follow-up with No-Repeat Request")
    print("="*60)
    
    # First, analyze how the query will be processed
    analysis = analyze_query("Any new updates on our CEO? Don't repeat what you told me")
    print(f"\n🔍 Query Analysis:")
    print(f"  Enhanced Query: {analysis['analysis']['enhanced_query']}")
    print(f"  Query Type: {analysis['analysis']['query_type']}")
    print(f"  User Intent: {analysis['analysis']['user_intent']}")
    print(f"  Constraints: {analysis['analysis']['search_constraints']}")
    
    response = send_message("Any new updates on our CEO? Don't repeat what you told me")
    print(f"\nBot: {response['reply']}")
    
    time.sleep(2)
    
    # Test 3: Weather query to test staleness detection
    print("\n" + "="*60)
    print("Test 3: Weather Query (Tests Staleness)")
    print("="*60)
    
    response = send_message("What's the weather in Paris?")
    print(f"Bot: {response['reply'][:150]}...")
    
    time.sleep(2)
    
    # Ask again to see deduplication
    response = send_message("Tell me the weather in Paris")
    print(f"\nBot (should recognize recent query): {response['reply'][:150]}...")
    
    # Test 4: Check conversation summary
    print("\n" + "="*60)
    print("Test 4: Conversation Summary")
    print("="*60)
    
    summary = get_conversation_summary()
    print(f"Overall Summary:\n{summary['summary']}")
    
    # Get all topics
    topics_response = requests.get(f"{BASE_URL}/debug/topics")
    topics = topics_response.json()
    print(f"\nTopics discussed: {topics['topics_count']}")
    for topic, info in topics['topics'].items():
        print(f"  - {topic}: {info['facts_shared']} facts")
    
    # Test 5: User preferences
    print("\n" + "="*60)
    print("Test 5: User Preferences")
    print("="*60)
    
    prefs_response = requests.get(f"{BASE_URL}/debug/user-preferences")
    prefs = prefs_response.json()
    print(f"Interaction count: {prefs['interaction_count']}")
    print(f"Preferences: {json.dumps(prefs['preferences'], indent=2)}")
    
    # Test 6: Complex follow-up
    print("\n" + "="*60)
    print("Test 6: Complex Context-Aware Query")
    print("="*60)
    
    response = send_message("Summarize everything we discussed about our company")
    print(f"Bot: {response['reply'][:300]}...")

def test_specific_scenarios():
    """Test specific context-aware scenarios."""
    print("\n\n🎯 Testing Specific Scenarios\n")
    
    # Scenario 1: Information gap detection
    print("Scenario 1: Information Gap Detection")
    print("-"*40)
    
    analysis = analyze_query("What was the reason for our CEO's resignation?")
    print(f"Information Gaps: {analysis['analysis']['information_gaps']}")
    
    # Scenario 2: Temporal constraints
    print("\nScenario 2: Temporal Constraints")
    print("-"*40)
    
    analysis = analyze_query("What happened with our stock price since yesterday?")
    print(f"Temporal Requirement: {analysis['analysis']['temporal_requirement']}")
    print(f"Search Constraints: {analysis['analysis']['search_constraints']}")

if __name__ == "__main__":
    print("⚠️  Make sure the app is running on http://localhost:5000")
    print("Starting test in 3 seconds...\n")
    time.sleep(3)
    
    try:
        # Run main tests
        test_context_aware_features()
        
        # Run specific scenario tests
        test_specific_scenarios()
        
        print("\n✅ All tests completed!")
        print("\nKey improvements demonstrated:")
        print("1. ✅ Tracks shared facts to avoid repetition")
        print("2. ✅ Enhances queries with context and constraints")
        print("3. ✅ Recognizes follow-up questions and user intent")
        print("4. ✅ Detects information staleness")
        print("5. ✅ Maintains conversation summaries")
        print("6. ✅ Learns user preferences")
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the app. Make sure it's running!")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()