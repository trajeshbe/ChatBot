"""
Multi-Channel Content Processor with Full Traceability

For a single document, processes content through multiple channels:
- Text Channel → Text embeddings
- Visual Channel → CLIP embeddings
- Table Channel → Table embeddings
- Code Channel → CodeBERT embeddings

Each chunk maintains traceability:
Document A → Chunk 1 → Multiple embeddings (text, visual, table)

Traceability Structure:
{
    "document_id": "uuid",
    "chunk_id": "uuid",
    "chunk_index": 1,
    "content": "text content",
    "embeddings": {
        "text": {
            "vector": [384-dim],
            "model": "all-MiniLM-L6-v2",
            "confidence": 0.95,
            "source": "text_extraction"
        },
        "visual": {
            "vector": [512-dim],
            "model": "clip-vit-base-patch32",
            "confidence": 0.85,
            "source": "page_screenshot",
            "page_num": 1,
            "coordinates": [x, y, w, h]
        },
        "table": {
            "vector": [512-dim],
            "model": "table-transformer",
            "confidence": 0.9,
            "source": "table_extraction",
            "table_index": 0
        }
    },
    "metadata": {
        "channels_processed": ["text", "visual"],
        "primary_channel": "visual",
        "processing_timestamp": "2025-12-02T12:00:00Z"
    }
}
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)


class ChannelType:
    """Processing channel types"""
    TEXT = "text"
    VISUAL = "visual"
    TABLE = "table"
    CODE = "code"
    NUMERICAL = "numerical"


class ChunkEmbedding:
    """
    Single embedding for a chunk

    Maintains full traceability: which model, which source, confidence
    """
    def __init__(
        self,
        channel: str,
        vector: np.ndarray,
        model: str,
        confidence: float,
        source: str,
        metadata: Dict[str, Any] = None
    ):
        self.channel = channel
        self.vector = vector
        self.model = model
        self.confidence = confidence
        self.source = source
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "channel": self.channel,
            "vector": self.vector.tolist() if isinstance(self.vector, np.ndarray) else self.vector,
            "model": self.model,
            "confidence": self.confidence,
            "source": self.source,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }


class TraceableChunk:
    """
    A document chunk with multiple embeddings and full traceability

    Document A → Chunk 1 → [Text Embedding, Visual Embedding, Table Embedding]
    """
    def __init__(
        self,
        document_id: str,
        chunk_index: int,
        content: str,
        source_info: Dict[str, Any]
    ):
        self.document_id = document_id
        self.chunk_index = int  # Unique chunk identifier
        self.content = content
        self.source_info = source_info  # Original source (page, coordinates, etc.)

        # Multiple embeddings per chunk
        self.embeddings: Dict[str, ChunkEmbedding] = {}

        # Metadata
        self.channels_processed = []
        self.primary_channel = None
        self.processing_timestamp = datetime.utcnow().isoformat()

    def add_embedding(
        self,
        channel: str,
        vector: np.ndarray,
        model: str,
        confidence: float,
        source: str,
        metadata: Dict[str, Any] = None
    ):
        """Add an embedding to this chunk"""
        embedding = ChunkEmbedding(
            channel=channel,
            vector=vector,
            model=model,
            confidence=confidence,
            source=source,
            metadata=metadata
        )

        self.embeddings[channel] = embedding

        if channel not in self.channels_processed:
            self.channels_processed.append(channel)

        # Set primary channel (highest confidence)
        if self.primary_channel is None or confidence > self.embeddings[self.primary_channel].confidence:
            self.primary_channel = channel

    def get_embedding(self, channel: str) -> Optional[ChunkEmbedding]:
        """Get embedding for specific channel"""
        return self.embeddings.get(channel)

    def get_primary_embedding(self) -> Optional[ChunkEmbedding]:
        """Get primary (highest confidence) embedding"""
        if self.primary_channel:
            return self.embeddings.get(self.primary_channel)
        return None

    def get_all_embeddings(self) -> Dict[str, ChunkEmbedding]:
        """Get all embeddings for consolidation"""
        return self.embeddings

    def to_database_format(self) -> Dict[str, Any]:
        """
        Convert to database format

        Stores embeddings in appropriate columns with full traceability metadata
        """
        result = {
            "document_id": self.document_id,
            "chunk_index": self.chunk_index,
            "content": self.content,
            "source_info": self.source_info,

            # Vector columns (one per channel)
            "embedding": None,
            "visual_embedding": None,
            "table_embedding": None,
            "code_embedding": None,
            "numerical_embedding": None,

            # Traceability metadata
            "embedding_metadata": {
                "channels_processed": self.channels_processed,
                "primary_channel": self.primary_channel,
                "processing_timestamp": self.processing_timestamp,
                "embeddings_detail": {}
            }
        }

        # Populate vector columns
        for channel, embedding in self.embeddings.items():
            if channel == ChannelType.TEXT:
                result["embedding"] = embedding.vector
                result["embedding_metadata"]["embeddings_detail"]["text"] = {
                    "model": embedding.model,
                    "confidence": embedding.confidence,
                    "source": embedding.source,
                    "metadata": embedding.metadata
                }
            elif channel == ChannelType.VISUAL:
                result["visual_embedding"] = embedding.vector
                result["embedding_metadata"]["embeddings_detail"]["visual"] = {
                    "model": embedding.model,
                    "confidence": embedding.confidence,
                    "source": embedding.source,
                    "metadata": embedding.metadata
                }
            elif channel == ChannelType.TABLE:
                result["table_embedding"] = embedding.vector
                result["embedding_metadata"]["embeddings_detail"]["table"] = {
                    "model": embedding.model,
                    "confidence": embedding.confidence,
                    "source": embedding.source,
                    "metadata": embedding.metadata
                }
            elif channel == ChannelType.CODE:
                result["code_embedding"] = embedding.vector
                result["embedding_metadata"]["embeddings_detail"]["code"] = {
                    "model": embedding.model,
                    "confidence": embedding.confidence,
                    "source": embedding.source,
                    "metadata": embedding.metadata
                }
            elif channel == ChannelType.NUMERICAL:
                result["numerical_embedding"] = embedding.vector
                result["embedding_metadata"]["embeddings_detail"]["numerical"] = {
                    "model": embedding.model,
                    "confidence": embedding.confidence,
                    "source": embedding.source,
                    "metadata": embedding.metadata
                }

        return result

    def __repr__(self):
        return f"TraceableChunk(doc={self.document_id[:8]}, chunk={self.chunk_index}, channels={self.channels_processed})"


class MultiChannelProcessor:
    """
    Multi-channel content processor with full traceability

    Processes document through multiple channels and maintains complete
    traceability of all embeddings.
    """

    def __init__(self):
        """Initialize multi-channel processor"""
        self.channels_enabled = {
            ChannelType.TEXT: True,      # Always enabled
            ChannelType.VISUAL: True,    # ✅ ENABLED! CLIP processing for image-heavy PDFs
            ChannelType.TABLE: False,    # Enable when table model available
            ChannelType.CODE: False,     # Enable when CodeBERT available
            ChannelType.NUMERICAL: False # Enable when numerical model available
        }

        logger.info(f"MultiChannelProcessor initialized. Enabled channels: {[k for k, v in self.channels_enabled.items() if v]}")

    async def process_document(
        self,
        document_id: str,
        file_path: str,
        content_classification: Dict[str, Any],
        text_chunks: List[Dict[str, Any]]
    ) -> List[TraceableChunk]:
        """
        Process document through multiple channels

        Args:
            document_id: Document UUID
            file_path: Path to document file
            content_classification: Result from multi-analyzer ensemble
            text_chunks: Already extracted text chunks

        Returns:
            List[TraceableChunk]: Chunks with multiple embeddings
        """

        content_type = content_classification.get("content_type")
        logger.info(f"🔄 Multi-channel processing for document {document_id[:8]} (type: {content_type})")

        # Determine which channels to process based on content type
        channels_to_process = self._determine_channels(content_classification)

        logger.info(f"📡 Processing channels: {channels_to_process}")

        # Create traceable chunks
        traceable_chunks = []

        if text_chunks:
            # Text-based chunks
            for i, text_chunk in enumerate(text_chunks):
                chunk = TraceableChunk(
                    document_id=document_id,
                    chunk_index=i,
                    content=text_chunk['content'],
                    source_info={
                        "page": text_chunk.get('page', None),
                        "start": text_chunk.get('start', 0),
                        "end": text_chunk.get('end', 0)
                    }
                )
                traceable_chunks.append(chunk)
        elif ChannelType.VISUAL in channels_to_process:
            # Visual-only document (no text extracted)
            # Create synthetic chunks for visual content
            logger.info(f"📄 Visual-only document detected - creating synthetic chunks for visual content")
            import fitz  # PyMuPDF
            try:
                doc = fitz.open(file_path)
                num_pages = len(doc)
                doc.close()

                for page_num in range(num_pages):
                    chunk = TraceableChunk(
                        document_id=document_id,
                        chunk_index=page_num,
                        content=f"[Visual content from page {page_num + 1}]",
                        source_info={
                            "page": page_num + 1,
                            "start": 0,
                            "end": 0,
                            "synthetic": True
                        }
                    )
                    traceable_chunks.append(chunk)
                logger.info(f"✅ Created {len(traceable_chunks)} synthetic chunks for visual-only document")
            except Exception as e:
                logger.warning(f"Failed to create synthetic chunks: {e}")

        # Process each channel
        # Always process text channel if enabled (even for synthetic chunks in visual-only documents)
        if ChannelType.TEXT in channels_to_process and traceable_chunks:
            await self._process_text_channel(traceable_chunks, text_chunks)

        if ChannelType.VISUAL in channels_to_process:
            await self._process_visual_channel(traceable_chunks, file_path)

        if ChannelType.TABLE in channels_to_process:
            await self._process_table_channel(traceable_chunks, file_path)

        logger.info(f"✅ Multi-channel processing complete: {len(traceable_chunks)} chunks processed")

        return traceable_chunks

    def _determine_channels(self, content_classification: Dict[str, Any]) -> List[str]:
        """Determine which channels to process based on content type"""
        from app.services.multi_analyzer_ensemble import ContentType as ContentTypeEnum

        content_type = content_classification.get("content_type")

        # Convert to string for comparison if it's an enum
        content_type_str = content_type.value if hasattr(content_type, 'value') else str(content_type)

        channels = [ChannelType.TEXT]  # Always process text

        # Add visual channel for image-heavy, scanned, or vector graphics
        # SCANNED documents often have visual content (diagrams, photos) that needs CLIP indexing
        if content_type_str in ["image_heavy", "vector_graphics", "mixed", "scanned"]:
            if self.channels_enabled[ChannelType.VISUAL]:
                channels.append(ChannelType.VISUAL)

        # Add table channel for table-heavy
        if content_type_str in ["table_heavy", "numerical", "mixed"]:
            if self.channels_enabled[ChannelType.TABLE]:
                channels.append(ChannelType.TABLE)

        # Add code channel for code
        if content_type_str == "code":
            if self.channels_enabled[ChannelType.CODE]:
                channels.append(ChannelType.CODE)

        return channels

    async def _process_text_channel(
        self,
        chunks: List[TraceableChunk],
        text_chunks: List[Dict[str, Any]]
    ):
        """Process text channel (generate text embeddings)"""
        from app.services.embedding_service import embedding_service

        logger.info(f"📝 Processing text channel for {len(chunks)} chunks...")

        # Extract text content
        texts = [chunk.content for chunk in chunks]

        # Generate embeddings
        embeddings = await embedding_service.get_embeddings_batch(texts)

        # Add to traceable chunks
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            chunk.add_embedding(
                channel=ChannelType.TEXT,
                vector=embedding,
                model="sentence-transformers/all-MiniLM-L6-v2",
                confidence=0.95,
                source="text_extraction",
                metadata={
                    "text_length": len(chunk.content),
                    "chunk_index": i
                }
            )

        logger.info(f"✅ Text channel complete: {len(chunks)} embeddings generated")

    async def _process_visual_channel(
        self,
        chunks: List[TraceableChunk],
        file_path: str
    ):
        """
        Process visual channel (generate CLIP embeddings from page screenshots)

        Extracts images from PDF pages and generates CLIP embeddings for visual content.
        This enables text-to-image search (e.g., "show me photos of construction site")
        """
        import os
        from pathlib import Path

        logger.info(f"🎨 Processing visual channel for {file_path}...")

        # Only process PDFs for now
        if not file_path.lower().endswith('.pdf'):
            logger.info(f"   Skipping visual channel: Only PDF files supported (got: {Path(file_path).suffix})")
            return

        try:
            # Import services
            from app.services.intelligent_embedding_service import intelligent_embedding_service
            import fitz  # PyMuPDF

            # Initialize intelligent embedding service if needed
            if not intelligent_embedding_service._initialized:
                await intelligent_embedding_service.initialize()

            # Convert PDF pages to images
            logger.info(f"   📄 Converting PDF to images...")
            doc = fitz.open(file_path)
            image_paths = []

            output_dir = "/tmp"
            pdf_name = Path(file_path).stem

            for page_num in range(len(doc)):
                page = doc[page_num]

                # Render page at 150 DPI (balanced quality/performance)
                mat = fitz.Matrix(150/72, 150/72)
                pix = page.get_pixmap(matrix=mat)

                # Save as PNG
                image_path = f"{output_dir}/{pdf_name}_clip_page_{page_num + 1}.png"
                pix.save(image_path)
                image_paths.append(image_path)

            doc.close()
            logger.info(f"   ✅ Converted {len(image_paths)} pages to images")

            if not image_paths:
                logger.warning(f"   ⚠️  No images extracted from PDF")
                return

            # Generate CLIP embeddings for all pages
            logger.info(f"   🧠 Generating CLIP embeddings for {len(image_paths)} pages...")
            visual_embeddings = await intelligent_embedding_service._embed_visual(image_paths)

            logger.info(f"   ✅ Generated {len(visual_embeddings)} visual embeddings (512-dim)")

            # Distribute visual embeddings across chunks
            # Strategy: Assign page embeddings to chunks based on page distribution
            if len(chunks) <= len(visual_embeddings):
                # More pages than chunks: Assign each chunk the embedding of its corresponding page
                # Assumes chunks are roughly evenly distributed across pages
                for i, chunk in enumerate(chunks):
                    # Map chunk index to page number (proportional distribution)
                    page_index = int((i / len(chunks)) * len(visual_embeddings))
                    page_index = min(page_index, len(visual_embeddings) - 1)

                    chunk.add_embedding(
                        channel=ChannelType.VISUAL,
                        vector=np.array(visual_embeddings[page_index]),
                        model="openai/clip-vit-base-patch32",
                        confidence=0.85,
                        source="page_screenshot",
                        metadata={
                            "page_num": page_index + 1,
                            "total_pages": len(visual_embeddings),
                            "image_path": image_paths[page_index]
                        }
                    )
            else:
                # More chunks than pages: Assign page embeddings to multiple chunks
                chunks_per_page = len(chunks) // len(visual_embeddings)

                for i, chunk in enumerate(chunks):
                    page_index = min(i // max(chunks_per_page, 1), len(visual_embeddings) - 1)

                    chunk.add_embedding(
                        channel=ChannelType.VISUAL,
                        vector=np.array(visual_embeddings[page_index]),
                        model="openai/clip-vit-base-patch32",
                        confidence=0.85,
                        source="page_screenshot",
                        metadata={
                            "page_num": page_index + 1,
                            "total_pages": len(visual_embeddings),
                            "image_path": image_paths[page_index]
                        }
                    )

            # Clean up temporary image files
            for img_path in image_paths:
                try:
                    if os.path.exists(img_path):
                        os.remove(img_path)
                except Exception as e:
                    logger.warning(f"Failed to clean up temp image {img_path}: {e}")

            logger.info(f"   ✅ Visual channel complete: {len(chunks)} chunks with CLIP embeddings")

        except Exception as e:
            logger.error(f"❌ Visual channel processing failed: {e}", exc_info=True)
            logger.info("   Continuing without visual embeddings")
            # Don't raise - allow document processing to continue with text-only

    async def _process_table_channel(
        self,
        chunks: List[TraceableChunk],
        file_path: str
    ):
        """Process table channel (generate table embeddings)"""
        logger.info(f"📊 Table channel processing not yet implemented")
        # Future: Extract tables, generate specialized embeddings
        # For now, skip


# Global singleton
multi_channel_processor = MultiChannelProcessor()
