#!/bin/bash
# Fix sales.csv in agent workspace volume
# This ensures the file persists across container restarts

echo "🔧 Fixing sales.csv in agent workspace..."

# Get volume path
VOLUME_PATH=$(docker volume inspect chatbot_agent_workspace --format '{{.Mountpoint}}')

if [ -z "$VOLUME_PATH" ]; then
    echo "❌ Error: Could not find agent_workspace volume"
    echo "Creating volume..."
    docker volume create chatbot_agent_workspace
    VOLUME_PATH=$(docker volume inspect chatbot_agent_workspace --format '{{.Mountpoint}}')
fi

echo "📁 Volume path: $VOLUME_PATH"

# Create sales.csv
echo "📝 Creating sales.csv..."
cat > /tmp/sales.csv << 'EOF'
date,product,category,quantity,unit_price,revenue,region
2024-01-01,Widget A,Electronics,100,15.00,1500.00,North
2024-01-01,Widget B,Electronics,50,20.00,1000.00,South
2024-01-02,Widget A,Electronics,75,15.00,1125.00,East
2024-01-02,Widget C,Furniture,30,50.00,1500.00,West
2024-01-03,Widget B,Electronics,80,20.00,1600.00,North
2024-01-03,Widget D,Furniture,25,60.00,1500.00,South
2024-01-04,Widget A,Electronics,120,15.00,1800.00,East
2024-01-04,Widget C,Furniture,40,50.00,2000.00,West
2024-01-05,Widget B,Electronics,90,20.00,1800.00,North
2024-01-05,Widget D,Furniture,35,60.00,2100.00,South
EOF

# Copy to volume
echo "📂 Copying to volume..."
sudo cp /tmp/sales.csv $VOLUME_PATH/sales.csv

# Set permissions (UID 1000 is default container user)
echo "🔐 Setting permissions..."
sudo chown 1000:1000 $VOLUME_PATH/sales.csv
sudo chmod 644 $VOLUME_PATH/sales.csv

# Verify
echo "✅ File copied to volume"
echo ""
echo "📁 Volume contents:"
sudo ls -lah $VOLUME_PATH/

# Wait for container
echo ""
echo "⏳ Waiting for container to be ready..."
sleep 3

# Verify from container
echo ""
echo "🐳 Verifying from container:"
if docker exec rag-agent-runtime ls -lah /workspace/ 2>/dev/null; then
    echo ""
    echo "📄 Checking if file is readable:"
    if docker exec rag-agent-runtime cat /workspace/sales.csv | head -3; then
        echo ""
        echo "✅✅✅ SUCCESS! File is accessible from container ✅✅✅"
    else
        echo "⚠️  File exists but cannot be read (permission issue)"
    fi
else
    echo "⚠️  Container is restarting, file will be available when it starts"
    echo "Run this command to verify later:"
    echo "  docker exec rag-agent-runtime ls -lah /workspace/"
fi

echo ""
echo "================================================================"
echo "✅ Fix complete!"
echo "================================================================"
echo ""
echo "Next steps:"
echo "1. Go to http://localhost:3001"
echo "2. Click 'Agent Tasks' in the sidebar"
echo "3. Create a new task with description:"
echo "   'List all files in /workspace and show the first 5 lines of sales.csv'"
echo ""
echo "Or test with:"
echo "   'Analyze the sales data in /workspace/sales.csv and summarize total revenue by region'"
echo ""
