#!/usr/bin/env python3
"""
Test OpenAI Responses API with web search
Run: python test_responses_api.py
"""

import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# Check API key
if not os.getenv("OPENAI_API_KEY"):
    print("❌ OPENAI_API_KEY not found in .env")
    exit(1)

print("✅ OpenAI API key found")

# Initialize client
client = OpenAI()

print("\n🧪 Testing OpenAI Responses API with Web Search")
print("=" * 60)

# Test 1: Basic responses API test
print("\n1️⃣ Testing basic Responses API...")
try:
    response = client.responses.create(
        model="gpt-4-1",
        input="Hello, can you respond?"
    )
    print("✅ Basic Responses API works!")
    print(f"Response: {response.output_text[:100]}...")
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nMake sure you have access to the Responses API")

# Test 2: Web search test
print("\n2️⃣ Testing web search functionality...")
test_queries = [
    "What is the weather in Paris today?",
    "Latest news about artificial intelligence",
    "Current stock price of Apple"
]

for query in test_queries:
    print(f"\n📝 Query: {query}")
    try:
        response = client.responses.create(
            model="gpt-4-1",
            tools=[{"type": "web_search_preview"}],
            tool_choice={"type": "web_search_preview"},
            input=query
        )
        
        print("✅ Web search successful!")
        print(f"Response preview: {response.output_text[:200]}...")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        
        # Try without forcing tool choice
        print("   Retrying without tool_choice...")
        try:
            response = client.responses.create(
                model="gpt-4-1",
                tools=[{"type": "web_search_preview"}],
                input=query
            )
            print("✅ Success without tool_choice!")
            print(f"Response preview: {response.output_text[:200]}...")
        except Exception as e2:
            print(f"❌ Still failed: {e2}")

# Test 3: Test the full implementation
print("\n\n3️⃣ Testing full web_search.py implementation...")
try:
    from web_search import search_and_scrape
    
    result = search_and_scrape("weather in paris today")
    if result:
        print("✅ Full implementation works!")
        print(f"Got {len(result)} results")
    else:
        print("❌ No results returned")
except Exception as e:
    print(f"❌ Implementation error: {e}")

print("\n✅ Test complete!")
print("\n📝 Notes:")
print("- If web search failed, check if your API key has Responses API access")
print("- The Responses API is different from the regular chat completions API")
print("- Web search results are returned as synthesized text, not raw URLs")