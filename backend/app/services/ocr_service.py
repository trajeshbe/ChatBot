"""
OCR Service - Hybrid Docling + Tesseract

Provides intelligent OCR capabilities with automatic fallback.

Strategy:
1. Try Docling first (best for PDFs with complex layouts)
2. If Docling fails or returns empty → use Tesseract
3. Support pure images (JPG, PNG) directly with Tesseract
"""

import logging
import os
from typing import Dict, Any, Optional, List
from pathlib import Path

# Docling imports
try:
    from docling.document_converter import DocumentConverter
    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False
    logging.warning("Docling not available - will use Tesseract only")

# Tesseract imports
try:
    import pytesseract
    from PIL import Image
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    logging.warning("Tesseract not available - will use Docling only")

logger = logging.getLogger(__name__)


class OCRService:
    """
    Hybrid OCR service: Docling → Tesseract fallback

    Features:
    - Intelligent method selection based on file type
    - Automatic fallback if primary method fails
    - Confidence scoring
    - Page-by-page extraction
    """

    def __init__(self):
        """Initialize OCR service with available backends"""
        self.docling_available = DOCLING_AVAILABLE
        self.tesseract_available = TESSERACT_AVAILABLE

        # Initialize Docling converter if available
        self.docling_converter = None
        if self.docling_available:
            try:
                self.docling_converter = DocumentConverter()
                logger.info("Docling OCR backend initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Docling: {e}")
                self.docling_available = False

        # Check Tesseract availability
        if self.tesseract_available:
            try:
                pytesseract.get_tesseract_version()
                logger.info("Tesseract OCR backend initialized")
            except Exception as e:
                logger.error(f"Tesseract not found: {e}")
                self.tesseract_available = False

        # Validate at least one backend is available
        if not self.docling_available and not self.tesseract_available:
            logger.error("No OCR backends available!")

    async def extract_text(
        self,
        file_path: str,
        method: str = "auto",
        language: str = "eng",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Extract text with intelligent method selection.

        Args:
            file_path: Path to document/image file
            method: Extraction method ("auto", "docling", "tesseract")
            language: Tesseract language code (default: "eng")
            **kwargs: Additional method-specific options

        Returns:
            {
                "text": str,                    # Extracted text content
                "method_used": str,             # "docling" or "tesseract"
                "confidence": float,            # 0.0-1.0
                "pages": int,                   # Number of pages processed
                "file_path": str,               # Original file path
                "file_type": str,               # File extension
                "metadata": dict                # Additional metadata
            }

        Raises:
            ValueError: If file doesn't exist or no OCR backend available
            RuntimeError: If all OCR methods fail
        """
        # Validate file exists
        if not os.path.exists(file_path):
            raise ValueError(f"File not found: {file_path}")

        file_ext = Path(file_path).suffix.lower()
        file_type = file_ext.lstrip('.')

        logger.info(f"OCR extraction request: {file_path} ({file_type}), method={method}")

        # Determine extraction method
        if method == "auto":
            method = self._select_method(file_type)
        elif method not in ["docling", "tesseract"]:
            raise ValueError(f"Invalid method: {method}. Must be 'auto', 'docling', or 'tesseract'")

        # Try primary method
        result = None
        error = None

        try:
            if method == "docling":
                result = await self._extract_with_docling(file_path, **kwargs)
            elif method == "tesseract":
                result = await self._extract_with_tesseract(file_path, language=language, **kwargs)
        except Exception as e:
            logger.warning(f"{method} extraction failed: {e}")
            error = str(e)

        # Fallback logic
        if result is None or not result.get("text") or result.get("text", "").strip() == "":
            logger.info(f"Primary method ({method}) failed or returned empty, trying fallback...")

            # Try fallback method
            fallback_method = "tesseract" if method == "docling" else "docling"

            # Check if fallback is available
            if fallback_method == "tesseract" and not self.tesseract_available:
                raise RuntimeError(f"Primary method failed and Tesseract not available: {error}")
            elif fallback_method == "docling" and not self.docling_available:
                raise RuntimeError(f"Primary method failed and Docling not available: {error}")

            try:
                if fallback_method == "tesseract":
                    result = await self._extract_with_tesseract(file_path, language=language, **kwargs)
                else:
                    result = await self._extract_with_docling(file_path, **kwargs)

                # Update method used
                result["method_used"] = f"{method} (failed) → {fallback_method} (fallback)"
                logger.info(f"Fallback successful: {fallback_method}")

            except Exception as e:
                logger.error(f"Fallback method ({fallback_method}) also failed: {e}")
                raise RuntimeError(f"All OCR methods failed. Primary: {error}, Fallback: {str(e)}")

        # Add common metadata
        result["file_path"] = file_path
        result["file_type"] = file_type

        logger.info(f"OCR extraction completed: {result['pages']} pages, {len(result['text'])} chars")

        return result

    def _select_method(self, file_type: str) -> str:
        """
        Select optimal OCR method based on file type.

        Args:
            file_type: File extension (pdf, jpg, png, etc.)

        Returns:
            Method name ("docling" or "tesseract")
        """
        # PDFs → Docling first (better for complex layouts)
        if file_type == "pdf":
            return "docling" if self.docling_available else "tesseract"

        # Images → Tesseract directly
        elif file_type in ["jpg", "jpeg", "png", "tiff", "bmp", "gif"]:
            return "tesseract" if self.tesseract_available else "docling"

        # Default: try Docling first
        return "docling" if self.docling_available else "tesseract"

    async def _extract_with_docling(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """
        Extract text using Docling.

        Args:
            file_path: Path to document
            **kwargs: Additional Docling options

        Returns:
            Extraction result dictionary
        """
        if not self.docling_available or self.docling_converter is None:
            raise RuntimeError("Docling not available")

        logger.info(f"Extracting with Docling: {file_path}")

        # Convert document
        result = self.docling_converter.convert(file_path)

        # Extract markdown text
        text = result.document.export_to_markdown()

        # Count pages (estimate based on document structure)
        pages = len(result.document.pages) if hasattr(result.document, 'pages') else 1

        # Calculate confidence (Docling doesn't provide this, use heuristic)
        confidence = 0.95 if len(text) > 100 else 0.7

        return {
            "text": text,
            "method_used": "docling",
            "confidence": confidence,
            "pages": pages,
            "metadata": {
                "has_tables": hasattr(result.document, 'tables'),
                "has_images": hasattr(result.document, 'pictures'),
                "converter": "docling"
            }
        }

    async def _extract_with_tesseract(
        self,
        file_path: str,
        language: str = "eng",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Extract text using Tesseract OCR.

        Args:
            file_path: Path to image/document
            language: Tesseract language code (default: "eng")
            **kwargs: Additional Tesseract options

        Returns:
            Extraction result dictionary
        """
        if not self.tesseract_available:
            raise RuntimeError("Tesseract not available")

        logger.info(f"Extracting with Tesseract: {file_path}, language={language}")

        # Handle PDF (convert to images first)
        file_ext = Path(file_path).suffix.lower()
        if file_ext == ".pdf":
            return await self._extract_pdf_with_tesseract(file_path, language, **kwargs)

        # Handle images directly
        try:
            image = Image.open(file_path)

            # Extract text with confidence
            data = pytesseract.image_to_data(
                image,
                lang=language,
                output_type=pytesseract.Output.DICT
            )

            # Combine text
            text = " ".join([
                word for word in data['text']
                if word.strip() != ""
            ])

            # Calculate average confidence
            confidences = [
                int(conf) for conf in data['conf']
                if conf != '-1'
            ]
            avg_confidence = sum(confidences) / len(confidences) / 100.0 if confidences else 0.0

            return {
                "text": text,
                "method_used": "tesseract",
                "confidence": avg_confidence,
                "pages": 1,
                "metadata": {
                    "language": language,
                    "words_detected": len(data['text']),
                    "avg_confidence": avg_confidence
                }
            }

        except Exception as e:
            logger.error(f"Tesseract image extraction failed: {e}")
            raise

    async def _extract_pdf_with_tesseract(
        self,
        pdf_path: str,
        language: str = "eng",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Extract text from PDF using Tesseract (convert PDF to images first).

        Note: This requires pdf2image package for production use.
        For now, we'll try to use Pillow directly if possible.

        Args:
            pdf_path: Path to PDF file
            language: Tesseract language code
            **kwargs: Additional options

        Returns:
            Extraction result dictionary
        """
        logger.warning(
            "Tesseract PDF extraction requires pdf2image package. "
            "Consider using Docling for PDFs instead."
        )

        # For now, raise error and force fallback to Docling
        raise RuntimeError(
            "Tesseract PDF extraction not fully implemented. "
            "Install pdf2image or use Docling for PDFs."
        )

    def get_available_backends(self) -> List[str]:
        """
        Get list of available OCR backends.

        Returns:
            List of backend names
        """
        backends = []
        if self.docling_available:
            backends.append("docling")
        if self.tesseract_available:
            backends.append("tesseract")
        return backends

    def get_status(self) -> Dict[str, Any]:
        """
        Get OCR service status.

        Returns:
            Status dictionary
        """
        return {
            "service": "ocr",
            "backends": {
                "docling": {
                    "available": self.docling_available,
                    "description": "IBM Docling - Advanced PDF/Document processor"
                },
                "tesseract": {
                    "available": self.tesseract_available,
                    "description": "Tesseract OCR - Open-source OCR engine"
                }
            },
            "ready": self.docling_available or self.tesseract_available
        }
