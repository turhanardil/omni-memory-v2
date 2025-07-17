# File: graph_setup.py

import os
from typing_extensions import TypedDict
from dotenv import load_dotenv

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

from azure_search_retriever import AzureSearchRetriever

# ─── Load environment variables ────────────────────────────────
load_dotenv()

# ─── 1) Define your chatbot’s persistent state schema ───────────
class ChatState(TypedDict):
    messages: list[str]   # All chat lines (user + assistant)
    memories: list[str]   # Long‑term facts or summaries

# ─── 2) Instantiate your Azure Search retriever ────────────────
retriever = AzureSearchRetriever(
    endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
    api_key=os.getenv("AZURE_SEARCH_API_KEY"),
    index_name=os.getenv("AZURE_INDEX_NAME"),
    k=3
)

# ─── 3) Choose a checkpointer for persistence ───────────────────
checkpointer = InMemorySaver()

# ─── 4) Build the LangGraph and add an entrypoint ───────────────
builder = StateGraph(ChatState)

# 4a) Define a pass‑through node that only takes `state` (no separate inputs) :contentReference[oaicite:0]{index=0}
def noop_node(state: ChatState) -> ChatState:
    # Just return the state unchanged
    return state

builder.add_node("noop", noop_node)

# 4b) Wire START → noop → END so the graph has a valid entrypoint :contentReference[oaicite:1]{index=1}
builder.add_edge(START, "noop")
builder.add_edge("noop", END)

# ─── 5) Compile with persistence ───────────────────────────────
graph = builder.compile(checkpointer=checkpointer)
