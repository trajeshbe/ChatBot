"""
Sample Complexity Analyzer Service

This service analyzes uploaded sample files (PDF, Excel, images) to determine
project complexity using LLM-based intelligent analysis with fallback to specialized tools.

Strategy:
1. Primary: Use LLM/vision services for intelligent analysis (RECOMMENDED)
2. Fallback: Use specialized libraries (Docling, Tesseract, openpyxl) when LLM unavailable

The complexity rating (Low/Medium/High) cascades through the workflow to:
- Adjust effort hours via multipliers
- Adjust billing rates
- Determine skill level requirements
- Add specialized teams when needed

Author: Claude Code
Date: 2025-11-25
"""

import os
import logging
import json
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class ComplexityAnalyzerService:
    """
    Analyzes uploaded sample files to determine project complexity.

    Primary Strategy: LLM/Vision-based Analysis
    - Uses vision_service.py for PDF/image analysis (intelligent understanding)
    - Uses llm_service.py for content assessment and complexity rating
    - Uses ocr_service.py for text extraction when needed
    - Uses document_service.py for document processing

    Fallback Strategy: Library-based Analysis
    - Docling for PDF structure analysis
    - Tesseract for OCR/image analysis
    - pandas/openpyxl for Excel complexity analysis
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.llm_service = None
        self.vision_service = None
        self.ocr_service = None

    async def _initialize_services(self):
        """Initialize LLM/vision services lazily (only when needed)."""
        if self.llm_service is None:
            try:
                from app.services.llm_service import llm_service
                self.llm_service = llm_service
                await self.llm_service.initialize()
                self.logger.info("✅ LLM service initialized for complexity analysis")
            except Exception as e:
                self.logger.warning(f"⚠️  Could not initialize LLM service: {e}")
                self.llm_service = None

        if self.vision_service is None:
            try:
                from app.services.vision_service import get_vision_service
                self.vision_service = await get_vision_service()
                self.logger.info("✅ Vision service initialized for complexity analysis")
            except Exception as e:
                self.logger.warning(f"⚠️  Could not initialize vision service: {e}")
                self.vision_service = None

        if self.ocr_service is None:
            try:
                from app.services.ocr_service import OCRService
                self.ocr_service = OCRService()
                self.logger.info("✅ OCR service initialized for complexity analysis")
            except Exception as e:
                self.logger.warning(f"⚠️  Could not initialize OCR service: {e}")
                self.ocr_service = None

    async def analyze_samples(
        self,
        brd_files: List[str] = None,
        cost_files: List[str] = None,
        sample_files: List[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze all uploaded sample files and return complexity assessment.

        Strategy:
        1. Try LLM/vision-based analysis first (intelligent, context-aware)
        2. Fall back to library-based analysis if LLM unavailable

        Args:
            brd_files: List of paths to BRD sample files (PDF, DOCX)
            cost_files: List of paths to cost estimation sample files (Excel)
            sample_files: List of paths to other sample files (images, data files)

        Returns:
            Dictionary with complexity analysis results
        """
        try:
            self.logger.info("="*80)
            self.logger.info("🔍 AGENT 1.1: Sample Complexity Analyzer - Starting Analysis")
            self.logger.info("="*80)

            brd_files = brd_files or []
            cost_files = cost_files or []
            sample_files = sample_files or []

            # If no samples provided, return default low complexity
            if not brd_files and not cost_files and not sample_files:
                self.logger.info("No sample files provided, returning default Low complexity")
                return self._get_default_complexity()

            self.logger.info(f"📊 Files to analyze:")
            self.logger.info(f"   - BRD files: {len(brd_files)}")
            self.logger.info(f"   - Cost files: {len(cost_files)}")
            self.logger.info(f"   - Sample files: {len(sample_files)}")

            # Initialize services
            await self._initialize_services()

            # Try LLM/vision-based analysis first
            if self.llm_service and self.vision_service:
                self.logger.info("\n🤖 Using LLM/Vision-based analysis (PRIMARY)")
                try:
                    result = await self._analyze_with_llm(
                        brd_files, cost_files, sample_files
                    )
                    self.logger.info("✅ LLM/Vision analysis successful")
                    return result
                except Exception as e:
                    self.logger.warning(f"⚠️  LLM/Vision analysis failed: {e}")
                    self.logger.info("🔄 Falling back to library-based analysis...")

            # Fallback: Library-based analysis
            self.logger.info("\n📚 Using library-based analysis (FALLBACK)")
            pdf_analysis = await self._analyze_pdf_files(brd_files)
            excel_analysis = await self._analyze_excel_files(cost_files)
            image_analysis = await self._analyze_image_files(sample_files)

            # Calculate overall complexity
            overall_rating, recommendations = self._calculate_overall_complexity(
                pdf_analysis,
                excel_analysis,
                image_analysis
            )

            # Build detailed analysis result
            result = {
                "complexity_analysis": {
                    "overall_rating": overall_rating,
                    "confidence_score": self._calculate_confidence(
                        len(brd_files) + len(cost_files) + len(sample_files)
                    ),

                    "detailed_analysis": {
                        "pdf_complexity": pdf_analysis,
                        "ocr_requirements": image_analysis,
                        "data_complexity": excel_analysis
                    },

                    "impact_on_estimation": recommendations,

                    "reasoning": self._generate_reasoning(
                        overall_rating,
                        pdf_analysis,
                        excel_analysis,
                        image_analysis,
                        len(brd_files),
                        len(cost_files),
                        len(sample_files)
                    )
                }
            }

            self.logger.info(f"Complexity analysis complete: {overall_rating} complexity")
            return result

        except Exception as e:
            self.logger.error(f"Error analyzing samples: {e}", exc_info=True)
            return self._get_default_complexity()

    async def _analyze_with_llm(
        self,
        brd_files: List[str],
        cost_files: List[str],
        sample_files: List[str]
    ) -> Dict[str, Any]:
        """
        Use LLM/vision services for intelligent complexity analysis (PRIMARY APPROACH).

        This method leverages:
        - vision_service for PDF/image understanding
        - llm_service for intelligent content assessment
        - ocr_service for text extraction when needed
        """
        self.logger.info("🤖 Starting LLM-based complexity analysis...")

        # Build comprehensive prompt for LLM
        analysis_parts = []

        # Analyze PDFs with vision/OCR
        for pdf_path in brd_files:
            if os.path.exists(pdf_path):
                try:
                    # Try vision service first
                    result = await self.vision_service.describe_image(
                        pdf_path,
                        question="Analyze this document's complexity. How many pages? Are there tables, charts, or complex layouts? Rate complexity as Low/Medium/High."
                    )
                    analysis_parts.append(f"PDF Analysis ({Path(pdf_path).name}): {result}")
                except Exception as e:
                    self.logger.warning(f"Vision analysis failed for {pdf_path}: {e}, trying OCR...")
                    try:
                        ocr_result = await self.ocr_service.extract_text(pdf_path)
                        text_preview = ocr_result.get("text", "")[:500]
                        analysis_parts.append(f"PDF OCR ({Path(pdf_path).name}): {len(text_preview)} chars extracted")
                    except:
                        pass

        # Analyze images
        for img_path in sample_files:
            if Path(img_path).suffix.lower() in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
                try:
                    result = await self.vision_service.describe_image(
                        img_path,
                        question="Describe this image. Is it a diagram, screenshot, or scanned document? How complex is it?"
                    )
                    analysis_parts.append(f"Image Analysis ({Path(img_path).name}): {result}")
                except Exception as e:
                    self.logger.warning(f"Vision analysis failed for {img_path}: {e}")

        # For Excel files, use library-based analysis (openpyxl is more reliable than vision for structured data)
        excel_summary = []
        for excel_path in cost_files:
            if os.path.exists(excel_path):
                try:
                    from app.utils.excel_analyzer import analyze_excel_complexity
                    analysis = await analyze_excel_complexity(excel_path)
                    excel_summary.append(f"Excel ({Path(excel_path).name}): {analysis.get('sheet_count', 0)} sheets, formula density {analysis.get('formula_density', 0):.0%}")
                except Exception as e:
                    self.logger.warning(f"Excel analysis failed: {e}")

        if excel_summary:
            analysis_parts.extend(excel_summary)

        # Build comprehensive prompt for LLM
        analyses_text = "\n\n".join(analysis_parts) if analysis_parts else "No detailed analysis available"

        prompt = f"""You are an expert project estimator analyzing sample files to determine project complexity.

Based on the following file analyses, rate the overall project complexity as Low, Medium, or High.

File Analyses:
{analyses_text}

Consider:
- Document structure (pages, tables, charts, forms)
- Data complexity (formulas, pivots, macros in Excel files)
- Image quality (if scanned documents or screenshots)
- Overall processing difficulty

Return ONLY a valid JSON object (no markdown, no code blocks) with this exact structure:
{{
    "overall_rating": "Low|Medium|High",
    "effort_multiplier": 1.0-1.8,
    "rate_multiplier": 1.0-1.30,
    "skill_level": "Mid|Senior|Senior/Expert",
    "recommended_teams": [],
    "reasoning": "Brief explanation"
}}

Multiplier Guidelines:
- Low: effort=1.0, rate=1.0, skill=Mid, teams=[]
- Medium: effort=1.3, rate=1.15, skill=Senior, teams=["Document Processing Team"]
- High: effort=1.8, rate=1.30, skill=Senior/Expert, teams=["Document Processing Team", "Data Engineering Team"]
"""

        # Get LLM assessment
        self.logger.info("📝 Sending complexity analysis request to LLM...")
        llm_response = await self.llm_service.generate(
            prompt=prompt,
            max_tokens=512,
            temperature=0.3  # Lower temperature for more consistent results
        )

        response_text = llm_response.get("content", "")
        self.logger.info(f"🤖 LLM Response: {response_text[:200]}...")

        # Parse LLM response
        try:
            # Try to extract JSON from response (handle markdown code blocks)
            json_text = response_text.strip()
            if "```json" in json_text:
                json_text = json_text.split("```json")[1].split("```")[0].strip()
            elif "```" in json_text:
                json_text = json_text.split("```")[1].split("```")[0].strip()

            llm_analysis = json.loads(json_text)

            # Build result
            overall_rating = llm_analysis.get("overall_rating", "Medium")
            effort_multiplier = float(llm_analysis.get("effort_multiplier", 1.3))
            rate_multiplier = float(llm_analysis.get("rate_multiplier", 1.15))
            skill_level = llm_analysis.get("skill_level", "Senior")
            recommended_teams = llm_analysis.get("recommended_teams", [])
            reasoning = llm_analysis.get("reasoning", "LLM-based complexity assessment")

            self.logger.info(f"✅ Complexity Rating: {overall_rating}")
            self.logger.info(f"   Effort Multiplier: {effort_multiplier}x")
            self.logger.info(f"   Rate Multiplier: {rate_multiplier}x")
            self.logger.info(f"   Skill Level: {skill_level}")
            self.logger.info(f"   Teams: {recommended_teams}")

            result = {
                "complexity_analysis": {
                    "overall_rating": overall_rating,
                    "confidence_score": 0.90,  # High confidence with LLM analysis

                    "detailed_analysis": {
                        "pdf_complexity": {
                            "files_analyzed": len(brd_files),
                            "structure_rating": overall_rating
                        },
                        "ocr_requirements": {
                            "files_analyzed": len([f for f in sample_files if Path(f).suffix.lower() in ['.png', '.jpg', '.jpeg']]),
                            "estimated_accuracy": overall_rating
                        },
                        "data_complexity": {
                            "files_analyzed": len(cost_files),
                            "processing_difficulty": overall_rating
                        }
                    },

                    "impact_on_estimation": {
                        "effort_multiplier": effort_multiplier,
                        "rate_multiplier": rate_multiplier,
                        "skill_requirements": {
                            "minimum_level": skill_level,
                            "specialized_skills": ["LLM-assessed complexity"]
                        },
                        "recommended_teams": recommended_teams
                    },

                    "reasoning": f"LLM-based analysis: {reasoning}. Analyzed {len(brd_files)} PDFs, {len(cost_files)} Excel files, {len(sample_files)} other files."
                }
            }

            self.logger.info("="*80)
            return result

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse LLM JSON response: {e}")
            self.logger.error(f"Raw response: {response_text}")
            raise Exception(f"LLM returned invalid JSON: {e}")

    async def _analyze_pdf_files(self, pdf_files: List[str]) -> Dict[str, Any]:
        """Analyze PDF files for structure complexity."""
        if not pdf_files:
            return {
                "average_pages": 0,
                "has_complex_layouts": False,
                "structure_rating": "N/A"
            }

        try:
            # Import Docling (only if needed)
            from app.utils.docling_analyzer import analyze_pdf_complexity

            total_pages = 0
            has_tables = False
            has_images = False
            structure_scores = []

            for pdf_path in pdf_files:
                if os.path.exists(pdf_path):
                    analysis = await analyze_pdf_complexity(pdf_path)
                    total_pages += analysis.get("page_count", 0)
                    has_tables = has_tables or analysis.get("has_tables", False)
                    has_images = has_images or analysis.get("has_images", False)
                    structure_scores.append(analysis.get("structure_score", 5))

            avg_pages = total_pages // len(pdf_files) if pdf_files else 0
            avg_structure_score = sum(structure_scores) / len(structure_scores) if structure_scores else 5

            # Determine structure rating
            if avg_structure_score < 3.5:
                structure_rating = "Low"
            elif avg_structure_score < 7.0:
                structure_rating = "Medium"
            else:
                structure_rating = "High"

            return {
                "average_pages": avg_pages,
                "has_complex_layouts": has_tables or has_images,
                "structure_rating": structure_rating,
                "structure_score": avg_structure_score
            }

        except Exception as e:
            self.logger.error(f"Error analyzing PDF files: {e}")
            return {
                "average_pages": 0,
                "has_complex_layouts": False,
                "structure_rating": "Unknown"
            }

    async def _analyze_excel_files(self, excel_files: List[str]) -> Dict[str, Any]:
        """Analyze Excel files for data complexity."""
        if not excel_files:
            return {
                "excel_formula_density": 0.0,
                "has_advanced_features": False,
                "processing_difficulty": "N/A"
            }

        try:
            # Import Excel analyzer (only if needed)
            from app.utils.excel_analyzer import analyze_excel_complexity

            total_formula_density = 0.0
            has_pivots = False
            has_macros = False

            for excel_path in excel_files:
                if os.path.exists(excel_path):
                    analysis = await analyze_excel_complexity(excel_path)
                    total_formula_density += analysis.get("formula_density", 0.0)
                    has_pivots = has_pivots or analysis.get("has_pivot_tables", False)
                    has_macros = has_macros or analysis.get("has_macros", False)

            avg_formula_density = total_formula_density / len(excel_files) if excel_files else 0.0
            has_advanced = has_pivots or has_macros

            # Determine processing difficulty
            if avg_formula_density < 0.10 and not has_advanced:
                difficulty = "Low"
            elif avg_formula_density < 0.25 or has_pivots:
                difficulty = "Medium"
            else:
                difficulty = "High"

            return {
                "excel_formula_density": round(avg_formula_density, 2),
                "has_advanced_features": has_advanced,
                "processing_difficulty": difficulty
            }

        except Exception as e:
            self.logger.error(f"Error analyzing Excel files: {e}")
            return {
                "excel_formula_density": 0.0,
                "has_advanced_features": False,
                "processing_difficulty": "Unknown"
            }

    async def _analyze_image_files(self, image_files: List[str]) -> Dict[str, Any]:
        """Analyze image files for OCR requirements."""
        # Filter to only image files
        image_extensions = {'.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif'}
        image_files = [
            f for f in image_files
            if Path(f).suffix.lower() in image_extensions
        ]

        if not image_files:
            return {
                "average_confidence": 1.0,
                "estimated_accuracy": "High",
                "requires_specialized_ocr": False
            }

        try:
            # Import OCR analyzer (only if needed)
            from app.utils.ocr_analyzer import analyze_image_complexity

            confidences = []

            for image_path in image_files:
                if os.path.exists(image_path):
                    analysis = await analyze_image_complexity(image_path)
                    confidences.append(analysis.get("ocr_confidence", 1.0))

            avg_confidence = sum(confidences) / len(confidences) if confidences else 1.0

            # Determine accuracy rating
            if avg_confidence > 0.90:
                accuracy = "High"
                requires_specialized = False
            elif avg_confidence > 0.70:
                accuracy = "Medium"
                requires_specialized = False
            else:
                accuracy = "Low"
                requires_specialized = True

            return {
                "average_confidence": round(avg_confidence, 2),
                "estimated_accuracy": accuracy,
                "requires_specialized_ocr": requires_specialized
            }

        except Exception as e:
            self.logger.error(f"Error analyzing image files: {e}")
            return {
                "average_confidence": 1.0,
                "estimated_accuracy": "Unknown",
                "requires_specialized_ocr": False
            }

    def _calculate_overall_complexity(
        self,
        pdf_analysis: Dict[str, Any],
        excel_analysis: Dict[str, Any],
        image_analysis: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Calculate overall complexity rating and recommendations.

        Returns:
            Tuple of (complexity_rating, recommendations)
        """
        scores = []

        # PDF complexity contributes 40%
        pdf_rating = pdf_analysis.get("structure_rating", "Low")
        if pdf_rating == "High":
            scores.append(8.0 * 0.4)
        elif pdf_rating == "Medium":
            scores.append(5.0 * 0.4)
        elif pdf_rating == "Low":
            scores.append(2.0 * 0.4)

        # Excel complexity contributes 30%
        excel_difficulty = excel_analysis.get("processing_difficulty", "Low")
        if excel_difficulty == "High":
            scores.append(8.0 * 0.3)
        elif excel_difficulty == "Medium":
            scores.append(5.0 * 0.3)
        elif excel_difficulty == "Low":
            scores.append(2.0 * 0.3)

        # Image/OCR complexity contributes 30%
        image_accuracy = image_analysis.get("estimated_accuracy", "High")
        if image_accuracy == "Low":
            scores.append(8.0 * 0.3)
        elif image_accuracy == "Medium":
            scores.append(5.0 * 0.3)
        elif image_accuracy == "High":
            scores.append(2.0 * 0.3)

        # Calculate average score
        avg_score = sum(scores) / len(scores) if scores else 3.0

        # Map score to rating and multipliers
        if avg_score < 3.5:
            rating = "Low"
            effort_multiplier = 1.0
            rate_multiplier = 1.0
            skill_level = "Mid"
            recommended_teams = []
        elif avg_score < 6.0:
            rating = "Medium"
            effort_multiplier = 1.3
            rate_multiplier = 1.15
            skill_level = "Senior"
            recommended_teams = ["Document Processing Team"]
        else:
            rating = "High"
            effort_multiplier = 1.8
            rate_multiplier = 1.30
            skill_level = "Senior/Expert"
            recommended_teams = ["Document Processing Team", "Data Engineering Team"]

            # Add OCR team if images are poor quality
            if image_analysis.get("requires_specialized_ocr", False):
                recommended_teams.append("OCR Engineering Team")

        recommendations = {
            "effort_multiplier": effort_multiplier,
            "rate_multiplier": rate_multiplier,
            "skill_requirements": {
                "minimum_level": skill_level,
                "specialized_skills": self._determine_specialized_skills(
                    pdf_analysis,
                    excel_analysis,
                    image_analysis
                )
            },
            "recommended_teams": recommended_teams
        }

        return rating, recommendations

    def _determine_specialized_skills(
        self,
        pdf_analysis: Dict[str, Any],
        excel_analysis: Dict[str, Any],
        image_analysis: Dict[str, Any]
    ) -> List[str]:
        """Determine specialized skills needed based on analysis."""
        skills = []

        if pdf_analysis.get("has_complex_layouts", False):
            skills.append("Document Processing")

        if excel_analysis.get("has_advanced_features", False):
            skills.append("Data Analysis")

        if image_analysis.get("requires_specialized_ocr", False):
            skills.append("OCR Engineering")

        return skills

    def _calculate_confidence(self, num_samples: int) -> float:
        """Calculate confidence score based on number of samples analyzed."""
        if num_samples == 0:
            return 0.0
        elif num_samples == 1:
            return 0.60
        elif num_samples == 2:
            return 0.75
        elif num_samples >= 3:
            return 0.85
        return 0.50

    def _generate_reasoning(
        self,
        rating: str,
        pdf_analysis: Dict[str, Any],
        excel_analysis: Dict[str, Any],
        image_analysis: Dict[str, Any],
        num_pdfs: int,
        num_excels: int,
        num_images: int
    ) -> str:
        """Generate human-readable reasoning for complexity rating."""
        parts = []

        parts.append(f"Based on analysis of uploaded samples: ")

        if num_pdfs > 0:
            avg_pages = pdf_analysis.get("average_pages", 0)
            structure = pdf_analysis.get("structure_rating", "Unknown")
            parts.append(f"{num_pdfs} PDF file(s) with {structure} complexity (avg {avg_pages} pages)")

        if num_excels > 0:
            formula_density = excel_analysis.get("excel_formula_density", 0)
            parts.append(f"{num_excels} Excel file(s) with formula density {formula_density:.0%}")

        if num_images > 0:
            confidence = image_analysis.get("average_confidence", 1.0)
            parts.append(f"{num_images} image(s) with OCR confidence {confidence:.0%}")

        reasoning = ", ".join(parts) + ". "

        # Add recommendation
        if rating == "High":
            reasoning += "Recommending 80% effort increase and Expert-level resources."
        elif rating == "Medium":
            reasoning += "Recommending 30% effort increase and Senior-level resources."
        else:
            reasoning += "Standard effort and resource levels are appropriate."

        return reasoning

    def _get_default_complexity(self) -> Dict[str, Any]:
        """Return default complexity when no samples provided."""
        return {
            "complexity_analysis": {
                "overall_rating": "Low",
                "confidence_score": 0.0,

                "detailed_analysis": {
                    "pdf_complexity": {
                        "average_pages": 0,
                        "has_complex_layouts": False,
                        "structure_rating": "N/A"
                    },
                    "ocr_requirements": {
                        "average_confidence": 1.0,
                        "estimated_accuracy": "N/A",
                        "requires_specialized_ocr": False
                    },
                    "data_complexity": {
                        "excel_formula_density": 0.0,
                        "has_advanced_features": False,
                        "processing_difficulty": "N/A"
                    }
                },

                "impact_on_estimation": {
                    "effort_multiplier": 1.0,
                    "rate_multiplier": 1.0,
                    "skill_requirements": {
                        "minimum_level": "Mid",
                        "specialized_skills": []
                    },
                    "recommended_teams": []
                },

                "reasoning": "No sample files provided. Using default Low complexity with standard effort and resource levels."
            }
        }


# Global service instance
_complexity_analyzer_service: Optional[ComplexityAnalyzerService] = None


def get_complexity_analyzer_service() -> ComplexityAnalyzerService:
    """Get or create the global complexity analyzer service instance."""
    global _complexity_analyzer_service
    if _complexity_analyzer_service is None:
        _complexity_analyzer_service = ComplexityAnalyzerService()
    return _complexity_analyzer_service
