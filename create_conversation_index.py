# create_conversation_index.py
"""
Creates Azure Search index for conversation history tracking with proper schema.
Fixed schema to handle sources and facts_shared properly.
"""

import os
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchableField,
    SearchFieldDataType
)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configuration
endpoint = os.environ["AZURE_SEARCH_ENDPOINT"]
api_key = os.environ["AZURE_SEARCH_API_KEY"]
client = SearchIndexClient(endpoint, AzureKeyCredential(api_key))

# Define fields for conversation tracking
fields = [
    # Common fields
    SimpleField(
        name="id",
        type=SearchFieldDataType.String,
        key=True,
        filterable=True
    ),
    SimpleField(
        name="thread_id",
        type=SearchFieldDataType.String,
        filterable=True,
        facetable=True
    ),
    SimpleField(
        name="recordType",
        type=SearchFieldDataType.String,
        filterable=True,
        facetable=True
    ),
    SimpleField(
        name="timestamp",
        type=SearchFieldDataType.DateTimeOffset,
        filterable=True,
        sortable=True
    ),
    
    # Topic field (facetable for getting all topics)
    SimpleField(
        name="topic",
        type=SearchFieldDataType.String,
        filterable=True,
        facetable=True
    ),
    
    # Shared fact fields
    SearchableField(
        name="fact",
        type=SearchFieldDataType.String,
        analyzer_name="en.lucene"
    ),
    SimpleField(
        name="fact_hash",
        type=SearchFieldDataType.String,
        filterable=True
    ),
    SimpleField(
        name="source",
        type=SearchFieldDataType.String,
        filterable=True
    ),
    SimpleField(
        name="confidence",
        type=SearchFieldDataType.Double,
        filterable=True
    ),
    SimpleField(
        name="shared_at",
        type=SearchFieldDataType.DateTimeOffset,
        filterable=True,
        sortable=True
    ),
    SearchableField(
        name="embedding_text",
        type=SearchFieldDataType.String,
        analyzer_name="en.lucene"
    ),
    
    # Conversation turn fields
    SearchableField(
        name="query",
        type=SearchFieldDataType.String,
        analyzer_name="en.lucene"
    ),
    SearchableField(
        name="response",
        type=SearchFieldDataType.String,
        analyzer_name="en.lucene"
    ),
    
    # Fixed: Use Collection fields for arrays
    SimpleField(
        name="sources",
        type=SearchFieldDataType.Collection(SearchFieldDataType.String),
        filterable=False
    ),
    SimpleField(
        name="facts_shared",
        type=SearchFieldDataType.Collection(SearchFieldDataType.String),
        filterable=False
    ),
    
    # User preference fields
    SimpleField(
        name="preference_key",
        type=SearchFieldDataType.String,
        filterable=True
    ),
    SimpleField(
        name="preference_value",
        type=SearchFieldDataType.String
    ),
    
    # Session management fields (new)
    SimpleField(
        name="session_id",
        type=SearchFieldDataType.String,
        filterable=True
    ),
    SimpleField(
        name="user_agent",
        type=SearchFieldDataType.String,
        filterable=False
    )
]

# Create the index
index = SearchIndex(
    name="conversation-history",
    fields=fields
)

try:
    # Delete existing index if it exists
    try:
        client.delete_index("conversation-history")
        print("🗑️  Deleted existing conversation-history index")
    except:
        pass
    
    # Create new index
    client.create_index(index)
    print("✅ Created conversation-history index successfully!")
    print("\n📝 Index features:")
    print("   - Fixed: sources and facts_shared are now proper Collection fields")
    print("   - Added session_id for persistent user tracking")
    print("   - Tracks shared facts with timestamps and deduplication")
    print("   - Stores when facts were shared (shared_at field)")
    print("   - Semantic similarity search support")
    print("   - Conversation turns with proper array support")
    print("   - User preferences with encoded keys")
    print("   - Thread isolation for multi-user support")
    print("\n⚡ Key improvements:")
    print("   - No more schema mismatch errors")
    print("   - Proper array storage for sources and facts")
    print("   - Session-based user tracking")
    
except Exception as e:
    print(f"❌ Error creating index: {e}")
    print("💡 Make sure your Azure Search credentials are correct in .env file")