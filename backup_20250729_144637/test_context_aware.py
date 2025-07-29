# test_context_aware.py
"""
Test script to demonstrate context-aware memory system.
Run this after starting the app to see how it handles personal context.
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

def test_context_aware_chat():
    """Test the context-aware features."""
    print("🧪 Testing Context-Aware Memory Chatbot\n")
    
    # Test conversation
    test_messages = [
        "Hi, my name is Jack",
        "I work at Renault",
        "My favorite color is blue",
        "What is my name?",
        "any updates on our CEO's resignation?",
        "what's happening with my company's stock price?",
        "tell me about recent news from our company"
    ]
    
    for i, message in enumerate(test_messages):
        print(f"\n{'='*60}")
        print(f"Test {i+1}: {message}")
        print("="*60)
        
        # Send message
        response = send_message(message)
        
        if "reply" in response:
            print(f"Bot: {response['reply']}")
        else:
            print(f"Error: {response}")
        
        # Wait a bit between messages
        time.sleep(2)
    
    print("\n\n🔍 Testing Debug Endpoints...")
    
    # Test decision endpoint
    print("\n1. Query Analysis for 'our CEO':")
    decision = requests.get(f"{BASE_URL}/debug/decision?query=any updates on our CEO's resignation?")
    decision_data = decision.json()
    print(f"   - Query Type: {decision_data['analysis']['query_type']}")
    print(f"   - Needs Search: {decision_data['analysis']['needs_search']}")
    print(f"   - Enhanced Query: {decision_data['analysis']['search_query']}")
    print(f"   - Context Used: {decision_data['analysis'].get('context_used', 'None')}")
    
    # Test user context endpoint
    print("\n2. User Context:")
    context = requests.get(f"{BASE_URL}/debug/user-context")
    context_data = context.json()
    print(f"   - Total Facts: {context_data['total_facts']}")
    if context_data['user_context']['name']:
        print(f"   - Name: {context_data['user_context']['name']}")
    if context_data['user_context']['company']:
        print(f"   - Company: {context_data['user_context']['company']}")
    for fact in context_data['user_context']['facts'][:3]:
        print(f"   - Fact: {fact}")
    
    print("\n✅ Test completed!")

if __name__ == "__main__":
    print("⚠️  Make sure the app is running on http://localhost:5000")
    print("Starting test in 3 seconds...\n")
    time.sleep(3)
    
    try:
        test_context_aware_chat()
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the app. Make sure it's running!")
    except Exception as e:
        print(f"❌ Error: {e}")