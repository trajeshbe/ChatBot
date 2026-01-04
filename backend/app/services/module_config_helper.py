"""
Module Configuration Helper

Provides convenience functions for loading module configurations in route handlers.
Auto-loads saved configurations from POCConfigManager for LLM calls.
"""

from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.poc_config_service import poc_config_service


async def load_module_config(
    db: AsyncSession,
    module_name: str,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Load module configuration with 3-level resolution:
    1. Global defaults
    2. Module-specific config (from POCConfigManager)
    3. User-specific overrides (if user_id provided)

    Args:
        db: Database session
        module_name: Module identifier (e.g., 'sentiment_social', 'customer_churn')
        user_id: Optional user ID for user-specific overrides

    Returns:
        Merged configuration dictionary

    Example:
        ```python
        config = await load_module_config(db, "sentiment_social")

        # Access LLM settings
        model = config['llm']['default']['model']  # e.g., 'gpt-4o-mini'
        temperature = config['llm']['default']['temperature']  # e.g., 0.2

        # Access prompts
        system_prompt = config['prompts']['system']['default']

        # Access retrieval settings
        top_k = config['retrieval']['top_k']  # e.g., 10
        ```
    """
    return await poc_config_service.get_config(
        db=db,
        module_name=module_name,
        user_id=user_id,
        include_overrides=True
    )


def extract_llm_params(config: Dict[str, Any], llm_key: str = 'default') -> Dict[str, Any]:
    """
    Extract LLM parameters from module config for easy use in LLM calls.

    Args:
        config: Module configuration dictionary
        llm_key: LLM configuration key ('default', 'primary', 'secondary', etc.)

    Returns:
        Dictionary with LLM parameters ready for OpenAI/Anthropic API calls

    Example:
        ```python
        config = await load_module_config(db, "sentiment_social")
        llm_params = extract_llm_params(config)

        response = await openai_client.chat.completions.create(
            **llm_params,
            messages=[...]
        )
        ```
    """
    llm_config = config.get('llm', {}).get(llm_key, {})

    return {
        'model': llm_config.get('model', 'gpt-4o-mini'),
        'temperature': llm_config.get('temperature', 0.2),
        'max_tokens': llm_config.get('max_tokens', 1000),
        'top_p': llm_config.get('top_p', 1.0),
        'frequency_penalty': llm_config.get('frequency_penalty', 0.0),
        'presence_penalty': llm_config.get('presence_penalty', 0.0)
    }


def get_system_prompt(config: Dict[str, Any], prompt_key: str = 'default') -> str:
    """
    Extract system prompt from module config.

    Args:
        config: Module configuration dictionary
        prompt_key: Prompt configuration key ('default', 'analysis', 'extraction', etc.)

    Returns:
        System prompt string
    """
    return config.get('prompts', {}).get('system', {}).get(
        prompt_key,
        "You are a helpful AI assistant."
    )


def get_retrieval_params(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract retrieval parameters from module config.

    Args:
        config: Module configuration dictionary

    Returns:
        Dictionary with retrieval parameters (top_k, rerank_top_k, etc.)
    """
    retrieval = config.get('retrieval', {})

    return {
        'top_k': retrieval.get('top_k', 10),
        'rerank_top_k': retrieval.get('rerank_top_k', 5),
        'min_score': retrieval.get('min_score', 0.0)
    }
