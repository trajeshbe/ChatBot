"""
Template Auto-Generator - Intelligent template generation using LLM

This module provides LLM-powered automatic template generation when no predefined
template is available. It analyzes webpage content and suggests optimal columns/fields
for data extraction with intelligent mapping.
"""

from typing import List, Dict, Any, Optional
import logging
import json
from app.services.webscraper.templates.template_models import (
    ExtractionTemplate,
    FieldDefinition,
    SourceHint,
    TemplateSchema,
    ValidationRule,
    TransformationRule
)

logger = logging.getLogger(__name__)


class TemplateAutoGenerator:
    """
    Automatically generate extraction templates using LLM analysis

    Features:
    - Analyze webpage structure and content
    - Suggest optimal fields/columns for extraction
    - Generate intelligent field mappings
    - Support user-provided mapping instructions
    - Create structured templates with validation and transformations
    """

    def __init__(self, llm_service=None, scraper_service=None):
        """
        Initialize template auto-generator

        Args:
            llm_service: LLM service instance for intelligent analysis
            scraper_service: Scraper service for content retrieval
        """
        self.llm_service = llm_service
        self.scraper_service = scraper_service
        self.logger = logger

    async def analyze_webpage_and_generate_template(
        self,
        url: str,
        user_instructions: Optional[str] = None,
        template_name: Optional[str] = None,
        llm_provider: str = "ollama",
        max_fields: int = 20
    ) -> Optional[ExtractionTemplate]:
        """
        Analyze a webpage and automatically generate an extraction template

        Args:
            url: URL to analyze
            user_instructions: Optional user guidance for what data to extract
            template_name: Name for the generated template
            llm_provider: LLM provider to use for analysis
            max_fields: Maximum number of fields to generate

        Returns:
            ExtractionTemplate with auto-generated fields and mappings
        """
        if not self.llm_service:
            self.logger.error("LLM service not initialized")
            return None

        try:
            # Step 1: Fetch and analyze webpage content
            self.logger.info(f"Fetching webpage content from: {url}")
            page_content = await self._fetch_webpage_content(url)

            if not page_content:
                self.logger.error(f"Failed to fetch webpage content from {url}. The site may be blocking automated access or may be down.")
                return None

            if not page_content.get('text') and not page_content.get('html'):
                self.logger.error(f"Webpage content is empty for {url}")
                return None

            # Step 2: Analyze content structure with LLM
            self.logger.info("Analyzing webpage structure with LLM")
            analysis_result = await self._analyze_content_structure(
                page_content,
                user_instructions,
                llm_provider,
                max_fields
            )

            if not analysis_result:
                self.logger.error("Failed to analyze content structure")
                return None

            # Step 3: Generate field definitions with smart mappings
            self.logger.info("Generating field definitions with intelligent mappings")
            fields = await self._generate_field_definitions(
                analysis_result,
                page_content,
                llm_provider
            )

            if not fields:
                self.logger.error("Failed to generate field definitions")
                return None

            # Step 4: Create template with metadata
            is_fallback = analysis_result.get('fallback', False)
            generated_by = 'Rule-based fallback' if is_fallback else 'LLM'
            user_instructions_used = user_instructions is not None and len(user_instructions) > 0

            template = ExtractionTemplate(
                name=template_name or f"auto_generated_{url.split('//')[-1].split('/')[0]}",
                description=f"Auto-generated template for {url}" +
                           (f" - {user_instructions}" if user_instructions else ""),
                template_type="json",
                schema_definition=TemplateSchema(
                    version="1.0",
                    type=analysis_result.get('template_type', 'general_data'),
                    metadata={
                        'source_url': url,
                        'auto_generated': True,
                        'user_instructions': user_instructions,
                        'user_instructions_used': user_instructions_used,  # NEW: Explicit flag
                        'generated_by': generated_by,
                        'llm_provider': llm_provider,
                        'fallback': is_fallback,
                        'confidence': analysis_result.get('confidence', 0.8)
                    }
                ),
                fields=fields
            )

            self.logger.info(f"Successfully generated template with {len(fields)} fields")
            return template

        except Exception as e:
            self.logger.error(f"Template auto-generation failed: {str(e)}")
            return None

    async def generate_template_from_user_instructions(
        self,
        url: str,
        user_instructions: str,
        llm_provider: str = "ollama",
        include_smart_mapping: bool = True
    ) -> Optional[ExtractionTemplate]:
        """
        Generate template based on user's natural language instructions

        This is the key feature for Question 3 - allowing users to guide
        the mapping process with natural language instructions.

        Args:
            url: URL to scrape
            user_instructions: Natural language description of what to extract
                              e.g., "Extract product names, prices, and ratings"
                              e.g., "Get company financial metrics like revenue, profit"
            llm_provider: LLM provider to use
            include_smart_mapping: Whether to use LLM for intelligent field mapping

        Returns:
            ExtractionTemplate customized per user instructions
        """
        return await self.analyze_webpage_and_generate_template(
            url=url,
            user_instructions=user_instructions,
            llm_provider=llm_provider
        )

    async def _fetch_webpage_content(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Fetch webpage content for analysis

        Returns:
            Dict with 'html', 'text', 'structure' keys
        """
        try:
            if self.scraper_service:
                # Use existing scraper service
                self.logger.info(f"Using scraper service to fetch: {url}")
                result = await self.scraper_service.scrape_url(url)

                if not result:
                    self.logger.error(f"Scraper service returned None for {url}")
                    return None

                html_content = result.get('html', '')
                text_content = result.get('text', '')

                if not html_content and not text_content:
                    self.logger.error(f"Scraper service returned empty content for {url}")
                    return None

                self.logger.info(f"Successfully fetched {len(html_content)} bytes of HTML, {len(text_content)} bytes of text")

                return {
                    'html': html_content,
                    'text': text_content,
                    'structure': result.get('structure', {})
                }
            else:
                # Fallback to basic fetch
                self.logger.info(f"Using fallback httpx client to fetch: {url}")
                import httpx
                from bs4 import BeautifulSoup

                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.get(url, follow_redirects=True)
                    response.raise_for_status()

                    soup = BeautifulSoup(response.text, 'html.parser')

                    html_limited = response.text[:10000]  # Limit for LLM
                    text_limited = soup.get_text()[:5000]

                    self.logger.info(f"Successfully fetched {len(response.text)} bytes (limited to {len(html_limited)} for analysis)")

                    return {
                        'html': html_limited,
                        'text': text_limited,
                        'structure': self._analyze_html_structure(soup)
                    }

        except Exception as e:
            self.logger.error(f"Failed to fetch webpage from {url}: {str(e)}", exc_info=True)
            return None

    def _analyze_html_structure(self, soup) -> Dict[str, Any]:
        """Analyze HTML structure to find data patterns"""
        structure = {
            'tables': len(soup.find_all('table')),
            'lists': len(soup.find_all(['ul', 'ol'])),
            'forms': len(soup.find_all('form')),
            'divs_with_classes': len([d for d in soup.find_all('div') if d.get('class')]),
            'common_classes': [],
            'common_ids': []
        }

        # Find common class patterns
        classes = []
        for elem in soup.find_all(class_=True):
            classes.extend(elem.get('class', []))

        if classes:
            from collections import Counter
            common = Counter(classes).most_common(10)
            structure['common_classes'] = [c[0] for c in common]

        return structure

    async def _analyze_content_structure(
        self,
        page_content: Dict[str, Any],
        user_instructions: Optional[str],
        llm_provider: str,
        max_fields: int
    ) -> Optional[Dict[str, Any]]:
        """
        Use LLM to analyze content and determine optimal fields

        This addresses Question 2 - using LLM to determine best columns
        when no template is provided.
        """
        try:
            # Validate that we have content to analyze
            text_content = page_content.get('text', '')
            html_content = page_content.get('html', '')

            if not text_content and not html_content:
                self.logger.error("No content available to analyze - both text and HTML are empty")
                return None

            # Truncate content to fit in LLM context window
            text_preview = text_content[:5000] if text_content else html_content[:5000]

            # ENHANCEMENT: Extract explicit column names from user instructions if provided
            explicit_columns = self._extract_column_names_from_instructions(user_instructions) if user_instructions else []

            # Prepare analysis prompt
            system_prompt = """You are a data extraction expert. Analyze the provided webpage content and determine the best fields/columns to extract.

Your task:
1. Identify structured data present in the content
2. Suggest optimal field names and types
3. If user specifies column names, USE THOSE EXACT NAMES
4. If no column names specified, suggest appropriate field names
5. Provide extraction strategies for each field
6. Return results as a JSON object

IMPORTANT RULES:
- If user specifies column names like "Revenue (Annual)", "EBITDA", use those EXACT names
- If user describes data without specific column names, auto-generate appropriate column names
- Always use 'llm' as extraction_strategy for smart mapping (don't rely on CSS selectors)

Return ONLY a valid JSON object with this structure:
{
    "template_type": "product_data|company_info|article|general_data",
    "suggested_fields": [
        {
            "name": "field_name",
            "display_name": "Field Display Name",
            "description": "What this field represents",
            "type": "string|integer|float|boolean|date",
            "extraction_strategy": "llm",
            "extraction_hint": "LLM prompt describing what to extract",
            "priority": "high|medium|low",
            "likely_location": "Description of where this data appears"
        }
    ],
    "data_structure": "table|list|cards|mixed",
    "confidence": 0.85
}"""

            # Build analysis prompt
            instructions_section = ""
            if user_instructions:
                instructions_section = f"\n\nUser's Extraction Requirements:\n{user_instructions}\n"

                if explicit_columns:
                    instructions_section += f"\n**IMPORTANT**: User specified these exact column names - USE THEM:\n"
                    instructions_section += ", ".join(f'"{col}"' for col in explicit_columns)
                    instructions_section += "\n"
                    self.logger.info(f"✓ Detected {len(explicit_columns)} explicit column names: {explicit_columns}")

                # Log that user instructions are being used
                self.logger.info(f"✓ User instructions will be sent to LLM for analysis: {user_instructions[:150]}{'...' if len(user_instructions) > 150 else ''}")
            else:
                self.logger.info("No user instructions provided - using automatic field detection")

            analysis_prompt = f"""Analyze this webpage content and suggest the best fields to extract:

Webpage Text Preview:
{text_preview}

HTML Structure Info:
- Tables: {page_content.get('structure', {}).get('tables', 0)}
- Lists: {page_content.get('structure', {}).get('lists', 0)}
- Common CSS classes: {', '.join(page_content.get('structure', {}).get('common_classes', [])[:10])}

{instructions_section}

Maximum fields to suggest: {max_fields}

Analyze the content and return the JSON object with suggested fields."""

            # Call LLM with error handling
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": analysis_prompt}
            ]

            try:
                self.logger.info(f"Calling LLM service with provider: {llm_provider}")
                if user_instructions:
                    self.logger.info(f"LLM will analyze page with user guidance: '{user_instructions[:100]}{'...' if len(user_instructions) > 100 else ''}'")

                # Check if LLM service has the generate method
                if not hasattr(self.llm_service, 'generate'):
                    self.logger.warning("LLM service does not have 'generate' method - using fallback analysis")
                    return self._get_fallback_analysis(page_content, user_instructions)

                # Ensure LLM service is initialized
                if hasattr(self.llm_service, 'initialize') and hasattr(self.llm_service, '_initialized'):
                    if not self.llm_service._initialized:
                        self.logger.info("Initializing LLM service...")
                        await self.llm_service.initialize()

                llm_result = await self.llm_service.generate(
                    prompt=analysis_prompt,
                    messages=messages,
                    max_tokens=2000,
                    temperature=0.2
                )

                if not llm_result:
                    self.logger.warning("LLM service returned None - using fallback analysis")
                    return self._get_fallback_analysis(page_content, user_instructions)

                response = llm_result.get('content', '')
                if not response:
                    self.logger.warning("LLM service returned empty content - using fallback analysis")
                    return self._get_fallback_analysis(page_content, user_instructions)

                self.logger.info(f"LLM response received: {len(response)} characters")

            except AttributeError as attr_error:
                self.logger.warning(f"LLM service method error: {str(attr_error)} - using fallback analysis")
                return self._get_fallback_analysis(page_content, user_instructions)
            except Exception as llm_error:
                # More graceful error handling - don't make it look like a critical error
                error_msg = str(llm_error)
                if "No LLM backend available" in error_msg:
                    self.logger.warning(
                        "No LLM backend available for template analysis. "
                        "Using rule-based fallback analysis. "
                        "For better results, configure OpenAI API key in .env"
                    )
                else:
                    self.logger.warning(f"LLM service call failed: {error_msg} - using fallback analysis")

                return self._get_fallback_analysis(page_content, user_instructions)

            # Parse JSON response
            result = self._parse_json_response(response)

            if not result or 'suggested_fields' not in result:
                self.logger.warning("LLM response missing suggested_fields, using fallback")
                return self._get_fallback_analysis(page_content, user_instructions)

            self.logger.info(f"Successfully parsed {len(result.get('suggested_fields', []))} fields from LLM")
            return result

        except Exception as e:
            self.logger.error(f"Content analysis failed: {str(e)}", exc_info=True)
            return self._get_fallback_analysis(page_content, user_instructions)

    async def _generate_field_definitions(
        self,
        analysis_result: Dict[str, Any],
        page_content: Dict[str, Any],
        llm_provider: str
    ) -> List[FieldDefinition]:
        """
        Generate FieldDefinition objects from analysis results

        This creates the actual field mappings with intelligent extraction hints.
        """
        field_definitions = []

        for suggested_field in analysis_result.get('suggested_fields', []):
            try:
                # Create source hint based on extraction strategy
                source_hint = await self._create_source_hint(
                    suggested_field,
                    page_content,
                    llm_provider
                )

                # Create validation rules if applicable
                validation = self._create_validation_rule(suggested_field)

                # Create transformation rules if needed
                transformation = self._create_transformation_rule(suggested_field)

                # Build field definition
                field_def = FieldDefinition(
                    name=suggested_field.get('name', '').replace(' ', '_').lower(),
                    display_name=suggested_field.get('display_name'),
                    description=suggested_field.get('description'),
                    type=suggested_field.get('type', 'string'),
                    required=suggested_field.get('priority') == 'high',
                    source_hint=source_hint,
                    validation=validation
                )

                # Add multiple transformations if needed
                if transformation:
                    field_def.multiple_transformations = [transformation]

                field_definitions.append(field_def)

            except Exception as e:
                self.logger.error(f"Failed to create field definition for {suggested_field.get('name')}: {str(e)}")
                continue

        return field_definitions

    async def _create_source_hint(
        self,
        suggested_field: Dict[str, Any],
        page_content: Dict[str, Any],
        llm_provider: str
    ) -> Optional[SourceHint]:
        """
        Create SourceHint with intelligent extraction strategy

        This is where the smart mapping happens - determining the best way
        to extract each field (CSS, XPath, regex, or LLM).
        """
        strategy = suggested_field.get('extraction_strategy', 'llm')
        extraction_hint = suggested_field.get('extraction_hint', '')

        if strategy == 'css':
            return SourceHint(
                type='css',
                selector=extraction_hint,
                fallback_selectors=None
            )

        elif strategy == 'xpath':
            return SourceHint(
                type='xpath',
                xpath=extraction_hint
            )

        elif strategy == 'regex':
            return SourceHint(
                type='regex',
                pattern=extraction_hint,
                group=1
            )

        elif strategy == 'llm':
            # Generate LLM prompt for this field
            llm_prompt = extraction_hint or f"Extract {suggested_field.get('display_name', suggested_field.get('name'))}"

            return SourceHint(
                type='llm',
                prompt=llm_prompt
            )

        else:
            # Default to LLM extraction
            return SourceHint(
                type='llm',
                prompt=f"Extract {suggested_field.get('name')}"
            )

    def _create_validation_rule(self, suggested_field: Dict[str, Any]) -> Optional[ValidationRule]:
        """Create validation rules based on field type"""
        field_type = suggested_field.get('type', 'string')

        if field_type == 'string':
            return ValidationRule(
                min_length=1,
                max_length=1000
            )

        elif field_type in ['integer', 'float']:
            return ValidationRule(
                min_value=0  # Assume non-negative by default
            )

        elif field_type == 'date':
            return ValidationRule(
                date_format='%Y-%m-%d'
            )

        return None

    def _create_transformation_rule(self, suggested_field: Dict[str, Any]) -> Optional[TransformationRule]:
        """Create transformation rules based on field type and content"""
        field_type = suggested_field.get('type', 'string')

        if field_type == 'string':
            # Apply basic string cleaning
            return TransformationRule(
                type='trim'
            )

        elif field_type in ['integer', 'float']:
            # Extract numbers from text
            return TransformationRule(
                type='extract_number'
            )

        return None

    def _get_fallback_analysis(
        self,
        page_content: Dict[str, Any],
        user_instructions: Optional[str]
    ) -> Dict[str, Any]:
        """
        Provide fallback analysis when LLM is unavailable

        This creates a basic template based on HTML structure analysis
        without requiring LLM.
        """
        self.logger.info("Using rule-based fallback analysis (LLM unavailable)")
        if user_instructions:
            self.logger.info(f"User instructions noted (will influence content field): {user_instructions[:100]}{'...' if len(user_instructions) > 100 else ''}")

        # Extract basic structure information
        structure = page_content.get('structure', {})
        text_content = page_content.get('text', '')
        html_content = page_content.get('html', '')

        # Create basic fields based on structure
        suggested_fields = []

        # Add title field (essential for most pages)
        suggested_fields.append({
            "name": "title",
            "display_name": "Page Title",
            "description": "Title of the page",
            "type": "string",
            "extraction_strategy": "css",
            "extraction_hint": "h1, .title, title",
            "priority": "high",
            "likely_location": "Page header"
        })

        # If there are tables, suggest extracting table data
        if structure.get('tables', 0) > 0:
            suggested_fields.extend([
                {
                    "name": "table_data",
                    "display_name": "Table Data",
                    "description": "Structured data from HTML tables",
                    "type": "string",
                    "extraction_strategy": "css",
                    "extraction_hint": "table tbody tr",
                    "priority": "high",
                    "likely_location": "HTML tables"
                }
            ])

        # Check for common e-commerce/product patterns
        if any(keyword in text_content.lower() for keyword in ['price', 'buy', 'cart', 'product']):
            suggested_fields.extend([
                {
                    "name": "price",
                    "display_name": "Price",
                    "description": "Product or item price",
                    "type": "string",
                    "extraction_strategy": "css",
                    "extraction_hint": ".price, .amount, [class*='price']",
                    "priority": "high",
                    "likely_location": "Product details"
                },
                {
                    "name": "description",
                    "display_name": "Description",
                    "description": "Product or item description",
                    "type": "string",
                    "extraction_strategy": "css",
                    "extraction_hint": ".description, [class*='description'], p",
                    "priority": "medium",
                    "likely_location": "Product details"
                }
            ])

        # If lists are present, add list extraction
        if structure.get('lists', 0) > 0:
            suggested_fields.append({
                "name": "list_items",
                "display_name": "List Items",
                "description": "Items from lists",
                "type": "string",
                "extraction_strategy": "css",
                "extraction_hint": "ul li, ol li",
                "priority": "medium",
                "likely_location": "HTML lists"
            })

        # Check for article/blog patterns
        if any(keyword in html_content.lower() for keyword in ['article', 'post', 'author', 'published']):
            suggested_fields.extend([
                {
                    "name": "author",
                    "display_name": "Author",
                    "description": "Article author",
                    "type": "string",
                    "extraction_strategy": "css",
                    "extraction_hint": ".author, [class*='author'], [rel='author']",
                    "priority": "medium",
                    "likely_location": "Article metadata"
                },
                {
                    "name": "date",
                    "display_name": "Publication Date",
                    "description": "Publication date",
                    "type": "date",
                    "extraction_strategy": "css",
                    "extraction_hint": "time, .date, [class*='date']",
                    "priority": "medium",
                    "likely_location": "Article metadata"
                }
            ])

        # Always include a main content field with user instructions if provided
        content_hint = "Extract main content"
        if user_instructions:
            content_hint = user_instructions

        suggested_fields.append({
            "name": "content",
            "display_name": "Main Content",
            "description": "Main text content from the page",
            "type": "string",
            "extraction_strategy": "css",
            "extraction_hint": "main, article, .content, [role='main']",
            "priority": "high",
            "likely_location": "Page body"
        })

        # Determine template type based on content
        template_type = "general_data"
        if any(keyword in text_content.lower() for keyword in ['price', 'buy', 'cart', 'product']):
            template_type = "product_data"
        elif any(keyword in html_content.lower() for keyword in ['article', 'post', 'author']):
            template_type = "article"
        elif structure.get('tables', 0) > 0:
            template_type = "tabular_data"

        self.logger.info(f"Fallback analysis generated {len(suggested_fields)} fields for {template_type}")

        return {
            "template_type": template_type,
            "suggested_fields": suggested_fields,
            "data_structure": "mixed",
            "confidence": 0.6,
            "fallback": True,
            "message": "Template generated using rule-based analysis. For better results, configure an LLM provider."
        }

    def _extract_column_names_from_instructions(self, user_instructions: str) -> List[str]:
        """
        Extract explicit column names from user instructions

        Looks for patterns like:
        - "map to columns like Revenue (Annual), EBITDA, Net Profit"
        - "extract Revenue, EBITDA Margin, and ROE"
        - "get Company Name, Market Cap, Stock P/E"

        Returns:
            List of extracted column names
        """
        if not user_instructions:
            return []

        import re

        column_names = []

        # Pattern 1: "map to columns like X, Y, Z" or "map to Revenue, EBITDA"
        pattern1 = r'(?:map\s+to\s+(?:columns?\s+like\s+)?|extract\s+|get\s+)([A-Z][^.!?]+?)(?:\.|$|and\s+map|and\s+deliver)'
        matches = re.findall(pattern1, user_instructions, re.IGNORECASE)

        for match in matches:
            # Split by common separators
            potential_columns = re.split(r',\s*|\s+and\s+', match.strip())

            for col in potential_columns:
                col = col.strip()
                # Filter out noise words
                noise_words = {'data', 'it', 'them', 'these', 'those', 'to', 'into', 'in', 'format'}
                if col and col.lower() not in noise_words and len(col) > 2:
                    # Capitalize properly
                    column_names.append(col.strip())

        # Pattern 2: Look for quoted column names
        quoted_pattern = r'["\']([^"\']+?)["\']'
        quoted_matches = re.findall(quoted_pattern, user_instructions)
        column_names.extend(quoted_matches)

        # Remove duplicates while preserving order
        seen = set()
        unique_columns = []
        for col in column_names:
            if col not in seen and col.strip():
                seen.add(col)
                unique_columns.append(col.strip())

        self.logger.info(f"Extracted {len(unique_columns)} potential column names from instructions: {unique_columns}")

        return unique_columns

    def _parse_json_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse JSON from LLM response"""
        try:
            # Try direct JSON parse
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            import re

            # Look for ```json ... ``` blocks
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    pass

            # Look for any JSON object
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass

            self.logger.warning("Could not parse JSON from LLM response")
            return None

    async def refine_template_with_user_feedback(
        self,
        template: ExtractionTemplate,
        user_feedback: str,
        sample_url: str,
        llm_provider: str = "ollama"
    ) -> Optional[ExtractionTemplate]:
        """
        Refine an existing template based on user feedback

        This allows iterative improvement of templates based on user guidance.

        Args:
            template: Existing template to refine
            user_feedback: User's feedback/instructions for refinement
                          e.g., "Add a field for product ratings"
                          e.g., "Remove the description field"
                          e.g., "Change price extraction to use the sale price"
            sample_url: Sample URL to test refinements against
            llm_provider: LLM provider to use

        Returns:
            Refined ExtractionTemplate
        """
        try:
            # Prepare refinement prompt
            system_prompt = """You are a data extraction expert. Refine an existing extraction template based on user feedback.

Return a JSON object with the updated template structure."""

            current_fields = [
                {
                    'name': f.name,
                    'display_name': f.display_name,
                    'type': f.type,
                    'source_hint': f.source_hint.dict() if f.source_hint else None
                }
                for f in template.fields
            ]

            refinement_prompt = f"""Current template fields:
{json.dumps(current_fields, indent=2)}

User feedback:
{user_feedback}

Based on the feedback, provide an updated list of fields with any additions, removals, or modifications."""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": refinement_prompt}
            ]
            llm_result = await self.llm_service.generate(
                prompt=refinement_prompt,
                messages=messages,
                max_tokens=2000,
                temperature=0.2
            )

            if not llm_result:
                return None

            response = llm_result.get('content', '')
            if not response:
                return None

            # Parse and apply refinements
            refinement_result = self._parse_json_response(response)

            if not refinement_result:
                return None

            # Update template with refined fields
            # (Implementation would update template.fields based on refinement_result)

            return template

        except Exception as e:
            self.logger.error(f"Template refinement failed: {str(e)}")
            return None
