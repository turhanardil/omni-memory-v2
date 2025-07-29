#!/usr/bin/env python3
"""
Test script to debug Bing search results directly
Run: python test_bing_search.py
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

BING_KEY = os.getenv("BING_SEARCH_KEY")
BING_ENDPOINT = "https://api.bing.microsoft.com/v7.0"

def test_bing_search(query, freshness=None):
    """Test Bing search with different parameters."""
    
    print(f"\n🔍 Testing search for: '{query}'")
    print(f"   Freshness filter: {freshness or 'None'}")
    
    headers = {'Ocp-Apim-Subscription-Key': BING_KEY}
    params = {
        'q': query,
        'count': 10,
        'responseFilter': 'webpages',
        'textDecorations': False,
        'textFormat': 'Raw',
        'safeSearch': 'Moderate',
        'mkt': 'en-US'
    }
    
    if freshness:
        params['freshness'] = freshness
    
    try:
        response = requests.get(f"{BING_ENDPOINT}/search", headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        if 'webPages' in data and 'value' in data['webPages']:
            results = data['webPages']['value']
            print(f"\n✅ Found {len(results)} results:")
            
            for i, result in enumerate(results[:5], 1):
                print(f"\n{i}. {result['name'][:80]}...")
                print(f"   URL: {result['url'][:80]}...")
                print(f"   Snippet: {result['snippet'][:120]}...")
                
                # Check if it's a good weather source
                url_lower = result['url'].lower()
                good_weather = any(domain in url_lower for domain in [
                    'weather.com', 'accuweather.com', 'weather.gov', 
                    'timeanddate.com', 'wunderground.com'
                ])
                if good_weather:
                    print(f"   ✅ GOOD WEATHER SOURCE")
        else:
            print("❌ No results found")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🧪 Bing Search Test Script")
    print(f"🔑 API Key: {'✅ Found' if BING_KEY else '❌ Missing'}")
    
    if not BING_KEY:
        print("Please set BING_SEARCH_KEY in your .env file")
        exit(1)
    
    # Test different queries
    test_queries = [
        ("paris weather today", "Day"),
        ("paris weather today", None),
        ("weather in paris france today", "Day"),
        ("istanbul weather today", "Day"),
        ("istanbul weather", None),
        ("current weather istanbul turkey", None),
        ("weather.com paris", None),
        ("accuweather istanbul", None)
    ]
    
    for query, freshness in test_queries:
        test_bing_search(query, freshness)
        
    print("\n✅ Test complete!")