# fix_azure_search_data.py
"""
Script to diagnose and fix Azure Search data issues.
Helps with indexing delays and data visibility problems.
"""

import os
import time
from datetime import datetime, timezone
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient

load_dotenv()

def check_index_statistics():
    """Check index statistics to understand data volume."""
    print("📊 Checking index statistics...")
    
    try:
        client = SearchIndexClient(
            os.environ["AZURE_SEARCH_ENDPOINT"],
            AzureKeyCredential(os.environ["AZURE_SEARCH_API_KEY"])
        )
        
        # Get index statistics
        index_name = "conversation-history"
        stats = client.get_index_statistics(index_name)
        
        print(f"\n✅ Index: {index_name}")
        if hasattr(stats, 'document_count'):
            print(f"   Document Count: {stats.document_count}")
            print(f"   Storage Size: {stats.storage_size} bytes")
        else:
            # Stats might be a dict
            print(f"   Statistics: {stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error getting statistics: {e}")
        return False

def test_document_upload_and_retrieval():
    """Test uploading a document and retrieving it."""
    print("\n🧪 Testing document upload and retrieval...")
    
    try:
        client = SearchClient(
            os.environ["AZURE_SEARCH_ENDPOINT"],
            "conversation-history",
            AzureKeyCredential(os.environ["AZURE_SEARCH_API_KEY"])
        )
        
        # Create a test document
        test_id = f"test_doc_{int(time.time())}"
        test_doc = {
            "id": test_id,
            "thread_id": "test_thread",
            "topic": "test_topic",
            "recordType": "conversation_turn",
            "query": "Test query",
            "response": "Test response",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "sources": ["test_source"],
            "facts_shared": ["test_fact"],
            "session_id": "test_session"
        }
        
        print(f"📤 Uploading test document with ID: {test_id}")
        result = client.upload_documents(documents=[test_doc])
        
        if result[0].succeeded:
            print("✅ Upload successful")
        else:
            print(f"❌ Upload failed: {result[0].error}")
            return False
        
        # Try to retrieve immediately
        print("\n🔍 Attempting immediate retrieval...")
        doc = client.get_document(key=test_id)
        if doc:
            print("✅ Document retrieved immediately!")
        
        # Wait and try again
        print("\n⏳ Waiting 2 seconds for indexing...")
        time.sleep(2)
        
        print("🔍 Attempting retrieval after delay...")
        doc = client.get_document(key=test_id)
        if doc:
            print("✅ Document retrieved after delay!")
            print(f"   Document: {doc}")
        else:
            print("❌ Document not found even after delay")
        
        # Try searching
        print("\n🔍 Testing search...")
        results = client.search(
            search_text="*",
            filter=f"id eq '{test_id}'",
            select=["id", "thread_id", "topic"]
        )
        
        found = False
        for result in results:
            if result["id"] == test_id:
                found = True
                print("✅ Document found via search!")
                break
        
        if not found:
            print("❌ Document not found via search")
            
            # Wait more and try again
            print("\n⏳ Waiting 5 more seconds...")
            time.sleep(5)
            
            results = client.search(
                search_text="*",
                filter=f"id eq '{test_id}'",
                select=["id", "thread_id", "topic"]
            )
            
            for result in results:
                if result["id"] == test_id:
                    found = True
                    print("✅ Document found after extended wait!")
                    break
        
        # Clean up
        print("\n🧹 Cleaning up test document...")
        client.delete_documents(documents=[{"id": test_id}])
        
        return found
        
    except Exception as e:
        print(f"❌ Error in test: {e}")
        import traceback
        traceback.print_exc()
        return False

def analyze_indexing_delay():
    """Analyze typical indexing delay by uploading multiple documents."""
    print("\n⏱️  Analyzing indexing delays...")
    
    try:
        client = SearchClient(
            os.environ["AZURE_SEARCH_ENDPOINT"],
            "conversation-history",
            AzureKeyCredential(os.environ["AZURE_SEARCH_API_KEY"])
        )
        
        # Upload multiple test documents
        test_docs = []
        base_time = int(time.time())
        
        for i in range(5):
            doc_id = f"delay_test_{base_time}_{i}"
            test_docs.append({
                "id": doc_id,
                "thread_id": f"delay_test_thread_{base_time}",
                "topic": "delay_test",
                "recordType": "conversation_turn",
                "query": f"Test query {i}",
                "response": f"Test response {i}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "sources": [],
                "facts_shared": [],
                "session_id": "delay_test"
            })
        
        print(f"📤 Uploading {len(test_docs)} test documents...")
        upload_time = time.time()
        results = client.upload_documents(documents=test_docs)
        
        # Check upload success
        successful = sum(1 for r in results if r.succeeded)
        print(f"✅ {successful}/{len(test_docs)} documents uploaded successfully")
        
        # Test retrieval at different intervals
        delays = []
        for delay in [0.5, 1.0, 2.0, 3.0, 5.0]:
            time.sleep(delay)
            elapsed = time.time() - upload_time
            
            # Search for documents
            search_results = client.search(
                search_text="*",
                filter=f"thread_id eq 'delay_test_thread_{base_time}'",
                top=10
            )
            
            found_count = sum(1 for _ in search_results)
            delays.append((elapsed, found_count))
            print(f"   After {elapsed:.1f}s: Found {found_count}/{len(test_docs)} documents")
            
            if found_count == len(test_docs):
                print(f"✅ All documents indexed after {elapsed:.1f} seconds")
                break
        
        # Clean up
        print("\n🧹 Cleaning up test documents...")
        for doc in test_docs:
            try:
                client.delete_documents(documents=[{"id": doc["id"]}])
            except:
                pass
        
        # Recommendations
        print("\n💡 Recommendations based on analysis:")
        if delays and delays[-1][1] == len(test_docs):
            optimal_delay = delays[-1][0]
            print(f"   - Use a delay of at least {optimal_delay:.1f} seconds after uploads")
        else:
            print("   - Indexing seems slow; consider using longer delays (5+ seconds)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error analyzing delays: {e}")
        return False

def verify_field_types():
    """Verify that field types are correct in the index."""
    print("\n🔍 Verifying field types in index...")
    
    try:
        client = SearchIndexClient(
            os.environ["AZURE_SEARCH_ENDPOINT"],
            AzureKeyCredential(os.environ["AZURE_SEARCH_API_KEY"])
        )
        
        index = client.get_index("conversation-history")
        
        # Check critical fields
        critical_fields = {
            "sources": "Collection(Edm.String)",
            "facts_shared": "Collection(Edm.String)",
            "thread_id": "Edm.String",
            "session_id": "Edm.String"
        }
        
        print("\n📋 Field type verification:")
        all_good = True
        
        for field in index.fields:
            if field.name in critical_fields:
                expected = critical_fields[field.name]
                actual = str(field.type)
                
                if expected in actual:
                    print(f"   ✅ {field.name}: {actual}")
                else:
                    print(f"   ❌ {field.name}: Expected {expected}, got {actual}")
                    all_good = False
        
        if all_good:
            print("\n✅ All critical fields have correct types!")
        else:
            print("\n❌ Some fields have incorrect types. Recreate the index.")
        
        return all_good
        
    except Exception as e:
        print(f"❌ Error verifying fields: {e}")
        return False

def main():
    """Run all diagnostics and provide recommendations."""
    print("🔧 Azure Search Data Diagnostics")
    print("="*60)
    
    # Check index statistics
    check_index_statistics()
    
    # Verify field types
    field_types_ok = verify_field_types()
    
    if not field_types_ok:
        print("\n⚠️  Field type issues detected!")
        print("   Run: python create_conversation_index.py")
        print("   to recreate the index with correct schema.")
        return
    
    # Test upload and retrieval
    upload_ok = test_document_upload_and_retrieval()
    
    # Analyze delays
    analyze_indexing_delay()
    
    print("\n" + "="*60)
    print("📊 Summary and Recommendations:")
    print("="*60)
    
    if upload_ok:
        print("\n✅ Azure Search is working correctly!")
        print("\n💡 Best Practices:")
        print("   1. Add delays after uploads (2-3 seconds recommended)")
        print("   2. Use force_refresh() when testing persistence")
        print("   3. For production, consider using Azure Search's")
        print("      'refresh' parameter or implement retry logic")
    else:
        print("\n❌ Issues detected with Azure Search")
        print("\n🔧 Troubleshooting steps:")
        print("   1. Check your Azure Search service tier")
        print("   2. Verify index isn't at capacity")
        print("   3. Check Azure portal for service health")
        print("   4. Consider recreating the index")
    
    print("\n📝 Code recommendations:")
    print("   - Update ConversationTracker to use 2-3 second delays")
    print("   - Implement retry logic for searches after uploads")
    print("   - Use force_refresh() when loading historical data")

if __name__ == "__main__":
    main()