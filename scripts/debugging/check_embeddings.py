#!/usr/bin/env python3
"""
Diagnostic script to check embedding status in the database
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy import create_engine, text
from app.core.config import settings

def check_embeddings():
    """Check the status of embeddings in the database"""

    # Create database engine
    engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)

    print("=" * 60)
    print("EMBEDDING DIAGNOSTIC REPORT")
    print("=" * 60)
    print()

    with engine.connect() as conn:
        # Check total documents
        result = conn.execute(text("SELECT COUNT(*) as count FROM documents"))
        doc_count = result.fetchone()[0]
        print(f"📄 Total documents: {doc_count}")

        # Check total chunks
        result = conn.execute(text("SELECT COUNT(*) as count FROM document_chunks"))
        chunk_count = result.fetchone()[0]
        print(f"🧩 Total chunks: {chunk_count}")

        # Check chunks with embeddings
        result = conn.execute(text("""
            SELECT
                COUNT(*) as total,
                COUNT(embedding) as with_embedding,
                COUNT(*) FILTER (WHERE embedding IS NULL) as without_embedding
            FROM document_chunks
        """))
        row = result.fetchone()
        print(f"✅ Chunks with embeddings: {row[1]}")
        print(f"❌ Chunks without embeddings: {row[2]}")
        print()

        # If no embeddings, check what's wrong
        if row[1] == 0 and chunk_count > 0:
            print("⚠️  WARNING: Chunks exist but have NO embeddings!")
            print()
            print("Checking chunk details...")
            result = conn.execute(text("""
                SELECT dc.id, dc.document_id, d.filename, dc.chunk_index,
                       LENGTH(dc.content) as content_length,
                       dc.embedding IS NULL as missing_embedding
                FROM document_chunks dc
                JOIN documents d ON dc.document_id = d.id
                LIMIT 5
            """))

            print("\nFirst 5 chunks:")
            for row in result:
                print(f"  - {row[2]} (chunk {row[3]}): {row[4]} chars, embedding={'MISSING' if row[5] else 'OK'}")

        # Check documents with processing errors
        print()
        print("Checking for processing errors...")
        result = conn.execute(text("""
            SELECT filename, processing_error
            FROM documents
            WHERE processing_error IS NOT NULL
            LIMIT 5
        """))

        errors = list(result)
        if errors:
            print(f"❌ Found {len(errors)} documents with processing errors:")
            for row in errors:
                print(f"  - {row[0]}: {row[1][:100]}")
        else:
            print("✅ No processing errors found")

        # Check session documents
        print()
        result = conn.execute(text("SELECT COUNT(*) FROM session_documents"))
        session_doc_count = result.fetchone()[0]
        print(f"🔗 Session documents: {session_doc_count}")

        # Check if pgvector extension is installed
        print()
        print("Checking pgvector extension...")
        result = conn.execute(text("""
            SELECT extname, extversion
            FROM pg_extension
            WHERE extname = 'vector'
        """))
        row = result.fetchone()
        if row:
            print(f"✅ pgvector extension installed: version {row[1]}")
        else:
            print("❌ pgvector extension NOT installed!")

        # Check vector index
        print()
        print("Checking vector indexes...")
        result = conn.execute(text("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE tablename = 'document_chunks'
            AND indexdef LIKE '%embedding%'
        """))

        indexes = list(result)
        if indexes:
            print(f"✅ Found {len(indexes)} vector index(es):")
            for row in indexes:
                print(f"  - {row[0]}")
        else:
            print("⚠️  No vector indexes found on document_chunks.embedding")

        # Sample a chunk to check embedding dimensions
        if chunk_count > 0:
            print()
            print("Checking embedding dimensions...")
            result = conn.execute(text("""
                SELECT array_length(embedding::float[], 1) as dimensions
                FROM document_chunks
                WHERE embedding IS NOT NULL
                LIMIT 1
            """))
            row = result.fetchone()
            if row and row[0]:
                print(f"✅ Embedding dimensions: {row[0]}")
                if row[0] != 384:
                    print(f"⚠️  WARNING: Expected 384 dimensions, but found {row[0]}")
            else:
                print("❌ Could not determine embedding dimensions")

    print()
    print("=" * 60)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    try:
        check_embeddings()
    except Exception as e:
        print(f"❌ Error running diagnostics: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
