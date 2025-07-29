# install_dependencies.py
"""
Smart dependency installation script that handles version conflicts.
"""

import subprocess
import sys
import os

def run_pip_command(command):
    """Run a pip command and return success status."""
    try:
        subprocess.check_call([sys.executable, "-m", "pip"] + command.split())
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        return False

def install_dependencies():
    """Install dependencies in the correct order to avoid conflicts."""
    print("🚀 Smart Dependency Installation")
    print("="*60)
    
    # First, upgrade pip
    print("\n📦 Upgrading pip...")
    run_pip_command("install --upgrade pip")
    
    # Core dependencies that rarely have conflicts
    print("\n📦 Installing core dependencies...")
    core_deps = [
        "flask==3.0.3",
        "python-dotenv==1.0.1",
        "requests==2.32.3",
        "beautifulsoup4==4.12.3",
        "urllib3==2.2.2",
        "pytz==2024.1",
        "lxml==5.2.2",
        "numpy==1.26.4",
        "tenacity==8.5.0",
        "dataclasses-json==0.6.3"
    ]
    
    for dep in core_deps:
        print(f"   Installing {dep}...")
        if not run_pip_command(f"install {dep}"):
            print(f"   ⚠️  Failed to install {dep}, continuing...")
    
    # Azure dependencies
    print("\n📦 Installing Azure dependencies...")
    azure_deps = [
        "azure-core==1.30.2",
        "azure-identity==1.16.1",
        "azure-search-documents==11.4.0"
    ]
    
    for dep in azure_deps:
        print(f"   Installing {dep}...")
        if not run_pip_command(f"install {dep}"):
            print(f"   ⚠️  Failed to install {dep}, continuing...")
    
    # OpenAI and related
    print("\n📦 Installing OpenAI...")
    run_pip_command("install openai==1.40.0")
    run_pip_command("install tiktoken==0.7.0")
    run_pip_command("install pydantic==2.8.2")
    run_pip_command("install httpx==0.27.0")
    run_pip_command("install httpcore==1.0.5")
    
    # LangChain - install in specific order
    print("\n📦 Installing LangChain components (this may take a while)...")
    
    # First, uninstall any existing langchain packages to avoid conflicts
    print("   Cleaning up existing installations...")
    for pkg in ["langchain", "langchain-core", "langchain-openai", "langchain-community", "langgraph"]:
        subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", pkg], 
                      capture_output=True, text=True)
    
    # Install langchain-core first with specific version
    print("   Installing langchain-core...")
    if not run_pip_command("install langchain-core==0.2.40"):
        print("   Trying alternative version...")
        run_pip_command("install langchain-core==0.2.27")
    
    # Then install the rest
    print("   Installing langchain packages...")
    langchain_deps = [
        "langchain==0.2.16",
        "langchain-openai==0.1.25",
        "langchain-community==0.2.16",
        "langgraph==0.2.16"
    ]
    
    for dep in langchain_deps:
        print(f"   Installing {dep}...")
        if not run_pip_command(f"install {dep}"):
            print(f"   ⚠️  Failed to install {dep}")
    
    # Verify critical imports
    print("\n🔍 Verifying installations...")
    critical_imports = [
        ("flask", "Flask"),
        ("openai", "OpenAI"),
        ("langchain", "LangChain"),
        ("langgraph", "LangGraph"),
        ("azure.search.documents", "Azure Search"),
        ("conversation_tracker", "Conversation Tracker (local)")
    ]
    
    all_good = True
    for module, name in critical_imports:
        try:
            if module == "conversation_tracker":
                # Skip local module check
                continue
            __import__(module)
            print(f"   ✅ {name}")
        except ImportError as e:
            print(f"   ❌ {name}: {e}")
            all_good = False
    
    print("\n" + "="*60)
    if all_good:
        print("✅ All dependencies installed successfully!")
        print("\n🎯 Next steps:")
        print("   1. Run: python diagnose_issues.py")
        print("   2. Run: python fix_azure_search_data.py")
        print("   3. Run: python app.py")
    else:
        print("⚠️  Some dependencies failed to install.")
        print("\n🔧 Try these fixes:")
        print("   1. Create a fresh virtual environment:")
        print("      python -m venv .venv_new")
        print("      source .venv_new/bin/activate  # On Windows: .venv_new\\Scripts\\activate")
        print("   2. Run this script again")
        print("\n   OR manually install with compatible versions:")
        print("      pip install langchain==0.2.16 langchain-core==0.2.40 langgraph==0.2.16")

if __name__ == "__main__":
    install_dependencies()