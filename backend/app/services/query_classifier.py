"""
Query Classification and Preprocessing Service

This service provides:
1. Query Classification: Determine if queries need documents (ai_personal, document_specific, general, ambiguous)
2. Query Preprocessing: Improve retrieval by rewriting and expanding queries
3. Proper Noun Detection: Identify names/entities to adjust similarity thresholds
4. Adaptive Thresholding: Recommend appropriate similarity thresholds per query

This prevents the system from returning irrelevant documents for queries
that don't require document context, and improves retrieval accuracy.
"""

import json
import re
from typing import Dict, List, TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class QueryClassifier:
    """Classify and preprocess queries to improve RAG relevance and retrieval accuracy"""

    # Conversational patterns to rewrite for better retrieval
    CONVERSATIONAL_PATTERNS = {
        r"^do you know (about )?(.+)\??$": "tell me about \\2",
        r"^are you familiar with (.+)\??$": "explain \\1",
        r"^have you heard (of |about )?(.+)\??$": "describe \\2",
        r"^can you tell me (about )?(.+)\??$": "tell me about \\2",
        r"^what do you know about (.+)\??$": "tell me about \\1",
        r"^(.+)\s*\?+\s*$": "tell me about \\1",  # Just "X ?" → "tell me about X"
    }

    # Informational query starters (good patterns that don't need rewriting)
    INFORMATIONAL_STARTERS = {
        'tell me', 'explain', 'describe', 'what is', 'who is', 'where is',
        'when was', 'how does', 'why did', 'define', 'summarize'
    }

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

        # General knowledge patterns (NEW - Fix for Bug #1)
        # These are common factual questions that should use direct LLM, not documents
        general_knowledge_starters = [
            'what is the capital of',
            'what is the population of',
            'when was',
            'when did',
            'who invented',
            'who discovered',
            'how many',
            'how much',
            'where is',
            'what year',
            'what language',
            'what currency',
            'what continent',
            'what ocean',
            'what mountain',
            'what river',
            'define ',
            'what does ',
            'how does photosynthesis',
            'how does gravity',
            'what causes',
            'what is dna',
            'what is rna',
            'what is the speed of light',
            'what is the distance',
            'what is the formula',
            'how to calculate',
            'what is pi',
            'who is the president',
            'who is the prime minister',
            'what is the largest',
            'what is the smallest',
            'what is the tallest',
            'what is the longest',
            'what is the fastest'
        ]

        for pattern in general_knowledge_starters:
            if query_lower.startswith(pattern):
                return {
                    'query_type': 'general',
                    'confidence': 0.85,
                    'use_documents': False,
                    'reason': f'Matched general knowledge pattern: "{pattern}"'
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

    def preprocess_query(self, query: str) -> Dict:
        """
        Preprocess query to improve retrieval accuracy

        Args:
            query: Original user query

        Returns:
            Dict with:
                - original_query: Original query text
                - processed_query: Preprocessed query text
                - rewritten: Whether query was rewritten
                - expanded: Whether query was expanded
                - has_proper_nouns: Whether query contains proper nouns
                - proper_nouns: List of detected proper nouns
                - recommended_threshold: Recommended similarity threshold
        """
        original_query = query.strip()
        processed_query = original_query
        rewritten = False
        expanded = False

        # Step 1: Detect proper nouns FIRST (before any rewriting)
        proper_nouns = self._detect_proper_nouns(original_query)
        has_proper_nouns = len(proper_nouns) > 0

        # Step 2: Rewrite conversational queries
        rewritten_query = self._rewrite_conversational(processed_query)
        if rewritten_query != processed_query:
            logger.info(f"🔄 Query rewritten: '{processed_query}' → '{rewritten_query}'")
            processed_query = rewritten_query
            rewritten = True

        # Step 3: Expand short queries
        expanded_query = self._expand_short_query(processed_query)
        if expanded_query != processed_query:
            logger.info(f"📝 Query expanded: '{processed_query}' → '{expanded_query}'")
            processed_query = expanded_query
            expanded = True

        # Step 4: Determine recommended threshold based on query characteristics
        recommended_threshold = self._calculate_recommended_threshold(
            query=processed_query,
            has_proper_nouns=has_proper_nouns,
            is_short=len(original_query.split()) <= 4
        )

        result = {
            'original_query': original_query,
            'processed_query': processed_query,
            'rewritten': rewritten,
            'expanded': expanded,
            'has_proper_nouns': has_proper_nouns,
            'proper_nouns': proper_nouns,
            'recommended_threshold': recommended_threshold,
            'preprocessing_applied': rewritten or expanded
        }

        if result['preprocessing_applied']:
            logger.info(
                f"✅ Query preprocessing: proper_nouns={has_proper_nouns} ({proper_nouns}), "
                f"threshold={recommended_threshold:.2f}"
            )

        return result

    def _detect_proper_nouns(self, query: str) -> List[str]:
        """
        Detect proper nouns (names, places, brands) in query

        Proper nouns are:
        - Capitalized words (except sentence start)
        - Words with mixed case (like "iPhone")
        - All-caps acronyms (min 2 letters)
        """
        proper_nouns = []

        # Pattern 1: Capitalized words (not at sentence start)
        words = query.split()
        for i, word in enumerate(words):
            # Clean punctuation
            clean_word = re.sub(r'[^\w\s]', '', word)

            # Skip if empty after cleaning
            if not clean_word:
                continue

            # Skip common question words at start
            if i == 0 and clean_word.lower() in {'do', 'are', 'can', 'have', 'what', 'who', 'where', 'when', 'why', 'how'}:
                continue

            # Capitalized word (like "Aadhan", "John", "Microsoft")
            if len(clean_word) > 1 and clean_word[0].isupper():
                # Not at sentence start OR sentence doesn't start with question word
                if i > 0 or (i == 0 and words[0][0].lower() not in {'d', 'a', 'c', 'h', 'w'}):
                    proper_nouns.append(clean_word)

        # Pattern 2: All-caps acronyms (min 2 letters)
        acronyms = re.findall(r'\b[A-Z]{2,}\b', query)
        proper_nouns.extend(acronyms)

        # Pattern 3: Mixed case (like iPhone, macOS)
        mixed_case = re.findall(r'\b[a-z]+[A-Z][a-zA-Z]*\b|\b[A-Z][a-z]+[A-Z][a-zA-Z]*\b', query)
        proper_nouns.extend(mixed_case)

        # Deduplicate
        proper_nouns = list(set(proper_nouns))

        if proper_nouns:
            logger.debug(f"🏷️  Detected proper nouns: {proper_nouns}")

        return proper_nouns

    def _rewrite_conversational(self, query: str) -> str:
        """
        Rewrite conversational queries to informational format

        Examples:
            "do you know Aadhan?" → "tell me about Aadhan"
            "are you familiar with Python?" → "explain Python"
            "Aadhan ?" → "tell me about Aadhan"
        """
        query_lower = query.lower().strip()

        # Check if already informational
        for starter in self.INFORMATIONAL_STARTERS:
            if query_lower.startswith(starter):
                # Already informational, no need to rewrite
                return query

        # Try to match and rewrite conversational patterns
        for pattern, replacement in self.CONVERSATIONAL_PATTERNS.items():
            match = re.match(pattern, query_lower, re.IGNORECASE)
            if match:
                # Extract the important part (usually the last group)
                rewritten = re.sub(pattern, replacement, query_lower, flags=re.IGNORECASE)
                # Clean up extra spaces and punctuation
                rewritten = re.sub(r'\s+', ' ', rewritten).strip()
                rewritten = rewritten.rstrip('?!.,')
                return rewritten

        # No pattern matched, return original
        return query

    def _expand_short_query(self, query: str) -> str:
        """
        Expand very short queries for better embedding

        Short queries (1-3 words) often don't embed well.
        Add context words to improve semantic matching.

        Examples:
            "Aadhan" → "tell me about Aadhan"
            "Python tutorial" → "explain Python tutorial"
        """
        words = query.split()

        # Only expand if very short (1-3 words)
        if len(words) > 3:
            return query

        # Don't expand if already has informational starter
        query_lower = query.lower()
        for starter in self.INFORMATIONAL_STARTERS:
            if query_lower.startswith(starter):
                return query

        # Expand based on length
        if len(words) == 1:
            # Single word: "Aadhan" → "tell me about Aadhan"
            return f"tell me about {query}"
        elif len(words) == 2:
            # Two words: "Aadhan story" → "tell me about Aadhan story"
            return f"tell me about {query}"
        elif len(words) == 3:
            # Three words: might be okay, but add light expansion
            return f"explain {query}"

        return query

    def _calculate_recommended_threshold(self, query: str,
                                        has_proper_nouns: bool,
                                        is_short: bool) -> float:
        """
        Calculate recommended similarity threshold based on query characteristics

        Proper nouns (names, places) often have lower semantic similarity
        because they're specific and may not appear frequently in training data.

        Args:
            query: Preprocessed query text
            has_proper_nouns: Whether query contains proper nouns
            is_short: Whether query is short (<= 4 words)

        Returns:
            Recommended threshold (between 0.45 and 0.75)
        """
        # Start with lower default than original 0.75
        threshold = 0.60

        # Adjust for proper nouns (lower threshold for better recall)
        if has_proper_nouns:
            threshold -= 0.10  # Lower to 0.50 for proper nouns

        # Adjust for short queries (lower threshold for better recall)
        if is_short:
            threshold -= 0.05  # Lower by another 0.05

        # Clamp to reasonable range
        threshold = max(0.45, min(0.75, threshold))

        return threshold


# Singleton
query_classifier = QueryClassifier()
