#!/usr/bin/env python3
"""
Test the improved weather search functionality
Run: python test_weather_search.py
"""

import sys
sys.path.append('.')  # Add current directory to path

from web_search import (
    generate_simple_search_query, 
    bing_search, 
    validate_weather_content,
    search_and_scrape
)

def test_query_generation():
    """Test improved query generation."""
    print("\n🧪 Testing Query Generation")
    print("=" * 50)
    
    test_cases = [
        "how is the weather today in paris",
        "weather in istanbul right now",
        "what's the weather like in london today",
        "berlin weather",
        "weather forecast tokyo"
    ]
    
    for query in test_cases:
        generated = generate_simple_search_query(query, "weather")
        print(f"Input:  {query}")
        print(f"Output: {generated}")
        print()

def test_content_validation():
    """Test content validation."""
    print("\n🧪 Testing Content Validation")
    print("=" * 50)
    
    # Test cases with sample content
    test_cases = [
        {
            "query": "weather in paris today",
            "content": "Paris, France weather forecast: Temperature 22°C, partly cloudy with chance of rain.",
            "should_pass": True
        },
        {
            "query": "weather in paris today",
            "content": "Tour de France Stage 17 passes through French countryside near Paris.",
            "should_pass": False
        },
        {
            "query": "weather in istanbul",
            "content": "Istanbul weather today: 38°C and sunny. Very hot conditions in Turkey.",
            "should_pass": True
        },
        {
            "query": "weather in paris",
            "content": "Cricket match in India delayed due to rain. French players disappointed.",
            "should_pass": False
        }
    ]
    
    for test in test_cases:
        result = validate_weather_content(test["content"], test["query"])
        status = "✅ PASS" if result == test["should_pass"] else "❌ FAIL"
        print(f"\nQuery: {test['query']}")
        print(f"Content: {test['content'][:80]}...")
        print(f"Expected: {'Valid' if test['should_pass'] else 'Invalid'}")
        print(f"Result: {status}")

def test_live_search():
    """Test live search with real Bing API."""
    print("\n🧪 Testing Live Search")
    print("=" * 50)
    
    test_queries = [
        "Paris France weather forecast",
        "Istanbul Turkey weather forecast",
        "site:weather.com Paris"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Testing: {query}")
        results = bing_search(query, 3)
        
        if results:
            print(f"✅ Got {len(results)} results:")
            for i, result in enumerate(results[:3], 1):
                print(f"\n{i}. {result['title'][:60]}...")
                print(f"   {result['url'][:60]}...")
                print(f"   Weather site: {'Yes' if any(site in result['url'].lower() for site in ['weather.com', 'accuweather', 'timeanddate']) else 'No'}")
        else:
            print("❌ No results")

def test_full_search_and_scrape():
    """Test the full search and scrape flow."""
    print("\n🧪 Testing Full Search & Scrape")
    print("=" * 50)
    
    queries = [
        "how is the weather in paris today",
        "weather in istanbul right now"
    ]
    
    for query in queries:
        print(f"\n📍 Testing: {query}")
        results = search_and_scrape(query, num_urls=2)
        
        if results:
            print(f"✅ Successfully scraped {len(results)} pages")
            for result in results:
                print(f"\n- Title: {result['title'][:60]}...")
                print(f"  URL: {result['url'][:60]}...")
                # Check if content mentions temperature
                content_preview = result['content'][:200]
                has_temp = any(x in content_preview for x in ['°', 'degrees', 'temperature'])
                print(f"  Has temperature: {'Yes' if has_temp else 'No'}")
        else:
            print("❌ No results scraped")

if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    print("🚀 Weather Search Test Suite")
    print(f"🔑 Bing API Key: {'✅ Found' if os.getenv('BING_SEARCH_KEY') else '❌ Missing'}")
    
    # Run tests
    test_query_generation()
    test_content_validation()
    
    if os.getenv('BING_SEARCH_KEY'):
        test_live_search()
        test_full_search_and_scrape()
    else:
        print("\n⚠️  Skipping live tests - no Bing API key found")
    
    print("\n✅ Test suite complete!")