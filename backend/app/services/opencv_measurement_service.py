"""
OpenCV-based Geometric Measurement Service for Construction Drawings

This service provides computer vision capabilities for extracting metrics from
architectural drawings when they are not explicitly labeled.

Capabilities:
1. Scale bar detection and reading (e.g., "1:50", "1:100", "1:200")
2. Floor plan boundary detection using contour analysis
3. Area calculation from polygonal contours
4. Dimension measurement with pixel-to-meter conversion
5. Handling of irregular and complex floor shapes

Author: Construction Metrics Agent - Phase 2
Date: 2025-12-03
"""

import cv2
import numpy as np
import pytesseract
from typing import Dict, Any, Optional, List, Tuple
import logging
from pathlib import Path
import re

logger = logging.getLogger(__name__)


class OpenCVMeasurementService:
    """
    Computer vision service for precise geometric measurements from construction drawings.

    This service uses OpenCV to:
    - Detect scale bars in architectural drawings
    - Read scale ratios using OCR (1:50, 1:100, etc.)
    - Measure floor plan areas using contour detection
    - Convert pixel measurements to real-world dimensions
    """

    def __init__(self):
        """Initialize OpenCV Measurement Service"""
        self.scale_templates = self._load_scale_templates()
        logger.info("OpenCVMeasurementService initialized")

    def detect_scale_bar(self, image_path: str) -> Optional[Dict[str, Any]]:
        """
        Detect and read scale bar from architectural drawing.

        Architectural drawings typically have scale bars (rulers) showing the
        scale ratio like "1:100" which means 1cm on the drawing = 1m in reality.

        Args:
            image_path: Path to image or PDF file

        Returns:
            {
                "scale_ratio": float,      # e.g., 1.0 for 1:100 (1cm = 1m)
                "scale_text": str,         # e.g., "1:100"
                "confidence": float,       # 0.0-1.0
                "location": (x, y, w, h),  # Bounding box of scale bar
                "method": str              # Detection method used
            }
            or None if no scale bar found
        """
        try:
            # Load image
            if image_path.lower().endswith('.pdf'):
                # For PDFs, convert first page to image
                img = self._pdf_to_image(image_path)
            else:
                img = cv2.imread(image_path)

            if img is None:
                logger.error(f"Could not load image: {image_path}")
                return None

            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # Method 1: Look for horizontal lines (scale bars often have ruler marks)
            scale_result = self._detect_scale_by_lines(gray, img)
            if scale_result:
                logger.info(f"Scale detected (line method): {scale_result['scale_text']}")
                return scale_result

            # Method 2: Look for scale text anywhere in the image
            scale_result = self._detect_scale_by_text(gray, img)
            if scale_result:
                logger.info(f"Scale detected (text method): {scale_result['scale_text']}")
                return scale_result

            logger.warning(f"No scale bar found in {image_path}")
            return None

        except Exception as e:
            logger.error(f"Error detecting scale bar in {image_path}: {e}")
            return None

    def _detect_scale_by_lines(
        self,
        gray: np.ndarray,
        img: np.ndarray
    ) -> Optional[Dict[str, Any]]:
        """
        Detect scale bar by finding horizontal lines (ruler marks).

        Args:
            gray: Grayscale image
            img: Original color image

        Returns:
            Scale detection result or None
        """
        # Detect horizontal lines using morphology
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (50, 1))
        detected_lines = cv2.morphologyEx(gray, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)

        # Find contours
        contours, _ = cv2.findContours(detected_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Get image dimensions
        img_height, img_width = gray.shape

        # Look for scale bar candidates (horizontal lines near bottom of page)
        scale_candidates = []

        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)

            # Scale bars typically:
            # - Horizontal (width >> height)
            # - Moderate width (5-20% of page width)
            # - Near bottom (y > 70% of height) or top (y < 20% of height)
            is_horizontal = w > h * 5
            is_moderate_width = 0.05 * img_width < w < 0.25 * img_width
            is_near_bottom = y > 0.70 * img_height
            is_near_top = y < 0.20 * img_height

            if is_horizontal and is_moderate_width and (is_near_bottom or is_near_top):
                scale_candidates.append((x, y, w, h))

        # Try OCR on each candidate region
        for x, y, w, h in scale_candidates:
            # Expand region slightly to capture text near ruler
            roi = gray[max(0, y-20):min(img_height, y+h+20),
                      max(0, x-10):min(img_width, x+w+10)]

            # Apply thresholding for better OCR
            _, thresh = cv2.threshold(roi, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # OCR
            scale_text = pytesseract.image_to_string(thresh, config='--psm 6')
            scale_ratio = self._parse_scale_text(scale_text)

            if scale_ratio:
                return {
                    "scale_ratio": scale_ratio,
                    "scale_text": self._extract_scale_string(scale_text),
                    "confidence": 0.8,
                    "location": (x, y, w, h),
                    "method": "line_detection"
                }

        return None

    def _detect_scale_by_text(
        self,
        gray: np.ndarray,
        img: np.ndarray
    ) -> Optional[Dict[str, Any]]:
        """
        Detect scale by searching for scale text (e.g., "SCALE 1:100") anywhere in image.

        Args:
            gray: Grayscale image
            img: Original color image

        Returns:
            Scale detection result or None
        """
        img_height, img_width = gray.shape

        # Focus on bottom third of image (common location for title blocks with scale)
        bottom_third = gray[int(img_height * 0.66):, :]

        # Apply thresholding for better OCR
        _, thresh = cv2.threshold(bottom_third, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # OCR
        text = pytesseract.image_to_string(thresh, config='--psm 6')
        scale_ratio = self._parse_scale_text(text)

        if scale_ratio:
            return {
                "scale_ratio": scale_ratio,
                "scale_text": self._extract_scale_string(text),
                "confidence": 0.7,
                "location": (0, int(img_height * 0.66), img_width, int(img_height * 0.34)),
                "method": "text_search"
            }

        return None

    def _parse_scale_text(self, text: str) -> Optional[float]:
        """
        Parse scale text like "1:100", "1:50", "SCALE 1:200" to ratio.

        Scale Interpretation:
        - "1:100" means 1cm on drawing = 100cm in reality = 1 meter
        - "1:50" means 1cm on drawing = 50cm in reality = 0.5 meters
        - "1:200" means 1cm on drawing = 200cm in reality = 2 meters

        Args:
            text: OCR text containing scale

        Returns:
            Scale ratio as meters per centimeter (e.g., 1.0 for 1:100)
            None if no valid scale found
        """
        # Match patterns: "1:100", "1:50", "SCALE 1:200", "@ 1:100", etc.
        match = re.search(r'1\s*[:@]\s*(\d+)', text, re.IGNORECASE)
        if match:
            scale_denominator = int(match.group(1))
            # Convert: 1:100 means 1cm drawing = 100cm reality = 1m reality
            # So 1cm on drawing = (scale_denominator / 100) meters
            return scale_denominator / 100  # e.g., 100/100 = 1.0 for 1:100

        return None

    def _extract_scale_string(self, text: str) -> str:
        """Extract the scale string (e.g., '1:100') from OCR text"""
        match = re.search(r'1\s*[:@]\s*\d+', text, re.IGNORECASE)
        if match:
            # Clean up whitespace
            scale_str = match.group(0).replace(' ', '')
            # Normalize to colon format
            return scale_str.replace('@', ':')
        return "unknown"

    def measure_floor_plan_area(
        self,
        image_path: str,
        scale_ratio: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Measure floor plan area using contour detection.

        This method detects the boundaries of floor plans in the image and
        calculates their areas. If a scale_ratio is provided, it converts
        pixel areas to real-world square meters.

        Args:
            image_path: Path to floor plan image
            scale_ratio: Scale ratio from detect_scale_bar() (meters per cm)

        Returns:
            {
                "floor_areas": [
                    {"floor": "Floor 1", "area_m2": 850.5, "confidence": 0.75}
                ],
                "total_area_m2": 850.5,
                "confidence": 0.75,
                "method": "opencv_contour",
                "scale_used": scale_ratio
            }
        """
        try:
            # Load image
            if image_path.lower().endswith('.pdf'):
                img = self._pdf_to_image(image_path)
            else:
                img = cv2.imread(image_path)

            if img is None:
                logger.error(f"Could not load image: {image_path}")
                return self._empty_measurement_result()

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # Detect floor plan boundaries
            floor_contours = self._detect_floor_plan_contours(gray)

            if not floor_contours:
                logger.warning(f"No floor plan contours detected in {image_path}")
                return self._empty_measurement_result()

            # Calculate areas
            floor_areas = []
            for i, contour in enumerate(floor_contours):
                pixel_area = cv2.contourArea(contour)

                # Convert to real-world area if scale available
                if scale_ratio:
                    real_area_m2 = self._convert_pixel_area_to_m2(
                        pixel_area,
                        scale_ratio
                    )

                    floor_areas.append({
                        "floor": f"Floor {i+1}",
                        "area_m2": round(real_area_m2, 2),
                        "pixel_area": int(pixel_area),
                        "confidence": 0.7
                    })
                else:
                    # Return pixel area without conversion (low confidence)
                    floor_areas.append({
                        "floor": f"Floor {i+1}",
                        "pixel_area": int(pixel_area),
                        "area_m2": None,
                        "confidence": 0.3  # Low confidence without scale
                    })

            total_area = sum(f.get("area_m2", 0) or 0 for f in floor_areas)

            confidence = 0.7 if scale_ratio else 0.3

            return {
                "floor_areas": floor_areas,
                "total_area_m2": total_area if scale_ratio else None,
                "confidence": confidence,
                "method": "opencv_contour",
                "scale_used": scale_ratio
            }

        except Exception as e:
            logger.error(f"Error measuring floor plan area in {image_path}: {e}")
            return self._empty_measurement_result()

    def _detect_floor_plan_contours(self, gray: np.ndarray) -> List[np.ndarray]:
        """
        Detect floor plan boundaries using edge detection and contours.

        Args:
            gray: Grayscale image

        Returns:
            List of contours representing floor plan boundaries
        """
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Canny edge detection
        edges = cv2.Canny(blurred, 30, 100)

        # Dilate edges to close small gaps
        kernel = np.ones((3, 3), np.uint8)
        dilated = cv2.dilate(edges, kernel, iterations=2)

        # Find contours
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Filter contours: keep large ones (likely floor plans)
        img_area = gray.shape[0] * gray.shape[1]
        min_area = 0.02 * img_area  # At least 2% of image
        max_area = 0.80 * img_area  # At most 80% of image (avoid full-page borders)

        floor_contours = [
            c for c in contours
            if min_area < cv2.contourArea(c) < max_area
        ]

        # Sort by area (largest first)
        floor_contours.sort(key=cv2.contourArea, reverse=True)

        # Return top 5 largest contours (multiple floors)
        return floor_contours[:5]

    def _convert_pixel_area_to_m2(
        self,
        pixel_area: float,
        scale_ratio: float,
        dpi: int = 200
    ) -> float:
        """
        Convert pixel area to square meters using scale ratio.

        Args:
            pixel_area: Area in pixels²
            scale_ratio: Scale ratio (meters per cm on drawing)
            dpi: Image DPI (dots per inch), default 200

        Returns:
            Area in square meters
        """
        # Calculate pixels per centimeter
        # 1 inch = 2.54 cm
        # dpi pixels/inch = dpi/2.54 pixels/cm
        pixels_per_cm = dpi / 2.54

        # Convert pixel area to cm²
        cm_squared = pixel_area / (pixels_per_cm ** 2)

        # Convert cm² to m² using scale ratio
        # scale_ratio is meters per cm on drawing
        # So area in reality = cm² × (scale_ratio)²
        meters_squared = cm_squared * (scale_ratio ** 2)

        return meters_squared

    def _pdf_to_image(self, pdf_path: str, page: int = 0) -> Optional[np.ndarray]:
        """
        Convert PDF page to image for OpenCV processing.

        Args:
            pdf_path: Path to PDF file
            page: Page number (0-indexed)

        Returns:
            OpenCV image (numpy array) or None if conversion fails
        """
        try:
            # Use PyMuPDF (fitz) for PDF to image conversion
            import fitz  # PyMuPDF

            doc = fitz.open(pdf_path)
            page_obj = doc[page]

            # Render page to image at 200 DPI
            mat = fitz.Matrix(200/72, 200/72)  # 200 DPI
            pix = page_obj.get_pixmap(matrix=mat)

            # Convert to OpenCV format (BGR)
            img_data = pix.tobytes("ppm")

            # Decode to OpenCV image
            img_array = np.frombuffer(img_data, dtype=np.uint8)
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

            doc.close()

            return img

        except ImportError:
            logger.error("PyMuPDF (fitz) not installed. Cannot convert PDF to image.")
            logger.info("Install with: pip install PyMuPDF")
            return None
        except Exception as e:
            logger.error(f"Error converting PDF to image: {e}")
            return None

    def _empty_measurement_result(self) -> Dict[str, Any]:
        """Return empty measurement result structure"""
        return {
            "floor_areas": [],
            "total_area_m2": None,
            "confidence": 0.0,
            "method": "opencv_contour",
            "scale_used": None
        }

    def _load_scale_templates(self) -> List[np.ndarray]:
        """
        Load pre-defined scale bar templates for template matching.

        Future enhancement: Add template images for common scale bar styles
        to improve detection accuracy.

        Returns:
            List of OpenCV template images
        """
        # TODO: Add scale bar template images
        # Templates would be stored in backend/app/services/templates/scale_bars/
        return []


# ============================================================================
# Utility Functions
# ============================================================================

def calculate_derived_metrics(
    metrics: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Calculate derived metrics based on available data.

    For example:
    - External Area = Site Area - GFA (if both available)
    - Multi-floor GFA = Sum of floor areas

    Args:
        metrics: Dictionary of extracted metrics

    Returns:
        Updated metrics with derived values
    """
    # Calculate External Area if Site Area and GFA are known
    site_area = metrics.get('site_area_m2')
    gfa = metrics.get('gross_floor_area_m2')

    if site_area and gfa and not metrics.get('external_area_m2'):
        external_area = site_area - gfa
        if external_area > 0:
            metrics['external_area_m2'] = round(external_area, 2)
            metrics['external_area_calculation_method'] = 'derived_from_site_minus_gfa'
            logger.info(f"Derived External Area: {external_area:.2f} m² (Site - GFA)")

    return metrics
