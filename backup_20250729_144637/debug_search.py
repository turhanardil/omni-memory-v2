#!/usr/bin/env python3
"""
Debug tool to understand why search results are being rejected
Run: python debug_search.py "weather in paris today"
"""

import sys
import os
from dotenv import load_dotenv

load_dotenv()

# Add current directory to path
sys.path.append('.')

from web_search import (
    bing_search,
    is_quality_source,
    validate_weather_content,
    scrape_content,
    categorize_query_type
)

def debug_search(query):
    """Debug why search results are accepted or rejected."""
    
    print(f"🔍 Debugging search for: '{query}'")
    query_type = categorize_query_type(query)
    print(f"📊 Query type: {query_type}")
    print("=" * 80)
    
    # Perform search
    results = bing_search(query, 10)
    
    if not results:
        print("❌ No search results returned from Bing")
        return
    
    print(f"✅ Got {len(results)} search results\n")
    
    # Analyze each result
    for i, result in enumerate(results, 1):
        print(f"\n{'='*80}")
        print(f"Result #{i}")
        print(f"Title: {result['title']}")
        print(f"URL: {result['url']}")
        print(f"Snippet: {result['snippet'][:150]}...")
        
        # Check quality source
        print("\n🔍 Quality Check:")
        is_quality = is_quality_source(
            result['url'], 
            result['title'], 
            result['snippet'], 
            query_type
        )
        print(f"Quality source: {'✅ YES' if is_quality else '❌ NO'}")
        
        if not is_quality:
            print("Skipping scrape due to quality check failure")
            continue
        
        # Try to scrape
        print("\n📄 Attempting to scrape...")
        content = scrape_content(result['url'], query, query_type, max_chars=500)
        
        if content:
            print(f"✅ Scraping successful ({len(content)} chars)")
            print(f"Content preview: {content[:200]}...")
            
            # Validate content
            print("\n🔍 Content Validation:")
            if query_type == "weather":
                is_valid = validate_weather_content(content, query)
                print(f"Weather validation: {'✅ PASS' if is_valid else '❌ FAIL'}")
                
                # Detailed weather checks
                content_lower = content.lower()
                print("\nDetailed checks:")
                print(f"- Has temperature: {'Yes' if any(x in content_lower for x in ['°', 'degrees', 'temperature']) else 'No'}")
                print(f"- Has weather words: {'Yes' if any(x in content_lower for x in ['weather', 'forecast', 'conditions']) else 'No'}")
                
                # Check location
                import re
                location_match = re.search(r'(?:weather\s+(?:in\s+)?|in\s+)([a-zA-Z\s]+?)(?:\s+today|\s+right|\s*$)', query, re.IGNORECASE)
                if location_match:
                    location = location_match.group(1).strip().lower()
                    print(f"- Location '{location}' in content: {'Yes' if location in content_lower else 'No'}")
        else:
            print("❌ Scraping failed")
        
        print(f"\nFinal verdict: {'✅ WOULD BE USED' if is_quality and content and (not query_type == 'weather' or validate_weather_content(content, query)) else '❌ REJECTED'}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        query = ' '.join(sys.argv[1:])
    else:
        query = "weather in paris today"
    
    if not os.getenv('BING_SEARCH_KEY'):
        print("❌ BING_SEARCH_KEY not found in .env file")
        sys.exit(1)
    
    debug_search(query)