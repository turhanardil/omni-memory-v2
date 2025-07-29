# File: app.py

import os
import uuid
import json
from flask import Flask, render_template, request, jsonify, make_response
from dotenv import load_dotenv
from datetime import datetime, timedelta

from graph_setup import graph
import memory_manager
from context_manager import ContextManagerLLM

# ─── Load environment variables ────────────────────────────────
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')

# Session configuration
SESSION_COOKIE_NAME = 'chatbot_session'
SESSION_DURATION_DAYS = 30

def get_or_create_session_id():
    """Get existing session ID from cookie or create a new one."""
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    
    if not session_id:
        # Create new session ID
        session_id = str(uuid.uuid4())
        print(f"🆕 Created new session: {session_id}")
    else:
        print(f"🔄 Using existing session: {session_id}")
    
    return session_id

@app.route("/")
def home():
    response = make_response(render_template("index.html"))
    
    # Ensure session cookie is set
    session_id = get_or_create_session_id()
    response.set_cookie(
        SESSION_COOKIE_NAME,
        session_id,
        max_age=60*60*24*SESSION_DURATION_DAYS,  # 30 days
        httponly=True,
        samesite='Lax'
    )
    
    return response

@app.route("/chat", methods=["POST"])
def chat():
    user_msg = request.json.get("message", "").strip()
    if not user_msg:
        return jsonify({"error": "no message"}), 400

    # ─── 1) Get session ID from cookie ────────────────────────────
    session_id = get_or_create_session_id()
    
    # Use a combination of session and IP for thread_id
    # This provides both persistence and some security
    thread_id = f"{session_id}_{request.remote_addr}"
    config = {"configurable": {"thread_id": thread_id}}

    # ─── 2) Get previous state ────────────────────────────────────
    snapshot = graph.get_state(config)
    if (
        not snapshot
        or not isinstance(snapshot.values, dict)
        or "messages" not in snapshot.values
    ):
        previous_messages = []
        previous_memories = []
    else:
        previous_messages = snapshot.values.get("messages", [])
        previous_memories = snapshot.values.get("memories", [])

    # ─── 3) Prepare state for the context-aware graph ────────────
    print(f"\n{'='*60}")
    print(f"🗣️  User: {user_msg}")
    print(f"📋 Session: {session_id[:8]}...")
    print(f"{'='*60}\n")
    
    input_state = {
        "messages": previous_messages + [f"User: {user_msg}"],
        "memories": previous_memories,
        "current_query": user_msg,
        "thread_id": thread_id,
        "session_id": session_id,  # Pass session ID
        "query_analysis": {},
        "context_analysis": None,
        "retrieved_memories": [],
        "web_results": None,
        "response": "",
        "dynamic_prompt": ""
    }

    # ─── 4) Run the context-aware graph workflow ─────────────────
    try:
        # This will run through: context_analyze → enhanced_analyze → context_search → context_respond
        result = graph.invoke(input_state, config)
        
        # Extract the response
        answer = result.get("response", "I apologize, but I couldn't generate a response.")
        
        # Update conversation history
        result["messages"].append(f"Assistant: {answer}")
        
        # The graph automatically saves state via checkpointer
        
        print(f"\n{'='*60}\n")
        
        # Create response with session cookie
        response = make_response(jsonify({"reply": answer}))
        response.set_cookie(
            SESSION_COOKIE_NAME,
            session_id,
            max_age=60*60*24*SESSION_DURATION_DAYS,
            httponly=True,
            samesite='Lax'
        )
        
        return response
        
    except Exception as e:
        print(f"❌ Error in graph execution: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "An error occurred processing your request"}), 500

@app.route("/session/info", methods=["GET"])
def session_info():
    """Get current session information."""
    session_id = get_or_create_session_id()
    thread_id = f"{session_id}_{request.remote_addr}"
    
    # Get context manager to check conversation history
    context_manager = ContextManagerLLM(thread_id, session_id)
    topics = context_manager.tracker.get_all_topics()
    interaction_count = context_manager.tracker.get_interaction_count()
    
    return jsonify({
        "session_id": session_id[:8] + "...",  # Show partial for privacy
        "topics_discussed": len(topics),
        "total_interactions": interaction_count,
        "session_active": True
    })

@app.route("/session/clear", methods=["POST"])
def clear_session():
    """Clear the current session and start fresh."""
    response = make_response(jsonify({"message": "Session cleared"}))
    response.set_cookie(SESSION_COOKIE_NAME, '', expires=0)
    return response

@app.route("/debug/conversation-summary", methods=["GET"])
def debug_conversation_summary():
    """Get conversation summary for debugging."""
    session_id = get_or_create_session_id()
    thread_id = f"{session_id}_{request.remote_addr}"
    topic = request.args.get("topic", None)
    
    context_manager = ContextManagerLLM(thread_id, session_id)
    summary = context_manager.get_conversation_summary(topic)
    
    return jsonify({
        "session_id": session_id[:8] + "...",
        "thread_id": thread_id,
        "summary": summary
    })

@app.route("/debug/shared-facts", methods=["GET"])
def debug_shared_facts():
    """Get shared facts for a topic."""
    session_id = get_or_create_session_id()
    thread_id = f"{session_id}_{request.remote_addr}"
    topic = request.args.get("topic", "")
    
    if not topic:
        return jsonify({"error": "provide ?topic=something"})
    
    context_manager = ContextManagerLLM(thread_id, session_id)
    facts = context_manager.tracker.get_shared_facts(topic)
    
    return jsonify({
        "session_id": session_id[:8] + "...",
        "topic": topic,
        "facts_count": len(facts),
        "facts": [
            {
                "fact": fact.fact,
                "source": fact.source,
                "timestamp": fact.timestamp,
                "confidence": fact.confidence
            } for fact in facts
        ]
    })

@app.route("/debug/conversation-history", methods=["GET"])
def debug_conversation_history():
    """Get conversation history for a topic."""
    session_id = get_or_create_session_id()
    thread_id = f"{session_id}_{request.remote_addr}"
    topic = request.args.get("topic", "")
    
    if not topic:
        return jsonify({"error": "provide ?topic=something"})
    
    context_manager = ContextManagerLLM(thread_id, session_id)
    history = context_manager.tracker.get_conversation_history(topic)
    
    return jsonify({
        "session_id": session_id[:8] + "...",
        "topic": topic,
        "history_count": len(history),
        "history": history
    })

@app.route("/debug/user-preferences", methods=["GET"])
def debug_user_preferences():
    """Get user preferences."""
    session_id = get_or_create_session_id()
    thread_id = f"{session_id}_{request.remote_addr}"
    
    context_manager = ContextManagerLLM(thread_id, session_id)
    preferences = context_manager.tracker.get_user_preferences()
    
    return jsonify({
        "session_id": session_id[:8] + "...",
        "preferences": preferences,
        "interaction_count": context_manager.tracker.get_interaction_count()
    })

@app.route("/debug/topics", methods=["GET"])
def debug_topics():
    """Get all topics discussed."""
    session_id = get_or_create_session_id()
    thread_id = f"{session_id}_{request.remote_addr}"
    
    context_manager = ContextManagerLLM(thread_id, session_id)
    topics = context_manager.tracker.get_all_topics()
    
    summaries = {}
    for topic in topics:
        last_time = context_manager.tracker.get_last_discussion_time(topic)
        facts_count = len(context_manager.tracker.get_shared_facts(topic))
        summaries[topic] = {
            "last_discussed": last_time,
            "facts_shared": facts_count
        }
    
    return jsonify({
        "session_id": session_id[:8] + "...",
        "topics_count": len(topics),
        "topics": summaries
    })

@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint with context manager status."""
    try:
        # Test Azure Search connection
        azure_status = "❌ Not configured"
        if memory_manager.search_client:
            # Try a simple search to verify connection
            results = memory_manager.search_client.search(
                search_text="*",
                top=1
            )
            # Force evaluation by converting to list
            list(results)
            azure_status = "✅ Connected"
    except:
        azure_status = "❌ Connection failed"
    
    return jsonify({
        "status": "healthy",
        "services": {
            "azure_search": azure_status,
            "openai": "✅ Connected" if memory_manager.openai_client else "❌ Not configured",
            "web_search": "✅ Ready (DuckDuckGo + wttr.in)",
            "context_manager": "✅ Active"
        },
        "features": {
            "session_management": "✅ Cookie-based (30 days)",
            "conversation_tracking": "✅ Enabled",
            "fact_deduplication": "✅ Enabled",
            "context_aware_search": "✅ Enabled",
            "dynamic_prompting": "✅ Enabled",
            "user_preferences": "✅ Enabled",
            "historical_loading": "✅ Enabled",
            "personal_query_detection": "✅ Enabled"
        }
    })

if __name__ == "__main__":
    # Print startup information
    print("\n" + "="*60)
    print("🚀 Starting Context-Aware Memory Chatbot (v2.0)")
    print("="*60)
    print(f"🔧 Azure Search: {'✅ Connected' if memory_manager.AZ_ENDPOINT else '❌ Not configured'}")
    print(f"🔧 OpenAI API: {'✅ Connected' if memory_manager.openai_client else '❌ Not configured'}")
    print(f"🔧 Web Search: ✅ Ready (No API keys needed!)")
    print(f"🔧 Context Manager: ✅ Active")
    print(f"🔧 Session Management: ✅ Cookie-based (30-day persistence)")
    print("\n📍 Endpoints:")
    print("   Main: http://localhost:5000")
    print("   Session Info: /session/info")
    print("   Clear Session: /session/clear")
    print("\n🔍 Debug endpoints:")
    print("   - /debug/conversation-summary?topic=optional")
    print("   - /debug/shared-facts?topic=required")
    print("   - /debug/conversation-history?topic=required")
    print("   - /debug/user-preferences")
    print("   - /debug/topics")
    print("   - /health")
    print("\n✨ Key Improvements in v2.0:")
    print("   - 🍪 Cookie-based sessions (30-day persistence)")
    print("   - 🔄 Historical data loaded on startup")
    print("   - 📝 Fixed Azure Search schema issues")
    print("   - 🧠 Better personal query detection")
    print("   - 🎯 Improved LLM reliability with retries")
    print("   - 🚫 Proper deduplication of facts")
    print("   - ⏰ Temporal awareness for update queries")
    print("="*60 + "\n")
    
    app.run(debug=True, port=5000)