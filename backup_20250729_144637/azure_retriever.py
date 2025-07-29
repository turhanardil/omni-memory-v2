# azure_retriever.py
import os
from langchain_community.retrievers import AzureAISearchRetriever
from dotenv import load_dotenv

load_dotenv()

retriever = AzureAISearchRetriever(
    service_name=os.getenv("AZURE_AI_SEARCH_SERVICE_NAME"),
    index_name=os.getenv("AZURE_INDEX_NAME"),
    api_key=os.getenv("AZURE_AI_SEARCH_API_KEY"),
    content_key="content",                     # defaults to "content"
    top_k=3,                                    # how many long‑term memories to pull
    vector_search_configuration="hnsw-config",  # matches your index
    semantic_search=False
)
