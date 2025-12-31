"""
Ultra-Smart Extractor - AI-Powered Multi-Modal Data Extraction

This module provides the most advanced extraction capabilities combining:
- Docling for document processing (PDF, DOCX, PPTX, images in PDFs)
- Vision models for image analysis (GPT-4V, Claude Vision)
- LLMs for intelligent text extraction
- Playwright for web scraping
- Intelligent fallback strategies

Handles ANY content type robustly and smartly.
"""

from typing import Optional, Dict, Any, List, Union
import logging
import json
import base64
import io
from pathlib import Path
import asyncio

logger = logging.getLogger(__name__)


class UltraSmartExtractor:
    """
    Most advanced extractor that handles all content types intelligently

    Features:
    - Multi-modal extraction (text, images, documents, web pages)
    - Docling integration for superior document processing
    - Vision model support (GPT-4V, Claude Vision) for images
    - Intelligent fallback chains
    - Smart content type detection
    - Robust error handling
    """

    def __init__(
        self,
        llm_service=None,
        scraper_service=None,
        document_service=None
    ):
        """
        Initialize ultra-smart extractor

        Args:
            llm_service: LLM service instance (supports OpenAI, Anthropic, Ollama)
            scraper_service: Web scraper service
            document_service: Document processing service (with Docling)
        """
        self.logger = logger
        self.llm_service = llm_service
        self.scraper_service = scraper_service
        self.document_service = document_service

        # Check for Docling availability
        try:
            from docling.document_converter import DocumentConverter
            self.doc_converter = DocumentConverter()
            self.docling_available = True
            logger.info("✅ Docling initialized for advanced document processing")
        except Exception as e:
            self.docling_available = False
            logger.warning(f"⚠️ Docling not available ({str(e)[:100]}) - using fallback processors")

    async def extract_from_any_source(
        self,
        source: Union[str, bytes],
        source_type: str,
        user_instructions: str,
        llm_provider: str = "openai",
        vision_provider: str = "openai",  # openai=GPT-4V, anthropic=Claude Vision
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Extract data from ANY source type intelligently

        Args:
            source: URL (str), file bytes (bytes), or file path (str with file://)
            source_type: Type hint: 'url', 'pdf', 'image', 'docx', 'pptx', 'auto'
            user_instructions: Natural language instructions for what to extract
            llm_provider: LLM to use (openai, anthropic, ollama)
            vision_provider: Vision model for images (openai, anthropic)
            **kwargs: Additional parameters

        Returns:
            {
                "success": bool,
                "data": [{"field": "value", ...}],
                "source_type_detected": str,
                "extraction_method": str,
                "confidence": float,
                "metadata": {...}
            }
        """
        try:
            logger.info("="*80)
            logger.info("🚀 ULTRA-SMART EXTRACTION INITIATED")
            logger.info("="*80)
            logger.info(f"📋 User Instructions: {user_instructions}")
            logger.info(f"🎯 Source Type: {source_type}")
            logger.info(f"🤖 LLM Provider: {llm_provider}")
            logger.info(f"👁️  Vision Provider: {vision_provider}")
            logger.info("="*80)

            # Auto-detect source type if needed
            if source_type == "auto":
                source_type = await self._detect_source_type(source)
                logger.info(f"🔍 Auto-detected source type: {source_type}")

            # Extract model_id and max_steps from kwargs for dynamic model selection
            model_id = kwargs.get('model_id', None)
            max_steps = kwargs.get('max_steps', 10)
            logger.info(f"🎯 Model ID: {model_id or 'default'}")
            logger.info(f"🔢 Max Steps: {max_steps}")

            # Route to appropriate extraction method
            if source_type == "url" or (isinstance(source, str) and source.startswith("http")):
                return await self._extract_from_url(source, user_instructions, llm_provider, vision_provider, model_id, max_steps)

            elif source_type in ["pdf", "docx", "pptx", "doc"] or (isinstance(source, bytes)):
                return await self._extract_from_document(
                    source, source_type, user_instructions, llm_provider, vision_provider, model_id
                )

            elif source_type in ["image", "png", "jpg", "jpeg", "webp"]:
                return await self._extract_from_image(
                    source, user_instructions, vision_provider
                )

            elif source_type == "text":
                return await self._extract_from_text(source, user_instructions, llm_provider, model_id)

            else:
                # Fallback: Try to intelligently handle unknown types
                logger.warning(f"⚠️ Unknown source type '{source_type}', attempting intelligent detection")
                return await self._extract_with_intelligent_fallback(
                    source, user_instructions, llm_provider, vision_provider, model_id
                )

        except Exception as e:
            logger.error(f"❌ Ultra-smart extraction failed: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "data": [],
                "extraction_method": "failed"
            }

    async def _extract_from_url(
        self,
        url: str,
        user_instructions: str,
        llm_provider: str,
        vision_provider: str = "openai",
        model_id: Optional[str] = None,
        max_steps: int = 10
    ) -> Dict[str, Any]:
        """Extract from web URL using Playwright + LLM (or Docling for PDFs)"""
        logger.info(f"🌐 Extracting from URL: {url}")
        logger.info(f"🤖 Using model: {model_id or 'default'}")

        try:
            # Check if instructions require AI-powered navigation
            requires_navigation = await self._check_if_requires_navigation(user_instructions)

            if requires_navigation:
                logger.info("🧭 Instructions require AI-powered navigation - using Navigation Agent")
                from app.services.webscraper.agents import NavigationAgent

                nav_agent = NavigationAgent(llm_service=self.llm_service)

                # Ensure model_id is provided for navigation
                if not model_id:
                    raise ValueError("model_id is required for navigation. No default model fallback configured.")

                result = await nav_agent.navigate_and_extract(
                    url=url,
                    user_instructions=user_instructions,
                    llm_provider=llm_provider,
                    model_id=model_id,
                    max_steps=max_steps
                )

                if result["success"]:
                    logger.info(f"✅ Navigation agent extracted {len(result['data'])} items")

                    return {
                        "success": True,
                        "data": result["data"],
                        "source_type_detected": "url",
                        "extraction_method": f"playwright_navigation+{llm_provider}",
                        "confidence": 0.95,
                        "metadata": {
                            "navigation_path": result["navigation_path"],
                            "steps_taken": result["steps_taken"],
                            "final_url": result["final_url"]
                        }
                    }
                else:
                    logger.warning(f"⚠️ Navigation agent failed: {result.get('error')}")
                    logger.info("🔄 Falling back to standard extraction...")

            # Check if URL points to a PDF document
            is_pdf = url.lower().endswith('.pdf')

            if not is_pdf:
                # Try to detect PDF by Content-Type header
                import httpx
                try:
                    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                        head_response = await client.head(url)
                        content_type = head_response.headers.get('content-type', '').lower()
                        if 'application/pdf' in content_type:
                            is_pdf = True
                            logger.info(f"🔍 Detected PDF from Content-Type: {content_type}")
                except Exception as e:
                    logger.debug(f"HEAD request failed, continuing with normal fetch: {e}")

            # If URL points to PDF, download and use Docling
            if is_pdf:
                logger.info("📄 URL points to PDF - routing to Docling extraction...")

                import httpx
                async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                    pdf_response = await client.get(url)
                    pdf_bytes = pdf_response.content

                logger.info(f"📥 Downloaded PDF: {len(pdf_bytes):,} bytes")

                # Route to document extraction with Docling
                return await self._extract_from_document(
                    source=pdf_bytes,
                    source_type="pdf",
                    user_instructions=user_instructions,
                    llm_provider=llm_provider,
                    vision_provider=vision_provider,
                    model_id=model_id
                )

            # Otherwise, proceed with normal HTML extraction
            # Use scraper service to fetch content
            if self.scraper_service:
                logger.info("📡 Using Playwright to fetch webpage...")
                scrape_result = await self.scraper_service.scrape_url(url, db=None)

                if not scrape_result or not scrape_result.get('html'):
                    logger.error("❌ Failed to fetch webpage content")
                    return {"success": False, "error": "Failed to fetch webpage", "data": []}

                html_content = scrape_result['html']
                text_content = scrape_result.get('text', '')

                logger.info(f"✅ Fetched {len(html_content):,} chars of HTML")
                logger.info(f"📝 Extracted {len(text_content):,} chars of clean text")
            else:
                logger.error("❌ Scraper service not initialized")
                return {"success": False, "error": "Scraper service unavailable", "data": []}

            # Extract fields using LLM
            logger.info(f"🤖 Using {llm_provider} LLM to extract structured data...")
            extracted_data = await self._llm_extract_fields(
                text_content, user_instructions, llm_provider, model_id
            )

            return {
                "success": True,
                "data": [extracted_data] if extracted_data else [],
                "source_type_detected": "url",
                "extraction_method": f"playwright+{llm_provider}",
                "metadata": {
                    "url": url,
                    "html_length": len(html_content),
                    "text_length": len(text_content)
                }
            }

        except Exception as e:
            logger.error(f"❌ URL extraction failed: {str(e)}")
            return {"success": False, "error": str(e), "data": []}

    async def _extract_from_document(
        self,
        source: Union[str, bytes],
        source_type: str,
        user_instructions: str,
        llm_provider: str,
        vision_provider: str,
        model_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract from documents (PDF, DOCX, PPTX) using Docling

        Docling handles:
        - Text extraction (better than PyPDF2)
        - Tables and structured data
        - Images within documents
        - Layout preservation
        """
        logger.info(f"📄 Extracting from {source_type.upper()} document using Docling")

        try:
            # Get file bytes
            if isinstance(source, str) and source.startswith("file://"):
                # File path
                file_path = source.replace("file://", "")
                with open(file_path, 'rb') as f:
                    file_data = f.read()
            elif isinstance(source, bytes):
                file_data = source
            else:
                logger.error(f"❌ Invalid document source type: {type(source)}")
                return {"success": False, "error": "Invalid document source", "data": []}

            # Use Docling if available
            if self.docling_available and self.doc_converter:
                logger.info("🔧 Using Docling for document processing...")

                # Save temporarily for Docling
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{source_type}") as tmp:
                    tmp.write(file_data)
                    tmp_path = tmp.name

                try:
                    # Convert with Docling
                    result = self.doc_converter.convert(tmp_path)

                    # Extract text
                    text_content = result.document.export_to_markdown()
                    logger.info(f"✅ Docling extracted {len(text_content):,} chars")

                    # Check for images
                    images = []
                    if hasattr(result.document, 'pictures'):
                        images = result.document.pictures
                        logger.info(f"🖼️  Found {len(images)} images in document")

                    # Extract tables
                    tables = []
                    if hasattr(result.document, 'tables'):
                        tables = result.document.tables
                        logger.info(f"📊 Found {len(tables)} tables in document")

                    # Clean up temp file
                    import os
                    os.unlink(tmp_path)

                except Exception as e:
                    logger.error(f"❌ Docling processing failed: {str(e)}")
                    # Fall back to basic extraction
                    text_content = await self._extract_document_fallback(file_data, source_type)
                    images = []
                    tables = []

            else:
                logger.warning("⚠️ Docling not available, using fallback extraction")
                text_content = await self._extract_document_fallback(file_data, source_type)
                images = []
                tables = []

            # If document has images and vision model available, analyze them too
            extracted_from_images = []
            if images and vision_provider:
                logger.info(f"👁️  Analyzing {len(images)} images with {vision_provider} Vision...")
                for idx, image in enumerate(images[:5]):  # Limit to 5 images
                    try:
                        image_data = await self._analyze_image_with_vision(
                            image, user_instructions, vision_provider
                        )
                        if image_data:
                            extracted_from_images.append(image_data)
                    except Exception as e:
                        logger.warning(f"⚠️ Image {idx+1} analysis failed: {str(e)}")

            # Extract fields from text using LLM
            logger.info(f"🤖 Using {llm_provider} to extract structured data from text...")
            text_data = await self._llm_extract_fields(
                text_content, user_instructions, llm_provider, model_id
            )

            # Combine text and image extractions
            combined_data = text_data.copy() if text_data else {}

            # Merge image data (prefer text data if conflicts)
            for img_data in extracted_from_images:
                for key, value in img_data.items():
                    if key not in combined_data or combined_data[key] in ["—", "", None]:
                        combined_data[key] = value

            return {
                "success": True,
                "data": [combined_data] if combined_data else [],
                "source_type_detected": source_type,
                "extraction_method": f"docling+{llm_provider}" + (f"+{vision_provider}_vision" if images else ""),
                "metadata": {
                    "text_length": len(text_content),
                    "images_found": len(images),
                    "tables_found": len(tables),
                    "images_analyzed": len(extracted_from_images)
                }
            }

        except Exception as e:
            logger.error(f"❌ Document extraction failed: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e), "data": []}

    async def _extract_from_image(
        self,
        source: Union[str, bytes],
        user_instructions: str,
        vision_provider: str
    ) -> Dict[str, Any]:
        """Extract data from images using vision models (GPT-4V / Claude Vision)"""
        logger.info(f"🖼️  Extracting from image using {vision_provider} Vision")

        try:
            # Get image bytes
            if isinstance(source, str) and source.startswith("file://"):
                with open(source.replace("file://", ""), 'rb') as f:
                    image_data = f.read()
            elif isinstance(source, str) and source.startswith("http"):
                # Download image
                import httpx
                async with httpx.AsyncClient() as client:
                    response = await client.get(source)
                    image_data = response.content
            elif isinstance(source, bytes):
                image_data = source
            else:
                return {"success": False, "error": "Invalid image source", "data": []}

            # Analyze with vision model
            extracted_data = await self._analyze_image_with_vision(
                image_data, user_instructions, vision_provider
            )

            return {
                "success": True,
                "data": [extracted_data] if extracted_data else [],
                "source_type_detected": "image",
                "extraction_method": f"{vision_provider}_vision",
                "metadata": {
                    "image_size": len(image_data)
                }
            }

        except Exception as e:
            logger.error(f"❌ Image extraction failed: {str(e)}")
            return {"success": False, "error": str(e), "data": []}

    async def _extract_from_text(
        self,
        text: str,
        user_instructions: str,
        llm_provider: str,
        model_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Extract from plain text using LLM"""
        logger.info("📝 Extracting from plain text")

        try:
            extracted_data = await self._llm_extract_fields(
                text, user_instructions, llm_provider, model_id
            )

            return {
                "success": True,
                "data": [extracted_data] if extracted_data else [],
                "source_type_detected": "text",
                "extraction_method": llm_provider,
                "metadata": {
                    "text_length": len(text)
                }
            }

        except Exception as e:
            logger.error(f"❌ Text extraction failed: {str(e)}")
            return {"success": False, "error": str(e), "data": []}

    async def _llm_extract_fields(
        self,
        content: str,
        user_instructions: str,
        llm_provider: str,
        model_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Use LLM to extract structured fields from content"""
        if not self.llm_service:
            logger.error("❌ LLM service not initialized")
            return None

        try:
            # Parse user instructions to extract field names
            fields = self._parse_field_names(user_instructions)
            logger.info(f"📋 Detected {len(fields)} fields to extract: {fields}")

            # Build extraction prompt
            system_prompt = """You are an expert data extraction assistant. Extract the requested information from the provided content.

CRITICAL RULES:
1. Extract ONLY values that exist in the content
2. NEVER hallucinate or make up values
3. If a field is not found, use "—"
4. Return VALID JSON ONLY (no markdown, no explanations)
5. Be thorough - search entire content carefully

Return format:
{
  "field1": "extracted_value",
  "field2": "extracted_value",
  "field3": "—"
}"""

            fields_list = "\n".join([f"- {field}" for field in fields])

            user_prompt = f"""Content to analyze:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{content[:20000]}
{"... [content truncated] ..." if len(content) > 20000 else ""}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Extract these fields:
{fields_list}

Instructions: {user_instructions}

Return pure JSON with the extracted values."""

            # DEBUG: Log actual LLM input
            logger.info("=" * 80)
            logger.info("🔍 LLM EXTRACTION DEBUG INFO:")
            logger.info(f"📊 Content length: {len(content)} chars")
            logger.info(f"📋 Fields to extract: {fields}")
            logger.info(f"📝 User instructions: {user_instructions}")
            logger.info("📄 Content preview (first 500 chars):")
            logger.info(content[:500])
            logger.info("💬 Full user prompt being sent to LLM:")
            logger.info(user_prompt[:1000] + "..." if len(user_prompt) > 1000 else user_prompt)
            logger.info("=" * 80)

            # Call LLM
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]

            llm_result = await self.llm_service.generate(
                prompt=user_prompt,
                messages=messages,
                max_tokens=2000,
                temperature=0.0,  # Deterministic extraction
                model_id=model_id  # Dynamic model selection like chat
            )

            # DEBUG: Log LLM response
            logger.info("🤖 LLM Response:")
            logger.info(f"Response: {llm_result}")

            if not llm_result or not llm_result.get('content'):
                logger.error("❌ LLM returned empty response")
                return None

            # Parse JSON response
            response = llm_result['content']
            extracted = self._parse_json_response(response)

            logger.info(f"✅ Extracted {len(extracted)} fields")
            return extracted

        except Exception as e:
            logger.error(f"❌ LLM extraction failed: {str(e)}")
            return None

    async def _analyze_image_with_vision(
        self,
        image_data: bytes,
        user_instructions: str,
        vision_provider: str
    ) -> Optional[Dict[str, Any]]:
        """Analyze image using vision models (GPT-4V or Claude Vision)"""
        if not self.llm_service:
            logger.error("❌ LLM service not initialized")
            return None

        try:
            # Encode image to base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')

            # Determine image format
            import imghdr
            image_format = imghdr.what(None, h=image_data) or 'jpeg'

            # Build vision prompt
            system_prompt = "You are an expert at analyzing images and extracting structured data. Extract ONLY information visible in the image. Return pure JSON."

            user_prompt = f"""Analyze this image and extract the requested information.

Instructions: {user_instructions}

Return the data as pure JSON (no markdown, no explanations)."""

            if vision_provider == "openai":
                # OpenAI GPT-4 Vision format
                messages = [
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/{image_format};base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ]

                # Call with vision model
                llm_result = await self.llm_service.generate(
                    prompt=user_prompt,
                    messages=messages,
                    max_tokens=1500,
                    temperature=0.0,
                    model="gpt-4-vision-preview"  # or gpt-4o which has vision
                )

            elif vision_provider == "anthropic":
                # Claude Vision format
                messages = [
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": f"image/{image_format}",
                                    "data": image_base64
                                }
                            },
                            {"type": "text", "text": user_prompt}
                        ]
                    }
                ]

                llm_result = await self.llm_service.generate(
                    prompt=user_prompt,
                    messages=messages,
                    max_tokens=1500,
                    temperature=0.0,
                    model="claude-3-opus-20240229"  # or claude-3-sonnet
                )

            else:
                logger.error(f"❌ Unsupported vision provider: {vision_provider}")
                return None

            if not llm_result or not llm_result.get('content'):
                return None

            # Parse JSON response
            response = llm_result['content']
            extracted = self._parse_json_response(response)

            logger.info(f"✅ Vision model extracted {len(extracted)} fields from image")
            return extracted

        except Exception as e:
            logger.error(f"❌ Vision analysis failed: {str(e)}")
            return None

    async def _extract_document_fallback(self, file_data: bytes, file_type: str) -> str:
        """Fallback document extraction using basic libraries"""
        try:
            if file_type == "pdf":
                from PyPDF2 import PdfReader
                pdf = PdfReader(io.BytesIO(file_data))
                text = "\n\n".join([page.extract_text() for page in pdf.pages])
                return text

            elif file_type in ["docx", "doc"]:
                from docx import Document as DocxDocument
                doc = DocxDocument(io.BytesIO(file_data))
                text = "\n\n".join([para.text for para in doc.paragraphs])
                return text

            elif file_type == "pptx":
                from pptx import Presentation
                prs = Presentation(io.BytesIO(file_data))
                text_runs = []
                for slide in prs.slides:
                    for shape in slide.shapes:
                        if hasattr(shape, "text"):
                            text_runs.append(shape.text)
                return "\n\n".join(text_runs)

            else:
                return file_data.decode('utf-8', errors='ignore')

        except Exception as e:
            logger.error(f"❌ Fallback extraction failed: {str(e)}")
            return ""

    async def _detect_source_type(self, source: Union[str, bytes]) -> str:
        """Auto-detect source type"""
        if isinstance(source, str):
            if source.startswith("http"):
                return "url"
            elif source.endswith(".pdf"):
                return "pdf"
            elif source.endswith((".png", ".jpg", ".jpeg", ".webp")):
                return "image"
            elif source.endswith((".docx", ".doc")):
                return "docx"
            elif source.endswith(".pptx"):
                return "pptx"
            else:
                return "text"

        elif isinstance(source, bytes):
            # Check magic bytes
            if source[:4] == b'%PDF':
                return "pdf"
            elif source[:2] in [b'\xff\xd8', b'\x89\x50']:  # JPEG or PNG
                return "image"
            elif source[:2] == b'PK':  # ZIP-based (DOCX, PPTX)
                # Check for specific markers
                if b'word/' in source[:1000]:
                    return "docx"
                elif b'ppt/' in source[:1000]:
                    return "pptx"

            return "text"

        return "unknown"

    async def _extract_with_intelligent_fallback(
        self,
        source: Union[str, bytes],
        user_instructions: str,
        llm_provider: str,
        vision_provider: str,
        model_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Intelligent fallback - try multiple methods"""
        logger.info("🔄 Using intelligent fallback strategy...")

        # Try as URL first
        if isinstance(source, str) and ("http" in source or "www" in source):
            result = await self._extract_from_url(source, user_instructions, llm_provider, vision_provider, model_id)
            if result.get("success"):
                return result

        # Try as document
        if isinstance(source, bytes):
            result = await self._extract_from_document(
                source, "auto", user_instructions, llm_provider, vision_provider, model_id
            )
            if result.get("success"):
                return result

        # Try as text
        if isinstance(source, str):
            result = await self._extract_from_text(source, user_instructions, llm_provider, model_id)
            if result.get("success"):
                return result

        return {"success": False, "error": "All extraction methods failed", "data": []}

    def _parse_field_names(self, user_instructions: str) -> List[str]:
        """Parse field names from user instructions"""
        # Common patterns: "Extract X and Y", "Get X, Y, Z", etc.
        import re

        # Look for explicit field mentions
        patterns = [
            r"extract[:\s]+([^.!?]+)",
            r"get[:\s]+([^.!?]+)",
            r"find[:\s]+([^.!?]+)",
        ]

        fields = []
        for pattern in patterns:
            match = re.search(pattern, user_instructions.lower())
            if match:
                field_text = match.group(1)
                # Split by common delimiters
                field_parts = re.split(r',|\band\b|\bor\b', field_text)
                fields.extend([f.strip().title() for f in field_parts if f.strip()])

        # If no fields found, try to extract key nouns
        if not fields:
            words = user_instructions.split()
            fields = [word.title() for word in words if len(word) > 3 and word.isalpha()][:5]

        return fields[:10]  # Limit to 10 fields

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON from LLM response"""
        import re

        # Clean response
        response = response.strip()

        # Try direct JSON parse
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # Try extracting from markdown code blocks
        markdown_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
        if markdown_match:
            try:
                return json.loads(markdown_match.group(1))
            except json.JSONDecodeError:
                pass

        # Try finding any JSON object
        json_match = re.search(r'\{(?:[^{}]|\{[^{}]*\})*\}', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        logger.error(f"❌ Failed to parse JSON from response: {response[:200]}...")
        return {}

    async def extract_to_table(
        self,
        source: Union[str, bytes],
        source_type: str = "auto",
        user_instructions: Optional[str] = None,
        llm_provider: str = "openai",
        vision_provider: str = "openai",
        model_id: Optional[str] = None,
        max_steps: int = 10
    ) -> Dict[str, Any]:
        """
        🎯 ULTIMATE GOAL: Extract ANY random content → ALWAYS return tabular/structured output

        This is the "throw anything at it" method that GUARANTEES tabular output.

        Args:
            source: ANYTHING - URL, file bytes, file path, text
            source_type: 'auto' to detect, or specify: 'url', 'pdf', 'image', 'docx', etc.
            user_instructions: Optional natural language instructions
            llm_provider: LLM to use (openai, anthropic, ollama)
            vision_provider: Vision model for images (openai, anthropic)

        Returns:
            {
                "success": true,
                "table": [
                    {"col1": "val1", "col2": "val2", ...},  # Row 1
                    {"col1": "val3", "col2": "val4", ...}   # Row 2
                ],
                "columns": ["col1", "col2", ...],
                "row_count": 2,
                "extraction_metadata": {...}
            }

        Examples:
            # Random PDF
            >>> result = await extractor.extract_to_table(pdf_bytes, source_type="pdf")
            >>> result["table"]  # Always a list of dicts (tabular)

            # Random image
            >>> result = await extractor.extract_to_table(image_url, source_type="url")
            >>> result["table"]  # Structured table extracted from image

            # Random text
            >>> result = await extractor.extract_to_table("Some random text", source_type="text")
            >>> result["table"]  # Converts unstructured text to structured table
        """
        try:
            logger.info("="*80)
            logger.info("🎯 ULTRA-SMART TABLE EXTRACTION - Handle ANY random content")
            logger.info("="*80)

            # Step 1: Use extract_from_any_source to get raw data
            if not user_instructions:
                user_instructions = "Extract all relevant information into a structured format"

            raw_result = await self.extract_from_any_source(
                source=source,
                source_type=source_type,
                user_instructions=user_instructions,
                llm_provider=llm_provider,
                vision_provider=vision_provider,
                model_id=model_id,
                max_steps=max_steps
            )

            if not raw_result.get("success"):
                # Even on failure, return structured empty table
                return {
                    "success": False,
                    "table": [],
                    "columns": [],
                    "row_count": 0,
                    "error": raw_result.get("error", "Extraction failed"),
                    "extraction_metadata": raw_result.get("metadata", {})
                }

            # Step 2: Ensure data is in tabular format
            raw_data = raw_result.get("data", [])

            # Handle different data structures
            if isinstance(raw_data, list) and len(raw_data) > 0:
                # Already a list of dicts (perfect tabular format)
                if isinstance(raw_data[0], dict):
                    table = raw_data
                    columns = list(raw_data[0].keys()) if raw_data else []

                # List of lists (convert to dicts)
                elif isinstance(raw_data[0], list):
                    # First row is headers
                    columns = raw_data[0] if raw_data else []
                    table = [
                        {columns[i]: row[i] for i in range(min(len(columns), len(row)))}
                        for row in raw_data[1:]
                    ]

                # List of strings (convert to single column table)
                else:
                    columns = ["value"]
                    table = [{"value": item} for item in raw_data]

            elif isinstance(raw_data, dict):
                # Single dict (convert to single-row table)
                columns = list(raw_data.keys())
                table = [raw_data]

            else:
                # Fallback: empty table
                columns = []
                table = []

            # Step 3: Normalize and clean table
            table = self._normalize_table(table)

            logger.info(f"✅ Structured table created: {len(table)} rows × {len(columns)} columns")

            return {
                "success": True,
                "table": table,
                "columns": columns,
                "row_count": len(table),
                "extraction_metadata": {
                    "source_type": raw_result.get("source_type_detected", source_type),
                    "extraction_method": raw_result.get("extraction_method", "unknown"),
                    "metadata": raw_result.get("metadata", {})
                }
            }

        except Exception as e:
            logger.error(f"❌ Table extraction failed: {str(e)}", exc_info=True)
            return {
                "success": False,
                "table": [],
                "columns": [],
                "row_count": 0,
                "error": str(e),
                "extraction_metadata": {}
            }

    def _generate_css_selectors_from_html(
        self,
        html_content: str,
        extracted_table: List[Dict[str, Any]]
    ) -> Dict[str, str]:
        """
        Generate CSS selectors for extracted fields using heuristic pattern matching

        This uses BeautifulSoup to find elements containing the extracted values,
        then generates stable CSS selectors based on element attributes.

        Args:
            html_content: Raw HTML from the page
            extracted_table: Extracted data table

        Returns:
            Dict mapping field names to CSS selectors
            Example: {"title": "h3 a", "price": ".price_color"}
        """
        if not html_content or not extracted_table:
            return {}

        try:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(html_content, 'html.parser')
            selectors = {}

            # Get first row as example
            first_row = extracted_table[0] if extracted_table else {}

            for field_name, field_value in first_row.items():
                if not field_value or field_value == "—":
                    continue

                # Clean the value for matching
                clean_value = str(field_value).strip()

                # Find elements containing this value
                matching_elements = []
                for element in soup.find_all(string=lambda text: text and clean_value in str(text).strip()):
                    parent = element.parent
                    if parent:
                        matching_elements.append(parent)

                if not matching_elements:
                    continue

                # Pick the best element (most specific)
                best_element = matching_elements[0]

                # Generate CSS selector
                selector = self._generate_best_selector(best_element)
                if selector:
                    selectors[field_name] = selector
                    logger.debug(f"Generated selector for '{field_name}': {selector}")

            return selectors

        except Exception as e:
            logger.warning(f"⚠️  Failed to generate CSS selectors: {e}")
            return {}

    def _generate_best_selector(self, element) -> str:
        """
        Generate the best CSS selector for a BeautifulSoup element

        Priority:
        1. ID (if unique)
        2. Class + element type (e.g., h3.product-title)
        3. Element type only
        """
        try:
            # Try ID first
            elem_id = element.get('id')
            if elem_id and elem_id.strip():
                return f"#{elem_id}"

            # Try class + element
            classes = element.get('class', [])
            if classes:
                # Use first class
                class_name = classes[0] if isinstance(classes, list) else classes
                return f"{element.name}.{class_name}"

            # Fallback to just element type
            return element.name

        except Exception as e:
            logger.debug(f"Selector generation error: {e}")
            return element.name if hasattr(element, 'name') else ''

    def _normalize_table(self, table: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalize table to ensure all rows have same columns

        Handles:
        - Missing fields in some rows
        - Inconsistent column names
        - Empty values
        """
        if not table:
            return []

        # Get all unique columns across all rows
        all_columns = set()
        for row in table:
            all_columns.update(row.keys())

        all_columns = sorted(list(all_columns))

        # Ensure each row has all columns
        normalized_table = []
        for row in table:
            normalized_row = {}
            for col in all_columns:
                normalized_row[col] = row.get(col, "—")
            normalized_table.append(normalized_row)

        return normalized_table

    async def extract_multi_row(
        self,
        source: Union[str, bytes],
        source_type: str = "auto",
        user_instructions: Optional[str] = None,
        llm_provider: str = "openai",
        vision_provider: str = "openai",
        max_rows: int = 100
    ) -> Dict[str, Any]:
        """
        Extract multiple rows from content (e.g., list of products, table of data)

        Perfect for:
        - PDFs with tables
        - Web pages with product listings
        - Screenshots of spreadsheets
        - Documents with repeated data

        Args:
            source: Content to extract from
            source_type: Type or 'auto'
            user_instructions: What to extract
            llm_provider: LLM to use
            vision_provider: Vision model for images
            max_rows: Maximum rows to extract (default 100)

        Returns:
            Same format as extract_to_table but optimized for multi-row extraction
        """
        try:
            logger.info(f"🔢 Multi-row extraction (max {max_rows} rows)")

            # Enhanced instructions for multi-row extraction
            if not user_instructions:
                enhanced_instructions = "Extract ALL items/entries as separate rows in a table"
            else:
                enhanced_instructions = f"{user_instructions}. Extract EACH item as a separate row. Return up to {max_rows} rows."

            # Use the table extraction method
            result = await self.extract_to_table(
                source=source,
                source_type=source_type,
                user_instructions=enhanced_instructions,
                llm_provider=llm_provider,
                vision_provider=vision_provider
            )

            # Limit rows if needed
            if result.get("success") and result.get("row_count", 0) > max_rows:
                logger.warning(f"⚠️ Limiting output from {result['row_count']} to {max_rows} rows")
                result["table"] = result["table"][:max_rows]
                result["row_count"] = max_rows
                result["truncated"] = True

            return result

        except Exception as e:
            logger.error(f"❌ Multi-row extraction failed: {str(e)}")
            return {
                "success": False,
                "table": [],
                "columns": [],
                "row_count": 0,
                "error": str(e)
            }

    async def extract_with_navigation(
        self,
        url: str,
        user_instructions: str,
        navigation_config: Optional[Dict[str, Any]] = None,
        llm_provider: str = "openai",
        max_pages: int = 10
    ) -> Dict[str, Any]:
        """
        🧭 ADVANCED: Extract data from complex websites requiring navigation

        Handles:
        - Clicking buttons/links
        - Scrolling to load dynamic content
        - Pagination (next/previous buttons)
        - Form submissions
        - Waiting for dynamic elements
        - Multi-page traversal

        Args:
            url: Starting URL
            user_instructions: What to extract (e.g., "Extract all product names and prices")
            navigation_config: Configuration for navigation (optional)
                {
                    "actions": [  # Sequence of actions to perform
                        {"type": "click", "selector": ".next-button"},
                        {"type": "scroll", "direction": "down", "amount": 1000},
                        {"type": "wait", "selector": ".product-card", "timeout": 5000},
                        {"type": "input", "selector": "#search", "value": "query"},
                        {"type": "pagination", "next_selector": ".next", "max_pages": 5}
                    ],
                    "wait_for_load": True,  # Wait for page load after each action
                    "scroll_to_bottom": False,  # Auto-scroll to load lazy content
                    "extract_per_page": True  # Extract data from each page separately
                }
            llm_provider: LLM to use for extraction
            max_pages: Maximum pages to traverse (safety limit)

        Returns:
            {
                "success": true,
                "table": [...],  # Combined data from all pages
                "columns": [...],
                "row_count": int,
                "pages_visited": int,
                "navigation_log": [...],  # Log of navigation actions
                "extraction_metadata": {...}
            }

        Examples:
            # Simple pagination
            >>> result = await extractor.extract_with_navigation(
            ...     url="https://example.com/products",
            ...     user_instructions="Extract product name, price, rating",
            ...     navigation_config={
            ...         "actions": [
            ...             {"type": "pagination", "next_selector": ".next-page", "max_pages": 5}
            ...         ]
            ...     }
            ... )

            # Complex interaction
            >>> result = await extractor.extract_with_navigation(
            ...     url="https://example.com",
            ...     user_instructions="Extract all search results",
            ...     navigation_config={
            ...         "actions": [
            ...             {"type": "input", "selector": "#search", "value": "laptop"},
            ...             {"type": "click", "selector": "#search-button"},
            ...             {"type": "wait", "selector": ".results", "timeout": 3000},
            ...             {"type": "scroll", "direction": "down", "amount": "bottom"}
            ...         ]
            ...     }
            ... )
        """
        try:
            logger.info("="*80)
            logger.info("🧭 ULTRA-SMART NAVIGATION EXTRACTION - Complex Website Traversal")
            logger.info("="*80)
            logger.info(f"🌐 Starting URL: {url}")
            logger.info(f"📋 Instructions: {user_instructions}")
            logger.info(f"📄 Max Pages: {max_pages}")
            logger.info("="*80)

            # Initialize Playwright
            from playwright.async_api import async_playwright

            all_extracted_data = []
            navigation_log = []
            pages_visited = 0

            async with async_playwright() as p:
                # Launch browser
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                )
                page = await context.new_page()

                try:
                    # Navigate to initial URL
                    logger.info(f"🚀 Navigating to {url}")
                    await page.goto(url, wait_until="networkidle", timeout=30000)
                    navigation_log.append({"action": "goto", "url": url, "status": "success"})
                    pages_visited += 1

                    # Extract data from first page
                    first_page_data = await self._extract_from_page(
                        page, user_instructions, llm_provider
                    )
                    if first_page_data:
                        all_extracted_data.extend(first_page_data)
                        logger.info(f"✅ Extracted {len(first_page_data)} rows from page 1")

                    # Execute navigation actions if provided
                    if navigation_config and "actions" in navigation_config:
                        actions = navigation_config["actions"]

                        for action in actions:
                            action_type = action.get("type")

                            # Handle pagination specially (multiple page extractions)
                            if action_type == "pagination":
                                pagination_data = await self._handle_pagination(
                                    page, action, user_instructions, llm_provider, max_pages, pages_visited
                                )
                                all_extracted_data.extend(pagination_data["data"])
                                navigation_log.extend(pagination_data["log"])
                                pages_visited += pagination_data["pages_visited"]

                            # Handle single actions
                            else:
                                action_result = await self._execute_navigation_action(page, action)
                                navigation_log.append(action_result)

                                # If extract_per_page is enabled, extract after each action
                                if navigation_config.get("extract_per_page"):
                                    page_data = await self._extract_from_page(
                                        page, user_instructions, llm_provider
                                    )
                                    if page_data:
                                        all_extracted_data.extend(page_data)
                                        logger.info(f"✅ Extracted {len(page_data)} rows after {action_type}")

                    # Auto-scroll to bottom if configured
                    if navigation_config and navigation_config.get("scroll_to_bottom"):
                        logger.info("📜 Auto-scrolling to load lazy content...")
                        await self._scroll_to_bottom(page)

                        # Extract after scrolling
                        scroll_data = await self._extract_from_page(
                            page, user_instructions, llm_provider
                        )
                        if scroll_data:
                            all_extracted_data.extend(scroll_data)
                            logger.info(f"✅ Extracted {len(scroll_data)} rows after scrolling")

                finally:
                    await browser.close()

            # Convert extracted data to table format
            if all_extracted_data:
                # Normalize table structure
                table = self._normalize_table(all_extracted_data)
                columns = list(table[0].keys()) if table else []

                logger.info(f"✅ Navigation extraction complete: {len(table)} total rows from {pages_visited} pages")

                return {
                    "success": True,
                    "table": table,
                    "columns": columns,
                    "row_count": len(table),
                    "pages_visited": pages_visited,
                    "navigation_log": navigation_log,
                    "extraction_metadata": {
                        "source_type": "url_with_navigation",
                        "extraction_method": f"playwright_navigation+{llm_provider}",
                        "starting_url": url
                    }
                }
            else:
                logger.warning("⚠️ No data extracted during navigation")
                return {
                    "success": False,
                    "table": [],
                    "columns": [],
                    "row_count": 0,
                    "pages_visited": pages_visited,
                    "navigation_log": navigation_log,
                    "error": "No data extracted",
                    "extraction_metadata": {}
                }

        except Exception as e:
            logger.error(f"❌ Navigation extraction failed: {str(e)}", exc_info=True)
            return {
                "success": False,
                "table": [],
                "columns": [],
                "row_count": 0,
                "pages_visited": pages_visited,
                "error": str(e),
                "extraction_metadata": {}
            }

    async def _extract_from_page(
        self,
        page,
        user_instructions: str,
        llm_provider: str
    ) -> List[Dict[str, Any]]:
        """Extract data from current page state"""
        try:
            # Primary: Use Playwright's built-in text extraction (most reliable)
            text_content = await page.inner_text("body")

            # If Playwright extraction is empty or very short, try trafilatura as fallback
            if len(text_content.strip()) < 100:
                logger.info("🔄 Playwright text too short, trying trafilatura fallback...")
                try:
                    import trafilatura
                    content = await page.content()
                    trafilatura_text = trafilatura.extract(content)
                    if trafilatura_text and len(trafilatura_text) > len(text_content):
                        text_content = trafilatura_text
                        logger.info(f"✅ Using trafilatura text ({len(text_content)} chars)")
                except Exception as e:
                    logger.debug(f"Trafilatura extraction failed: {e}")

            logger.info(f"📝 Extracted {len(text_content)} characters of text for LLM")

            # Extract using LLM
            extracted_data = await self._llm_extract_fields(
                text_content, user_instructions, llm_provider
            )

            # Return as list (single row)
            return [extracted_data] if extracted_data else []

        except Exception as e:
            logger.error(f"❌ Page extraction failed: {str(e)}")
            return []

    async def _execute_navigation_action(self, page, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single navigation action"""
        action_type = action.get("type")
        log_entry = {"action": action_type, "status": "pending"}

        try:
            if action_type == "click":
                selector = action.get("selector")
                logger.info(f"🖱️  Clicking: {selector}")
                await page.click(selector, timeout=action.get("timeout", 5000))
                log_entry["status"] = "success"
                log_entry["selector"] = selector

            elif action_type == "scroll":
                direction = action.get("direction", "down")
                amount = action.get("amount", 1000)
                logger.info(f"📜 Scrolling {direction} by {amount}px")

                if amount == "bottom":
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                elif direction == "down":
                    await page.evaluate(f"window.scrollBy(0, {amount})")
                elif direction == "up":
                    await page.evaluate(f"window.scrollBy(0, -{amount})")

                log_entry["status"] = "success"
                log_entry["direction"] = direction
                log_entry["amount"] = amount

            elif action_type == "wait":
                selector = action.get("selector")
                timeout = action.get("timeout", 5000)
                logger.info(f"⏳ Waiting for: {selector}")
                await page.wait_for_selector(selector, timeout=timeout)
                log_entry["status"] = "success"
                log_entry["selector"] = selector

            elif action_type == "input":
                selector = action.get("selector")
                value = action.get("value", "")
                logger.info(f"⌨️  Inputting '{value}' into {selector}")
                await page.fill(selector, value)
                log_entry["status"] = "success"
                log_entry["selector"] = selector
                log_entry["value"] = value

            elif action_type == "wait_for_load":
                logger.info("⏳ Waiting for network idle...")
                await page.wait_for_load_state("networkidle")
                log_entry["status"] = "success"

            else:
                logger.warning(f"⚠️ Unknown action type: {action_type}")
                log_entry["status"] = "unknown"

            return log_entry

        except Exception as e:
            logger.error(f"❌ Action '{action_type}' failed: {str(e)}")
            log_entry["status"] = "failed"
            log_entry["error"] = str(e)
            return log_entry

    async def _handle_pagination(
        self,
        page,
        pagination_config: Dict[str, Any],
        user_instructions: str,
        llm_provider: str,
        max_pages_global: int,
        current_page_count: int
    ) -> Dict[str, Any]:
        """Handle pagination and extract data from each page"""
        next_selector = pagination_config.get("next_selector", ".next")
        max_pages_local = pagination_config.get("max_pages", 10)
        max_pages = min(max_pages_local, max_pages_global)

        all_data = []
        log = []
        pages_visited = 0

        logger.info(f"📄 Starting pagination (max {max_pages} pages, selector: '{next_selector}')")

        for page_num in range(2, max_pages + 1):  # Start from 2 (page 1 already extracted)
            if current_page_count + pages_visited >= max_pages_global:
                logger.warning(f"⚠️ Reached global max pages limit ({max_pages_global})")
                break

            try:
                # Check if next button exists
                next_button = await page.query_selector(next_selector)
                if not next_button:
                    logger.info(f"📄 No more pages ('{next_selector}' not found)")
                    log.append({"action": "pagination_end", "reason": "no_next_button", "page": page_num})
                    break

                # Check if next button is disabled
                is_disabled = await next_button.get_attribute("disabled")
                if is_disabled:
                    logger.info(f"📄 Next button disabled, pagination complete")
                    log.append({"action": "pagination_end", "reason": "button_disabled", "page": page_num})
                    break

                # Click next
                logger.info(f"🖱️  Clicking next page ({page_num}/{max_pages})...")
                await page.click(next_selector, timeout=5000)
                await page.wait_for_load_state("networkidle", timeout=10000)
                pages_visited += 1

                log.append({"action": "next_page", "page": page_num, "status": "success"})

                # Extract data from this page
                page_data = await self._extract_from_page(page, user_instructions, llm_provider)
                if page_data:
                    all_data.extend(page_data)
                    logger.info(f"✅ Extracted {len(page_data)} rows from page {page_num}")
                else:
                    logger.warning(f"⚠️ No data extracted from page {page_num}")

                # Small delay to be respectful
                await asyncio.sleep(0.5)

            except Exception as e:
                logger.error(f"❌ Pagination failed at page {page_num}: {str(e)}")
                log.append({"action": "pagination_error", "page": page_num, "error": str(e)})
                break

        logger.info(f"✅ Pagination complete: {pages_visited} additional pages visited")

        return {
            "data": all_data,
            "log": log,
            "pages_visited": pages_visited
        }

    async def _scroll_to_bottom(self, page):
        """Scroll to bottom of page to trigger lazy loading"""
        try:
            last_height = await page.evaluate("document.body.scrollHeight")

            while True:
                # Scroll down
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(1)

                # Check if new content loaded
                new_height = await page.evaluate("document.body.scrollHeight")
                if new_height == last_height:
                    break

                last_height = new_height

            logger.info("✅ Scrolled to bottom, all lazy content loaded")

        except Exception as e:
            logger.error(f"❌ Scroll to bottom failed: {str(e)}")

    async def _check_if_requires_navigation(self, user_instructions: str) -> bool:
        """
        Check if user instructions require website navigation

        Returns True if instructions contain phrases like:
        - "navigate to...", "go to...", "find...", "under..."
        - "category X", "section X", "page X"
        - Multiple steps implied (e.g., "get all books under Fantasy")

        Examples that require navigation:
        - "get all books under Fantasy" -> True
        - "navigate to Mystery section and extract books" -> True
        - "find products in Electronics category" -> True

        Examples that DON'T require navigation:
        - "extract all books from this page" -> False
        - "get book title and price" -> False
        """
        instructions_lower = user_instructions.lower()

        # Navigation keywords - using only action verbs and generic patterns
        navigation_keywords = [
            # Explicit navigation phrases
            'under', 'in category', 'in section',
            'navigate to', 'go to', 'find',
            'click', 'menu', 'link to',
            'section', 'tab',

            # Action verbs for retrieval (generic - work with any content type)
            'get all', 'fetch all', 'extract all',
            'get the', 'fetch the', 'extract the',
            'retrieve all', 'collect all', 'gather all',
            'list all', 'show all', 'display all',

            # Category/section indicators
            'category', 'from category',
            'from section', 'from the',
            'in the', 'within',

            # Action verbs that imply navigation (no hardcoded item types)
            'browse', 'explore', 'search for',
            'look for', 'show me', 'give me',
            'find all', 'list', 'display'
        ]

        # Check if any navigation keyword is present
        for keyword in navigation_keywords:
            if keyword in instructions_lower:
                logger.info(f"🔍 Detected navigation keyword: '{keyword}'")
                return True

        # Additional pattern matching for "get/fetch/extract [category] [anything]"
        # This catches patterns like "get mystery books", "fetch electronics products", etc.
        # Pattern: action verb + word + word (where second word is the target item)
        import re
        category_item_pattern = r'\b(get|fetch|extract|show|give|find|retrieve|collect|gather|list)\s+\w+\s+\w+'
        if re.search(category_item_pattern, instructions_lower):
            logger.info(f"🔍 Detected action+category+item pattern in: '{user_instructions}'")
            return True

        return False
