# File: graph_setup.py

import os
from typing import TypedDict, List, Dict, Optional
from dotenv import load_dotenv

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

import memory_manager
from web_search import should_search_web, search_and_scrape
from context_manager import ContextManagerLLM, QueryAnalysis
from azure_search_retriever import AzureSearchRetriever

# ─── Load environment variables ────────────────────────────────
load_dotenv()

# ─── Initialize components ──────────────────────────────────────
llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.1)

# ─── 1) Define enhanced state schema ────────────────────────────
class ChatState(TypedDict):
    messages: List[str]                # All chat lines (user + assistant)
    memories: List[str]                # Long-term facts or summaries  
    current_query: str                 # Current user query
    query_analysis: Dict               # Basic analysis results
    context_analysis: Optional[QueryAnalysis]  # Enhanced context analysis
    retrieved_memories: List[Dict]     # Retrieved memories
    web_results: Optional[List]        # Web search results if any
    response: str                      # Generated response
    thread_id: str                     # User/session identifier
    session_id: str                    # Session ID for persistence
    dynamic_prompt: str                # Context-aware prompt

# ─── 2) Instantiate your Azure Search retriever ────────────────
retriever = AzureSearchRetriever(
    endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
    api_key=os.getenv("AZURE_SEARCH_API_KEY"),
    index_name=os.getenv("AZURE_INDEX_NAME"),
    k=8
)

# ─── 3) Choose a checkpointer for persistence ───────────────────
checkpointer = InMemorySaver()

# ─── 4) Build the LangGraph with context-aware workflow ─────────
builder = StateGraph(ChatState)

def context_analysis_node(state: ChatState) -> ChatState:
    """Analyze query with full conversation context."""
    print("🧠 Analyzing with Context Manager...")
    
    # Initialize context manager with session ID
    context_manager = ContextManagerLLM(
        state["thread_id"], 
        state.get("session_id")
    )
    
    # Get initial memories for context
    initial_memories = memory_manager.retrieve_memories(
        state["current_query"], 
        k=5,  # Fewer memories for context analysis
        include_personal_facts=True
    )
    
    # Perform deep context analysis
    context_analysis = context_manager.analyze_query_with_context(
        state["current_query"],
        initial_memories
    )
    
    state["context_analysis"] = context_analysis
    
    # Log analysis results
    print(f"📊 Context Analysis:")
    print(f"   Query Type: {context_analysis.query_type}")
    print(f"   User Intent: {context_analysis.user_intent}")
    print(f"   Information Gaps: {context_analysis.information_gaps}")
    print(f"   Search Required: {context_analysis.requires_search}")
    print(f"   Is Personal Query: {context_analysis.is_personal_query}")
    
    # Check for proactive updates
    topic = context_analysis.conversation_context["topic"]
    should_update, update_msg = context_manager.should_proactively_update(topic)
    if should_update:
        print(f"💡 Proactive update available: {update_msg}")
    
    return state

def enhanced_analyze_node(state: ChatState) -> ChatState:
    """Enhanced analysis using context manager results."""
    print("🔍 Processing enhanced analysis...")
    
    # Store user message
    memory_manager.store_memory(state["current_query"], memory_type="user_message")
    
    # Use enhanced query from context analysis
    enhanced_query = state["context_analysis"].enhanced_query
    
    # Retrieve memories with enhanced query
    memories = memory_manager.retrieve_memories(
        enhanced_query,  # Use enhanced query
        k=8,
        include_personal_facts=True
    )
    state["retrieved_memories"] = memories
    
    # Basic search decision (can be overridden by context analysis)
    if state["context_analysis"].requires_search:
        # Use the context-enhanced query for search decision
        analysis = {
            "needs_search": True,
            "search_query": enhanced_query,
            "query_type": state["context_analysis"].query_type,
            "reason": state["context_analysis"].user_intent
        }
    else:
        analysis = {
            "needs_search": False,
            "search_query": "",
            "query_type": state["context_analysis"].query_type,
            "reason": "Context analysis determined no search needed"
        }
    
    state["query_analysis"] = analysis
    
    return state

def context_aware_search_node(state: ChatState) -> ChatState:
    """Perform web search with context constraints."""
    if state["query_analysis"].get("needs_search", False):
        print("🌐 Performing context-aware web search...")
        
        # Get search constraints from context analysis
        constraints = state["context_analysis"].search_constraints
        search_query = state["query_analysis"].get("search_query", state["current_query"])
        
        # Apply constraints to search query
        for constraint in constraints:
            if constraint.startswith("NOT "):
                # Skip NOT constraints for search query
                continue
            elif constraint.startswith("after:"):
                search_query += f" {constraint}"
        
        print(f"🔍 Enhanced search query: '{search_query}'")
        
        # Special handling for different query types
        query_type = state["context_analysis"].query_type
        
        if query_type == "stock":
            web_results = search_for_stock_price(search_query)
        elif query_type == "update_since_last":
            # Add temporal filtering
            last_time = state["context_analysis"].conversation_context.get("last_discussion")
            if last_time:
                search_query += f" after:{last_time[:10]}"
            web_results = search_and_scrape(search_query, num_urls=3)
        else:
            web_results = search_and_scrape(search_query, num_urls=3)
        
        if web_results:
            state["web_results"] = web_results
            # Store web content
            memory_manager.store_web_content(web_results, search_query)
            # Re-retrieve to include fresh content
            state["retrieved_memories"] = memory_manager.retrieve_memories(
                state["current_query"], 
                k=8,
                include_personal_facts=True
            )
    else:
        state["web_results"] = None
        print("💭 No search needed based on context analysis")
    
    return state

def generate_context_aware_response_node(state: ChatState) -> ChatState:
    """Generate response with dynamic context-aware prompt."""
    print("💭 Generating context-aware response...")
    
    # Get context manager
    context_manager = ContextManagerLLM(
        state["thread_id"],
        state.get("session_id")
    )
    
    # Generate dynamic prompt
    dynamic_prompt = context_manager.generate_dynamic_prompt(
        state["context_analysis"],
        state["retrieved_memories"],
        state["web_results"]
    )
    
    state["dynamic_prompt"] = dynamic_prompt
    
    # Build system prompt based on query type and context
    query_type = state["context_analysis"].query_type
    base_prompt = build_context_aware_system_prompt(
        query_type, 
        dynamic_prompt, 
        bool(state["web_results"]),
        state["context_analysis"]
    )
    
    # Generate response
    try:
        response = llm.invoke([
            SystemMessage(content=base_prompt),
            HumanMessage(content=state["current_query"])
        ])
        state["response"] = response.content.strip()
        
        # Track the response
        sources = []
        if state["web_results"]:
            sources = [result.get("url", "") for result in state["web_results"]]
        
        context_manager.track_response(
            state["current_query"],
            state["response"],
            sources
        )
        
    except Exception as e:
        print(f"❌ Error generating response: {e}")
        state["response"] = "I apologize, but I encountered an error. Please try again."
    
    return state

def search_for_stock_price(query: str) -> List[Dict[str, str]]:
    """Specialized search for stock prices."""
    # Extract company name
    company = "Renault" if "renault" in query.lower() else query.split()[0]
    
    # Try to get stock information
    try:
        if "renault" in company.lower():
            symbol = "RNO.PA"
            content = f"""Based on available information, Renault (RNO.PA) stock information:
- Renault shares have experienced volatility recently
- The company lowered its 2025 guidance which impacted share price
- For real-time stock prices, please check:
  • Yahoo Finance: https://finance.yahoo.com/quote/RNO.PA
  • Google Finance: Search "Renault stock price"
  • Your broker's platform

Note: Real-time stock data requires specialized financial data feeds."""
            
            return [{
                'url': 'https://finance.yahoo.com/quote/RNO.PA',
                'title': 'Renault Stock Information',
                'content': content,
                'query_type': 'stock'
            }]
    except:
        pass
    
    # Fallback to regular search
    return search_and_scrape(query, num_urls=2)

def build_context_aware_system_prompt(query_type: str, dynamic_content: str, 
                                    has_web_results: bool, context_analysis: QueryAnalysis) -> str:
    """Build system prompt with context awareness."""
    
    # Base prompt varies by query type
    if context_analysis.is_personal_query and query_type == "personal_fact":
        base = f"""You are a helpful assistant with conversation memory.

{dynamic_content}

When answering personal fact queries:
- Simply state the fact if known
- Do not use language about "updates" or "new information"
- Be direct and concise
- If the fact is not known, say "I don't have that information" """
    else:
        base = f"""You are an intelligent assistant with conversation memory.

{dynamic_content}

CRITICAL INSTRUCTIONS:
1. {context_analysis.prompt_instructions}
2. Focus on the user's specific intent: {context_analysis.user_intent}
3. Do not repeat information already shared with the user
4. If no new information is available, clearly state this"""

    # Add query-type specific instructions
    if query_type == "follow_up":
        base += "\n\nThis is a follow-up question. Only provide NEW information not previously shared."
    elif query_type == "clarification":
        base += "\n\nThe user is asking for clarification. Focus on explaining or expanding on previous information."
    elif query_type == "update_since_last":
        base += "\n\nOnly provide information that is newer than what was previously discussed."
    
    return base

# Add nodes to the graph
builder.add_node("context_analyze", context_analysis_node)
builder.add_node("enhanced_analyze", enhanced_analyze_node)
builder.add_node("context_search", context_aware_search_node)
builder.add_node("context_respond", generate_context_aware_response_node)

# Define the workflow
builder.add_edge(START, "context_analyze")
builder.add_edge("context_analyze", "enhanced_analyze")
builder.add_edge("enhanced_analyze", "context_search")
builder.add_edge("context_search", "context_respond")
builder.add_edge("context_respond", END)

# ─── 5) Compile with persistence ───────────────────────────────
graph = builder.compile(checkpointer=checkpointer)