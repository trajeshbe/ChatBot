#!/usr/bin/env python3
"""
Direct Test Script for Aadhan Query
Bypasses the agent layer and directly tests document_service.search_similar_chunks()
"""

import asyncio
import sys
from sentence_transformers import SentenceTransformer

# Add backend to path
sys.path.insert(0, 'backend')

from app.services.document_service import document_service
from app.core.database import AsyncSessionLocal
from app.core.config import settings


async def test_aadhan_direct_search():
    """Test direct search for 'Who is Aadhan?' bypassing all agent/classification layers"""

    print("=" * 80)
    print("DIRECT AADHAN SEARCH TEST")
    print("=" * 80)

    query = "Who is Aadhan?"
    print(f"\n📝 Query: {query}")

    # Generate embedding directly
    print("\n🔧 Loading embedding model...")
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

    print("🔧 Generating query embedding...")
    query_embedding = model.encode(query).tolist()
    print(f"✅ Embedding generated: {len(query_embedding)} dimensions")

    async with AsyncSessionLocal() as db:
        print("\n" + "=" * 80)
        print("TEST 1: Pure Semantic Search (No Hybrid)")
        print("=" * 80)

        chunks = await document_service.search_similar_chunks(
            query_embedding=query_embedding,
            query_text=None,  # No keyword search
            top_k=10,
            threshold=0.35,
            use_hybrid=False,
            use_cascading_fallback=False,
            db=db
        )

        print(f"\n📊 Results: {len(chunks)} chunks found")
        if chunks:
            for i, chunk in enumerate(chunks, 1):
                print(f"\n  [{i}] File: {chunk['filename']}")
                print(f"      Score: {chunk['similarity']:.4f}")
                print(f"      Content: {chunk['content'][:100]}...")
        else:
            print("  ❌ No chunks found with pure semantic search")

        print("\n" + "=" * 80)
        print("TEST 2: Hybrid Search (60/40 weights - OLD)")
        print("=" * 80)

        chunks = await document_service.search_similar_chunks(
            query_embedding=query_embedding,
            query_text=query,  # Enable keyword search
            top_k=10,
            threshold=0.35,
            use_hybrid=True,
            use_cascading_fallback=False,
            semantic_weight=0.6,
            keyword_weight=0.4,
            db=db
        )

        print(f"\n📊 Results: {len(chunks)} chunks found")
        if chunks:
            for i, chunk in enumerate(chunks, 1):
                print(f"\n  [{i}] File: {chunk['filename']}")
                print(f"      Combined Score: {chunk['similarity']:.4f}")
                print(f"      Semantic: {chunk.get('semantic_score', 0):.4f}")
                print(f"      Keyword: {chunk.get('keyword_score', 0):.4f}")
                print(f"      Content: {chunk['content'][:100]}...")
        else:
            print("  ❌ No chunks found with 60/40 hybrid search")

        print("\n" + "=" * 80)
        print("TEST 3: Hybrid Search (80/20 weights - NEW)")
        print("=" * 80)

        chunks = await document_service.search_similar_chunks(
            query_embedding=query_embedding,
            query_text=query,  # Enable keyword search
            top_k=10,
            threshold=0.35,
            use_hybrid=True,
            use_cascading_fallback=False,
            semantic_weight=0.8,
            keyword_weight=0.2,
            db=db
        )

        print(f"\n📊 Results: {len(chunks)} chunks found")
        if chunks:
            for i, chunk in enumerate(chunks, 1):
                print(f"\n  [{i}] File: {chunk['filename']}")
                print(f"      Combined Score: {chunk['similarity']:.4f}")
                print(f"      Semantic: {chunk.get('semantic_score', 0):.4f}")
                print(f"      Keyword: {chunk.get('keyword_score', 0):.4f}")
                print(f"      Content: {chunk['content'][:100]}...")
        else:
            print("  ❌ No chunks found with 80/20 hybrid search")

        print("\n" + "=" * 80)
        print("TEST 4: Hybrid Search with Cascading Fallback (80/20)")
        print("=" * 80)

        chunks = await document_service.search_similar_chunks(
            query_embedding=query_embedding,
            query_text=query,  # Enable keyword search
            top_k=10,
            threshold=0.50,  # Start with higher threshold
            use_hybrid=True,
            use_cascading_fallback=True,  # Enable cascading
            semantic_weight=0.8,
            keyword_weight=0.2,
            db=db
        )

        print(f"\n📊 Results: {len(chunks)} chunks found")
        if chunks:
            for i, chunk in enumerate(chunks, 1):
                print(f"\n  [{i}] File: {chunk['filename']}")
                print(f"      Combined Score: {chunk['similarity']:.4f}")
                print(f"      Semantic: {chunk.get('semantic_score', 0):.4f}")
                print(f"      Keyword: {chunk.get('keyword_score', 0):.4f}")
                print(f"      Content: {chunk['content'][:100]}...")
        else:
            print("  ❌ No chunks found even with cascading fallback")

        print("\n" + "=" * 80)
        print("TEST 5: Direct SQL Query (Raw Vector Search)")
        print("=" * 80)

        from sqlalchemy import text as sql_text

        embedding_str = f"[{','.join(map(str, query_embedding))}]"

        query_sql = sql_text(f"""
            SELECT
                dc.id,
                d.filename,
                dc.content,
                1 - (dc.embedding <=> '{embedding_str}'::vector) as similarity
            FROM document_chunks dc
            JOIN documents d ON dc.document_id = d.id
            WHERE dc.embedding IS NOT NULL
            ORDER BY dc.embedding <=> '{embedding_str}'::vector
            LIMIT 10
        """)

        result = await db.execute(query_sql)
        rows = result.fetchall()

        print(f"\n📊 Results: {len(rows)} chunks found")
        for i, row in enumerate(rows, 1):
            print(f"\n  [{i}] File: {row.filename}")
            print(f"      Similarity: {row.similarity:.4f}")
            print(f"      Content: {row.content[:100]}...")

        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"✅ Direct SQL query returned {len(rows)} results")
        print(f"⚙️  Current config:")
        print(f"    - SEMANTIC_WEIGHT: {settings.SEMANTIC_WEIGHT}")
        print(f"    - KEYWORD_WEIGHT: {settings.KEYWORD_WEIGHT}")
        print(f"    - SIMILARITY_THRESHOLD: {settings.SIMILARITY_THRESHOLD}")
        print(f"    - MIN_SIMILARITY_THRESHOLD: {settings.MIN_SIMILARITY_THRESHOLD}")
        print(f"    - NO_RELEVANT_DOCS_THRESHOLD: {settings.NO_RELEVANT_DOCS_THRESHOLD}")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_aadhan_direct_search())
