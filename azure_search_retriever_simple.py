# azure_search_retriever_simple.py
"""
Simple Azure Search retriever without Pydantic complications.
"""

import os
from typing import List
from dotenv import load_dotenv

from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.models import VectorizedQuery

from openai import OpenAI
from langchain.schema import Document

# Load environment variables
load_dotenv()

class SimpleAzureSearchRetriever:
    """
    Simple retriever that uses Azure Cognitive Search vector search.
    No Pydantic, just plain Python class.
    """
    
    def __init__(
        self,
        endpoint: str,
        api_key: str,
        index_name: str,
        k: int = 3
    ):
        """
        Initialize the Azure Search client and the OpenAI client.

        Args:
            endpoint: URL of the Azure Cognitive Search service
            api_key: Admin or query key for Azure Search
            index_name: Name of the index to search against
            k: Number of top results to return
        """
        self.endpoint = endpoint
        self.api_key = api_key
        self.index_name = index_name
        self.k = k
        
        # Initialize clients
        self.client = SearchClient(
            endpoint=endpoint,
            index_name=index_name,
            credential=AzureKeyCredential(api_key)
        )
        self.openai = OpenAI()  # uses OPENAI_API_KEY from env

    def get_relevant_documents(self, query: str) -> List[Document]:
        """
        Retrieve semantically relevant documents from Azure Search.

        Args:
            query: The input query string.

        Returns:
            A list of LangChain Document instances.
        """
        try:
            # 1) Create embedding
            resp = self.openai.embeddings.create(
                model="text-embedding-ada-002",
                input=query
            )
            q_vec = resp.data[0].embedding

            # 2) Build VectorizedQuery with the correct field
            vq = VectorizedQuery(
                vector=q_vec,
                k_nearest_neighbors=self.k,
                fields="contentVector"
            )

            # 3) Execute vector search
            results = self.client.search(
                search_text="*",
                vector_queries=[vq]
            )

            # 4) Wrap hits in Documents
            docs: List[Document] = []
            for r in results:
                docs.append(
                    Document(
                        page_content=r.get("content", ""),
                        metadata={"id": r.get("id", "")}
                    )
                )
            return docs
            
        except Exception as e:
            print(f"❌ Error in Azure Search retriever: {e}")
            return []
    
    # Methods for LangChain compatibility
    def invoke(self, query: str) -> List[Document]:
        """LangChain compatible invoke method."""
        return self.get_relevant_documents(query)
    
    def _get_relevant_documents(self, query: str) -> List[Document]:
        """LangChain compatible method."""
        return self.get_relevant_documents(query)
    
    async def _aget_relevant_documents(self, query: str) -> List[Document]:
        """Async version for compatibility."""
        return self.get_relevant_documents(query)
