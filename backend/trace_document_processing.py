#!/usr/bin/env python3
"""
Document Processing Flow Tracer
================================
Comprehensive tool to trace the complete document processing pipeline:
- Multi-analyzer ensemble classification
- Content type detection
- Text extraction
- Hybrid OCR+Vision decisions
- Chunking and embedding generation

Usage:
    python trace_document_processing.py <filename>
    python trace_document_processing.py <document_id>
    python trace_document_processing.py --latest
    python trace_document_processing.py --all
"""

import sys
import os
import asyncio
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
import argparse
from pathlib import Path
import uuid

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import select, func, text, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models.database import Document, DocumentChunk

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


async def trace_document_processing(
    document_id: Optional[uuid.UUID] = None,
    filename: Optional[str] = None,
    latest: bool = False
):
    """Trace the complete processing flow for a document"""

    print_section("DOCUMENT PROCESSING FLOW TRACER")

    async with AsyncSessionLocal() as db:
        try:
            # Find document
            if document_id:
                query = select(Document).where(Document.id == document_id)
                print_info("Searching by", f"Document ID: {document_id}")
            elif filename:
                query = select(Document).where(Document.filename == filename).order_by(desc(Document.created_at))
                print_info("Searching by", f"Filename: {filename}")
            elif latest:
                query = select(Document).order_by(desc(Document.created_at)).limit(1)
                print_info("Searching by", "Latest document")
            else:
                print_error("Must specify document_id, filename, or --latest")
                return

            result = await db.execute(query)
            document = result.scalar_one_or_none()

            if not document:
                print_error("Document not found!")
                return

            print_success(f"Found document: {document.filename}")
            print()

            # Phase 1: Document Metadata
            print_section("PHASE 1: DOCUMENT METADATA")
            print_info("Document ID", document.id)
            print_info("Filename", document.filename)
            print_info("File Type", document.file_type)
            print_info("File Size", f"{document.file_size:,} bytes")
            print_info("Source Type", document.source_type)
            print_info("Upload Date", document.created_at)
            print_info("Processing Status", document.processing_status or "N/A")

            if document.source_url:
                print_info("Source URL", document.source_url)

            # Organizational info
            if hasattr(document, 'department'):
                print_subsection("Organizational Context")
                print_info("Department", document.department or "N/A")
                print_info("Team", document.team or "N/A")
                print_info("User Role", document.user_role or "N/A")

            if hasattr(document, 'minio_path') and document.minio_path:
                print_info("MinIO Path", document.minio_path)

            # Phase 2: Chunks Analysis
            print_section("PHASE 2: CHUNKING & EMBEDDING")

            chunk_query = select(DocumentChunk).where(
                DocumentChunk.document_id == document.id
            ).order_by(DocumentChunk.chunk_index)

            chunk_result = await db.execute(chunk_query)
            chunks = chunk_result.scalars().all()

            print_info("Total Chunks", len(chunks))

            if not chunks:
                print_warning("No chunks found! Document may not have been processed.")
                return

            # Analyze first chunk for classification details
            first_chunk = chunks[0]

            print_subsection("Content Extraction")
            print_info("Extracted Text Length", len(first_chunk.content))
            print_info("Content Preview", f'"{first_chunk.content[:200]}..."' if len(first_chunk.content) > 200 else f'"{first_chunk.content}"')

            # Phase 3: Multi-Analyzer Ensemble Results
            if first_chunk.embedding_metadata:
                print_section("PHASE 3: MULTI-ANALYZER ENSEMBLE CLASSIFICATION")

                metadata = first_chunk.embedding_metadata

                # Content Analysis
                if 'content_analysis' in metadata:
                    analysis = metadata['content_analysis']
                    print_subsection("Classification Results")
                    print_info("Content Type", analysis.get('content_type', 'unknown'))
                    print_info("Confidence", f"{analysis.get('confidence', 0):.2%}")
                    print_info("Strategy Selected", first_chunk.embedding_strategy or "N/A")
                    print_info("Reasoning", analysis.get('reasoning', 'N/A'))

                    # Analyzer breakdown (if available in logs)
                    # This would need to be stored in metadata for full visibility

                # Embedding Details
                print_subsection("Embedding Generation")
                print_info("Model", metadata.get('embeddings_detail', {}).get('text', {}).get('model', 'unknown'))
                print_info("Vector Column", metadata.get('vector_column', 'unknown'))
                print_info("Dimension", metadata.get('dimension', 'unknown'))
                print_info("Channels Processed", metadata.get('channels_processed', []))
                print_info("Processing Timestamp", metadata.get('processing_timestamp', 'unknown'))

            # Phase 4: Embedding Status
            print_section("PHASE 4: EMBEDDING STATUS")

            embeddings_status = {
                'embedding': 0,
                'visual_embedding': 0,
                'table_embedding': 0,
                'code_embedding': 0,
                'numerical_embedding': 0
            }

            for chunk in chunks:
                if chunk.embedding is not None:
                    embeddings_status['embedding'] += 1
                if hasattr(chunk, 'visual_embedding') and chunk.visual_embedding is not None:
                    embeddings_status['visual_embedding'] += 1
                if hasattr(chunk, 'table_embedding') and chunk.table_embedding is not None:
                    embeddings_status['table_embedding'] += 1
                if hasattr(chunk, 'code_embedding') and chunk.code_embedding is not None:
                    embeddings_status['code_embedding'] += 1
                if hasattr(chunk, 'numerical_embedding') and chunk.numerical_embedding is not None:
                    embeddings_status['numerical_embedding'] += 1

            for emb_type, count in embeddings_status.items():
                if count > 0:
                    percentage = (count / len(chunks)) * 100
                    print_info(f"{emb_type.replace('_', ' ').title()}", f"{count}/{len(chunks)} ({percentage:.1f}%)")

            # Phase 5: Session Associations
            print_section("PHASE 5: SESSION ASSOCIATIONS")

            try:
                from app.models.database_enhanced import SessionDocument

                session_query = select(SessionDocument).where(
                    SessionDocument.document_id == document.id
                )
                session_result = await db.execute(session_query)
                session_docs = session_result.scalars().all()

                if session_docs:
                    print_success(f"Associated with {len(session_docs)} session(s)")
                    for sd in session_docs:
                        print_info("Session ID", sd.session_id)
                        print_info("  Added At", sd.added_at)
                else:
                    print_warning("Not associated with any sessions")
            except Exception as e:
                print_warning(f"Could not check session associations: {e}")

            # Phase 6: Diagnostic Analysis
            print_section("PHASE 6: DIAGNOSTIC ANALYSIS")

            # Check for issues
            issues = []
            warnings = []

            # Issue 1: Low text extraction
            if first_chunk.content and len(first_chunk.content) < 50:
                issues.append("Very low text extraction (<50 chars)")
                warnings.append("Possible causes:")
                warnings.append("  - Image-based PDF without OCR")
                warnings.append("  - Scanned document not detected")
                warnings.append("  - Hybrid extraction not triggered")

            # Issue 2: Placeholder content
            if first_chunk.content and "<!-- image -->" in first_chunk.content:
                issues.append("Content contains placeholder text '<!-- image -->'")
                warnings.append("This indicates:")
                warnings.append("  - Docling detected images but couldn't extract text")
                warnings.append("  - Hybrid OCR+Vision was likely not triggered")
                warnings.append("  - Document may have been misclassified")

            # Issue 3: Missing embeddings
            missing_embeddings = len(chunks) - embeddings_status['embedding']
            if missing_embeddings > 0:
                issues.append(f"{missing_embeddings} chunks missing embeddings")

            # Issue 4: Classification mismatch
            if first_chunk.embedding_metadata:
                content_analysis = first_chunk.embedding_metadata.get('content_analysis', {})
                content_type = content_analysis.get('content_type', '')
                confidence = content_analysis.get('confidence', 1.0)

                if content_type in ['image_heavy', 'scanned'] and len(first_chunk.content) < 100:
                    issues.append("Classified as image/scanned but minimal text extracted")
                    warnings.append("Hybrid extraction should have been triggered")

                if confidence < 0.7:
                    warnings.append(f"Low classification confidence: {confidence:.2%}")
                    warnings.append("  - Multiple analyzers may have disagreed")

            # Print diagnosis
            if issues:
                print_subsection("Issues Detected")
                for issue in issues:
                    print_error(issue)

            if warnings:
                print_subsection("Diagnostic Warnings")
                for warning in warnings:
                    print_warning(warning)

            if not issues and not warnings:
                print_success("No issues detected! Document processed successfully.")

            # Phase 7: Recommendations
            if issues:
                print_section("RECOMMENDATIONS")

                if any("image" in issue.lower() or "placeholder" in issue.lower() for issue in issues):
                    print_subsection("Improve Classification")
                    print("1. Check multi-analyzer ensemble voting logic")
                    print("2. Tune analyzer thresholds (multi_analyzer_ensemble.py)")
                    print("3. Consider adding vision-first analyzer")

                    print_subsection("Enable Hybrid Extraction")
                    print("1. Lower content_type threshold in document_service.py")
                    print("2. Add 'scanned' to hybrid extraction trigger")
                    print("3. Test with: vision_model='llama3.2-vision:11b'")

                if missing_embeddings > 0:
                    print_subsection("Fix Missing Embeddings")
                    print("1. Check embedding service logs")
                    print("2. Verify sentence-transformers model loaded")
                    print("3. Ensure database transaction commits")

        except Exception as e:
            print_error(f"Error tracing document: {e}")
            import traceback
            traceback.print_exc()


async def list_recent_documents(limit: int = 10):
    """List recent documents for selection"""
    print_section("RECENT DOCUMENTS")

    async with AsyncSessionLocal() as db:
        try:
            query = select(
                Document.id,
                Document.filename,
                Document.file_type,
                Document.file_size,
                Document.created_at,
                func.count(DocumentChunk.id).label('chunk_count')
            ).outerjoin(
                DocumentChunk, Document.id == DocumentChunk.document_id
            ).group_by(
                Document.id
            ).order_by(
                desc(Document.created_at)
            ).limit(limit)

            result = await db.execute(query)
            rows = result.all()

            if not rows:
                print_warning("No documents found in database")
                return

            print(f"{'#':<3} {'Document ID':<38} {'Filename':<30} {'Chunks':<8} {'Upload Date'}")
            print("-" * 100)

            for i, row in enumerate(rows, 1):
                doc_id = str(row.id)
                filename = row.filename[:28] + ".." if len(row.filename) > 30 else row.filename
                chunk_count = row.chunk_count
                upload_date = row.created_at.strftime("%Y-%m-%d %H:%M:%S") if row.created_at else "N/A"

                print(f"{i:<3} {doc_id:<38} {filename:<30} {chunk_count:<8} {upload_date}")

            print()
            print_info("Usage", "python trace_document_processing.py <document_id>")
            print_info("Example", f"python trace_document_processing.py {rows[0].id}")

        except Exception as e:
            print_error(f"Error listing documents: {e}")


async def main():
    parser = argparse.ArgumentParser(description="Trace Document Processing Flow")
    parser.add_argument("identifier", nargs="?", help="Document ID or filename")
    parser.add_argument("--latest", action="store_true", help="Trace latest document")
    parser.add_argument("--all", action="store_true", help="List all recent documents")
    parser.add_argument("--limit", type=int, default=10, help="Number of documents to list (with --all)")

    args = parser.parse_args()

    if args.all:
        await list_recent_documents(args.limit)
        return

    if args.latest:
        await trace_document_processing(latest=True)
    elif args.identifier:
        # Check if it's a UUID or filename
        try:
            doc_id = uuid.UUID(args.identifier)
            await trace_document_processing(document_id=doc_id)
        except ValueError:
            # Not a UUID, treat as filename
            await trace_document_processing(filename=args.identifier)
    else:
        # No args provided, list recent documents
        await list_recent_documents()


if __name__ == "__main__":
    asyncio.run(main())
