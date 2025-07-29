#!/usr/bin/env python3
"""
Check what's actually stored in memory after search
Run: python check_memories.py
"""

import memory_manager

# Retrieve memories for weather query
print("🧠 Checking stored memories for weather query...\n")

memories = memory_manager.retrieve_memories("weather in paris", k=5)

if memories:
    for i, mem in enumerate(memories, 1):
        print(f"\n{'='*60}")
        print(f"Memory #{i}")
        print(f"Category: {mem.get('category')}")
        print(f"Score: {mem.get('score', 0):.3f}")
        
        content = mem.get('content', '')
        print(f"\nContent preview (500 chars):")
        print("-" * 60)
        print(content[:500])
        print("-" * 60)
        
        # Check for actual weather data
        if mem.get('category') == 'web_content':
            content_lower = content.lower()
            print("\n🔍 Content analysis:")
            print(f"- Has temperature: {'°' in content or 'degrees' in content_lower}")
            print(f"- Mentions Paris: {'paris' in content_lower}")
            print(f"- Has weather words: {any(w in content_lower for w in ['weather', 'temperature', 'forecast', 'cloudy', 'sunny', 'rain'])}")
            
            # Try to find temperature
            import re
            temps = re.findall(r'\d+°[CF]|\d+\s*degrees', content)
            if temps:
                print(f"- Found temps: {temps[:3]}")
else:
    print("❌ No memories found")

# Also check formatted prompt
print("\n\n📝 Formatted prompt that LLM sees:")
print("="*60)
formatted = memory_manager.format_memories_for_prompt(memories)
print(formatted)
print("="*60)

print("\n💡 If no weather data visible:")
print("1. Sites might use JavaScript (can't scrape)")
print("2. Try the weather API solution instead")
print("3. Or use Serper API (better scraping)")