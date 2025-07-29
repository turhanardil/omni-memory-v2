# fix_pydantic_issue.py
"""
Fix the Pydantic BaseRetriever issue in AzureSearchRetriever.
"""

import os
import shutil

def create_simple_retriever():
    """Create the simple retriever file."""
    print("📝 Creating simple Azure Search retriever...")
    
    simple_retriever_code = '''# azure_search_retriever_simple.py
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
'''
    
    with open("azure_search_retriever_simple.py", "w") as f:
        f.write(simple_retriever_code)
    
    print("   ✅ Created azure_search_retriever_simple.py")

def update_graph_setup():
    """Update graph_setup.py to use the simple retriever."""
    print("\n🔧 Updating graph_setup.py...")
    
    if not os.path.exists("graph_setup.py"):
        print("   ❌ graph_setup.py not found!")
        return False
    
    try:
        with open("graph_setup.py", "r") as f:
            content = f.read()
        
        # Replace the import
        content = content.replace(
            "from azure_search_retriever import AzureSearchRetriever",
            "from azure_search_retriever_simple import SimpleAzureSearchRetriever"
        )
        
        # Replace the instantiation
        content = content.replace(
            "retriever = AzureSearchRetriever(",
            "retriever = SimpleAzureSearchRetriever("
        )
        
        # Write back
        with open("graph_setup.py", "w") as f:
            f.write(content)
        
        print("   ✅ Updated graph_setup.py")
        return True
        
    except Exception as e:
        print(f"   ❌ Error updating graph_setup.py: {e}")
        return False

def backup_original():
    """Backup the original azure_search_retriever.py."""
    print("\n📦 Backing up original files...")
    
    if os.path.exists("azure_search_retriever.py"):
        shutil.copy("azure_search_retriever.py", "azure_search_retriever_original.py")
        print("   ✅ Backed up azure_search_retriever.py")

def test_import():
    """Test that the imports work."""
    print("\n🔍 Testing imports...")
    
    try:
        # Test the simple retriever import
        from azure_search_retriever_simple import SimpleAzureSearchRetriever
        print("   ✅ SimpleAzureSearchRetriever imports successfully")
        
        # Test instantiation
        test_retriever = SimpleAzureSearchRetriever(
            endpoint="https://test.search.windows.net",
            api_key="test-key",
            index_name="test-index",
            k=5
        )
        print("   ✅ SimpleAzureSearchRetriever instantiates successfully")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Import test failed: {e}")
        return False

def main():
    print("🚀 Fixing Pydantic BaseRetriever Issue")
    print("="*60)
    
    # Step 1: Backup original
    backup_original()
    
    # Step 2: Create simple retriever
    create_simple_retriever()
    
    # Step 3: Update graph_setup.py
    update_graph_setup()
    
    # Step 4: Test imports
    if test_import():
        print("\n✅ All fixes applied successfully!")
        print("\n🎯 Next steps:")
        print("   1. Run: python app.py")
        print("\n💡 Note: The simple retriever avoids Pydantic complexity")
        print("   while maintaining the same functionality.")
    else:
        print("\n⚠️  Some issues remain. Check the errors above.")

if __name__ == "__main__":
    main()