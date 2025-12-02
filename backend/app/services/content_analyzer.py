"""
Content Analyzer - Intelligent Document Content Analysis

Analyzes document content to determine optimal embedding strategy.
Ensures storage, retrieval, and comparison strategies are synchronized.

Philosophy:
- Analyze BEFORE embedding (understand what you have)
- Choose strategy based on content type (not just file type)
- Sync storage/retrieval/comparison (same strategy throughout)
"""

import logging
from enum import Enum
from typing import Dict, Any, Optional, List
from pathlib import Path

# Optional: PyMuPDF for advanced PDF analysis (fallback to simple analysis if not available)
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    logging.warning("PyMuPDF not available - using basic content analysis")

# Optional: PIL for image analysis
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# Optional: numpy for numerical analysis
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

logger = logging.getLogger(__name__)


class ContentType(Enum):
    """Content type classification for embedding strategy"""
    TEXT_HEAVY = "text_heavy"          # >80% text, few images/tables
    TABLE_HEAVY = "table_heavy"        # Multiple tables, structured data
    IMAGE_HEAVY = "image_heavy"        # Diagrams, charts, visual content
    CODE = "code"                      # Programming code
    NUMERICAL = "numerical"            # Spreadsheets, financial data
    MIXED = "mixed"                    # Mixed content (text + tables + images)
    SCANNED_LOW_QUALITY = "scanned_low_quality"   # Scanned, poor OCR
    SCANNED_HIGH_QUALITY = "scanned_high_quality" # Scanned, good OCR


class SimilarityMetric(Enum):
    """Similarity metrics synchronized with content type"""
    COSINE = "cosine"               # For text/semantic embeddings
    EUCLIDEAN = "euclidean"         # For numerical embeddings
    DOT_PRODUCT = "dot_product"     # For vision embeddings
    STATISTICAL = "statistical"     # For numerical data comparison
    STRUCTURAL = "structural"       # For table structure comparison


class ContentAnalyzer:
    """
    Analyze document content to determine embedding strategy

    Ensures synchronization between:
    - Content type detection
    - Embedding strategy selection
    - Storage format (which vector column)
    - Retrieval strategy (which index to search)
    - Similarity metric (how to compare)
    """

    def __init__(self):
        """Initialize content analyzer"""
        logger.info("ContentAnalyzer initialized")

    async def analyze(
        self,
        file_path: str,
        file_type: str,
        file_size: int
    ) -> Dict[str, Any]:
        """
        Analyze document content

        Args:
            file_path: Path to document file
            file_type: MIME type or file extension
            file_size: File size in bytes

        Returns:
            {
                "content_type": ContentType,
                "embedding_strategy": str,  # "text_semantic", "table_structure", etc.
                "similarity_metric": SimilarityMetric,
                "vector_column": str,  # "embedding", "table_embedding", "visual_embedding"
                "index_name": str,     # Which index to use for retrieval

                # Detailed analysis
                "has_tables": bool,
                "table_count": int,
                "has_images": bool,
                "image_count": int,
                "text_percentage": float,
                "is_scanned": bool,
                "ocr_confidence": Optional[float],
                "page_count": int,

                # Confidence and reasoning
                "confidence": float,
                "reasoning": str
            }
        """

        if "pdf" in file_type.lower():
            return await self._analyze_pdf(file_path)
        elif "image" in file_type.lower() or file_type.lower() in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
            return await self._analyze_image(file_path)
        elif "spreadsheet" in file_type.lower() or file_type.lower() in ['.xlsx', '.xls', '.csv']:
            return await self._analyze_excel(file_path)
        elif file_type.lower() in ['.py', '.js', '.java', '.cpp', '.c', '.go', '.rs']:
            return await self._analyze_code(file_path)
        else:
            # Default text analysis
            return await self._analyze_text(file_path)

    async def _analyze_pdf(self, file_path: str) -> Dict[str, Any]:
        """
        Analyze PDF document content

        Detects:
        - Text vs scanned (OCR quality)
        - Tables (heuristic: grids, numbers)
        - Images/diagrams
        - Overall content distribution
        """
        # If PyMuPDF not available, use basic analysis
        if not PYMUPDF_AVAILABLE:
            logger.warning("PyMuPDF not available - using basic text_semantic strategy for PDF")
            return {
                "content_type": ContentType.TEXT_HEAVY,
                "embedding_strategy": "text_semantic",
                "similarity_metric": SimilarityMetric.COSINE,
                "vector_column": "embedding",
                "index_name": "idx_chunks_embedding",
                "has_tables": False,
                "table_count": 0,
                "has_images": False,
                "image_count": 0,
                "is_scanned": False,
                "confidence": 0.7,
                "reasoning": "Basic analysis (PyMuPDF not available) - using text embeddings",
                "strategy_details": {
                    "dimension": 384,
                    "model": "sentence-transformers/all-MiniLM-L6-v2"
                }
            }

        try:
            doc = fitz.open(file_path)

            page_count = len(doc)
            total_text_length = 0
            total_chars = 0
            table_indicators = 0
            image_count = 0
            is_scanned = False

            for page_num, page in enumerate(doc):
                # Extract text
                text = page.get_text()
                total_text_length += len(text.strip())

                # Check if scanned (very little text layer)
                if len(text.strip()) < 50:  # Very little text → likely scanned
                    is_scanned = True

                # Count images
                images = page.get_images()
                image_count += len(images)

                # Detect tables (heuristic: lots of whitespace + numbers)
                # This is simplified - in production, use a table detection library
                if self._has_table_indicators(text):
                    table_indicators += 1

            doc.close()

            # Classify content type
            table_percentage = table_indicators / page_count if page_count > 0 else 0
            has_tables = table_percentage > 0.3  # >30% pages have tables
            has_images = image_count > 3

            # Determine content type
            if is_scanned:
                # Would need actual OCR to determine quality
                # For now, assume medium quality
                content_type = ContentType.SCANNED_HIGH_QUALITY
                embedding_strategy = "text_semantic"  # After OCR
                similarity_metric = SimilarityMetric.COSINE
                vector_column = "embedding"
                reasoning = "Scanned PDF detected, using OCR + text embeddings"

            elif has_tables and table_percentage > 0.5:
                content_type = ContentType.TABLE_HEAVY
                embedding_strategy = "table_structure"
                similarity_metric = SimilarityMetric.STRUCTURAL
                vector_column = "table_embedding"
                reasoning = f"Table-heavy PDF ({table_percentage:.1%} pages with tables)"

            elif has_images and image_count > page_count:
                content_type = ContentType.IMAGE_HEAVY
                embedding_strategy = "vision"
                similarity_metric = SimilarityMetric.DOT_PRODUCT
                vector_column = "visual_embedding"
                reasoning = f"Image-heavy PDF ({image_count} images in {page_count} pages)"

            elif has_tables or has_images:
                content_type = ContentType.MIXED
                embedding_strategy = "hybrid"
                similarity_metric = SimilarityMetric.COSINE
                vector_column = "embedding"  # Primary: text, secondary: other modalities
                reasoning = "Mixed content PDF (text + tables/images)"

            else:
                content_type = ContentType.TEXT_HEAVY
                embedding_strategy = "text_semantic"
                similarity_metric = SimilarityMetric.COSINE
                vector_column = "embedding"
                reasoning = "Text-heavy PDF, using semantic text embeddings"

            return {
                "content_type": content_type,
                "embedding_strategy": embedding_strategy,
                "similarity_metric": similarity_metric,
                "vector_column": vector_column,
                "index_name": f"idx_chunks_{vector_column}",

                # Details
                "has_tables": has_tables,
                "table_count": table_indicators,
                "has_images": has_images,
                "image_count": image_count,
                "text_percentage": min(1.0, total_text_length / (page_count * 500)),  # Estimate
                "is_scanned": is_scanned,
                "ocr_confidence": None,  # Would need actual OCR
                "page_count": page_count,

                # Confidence
                "confidence": 0.85,
                "reasoning": reasoning
            }

        except Exception as e:
            logger.error(f"PDF analysis failed: {e}")

            # Fallback to text semantic
            return {
                "content_type": ContentType.TEXT_HEAVY,
                "embedding_strategy": "text_semantic",
                "similarity_metric": SimilarityMetric.COSINE,
                "vector_column": "embedding",
                "index_name": "idx_chunks_embedding",
                "has_tables": False,
                "table_count": 0,
                "has_images": False,
                "image_count": 0,
                "text_percentage": 1.0,
                "is_scanned": False,
                "ocr_confidence": None,
                "page_count": 0,
                "confidence": 0.5,
                "reasoning": f"Analysis failed, using fallback: {e}"
            }

    async def _analyze_image(self, file_path: str) -> Dict[str, Any]:
        """Analyze image file"""
        try:
            img = Image.open(file_path)
            width, height = img.size

            # Check if image likely contains text (aspect ratio, size)
            aspect_ratio = width / height if height > 0 else 1.0
            is_likely_document = 0.7 < aspect_ratio < 1.5  # Square-ish

            if is_likely_document and width > 800:
                # Likely screenshot or scanned document → OCR
                content_type = ContentType.SCANNED_HIGH_QUALITY
                embedding_strategy = "text_semantic"  # After OCR
                similarity_metric = SimilarityMetric.COSINE
                vector_column = "embedding"
                reasoning = "Image likely contains text (document screenshot)"
            else:
                # Diagram, chart, photo → vision embeddings
                content_type = ContentType.IMAGE_HEAVY
                embedding_strategy = "vision"
                similarity_metric = SimilarityMetric.DOT_PRODUCT
                vector_column = "visual_embedding"
                reasoning = "Image content (diagram/chart/photo)"

            return {
                "content_type": content_type,
                "embedding_strategy": embedding_strategy,
                "similarity_metric": similarity_metric,
                "vector_column": vector_column,
                "index_name": f"idx_chunks_{vector_column}",
                "has_tables": False,
                "table_count": 0,
                "has_images": True,
                "image_count": 1,
                "text_percentage": 0.0,
                "is_scanned": False,
                "ocr_confidence": None,
                "page_count": 1,
                "confidence": 0.75,
                "reasoning": reasoning
            }

        except Exception as e:
            logger.error(f"Image analysis failed: {e}")
            return self._default_analysis("vision", f"Image analysis error: {e}")

    async def _analyze_excel(self, file_path: str) -> Dict[str, Any]:
        """Analyze Excel/CSV file"""
        return {
            "content_type": ContentType.NUMERICAL,
            "embedding_strategy": "numerical",
            "similarity_metric": SimilarityMetric.STATISTICAL,
            "vector_column": "numerical_embedding",
            "index_name": "idx_chunks_numerical_embedding",
            "has_tables": True,
            "table_count": 1,  # At least one sheet
            "has_images": False,
            "image_count": 0,
            "text_percentage": 0.2,  # Headers
            "is_scanned": False,
            "ocr_confidence": None,
            "page_count": 1,
            "confidence": 0.95,
            "reasoning": "Excel/CSV file with numerical data"
        }

    async def _analyze_code(self, file_path: str) -> Dict[str, Any]:
        """Analyze code file"""
        return {
            "content_type": ContentType.CODE,
            "embedding_strategy": "code",
            "similarity_metric": SimilarityMetric.COSINE,
            "vector_column": "code_embedding",
            "index_name": "idx_chunks_code_embedding",
            "has_tables": False,
            "table_count": 0,
            "has_images": False,
            "image_count": 0,
            "text_percentage": 1.0,
            "is_scanned": False,
            "ocr_confidence": None,
            "page_count": 1,
            "confidence": 1.0,
            "reasoning": "Code file detected"
        }

    async def _analyze_text(self, file_path: str) -> Dict[str, Any]:
        """Analyze plain text file"""
        return self._default_analysis("text_semantic", "Plain text file")

    def _default_analysis(self, strategy: str = "text_semantic", reason: str = "Default") -> Dict[str, Any]:
        """Default fallback analysis"""
        return {
            "content_type": ContentType.TEXT_HEAVY,
            "embedding_strategy": strategy,
            "similarity_metric": SimilarityMetric.COSINE,
            "vector_column": "embedding",
            "index_name": "idx_chunks_embedding",
            "has_tables": False,
            "table_count": 0,
            "has_images": False,
            "image_count": 0,
            "text_percentage": 1.0,
            "is_scanned": False,
            "ocr_confidence": None,
            "page_count": 0,
            "confidence": 0.5,
            "reasoning": reason
        }

    def _has_table_indicators(self, text: str) -> bool:
        """
        Heuristic to detect tables in text

        Looks for:
        - Multiple numbers
        - Aligned whitespace (tabs/spaces)
        - Short lines (table rows)
        """
        lines = text.split('\n')

        # Count lines with numbers
        numeric_lines = sum(1 for line in lines if any(c.isdigit() for c in line))

        # Check for alignment (multiple tabs or consistent spacing)
        tabbed_lines = sum(1 for line in lines if '\t' in line)

        # Short lines (table rows are typically short)
        short_lines = sum(1 for line in lines if 10 < len(line.strip()) < 80)

        # Heuristic: if >30% lines are numeric and aligned, likely a table
        if len(lines) > 0:
            numeric_ratio = numeric_lines / len(lines)
            tabbed_ratio = tabbed_lines / len(lines)

            return numeric_ratio > 0.3 and (tabbed_ratio > 0.2 or short_lines > len(lines) * 0.5)

        return False


# Global singleton
content_analyzer = ContentAnalyzer()
