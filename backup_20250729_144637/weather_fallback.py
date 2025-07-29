#!/usr/bin/env python3
"""
Fallback solution: Use wttr.in for weather (no API key needed!)
Run: python weather_fallback.py
"""

import requests

def get_weather_wttr(location: str) -> str:
    """
    Get weather from wttr.in - a free weather service
    No API key needed!
    """
    try:
        # Simple text format
        url = f"https://wttr.in/{location}?format=3"
        response = requests.get(url, headers={'User-Agent': 'curl'})
        
        if response.status_code == 200:
            # Returns something like: "Paris: ⛅️ +22°C"
            return response.text.strip()
        
        # Try more detailed format
        url = f"https://wttr.in/{location}?format=%l:+%c+%t+%h+%w"
        response = requests.get(url, headers={'User-Agent': 'curl'})
        
        if response.status_code == 200:
            return response.text.strip()
            
    except Exception as e:
        print(f"Error: {e}")
    
    return None

# Test it
print("🌤️ Testing wttr.in weather service (FREE, no API key!)\n")

locations = ["Paris", "London", "Tokyo", "New York"]

for location in locations:
    weather = get_weather_wttr(location)
    if weather:
        print(f"✅ {weather}")
    else:
        print(f"❌ Failed for {location}")

print("\n💡 Add this to web_search.py as a fallback for weather queries!")

# More detailed weather
print("\n📊 Detailed weather for Paris:")
try:
    url = "https://wttr.in/Paris?format=Current+weather+in+%l:+%c+%t+(feels+like+%f)+Humidity:+%h+Wind:+%w"
    response = requests.get(url, headers={'User-Agent': 'curl'})
    print(response.text)
except Exception as e:
    print(f"Error: {e}")

print("\n✅ This is a reliable fallback for weather!")