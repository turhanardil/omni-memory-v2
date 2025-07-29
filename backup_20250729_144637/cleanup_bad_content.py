# cleanup_bad_content.py
"""
Utility to clean up bad/irrelevant content from Azure Search index.
Run this when you notice the system has cached incorrect information.
"""

import os
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from dotenv import load_dotenv

load_dotenv()

AZ_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
AZ_KEY = os.getenv("AZURE_SEARCH_API_KEY")
INDEX_NAME = os.getenv("AZURE_INDEX_NAME")

search_client = SearchClient(AZ_ENDPOINT, INDEX_NAME, AzureKeyCredential(AZ_KEY))

def find_and_remove_bad_tokyo_content():
    """Find and remove Tokyo weather content that actually contains Minnesota information."""
    
    print("🔍 Searching for potentially bad Tokyo weather content...")
    
    # Search for web content related to Tokyo weather
    results = search_client.search(
        search_text="Tokyo weather",
        search_fields=["content", "memorySummary"],
        filter="memoryCategory eq 'web_content'",
        select=["id", "content", "memorySummary", "source_url"]
    )
    
    bad_content_ids = []
    
    for result in results:
        content = result.get("content", "").lower()
        summary = result.get("memorySummary", "").lower()
        
        # Check if content mentions wrong locations
        if 'minnesota' in content or 'minnesota' in summary:
            print(f"❌ Found bad content (ID: {result['id']}): {result.get('memorySummary', '')[:100]}...")
            bad_content_ids.append(result["id"])
    
    if bad_content_ids:
        print(f"🗑️  Removing {len(bad_content_ids)} bad content items...")
        
        # Delete bad content
        documents_to_delete = [{"id": doc_id} for doc_id in bad_content_ids]
        result = search_client.delete_documents(documents=documents_to_delete)
        
        successful_deletions = sum(1 for r in result if r.succeeded)
        print(f"✅ Successfully removed {successful_deletions} bad content items")
    else:
        print("✅ No bad Tokyo weather content found")

def remove_all_web_content():
    """Remove ALL web content - use this to start fresh with web searches."""
    
    print("🗑️  WARNING: This will remove ALL web search results from memory!")
    confirm = input("Type 'yes' to confirm: ")
    
    if confirm.lower() != 'yes':
        print("❌ Cancelled")
        return
    
    print("🔍 Finding all web content...")
    
    results = search_client.search(
        search_text="*",
        filter="memoryCategory eq 'web_content'",
        select=["id"]
    )
    
    web_content_ids = [result["id"] for result in results]
    
    if web_content_ids:
        print(f"🗑️  Removing {len(web_content_ids)} web content items...")
        
        documents_to_delete = [{"id": doc_id} for doc_id in web_content_ids]
        result = search_client.delete_documents(documents=documents_to_delete)
        
        successful_deletions = sum(1 for r in result if r.succeeded)
        print(f"✅ Successfully removed {successful_deletions} web content items")
    else:
        print("✅ No web content found to remove")

def show_recent_content():
    """Show recent content to help identify what needs cleaning."""
    
    print("📋 Recent web content:")
    
    results = search_client.search(
        search_text="*",
        filter="memoryCategory eq 'web_content'",
        select=["id", "memorySummary", "source_url", "timestamp"],
        order_by=["timestamp desc"],
        top=10
    )
    
    for i, result in enumerate(results, 1):
        print(f"{i}. {result.get('memorySummary', 'No summary')[:100]}...")
        print(f"   Source: {result.get('source_url', 'No URL')}")
        print(f"   Time: {result.get('timestamp', 'No timestamp')}")
        print()

if __name__ == "__main__":
    print("🧹 Azure Search Content Cleanup Utility")
    print("=" * 50)
    
    while True:
        print("\nOptions:")
        print("1. Show recent web content")
        print("2. Remove bad Tokyo weather content")
        print("3. Remove ALL web content (nuclear option)")
        print("4. Exit")
        
        choice = input("\nChoose an option (1-4): ").strip()
        
        if choice == "1":
            show_recent_content()
        elif choice == "2":
            find_and_remove_bad_tokyo_content()
        elif choice == "3":
            remove_all_web_content()
        elif choice == "4":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice")