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
    import numpy as np
    import cv2
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
        extract_embedded_images: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Extract text with intelligent method selection + embedded image OCR.

        Comprehensively extracts text from:
        - Document text content (via Docling)
        - PDF pages rendered as images (via Tesseract)
        - Embedded images in PDFs, DOCX, PPTX, XLSX (via Tesseract)

        Args:
            file_path: Path to document/image file
            method: Extraction method ("auto", "docling", "tesseract")
            language: Tesseract language code (default: "eng")
            extract_embedded_images: Extract and OCR embedded images (default: True)
            **kwargs: Additional method-specific options

        Returns:
            {
                "text": str,                    # Extracted text content
                "method_used": str,             # "docling" or "tesseract"
                "confidence": float,            # 0.0-1.0
                "pages": int,                   # Number of pages processed
                "file_path": str,               # Original file path
                "file_type": str,               # File extension
                "embedded_images_text": str,    # Text from embedded images
                "embedded_images_count": int,   # Number of images processed
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

        Uses PyMuPDF to render PDF pages as high-resolution images,
        then applies Tesseract OCR with preprocessing optimized for technical drawings.

        Args:
            pdf_path: Path to PDF file
            language: Tesseract language code
            **kwargs: Additional options

        Returns:
            Extraction result dictionary
        """
        try:
            import fitz  # PyMuPDF
            import cv2
            import numpy as np
            from io import BytesIO
        except ImportError as e:
            logger.error(f"Required library not available for PDF OCR: {e}")
            raise RuntimeError(
                "PDF OCR requires PyMuPDF, cv2, and numpy. "
                "Please install with: pip install PyMuPDF opencv-python numpy"
            )

        logger.info(f"Extracting PDF with Tesseract OCR: {pdf_path}")

        try:
            doc = fitz.open(pdf_path)
            all_text = []
            all_confidences = []
            total_words = 0

            for page_num in range(len(doc)):
                page = doc[page_num]

                # Render page at high DPI for better OCR (300 DPI)
                mat = fitz.Matrix(300/72, 300/72)
                pix = page.get_pixmap(matrix=mat)

                # Convert to PIL Image
                img_data = pix.tobytes("png")
                img = Image.open(BytesIO(img_data))

                # Convert to numpy array for preprocessing
                img_array = np.array(img)

                # Preprocess for technical drawings
                preprocessed = self._preprocess_for_technical_drawings(img_array)

                # Run Tesseract OCR with confidence data
                try:
                    data = pytesseract.image_to_data(
                        preprocessed,
                        lang=language,
                        config=r'--oem 3 --psm 11',  # Sparse text mode (good for drawings)
                        output_type=pytesseract.Output.DICT
                    )

                    # Extract text from this page
                    page_text = []
                    page_confidences = []

                    for i in range(len(data['text'])):
                        if data['conf'][i] != '-1' and int(data['conf'][i]) > 0:
                            word = data['text'][i].strip()
                            if word:
                                page_text.append(word)
                                page_confidences.append(int(data['conf'][i]))
                                total_words += 1

                    if page_text:
                        all_text.append(" ".join(page_text))
                        all_confidences.extend(page_confidences)

                    logger.debug(f"   Page {page_num + 1}: {len(page_text)} words extracted")

                except Exception as e:
                    logger.warning(f"OCR failed for page {page_num + 1}: {e}")
                    continue

            doc.close()

            # Combine all pages
            full_text = "\n\n".join(all_text)

            # Calculate average confidence
            avg_confidence = sum(all_confidences) / len(all_confidences) / 100.0 if all_confidences else 0.0

            logger.info(f"Tesseract PDF extraction complete: {len(doc)} pages, {total_words} words, {avg_confidence:.1%} confidence")

            return {
                "text": full_text,
                "method_used": "tesseract (PDF OCR)",
                "confidence": avg_confidence,
                "pages": len(doc),
                "metadata": {
                    "language": language,
                    "words_detected": total_words,
                    "avg_confidence": avg_confidence,
                    "dpi": 300,
                    "preprocessing": "technical_drawings"
                }
            }

        except Exception as e:
            logger.error(f"Tesseract PDF extraction failed: {e}", exc_info=True)
            raise

    def _preprocess_for_technical_drawings(self, img_array: np.ndarray) -> np.ndarray:
        """
        Preprocess image for better OCR on technical drawings.

        Technical drawings typically have:
        - High contrast lines
        - Small text annotations
        - Mixed text sizes
        - Background grid patterns

        Args:
            img_array: Input image as numpy array (RGB or grayscale)

        Returns:
            Preprocessed image optimized for OCR
        """
        import cv2
        import numpy as np

        # Convert to grayscale if needed
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array

        # Apply bilateral filter to reduce noise while preserving edges
        # (good for technical drawings with fine lines)
        filtered = cv2.bilateralFilter(gray, 9, 75, 75)

        # Adaptive thresholding (works well for varying lighting/contrast)
        binary = cv2.adaptiveThreshold(
            filtered,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11,  # Block size
            2    # Constant subtracted from mean
        )

        # Optional: Morphological operations to clean up small noise
        kernel = np.ones((2, 2), np.uint8)
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

        return cleaned

    async def extract_all_embedded_images(
        self,
        file_path: str,
        language: str = "eng"
    ) -> Dict[str, Any]:
        """
        Extract and OCR all embedded images from document.

        Supports: PDF, DOCX, PPTX, XLSX

        Args:
            file_path: Path to document
            language: Tesseract language code

        Returns:
            {
                "images_extracted": int,
                "text_from_images": str,
                "confidence": float,
                "images_detail": List[Dict]
            }
        """
        file_ext = Path(file_path).suffix.lower()

        logger.info(f"🖼️  Extracting embedded images from {file_ext} document...")

        # Extract images based on file type
        images = []

        if file_ext == ".pdf":
            images = await self._extract_images_from_pdf(file_path)
        elif file_ext == ".docx":
            images = await self._extract_images_from_docx(file_path)
        elif file_ext == ".pptx":
            images = await self._extract_images_from_pptx(file_path)
        elif file_ext == ".xlsx":
            images = await self._extract_images_from_xlsx(file_path)
        else:
            logger.warning(f"Image extraction not supported for {file_ext}")
            return {
                "images_extracted": 0,
                "text_from_images": "",
                "confidence": 0.0,
                "images_detail": []
            }

        if not images:
            logger.info("No embedded images found")
            return {
                "images_extracted": 0,
                "text_from_images": "",
                "confidence": 0.0,
                "images_detail": []
            }

        logger.info(f"Found {len(images)} embedded images, running OCR...")

        # OCR each image
        results = await self._ocr_extracted_images(images, language)

        return results

    async def _extract_images_from_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Extract embedded raster images from PDF"""
        try:
            import fitz
            from io import BytesIO
        except ImportError:
            logger.error("PyMuPDF required for PDF image extraction")
            return []

        images = []
        doc = fitz.open(pdf_path)

        for page_num in range(len(doc)):
            page = doc[page_num]

            # Get list of images on this page
            image_list = page.get_images()

            for img_index, img in enumerate(image_list):
                xref = img[0]  # Image reference number

                # Extract image
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]

                # Convert to PIL Image
                img_pil = Image.open(BytesIO(image_bytes))

                images.append({
                    "source": "pdf",
                    "page": page_num + 1,
                    "index": img_index,
                    "format": image_ext,
                    "size": img_pil.size,
                    "image": img_pil
                })

        doc.close()

        logger.info(f"   Extracted {len(images)} embedded images from PDF")
        return images

    async def _extract_images_from_docx(self, docx_path: str) -> List[Dict[str, Any]]:
        """Extract embedded images from Word document"""
        try:
            from docx import Document as DocxDocument
            from io import BytesIO
        except ImportError:
            logger.error("python-docx required for DOCX image extraction")
            return []

        images = []
        doc = DocxDocument(docx_path)

        # Images are stored in document relationships
        for rel in doc.part.rels.values():
            if "image" in rel.target_ref:
                try:
                    image_bytes = rel.target_part.blob
                    img_pil = Image.open(BytesIO(image_bytes))

                    images.append({
                        "source": "docx",
                        "rel_id": rel.rId,
                        "format": img_pil.format,
                        "size": img_pil.size,
                        "image": img_pil
                    })
                except Exception as e:
                    logger.warning(f"Failed to extract image {rel.rId}: {e}")
                    continue

        logger.info(f"   Extracted {len(images)} embedded images from DOCX")
        return images

    async def _extract_images_from_pptx(self, pptx_path: str) -> List[Dict[str, Any]]:
        """Extract embedded images from PowerPoint"""
        try:
            from pptx import Presentation
            from io import BytesIO
        except ImportError:
            logger.error("python-pptx required for PPTX image extraction")
            return []

        images = []
        prs = Presentation(pptx_path)

        for slide_num, slide in enumerate(prs.slides):
            for shape in slide.shapes:
                if hasattr(shape, "image"):
                    try:
                        image_bytes = shape.image.blob
                        img_pil = Image.open(BytesIO(image_bytes))

                        images.append({
                            "source": "pptx",
                            "slide": slide_num + 1,
                            "format": img_pil.format,
                            "size": img_pil.size,
                            "image": img_pil
                        })
                    except Exception as e:
                        logger.warning(f"Failed to extract image from slide {slide_num + 1}: {e}")
                        continue

        logger.info(f"   Extracted {len(images)} embedded images from PPTX")
        return images

    async def _extract_images_from_xlsx(self, xlsx_path: str) -> List[Dict[str, Any]]:
        """Extract embedded images from Excel"""
        try:
            from openpyxl import load_workbook
            from openpyxl.drawing.image import Image as XlImage
            from io import BytesIO
        except ImportError:
            logger.error("openpyxl required for XLSX image extraction")
            return []

        images = []
        wb = load_workbook(xlsx_path)

        for sheet_name in wb.sheetnames:
            sheet = wb[sheet_name]

            # Check if sheet has images
            if hasattr(sheet, '_images'):
                for img_obj in sheet._images:
                    try:
                        # Get image bytes
                        image_bytes = img_obj._data()
                        img_pil = Image.open(BytesIO(image_bytes))

                        images.append({
                            "source": "xlsx",
                            "sheet": sheet_name,
                            "format": img_pil.format,
                            "size": img_pil.size,
                            "image": img_pil
                        })
                    except Exception as e:
                        logger.warning(f"Failed to extract image from {sheet_name}: {e}")
                        continue

        wb.close()

        logger.info(f"   Extracted {len(images)} embedded images from XLSX")
        return images

    async def _ocr_extracted_images(
        self,
        images: List[Dict[str, Any]],
        language: str = "eng"
    ) -> Dict[str, Any]:
        """
        Run OCR on all extracted images

        Args:
            images: List of extracted images with metadata
            language: Tesseract language code

        Returns:
            Combined OCR results
        """
        if not self.tesseract_available:
            logger.warning("Tesseract not available for image OCR")
            return {
                "images_extracted": len(images),
                "text_from_images": "",
                "confidence": 0.0,
                "images_detail": []
            }

        all_text = []
        all_confidences = []
        images_detail = []

        for i, img_data in enumerate(images):
            try:
                img_pil = img_data["image"]

                # Preprocess image
                img_array = np.array(img_pil.convert('RGB'))
                preprocessed = self._preprocess_for_technical_drawings(img_array)

                # Run OCR
                data = pytesseract.image_to_data(
                    preprocessed,
                    lang=language,
                    config=r'--oem 3 --psm 11',
                    output_type=pytesseract.Output.DICT
                )

                # Extract text
                image_text = []
                image_confidences = []

                for j in range(len(data['text'])):
                    if data['conf'][j] != '-1' and int(data['conf'][j]) > 0:
                        word = data['text'][j].strip()
                        if word:
                            image_text.append(word)
                            image_confidences.append(int(data['conf'][j]))

                if image_text:
                    text = " ".join(image_text)
                    confidence = sum(image_confidences) / len(image_confidences) / 100.0

                    all_text.append(f"\n--- Image {i+1} ({img_data['source']}) ---\n{text}")
                    all_confidences.extend(image_confidences)

                    images_detail.append({
                        "index": i + 1,
                        "source": img_data["source"],
                        "page": img_data.get("page"),
                        "slide": img_data.get("slide"),
                        "sheet": img_data.get("sheet"),
                        "words_extracted": len(image_text),
                        "confidence": confidence
                    })

                    logger.debug(f"      Image {i+1}: {len(image_text)} words ({confidence:.1%} confidence)")

            except Exception as e:
                logger.warning(f"OCR failed for image {i+1}: {e}")
                continue

        # Combine results
        combined_text = "\n".join(all_text)
        avg_confidence = sum(all_confidences) / len(all_confidences) / 100.0 if all_confidences else 0.0

        logger.info(f"✅ OCR complete: {len(images_detail)}/{len(images)} images processed ({avg_confidence:.1%} avg confidence)")

        return {
            "images_extracted": len(images),
            "text_from_images": combined_text,
            "confidence": avg_confidence,
            "images_detail": images_detail
        }

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


# Global singleton
ocr_service = OCRService()
