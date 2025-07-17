# File: app.py

import os
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

from graph_setup import graph, retriever  # checkpointer is inside graph
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage, AIMessage

import memory_manager

# ─── Load environment variables ────────────────────────────────
load_dotenv()

app = Flask(__name__)

# ─── Initialize the chat‑completion model ───────────────────────
llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_msg = request.json.get("message", "").strip()
    if not user_msg:
        return jsonify({"error": "no message"}), 400

    # ─── 1) Identify the conversation thread ──────────────────────
    thread_id = request.remote_addr  # swap for real user IDs in prod

    # ─── 2) Restore previous state via LangGraph ──────────────────
    config = {"configurable": {"thread_id": thread_id}}
    snapshot = graph.get_state(config)
    if (
        not snapshot
        or not isinstance(snapshot.values, dict)
        or "messages" not in snapshot.values
        or "memories" not in snapshot.values
    ):
        state = {"messages": [], "memories": []}
    else:
        state = snapshot.values

    # ─── 3) Append the new user message ──────────────────────────
    state["messages"].append(f"User: {user_msg}")

    # ─── 4) Semantic recall from Azure Search ────────────────────
    docs = retriever.get_relevant_documents(user_msg)  # deprecated warning OK for now
    for d in docs:
        fact = d.page_content
        if fact not in state["memories"]:
            state["memories"].append(fact)

    # ─── 5) Build System & Human messages for the chat model ─────
    system_prompt = (
        "You are a helpful assistant. Use only the following facts:\n"
        + "\n".join(f"- {m}" for m in state["memories"])
    )
    history = "\n".join(state["messages"])
    human_prompt = f"Conversation so far:\n{history}\n\nUser: {user_msg}"

    # ─── 6) Invoke the chat model correctly via v1/chat/completions ─
    ai_message: AIMessage = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_prompt)
    ])
    answer = ai_message.content.strip()

    # ─── 7) Append assistant’s reply ─────────────────────────────
    state["messages"].append(f"Assistant: {answer}")

    # ─── 8) Persist updated state via the graph (auto‑saves) ─────
    # Provide the entire updated state as the “inputs” map so LangGraph overwrites and checkpoints it :contentReference[oaicite:3]{index=3}
    graph.invoke(state, config)

    # ─── 9) Also store the raw user turn as a new vector memory ───
    memory_manager.store_memory(user_msg)

    return jsonify({"reply": answer})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
