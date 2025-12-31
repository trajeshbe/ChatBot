#!/bin/bash

###############################################################################
# Run Consolidation Tests in Docker Container
###############################################################################

set -e

echo "======================================================================"
echo "🧪 RUNNING SERVICE CONSOLIDATION TESTS IN DOCKER"
echo "======================================================================"
echo ""

# Check if backend container is running
if ! docker-compose ps | grep -q "backend.*Up"; then
    echo "⚠️  Backend container is not running. Starting it..."
    docker-compose up -d backend
    echo "Waiting for backend to be ready..."
    sleep 10
fi

echo "✅ Backend container is running"
echo ""

# Run test script inside Docker container
echo "📦 Executing tests inside backend container..."
echo ""

docker-compose exec -T backend bash -c "cd /app && bash test_consolidation_full.sh"

exit_code=$?

echo ""
if [ $exit_code -eq 0 ]; then
    echo "✅ All tests passed successfully!"
else
    echo "❌ Some tests failed. Check output above."
fi

exit $exit_code
