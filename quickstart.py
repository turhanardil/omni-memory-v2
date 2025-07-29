# quickstart.py
"""
Quick start script - fixes all issues and starts the app.
"""

import subprocess
import sys
import os
import time

def run_command(cmd, description):
    """Run a command and show status."""
    print(f"\n🔧 {description}...")
    try:
        result = subprocess.run(
            [sys.executable] + cmd.split(),
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"   ✅ Success!")
            if result.stdout and len(result.stdout.strip()) < 200:
                print(f"   {result.stdout.strip()}")
            return True
        else:
            print(f"   ❌ Failed!")
            if result.stderr:
                print(f"   Error: {result.stderr[:200]}")
            return False
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return False

def main():
    print("🚀 Memory Chatbot Quick Start")
    print("="*60)
    
    # Step 1: Create compatibility wrapper if needed
    if not os.path.exists("langchain_chat_compat.py"):
        print("\n📝 Creating compatibility wrapper...")
        compat_code = '''# langchain_chat_compat.py
"""
Compatibility wrapper for ChatOpenAI to handle import changes.
"""

import warnings

# Suppress the specific deprecation warning
warnings.filterwarnings("ignore", category=DeprecationWarning, module="langchain.chat_models")

try:
    # Try the new import first
    from langchain_openai import ChatOpenAI
except ImportError:
    try:
        # Fall back to community import
        from langchain_community.chat_models import ChatOpenAI
    except ImportError:
        # Final fallback to old import
        from langchain.chat_models import ChatOpenAI

# Re-export
__all__ = ['ChatOpenAI']
'''
        with open("langchain_chat_compat.py", "w") as f:
            f.write(compat_code)
        print("   ✅ Created langchain_chat_compat.py")
    
    # Step 2: Run the comprehensive fix
    if os.path.exists("fix_all_issues.py"):
        run_command("fix_all_issues.py", "Running comprehensive fixes")
    else:
        # Run individual fixes
        if os.path.exists("fix_datetime_format.py"):
            run_command("fix_datetime_format.py", "Fixing datetime formats")
        
        if os.path.exists("fix_imports.py"):
            run_command("fix_imports.py", "Fixing imports")
    
    # Step 3: Test Azure Search
    print("\n🔍 Testing Azure Search connection...")
    if os.path.exists("test_azure_datetime.py"):
        if not run_command("test_azure_datetime.py", "Testing datetime fixes"):
            print("\n⚠️  Azure Search test failed. Continuing anyway...")
    
    # Step 4: Run diagnostics
    if run_command("diagnose_issues.py", "Running diagnostics"):
        print("\n✅ All systems operational!")
    
    # Step 5: Ask if user wants to start the app
    print("\n" + "="*60)
    response = input("\n🚀 Ready to start the app? (yes/no): ")
    
    if response.lower() in ['yes', 'y']:
        print("\n🌟 Starting Memory Chatbot...")
        print("   Open your browser to: http://localhost:5000")
        print("   Press Ctrl+C to stop\n")
        
        # Start the app
        try:
            subprocess.run([sys.executable, "app.py"])
        except KeyboardInterrupt:
            print("\n\n👋 Shutting down gracefully...")
    else:
        print("\n💡 To start the app later, run: python app.py")

if __name__ == "__main__":
    main()