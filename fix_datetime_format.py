# fix_datetime_format.py
"""
Fix datetime format issues across all Python files.
Azure Search requires timezone-aware datetime strings.
"""

import os
import re

def fix_datetime_in_file(filepath):
    """Fix datetime usage in a single file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Fix datetime imports
        if 'from datetime import datetime' in content and 'timezone' not in content:
            content = content.replace(
                'from datetime import datetime',
                'from datetime import datetime, timezone'
            )
        
        # Fix datetime.utcnow() calls
        content = re.sub(
            r'datetime\.utcnow\(\)\.isoformat\(\)',
            'datetime.now(timezone.utc).isoformat()',
            content
        )
        
        # Also fix standalone datetime.utcnow()
        content = re.sub(
            r'datetime\.utcnow\(\)',
            'datetime.now(timezone.utc)',
            content
        )
        
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Fixed datetime in: {filepath}")
            return True
        else:
            print(f"   No datetime fixes needed in: {filepath}")
            return False
            
    except Exception as e:
        print(f"❌ Error processing {filepath}: {e}")
        return False

def main():
    """Fix datetime issues in all Python files."""
    print("🔧 Fixing DateTime Format Issues")
    print("="*60)
    
    # Files to check
    files_to_check = [
        "fix_azure_search_data.py",
        "conversation_tracker.py",
        "context_manager.py",
        "memory_manager.py",
        "app.py",
        "test_conversation_history.py",
        "migrate_conversation_data.py"
    ]
    
    fixed_count = 0
    for filename in files_to_check:
        if os.path.exists(filename):
            if fix_datetime_in_file(filename):
                fixed_count += 1
        else:
            print(f"⚠️  File not found: {filename}")
    
    print("\n" + "="*60)
    print(f"✅ Fixed {fixed_count} files")

if __name__ == "__main__":
    main()