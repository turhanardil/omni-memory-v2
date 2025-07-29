# context_manager.py
"""
Context Manager LLM - Manages conversation context, tracks shared information,
and enhances queries based on conversation history with proper temporal filtering.
Fixed: Better LLM handling, query classification, and personal fact detection.
"""

import os
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from collections import defaultdict
import hashlib
import time

from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential

from conversation_tracker import ConversationTracker, SharedFact
import memory_manager

load_dotenv()

@dataclass
class QueryAnalysis:
    """Enhanced query analysis with conversation context"""
    original_query: str
    enhanced_query: str
    query_type: str  # personal_fact, temporal_update, news, weather, etc.
    temporal_requirement: str
    conversation_context: Dict[str, Any]
    search_constraints: List[str]
    information_gaps: List[str]
    user_intent: str
    requires_search: bool
    prompt_instructions: str
    exclude_facts: List[str]
    is_personal_query: bool  # New field

class ContextManagerLLM:
    """
    Intelligent context manager that tracks conversations and enhances queries.
    Fixed: Better error handling, simpler prompts, personal query detection.
    """
    
    def __init__(self, thread_id: str, session_id: Optional[str] = None):
        self.thread_id = thread_id
        self.session_id = session_id
        self.tracker = ConversationTracker(thread_id, session_id)
        
        # Initialize LLM with retry logic
        api_key = os.getenv("OPENAI_API_KEY")
        
        # Use gpt-3.5-turbo for better reliability
        self.llm = ChatOpenAI(
            model_name="gpt-3.5-turbo",
            temperature=0,
            api_key=api_key,
            max_retries=3,
            request_timeout=30
        )
        
        # Load user preferences
        self.user_preferences = self.tracker.get_user_preferences()
        
        # Track facts shared in current session
        self._current_session_facts = []
        
        # Personal query patterns
        self._personal_patterns = {
            "name": ["what is my name", "who am i", "my name"],
            "color": ["what is my favorite color", "my favorite color", "my fav color", 
                     "which color do i like", "what color do i like", "what is my fav color"],
            "work": ["where do i work", "what company", "my company", "who do i work for"],
            "location": ["where do i live", "where am i from", "my location"],
            "preference": ["what do i like", "my favorite", "my preference"]
        }
    
    def _is_personal_fact_query(self, query: str) -> Tuple[bool, str]:
        """Detect if this is a personal fact query and return the fact type."""
        query_lower = query.lower().strip()
        
        # Check each pattern
        for fact_type, patterns in self._personal_patterns.items():
            for pattern in patterns:
                if pattern in query_lower:
                    return True, fact_type
        
        # Check for generic personal queries
        if any(word in query_lower for word in ["my", "i", "me"]) and \
           any(word in query_lower for word in ["favorite", "name", "work", "live", "like"]) and \
           "?" in query:
            return True, "personal"
        
        return False, ""
    
    def analyze_query_with_context(self, query: str, memories: List[Dict]) -> QueryAnalysis:
        """
        Analyze query with full conversation context and temporal awareness.
        Fixed: Better personal query detection and simpler LLM prompts.
        """
        # First check if this is a personal fact query
        is_personal, personal_type = self._is_personal_fact_query(query)
        
        # Get conversation history for this topic
        topic = self._extract_topic(query)
        conversation_history = self.tracker.get_conversation_history(topic)
        
        # Get last discussion time BEFORE getting facts
        last_discussion_time = self.tracker.get_last_discussion_time(topic)
        
        # Check if asking for updates
        is_asking_for_updates = any(word in query.lower() for word in 
                                  ["new", "update", "latest", "recent", "any more", 
                                   "anything new", "as of now", "since"])
        
        # Handle personal queries differently
        if is_personal and not is_asking_for_updates:
            # For personal queries, we want to return the fact, not check for updates
            user_context = memory_manager.get_user_context()
            
            return QueryAnalysis(
                original_query=query,
                enhanced_query=query,
                query_type="personal_fact",
                temporal_requirement="none",
                conversation_context={
                    "topic": personal_type,
                    "user_context": user_context,
                    "is_personal": True
                },
                search_constraints=[],
                information_gaps=[],
                user_intent=f"User wants to know their {personal_type}",
                requires_search=False,
                prompt_instructions=f"Simply state the user's {personal_type} if known",
                exclude_facts=[],
                is_personal_query=True
            )
        
        # For non-personal queries or update queries, continue with normal analysis
        shared_facts = self.tracker.get_shared_facts(topic)
        
        # Get facts to exclude based on temporal requirements
        if is_asking_for_updates and last_discussion_time:
            facts_to_exclude = [f for f in shared_facts if f.shared_at < last_discussion_time]
        else:
            facts_to_exclude = shared_facts if not is_personal else []
        
        # Get user context
        user_context = memory_manager.get_user_context()
        
        # Check for information staleness
        stale_facts = self._identify_stale_facts(shared_facts, topic)
        
        # Build comprehensive context for analysis
        context = {
            "user_query": query,
            "topic": topic,
            "user_context": user_context,
            "conversation_history": conversation_history,
            "shared_facts": [asdict(fact) for fact in facts_to_exclude],
            "stale_facts": stale_facts,
            "last_discussion": last_discussion_time,
            "is_asking_for_updates": is_asking_for_updates,
            "user_preferences": self.user_preferences,
            "is_personal_query": is_personal
        }
        
        # Use LLM to analyze the query with context
        analysis = self._llm_analyze_query(context)
        
        # Override LLM if we detected personal query
        if is_personal:
            analysis.is_personal_query = True
            analysis.query_type = "personal_fact"
            if not is_asking_for_updates:
                analysis.requires_search = False
        
        # Add facts to exclude
        analysis.exclude_facts = [f.fact for f in facts_to_exclude]
        
        return analysis
    
    def _extract_topic(self, query: str) -> str:
        """Extract the main topic from a query."""
        # For personal queries, use specific topics
        is_personal, personal_type = self._is_personal_fact_query(query)
        if is_personal:
            return f"personal_{personal_type}"
        
        # Simple keyword extraction for common topics
        query_lower = query.lower()
        if "ceo" in query_lower and "resignation" in query_lower:
            return "CEO resignation"
        elif "weather" in query_lower:
            location = "unknown"
            # Try to extract location
            words = query_lower.split()
            if "in" in words:
                idx = words.index("in")
                if idx + 1 < len(words):
                    location = words[idx + 1]
            return f"weather_{location}"
        elif "stock" in query_lower:
            return "stock_price"
        else:
            # Use first 50 chars as topic
            return query[:50].strip()
    
    def _identify_stale_facts(self, facts: List[SharedFact], topic: str) -> List[SharedFact]:
        """Identify facts that may need updating based on topic type."""
        stale_facts = []
        now = datetime.now(timezone.utc)
        
        # Define staleness by topic type
        staleness_rules = {
            "weather": timedelta(hours=1),
            "stock": timedelta(hours=4),
            "news": timedelta(days=1),
            "personal": timedelta(days=365),  # Personal facts rarely go stale
            "general": timedelta(days=7)
        }
        
        # Determine topic type
        topic_type = "general"
        for key in ["weather", "stock", "news", "ceo", "resignation", "personal"]:
            if key in topic.lower():
                topic_type = "news" if key in ["ceo", "resignation"] else key
                break
        
        max_age = staleness_rules.get(topic_type, timedelta(days=7))
        
        for fact in facts:
            fact_age = now - datetime.fromisoformat(fact.timestamp)
            if fact_age > max_age:
                stale_facts.append(fact)
        
        return stale_facts
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _llm_analyze_query(self, context: Dict) -> QueryAnalysis:
        """Use LLM to perform deep query analysis with context. Now with retries and simpler prompt."""
        
        # Simplified, more reliable prompt
        system_prompt = """Analyze the user query and provide a JSON response.

Return EXACTLY this JSON structure:
{
    "enhanced_query": "the query enhanced with any user context",
    "query_type": "personal_fact|news|weather|stock|temporal_update|general",
    "temporal_requirement": "immediate|recent|update_since_last|none",
    "search_constraints": [],
    "information_gaps": [],
    "user_intent": "what the user wants to know",
    "requires_search": true/false,
    "prompt_instructions": "instructions for the assistant"
}

Rules:
- If query is about user's personal info (name, favorite color, etc), set query_type="personal_fact" and requires_search=false
- If query contains "new", "update", "latest", "recent", set temporal_requirement="update_since_last"
- Only set requires_search=true if web search is needed
- Keep responses simple and direct"""

        # Build simpler user prompt
        user_prompt = f"""Query: {context['user_query']}

User Info:
- Name: {context['user_context'].get('name', 'Unknown')}
- Company: {context['user_context'].get('company', 'Unknown')}

Is asking for updates: {context['is_asking_for_updates']}
Is personal query: {context.get('is_personal_query', False)}
Last discussed: {context['last_discussion'] or 'Never'}"""

        try:
            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ])
            
            # Parse JSON with better error handling
            content = response.content.strip()
            if not content:
                raise ValueError("Empty response from LLM")
            
            # Try to extract JSON even if there's extra text
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                content = json_match.group()
            
            result = json.loads(content)
            
            # Validate and set defaults
            return QueryAnalysis(
                original_query=context["user_query"],
                enhanced_query=result.get("enhanced_query", context["user_query"]),
                query_type=result.get("query_type", "general"),
                temporal_requirement=result.get("temporal_requirement", "none"),
                conversation_context=context,
                search_constraints=result.get("search_constraints", []),
                information_gaps=result.get("information_gaps", []),
                user_intent=result.get("user_intent", "General information request"),
                requires_search=result.get("requires_search", False),
                prompt_instructions=result.get("prompt_instructions", ""),
                exclude_facts=[],
                is_personal_query=context.get('is_personal_query', False)
            )
            
        except Exception as e:
            print(f"⚠️ LLM analysis error (will use fallback): {e}")
            return self._fallback_analysis(context)
    
    def _fallback_analysis(self, context: Dict) -> QueryAnalysis:
        """Enhanced fallback analysis when LLM fails."""
        query = context["user_query"]
        query_lower = query.lower()
        
        # Check if personal query
        is_personal, personal_type = self._is_personal_fact_query(query)
        
        # Default values
        enhanced_query = query
        query_type = "general"
        requires_search = True
        search_constraints = []
        prompt_instructions = ""
        
        # Personal query handling
        if is_personal:
            query_type = "personal_fact"
            requires_search = False
            prompt_instructions = f"State the user's {personal_type} if known"
        # News/updates query
        elif any(word in query_lower for word in ["ceo", "resignation", "news"]):
            query_type = "news"
            if context["user_context"].get("company"):
                enhanced_query = query.replace("our", context["user_context"]["company"])
        # Weather query
        elif "weather" in query_lower:
            query_type = "weather"
        # Stock query
        elif "stock" in query_lower:
            query_type = "stock"
        
        # Temporal handling
        temporal_requirement = "none"
        if context['is_asking_for_updates']:
            temporal_requirement = "update_since_last"
            if context["last_discussion"]:
                after_date = context["last_discussion"].split('T')[0]
                search_constraints.append(f"after:{after_date}")
                prompt_instructions = "Only provide information newer than the last discussion"
        
        return QueryAnalysis(
            original_query=query,
            enhanced_query=enhanced_query,
            query_type=query_type,
            temporal_requirement=temporal_requirement,
            conversation_context=context,
            search_constraints=search_constraints,
            information_gaps=["Unable to determine specific gaps"],
            user_intent=f"User wants to know about {query_type}",
            requires_search=requires_search and not is_personal,
            prompt_instructions=prompt_instructions,
            exclude_facts=[f['fact'] for f in context.get("shared_facts", [])],
            is_personal_query=is_personal
        )
    
    def generate_dynamic_prompt(self, 
                              query_analysis: QueryAnalysis,
                              retrieved_memories: List[Dict],
                              web_results: Optional[List] = None) -> str:
        """
        Generate a dynamic prompt based on conversation context.
        Fixed: Better handling of personal queries and clearer instructions.
        """
        # For personal queries, generate simple direct prompt
        if query_analysis.is_personal_query and not web_results:
            base_facts = memory_manager.format_memories_for_prompt(retrieved_memories)
            return f"""{base_facts}

**Instructions:** 
- This is a personal fact query. Simply state the requested information if available.
- Do not mention updates or new information.
- If the information is not available, say you don't have that information."""
        
        # For other queries, use normal prompt generation
        base_facts = memory_manager.format_memories_for_prompt(retrieved_memories)
        
        # Build conversation-aware instructions
        instructions = []
        
        # Add exclusion instructions only for update queries
        if query_analysis.exclude_facts and query_analysis.temporal_requirement == "update_since_last":
            instructions.append("\n**CRITICAL - DO NOT REPEAT ANY OF THESE FACTS:**")
            for fact in query_analysis.exclude_facts:
                instructions.append(f"❌ {fact}")
            instructions.append("\nIf asked for updates and you only have the above information, clearly state that there are no new updates.")
        
        # Add temporal context
        if query_analysis.temporal_requirement == "update_since_last":
            last_time = query_analysis.conversation_context.get("last_discussion")
            if last_time:
                date_str = datetime.fromisoformat(last_time).strftime("%B %d, %Y")
                instructions.append(f"\n**The user is asking for updates AFTER {date_str}. Only provide information newer than this date.**")
        
        # Add query-specific instructions
        if query_analysis.prompt_instructions:
            instructions.append(f"\n{query_analysis.prompt_instructions}")
        
        # Add user intent clarification
        if query_analysis.user_intent:
            instructions.append(f"\n**User Intent:** {query_analysis.user_intent}")
        
        # Handle no new information scenario
        if query_analysis.temporal_requirement == "update_since_last" and not web_results:
            instructions.append("\n**If no new information is available, clearly state: 'I don't have any new updates on [topic] since our last discussion.'**")
        
        # Combine everything
        full_prompt = f"""{base_facts}

{''.join(instructions)}"""
        
        return full_prompt
    
    def track_response(self, query: str, response: str, sources: List[str] = None):
        """
        Track what information was shared in the response.
        Enhanced with better fact extraction.
        """
        topic = self._extract_topic(query)
        
        # Don't track facts for certain responses
        no_track_phrases = [
            "I don't have any new updates",
            "There are no new updates",
            "No new information",
            "I don't have that information"
        ]
        
        should_track = not any(phrase in response for phrase in no_track_phrases)
        
        fact_ids = []
        if should_track:
            # Extract facts from response
            facts = self._extract_facts_from_response(response, topic)
            
            # Store each fact
            for fact in facts:
                fact_id = self.tracker.add_shared_fact(
                    topic=topic,
                    fact=fact["fact"],
                    source=fact.get("source", "conversation"),
                    confidence=fact.get("confidence", 0.8)
                )
                if fact_id:
                    fact_ids.append(fact_id)
                    self._current_session_facts.append(fact["fact"])
        
        # Always store conversation turn
        self.tracker.add_conversation_turn(
            topic=topic,
            query=query,
            response=response,
            sources=sources or [],
            fact_ids=fact_ids
        )
        
        # Update user preferences based on interaction
        self._update_user_preferences(query, response)
    
    def _extract_facts_from_response(self, response: str, topic: str) -> List[Dict]:
        """Extract individual facts from a response - simplified version."""
        facts = []
        
        # Don't extract from negative responses
        if any(phrase in response.lower() for phrase in ["don't have", "no new", "not available"]):
            return facts
        
        # Simple extraction for personal facts
        if "personal_" in topic:
            # Extract statements about user
            if "name is" in response.lower():
                import re
                match = re.search(r"name is (\w+)", response, re.IGNORECASE)
                if match:
                    facts.append({
                        "fact": f"Name: {match.group(1)}",
                        "confidence": 0.9,
                        "source": "user"
                    })
            if "favorite color" in response.lower() and "is" in response.lower():
                match = re.search(r"favorite color is (\w+)", response, re.IGNORECASE)
                if match:
                    facts.append({
                        "fact": f"Favorite color: {match.group(1)}",
                        "confidence": 0.9,
                        "source": "user"
                    })
        else:
            # For other topics, extract key sentences
            sentences = response.split('.')
            for sentence in sentences:
                sentence = sentence.strip()
                # Look for factual statements
                if len(sentence) > 20 and any(indicator in sentence.lower() for indicator in 
                                             ['is', 'are', 'was', 'were', 'will', 'has', 'have']):
                    # Skip meta-statements
                    if not any(skip in sentence.lower() for skip in 
                             ["i don't", "there are no", "i can", "if you"]):
                        facts.append({
                            "fact": sentence + ".",
                            "confidence": 0.7,
                            "source": "conversation"
                        })
        
        return facts[:5]  # Limit to 5 facts per response
    
    def _update_user_preferences(self, query: str, response: str):
        """Learn from user interactions to improve future responses."""
        # Track query patterns
        self.tracker.update_preference("query_patterns", {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "query_type": self._extract_topic(query),
            "query_length": len(query),
            "response_length": len(response)
        })
        
        # Detect preferences from query
        if "brief" in query.lower() or "summary" in query.lower():
            self.tracker.update_preference("response_style", "concise")
        elif "detail" in query.lower() or "explain" in query.lower():
            self.tracker.update_preference("response_style", "detailed")
        
        # Track interaction frequency
        self.tracker.increment_interaction_count()
    
    def get_conversation_summary(self, topic: Optional[str] = None) -> str:
        """Get a summary of conversations on a topic."""
        if topic:
            facts_summary = self.tracker.get_facts_summary(topic)
            
            summary = f"**Conversation Summary - {topic}:**\n"
            summary += f"- Facts shared: {facts_summary['fact_count']}\n"
            
            if facts_summary['last_shared']:
                summary += f"- Last discussed: {facts_summary['last_shared']}\n"
            
            if facts_summary['facts']:
                summary += "\nKey facts shared:\n"
                for fact_info in facts_summary['facts'][-5:]:  # Last 5 facts
                    summary += f"- {fact_info['fact']}\n"
            
            return summary
        else:
            # Overall summary
            all_topics = self.tracker.get_all_topics()
            return f"**Overall Conversation Summary:**\n- Topics discussed: {len(all_topics)}\n- Total interactions: {self.tracker.get_interaction_count()}"
    
    def should_proactively_update(self, topic: str) -> Tuple[bool, str]:
        """Determine if we should proactively offer updates on a topic."""
        last_discussion = self.tracker.get_last_discussion_time(topic)
        if not last_discussion:
            return False, ""
        
        # Check time since last discussion
        time_since = datetime.now(timezone.utc) - datetime.fromisoformat(last_discussion)
        
        # Rules for proactive updates
        if "stock" in topic.lower() and time_since > timedelta(hours=4):
            return True, f"It's been {time_since.total_seconds() // 3600} hours since we discussed {topic}. Would you like an update?"
        elif ("news" in topic.lower() or "ceo" in topic.lower()) and time_since > timedelta(days=1):
            return True, f"There may be new developments on {topic} since we last talked."
        
        return False, ""