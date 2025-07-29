# Enhanced Memory Chatbot Testing Guide

## 🚀 Setup Commands

```bash
# Navigate to project directory
cd chat_memory_bot

# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install any new dependencies
pip install -r requirements.txt

# Start the enhanced application
python app.py
```

## 🧪 Testing Scenarios

### Test 1: Smart Deduplication (Weather)
**Purpose**: Verify the system doesn't re-search when recent content exists

1. **First ask**: "What's the weather in London today?"
   - **Expected**: Web search triggered, fresh data retrieved
   - **Terminal should show**: `🔍 Web search triggered`

2. **Wait 30 seconds, then ask**: "How's the weather in London right now?"
   - **Expected**: No web search (content is fresh)
   - **Terminal should show**: `✋ No web search needed - using existing knowledge`
   - **Response should still include current weather data**

### Test 2: Query Type Intelligence
**Purpose**: Test different freshness requirements

1. **Ask**: "What's the current stock price of Apple?"
   - **Expected**: Web search (stock data expires quickly)
   - **Terminal**: `🏷️ Query type: stock`

2. **Ask**: "Tell me about machine learning"
   - **Expected**: No web search (general knowledge)
   - **Terminal**: `🏷️ Query type: general`

3. **Ask**: "What are the latest news about climate change?"
   - **Expected**: Web search (news expires in 6 hours)
   - **Terminal**: `🏷️ Query type: news`

### Test 3: Enhanced Decision Making
**Purpose**: Verify intelligent search decisions

1. **Ask**: "What's the traffic like on Highway 101?"
   - **Expected**: Web search (traffic changes very quickly)
   - **Terminal**: `🏷️ Query type: traffic`

2. **Ask the same question again within 30 minutes**
   - **Expected**: Might still search (traffic freshness = 1 hour)

### Test 4: Memory + Web Integration
**Purpose**: Test contextual intelligence with mixed sources

1. **Say**: "My favorite team is Barcelona"
2. **Ask**: "How did my favorite team perform in their last match?"
   - **Expected**: 
     - Remember "Barcelona" from conversation
     - Search for recent Barcelona match results
     - Combine both in response

### Test 5: Query Optimization
**Purpose**: Verify improved search queries

1. **Ask**: "Can you please tell me what the weather is like in Tokyo today?"
   - **Expected optimized query**: "weather Tokyo today"
   - **Terminal should show optimized query**

## 🔍 Debug Endpoints

### Decision Analysis
```
http://localhost:5000/debug/decision?query=weather%20in%20Paris
```
**Shows**: 
- Query type categorization
- Search decision reasoning
- Memory analysis

### Memory Analysis
```
http://localhost:5000/debug/memories?query=your%20test%20query
```
**Shows**:
- Retrieved memories with scores
- Memory type breakdown
- Formatted prompt preview

### Health Check
```
http://localhost:5000/health
```
**Shows**:
- All service configurations
- Component status

## 📊 Expected Improvements

### Terminal Output Should Show:
```
🏷️  Query type: weather
🤔 Making intelligent search decision...
🎯 Decision: Current weather data needed - existing content is 3 hours old
🔍 Web search triggered with optimized query: 'weather Paris today'
📊 Existing web items: 2, Fresh: 0
✨ Response enhanced with fresh web data
```

### Response Quality Indicators:
- **More specific data**: Exact temperatures, times, details
- **Source awareness**: "Based on current information..." 
- **Efficiency**: Faster responses when using cached data
- **Context**: Better integration of personal preferences + web data

## 🐛 Troubleshooting

### If no web search triggers:
1. Check BING_SEARCH_KEY in .env
2. Use `/debug/decision` endpoint to see reasoning
3. Try explicit queries like "current weather" or "latest news"

### If responses seem generic:
1. Check `/debug/memories` to see if web content is stored
2. Verify scraped content isn't empty
3. Look for "🌐 Web content integrated" in terminal

### If getting old information:
1. Check query type classification in terminal
2. Verify timestamp parsing works
3. Use different query types to test freshness logic

## ✅ Success Criteria

**The enhanced system is working when**:
- ✅ Avoids redundant searches for fresh content
- ✅ Triggers searches for stale content automatically  
- ✅ Shows intelligent query type detection
- ✅ Provides more specific, current information
- ✅ Integrates personal context with web data seamlessly
- ✅ Shows clear decision reasoning in debug endpoints