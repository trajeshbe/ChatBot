#!/bin/bash
# Direct database query to check what's actually in the database

echo "Checking PostgreSQL database directly..."
echo

# Database connection from docker-compose
export PGPASSWORD=postgres

# Check documents table
echo "=== Documents Table ==="
psql -h localhost -U postgres -d chatbot -c "SELECT id, filename, processed, processing_error, upload_date FROM documents ORDER BY upload_date DESC LIMIT 5;"
echo

# Check chunks table
echo "=== Document Chunks Table ==="
psql -h localhost -U postgres -d chatbot -c "SELECT COUNT(*) as chunk_count, document_id FROM document_chunks GROUP BY document_id;"
echo

# Check session documents
echo "=== Session Documents ==="
psql -h localhost -U postgres -d chatbot -c "SELECT COUNT(*) FROM session_documents;"
echo

# Check for any processing errors
echo "=== Documents with Processing Errors ==="
psql -h localhost -U postgres -d chatbot -c "SELECT id, filename, processing_error FROM documents WHERE processing_error IS NOT NULL;"
