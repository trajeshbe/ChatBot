"""
Grant Thornton Embedding Service

Specialized embedding service for Grant Thornton financial documents.
Uses BAAI/bge-large-en-v1.5 (1024-dimensional embeddings).

Integrates with existing EmbeddingService infrastructure while adding
specialized financial document embeddings.

Author: Claude Code
Date: 2026-01-01
"""

import logging
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
import numpy as np
import time

# Import existing embedding service as base
from app.tier_1.embeddings.embedding_service import EmbeddingService as BaseEmbeddingService

logger = logging.getLogger(__name__)


class GrantThorntonEmbeddingService:
    """
    Specialized embedding service for Grant Thornton.

    Uses BAAI/bge-large-en-v1.5 (1024-dim) optimized for financial documents.
    Maintains compatibility with existing infrastructure.
    """

    MODEL_NAME = "BAAI/bge-large-en-v1.5"
    EMBEDDING_DIMENSION = 1024

    def __init__(self):
        self.model = None
        self._initialized = False

    async def initialize(self):
        """Initialize the BAAI embedding model"""
        if self._initialized:
            return

        try:
            logger.info(f"Loading Grant Thornton embedding model: {self.MODEL_NAME}")
            self.model = SentenceTransformer(self.MODEL_NAME)

            # Optimize for GPU if available
            if self.model.device.type == 'cuda':
                logger.info(f"✅ Model loaded on GPU: {self.model.device}")
            else:
                logger.info(f"⚠️ Model loaded on CPU (GPU recommended for performance)")

            self._initialized = True
            logger.info(f"✅ Grant Thornton embeddings ready (dim={self.EMBEDDING_DIMENSION})")

        except Exception as e:
            logger.error(f"Error loading Grant Thornton embedding model: {e}", exc_info=True)
            raise

    async def get_embedding(self, text: str) -> List[float]:
        """
        Get 1024-dim embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            List of 1024 floats
        """
        if not self._initialized:
            await self.initialize()

        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            # Return zero vector as fallback
            return [0.0] * self.EMBEDDING_DIMENSION

    async def get_embeddings_batch(
        self,
        texts: List[str],
        batch_size: int = 32,
        show_progress: bool = True
    ) -> List[List[float]]:
        """
        Get embeddings for multiple texts (optimized for GPU batch processing).

        Args:
            texts: List of texts to embed
            batch_size: Batch size for encoding
            show_progress: Show progress bar for large batches

        Returns:
            List of 1024-dim embedding vectors
        """
        if not self._initialized:
            await self.initialize()

        if not texts:
            return []

        start_time = time.time()

        try:
            # Batch encode for efficiency
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                convert_to_numpy=True,
                show_progress_bar=show_progress and len(texts) > 10
            )

            result = embeddings.tolist()

            elapsed = time.time() - start_time
            logger.info(
                f"✅ Generated {len(result)} embeddings in {elapsed:.2f}s "
                f"({len(result)/elapsed:.1f} docs/sec)"
            )

            return result

        except Exception as e:
            logger.error(f"Error in batch embedding: {e}", exc_info=True)
            # Return zero vectors as fallback
            return [[0.0] * self.EMBEDDING_DIMENSION for _ in texts]

    async def embed_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Embed Document chunks (from PDF parser).

        Args:
            chunks: List of Document objects with page_content

        Returns:
            Same chunks with 'embedding' field added
        """
        if not chunks:
            return []

        # Extract text content
        texts = [
            chunk.page_content if hasattr(chunk, 'page_content') else chunk.get('content', '')
            for chunk in chunks
        ]

        # Generate embeddings
        embeddings = await self.get_embeddings_batch(texts)

        # Add embeddings to chunks
        for chunk, embedding in zip(chunks, embeddings):
            if hasattr(chunk, 'metadata'):
                chunk.metadata['embedding'] = embedding
            else:
                chunk['embedding'] = embedding

        return chunks

    @staticmethod
    def cosine_similarity(a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two embeddings"""
        a_np = np.array(a)
        b_np = np.array(b)

        norm_a = np.linalg.norm(a_np)
        norm_b = np.linalg.norm(b_np)

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return float(np.dot(a_np, b_np) / (norm_a * norm_b))

    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        return {
            "model_name": self.MODEL_NAME,
            "embedding_dimension": self.EMBEDDING_DIMENSION,
            "device": str(self.model.device) if self.model else "not_loaded",
            "initialized": self._initialized
        }


# Singleton instance
_gt_embedding_service = None


async def get_grant_thornton_embeddings() -> GrantThorntonEmbeddingService:
    """
    Get or create Grant Thornton embedding service singleton.

    Returns:
        Initialized GrantThorntonEmbeddingService
    """
    global _gt_embedding_service

    if _gt_embedding_service is None:
        _gt_embedding_service = GrantThorntonEmbeddingService()
        await _gt_embedding_service.initialize()

    return _gt_embedding_service
