#!/bin/bash

# Quick fix script for embedding dimension mismatch
# This resolves the issue where database expects 1536-dim but app uses 384-dim embeddings

echo "=============================================="
echo "  Embedding Dimension Fix"
echo "=============================================="
echo ""
echo "Problem: Database schema expects 1536-dimensional embeddings (OpenAI)"
echo "         But app uses 384-dimensional embeddings (sentence-transformers)"
echo ""
echo "Solution: Update database schema to vector(384)"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MIGRATION_FILE="$SCRIPT_DIR/backend/migrations/002_fix_embedding_dimensions.sql"

echo -e "${YELLOW}⚠  WARNING: This will delete any existing embeddings!${NC}"
echo "   Documents will need to be re-uploaded to generate chunks."
echo ""
read -p "Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

echo ""
echo "Checking PostgreSQL connection..."
if ! docker exec rag-postgres psql -U postgres -c "SELECT 1;" > /dev/null 2>&1; then
    echo -e "${RED}✗ Cannot connect to PostgreSQL${NC}"
    echo "  Make sure PostgreSQL is running: docker compose up -d postgres"
    exit 1
fi
echo -e "${GREEN}✓ PostgreSQL connected${NC}"

echo ""
echo "Applying dimension fix migration..."
if [ ! -f "$MIGRATION_FILE" ]; then
    echo -e "${RED}✗ Migration file not found: $MIGRATION_FILE${NC}"
    exit 1
fi

docker exec -i rag-postgres psql -U postgres -d ragchatbot < "$MIGRATION_FILE" 2>&1

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ Embedding dimensions fixed successfully!${NC}"
    echo ""
    echo "Verification:"
    docker exec rag-postgres psql -U postgres -d ragchatbot -c \
        "SELECT column_name, data_type FROM information_schema.columns WHERE table_name='document_chunks' AND column_name='embedding';"

    echo ""
    echo "Next steps:"
    echo "  1. Restart backend to clear any cached data:"
    echo "     docker compose restart backend"
    echo ""
    echo "  2. Re-upload your documents - they will now be chunked properly!"
    echo ""
    echo "  3. Verify chunks are created:"
    echo "     ./diagnose-documents.sh"
    echo ""
else
    echo -e "${RED}✗ Migration failed${NC}"
    echo "Check the error messages above for details."
    exit 1
fi
