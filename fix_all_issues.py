# fix_all_issues.py
"""
Comprehensive fix script for all current issues.
"""

import os
import re
import subprocess
import sys

def fix_datetime_issues():
    """Fix datetime format issues in all files."""
    print("🔧 Fixing DateTime format issues...")
    
    files_with_datetime = [
        "fix_azure_search_data.py",
        "conversation_tracker.py", 
        "context_manager.py",
        "memory_manager.py",
        "test_conversation_history.py",
        "migrate_conversation_data.py"
    ]
    
    for filepath in files_with_datetime:
        if not os.path.exists(filepath):
            continue
            
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original = content
            
            # Fix imports
            if 'from datetime import datetime' in content and ', timezone' not in content:
                content = content.replace(
                    'from datetime import datetime',
                    'from datetime import datetime, timezone'
                )
            
            # Fix datetime.utcnow() usage
            content = re.sub(
                r'datetime\.utcnow\(\)\.isoformat\(\)',
                'datetime.now(timezone.utc).isoformat()',
                content
            )
            
            content = re.sub(
                r'datetime\.utcnow\(\)',
                'datetime.now(timezone.utc)',
                content
            )
            
            if content != original:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"   ✅ Fixed datetime in {filepath}")
                
        except Exception as e:
            print(f"   ❌ Error fixing {filepath}: {e}")

def fix_langgraph_imports():
    """Fix langgraph import issues."""
    print("\n🔧 Fixing langgraph imports...")
    
    # Update graph_setup.py
    graph_file = "graph_setup.py"
    if os.path.exists(graph_file):
        try:
            with open(graph_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Fix InMemorySaver import
            content = content.replace(
                'from langgraph.checkpoint.memory import InMemorySaver',
                'from langgraph.checkpoint.memory import MemorySaver'
            )
            
            # Fix usage
            content = content.replace('InMemorySaver()', 'MemorySaver()')
            
            with open(graph_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("   ✅ Fixed langgraph imports")
            
        except Exception as e:
            print(f"   ❌ Error fixing langgraph: {e}")

def fix_langchain_imports():
    """Update all files to use the compatibility wrapper."""
    print("\n🔧 Updating LangChain imports...")
    
    files_to_update = [
        "memory_manager.py",
        "context_manager.py",
        "graph_setup.py",
        "web_search.py"
    ]
    
    for filepath in files_to_update:
        if not os.path.exists(filepath):
            continue
            
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Replace various import patterns
            replacements = [
                ('from langchain.chat_models import ChatOpenAI', 
                 'from langchain_chat_compat import ChatOpenAI'),
                ('from langchain_openai import ChatOpenAI',
                 'from langchain_chat_compat import ChatOpenAI'),
                ('from langchain_community.chat_models import ChatOpenAI',
                 'from langchain_chat_compat import ChatOpenAI')
            ]
            
            for old, new in replacements:
                if old in content:
                    content = content.replace(old, new)
                    print(f"   ✅ Updated imports in {filepath}")
                    
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
                
        except Exception as e:
            print(f"   ❌ Error updating {filepath}: {e}")

def create_web_search_fix():
    """Fix web_search.py specifically."""
    print("\n🔧 Fixing web_search.py...")
    
    if os.path.exists("web_search.py"):
        try:
            with open("web_search.py", 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Update the import and initialization
            for i, line in enumerate(lines):
                if 'from langchain' in line and 'ChatOpenAI' in line:
                    lines[i] = 'from langchain_chat_compat import ChatOpenAI\n'
                elif 'query_analyzer = ChatOpenAI' in line:
                    # Already should be fine
                    pass
            
            with open("web_search.py", 'w', encoding='utf-8') as f:
                f.writelines(lines)
                
            print("   ✅ Fixed web_search.py")
            
        except Exception as e:
            print(f"   ❌ Error fixing web_search.py: {e}")

def verify_fixes():
    """Verify that the fixes work."""
    print("\n🔍 Verifying fixes...")
    
    # Test imports
    try:
        print("   Testing imports...")
        subprocess.check_output([sys.executable, "-c", 
            "from langchain_chat_compat import ChatOpenAI; "
            "from langgraph.checkpoint.memory import MemorySaver; "
            "from datetime import datetime, timezone; "
            "print('✅ All imports working!')"
        ], stderr=subprocess.STDOUT, text=True)
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Import test failed: {e.output}")
        return False
    
    return True

def main():
    print("🚀 Comprehensive Fix Script")
    print("="*60)
    
    # Run all fixes
    fix_datetime_issues()
    fix_langgraph_imports()
    fix_langchain_imports()
    fix_web_search_fix()
    
    # Verify
    if verify_fixes():
        print("\n✅ All fixes applied successfully!")
        print("\n🎯 Next steps:")
        print("   1. Run: python diagnose_issues.py")
        print("   2. Run: python test_conversation_history.py")
        print("   3. Run: python app.py")
    else:
        print("\n⚠️  Some fixes may have failed. Check the output above.")

if __name__ == "__main__":
    main()