# web_search.py - Enhanced with user context awareness
"""
Web search with intelligent LLM-based query analysis and user context.
Supports direct weather fallback and DuckDuckGo for everything else.
No API keys needed for search!
"""

import os
import re
import json
import requests
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

load_dotenv()

# Initialize LLM for query analysis
query_analyzer = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)

def extract_user_context(memories: List[Dict[str, any]]) -> Dict[str, str]:
    """
    Extract user context from memories (name, company, preferences, etc.)
    """
    context = {
        "name": None,
        "company": None,
        "role": None,
        "preferences": [],
        "locations": [],
        "other_facts": []
    }
    
    for mem in memories:
        content = mem.get("content", "").lower()
        original_content = mem.get("content", "")
        
        # Extract name
        if "my name is" in content or "i am" in content:
            name_match = re.search(r"(?:my name is|i am)\s+([a-zA-Z]+)", original_content, re.IGNORECASE)
            if name_match:
                context["name"] = name_match.group(1)
        
        # Extract company
        if "i work at" in content or "work for" in content:
            company_match = re.search(r"(?:work at|work for)\s+([a-zA-Z\s]+?)(?:\.|,|$)", original_content, re.IGNORECASE)
            if company_match:
                context["company"] = company_match.group(1).strip()
        
        # Extract preferences
        if "favorite" in content or "i like" in content or "i love" in content:
            context["preferences"].append(original_content)
        
        # Extract locations
        if "i live in" in content or "i'm from" in content:
            location_match = re.search(r"(?:live in|i'm from)\s+([a-zA-Z\s]+?)(?:\.|,|$)", original_content, re.IGNORECASE)
            if location_match:
                context["locations"].append(location_match.group(1).strip())
    
    return context

def analyze_query_with_llm(query: str, memories: List[Dict[str, any]]) -> Dict[str, any]:
    """
    Use LLM to intelligently analyze the query and determine if web search is needed.
    Now includes user context awareness.
    """
    # Extract user context from memories
    user_context = extract_user_context(memories)
    
    # Prepare memory context for the LLM
    memory_context = ""
    if memories:
        web_memories = [m for m in memories if m.get("category") == "web_content"]
        user_memories = [m for m in memories if m.get("category") == "user_message"]
        
        if user_memories:
            memory_context += "\nRecent user messages:\n"
            for i, mem in enumerate(user_memories[-5:]):  # Last 5 user messages
                memory_context += f"- {mem.get('content', '')}\n"
        
        if web_memories:
            memory_context += f"\nExisting web content in memory (count: {len(web_memories)}):\n"
            for i, mem in enumerate(web_memories[:3]):
                timestamp = mem.get("timestamp", "")
                summary = mem.get("content", "")[:100] + "..."
                memory_context += f"{i+1}. {summary} (from: {timestamp})\n"
    
    # Build user context string
    user_context_str = ""
    if user_context["name"]:
        user_context_str += f"User's name: {user_context['name']}\n"
    if user_context["company"]:
        user_context_str += f"User works at: {user_context['company']}\n"
    if user_context["locations"]:
        user_context_str += f"User's locations: {', '.join(user_context['locations'])}\n"
    
    system_prompt = """You are a query analyzer that determines if a web search is needed.
    
CRITICAL: When the user uses words like "our", "my company", "we", etc., you MUST use their personal context to enhance the search query.

Analyze the user's query and return a JSON response with:
{
    "needs_search": boolean,
    "query_type": "weather" | "news" | "stock" | "factual" | "personal" | "general",
    "search_query": "optimized search query with user context if search is needed",
    "reason": "brief explanation of your decision",
    "temporal_requirement": "immediate" | "recent" | "historical" | "none",
    "context_used": "what user context was applied to enhance the query"
}

Guidelines:
1. Personal queries (greetings, user info, etc.) never need search
2. Weather queries ALWAYS need search for current conditions
3. News queries usually need search unless asking about historical events
4. Questions about current events, recent happenings, or anything time-sensitive need search
5. Questions asking "what's going on", "what's happening", "tell me about" regarding current topics need search
6. Factual questions about stable information don't need search unless user explicitly asks for current/latest
7. If the query implies wanting current information (even without explicit temporal words), mark it for search

IMPORTANT CONTEXT RULES:
- If user says "our CEO" and they work at Company X, search for "Company X CEO"
- If user says "my company" and they work at Company Y, search for "Company Y"
- Always enhance search queries with relevant user context
- Include the company name, location, or other relevant details in the search query

Current date: Wednesday, July 23, 2025"""

    user_prompt = f"""Query: {query}

User Context:
{user_context_str if user_context_str else "No personal context available"}

{memory_context}"""
    
    try:
        response = query_analyzer.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])
        
        # Parse the JSON response
        result = json.loads(response.content)
        
        # Validate and enhance the result
        result["query_type"] = result.get("query_type", "general")
        result["needs_search"] = bool(result.get("needs_search", False))
        result["search_query"] = result.get("search_query", query if result["needs_search"] else "")
        result["reason"] = result.get("reason", "LLM analysis")
        result["temporal_requirement"] = result.get("temporal_requirement", "none")
        result["context_used"] = result.get("context_used", "None")
        result["user_context"] = user_context  # Include for debugging
        
        print(f"🤖 LLM Analysis: {result['reason']}")
        print(f"   Query Type: {result['query_type']}, Temporal: {result['temporal_requirement']}")
        if result.get("context_used") != "None":
            print(f"   Context Applied: {result['context_used']}")
        if result["needs_search"]:
            print(f"   Enhanced Query: '{result['search_query']}'")
        
        return result
        
    except Exception as e:
        print(f"⚠️ LLM analysis failed, falling back to keyword analysis: {e}")
        # Fallback to simplified keyword analysis
        return fallback_query_analysis(query, memories, user_context)

def fallback_query_analysis(query: str, memories: List[Dict[str, any]], user_context: Dict[str, str]) -> Dict[str, any]:
    """
    Fallback keyword-based analysis if LLM fails.
    Now context-aware.
    """
    query_lower = query.lower()
    
    # Check for personal queries
    if any(phrase in query_lower for phrase in ['hi', 'hello', 'my name', 'who am i']):
        return {
            "needs_search": False,
            "query_type": "personal",
            "search_query": "",
            "reason": "Personal query",
            "temporal_requirement": "none",
            "context_used": "None",
            "user_context": user_context
        }
    
    # Enhance query with context for "our" or "my company" references
    enhanced_query = query
    context_used = "None"
    
    if user_context["company"] and any(word in query_lower for word in ["our", "my company", "we"]):
        # Replace generic terms with specific company
        enhanced_query = query
        for term in ["our CEO", "our company", "my company"]:
            if term.lower() in query_lower:
                enhanced_query = enhanced_query.replace(term, f"{user_context['company']} {term.split()[-1]}")
                context_used = f"Company: {user_context['company']}"
    
    # Weather always needs search
    if any(word in query_lower for word in ["weather", "temperature", "rain", "snow"]):
        return {
            "needs_search": True,
            "query_type": "weather",
            "search_query": enhanced_query,
            "reason": "Weather query needs current data",
            "temporal_requirement": "immediate",
            "context_used": context_used,
            "user_context": user_context
        }
    
    # News-like queries - be more lenient
    news_indicators = ["news", "happening", "going on", "latest", "recent", "current", "update", "situation", "resignation", "announcement"]
    if any(word in query_lower for word in news_indicators):
        return {
            "needs_search": True,
            "query_type": "news",
            "search_query": enhanced_query,
            "reason": "Query about current events",
            "temporal_requirement": "recent",
            "context_used": context_used,
            "user_context": user_context
        }
    
    # Default to search if uncertain and query seems informational
    if "?" in query and len(query.split()) > 3:
        return {
            "needs_search": True,
            "query_type": "general",
            "search_query": enhanced_query,
            "reason": "Informational query that may benefit from search",
            "temporal_requirement": "none",
            "context_used": context_used,
            "user_context": user_context
        }
    
    return {
        "needs_search": False,
        "query_type": "general",
        "search_query": "",
        "reason": "General query, no search needed",
        "temporal_requirement": "none",
        "context_used": context_used,
        "user_context": user_context
    }

def get_weather_direct(location: str) -> Optional[str]:
    """
    Get weather directly from wttr.in - FREE, no API key!
    Returns formatted weather string that's easy for LLM to read.
    """
    try:
        # Clean location name
        location = location.strip()
        
        # Get detailed weather with clear formatting
        url = f"https://wttr.in/{location}"
        params = {
            'format': 'Weather in %l: %t (feels like %f), %C. Humidity: %h, Wind: %w'
        }
        
        response = requests.get(url, params=params, headers={'User-Agent': 'curl'}, timeout=5)
        
        if response.status_code == 200:
            weather_text = response.text.strip()
            # Make it even clearer for the LLM
            enhanced_text = f"Current weather report for {location}:\n{weather_text}\n\nThis is real-time weather data retrieved just now."
            return enhanced_text
            
    except Exception as e:
        print(f"⚠️ Weather service error: {e}")
    
    return None

def search_duckduckgo(query: str, num_results: int = 5) -> List[Dict[str, str]]:
    """Search using DuckDuckGo HTML API (no API key needed!)"""
    
    print(f"🦆 Searching DuckDuckGo for: '{query}'")
    
    try:
        url = "https://html.duckduckgo.com/html/"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        data = {'q': query}
        
        response = requests.post(url, headers=headers, data=data, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        results = []
        
        for result in soup.find_all('div', class_='links_main')[:num_results]:
            link = result.find('a', class_='result__a')
            snippet_div = result.find('a', class_='result__snippet')
            
            if link and link.get('href'):
                results.append({
                    'url': link.get('href', ''),
                    'title': link.text.strip(),
                    'snippet': snippet_div.text.strip() if snippet_div else ''
                })
        
        print(f"✅ DuckDuckGo returned {len(results)} results")
        return results
        
    except Exception as e:
        print(f"❌ DuckDuckGo search error: {e}")
        return []

def scrape_content(url: str, max_chars: int = 3000) -> Optional[str]:
    """Scrape text content from a URL."""
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml',
            'Accept-Language': 'en-US,en;q=0.9'
        }
        
        response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove unwanted elements
        for element in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
            element.decompose()
        
        # Get all text
        text = soup.get_text(separator=' ', strip=True)
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        clean_text = ' '.join(chunk for chunk in chunks if chunk)
        
        # Remove excessive whitespace
        clean_text = ' '.join(clean_text.split())
        
        if len(clean_text) > max_chars:
            clean_text = clean_text[:max_chars] + "..."
        
        return clean_text if len(clean_text) > 100 else None
        
    except Exception as e:
        print(f"⚠️  Error scraping {url}: {e}")
        return None

def search_and_scrape(query: str, num_urls: int = 3) -> List[Dict[str, str]]:
    """
    Enhanced search and scrape with weather fallback.
    """
    
    query_type = categorize_query_type(query)
    
    # For weather queries, ALWAYS use direct weather service
    if query_type == "weather":
        # Extract location with multiple patterns
        location = None
        patterns = [
            r'weather\s+(?:in\s+)?([a-zA-Z\s]+?)(?:\s+today|\s+now|\s+tomorrow|\s*$)',
            r'(?:in|at)\s+([a-zA-Z\s]+?)(?:\s+weather|\s+today)',
            r"what'?s?\s+the\s+weather\s+(?:like\s+)?(?:in\s+)?([a-zA-Z\s]+)",
            r'how\s+is\s+the\s+weather\s+(?:in\s+)?([a-zA-Z\s]+)',
            r'([a-zA-Z\s]+?)\s+weather',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                location = match.group(1).strip()
                # Remove common words
                if location.lower() not in ['the', 'is', 'today', 'now', 'like', 'tomorrow']:
                    break
        
        if location:
            print(f"🌤️ Getting weather for: {location}")
            weather = get_weather_direct(location)
            
            if weather:
                print("✅ Got direct weather data!")
                return [{
                    'url': f'https://wttr.in/{location}',
                    'title': f'Current Weather in {location}',
                    'content': weather,
                    'query_type': 'weather'
                }]
            else:
                print("⚠️ Direct weather failed")
    
    # For non-weather queries, use DuckDuckGo
    print(f"🌐 Web search for: '{query}'")
    
    search_results = search_duckduckgo(query)
    
    if not search_results:
        print("❌ No search results")
        # For weather, try one more time with just the location
        if query_type == "weather" and location:
            weather = get_weather_direct(location)
            if weather:
                return [{
                    'url': f'https://wttr.in/{location}',
                    'title': f'Weather in {location}',
                    'content': weather,
                    'query_type': 'weather'
                }]
        return []
    
    scraped_results = []
    
    for i, result in enumerate(search_results[:num_urls + 2]):
        url = result['url']
        title = result['title']
        
        print(f"📄 [{i+1}/{min(len(search_results), num_urls+2)}] Scraping: {title[:50]}...")
        content = scrape_content(url)
        
        if content:
            scraped_results.append({
                'url': url,
                'title': title,
                'content': content,
                'query_type': query_type
            })
            print(f"   ✅ Successfully scraped {len(content)} chars")
            
            if len(scraped_results) >= num_urls:
                break
        else:
            print(f"   ❌ Failed to scrape")
    
    print(f"✅ Total results: {len(scraped_results)}")
    return scraped_results

def categorize_query_type(query: str) -> str:
    """Simple categorization for backward compatibility."""
    query_lower = query.lower()
    
    if any(word in query_lower for word in ["weather", "temperature", "rain", "snow", "forecast"]):
        return "weather"
    elif any(word in query_lower for word in ["news", "latest", "recent", "happening", "update", "resignation"]):
        return "news"
    elif any(word in query_lower for word in ["stock", "price", "market"]):
        return "stock"
    else:
        return "general"

def is_content_fresh(timestamp_str: str, query_type: str, temporal_requirement: str = "none") -> bool:
    """Check if content is fresh enough based on query requirements."""
    try:
        if timestamp_str.endswith('Z'):
            timestamp = datetime.fromisoformat(timestamp_str[:-1] + '+00:00')
        else:
            timestamp = datetime.fromisoformat(timestamp_str)
        
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        
        # Adjust freshness requirements based on temporal needs
        if temporal_requirement == "immediate":
            max_age_hours = 1
        elif temporal_requirement == "recent":
            max_age_hours = 24
        else:
            max_age_hours = {
                "weather": 1,
                "news": 12,
                "stock": 4,
                "general": 48
            }.get(query_type, 48)
        
        age_limit = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
        return timestamp > age_limit
        
    except Exception:
        return False

def should_search_web(user_input: str, retrieved_memories: List[Dict[str, any]]) -> Dict[str, any]:
    """
    Determine if web search is needed using LLM analysis with user context.
    """
    
    # Use LLM to analyze the query with context
    analysis = analyze_query_with_llm(user_input, retrieved_memories)
    
    # Count existing web items and fresh items
    web_items = 0
    fresh_items = 0
    
    for mem in retrieved_memories:
        if mem.get("category") == "web_content":
            web_items += 1
            if is_content_fresh(
                mem.get("timestamp", ""), 
                analysis["query_type"],
                analysis.get("temporal_requirement", "none")
            ):
                fresh_items += 1
    
    # Add memory stats to the analysis
    analysis["existing_web_items"] = web_items
    analysis["fresh_web_items"] = fresh_items
    
    # Override LLM decision if we already have fresh content for non-immediate queries
    if analysis["temporal_requirement"] != "immediate" and fresh_items > 0:
        if not any(word in user_input.lower() for word in ["more", "other", "else", "additional"]):
            analysis["needs_search"] = False
            analysis["reason"] += f" (Found {fresh_items} fresh items in memory)"
    
    return analysis

def validate_web_content_relevance(content: str, query: str, query_type: str = None) -> bool:
    """Always return True - we trust our search results."""
    return True

# Test functionality
if __name__ == "__main__":
    print("🧪 Testing context-aware web search\n")
    
    # Simulate memories with user context
    test_memories = [
        {"content": "User: my name is Jack", "category": "user_message"},
        {"content": "User: i work at renault", "category": "user_message"},
        {"content": "User: my favorite color is blue", "category": "user_message"}
    ]
    
    test_queries = [
        "any updates on our CEO's resignation?",
        "what's the latest news about my company?",
        "how is our stock performing?",
        "weather in paris",
        "hello"
    ]
    
    for query in test_queries:
        print(f"\n📝 Testing: '{query}'")
        decision = should_search_web(query, test_memories)
        print(f"   Needs search: {decision['needs_search']}")
        print(f"   Type: {decision['query_type']}")
        print(f"   Context used: {decision.get('context_used', 'None')}")
        print(f"   Reason: {decision['reason']}")
        
        if decision['needs_search']:
            print(f"   Enhanced query: '{decision['search_query']}'")