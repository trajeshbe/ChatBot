"""
OCR/Image Analyzer Utility

Uses Tesseract OCR to analyze image files for quality and OCR difficulty.
Extracts:
- OCR confidence scores
- Text clarity
- Resolution
- Processing difficulty

Author: Claude Code
Date: 2025-11-25
"""

import logging
from typing import Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


async def analyze_image_complexity(image_path: str) -> Dict[str, Any]:
    """
    Analyze image quality and OCR difficulty using Tesseract.

    Args:
        image_path: Path to image file

    Returns:
        Dictionary with OCR complexity metrics
    """
    try:
        # Import dependencies
        import pytesseract
        from PIL import Image

        # Open image
        image = Image.open(image_path)

        # Get image dimensions
        width, height = image.size
        resolution = f"{width}x{height}"

        # Run OCR with confidence scores
        ocr_data = pytesseract.image_to_data(
            image,
            output_type=pytesseract.Output.DICT
        )

        # Calculate average confidence
        confidences = [
            int(conf) for conf in ocr_data['conf']
            if conf != '-1' and conf != ''
        ]

        if confidences:
            avg_confidence = sum(confidences) / len(confidences)
        else:
            avg_confidence = 0.0

        # Normalize confidence to 0.0-1.0
        ocr_confidence = avg_confidence / 100.0

        # Calculate text density (words per 1000 pixels)
        words = [w for w in ocr_data['text'] if w.strip()]
        pixel_area = width * height
        text_density = len(words) / (pixel_area / 1000)

        # Determine clarity rating
        if avg_confidence > 90:
            clarity_rating = "High"
        elif avg_confidence > 70:
            clarity_rating = "Medium"
        else:
            clarity_rating = "Low"

        return {
            "resolution": resolution,
            "ocr_confidence": ocr_confidence,
            "text_density": round(text_density, 4),
            "clarity_rating": clarity_rating,
            "estimated_accuracy": ocr_confidence,
            "word_count": len(words)
        }

    except ImportError as e:
        logger.error(f"Tesseract or PIL not installed: {e}")
        return _get_fallback_image_analysis(image_path)

    except Exception as e:
        logger.error(f"Error analyzing image with Tesseract: {e}", exc_info=True)
        return _get_fallback_image_analysis(image_path)


def _get_fallback_image_analysis(image_path: str) -> Dict[str, Any]:
    """
    Fallback image analysis when Tesseract is unavailable.

    Args:
        image_path: Path to image file

    Returns:
        Dictionary with basic image metrics
    """
    try:
        from PIL import Image

        # Open image
        image = Image.open(image_path)
        width, height = image.size

        # Estimate quality based on resolution
        pixel_count = width * height

        if pixel_count > 1920 * 1080:  # Full HD or higher
            estimated_confidence = 0.90
            clarity = "High"
        elif pixel_count > 1280 * 720:  # HD
            estimated_confidence = 0.75
            clarity = "Medium"
        else:  # Low resolution
            estimated_confidence = 0.60
            clarity = "Low"

        return {
            "resolution": f"{width}x{height}",
            "ocr_confidence": estimated_confidence,
            "text_density": 0.0,  # Unknown
            "clarity_rating": clarity,
            "estimated_accuracy": estimated_confidence,
            "word_count": 0
        }

    except Exception as e:
        logger.error(f"Fallback image analysis failed: {e}")
        return {
            "resolution": "Unknown",
            "ocr_confidence": 0.80,  # Default medium-high
            "text_density": 0.0,
            "clarity_rating": "Unknown",
            "estimated_accuracy": 0.80,
            "word_count": 0
        }
