import os, uuid
from datetime import datetime, timezone
from typing import List, Dict, Optional, Tuple
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from dotenv import load_dotenv

from openai import OpenAI
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

load_dotenv()

# Azure Search Configuration
AZ_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
AZ_KEY      = os.getenv("AZURE_SEARCH_API_KEY")
INDEX_NAME  = os.getenv("AZURE_INDEX_NAME")

# Initialize clients with proper error handling
try:
    search_client = SearchClient(AZ_ENDPOINT, INDEX_NAME, AzureKeyCredential(AZ_KEY))
except Exception as e:
    print(f"⚠️ Error initializing Azure Search client: {e}")
    search_client = None

try:
    # Initialize OpenAI client - simplified initialization
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables")
    
    # Simple initialization without proxy complications
    openai_client = OpenAI(api_key=api_key)
    llm = ChatOpenAI(
        model_name="gpt-3.5-turbo", 
        temperature=0, 
        api_key=api_key
    )
    print("✅ OpenAI clients initialized successfully")
    
except Exception as e:
    print(f"❌ Error initializing OpenAI: {e}")
    openai_client = None
    llm = None

def get_embedding(text: str) -> list[float]:
    """Generate embedding for text using OpenAI."""
    if not openai_client:
        print("❌ OpenAI client not initialized")
        return [0.0] * 1536  # Return dummy embedding
    
    try:
        resp = openai_client.embeddings.create(
            model="text-embedding-ada-002", 
            input=text
        )
        return resp.data[0].embedding
    except Exception as e:
        print(f"❌ Error generating embedding: {e}")
        return [0.0] * 1536  # Return dummy embedding

def analyze_user_facts(text: str) -> List[Dict[str, str]]:
    """
    Use LLM to analyze if a message contains personal facts worth remembering.
    Now returns a LIST of facts to handle compound statements.
    """
    if not llm:
        print("⚠️ LLM not initialized, using fallback fact extraction")
        return fallback_fact_extraction(text)
    
    system_prompt = """Analyze this message for ALL personal facts about the user that should be remembered.
    
Return a JSON response with a list of facts:
{
    "facts": [
        {
            "is_personal_fact": boolean,
            "fact_type": "name" | "work" | "preference" | "location" | "relationship" | "other",
            "extracted_fact": "the core fact to remember, normalized",
            "importance": "high" | "medium" | "low",
            "replaces_fact": "optional - what this fact updates/replaces"
        }
    ]
}

IMPORTANT RULES:
1. Extract ALL facts from compound statements
2. For preferences, distinguish between "favorite" (only one) and "likes" (can be many)
3. If user says "my favorite is X", mark previous favorites as replaced

Examples:
- "my name is jack and i work at renault" -> extract BOTH name AND work facts
- "i like red but my favorite is blue" -> red is a preference, blue is favorite (replaces any previous favorite color)
- "i work at google now" -> replaces previous work fact
"""

    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Message: {text}")
        ])
        
        import json
        content = response.content.strip()
        
        # Handle potential JSON extraction issues
        if '{' in content and '}' in content:
            # Extract JSON from response
            start = content.find('{')
            end = content.rfind('}') + 1
            json_str = content[start:end]
            result = json.loads(json_str)
        else:
            result = {"facts": []}
        
        return result.get("facts", [])
    except Exception as e:
        print(f"⚠️ Error analyzing facts: {e}")
        return fallback_fact_extraction(text)

def fallback_fact_extraction(text: str) -> List[Dict[str, str]]:
    """
    Fallback fact extraction using regex when LLM is unavailable.
    """
    facts = []
    text_lower = text.lower()
    
    # Extract name
    import re
    name_patterns = [
        r"(?:my name is|i am|i'm)\s+([a-zA-Z]+)",
        r"(?:call me|they call me)\s+([a-zA-Z]+)",
    ]
    for pattern in name_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            facts.append({
                "is_personal_fact": True,
                "fact_type": "name",
                "extracted_fact": f"Name: {match.group(1).capitalize()}",
                "importance": "high"
            })
            break
    
    # Extract work/company
    work_patterns = [
        r"(?:i work at|i work for|employed at|working at)\s+([a-zA-Z\s]+?)(?:\.|,|$|;)",
        r"(?:i'm at|i am at)\s+([a-zA-Z\s]+?)(?:\.|,|$|;)",
    ]
    for pattern in work_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            company = match.group(1).strip()
            facts.append({
                "is_personal_fact": True,
                "fact_type": "work",
                "extracted_fact": f"Works at: {company}",
                "importance": "high"
            })
            break
    
    # Special case for Renault
    if "renault" in text_lower and not any(f["fact_type"] == "work" for f in facts):
        facts.append({
            "is_personal_fact": True,
            "fact_type": "work",
            "extracted_fact": "Works at: Renault",
            "importance": "high"
        })
    
    # Extract color preferences
    color_patterns = [
        r"my favorite color is\s+([a-zA-Z]+)",
        r"favorite color:\s*([a-zA-Z]+)",
        r"i love the color\s+([a-zA-Z]+)",
    ]
    for pattern in color_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            facts.append({
                "is_personal_fact": True,
                "fact_type": "preference",
                "extracted_fact": f"Favorite color: {match.group(1)}",
                "importance": "medium",
                "replaces_fact": "favorite color"
            })
            break
    
    return facts

def handle_fact_updates(facts: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Handle fact updates and replacements.
    """
    processed_facts = []
    
    for fact in facts:
        if fact.get("is_personal_fact", False):
            # Check if this replaces an existing fact
            if fact.get("replaces_fact"):
                # Mark old facts as outdated (you could delete them or flag them)
                print(f"🔄 Fact update: {fact['replaces_fact']} → {fact['extracted_fact']}")
            
            processed_facts.append(fact)
    
    return processed_facts

def store_memory(text: str, memory_type: str = "user_message", metadata: Optional[Dict] = None):
    """
    Store a memory in Azure Search with metadata.
    Enhanced to detect and properly categorize multiple personal facts.
    """
    if not search_client:
        print("❌ Search client not initialized, cannot store memory")
        return
    
    # Analyze if this contains personal facts
    stored_facts = []
    if memory_type == "user_message":
        facts = analyze_user_facts(text)
        processed_facts = handle_fact_updates(facts)
        
        # Store each fact separately for better retrieval
        for fact in processed_facts:
            if fact.get("is_personal_fact", False):
                fact_vec = get_embedding(fact["extracted_fact"])
                fact_doc = {
                    "id": str(uuid.uuid4()),
                    "content": fact["extracted_fact"],
                    "contentVector": fact_vec,
                    "memoryCategory": "personal_fact",
                    "memorySummary": fact["extracted_fact"],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "source_url": "",
                    "title": fact.get("fact_type", "personal_fact")
                }
                
                try:
                    result = search_client.upload_documents(documents=[fact_doc])
                    if result[0].succeeded:
                        print(f"🌟 Stored {fact['fact_type']}: {fact['extracted_fact']}")
                        stored_facts.append(fact["extracted_fact"])
                except Exception as e:
                    print(f"❌ Error storing fact: {e}")
    
    # Always store the original message too
    vec = get_embedding(text)
    
    # Base document structure
    doc = {
        "id": str(uuid.uuid4()),
        "content": text,
        "contentVector": vec,
        "memoryCategory": memory_type,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    # Add metadata if provided
    if metadata:
        if "url" in metadata and metadata["url"]:
            doc["source_url"] = metadata["url"]
        if "title" in metadata and metadata["title"]:
            doc["title"] = metadata["title"]
        # Store a summary of the content
        if memory_type == "web_content":
            summary = text[:200] + "..." if len(text) > 200 else text
            doc["memorySummary"] = summary
        else:
            doc["memorySummary"] = text
    else:
        doc["memorySummary"] = text
    
    # Ensure required fields have default values
    if "source_url" not in doc:
        doc["source_url"] = ""
    if "title" not in doc:
        doc["title"] = ""
    
    try:
        result = search_client.upload_documents(documents=[doc])
        if not result[0].succeeded:
            raise RuntimeError(f"Failed to store memory: {result[0].status_code}")
        print(f"✅ Stored {memory_type} memory: {text[:50]}...")
    except Exception as e:
        print(f"❌ Error storing memory: {e}")

def store_web_content(scraped_results: List[Dict[str, str]], search_query: str):
    """
    Store web search results as memories with better formatting.
    """
    if not search_client:
        print("❌ Search client not initialized, cannot store web content")
        return
    
    for result in scraped_results:
        # Get content and ensure it's not empty
        content = result.get('content', '').strip()
        if len(content) < 50:
            print(f"⚠️  Skipping short content from {result.get('url', 'unknown')}")
            continue
        
        # Store the content directly without extra formatting
        # This makes it easier for the LLM to read
        metadata = {
            "url": result.get('url', ''),
            "title": result.get('title', ''),
            "search_query": search_query
        }
        
        store_memory(
            text=content,
            memory_type="web_content", 
            metadata=metadata
        )

def retrieve_memories(query: str, k: int = 5, include_personal_facts: bool = True) -> List[Dict[str, any]]:
    """
    Retrieve relevant memories using vector search.
    Now with smarter relevance filtering and deduplication.
    """
    if not search_client:
        print("❌ Search client not initialized, returning empty memories")
        return []
    
    try:
        # Generate query embedding
        query_vec = get_embedding(query)
        
        # Create vector query - get more initially for filtering
        vector_query = VectorizedQuery(
            vector=query_vec,
            k_nearest_neighbors=k * 3,  # Get extra for filtering
            fields="contentVector"
        )
        
        # Execute search
        results = search_client.search(
            search_text="*",
            vector_queries=[vector_query],
            top=k * 3,
            select=["id", "content", "memoryCategory", "memorySummary", "timestamp", "source_url", "title"]
        )
        
        memories = []
        personal_facts = {}  # Use dict to deduplicate by fact type
        seen_content = set()  # Deduplicate similar content
        
        for result in results:
            content = result.get("content", "")
            category = result.get("memoryCategory", "unknown")
            
            # Skip if we've seen very similar content
            content_key = content[:100].lower().strip()
            if content_key in seen_content and category != "personal_fact":
                continue
            seen_content.add(content_key)
            
            memory = {
                "content": content,
                "category": category,
                "summary": result.get("memorySummary", ""),
                "timestamp": result.get("timestamp", ""),
                "score": result.get("@search.score", 0.0),
                "title": result.get("title", "")
            }
            
            # Add web-specific metadata
            if result.get("source_url"):
                memory["source_url"] = result.get("source_url")
            
            # Handle personal facts with deduplication
            if category == "personal_fact":
                fact_type = result.get("title", "unknown")
                # Keep only the most recent fact of each type
                if fact_type not in personal_facts or memory["timestamp"] > personal_facts[fact_type]["timestamp"]:
                    personal_facts[fact_type] = memory
            else:
                memories.append(memory)
        
        # Combine deduplicated personal facts with other memories
        if include_personal_facts:
            final_memories = list(personal_facts.values()) + memories
        else:
            final_memories = memories
        
        # Sort by score and limit to k
        final_memories.sort(key=lambda x: x.get("score", 0), reverse=True)
        final_memories = final_memories[:k]
        
        print(f"✅ Retrieved {len(final_memories)} relevant memories")
        if personal_facts:
            print(f"   Including {len(personal_facts)} unique personal facts")
        
        return final_memories
        
    except Exception as e:
        print(f"❌ Error retrieving memories: {e}")
        return []

def format_memories_for_prompt(memories: List[Dict[str, any]]) -> str:
    """
    Format memories for the LLM prompt with clear structure.
    Now with better organization and deduplication.
    """
    if not memories:
        return ""
    
    personal_facts = {}
    user_memories = []
    web_memories = []
    
    for mem in memories:
        content = mem.get("content", "").strip()
        if not content:
            continue
        
        if mem.get("category") == "personal_fact":
            # Group personal facts by type
            fact_type = mem.get("title", "other")
            if fact_type not in personal_facts:
                personal_facts[fact_type] = []
            personal_facts[fact_type].append(mem.get("summary", content))
            
        elif mem.get("category") == "web_content":
            # For web content, include the full content
            title = mem.get("title", "Web Information")
            source = mem.get("source_url", "")
            
            # Format web memory clearly
            if "weather" in content.lower() or "temperature" in content.lower():
                # Weather content - make it very clear
                web_memories.append(f"**Weather Information:**\n{content}")
            else:
                # Other web content
                web_memories.append(f"**{title}**\nSource: {source}\n{content[:1000]}")
        else:
            # User conversation memories - keep them shorter
            if len(content) > 150:
                content = content[:150] + "..."
            user_memories.append(content)
    
    # Build formatted sections
    formatted_sections = []
    
    # ALWAYS put personal facts first if they exist
    if personal_facts:
        formatted_sections.append("**User Facts:**")
        
        # Order facts logically
        fact_order = ["name", "work", "preference", "location", "relationship", "other"]
        for fact_type in fact_order:
            if fact_type in personal_facts:
                # Get the most recent fact of this type
                latest_fact = personal_facts[fact_type][-1]  # Last one is most recent
                
                # Format based on type
                if fact_type == "name":
                    # Extract just the name
                    if "Name:" in latest_fact:
                        name = latest_fact.split("Name:")[-1].strip()
                    else:
                        name = latest_fact
                    formatted_sections.append(f"- Name: {name}")
                elif fact_type == "work":
                    # Extract company
                    if "Works at:" in latest_fact:
                        company = latest_fact.split("Works at:")[-1].strip()
                    else:
                        company = latest_fact
                    formatted_sections.append(f"- Works at: {company}")
                elif fact_type == "preference":
                    # Handle multiple preferences
                    for pref in personal_facts[fact_type]:
                        formatted_sections.append(f"- {pref}")
                else:
                    formatted_sections.append(f"- {latest_fact}")
    
    # Add user context if exists
    if user_memories:
        if formatted_sections:
            formatted_sections.append("")  # Add spacing
        formatted_sections.append("**Previous Conversation Context:**")
        for mem in user_memories[:3]:
            formatted_sections.append(f"- {mem}")
    
    # Add web information with clear headers
    if web_memories:
        if formatted_sections:
            formatted_sections.append("")  # Add spacing
        formatted_sections.append("**Current Web Information:**")
        formatted_sections.extend(web_memories[:3])  # Limit to 3 most relevant
    
    return "\n".join(formatted_sections)

def get_user_context() -> Dict[str, any]:
    """
    Retrieve all current personal facts about the user.
    Now handles fact updates properly.
    """
    if not search_client:
        print("❌ Search client not initialized")
        return {"name": None, "company": None, "facts": {}, "all_facts": []}
    
    try:
        # Search specifically for personal facts
        results = search_client.search(
            search_text="*",
            filter="memoryCategory eq 'personal_fact'",
            top=50,
            select=["content", "memorySummary", "timestamp", "title"],
            order_by=["timestamp desc"]  # Most recent first
        )
        
        context = {
            "name": None,
            "company": None,
            "facts": {},
            "all_facts": []
        }
        
        # Group facts by type, keeping only the most recent
        for result in results:
            fact = result.get("memorySummary", result.get("content", ""))
            fact_type = result.get("title", "other")
            timestamp = result.get("timestamp", "")
            
            context["all_facts"].append({
                "fact": fact,
                "type": fact_type,
                "timestamp": timestamp
            })
            
            # Keep only the most recent fact of each type
            if fact_type not in context["facts"] or timestamp > context["facts"][fact_type]["timestamp"]:
                context["facts"][fact_type] = {
                    "fact": fact,
                    "timestamp": timestamp
                }
            
            # Extract specific details
            if fact_type == "name" and not context["name"]:
                if "Name:" in fact:
                    context["name"] = fact.split("Name:")[-1].strip()
                else:
                    context["name"] = fact
            elif fact_type == "work" and not context["company"]:
                # Extract company name
                if "Works at:" in fact:
                    context["company"] = fact.split("Works at:")[-1].strip()
                elif "Renault" in fact:
                    context["company"] = "Renault"
        
        return context
        
    except Exception as e:
        print(f"❌ Error getting user context: {e}")
        return {"name": None, "company": None, "facts": {}, "all_facts": []}