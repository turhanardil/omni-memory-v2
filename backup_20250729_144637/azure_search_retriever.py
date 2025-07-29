import os
from typing import List
from dotenv import load_dotenv

from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.models import VectorizedQuery

from openai import OpenAI
from langchain.schema import BaseRetriever, Document
from pydantic import PrivateAttr

# Load environment variables
load_dotenv()

class AzureSearchRetriever(BaseRetriever):
    """
    Custom retriever that uses Azure Cognitive Search vector search
    to fetch semantically relevant documents.
    """
    # Private attributes (excluded from Pydantic model validation)
    _client: SearchClient = PrivateAttr()
    _openai: OpenAI = PrivateAttr()
    _k: int = PrivateAttr()

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
        super().__init__()  # initialize BaseRetriever
        # Assign private attributes
        self._client = SearchClient(
            endpoint=endpoint,
            index_name=index_name,
            credential=AzureKeyCredential(api_key)
        )
        self._k = k
        self._openai = OpenAI()  # uses OPENAI_API_KEY from env

    def get_relevant_documents(self, query: str) -> List[Document]:
        """
        Retrieve semantically relevant documents from Azure Search.

        Args:
            query: The input query string.

        Returns:
            A list of LangChain Document instances.
        """
        # 1) Create embedding
        resp = self._openai.embeddings.create(
            model="text-embedding-ada-002",
            input=query
        )
        q_vec = resp.data[0].embedding

        # 2) Build VectorizedQuery with the correct field
        vq = VectorizedQuery(
            vector=q_vec,
            k_nearest_neighbors=self._k,
            fields="contentVector"
        )

        # 3) Execute vector search
        results = self._client.search(
            search_text="*",
            vector_queries=[vq]
        )

        # 4) Wrap hits in Documents
        docs: List[Document] = []
        for r in results:
            docs.append(
                Document(
                    page_content=r["content"],
                    metadata={"id": r["id"]}
                )
            )
        return docs