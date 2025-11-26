"""
Text Compression Utilities for Context Window Optimization

Provides efficient text compression methods to fit content within
limited context windows of smaller LLMs while preserving key information.

Usage:
    from app.utils.text_compression import compress_text, count_tokens

    compressed = compress_text(long_text, max_tokens=500, method="extractive")
"""

import re
import tiktoken
from typing import List, Dict, Tuple
from collections import Counter
import logging

logger = logging.getLogger(__name__)

# Initialize tokenizer (using GPT-4 tokenizer as reference)
try:
    TOKENIZER = tiktoken.encoding_for_model("gpt-4")
except Exception as e:
    logger.warning(f"Failed to load tiktoken, using fallback: {e}")
    TOKENIZER = None


def count_tokens(text: str) -> int:
    """
    Count tokens in text using tiktoken.

    Args:
        text: Input text

    Returns:
        Estimated token count
    """
    if TOKENIZER:
        return len(TOKENIZER.encode(text))
    else:
        # Fallback: rough estimate (1 token ≈ 4 characters)
        return len(text) // 4


def compress_text(
    text: str,
    max_tokens: int,
    method: str = "extractive",
    preserve_structure: bool = True
) -> str:
    """
    Compress text to fit within max_tokens.

    Args:
        text: Input text to compress
        max_tokens: Maximum number of tokens allowed
        method: Compression method ("truncate", "extractive", "smart")
        preserve_structure: Keep structure markers like bullet points

    Returns:
        Compressed text
    """
    current_tokens = count_tokens(text)

    # If already within limit, return as-is
    if current_tokens <= max_tokens:
        return text

    logger.info(f"Compressing text from {current_tokens} to {max_tokens} tokens using {method}")

    if method == "truncate":
        return truncate_text(text, max_tokens)
    elif method == "extractive":
        return extractive_summarization(text, max_tokens, preserve_structure)
    elif method == "smart":
        return smart_compression(text, max_tokens, preserve_structure)
    else:
        raise ValueError(f"Unknown compression method: {method}")


def truncate_text(text: str, max_tokens: int) -> str:
    """
    Simple truncation with word boundaries.

    Args:
        text: Input text
        max_tokens: Maximum tokens

    Returns:
        Truncated text
    """
    # Estimate character limit (1 token ≈ 4 chars)
    max_chars = max_tokens * 4

    if len(text) <= max_chars:
        return text

    # Truncate at word boundary
    truncated = text[:max_chars]
    last_space = truncated.rfind(' ')

    if last_space > 0:
        truncated = truncated[:last_space]

    return truncated + "..."


def extractive_summarization(
    text: str,
    max_tokens: int,
    preserve_structure: bool = True
) -> str:
    """
    Extract most important sentences to fit within token budget.

    Uses sentence scoring based on:
    - Keyword frequency
    - Position in text
    - Length (prefer medium-length sentences)

    Args:
        text: Input text
        max_tokens: Maximum tokens
        preserve_structure: Keep bullet points and formatting

    Returns:
        Extracted summary with top sentences
    """
    # Split into sentences
    sentences = split_into_sentences(text)

    if len(sentences) == 0:
        return truncate_text(text, max_tokens)

    # Score each sentence
    scored_sentences = score_sentences(sentences, text)

    # Select top sentences until token limit
    selected = []
    current_tokens = 0

    # Sort by score (descending) but maintain original order in output
    sorted_sentences = sorted(scored_sentences, key=lambda x: x[1], reverse=True)

    for sentence, score, original_idx in sorted_sentences:
        sentence_tokens = count_tokens(sentence)

        if current_tokens + sentence_tokens <= max_tokens:
            selected.append((sentence, original_idx))
            current_tokens += sentence_tokens

        if current_tokens >= max_tokens * 0.95:  # Stop at 95% to avoid overflow
            break

    # Sort by original order
    selected.sort(key=lambda x: x[1])

    # Reconstruct text
    result = ' '.join([s[0] for s in selected])

    logger.info(f"Selected {len(selected)}/{len(sentences)} sentences ({current_tokens} tokens)")

    return result


def smart_compression(
    text: str,
    max_tokens: int,
    preserve_structure: bool = True
) -> str:
    """
    Smart compression that preserves structure and key information.

    Strategy:
    1. Identify sections (headers, bullet points)
    2. Compress each section proportionally
    3. Keep critical sections intact

    Args:
        text: Input text
        max_tokens: Maximum tokens
        preserve_structure: Keep structure markers

    Returns:
        Compressed text with preserved structure
    """
    # Detect structure
    lines = text.split('\n')
    sections = []
    current_section = []
    section_type = "normal"

    for line in lines:
        stripped = line.strip()

        # Detect headers (lines with #, **, etc.)
        if stripped.startswith('#') or stripped.startswith('**'):
            if current_section:
                sections.append((section_type, '\n'.join(current_section)))
            section_type = "header"
            current_section = [line]
        # Detect bullet points
        elif stripped.startswith('-') or stripped.startswith('*') or stripped.startswith('•'):
            if section_type != "list":
                if current_section:
                    sections.append((section_type, '\n'.join(current_section)))
                section_type = "list"
                current_section = []
            current_section.append(line)
        else:
            if section_type == "list" and stripped:
                if current_section:
                    sections.append((section_type, '\n'.join(current_section)))
                section_type = "normal"
                current_section = []
            current_section.append(line)

    if current_section:
        sections.append((section_type, '\n'.join(current_section)))

    # Calculate compression ratio needed
    total_tokens = count_tokens(text)
    compression_ratio = max_tokens / total_tokens

    # Compress each section
    compressed_sections = []
    current_tokens = 0

    for section_type, section_text in sections:
        section_tokens = count_tokens(section_text)
        target_tokens = int(section_tokens * compression_ratio)

        if section_type == "header":
            # Keep headers intact (they're usually short)
            compressed_sections.append(section_text)
            current_tokens += section_tokens
        elif section_type == "list":
            # Compress lists by removing low-priority items
            compressed = compress_list(section_text, target_tokens)
            compressed_sections.append(compressed)
            current_tokens += count_tokens(compressed)
        else:
            # Compress normal text using extractive method
            compressed = extractive_summarization(section_text, target_tokens, False)
            compressed_sections.append(compressed)
            current_tokens += count_tokens(compressed)

        # Stop if we've reached the limit
        if current_tokens >= max_tokens:
            break

    result = '\n\n'.join(compressed_sections)

    logger.info(f"Smart compression: {total_tokens} → {current_tokens} tokens")

    return result


def compress_list(list_text: str, max_tokens: int) -> str:
    """
    Compress a bullet point list by keeping most important items.

    Args:
        list_text: Text containing bullet points
        max_tokens: Maximum tokens allowed

    Returns:
        Compressed list
    """
    lines = list_text.split('\n')
    items = []

    for line in lines:
        stripped = line.strip()
        if stripped and (stripped.startswith('-') or stripped.startswith('*') or stripped.startswith('•')):
            items.append(line)

    if not items:
        return list_text

    # Score items by length and keyword importance
    scored_items = []
    for item in items:
        # Prefer items with numbers, percentages, or keywords
        score = 0
        if re.search(r'\d+', item):
            score += 2
        if re.search(r'%', item):
            score += 1
        if any(kw in item.lower() for kw in ['critical', 'important', 'key', 'must', 'required']):
            score += 3

        # Penalize very long items
        tokens = count_tokens(item)
        if tokens > 50:
            score -= 1

        scored_items.append((item, score))

    # Sort by score
    scored_items.sort(key=lambda x: x[1], reverse=True)

    # Select items until token limit
    selected = []
    current_tokens = 0

    for item, score in scored_items:
        item_tokens = count_tokens(item)
        if current_tokens + item_tokens <= max_tokens:
            selected.append(item)
            current_tokens += item_tokens

    return '\n'.join(selected)


def split_into_sentences(text: str) -> List[str]:
    """
    Split text into sentences.

    Args:
        text: Input text

    Returns:
        List of sentences
    """
    # Simple sentence splitter (can be improved with nltk)
    # Split on . ! ? followed by space and capital letter
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
    return [s.strip() for s in sentences if s.strip()]


def score_sentences(
    sentences: List[str],
    full_text: str
) -> List[Tuple[str, float, int]]:
    """
    Score sentences by importance.

    Args:
        sentences: List of sentences
        full_text: Full text for context

    Returns:
        List of (sentence, score, original_index) tuples
    """
    # Extract keywords (words appearing multiple times)
    words = re.findall(r'\b\w+\b', full_text.lower())
    word_freq = Counter(words)

    # Remove common stop words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
    keywords = {word: freq for word, freq in word_freq.items()
                if freq > 1 and word not in stop_words and len(word) > 3}

    scored = []
    for idx, sentence in enumerate(sentences):
        score = 0.0
        sentence_lower = sentence.lower()

        # Keyword frequency score
        for keyword, freq in keywords.items():
            if keyword in sentence_lower:
                score += freq

        # Position score (earlier sentences are more important)
        position_score = 1.0 - (idx / len(sentences)) * 0.3
        score *= position_score

        # Length score (prefer medium-length sentences)
        length = len(sentence.split())
        if 10 <= length <= 30:
            score *= 1.2
        elif length < 5:
            score *= 0.5

        # Boost sentences with numbers or special markers
        if re.search(r'\d+', sentence):
            score *= 1.1
        if any(marker in sentence_lower for marker in ['important', 'critical', 'key', 'must', 'should']):
            score *= 1.3

        scored.append((sentence, score, idx))

    return scored


def compress_json_output(json_text: str, max_tokens: int) -> str:
    """
    Compress JSON-like output by removing unnecessary fields.

    Args:
        json_text: JSON or structured text
        max_tokens: Maximum tokens

    Returns:
        Compressed version
    """
    # For JSON, we can remove whitespace and compact formatting
    # This is a simple version - can be improved with actual JSON parsing

    # Remove extra whitespace
    compressed = re.sub(r'\s+', ' ', json_text)

    # If still too long, use extractive method
    if count_tokens(compressed) > max_tokens:
        return extractive_summarization(compressed, max_tokens, False)

    return compressed


def get_compression_stats(original: str, compressed: str) -> Dict[str, any]:
    """
    Get statistics about compression.

    Args:
        original: Original text
        compressed: Compressed text

    Returns:
        Dictionary with statistics
    """
    original_tokens = count_tokens(original)
    compressed_tokens = count_tokens(compressed)

    return {
        "original_tokens": original_tokens,
        "compressed_tokens": compressed_tokens,
        "reduction_tokens": original_tokens - compressed_tokens,
        "reduction_percentage": (1 - compressed_tokens / original_tokens) * 100 if original_tokens > 0 else 0,
        "original_chars": len(original),
        "compressed_chars": len(compressed)
    }
