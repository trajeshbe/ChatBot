#!/usr/bin/env python3
"""
Debug script to test session document retrieval
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, '/home/user/ChatBot/backend')

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, text as sql_text, func
from app.models.database_enhanced import ChatSession, SessionDocument
from app.models.database import Document, DocumentChunk

DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/ragchatbot"

async def main():
    # Create engine
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        # Find most recent test session
        print("=" * 60)
        print("Finding recent test sessions...")
        print("=" * 60)

        sessions_query = select(ChatSession).where(
            ChatSession.session_id.like('test-session-%')
        ).order_by(ChatSession.created_at.desc()).limit(5)

        sessions_result = await db.execute(sessions_query)
        sessions = sessions_result.scalars().all()

        if not sessions:
            print("❌ No test sessions found!")
            return

        print(f"✅ Found {len(sessions)} test session(s)\n")

        for session in sessions:
            print(f"Session: {session.session_id}")
            print(f"  ID (UUID): {session.id}")
            print(f"  Created: {session.created_at}")

            # Count documents in this session
            count_query = select(func.count()).select_from(SessionDocument).where(
                SessionDocument.session_id == session.id
            )
            count_result = await db.execute(count_query)
            doc_count = count_result.scalar()

            print(f"  Documents: {doc_count}")

            if doc_count > 0:
                # Get session documents
                doc_query = select(SessionDocument).where(
                    SessionDocument.session_id == session.id
                )
                doc_result = await db.execute(doc_query)
                session_docs = doc_result.scalars().all()

                for sd in session_docs:
                    # Get document details
                    doc_detail_query = select(Document).where(
                        Document.id == sd.document_id
                    )
                    doc_detail_result = await db.execute(doc_detail_query)
                    doc = doc_detail_result.scalar_one_or_none()

                    if doc:
                        print(f"    - {doc.filename} (ID: {doc.id})")
                        print(f"      Priority: {sd.priority}")
                        print(f"      Processed: {doc.processed}")

                        # Count chunks
                        chunk_count_query = select(func.count()).select_from(DocumentChunk).where(
                            DocumentChunk.document_id == doc.id
                        )
                        chunk_count_result = await db.execute(chunk_count_query)
                        chunk_count = chunk_count_result.scalar()
                        print(f"      Chunks: {chunk_count}")

                        # Count chunks with embeddings
                        embed_count_query = select(func.count()).select_from(DocumentChunk).where(
                            DocumentChunk.document_id == doc.id
                        ).where(DocumentChunk.embedding.isnot(None))
                        embed_count_result = await db.execute(embed_count_query)
                        embed_count = embed_count_result.scalar()
                        print(f"      Chunks with embeddings: {embed_count}")

            print()

        # Now test the actual query that the RAG service uses
        test_session = sessions[0]
        print("=" * 60)
        print(f"Testing vector search for session: {test_session.session_id}")
        print("=" * 60)

        # Get a test embedding (just use zeros for now)
        test_embedding = [0.0] * 384
        embedding_str = f"[{','.join(map(str, test_embedding))}]"

        # Run the same query as _search_session_documents
        query = sql_text(f"""
            SELECT
                dc.id,
                dc.document_id,
                dc.content,
                d.filename,
                d.source_type,
                sd.priority,
                1 - (dc.embedding <=> '{embedding_str}'::vector) as similarity
            FROM document_chunks dc
            JOIN documents d ON dc.document_id = d.id
            JOIN session_documents sd ON d.id = sd.document_id
            WHERE sd.session_id = :session_id
                AND dc.embedding IS NOT NULL
            ORDER BY sd.priority DESC, similarity DESC
            LIMIT 10
        """)

        result = await db.execute(query, {"session_id": test_session.id})
        rows = result.fetchall()

        print(f"Query returned {len(rows)} chunks")

        if rows:
            print("\nSample chunks:")
            for i, row in enumerate(rows[:3], 1):
                print(f"\n  Chunk {i}:")
                print(f"    Filename: {row.filename}")
                print(f"    Priority: {row.priority}")
                print(f"    Similarity: {row.similarity:.4f}")
                print(f"    Content preview: {row.content[:100]}...")
        else:
            print("❌ No chunks found!")

            # Debug: check if chunks exist at all
            all_chunks_query = sql_text("""
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN embedding IS NOT NULL THEN 1 ELSE 0 END) as with_embedding
                FROM document_chunks dc
                JOIN documents d ON dc.document_id = d.id
                JOIN session_documents sd ON d.id = sd.document_id
                WHERE sd.session_id = :session_id
            """)
            debug_result = await db.execute(all_chunks_query, {"session_id": test_session.id})
            debug_row = debug_result.first()

            if debug_row:
                print(f"\nDebug info:")
                print(f"  Total chunks for session: {debug_row.total}")
                print(f"  Chunks with embeddings: {debug_row.with_embedding}")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
