#!/bin/bash
# setup_context_manager.sh - Automated setup for Context Manager

echo "🚀 Setting up Context-Aware Memory Chatbot"
echo "=========================================="

# Step 1: Check Python version
echo -e "\n1. Checking Python version..."
python_version=$(python3 --version 2>&1)
echo "   $python_version"

# Step 2: Update dependencies
echo -e "\n2. Installing/updating dependencies..."
pip install -r requirements.txt --upgrade

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    echo "   Try: pip install --force-reinstall -r requirements.txt"
    exit 1
fi

# Step 3: Check environment variables
echo -e "\n3. Checking environment variables..."
required_vars=("AZURE_SEARCH_ENDPOINT" "AZURE_SEARCH_API_KEY" "AZURE_INDEX_NAME" "OPENAI_API_KEY")
missing_vars=()

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        missing_vars+=($var)
        echo "   ❌ $var is not set"
    else
        echo "   ✅ $var is set"
    fi
done

if [ ${#missing_vars[@]} -ne 0 ]; then
    echo -e "\n❌ Missing environment variables. Please set them in your .env file:"
    for var in "${missing_vars[@]}"; do
        echo "   $var="
    done
    exit 1
fi

# Step 4: Create conversation history index
echo -e "\n4. Creating conversation history index..."
python3 create_conversation_index.py

if [ $? -ne 0 ]; then
    echo "❌ Failed to create conversation index"
    echo "   Check your Azure Search credentials"
    exit 1
fi

# Step 5: Test imports
echo -e "\n5. Testing Python imports..."
python3 -c "
try:
    import context_manager
    print('   ✅ context_manager imported')
except Exception as e:
    print(f'   ❌ context_manager import failed: {e}')
    exit(1)

try:
    import conversation_tracker
    print('   ✅ conversation_tracker imported')
except Exception as e:
    print(f'   ❌ conversation_tracker import failed: {e}')
    exit(1)

try:
    from graph_setup import graph
    print('   ✅ graph_setup imported')
except Exception as e:
    print(f'   ❌ graph_setup import failed: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ Import tests failed"
    exit 1
fi

# Step 6: Create required files if missing
echo -e "\n6. Checking required files..."
required_files=("context_manager.py" "conversation_tracker.py" "graph_setup.py" "app.py")

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✅ $file exists"
    else
        echo "   ❌ $file is missing"
        exit 1
    fi
done

# Step 7: Final summary
echo -e "\n✅ Setup completed successfully!"
echo -e "\n📋 Next steps:"
echo "1. Run the application: python app.py"
echo "2. Test the context features: python test_context_manager.py"
echo "3. Check the debug endpoints listed when the app starts"
echo -e "\n🎉 Your chatbot now has intelligent context awareness!"
echo ""
echo "Key improvements:"
echo "- Won't repeat information already shared"
echo "- Understands conversation context"
echo "- Tracks what you've discussed"
echo "- Learns your preferences"
echo "- Provides truly new updates only"