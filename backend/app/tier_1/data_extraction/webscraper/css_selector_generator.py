"""
CSS Selector Generator - AI-Powered Reverse Engineering of CSS Selectors

This service takes extracted data and HTML to automatically generate CSS selectors
that can be used for fast, deterministic extraction in the future.

Workflow:
1. Receive extracted data (field: value pairs) and HTML
2. Use AI to find where each value appears in the HTML
3. Generate robust CSS selectors for each field
4. Validate selectors work correctly
5. Score selector quality (specificity vs. robustness)
6. Return ready-to-use CSS template

This enables the "use AI once, then use CSS selectors for speed" optimization.
"""

from typing import Dict, List, Optional, Any, Tuple
import logging
from bs4 import BeautifulSoup
import re
import json

logger = logging.getLogger(__name__)


class CSSSelectorGenerator:
    """
    Generate CSS selectors from extracted data using AI analysis

    This class enables automatic template creation from Smart/Mapper extractions:
    - Analyzes HTML structure
    - Finds elements containing extracted values
    - Generates optimized CSS selectors
    - Validates and scores selectors
    """

    def __init__(self, llm_service=None):
        """
        Initialize CSS Selector Generator

        Args:
            llm_service: LLM service for AI-powered selector generation
        """
        self.llm_service = llm_service
        self.logger = logger

    async def generate_selectors_from_extraction(
        self,
        html_content: str,
        extracted_data: Dict[str, Any],
        llm_provider: str = "openai",
        model_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate CSS selectors for all fields in extracted data

        Args:
            html_content: HTML source where data was extracted from
            extracted_data: Dictionary of extracted field:value pairs
            llm_provider: LLM provider to use (openai, anthropic, ollama)
            model_id: Specific model ID (optional)

        Returns:
            {
                "success": bool,
                "selectors": {
                    "field_name": {
                        "selector": "css selector string",
                        "xpath": "xpath alternative",
                        "attribute": "text|href|src|etc",
                        "confidence": float,
                        "validation_passed": bool,
                        "fallback_selectors": ["selector1", "selector2"]
                    },
                    ...
                },
                "overall_quality": float,
                "generation_method": "ai" | "pattern_matching",
                "message": str
            }
        """
        try:
            self.logger.info("="*80)
            self.logger.info("🎯 CSS SELECTOR GENERATION STARTED")
            self.logger.info(f"📊 Fields to generate selectors for: {list(extracted_data.keys())}")
            self.logger.info(f"📄 HTML content size: {len(html_content)} characters")
            self.logger.info("="*80)

            # Parse HTML
            soup = BeautifulSoup(html_content, 'html.parser')

            # Generate selectors for each field
            selectors = {}
            successful_generations = 0

            for field_name, field_value in extracted_data.items():
                self.logger.info(f"\n🔍 Generating selector for field: '{field_name}' = '{field_value}'")

                # Generate selector using AI
                selector_result = await self._generate_selector_for_field(
                    soup=soup,
                    html_content=html_content,
                    field_name=field_name,
                    field_value=field_value,
                    llm_provider=llm_provider,
                    model_id=model_id
                )

                if selector_result and selector_result.get("selector"):
                    selectors[field_name] = selector_result
                    successful_generations += 1
                    self.logger.info(f"✅ Generated: {selector_result['selector']} (confidence: {selector_result['confidence']:.2f})")
                else:
                    self.logger.warning(f"⚠️ Failed to generate selector for '{field_name}'")
                    # Add placeholder with low confidence
                    selectors[field_name] = {
                        "selector": "",
                        "xpath": "",
                        "attribute": "text",
                        "confidence": 0.0,
                        "validation_passed": False,
                        "fallback_selectors": [],
                        "error": "Could not generate selector"
                    }

            # Calculate overall quality
            overall_quality = successful_generations / len(extracted_data) if extracted_data else 0.0

            self.logger.info(f"\n✅ Generation complete: {successful_generations}/{len(extracted_data)} selectors generated")
            self.logger.info(f"📊 Overall quality score: {overall_quality:.2%}")

            return {
                "success": successful_generations > 0,
                "selectors": selectors,
                "overall_quality": overall_quality,
                "generation_method": "ai" if self.llm_service else "pattern_matching",
                "fields_total": len(extracted_data),
                "fields_successful": successful_generations,
                "message": f"Generated {successful_generations}/{len(extracted_data)} CSS selectors successfully"
            }

        except Exception as e:
            self.logger.error(f"❌ CSS selector generation failed: {e}", exc_info=True)
            return {
                "success": False,
                "selectors": {},
                "overall_quality": 0.0,
                "generation_method": "failed",
                "message": f"CSS selector generation error: {str(e)}"
            }

    async def _generate_selector_for_field(
        self,
        soup: BeautifulSoup,
        html_content: str,
        field_name: str,
        field_value: Any,
        llm_provider: str,
        model_id: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """
        Generate CSS selector for a single field using AI analysis

        Strategy:
        1. Find elements in HTML that contain the field value
        2. Analyze element hierarchy and attributes
        3. Generate robust CSS selector
        4. Validate selector works
        5. Return selector with confidence score
        """
        try:
            # Convert value to string for searching
            value_str = str(field_value).strip()

            if not value_str or value_str in ["", "N/A", "—", "— (requires additional research)"]:
                return None

            # Find all elements containing this value
            matching_elements = self._find_elements_with_value(soup, value_str)

            if not matching_elements:
                self.logger.warning(f"   Could not find '{value_str}' in HTML")
                return await self._fallback_selector_generation(
                    soup, html_content, field_name, value_str, llm_provider, model_id
                )

            self.logger.info(f"   Found {len(matching_elements)} elements containing '{value_str[:50]}...'")

            # Use AI to analyze and generate best selector
            if self.llm_service:
                selector = await self._ai_generate_selector(
                    matching_elements=matching_elements,
                    field_name=field_name,
                    field_value=value_str,
                    html_context=html_content,
                    llm_provider=llm_provider,
                    model_id=model_id
                )
            else:
                # Fallback to pattern-based generation
                selector = self._pattern_based_selector(matching_elements[0], field_name)

            # Validate selector
            validation_result = self._validate_selector(soup, selector["selector"], value_str)
            selector["validation_passed"] = validation_result["passed"]
            selector["confidence"] = validation_result["confidence"]

            return selector

        except Exception as e:
            self.logger.error(f"   Error generating selector for {field_name}: {e}")
            return None

    def _find_elements_with_value(self, soup: BeautifulSoup, value: str) -> List[Any]:
        """
        Find all HTML elements that contain the given value

        Returns list of BeautifulSoup elements sorted by relevance
        """
        matching_elements = []

        # Search for exact text matches
        for element in soup.find_all(text=True):
            if value in element.strip():
                parent = element.parent
                if parent and parent.name not in ['script', 'style', 'meta', 'link']:
                    matching_elements.append(parent)

        # Also search in attributes (like href, src, data-* attributes)
        for element in soup.find_all():
            for attr_name, attr_value in element.attrs.items():
                if isinstance(attr_value, str) and value in attr_value:
                    matching_elements.append(element)
                    break

        # Remove duplicates while preserving order
        seen = set()
        unique_elements = []
        for elem in matching_elements:
            elem_id = id(elem)
            if elem_id not in seen:
                seen.add(elem_id)
                unique_elements.append(elem)

        return unique_elements[:10]  # Limit to top 10 matches

    async def _ai_generate_selector(
        self,
        matching_elements: List[Any],
        field_name: str,
        field_value: str,
        html_context: str,
        llm_provider: str,
        model_id: Optional[str]
    ) -> Dict[str, Any]:
        """
        Use AI to analyze HTML structure and generate optimal CSS selector

        This is the core AI-powered selector generation logic.
        """
        try:
            # Prepare context for AI
            element_descriptions = []
            for idx, elem in enumerate(matching_elements[:3]):  # Top 3 elements
                # Get element path
                path = self._get_element_path(elem)

                # Get element attributes
                attrs = dict(elem.attrs) if hasattr(elem, 'attrs') else {}

                # Get parent context
                parent_tag = elem.parent.name if elem.parent else "None"

                element_descriptions.append({
                    "index": idx,
                    "tag": elem.name,
                    "path": path,
                    "attributes": attrs,
                    "parent": parent_tag,
                    "text_content": elem.get_text(strip=True)[:100]
                })

            # Create AI prompt
            prompt = f"""Analyze the following HTML elements and generate the BEST CSS selector for extracting the field "{field_name}" with value "{field_value}".

Elements containing this value:
{json.dumps(element_descriptions, indent=2)}

Requirements:
1. Generate a CSS selector that is:
   - SPECIFIC enough to target the right element
   - ROBUST enough to work even if page layout changes slightly
   - SIMPLE and maintainable

2. Choose the best strategy:
   - Use semantic class names if available (e.g., .product-title, .price)
   - Use data-* attributes if present
   - Use structural selectors as fallback
   - Avoid overly specific selectors (no long chains of > selectors)

3. Return ONLY a valid CSS selector string, nothing else.

Examples of good selectors:
- ".product-title"
- "h1.title"
- "[data-testid='product-name']"
- ".card > .price"

Generate the CSS selector now:"""

            # Call LLM
            await self.llm_service.initialize()
            response = await self.llm_service.generate_text(
                prompt=prompt,
                provider=llm_provider,
                model=model_id,
                max_tokens=200,
                temperature=0.1  # Low temperature for deterministic output
            )

            # Extract selector from response
            selector_text = response.strip()

            # Clean up selector (remove quotes, extra whitespace)
            selector_text = selector_text.strip('"\'').strip()

            # Determine attribute to extract
            attribute = self._determine_attribute(matching_elements[0])

            return {
                "selector": selector_text,
                "xpath": "",  # Could add XPath generation later
                "attribute": attribute,
                "confidence": 0.8,  # Will be updated by validation
                "fallback_selectors": [],
                "generation_method": "ai"
            }

        except Exception as e:
            self.logger.warning(f"   AI selector generation failed: {e}, falling back to pattern-based")
            return self._pattern_based_selector(matching_elements[0], field_name)

    def _pattern_based_selector(self, element: Any, field_name: str) -> Dict[str, Any]:
        """
        Generate CSS selector using pattern matching (fallback when AI is unavailable)

        Strategy:
        1. Check for unique ID
        2. Check for semantic class names
        3. Check for data-* attributes
        4. Build structural selector
        """
        try:
            selectors = []

            # Strategy 1: ID selector (most specific)
            if element.get('id'):
                selectors.append(f"#{element['id']}")

            # Strategy 2: Class selectors
            if element.get('class'):
                classes = element['class'] if isinstance(element['class'], list) else [element['class']]
                # Prefer semantic class names
                semantic_classes = [c for c in classes if any(keyword in c.lower() for keyword in ['title', 'name', 'price', 'description', 'value', field_name.lower().replace(' ', '-')])]
                if semantic_classes:
                    selectors.append(f".{semantic_classes[0]}")
                elif classes:
                    selectors.append(f".{classes[0]}")

            # Strategy 3: Data attributes
            data_attrs = {k: v for k, v in element.attrs.items() if k.startswith('data-')}
            if data_attrs:
                first_data_attr = list(data_attrs.items())[0]
                selectors.append(f"[{first_data_attr[0]}='{first_data_attr[1]}']")

            # Strategy 4: Tag with class
            if element.get('class'):
                classes = element['class'] if isinstance(element['class'], list) else [element['class']]
                if classes:
                    selectors.append(f"{element.name}.{classes[0]}")

            # Strategy 5: Simple tag selector as last resort
            selectors.append(element.name)

            # Choose best selector (prefer more specific ones)
            best_selector = selectors[0] if selectors else element.name

            # Determine attribute
            attribute = self._determine_attribute(element)

            return {
                "selector": best_selector,
                "xpath": "",
                "attribute": attribute,
                "confidence": 0.6,  # Lower confidence for pattern-based
                "fallback_selectors": selectors[1:4],  # Provide alternatives
                "generation_method": "pattern_based"
            }

        except Exception as e:
            self.logger.error(f"   Pattern-based selector generation failed: {e}")
            return {
                "selector": "",
                "xpath": "",
                "attribute": "text",
                "confidence": 0.0,
                "fallback_selectors": [],
                "generation_method": "failed"
            }

    def _determine_attribute(self, element: Any) -> str:
        """
        Determine which attribute to extract from element

        Returns:
            "text" | "href" | "src" | "value" | "data-*" | etc.
        """
        # Check if value is in text content
        if element.get_text(strip=True):
            return "text"

        # Check common attributes
        if element.get('href'):
            return "href"
        if element.get('src'):
            return "src"
        if element.get('value'):
            return "value"
        if element.get('content'):
            return "content"

        # Check data attributes
        data_attrs = [k for k in element.attrs.keys() if k.startswith('data-')]
        if data_attrs:
            return data_attrs[0]

        return "text"  # Default

    def _get_element_path(self, element: Any) -> str:
        """
        Get CSS path to element (e.g., "html > body > div.container > h1")
        """
        path_parts = []
        current = element

        while current and current.name != '[document]':
            identifier = current.name

            # Add class or ID if available
            if current.get('id'):
                identifier += f"#{current['id']}"
            elif current.get('class'):
                classes = current['class'] if isinstance(current['class'], list) else [current['class']]
                if classes:
                    identifier += f".{classes[0]}"

            path_parts.insert(0, identifier)
            current = current.parent

            # Limit depth to avoid overly long paths
            if len(path_parts) >= 5:
                break

        return " > ".join(path_parts)

    def _validate_selector(self, soup: BeautifulSoup, selector: str, expected_value: str) -> Dict[str, Any]:
        """
        Validate that the generated CSS selector actually extracts the expected value

        Returns:
            {
                "passed": bool,
                "confidence": float,
                "extracted_value": str,
                "match_count": int
            }
        """
        try:
            if not selector:
                return {"passed": False, "confidence": 0.0, "extracted_value": "", "match_count": 0}

            # Try to find elements using CSS selector
            matches = soup.select(selector)

            if not matches:
                return {"passed": False, "confidence": 0.0, "extracted_value": "", "match_count": 0}

            # Check if first match contains expected value
            first_match = matches[0]
            extracted_text = first_match.get_text(strip=True)

            # Calculate confidence based on:
            # 1. Does it match expected value?
            # 2. How many elements match (prefer unique selectors)
            # 3. How specific is the selector?

            exact_match = expected_value in extracted_text
            match_count = len(matches)

            # Confidence scoring
            confidence = 0.0

            if exact_match:
                confidence = 1.0

                # Penalize if selector matches too many elements
                if match_count > 1:
                    confidence *= (1.0 / match_count) * 2  # Prefer unique selectors
                    confidence = min(confidence, 0.9)  # Cap at 0.9 for non-unique selectors

                # Bonus for semantic selectors
                if any(keyword in selector.lower() for keyword in ['title', 'price', 'name', 'description']):
                    confidence = min(confidence + 0.1, 1.0)

            return {
                "passed": exact_match,
                "confidence": confidence,
                "extracted_value": extracted_text[:100],
                "match_count": match_count
            }

        except Exception as e:
            self.logger.error(f"   Selector validation failed: {e}")
            return {"passed": False, "confidence": 0.0, "extracted_value": "", "match_count": 0}

    async def _fallback_selector_generation(
        self,
        soup: BeautifulSoup,
        html_content: str,
        field_name: str,
        field_value: str,
        llm_provider: str,
        model_id: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """
        Last-resort selector generation when value not found in HTML

        Strategy: Use field name to guess likely selectors
        """
        self.logger.info(f"   Using fallback generation for '{field_name}'")

        # Generate selectors based on field name
        field_slug = field_name.lower().replace(' ', '-').replace('_', '-')

        candidate_selectors = [
            f".{field_slug}",
            f"#{field_slug}",
            f"[data-field='{field_slug}']",
            f"[data-name='{field_slug}']",
            f".field-{field_slug}",
        ]

        # Test each candidate
        for selector in candidate_selectors:
            matches = soup.select(selector)
            if matches:
                return {
                    "selector": selector,
                    "xpath": "",
                    "attribute": "text",
                    "confidence": 0.3,  # Low confidence for fallback
                    "validation_passed": False,
                    "fallback_selectors": [],
                    "generation_method": "fallback"
                }

        # Could not generate
        return None
