"""
LLM Extractor - Extract data using Large Language Models

This module provides LLM-powered data extraction from unstructured content.
Leverages the existing LLM service for OpenAI, Anthropic, and Ollama support.
"""

from typing import Optional, Dict, Any, List
import logging
import json
import re

logger = logging.getLogger(__name__)


class LLMExtractor:
    """
    Extract data from content using LLMs

    Features:
    - Multi-provider support (Ollama, OpenAI, Anthropic)
    - Structured output extraction
    - Field-specific prompts
    - Confidence scoring
    """

    def __init__(self, llm_service=None):
        """
        Initialize LLM extractor

        Args:
            llm_service: LLM service instance (from app.services.llm_service)
        """
        self.logger = logger
        self.llm_service = llm_service

    async def extract(
        self,
        content: str,
        prompt: str,
        field_name: str = "value",
        field_type: str = "string",
        llm_provider: str = "openai",
        return_confidence: bool = False
    ) -> Optional[Any]:
        """
        Extract field value using LLM

        Args:
            content: Text content to extract from
            prompt: Extraction prompt describing what to extract
            field_name: Name of the field being extracted
            field_type: Type of field (string, integer, float, boolean, etc.)
            llm_provider: LLM provider to use
            return_confidence: Whether to return confidence score

        Returns:
            Extracted value, or dict with value and confidence if return_confidence=True
        """
        if not self.llm_service:
            self.logger.error("LLM service not initialized")
            return None

        try:
            # Construct extraction prompt
            system_prompt = self._build_system_prompt(field_name, field_type)
            extraction_prompt = self._build_extraction_prompt(
                content, prompt, field_name, field_type
            )

            # Call LLM
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": extraction_prompt}
            ]
            llm_result = await self.llm_service.generate(
                prompt=extraction_prompt,
                messages=messages,
                max_tokens=500,
                temperature=0.1  # Low temperature for factual extraction
            )

            if not llm_result:
                self.logger.warning(f"LLM returned empty response for field '{field_name}'")
                return None

            response = llm_result.get('content', '')
            if not response:
                return None

            # Parse and validate response
            result = self._parse_response(response, field_type)

            if return_confidence:
                # Extract confidence if mentioned in response
                confidence = self._extract_confidence(response)
                return {
                    'value': result,
                    'confidence': confidence
                }

            return result

        except Exception as e:
            self.logger.error(f"LLM extraction failed for field '{field_name}': {str(e)}")
            return None

    async def extract_multiple_fields(
        self,
        content: str,
        field_definitions: List[Dict[str, Any]],
        llm_provider: str = "ollama"
    ) -> Dict[str, Any]:
        """
        Extract multiple fields in a single LLM call

        Args:
            content: Text content to extract from
            field_definitions: List of dicts with 'name', 'prompt', 'type'
            llm_provider: LLM provider to use

        Returns:
            Dictionary mapping field names to extracted values
        """
        if not self.llm_service:
            self.logger.error("LLM service not initialized")
            return {}

        try:
            # Build comprehensive extraction prompt
            system_prompt = """You are a data extraction assistant. Extract the requested information from the provided content.
Return ONLY a valid JSON object with the extracted field values. Do not include any explanations or additional text."""

            fields_description = []
            for field_def in field_definitions:
                field_name = field_def.get('name', 'unknown')
                field_prompt = field_def.get('prompt', f'Extract {field_name}')
                field_type = field_def.get('type', 'string')

                fields_description.append(
                    f"- {field_name} ({field_type}): {field_prompt}"
                )

            extraction_prompt = f"""Content to analyze:
{content[:2000]}  # Limit content length

Extract the following fields:
{chr(10).join(fields_description)}

Return the results as a JSON object with field names as keys."""

            # Call LLM
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": extraction_prompt}
            ]
            llm_result = await self.llm_service.generate(
                prompt=extraction_prompt,
                messages=messages,
                max_tokens=1000,
                temperature=0.1
            )

            if not llm_result:
                return {}

            response = llm_result.get('content', '')
            if not response:
                return {}

            # Parse JSON response
            result = self._parse_json_response(response)

            # Validate and convert field types
            validated_result = {}
            for field_def in field_definitions:
                field_name = field_def['name']
                field_type = field_def.get('type', 'string')

                if field_name in result:
                    validated_value = self._convert_type(
                        result[field_name], field_type
                    )
                    validated_result[field_name] = validated_value

            return validated_result

        except Exception as e:
            self.logger.error(f"Multiple field extraction failed: {str(e)}")
            return {}

    def _build_system_prompt(self, field_name: str, field_type: str) -> str:
        """Build system prompt for extraction"""
        return f"""You are a precise data extraction assistant.
Extract the requested information from the provided content.
The field to extract is: {field_name} (type: {field_type})
Return ONLY the extracted value without any explanation or additional text.
If the information is not found, return "NOT_FOUND"."""

    def _build_extraction_prompt(
        self,
        content: str,
        prompt: str,
        field_name: str,
        field_type: str
    ) -> str:
        """Build extraction prompt"""
        # Limit content length to avoid token limits
        max_content_length = 2000
        truncated_content = content[:max_content_length]
        if len(content) > max_content_length:
            truncated_content += "... [content truncated]"

        return f"""Content:
{truncated_content}

Task: {prompt}

Extract the {field_name} ({field_type}) from the above content.
Return only the extracted value."""

    def _parse_response(self, response: str, field_type: str) -> Optional[Any]:
        """Parse and validate LLM response"""
        try:
            # Remove common wrapper phrases
            response = response.strip()
            response = re.sub(r'^(The|A|An)\s+', '', response, flags=re.IGNORECASE)
            response = re.sub(r'\s*is\s*:', '', response, flags=re.IGNORECASE)

            # Check for "not found" responses
            if response.upper() == "NOT_FOUND" or "not found" in response.lower():
                return None

            # Convert to appropriate type
            return self._convert_type(response, field_type)

        except Exception as e:
            self.logger.error(f"Response parsing failed: {str(e)}")
            return response  # Return as-is if parsing fails

    def _convert_type(self, value: Any, field_type: str) -> Optional[Any]:
        """Convert value to specified type"""
        try:
            if value is None or value == "NOT_FOUND":
                return None

            if field_type == "string":
                return str(value).strip()

            elif field_type == "integer":
                # Extract first number if string contains text
                if isinstance(value, str):
                    match = re.search(r'-?\d+', value)
                    if match:
                        return int(match.group())
                return int(value)

            elif field_type == "float":
                # Extract number (handles currency symbols, commas, etc.)
                if isinstance(value, str):
                    # Remove common separators
                    cleaned = re.sub(r'[,$€£¥]', '', value)
                    match = re.search(r'-?\d+(?:\.\d+)?', cleaned)
                    if match:
                        return float(match.group())
                return float(value)

            elif field_type == "boolean":
                if isinstance(value, bool):
                    return value
                value_str = str(value).lower().strip()
                return value_str in ['true', 'yes', '1', 'y']

            elif field_type in ["date", "datetime"]:
                # Return as string, let downstream handle parsing
                return str(value).strip()

            elif field_type == "array":
                if isinstance(value, list):
                    return value
                # Try to parse as JSON array
                if isinstance(value, str):
                    if value.startswith('['):
                        return json.loads(value)
                    # Split by common delimiters
                    return [v.strip() for v in re.split(r'[,;|]', value)]
                return [value]

            else:
                return value

        except Exception as e:
            self.logger.error(f"Type conversion failed: {str(e)}")
            return value

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON from LLM response with improved error handling"""
        if not response:
            self.logger.error("Empty response from LLM")
            return {}

        # Clean the response first
        response_cleaned = response.strip()

        try:
            # Try direct JSON parse
            result = json.loads(response_cleaned)
            self.logger.debug(f"✓ Successfully parsed JSON directly")
            return result
        except json.JSONDecodeError as e:
            self.logger.debug(f"Direct JSON parse failed: {str(e)}")

        # Try to extract JSON from markdown code blocks (```json ... ```)
        markdown_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_cleaned, re.DOTALL | re.IGNORECASE)
        if markdown_match:
            try:
                result = json.loads(markdown_match.group(1))
                self.logger.debug(f"✓ Successfully parsed JSON from markdown code block")
                return result
            except json.JSONDecodeError as e:
                self.logger.debug(f"Markdown JSON parse failed: {str(e)}")

        # Try to extract JSON object from anywhere in the response (more robust regex)
        # Match nested objects properly - improved to handle more complex nesting
        json_match = re.search(r'\{[^}]*"mapped_data"[^}]*\{.*?\}[^}]*\}', response_cleaned, re.DOTALL)
        if json_match:
            try:
                result = json.loads(json_match.group())
                self.logger.debug(f"✓ Successfully parsed JSON using regex extraction")
                return result
            except json.JSONDecodeError as e:
                self.logger.debug(f"Regex JSON parse failed: {str(e)}")

        # Last resort: try to find any JSON object in the response
        json_match_generic = re.search(r'\{(?:[^{}]|\{[^{}]*\})*\}', response_cleaned, re.DOTALL)
        if json_match_generic:
            try:
                result = json.loads(json_match_generic.group())
                self.logger.warning(f"Parsed JSON using generic regex - may not have expected structure")
                return result
            except json.JSONDecodeError as e:
                self.logger.debug(f"Generic regex JSON parse failed: {str(e)}")

        # Log the actual response for debugging
        response_preview = response_cleaned[:500] if len(response_cleaned) > 500 else response_cleaned
        self.logger.error(
            f"✗ Failed to parse LLM response as JSON after trying all methods.\n"
            f"Response preview (first 500 chars):\n{response_preview}\n"
            f"Response length: {len(response_cleaned)} chars"
        )
        return {}

    def _extract_confidence(self, response: str) -> float:
        """Extract confidence score from response if present"""
        # Look for confidence mentions
        confidence_patterns = [
            r'confidence[:\s]+(\d+(?:\.\d+)?)',
            r'(\d+(?:\.\d+)?)\s*%\s*confident',
            r'certainty[:\s]+(\d+(?:\.\d+)?)',
        ]

        for pattern in confidence_patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                confidence = float(match.group(1))
                # Normalize to 0-1 range if percentage
                if confidence > 1:
                    confidence = confidence / 100
                return max(0.0, min(1.0, confidence))

        # Default confidence if not mentioned
        return 0.8

    async def extract_structured(
        self,
        content: str,
        schema: Dict[str, Any],
        llm_provider: str = "ollama"
    ) -> Optional[Dict[str, Any]]:
        """
        Extract structured data according to a schema

        Args:
            content: Text content to extract from
            schema: JSON schema defining the structure to extract
            llm_provider: LLM provider to use

        Returns:
            Extracted structured data matching schema
        """
        if not self.llm_service:
            return None

        try:
            system_prompt = """You are a data extraction assistant. Extract information according to the provided schema.
Return ONLY a valid JSON object matching the schema. Do not include any explanations."""

            extraction_prompt = f"""Content:
{content[:2000]}

Schema:
{json.dumps(schema, indent=2)}

Extract data matching the above schema from the content."""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": extraction_prompt}
            ]
            llm_result = await self.llm_service.generate(
                prompt=extraction_prompt,
                messages=messages,
                max_tokens=1500,
                temperature=0.1
            )

            if not llm_result:
                return None

            response = llm_result.get('content', '')
            if not response:
                return None

            return self._parse_json_response(response)

        except Exception as e:
            self.logger.error(f"Structured extraction failed: {str(e)}")
            return None

    async def map_to_custom_template(
        self,
        scraped_data: str,
        template_columns: List[str],
        template_examples: Optional[Dict[str, Any]] = None,
        llm_provider: str = "openai"
    ) -> Optional[Dict[str, Any]]:
        """
        Map scraped data to custom template columns using LLM

        This method takes raw scraped data and a custom template (with column headers
        and optionally example values), and uses an LLM to intelligently map the
        scraped values to the correct template columns.

        Key features:
        - Never hallucinates or makes up values
        - Only extracts values that exist in the scraped data
        - Marks missing fields as "— (requires additional research)"
        - Provides transparency about which data points need external sources

        Args:
            scraped_data: Raw scraped content (HTML or text)
            template_columns: List of column headers from the custom template
            template_examples: Optional dict with example values for each column
            llm_provider: LLM provider to use (openai recommended for accuracy)

        Returns:
            Dictionary mapping template columns to extracted values, or None if failed

        Example:
            >>> scraped = "<html>... Market Cap: ₹ 1,234 Cr ... P/E: 25.3 ...</html>"
            >>> columns = ["Market Cap", "Stock P/E", "Revenue Growth", "Notes"]
            >>> examples = {"Market Cap": "1234", "Stock P/E": "25.3"}
            >>> result = await extractor.map_to_custom_template(scraped, columns, examples)
            >>> # Result: {
            >>>     "mapped_data": {
            >>>         "Market Cap": "1234",
            >>>         "Stock P/E": "25.3",
            >>>         "Revenue Growth": "— (requires additional research)",
            >>>         "Notes": ""
            >>>     },
            >>>     "missing_fields": ["Revenue Growth"],
            >>>     "extraction_complete": False
            >>> }
        """
        if not self.llm_service:
            self.logger.error("LLM service not initialized")
            return None

        try:
            logger.info("="*80)
            logger.info("🤖 LLM TEMPLATE MAPPING STARTED")
            logger.info("="*80)
            logger.info(f"📊 Template columns to map: {len(template_columns)}")
            logger.info(f"📋 Columns: {', '.join(template_columns)}")
            logger.info(f"📏 Scraped data length: {len(scraped_data):,} characters")
            logger.info(f"🤖 LLM Provider: {llm_provider}")
            logger.info(f"📝 Template examples provided: {'Yes' if template_examples else 'No'}")
            if template_examples:
                logger.info(f"   Examples: {template_examples}")
            logger.info("="*80)

            # Build the system prompt with clear instructions
            system_prompt = """You are a professional data extraction and mapping assistant specialized in extracting structured data from webpages.

Your task: Extract data from scraped webpage content and map it to template columns.

CRITICAL RULES:
1. Extract ONLY values that actually exist in the scraped data
2. NEVER make up, infer, or hallucinate values
3. If a field is not found in the scraped data, use: "—"
4. Return VALID JSON ONLY - no markdown, no code blocks, no explanations
5. Extract exact values as they appear (preserve numbers, text, formatting)
6. Look for variations of the column name (e.g., "Market Cap" might appear as "Market Capitalization", "Mkt Cap", or "MCap")
7. For financial data: Extract numbers with their units (Cr, L, $, %, etc.)
8. For company names: Look in page title, headers, or main content
9. Search the ENTIRE content thoroughly - data might appear in tables, spans, divs, or text

OUTPUT FORMAT - You MUST return a JSON object exactly like this:
{
  "mapped_data": {
    "Column1": "value found in data",
    "Column2": "another value",
    "Column3": "—"
  },
  "missing_fields": ["Column3"]
}

IMPORTANT: Return ONLY the JSON object. No markdown formatting. No code blocks. No explanations."""

            # Build the extraction prompt
            template_info = "TEMPLATE COLUMNS TO EXTRACT:\n"
            for i, col in enumerate(template_columns, 1):
                example_val = ""
                if template_examples and col in template_examples:
                    example_val = f" (expected format: {template_examples[col]})"
                template_info += f"{i}. {col}{example_val}\n"

            # Truncate scraped data if too long (keep first 20000 chars for better context)
            # Increased from 10000 to 20000 to capture more data from complex pages
            truncated_data = scraped_data[:20000]
            if len(scraped_data) > 20000:
                truncated_data += "\n\n[... content truncated ...]"

            extraction_prompt = f"""SCRAPED WEBPAGE CONTENT:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{truncated_data}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{template_info}

EXTRACTION INSTRUCTIONS:
1. Read the scraped content thoroughly - check ALL sections
2. For EACH template column:
   a. Search for exact matches or close variations of the column name
   b. Look in common locations: headers, tables, lists, key-value pairs
   c. Extract the value exactly as it appears (with units like Cr, %, $, etc.)
   d. If the column has multiple possible matches, choose the most relevant one
3. For missing fields: If you cannot find ANY relevant data for a column, use "—"
4. Important: Financial/numeric data often appears in tables - parse them carefully
5. Return a valid JSON object with "mapped_data" and "missing_fields"

EXAMPLE PATTERNS TO LOOK FOR:
- Company Name: Often in <title>, <h1>, or main heading
- Market Cap: Look for "Market Cap", "MCap", "Market Capitalization"
- Revenue/EBITDA: Often in financial tables with labels like "Sales", "Revenue", "Operating Profit"
- Percentages: Often shown as "25.3%", "25.3 %", or "25.3 percent"
- Founded Year: Look for "Founded", "Established", "Since"

Return your response as PURE JSON (no markdown, no code blocks):"""

            # Log the mapping attempt
            logger.info("─"*80)
            logger.info(f"📡 Calling LLM service...")
            logger.info(f"🤖 Provider: {llm_provider}")
            logger.info(f"🎯 Max tokens: 3000")
            logger.info(f"🌡️  Temperature: 0.0 (deterministic)")
            logger.info("─"*80)

            # Call LLM
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": extraction_prompt}
            ]

            llm_result = await self.llm_service.generate(
                prompt=extraction_prompt,
                messages=messages,
                max_tokens=3000,  # Increased from 2000 to handle more fields
                temperature=0.0  # Zero temperature for maximum consistency
            )

            if not llm_result:
                logger.error("❌ LLM returned empty response for template mapping")
                logger.error("💡 Possible causes:")
                logger.error("   - LLM service not properly configured")
                logger.error("   - API key missing or invalid")
                logger.error("   - Network connectivity issues")
                logger.error("   - LLM service timeout")
                return None

            logger.info("✅ LLM response received")
            logger.info(f"📊 Response metadata: {llm_result.get('model', 'unknown')} model")
            if 'tokens' in llm_result:
                logger.info(f"🔢 Tokens used: {llm_result.get('tokens', 0)}")
            if 'latency_ms' in llm_result:
                logger.info(f"⏱️  Latency: {llm_result.get('latency_ms', 0):.0f}ms")

            response = llm_result.get('content', '')
            if not response:
                logger.error("❌ LLM response content is empty")
                return None

            logger.info(f"📏 Response length: {len(response):,} characters")
            logger.info(f"📝 Response preview (first 500 chars):")
            logger.info(f"   {response[:500]}")
            logger.info("─"*80)

            # Parse the JSON response
            logger.info("🔍 Parsing LLM response as JSON...")
            result = self._parse_json_response(response)

            if not result:
                self.logger.error(
                    "✗ Failed to parse LLM response as JSON. "
                    "Returning None to indicate extraction failure."
                )
                return None

            # Extract mapped_data and missing_fields
            mapped_data = result.get('mapped_data', {})
            missing_fields = result.get('missing_fields', [])

            # Validate the structure
            if not isinstance(mapped_data, dict):
                self.logger.error(
                    f"✗ Invalid LLM response structure: 'mapped_data' is not a dict. "
                    f"Got type: {type(mapped_data)}"
                )
                return None

            # Standardize missing field markers to just "—"
            for key, value in mapped_data.items():
                if value in ["— (requires additional research)", "—(requires additional research)"]:
                    mapped_data[key] = "—"

            # Count non-empty extracted values
            non_empty_values = sum(
                1 for v in mapped_data.values()
                if v and v not in ["—", "", None]
            )

            if non_empty_values == 0:
                self.logger.warning(
                    f"⚠ LLM extraction returned 0 non-empty values out of {len(template_columns)} fields. "
                    f"This may indicate the scraped data doesn't contain the requested information."
                )
            elif missing_fields:
                self.logger.info(
                    f"✓ Mapped {non_empty_values}/{len(template_columns)} fields successfully. "
                    f"{len(missing_fields)} fields require additional research: {', '.join(missing_fields)}"
                )
            else:
                self.logger.info(
                    f"✓ Successfully mapped all {len(mapped_data)} template fields "
                    f"({non_empty_values} non-empty values)"
                )

            # Ensure all template columns are present in the result
            for col in template_columns:
                if col not in mapped_data:
                    mapped_data[col] = "—"
                    if col not in missing_fields:
                        missing_fields.append(col)

            return {
                'mapped_data': mapped_data,
                'missing_fields': missing_fields,
                'extraction_complete': len(missing_fields) == 0,
                'non_empty_count': non_empty_values
            }

        except Exception as e:
            self.logger.error(f"Template mapping failed: {str(e)}", exc_info=True)
            return None
