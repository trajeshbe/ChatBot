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
import time

# Tool usage tracking
try:
    from app.services.tool_usage_tracker import tool_tracker, ToolCategory
    from app.core.database import AsyncSessionLocal
    TOOL_TRACKING_ENABLED = True
except ImportError:
    TOOL_TRACKING_ENABLED = False
    logging.warning("Tool usage tracking not available")

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


def sanitize_path_component(component: str) -> str:
    """
    Remove dangerous characters from path components for safe MinIO paths

    Args:
        component: Raw path component (e.g., "DevOps Team")

    Returns:
        Sanitized component (e.g., "DevOps-Team")
    """
    if not component:
        return ""

    # Replace spaces with hyphens
    sanitized = component.replace(" ", "-")

    # Remove dangerous characters: / \ : * ? " < > | and ..
    sanitized = re.sub(r'[/\\:*?"<>|]', '', sanitized)
    sanitized = sanitized.replace('..', '')

    return sanitized.strip()


def construct_minio_path(
    department: Optional[str],
    team: Optional[str],
    username: str,
    project: str,
    filename: str,
    folder: str = "documents"
) -> str:
    """
    Construct hierarchical MinIO path for file organization

    Format: {department}/{team}/{project}/{username}/{folder}/{filename}
    Example: Technology/Tech-Team-1/Construction-Intelligence/admin/documents/blueprint.pdf

    Args:
        department: Department name (or None → "Unassigned")
        team: Team name (or None → "General")
        username: Username
        project: Project name (defaults to "Global" in caller)
        filename: Original filename (preserved as-is)
        folder: Folder type (documents, extractions, exports, temp)

    Returns:
        Full MinIO path
    """
    # Valid folder types
    VALID_FOLDERS = ['documents', 'extractions', 'exports', 'temp']

    # Sanitize organizational components
    safe_dept = sanitize_path_component(department) if department else "Unassigned"
    safe_team = sanitize_path_component(team) if team else "General"
    safe_project = sanitize_path_component(project) if project else "Global"
    safe_username = sanitize_path_component(username) if username else "anonymous"
    safe_folder = folder if folder in VALID_FOLDERS else "documents"

    # DON'T sanitize filename - preserve original name
    # MinIO/S3 handles special chars in filenames

    # Construct path: dept/team/project/user/folder/file
    return f"{safe_dept}/{safe_team}/{safe_project}/{safe_username}/{safe_folder}/{filename}"


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
        session_id: Optional[str] = None,
        db: AsyncSession = None,
        user_id: Optional[uuid.UUID] = None,
        department: Optional[str] = None,
        team: Optional[str] = None,
        project_id: Optional[uuid.UUID] = None,
        minio_path: Optional[str] = None,
        user_role: Optional[str] = None
    ) -> Document:
        """
        Upload file to MinIO and create database record

        Args:
            file_data: File bytes
            filename: Original filename
            file_type: MIME type
            source_type: "upload" or "scrape"
            source_url: Source URL if scraped
            session_id: Chat session ID
            db: Database session
            user_id: Uploading user ID
            department: User's department
            team: User's team
            project_id: Project ID
            minio_path: Hierarchical MinIO path (dept/team/user/project/file)
        """
        if not self._initialized:
            await self.initialize()

        try:
            # Generate unique file path
            file_id = str(uuid.uuid4())
            file_extension = Path(filename).suffix
            object_name = f"{file_id}{file_extension}"

            # Use organizational path if provided, otherwise fall back to UUID
            final_object_name = minio_path if minio_path else object_name

            # Upload to MinIO
            self.minio_client.put_object(
                settings.MINIO_BUCKET_NAME,
                final_object_name,
                io.BytesIO(file_data),
                length=len(file_data),
                content_type=file_type
            )

            logger.info(f"Uploaded file to MinIO: {final_object_name}")
            if minio_path:
                logger.info(f"📁 Organizational path: {minio_path}")

            # Create database record with organizational metadata
            document = Document(
                id=uuid.UUID(file_id),
                filename=filename,
                file_path=object_name,  # Keep UUID for backward compatibility
                minio_path=minio_path,  # Store hierarchical path
                file_type=file_type,
                file_size=len(file_data),
                source_type=source_type,
                source_url=source_url,
                processing_status='pending',  # Fixed: was 'processed'
                uploaded_by=user_id,
                department=department,
                team=team,
                user_role=user_role,  # Add user role
                project_id=project_id  # Added: link to project
            )

            if db:
                db.add(document)
                await db.flush()  # Flush to get ID without committing
                await db.refresh(document)

                # Associate with session if session_id provided
                if session_id:
                    try:
                        from app.models.database_enhanced import SessionDocument
                        session_doc = SessionDocument(
                            session_id=uuid.UUID(session_id) if isinstance(session_id, str) else session_id,
                            document_id=document.id
                        )
                        db.add(session_doc)
                        await db.flush()
                        logger.info(f"Associated document {document.id} with session {session_id}")
                    except Exception as e:
                        # Log warning but don't fail the upload
                        logger.warning(f"Could not associate document with session {session_id}: {e}")

            return document

        except Exception as e:
            logger.error(f"Error uploading file: {e}")
            raise

    def _get_processor_name(self, file_type: str, filename: str) -> str:
        """Get the name of the processor tool used for a file type"""
        if file_type == "application/pdf" or filename.endswith('.pdf'):
            return "pypdf2"
        elif filename.endswith('.docx'):
            return "python_docx"
        elif filename.endswith('.pptx'):
            return "python_pptx"
        elif filename.endswith('.json'):
            return "json_parser"
        elif filename.endswith('.md'):
            return "markdown_parser"
        else:
            return "text_parser"

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
        db: AsyncSession,
        user_id: Optional[uuid.UUID] = None,
        department: Optional[str] = None,
        team: Optional[str] = None,
        project_id: Optional[uuid.UUID] = None
    ) -> List[DocumentChunk]:
        """
        Process document and create embeddings

        Args:
            document_id: Document UUID
            db: Database session
            user_id: Uploading user ID
            department: User's department
            team: User's team
            project_id: Project ID
        """
        if not self._initialized:
            await self.initialize()

        try:
            # Get document from database
            result = await db.execute(select(Document).where(Document.id == document_id))
            document = result.scalar_one_or_none()

            if not document:
                raise ValueError(f"Document not found: {document_id}")

            # Download file from MinIO (use minio_path if available, fallback to file_path)
            object_key = document.minio_path if document.minio_path else document.file_path
            logger.info(f"Retrieving file from MinIO: {object_key}")

            response = self.minio_client.get_object(
                settings.MINIO_BUCKET_NAME,
                object_key
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
                    start_time = time.time()
                    result = self.doc_converter.convert(temp_path)
                    text = result.document.export_to_markdown()
                    processing_time = (time.time() - start_time) * 1000

                    # Track Docling usage
                    if TOOL_TRACKING_ENABLED:
                        try:
                            async with AsyncSessionLocal() as track_db:
                                await tool_tracker.record_tool_usage(
                                    category=ToolCategory.DOCUMENT_PROCESSING,
                                    tool_name="docling",
                                    operation="parse_document",
                                    db=track_db,
                                    session_id=None,
                                    success=True,
                                    latency_ms=processing_time,
                                    input_size=len(file_data),
                                    output_size=len(text),
                                    metadata={
                                        'file_type': document.file_type,
                                        'filename': document.filename
                                    }
                                )
                                await track_db.commit()
                        except Exception as track_err:
                            logger.warning(f"Failed to track Docling usage: {track_err}")

                    # Clean up
                    os.remove(temp_path)
                except Exception as e:
                    logger.warning(f"Docling processing failed, using fallback: {e}")
                    start_time = time.time()
                    text = self._extract_text_fallback(file_data, document.file_type, document.filename)
                    processing_time = (time.time() - start_time) * 1000

                    # Track fallback processor usage
                    if TOOL_TRACKING_ENABLED:
                        tool_name = self._get_processor_name(document.file_type, document.filename)
                        try:
                            async with AsyncSessionLocal() as track_db:
                                await tool_tracker.record_tool_usage(
                                    category=ToolCategory.DOCUMENT_PROCESSING,
                                    tool_name=tool_name,
                                    operation="parse_document",
                                    db=track_db,
                                    session_id=None,
                                    success=True,
                                    latency_ms=processing_time,
                                    input_size=len(file_data),
                                    output_size=len(text),
                                    metadata={'file_type': document.file_type, 'filename': document.filename}
                                )
                                await track_db.commit()
                        except Exception as track_err:
                            logger.warning(f"Failed to track fallback processor usage: {track_err}")
            else:
                start_time = time.time()
                text = self._extract_text_fallback(file_data, document.file_type, document.filename)
                processing_time = (time.time() - start_time) * 1000

                # Track fallback processor usage
                if TOOL_TRACKING_ENABLED:
                    tool_name = self._get_processor_name(document.file_type, document.filename)
                    try:
                        async with AsyncSessionLocal() as track_db:
                            await tool_tracker.record_tool_usage(
                                category=ToolCategory.DOCUMENT_PROCESSING,
                                tool_name=tool_name,
                                operation="parse_document",
                                db=track_db,
                                session_id=None,
                                success=True,
                                latency_ms=processing_time,
                                input_size=len(file_data),
                                output_size=len(text),
                                metadata={'file_type': document.file_type, 'filename': document.filename}
                            )
                            await track_db.commit()
                    except Exception as track_err:
                        logger.warning(f"Failed to track fallback processor usage: {track_err}")

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
                    },
                    project_id=project_id,
                    uploaded_by=user_id,
                    department=department,
                    team=team
                )
                db.add(chunk_record)
                document_chunks.append(chunk_record)

            # Mark document as processed
            document.processing_status = 'completed'
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
        use_hybrid: bool = True,
        use_cascading_fallback: bool = True,
        semantic_weight: Optional[float] = None,
        keyword_weight: Optional[float] = None,
        project_id: Optional[str] = None  # Filter by project
    ) -> List[Dict]:
        """
        Search for similar document chunks using robust hybrid search with cascading fallback:
        1. Vector similarity search (semantic)
        2. Keyword matching (lexical) - optional
        3. Combined reranking for better results
        4. Cascading fallback with progressively lower thresholds if no results

        Args:
            query_embedding: Vector embedding of the query
            top_k: Number of results to return
            threshold: Initial similarity threshold
            db: Database session
            query_text: Original query text for keyword matching
            use_hybrid: Enable hybrid search (semantic + keyword)
            use_cascading_fallback: Enable cascading fallback with lower thresholds
            semantic_weight: Weight for semantic similarity (0-1), defaults to config setting
            keyword_weight: Weight for keyword matching (0-1), defaults to config setting
        """
        from sqlalchemy import text as sql_text, select, func
        from app.models.database import DocumentChunk

        try:
            # Use config defaults if weights not provided
            _semantic_weight = semantic_weight if semantic_weight is not None else settings.SEMANTIC_WEIGHT
            _keyword_weight = keyword_weight if keyword_weight is not None else settings.KEYWORD_WEIGHT

            # Validate weights sum to 1.0 (with small tolerance for floating point)
            weight_sum = _semantic_weight + _keyword_weight
            if not (0.99 <= weight_sum <= 1.01):
                logger.warning(f"Semantic ({_semantic_weight}) + Keyword ({_keyword_weight}) weights don't sum to 1.0 (sum={weight_sum:.3f}). Normalizing...")
                # Normalize to ensure they sum to 1.0
                total = _semantic_weight + _keyword_weight
                _semantic_weight = _semantic_weight / total
                _keyword_weight = _keyword_weight / total

            logger.debug(f"Using hybrid weights: semantic={_semantic_weight:.2f}, keyword={_keyword_weight:.2f}")
            # First check if there are any document chunks at all
            count_query = select(func.count()).select_from(DocumentChunk)
            count_result = await db.execute(count_query)
            chunk_count = count_result.scalar()

            if chunk_count == 0:
                logger.warning("❌ No document chunks found in database")
                return []

            # Check chunks with embeddings
            embedding_count_query = select(func.count()).select_from(DocumentChunk).where(
                DocumentChunk.embedding.isnot(None)
            )
            embedding_count_result = await db.execute(embedding_count_query)
            embedding_count = embedding_count_result.scalar()

            if embedding_count == 0:
                logger.error(f"❌ No embeddings found! {chunk_count} chunks exist but none have embeddings")
                return []

            logger.info(f"📊 Database status: {chunk_count} total chunks, {embedding_count} with embeddings")

            # Cascading fallback strategy: try multiple thresholds
            # Conservative approach to avoid irrelevant results
            thresholds_to_try = [threshold]
            if use_cascading_fallback:
                # Add only ONE fallback level to minimum threshold
                # This prevents too many low-quality matches
                if settings.MIN_SIMILARITY_THRESHOLD < threshold:
                    thresholds_to_try.append(settings.MIN_SIMILARITY_THRESHOLD)
                # Remove duplicates and sort descending
                thresholds_to_try = sorted(list(set(thresholds_to_try)), reverse=True)
                logger.info(f"🔄 Cascading fallback enabled: will try thresholds {[f'{t:.0%}' for t in thresholds_to_try]}")

            chunks = []
            threshold_used = threshold

            for current_threshold in thresholds_to_try:
                if current_threshold < 0:
                    continue

                logger.info(f"🔍 Searching with threshold={current_threshold:.2f}, hybrid={use_hybrid}")

                chunks = await self._execute_search(
                    query_embedding=query_embedding,
                    query_text=query_text,
                    threshold=current_threshold,
                    top_k=top_k,
                    use_hybrid=use_hybrid,
                    semantic_weight=_semantic_weight,
                    keyword_weight=_keyword_weight,
                    project_id=project_id,
                    db=db
                )

                if chunks:
                    threshold_used = current_threshold
                    logger.info(f"✅ Found {len(chunks)} chunks with threshold={current_threshold:.2f}")
                    break
                else:
                    logger.warning(f"⚠️ No results with threshold={current_threshold:.2f}, trying lower threshold...")

            # Final fallback: pure keyword search (if query_text provided and still no results)
            if not chunks and query_text and use_hybrid:
                logger.info("🔍 Final fallback: trying pure keyword search...")
                chunks = await self._keyword_only_search(query_text, top_k, project_id, db)
                if chunks:
                    logger.info(f"✅ Found {len(chunks)} chunks with keyword-only search")
                    # Add low semantic scores for keyword-only results
                    for chunk in chunks:
                        chunk['semantic_score'] = 0.1
                        chunk['combined_score'] = chunk.get('keyword_score', 0.5)
                        chunk['similarity'] = chunk['combined_score']

            if chunks:
                # Diversify results - avoid too many chunks from same document
                chunks = self._diversify_chunks(chunks, top_k)
                logger.info(f"📄 Final result: {len(chunks)} chunks from {len(set(c['filename'] for c in chunks))} documents")
            else:
                logger.warning(f"❌ No relevant chunks found after all fallback strategies (total chunks in DB: {chunk_count}, with embeddings: {embedding_count})")

            return chunks

        except Exception as e:
            logger.error(f"❌ Error searching similar chunks: {e}", exc_info=True)
            # Rollback transaction on error to prevent "transaction aborted" state
            await db.rollback()
            # Return empty list instead of raising to allow graceful degradation
            return []

    async def _execute_search(
        self,
        query_embedding: List[float],
        query_text: Optional[str],
        threshold: float,
        top_k: int,
        use_hybrid: bool,
        semantic_weight: float,
        keyword_weight: float,
        project_id: Optional[str],
        db: AsyncSession
    ) -> List[Dict]:
        """
        Execute a single search with given parameters.

        SECURITY: Uses parameterized queries to prevent SQL injection.
        WEIGHTS: Configurable semantic/keyword weights for robust retrieval.
        Default: 80% semantic, 20% keyword for better semantic matching.

        Args:
            semantic_weight: Weight for vector similarity (0-1)
            keyword_weight: Weight for keyword matching (0-1)
        """
        from sqlalchemy import text as sql_text

        try:
            # Convert embedding to PostgreSQL vector format string
            embedding_str = f"[{','.join(map(str, query_embedding))}]"

            # Hybrid search: combine semantic and keyword search
            if use_hybrid and query_text:
                # Extract keywords from query for keyword matching
                keywords = self._extract_keywords(query_text)
                if not keywords:
                    # If no keywords extracted, fall back to semantic only
                    return await self._execute_search(
                        query_embedding, None, threshold, top_k, False,
                        semantic_weight, keyword_weight, project_id, db
                    )

                # SECURITY FIX: Sanitize keywords to prevent SQL injection
                sanitized_keywords = [self._sanitize_keyword(kw) for kw in keywords]
                sanitized_keywords = [kw for kw in sanitized_keywords if kw]  # Remove empty

                if not sanitized_keywords:
                    # If all keywords were filtered out, fall back to semantic only
                    logger.warning("All keywords filtered out during sanitization, using semantic search only")
                    return await self._execute_search(
                        query_embedding, None, threshold, top_k, False,
                        semantic_weight, keyword_weight, project_id, db
                    )

                # Build parameterized keyword conditions (SAFE from SQL injection)
                keyword_conditions = " OR ".join([f"dc.content ILIKE :keyword_{i}" for i in range(len(sanitized_keywords))])

                logger.debug(f"Keywords extracted: {sanitized_keywords}")
                logger.debug(f"Using weights: semantic={semantic_weight:.2f}, keyword={keyword_weight:.2f}")

                # Hybrid query with both semantic and keyword matching
                # CONFIGURABLE WEIGHTS: Default 80% semantic, 20% keyword (can be overridden)
                # This fixes the issue where good semantic matches (0.56) were filtered out
                # due to low combined scores with old weights (0.56 * 0.6 = 0.336 < threshold 0.35)
                # Build WHERE clause with optional project filter
                project_filter = ""
                if project_id:
                    project_filter = "AND d.project_id = :project_id"

                query = sql_text(f"""
                    WITH semantic_search AS (
                        SELECT
                            dc.id,
                            dc.document_id,
                            dc.content,
                            dc.meta_info::jsonb as meta_info,
                            d.filename,
                            d.source_type,
                            d.source_url,
                            1 - (dc.embedding <=> '{embedding_str}'::vector) as semantic_score
                        FROM document_chunks dc
                        JOIN documents d ON dc.document_id = d.id
                        WHERE dc.embedding IS NOT NULL {project_filter}
                    ),
                    keyword_search AS (
                        SELECT
                            id,
                            CASE
                                WHEN ({keyword_conditions}) THEN 1.0
                                ELSE 0.0
                            END as keyword_score
                        FROM document_chunks dc
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
                        (ss.semantic_score * {semantic_weight} + COALESCE(ks.keyword_score, 0) * {keyword_weight}) as combined_score
                    FROM semantic_search ss
                    LEFT JOIN keyword_search ks ON ss.id = ks.id
                    WHERE (ss.semantic_score * {semantic_weight} + COALESCE(ks.keyword_score, 0) * {keyword_weight}) > :threshold
                    ORDER BY combined_score DESC
                    LIMIT :limit
                """)
            else:
                # Standard semantic search only
                # Build WHERE clause with optional project filter
                project_filter = ""
                if project_id:
                    project_filter = "AND d.project_id = :project_id"

                query = sql_text(f"""
                    SELECT
                        dc.id,
                        dc.document_id,
                        dc.content,
                        dc.meta_info::jsonb as meta_info,
                        d.filename,
                        d.source_type,
                        d.source_url,
                        1 - (dc.embedding <=> '{embedding_str}'::vector) as semantic_score,
                        0.0 as keyword_score,
                        1 - (dc.embedding <=> '{embedding_str}'::vector) as combined_score
                    FROM document_chunks dc
                    JOIN documents d ON dc.document_id = d.id
                    WHERE dc.embedding IS NOT NULL
                        {project_filter}
                        AND 1 - (dc.embedding <=> '{embedding_str}'::vector) > :threshold
                    ORDER BY dc.embedding <=> '{embedding_str}'::vector
                    LIMIT :limit
                """)

            # Build parameters dictionary
            params = {
                "threshold": threshold,
                "limit": top_k * 2  # Get more results for better diversity
            }

            # Add project_id if provided
            if project_id:
                params["project_id"] = project_id

            # Add keyword parameters if using hybrid search (SECURITY: Parameterized queries)
            if use_hybrid and query_text and 'sanitized_keywords' in locals():
                for i, keyword in enumerate(sanitized_keywords):
                    params[f"keyword_{i}"] = f"%{keyword}%"

            result = await db.execute(query, params)

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

            return chunks

        except Exception as e:
            logger.error(f"Error in _execute_search: {e}", exc_info=True)
            await db.rollback()
            return []

    async def _keyword_only_search(
        self,
        query_text: str,
        top_k: int,
        project_id: Optional[str],
        db: AsyncSession
    ) -> List[Dict]:
        """
        Pure keyword search as final fallback when semantic search fails
        """
        from sqlalchemy import text as sql_text

        try:
            keywords = self._extract_keywords(query_text)
            if not keywords:
                return []

            # Build ILIKE conditions for each keyword
            keyword_conditions = [f"dc.content ILIKE :kw{i}" for i in range(len(keywords))]
            keyword_clause = " OR ".join(keyword_conditions)

            # Build project filter
            project_filter = ""
            if project_id:
                project_filter = "AND d.project_id = :project_id"

            query = sql_text(f"""
                SELECT
                    dc.id,
                    dc.document_id,
                    dc.content,
                    dc.meta_info::jsonb as meta_info,
                    d.filename,
                    d.source_type,
                    d.source_url
                FROM document_chunks dc
                JOIN documents d ON dc.document_id = d.id
                WHERE ({keyword_clause}) {project_filter}
                LIMIT :limit
            """)

            # Build parameters dict
            params = {f"kw{i}": f"%{kw}%" for i, kw in enumerate(keywords)}
            params["limit"] = top_k * 2

            # Add project_id if provided
            if project_id:
                params["project_id"] = project_id

            result = await db.execute(query, params)

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
                    'keyword_score': 1.0,
                    'search_type': 'keyword_only'
                })

            return chunks

        except Exception as e:
            logger.error(f"Error in keyword-only search: {e}", exc_info=True)
            await db.rollback()
            return []

    def _extract_keywords(self, text: str, max_keywords: int = 8) -> List[str]:
        """
        Extract important keywords from query text with improved extraction.
        Returns more keywords with better handling of names, acronyms, and important terms.
        """
        # Remove common stop words (expanded list)
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'what', 'which', 'who', 'when', 'where', 'why', 'how', 'can', 'could',
            'should', 'would', 'will', 'shall', 'may', 'might', 'must', 'do', 'does', 'did',
            'have', 'has', 'had', 'this', 'that', 'these', 'those', 'there', 'their',
            'them', 'they', 'about', 'after', 'before', 'between', 'into', 'through',
            'during', 'from', 'up', 'down', 'out', 'off', 'over', 'under', 'again',
            'further', 'then', 'once'
        }

        # Extract words and phrases
        # 1. Extract capitalized words (likely names, acronyms) - min 2 chars
        capitalized = re.findall(r'\b[A-Z][a-zA-Z0-9]{1,}\b', text)

        # 2. Extract all words (alphanumeric, min 2 chars for better coverage)
        words = re.findall(r'\b[a-zA-Z0-9]{2,}\b', text.lower())

        # 3. Extract quoted phrases (if any)
        quoted = re.findall(r'"([^"]+)"', text)
        quoted_words = []
        for phrase in quoted:
            quoted_words.extend(phrase.lower().split())

        # Combine all keywords
        all_keywords = []

        # Priority 1: Capitalized words (names, acronyms) - keep as-is
        for word in capitalized:
            if word.lower() not in stop_words:
                all_keywords.append(word)

        # Priority 2: Quoted words
        for word in quoted_words:
            if word not in stop_words and len(word) >= 2:
                all_keywords.append(word)

        # Priority 3: Regular words filtered by stop words
        for word in words:
            if word not in stop_words and word not in [k.lower() for k in all_keywords]:
                all_keywords.append(word)

        # Remove duplicates while preserving order (case-insensitive)
        seen = set()
        unique_keywords = []
        for kw in all_keywords:
            kw_lower = kw.lower()
            if kw_lower not in seen:
                seen.add(kw_lower)
                unique_keywords.append(kw)

        # Prioritize by:
        # 1. Capitalized words (likely names)
        # 2. Longer words (more specific)
        # 3. Words that appear in original case (not lowercased)
        def keyword_priority(kw):
            is_capitalized = kw[0].isupper() if kw else False
            return (
                1 if is_capitalized else 2,  # Capitalized first
                -len(kw),  # Longer words first
                kw.lower()  # Alphabetical for tie-breaking
            )

        unique_keywords.sort(key=keyword_priority)

        # Return top keywords
        result = unique_keywords[:max_keywords]
        logger.debug(f"Extracted keywords from '{text}': {result}")
        return result

    def _sanitize_keyword(self, keyword: str) -> str:
        """
        Sanitize keyword to prevent SQL injection.

        SECURITY: Only allows alphanumeric characters, spaces, hyphens, and underscores.
        Removes all other special characters that could be used for SQL injection.

        Args:
            keyword: Raw keyword string

        Returns:
            Sanitized keyword safe for SQL queries
        """
        if not keyword:
            return ""

        # Remove leading/trailing whitespace
        keyword = keyword.strip()

        # Only allow alphanumeric, spaces, hyphens, underscores
        # This prevents SQL injection characters: ', ", ;, --, /*, */, etc.
        sanitized = re.sub(r'[^a-zA-Z0-9\s\-_]', '', keyword)

        # Remove multiple spaces
        sanitized = ' '.join(sanitized.split())

        # Limit length to prevent abuse
        max_length = 50
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]

        return sanitized

    def _diversify_chunks(self, chunks: List[Dict], top_k: int) -> List[Dict]:
        """
        Diversify results to avoid too many chunks from the same document.
        Ensures we get variety in sources while maintaining quality.
        """
        if len(chunks) <= top_k:
            return chunks

        # Group by document
        from collections import defaultdict
        doc_chunks = defaultdict(list)
        for chunk in chunks:
            doc_chunks[chunk['document_id']].append(chunk)

        # Select diverse chunks with quality consideration
        diversified = []
        max_per_doc = max(2, top_k // len(doc_chunks))  # At least 2 per doc if we have few docs

        # First pass: add top chunk from each document (only if high quality)
        for doc_id, doc_chunk_list in doc_chunks.items():
            if len(diversified) < top_k:
                top_chunk = doc_chunk_list[0]
                # Only include if it meets minimum display quality
                if top_chunk.get('similarity', 0) >= settings.SOURCE_DISPLAY_THRESHOLD:
                    diversified.append(top_chunk)

        # Second pass: fill remaining slots with best chunks (maintaining quality)
        remaining = [
            c for c in chunks
            if c not in diversified and c.get('similarity', 0) >= settings.SOURCE_DISPLAY_THRESHOLD
        ]
        diversified.extend(remaining[:top_k - len(diversified)])

        # Sort by similarity descending to show best sources first
        diversified.sort(key=lambda x: x.get('similarity', 0), reverse=True)

        logger.info(f"🎯 Diversified to {len(diversified)} chunks from {len(set(c['document_id'] for c in diversified))} documents")

        return diversified[:top_k]


# Singleton instance
document_service = DocumentService()
