#!/usr/bin/env python3
"""
Script to regenerate embeddings for documents that are missing them.

This script will:
1. Find all document chunks without embeddings
2. Generate embeddings for those chunks
3. Update the database with the new embeddings

Usage:
    python regenerate_embeddings.py [--batch-size 100] [--document-id UUID]
"""

import asyncio
import argparse
import logging
from typing import List, Optional
import uuid

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

# Add app to path
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.core.database import async_session_maker
from app.models.database import Document, DocumentChunk
from app.services.embedding_service import embedding_service

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def count_chunks_without_embeddings(
    db: AsyncSession,
    document_id: Optional[uuid.UUID] = None
) -> int:
    """Count how many chunks are missing embeddings"""
    query = select(func.count()).select_from(DocumentChunk).where(
        DocumentChunk.embedding == None
    )

    if document_id:
        query = query.where(DocumentChunk.document_id == document_id)

    result = await db.execute(query)
    return result.scalar()


async def regenerate_embeddings_for_document(
    document_id: uuid.UUID,
    db: AsyncSession,
    batch_size: int = 100
) -> dict:
    """Regenerate embeddings for a single document"""

    # Get document
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()

    if not document:
        raise ValueError(f"Document not found: {document_id}")

    logger.info(f"Processing document: {document.filename}")

    # Get chunks without embeddings
    chunks_query = select(DocumentChunk).where(
        DocumentChunk.document_id == document_id,
        DocumentChunk.embedding == None
    )
    chunks_result = await db.execute(chunks_query)
    chunks = chunks_result.scalars().all()

    if not chunks:
        logger.info(f"  ✅ All chunks already have embeddings")
        return {
            'document_id': str(document_id),
            'filename': document.filename,
            'chunks_processed': 0,
            'status': 'already_complete'
        }

    logger.info(f"  Found {len(chunks)} chunks without embeddings")

    # Process in batches
    total_processed = 0
    errors = 0

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        chunk_texts = [chunk.content for chunk in batch]

        try:
            # Generate embeddings for batch
            logger.info(f"  Generating embeddings for batch {i//batch_size + 1} ({len(batch)} chunks)")
            embeddings = await embedding_service.get_embeddings_batch(chunk_texts)

            if not embeddings or len(embeddings) != len(batch):
                logger.error(f"  ❌ Expected {len(batch)} embeddings, got {len(embeddings)}")
                errors += len(batch)
                continue

            # Verify dimensions
            if embeddings[0] and len(embeddings[0]) != 384:
                logger.error(f"  ❌ Invalid embedding dimensions: {len(embeddings[0])}")
                errors += len(batch)
                continue

            # Update chunks with embeddings
            for chunk, embedding in zip(batch, embeddings):
                chunk.embedding = embedding

            # Commit batch
            await db.flush()
            total_processed += len(batch)
            logger.info(f"  ✅ Processed {total_processed}/{len(chunks)} chunks")

        except Exception as e:
            logger.error(f"  ❌ Error processing batch: {e}", exc_info=True)
            errors += len(batch)
            await db.rollback()
            continue

    # Final commit
    await db.commit()

    return {
        'document_id': str(document_id),
        'filename': document.filename,
        'chunks_processed': total_processed,
        'errors': errors,
        'status': 'completed' if errors == 0 else 'partial'
    }


async def regenerate_all_embeddings(
    db: AsyncSession,
    batch_size: int = 100,
    document_id: Optional[uuid.UUID] = None
) -> dict:
    """Regenerate embeddings for all documents (or a specific document)"""

    logger.info("=" * 60)
    logger.info("EMBEDDING REGENERATION SCRIPT")
    logger.info("=" * 60)

    # Count chunks without embeddings
    missing_count = await count_chunks_without_embeddings(db, document_id)
    logger.info(f"Found {missing_count} chunks without embeddings")

    if missing_count == 0:
        logger.info("✅ All chunks already have embeddings!")
        return {
            'total_chunks_processed': 0,
            'documents_processed': 0,
            'status': 'already_complete'
        }

    # Get documents with missing embeddings
    if document_id:
        # Process specific document
        documents_query = select(Document).where(Document.id == document_id)
    else:
        # Get all documents that have chunks without embeddings
        documents_query = select(Document).where(
            Document.id.in_(
                select(DocumentChunk.document_id)
                .where(DocumentChunk.embedding == None)
                .distinct()
            )
        )

    documents_result = await db.execute(documents_query)
    documents = documents_result.scalars().all()

    logger.info(f"Found {len(documents)} documents to process")
    logger.info("")

    # Process each document
    results = []
    total_chunks = 0
    total_errors = 0

    for i, doc in enumerate(documents, 1):
        logger.info(f"[{i}/{len(documents)}] Processing: {doc.filename}")
        try:
            result = await regenerate_embeddings_for_document(
                doc.id,
                db,
                batch_size
            )
            results.append(result)
            total_chunks += result['chunks_processed']
            total_errors += result.get('errors', 0)
        except Exception as e:
            logger.error(f"  ❌ Error processing document: {e}", exc_info=True)
            results.append({
                'document_id': str(doc.id),
                'filename': doc.filename,
                'status': 'error',
                'error': str(e)
            })
            total_errors += 1

        logger.info("")

    logger.info("=" * 60)
    logger.info("REGENERATION COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Documents processed: {len(documents)}")
    logger.info(f"Chunks processed: {total_chunks}")
    logger.info(f"Errors: {total_errors}")
    logger.info("")

    return {
        'total_chunks_processed': total_chunks,
        'documents_processed': len(documents),
        'errors': total_errors,
        'status': 'completed' if total_errors == 0 else 'partial',
        'details': results
    }


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Regenerate embeddings for documents'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Number of chunks to process in each batch (default: 100)'
    )
    parser.add_argument(
        '--document-id',
        type=str,
        help='Specific document ID to process (optional)'
    )
    args = parser.parse_args()

    # Parse document ID if provided
    document_id = None
    if args.document_id:
        try:
            document_id = uuid.UUID(args.document_id)
        except ValueError:
            logger.error(f"Invalid document ID: {args.document_id}")
            return

    # Initialize embedding service
    await embedding_service.initialize()

    # Run regeneration
    async with async_session_maker() as db:
        try:
            result = await regenerate_all_embeddings(
                db,
                batch_size=args.batch_size,
                document_id=document_id
            )

            if result['status'] == 'completed':
                logger.info("✅ SUCCESS: All embeddings regenerated successfully")
            elif result['status'] == 'partial':
                logger.warning("⚠️  PARTIAL: Some embeddings failed to regenerate")
            elif result['status'] == 'already_complete':
                logger.info("✅ All embeddings already exist")

        except Exception as e:
            logger.error(f"❌ FATAL ERROR: {e}", exc_info=True)
            raise


if __name__ == "__main__":
    asyncio.run(main())
