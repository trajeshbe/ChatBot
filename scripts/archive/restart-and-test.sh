#!/bin/bash

echo "=============================================="
echo "  Restart Backend & Test"
echo "=============================================="
echo ""

echo "Step 1: Rebuilding backend with fix..."
docker compose up -d --build backend

echo ""
echo "Step 2: Waiting for backend to start (15 seconds)..."
sleep 15

echo ""
echo "Step 3: Checking backend health..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend is healthy!"
    echo ""
    curl -s http://localhost:8000/health | jq '.'
else
    echo "❌ Backend not responding yet. Waiting 10 more seconds..."
    sleep 10
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Backend is now healthy!"
        curl -s http://localhost:8000/health | jq '.'
    else
        echo "❌ Backend still not responding. Check logs:"
        echo "   docker compose logs backend --tail=50"
        exit 1
    fi
fi

echo ""
echo "Step 4: Testing enhanced features..."
FEATURES=$(curl -s http://localhost:8000/health | jq -r '.features')
echo "$FEATURES" | jq '.'

if echo "$FEATURES" | grep -q '"enhanced_rag":true'; then
    echo "✅ Enhanced RAG with memory hierarchy is ACTIVE"
else
    echo "⚠️  Enhanced RAG is not active (will use basic RAG)"
fi

if echo "$FEATURES" | grep -q '"audit_logging":true'; then
    echo "✅ Audit logging is ACTIVE"
else
    echo "⚠️  Audit logging is not active"
fi

echo ""
echo "Step 5: Validating all services..."
./validate-services.sh

echo ""
echo "=============================================="
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Access admin dashboard: http://localhost:3001/admin"
echo "  2. Test upload with session: See QUICKSTART.md"
echo "  3. View audit logs in admin dashboard"
echo ""
