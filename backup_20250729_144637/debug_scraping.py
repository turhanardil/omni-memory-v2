#!/usr/bin/env python3
"""
Debug what content is actually being scraped
Run: python debug_scraping.py
"""

from web_search import search_and_scrape

# Test scraping
print("🔍 Testing web scraping for weather...\n")

results = search_and_scrape("weather in paris today", num_urls=1)

if results:
    for i, result in enumerate(results, 1):
        print(f"\n{'='*60}")
        print(f"Result #{i}")
        print(f"Title: {result['title']}")
        print(f"URL: {result['url']}")
        print(f"\nContent (first 1000 chars):")
        print("-" * 60)
        print(result['content'][:1000])
        print("-" * 60)
        
        # Check for weather indicators
        content_lower = result['content'].lower()
        
        print("\n🔍 Weather indicators check:")
        print(f"- Has temperature (°): {'°' in result['content']}")
        print(f"- Has 'degrees': {'degrees' in content_lower}")
        print(f"- Has 'temperature': {'temperature' in content_lower}")
        print(f"- Has 'weather': {'weather' in content_lower}")
        print(f"- Has 'forecast': {'forecast' in content_lower}")
        
        # Look for numbers that might be temperatures
        import re
        temps = re.findall(r'\b\d{1,2}°[CF]\b', result['content'])
        if temps:
            print(f"\n🌡️ Found temperatures: {temps[:5]}")
else:
    print("❌ No results scraped")

print("\n💡 If no weather data found, the site might be:")
print("- Using JavaScript to load weather (can't scrape)")
print("- Blocking scrapers")
print("- Showing different content to bots")