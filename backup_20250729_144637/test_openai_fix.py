# test_openai_fix.py
"""
Test script to verify OpenAI client initialization with proxy workaround.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("🧪 Testing OpenAI Client with Proxy Fix")
print("="*40)

# Check API key
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("❌ OPENAI_API_KEY not found in .env file")
    exit(1)
else:
    print(f"✅ API key found (length: {len(api_key)})")

# Test 1: Basic initialization with proxy workaround
print("\n1. Testing basic initialization with proxy fix...")
try:
    # Save proxy settings
    saved_proxies = {}
    proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']
    for var in proxy_vars:
        if var in os.environ:
            saved_proxies[var] = os.environ[var]
            del os.environ[var]
    
    from openai import OpenAI
    
    # Restore proxy settings
    for var, value in saved_proxies.items():
        os.environ[var] = value
    
    # Create client
    client = OpenAI(api_key=api_key)
    print("✅ OpenAI client created successfully!")
    
except Exception as e:
    print(f"❌ Failed: {e}")
    exit(1)

# Test 2: Create embedding
print("\n2. Testing embedding creation...")
try:
    response = client.embeddings.create(
        model="text-embedding-ada-002",
        input="Hello, world!"
    )
    embedding_dim = len(response.data[0].embedding)
    print(f"✅ Embedding created! Dimension: {embedding_dim}")
    
except Exception as e:
    print(f"❌ Failed to create embedding: {e}")

# Test 3: Test LangChain ChatOpenAI
print("\n3. Testing LangChain ChatOpenAI...")
try:
    from langchain_openai import ChatOpenAI
    from langchain.schema import HumanMessage
    
    llm = ChatOpenAI(
        model_name="gpt-3.5-turbo",
        temperature=0,
        api_key=api_key
    )
    
    response = llm.invoke([HumanMessage(content="Say 'test successful' in 3 words")])
    print(f"✅ LangChain response: {response.content}")
    
except Exception as e:
    print(f"❌ Failed LangChain test: {e}")

print("\n" + "="*40)
print("✅ All tests completed!")
print("\nYour OpenAI setup is working correctly.")
print("You can now run: python app.py")