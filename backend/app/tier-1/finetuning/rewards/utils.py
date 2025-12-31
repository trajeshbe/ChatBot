"""
Utility functions for reward calculation

Helper functions for:
- Extracting reasoning steps from text
- Parsing CoT format responses
- Normalizing text for comparison
"""

import re
from typing import List, Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


def extract_reasoning_steps(text: str) -> List[str]:
    """
    Extract reasoning steps from response text

    Supports multiple formats:
    - Numbered steps (1., 2., 3. or 1), 2), 3))
    - Bulleted steps (-, *, •)
    - Newline-separated paragraphs

    Args:
        text: Response text containing reasoning

    Returns:
        List of extracted reasoning steps
    """
    steps = []

    # Method 1: Try numbered steps (1., 2., 3.)
    numbered_pattern = r'^\s*(\d+)[\.\):](.+?)(?=^\s*\d+[\.\):]|\Z)'
    numbered_matches = re.findall(numbered_pattern, text, re.MULTILINE | re.DOTALL)

    if numbered_matches and len(numbered_matches) >= 2:
        steps = [match[1].strip() for match in numbered_matches]
        logger.debug(f"Extracted {len(steps)} numbered steps")
        return steps

    # Method 2: Try bulleted steps (-, *, •)
    bulleted_pattern = r'^\s*[-•*](.+?)(?=^\s*[-•*]|\Z)'
    bulleted_matches = re.findall(bulleted_pattern, text, re.MULTILINE | re.DOTALL)

    if bulleted_matches and len(bulleted_matches) >= 2:
        steps = [match.strip() for match in bulleted_matches]
        logger.debug(f"Extracted {len(steps)} bulleted steps")
        return steps

    # Method 3: Split by explicit step markers
    step_markers = [
        r'Step \d+:',
        r'First,',
        r'Second,',
        r'Third,',
        r'Next,',
        r'Then,',
        r'Finally,'
    ]

    for marker in step_markers:
        parts = re.split(marker, text, flags=re.IGNORECASE)
        if len(parts) > 2:  # Found multiple steps
            # Remove empty first part if marker started the text
            steps = [p.strip() for p in parts if p.strip()]
            logger.debug(f"Extracted {len(steps)} steps using marker '{marker}'")
            return steps

    # Method 4: Fallback - split by sentences/paragraphs
    # Split by double newline (paragraphs)
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]

    if len(paragraphs) >= 2:
        # Filter out very short paragraphs (likely not steps)
        steps = [p for p in paragraphs if len(p.split()) >= 5]
        logger.debug(f"Extracted {len(steps)} paragraph-based steps")
        return steps

    # Method 5: Split by single newline if no paragraphs
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    steps = [line for line in lines if len(line.split()) >= 5]

    logger.debug(f"Extracted {len(steps)} line-based steps (fallback)")
    return steps


def parse_cot_response(response: str) -> Dict[str, Any]:
    """
    Parse Chain-of-Thought formatted response

    Expected formats:
    1. Explicit sections:
       Reasoning: <steps>
       Answer: <answer>

    2. Implicit format:
       <reasoning steps>
       Therefore, <answer>

    Args:
        response: Response text in CoT format

    Returns:
        Dict with keys: reasoning_steps, answer, raw_reasoning
    """
    result = {
        "reasoning_steps": [],
        "answer": "",
        "raw_reasoning": ""
    }

    # Method 1: Try explicit sections
    reasoning_match = re.search(
        r'(?:Reasoning|Steps|Solution):\s*(.+?)(?=Answer:|$)',
        response,
        re.IGNORECASE | re.DOTALL
    )
    answer_match = re.search(
        r'(?:Answer|Result|Solution):\s*(.+?)$',
        response,
        re.IGNORECASE | re.DOTALL
    )

    if reasoning_match and answer_match:
        raw_reasoning = reasoning_match.group(1).strip()
        result["raw_reasoning"] = raw_reasoning
        result["reasoning_steps"] = extract_reasoning_steps(raw_reasoning)
        result["answer"] = answer_match.group(1).strip()
        logger.debug("Parsed CoT with explicit sections")
        return result

    # Method 2: Try implicit format (conclusion markers)
    conclusion_markers = [
        r'(?:Therefore|Thus|Hence|So),?\s+(.+?)$',
        r'(?:The answer is|Answer:)\s+(.+?)$',
        r'(?:We conclude|In conclusion),?\s+(.+?)$'
    ]

    for marker_pattern in conclusion_markers:
        match = re.search(marker_pattern, response, re.IGNORECASE | re.MULTILINE)
        if match:
            # Everything before marker is reasoning
            marker_pos = match.start()
            raw_reasoning = response[:marker_pos].strip()
            answer = match.group(1).strip()

            result["raw_reasoning"] = raw_reasoning
            result["reasoning_steps"] = extract_reasoning_steps(raw_reasoning)
            result["answer"] = answer
            logger.debug(f"Parsed CoT with conclusion marker: {marker_pattern}")
            return result

    # Method 3: Fallback - last sentence is answer, rest is reasoning
    sentences = [s.strip() for s in re.split(r'[.!?]', response) if s.strip()]

    if len(sentences) >= 2:
        answer = sentences[-1]
        raw_reasoning = '. '.join(sentences[:-1]) + '.'

        result["raw_reasoning"] = raw_reasoning
        result["reasoning_steps"] = extract_reasoning_steps(raw_reasoning)
        result["answer"] = answer
        logger.debug("Parsed CoT with fallback (last sentence as answer)")
        return result

    # Failed to parse - return full response as reasoning
    result["raw_reasoning"] = response
    result["reasoning_steps"] = extract_reasoning_steps(response)
    result["answer"] = ""
    logger.warning("Could not parse CoT format, treating full response as reasoning")

    return result


def normalize_answer(answer: str) -> str:
    """
    Normalize answer text for comparison

    - Remove extra whitespace
    - Remove punctuation
    - Lowercase
    - Remove common filler words

    Args:
        answer: Answer text to normalize

    Returns:
        Normalized answer string
    """
    # Remove extra whitespace
    normalized = ' '.join(answer.split())

    # Remove punctuation except math symbols
    normalized = re.sub(r'[^\w\s=+\-*/√²³π]', '', normalized)

    # Lowercase
    normalized = normalized.lower()

    # Remove common filler words
    filler_words = ['the', 'a', 'an', 'is', 'are', 'was', 'were']
    words = normalized.split()
    words = [w for w in words if w not in filler_words]

    return ' '.join(words)


def extract_mathematical_expressions(text: str) -> List[str]:
    """
    Extract mathematical expressions from text

    Args:
        text: Text containing math expressions

    Returns:
        List of mathematical expressions (equations, formulas)
    """
    expressions = []

    # Pattern 1: Equations (something = something)
    equations = re.findall(r'[^=\n]+=[^=\n]+', text)
    expressions.extend(equations)

    # Pattern 2: LaTeX-style math ($...$)
    latex_inline = re.findall(r'\$(.+?)\$', text)
    expressions.extend(latex_inline)

    # Pattern 3: LaTeX display mode ($$...$$)
    latex_display = re.findall(r'\$\$(.+?)\$\$', text, re.DOTALL)
    expressions.extend(latex_display)

    # Pattern 4: Common math functions
    math_functions = re.findall(
        r'(?:sin|cos|tan|log|ln|sqrt|exp|abs)\s*\([^)]+\)',
        text,
        re.IGNORECASE
    )
    expressions.extend(math_functions)

    return [expr.strip() for expr in expressions if expr.strip()]


def count_logical_connectors(text: str) -> int:
    """
    Count logical connectors in text

    Args:
        text: Text to analyze

    Returns:
        Count of logical connectors
    """
    connectors = [
        "therefore", "thus", "hence", "consequently",
        "because", "since", "as", "given that",
        "this means", "which implies", "leads to",
        "if", "then", "so", "however", "but",
        "moreover", "furthermore", "additionally"
    ]

    text_lower = text.lower()
    count = sum(1 for connector in connectors if connector in text_lower)

    return count


def split_into_sentences(text: str) -> List[str]:
    """
    Split text into sentences

    Args:
        text: Text to split

    Returns:
        List of sentences
    """
    # Split by sentence-ending punctuation
    sentences = re.split(r'[.!?]+', text)

    # Clean and filter
    sentences = [s.strip() for s in sentences if s.strip()]

    return sentences


def calculate_text_similarity(text1: str, text2: str) -> float:
    """
    Calculate similarity between two texts using character-level ratio

    Args:
        text1: First text
        text2: Second text

    Returns:
        Similarity score (0.0 to 1.0)
    """
    from difflib import SequenceMatcher

    # Normalize both texts
    norm1 = normalize_answer(text1)
    norm2 = normalize_answer(text2)

    # Calculate similarity
    similarity = SequenceMatcher(None, norm1, norm2).ratio()

    return similarity


def validate_reasoning_format(
    response: str,
    require_steps: bool = True,
    require_answer: bool = True,
    min_steps: int = 2
) -> Tuple[bool, str]:
    """
    Validate that response follows proper reasoning format

    Args:
        response: Response to validate
        require_steps: Whether reasoning steps are required
        require_answer: Whether explicit answer is required
        min_steps: Minimum number of reasoning steps

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Parse the response
    parsed = parse_cot_response(response)

    # Check reasoning steps
    if require_steps:
        if not parsed["reasoning_steps"]:
            return False, "No reasoning steps found"

        if len(parsed["reasoning_steps"]) < min_steps:
            return False, f"Insufficient reasoning steps (found {len(parsed['reasoning_steps'])}, need {min_steps})"

    # Check answer
    if require_answer:
        if not parsed["answer"]:
            return False, "No explicit answer found"

    return True, ""


def format_reasoning_dataset_entry(
    prompt: str,
    reasoning_steps: List[str],
    answer: str,
    ground_truth: Optional[str] = None
) -> Dict[str, Any]:
    """
    Format a reasoning dataset entry for GRPO training

    Args:
        prompt: Input question/prompt
        reasoning_steps: List of reasoning steps
        answer: Final answer
        ground_truth: Optional correct answer for validation

    Returns:
        Formatted dataset entry dict
    """
    # Format reasoning as text
    reasoning_text = ""
    for i, step in enumerate(reasoning_steps, 1):
        reasoning_text += f"{i}. {step}\n"

    # Create full response
    full_response = f"Let me solve this step by step:\n\n{reasoning_text}\nTherefore, {answer}"

    entry = {
        "prompt": prompt,
        "reasoning": reasoning_steps,
        "answer": answer,
        "full_response": full_response
    }

    if ground_truth:
        entry["ground_truth"] = ground_truth

    return entry


def convert_sft_to_reasoning_format(
    sft_example: Dict[str, str],
    use_llm: bool = False,
    llm_model: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Convert SFT dataset entry to reasoning format

    Args:
        sft_example: SFT entry with 'input' and 'output' keys
        use_llm: Whether to use LLM to generate reasoning steps
        llm_model: LLM model instance (if use_llm=True)

    Returns:
        Reasoning format entry
    """
    prompt = sft_example.get("input", sft_example.get("prompt", ""))
    output = sft_example.get("output", sft_example.get("response", ""))

    if use_llm and llm_model:
        # Use LLM to generate reasoning steps
        # (Implementation would call LLM with specific prompt)
        logger.warning("LLM-based reasoning generation not yet implemented, using fallback")

    # Fallback: Parse existing output for reasoning steps
    parsed = parse_cot_response(output)

    if parsed["reasoning_steps"]:
        # Already has reasoning
        return format_reasoning_dataset_entry(
            prompt=prompt,
            reasoning_steps=parsed["reasoning_steps"],
            answer=parsed["answer"] or output
        )
    else:
        # No reasoning found - create simple step
        return format_reasoning_dataset_entry(
            prompt=prompt,
            reasoning_steps=[f"Based on the question, {output}"],
            answer=output
        )
