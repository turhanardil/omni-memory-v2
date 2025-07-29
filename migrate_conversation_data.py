# migrate_conversation_data.py
"""
Migration script to fix existing conversation data with the new schema.
This will read old data and re-upload it with the correct field types.
"""

import os
import json
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from datetime import datetime, timezone

load_dotenv()

def migrate_conversation_history():
    """Migrate conversation history data to new schema."""
    print("🔄 Starting conversation history migration...")
    
    endpoint = os.environ["AZURE_SEARCH_ENDPOINT"]
    api_key = os.environ["AZURE_SEARCH_API_KEY"]
    
    # Connect to old index
    old_client = SearchClient(
        endpoint,
        "conversation-history",
        AzureKeyCredential(api_key)
    )
    
    # Backup data first
    print("📦 Backing up existing data...")
    backup_data = []
    
    try:
        # Get all documents
        results = old_client.search(
            search_text="*",
            select=["*"],
            top=1000
        )
        
        for doc in results:
            backup_data.append(doc)
        
        print(f"✅ Backed up {len(backup_data)} documents")
        
        # Save backup to file
        backup_filename = f"conversation_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(backup_filename, 'w') as f:
            json.dump(backup_data, f, indent=2, default=str)
        print(f"💾 Backup saved to {backup_filename}")
        
    except Exception as e:
        print(f"❌ Error backing up data: {e}")
        return False
    
    # Process and fix documents
    print("\n🔧 Processing documents for migration...")
    fixed_docs = []
    
    for doc in backup_data:
        try:
            fixed_doc = doc.copy()
            
            # Fix conversation turn documents
            if doc.get("recordType") == "conversation_turn":
                # Convert sources_str to sources array
                if "sources_str" in doc and "sources" not in doc:
                    try:
                        fixed_doc["sources"] = json.loads(doc["sources_str"])
                    except:
                        fixed_doc["sources"] = []
                elif "sources" not in doc:
                    fixed_doc["sources"] = []
                
                # Convert facts_shared_str to facts_shared array
                if "facts_shared_str" in doc and "facts_shared" not in doc:
                    try:
                        fixed_doc["facts_shared"] = json.loads(doc["facts_shared_str"])
                    except:
                        fixed_doc["facts_shared"] = []
                elif "facts_shared" not in doc:
                    fixed_doc["facts_shared"] = []
                
                # Remove old string fields
                fixed_doc.pop("sources_str", None)
                fixed_doc.pop("facts_shared_str", None)
            
            # Ensure all required fields exist
            if "session_id" not in fixed_doc:
                fixed_doc["session_id"] = fixed_doc.get("thread_id", "unknown")
            
            if "user_agent" not in fixed_doc:
                fixed_doc["user_agent"] = ""
            
            fixed_docs.append(fixed_doc)
            
        except Exception as e:
            print(f"⚠️ Error processing document {doc.get('id', 'unknown')}: {e}")
    
    print(f"✅ Processed {len(fixed_docs)} documents")
    
    # Ask for confirmation before uploading
    print("\n⚠️  This will update the conversation-history index with the new schema.")
    response = input("Do you want to proceed? (yes/no): ")
    
    if response.lower() != "yes":
        print("❌ Migration cancelled")
        return False
    
    # Upload fixed documents
    print("\n📤 Uploading fixed documents...")
    try:
        # Upload in batches
        batch_size = 100
        for i in range(0, len(fixed_docs), batch_size):
            batch = fixed_docs[i:i+batch_size]
            results = old_client.merge_or_upload_documents(documents=batch)
            
            successful = sum(1 for r in results if r.succeeded)
            print(f"   Batch {i//batch_size + 1}: {successful}/{len(batch)} documents uploaded")
        
        print("\n✅ Migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error uploading documents: {e}")
        print("💡 Your backup is saved. You may need to recreate the index with the new schema.")
        return False

def verify_migration():
    """Verify that the migration was successful."""
    print("\n🔍 Verifying migration...")
    
    try:
        client = SearchClient(
            os.environ["AZURE_SEARCH_ENDPOINT"],
            "conversation-history",
            AzureKeyCredential(os.environ["AZURE_SEARCH_API_KEY"])
        )
        
        # Check a few conversation turns
        results = client.search(
            search_text="*",
            filter="recordType eq 'conversation_turn'",
            top=5
        )
        
        issues = []
        for doc in results:
            if "sources" not in doc or not isinstance(doc.get("sources"), list):
                issues.append(f"Document {doc['id']} missing proper sources array")
            if "facts_shared" not in doc or not isinstance(doc.get("facts_shared"), list):
                issues.append(f"Document {doc['id']} missing proper facts_shared array")
        
        if issues:
            print("❌ Migration verification failed:")
            for issue in issues:
                print(f"   - {issue}")
            return False
        else:
            print("✅ Migration verification passed!")
            return True
            
    except Exception as e:
        print(f"❌ Error verifying migration: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Conversation History Migration Tool")
    print("="*60)
    print("This tool will migrate your conversation history to the new schema.")
    print("It will create a backup before making any changes.")
    print("="*60)
    print()
    
    # Run migration
    if migrate_conversation_history():
        # Verify if successful
        verify_migration()
    
    print("\n✅ Migration process complete!")