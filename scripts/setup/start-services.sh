#!/bin/bash
# Script to start all services for the RAG Chatbot

set -e

echo "🚀 Starting Enterprise RAG Chatbot Stack..."
echo

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null && ! command -v docker compose &> /dev/null; then
    echo "❌ Error: docker-compose is not installed or not available"
    echo "Please install Docker and Docker Compose first:"
    echo "  - Docker: https://docs.docker.com/get-docker/"
    echo "  - Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found. Creating from .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✅ Created .env file. Please update it with your API keys."
        echo "   Especially: OPENAI_API_KEY"
    else
        echo "❌ Error: .env.example not found"
        exit 1
    fi
fi

# Start services
echo "📦 Starting Docker containers..."
if command -v docker-compose &> /dev/null; then
    docker-compose up -d
else
    docker compose up -d
fi

echo
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check service status
echo
echo "📊 Service Status:"
if command -v docker-compose &> /dev/null; then
    docker-compose ps
else
    docker compose ps
fi

echo
echo "✅ Services started successfully!"
echo
echo "🌐 Access points:"
echo "  - Frontend:        http://localhost:3001"
echo "  - Backend API:     http://localhost:8000"
echo "  - API Docs:        http://localhost:8000/api/docs"
echo "  - GraphQL:         http://localhost:8000/graphql"
echo "  - Grafana:         http://localhost:3000 (admin/admin)"
echo "  - MinIO Console:   http://localhost:9001 (minioadmin/minioadmin)"
echo "  - Prefect UI:      http://localhost:4200"
echo "  - Redis Insight:   http://localhost:8002"
echo
echo "📝 To check logs: docker-compose logs -f [service-name]"
echo "📝 To stop: docker-compose down"
echo "📝 To check database: ./check-db-direct.sh"
