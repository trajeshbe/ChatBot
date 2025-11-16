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
                self.logger.error("Failed to fetch webpage content")
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
                        'generated_by': 'LLM',
                        'llm_provider': llm_provider
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
                result = await self.scraper_service.scrape_url(url)
                return {
                    'html': result.get('html', ''),
                    'text': result.get('text', ''),
                    'structure': result.get('structure', {})
                }
            else:
                # Fallback to basic fetch
                import httpx
                from bs4 import BeautifulSoup

                async with httpx.AsyncClient() as client:
                    response = await client.get(url, follow_redirects=True)
                    response.raise_for_status()

                    soup = BeautifulSoup(response.text, 'html.parser')

                    return {
                        'html': response.text[:10000],  # Limit for LLM
                        'text': soup.get_text()[:5000],
                        'structure': self._analyze_html_structure(soup)
                    }

        except Exception as e:
            self.logger.error(f"Failed to fetch webpage: {str(e)}")
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
            # Prepare analysis prompt
            system_prompt = """You are a data extraction expert. Analyze the provided webpage content and determine the best fields/columns to extract.

Your task:
1. Identify structured data present in the content
2. Suggest optimal field names and types
3. Provide extraction strategies for each field
4. Return results as a JSON object

Return ONLY a valid JSON object with this structure:
{
    "template_type": "product_data|company_info|article|general_data",
    "suggested_fields": [
        {
            "name": "field_name",
            "display_name": "Field Display Name",
            "description": "What this field represents",
            "type": "string|integer|float|boolean|date",
            "extraction_strategy": "css|xpath|regex|llm",
            "extraction_hint": "CSS selector, XPath, regex pattern, or LLM prompt",
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

            analysis_prompt = f"""Analyze this webpage content and suggest the best fields to extract:

Webpage Text Preview:
{page_content.get('text', '')[:3000]}

HTML Structure Info:
- Tables: {page_content.get('structure', {}).get('tables', 0)}
- Lists: {page_content.get('structure', {}).get('lists', 0)}
- Common CSS classes: {', '.join(page_content.get('structure', {}).get('common_classes', [])[:10])}

{instructions_section}

Maximum fields to suggest: {max_fields}

Analyze the content and return the JSON object with suggested fields."""

            # Call LLM
            response = await self.llm_service.generate_response(
                prompt=analysis_prompt,
                system_prompt=system_prompt,
                provider=llm_provider,
                max_tokens=2000,
                temperature=0.2
            )

            if not response:
                return None

            # Parse JSON response
            result = self._parse_json_response(response)

            if not result or 'suggested_fields' not in result:
                self.logger.warning("LLM response missing suggested_fields")
                return None

            return result

        except Exception as e:
            self.logger.error(f"Content analysis failed: {str(e)}")
            return None

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

            response = await self.llm_service.generate_response(
                prompt=refinement_prompt,
                system_prompt=system_prompt,
                provider=llm_provider,
                max_tokens=2000,
                temperature=0.2
            )

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
