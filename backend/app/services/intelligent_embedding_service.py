"""
Intelligent Embedding Service - Content-Aware Embedding Strategy Selection

Analyzes document content and applies optimal embedding strategy:
- Text-heavy: Semantic text embeddings (SentenceTransformer)
- Table-heavy: Table structure embeddings + numerical
- Image-heavy: Vision embeddings (CLIP)
- Code: Code embeddings (CodeBERT)
- Numerical: Statistical embeddings for Excel/CSV

Philosophy:
- Analyze BEFORE embedding (understand document type)
- Choose strategy based on content, not just file extension
- Sync storage/retrieval/comparison (same strategy throughout)
"""

import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from sentence_transformers import SentenceTransformer
import redis.asyncio as redis
import hashlib
import json
import time

from app.core.config import settings
from app.services.content_analyzer import content_analyzer, ContentType, SimilarityMetric

# Tool usage tracking
try:
    from app.services.tool_usage_tracker import tool_tracker, ToolCategory
    from app.core.database import AsyncSessionLocal
    TOOL_TRACKING_ENABLED = True
except ImportError:
    TOOL_TRACKING_ENABLED = False
    logging.warning("Tool usage tracking not available")

logger = logging.getLogger(__name__)


class IntelligentEmbeddingService:
    """
    Intelligent embedding service that selects optimal strategy based on content type

    Supports multiple embedding strategies:
    - text_semantic: Sentence-transformers for text
    - table_structure: Table embeddings (future)
    - vision: CLIP for images (future)
    - numerical: Statistical embeddings (future)
    - code: CodeBERT for code (future)
    """

    def __init__(self):
        """Initialize embedding service"""
        self.models = {}  # Dict of model_name -> model instance
        self.redis_client = None
        self._initialized = False

        # Model registry - maps strategy to model configuration
        self.model_registry = {
            "text_semantic": {
                "model_name": settings.EMBEDDING_MODEL,  # Default: all-MiniLM-L6-v2
                "dimension": settings.EMBEDDING_DIMENSION,  # 384
                "vector_column": "embedding",
                "similarity_metric": "cosine",
                "type": "sentence_transformer"
            },
            # Future strategies (P1)
            "table_structure": {
                "model_name": "table_transformer",
                "dimension": 512,
                "vector_column": "table_embedding",
                "similarity_metric": "structural",
                "type": "custom"
            },
            "vision": {
                "model_name": "openai/clip-vit-base-patch32",
                "dimension": 512,
                "vector_column": "visual_embedding",
                "similarity_metric": "dot_product",
                "type": "clip"
            },
            "numerical": {
                "model_name": "statistical",
                "dimension": 256,
                "vector_column": "numerical_embedding",
                "similarity_metric": "statistical",
                "type": "custom"
            },
            "code": {
                "model_name": "microsoft/codebert-base",
                "dimension": 768,
                "vector_column": "code_embedding",
                "similarity_metric": "cosine",
                "type": "sentence_transformer"
            }
        }

    async def initialize(self):
        """Initialize embedding models and Redis connection"""
        if self._initialized:
            return

        try:
            # Load primary text semantic model (always needed)
            text_config = self.model_registry["text_semantic"]
            logger.info(f"Loading text semantic model: {text_config['model_name']}")
            self.models["text_semantic"] = SentenceTransformer(text_config["model_name"])
            logger.info("Text semantic model loaded successfully")

            # Initialize Redis for caching
            if settings.USE_SEMANTIC_CACHE:
                self.redis_client = await redis.from_url(
                    settings.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=False
                )
                logger.info("Redis cache connected")

            self._initialized = True
            logger.info("IntelligentEmbeddingService initialized")

        except Exception as e:
            logger.error(f"Error initializing intelligent embedding service: {e}")
            raise

    async def close(self):
        """Close connections"""
        if self.redis_client:
            await self.redis_client.close()

    def _get_cache_key(self, text: str, strategy: str) -> str:
        """Generate cache key for text + strategy"""
        content_hash = hashlib.md5(text.encode()).hexdigest()
        return f"emb:{strategy}:{content_hash}"

    async def analyze_and_embed(
        self,
        file_path: str,
        file_type: str,
        file_size: int,
        texts: List[str],
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze document content and generate embeddings with optimal strategy

        Args:
            file_path: Path to document file
            file_type: MIME type or file extension
            file_size: File size in bytes
            texts: List of text chunks to embed
            session_id: Session ID for tracking

        Returns:
            {
                "embeddings": List[List[float]],  # Embedding vectors
                "strategy": str,                   # Strategy used
                "vector_column": str,              # Database column to store in
                "similarity_metric": str,          # Metric for retrieval
                "dimension": int,                  # Embedding dimension
                "content_analysis": Dict,          # ContentAnalyzer results
                "metadata": Dict                   # Additional metadata
            }
        """
        if not self._initialized:
            await self.initialize()

        start_time = time.time()

        # Step 1: Analyze document content
        logger.info(f"📊 Analyzing document content: {file_path}")
        content_analysis = await content_analyzer.analyze(
            file_path=file_path,
            file_type=file_type,
            file_size=file_size
        )

        embedding_strategy = content_analysis["embedding_strategy"]
        vector_column = content_analysis["vector_column"]
        similarity_metric = content_analysis["similarity_metric"]

        logger.info(
            f"🎯 Content Analysis Complete:\n"
            f"   Content Type: {content_analysis['content_type'].value}\n"
            f"   Strategy: {embedding_strategy}\n"
            f"   Vector Column: {vector_column}\n"
            f"   Similarity Metric: {similarity_metric.value}\n"
            f"   Confidence: {content_analysis['confidence']:.2f}\n"
            f"   Reasoning: {content_analysis['reasoning']}"
        )

        # Step 2: Generate embeddings using selected strategy
        embeddings = await self._generate_embeddings(
            texts=texts,
            strategy=embedding_strategy,
            session_id=session_id
        )

        processing_time = (time.time() - start_time) * 1000

        # Get model config
        model_config = self.model_registry.get(embedding_strategy, self.model_registry["text_semantic"])

        result = {
            "embeddings": embeddings,
            "strategy": embedding_strategy,
            "vector_column": vector_column,
            "similarity_metric": similarity_metric.value,
            "dimension": model_config["dimension"],
            "content_analysis": content_analysis,
            "metadata": {
                "num_chunks": len(texts),
                "processing_time_ms": processing_time,
                "model_name": model_config["model_name"],
                "content_type": content_analysis["content_type"].value
            }
        }

        logger.info(
            f"✅ Embeddings generated: {len(embeddings)} vectors, "
            f"{model_config['dimension']}-dim, "
            f"{processing_time:.2f}ms"
        )

        return result

    async def _generate_embeddings(
        self,
        texts: List[str],
        strategy: str,
        session_id: Optional[str] = None
    ) -> List[List[float]]:
        """
        Generate embeddings using specified strategy

        Args:
            texts: List of text chunks
            strategy: Embedding strategy (text_semantic, table_structure, etc.)
            session_id: Session ID for tracking

        Returns:
            List of embedding vectors
        """
        start_time = time.time()

        # Route to appropriate embedding method
        if strategy == "text_semantic":
            embeddings = await self._embed_text_semantic(texts)
        elif strategy == "table_structure":
            # Table structure embeddings with enhanced structural metadata
            logger.info("📊 Generating table structure embeddings (hybrid approach)")
            embeddings = await self._embed_table_structure(texts)
        elif strategy == "vision":
            # Vision embeddings using CLIP (text-to-image for queries)
            logger.info("🎨 Generating vision embeddings using CLIP (text-to-image)")
            # For queries: Use text-to-image CLIP embeddings
            # This allows searching for images using text prompts like "show me diagrams"
            embeddings = await self._embed_text_for_visual_search(texts)
        elif strategy == "numerical":
            # Future: Numerical embeddings
            logger.warning("⚠️  Numerical embeddings not yet implemented, using text semantic")
            embeddings = await self._embed_text_semantic(texts)
        elif strategy == "code":
            # Future: Code embeddings (CodeBERT)
            logger.warning("⚠️  Code embeddings not yet implemented, using text semantic")
            embeddings = await self._embed_text_semantic(texts)
        elif strategy == "hybrid":
            # Future: Multi-modal embeddings
            logger.warning("⚠️  Hybrid embeddings not yet implemented, using text semantic")
            embeddings = await self._embed_text_semantic(texts)
        else:
            logger.warning(f"⚠️  Unknown strategy {strategy}, using text semantic")
            embeddings = await self._embed_text_semantic(texts)

        processing_time = (time.time() - start_time) * 1000

        # Track embedding generation
        if TOOL_TRACKING_ENABLED and session_id:
            try:
                async with AsyncSessionLocal() as track_db:
                    await tool_tracker.record_tool_usage(
                        category=ToolCategory.EMBEDDING,
                        tool_name=f"{strategy}_embeddings",
                        operation="generate_embeddings",
                        db=track_db,
                        session_id=session_id,
                        success=True,
                        latency_ms=processing_time,
                        input_size=len(texts),
                        output_size=len(embeddings),
                        metadata={
                            'strategy': strategy,
                            'dimension': len(embeddings[0]) if embeddings else 0,
                            'num_chunks': len(texts)
                        }
                    )
                    await track_db.commit()
            except Exception as track_err:
                logger.warning(f"Failed to track embedding generation: {track_err}")

        return embeddings

    async def _embed_text_semantic(self, texts: List[str]) -> List[List[float]]:
        """
        Generate text semantic embeddings using SentenceTransformer

        Args:
            texts: List of text chunks

        Returns:
            List of embedding vectors
        """
        model = self.models.get("text_semantic")
        if not model:
            raise RuntimeError("Text semantic model not loaded")

        # Check cache for each text
        cached_embeddings = []
        texts_to_embed = []
        cache_indices = []

        if self.redis_client:
            for i, text in enumerate(texts):
                cache_key = self._get_cache_key(text, "text_semantic")
                cached = await self.redis_client.get(cache_key)
                if cached:
                    cached_embeddings.append((i, json.loads(cached)))
                else:
                    texts_to_embed.append(text)
                    cache_indices.append(i)
        else:
            texts_to_embed = texts
            cache_indices = list(range(len(texts)))

        # Generate embeddings for non-cached texts
        if texts_to_embed:
            logger.debug(f"Generating {len(texts_to_embed)} embeddings (cache miss)")
            new_embeddings = model.encode(
                texts_to_embed,
                convert_to_numpy=True,
                show_progress_bar=len(texts_to_embed) > 10
            ).tolist()

            # Cache new embeddings
            if self.redis_client:
                for text, embedding in zip(texts_to_embed, new_embeddings):
                    cache_key = self._get_cache_key(text, "text_semantic")
                    await self.redis_client.setex(
                        cache_key,
                        3600,  # 1 hour TTL
                        json.dumps(embedding)
                    )
        else:
            new_embeddings = []
            logger.debug(f"All {len(texts)} embeddings from cache")

        # Merge cached and new embeddings in correct order
        result = [None] * len(texts)
        for i, emb in cached_embeddings:
            result[i] = emb
        for i, emb in zip(cache_indices, new_embeddings):
            result[i] = emb

        return result

    async def _load_clip_model(self):
        """Lazy-load CLIP model for vision embeddings"""
        if "vision" in self.models:
            return self.models["vision"], self.models["vision_processor"]

        try:
            logger.info("🎨 Loading CLIP model for vision embeddings...")
            import torch
            from transformers import CLIPModel, CLIPProcessor

            model_name = self.model_registry["vision"]["model_name"]
            model = CLIPModel.from_pretrained(model_name)
            processor = CLIPProcessor.from_pretrained(model_name)

            # Move model to GPU if available
            if torch.cuda.is_available():
                device = torch.device("cuda")
                model = model.to(device)
                logger.info(f"✅ CLIP model moved to GPU: {torch.cuda.get_device_name(0)}")
            else:
                logger.warning("⚠️ GPU not available, using CPU for CLIP")

            self.models["vision"] = model
            self.models["vision_processor"] = processor

            logger.info(f"✅ CLIP model loaded: {model_name}")
            return model, processor

        except Exception as e:
            logger.error(f"Failed to load CLIP model: {e}")
            raise

    def _parse_table_structure(self, text: str) -> Dict[str, Any]:
        """
        Parse table structure from markdown/text table format

        Args:
            text: Text containing table (markdown format with | delimiters)

        Returns:
            Dictionary with table metadata (rows, columns, structure)
        """
        import re

        # Detect if text contains table patterns
        has_table_markers = '|' in text and '\n' in text

        if not has_table_markers:
            return {
                'has_table': False,
                'num_rows': 0,
                'num_columns': 0,
                'columns': [],
                'data_rows': []
            }

        # Split into lines and filter table lines (contain |)
        lines = [line.strip() for line in text.split('\n') if '|' in line]

        if len(lines) < 2:  # Need at least header + 1 data row
            return {
                'has_table': False,
                'num_rows': 0,
                'num_columns': 0,
                'columns': [],
                'data_rows': []
            }

        # Parse header (first line with |)
        header_line = lines[0]
        columns = [col.strip() for col in header_line.split('|') if col.strip()]

        # Skip separator lines (---, ===, |||)
        data_lines = [line for line in lines[1:] if not re.match(r'^\|?[\s\-=|]+\|?$', line)]

        # Parse data rows
        data_rows = []
        for line in data_lines[:10]:  # Limit to first 10 rows for metadata
            cells = [cell.strip() for cell in line.split('|') if cell.strip()]
            if len(cells) == len(columns):  # Valid row
                data_rows.append(cells)

        return {
            'has_table': True,
            'num_rows': len(data_rows),
            'num_columns': len(columns),
            'columns': columns,
            'data_rows': data_rows[:3],  # Sample first 3 rows
            'total_cells': len(columns) * len(data_rows)
        }

    async def _embed_table_structure(self, texts: List[str]) -> List[List[float]]:
        """
        Generate table structure embeddings using hybrid approach

        Strategy:
        1. Parse table structure (rows, columns, cells)
        2. Enhance text with structural metadata
        3. Generate text embeddings with enhanced context
        4. Project to 512 dimensions (matching table_embedding column)

        Args:
            texts: List of text chunks (may contain tables)

        Returns:
            List of 512-dimensional embedding vectors
        """
        model = self.models.get("text_semantic")
        if not model:
            raise RuntimeError("Text semantic model not loaded")

        enhanced_embeddings = []

        for text in texts:
            # Parse table structure
            table_info = self._parse_table_structure(text)

            if table_info['has_table']:
                # Enhance text with structural metadata
                structural_context = f"""
Table with {table_info['num_rows']} rows and {table_info['num_columns']} columns.
Columns: {', '.join(table_info['columns'])}
Total cells: {table_info['total_cells']}
Sample data: {' | '.join([' '.join(row) for row in table_info['data_rows']])}

Table content:
{text}
"""
                logger.debug(f"📊 Enhanced table text: {len(structural_context)} chars")
            else:
                # Not a table, use original text
                structural_context = text

            # Generate base embedding (384-dim)
            base_embedding = model.encode(
                [structural_context],
                convert_to_numpy=True,
                show_progress_bar=False
            )[0].tolist()

            # Project to 512 dimensions (match database schema)
            # Strategy: Zero-pad from 384 to 512 dimensions
            # This preserves the original semantic information while meeting schema requirements
            padded_embedding = base_embedding + [0.0] * (512 - len(base_embedding))

            enhanced_embeddings.append(padded_embedding)

        logger.info(f"✅ Generated {len(enhanced_embeddings)} table embeddings (512-dim)")
        return enhanced_embeddings

    async def _embed_visual(self, image_paths: List[str]) -> List[List[float]]:
        """
        Generate visual embeddings using CLIP

        Args:
            image_paths: List of image file paths to embed

        Returns:
            List of 512-dimensional CLIP embedding vectors
        """
        import torch
        from PIL import Image

        # Load CLIP model (lazy load)
        model, processor = await self._load_clip_model()

        # Check cache for each image
        cached_embeddings = []
        images_to_embed = []
        cache_indices = []

        if self.redis_client:
            for i, img_path in enumerate(image_paths):
                cache_key = self._get_cache_key(img_path, "vision")
                cached = await self.redis_client.get(cache_key)
                if cached:
                    cached_embeddings.append((i, json.loads(cached)))
                else:
                    images_to_embed.append(img_path)
                    cache_indices.append(i)
        else:
            images_to_embed = image_paths
            cache_indices = list(range(len(image_paths)))

        # Generate embeddings for non-cached images
        new_embeddings = []
        if images_to_embed:
            logger.debug(f"Generating {len(images_to_embed)} CLIP embeddings (cache miss)")

            for img_path in images_to_embed:
                try:
                    # Load and preprocess image
                    image = Image.open(img_path).convert('RGB')
                    inputs = processor(images=image, return_tensors="pt")

                    # Move inputs to same device as model
                    if torch.cuda.is_available():
                        inputs = {k: v.to("cuda") for k, v in inputs.items()}

                    # Generate embedding
                    with torch.no_grad():
                        image_features = model.get_image_features(**inputs)
                        # Normalize embedding (CLIP uses cosine similarity)
                        image_features = image_features / image_features.norm(dim=-1, keepdim=True)
                        embedding = image_features.squeeze().cpu().numpy().tolist()

                    new_embeddings.append(embedding)

                    # Cache embedding
                    if self.redis_client:
                        cache_key = self._get_cache_key(img_path, "vision")
                        await self.redis_client.setex(
                            cache_key,
                            3600,  # 1 hour TTL
                            json.dumps(embedding)
                        )

                except Exception as e:
                    logger.error(f"Failed to generate CLIP embedding for {img_path}: {e}")
                    # Return zero vector as fallback
                    new_embeddings.append([0.0] * 512)
        else:
            logger.debug(f"All {len(image_paths)} CLIP embeddings from cache")

        # Merge cached and new embeddings in correct order
        result = [None] * len(image_paths)
        for i, emb in cached_embeddings:
            result[i] = emb
        for i, emb in zip(cache_indices, new_embeddings):
            result[i] = emb

        return result

    async def _embed_text_for_visual_search(self, texts: List[str]) -> List[List[float]]:
        """
        Generate text embeddings using CLIP for text-to-image search

        This allows querying images using text prompts.
        E.g., "show me diagrams with network architecture"

        Args:
            texts: List of text queries

        Returns:
            List of 512-dimensional CLIP text embedding vectors
        """
        import torch

        # Load CLIP model (lazy load)
        model, processor = await self._load_clip_model()

        embeddings = []
        for text in texts:
            try:
                # Process text
                inputs = processor(text=text, return_tensors="pt", padding=True)

                # Generate embedding
                with torch.no_grad():
                    text_features = model.get_text_features(**inputs)
                    # Normalize embedding
                    text_features = text_features / text_features.norm(dim=-1, keepdim=True)
                    embedding = text_features.squeeze().cpu().numpy().tolist()

                embeddings.append(embedding)

            except Exception as e:
                logger.error(f"Failed to generate CLIP text embedding for '{text}': {e}")
                # Return zero vector as fallback
                embeddings.append([0.0] * 512)

        return embeddings

    async def get_embedding(
        self,
        text: str,
        strategy: str = "text_semantic"
    ) -> List[float]:
        """
        Get single embedding with specified strategy

        Args:
            text: Text to embed
            strategy: Embedding strategy

        Returns:
            Embedding vector
        """
        if not self._initialized:
            await self.initialize()

        embeddings = await self._generate_embeddings(
            texts=[text],
            strategy=strategy,
            session_id=None
        )

        return embeddings[0]

    async def get_embeddings_batch(
        self,
        texts: List[str],
        strategy: str = "text_semantic",
        session_id: Optional[str] = None
    ) -> List[List[float]]:
        """
        Get batch embeddings with specified strategy

        Args:
            texts: List of texts to embed
            strategy: Embedding strategy
            session_id: Session ID for tracking

        Returns:
            List of embedding vectors
        """
        if not self._initialized:
            await self.initialize()

        return await self._generate_embeddings(
            texts=texts,
            strategy=strategy,
            session_id=session_id
        )

    def calculate_similarity(
        self,
        embedding_a: List[float],
        embedding_b: List[float],
        metric: str = "cosine"
    ) -> float:
        """
        Calculate similarity between two embeddings

        Args:
            embedding_a: First embedding
            embedding_b: Second embedding
            metric: Similarity metric (cosine, euclidean, dot_product)

        Returns:
            Similarity score
        """
        a_np = np.array(embedding_a)
        b_np = np.array(embedding_b)

        if metric == "cosine":
            # Cosine similarity
            return float(np.dot(a_np, b_np) / (np.linalg.norm(a_np) * np.linalg.norm(b_np)))
        elif metric == "euclidean":
            # Euclidean distance (inverted to similarity: smaller = more similar)
            distance = np.linalg.norm(a_np - b_np)
            return float(1.0 / (1.0 + distance))
        elif metric == "dot_product":
            # Dot product (for normalized embeddings)
            return float(np.dot(a_np, b_np))
        else:
            logger.warning(f"Unknown metric {metric}, using cosine")
            return float(np.dot(a_np, b_np) / (np.linalg.norm(a_np) * np.linalg.norm(b_np)))

    async def load_strategy_model(self, strategy: str):
        """
        Load model for specific strategy (on-demand loading)

        Args:
            strategy: Strategy name (table_structure, vision, etc.)
        """
        if strategy in self.models:
            logger.debug(f"Model for {strategy} already loaded")
            return

        config = self.model_registry.get(strategy)
        if not config:
            raise ValueError(f"Unknown strategy: {strategy}")

        try:
            if config["type"] == "sentence_transformer":
                logger.info(f"Loading {strategy} model: {config['model_name']}")
                self.models[strategy] = SentenceTransformer(config["model_name"])
                logger.info(f"{strategy} model loaded successfully")
            elif config["type"] == "clip":
                # Future: Load CLIP model
                logger.warning(f"CLIP model loading not yet implemented for {strategy}")
            elif config["type"] == "custom":
                # Future: Load custom models
                logger.warning(f"Custom model loading not yet implemented for {strategy}")
            else:
                raise ValueError(f"Unknown model type: {config['type']}")
        except Exception as e:
            logger.error(f"Failed to load model for {strategy}: {e}")
            raise


# Singleton instance
intelligent_embedding_service = IntelligentEmbeddingService()
