"""
Translation Service - Multi-backend with Intelligent Routing

Provides translation capabilities using multiple backends:
1. LLM (GPT-4/Claude) - High quality, contextual translation
2. Transformers (Helsinki-NLP) - Cost-effective bulk translation

Intelligent Routing:
- Text < 500 chars → LLM (accurate)
- Text >= 500 chars → Transformers (cost-effective)
- User specifies "high_quality" → LLM
- User specifies "standard" → Transformers
"""

import logging
from typing import Dict, Any, Optional, List
import asyncio

# LLM service imports
from app.services.llm_service import LLMService

# Transformers imports (Helsinki-NLP models)
try:
    from transformers import MarianMTModel, MarianTokenizer
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("Transformers not available - will use LLM only for translation")

logger = logging.getLogger(__name__)


class TranslationService:
    """
    Multi-backend translation service with intelligent routing.

    Features:
    - LLM backend (OpenAI, Anthropic) for high-quality translation
    - Transformers backend (Helsinki-NLP) for cost-effective bulk translation
    - Automatic backend selection based on text length and quality requirements
    - Language detection
    - Confidence scoring
    """

    # Character threshold for routing decision
    LLM_THRESHOLD_CHARS = 500

    # Supported language codes (ISO 639-1)
    SUPPORTED_LANGUAGES = {
        "en": "English",
        "es": "Spanish",
        "fr": "French",
        "de": "German",
        "it": "Italian",
        "pt": "Portuguese",
        "ru": "Russian",
        "ja": "Japanese",
        "ko": "Korean",
        "zh": "Chinese",
        "ar": "Arabic",
        "hi": "Hindi",
        "nl": "Dutch",
        "pl": "Polish",
        "tr": "Turkish",
        "sv": "Swedish",
        "fi": "Finnish",
        "da": "Danish",
        "no": "Norwegian",
        "cs": "Czech",
        "ro": "Romanian",
        "hu": "Hungarian",
        "el": "Greek",
        "th": "Thai",
        "vi": "Vietnamese",
        "id": "Indonesian"
    }

    def __init__(self, llm_service: Optional[LLMService] = None):
        """
        Initialize translation service.

        Args:
            llm_service: Optional LLMService instance for LLM backend
        """
        self.llm_service = llm_service
        self.transformers_available = TRANSFORMERS_AVAILABLE

        # Cache for transformer models
        self._model_cache = {}

        logger.info(
            f"Translation service initialized - "
            f"LLM: {self.llm_service is not None}, "
            f"Transformers: {self.transformers_available}"
        )

    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        quality: str = "auto",
        backend: str = "auto",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Translate text with intelligent backend selection.

        Args:
            text: Text to translate
            source_lang: Source language code (e.g., "en", "es", "fr")
            target_lang: Target language code
            quality: Translation quality ("auto", "high", "standard")
            backend: Backend to use ("auto", "llm", "transformers")
            **kwargs: Additional backend-specific options

        Returns:
            {
                "translated_text": str,
                "source_lang": str,
                "target_lang": str,
                "backend_used": str,
                "confidence": float,
                "metadata": dict
            }

        Raises:
            ValueError: If languages are invalid or no backend available
            RuntimeError: If translation fails
        """
        # Validate languages
        if source_lang not in self.SUPPORTED_LANGUAGES:
            raise ValueError(f"Unsupported source language: {source_lang}")
        if target_lang not in self.SUPPORTED_LANGUAGES:
            raise ValueError(f"Unsupported target language: {target_lang}")

        # Same language - no translation needed
        if source_lang == target_lang:
            return {
                "translated_text": text,
                "source_lang": source_lang,
                "target_lang": target_lang,
                "backend_used": "none",
                "confidence": 1.0,
                "metadata": {"reason": "Same language - no translation needed"}
            }

        logger.info(
            f"Translation request: {source_lang} → {target_lang}, "
            f"length={len(text)}, quality={quality}, backend={backend}"
        )

        # Determine backend
        if backend == "auto":
            backend = self._select_backend(text, quality)
        elif backend not in ["llm", "transformers"]:
            raise ValueError(f"Invalid backend: {backend}. Must be 'auto', 'llm', or 'transformers'")

        # Validate backend availability
        if backend == "llm" and self.llm_service is None:
            raise ValueError("LLM backend requested but LLM service not available")
        if backend == "transformers" and not self.transformers_available:
            raise ValueError("Transformers backend requested but not available")

        # Translate with selected backend
        try:
            if backend == "llm":
                result = await self._translate_with_llm(text, source_lang, target_lang, **kwargs)
            else:
                result = await self._translate_with_transformers(text, source_lang, target_lang, **kwargs)

            logger.info(f"Translation completed with {backend}: {len(result['translated_text'])} chars")
            return result

        except Exception as e:
            logger.error(f"Translation with {backend} failed: {e}")

            # Try fallback
            fallback_backend = "transformers" if backend == "llm" else "llm"

            if fallback_backend == "llm" and self.llm_service is not None:
                logger.info(f"Trying fallback: {fallback_backend}")
                try:
                    result = await self._translate_with_llm(text, source_lang, target_lang, **kwargs)
                    result["backend_used"] = f"{backend} (failed) → {fallback_backend} (fallback)"
                    return result
                except Exception as e2:
                    logger.error(f"Fallback also failed: {e2}")

            elif fallback_backend == "transformers" and self.transformers_available:
                logger.info(f"Trying fallback: {fallback_backend}")
                try:
                    result = await self._translate_with_transformers(text, source_lang, target_lang, **kwargs)
                    result["backend_used"] = f"{backend} (failed) → {fallback_backend} (fallback)"
                    return result
                except Exception as e2:
                    logger.error(f"Fallback also failed: {e2}")

            # Both failed
            raise RuntimeError(f"Translation failed with all backends: {str(e)}")

    def _select_backend(self, text: str, quality: str) -> str:
        """
        Select optimal backend based on text characteristics and quality requirement.

        Args:
            text: Text to translate
            quality: Quality requirement ("auto", "high", "standard")

        Returns:
            Backend name ("llm" or "transformers")
        """
        # Quality-based selection
        if quality == "high":
            return "llm" if self.llm_service else "transformers"
        elif quality == "standard":
            return "transformers" if self.transformers_available else "llm"

        # Auto selection based on text length
        text_length = len(text)

        # Short text → LLM (better for context and nuance)
        if text_length < self.LLM_THRESHOLD_CHARS:
            return "llm" if self.llm_service else "transformers"

        # Long text → Transformers (more cost-effective)
        return "transformers" if self.transformers_available else "llm"

    async def _translate_with_llm(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Translate using LLM backend (OpenAI/Anthropic).

        Args:
            text: Text to translate
            source_lang: Source language code
            target_lang: Target language code
            **kwargs: Additional LLM options

        Returns:
            Translation result dictionary
        """
        if self.llm_service is None:
            raise RuntimeError("LLM service not available")

        logger.info(f"Translating with LLM: {source_lang} → {target_lang}")

        # Get language names
        source_lang_name = self.SUPPORTED_LANGUAGES[source_lang]
        target_lang_name = self.SUPPORTED_LANGUAGES[target_lang]

        # Build translation prompt
        prompt = f"""Translate the following text from {source_lang_name} to {target_lang_name}.

Preserve:
- Original meaning and context
- Tone and style
- Special terms and proper nouns
- Formatting (if any)

Text to translate:
{text}

Translation:"""

        # Call LLM
        response = await self.llm_service.generate_response(
            prompt=prompt,
            model_id=kwargs.get("model_id", "gpt-4-turbo"),
            temperature=kwargs.get("temperature", 0.3),  # Low temperature for consistency
            max_tokens=kwargs.get("max_tokens", len(text) * 2)  # Estimate
        )

        translated_text = response.get("response", "").strip()

        # Calculate confidence (heuristic based on length ratio)
        length_ratio = len(translated_text) / len(text) if len(text) > 0 else 0.0
        confidence = min(1.0, 0.5 + (0.5 * (1.0 - abs(1.0 - length_ratio))))

        return {
            "translated_text": translated_text,
            "source_lang": source_lang,
            "target_lang": target_lang,
            "backend_used": "llm",
            "confidence": confidence,
            "metadata": {
                "model": response.get("model", "unknown"),
                "tokens_used": response.get("tokens", 0),
                "source_length": len(text),
                "target_length": len(translated_text),
                "length_ratio": length_ratio
            }
        }

    async def _translate_with_transformers(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Translate using Transformers backend (Helsinki-NLP).

        Args:
            text: Text to translate
            source_lang: Source language code
            target_lang: Target language code
            **kwargs: Additional transformer options

        Returns:
            Translation result dictionary
        """
        if not self.transformers_available:
            raise RuntimeError("Transformers not available")

        logger.info(f"Translating with Transformers: {source_lang} → {target_lang}")

        # Get model name
        model_name = self._get_helsinki_model_name(source_lang, target_lang)

        # Load or get cached model
        model, tokenizer = await self._load_model(model_name)

        # Tokenize
        inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)

        # Translate
        with torch.no_grad():
            outputs = model.generate(**inputs)

        # Decode
        translated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Calculate confidence (transformers don't provide this directly, use heuristic)
        length_ratio = len(translated_text) / len(text) if len(text) > 0 else 0.0
        confidence = min(1.0, 0.4 + (0.4 * (1.0 - abs(1.0 - length_ratio))))

        return {
            "translated_text": translated_text,
            "source_lang": source_lang,
            "target_lang": target_lang,
            "backend_used": "transformers",
            "confidence": confidence,
            "metadata": {
                "model": model_name,
                "source_length": len(text),
                "target_length": len(translated_text),
                "length_ratio": length_ratio
            }
        }

    def _get_helsinki_model_name(self, source_lang: str, target_lang: str) -> str:
        """
        Get Helsinki-NLP model name for language pair.

        Args:
            source_lang: Source language code
            target_lang: Target language code

        Returns:
            Model name (e.g., "Helsinki-NLP/opus-mt-en-es")
        """
        return f"Helsinki-NLP/opus-mt-{source_lang}-{target_lang}"

    async def _load_model(self, model_name: str) -> tuple:
        """
        Load or get cached transformer model.

        Args:
            model_name: Model name to load

        Returns:
            Tuple of (model, tokenizer)
        """
        # Check cache
        if model_name in self._model_cache:
            logger.debug(f"Using cached model: {model_name}")
            return self._model_cache[model_name]

        # Load model (run in executor to avoid blocking)
        logger.info(f"Loading transformer model: {model_name}")

        def load_sync():
            tokenizer = MarianTokenizer.from_pretrained(model_name)
            model = MarianMTModel.from_pretrained(model_name)
            return model, tokenizer

        # Run in executor
        loop = asyncio.get_event_loop()
        model, tokenizer = await loop.run_in_executor(None, load_sync)

        # Cache
        self._model_cache[model_name] = (model, tokenizer)

        logger.info(f"Model loaded and cached: {model_name}")

        return model, tokenizer

    def get_supported_languages(self) -> List[Dict[str, str]]:
        """
        Get list of supported languages.

        Returns:
            List of language dictionaries with code and name
        """
        return [
            {"code": code, "name": name}
            for code, name in sorted(self.SUPPORTED_LANGUAGES.items(), key=lambda x: x[1])
        ]

    def get_available_backends(self) -> List[str]:
        """
        Get list of available backends.

        Returns:
            List of backend names
        """
        backends = []
        if self.llm_service is not None:
            backends.append("llm")
        if self.transformers_available:
            backends.append("transformers")
        return backends

    def get_status(self) -> Dict[str, Any]:
        """
        Get translation service status.

        Returns:
            Status dictionary
        """
        return {
            "service": "translation",
            "backends": {
                "llm": {
                    "available": self.llm_service is not None,
                    "description": "High-quality contextual translation",
                    "cost": "~$0.01 per 1K chars"
                },
                "transformers": {
                    "available": self.transformers_available,
                    "description": "Cost-effective bulk translation",
                    "cost": "Free (offline)"
                }
            },
            "supported_languages": len(self.SUPPORTED_LANGUAGES),
            "routing_threshold": self.LLM_THRESHOLD_CHARS,
            "ready": (self.llm_service is not None) or self.transformers_available
        }
