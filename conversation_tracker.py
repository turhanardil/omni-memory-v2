# conversation_tracker.py
"""
Tracks conversation history, shared facts, and user preferences.
Fixed storage issues and added historical data loading on startup.
"""

import os
import json
import uuid
import base64
import time
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
import hashlib

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from dotenv import load_dotenv

load_dotenv()

@dataclass
class SharedFact:
    """Represents a fact shared with the user"""
    id: str
    topic: str
    fact: str
    fact_hash: str  # For deduplication
    source: str
    timestamp: str
    shared_at: str  # When this was shared with user
    confidence: float
    thread_id: str
    embedding_text: str  # For semantic similarity

@dataclass
class ConversationTurn:
    """Represents one turn in a conversation"""
    id: str
    topic: str
    query: str
    response: str
    timestamp: str
    sources: List[str]
    thread_id: str
    facts_shared: List[str]  # Track which facts were shared in this turn

class ConversationTracker:
    """
    Tracks conversation history and shared information with temporal awareness.
    Now with proper persistence and historical loading.
    """
    
    def __init__(self, thread_id: str, session_id: Optional[str] = None):
        # Encode thread_id to be Azure Search compliant
        self.thread_id = self._encode_key(thread_id)
        self.raw_thread_id = thread_id
        self.session_id = session_id or self.thread_id
        
        # Initialize Azure Search client
        self.endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
        self.api_key = os.getenv("AZURE_SEARCH_API_KEY")
        self.index_name = "conversation-history"
        
        try:
            self.search_client = SearchClient(
                self.endpoint, 
                self.index_name, 
                AzureKeyCredential(self.api_key)
            )
            print(f"✅ ConversationTracker initialized for thread: {self.raw_thread_id}")
            
            # Load historical data on initialization
            self._load_historical_data()
            
        except Exception as e:
            print(f"⚠️ Error initializing conversation tracker: {e}")
            self.search_client = None
            # Initialize empty caches if Azure Search fails
            self._fact_cache = {}
            self._preference_cache = {}
            self._last_discussion_times = {}
            self._topics_cache = set()
    
    def _load_historical_data(self):
        """Load all historical conversation data from Azure Search into caches."""
        print("📚 Loading historical conversation data...")
        
        # Initialize caches
        self._fact_cache = {}
        self._preference_cache = {}
        self._last_discussion_times = {}
        self._topics_cache = set()
        
        if not self.search_client:
            return
        
        try:
            # Load all conversation turns to get topics and last discussion times
            conv_results = self.search_client.search(
                search_text="*",
                filter=f"thread_id eq '{self.thread_id}' and recordType eq 'conversation_turn'",
                order_by=["timestamp desc"],
                top=1000,
                select=["topic", "timestamp"]
            )
            
            for result in conv_results:
                topic = result["topic"]
                timestamp = result["timestamp"]
                
                self._topics_cache.add(topic)
                
                # Keep the most recent timestamp for each topic
                if topic not in self._last_discussion_times or timestamp > self._last_discussion_times[topic]:
                    self._last_discussion_times[topic] = timestamp
            
            print(f"   📝 Loaded {len(self._topics_cache)} topics with discussion times")
            
            # Load shared facts into cache
            fact_results = self.search_client.search(
                search_text="*",
                filter=f"thread_id eq '{self.thread_id}' and recordType eq 'shared_fact'",
                top=1000,
                select=["fact_hash", "fact", "topic", "shared_at"]
            )
            
            fact_count = 0
            for result in fact_results:
                fact_hash = result["fact_hash"]
                self._fact_cache[fact_hash] = SharedFact(
                    id=result.get("id", ""),
                    topic=result["topic"],
                    fact=result["fact"],
                    fact_hash=fact_hash,
                    source=result.get("source", ""),
                    timestamp=result.get("timestamp", ""),
                    shared_at=result["shared_at"],
                    confidence=result.get("confidence", 0.8),
                    thread_id=self.thread_id,
                    embedding_text=result.get("embedding_text", result["fact"])
                )
                fact_count += 1
            
            print(f"   📚 Loaded {fact_count} shared facts into cache")
            
            # Load user preferences
            pref_results = self.search_client.search(
                search_text="*",
                filter=f"thread_id eq '{self.thread_id}' and recordType eq 'user_preference'",
                top=100
            )
            
            for result in pref_results:
                key = result["preference_key"]
                value = json.loads(result["preference_value"])
                self._preference_cache[key] = value
            
            print(f"   ⚙️  Loaded {len(self._preference_cache)} user preferences")
            print("✅ Historical data loading complete")
            
        except Exception as e:
            print(f"❌ Error loading historical data: {e}")
    
    def _encode_key(self, key: str) -> str:
        """Encode keys to be Azure Search compliant (alphanumeric, _, -, =)"""
        # Replace dots and other special characters
        encoded = key.replace(".", "_").replace(":", "_").replace("/", "_")
        # If still has invalid chars, use base64
        if not all(c.isalnum() or c in ['_', '-', '='] for c in encoded):
            encoded = base64.urlsafe_b64encode(key.encode()).decode().rstrip('=')
        return encoded
    
    def add_shared_fact(self, topic: str, fact: str, source: str, confidence: float = 0.8) -> Optional[str]:
        """Add a fact that was shared with the user, returns fact ID if stored."""
        if not self.search_client:
            return None
        
        # Create hash for deduplication
        fact_hash = hashlib.md5(fact.lower().strip().encode()).hexdigest()
        
        # Check cache first
        if fact_hash in self._fact_cache:
            print(f"📝 Fact already in cache: {fact[:50]}...")
            return self._fact_cache[fact_hash].id
        
        # Check if similar fact already exists in Azure
        similar_facts = self._find_similar_facts(fact)
        if similar_facts:
            print(f"📝 Similar fact already tracked: {fact[:50]}...")
            return similar_facts[0].get("id")
        
        fact_id = str(uuid.uuid4())
        shared_fact = SharedFact(
            id=fact_id,
            topic=topic,
            fact=fact,
            fact_hash=fact_hash,
            source=source,
            timestamp=datetime.now(timezone.utc).isoformat(),
            shared_at=datetime.now(timezone.utc).isoformat(),
            confidence=confidence,
            thread_id=self.thread_id,
            embedding_text=fact
        )
        
        try:
            # Store in Azure Search
            doc = {
                **asdict(shared_fact),
                "recordType": "shared_fact",
                "session_id": self.session_id
            }
            
            result = self.search_client.upload_documents(documents=[doc])
            if result[0].succeeded:
                print(f"✅ Tracked fact: {fact[:50]}...")
                # Update caches
                self._fact_cache[fact_hash] = shared_fact
                self._last_discussion_times[topic] = datetime.now(timezone.utc).isoformat()
                self._topics_cache.add(topic)
                
                # Force a small delay to ensure indexing
                time.sleep(0.5)
                
                return fact_id
        except Exception as e:
            print(f"❌ Error tracking fact: {e}")
        
        return None
    
    def _find_similar_facts(self, fact: str, threshold: float = 0.85) -> List[Dict]:
        """Find semantically similar facts to prevent duplication."""
        if not self.search_client:
            return []
        
        try:
            # First check exact hash match
            fact_hash = hashlib.md5(fact.lower().strip().encode()).hexdigest()
            
            # Check cache
            if fact_hash in self._fact_cache:
                return [{"id": self._fact_cache[fact_hash].id}]
            
            # Search for similar facts
            results = self.search_client.search(
                search_text=fact,
                filter=f"thread_id eq '{self.thread_id}' and recordType eq 'shared_fact'",
                top=5,
                include_total_count=True
            )
            
            similar_facts = []
            for result in results:
                # Check semantic similarity (using search score as proxy)
                if result.get("@search.score", 0) > threshold:
                    similar_facts.append(result)
                # Also check hash match
                elif result.get("fact_hash") == fact_hash:
                    similar_facts.append(result)
            
            return similar_facts
            
        except Exception as e:
            print(f"⚠️ Error finding similar facts: {e}")
            return []
    
    def get_shared_facts(self, topic: str, after_timestamp: Optional[str] = None) -> List[SharedFact]:
        """Get all facts shared about a topic, optionally after a specific timestamp."""
        # First check cache
        cached_facts = [f for f in self._fact_cache.values() if f.topic == topic]
        
        # If we have cache and no temporal filter, return from cache
        if cached_facts and not after_timestamp:
            return sorted(cached_facts, key=lambda f: f.shared_at, reverse=True)
        
        # Otherwise query Azure Search
        if not self.search_client:
            return cached_facts
        
        try:
            # Build filter
            filter_parts = [
                f"topic eq '{topic}'",
                f"thread_id eq '{self.thread_id}'",
                "recordType eq 'shared_fact'"
            ]
            
            if after_timestamp:
                filter_parts.append(f"shared_at gt '{after_timestamp}'")
            
            filter_str = " and ".join(filter_parts)
            
            results = self.search_client.search(
                search_text="*",
                filter=filter_str,
                order_by=["shared_at desc"],
                top=50
            )
            
            facts = []
            for result in results:
                fact = SharedFact(
                    id=result["id"],
                    topic=result["topic"],
                    fact=result["fact"],
                    fact_hash=result["fact_hash"],
                    source=result["source"],
                    timestamp=result["timestamp"],
                    shared_at=result.get("shared_at", result["timestamp"]),
                    confidence=result.get("confidence", 0.8),
                    thread_id=result["thread_id"],
                    embedding_text=result.get("embedding_text", result["fact"])
                )
                facts.append(fact)
                
                # Update cache
                self._fact_cache[fact.fact_hash] = fact
            
            return facts
            
        except Exception as e:
            print(f"❌ Error retrieving facts: {e}")
            return cached_facts
    
    def add_conversation_turn(self, topic: str, query: str, response: str, 
                            sources: List[str], fact_ids: List[str] = None):
        """Record a conversation turn with facts shared."""
        if not self.search_client:
            return
        
        turn_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        
        turn = ConversationTurn(
            id=turn_id,
            topic=topic,
            query=query,
            response=response,
            timestamp=timestamp,
            sources=sources,
            thread_id=self.thread_id,
            facts_shared=fact_ids or []
        )
        
        try:
            # Store with proper array fields
            doc = {
                "id": turn_id,
                "topic": topic,
                "query": query,
                "response": response,
                "timestamp": timestamp,
                "sources": sources,  # Now properly stored as array
                "facts_shared": fact_ids or [],  # Now properly stored as array
                "thread_id": self.thread_id,
                "recordType": "conversation_turn",
                "session_id": self.session_id
            }
            
            result = self.search_client.upload_documents(documents=[doc])
            if result[0].succeeded:
                print(f"✅ Tracked conversation turn")
                # Update caches
                self._last_discussion_times[topic] = timestamp
                self._topics_cache.add(topic)
                
                # Force a small delay to ensure indexing
                time.sleep(0.5)
            else:
                print(f"❌ Failed to track conversation: {result[0].error}")
        except Exception as e:
            print(f"❌ Error tracking conversation: {e}")
    
    def get_conversation_history(self, topic: str, limit: int = 10) -> List[Dict]:
        """Get conversation history for a topic."""
        if not self.search_client:
            return []
        
        try:
            results = self.search_client.search(
                search_text="*",
                filter=f"topic eq '{topic}' and thread_id eq '{self.thread_id}' and recordType eq 'conversation_turn'",
                order_by=["timestamp desc"],
                top=limit
            )
            
            history = []
            for result in results:
                history.append({
                    "query": result["query"],
                    "response": result["response"],
                    "timestamp": result["timestamp"],
                    "sources": result.get("sources", []),
                    "facts_shared": result.get("facts_shared", [])
                })
            
            return list(reversed(history))  # Return in chronological order
            
        except Exception as e:
            print(f"❌ Error retrieving history: {e}")
            return []
    
    def get_last_discussion_time(self, topic: str) -> Optional[str]:
        """Get the timestamp of the last discussion about a topic."""
        # Check cache first
        if topic in self._last_discussion_times:
            return self._last_discussion_times[topic]
        
        # If not in cache, query Azure Search
        if not self.search_client:
            return None
        
        try:
            results = self.search_client.search(
                search_text="*",
                filter=f"topic eq '{topic}' and thread_id eq '{self.thread_id}' and recordType eq 'conversation_turn'",
                order_by=["timestamp desc"],
                top=1,
                select=["timestamp"]
            )
            
            for result in results:
                timestamp = result["timestamp"]
                self._last_discussion_times[topic] = timestamp
                return timestamp
                
        except Exception as e:
            print(f"❌ Error getting last discussion time: {e}")
        
        return None
    
    def get_all_topics(self) -> List[str]:
        """Get all topics discussed in this thread."""
        # Return from cache if available
        if self._topics_cache:
            return list(self._topics_cache)
        
        # Otherwise query Azure Search
        if not self.search_client:
            return []
        
        try:
            # Get topics by searching for all conversation turns
            results = self.search_client.search(
                search_text="*",
                filter=f"thread_id eq '{self.thread_id}' and recordType eq 'conversation_turn'",
                select=["topic"],
                top=1000
            )
            
            topics = set()
            for result in results:
                if "topic" in result:
                    topics.add(result["topic"])
                    self._topics_cache.add(result["topic"])
            
            return list(topics)
            
        except Exception as e:
            print(f"❌ Error getting topics: {e}")
            return []
    
    def update_preference(self, key: str, value: Any):
        """Update user preferences."""
        if not self.search_client:
            self._preference_cache[key] = value
            return
        
        # Encode the preference key
        pref_id = f"pref_{self.thread_id}_{self._encode_key(key)}"
        
        try:
            doc = {
                "id": pref_id,
                "thread_id": self.thread_id,
                "preference_key": key,
                "preference_value": json.dumps(value),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "recordType": "user_preference",
                "session_id": self.session_id
            }
            
            result = self.search_client.merge_or_upload_documents(documents=[doc])
            if result[0].succeeded:
                self._preference_cache[key] = value
                
                # Force a small delay to ensure indexing
                time.sleep(0.5)
                
        except Exception as e:
            print(f"❌ Error updating preference: {e}")
            # Still update cache even if Azure fails
            self._preference_cache[key] = value
    
    def get_user_preferences(self) -> Dict[str, Any]:
        """Get all user preferences."""
        # Always return from cache since we load on init
        return self._preference_cache.copy()
    
    def increment_interaction_count(self):
        """Increment the interaction counter."""
        current = self._preference_cache.get("interaction_count", 0)
        self.update_preference("interaction_count", current + 1)
    
    def get_interaction_count(self) -> int:
        """Get total interaction count."""
        return self._preference_cache.get("interaction_count", 0)
    
    def get_facts_summary(self, topic: str) -> Dict[str, Any]:
        """Get a summary of facts shared about a topic."""
        facts = self.get_shared_facts(topic)
        
        if not facts:
            return {
                "topic": topic,
                "fact_count": 0,
                "last_shared": None,
                "facts": []
            }
        
        return {
            "topic": topic,
            "fact_count": len(facts),
            "last_shared": max(f.shared_at for f in facts),
            "first_shared": min(f.shared_at for f in facts),
            "facts": [
                {
                    "fact": f.fact,
                    "shared_at": f.shared_at,
                    "source": f.source
                } for f in facts
            ]
        }
    
    def force_refresh(self):
        """Force a refresh of cached data from Azure Search."""
        print("🔄 Forcing data refresh from Azure Search...")
        # Clear caches
        self._fact_cache.clear()
        self._preference_cache.clear()
        self._last_discussion_times.clear()
        self._topics_cache.clear()
        
        # Reload data
        self._load_historical_data()
        
    def wait_for_indexing(self, seconds: float = 1.0):
        """Wait for Azure Search indexing to complete."""
        time.sleep(seconds)