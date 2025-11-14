#!/bin/bash

echo "=============================================="
echo "  Document Processing Diagnostic Tool"
echo "=============================================="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Checking Documents in Database ===${NC}"

# Check documents table
echo -e "\n${YELLOW}Documents uploaded:${NC}"
docker exec rag-postgres psql -U postgres -d rag_chatbot -c \
"SELECT id, filename, file_type, source_type, processed, upload_date, processing_error
FROM documents
ORDER BY upload_date DESC
LIMIT 10;" 2>/dev/null || echo "Error querying documents table"

# Count total documents
doc_count=$(docker exec rag-postgres psql -U postgres -d rag_chatbot -t -c \
"SELECT COUNT(*) FROM documents;" 2>/dev/null | tr -d ' ' || echo "0")
doc_count=${doc_count:-0}
echo -e "\n${GREEN}Total documents: $doc_count${NC}"

# Count processed documents
processed_count=$(docker exec rag-postgres psql -U postgres -d rag_chatbot -t -c \
"SELECT COUNT(*) FROM documents WHERE processed = true;" 2>/dev/null | tr -d ' ' || echo "0")
processed_count=${processed_count:-0}
echo -e "${GREEN}Processed documents: $processed_count${NC}"

# Count failed documents
failed_count=$(docker exec rag-postgres psql -U postgres -d rag_chatbot -t -c \
"SELECT COUNT(*) FROM documents WHERE processing_error IS NOT NULL;" 2>/dev/null | tr -d ' ' || echo "0")
failed_count=${failed_count:-0}
if [ "$failed_count" -gt 0 ]; then
    echo -e "${RED}Failed documents: $failed_count${NC}"
    echo -e "\n${RED}Processing errors:${NC}"
    docker exec rag-postgres psql -U postgres -d rag_chatbot -c \
    "SELECT filename, processing_error FROM documents WHERE processing_error IS NOT NULL;" 2>/dev/null
fi

echo -e "\n${BLUE}=== Checking Document Chunks (Embeddings) ===${NC}"

# Count chunks
chunk_count=$(docker exec rag-postgres psql -U postgres -d rag_chatbot -t -c \
"SELECT COUNT(*) FROM document_chunks;" 2>/dev/null | tr -d ' ' || echo "0")
chunk_count=${chunk_count:-0}
echo -e "${GREEN}Total chunks: $chunk_count${NC}"

if [ "$chunk_count" -gt 0 ]; then
    echo -e "\n${YELLOW}Sample chunks:${NC}"
    docker exec rag-postgres psql -U postgres -d rag_chatbot -c \
    "SELECT dc.id, d.filename, dc.chunk_index,
     LENGTH(dc.content) as content_length,
     CASE WHEN dc.embedding IS NOT NULL THEN 'Yes' ELSE 'No' END as has_embedding
     FROM document_chunks dc
     JOIN documents d ON dc.document_id = d.id
     ORDER BY dc.created_at DESC
     LIMIT 5;"
fi

echo -e "\n${BLUE}=== Checking MinIO Object Storage ===${NC}"

# List objects in MinIO
echo -e "${YELLOW}Files in MinIO:${NC}"
docker exec rag-minio mc ls minio/documents 2>/dev/null || echo "MinIO bucket not accessible or empty"

echo -e "\n${BLUE}=== Checking Query Cache ===${NC}"

# Count cached queries
cache_count=$(docker exec rag-postgres psql -U postgres -d rag_chatbot -t -c \
"SELECT COUNT(*) FROM query_cache;" 2>/dev/null | tr -d ' ' || echo "0")
cache_count=${cache_count:-0}
echo -e "${GREEN}Cached queries: $cache_count${NC}"

if [ "$cache_count" -gt 0 ]; then
    echo -e "\n${YELLOW}Recent cached queries:${NC}"
    docker exec rag-postgres psql -U postgres -d rag_chatbot -c \
    "SELECT LEFT(query_text, 60) as query, hit_count, created_at
     FROM query_cache
     ORDER BY created_at DESC
     LIMIT 5;"
fi

echo -e "\n${BLUE}=== Checking Backend Logs for Errors ===${NC}"
echo -e "${YELLOW}Recent processing logs:${NC}"
docker compose logs backend --tail=50 2>/dev/null | grep -i "process\|upload\|chunk\|embed" | tail -20

echo -e "\n${YELLOW}Recent errors:${NC}"
docker compose logs backend --tail=100 2>/dev/null | grep -i "error\|exception\|failed" | tail -10

echo ""
echo "=============================================="
echo -e "${BLUE}Diagnostic Summary:${NC}"
echo "  Documents uploaded: $doc_count"
echo "  Documents processed: $processed_count"
echo "  Document chunks (embeddings): $chunk_count"
echo "  Cached queries: $cache_count"

if [ "$chunk_count" -eq 0 ] && [ "$doc_count" -gt 0 ]; then
    echo ""
    echo -e "${RED}⚠️  WARNING: Documents uploaded but no chunks created!${NC}"
    echo -e "${YELLOW}This means documents are NOT being processed into embeddings.${NC}"
    echo ""
    echo "Possible causes:"
    echo "  1. Document processing is failing (check errors above)"
    echo "  2. pgvector extension not installed"
    echo "  3. Embedding service not working"
    echo ""
    echo "Troubleshooting steps:"
    echo "  1. Check backend logs: docker compose logs backend | grep -i error"
    echo "  2. Verify pgvector: docker exec rag-postgres psql -U postgres -d rag_chatbot -c 'CREATE EXTENSION IF NOT EXISTS vector;'"
    echo "  3. Test embedding service: curl http://localhost:8000/api/v1/models/"
elif [ "$chunk_count" -gt 0 ]; then
    echo ""
    echo -e "${GREEN}✅ Document processing appears to be working!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Try a query: Ask a question about your uploaded documents"
    echo "  2. Check if RAG is working: Look for 'sources' in the response"
    echo "  3. If still not working, check similarity threshold in .env (SIMILARITY_THRESHOLD)"
fi

echo ""
