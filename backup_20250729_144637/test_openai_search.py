#!/usr/bin/env python3
"""
Test OpenAI search implementation
Run: python test_openai_search.py
"""

import os
import sys
from dotenv import load_dotenv

# Add current directory to path
sys.path.append('.')

load_dotenv()

def test_openai_search():
    """Test the OpenAI search functionality."""
    
    print("🚀 Testing OpenAI Search Implementation")
    print("=" * 60)
    
    # Check API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not found in .env")
        return
    
    print("✅ OpenAI API key found")
    
    # Import after confirming API key
    from web_search import openai_search, search_and_scrape, categorize_query_type
    
    # Test queries
    test_queries = [
        "weather in paris today",
        "weather in istanbul right now",
        "latest news about artificial intelligence"
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Testing: {query}")
        query_type = categorize_query_type(query)
        print(f"Query type: {query_type}")
        
        # Test OpenAI search
        print("\n1️⃣ Testing openai_search()...")
        results = openai_search(query, query_type)
        
        if results:
            print(f"✅ Got {len(results)} results:")
            for i, result in enumerate(results[:3], 1):
                print(f"\n{i}. {result.get('title', 'No title')[:60]}...")
                print(f"   URL: {result.get('url', 'No URL')[:60]}...")
                print(f"   Snippet: {result.get('snippet', 'No snippet')[:80]}...")
        else:
            print("❌ No results returned")
        
        # Test full search and scrape
        print("\n2️⃣ Testing search_and_scrape()...")
        scraped = search_and_scrape(query, num_urls=2)
        
        if scraped:
            print(f"✅ Successfully scraped {len(scraped)} pages:")
            for result in scraped:
                print(f"\n- {result['title'][:60]}...")
                print(f"  URL: {result['url'][:60]}...")
                content_preview = result['content'][:150].replace('\n', ' ')
                print(f"  Content: {content_preview}...")
                
                # Check for weather indicators
                if query_type == "weather":
                    has_temp = any(x in result['content'] for x in ['°', 'degrees', 'temperature'])
                    print(f"  Has temperature: {'✅' if has_temp else '❌'}")
        else:
            print("❌ No pages scraped")

def test_direct_openai_call():
    """Test direct OpenAI API call to verify web search capability."""
    
    print("\n" + "="*60)
    print("Testing Direct OpenAI API Call")
    print("="*60)
    
    try:
        from openai import OpenAI
        client = OpenAI()
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "user",
                    "content": "What's the current weather in Paris? Please search the web for this information."
                }
            ],
            tools=[{"type": "web_search"}],
            tool_choice="auto"
        )
        
        print("✅ OpenAI API call successful")
        print(f"Response: {response.choices[0].message}")
        
        if response.choices[0].message.tool_calls:
            print("✅ Tool calls detected - web search capability confirmed")
        else:
            print("⚠️  No tool calls - web search might not be available")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nNote: OpenAI web search requires:")
        print("- GPT-4 model access")
        print("- Web search capability enabled on your API key")
        print("- Correct API version")

if __name__ == "__main__":
    # First test direct API
    test_direct_openai_call()
    
    # Then test our implementation
    print("\n")
    test_openai_search()
    
    print("\n✅ Test complete!")