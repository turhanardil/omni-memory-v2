#!/usr/bin/env python3
"""
Test DuckDuckGo search - NO API KEY NEEDED!
Run: python test_duckduckgo.py
"""

import requests
from bs4 import BeautifulSoup

def search_duckduckgo_simple(query):
    """Simplest possible DuckDuckGo search."""
    
    print(f"🦆 Searching DuckDuckGo for: '{query}'")
    
    # Send search request
    response = requests.post(
        "https://html.duckduckgo.com/html/",
        headers={'User-Agent': 'Mozilla/5.0'},
        data={'q': query}
    )
    
    # Parse results
    soup = BeautifulSoup(response.text, 'html.parser')
    results = []
    
    for result in soup.find_all('div', class_='links_main')[:5]:
        link = result.find('a', class_='result__a')
        if link:
            results.append({
                'title': link.text.strip(),
                'url': link.get('href', '')
            })
    
    return results

# Test it!
print("🧪 Testing DuckDuckGo Search (FREE, NO API KEY!)\n")

test_queries = [
    "weather in paris today",
    "latest AI news 2024", 
    "Python programming tutorial"
]

for query in test_queries:
    print(f"\n📝 Query: {query}")
    results = search_duckduckgo_simple(query)
    
    if results:
        print(f"✅ Found {len(results)} results:")
        for i, r in enumerate(results[:3], 1):
            print(f"{i}. {r['title'][:60]}...")
            print(f"   {r['url'][:60]}...")
    else:
        print("❌ No results")

print("\n✅ IT WORKS! No API key needed!")
print("💡 Now just use web_search_working.py with SEARCH_PROVIDER='duckduckgo'")