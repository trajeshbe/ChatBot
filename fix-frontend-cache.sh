#!/bin/bash
# Fix Next.js webpack cache issues in Docker

echo "🔧 Fixing frontend webpack cache issues..."

# Stop frontend container
echo "Stopping frontend container..."
docker compose stop frontend

# Remove the .next volume
echo "Removing .next cache volume..."
docker compose rm -f frontend

# Remove any orphaned volumes
echo "Cleaning up volumes..."
docker volume ls -q -f dangling=true | xargs -r docker volume rm

# Rebuild and restart frontend
echo "Rebuilding frontend container..."
docker compose build frontend --no-cache

echo "Starting frontend..."
docker compose up -d frontend

echo ""
echo "✅ Frontend cache cleared and restarted!"
echo "Monitor logs with: docker compose logs -f frontend"
echo ""
echo "The webpack cache warnings should be gone now."
