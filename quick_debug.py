#!/usr/bin/env python3
"""
Quick debug to find what's wrong
Run: python quick_debug.py
"""

# Test 1: Is wttr.in working?
print("1️⃣ Testing wttr.in weather service...")
import requests

try:
    response = requests.get("https://wttr.in/Paris?format=3", headers={'User-Agent': 'curl'})
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text.strip()}")
    print("   ✅ wttr.in is working!" if response.status_code == 200 else "   ❌ wttr.in failed")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 2: Check which web_search is being used
print("\n2️⃣ Checking web_search.py...")
try:
    with open('web_search.py', 'r') as f:
        content = f.read()
        if 'wttr.in' in content:
            print("   ✅ Enhanced version with wttr.in is installed")
        else:
            print("   ❌ Old version without wttr.in - need to update!")
            print("   Run: cp web_search_enhanced.py web_search.py")
except Exception as e:
    print(f"   ❌ Error reading web_search.py: {e}")

# Test 3: Import and test the search function
print("\n3️⃣ Testing search function...")
try:
    from web_search import search_and_scrape
    
    results = search_and_scrape("weather in paris today", num_urls=1)
    
    if results:
        print(f"   ✅ Got {len(results)} results")
        print(f"   Title: {results[0]['title']}")
        print(f"   Content preview: {results[0]['content'][:100]}...")
        
        # Check if it's actual weather data
        content = results[0]['content'].lower()
        if any(word in content for word in ['temperature', '°c', 'weather', 'humidity']):
            print("   ✅ Contains weather data!")
        else:
            print("   ❌ No weather data found in content")
    else:
        print("   ❌ No results returned")
        
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 4: Direct weather function test
print("\n4️⃣ Testing direct weather function...")
try:
    from web_search import get_weather_direct
    
    weather = get_weather_direct("Paris")
    if weather:
        print("   ✅ Direct weather works!")
        print(f"   Weather: {weather[:100]}...")
    else:
        print("   ❌ Direct weather failed")
except ImportError:
    print("   ❌ get_weather_direct not found - old version of web_search.py")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n📊 Summary:")
print("If tests 1 & 4 work but test 2 fails, you need to update web_search.py")
print("Run: cp web_search_enhanced.py web_search.py")