# fix_imports.py
"""
Fix LangChain import compatibility issues across all files.
"""

import os
import re

def fix_imports_in_file(filepath):
    """Fix imports in a single file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Fix langchain imports
        replacements = [
            # Fix ChatOpenAI import
            (r'from langchain_openai import ChatOpenAI',
             'from langchain.chat_models import ChatOpenAI'),
            
            # Fix langchain-community imports if any
            (r'from langchain_community',
             'from langchain'),
             
            # Fix text splitter imports if any
            (r'from langchain_text_splitters',
             'from langchain.text_splitter'),
        ]
        
        for old_pattern, new_pattern in replacements:
            content = re.sub(old_pattern, new_pattern, content)
        
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Fixed imports in: {filepath}")
            return True
        else:
            print(f"   No changes needed in: {filepath}")
            return False
            
    except Exception as e:
        print(f"❌ Error processing {filepath}: {e}")
        return False

def main():
    """Fix imports in all Python files."""
    print("🔧 Fixing LangChain Import Compatibility")
    print("="*60)
    
    # Files to check
    files_to_check = [
        "memory_manager.py",
        "context_manager.py",
        "graph_setup.py",
        "web_search.py",
        "app.py",
        "azure_search_retriever.py"
    ]
    
    fixed_count = 0
    for filename in files_to_check:
        if os.path.exists(filename):
            if fix_imports_in_file(filename):
                fixed_count += 1
        else:
            print(f"⚠️  File not found: {filename}")
    
    print("\n" + "="*60)
    print(f"✅ Fixed {fixed_count} files")
    
    # Additional compatibility layer
    print("\n📝 Creating compatibility layer...")
    
    compat_content = '''# langchain_compat.py
"""
Compatibility layer for different LangChain versions.
"""

try:
    # Try new import structure first
    from langchain_openai import ChatOpenAI
except ImportError:
    # Fall back to old structure
    from langchain.chat_models import ChatOpenAI

try:
    from langchain_community import *
except ImportError:
    from langchain import *

# Export for other modules
__all__ = ['ChatOpenAI']
'''
    
    with open('langchain_compat.py', 'w') as f:
        f.write(compat_content)
    
    print("✅ Created langchain_compat.py")
    print("\n💡 You can now import from langchain_compat for version-agnostic imports:")
    print("   from langchain_compat import ChatOpenAI")

if __name__ == "__main__":
    main()