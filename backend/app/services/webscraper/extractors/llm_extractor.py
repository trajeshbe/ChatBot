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
        llm_provider: str = "ollama",
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
            response = await self.llm_service.generate_response(
                prompt=extraction_prompt,
                system_prompt=system_prompt,
                provider=llm_provider,
                max_tokens=500,
                temperature=0.1  # Low temperature for factual extraction
            )

            if not response:
                self.logger.warning(f"LLM returned empty response for field '{field_name}'")
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
            response = await self.llm_service.generate_response(
                prompt=extraction_prompt,
                system_prompt=system_prompt,
                provider=llm_provider,
                max_tokens=1000,
                temperature=0.1
            )

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
        """Parse JSON from LLM response"""
        try:
            # Try direct JSON parse
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON from response
            match = re.search(r'\{[^}]+\}', response, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass

            self.logger.warning("Could not parse JSON from LLM response")
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

            response = await self.llm_service.generate_response(
                prompt=extraction_prompt,
                system_prompt=system_prompt,
                provider=llm_provider,
                max_tokens=1500,
                temperature=0.1
            )

            if not response:
                return None

            return self._parse_json_response(response)

        except Exception as e:
            self.logger.error(f"Structured extraction failed: {str(e)}")
            return None
