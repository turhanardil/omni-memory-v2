# File: memory_setup.py

import os
from dotenv import load_dotenv
from langchain.memory import ConversationBufferMemory
from azure_search_retriever import AzureSearchRetriever

# Load environment variables from .env
load_dotenv()

# 1) Short‑term buffer: keep only the last 5 messages
buffer_memory = ConversationBufferMemory(
    memory_key="chat_history",
    k=5,
    return_messages=True
)

# 2) Long‑term semantic retriever via Azure Search
retriever = AzureSearchRetriever(
    endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
    api_key=os.getenv("AZURE_SEARCH_API_KEY"),
    index_name=os.getenv("AZURE_INDEX_NAME"),
    k=3
)
