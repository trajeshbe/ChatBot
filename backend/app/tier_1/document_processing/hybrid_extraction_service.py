"""
Hybrid Extraction Service - Combines OCR and Vision Models

This service provides comprehensive text and context extraction from technical
drawings and documents by combining:
1. OCR (Tesseract) - Fast, accurate text extraction
2. Vision Models (LLaMA 3.2 Vision) - Context understanding and visual reasoning

Author: AI Assistant
Date: 2025-12-02
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from enum import Enum

from app.tier_1.document_processing.ocr_service import ocr_service
from app.tier_1.document_processing.vision_service import VisionService

logger = logging.getLogger(__name__)


class ExtractionStrategy(str, Enum):
    """Extraction strategy options"""
    AUTO = "auto"
    OCR_ONLY = "ocr_only"
    VISION_ONLY = "vision_only"
    OCR_FIRST = "ocr_first"
    VISION_FIRST = "vision_first"
    BOTH_PARALLEL = "both_parallel"
    BOTH_SEQUENTIAL = "both_sequential"


class ContentType(str, Enum):
    """Content types from multi-analyzer"""
    VECTOR_GRAPHICS = "vector_graphics"
    IMAGE_HEAVY = "image_heavy"
    TEXT_HEAVY = "text_heavy"
    MIXED_CONTENT = "mixed_content"


class VisionModel(str, Enum):
    """Available vision models"""
    LLAMA_11B = "llama3.2-vision:11b"
    LLAMA_3B = "llama3.2-vision:3b"
    MINICPM_V = "minicpm-v:latest"
    GPT4V = "gpt-4-vision-preview"  # API-based
    CLAUDE_3_OPUS = "claude-3-opus-20240229"  # API-based


class HybridExtractionService:
    """
    Hybrid OCR + Vision Model extraction service

    Uses both Tesseract OCR and vision-language models for
    comprehensive image and drawing understanding.

    Strategies:
    - ocr_only: Fast text extraction (1-2 sec/page)
    - vision_only: Context understanding (5-10 sec/page)
    - ocr_first: OCR then fallback to vision if needed
    - vision_first: Vision then fallback to OCR if needed
    - both_parallel: Run both simultaneously (fastest for hybrid)
    - both_sequential: Run OCR then Vision (best quality)
    """

    # Vision model configurations
    VISION_MODEL_CONFIGS = {
        VisionModel.LLAMA_11B: {
            "memory_gb": 8,
            "speed_sec": 8,
            "quality": "excellent",
            "best_for": "Production use with GPU"
        },
        VisionModel.LLAMA_3B: {
            "memory_gb": 4,
            "speed_sec": 4,
            "quality": "very_good",
            "best_for": "Limited GPU memory"
        },
        VisionModel.MINICPM_V: {
            "memory_gb": 2,
            "speed_sec": 2,
            "quality": "good",
            "best_for": "CPU-only environments"
        },
        VisionModel.GPT4V: {
            "memory_gb": 0,
            "speed_sec": 3,
            "quality": "excellent",
            "best_for": "No local GPU, API usage"
        },
        VisionModel.CLAUDE_3_OPUS: {
            "memory_gb": 0,
            "speed_sec": 3,
            "quality": "excellent",
            "best_for": "No local GPU, API usage"
        }
    }

    def __init__(self):
        """Initialize hybrid extraction service"""
        self.ocr_service = ocr_service
        self.vision_service = None  # Lazy initialization

        # Default configurations
        self.default_strategy = ExtractionStrategy.OCR_FIRST
        self.default_vision_model = VisionModel.LLAMA_11B

        logger.info("✅ HybridExtractionService initialized")

    def _get_vision_service(self) -> VisionService:
        """Lazy initialization of vision service"""
        if self.vision_service is None:
            self.vision_service = VisionService()
        return self.vision_service

    async def extract_from_document(
        self,
        file_path: str,
        content_type: str,
        strategy: str = "auto",
        vision_model: str = "llama3.2-vision:11b",
        custom_prompt: Optional[str] = None,
        allow_fallback: bool = False
    ) -> Dict[str, Any]:
        """
        Extract text and context from document using hybrid approach

        Args:
            file_path: Path to document/image file
            content_type: Content type from multi-analyzer (vector_graphics, image_heavy, etc.)
            strategy: Extraction strategy (auto, ocr_only, vision_only, both)
            vision_model: Vision model to use (llama3.2-vision:11b, etc.)
            custom_prompt: Custom prompt for vision model (overrides default)
            allow_fallback: Allow automatic model fallback for memory constraints (default: False)
                           Set to True for agent tasks (e.g., construction metrics)

        Returns:
            {
                "ocr_text": str,
                "vision_context": str,
                "combined_text": str,
                "confidence": float,
                "methods_used": List[str],
                "metadata": {
                    "strategy_used": str,
                    "ocr_confidence": float,
                    "vision_model": str,
                    "processing_time_ms": float,
                    "fallback_occurred": bool  # 🆕 Track if model fallback happened
                }
            }
        """
        import time
        start_time = time.time()

        logger.info(f"🔄 Hybrid extraction started for: {Path(file_path).name}")
        logger.info(f"   Content type: {content_type}")
        logger.info(f"   Strategy: {strategy}")

        # Auto-select strategy based on content type
        if strategy == ExtractionStrategy.AUTO:
            strategy = self._select_strategy(content_type)
            logger.info(f"   Auto-selected strategy: {strategy}")

        results = {}

        try:
            # Execute extraction based on strategy
            # 🆕 CRITICAL FIX: Pass allow_fallback to all vision-based strategies
            if strategy == ExtractionStrategy.OCR_ONLY:
                results = await self._ocr_only(file_path)

            elif strategy == ExtractionStrategy.VISION_ONLY:
                results = await self._vision_only(
                    file_path,
                    content_type,
                    vision_model,
                    custom_prompt,
                    allow_fallback  # 🆕 Enable fallback for agent tasks
                )

            elif strategy == ExtractionStrategy.OCR_FIRST:
                results = await self._ocr_first(
                    file_path,
                    content_type,
                    vision_model,
                    custom_prompt,
                    allow_fallback  # 🆕 Enable fallback for agent tasks
                )

            elif strategy == ExtractionStrategy.VISION_FIRST:
                results = await self._vision_first(
                    file_path,
                    content_type,
                    vision_model,
                    custom_prompt,
                    allow_fallback  # 🆕 Enable fallback for agent tasks
                )

            elif strategy == ExtractionStrategy.BOTH_PARALLEL:
                results = await self._both_parallel(
                    file_path,
                    content_type,
                    vision_model,
                    custom_prompt,
                    allow_fallback  # 🆕 Enable fallback for agent tasks
                )

            elif strategy == ExtractionStrategy.BOTH_SEQUENTIAL:
                results = await self._both_sequential(
                    file_path,
                    content_type,
                    vision_model,
                    custom_prompt,
                    allow_fallback  # 🆕 Enable fallback for agent tasks
                )

            else:
                raise ValueError(f"Unknown strategy: {strategy}")

            # Add metadata
            results["metadata"]["strategy_used"] = strategy
            results["metadata"]["processing_time_ms"] = (time.time() - start_time) * 1000

            logger.info(f"✅ Hybrid extraction complete: {results['metadata']['processing_time_ms']:.2f}ms")
            logger.info(f"   Methods used: {results['methods_used']}")
            logger.info(f"   Combined text length: {len(results['combined_text'])} chars")

            return results

        except Exception as e:
            logger.error(f"❌ Hybrid extraction failed: {str(e)}")
            raise

    # ============================================================================
    # Strategy Implementations
    # ============================================================================

    async def _ocr_only(self, file_path: str) -> Dict[str, Any]:
        """OCR-only extraction (fast, text-focused)"""
        logger.info("   Running: OCR-only extraction")

        ocr_result = await self.ocr_service.extract_text(
            file_path=file_path,
            method="auto"  # Auto-select best OCR method
        )

        return {
            "ocr_text": ocr_result.get("text", ""),
            "vision_context": "",
            "combined_text": ocr_result.get("text", ""),
            "confidence": ocr_result.get("confidence", 0.0),
            "methods_used": ["ocr"],
            "metadata": {
                "ocr_method": ocr_result.get("method_used", "unknown"),
                "ocr_confidence": ocr_result.get("confidence", 0.0),
                "ocr_metadata": ocr_result.get("metadata", {})
            }
        }

    def _convert_pdf_to_images(self, pdf_path: str, output_dir: str = "/tmp") -> List[str]:
        """
        Convert PDF pages to images for vision model processing

        Args:
            pdf_path: Path to PDF file
            output_dir: Directory to save images

        Returns:
            List of image file paths
        """
        import fitz  # PyMuPDF
        from pathlib import Path

        pdf_name = Path(pdf_path).stem
        doc = fitz.open(pdf_path)
        image_paths = []

        for page_num in range(len(doc)):
            page = doc[page_num]

            # Render page at 300 DPI for good quality
            mat = fitz.Matrix(300/72, 300/72)
            pix = page.get_pixmap(matrix=mat)

            # Save as PNG
            image_path = f"{output_dir}/{pdf_name}_page_{page_num + 1}.png"
            pix.save(image_path)
            image_paths.append(image_path)

        doc.close()
        logger.info(f"   Converted PDF to {len(image_paths)} images")
        return image_paths

    async def _vision_only(
        self,
        file_path: str,
        content_type: str,
        vision_model: str,
        custom_prompt: Optional[str],
        allow_fallback: bool = False
    ) -> Dict[str, Any]:
        """Vision-only extraction (context understanding)"""
        logger.info(f"   Running: Vision-only extraction with {vision_model}")
        if allow_fallback:
            logger.info("   ✅ Fallback enabled for memory constraints")

        # Convert PDF to images if needed
        import os
        if file_path.lower().endswith('.pdf'):
            logger.info("   Converting PDF to images for vision processing...")
            image_paths = self._convert_pdf_to_images(file_path)
            # Process first few pages (limit to 10 for performance)
            image_paths = image_paths[:10]
        else:
            image_paths = [file_path]

        vision_service = self._get_vision_service()
        prompt = custom_prompt or self._get_vision_prompt(content_type)

        # Process all images and combine results
        all_vision_text = []
        fallback_occurred = False
        model_used = vision_model

        for image_path in image_paths:
            # 🆕 CRITICAL FIX: Pass allow_fallback to vision service
            vision_result = await vision_service.process_image(
                image_path=image_path,
                prompt=prompt,
                allow_fallback=allow_fallback
            )
            vision_text = vision_result.get("text", "")
            if vision_text:
                all_vision_text.append(vision_text)

            # Track fallback metadata
            if vision_result.get("metadata", {}).get("fallback_occurred"):
                fallback_occurred = True
                model_used = vision_result.get("model", vision_model)

        # Cleanup temporary images
        if file_path.lower().endswith('.pdf'):
            for img_path in image_paths:
                try:
                    os.remove(img_path)
                except:
                    pass

        combined_vision_text = "\n\n".join(all_vision_text)

        return {
            "ocr_text": "",
            "vision_context": combined_vision_text,
            "combined_text": combined_vision_text,
            "confidence": 0.85,  # Default vision confidence
            "methods_used": ["vision"],
            "metadata": {
                "vision_model": model_used,  # 🆕 Track actual model used
                "pages_processed": len(image_paths),
                "total_images": len(image_paths),
                "fallback_occurred": fallback_occurred  # 🆕 Track fallback
            }
        }

    async def _ocr_first(
        self,
        file_path: str,
        content_type: str,
        vision_model: str,
        custom_prompt: Optional[str],
        allow_fallback: bool = False
    ) -> Dict[str, Any]:
        """OCR first, fallback to vision if confidence low"""
        logger.info("   Running: OCR-first strategy")

        # Try OCR first
        ocr_result = await self._ocr_only(file_path)

        # Check if OCR confidence is acceptable
        ocr_confidence = ocr_result["confidence"]

        if ocr_confidence >= 0.70:  # Good OCR result
            logger.info(f"   ✅ OCR confidence acceptable: {ocr_confidence:.2%}")
            return ocr_result
        else:
            logger.info(f"   ⚠️  OCR confidence low: {ocr_confidence:.2%}, falling back to vision")
            # Fallback to vision
            # 🆕 CRITICAL FIX: Pass allow_fallback to vision
            vision_result = await self._vision_only(
                file_path,
                content_type,
                vision_model,
                custom_prompt,
                allow_fallback
            )
            return vision_result

    async def _vision_first(
        self,
        file_path: str,
        content_type: str,
        vision_model: str,
        custom_prompt: Optional[str],
        allow_fallback: bool = False
    ) -> Dict[str, Any]:
        """Vision first, fallback to OCR if vision fails"""
        logger.info("   Running: Vision-first strategy")

        try:
            # Try vision first
            # 🆕 CRITICAL FIX: Pass allow_fallback to vision
            vision_result = await self._vision_only(
                file_path,
                content_type,
                vision_model,
                custom_prompt,
                allow_fallback
            )

            if vision_result["vision_context"]:
                logger.info("   ✅ Vision extraction successful")
                return vision_result
            else:
                raise ValueError("Vision returned empty result")

        except Exception as e:
            logger.warning(f"   ⚠️  Vision failed: {str(e)}, falling back to OCR")
            # Fallback to OCR
            ocr_result = await self._ocr_only(file_path)
            return ocr_result

    async def _both_parallel(
        self,
        file_path: str,
        content_type: str,
        vision_model: str,
        custom_prompt: Optional[str],
        allow_fallback: bool = False
    ) -> Dict[str, Any]:
        """Run OCR and Vision in parallel (fastest hybrid)"""
        logger.info("   Running: Both parallel extraction")

        # Run both simultaneously
        ocr_task = asyncio.create_task(self._ocr_only(file_path))
        # 🆕 CRITICAL FIX: Pass allow_fallback to vision
        vision_task = asyncio.create_task(
            self._vision_only(file_path, content_type, vision_model, custom_prompt, allow_fallback)
        )

        # Wait for both
        ocr_result, vision_result = await asyncio.gather(ocr_task, vision_task)

        # Merge results
        return self._merge_results(ocr_result, vision_result)

    async def _both_sequential(
        self,
        file_path: str,
        content_type: str,
        vision_model: str,
        custom_prompt: Optional[str],
        allow_fallback: bool = False
    ) -> Dict[str, Any]:
        """Run OCR then Vision sequentially (best quality)"""
        logger.info("   Running: Both sequential extraction")

        # Run OCR first
        ocr_result = await self._ocr_only(file_path)

        # Then run vision
        # 🆕 CRITICAL FIX: Pass allow_fallback to vision
        vision_result = await self._vision_only(
            file_path,
            content_type,
            vision_model,
            custom_prompt,
            allow_fallback
        )

        # Merge results
        return self._merge_results(ocr_result, vision_result)

    # ============================================================================
    # Helper Methods
    # ============================================================================

    def _select_strategy(self, content_type: str) -> str:
        """
        Auto-select extraction strategy based on content type

        Rules:
        - vector_graphics: Both parallel (technical drawings need both)
        - image_heavy: Vision first (photos/diagrams benefit from vision)
        - text_heavy: OCR only (standard text doesn't need vision)
        - mixed_content: OCR first (balanced approach)
        """
        strategy_map = {
            ContentType.VECTOR_GRAPHICS: ExtractionStrategy.BOTH_PARALLEL,
            ContentType.IMAGE_HEAVY: ExtractionStrategy.VISION_FIRST,
            ContentType.TEXT_HEAVY: ExtractionStrategy.OCR_ONLY,
            ContentType.MIXED_CONTENT: ExtractionStrategy.OCR_FIRST
        }

        return strategy_map.get(content_type, ExtractionStrategy.OCR_FIRST)

    def _get_vision_prompt(self, content_type: str) -> str:
        """Get appropriate prompt for vision model based on content type"""

        prompts = {
            ContentType.VECTOR_GRAPHICS: (
                "This is a technical drawing or CAD plan. Please analyze it comprehensively and provide:\n\n"
                "1. **Type of drawing**: Identify if it's a floor plan, elevation, section, detail, or other type\n"
                "2. **Key measurements and dimensions**: Extract all visible dimensions, areas, and measurements\n"
                "3. **Important annotations and labels**: List all text labels, room names, equipment names, etc.\n"
                "4. **Specifications and requirements**: Note any technical specifications or requirements\n"
                "5. **Overall purpose**: Describe the overall purpose or function shown in the drawing\n"
                "6. **Critical information**: Extract any critical information like:\n"
                "   - Gross Floor Area (GFA)\n"
                "   - External Area\n"
                "   - Number of levels above ground\n"
                "   - Number of levels below ground\n"
                "   - Building height\n"
                "   - Any other key metrics\n\n"
                "Please be thorough and precise in your extraction."
            ),

            ContentType.IMAGE_HEAVY: (
                "Analyze this image in detail. Please describe:\n\n"
                "1. **Main subjects**: What are the primary subjects or objects in the image?\n"
                "2. **Text visible**: Any text, signs, labels, captions, or annotations visible\n"
                "3. **Context and purpose**: What is the context and apparent purpose of this image?\n"
                "4. **Notable details**: Any notable details, patterns, or elements worth mentioning\n"
                "5. **Technical information**: Any technical information, measurements, or specifications\n\n"
                "Be comprehensive and detailed in your description."
            ),

            ContentType.MIXED_CONTENT: (
                "This document contains mixed content (text and images). Please:\n\n"
                "1. Identify and extract all visible text\n"
                "2. Describe any images, diagrams, or illustrations\n"
                "3. Note the relationship between text and visual elements\n"
                "4. Extract any important information, metrics, or data\n\n"
                "Provide a complete analysis of all content."
            )
        }

        return prompts.get(
            content_type,
            "Please analyze this image and extract all visible text and relevant information."
        )

    def _merge_results(
        self,
        ocr_result: Dict[str, Any],
        vision_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge OCR and Vision results intelligently

        Creates combined text with clear attribution for traceability
        """
        ocr_text = ocr_result.get("ocr_text", "")
        vision_text = vision_result.get("vision_context", "")

        # Combine with clear attribution
        combined_parts = []

        if ocr_text:
            combined_parts.append("=== OCR EXTRACTED TEXT ===\n\n" + ocr_text)

        if vision_text:
            combined_parts.append("=== VISION MODEL ANALYSIS ===\n\n" + vision_text)

        combined_text = "\n\n".join(combined_parts)

        # Calculate overall confidence
        confidence = self._calculate_confidence(ocr_result, vision_result)

        return {
            "ocr_text": ocr_text,
            "vision_context": vision_text,
            "combined_text": combined_text,
            "confidence": confidence,
            "methods_used": ["ocr", "vision"],
            "metadata": {
                "ocr_method": ocr_result.get("metadata", {}).get("ocr_method", "unknown"),
                "ocr_confidence": ocr_result.get("confidence", 0.0),
                "ocr_metadata": ocr_result.get("metadata", {}),
                "vision_model": vision_result.get("metadata", {}).get("vision_model", "unknown"),
                "vision_metadata": vision_result.get("metadata", {})
            }
        }

    def _calculate_confidence(
        self,
        ocr_result: Dict[str, Any],
        vision_result: Dict[str, Any]
    ) -> float:
        """
        Calculate overall confidence from OCR and Vision results

        Strategy: Weighted average based on text length
        - More text from OCR → higher weight for OCR confidence
        - More text from Vision → higher weight for vision confidence
        """
        ocr_text = ocr_result.get("ocr_text", "")
        vision_text = vision_result.get("vision_context", "")

        ocr_conf = ocr_result.get("confidence", 0.0)
        vision_conf = 0.85  # Default vision confidence

        ocr_len = len(ocr_text)
        vision_len = len(vision_text)
        total_len = ocr_len + vision_len

        if total_len == 0:
            return 0.0

        # Weighted average
        ocr_weight = ocr_len / total_len
        vision_weight = vision_len / total_len

        combined_confidence = (ocr_conf * ocr_weight) + (vision_conf * vision_weight)

        return combined_confidence

    def get_available_vision_models(self) -> Dict[str, Dict[str, Any]]:
        """Get list of available vision models with their configurations"""
        return self.VISION_MODEL_CONFIGS.copy()

    def get_recommended_strategy(self, content_type: str) -> Dict[str, Any]:
        """Get recommended strategy and vision model for content type"""
        strategy = self._select_strategy(content_type)

        # Recommend vision model based on content type
        if content_type == ContentType.VECTOR_GRAPHICS:
            recommended_model = VisionModel.LLAMA_11B  # Best quality for technical
        elif content_type == ContentType.IMAGE_HEAVY:
            recommended_model = VisionModel.LLAMA_3B  # Good balance
        else:
            recommended_model = VisionModel.MINICPM_V  # Lightweight

        return {
            "content_type": content_type,
            "recommended_strategy": strategy,
            "recommended_vision_model": recommended_model,
            "model_config": self.VISION_MODEL_CONFIGS.get(recommended_model, {})
        }


# ============================================================================
# Singleton Instance
# ============================================================================

hybrid_extraction_service = HybridExtractionService()
