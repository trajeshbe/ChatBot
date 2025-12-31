#!/usr/bin/env python3
"""
Script to diagnose document chunking issues.
Checks if documents are being chunked and embedded properly.
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import select, func
from app.core.database import AsyncSessionLocal
from app.models.database import Document, DocumentChunk


async def diagnose():
    print("=" * 50)
    print("  Document Chunking Diagnostics")
    print("=" * 50)
    print()

    async with AsyncSessionLocal() as db:
        try:
            # Check total documents
            doc_count_query = select(func.count()).select_from(Document)
            doc_result = await db.execute(doc_count_query)
            doc_count = doc_result.scalar()
            print(f"✓ Total documents in database: {doc_count}")

            # Check total chunks
            chunk_count_query = select(func.count()).select_from(DocumentChunk)
            chunk_result = await db.execute(chunk_count_query)
            chunk_count = chunk_result.scalar()
            print(f"✓ Total chunks in database: {chunk_count}")

            # Check chunks with embeddings
            embedding_count_query = select(func.count()).select_from(DocumentChunk).where(
                DocumentChunk.embedding.isnot(None)
            )
            embedding_result = await db.execute(embedding_count_query)
            embedding_count = embedding_result.scalar()
            print(f"✓ Chunks with embeddings: {embedding_count}")

            print()
            print("-" * 50)
            print("  Documents and Their Chunks")
            print("-" * 50)
            print()

            # Get documents with chunk counts
            query = select(
                Document.id,
                Document.filename,
                Document.processed,
                Document.processing_error,
                func.count(DocumentChunk.id).label('chunk_count')
            ).outerjoin(
                DocumentChunk, Document.id == DocumentChunk.document_id
            ).group_by(
                Document.id
            ).order_by(
                Document.upload_date.desc()
            ).limit(10)

            result = await db.execute(query)
            rows = result.all()

            if not rows:
                print("⚠️  No documents found in database!")
            else:
                for row in rows:
                    status = "✓" if row.processed else "✗"
                    error = f" ERROR: {row.processing_error}" if row.processing_error else ""
                    print(f"{status} {row.filename}")
                    print(f"   ID: {row.id}")
                    print(f"   Processed: {row.processed}")
                    print(f"   Chunks: {row.chunk_count}{error}")
                    print()

            print()
            print("-" * 50)
            print("  Diagnosis")
            print("-" * 50)
            print()

            if doc_count == 0:
                print("❌ No documents found in database")
                print("   → Upload some documents first")
            elif chunk_count == 0:
                print("❌ Documents exist but NO CHUNKS created!")
                print("   → This is the problem!")
                print()
                print("Possible causes:")
                print("  1. process_document() is not being called after upload")
                print("  2. process_document() is failing with errors")
                print("  3. Database transaction is not being committed")
                print("  4. Embedding service is not working")
                print()
                print("Next steps:")
                print("  1. Check backend logs: docker compose logs backend --tail=50")
                print("  2. Look for processing errors in the logs")
                print("  3. Try uploading a new document and watch the logs")
            elif embedding_count == 0:
                print("❌ Chunks exist but NO EMBEDDINGS generated!")
                print("   → Embedding service is not working")
            elif chunk_count < doc_count:
                print("⚠️  Some documents have no chunks")
                print(f"   → {doc_count} documents but only {chunk_count} chunks")
                print("   → Check processing_error column above")
            else:
                print("✅ Documents are being chunked and embedded properly!")
                print(f"   → {doc_count} documents, {chunk_count} chunks, {embedding_count} embeddings")

        except Exception as e:
            print(f"❌ Error during diagnosis: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(diagnose())
