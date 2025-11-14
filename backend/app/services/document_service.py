from minio import Minio
from minio.error import S3Error
import aiofiles
import logging
from pathlib import Path
from typing import List, Dict, Optional
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.models.database import Document, DocumentChunk
from app.services.embedding_service import embedding_service
import io
import os
import re

# Document processing imports
try:
    from docling.document_converter import DocumentConverter
    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False
    logging.warning("Docling not available, using fallback processors")

from PyPDF2 import PdfReader
from docx import Document as DocxDocument
from pptx import Presentation
import json

# LangChain for better text splitting
from langchain.text_splitter import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)


class DocumentService:
    def __init__(self):
        self.minio_client = None
        self.doc_converter = None
        self._initialized = False

    async def initialize(self):
        """Initialize MinIO and document converter"""
        if self._initialized:
            return

        try:
            # Initialize MinIO
            self.minio_client = Minio(
                settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_SECURE
            )

            # Create bucket if it doesn't exist
            if not self.minio_client.bucket_exists(settings.MINIO_BUCKET_NAME):
                self.minio_client.make_bucket(settings.MINIO_BUCKET_NAME)
                logger.info(f"Created MinIO bucket: {settings.MINIO_BUCKET_NAME}")

            # Initialize Docling if available
            if DOCLING_AVAILABLE:
                self.doc_converter = DocumentConverter()
                logger.info("Docling document converter initialized")

            self._initialized = True
            logger.info("Document service initialized")

        except Exception as e:
            logger.error(f"Error initializing document service: {e}")
            raise

    async def upload_file(
        self,
        file_data: bytes,
        filename: str,
        file_type: str,
        source_type: str = "upload",
        source_url: Optional[str] = None,
        db: AsyncSession = None
    ) -> Document:
        """Upload file to MinIO and create database record"""
        if not self._initialized:
            await self.initialize()

        try:
            # Generate unique file path
            file_id = str(uuid.uuid4())
            file_extension = Path(filename).suffix
            object_name = f"{file_id}{file_extension}"

            # Upload to MinIO
            self.minio_client.put_object(
                settings.MINIO_BUCKET_NAME,
                object_name,
                io.BytesIO(file_data),
                length=len(file_data),
                content_type=file_type
            )

            logger.info(f"Uploaded file to MinIO: {object_name}")

            # Create database record
            document = Document(
                id=uuid.UUID(file_id),
                filename=filename,
                file_path=object_name,
                file_type=file_type,
                file_size=len(file_data),
                source_type=source_type,
                source_url=source_url,
                processed=False
            )

            if db:
                db.add(document)
                await db.flush()  # Flush to get ID without committing
                await db.refresh(document)

            return document

        except Exception as e:
            logger.error(f"Error uploading file: {e}")
            raise

    def _extract_text_fallback(self, file_data: bytes, file_type: str, filename: str) -> str:
        """Fallback text extraction for common file types"""
        try:
            if file_type == "application/pdf" or filename.endswith('.pdf'):
                pdf = PdfReader(io.BytesIO(file_data))
                text = "\n\n".join([page.extract_text() for page in pdf.pages])
                return text
            elif file_type.startswith("text/") or filename.endswith('.txt'):
                return file_data.decode('utf-8', errors='ignore')
            elif filename.endswith('.docx'):
                doc = DocxDocument(io.BytesIO(file_data))
                text = "\n\n".join([para.text for para in doc.paragraphs])
                return text
            elif filename.endswith('.pptx'):
                # Extract text from PowerPoint presentations
                prs = Presentation(io.BytesIO(file_data))
                text_runs = []
                for slide in prs.slides:
                    for shape in slide.shapes:
                        if hasattr(shape, "text"):
                            text_runs.append(shape.text)
                text = "\n\n".join(text_runs)
                return text
            elif filename.endswith('.json'):
                data = json.loads(file_data)
                return json.dumps(data, indent=2)
            elif filename.endswith('.md'):
                return file_data.decode('utf-8', errors='ignore')
            else:
                return file_data.decode('utf-8', errors='ignore')
        except Exception as e:
            logger.error(f"Fallback extraction failed: {e}")
            raise

    async def process_document(
        self,
        document_id: uuid.UUID,
        db: AsyncSession
    ) -> List[DocumentChunk]:
        """Process document and create embeddings"""
        if not self._initialized:
            await self.initialize()

        try:
            # Get document from database
            result = await db.execute(select(Document).where(Document.id == document_id))
            document = result.scalar_one_or_none()

            if not document:
                raise ValueError(f"Document not found: {document_id}")

            # Download file from MinIO
            response = self.minio_client.get_object(
                settings.MINIO_BUCKET_NAME,
                document.file_path
            )
            file_data = response.read()
            response.close()
            response.release_conn()

            # Extract text using Docling or fallback
            if self.doc_converter and DOCLING_AVAILABLE:
                try:
                    # Save temporarily for Docling
                    temp_path = f"/tmp/{document.file_path}"
                    async with aiofiles.open(temp_path, 'wb') as f:
                        await f.write(file_data)

                    # Convert with Docling
                    result = self.doc_converter.convert(temp_path)
                    text = result.document.export_to_markdown()

                    # Clean up
                    os.remove(temp_path)
                except Exception as e:
                    logger.warning(f"Docling processing failed, using fallback: {e}")
                    text = self._extract_text_fallback(file_data, document.file_type, document.filename)
            else:
                text = self._extract_text_fallback(file_data, document.file_type, document.filename)

            logger.info(f"Extracted {len(text)} characters from {document.filename}")

            # Chunk the text
            chunks = self._chunk_text(text)
            logger.info(f"Created {len(chunks)} chunks")

            # Generate embeddings
            chunk_texts = [chunk['content'] for chunk in chunks]
            logger.info(f"Generating embeddings for {len(chunk_texts)} chunks...")
            embeddings = await embedding_service.get_embeddings_batch(chunk_texts)
            logger.info(f"Generated {len(embeddings)} embeddings")

            # Verify embeddings
            if not embeddings or len(embeddings) != len(chunk_texts):
                raise ValueError(f"Expected {len(chunk_texts)} embeddings, got {len(embeddings)}")

            # Verify embedding dimensions
            if embeddings and len(embeddings[0]) != 384:
                raise ValueError(f"Expected 384-dimensional embeddings, got {len(embeddings[0])}")

            logger.info(f"✅ All embeddings valid (384 dimensions)")

            # Create chunk records
            document_chunks = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                chunk_record = DocumentChunk(
                    document_id=document_id,
                    chunk_index=i,
                    content=chunk['content'],
                    embedding=embedding,
                    meta_info={
                        'source': document.filename,
                        'source_type': document.source_type,
                        'source_url': document.source_url,
                        'char_start': chunk.get('start', 0),
                        'char_end': chunk.get('end', 0)
                    }
                )
                db.add(chunk_record)
                document_chunks.append(chunk_record)

            # Mark document as processed
            document.processed = True
            await db.flush()  # Flush changes without committing

            logger.info(f"Successfully processed document {document_id} with {len(document_chunks)} chunks")
            return document_chunks

        except Exception as e:
            logger.error(f"Error processing document: {e}", exc_info=True)
            # Mark document as failed
            if document:
                document.processing_error = str(e)
                await db.flush()  # Flush error state without committing
            raise

    def _chunk_text(self, text: str) -> List[Dict]:
        """
        Split text into overlapping chunks with semantic boundaries.
        Uses LangChain's RecursiveCharacterTextSplitter for better semantic chunking.
        """
        # Clean the text first
        text = self._clean_text(text)

        # Use RecursiveCharacterTextSplitter for better semantic chunking
        # This splits on paragraphs, then sentences, then words
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            length_function=len,
            separators=[
                "\n\n\n",  # Multiple newlines (section breaks)
                "\n\n",    # Paragraph breaks
                "\n",      # Line breaks
                ". ",      # Sentence endings
                "! ",      # Exclamations
                "? ",      # Questions
                "; ",      # Semicolons
                ", ",      # Commas
                " ",       # Spaces
                ""         # Characters
            ],
            is_separator_regex=False,
        )

        # Split the text
        chunk_texts = text_splitter.split_text(text)

        # Create chunks with metadata
        chunks = []
        char_position = 0
        for i, chunk_text in enumerate(chunk_texts):
            # Find the chunk in the original text for accurate positioning
            start_pos = text.find(chunk_text, char_position)
            if start_pos == -1:
                start_pos = char_position
            end_pos = start_pos + len(chunk_text)

            chunks.append({
                'content': chunk_text.strip(),
                'start': start_pos,
                'end': end_pos,
                'chunk_index': i
            })

            char_position = end_pos

        logger.info(f"Created {len(chunks)} semantic chunks (avg size: {sum(len(c['content']) for c in chunks) / len(chunks):.0f} chars)")
        return chunks

    def _clean_text(self, text: str) -> str:
        """
        Clean extracted text for better chunking and embedding.
        """
        # Remove excessive whitespace while preserving structure
        text = re.sub(r'\n{4,}', '\n\n\n', text)  # Max 3 consecutive newlines
        text = re.sub(r' {3,}', '  ', text)  # Max 2 consecutive spaces
        text = re.sub(r'\t+', ' ', text)  # Replace tabs with spaces

        # Remove page numbers and headers/footers patterns (common in PDFs)
        text = re.sub(r'\n\d+\n', '\n', text)  # Standalone page numbers
        text = re.sub(r'Page \d+ of \d+', '', text, flags=re.IGNORECASE)

        # Remove excessive dashes (often used as separators)
        text = re.sub(r'-{4,}', '', text)
        text = re.sub(r'_{4,}', '', text)

        return text.strip()

    async def search_similar_chunks(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        threshold: float = 0.5,
        db: AsyncSession = None,
        query_text: str = None,
        use_hybrid: bool = True
    ) -> List[Dict]:
        """
        Search for similar document chunks using hybrid search:
        1. Vector similarity search (semantic)
        2. Keyword matching (lexical) - optional
        3. Combined reranking for better results
        """
        from sqlalchemy import text as sql_text, select, func
        from app.models.database import DocumentChunk

        try:
            # First check if there are any document chunks at all
            count_query = select(func.count()).select_from(DocumentChunk)
            count_result = await db.execute(count_query)
            chunk_count = count_result.scalar()

            if chunk_count == 0:
                logger.info("No documents found in database")
                return []

            # Convert embedding to PostgreSQL vector format string
            embedding_str = f"[{','.join(map(str, query_embedding))}]"

            # Hybrid search: combine semantic and keyword search
            if use_hybrid and query_text:
                # Extract keywords from query for keyword matching
                keywords = self._extract_keywords(query_text)
                keyword_condition = " OR ".join([f"dc.content ILIKE '%{kw}%'" for kw in keywords]) if keywords else "TRUE"

                # Hybrid query with both semantic and keyword matching
                query = sql_text(f"""
                    WITH semantic_search AS (
                        SELECT
                            dc.id,
                            dc.document_id,
                            dc.content,
                            dc.meta_info,
                            d.filename,
                            d.source_type,
                            d.source_url,
                            1 - (dc.embedding <=> '{embedding_str}'::vector) as semantic_score
                        FROM document_chunks dc
                        JOIN documents d ON dc.document_id = d.id
                        WHERE dc.embedding IS NOT NULL
                    ),
                    keyword_search AS (
                        SELECT
                            id,
                            CASE
                                WHEN ({keyword_condition}) THEN 1.0
                                ELSE 0.0
                            END as keyword_score
                        FROM document_chunks
                    )
                    SELECT
                        ss.id,
                        ss.document_id,
                        ss.content,
                        ss.meta_info,
                        ss.filename,
                        ss.source_type,
                        ss.source_url,
                        ss.semantic_score,
                        COALESCE(ks.keyword_score, 0) as keyword_score,
                        (ss.semantic_score * 0.7 + COALESCE(ks.keyword_score, 0) * 0.3) as combined_score
                    FROM semantic_search ss
                    LEFT JOIN keyword_search ks ON ss.id = ks.id
                    WHERE (ss.semantic_score * 0.7 + COALESCE(ks.keyword_score, 0) * 0.3) > :threshold
                    ORDER BY combined_score DESC
                    LIMIT :limit
                """)
            else:
                # Standard semantic search only
                query = sql_text(f"""
                    SELECT
                        dc.id,
                        dc.document_id,
                        dc.content,
                        dc.meta_info,
                        d.filename,
                        d.source_type,
                        d.source_url,
                        1 - (dc.embedding <=> '{embedding_str}'::vector) as semantic_score,
                        0.0 as keyword_score,
                        1 - (dc.embedding <=> '{embedding_str}'::vector) as combined_score
                    FROM document_chunks dc
                    JOIN documents d ON dc.document_id = d.id
                    WHERE dc.embedding IS NOT NULL
                        AND 1 - (dc.embedding <=> '{embedding_str}'::vector) > :threshold
                    ORDER BY dc.embedding <=> '{embedding_str}'::vector
                    LIMIT :limit
                """)

            result = await db.execute(
                query,
                {
                    "threshold": threshold,
                    "limit": top_k * 2  # Get more results for better diversity
                }
            )

            chunks = []
            for row in result:
                chunks.append({
                    'id': str(row.id),
                    'document_id': str(row.document_id),
                    'content': row.content,
                    'meta_info': row.meta_info,
                    'filename': row.filename,
                    'source_type': row.source_type,
                    'source_url': row.source_url,
                    'similarity': float(row.combined_score),
                    'semantic_score': float(row.semantic_score),
                    'keyword_score': float(row.keyword_score)
                })

            # Diversify results - avoid too many chunks from same document
            chunks = self._diversify_chunks(chunks, top_k)

            logger.info(f"Found {len(chunks)} similar chunks out of {chunk_count} total (hybrid={use_hybrid})")
            return chunks

        except Exception as e:
            logger.error(f"Error searching similar chunks: {e}")
            # Rollback transaction on error to prevent "transaction aborted" state
            await db.rollback()
            # Return empty list instead of raising to allow graceful degradation
            return []

    def _extract_keywords(self, text: str, max_keywords: int = 5) -> List[str]:
        """Extract important keywords from query text"""
        # Remove common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'what', 'which', 'who', 'when', 'where', 'why', 'how', 'can', 'could',
            'should', 'would', 'will', 'shall', 'may', 'might', 'must', 'do', 'does', 'did'
        }

        # Extract words (alphanumeric, min 3 chars)
        words = re.findall(r'\b[a-zA-Z0-9]{3,}\b', text.lower())

        # Filter stop words and get unique keywords
        keywords = [w for w in words if w not in stop_words]

        # Return top keywords (by length as simple heuristic)
        keywords = sorted(set(keywords), key=len, reverse=True)[:max_keywords]

        return keywords

    def _diversify_chunks(self, chunks: List[Dict], top_k: int) -> List[Dict]:
        """
        Diversify results to avoid too many chunks from the same document.
        Ensures we get variety in sources.
        """
        if len(chunks) <= top_k:
            return chunks

        # Group by document
        from collections import defaultdict
        doc_chunks = defaultdict(list)
        for chunk in chunks:
            doc_chunks[chunk['document_id']].append(chunk)

        # Select diverse chunks
        diversified = []
        max_per_doc = max(2, top_k // len(doc_chunks))  # At least 2 per doc if we have few docs

        # First pass: add top chunk from each document
        for doc_id, doc_chunk_list in doc_chunks.items():
            if len(diversified) < top_k:
                diversified.append(doc_chunk_list[0])

        # Second pass: fill remaining slots with best chunks
        remaining = [c for c in chunks if c not in diversified]
        diversified.extend(remaining[:top_k - len(diversified)])

        return diversified[:top_k]


# Singleton instance
document_service = DocumentService()
