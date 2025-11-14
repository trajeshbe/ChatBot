#!/bin/bash

echo "=========================================="
echo "  Document Processing Diagnostics"
echo "=========================================="
echo ""

# Check if database exists and tables are created
echo "1. Checking database tables..."
echo "---"

# Check documents table
echo "Documents in database:"
docker exec rag-postgres psql -U postgres -d rag_chatbot -c \
  "SELECT id, filename, created_at, processing_status FROM documents ORDER BY created_at DESC LIMIT 5;" 2>/dev/null

echo ""
echo "Document chunks (embeddings):"
docker exec rag-postgres psql -U postgres -d rag_chatbot -c \
  "SELECT d.filename, COUNT(dc.id) as chunk_count
   FROM documents d
   LEFT JOIN document_chunks dc ON d.id = dc.document_id
   GROUP BY d.id, d.filename
   ORDER BY d.created_at DESC LIMIT 5;" 2>/dev/null

echo ""
echo "Session documents (short-term memory):"
docker exec rag-postgres psql -U postgres -d rag_chatbot -c \
  "SELECT cs.session_id, d.filename, sd.priority, sd.added_at
   FROM session_documents sd
   JOIN documents d ON sd.document_id = d.id
   JOIN chat_sessions cs ON sd.session_id = cs.id
   ORDER BY sd.added_at DESC LIMIT 5;" 2>/dev/null

echo ""
echo "---"
echo "2. Checking MinIO files..."
docker exec rag-minio mc ls myminio/documents/ 2>/dev/null | tail -5

echo ""
echo "---"
echo "3. Checking backend logs for errors..."
docker compose logs backend --tail=50 | grep -i "error\|exception\|fail" | tail -10

echo ""
echo "---"
echo "4. Checking if enhanced RAG is loaded..."
docker compose logs backend | grep -i "enhanced rag" | tail -3

echo ""
echo "=========================================="
echo "  Diagnostic Summary"
echo "=========================================="
echo ""

# Count documents
doc_count=$(docker exec rag-postgres psql -U postgres -d rag_chatbot -t -c \
  "SELECT COUNT(*) FROM documents;" 2>/dev/null | tr -d ' ')

chunk_count=$(docker exec rag-postgres psql -U postgres -d rag_chatbot -t -c \
  "SELECT COUNT(*) FROM document_chunks;" 2>/dev/null | tr -d ' ')

session_doc_count=$(docker exec rag-postgres psql -U postgres -d rag_chatbot -t -c \
  "SELECT COUNT(*) FROM session_documents;" 2>/dev/null | tr -d ' ')

echo "Total documents: ${doc_count:-0}"
echo "Total chunks (embeddings): ${chunk_count:-0}"
echo "Documents in sessions: ${session_doc_count:-0}"
echo ""

if [ "${chunk_count:-0}" -eq 0 ] && [ "${doc_count:-0}" -gt 0 ]; then
  echo "⚠️  WARNING: Documents exist but NO CHUNKS found!"
  echo "    This means documents are not being processed (chunked & embedded)."
  echo ""
  echo "Possible causes:"
  echo "  1. document_service.process_document() is failing"
  echo "  2. Embedding service is not working"
  echo "  3. Database migration for document_chunks table not run"
  echo ""
fi

if [ "${session_doc_count:-0}" -eq 0 ] && [ "${doc_count:-0}" -gt 0 ]; then
  echo "⚠️  WARNING: Documents exist but NOT linked to sessions!"
  echo "    This means documents won't be found in short-term memory."
  echo ""
  echo "Possible causes:"
  echo "  1. session_id not being passed during upload"
  echo "  2. session_documents table doesn't exist"
  echo "  3. Enhanced RAG service not loaded"
  echo ""
fi

if [ "${chunk_count:-0}" -gt 0 ] && [ "${session_doc_count:-0}" -gt 0 ]; then
  echo "✅ Documents are being processed and linked to sessions!"
  echo ""
  echo "If queries still don't work, check:"
  echo "  1. Is session_id being passed in queries?"
  echo "  2. Are embeddings being generated correctly?"
  echo "  3. Check backend logs for query errors"
fi

echo ""
echo "To view detailed logs:"
echo "  docker compose logs backend --tail=100"
echo ""
