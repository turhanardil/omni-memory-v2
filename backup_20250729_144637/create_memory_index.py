# create_memory_index.py
import os
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchableField,
    SearchField,
    SearchFieldDataType,
    VectorSearch,
    VectorSearchProfile,
    HnswAlgorithmConfiguration,
    HnswParameters
)

# ─── CONFIG ──────────────────────────
endpoint = os.environ["AZURE_SEARCH_ENDPOINT"]
api_key  = os.environ["AZURE_SEARCH_API_KEY"]
client   = SearchIndexClient(endpoint, AzureKeyCredential(api_key))

# ─── FIELDS ──────────────────────────
fields = [
    # the document key
    SimpleField(
        name="id",
        type=SearchFieldDataType.String,
        key=True,
        filterable=True,
        sortable=True
    ),
    # raw user content
    SearchableField(
        name="content",
        type=SearchFieldDataType.String,
        analyzer_name="en.lucene"
    ),
    # memory category: personal_fact, user_message, web_content, etc.
    SimpleField(
        name="memoryCategory",
        type=SearchFieldDataType.String,
        filterable=True,
        facetable=True
    ),
    # normalized summary of the fact/content
    SearchableField(
        name="memorySummary",
        type=SearchFieldDataType.String,
        analyzer_name="en.lucene"
    ),
    # timestamp with proper timezone support
    SimpleField(
        name="timestamp",
        type=SearchFieldDataType.DateTimeOffset,
        filterable=True,
        sortable=True
    ),
    # source URL for web content
    SimpleField(
        name="source_url",
        type=SearchFieldDataType.String,
        filterable=True,
        facetable=False
    ),
    # title for web content or fact type
    SearchableField(
        name="title",
        type=SearchFieldDataType.String,
        analyzer_name="en.lucene"
    ),
    # the embedding vector field
    SearchField(
        name="contentVector",
        type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
        searchable=True,
        vector_search_dimensions=1536,
        vector_search_profile_name="hnsw-config"
    )
]

# ─── VECTOR CONFIG ───────────────────
vector_search = VectorSearch(
    profiles=[
        VectorSearchProfile(
            name="hnsw-config",
            algorithm_configuration_name="hnsw-config"
        )
    ],
    algorithms=[
        HnswAlgorithmConfiguration(
            name="hnsw-config",
            parameters=HnswParameters(
                m=4,
                ef_construction=400,
                ef_search=100,
                metric="cosine"
            )
        )
    ]
)

# ─── BUILD & PUSH INDEX ─────────────
index = SearchIndex(
    name="omniscient-memory",
    fields=fields,
    vector_search=vector_search
)

try:
    client.create_or_update_index(index)
    print("✅ Index updated with context-aware memory support")
    print("📝 Supported memory categories:")
    print("   - personal_fact: User's personal information (name, company, preferences)")
    print("   - user_message: User's conversation messages")
    print("   - web_content: Information from web searches")
    print("   - Other custom categories as needed")
    print("\n🔧 Features:")
    print("   - Vector search with cosine similarity")
    print("   - Full-text search on content and summaries")
    print("   - Filtering by category and timestamp")
    print("   - Support for web content metadata (URL, title)")
except Exception as e:
    print(f"❌ Error updating index: {e}")
    print("💡 Make sure your Azure Search credentials are correct in .env file")