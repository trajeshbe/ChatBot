"""
Vision Processing Service using LLaVA via Ollama

This service provides image understanding capabilities using vision-language models.
It's superior to traditional OCR for:
- Handwritten text
- Complex layouts
- Low-quality images
- Understanding context and meaning
"""

import logging
import base64
from typing import Dict, Any, Optional
from pathlib import Path
import httpx
from app.services.gpu_resource_manager import get_gpu_manager

logger = logging.getLogger(__name__)


class VisionService:
    """Service for processing images with vision-language models"""

    def __init__(self, ollama_base_url: str = "http://ollama:11434"):
        self.ollama_base_url = ollama_base_url
        # 🆕 FIXED: Changed default to smaller model that fits in memory (6.0 GB vs 7.8 GB)
        self.vision_model = "qwen2.5vl:latest"
        self.timeout = 300.0  # 🆕 INCREASED: Vision processing can take 2-3 minutes for complex images

    async def process_image(
        self,
        image_path: str,
        prompt: Optional[str] = None,
        model_id: Optional[str] = None,
        allow_fallback: bool = True
    ) -> Dict[str, Any]:
        """
        Process an image using a vision-language model.

        Tries UI-selected model first (OpenAI/Anthropic), then falls back to Ollama if needed.

        Args:
            image_path: Path to the image file
            prompt: Optional custom prompt (defaults to text extraction)
            model_id: UI-selected model ID (e.g., "gpt-4o-mini", "claude-3.5-sonnet")
                     If None, uses Ollama vision models directly
            allow_fallback: Allow automatic fallback to Ollama if API model fails (default: True)

        Returns:
            Dict with extracted text and metadata
        """
        try:
            # Read and encode image
            image_data = self._encode_image(image_path)

            # Default prompt for text extraction
            if prompt is None:
                prompt = (
                    "Please carefully read and transcribe ALL text visible in this image. "
                    "Include handwritten text, typed text, labels, captions, and any other written content. "
                    "Preserve the original formatting and layout as much as possible. "
                    "If the text is handwritten, do your best to decipher it accurately."
                )

            # Try UI-selected model first if provided
            if model_id:
                # Handle OpenAI/Anthropic API models
                if "gpt" in model_id.lower() or "claude" in model_id.lower():
                    try:
                        logger.info(f"🎯 Attempting vision analysis with UI-selected API model: {model_id}")
                        response = await self._call_api_vision(model_id, image_data, prompt)

                        if response.get("success"):
                            logger.info(f"✅ Vision analysis succeeded with {model_id}")
                            return response

                    except Exception as e:
                        logger.warning(f"⚠️ API vision model {model_id} failed: {e}")

                        if not allow_fallback:
                            raise

                        logger.info(f"🔄 Falling back to Ollama vision models...")

                # Handle Ollama models (use UI-selected model directly)
                else:
                    logger.info(f"🎯 Using UI-selected Ollama vision model: {model_id}")

                    # 🆕 Use GPU resource manager for automatic cleanup
                    gpu_manager = get_gpu_manager()
                    async with gpu_manager.gpu_task(model_id, "vision"):
                        response = await self._call_ollama_vision(
                            model=model_id,  # Use UI-selected model
                            prompt=prompt,
                            image_data=image_data,
                            allow_fallback=allow_fallback
                        )

                    extracted_text = response.get("response", "")

                    return {
                        "text": extracted_text,
                        "model": response.get("model_used", model_id),
                        "method": "vision_language_model",
                        "success": True,
                        "metadata": {
                            "prompt_tokens": response.get("prompt_eval_count", 0),
                            "response_tokens": response.get("eval_count", 0),
                            "total_duration_ms": response.get("total_duration", 0) / 1_000_000,
                            "fallback_occurred": response.get("fallback_occurred", False)
                        }
                    }

            # Fallback to default Ollama vision model if no model_id provided
            # 🆕 Use GPU resource manager for automatic cleanup
            gpu_manager = get_gpu_manager()
            async with gpu_manager.gpu_task(self.vision_model, "vision"):
                response = await self._call_ollama_vision(
                    model=self.vision_model,  # Use default only if no UI selection
                    prompt=prompt,
                    image_data=image_data,
                    allow_fallback=allow_fallback
                )

            extracted_text = response.get("response", "")

            return {
                "text": extracted_text,
                "model": response.get("model_used", self.vision_model),  # 🆕 Track actual model used
                "method": "vision_language_model",
                "success": True,
                "metadata": {
                    "prompt_tokens": response.get("prompt_eval_count", 0),
                    "response_tokens": response.get("eval_count", 0),
                    "total_duration_ms": response.get("total_duration", 0) / 1_000_000,
                    "fallback_occurred": response.get("fallback_occurred", False)  # 🆕 Track fallback
                }
            }

        except FileNotFoundError:
            logger.error(f"Image file not found: {image_path}")
            return {
                "text": "",
                "model": self.vision_model,
                "method": "vision_language_model",
                "success": False,
                "error": f"Image file not found: {image_path}"
            }
        except Exception as e:
            logger.error(f"Vision processing failed: {e}", exc_info=True)
            return {
                "text": "",
                "model": self.vision_model,
                "method": "vision_language_model",
                "success": False,
                "error": str(e)
            }

    def _encode_image(self, image_path: str) -> str:
        """
        Encode image file to base64.

        Args:
            image_path: Path to image file

        Returns:
            Base64 encoded image string
        """
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image file does not exist: {image_path}")

        with open(image_path, "rb") as image_file:
            image_bytes = image_file.read()
            encoded = base64.b64encode(image_bytes).decode('utf-8')
            return encoded

    async def _call_api_vision(
        self,
        model_id: str,
        image_data: str,
        prompt: str
    ) -> Dict[str, Any]:
        """
        Call OpenAI/Anthropic vision APIs.

        Args:
            model_id: Model ID (e.g., "gpt-4o-mini", "claude-3.5-sonnet")
            image_data: Base64 encoded image
            prompt: Text prompt for analysis

        Returns:
            Dict with text, model, method, success, and metadata
        """
        from app.tier_1.llm.llm_service import get_llm_service

        llm_service = get_llm_service()

        if "gpt" in model_id.lower():
            # OpenAI Vision API
            logger.info(f"🎨 Calling OpenAI vision: {model_id}")

            response = await llm_service.call_openai_vision(
                model=model_id,
                prompt=prompt,
                image_base64=image_data
            )

            return {
                "text": response.get("content", ""),
                "model": model_id,
                "method": "openai_vision",
                "success": True,
                "metadata": {
                    "prompt_tokens": response.get("usage", {}).get("prompt_tokens", 0),
                    "completion_tokens": response.get("usage", {}).get("completion_tokens", 0),
                    "total_tokens": response.get("usage", {}).get("total_tokens", 0)
                }
            }

        elif "claude" in model_id.lower():
            # Anthropic Vision API (future implementation)
            logger.warning(f"⚠️ Anthropic vision not yet implemented for {model_id}")
            raise NotImplementedError(f"Anthropic vision support coming soon")

        else:
            raise ValueError(f"Unknown vision model provider for: {model_id}")

    async def _call_ollama_vision(
        self,
        model: str,
        prompt: str,
        image_data: str,
        allow_fallback: bool = False
    ) -> Dict[str, Any]:
        """
        Call Ollama vision API with memory-aware fallback.

        Args:
            model: Vision model name
            prompt: Text prompt
            image_data: Base64 encoded image
            allow_fallback: Allow automatic model fallback for memory constraints

        Returns:
            API response dict with fallback metadata
        """
        url = f"{self.ollama_base_url}/api/generate"

        payload = {
            "model": model,
            "prompt": prompt,
            "images": [image_data],
            "stream": False
        }

        model_used = model
        fallback_occurred = False

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                result = response.json()
                result["model_used"] = model_used
                result["fallback_occurred"] = fallback_occurred
                return result

        except httpx.HTTPStatusError as e:
            # 🆕 CRITICAL FIX: Check for memory error and fallback if allowed
            if e.response.status_code == 500 and allow_fallback:
                error_text = e.response.text

                # Check if error is memory-related
                if "memory" in error_text.lower() or "system memory" in error_text.lower():
                    logger.warning(
                        f"⚠️  Vision model {model} failed due to memory constraints\n"
                        f"   Error: {error_text[:200]}\n"
                        f"   Attempting fallback to smaller model..."
                    )

                    # Fallback chain for vision models (ONLY vision-capable models)
                    # 🆕 FIXED: Removed text-only model from fallback chain
                    fallback_models = [
                        "llama3.2-vision:3b",   # Smaller vision model (if available)
                        "qwen2.5vl:7b",          # Alternative vision model
                        "qwen2.5vl:latest"       # Our default vision model
                    ]

                    for fallback_model in fallback_models:
                        try:
                            logger.info(f"🔄 Trying fallback model: {fallback_model}")

                            fallback_payload = {
                                "model": fallback_model,
                                "prompt": prompt,
                                "images": [image_data],
                                "stream": False
                            }

                            async with httpx.AsyncClient(timeout=self.timeout) as fallback_client:
                                fallback_response = await fallback_client.post(url, json=fallback_payload)
                                fallback_response.raise_for_status()

                                result = fallback_response.json()
                                result["model_used"] = fallback_model
                                result["fallback_occurred"] = True
                                result["original_model"] = model

                                logger.info(
                                    f"✅ Fallback successful: {fallback_model}\n"
                                    f"   Original model: {model}\n"
                                    f"   Fallback model: {fallback_model}"
                                )

                                return result

                        except Exception as fallback_error:
                            logger.warning(f"Fallback to {fallback_model} failed: {fallback_error}")
                            continue

                    # All fallbacks failed
                    logger.error("❌ All vision model fallbacks failed")
                    raise ValueError(f"Vision processing failed: All models exhausted (original: {model}, tried: {fallback_models})")

            # Re-raise if not a memory error or fallback not allowed
            raise

    async def describe_image(
        self,
        image_path: str,
        question: Optional[str] = None,
        model_id: Optional[str] = None
    ) -> str:
        """
        Get a description of the image or answer a question about it.

        Args:
            image_path: Path to the image file
            question: Optional specific question about the image
            model_id: Optional UI-selected model ID (e.g., "gpt-4o-mini", "qwen2.5vl:latest")

        Returns:
            Description or answer as string
        """
        if question:
            prompt = f"Please answer this question about the image: {question}"
        else:
            prompt = (
                "Please provide a detailed description of this image, including: "
                "1. Main objects and subjects "
                "2. Text content (if any) "
                "3. Overall composition and layout "
                "4. Any notable details"
            )

        result = await self.process_image(image_path, prompt, model_id=model_id)
        return result.get("text", "")


# Global singleton
_vision_service = None


async def get_vision_service() -> VisionService:
    """Get or create the global vision service instance"""
    global _vision_service
    if _vision_service is None:
        _vision_service = VisionService()
    return _vision_service
