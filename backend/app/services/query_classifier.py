"""
Query Classification Service

Classifies queries using LLM to determine if they are:
1. AI-personal questions (about the AI itself, capabilities, identity)
2. Document-based questions (requiring RAG retrieval)
3. General knowledge questions (can be answered without documents)

This prevents the system from returning irrelevant documents for queries
that don't require document context.
"""

import json
from typing import Dict, TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class QueryClassifier:
    """Classify queries using LLM to improve RAG relevance"""

    CLASSIFICATION_PROMPT = """You are a query classification system. Analyze the user's query and classify it into one of these categories:

1. **ai_personal**: Questions about the AI assistant itself (identity, capabilities, how it works, greetings, asking the AI to introduce itself)
   Examples: "Who are you?", "What can you do?", "Hello!", "How do you work?", "Tell me about yourself", "Introduce yourself", "What are your capabilities?"

2. **document_specific**: Questions that explicitly reference documents or uploaded files
   Examples: "What does the document say?", "Summarize this PDF", "According to the uploaded file..."

3. **general**: General knowledge questions about the world (science, history, math, facts)
   Examples: "What is the capital of France?", "How does photosynthesis work?", "When was World War 2?"

4. **ambiguous**: Questions that could require documents but don't explicitly reference them
   Examples: "Tell me about machine learning", "What are the key findings?", "Explain the methodology"

User Query: "{query}"

Respond with ONLY a JSON object in this exact format (no markdown, no code blocks):
{{
    "query_type": "ai_personal" | "document_specific" | "general" | "ambiguous",
    "confidence": 0.0 to 1.0,
    "use_documents": true | false,
    "reason": "brief explanation of classification"
}}

Rules:
- ai_personal: use_documents = false
- document_specific: use_documents = true
- general: use_documents = false
- ambiguous: use_documents = true (default to checking documents when uncertain)
"""

    def __init__(self, llm_service: 'LLMService' = None):
        """
        Initialize the query classifier with an LLM service.

        Args:
            llm_service: LLM service instance for classification. If None, will be imported lazily.
        """
        self._llm_service = llm_service

    @property
    def llm_service(self) -> 'LLMService':
        """Lazy load LLM service to avoid circular imports"""
        if self._llm_service is None:
            from app.services.llm_service import llm_service
            self._llm_service = llm_service
        return self._llm_service

    def _rule_based_classify(self, query: str) -> Dict[str, any]:
        """
        Simple rule-based classification for common patterns (fallback)

        Returns classification or None if no rule matches
        """
        query_lower = query.lower().strip()

        # AI-personal patterns
        ai_patterns = [
            'who are you', 'what are you', 'tell me about yourself', 'introduce yourself',
            'what can you do', 'what are your capabilities', 'how do you work',
            'hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening'
        ]

        for pattern in ai_patterns:
            if pattern in query_lower:
                return {
                    'query_type': 'ai_personal',
                    'confidence': 0.9,
                    'use_documents': False,
                    'reason': f'Matched AI-personal pattern: "{pattern}"'
                }

        # Document-specific patterns
        doc_patterns = [
            'according to the document', 'in the file', 'the pdf says',
            'what does the document', 'summarize the', 'from the uploaded'
        ]

        for pattern in doc_patterns:
            if pattern in query_lower:
                return {
                    'query_type': 'document_specific',
                    'confidence': 0.95,
                    'use_documents': True,
                    'reason': f'Matched document-specific pattern: "{pattern}"'
                }

        return None  # No rule matched, use LLM

    async def classify(self, query: str) -> Dict[str, any]:
        """
        Classify a query using LLM with rule-based fallback

        Returns:
            Dict with:
                - query_type: 'ai_personal', 'document_specific', 'general', or 'ambiguous'
                - confidence: float 0-1
                - use_documents: bool - whether to use RAG retrieval
                - reason: str - explanation
        """
        query = query.strip()

        # Try rule-based classification first (fast and deterministic)
        rule_result = self._rule_based_classify(query)
        if rule_result:
            logger.info(f"🎯 Rule-based classification: {rule_result['query_type']} - {rule_result['reason']}")
            return rule_result

        try:
            # Use LLM to classify the query
            prompt = self.CLASSIFICATION_PROMPT.format(query=query)

            # Use a fast model for classification (prefer cheaper/faster models)
            # Note: Using the correct generate() method with proper parameters
            result = await self.llm_service.generate(
                prompt=prompt,
                max_tokens=200,  # Short response expected
                temperature=0.0,  # Deterministic classification
                model_id=None  # Use default model
            )

            # Extract the response content
            response_text = result.get('content', '').strip()
            if response_text.startswith('```'):
                # Remove code block markers
                lines = response_text.split('\n')
                response_text = '\n'.join(lines[1:-1]) if len(lines) > 2 else response_text
                response_text = response_text.replace('```json', '').replace('```', '').strip()

            classification = json.loads(response_text)

            # Validate response format
            required_fields = {'query_type', 'confidence', 'use_documents', 'reason'}
            if not all(field in classification for field in required_fields):
                raise ValueError(f"Missing required fields in classification response. Got: {classification.keys()}")

            # Validate query_type
            valid_types = {'ai_personal', 'document_specific', 'general', 'ambiguous'}
            if classification['query_type'] not in valid_types:
                raise ValueError(f"Invalid query_type: {classification['query_type']}")

            # Ensure confidence is a float between 0 and 1
            classification['confidence'] = max(0.0, min(1.0, float(classification['confidence'])))

            # Log classification
            emoji_map = {
                'ai_personal': '🤖',
                'document_specific': '📄',
                'general': '🌍',
                'ambiguous': '❓'
            }
            emoji = emoji_map.get(classification['query_type'], '❓')
            logger.info(
                f"{emoji} Classified as {classification['query_type']} "
                f"(confidence: {classification['confidence']:.2f}): {query[:50]}... - {classification['reason']}"
            )

            return classification

        except Exception as e:
            # Fallback to ambiguous classification on error
            logger.error(f"Error classifying query: {e}. Falling back to ambiguous classification.")
            return {
                'query_type': 'ambiguous',
                'confidence': 0.5,
                'use_documents': True,
                'reason': f'Classification error - defaulting to document retrieval. Error: {str(e)[:100]}'
            }

    async def should_skip_rag(self, query: str) -> bool:
        """
        Quick check if we should skip RAG entirely
        (for AI-personal questions)
        """
        classification = await self.classify(query)
        return not classification['use_documents']


# Singleton
query_classifier = QueryClassifier()
