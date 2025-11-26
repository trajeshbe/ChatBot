"""
Text Compression Tool for Small LLM Calls

A reusable tool that automatically compresses text inputs for small LLMs
to fit within their context window constraints.

This tool can be registered in the tool registry and used by any agent
or service that needs to call small LLMs.

Usage:
    from app.tools.text_compression_tool import compress_for_llm, get_text_compression_tool

    # Direct usage
    compressed_text = compress_for_llm(
        text="Very long text...",
        model_name="llama3.2-vision:11b",
        target_tokens=500
    )

    # As a tool for agent use
    tool_definition = get_text_compression_tool()
"""

import logging
from typing import Dict, Any, Optional
from app.utils.text_compression import compress_text, count_tokens
from app.agents.project_estimator.prompt_templates import PromptTemplates

logger = logging.getLogger(__name__)


def compress_for_llm(
    text: str,
    model_name: str,
    target_tokens: Optional[int] = None,
    compression_method: str = "smart",
    preserve_structure: bool = True
) -> str:
    """
    Compress text to fit within model's context window.

    Args:
        text: Input text to compress
        model_name: Name of the target LLM model
        target_tokens: Target token count (optional, auto-calculated if not provided)
        compression_method: Compression method ("truncate", "extractive", "smart")
        preserve_structure: Whether to preserve structure markers

    Returns:
        Compressed text that fits within model's context window
    """
    # Get model's context window size
    context_window = PromptTemplates.get_model_context_window(model_name)

    # Determine if compression is needed
    current_tokens = count_tokens(text)

    # Small models need aggressive compression
    # Reserve 70% of context for input, 30% for output
    max_input_tokens = int(context_window * 0.7)

    # Use target_tokens if provided, otherwise use calculated max
    target = target_tokens if target_tokens else max_input_tokens

    logger.info(f"🔧 Text Compression Tool:")
    logger.info(f"   Model: {model_name}")
    logger.info(f"   Context window: {context_window} tokens")
    logger.info(f"   Current text: {current_tokens} tokens")
    logger.info(f"   Target: {target} tokens")

    # Check if compression is needed
    if current_tokens <= target:
        logger.info(f"   ✅ No compression needed (fits within budget)")
        return text

    # Compress text
    logger.info(f"   🗜️  Compressing using '{compression_method}' method...")

    compressed = compress_text(
        text=text,
        max_tokens=target,
        method=compression_method,
        preserve_structure=preserve_structure
    )

    compressed_tokens = count_tokens(compressed)
    reduction_pct = (1 - compressed_tokens / current_tokens) * 100

    logger.info(f"   ✅ Compressed: {compressed_tokens} tokens ({reduction_pct:.1f}% reduction)")

    return compressed


def compress_conversation_history(
    messages: list,
    model_name: str,
    target_tokens: Optional[int] = None
) -> list:
    """
    Compress conversation history to fit within model's context window.

    Keeps recent messages intact and compresses older messages.

    Args:
        messages: List of conversation messages
        model_name: Name of the target LLM model
        target_tokens: Target token count (optional)

    Returns:
        Compressed message list
    """
    context_window = PromptTemplates.get_model_context_window(model_name)
    max_input_tokens = int(context_window * 0.6)  # Reserve 40% for output
    target = target_tokens if target_tokens else max_input_tokens

    # Calculate current token count
    current_tokens = sum(count_tokens(msg.get("content", "")) for msg in messages)

    logger.info(f"🔧 Conversation History Compression:")
    logger.info(f"   Model: {model_name}")
    logger.info(f"   Messages: {len(messages)}")
    logger.info(f"   Current tokens: {current_tokens}")
    logger.info(f"   Target tokens: {target}")

    if current_tokens <= target:
        logger.info(f"   ✅ No compression needed")
        return messages

    # Strategy: Keep system message, recent user/assistant messages, compress older ones
    if len(messages) == 0:
        return messages

    compressed_messages = []

    # Always keep system message (first message) if it exists
    if messages[0].get("role") == "system":
        compressed_messages.append(messages[0])
        remaining_messages = messages[1:]
    else:
        remaining_messages = messages

    # Keep last N messages intact (most recent context)
    recent_count = min(3, len(remaining_messages))  # Keep last 3 messages
    recent_messages = remaining_messages[-recent_count:] if remaining_messages else []
    older_messages = remaining_messages[:-recent_count] if len(remaining_messages) > recent_count else []

    # Compress older messages
    if older_messages:
        # Combine older messages into summary
        combined_text = "\n\n".join([
            f"{msg.get('role', 'user')}: {msg.get('content', '')}"
            for msg in older_messages
        ])

        # Compress combined text
        summary_tokens = target - sum(count_tokens(m.get("content", "")) for m in recent_messages) - 100
        summary_tokens = max(200, summary_tokens)  # At least 200 tokens for summary

        compressed_summary = compress_text(
            combined_text,
            max_tokens=summary_tokens,
            method="extractive",
            preserve_structure=False
        )

        # Add as system message
        compressed_messages.append({
            "role": "system",
            "content": f"[Previous conversation summary]\n{compressed_summary}"
        })

    # Add recent messages
    compressed_messages.extend(recent_messages)

    final_tokens = sum(count_tokens(msg.get("content", "")) for msg in compressed_messages)
    reduction_pct = (1 - final_tokens / current_tokens) * 100 if current_tokens > 0 else 0

    logger.info(f"   ✅ Compressed to {len(compressed_messages)} messages, {final_tokens} tokens")
    logger.info(f"   Reduction: {reduction_pct:.1f}%")

    return compressed_messages


def get_text_compression_tool() -> Dict[str, Any]:
    """
    Get tool definition for text compression tool.

    This can be registered in the tool registry for agent use.

    Returns:
        Tool definition dictionary compatible with LLM function calling
    """
    return {
        "type": "function",
        "function": {
            "name": "compress_text_for_llm",
            "description": (
                "Compress text to fit within a small LLM's context window. "
                "Automatically detects model's context window size and applies "
                "intelligent compression while preserving key information. "
                "Use this before calling small LLMs (LLaMA, Qwen, Mistral) with large inputs."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The text to compress"
                    },
                    "model_name": {
                        "type": "string",
                        "description": "Name of the target LLM model (e.g., 'llama3.2-vision:11b')"
                    },
                    "target_tokens": {
                        "type": "integer",
                        "description": "Optional target token count. If not provided, automatically calculated based on model's context window"
                    },
                    "compression_method": {
                        "type": "string",
                        "enum": ["truncate", "extractive", "smart"],
                        "description": "Compression method to use. 'smart' is recommended for preserving structure"
                    }
                },
                "required": ["text", "model_name"]
            }
        }
    }


async def execute_text_compression_tool(
    text: str,
    model_name: str,
    target_tokens: Optional[int] = None,
    compression_method: str = "smart"
) -> Dict[str, Any]:
    """
    Execute text compression tool (for agent function calling).

    Args:
        text: Text to compress
        model_name: Target model name
        target_tokens: Optional target token count
        compression_method: Compression method

    Returns:
        Result dictionary with compressed text and metadata
    """
    try:
        original_tokens = count_tokens(text)

        compressed_text = compress_for_llm(
            text=text,
            model_name=model_name,
            target_tokens=target_tokens,
            compression_method=compression_method
        )

        compressed_tokens = count_tokens(compressed_text)

        return {
            "success": True,
            "compressed_text": compressed_text,
            "original_tokens": original_tokens,
            "compressed_tokens": compressed_tokens,
            "reduction_percentage": (1 - compressed_tokens / original_tokens) * 100 if original_tokens > 0 else 0,
            "model_name": model_name,
            "method": compression_method
        }

    except Exception as e:
        logger.error(f"Text compression tool failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "compressed_text": text  # Return original text on failure
        }


# Example usage decorator for automatic compression
def auto_compress_for_small_llm(model_field: str = "model"):
    """
    Decorator that automatically compresses inputs for small LLMs.

    Args:
        model_field: Name of the field containing model name

    Usage:
        @auto_compress_for_small_llm(model_field="model_name")
        async def call_llm(text: str, model_name: str):
            # text will be automatically compressed if model is small
            return await llm_service.call(text, model_name)
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Get model name from kwargs
            model_name = kwargs.get(model_field)

            if not model_name:
                # Try to get from args (assume model is second arg)
                if len(args) > 1:
                    model_name = args[1]

            if model_name:
                # Check if this is a small model
                context_window = PromptTemplates.get_model_context_window(model_name)

                if context_window < 16000:  # Small LLM
                    logger.info(f"🔧 Auto-compressing input for small LLM: {model_name}")

                    # Find text parameter (assume first string arg or 'text'/'prompt' kwarg)
                    text_param = None
                    text_key = None

                    for key in ['text', 'prompt', 'content', 'input']:
                        if key in kwargs and isinstance(kwargs[key], str):
                            text_param = kwargs[key]
                            text_key = key
                            break

                    if not text_param and args and isinstance(args[0], str):
                        text_param = args[0]
                        text_key = 0

                    if text_param:
                        # Compress text
                        compressed = compress_for_llm(
                            text=text_param,
                            model_name=model_name,
                            compression_method="smart"
                        )

                        # Replace in kwargs or args
                        if isinstance(text_key, str):
                            kwargs[text_key] = compressed
                        elif isinstance(text_key, int):
                            args = list(args)
                            args[text_key] = compressed
                            args = tuple(args)

            # Call original function
            return await func(*args, **kwargs)

        return wrapper
    return decorator


# Utility function for quick compression check
def should_compress(text: str, model_name: str) -> bool:
    """
    Check if text should be compressed for the given model.

    Args:
        text: Input text
        model_name: Target model name

    Returns:
        True if compression is recommended
    """
    context_window = PromptTemplates.get_model_context_window(model_name)
    current_tokens = count_tokens(text)
    max_input_tokens = int(context_window * 0.7)

    return current_tokens > max_input_tokens


# Batch compression for multiple inputs
def compress_batch(
    texts: list,
    model_name: str,
    target_tokens_per_text: Optional[int] = None
) -> list:
    """
    Compress multiple texts in batch.

    Args:
        texts: List of texts to compress
        model_name: Target model name
        target_tokens_per_text: Target tokens per text (optional)

    Returns:
        List of compressed texts
    """
    logger.info(f"🔧 Batch compression for {len(texts)} texts")

    compressed_texts = []

    for i, text in enumerate(texts):
        try:
            compressed = compress_for_llm(
                text=text,
                model_name=model_name,
                target_tokens=target_tokens_per_text,
                compression_method="smart"
            )
            compressed_texts.append(compressed)
        except Exception as e:
            logger.error(f"Failed to compress text {i}: {e}")
            compressed_texts.append(text)  # Use original on failure

    logger.info(f"✅ Batch compression complete")

    return compressed_texts
