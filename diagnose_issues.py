# diagnose_issues.py
"""
Diagnostic script to help identify and fix common issues with the memory chatbot.
Run this when experiencing problems to get detailed diagnostic information.
"""

import os
import sys
from dotenv import load_dotenv
from datetime import datetime, timezone
import json

load_dotenv()

def check_environment():
    """Check if all required environment variables are set."""
    print("🔍 Checking environment variables...")
    
    required_vars = [
        "AZURE_SEARCH_ENDPOINT",
        "AZURE_SEARCH_API_KEY", 
        "AZURE_INDEX_NAME",
        "OPENAI_API_KEY"
    ]
    
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
            print(f"   ❌ {var}: NOT SET")
        else:
            value = os.getenv(var)
            # Mask sensitive data
            if "KEY" in var:
                masked = value[:8] + "..." + value[-4:] if len(value) > 12 else "***"
                print(f"   ✅ {var}: {masked}")
            else:
                print(f"   ✅ {var}: {value}")
    
    return len(missing) == 0

def test_openai_connection():
    """Test OpenAI API connection."""
    print("\n🔍 Testing OpenAI connection...")
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Try a simple embedding
        response = client.embeddings.create(
            model="text-embedding-ada-002",
            input="test"
        )
        
        print("   ✅ OpenAI connection successful!")
        print(f"   ✅ Embedding dimension: {len(response.data[0].embedding)}")
        return True
        
    except Exception as e:
        print(f"   ❌ OpenAI connection failed: {e}")
        return False

def test_azure_indices():
    """Test Azure Search indices and their schemas."""
    print("\n🔍 Testing Azure Search indices...")
    
    try:
        from azure.core.credentials import AzureKeyCredential
        from azure.search.documents import SearchClient
        from azure.search.documents.indexes import SearchIndexClient
        
        endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
        api_key = os.getenv("AZURE_SEARCH_API_KEY")
        
        # Test index client
        index_client = SearchIndexClient(endpoint, AzureKeyCredential(api_key))
        
        # Check indices
        indices = list(index_client.list_indexes())
        print(f"   ✅ Found {len(indices)} indices")
        
        required_indices = ["omniscient-memory", "conversation-history"]
        found_indices = [idx.name for idx in indices]
        
        for required in required_indices:
            if required in found_indices:
                print(f"   ✅ Index '{required}' exists")
                
                # Check if we can query it
                try:
                    client = SearchClient(endpoint, required, AzureKeyCredential(api_key))
                    results = list(client.search(search_text="*", top=1))
                    print(f"      - Can query: ✅")
                    
                    # Check schema for conversation-history
                    if required == "conversation-history":
                        idx = next(i for i in indices if i.name == required)
                        field_names = [f.name for f in idx.fields]
                        
                        # Check for critical fields
                        critical_fields = ["sources", "facts_shared"]
                        for field in critical_fields:
                            if field in field_names:
                                field_obj = next(f for f in idx.fields if f.name == field)
                                if hasattr(field_obj, 'type') and 'Collection' in str(field_obj.type):
                                    print(f"      - Field '{field}': ✅ (Collection type)")
                                else:
                                    print(f"      - Field '{field}': ⚠️  (Not a Collection type)")
                            else:
                                print(f"      - Field '{field}': ❌ (Missing)")
                                
                except Exception as e:
                    print(f"      - Can query: ❌ ({e})")
            else:
                print(f"   ❌ Index '{required}' NOT FOUND")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Azure Search test failed: {e}")
        return False

def test_conversation_tracking():
    """Test conversation tracking functionality."""
    print("\n🔍 Testing conversation tracking...")
    
    try:
        from conversation_tracker import ConversationTracker
        
        # Create a test tracker
        test_thread = f"diagnostic_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        tracker = ConversationTracker(test_thread)
        
        # Test adding a fact
        fact_id = tracker.add_shared_fact(
            topic="diagnostic_test",
            fact="This is a diagnostic test fact",
            source="diagnostic"
        )
        
        if fact_id:
            print("   ✅ Can add shared facts")
        else:
            print("   ❌ Cannot add shared facts")
        
        # Test adding conversation turn
        try:
            tracker.add_conversation_turn(
                topic="diagnostic_test",
                query="Test query",
                response="Test response",
                sources=["test_source"],
                fact_ids=[fact_id] if fact_id else []
            )
            print("   ✅ Can add conversation turns")
        except Exception as e:
            print(f"   ❌ Cannot add conversation turns: {e}")
        
        # Test retrieval
        facts = tracker.get_shared_facts("diagnostic_test")
        if facts:
            print(f"   ✅ Can retrieve facts (found {len(facts)})")
        else:
            print("   ⚠️  No facts retrieved (might be empty)")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Conversation tracking test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_web_search():
    """Test web search functionality."""
    print("\n🔍 Testing web search...")
    
    try:
        from web_search import search_and_scrape, get_weather_direct
        
        # Test weather API
        weather = get_weather_direct("London")
        if weather:
            print("   ✅ Weather API working")
        else:
            print("   ⚠️  Weather API not responding")
        
        # Test DuckDuckGo search
        results = search_and_scrape("Python programming", num_urls=1)
        if results:
            print(f"   ✅ DuckDuckGo search working (found {len(results)} results)")
        else:
            print("   ❌ DuckDuckGo search not working")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Web search test failed: {e}")
        return False

def analyze_common_issues():
    """Analyze and suggest fixes for common issues."""
    print("\n📋 Common Issues Analysis...")
    
    issues = []
    
    # Check for proxy issues
    proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']
    active_proxies = [var for var in proxy_vars if os.getenv(var)]
    if active_proxies:
        issues.append({
            "issue": "Proxy configuration detected",
            "severity": "warning",
            "fix": "Proxy settings may interfere with API calls. Consider unsetting them or configuring properly."
        })
    
    # Check for conversation history issues
    try:
        from azure.core.credentials import AzureKeyCredential
        from azure.search.documents import SearchClient
        
        client = SearchClient(
            os.getenv("AZURE_SEARCH_ENDPOINT"),
            "conversation-history",
            AzureKeyCredential(os.getenv("AZURE_SEARCH_API_KEY"))
        )
        
        # Look for documents with old schema
        results = client.search(
            search_text="*",
            filter="recordType eq 'conversation_turn'",
            select=["id", "sources_str", "facts_shared_str"],
            top=5
        )
        
        old_schema_docs = 0
        for doc in results:
            if "sources_str" in doc or "facts_shared_str" in doc:
                old_schema_docs += 1
        
        if old_schema_docs > 0:
            issues.append({
                "issue": f"Found {old_schema_docs} documents with old schema",
                "severity": "error",
                "fix": "Run migrate_conversation_data.py to fix the schema"
            })
            
    except:
        pass
    
    # Display issues
    if issues:
        print("\n⚠️  Issues found:")
        for issue in issues:
            icon = "❌" if issue["severity"] == "error" else "⚠️"
            print(f"\n{icon} {issue['issue']}")
            print(f"   Fix: {issue['fix']}")
    else:
        print("\n✅ No common issues detected!")

def generate_report():
    """Generate a diagnostic report."""
    print("\n" + "="*60)
    print("📊 DIAGNOSTIC REPORT")
    print("="*60)
    print(f"Generated: {datetime.now(timezone.utc).isoformat()}")
    print(f"Python Version: {sys.version.split()[0]}")
    print(f"Platform: {sys.platform}")
    
    # Summary
    all_tests = []
    
    print("\n🔧 Environment Check:")
    env_ok = check_environment()
    all_tests.append(("Environment Variables", env_ok))
    
    if env_ok:
        print("\n🔧 Service Tests:")
        
        openai_ok = test_openai_connection()
        all_tests.append(("OpenAI Connection", openai_ok))
        
        azure_ok = test_azure_indices()
        all_tests.append(("Azure Search", azure_ok))
        
        tracking_ok = test_conversation_tracking()
        all_tests.append(("Conversation Tracking", tracking_ok))
        
        search_ok = test_web_search()
        all_tests.append(("Web Search", search_ok))
    
    # Common issues
    analyze_common_issues()
    
    # Final summary
    print("\n" + "="*60)
    print("📊 SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, ok in all_tests if ok)
    total = len(all_tests)
    
    print(f"\nTests passed: {passed}/{total}")
    
    for test_name, ok in all_tests:
        status = "✅ PASS" if ok else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    if passed == total:
        print("\n✅ All systems operational!")
    else:
        print("\n❌ Some issues detected. Please review the output above.")
        print("\n💡 Next steps:")
        print("   1. Fix any missing environment variables")
        print("   2. If schema issues exist, run: python migrate_conversation_data.py")
        print("   3. If indices are missing, run: python create_conversation_index.py")
        print("   4. Check the error messages above for specific fixes")

if __name__ == "__main__":
    print("🔍 Memory Chatbot Diagnostic Tool")
    print("This will run various tests to identify issues with your setup.")
    print()
    
    generate_report()
    
    print("\n✅ Diagnostic complete!")