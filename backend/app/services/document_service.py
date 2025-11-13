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

# Document processing imports
try:
    from docling.document_converter import DocumentConverter
    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False
    logging.warning("Docling not available, using fallback processors")

from PyPDF2 import PdfReader
from docx import Document as DocxDocument
import json

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
                await db.commit()
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
            elif filename.endswith('.json'):
                data = json.loads(file_data)
                return json.dumps(data, indent=2)
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
            embeddings = await embedding_service.get_embeddings_batch(chunk_texts)

            # Create chunk records
            document_chunks = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                chunk_record = DocumentChunk(
                    document_id=document_id,
                    chunk_index=i,
                    content=chunk['content'],
                    embedding=embedding,
                    metadata={
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
            await db.commit()

            logger.info(f"Successfully processed document {document_id}")
            return document_chunks

        except Exception as e:
            logger.error(f"Error processing document: {e}")
            # Mark document as failed
            if document:
                document.processing_error = str(e)
                await db.commit()
            raise

    def _chunk_text(self, text: str) -> List[Dict]:
        """Split text into overlapping chunks"""
        chunks = []
        chunk_size = settings.CHUNK_SIZE
        overlap = settings.CHUNK_OVERLAP

        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk_text = text[start:end]

            # Try to break at sentence boundary
            if end < len(text):
                last_period = chunk_text.rfind('.')
                last_newline = chunk_text.rfind('\n')
                break_point = max(last_period, last_newline)
                if break_point > chunk_size * 0.5:  # Only if we're past halfway
                    end = start + break_point + 1
                    chunk_text = text[start:end]

            chunks.append({
                'content': chunk_text.strip(),
                'start': start,
                'end': end
            })

            start = end - overlap

        return chunks

    async def search_similar_chunks(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        threshold: float = 0.7,
        db: AsyncSession = None
    ) -> List[Dict]:
        """Search for similar document chunks using vector similarity"""
        from sqlalchemy import text as sql_text

        try:
            # Convert embedding to PostgreSQL vector format
            embedding_str = f"[{','.join(map(str, query_embedding))}]"

            # Perform vector similarity search
            query = sql_text("""
                SELECT
                    dc.id,
                    dc.document_id,
                    dc.content,
                    dc.metadata,
                    d.filename,
                    d.source_type,
                    d.source_url,
                    1 - (dc.embedding <=> :embedding::vector) as similarity
                FROM document_chunks dc
                JOIN documents d ON dc.document_id = d.id
                WHERE 1 - (dc.embedding <=> :embedding::vector) > :threshold
                ORDER BY dc.embedding <=> :embedding::vector
                LIMIT :limit
            """)

            result = await db.execute(
                query,
                {
                    "embedding": embedding_str,
                    "threshold": threshold,
                    "limit": top_k
                }
            )

            chunks = []
            for row in result:
                chunks.append({
                    'id': str(row.id),
                    'document_id': str(row.document_id),
                    'content': row.content,
                    'metadata': row.metadata,
                    'filename': row.filename,
                    'source_type': row.source_type,
                    'source_url': row.source_url,
                    'similarity': float(row.similarity)
                })

            return chunks

        except Exception as e:
            logger.error(f"Error searching similar chunks: {e}")
            raise


# Singleton instance
document_service = DocumentService()
