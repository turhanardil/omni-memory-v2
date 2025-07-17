import os, uuid
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

AZ_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
AZ_KEY      = os.getenv("AZURE_SEARCH_API_KEY")
INDEX_NAME  = os.getenv("AZURE_INDEX_NAME")

search_client = SearchClient(AZ_ENDPOINT, INDEX_NAME, AzureKeyCredential(AZ_KEY))
openai_client = OpenAI()

def get_embedding(text: str) -> list[float]:
    resp = openai_client.embeddings.create(model="text-embedding-ada-002", input=text)
    return resp.data[0].embedding

def store_memory(text: str):
    vec = get_embedding(text)
    doc = {
        "id": str(uuid.uuid4()),
        "content": text,
        "contentVector": vec
    }
    result = search_client.upload_documents(documents=[doc])
    if not result[0].succeeded:
        raise RuntimeError(f"Failed to store memory: {result[0].status_code}")
