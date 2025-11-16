#!/usr/bin/env python3
"""
Comprehensive test script for document upload and RAG pipeline.

This script tests:
1. File upload to MinIO
2. Document chunking and embedding to vector store
3. RAG query using the uploaded document

Run with: python test_upload_pipeline.py
"""

import asyncio
import sys
import time
import uuid
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.database import Document, DocumentChunk
from app.models.database_enhanced import ChatSession, SessionDocument
from app.services.document_service import document_service
from app.services.embedding_service import embedding_service
from app.services.rag_service_enhanced import enhanced_rag_service


async def test_pipeline():
    """Test the complete upload and RAG pipeline"""

    print("=" * 80)
    print("TESTING DOCUMENT UPLOAD AND RAG PIPELINE")
    print("=" * 80)

    # Initialize database connection
    print("\n1. Initializing database connection...")
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session_maker = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_maker() as db:
        # Initialize services
        print("\n2. Initializing services...")
        await document_service.initialize()
        await embedding_service.initialize()
        print("   ✅ Services initialized")

        # Create test document content
        test_content = """
        Enterprise RAG System Test Document

        This is a test document for validating the RAG pipeline.

        Key Features:
        - Document upload and processing
        - Text chunking with overlap
        - Semantic embeddings using sentence-transformers
        - Vector similarity search with pgvector
        - Multi-model LLM support (OpenAI, Claude, Ollama)
        - Session-based memory hierarchy

        The system uses a two-tier memory approach:
        1. Short-term memory: Documents associated with specific sessions
        2. Long-term memory: All documents in the vector store

        This ensures recently uploaded documents are prioritized for queries
        within their session context.
        """

        # Save test document to temporary file
        test_file = Path("/tmp/test_rag_doc.txt")
        test_file.write_text(test_content)
        print(f"\n3. Created test document: {test_file}")
        print(f"   Content length: {len(test_content)} characters")

        # Generate session ID
        session_id = f"test-session-{uuid.uuid4().hex[:8]}"
        print(f"\n4. Generated test session ID: {session_id}")

        # Upload document
        print("\n5. Uploading document to MinIO and database...")
        file_data = test_file.read_bytes()
        document = await document_service.upload_file(
            file_data=file_data,
            filename="test_rag_doc.txt",
            file_type="text/plain",
            source_type="upload",
            db=db
        )
        await db.commit()
        print(f"   ✅ Document uploaded: ID={document.id}")
        print(f"   ✅ Filename: {document.filename}")
        print(f"   ✅ File size: {document.file_size} bytes")
        print(f"   ✅ MinIO path: {document.file_path}")

        # Verify MinIO storage
        print("\n6. Verifying MinIO storage...")
        try:
            obj = document_service.minio_client.get_object(
                settings.MINIO_BUCKET_NAME,
                document.file_path
            )
            minio_data = obj.read()
            obj.close()
            obj.release_conn()
            assert len(minio_data) == document.file_size
            print(f"   ✅ File exists in MinIO: {len(minio_data)} bytes")
        except Exception as e:
            print(f"   ❌ MinIO verification failed: {e}")
            return False

        # Process document (chunking and embedding)
        print("\n7. Processing document (chunking and embedding)...")
        start_time = time.time()
        chunks = await document_service.process_document(document.id, db)
        await db.commit()
        processing_time = time.time() - start_time
        print(f"   ✅ Processing completed in {processing_time:.2f}s")
        print(f"   ✅ Created {len(chunks)} chunks")

        # Verify chunks in database
        print("\n8. Verifying chunks in database...")
        chunk_query = select(DocumentChunk).where(
            DocumentChunk.document_id == document.id
        )
        result = await db.execute(chunk_query)
        db_chunks = result.scalars().all()
        print(f"   ✅ Found {len(db_chunks)} chunks in database")

        # Check embeddings
        chunks_with_embeddings = sum(1 for chunk in db_chunks if chunk.embedding is not None)
        print(f"   ✅ Chunks with embeddings: {chunks_with_embeddings}/{len(db_chunks)}")

        if chunks_with_embeddings == 0:
            print("   ❌ ERROR: No embeddings generated!")
            return False

        # Show sample chunk
        if db_chunks:
            sample_chunk = db_chunks[0]
            print(f"\n   Sample chunk:")
            print(f"   - Content length: {len(sample_chunk.content)} chars")
            print(f"   - Content preview: {sample_chunk.content[:100]}...")
            if sample_chunk.embedding:
                print(f"   - Embedding dimension: {len(sample_chunk.embedding)}")

        # Associate with session
        print(f"\n9. Associating document with session {session_id}...")
        await enhanced_rag_service.associate_document_with_session(
            session_id=session_id,
            document_id=document.id,
            priority=1,
            db=db
        )
        print(f"   ✅ Document associated with session")

        # Verify session association
        session_query = select(ChatSession).where(
            ChatSession.session_id == session_id
        )
        session_result = await db.execute(session_query)
        session = session_result.scalar_one_or_none()

        if session:
            assoc_query = select(SessionDocument).where(
                SessionDocument.session_id == session.id,
                SessionDocument.document_id == document.id
            )
            assoc_result = await db.execute(assoc_query)
            association = assoc_result.scalar_one_or_none()
            if association:
                print(f"   ✅ Session association verified")
            else:
                print(f"   ❌ Session association not found!")
                return False
        else:
            print(f"   ❌ Session not found!")
            return False

        # Test RAG query
        print("\n10. Testing RAG query...")
        test_queries = [
            "What are the key features of the RAG system?",
            "How does the memory hierarchy work?",
            "What models are supported?"
        ]

        for i, query in enumerate(test_queries, 1):
            print(f"\n    Query {i}: {query}")
            start_time = time.time()

            try:
                result = await enhanced_rag_service.query(
                    query_text=query,
                    session_id=session_id,
                    user_id=None,
                    use_cache=False,
                    db=db
                )
                query_time = time.time() - start_time

                print(f"    ✅ Query completed in {query_time:.2f}s")
                print(f"    ✅ Model used: {result.get('model_name', result.get('model'))}")
                print(f"    ✅ Tokens: {result.get('tokens_used', 0)}")
                print(f"    ✅ Sources found: {result.get('num_sources', 0)}")

                # Check if our test document was used
                sources = result.get('sources', [])
                test_doc_used = any(
                    s.get('id') == str(document.id) or s.get('filename') == 'test_rag_doc.txt'
                    for s in sources
                )

                if test_doc_used:
                    print(f"    ✅ Test document WAS used in response!")
                    # Find the source
                    for source in sources:
                        if source.get('id') == str(document.id) or source.get('filename') == 'test_rag_doc.txt':
                            print(f"       - Memory type: {source.get('memory_type', 'unknown')}")
                            print(f"       - Relevance: {source.get('relevance', 0):.3f}")
                            print(f"       - Excerpt: {source.get('excerpt', '')[:100]}...")
                else:
                    print(f"    ❌ Test document NOT used in response")
                    print(f"       Sources: {[s.get('filename') for s in sources]}")

                # Show answer preview
                answer = result.get('answer', '')
                print(f"\n    Answer preview:")
                print(f"    {answer[:200]}...")

            except Exception as e:
                print(f"    ❌ Query failed: {e}")
                import traceback
                traceback.print_exc()
                return False

        # Cleanup
        print("\n11. Cleaning up test data...")
        await db.delete(document)  # Cascades to chunks and session associations
        await db.commit()
        test_file.unlink()
        print("   ✅ Cleanup completed")

        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED!")
        print("=" * 80)

        return True


if __name__ == "__main__":
    print("\nStarting comprehensive RAG pipeline test...\n")

    try:
        success = asyncio.run(test_pipeline())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
