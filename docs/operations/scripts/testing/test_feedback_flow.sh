#!/bin/bash

echo "🧪 Testing Complete Feedback & Evaluation Flow"
echo "=============================================="
echo ""

# Step 1: Check frontend is running
echo "1️⃣  Checking frontend status..."
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3001)
if [ "$FRONTEND_STATUS" = "200" ]; then
    echo "   ✅ Frontend is running (http://localhost:3001)"
else
    echo "   ❌ Frontend not responding (status: $FRONTEND_STATUS)"
    exit 1
fi

# Step 2: Check backend is running
echo ""
echo "2️⃣  Checking backend status..."
BACKEND_STATUS=$(curl -s http://localhost:8000/health | jq -r '.status')
if [ "$BACKEND_STATUS" = "healthy" ]; then
    echo "   ✅ Backend is healthy"
else
    echo "   ❌ Backend not healthy"
    exit 1
fi

# Step 3: Check evaluation endpoints
echo ""
echo "3️⃣  Testing evaluation endpoints..."
RESULTS_COUNT=$(curl -s "http://localhost:8000/api/v1/evaluation/results?session_id=test_eval_15df6855&limit=5" | jq 'length')
FEEDBACK_COUNT=$(curl -s "http://localhost:8000/api/v1/evaluation/feedback?session_id=test_eval_15df6855&limit=5" | jq 'length')

echo "   ✅ Evaluation results: $RESULTS_COUNT entries"
echo "   ✅ Human feedback: $FEEDBACK_COUNT entries"

# Step 4: Show testing instructions
echo ""
echo "4️⃣  Testing Instructions:"
echo "   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "   📱 IN YOUR BROWSER:"
echo "   ─────────────────"
echo "   1. Open: http://localhost:3001"
echo "   2. Press Ctrl+Shift+R (or Cmd+Shift+R on Mac) for hard refresh"
echo "   3. Go to the 'Chat' tab"
echo "   4. Send any test query (e.g., 'What is AI?')"
echo "   5. After response appears, look for:"
echo "      • 'Helpful?' with 👍 👎 buttons below the response"
echo "      • 'Rate:' with ⭐⭐⭐⭐⭐ stars"
echo "   6. Hover over buttons - cursor should change to pointer"
echo "   7. Click a button - you should see a green checkmark confirmation"
echo ""
echo "   🔍 DEBUGGING (if buttons don't work):"
echo "   ────────────────────────────────────"
echo "   1. Press F12 to open browser console"
echo "   2. Go to 'Console' tab"
echo "   3. Look for any red error messages"
echo "   4. Click a button and watch for network requests in 'Network' tab"
echo "   5. Check if you see POST to /api/v1/evaluation/feedback"
echo ""
echo "   📊 VIEW EVALUATION DASHBOARD:"
echo "   ────────────────────────────"
echo "   1. Click 'Evaluation' tab in sidebar"
echo "   2. You should see 50 evaluation results with metrics"
echo "   3. Charts showing score distributions"
echo "   4. 20 feedback entries with thumbs up/down counts"
echo ""
echo "   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Step 5: Monitor backend logs for auto-evaluation
echo "5️⃣  Monitoring backend for auto-evaluation..."
echo "   (This will show the last 20 lines of backend logs)"
echo ""
docker-compose logs --tail=20 backend | grep -E "Auto-evaluation|evaluation|quality_metrics" || echo "   No auto-evaluation logs found yet (try sending a chat query)"

echo ""
echo "✅ Setup verification complete!"
echo ""
