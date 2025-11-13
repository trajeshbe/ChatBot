#!/bin/bash

set -e

echo "================================================"
echo "Enterprise RAG Chatbot - Quick Start"
echo "================================================"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Error: docker-compose is not installed. Please install it and try again."
    exit 1
fi

echo "✅ Docker is running"
echo ""

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from .env.example..."
    cp .env.example .env
    echo "✅ .env file created. Please update it with your API keys if needed."
    echo ""
fi

# Pull images
echo "📦 Pulling required Docker images..."
docker-compose pull

# Build custom images
echo "🔨 Building custom images..."
docker-compose build

# Start services
echo "🚀 Starting services..."
docker-compose up -d

# Wait for services to be healthy
echo ""
echo "⏳ Waiting for services to be ready (this may take 2-3 minutes)..."
echo ""

for i in {1..60}; do
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Backend is ready!"
        break
    fi
    if [ $i -eq 60 ]; then
        echo "⚠️  Backend is taking longer than expected. Check logs with: docker-compose logs backend"
    fi
    sleep 3
    echo -n "."
done

echo ""
echo ""
echo "================================================"
echo "✅ Enterprise RAG Chatbot is running!"
echo "================================================"
echo ""
echo "Access the application:"
echo "  🌐 Frontend:          http://localhost:3001"
echo "  🔧 Backend API:       http://localhost:8000"
echo "  📚 API Docs:          http://localhost:8000/api/docs"
echo "  🎨 GraphQL:           http://localhost:8000/graphql"
echo "  📊 Grafana:           http://localhost:3000 (admin/admin)"
echo "  📦 MinIO Console:     http://localhost:9001 (minioadmin/minioadmin)"
echo "  🔍 Redis Insight:     http://localhost:8001"
echo "  🌊 Prefect UI:        http://localhost:4200"
echo ""
echo "Useful commands:"
echo "  📋 View logs:         docker-compose logs -f"
echo "  🛑 Stop services:     docker-compose down"
echo "  🔄 Restart services:  docker-compose restart"
echo "  🧹 Clean up:          docker-compose down -v"
echo ""
echo "For more information, see README.md"
echo "================================================"
