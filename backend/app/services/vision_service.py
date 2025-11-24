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

logger = logging.getLogger(__name__)


class VisionService:
    """Service for processing images with vision-language models"""

    def __init__(self, ollama_base_url: str = "http://ollama:11434"):
        self.ollama_base_url = ollama_base_url
        self.vision_model = "llama3.2-vision:11b"
        self.timeout = 120.0  # Vision processing can take longer

    async def process_image(
        self,
        image_path: str,
        prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process an image using a vision-language model.

        Args:
            image_path: Path to the image file
            prompt: Optional custom prompt (defaults to text extraction)

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

            # Call Ollama vision API
            response = await self._call_ollama_vision(
                model=self.vision_model,
                prompt=prompt,
                image_data=image_data
            )

            extracted_text = response.get("response", "")

            return {
                "text": extracted_text,
                "model": self.vision_model,
                "method": "vision_language_model",
                "success": True,
                "metadata": {
                    "prompt_tokens": response.get("prompt_eval_count", 0),
                    "response_tokens": response.get("eval_count", 0),
                    "total_duration_ms": response.get("total_duration", 0) / 1_000_000
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

    async def _call_ollama_vision(
        self,
        model: str,
        prompt: str,
        image_data: str
    ) -> Dict[str, Any]:
        """
        Call Ollama vision API.

        Args:
            model: Vision model name
            prompt: Text prompt
            image_data: Base64 encoded image

        Returns:
            API response dict
        """
        url = f"{self.ollama_base_url}/api/generate"

        payload = {
            "model": model,
            "prompt": prompt,
            "images": [image_data],
            "stream": False
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()

    async def describe_image(
        self,
        image_path: str,
        question: Optional[str] = None
    ) -> str:
        """
        Get a description of the image or answer a question about it.

        Args:
            image_path: Path to the image file
            question: Optional specific question about the image

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

        result = await self.process_image(image_path, prompt)
        return result.get("text", "")


# Global singleton
_vision_service = None


async def get_vision_service() -> VisionService:
    """Get or create the global vision service instance"""
    global _vision_service
    if _vision_service is None:
        _vision_service = VisionService()
    return _vision_service
