"""
Multi-Analyzer Ensemble System for Intelligent Content Classification

Runs multiple analyzers in parallel and consolidates results via voting,
confidence weighting, or LLM judgment.

Philosophy:
- Single analyzer = limited perspective
- Multiple analyzers = robust classification
- Ensemble voting = higher accuracy
- Full traceability = explainability

Analyzers:
1. PyMuPDF: Embedded raster images
2. Docling: Figures, tables, structure
3. PIL: Visual complexity, edge density
4. PDF Structure: Vector graphics, drawing commands
5. OCR: Scanned document detection
6. Vision LLM (optional): Page screenshot analysis
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from enum import Enum
from collections import Counter
import numpy as np

# Core dependencies
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    from PIL import Image
    import cv2
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

logger = logging.getLogger(__name__)


class ContentType(Enum):
    """Content type classification"""
    TEXT_HEAVY = "text_heavy"
    IMAGE_HEAVY = "image_heavy"
    TABLE_HEAVY = "table_heavy"
    CODE = "code"
    NUMERICAL = "numerical"
    MIXED = "mixed"
    SCANNED = "scanned"
    VECTOR_GRAPHICS = "vector_graphics"  # NEW: CAD/technical drawings


class AnalyzerResult:
    """Result from a single analyzer"""
    def __init__(
        self,
        analyzer_name: str,
        content_type: ContentType,
        confidence: float,
        reasoning: str,
        metrics: Dict[str, Any],
        processing_time_ms: float
    ):
        self.analyzer_name = analyzer_name
        self.content_type = content_type
        self.confidence = confidence
        self.reasoning = reasoning
        self.metrics = metrics
        self.processing_time_ms = processing_time_ms

    def to_dict(self) -> Dict[str, Any]:
        return {
            "analyzer_name": self.analyzer_name,
            "content_type": self.content_type.value,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "metrics": self.metrics,
            "processing_time_ms": self.processing_time_ms
        }


class MultiAnalyzerEnsemble:
    """
    Multi-analyzer ensemble for robust content classification

    Runs multiple analyzers in parallel and consolidates results.
    """

    def __init__(self):
        """Initialize multi-analyzer ensemble"""
        self.analyzers = []

        # Register available analyzers
        if PYMUPDF_AVAILABLE:
            self.analyzers.append("pymupdf")

        # Docling is always available (required dependency)
        self.analyzers.append("docling")

        if PIL_AVAILABLE:
            self.analyzers.append("pil_visual")

        self.analyzers.append("pdf_structure")

        logger.info(f"MultiAnalyzerEnsemble initialized with {len(self.analyzers)} analyzers: {self.analyzers}")

    async def analyze_document(
        self,
        file_path: str,
        file_type: str,
        file_size: int,
        consolidation_strategy: str = "voting"  # "voting", "confidence_weighted", "llm_judgment"
    ) -> Dict[str, Any]:
        """
        Analyze document with multiple analyzers in parallel

        Args:
            file_path: Path to document
            file_type: MIME type
            file_size: File size in bytes
            consolidation_strategy: How to consolidate results

        Returns:
            {
                "content_type": ContentType,
                "confidence": float,
                "reasoning": str,
                "strategy": str,
                "vector_column": str,
                "analyzer_results": List[AnalyzerResult],
                "consolidation_method": str,
                "metrics": dict
            }
        """

        if "pdf" not in file_type.lower():
            # For non-PDF, use simple analysis
            return await self._analyze_non_pdf(file_path, file_type)

        logger.info(f"🔍 Starting multi-analyzer ensemble for {Path(file_path).name}")

        # Run all analyzers in parallel
        tasks = []

        if "pymupdf" in self.analyzers:
            tasks.append(self._analyze_with_pymupdf(file_path))

        if "docling" in self.analyzers:
            tasks.append(self._analyze_with_docling(file_path))

        if "pil_visual" in self.analyzers:
            tasks.append(self._analyze_with_pil(file_path))

        if "pdf_structure" in self.analyzers:
            tasks.append(self._analyze_with_pdf_structure(file_path))

        # Execute all analyzers in parallel
        analyzer_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions
        valid_results = []
        for i, result in enumerate(analyzer_results):
            if isinstance(result, Exception):
                logger.error(f"Analyzer {i} failed: {result}")
            else:
                valid_results.append(result)

        if not valid_results:
            logger.error("All analyzers failed, using fallback")
            return self._fallback_analysis(file_path)

        logger.info(f"✅ {len(valid_results)}/{len(tasks)} analyzers completed successfully")

        # Consolidate results
        if consolidation_strategy == "voting":
            final_result = self._consolidate_by_voting(valid_results)
        elif consolidation_strategy == "confidence_weighted":
            final_result = self._consolidate_by_confidence(valid_results)
        elif consolidation_strategy == "llm_judgment":
            final_result = await self._consolidate_by_llm(valid_results, file_path)
        else:
            final_result = self._consolidate_by_voting(valid_results)

        # Add analyzer details
        final_result["analyzer_results"] = [r.to_dict() for r in valid_results]
        final_result["consolidation_method"] = consolidation_strategy

        logger.info(f"📊 Final classification: {final_result['content_type'].value} (confidence: {final_result['confidence']:.2%})")

        return final_result

    async def _analyze_with_pymupdf(self, file_path: str) -> AnalyzerResult:
        """Analyze with PyMuPDF (embedded raster images)"""
        import time
        start_time = time.time()

        try:
            doc = fitz.open(file_path)

            page_count = len(doc)
            total_images = 0
            total_text_length = 0

            for page in doc:
                # Count embedded images
                images = page.get_images()
                total_images += len(images)

                # Count text
                text = page.get_text()
                total_text_length += len(text.strip())

            doc.close()

            # Classification logic
            images_per_page = total_images / page_count if page_count > 0 else 0

            if total_images > 5 and images_per_page > 1:
                content_type = ContentType.IMAGE_HEAVY
                confidence = 0.8
                reasoning = f"PyMuPDF detected {total_images} embedded images ({images_per_page:.1f} per page)"
            elif total_text_length < 500:
                content_type = ContentType.SCANNED
                confidence = 0.7
                reasoning = "Very little text detected, likely scanned document"
            else:
                content_type = ContentType.TEXT_HEAVY
                confidence = 0.6
                reasoning = f"PyMuPDF found {total_images} images, mostly text"

            processing_time = (time.time() - start_time) * 1000

            return AnalyzerResult(
                analyzer_name="pymupdf",
                content_type=content_type,
                confidence=confidence,
                reasoning=reasoning,
                metrics={
                    "total_images": total_images,
                    "images_per_page": images_per_page,
                    "page_count": page_count,
                    "text_length": total_text_length,
                    "detection_method": "embedded_images"
                },
                processing_time_ms=processing_time
            )

        except Exception as e:
            logger.error(f"PyMuPDF analysis failed: {e}")
            raise

    async def _analyze_with_docling(self, file_path: str) -> AnalyzerResult:
        """Analyze with Docling (figures, tables, structure)"""
        import time
        start_time = time.time()

        try:
            from docling.document_converter import DocumentConverter

            converter = DocumentConverter()
            result = converter.convert(file_path)

            # Count figures and tables from Docling
            figure_count = 0
            table_count = 0
            text_count = 0

            for element in result.document.iterate_items():
                elem_type = element.get("type", "")
                if "figure" in elem_type.lower() or "picture" in elem_type.lower():
                    figure_count += 1
                elif "table" in elem_type.lower():
                    table_count += 1
                elif "text" in elem_type.lower() or "paragraph" in elem_type.lower():
                    text_count += 1

            total_elements = figure_count + table_count + text_count

            # Classification logic
            if figure_count > 3 and figure_count / total_elements > 0.3:
                content_type = ContentType.IMAGE_HEAVY
                confidence = 0.9
                reasoning = f"Docling detected {figure_count} figures ({figure_count/total_elements:.1%} of elements)"
            elif table_count > 3 and table_count / total_elements > 0.3:
                content_type = ContentType.TABLE_HEAVY
                confidence = 0.85
                reasoning = f"Docling detected {table_count} tables ({table_count/total_elements:.1%} of elements)"
            elif figure_count > 0 or table_count > 0:
                content_type = ContentType.MIXED
                confidence = 0.75
                reasoning = f"Docling found {figure_count} figures + {table_count} tables"
            else:
                content_type = ContentType.TEXT_HEAVY
                confidence = 0.7
                reasoning = "Mostly text content detected by Docling"

            processing_time = (time.time() - start_time) * 1000

            return AnalyzerResult(
                analyzer_name="docling",
                content_type=content_type,
                confidence=confidence,
                reasoning=reasoning,
                metrics={
                    "figure_count": figure_count,
                    "table_count": table_count,
                    "text_count": text_count,
                    "total_elements": total_elements,
                    "detection_method": "document_structure"
                },
                processing_time_ms=processing_time
            )

        except Exception as e:
            logger.error(f"Docling analysis failed: {e}")
            raise

    async def _analyze_with_pil(self, file_path: str) -> AnalyzerResult:
        """Analyze with PIL (visual complexity, edge density)"""
        import time
        start_time = time.time()

        try:
            import fitz  # Need to render PDF pages

            doc = fitz.open(file_path)

            edge_densities = []

            # Analyze first 3 pages (sample)
            for page_num in range(min(3, len(doc))):
                page = doc[page_num]

                # Render page as image
                pix = page.get_pixmap(dpi=72)  # Low DPI for speed
                img_data = pix.tobytes("png")

                # Load with PIL
                from io import BytesIO
                img = Image.open(BytesIO(img_data))

                # Convert to numpy for edge detection
                img_array = np.array(img.convert('L'))  # Grayscale

                # Compute edge density using Sobel
                edges_x = cv2.Sobel(img_array, cv2.CV_64F, 1, 0, ksize=3)
                edges_y = cv2.Sobel(img_array, cv2.CV_64F, 0, 1, ksize=3)
                edges = np.sqrt(edges_x**2 + edges_y**2)

                # Edge density = percentage of pixels with edges
                edge_density = np.sum(edges > 50) / edges.size
                edge_densities.append(edge_density)

            doc.close()

            avg_edge_density = np.mean(edge_densities)

            # Classification logic
            # High edge density = lots of lines/drawings
            if avg_edge_density > 0.15:
                content_type = ContentType.VECTOR_GRAPHICS
                confidence = 0.85
                reasoning = f"PIL detected high edge density ({avg_edge_density:.2%}) - likely technical drawings/vector graphics"
            elif avg_edge_density > 0.08:
                content_type = ContentType.IMAGE_HEAVY
                confidence = 0.75
                reasoning = f"PIL detected moderate edge density ({avg_edge_density:.2%})"
            else:
                content_type = ContentType.TEXT_HEAVY
                confidence = 0.65
                reasoning = f"PIL detected low edge density ({avg_edge_density:.2%})"

            processing_time = (time.time() - start_time) * 1000

            return AnalyzerResult(
                analyzer_name="pil_visual",
                content_type=content_type,
                confidence=confidence,
                reasoning=reasoning,
                metrics={
                    "avg_edge_density": avg_edge_density,
                    "pages_analyzed": len(edge_densities),
                    "edge_densities": edge_densities,
                    "detection_method": "visual_complexity"
                },
                processing_time_ms=processing_time
            )

        except Exception as e:
            logger.error(f"PIL visual analysis failed: {e}")
            raise

    async def _analyze_with_pdf_structure(self, file_path: str) -> AnalyzerResult:
        """Analyze PDF structure (vector drawing commands)"""
        import time
        start_time = time.time()

        try:
            import fitz

            doc = fitz.open(file_path)

            total_drawing_commands = 0
            total_text_commands = 0

            # Analyze first 5 pages (sample)
            for page_num in range(min(5, len(doc))):
                page = doc[page_num]

                # Get page content stream (PDF operators)
                content = page.get_text("dict")

                # Count paths (vector graphics indicators)
                paths = page.get_drawings()
                total_drawing_commands += len(paths)

                # Count text blocks
                blocks = page.get_text("blocks")
                total_text_commands += len(blocks)

            doc.close()

            # Classification logic
            drawing_ratio = total_drawing_commands / (total_drawing_commands + total_text_commands + 1)

            if total_drawing_commands > 50 and drawing_ratio > 0.6:
                content_type = ContentType.VECTOR_GRAPHICS
                confidence = 0.95
                reasoning = f"PDF structure analysis: {total_drawing_commands} vector paths ({drawing_ratio:.1%} ratio) - CAD/technical drawings"
            elif total_drawing_commands > 20 and drawing_ratio > 0.3:
                content_type = ContentType.IMAGE_HEAVY
                confidence = 0.8
                reasoning = f"PDF structure: {total_drawing_commands} vector paths detected"
            else:
                content_type = ContentType.TEXT_HEAVY
                confidence = 0.7
                reasoning = f"PDF structure: Minimal vector graphics ({total_drawing_commands} paths)"

            processing_time = (time.time() - start_time) * 1000

            return AnalyzerResult(
                analyzer_name="pdf_structure",
                content_type=content_type,
                confidence=confidence,
                reasoning=reasoning,
                metrics={
                    "total_drawing_commands": total_drawing_commands,
                    "total_text_commands": total_text_commands,
                    "drawing_ratio": drawing_ratio,
                    "detection_method": "pdf_operators"
                },
                processing_time_ms=processing_time
            )

        except Exception as e:
            logger.error(f"PDF structure analysis failed: {e}")
            raise

    def _consolidate_by_voting(self, results: List[AnalyzerResult]) -> Dict[str, Any]:
        """Consolidate results by majority voting"""

        # Count votes for each content type
        votes = Counter([r.content_type for r in results])

        # Get winning content type
        winning_type, vote_count = votes.most_common(1)[0]

        # Calculate average confidence of analyzers that voted for winner
        winner_confidences = [r.confidence for r in results if r.content_type == winning_type]
        avg_confidence = np.mean(winner_confidences)

        # Collect reasoning from winning analyzers
        winner_reasoning = [r.reasoning for r in results if r.content_type == winning_type]

        # Map to strategy
        strategy_map = {
            ContentType.TEXT_HEAVY: "text_semantic",
            ContentType.IMAGE_HEAVY: "vision",
            ContentType.VECTOR_GRAPHICS: "vision",
            ContentType.TABLE_HEAVY: "table_structure",
            ContentType.CODE: "code",
            ContentType.NUMERICAL: "numerical",
            ContentType.MIXED: "hybrid",
            ContentType.SCANNED: "text_semantic"
        }

        strategy = strategy_map.get(winning_type, "text_semantic")

        # Map to vector column
        column_map = {
            "text_semantic": "embedding",
            "vision": "visual_embedding",
            "table_structure": "table_embedding",
            "code": "code_embedding",
            "numerical": "numerical_embedding",
            "hybrid": "embedding"
        }

        vector_column = column_map.get(strategy, "embedding")

        reasoning = (
            f"Voting result: {winning_type.value} ({vote_count}/{len(results)} analyzers). "
            f"Winning analyzers: {', '.join(winner_reasoning[:2])}"
        )

        return {
            "content_type": winning_type,
            "confidence": float(avg_confidence),
            "reasoning": reasoning,
            "strategy": strategy,
            "vector_column": vector_column,
            "voting_breakdown": {k.value: v for k, v in votes.items()},
            "total_analyzers": len(results)
        }

    def _consolidate_by_confidence(self, results: List[AnalyzerResult]) -> Dict[str, Any]:
        """Consolidate results by confidence-weighted voting"""

        # Weight votes by confidence
        weighted_votes = {}
        for result in results:
            content_type = result.content_type
            if content_type not in weighted_votes:
                weighted_votes[content_type] = 0
            weighted_votes[content_type] += result.confidence

        # Get winning type
        winning_type = max(weighted_votes, key=weighted_votes.get)
        total_weight = sum(weighted_votes.values())
        final_confidence = weighted_votes[winning_type] / total_weight

        # Collect reasoning
        winner_reasoning = [r.reasoning for r in results if r.content_type == winning_type]

        # Map to strategy (same as voting)
        strategy_map = {
            ContentType.TEXT_HEAVY: "text_semantic",
            ContentType.IMAGE_HEAVY: "vision",
            ContentType.VECTOR_GRAPHICS: "vision",
            ContentType.TABLE_HEAVY: "table_structure",
            ContentType.CODE: "code",
            ContentType.NUMERICAL: "numerical",
            ContentType.MIXED: "hybrid",
            ContentType.SCANNED: "text_semantic"
        }

        strategy = strategy_map.get(winning_type, "text_semantic")

        column_map = {
            "text_semantic": "embedding",
            "vision": "visual_embedding",
            "table_structure": "table_embedding",
            "code": "code_embedding",
            "numerical": "numerical_embedding",
            "hybrid": "embedding"
        }

        vector_column = column_map.get(strategy, "embedding")

        reasoning = (
            f"Confidence-weighted result: {winning_type.value} (score: {weighted_votes[winning_type]:.2f}). "
            f"Top analyzers: {', '.join(winner_reasoning[:2])}"
        )

        return {
            "content_type": winning_type,
            "confidence": float(final_confidence),
            "reasoning": reasoning,
            "strategy": strategy,
            "vector_column": vector_column,
            "weighted_scores": {k.value: v for k, v in weighted_votes.items()},
            "total_analyzers": len(results)
        }

    async def _consolidate_by_llm(self, results: List[AnalyzerResult], file_path: str) -> Dict[str, Any]:
        """
        Consolidate results using LLM judgment with llama3.2-vision:11b fallback

        Uses EXISTING llm_service (respects user's chosen LLM) with vision model fallback

        Args:
            results: List of analyzer results to consolidate
            file_path: Path to the file being analyzed (for extracting filename)
        """
        import json
        from pathlib import Path
        from app.services.llm_service import get_llm_service

        try:
            # Extract filename from file path
            filename = Path(file_path).name

            # Build analyzer summary for LLM
            analyzer_votes = []
            for result in results:
                analyzer_votes.append({
                    'analyzer': result.analyzer_name,
                    'classification': result.content_type.value,
                    'confidence': result.confidence,
                    'reasoning': result.reasoning
                })

            # Filename keyword check (from existing pattern)
            VISUAL_KEYWORDS = ['arch', 'architecture', 'diagram', 'blueprint', 'drawing',
                              'plan', 'layout', 'schematic', 'flowchart', 'wireframe',
                              'chart', 'graph', 'figure', 'illustration', 'map']
            filename_suggests_visual = any(kw in filename.lower() for kw in VISUAL_KEYWORDS)

            # LLM classification prompt
            prompt = f"""Analyze these document classification results and determine the BEST content type.

**DOCUMENT**: {filename}
**Filename suggests visual content**: {filename_suggests_visual}

**ANALYZER VOTES**:
{json.dumps(analyzer_votes, indent=2)}

**CLASSIFICATION CATEGORIES**:
1. text_heavy - Primarily text, minimal images
2. image_heavy - Contains significant photos/images
3. vector_graphics - Diagrams, charts, technical drawings (USE VISUAL EMBEDDINGS!)
4. table_heavy - Primarily tables/structured data
5. code - Source code
6. mixed - Combination of types
7. scanned - Scanned document

**CRITICAL RULES**:
- If filename contains "{'" OR "'.join(VISUAL_KEYWORDS)}" → PREFER vector_graphics
- Architecture diagrams, flowcharts, technical drawings → vector_graphics (NOT text_heavy!)
- When uncertain between text_heavy and vector_graphics → choose vector_graphics

Respond with JSON only:
{{
    "content_type": "vector_graphics",
    "confidence": 0.95,
    "reasoning": "Filename 'arch1.pdf' suggests architecture diagram, analyzer detected edges"
}}"""

            llm_service = get_llm_service()

            # Try user's chosen LLM first, fallback to llama3.2-vision:11b
            try:
                response = await llm_service.generate(
                    prompt=prompt,
                    max_tokens=200,
                    temperature=0.1
                )
                result_text = response["content"]  # ✅ FIX: llm_service returns dict, not object
            except Exception as e:
                logger.warning(f"⚠️ User LLM failed, trying llama3.2-vision:11b: {e}")
                response = await llm_service.generate(
                    prompt=prompt,
                    max_tokens=200,
                    temperature=0.1,
                    model_id="llama3.2-vision:11b"
                )
                result_text = response["content"]  # ✅ FIX: llm_service returns dict, not object

            # Parse JSON
            classification = json.loads(result_text.strip())

            # Map to ContentType
            content_type_map = {
                "text_heavy": ContentType.TEXT_HEAVY,
                "image_heavy": ContentType.IMAGE_HEAVY,
                "vector_graphics": ContentType.VECTOR_GRAPHICS,
                "table_heavy": ContentType.TABLE_HEAVY,
                "code": ContentType.CODE,
                "mixed": ContentType.MIXED,
                "scanned": ContentType.SCANNED
            }

            content_type = content_type_map.get(classification['content_type'], ContentType.TEXT_HEAVY)

            # Map to strategy
            strategy_map = {
                ContentType.TEXT_HEAVY: "text_semantic",
                ContentType.IMAGE_HEAVY: "vision",
                ContentType.VECTOR_GRAPHICS: "vision",  # ✅ VISUAL EMBEDDINGS!
                ContentType.TABLE_HEAVY: "table_structure",
                ContentType.CODE: "code",
                ContentType.MIXED: "hybrid",
                ContentType.SCANNED: "text_semantic"
            }

            vector_column_map = {
                ContentType.TEXT_HEAVY: "embedding",
                ContentType.IMAGE_HEAVY: "visual_embedding",
                ContentType.VECTOR_GRAPHICS: "visual_embedding",  # ✅ USE CLIP!
                ContentType.TABLE_HEAVY: "embedding",
                ContentType.CODE: "embedding",
                ContentType.MIXED: "embedding",
                ContentType.SCANNED: "embedding"
            }

            logger.info(f"✅ LLM classified '{filename}' as: {content_type.value}")
            logger.info(f"   Confidence: {classification['confidence']}")
            logger.info(f"   Reasoning: {classification['reasoning']}")
            logger.info(f"   Filename boost: {filename_suggests_visual}")

            return {
                'content_type': content_type,
                'confidence': float(classification['confidence']),
                'reasoning': classification['reasoning'],
                'strategy': strategy_map[content_type],
                'vector_column': vector_column_map[content_type],
                'analyzer_results': results,
                'filename_boost_applied': filename_suggests_visual,
                'method': 'llm_judgment'
            }

        except Exception as e:
            logger.warning(f"⚠️ LLM classification failed: {e}, falling back to confidence-weighted")
            fallback_result = self._consolidate_by_confidence(results)

            # Keyword override if needed
            try:
                from pathlib import Path
                filename = Path(file_path).name
                VISUAL_KEYWORDS = ['arch', 'architecture', 'diagram', 'blueprint', 'drawing']
                if any(kw in filename.lower() for kw in VISUAL_KEYWORDS) and fallback_result['content_type'] == ContentType.TEXT_HEAVY:
                    logger.warning(f"📝 Keyword override: '{filename}' → vector_graphics")
                    fallback_result['content_type'] = ContentType.VECTOR_GRAPHICS
                    fallback_result['strategy'] = 'vision'
                    fallback_result['vector_column'] = 'visual_embedding'
                    fallback_result['reasoning'] += f" [OVERRIDE: Filename '{filename}' suggests visual content]"
            except Exception:
                pass

            return fallback_result

    async def _analyze_non_pdf(self, file_path: str, file_type: str) -> Dict[str, Any]:
        """Analyze non-PDF files"""
        if "image" in file_type.lower():
            return {
                "content_type": ContentType.IMAGE_HEAVY,
                "confidence": 0.95,
                "reasoning": "Image file type",
                "strategy": "vision",
                "vector_column": "visual_embedding",
                "analyzer_results": [],
                "consolidation_method": "file_type"
            }
        else:
            return {
                "content_type": ContentType.TEXT_HEAVY,
                "confidence": 0.8,
                "reasoning": "Text file type",
                "strategy": "text_semantic",
                "vector_column": "embedding",
                "analyzer_results": [],
                "consolidation_method": "file_type"
            }

    def _fallback_analysis(self, file_path: str) -> Dict[str, Any]:
        """Fallback when all analyzers fail"""
        return {
            "content_type": ContentType.TEXT_HEAVY,
            "confidence": 0.5,
            "reasoning": "All analyzers failed, using fallback",
            "strategy": "text_semantic",
            "vector_column": "embedding",
            "analyzer_results": [],
            "consolidation_method": "fallback"
        }


# Global singleton
multi_analyzer_ensemble = MultiAnalyzerEnsemble()
