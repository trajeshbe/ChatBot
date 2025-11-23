"""
Tool Registry

Central registry for all AI agent tools. Manages tool discovery,
registration, and invocation for the multi-tool agent.
"""

from typing import Dict, List, Any, Optional, Callable, Awaitable
from dataclasses import dataclass, field
import logging
import httpx
import json


logger = logging.getLogger(__name__)


@dataclass
class Tool:
    """
    Represents a single tool available to the agent

    Attributes:
        tool_id: Unique identifier for the tool
        name: Human-readable name
        description: Detailed description for LLM tool selection
        function: Async callable that executes the tool
        input_schema: JSON schema defining tool parameters
        tags: List of tags for categorization and search
        source: Source of the tool (built-in, mcp, custom)
        enabled: Whether the tool is currently enabled
    """
    tool_id: str
    name: str
    description: str
    function: Callable[..., Awaitable[Any]]
    input_schema: Dict[str, Any]
    tags: List[str] = field(default_factory=list)
    source: str = "built-in"
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_openai_function(self) -> Dict[str, Any]:
        """
        Convert tool to OpenAI function calling format

        Returns:
            Dict compatible with OpenAI function calling API
        """
        return {
            "type": "function",
            "function": {
                "name": self.tool_id,
                "description": self.description,
                "parameters": self.input_schema
            }
        }


class ToolRegistry:
    """
    Central registry for all agent tools

    Manages registration, discovery, and invocation of tools including:
    - Built-in tools (RAG, Smart Extraction, etc.)
    - MCP server tools (dynamically discovered)
    - Custom tools (user-defined)
    """

    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        self._register_builtin_tools()
        logger.info("ToolRegistry initialized")

    def _register_builtin_tools(self):
        """Register all built-in tools from existing services"""

        # Document RAG
        self.register(
            tool_id="document_rag",
            name="Document RAG Retrieval",
            description=(
                "Search uploaded documents using semantic similarity to answer questions. "
                "Best for: answering questions from your document library, finding information "
                "in previously uploaded PDFs/docs, retrieving context from knowledge base. "
                "Input: natural language question. "
                "Output: answer with source citations."
            ),
            function=self._wrap_document_rag,
            input_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The question to answer from documents"
                    },
                    "session_id": {
                        "type": "string",
                        "description": "Session ID for document scope (optional)"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of chunks to retrieve (default: 5)",
                        "default": 5
                    }
                },
                "required": ["query"]
            },
            tags=["documents", "search", "rag", "knowledge base"]
        )

        # Smart Web Extraction
        self.register(
            tool_id="smart_extraction",
            name="Smart Web Extraction",
            description=(
                "Extract structured data from any web page using AI-powered extraction. "
                "Handles dynamic content, JavaScript sites, and complex layouts. "
                "Best for: scraping websites, extracting tables/lists from web pages, "
                "getting specific data from URLs. "
                "Input: URL and extraction instructions. "
                "Output: structured data (table/JSON)."
            ),
            function=self._wrap_smart_extraction,
            input_schema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to extract data from"
                    },
                    "user_instructions": {
                        "type": "string",
                        "description": "Specific instructions on what to extract (e.g., 'extract all product prices')"
                    },
                    "llm_provider": {
                        "type": "string",
                        "description": "LLM provider to use (default: openai)",
                        "enum": ["openai", "anthropic"],
                        "default": "openai"
                    }
                },
                "required": ["url", "user_instructions"]
            },
            tags=["web scraping", "data extraction", "url", "ai extraction"]
        )

        # General Web Scraper
        self.register(
            tool_id="web_scraper",
            name="General Web Scraper",
            description=(
                "Basic web scraping using Playwright browser automation. "
                "Best for: simple page scraping, downloading web content, "
                "capturing screenshots, accessing JavaScript-heavy sites. "
                "Input: URL. "
                "Output: HTML content or screenshot."
            ),
            function=self._wrap_web_scraper,
            input_schema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to scrape"
                    },
                    "wait_for": {
                        "type": "string",
                        "description": "CSS selector to wait for before scraping (optional)"
                    }
                },
                "required": ["url"]
            },
            tags=["web scraping", "playwright", "browser automation"]
        )

        # Template Extraction
        self.register(
            tool_id="template_extraction",
            name="Template-Based Extraction",
            description=(
                "Extract data using predefined templates for known website structures. "
                "Best for: extracting from websites you've defined templates for, "
                "structured data extraction with high accuracy. "
                "Input: URL and template name. "
                "Output: structured data according to template."
            ),
            function=self._wrap_template_extraction,
            input_schema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to extract data from"
                    },
                    "template_name": {
                        "type": "string",
                        "description": "Name of the template to use (optional)"
                    }
                },
                "required": ["url"]
            },
            tags=["web scraping", "template", "structured data"]
        )

        # Docling PDF Processing
        self.register(
            tool_id="docling_pdf",
            name="Advanced PDF Processing",
            description=(
                "Extract text and structure from PDF documents using Docling. "
                "Handles complex PDFs with tables, images, and multi-column layouts. "
                "Best for: extracting from PDFs, research papers, forms. "
                "Input: PDF file path or URL. "
                "Output: structured markdown text with preserved formatting."
            ),
            function=self._wrap_docling_pdf,
            input_schema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to PDF file or URL"
                    },
                    "extract_tables": {
                        "type": "boolean",
                        "description": "Whether to extract tables separately",
                        "default": True
                    }
                },
                "required": ["file_path"]
            },
            tags=["pdf", "document processing", "extraction"]
        )

        # OCR for Images
        self.register(
            tool_id="ocr",
            name="Optical Character Recognition",
            description=(
                "Extract text from images using OCR (Tesseract). "
                "Best for: extracting text from screenshots, scanned documents, images. "
                "Input: image file path or URL. "
                "Output: extracted text."
            ),
            function=self._wrap_ocr,
            input_schema={
                "type": "object",
                "properties": {
                    "image_path": {
                        "type": "string",
                        "description": "Path to image file or URL"
                    },
                    "language": {
                        "type": "string",
                        "description": "OCR language (default: eng)",
                        "default": "eng"
                    }
                },
                "required": ["image_path"]
            },
            tags=["ocr", "image", "text extraction"]
        )

        # Navigation Agent
        self.register(
            tool_id="navigation_agent",
            name="Multi-Page Web Navigator",
            description=(
                "Navigate through multiple web pages to collect data. "
                "Uses AI to understand navigation patterns and follow links. "
                "Best for: scraping websites with pagination, following navigation menus, "
                "collecting data across multiple related pages. "
                "Input: starting URL and navigation instructions. "
                "Output: aggregated data from all visited pages."
            ),
            function=self._wrap_navigation_agent,
            input_schema={
                "type": "object",
                "properties": {
                    "start_url": {
                        "type": "string",
                        "description": "Starting URL for navigation"
                    },
                    "navigation_instructions": {
                        "type": "string",
                        "description": "Instructions for what to extract and where to navigate"
                    },
                    "max_pages": {
                        "type": "integer",
                        "description": "Maximum number of pages to visit (default: 10)",
                        "default": 10
                    }
                },
                "required": ["start_url", "navigation_instructions"]
            },
            tags=["web scraping", "navigation", "multi-page", "ai"]
        )

        logger.info(f"Registered {len(self.tools)} built-in tools")

    def register(
        self,
        tool_id: str,
        name: str,
        description: str,
        function: Callable,
        input_schema: Dict[str, Any],
        tags: List[str] = None,
        source: str = "built-in",
        enabled: bool = True,
        metadata: Dict[str, Any] = None
    ):
        """
        Register a new tool

        Args:
            tool_id: Unique identifier
            name: Human-readable name
            description: Detailed description for LLM
            function: Async function to execute
            input_schema: JSON schema for parameters
            tags: Categorization tags
            source: Tool source (built-in, mcp, custom)
            enabled: Whether tool is active
            metadata: Additional tool metadata
        """
        if tool_id in self.tools:
            logger.warning(f"Tool {tool_id} already registered, overwriting")

        tool = Tool(
            tool_id=tool_id,
            name=name,
            description=description,
            function=function,
            input_schema=input_schema,
            tags=tags or [],
            source=source,
            enabled=enabled,
            metadata=metadata or {}
        )

        self.tools[tool_id] = tool
        logger.info(f"Registered tool: {tool_id} ({name})")

    def get_tool(self, tool_id: str) -> Optional[Tool]:
        """Get a specific tool by ID"""
        return self.tools.get(tool_id)

    def get_all_tools(self, enabled_only: bool = True) -> List[Tool]:
        """
        Get all registered tools

        Args:
            enabled_only: Only return enabled tools

        Returns:
            List of Tool objects
        """
        tools = list(self.tools.values())

        if enabled_only:
            tools = [t for t in tools if t.enabled]

        return tools

    def get_tools_by_tag(self, tag: str, enabled_only: bool = True) -> List[Tool]:
        """
        Get tools by tag

        Args:
            tag: Tag to filter by
            enabled_only: Only return enabled tools

        Returns:
            List of matching Tool objects
        """
        tools = self.get_all_tools(enabled_only=enabled_only)
        return [t for t in tools if tag in t.tags]

    def get_tools_for_llm(self, enabled_only: bool = True) -> List[Dict[str, Any]]:
        """
        Get tools in OpenAI function calling format

        This format is used by LLM to select appropriate tools.

        Args:
            enabled_only: Only return enabled tools

        Returns:
            List of tool definitions in OpenAI format
        """
        tools = self.get_all_tools(enabled_only=enabled_only)
        return [tool.to_openai_function() for tool in tools]

    def disable_tool(self, tool_id: str):
        """Disable a tool (make it unavailable to agent)"""
        if tool_id in self.tools:
            self.tools[tool_id].enabled = False
            logger.info(f"Disabled tool: {tool_id}")

    def enable_tool(self, tool_id: str):
        """Enable a tool"""
        if tool_id in self.tools:
            self.tools[tool_id].enabled = True
            logger.info(f"Enabled tool: {tool_id}")

    async def execute_tool(
        self,
        tool_id: str,
        parameters: Dict[str, Any]
    ) -> Any:
        """
        Execute a tool with given parameters

        Args:
            tool_id: ID of tool to execute
            parameters: Tool parameters

        Returns:
            Tool execution result

        Raises:
            ValueError: If tool not found or disabled
            Exception: Any error from tool execution
        """
        tool = self.get_tool(tool_id)

        if not tool:
            raise ValueError(f"Tool not found: {tool_id}")

        if not tool.enabled:
            raise ValueError(f"Tool is disabled: {tool_id}")

        logger.info(f"Executing tool: {tool_id} with params: {parameters}")

        try:
            result = await tool.function(**parameters)
            logger.info(f"Tool {tool_id} executed successfully")
            return result

        except Exception as e:
            logger.error(f"Tool {tool_id} execution failed: {e}")
            raise

    # ========================================================================
    # Compliance Checking Helper
    # ========================================================================

    async def _check_scraping_compliance(self, url: str) -> Dict[str, Any]:
        """
        Check if scraping is allowed for a given URL

        Args:
            url: URL to check compliance for

        Returns:
            Dict with 'allowed' boolean and optional 'reason' for denial
        """
        try:
            from app.services.scraping_config_service import scraping_config_service
            from app.core.database import AsyncSessionLocal

            async with AsyncSessionLocal() as db:
                compliance_result = await scraping_config_service.check_scraping_allowed(db, url)
                return compliance_result

        except Exception as e:
            logger.error(f"Compliance check failed for {url}: {e}")
            # Fail-safe: allow scraping if compliance check fails
            return {
                "allowed": True,
                "reason": f"Compliance check error: {str(e)}"
            }

    async def _log_blocked_scraping_attempt(
        self,
        url: str,
        tool_id: str,
        reason: str,
        session_id: Optional[str] = None
    ):
        """
        Log a blocked scraping attempt to audit log

        Args:
            url: URL that was blocked
            tool_id: Tool that attempted the scrape
            reason: Reason for blocking
            session_id: Optional session ID
        """
        try:
            from app.services.scraping_config_service import scraping_config_service
            from app.core.database import AsyncSessionLocal

            async with AsyncSessionLocal() as db:
                await scraping_config_service.log_scraping_attempt(
                    db=db,
                    url=url,
                    method=tool_id,
                    success=False,
                    error_message=reason,
                    robots_txt_allowed=True,  # Blocked by policy, not robots.txt
                    session_id=session_id
                )
        except Exception as e:
            logger.error(f"Failed to log blocked scraping attempt: {e}")

    # ========================================================================
    # Tool Wrapper Functions
    # ========================================================================

    async def _wrap_document_rag(
        self,
        query: str,
        session_id: Optional[str] = None,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Wrapper for Document RAG service

        Calls the RAG service to query uploaded documents.
        """
        from app.services.rag_service import rag_service
        from app.core.database import AsyncSessionLocal

        async with AsyncSessionLocal() as db:
            result = await rag_service.query(
                query_text=query,
                conversation_history=[],
                use_cache=True,
                db=db
            )

        return {
            "answer": result.get("answer", ""),
            "sources": result.get("sources", []),
            "model_used": result.get("model_used", ""),
            "metadata": {
                "chunks_retrieved": len(result.get("sources", [])),
                "cache_hit": result.get("cache_hit", False)
            }
        }

    async def _wrap_smart_extraction(
        self,
        url: str,
        user_instructions: str,
        llm_provider: str = "openai"
    ) -> Dict[str, Any]:
        """
        Wrapper for Smart Web Extraction

        Calls the ultra-smart extraction endpoint to extract data from websites.
        """
        try:
            # Call the extraction API with increased timeout for complex sites
            async with httpx.AsyncClient(timeout=180.0) as client:
                response = await client.post(
                    "http://localhost:8000/api/v1/extract/ultra-smart",
                    json={
                        "url": url,
                        "user_instructions": user_instructions,
                        "source_type": "url",
                        "llm_provider": llm_provider
                    }
                )

                response.raise_for_status()
                data = response.json()

            # Check if extraction was successful
            if not data.get("success", False):
                error_msg = data.get("error", "Unknown extraction error")
                logger.warning(f"Smart extraction failed for {url}: {error_msg}")

            return {
                "success": data.get("success", False),
                "table": data.get("table", []),
                "columns": data.get("columns", []),
                "row_count": data.get("row_count", 0),
                "extraction_metadata": data.get("extraction_metadata", {}),
                "error": data.get("error"),
                "data": data.get("table", [])  # Also return data for easy access
            }

        except httpx.TimeoutException as e:
            logger.error(f"Smart extraction timeout for {url}: {e}")
            return {
                "success": False,
                "table": [],
                "columns": [],
                "row_count": 0,
                "extraction_metadata": {},
                "error": f"Extraction timeout after 180 seconds: {str(e)}"
            }

        except httpx.HTTPStatusError as e:
            logger.error(f"Smart extraction HTTP error for {url}: {e}")
            return {
                "success": False,
                "table": [],
                "columns": [],
                "row_count": 0,
                "extraction_metadata": {},
                "error": f"HTTP error {e.response.status_code}: {str(e)}"
            }

        except Exception as e:
            logger.error(f"Smart extraction failed for {url}: {e}")
            return {
                "success": False,
                "table": [],
                "columns": [],
                "row_count": 0,
                "extraction_metadata": {},
                "error": f"Extraction error: {str(e)}"
            }

    async def _wrap_web_scraper(
        self,
        url: str,
        wait_for: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Wrapper for General Web Scraper

        Uses Playwright to scrape web pages.
        """
        # ============================================================
        # SCRAPING COMPLIANCE CHECK - Check configured policies
        # ============================================================
        compliance_check = await self._check_scraping_compliance(url)

        if not compliance_check.get('allowed', False):
            error_msg = compliance_check.get('reason', 'Scraping not allowed for this domain')

            # Log the blocked attempt
            await self._log_blocked_scraping_attempt(
                url=url,
                tool_id="web_scraper",
                reason=error_msg,
                session_id=None  # Could be passed from context if available
            )

            logger.warning(f"🚫 Web scraping blocked by compliance: {error_msg}")

            return {
                "html": "",
                "text": "",
                "metadata": {},
                "success": False,
                "error": error_msg
            }

        logger.info(f"✅ Compliance check passed for {url}")

        # Proceed with scraping if allowed
        from app.services.scraper_service import scraper_service
        from app.core.database import AsyncSessionLocal

        async with AsyncSessionLocal() as db:
            result = await scraper_service.scrape_url(
                url=url,
                scrape_prompt=f"Wait for: {wait_for}" if wait_for else None,
                db=db
            )

        return {
            "html": result.get("html", ""),
            "text": result.get("text", ""),
            "metadata": result.get("metadata", {}),
            "success": result.get("success", False)
        }

    async def _wrap_template_extraction(
        self,
        url: str,
        template_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Wrapper for Template-Based Extraction

        Uses predefined templates to extract data from websites.
        """
        # Call the template extraction API
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "http://localhost:8000/api/v1/extract/template",
                json={
                    "url": url,
                    "template_name": template_name
                }
            )

            response.raise_for_status()
            data = response.json()

        return {
            "success": data.get("success", False),
            "table": data.get("table", []),
            "columns": data.get("columns", []),
            "row_count": data.get("row_count", 0),
            "metadata": data.get("metadata", {})
        }

    async def _wrap_docling_pdf(
        self,
        file_path: str,
        extract_tables: bool = True
    ) -> Dict[str, Any]:
        """
        Wrapper for Docling PDF Processing

        Extracts text and structure from PDFs using Docling.
        """
        try:
            from docling.document_converter import DocumentConverter
            import requests
            import tempfile
            import os

            converter = DocumentConverter()

            # Download if URL
            if file_path.startswith("http"):
                response = requests.get(file_path, timeout=30)
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(response.content)
                    temp_path = tmp.name
            else:
                temp_path = file_path

            # Convert with Docling
            result = converter.convert(temp_path)
            markdown_text = result.document.export_to_markdown()

            # Extract tables if requested
            tables = []
            if extract_tables and hasattr(result.document, 'tables'):
                tables = result.document.tables

            # Cleanup
            if file_path.startswith("http"):
                os.unlink(temp_path)

            return {
                "success": True,
                "markdown": markdown_text,
                "tables": tables,
                "text_length": len(markdown_text),
                "metadata": {
                    "source": file_path,
                    "extraction_method": "docling"
                }
            }

        except Exception as e:
            logger.error(f"Docling PDF extraction failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "markdown": "",
                "tables": []
            }

    async def _wrap_ocr(
        self,
        image_path: str,
        language: str = "eng"
    ) -> Dict[str, Any]:
        """
        Wrapper for OCR (Optical Character Recognition)

        Extracts text from images using Tesseract.
        """
        try:
            import pytesseract
            from PIL import Image
            import requests
            import tempfile
            import os

            # Download if URL
            if image_path.startswith("http"):
                response = requests.get(image_path, timeout=30)
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                    tmp.write(response.content)
                    temp_path = tmp.name
            else:
                temp_path = image_path

            # Open image and run OCR
            image = Image.open(temp_path)
            text = pytesseract.image_to_string(image, lang=language)

            # Cleanup
            if image_path.startswith("http"):
                os.unlink(temp_path)

            return {
                "success": True,
                "text": text,
                "text_length": len(text),
                "metadata": {
                    "source": image_path,
                    "language": language,
                    "extraction_method": "tesseract_ocr"
                }
            }

        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "text": ""
            }

    async def _wrap_navigation_agent(
        self,
        start_url: str,
        navigation_instructions: str,
        max_pages: int = 10
    ) -> Dict[str, Any]:
        """
        Wrapper for Navigation Agent

        Navigates through multiple pages using AI guidance.
        """
        # Call the ultra-smart extraction with navigation
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                "http://localhost:8000/api/v1/extract/ultra-smart",
                json={
                    "url": start_url,
                    "user_instructions": navigation_instructions,
                    "source_type": "url",
                    "llm_provider": "openai",
                    "model_id": "gpt-4-turbo"
                }
            )

            response.raise_for_status()
            data = response.json()

        return {
            "success": data.get("success", False),
            "table": data.get("table", []),
            "row_count": data.get("row_count", 0),
            "extraction_metadata": data.get("extraction_metadata", {}),
            "pages_visited": data.get("extraction_metadata", {}).get("metadata", {}).get("steps_taken", 1)
        }


# Global registry instance
tool_registry = ToolRegistry()
