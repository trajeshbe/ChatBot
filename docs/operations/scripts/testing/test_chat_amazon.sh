#!/bin/bash

echo "🧪 Testing Chat Interface - Amazon.com Access"
echo "=============================================="
echo ""

# Start monitoring logs in background
echo "📋 Starting log monitoring..."
docker-compose logs -f backend 2>&1 | grep -iE "amazon|compliance|blocked|scraping" &
LOG_PID=$!

sleep 2

echo ""
echo "💬 Sending query via chat interface asking about amazon.com..."
echo ""

curl -s -X POST http://localhost:8000/api/v1/query \
  -F "query=Can you tell me about products on https://www.amazon.com/?" \
  -F "model_id=gpt-4" \
  -o /tmp/chat_amazon_test.json

echo "✅ Query completed!"
echo ""

# Give logs time to appear
sleep 3

# Stop log monitoring
kill $LOG_PID 2>/dev/null

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 RESPONSE ANALYSIS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if the response contains an answer
if jq -e '.answer' /tmp/chat_amazon_test.json > /dev/null 2>&1; then
    ANSWER=$(jq -r '.answer' /tmp/chat_amazon_test.json)
    
    # Check if answer indicates blocking
    if echo "$ANSWER" | grep -qi "cannot\|unable\|blocked\|not allowed\|compliance"; then
        echo "✅ COMPLIANCE WORKING: Chat correctly refused to scrape amazon.com"
        echo ""
        echo "Answer preview:"
        echo "$ANSWER" | head -c 200
        echo "..."
    else
        echo "⚠️  Response received - checking if it's generic or actually scraped:"
        echo ""
        echo "Answer preview:"
        echo "$ANSWER" | head -c 300
        echo "..."
        echo ""
        
        # Check if sources contain amazon data
        SOURCES_COUNT=$(jq -r '.sources | length' /tmp/chat_amazon_test.json)
        if [ "$SOURCES_COUNT" -gt 0 ]; then
            echo ""
            echo "❌ POTENTIAL ISSUE: Found $SOURCES_COUNT sources - checking if amazon was scraped..."
            jq -r '.sources[0]' /tmp/chat_amazon_test.json | head -20
        else
            echo "✅ No sources returned - likely generic response without scraping"
        fi
    fi
else
    echo "❌ No answer in response"
    echo ""
    echo "Full response:"
    jq '.' /tmp/chat_amazon_test.json
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 CHECKING BACKEND LOGS FOR COMPLIANCE MESSAGES"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker-compose logs backend 2>&1 | grep -iE "amazon|compliance|blocked" | tail -10

