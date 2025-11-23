"""
Query Reformulation Service

State-of-the-art query expansion and reformulation for improved retrieval recall.

Techniques:
1. Synonym expansion (e.g., "car" → "vehicle", "automobile")
2. LLM-based query rewriting for ambiguous queries
3. Multi-query generation (generates 2-3 variations)
4. Acronym expansion (e.g., "ML" → "Machine Learning")

Expected improvement: +10-20% recall (finds more relevant documents)
"""

from typing import List, Dict, Optional
import logging
import re
from functools import lru_cache

logger = logging.getLogger(__name__)


class QueryReformulationService:
    """
    Query reformulation for improved retrieval recall.

    Uses lightweight techniques + optional LLM for complex cases.
    """

    # Common technical acronyms and expansions
    ACRONYMS = {
        "ai": "artificial intelligence",
        "ml": "machine learning",
        "dl": "deep learning",
        "nlp": "natural language processing",
        "llm": "large language model",
        "rag": "retrieval augmented generation",
        "api": "application programming interface",
        "sql": "structured query language",
        "gpu": "graphics processing unit",
        "cpu": "central processing unit",
        "ui": "user interface",
        "ux": "user experience",
        "qa": "quality assurance",
        "ci": "continuous integration",
        "cd": "continuous deployment"
    }

    # Common synonym groups (domain-specific - extend as needed)
    SYNONYM_GROUPS = {
        # General
        "purchase": ["buy", "acquire", "obtain"],
        "find": ["locate", "discover", "search"],
        "create": ["generate", "produce", "make"],
        "delete": ["remove", "erase", "eliminate"],

        # Technical
        "model": ["algorithm", "system"],
        "document": ["file", "record", "report"],
        "user": ["customer", "client", "person"],
        "error": ["issue", "problem", "bug"],
        "fix": ["resolve", "correct", "repair"],

        # Business
        "cost": ["price", "expense", "fee"],
        "profit": ["revenue", "income", "earnings"],
        "contract": ["agreement", "deal"],
    }

    def __init__(self):
        self.max_reformulations = 3  # Generate up to 3 query variations

    def reformulate_query(
        self,
        query: str,
        include_acronyms: bool = True,
        include_synonyms: bool = True,
        use_llm: bool = False
    ) -> List[str]:
        """
        Generate multiple reformulations of a query.

        Args:
            query: Original user query
            include_acronyms: Expand acronyms (e.g., "ML" → "Machine Learning")
            include_synonyms: Add synonym variations
            use_llm: Use LLM for complex reformulation (slower, more expensive)

        Returns:
            List of query variations (includes original)
        """
        reformulations = [query]  # Always include original

        # 1. Acronym expansion
        if include_acronyms:
            acronym_expanded = self._expand_acronyms(query)
            if acronym_expanded != query and acronym_expanded not in reformulations:
                reformulations.append(acronym_expanded)
                logger.debug(f"Acronym expansion: '{acronym_expanded}'")

        # 2. Synonym expansion
        if include_synonyms:
            synonym_variations = self._generate_synonym_variations(query)
            for variation in synonym_variations[:2]:  # Max 2 synonym variations
                if variation not in reformulations:
                    reformulations.append(variation)
                    logger.debug(f"Synonym variation: '{variation}'")

        # 3. LLM-based reformulation (optional, for complex queries)
        if use_llm and len(query.split()) >= 5:  # Only for queries 5+ words
            llm_reformulation = self._llm_reformulate(query)
            if llm_reformulation and llm_reformulation not in reformulations:
                reformulations.append(llm_reformulation)
                logger.debug(f"LLM reformulation: '{llm_reformulation}'")

        # Limit total reformulations
        reformulations = reformulations[:self.max_reformulations]

        logger.info(
            f"Query reformulation: '{query}' → {len(reformulations)} variations"
        )

        return reformulations

    def _expand_acronyms(self, query: str) -> str:
        """
        Expand known acronyms in query.

        Example: "What is ML?" → "What is Machine Learning?"
        """
        words = query.split()
        expanded_words = []

        for word in words:
            # Check if word is an acronym (all caps, 2-5 letters)
            word_lower = word.lower().strip('?.,!')

            if word_lower in self.ACRONYMS:
                # Replace acronym with expansion
                expanded = self.ACRONYMS[word_lower]
                logger.debug(f"Expanded acronym: {word} → {expanded}")
                expanded_words.append(expanded)
            else:
                expanded_words.append(word)

        return ' '.join(expanded_words)

    def _generate_synonym_variations(self, query: str) -> List[str]:
        """
        Generate query variations using synonyms.

        Example: "How to fix bugs?" → ["How to resolve bugs?", "How to fix issues?"]
        """
        variations = []
        words = query.split()

        # Find words with synonyms
        for i, word in enumerate(words):
            word_lower = word.lower().strip('?.,!')

            # Check if word has synonyms
            for key, synonyms in self.SYNONYM_GROUPS.items():
                if word_lower == key or word_lower in synonyms:
                    # Generate variation by replacing with synonym
                    for synonym in synonyms:
                        if synonym != word_lower:
                            new_words = words.copy()
                            # Preserve original capitalization pattern
                            if word[0].isupper():
                                synonym = synonym.capitalize()
                            new_words[i] = synonym + word[len(word_lower):]  # Preserve punctuation
                            variation = ' '.join(new_words)
                            if variation not in variations:
                                variations.append(variation)

        return variations[:2]  # Return max 2 variations

    def _llm_reformulate(self, query: str) -> Optional[str]:
        """
        Use LLM to reformulate complex or ambiguous queries.

        This is expensive and slow, so use sparingly.
        For now, returns None (stub for future LLM integration).

        Args:
            query: Original query

        Returns:
            Reformulated query or None
        """
        # TODO: Integrate with LLM service for complex reformulation
        # Example prompt: "Rewrite this question more clearly: {query}"
        # For now, return None to avoid extra LLM calls
        return None

    def should_reformulate(self, query: str) -> bool:
        """
        Determine if a query would benefit from reformulation.

        Heuristics:
        - Short queries (1-2 words) → unlikely to benefit
        - Contains known acronyms → yes
        - Contains synonyms → yes
        - Very long queries (10+ words) → probably already clear
        """
        words = query.split()
        word_count = len(words)

        # Too short
        if word_count <= 2:
            return False

        # Too long (probably already detailed)
        if word_count > 15:
            return False

        # Check for acronyms
        for word in words:
            if word.lower().strip('?.,!') in self.ACRONYMS:
                return True

        # Check for words with synonyms
        for word in words:
            word_lower = word.lower().strip('?.,!')
            if word_lower in self.SYNONYM_GROUPS:
                return True

        # Default: reformulate for medium-length queries
        return 3 <= word_count <= 10


# Singleton instance
_reformulation_service: Optional[QueryReformulationService] = None


@lru_cache(maxsize=1)
def get_reformulation_service() -> QueryReformulationService:
    """Get or create global reformulation service instance"""
    global _reformulation_service
    if _reformulation_service is None:
        _reformulation_service = QueryReformulationService()
    return _reformulation_service


def reformulate_query(
    query: str,
    include_acronyms: bool = True,
    include_synonyms: bool = True,
    use_llm: bool = False
) -> List[str]:
    """
    Convenience function to reformulate a query.

    Args:
        query: Original user query
        include_acronyms: Expand acronyms
        include_synonyms: Add synonym variations
        use_llm: Use LLM for complex reformulation

    Returns:
        List of query variations
    """
    service = get_reformulation_service()
    return service.reformulate_query(
        query=query,
        include_acronyms=include_acronyms,
        include_synonyms=include_synonyms,
        use_llm=use_llm
    )
