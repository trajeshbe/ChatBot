#!/bin/bash

echo "=============================================="
echo "  Document Flow Testing"
echo "=============================================="
echo ""

# Check if documents exist
echo "1. Checking documents in database..."
DOC_COUNT=$(docker exec rag-postgres psql -U postgres -d ragchatbot -t -c "SELECT COUNT(*) FROM documents;" 2>/dev/null | tr -d ' ')
echo "   Total documents: ${DOC_COUNT:-0}"

if [ "${DOC_COUNT:-0}" -gt 0 ]; then
    echo ""
    echo "2. Recent documents:"
    docker exec rag-postgres psql -U postgres -d ragchatbot -c "
        SELECT filename, processed, upload_date, processing_error
        FROM documents
        ORDER BY upload_date DESC
        LIMIT 5;
    "
    
    echo ""
    echo "3. Document chunks (embeddings):"
    docker exec rag-postgres psql -U postgres -d ragchatbot -c "
        SELECT d.filename, COUNT(dc.id) as chunk_count,
               CASE WHEN COUNT(dc.id) > 0 THEN 'Yes' ELSE 'No' END as has_chunks
        FROM documents d
        LEFT JOIN document_chunks dc ON d.id = dc.document_id
        GROUP BY d.filename
        ORDER BY d.upload_date DESC
        LIMIT 5;
    "
    
    echo ""
    echo "4. Checking if embeddings exist:"
    EMBEDDINGS=$(docker exec rag-postgres psql -U postgres -d ragchatbot -t -c "
        SELECT COUNT(*) FROM document_chunks WHERE embedding IS NOT NULL;
    " 2>/dev/null | tr -d ' ')
    echo "   Chunks with embeddings: ${EMBEDDINGS:-0}"
    
    if [ "${EMBEDDINGS:-0}" -eq 0 ]; then
        echo ""
        echo "   ⚠️  WARNING: Documents uploaded but NO embeddings created!"
        echo "   This means documents won't be found in queries."
        echo ""
        echo "   Checking backend logs for errors..."
        docker compose logs backend --tail=50 | grep -i "embed\|process\|error" | tail -20
    fi
else
    echo "   No documents found in database."
    echo ""
    echo "   To test, upload a document:"
    echo "   curl -X POST http://localhost:8000/api/v1/upload -F 'file=@test.pdf'"
fi

echo ""
echo "5. Testing embedding service..."
curl -s http://localhost:8000/health | jq -r '.status' > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "   ✓ Backend is accessible"
else
    echo "   ✗ Backend not accessible"
fi

echo ""
echo "=============================================="
