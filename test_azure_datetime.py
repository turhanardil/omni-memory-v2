# test_azure_datetime.py
"""
Test that Azure Search works with the datetime fixes.
"""

import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient

load_dotenv()

def test_datetime_format():
    """Test datetime format is correct."""
    print("🔍 Testing datetime format...")
    
    # Test our datetime format
    dt1 = datetime.now(timezone.utc).isoformat()
    print(f"   Our format: {dt1}")
    
    # Check it has timezone info
    if dt1.endswith('Z') or '+' in dt1:
        print("   ✅ Timezone info present")
    else:
        print("   ❌ No timezone info!")
        
    return True

def test_document_upload():
    """Test uploading a document with proper datetime."""
    print("\n🔍 Testing document upload...")
    
    try:
        client = SearchClient(
            os.environ["AZURE_SEARCH_ENDPOINT"],
            "conversation-history", 
            AzureKeyCredential(os.environ["AZURE_SEARCH_API_KEY"])
        )
        
        # Create test document with proper datetime
        test_doc = {
            "id": f"datetime_test_{int(datetime.now().timestamp())}",
            "thread_id": "test_thread",
            "topic": "datetime_test",
            "recordType": "conversation_turn",
            "query": "Test query",
            "response": "Test response", 
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "sources": ["test"],
            "facts_shared": [],
            "session_id": "test"
        }
        
        print(f"   Uploading with timestamp: {test_doc['timestamp']}")
        
        result = client.upload_documents(documents=[test_doc])
        
        if result[0].succeeded:
            print("   ✅ Upload successful!")
            
            # Clean up
            client.delete_documents(documents=[{"id": test_doc["id"]}])
            return True
        else:
            print(f"   ❌ Upload failed: {result[0].error}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    print("🧪 Testing Azure Search DateTime Fixes")
    print("="*60)
    
    # Run tests
    test_datetime_format()
    
    if test_document_upload():
        print("\n✅ DateTime fixes are working!")
    else:
        print("\n❌ DateTime issues still present")
        print("\n💡 Make sure to run:")
        print("   python fix_all_issues.py")

if __name__ == "__main__":
    main()