#!/usr/bin/env python3
"""
Diagnostic script to check session-document associations and embeddings
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy import select, text as sql_text, func
from app.core.database import get_async_session_maker
from app.models.database import Document, DocumentChunk
from app.models.database_enhanced import ChatSession, SessionDocument


async def diagnose_session(session_id_str: str):
    """Diagnose a specific session's document associations"""
    print(f"\n{'='*80}")
    print(f"DIAGNOSTIC REPORT FOR SESSION: {session_id_str}")
    print(f"{'='*80}\n")

    async_session_maker = get_async_session_maker()
    async with async_session_maker() as db:
        try:
            # 1. Check if session exists
            print("1. Checking if session exists in chat_sessions table...")
            session_query = select(ChatSession).where(ChatSession.session_id == session_id_str)
            session_result = await db.execute(session_query)
            session = session_result.scalar_one_or_none()

            if not session:
                print(f"   ❌ Session NOT FOUND: {session_id_str}")
                print(f"   This is the problem! The session was not created properly.")
                return

            print(f"   ✅ Session found:")
            print(f"      - UUID: {session.id}")
            print(f"      - Session ID (string): {session.session_id}")
            print(f"      - Created: {session.created_at}")
            print(f"      - User ID: {session.user_id}")

            # 2. Check session documents
            print(f"\n2. Checking session_documents associations...")
            sd_query = select(SessionDocument).where(SessionDocument.session_id == session.id)
            sd_result = await db.execute(sd_query)
            session_docs = sd_result.scalars().all()

            if not session_docs:
                print(f"   ❌ NO documents associated with this session!")
                print(f"   This is the problem! Documents were not linked to the session.")
                return

            print(f"   ✅ Found {len(session_docs)} document(s) associated with session:")
            for sd in session_docs:
                print(f"      - Document ID: {sd.document_id}")
                print(f"      - Priority: {sd.priority}")
                print(f"      - Added at: {sd.added_at}")

            # 3. Check documents
            print(f"\n3. Checking document details...")
            for sd in session_docs:
                doc_query = select(Document).where(Document.id == sd.document_id)
                doc_result = await db.execute(doc_query)
                doc = doc_result.scalar_one_or_none()

                if not doc:
                    print(f"   ❌ Document {sd.document_id} NOT FOUND!")
                    continue

                print(f"   📄 Document: {doc.filename}")
                print(f"      - ID: {doc.id}")
                print(f"      - Processed: {doc.processed}")
                print(f"      - Size: {doc.file_size} bytes")

                # Check chunks
                chunk_query = select(DocumentChunk).where(DocumentChunk.document_id == doc.id)
                chunk_result = await db.execute(chunk_query)
                chunks = chunk_result.scalars().all()

                print(f"      - Chunks: {len(chunks)}")

                if not chunks:
                    print(f"      ❌ NO CHUNKS found for this document!")
                    continue

                # Check embeddings
                chunks_with_embeddings = sum(1 for c in chunks if c.embedding is not None)
                print(f"      - Chunks with embeddings: {chunks_with_embeddings}/{len(chunks)}")

                if chunks_with_embeddings == 0:
                    print(f"      ❌ NO EMBEDDINGS found!")
                elif chunks_with_embeddings < len(chunks):
                    print(f"      ⚠️  Some chunks missing embeddings!")
                else:
                    print(f"      ✅ All chunks have embeddings")

                    # Check embedding dimensions
                    first_chunk = chunks[0]
                    if first_chunk.embedding:
                        print(f"      - Embedding dimensions: {len(first_chunk.embedding)}")

            # 4. Test the actual query that's failing
            print(f"\n4. Testing the session document search query...")

            # Generate a test embedding (all zeros for testing)
            test_embedding = [0.0] * 384
            embedding_str = f"[{','.join(map(str, test_embedding))}]"

            test_query = sql_text(f"""
                SELECT
                    dc.id,
                    dc.document_id,
                    d.filename,
                    sd.priority,
                    1 - (dc.embedding <=> '{embedding_str}'::vector) as similarity
                FROM document_chunks dc
                JOIN documents d ON dc.document_id = d.id
                JOIN session_documents sd ON d.id = sd.document_id
                WHERE sd.session_id = :session_id
                ORDER BY sd.priority DESC, dc.embedding <=> '{embedding_str}'::vector
                LIMIT 5
            """)

            test_result = await db.execute(test_query, {"session_id": session.id})
            test_rows = test_result.fetchall()

            if not test_rows:
                print(f"   ❌ Query returned NO results!")
                print(f"   This confirms the issue - the JOIN is not working correctly.")

                # Debug the JOIN
                print(f"\n5. Debugging the JOIN...")

                # Check if document_chunks exist
                chunk_count_query = select(func.count()).select_from(DocumentChunk)
                chunk_count_result = await db.execute(chunk_count_query)
                total_chunks = chunk_count_result.scalar()
                print(f"   - Total chunks in database: {total_chunks}")

                # Check chunks for session documents
                for sd in session_docs:
                    chunk_query = select(func.count()).select_from(DocumentChunk).where(
                        DocumentChunk.document_id == sd.document_id
                    )
                    chunk_result = await db.execute(chunk_query)
                    doc_chunks = chunk_result.scalar()
                    print(f"   - Chunks for document {sd.document_id}: {doc_chunks}")
            else:
                print(f"   ✅ Query returned {len(test_rows)} result(s):")
                for row in test_rows[:3]:
                    print(f"      - Chunk {row.id}: {row.filename} (similarity: {row.similarity:.4f})")

            print(f"\n{'='*80}")
            print("DIAGNOSIS COMPLETE")
            print(f"{'='*80}\n")

        except Exception as e:
            print(f"\n❌ ERROR during diagnosis: {e}")
            import traceback
            traceback.print_exc()


async def main():
    if len(sys.argv) < 2:
        print("Usage: python diagnose_session_documents.py <session_id>")
        print("\nExample:")
        print("  python diagnose_session_documents.py test-session-1763116752")
        sys.exit(1)

    session_id = sys.argv[1]
    await diagnose_session(session_id)


if __name__ == "__main__":
    asyncio.run(main())
