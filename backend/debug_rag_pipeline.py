#!/usr/bin/env python3
"""
RAG Pipeline Debug Script
=========================
Comprehensive debugging tool to trace the full flow of the RAG pipeline
and identify issues with embeddings, chunking, thresholds, query classification, etc.

Usage:
    python debug_rag_pipeline.py "your query here" [--session-id SESSION_ID]
    python debug_rag_pipeline.py --analyze-documents
    python debug_rag_pipeline.py --test-embedding "test text"
"""

import sys
import os
import asyncio
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
import argparse
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy import create_engine, text, func
from sqlalchemy.orm import sessionmaker
import numpy as np

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_section(title: str):
    """Print a section header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{title.center(80)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}\n")


def print_subsection(title: str):
    """Print a subsection header"""
    print(f"\n{Colors.OKCYAN}{Colors.BOLD}{'-' * 80}{Colors.ENDC}")
    print(f"{Colors.OKCYAN}{Colors.BOLD}{title}{Colors.ENDC}")
    print(f"{Colors.OKCYAN}{Colors.BOLD}{'-' * 80}{Colors.ENDC}")


def print_success(message: str):
    """Print success message"""
    print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}")


def print_warning(message: str):
    """Print warning message"""
    print(f"{Colors.WARNING}⚠ {message}{Colors.ENDC}")


def print_error(message: str):
    """Print error message"""
    print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")


def print_info(label: str, value: Any, indent: int = 0):
    """Print info with label"""
    indent_str = "  " * indent
    print(f"{indent_str}{Colors.OKBLUE}{label}:{Colors.ENDC} {value}")


class RAGPipelineDebugger:
    """Debug the RAG pipeline end-to-end"""

    def __init__(self):
        self.db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/ragchatbot")
        self.engine = create_engine(self.db_url)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def get_embedding_service(self):
        """Get embedding service instance"""
        try:
            from app.services.embedding_service import EmbeddingService
            return EmbeddingService()
        except Exception as e:
            print_error(f"Failed to import EmbeddingService: {e}")
            return None

    def get_rag_service(self):
        """Get RAG service instance"""
        try:
            from app.services.rag_service import RAGService
            db = self.SessionLocal()
            return RAGService(db)
        except Exception as e:
            print_error(f"Failed to import RAGService: {e}")
            return None

    async def analyze_query_classification(self, query: str):
        """Analyze how the query is being classified"""
        print_section("QUERY CLASSIFICATION ANALYSIS")

        print_info("Query", f'"{query}"')

        # Try to get the query classifier
        try:
            from app.services.rag_service import RAGService
            db = self.SessionLocal()
            rag_service = RAGService(db)

            # Check if should_skip_rag method exists
            if hasattr(rag_service, 'should_skip_rag'):
                should_skip = await rag_service.should_skip_rag(query)
                print_info("Should Skip RAG", should_skip)

                if should_skip:
                    print_warning("Query classified as NON-RETRIEVAL - will not search documents!")
                    print_info("Reason", "Query appears to be a direct AI question")
                else:
                    print_success("Query classified as RETRIEVAL - will search documents")

            # Check if there's a classify_query method
            if hasattr(rag_service, 'classify_query'):
                classification = await rag_service.classify_query(query)
                print_info("Classification Result", json.dumps(classification, indent=2))

            # Check for pattern-based classification
            direct_patterns = [
                "who are you", "what are you", "tell me about yourself",
                "what can you do", "how do you work", "explain yourself"
            ]

            query_lower = query.lower()
            matched_pattern = None
            for pattern in direct_patterns:
                if pattern in query_lower:
                    matched_pattern = pattern
                    break

            if matched_pattern:
                print_warning(f'Query matches direct pattern: "{matched_pattern}"')
                print_info("Impact", "May skip document retrieval entirely")

        except Exception as e:
            print_error(f"Failed to analyze query classification: {e}")
            import traceback
            traceback.print_exc()

    async def analyze_query_embedding(self, query: str):
        """Analyze query embedding generation"""
        print_section("QUERY EMBEDDING ANALYSIS")

        embedding_service = self.get_embedding_service()
        if not embedding_service:
            return None

        try:
            print_info("Generating embedding for query", f'"{query}"')

            # Generate embedding
            start_time = datetime.now()
            embedding = await embedding_service.generate_embedding(query)
            duration = (datetime.now() - start_time).total_seconds()

            print_success(f"Embedding generated in {duration:.3f}s")
            print_info("Embedding dimension", len(embedding))
            print_info("Embedding type", type(embedding).__name__)

            # Show statistics
            embedding_array = np.array(embedding)
            print_info("Embedding stats", "")
            print_info("  Mean", f"{embedding_array.mean():.6f}", indent=1)
            print_info("  Std Dev", f"{embedding_array.std():.6f}", indent=1)
            print_info("  Min", f"{embedding_array.min():.6f}", indent=1)
            print_info("  Max", f"{embedding_array.max():.6f}", indent=1)
            print_info("  Norm (L2)", f"{np.linalg.norm(embedding_array):.6f}", indent=1)

            # Show first 10 values
            print_info("First 10 values", embedding[:10])

            return embedding

        except Exception as e:
            print_error(f"Failed to generate embedding: {e}")
            import traceback
            traceback.print_exc()
            return None

    def analyze_documents(self):
        """Analyze all documents in the database"""
        print_section("DOCUMENT DATABASE ANALYSIS")

        db = self.SessionLocal()
        try:
            # Count total documents
            result = db.execute(text("SELECT COUNT(*) FROM documents"))
            total_docs = result.scalar()
            print_info("Total Documents", total_docs)

            if total_docs == 0:
                print_warning("No documents found in database!")
                return

            # Get document details
            result = db.execute(text("""
                SELECT
                    id,
                    filename,
                    file_type,
                    source_type,
                    source_url,
                    processed,
                    upload_date,
                    processing_error
                FROM documents
                ORDER BY upload_date DESC
            """))

            documents = result.fetchall()

            print_subsection("Document List")
            for i, doc in enumerate(documents, 1):
                print(f"\n{Colors.BOLD}Document {i}:{Colors.ENDC}")
                print_info("  ID", doc[0], indent=1)
                print_info("  Filename", doc[1], indent=1)
                print_info("  Type", doc[2], indent=1)
                print_info("  Source", doc[3], indent=1)
                if doc[4]:
                    print_info("  URL", doc[4], indent=1)
                print_info("  Processed", doc[5], indent=1)
                print_info("  Upload Date", doc[6], indent=1)
                if doc[7]:
                    print_error(f"  Error: {doc[7]}")

                # Get chunk count for this document
                chunk_result = db.execute(
                    text("SELECT COUNT(*) FROM document_chunks WHERE document_id = :doc_id"),
                    {"doc_id": doc[0]}
                )
                chunk_count = chunk_result.scalar()
                print_info("  Chunks", chunk_count, indent=1)

                # Get embedding count
                embedding_result = db.execute(
                    text("SELECT COUNT(*) FROM document_chunks WHERE document_id = :doc_id AND embedding IS NOT NULL"),
                    {"doc_id": doc[0]}
                )
                embedding_count = embedding_result.scalar()
                print_info("  Chunks with Embeddings", embedding_count, indent=1)

                if chunk_count > 0 and embedding_count == 0:
                    print_error("  ⚠ Document has chunks but NO embeddings!")
                elif chunk_count > embedding_count:
                    print_warning(f"  ⚠ {chunk_count - embedding_count} chunks missing embeddings")
                elif chunk_count > 0:
                    print_success("  All chunks have embeddings")

        except Exception as e:
            print_error(f"Failed to analyze documents: {e}")
            import traceback
            traceback.print_exc()
        finally:
            db.close()

    def analyze_chunks(self, limit: int = 5):
        """Analyze document chunks"""
        print_section("DOCUMENT CHUNKS ANALYSIS")

        db = self.SessionLocal()
        try:
            # Get total chunk count
            result = db.execute(text("SELECT COUNT(*) FROM document_chunks"))
            total_chunks = result.scalar()
            print_info("Total Chunks", total_chunks)

            if total_chunks == 0:
                print_warning("No chunks found in database!")
                return

            # Get chunks with embeddings
            result = db.execute(text("SELECT COUNT(*) FROM document_chunks WHERE embedding IS NOT NULL"))
            chunks_with_embeddings = result.scalar()
            print_info("Chunks with Embeddings", chunks_with_embeddings)

            if chunks_with_embeddings < total_chunks:
                print_warning(f"{total_chunks - chunks_with_embeddings} chunks missing embeddings!")

            # Get chunk statistics
            result = db.execute(text("""
                SELECT
                    MIN(LENGTH(content)) as min_length,
                    MAX(LENGTH(content)) as max_length,
                    AVG(LENGTH(content)) as avg_length
                FROM document_chunks
            """))
            stats = result.fetchone()

            print_subsection("Chunk Statistics")
            print_info("Min Length", stats[0])
            print_info("Max Length", stats[1])
            print_info("Avg Length", f"{stats[2]:.2f}")

            # Show sample chunks
            result = db.execute(text(f"""
                SELECT
                    c.id,
                    c.document_id,
                    d.filename,
                    c.chunk_index,
                    LENGTH(c.content) as content_length,
                    SUBSTRING(c.content, 1, 200) as content_preview,
                    CASE WHEN c.embedding IS NOT NULL THEN 'Yes' ELSE 'No' END as has_embedding
                FROM document_chunks c
                JOIN documents d ON c.document_id = d.id
                ORDER BY c.created_at DESC
                LIMIT {limit}
            """))

            chunks = result.fetchall()

            print_subsection(f"Sample Chunks (Latest {limit})")
            for i, chunk in enumerate(chunks, 1):
                print(f"\n{Colors.BOLD}Chunk {i}:{Colors.ENDC}")
                print_info("  Chunk ID", chunk[0], indent=1)
                print_info("  Document", chunk[2], indent=1)
                print_info("  Index", chunk[3], indent=1)
                print_info("  Length", chunk[4], indent=1)
                print_info("  Has Embedding", chunk[6], indent=1)
                print_info("  Preview", f'"{chunk[5]}..."', indent=1)

        except Exception as e:
            print_error(f"Failed to analyze chunks: {e}")
            import traceback
            traceback.print_exc()
        finally:
            db.close()

    async def test_vector_search(self, query: str, query_embedding: List[float], top_k: int = 5):
        """Test vector similarity search"""
        print_section("VECTOR SIMILARITY SEARCH")

        db = self.SessionLocal()
        try:
            print_info("Query", f'"{query}"')
            print_info("Top K", top_k)

            # Convert embedding to string format for PostgreSQL
            embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"

            # Perform vector search
            print_subsection("Searching for similar chunks...")

            sql = text("""
                SELECT
                    c.id,
                    c.document_id,
                    d.filename,
                    c.chunk_index,
                    c.content,
                    1 - (c.embedding <=> :query_embedding::vector) as similarity_score
                FROM document_chunks c
                JOIN documents d ON c.document_id = d.id
                WHERE c.embedding IS NOT NULL
                ORDER BY c.embedding <=> :query_embedding::vector
                LIMIT :top_k
            """)

            result = db.execute(
                sql,
                {
                    "query_embedding": embedding_str,
                    "top_k": top_k
                }
            )

            results = result.fetchall()

            if not results:
                print_warning("No results found! This could indicate:")
                print_warning("  1. No chunks have embeddings")
                print_warning("  2. Vector search is not working")
                print_warning("  3. pgvector extension is not installed")
                return []

            print_success(f"Found {len(results)} results")

            print_subsection("Search Results")
            for i, row in enumerate(results, 1):
                chunk_id, doc_id, filename, chunk_idx, content, score = row

                print(f"\n{Colors.BOLD}Result {i}:{Colors.ENDC}")
                print_info("  Document", filename, indent=1)
                print_info("  Chunk Index", chunk_idx, indent=1)
                print_info("  Similarity Score", f"{float(score):.4f}", indent=1)
                print_info("  Chunk ID", chunk_id, indent=1)

                # Show content preview
                preview = content[:300] + "..." if len(content) > 300 else content
                print_info("  Content", f'"{preview}"', indent=1)

                # Color-code by similarity
                score_float = float(score)
                if score_float > 0.7:
                    print_success(f"  Quality: Excellent match (>{0.7})")
                elif score_float > 0.5:
                    print_info("  Quality", f"Good match (>{0.5})")
                elif score_float > 0.3:
                    print_warning(f"  Quality: Fair match (>{0.3})")
                else:
                    print_error(f"  Quality: Poor match (<{0.3})")

            return results

        except Exception as e:
            print_error(f"Vector search failed: {e}")
            import traceback
            traceback.print_exc()
            return []
        finally:
            db.close()

    def check_session_documents(self, session_id: Optional[str]):
        """Check documents associated with a session"""
        if not session_id:
            print_info("Session ID", "None (will search all documents)")
            return

        print_section("SESSION DOCUMENT ANALYSIS")

        db = self.SessionLocal()
        try:
            print_info("Session ID", session_id)

            # Check if session exists
            result = db.execute(
                text("SELECT COUNT(*) FROM chat_sessions WHERE session_id = :session_id"),
                {"session_id": session_id}
            )
            session_exists = result.scalar() > 0

            if not session_exists:
                print_warning("Session does not exist in chat_sessions table")
                return

            print_success("Session found")

            # Get session documents
            result = db.execute(text("""
                SELECT
                    sd.id,
                    sd.document_id,
                    d.filename,
                    d.file_type,
                    sd.added_at
                FROM session_documents sd
                JOIN documents d ON sd.document_id = d.id
                WHERE sd.session_id = :session_id
                ORDER BY sd.added_at DESC
            """), {"session_id": session_id})

            session_docs = result.fetchall()

            if not session_docs:
                print_warning("No documents associated with this session")
                print_info("Impact", "Will search ALL documents (long-term memory)")
                return

            print_success(f"Found {len(session_docs)} session documents")

            print_subsection("Session Documents")
            for i, doc in enumerate(session_docs, 1):
                print(f"\n{Colors.BOLD}Document {i}:{Colors.ENDC}")
                print_info("  Filename", doc[2], indent=1)
                print_info("  Type", doc[3], indent=1)
                print_info("  Added", doc[4], indent=1)
                print_info("  Document ID", doc[1], indent=1)

        except Exception as e:
            print_error(f"Failed to check session documents: {e}")
            import traceback
            traceback.print_exc()
        finally:
            db.close()

    async def trace_full_pipeline(self, query: str, session_id: Optional[str] = None):
        """Trace the complete RAG pipeline for a query"""
        print_section("FULL RAG PIPELINE TRACE")

        print_info("Query", f'"{query}"')
        print_info("Session ID", session_id or "None")
        print_info("Timestamp", datetime.now().isoformat())

        # Step 1: Query Classification
        await self.analyze_query_classification(query)

        # Step 2: Session Document Check
        self.check_session_documents(session_id)

        # Step 3: Query Embedding
        query_embedding = await self.analyze_query_embedding(query)

        if not query_embedding:
            print_error("Cannot proceed without query embedding")
            return

        # Step 4: Vector Search
        results = await self.test_vector_search(query, query_embedding, top_k=5)

        # Step 5: RAG Service Analysis
        await self.analyze_rag_service_call(query, session_id)

        # Summary
        print_section("DEBUGGING SUMMARY")

        if not results:
            print_error("ISSUE: No search results found")
            print_warning("Possible causes:")
            print_warning("  1. No documents uploaded")
            print_warning("  2. Documents not processed (chunks not created)")
            print_warning("  3. Embeddings not generated for chunks")
            print_warning("  4. pgvector extension issues")
        elif results and float(results[0][5]) < 0.3:
            print_warning("ISSUE: Low similarity scores")
            print_warning("Possible causes:")
            print_warning("  1. Query and documents are semantically different")
            print_warning("  2. Embedding model not suitable for domain")
            print_warning("  3. Documents don't contain relevant information")
        else:
            print_success("Pipeline appears to be working correctly")
            print_info("Best similarity score", f"{float(results[0][5]):.4f}")

    async def analyze_rag_service_call(self, query: str, session_id: Optional[str]):
        """Analyze what the RAG service would actually return"""
        print_section("RAG SERVICE CALL SIMULATION")

        try:
            from app.services.rag_service import RAGService
            from app.schemas.rag import QueryRequest

            db = self.SessionLocal()
            rag_service = RAGService(db)

            # Create query request
            query_request = QueryRequest(
                query=query,
                session_id=session_id,
                model="gpt-4-turbo",
                top_k=5
            )

            print_info("Calling RAG service", "query_with_rag()")
            print_info("Parameters", json.dumps({
                "query": query,
                "session_id": session_id,
                "top_k": 5
            }, indent=2))

            # Call RAG service
            start_time = datetime.now()
            response = await rag_service.query_with_rag(query_request)
            duration = (datetime.now() - start_time).total_seconds()

            print_success(f"RAG service completed in {duration:.3f}s")

            # Analyze response
            print_subsection("Response Analysis")
            print_info("Answer Length", len(response.answer))
            print_info("Number of Sources", len(response.sources))
            print_info("Model Used", response.model_used)

            if hasattr(response, 'tokens'):
                print_info("Tokens Used", response.tokens)

            if response.sources:
                print_subsection("Sources Used")
                for i, source in enumerate(response.sources, 1):
                    print(f"\n{Colors.BOLD}Source {i}:{Colors.ENDC}")
                    print_info("  Document", source.filename, indent=1)
                    print_info("  Score", f"{source.score:.4f}", indent=1)
                    preview = source.content[:200] + "..." if len(source.content) > 200 else source.content
                    print_info("  Content", f'"{preview}"', indent=1)
            else:
                print_warning("No sources returned - likely answered without retrieval")

            # Show answer preview
            print_subsection("Answer Preview")
            answer_preview = response.answer[:500] + "..." if len(response.answer) > 500 else response.answer
            print(f"{answer_preview}\n")

        except Exception as e:
            print_error(f"RAG service call failed: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if 'db' in locals():
                db.close()

    def check_pgvector_installation(self):
        """Check if pgvector extension is properly installed"""
        print_section("PGVECTOR EXTENSION CHECK")

        db = self.SessionLocal()
        try:
            # Check extension
            result = db.execute(text("SELECT * FROM pg_extension WHERE extname = 'vector'"))
            extension = result.fetchone()

            if extension:
                print_success("pgvector extension is installed")
                print_info("Version", extension[1] if len(extension) > 1 else "Unknown")
            else:
                print_error("pgvector extension is NOT installed!")
                print_warning("Install with: CREATE EXTENSION vector;")
                return False

            # Check if we can create vector type
            try:
                result = db.execute(text("SELECT '[1,2,3]'::vector(3)"))
                print_success("Vector type is working")
            except Exception as e:
                print_error(f"Vector type test failed: {e}")
                return False

            # Check indexes
            result = db.execute(text("""
                SELECT indexname, indexdef
                FROM pg_indexes
                WHERE tablename = 'document_chunks'
                AND indexdef LIKE '%vector%'
            """))

            indexes = result.fetchall()
            if indexes:
                print_success(f"Found {len(indexes)} vector index(es)")
                for idx_name, idx_def in indexes:
                    print_info("  Index", idx_name, indent=1)
            else:
                print_warning("No vector indexes found on document_chunks")
                print_info("Recommendation", "Create index for faster searches")

            return True

        except Exception as e:
            print_error(f"pgvector check failed: {e}")
            return False
        finally:
            db.close()


async def main():
    parser = argparse.ArgumentParser(description="Debug RAG Pipeline")
    parser.add_argument("query", nargs="?", help="Query to test")
    parser.add_argument("--session-id", help="Session ID to test")
    parser.add_argument("--analyze-documents", action="store_true", help="Analyze all documents")
    parser.add_argument("--analyze-chunks", action="store_true", help="Analyze document chunks")
    parser.add_argument("--check-pgvector", action="store_true", help="Check pgvector installation")
    parser.add_argument("--test-embedding", help="Test embedding generation for text")
    parser.add_argument("--full-trace", action="store_true", help="Run full pipeline trace")

    args = parser.parse_args()

    debugger = RAGPipelineDebugger()

    # Run requested analyses
    if args.check_pgvector:
        debugger.check_pgvector_installation()

    if args.analyze_documents:
        debugger.analyze_documents()

    if args.analyze_chunks:
        debugger.analyze_chunks()

    if args.test_embedding:
        await debugger.analyze_query_embedding(args.test_embedding)

    if args.query:
        if args.full_trace or not any([args.analyze_documents, args.analyze_chunks, args.check_pgvector]):
            # Default to full trace if query is provided
            await debugger.trace_full_pipeline(args.query, args.session_id)
        else:
            # Just test the query
            print_section("QUERY TEST")
            print_info("Query", f'"{args.query}"')

            # Query classification
            await debugger.analyze_query_classification(args.query)

            # Generate embedding
            embedding = await debugger.analyze_query_embedding(args.query)

            # Search
            if embedding:
                await debugger.test_vector_search(args.query, embedding)

    if not any([args.query, args.analyze_documents, args.analyze_chunks, args.check_pgvector, args.test_embedding]):
        parser.print_help()
        print("\n" + Colors.BOLD + "Examples:" + Colors.ENDC)
        print('  python debug_rag_pipeline.py "what is the revenue of TCS?"')
        print('  python debug_rag_pipeline.py "your query" --session-id abc123')
        print('  python debug_rag_pipeline.py --analyze-documents')
        print('  python debug_rag_pipeline.py --check-pgvector')


if __name__ == "__main__":
    asyncio.run(main())
