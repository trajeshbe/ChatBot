"""
Query Classification Service

Classifies queries to determine if they are:
1. AI-personal questions (about the AI itself, capabilities, identity)
2. Document-based questions (requiring RAG retrieval)
3. General knowledge questions (can be answered without documents)

This prevents the system from returning irrelevant documents for queries
that don't require document context.
"""

import re
from typing import Dict, Literal
import logging

logger = logging.getLogger(__name__)


class QueryClassifier:
    """Classify queries to improve RAG relevance"""

    # Patterns for AI-personal questions
    AI_PERSONAL_PATTERNS = [
        # Direct questions about the AI
        r'\b(who|what)\s+(are|is)\s+you\b',
        r'\byour\s+(name|identity|purpose|capabilities)\b',
        r'\btell\s+me\s+about\s+(yourself|you)\b',
        r'\bwho\s+(created|made|built|developed)\s+you\b',
        r'\bwhat\s+(can|do)\s+you\s+do\b',
        r'\bhow\s+(do|does)\s+you\s+work\b',
        r'\bwhat\s+ai\s+are\s+you\b',
        r'\bwhat\s+model\s+are\s+you\b',
        r'\bwhat\s+language\s+model\b',
        r'\bare\s+you\s+(an|a)\s+(ai|bot|assistant|chatbot)\b',

        # Greetings and small talk
        r'^(hi|hello|hey|greetings|good\s+(morning|afternoon|evening))[!.,]?\s*$',
        r'^how\s+are\s+you[?!.]?\s*$',
        r'^what\'?s\s+up[?!.]?\s*$',

        # Questions about capabilities
        r'\bcan\s+you\s+(help|assist|answer|explain)\b',
        r'\bwhat\s+do\s+you\s+know\s+about\b(?!.*\bdocument)',
    ]

    # Patterns for document-specific questions
    DOCUMENT_SPECIFIC_PATTERNS = [
        r'\b(according|based\s+on|in|from)\s+the\s+(document|file|pdf|text|article)\b',
        r'\bwhat\s+(does|is)\s+the\s+document\s+(say|mention|state)\b',
        r'\bin\s+this\s+(file|document|pdf|text)\b',
        r'\bfrom\s+the\s+(uploaded|attached)\s+(file|document)\b',
        r'\bsummarize\s+(the|this)\s+(document|file|text)\b',
    ]

    # General knowledge questions that might not need documents
    GENERAL_KNOWLEDGE_PATTERNS = [
        r'\bwhat\s+is\s+(python|java|javascript|machine\s+learning|ai)\b',
        r'\bhow\s+(does|do|to)\s+[a-z]+\s+work\b',
        r'\bexplain\s+[a-z\s]+\b',
        r'\bdefine\s+[a-z\s]+\b',
    ]

    def __init__(self):
        self.ai_personal_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.AI_PERSONAL_PATTERNS]
        self.document_specific_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.DOCUMENT_SPECIFIC_PATTERNS]
        self.general_knowledge_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.GENERAL_KNOWLEDGE_PATTERNS]

    def classify(self, query: str) -> Dict[str, any]:
        """
        Classify a query

        Returns:
            Dict with:
                - query_type: 'ai_personal', 'document_specific', 'general', or 'ambiguous'
                - confidence: float 0-1
                - use_documents: bool - whether to use RAG retrieval
                - reason: str - explanation
        """
        query = query.strip()

        # Check for AI-personal questions
        ai_personal_matches = sum(1 for regex in self.ai_personal_regex if regex.search(query))
        if ai_personal_matches > 0:
            logger.info(f"🤖 Classified as AI-personal question: {query[:50]}...")
            return {
                'query_type': 'ai_personal',
                'confidence': min(1.0, ai_personal_matches * 0.5),
                'use_documents': False,  # Don't use documents for AI-personal questions
                'reason': 'Question is about the AI assistant itself, not document content'
            }

        # Check for explicit document-specific questions
        doc_specific_matches = sum(1 for regex in self.document_specific_regex if regex.search(query))
        if doc_specific_matches > 0:
            logger.info(f"📄 Classified as document-specific question: {query[:50]}...")
            return {
                'query_type': 'document_specific',
                'confidence': min(1.0, doc_specific_matches * 0.6),
                'use_documents': True,  # Definitely use documents
                'reason': 'Question explicitly references documents'
            }

        # Check for general knowledge
        general_matches = sum(1 for regex in self.general_knowledge_regex if regex.search(query))

        # Default: try documents but with awareness it might be general question
        if general_matches > 0:
            logger.info(f"🌍 Classified as general knowledge question: {query[:50]}...")
            return {
                'query_type': 'general',
                'confidence': 0.6,
                'use_documents': True,  # Try documents, but fallback gracefully
                'reason': 'General knowledge question - will try documents first'
            }

        # Ambiguous - try documents
        logger.info(f"❓ Ambiguous classification: {query[:50]}...")
        return {
            'query_type': 'ambiguous',
            'confidence': 0.5,
            'use_documents': True,
            'reason': 'Query type unclear - trying document retrieval'
        }

    def should_skip_rag(self, query: str) -> bool:
        """
        Quick check if we should skip RAG entirely
        (for AI-personal questions)
        """
        classification = self.classify(query)
        return not classification['use_documents']


# Singleton
query_classifier = QueryClassifier()
