#!/bin/bash
# clean_install.sh - Clean install to fix all dependency and proxy issues

echo "🔧 Clean Install for Memory Chatbot"
echo "==================================="

# Step 1: Clean up old packages
echo "1. Cleaning up old packages..."
pip uninstall -y openai langchain langchain-openai langchain-community httpx httpcore

# Step 2: Clear pip cache
echo -e "\n2. Clearing pip cache..."
pip cache purge

# Step 3: Install packages in correct order
echo -e "\n3. Installing packages in correct order..."

# Install httpx and httpcore first
pip install httpx==0.27.0 httpcore==1.0.5

# Install OpenAI
pip install openai==1.40.0

# Install LangChain packages
pip install langchain==0.3.0 langchain-openai==0.2.2 langchain-community==0.3.0 langgraph==0.2.16

# Install remaining packages
pip install flask==3.0.3 python-dotenv==1.0.1 requests==2.32.3 beautifulsoup4==4.12.3
pip install urllib3==2.2.2 pytz==2024.1 lxml==5.2.2
pip install azure-search-documents==11.4.0 azure-identity==1.16.1 azure-core==1.30.2
pip install tiktoken==0.7.0 pydantic==2.8.2 numpy==1.26.4 tenacity==8.5.0

# Step 4: Verify installation
echo -e "\n4. Verifying installation..."
python3 -c "
import sys
print('Python:', sys.version)
try:
    import openai
    print(f'✅ OpenAI: {openai.__version__}')
except Exception as e:
    print(f'❌ OpenAI: {e}')

try:
    import langchain
    print(f'✅ LangChain: {langchain.__version__}')
except Exception as e:
    print(f'❌ LangChain: {e}')

try:
    import httpx
    print(f'✅ httpx: {httpx.__version__}')
except Exception as e:
    print(f'❌ httpx: {e}')
"

echo -e "\n✅ Installation complete!"
echo "Now use the memory_manager.py with proxy fix"
echo "Run: python app.py"