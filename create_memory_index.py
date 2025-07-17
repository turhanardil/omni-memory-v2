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
    # generic category tag (fact, preference, goal…)
    SimpleField(
        name="memoryCategory",
        type=SearchFieldDataType.String,
        filterable=True,
        facetable=True
    ),
    # normalized summary of the fact
    SearchableField(
        name="memorySummary",
        type=SearchFieldDataType.String,
        analyzer_name="en.lucene"
    ),
    # timestamp
    SimpleField(
        name="timestamp",
        type=SearchFieldDataType.DateTimeOffset,
        filterable=True,
        sortable=True
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
                ef_search=100
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

client.create_or_update_index(index)
print("✅ Index updated with generic metadata fields.")
