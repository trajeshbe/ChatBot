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

    def __init__(self, openai_key: Optional[str] = None):
        # Set OpenAI API key if provided
        if openai_key:
            os.environ["OPENAI_API_KEY"] = openai_key
            print_success(f"OpenAI API key set (length: {len(openai_key)})")

            # CRITICAL: Clear settings cache and reload to pick up the new environment variable
            from app.core.config import get_settings
            get_settings.cache_clear()
            print_success("Settings cache cleared - API key will be picked up on next load")

        # Use 'postgres' service name in Docker, fallback to localhost for local development
        default_db_url = "postgresql://postgres:postgres@postgres:5432/ragchatbot"
        self.db_url = os.getenv("DATABASE_URL", default_db_url)
        self.engine = create_engine(self.db_url)
        self.SessionLocal = sessionmaker(bind=self.engine)

        # Initialize metrics tracking
        self.metrics = {
            'timing': {},
            'similarity_scores': [],
            'thresholds': {
                'excellent': 0.7,
                'good': 0.5,
                'fair': 0.3
            },
            'results_quality': {
                'excellent': 0,
                'good': 0,
                'fair': 0,
                'poor': 0
            },
            'performance': {},
            'evaluation': {}
        }

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
            return RAGService()
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
            rag_service = RAGService()

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
            embedding = await embedding_service.get_embedding(query)
            duration = (datetime.now() - start_time).total_seconds()

            # Track timing
            self.metrics['timing']['embedding_generation'] = duration

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

            # Time the search
            start_time = datetime.now()

            # Use f-string for embedding since it's already a sanitized string representation
            sql = text(f"""
                SELECT
                    c.id,
                    c.document_id,
                    d.filename,
                    c.chunk_index,
                    c.content,
                    1 - (c.embedding <=> '{embedding_str}'::vector) as similarity_score
                FROM document_chunks c
                JOIN documents d ON c.document_id = d.id
                WHERE c.embedding IS NOT NULL
                ORDER BY c.embedding <=> '{embedding_str}'::vector
                LIMIT :top_k
            """)

            result = db.execute(
                sql,
                {
                    "top_k": top_k
                }
            )

            results = result.fetchall()

            # Track search timing
            search_duration = (datetime.now() - start_time).total_seconds()
            self.metrics['timing']['vector_search'] = search_duration

            if not results:
                print_warning("No results found! This could indicate:")
                print_warning("  1. No chunks have embeddings")
                print_warning("  2. Vector search is not working")
                print_warning("  3. pgvector extension is not installed")
                return []

            print_success(f"Found {len(results)} results in {search_duration:.3f}s")

            # Collect similarity scores for metrics
            scores = [float(row[5]) for row in results]
            self.metrics['similarity_scores'] = scores

            # Calculate quality distribution
            thresholds = self.metrics['thresholds']
            for score in scores:
                if score > thresholds['excellent']:
                    self.metrics['results_quality']['excellent'] += 1
                elif score > thresholds['good']:
                    self.metrics['results_quality']['good'] += 1
                elif score > thresholds['fair']:
                    self.metrics['results_quality']['fair'] += 1
                else:
                    self.metrics['results_quality']['poor'] += 1

            # Store evaluation metrics
            if scores:
                self.metrics['evaluation']['max_score'] = max(scores)
                self.metrics['evaluation']['min_score'] = min(scores)
                self.metrics['evaluation']['avg_score'] = sum(scores) / len(scores)
                self.metrics['evaluation']['median_score'] = sorted(scores)[len(scores) // 2]
                self.metrics['evaluation']['score_std'] = np.std(scores)

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

        # Print comprehensive metrics summary
        self.print_comprehensive_metrics()

    def print_comprehensive_metrics(self):
        """Print comprehensive metrics summary"""
        print_section("COMPREHENSIVE METRICS SUMMARY")

        # Timing Metrics
        print_subsection("⏱️  Performance Metrics (Timing)")
        if self.metrics['timing']:
            total_time = sum(self.metrics['timing'].values())
            print_info("Total Pipeline Time", f"{total_time:.3f}s")

            for operation, duration in self.metrics['timing'].items():
                percentage = (duration / total_time * 100) if total_time > 0 else 0
                print_info(f"  {operation.replace('_', ' ').title()}",
                          f"{duration:.3f}s ({percentage:.1f}%)", indent=1)

            self.metrics['performance']['total_time'] = total_time
        else:
            print_warning("No timing metrics collected")

        # Threshold Configuration
        print_subsection("📊 Similarity Score Thresholds")
        thresholds = self.metrics['thresholds']
        print_info("Excellent Match", f"> {thresholds['excellent']}")
        print_info("Good Match", f"> {thresholds['good']}")
        print_info("Fair Match", f"> {thresholds['fair']}")
        print_info("Poor Match", f"< {thresholds['fair']}")

        # Quality Distribution
        print_subsection("🎯 Results Quality Distribution")
        quality = self.metrics['results_quality']
        total_results = sum(quality.values())

        if total_results > 0:
            for level in ['excellent', 'good', 'fair', 'poor']:
                count = quality[level]
                percentage = (count / total_results * 100)
                bar_length = int(percentage / 2)  # Max 50 chars
                bar = '█' * bar_length
                print(f"{Colors.OKBLUE}{level.capitalize():10s}:{Colors.ENDC} {count:2d} ({percentage:5.1f}%) {bar}")
        else:
            print_warning("No quality metrics collected")

        # Evaluation Metrics
        if self.metrics['evaluation']:
            print_subsection("📈 Evaluation Metrics")
            eval_metrics = self.metrics['evaluation']

            print_info("Maximum Similarity Score", f"{eval_metrics.get('max_score', 0):.4f}")
            print_info("Minimum Similarity Score", f"{eval_metrics.get('min_score', 0):.4f}")
            print_info("Average Similarity Score", f"{eval_metrics.get('avg_score', 0):.4f}")
            print_info("Median Similarity Score", f"{eval_metrics.get('median_score', 0):.4f}")
            print_info("Score Standard Deviation", f"{eval_metrics.get('score_std', 0):.4f}")

            # Score distribution visualization
            if self.metrics['similarity_scores']:
                print_subsection("📉 Score Distribution")
                scores = self.metrics['similarity_scores']
                bins = [0.0, 0.3, 0.5, 0.7, 1.0]
                bin_labels = ['0.0-0.3', '0.3-0.5', '0.5-0.7', '0.7-1.0']

                for i in range(len(bins) - 1):
                    count = sum(1 for s in scores if bins[i] <= s < bins[i+1])
                    if i == len(bins) - 2:  # Last bin includes upper bound
                        count = sum(1 for s in scores if bins[i] <= s <= bins[i+1])
                    percentage = (count / len(scores) * 100) if len(scores) > 0 else 0
                    bar_length = int(percentage / 2)
                    bar = '▓' * bar_length
                    print(f"{Colors.OKCYAN}{bin_labels[i]:10s}:{Colors.ENDC} {count:2d} ({percentage:5.1f}%) {bar}")

        # Relevance Analysis
        print_subsection("🔍 Relevance Analysis")
        if self.metrics['similarity_scores']:
            scores = self.metrics['similarity_scores']
            above_threshold = sum(1 for s in scores if s > thresholds['fair'])
            print_info("Total Results", len(scores))
            print_info("Results Above Fair Threshold",
                      f"{above_threshold} ({above_threshold/len(scores)*100:.1f}%)")

            # Determine overall quality
            avg_score = self.metrics['evaluation'].get('avg_score', 0)
            if avg_score > thresholds['excellent']:
                print_success("Overall Quality: EXCELLENT - Results highly relevant")
            elif avg_score > thresholds['good']:
                print_success("Overall Quality: GOOD - Results are relevant")
            elif avg_score > thresholds['fair']:
                print_warning("Overall Quality: FAIR - Results moderately relevant")
            else:
                print_error("Overall Quality: POOR - Results may not be relevant")

        # Token and Cost Metrics (if available)
        if 'tokens_used' in self.metrics.get('performance', {}):
            print_subsection("💰 Token Usage & Cost Metrics")
            print_info("Total Tokens Used", self.metrics['performance']['tokens_used'])
            if 'estimated_cost' in self.metrics['performance']:
                print_info("Estimated Cost", f"${self.metrics['performance']['estimated_cost']:.4f}")

        # RAGAS Evaluation Metrics (if available)
        if 'ragas' in self.metrics and self.metrics['ragas'].get('summary'):
            print_subsection("📊 RAGAS Evaluation Metrics")
            ragas = self.metrics['ragas']

            if ragas.get('faithfulness') is not None:
                print_info("Faithfulness", f"{ragas['faithfulness']:.4f}")
            if ragas.get('answer_relevancy') is not None:
                print_info("Answer Relevancy", f"{ragas['answer_relevancy']:.4f}")
            if ragas.get('context_precision') is not None:
                print_info("Context Precision", f"{ragas['context_precision']:.4f}")
            if ragas.get('context_recall') is not None:
                print_info("Context Recall", f"{ragas['context_recall']:.4f}")

            summary = ragas['summary']
            if summary.get('average') is not None:
                avg = summary['average']
                quality = "EXCELLENT" if avg > 0.8 else "GOOD" if avg > 0.6 else "FAIR" if avg > 0.4 else "POOR"
                print_info("Average RAGAS Score", f"{avg:.4f} ({quality})")

    async def analyze_rag_service_call(self, query: str, session_id: Optional[str]):
        """Analyze what the RAG service would actually return"""
        print_section("RAG SERVICE CALL SIMULATION")

        try:
            from app.services.rag_service import RAGService
            from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
            from sqlalchemy.orm import sessionmaker
            # Import LLM service to initialize it
            try:
                from app.services.llm_service_enhanced import llm_service
            except ImportError:
                from app.services.llm_service import llm_service

            # Initialize LLM service (CRITICAL: must be called before RAG service)
            print_info("Initializing LLM service", "...")
            await llm_service.initialize()
            print_success("LLM service initialized successfully")

            # Create async engine for RAG service
            async_db_url = self.db_url.replace('postgresql://', 'postgresql+asyncpg://')
            async_engine = create_async_engine(async_db_url)
            async_session_factory = sessionmaker(
                async_engine, class_=AsyncSession, expire_on_commit=False
            )

            rag_service = RAGService()

            print_info("Calling RAG service", "query()")
            print_info("Parameters", json.dumps({
                "query": query,
                "session_id": session_id,
                "model_id": "gpt-4-turbo"
            }, indent=2))

            # Call RAG service with async session
            async with async_session_factory() as db:
                start_time = datetime.now()
                response = await rag_service.query(
                    query_text=query,
                    conversation_history=None,
                    use_cache=True,
                    model_id="gpt-4-turbo",
                    db=db
                )
                duration = (datetime.now() - start_time).total_seconds()

            # Track RAG service timing
            self.metrics['timing']['rag_service_call'] = duration

            print_success(f"RAG service completed in {duration:.3f}s")

            # Analyze response
            print_subsection("Response Analysis")
            print_info("Answer Length", len(response['answer']))
            print_info("Number of Sources", len(response.get('sources', [])))
            print_info("Model Used", response.get('model', 'unknown'))
            print_info("Query Type", response.get('query_type', 'unknown'))
            print_info("Skipped RAG", response.get('skipped_rag', False))

            if 'tokens_used' in response:
                print_info("Tokens Used", response['tokens_used'])
                self.metrics['performance']['tokens_used'] = response['tokens_used']

                # Estimate cost (rough estimates for GPT-4)
                # Input: ~$0.01/1K tokens, Output: ~$0.03/1K tokens
                # For simplicity, use average of $0.02/1K tokens
                estimated_cost = (response['tokens_used'] / 1000) * 0.02
                self.metrics['performance']['estimated_cost'] = estimated_cost

            if response.get('sources'):
                print_subsection("Sources Used")
                for i, source in enumerate(response['sources'], 1):
                    print(f"\n{Colors.BOLD}Source {i}:{Colors.ENDC}")
                    print_info("  Document", source.get('filename', 'unknown'), indent=1)
                    print_info("  Relevance", f"{source.get('relevance', 0):.4f}", indent=1)
                    preview = source.get('excerpt', '')[:200]
                    if len(source.get('excerpt', '')) > 200:
                        preview += "..."
                    print_info("  Excerpt", f'"{preview}"', indent=1)
            else:
                print_warning("No sources returned - likely answered without retrieval")

            # Show answer preview
            print_subsection("Answer Preview")
            answer_preview = response['answer'][:500] + "..." if len(response['answer']) > 500 else response['answer']
            print(f"{answer_preview}\n")

            # RAGAS Evaluation
            await self.evaluate_with_ragas(query, response)

            # Clean up async engine
            await async_engine.dispose()

        except Exception as e:
            print_error(f"RAG service call failed: {e}")
            import traceback
            traceback.print_exc()

    async def evaluate_with_ragas(self, query: str, response: Dict):
        """
        Evaluate RAG response using RAGAS metrics

        Args:
            query: The user's question
            response: The RAG service response
        """
        print_section("RAGAS EVALUATION METRICS")

        try:
            from app.services.ragas_evaluator import ragas_evaluator

            # Initialize RAGAS evaluator
            print_info("Initializing RAGAS evaluator", "...")
            initialized = await ragas_evaluator.initialize()

            if not initialized:
                print_warning("RAGAS not available - skipping evaluation")
                print_info("Install with", "pip install ragas")
                return

            print_success("RAGAS evaluator initialized")

            # Extract contexts from sources
            contexts = []
            if response.get('sources'):
                for source in response['sources']:
                    content = source.get('excerpt', source.get('content', ''))
                    if content:
                        contexts.append(content)

            if not contexts:
                print_warning("No contexts available for RAGAS evaluation")
                return

            # Evaluate
            print_info("Running RAGAS evaluation", f"{len(contexts)} contexts")
            metrics = await ragas_evaluator.evaluate(
                question=query,
                answer=response['answer'],
                contexts=contexts,
                ground_truth=None  # No ground truth available in debug mode
            )

            # Display metrics
            print_subsection("RAGAS Scores (0.0 - 1.0)")

            if metrics.faithfulness is not None:
                score = metrics.faithfulness
                quality = "Excellent" if score > 0.8 else "Good" if score > 0.6 else "Fair" if score > 0.4 else "Poor"
                print_info("Faithfulness", f"{score:.4f} ({quality})")
                print(f"    {'→ How factually accurate is the answer based on context'}")

            if metrics.answer_relevancy is not None:
                score = metrics.answer_relevancy
                quality = "Excellent" if score > 0.8 else "Good" if score > 0.6 else "Fair" if score > 0.4 else "Poor"
                print_info("Answer Relevancy", f"{score:.4f} ({quality})")
                print(f"    {'→ How relevant is the answer to the question'}")

            if metrics.context_precision is not None:
                score = metrics.context_precision
                quality = "Excellent" if score > 0.8 else "Good" if score > 0.6 else "Fair" if score > 0.4 else "Poor"
                print_info("Context Precision", f"{score:.4f} ({quality})")
                print(f"    {'→ How precise is the retrieved context'}")

            if metrics.context_recall is not None:
                score = metrics.context_recall
                quality = "Excellent" if score > 0.8 else "Good" if score > 0.6 else "Fair" if score > 0.4 else "Poor"
                print_info("Context Recall", f"{score:.4f} ({quality})")
                print(f"    {'→ How well context supports the answer'}")

            # Summary
            summary = metrics.get_summary()
            if summary['average'] is not None:
                print_subsection("Overall RAGAS Quality")
                avg_score = summary['average']
                if avg_score > 0.8:
                    print_success(f"EXCELLENT - Average Score: {avg_score:.4f}")
                elif avg_score > 0.6:
                    print_success(f"GOOD - Average Score: {avg_score:.4f}")
                elif avg_score > 0.4:
                    print_warning(f"FAIR - Average Score: {avg_score:.4f}")
                else:
                    print_error(f"POOR - Average Score: {avg_score:.4f}")

                print_info("Min Score", f"{summary['min']:.4f}")
                print_info("Max Score", f"{summary['max']:.4f}")

                # Store in metrics
                self.metrics['ragas'] = metrics.to_dict()
                self.metrics['ragas']['summary'] = summary

        except Exception as e:
            print_error(f"RAGAS evaluation failed: {e}")
            import traceback
            traceback.print_exc()

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
    parser.add_argument("--openai-key", help="OpenAI API key (alternative to OPENAI_API_KEY env var)")

    args = parser.parse_args()

    # Initialize debugger with OpenAI key if provided
    debugger = RAGPipelineDebugger(openai_key=args.openai_key)

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
