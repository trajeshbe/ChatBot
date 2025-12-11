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
                        "description": "LLM provider to use (default: ollama)",
                        "enum": ["openai", "anthropic", "ollama"],
                        "default": "ollama"
                    },
                    "model_id": {
                        "type": "string",
                        "description": "Model ID to use for extraction (default: qwen2.5:1.5b)",
                        "default": "qwen2.5:1.5b"
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

        # Vision Language Model (Superior to OCR)
        self.register(
            tool_id="vision_analysis",
            name="Vision Language Model Analysis",
            description=(
                "Analyze images using advanced vision-language AI (LLaMA 3.2 Vision 11B). "
                "SUPERIOR to OCR for: construction drawings, floor plans, architectural diagrams, "
                "handwritten notes, complex layouts, spatial understanding, and visual reasoning. "
                "Can answer questions about images: count floors, measure dimensions, identify building types, "
                "extract Gross Floor Area (GFA), understand construction specifications. "
                "Best for: architectural drawings, construction documents, building plans, technical diagrams, "
                "engineering schematics, scanned blueprints, mixed text/image documents. "
                "Input: image/PDF path and optional question. "
                "Output: detailed visual analysis with text extraction and spatial understanding."
            ),
            function=self._wrap_vision_analysis,
            input_schema={
                "type": "object",
                "properties": {
                    "image_path": {
                        "type": "string",
                        "description": "Path to image file, PDF, or URL (supports PNG, JPG, PDF)"
                    },
                    "question": {
                        "type": "string",
                        "description": "Specific question about the image (e.g., 'How many floors?', 'What is the GFA?'). If omitted, provides general description and text extraction."
                    }
                },
                "required": ["image_path"]
            },
            tags=["vision", "image analysis", "construction drawings", "floor plans", "architectural", "pdf analysis"]
        )

        # Construction Metrics Extraction (NEW)
        self.register(
            tool_id="construction_extraction",
            name="Construction Metrics Extraction",
            description=(
                "Extract building metrics from construction project ZIP files. "
                "Analyzes architectural drawings, DA approvals, site photos, and specifications using Vision LLM + CLIP + OCR. "
                "Extracts: Levels (Above/Below Ground), Gross Floor Area (GFA), External Area, Site Area, Building Height. "
                "Best for: construction tender analysis, project sizing, building metric extraction, Australian civil projects. "
                "Input: ZIP file containing construction documents (PDFs, images). "
                "Output: Structured JSON with metrics, confidence scores, and source attribution. "
                "Returns 'NA' for metrics that cannot be extracted."
            ),
            function=self._wrap_construction_extraction,
            input_schema={
                "type": "object",
                "properties": {
                    "zip_file_path": {
                        "type": "string",
                        "description": "Path to uploaded ZIP file containing construction documents"
                    },
                    "project_name": {
                        "type": "string",
                        "description": "Project name (optional, extracted from ZIP filename if not provided)"
                    },
                    "session_id": {
                        "type": "string",
                        "description": "Session ID for tracking"
                    },
                    "model_id": {
                        "type": "string",
                        "description": "Vision LLM model to use (default: llama3.2-vision:11b)",
                        "default": "llama3.2-vision:11b"
                    }
                },
                "required": ["zip_file_path", "session_id"]
            },
            tags=["construction", "metrics", "extraction", "drawings", "tender", "building", "GFA", "levels", "architectural"]
        )

        # Text Compression for Small LLMs
        self.register(
            tool_id="compress_text_for_llm",
            name="Text Compression for Small LLMs",
            description=(
                "Compress text to fit within a small LLM's context window. "
                "Automatically detects model's context window size and applies "
                "intelligent compression while preserving key information. "
                "Use this before calling small LLMs (LLaMA, Qwen, Mistral) with large inputs. "
                "Best for: preparing prompts for small models, compressing long documents, "
                "fitting large context into limited token budgets. "
                "Input: text and target model name. "
                "Output: compressed text that fits within model's context window."
            ),
            function=self._wrap_text_compression,
            input_schema={
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
                        "description": "Compression method to use. 'smart' is recommended for preserving structure",
                        "default": "smart"
                    }
                },
                "required": ["text", "model_name"]
            },
            tags=["llm", "optimization", "compression", "context-window", "small-models"]
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
                    },
                    "llm_provider": {
                        "type": "string",
                        "description": "LLM provider to use (default: ollama)",
                        "enum": ["openai", "anthropic", "ollama"],
                        "default": "ollama"
                    },
                    "model_id": {
                        "type": "string",
                        "description": "Model ID to use for navigation (default: qwen2.5:1.5b)",
                        "default": "qwen2.5:1.5b"
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
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None,
        min_similarity_threshold: Optional[float] = None,
        no_relevant_docs_threshold: Optional[float] = None,
        semantic_weight: Optional[float] = None,
        keyword_weight: Optional[float] = None,
        model_id: Optional[str] = None,  # 🆕 Accept model_id for model selection
        project_id: Optional[str] = None,  # 🆕 Accept project_id for project-based filtering
        db = None,  # 🆕 Accept optional db session (reuse if provided)
        # Accept but ignore other routing metadata that may be passed
        complexity: Optional[str] = None,  # From TaskRouter
        available_memory_mb: Optional[int] = None,  # From TaskRouter
        **kwargs  # Catch any other unexpected parameters
    ) -> Dict[str, Any]:
        """
        Wrapper for Document RAG service

        Calls the RAG service to query uploaded documents.

        FIXED: Now properly passes all threshold and weight parameters from UI.
        🆕 FIXED: Accepts model_id and db parameters for model selection
        🆕 FIXED: Accepts project_id for project-based document filtering
        🆕 FIXED: Accepts and ignores routing metadata (complexity, available_memory_mb)
                 to prevent parameter mismatch errors
        """
        from app.services.rag_service import rag_service
        from app.core.database import AsyncSessionLocal

        # 🎚️ Extract unified_config from kwargs to pass to RAG service
        unified_config = kwargs.get('unified_config')

        # Use provided db session or create new one
        if db is None:
            async with AsyncSessionLocal() as db:
                result = await rag_service.query(
                    query_text=query,
                    session_id=session_id,
                    conversation_history=[],
                    use_cache=True,
                    model_id=model_id,  # 🆕 Pass model_id for model selection
                    project_id=project_id,  # 🆕 Pass project_id for project-based filtering
                    unified_config=unified_config,  # 🎚️ Pass unified_config for UI override logic
                    top_k=top_k,
                    similarity_threshold=similarity_threshold,
                    min_similarity_threshold=min_similarity_threshold,
                    no_relevant_docs_threshold=no_relevant_docs_threshold,
                    semantic_weight=semantic_weight,
                    keyword_weight=keyword_weight,
                    db=db
                )
        else:
            # Reuse provided db session (already in transaction context)
            result = await rag_service.query(
                query_text=query,
                session_id=session_id,
                conversation_history=[],
                use_cache=True,
                model_id=model_id,  # 🆕 Pass model_id for model selection
                project_id=project_id,  # 🆕 Pass project_id for project-based filtering
                unified_config=unified_config,  # 🎚️ Pass unified_config for UI override logic
                top_k=top_k,
                similarity_threshold=similarity_threshold,
                min_similarity_threshold=min_similarity_threshold,
                no_relevant_docs_threshold=no_relevant_docs_threshold,
                semantic_weight=semantic_weight,
                keyword_weight=keyword_weight,
                db=db
            )

        # 🆕 Preserve ALL metadata from RAG service (including quality_metrics)
        original_metadata = result.get("metadata", {})

        return {
            "answer": result.get("answer", ""),
            "sources": result.get("sources", []),
            "model": result.get("model", "unknown"),  # ✅ Pass through model identifier
            "model_name": result.get("model_name", result.get("model", "unknown")),  # ✅ Pass through model name
            "model_used": result.get("model_used", ""),
            "quality_metrics": result.get("quality_metrics"),  # ✅ Pass through quality_metrics
            "metadata": {
                **original_metadata,  # ✅ Spread original metadata (includes query_classification, etc.)
                "chunks_retrieved": len(result.get("sources", [])),
                "cache_hit": result.get("cache_hit", False),
                "num_sources": result.get("num_sources", 0)
            }
        }

    async def _wrap_smart_extraction(
        self,
        url: str,
        user_instructions: str,
        llm_provider: str = "ollama",
        model_id: str = "qwen2.5:1.5b"
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
                        "llm_provider": llm_provider,
                        "model_id": model_id
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

    async def _wrap_docling_pdf(self, **kwargs) -> Dict[str, Any]:
        """
        Wrapper for Docling PDF Processing

        Extracts text and structure from PDFs using Docling.

        Flexible parameter handling - accepts:
        - query/question: User's question (optional)
        - file_path: Direct path to PDF
        - session_id + db: To auto-discover PDF in session
        - extract_tables: Whether to extract tables (default: True)
        """
        try:
            from docling.document_converter import DocumentConverter
            import requests
            import tempfile
            import os
            from app.models.database import SessionDocument, Document
            from sqlalchemy import select

            # Extract parameters flexibly
            query = kwargs.get('query') or kwargs.get('question', '')
            session_id = kwargs.get('session_id')
            db = kwargs.get('db')
            file_path = kwargs.get('file_path')
            extract_tables = kwargs.get('extract_tables', True)

            # If no direct file_path, try to find PDF in session
            if not file_path and session_id and db:
                result = await db.execute(
                    select(Document)
                    .join(SessionDocument, SessionDocument.document_id == Document.id)
                    .where(SessionDocument.session_id == session_id)
                    .where(Document.file_type == 'pdf')
                    .order_by(Document.upload_date.desc())
                    .limit(1)
                )
                pdf_doc = result.scalar_one_or_none()

                if pdf_doc:
                    file_path = pdf_doc.file_path
                    logger.info(f"📄 Auto-discovered PDF: {pdf_doc.filename}")

            if not file_path:
                return {
                    "success": False,
                    "error": "No PDF file specified or found in session",
                    "text": "",
                    "markdown": "",
                    "tables": []
                }

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

            # If query provided, extract relevant answer
            response_text = markdown_text
            if query and markdown_text:
                # Use the extracted content as context for answering
                response_text = f"Extracted content:\n{markdown_text}"

            return {
                "success": True,
                "text": response_text,
                "markdown": markdown_text,
                "tables": tables,
                "text_length": len(markdown_text),
                "metadata": {
                    "source": file_path,
                    "extraction_method": "docling",
                    "query": query if query else None
                }
            }

        except Exception as e:
            logger.error(f"Docling PDF extraction failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "text": "",
                "markdown": "",
                "tables": []
            }

    async def _wrap_ocr(self, **kwargs) -> Dict[str, Any]:
        """
        Wrapper for OCR (Optical Character Recognition)

        Extracts text from images using Tesseract.

        Flexible parameter handling - accepts:
        - query/question: User's question (optional)
        - image_path/file_path: Direct path to image/PDF
        - session_id + db: To auto-discover image/PDF in session
        - language: OCR language (default: 'eng')
        """
        try:
            import pytesseract
            from PIL import Image
            import requests
            import tempfile
            import os
            from app.models.database import SessionDocument, Document
            from sqlalchemy import select

            # Extract parameters flexibly
            query = kwargs.get('query') or kwargs.get('question', '')
            session_id = kwargs.get('session_id')
            db = kwargs.get('db')
            image_path = kwargs.get('image_path') or kwargs.get('file_path')
            language = kwargs.get('language', 'eng')

            # If no direct image_path, try to find image/PDF in session
            if not image_path and session_id and db:
                result = await db.execute(
                    select(Document)
                    .join(SessionDocument, SessionDocument.document_id == Document.id)
                    .where(SessionDocument.session_id == session_id)
                    .where(Document.file_type.in_(['pdf', 'png', 'jpg', 'jpeg', 'tiff']))
                    .order_by(Document.upload_date.desc())
                    .limit(1)
                )
                doc = result.scalar_one_or_none()

                if doc:
                    image_path = doc.file_path
                    logger.info(f"🖼️ Auto-discovered file for OCR: {doc.filename}")

            if not image_path:
                return {
                    "success": False,
                    "error": "No image/PDF file specified or found in session",
                    "text": ""
                }

            # Download if URL
            if image_path.startswith("http"):
                response = requests.get(image_path, timeout=30)
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                    tmp.write(response.content)
                    temp_path = tmp.name
            else:
                temp_path = image_path

            # If PDF, convert first page to image for OCR
            if temp_path.lower().endswith('.pdf'):
                try:
                    from pdf2image import convert_from_path
                    images = convert_from_path(temp_path, first_page=1, last_page=1)
                    if images:
                        image = images[0]
                    else:
                        raise Exception("Failed to convert PDF to image")
                except ImportError:
                    # Fallback: try to open directly with PIL (works for some PDFs)
                    image = Image.open(temp_path)
            else:
                # Open image and run OCR
                image = Image.open(temp_path)

            text = pytesseract.image_to_string(image, lang=language)

            # Cleanup
            if image_path.startswith("http"):
                os.unlink(temp_path)

            # If query provided, include it in response
            response_text = text
            if query and text:
                response_text = f"OCR extracted text:\n{text}"

            return {
                "success": True,
                "text": response_text,
                "text_length": len(text),
                "metadata": {
                    "source": image_path,
                    "language": language,
                    "extraction_method": "tesseract_ocr",
                    "query": query if query else None
                }
            }

        except Exception as e:
            logger.error(f"OCR extraction failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "text": ""
            }

    async def _wrap_navigation_agent(
        self,
        start_url: str,
        navigation_instructions: str,
        max_pages: int = 10,
        llm_provider: str = "ollama",
        model_id: str = "qwen2.5:1.5b"
    ) -> Dict[str, Any]:
        """
        Wrapper for Navigation Agent

        Navigates through multiple pages using AI guidance.
        """
        import time
        from app.services.tool_usage_tracker import tool_tracker, ToolCategory
        from app.core.database import AsyncSessionLocal
        from app.core.config import settings

        start_time = time.time()

        try:
            # Call the ultra-smart extraction with navigation
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    "http://localhost:8000/api/v1/extract/ultra-smart",
                    json={
                        "url": start_url,
                        "user_instructions": navigation_instructions,
                        "source_type": "url",
                        "llm_provider": llm_provider,
                        "model_id": model_id
                    }
                )

                response.raise_for_status()
                data = response.json()

            processing_time = (time.time() - start_time) * 1000

            # Track navigation_agent tool usage
            try:
                async with AsyncSessionLocal() as track_db:
                    await tool_tracker.record_tool_usage(
                        category=ToolCategory.WEB_SCRAPING,
                        tool_name="navigation_agent",
                        operation="navigate_and_extract",
                        db=track_db,
                        session_id=None,
                        success=data.get("success", False),
                        latency_ms=processing_time,
                        input_size=len(start_url),
                        output_size=data.get("row_count", 0),
                        metadata={
                            'start_url': start_url,
                            'navigation_instructions': navigation_instructions[:200],  # Truncate
                            'max_pages': max_pages,
                            'pages_visited': data.get("extraction_metadata", {}).get("metadata", {}).get("steps_taken", 1),
                            'row_count': data.get("row_count", 0)
                        }
                    )
                    await track_db.commit()
                    logger.info(f"📊 Tool usage tracked: navigation_agent ({processing_time:.2f}ms)")
            except Exception as track_error:
                logger.warning(f"Failed to track navigation_agent usage: {track_error}")

            return {
                "success": data.get("success", False),
                "table": data.get("table", []),
                "row_count": data.get("row_count", 0),
                "extraction_metadata": data.get("extraction_metadata", {}),
                "pages_visited": data.get("extraction_metadata", {}).get("metadata", {}).get("steps_taken", 1)
            }

        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            logger.error(f"Navigation agent failed: {e}")

            # Track failed attempt
            try:
                async with AsyncSessionLocal() as track_db:
                    await tool_tracker.record_tool_usage(
                        category=ToolCategory.WEB_SCRAPING,
                        tool_name="navigation_agent",
                        operation="navigate_and_extract",
                        db=track_db,
                        session_id=None,
                        success=False,
                        latency_ms=processing_time,
                        input_size=len(start_url),
                        output_size=0,
                        metadata={
                            'start_url': start_url,
                            'error': str(e)[:500]
                        }
                    )
                    await track_db.commit()
            except Exception as track_error:
                logger.warning(f"Failed to track failed navigation_agent: {track_error}")

            return {
                "success": False,
                "table": [],
                "row_count": 0,
                "extraction_metadata": {},
                "pages_visited": 0,
                "error": str(e)
            }

    async def _wrap_vision_analysis(
        self,
        image_path: Optional[str] = None,
        question: Optional[str] = None,
        query: Optional[str] = None,
        session_id: Optional[str] = None,
        project_id: Optional[str] = None,
        db: Optional[Any] = None,
        **kwargs  # Accept all extra parameters from TaskRouter
    ) -> Dict[str, Any]:
        """
        Wrapper for Vision Language Model Analysis

        Uses LLaMA 3.2 Vision to analyze images, construction drawings,
        floor plans, and architectural documents.

        Superior to OCR for:
        - Spatial understanding
        - Visual reasoning
        - Counting objects (floors, windows, etc.)
        - Understanding technical drawings
        - Handwritten text

        Args:
            image_path: Path to specific image (optional)
            question: Question about the image (optional)
            query: Alternative to question (for TaskRouter compatibility)
            session_id: Session ID to find documents (optional, legacy)
            project_id: Project ID to find documents (preferred)
            db: Database session (optional)
            **kwargs: Accept extra parameters from TaskRouter
        """
        try:
            from app.services.vision_service import get_vision_service
            import os

            # Extract project_id from kwargs if not explicitly provided
            if not project_id:
                project_id = kwargs.get('project_id')

            # Map query to question if question not provided
            if not question and query:
                question = query

            # If no image_path provided, try to find documents with images
            # Priority: project_id (current) > session_id (legacy)
            if not image_path and db and (project_id or session_id):
                search_scope = f"project {project_id}" if project_id else f"session {session_id}"
                logger.info(f"🔍 No image_path provided, searching for image/PDF documents in {search_scope}")

                try:
                    from app.models.database import SessionDocument, Document
                    from sqlalchemy import select
                    from app.core.config import settings
                    from uuid import UUID

                    # Build query based on available scope (project-based is preferred)
                    if project_id:
                        # PROJECT-BASED: Search documents by project_id directly
                        query_builder = select(Document).where(Document.project_id == UUID(project_id))
                    else:
                        # SESSION-BASED (legacy): Search via SessionDocument join
                        query_builder = (
                            select(Document)
                            .join(SessionDocument, SessionDocument.document_id == Document.id)
                            .where(SessionDocument.session_id == session_id)
                        )

                    # Add file type filters (same for both approaches)
                    # Includes: PDFs, images, Word docs (with diagrams), PowerPoint (with slides/charts)
                    # Note: file_type can be short form ('pdf') or MIME type ('application/pdf')
                    query_builder = query_builder.where(
                        # Short forms
                        (Document.file_type.in_(['pdf', 'image', 'png', 'jpg', 'jpeg', 'docx', 'doc', 'pptx', 'ppt'])) |
                        # MIME types and partial matches
                        (Document.file_type.like('%pdf%')) |
                        (Document.file_type.like('%image%')) |
                        (Document.file_type.like('%png%')) |
                        (Document.file_type.like('%jpg%')) |
                        (Document.file_type.like('%jpeg%')) |
                        (Document.file_type.like('%word%')) |          # application/msword, wordprocessing
                        (Document.file_type.like('%docx%')) |
                        (Document.file_type.like('%doc%')) |
                        (Document.file_type.like('%powerpoint%')) |    # application/vnd.ms-powerpoint
                        (Document.file_type.like('%presentation%')) |  # presentationml
                        (Document.file_type.like('%pptx%')) |
                        (Document.file_type.like('%ppt%'))
                    )

                    # 🎯 FILTER BY FILENAME: If user mentions specific file in their query, prioritize it
                    mentioned_filename = None
                    if question:
                        # Extract potential filename from query (look for file extensions)
                        import re
                        filename_pattern = r'[\w\-\_]+\.(pdf|png|jpg|jpeg|docx|doc|pptx|ppt)'
                        filename_match = re.search(filename_pattern, question, re.IGNORECASE)
                        if filename_match:
                            mentioned_filename = filename_match.group(0)
                            logger.info(f"🎯 User mentioned specific file in query: {mentioned_filename}")
                            # Filter to only that file
                            query_builder = query_builder.where(Document.filename.ilike(f'%{mentioned_filename}%'))

                    # 🔝 PRIORITIZE PDFs: Add ORDER BY to prefer PDFs over DOCX/PPTX (more reliable for vision analysis)
                    from sqlalchemy import case
                    query_builder = query_builder.order_by(
                        case(
                            (Document.file_type == 'pdf', 1),
                            (Document.file_type.like('%pdf%'), 1),
                            (Document.file_type.in_(['png', 'jpg', 'jpeg', 'image']), 2),
                            (Document.file_type.like('%image%'), 2),
                            else_=3  # DOCX, PPTX come last
                        )
                    )

                    result = await db.execute(query_builder)
                    documents = result.scalars().all()

                    if documents:
                        # Use first document (already prioritized by ORDER BY)
                        doc = documents[0]

                        if mentioned_filename:
                            logger.info(f"✅ Found user-requested file: {doc.filename}")
                        else:
                            logger.info(f"📋 {len(documents)} visual documents found, selected: {doc.filename} (prioritized by file type)")

                        # Use minio_path if available, fallback to file_path
                        minio_path = doc.minio_path or doc.file_path
                        image_path = minio_path
                        scope_type = "project" if project_id else "session"
                        logger.info(f"📄 Found visual document in {scope_type}: {doc.filename} ({doc.file_type}) at {minio_path}")
                    else:
                        scope_type = "project" if project_id else "session"
                        logger.warning(f"No image/PDF documents found in {scope_type}")
                        return {
                            "success": False,
                            "error": f"No image or PDF documents found in {scope_type} to analyze",
                            "text": "",
                            "analysis": ""
                        }
                except Exception as e:
                    logger.error(f"Error finding documents: {e}", exc_info=True)
                    return {
                        "success": False,
                        "error": f"Could not find documents to analyze: {str(e)}",
                        "text": "",
                        "analysis": ""
                    }

            if not image_path:
                return {
                    "success": False,
                    "error": "No image_path provided and could not find documents in session",
                    "text": "",
                    "analysis": ""
                }

            vision_service = await get_vision_service()

            # Download from MinIO if needed (before PDF conversion)
            if image_path and not image_path.startswith('/') and not image_path.startswith('http'):
                logger.info(f"🔍 Detected MinIO path: {image_path}, downloading before processing...")
                local_path = await self._download_from_minio(image_path)
                if not local_path:
                    logger.error(f"❌ Failed to download from MinIO: {image_path}")
                    return {
                        "success": False,
                        "error": f"Failed to download file from MinIO: {image_path}",
                        "text": "",
                        "analysis": ""
                    }
                image_path = local_path
                logger.info(f"✅ Using downloaded file: {image_path}")

            # Handle PDF files - need to convert first page to image
            if image_path.lower().endswith('.pdf'):
                logger.info(f"📄 PDF detected: {image_path}, converting to image for vision analysis")

                # Use PyMuPDF (fitz) - already in our stack!
                try:
                    import fitz  # PyMuPDF

                    # Open PDF and convert first page only (construction drawings are typically single-page or page-by-page)
                    doc = fitz.open(image_path)
                    if len(doc) == 0:
                        raise Exception("PDF has no pages")

                    page = doc[0]  # First page

                    # Render page at 150 DPI (balanced quality/performance)
                    mat = fitz.Matrix(150/72, 150/72)
                    pix = page.get_pixmap(matrix=mat)

                    # Save as PNG
                    temp_image_path = f"/tmp/vision_pdf_{os.path.basename(image_path)}.png"
                    pix.save(temp_image_path)
                    doc.close()

                    image_path = temp_image_path
                    logger.info(f"✅ PDF converted to image using PyMuPDF: {temp_image_path}")

                except ImportError:
                    # PyMuPDF not available, try pdf2image as fallback
                    try:
                        from pdf2image import convert_from_path

                        images = convert_from_path(image_path, first_page=1, last_page=1, dpi=150)
                        if images:
                            temp_image_path = f"/tmp/vision_pdf_{os.path.basename(image_path)}.png"
                            images[0].save(temp_image_path, 'PNG')
                            image_path = temp_image_path
                            logger.info(f"✅ PDF converted to image using pdf2image: {temp_image_path}")
                        else:
                            raise Exception("pdf2image failed to convert PDF")
                    except ImportError:
                        raise Exception("Neither PyMuPDF nor pdf2image available")

                except (ImportError, Exception) as e:
                    # 🎯 PARALLEL MULTI-METHOD EXTRACTION with Consolidated Context
                    logger.warning(f"⚠️  PDF vision conversion failed: {e}")
                    logger.info("🚀 Using PARALLEL multi-method extraction for comprehensive PDF analysis")

                    import asyncio
                    import time

                    start_time = time.time()

                    # 🎯 Use TaskRouter's fallback chain if provided (respects user's weights config)
                    fallback_chain = kwargs.get('fallback_chain', ['docling_pdf', 'ocr', 'document_rag'])

                    # Map tool names to extraction methods
                    tool_method_map = {
                        'docling_pdf': lambda: self._extract_with_docling(image_path, question or query, session_id, db),
                        'ocr': lambda: self._extract_with_ocr(image_path, question or query, session_id, db),
                        'document_rag': lambda: self._extract_with_rag(
                            question or query or "Extract all information from this document",
                            session_id,
                            db,
                            top_k=10
                        ),
                        'vision_analysis': None,  # Avoid recursion
                    }

                    # Build extraction tasks from fallback chain (exclude vision_analysis to avoid recursion)
                    extraction_tasks = []
                    tools_used = []
                    for tool in fallback_chain:
                        if tool == 'vision_analysis':
                            continue  # Skip to avoid infinite recursion
                        method = tool_method_map.get(tool)
                        if method:
                            extraction_tasks.append(method())
                            tools_used.append(tool)

                    # Ensure we have at least 1 task
                    if not extraction_tasks:
                        # Fallback to default if fallback_chain is invalid
                        logger.warning("⚠️  Invalid fallback_chain, using defaults")
                        extraction_tasks = [
                            self._extract_with_docling(image_path, question or query, session_id, db),
                            self._extract_with_ocr(image_path, question or query, session_id, db),
                            self._extract_with_rag(
                                question or query or "Extract all information from this document",
                                session_id,
                                db,
                                top_k=10
                            ),
                        ]
                        tools_used = ['docling_pdf', 'ocr', 'document_rag']

                    logger.info(f"🚀 Running {len(extraction_tasks)} extraction methods in PARALLEL: {tools_used}")

                    # ✨ Run ALL methods concurrently using asyncio.gather()
                    results = await asyncio.gather(*extraction_tasks, return_exceptions=True)

                    elapsed = time.time() - start_time
                    logger.info(f"⚡ Parallel extraction completed in {elapsed:.2f}s")

                    # Collect all successful results
                    consolidated_context = []
                    method_names = ["docling_pdf", "ocr", "document_rag"]

                    for i, result in enumerate(results):
                        method_name = method_names[i]

                        if isinstance(result, Exception):
                            logger.warning(f"❌ {method_name} failed: {result}")
                        elif result and result.get('success'):
                            logger.info(f"✅ {method_name} succeeded")
                            consolidated_context.append({
                                "method": method_name,
                                "content": result.get('text') or result.get('answer', ''),
                                "confidence": result.get('confidence', 0.8)
                            })

                    # Build rich consolidated context from all successful extractions
                    if consolidated_context:
                        # Combine all extracted information
                        context_text = "\n\n".join([
                            f"=== {ctx['method'].upper()} EXTRACTION (confidence: {ctx['confidence']}) ===\n{ctx['content']}"
                            for ctx in consolidated_context
                        ])

                        logger.info(f"✅ Parallel extraction successful using {len(consolidated_context)} methods: {[ctx['method'] for ctx in consolidated_context]}")

                        return {
                            "success": True,
                            "text": context_text,
                            "analysis": context_text,
                            "methods_used": [ctx['method'] for ctx in consolidated_context],
                            "num_sources": len(consolidated_context),
                            "parallel_execution_time": elapsed,
                            "metadata": {
                                "extraction_methods": consolidated_context,
                                "approach": "parallel_multi_method_with_consolidated_context"
                            }
                        }
                    else:
                        # All extraction methods failed
                        return {
                            "success": False,
                            "error": f"PDF analysis failed: pdf2image not available and all parallel extraction methods failed (tried: {', '.join(method_names)})",
                            "text": "",
                            "analysis": "",
                            "methods_attempted": len(method_names)
                        }

            # Extract UI-selected model_id from kwargs (passed from TaskRouter)
            model_id = kwargs.get('model_id')

            # Analyze with vision model
            if question:
                # Specific question mode - pass UI-selected model
                logger.info(f"🎯 Calling describe_image with model_id: {model_id}")
                result = await vision_service.describe_image(
                    image_path,
                    question=question,
                    model_id=model_id  # Pass UI-selected model
                )
                text_content = result
            else:
                # General analysis + text extraction mode
                logger.info(f"🎯 Calling vision analysis with model_id: {model_id}")
                result_dict = await vision_service.process_image(
                    image_path,
                    prompt=None,
                    model_id=model_id,  # Pass UI-selected model
                    allow_fallback=True  # Enable Ollama fallback
                )
                text_content = result_dict.get("text", "")

            return {
                "success": True,
                "text": text_content if isinstance(text_content, str) else text_content.get("text", ""),
                "analysis": text_content,
                "model": "llama3.2-vision:11b",
                "metadata": {
                    "source": image_path,
                    "extraction_method": "vision_language_model",
                    "question": question
                }
            }

        except Exception as e:
            logger.error(f"Vision analysis failed for {image_path}: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "text": "",
                "analysis": ""
            }

    # ============================================================================
    # Helper Methods for Parallel Extraction and MinIO File Access
    # ============================================================================

    async def _download_from_minio(self, minio_path: str) -> Optional[str]:
        """
        Download file from MinIO to temporary local path

        Args:
            minio_path: MinIO object path (e.g., 'Technology/Backend-Development/.../file.pdf')

        Returns:
            Local temp file path if successful, None if failed
        """
        try:
            from minio import Minio
            from app.core.config import settings
            import tempfile
            import os

            # Initialize MinIO client
            minio_client = Minio(
                settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_SECURE
            )

            # Extract filename from minio_path
            filename = os.path.basename(minio_path)
            file_ext = os.path.splitext(filename)[1]

            # Create temp file with same extension
            temp_fd, temp_path = tempfile.mkstemp(suffix=file_ext)
            os.close(temp_fd)  # Close fd, MinIO will write to path

            # Download from MinIO
            bucket_name = settings.MINIO_BUCKET_NAME
            logger.info(f"📥 Downloading from MinIO: bucket={bucket_name}, path={minio_path}")

            minio_client.fget_object(
                bucket_name=bucket_name,
                object_name=minio_path,
                file_path=temp_path
            )

            logger.info(f"✅ Downloaded to temp path: {temp_path}")
            return temp_path

        except Exception as e:
            logger.error(f"❌ Failed to download from MinIO: {minio_path} - {e}")
            return None

    async def _extract_with_docling(self, file_path, query, session_id, db):
        """Extract with Docling PDF - handles structured documents"""
        try:
            # Check if file_path is a MinIO path (no leading slash)
            if file_path and not file_path.startswith('/') and not file_path.startswith('http'):
                logger.info(f"🔍 Detected MinIO path for Docling: {file_path}")
                local_path = await self._download_from_minio(file_path)
                if not local_path:
                    return {"success": False, "error": f"Failed to download file from MinIO: {file_path}"}
                file_path = local_path

            result = await self._wrap_docling_pdf(
                file_path=file_path,
                query=query,
                session_id=session_id,
                db=db
            )
            return result
        except Exception as e:
            logger.error(f"Docling extraction error: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def _extract_with_ocr(self, file_path, query, session_id, db):
        """Extract with OCR - handles scanned documents"""
        try:
            # Check if file_path is a MinIO path (no leading slash)
            if file_path and not file_path.startswith('/') and not file_path.startswith('http'):
                logger.info(f"🔍 Detected MinIO path for OCR: {file_path}")
                local_path = await self._download_from_minio(file_path)
                if not local_path:
                    return {"success": False, "error": f"Failed to download file from MinIO: {file_path}"}
                file_path = local_path

            result = await self._wrap_ocr(
                file_path=file_path,
                query=query,
                session_id=session_id,
                db=db
            )
            return result
        except Exception as e:
            logger.error(f"OCR extraction error: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def _extract_with_rag(self, query, session_id, db, top_k=10):
        """Extract with Document RAG - semantic search across chunks"""
        try:
            result = await self._wrap_document_rag(
                query=query,
                session_id=session_id,
                db=db,
                top_k=top_k
            )
            return result
        except Exception as e:
            logger.error(f"RAG extraction error: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def _wrap_text_compression(
        self,
        text: str,
        model_name: str,
        target_tokens: Optional[int] = None,
        compression_method: str = "smart"
    ) -> Dict[str, Any]:
        """
        Wrapper for Text Compression Tool

        Compresses text to fit within small LLM context windows using
        intelligent extractive summarization.

        Returns:
            Dict with compressed text and metadata
        """
        try:
            from app.tools.text_compression_tool import execute_text_compression_tool

            result = await execute_text_compression_tool(
                text=text,
                model_name=model_name,
                target_tokens=target_tokens,
                compression_method=compression_method
            )

            return result

        except Exception as e:
            logger.error(f"Text compression failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "compressed_text": text,  # Return original on failure
                "original_tokens": 0,
                "compressed_tokens": 0,
                "reduction_percentage": 0
            }

    async def _wrap_construction_extraction(
        self,
        zip_file_path: str,
        session_id: str,
        project_name: Optional[str] = None,
        model_id: Optional[str] = None,
        db = None
    ) -> Dict[str, Any]:
        """
        Wrapper for Construction Metrics Extraction Agent

        Extracts building metrics from construction project ZIP files using
        Vision LLM + CLIP + OCR multimodal analysis.

        Args:
            zip_file_path: Path to uploaded ZIP file
            session_id: Session ID for tracking
            project_name: Project name (optional)
            model_id: Vision LLM model to use (default: llama3.2-vision:11b)
            db: Database session (optional)

        Returns:
            Dict with extracted metrics:
            {
                "project_name": str,
                "metrics": {
                    "levels_above_ground": int or "NA",
                    "levels_below_ground": int or "NA",
                    "gross_floor_area_m2": float or "NA",
                    "external_area_m2": float or "NA",
                    "site_area_m2": float or "NA",
                    "building_height_m": float or "NA"
                },
                "confidence": float,
                "sources": [str],
                "details": {...}
            }
        """
        try:
            from app.agents.construction_metrics import ConstructionMetricsAgent
            from app.services.llm_service import LLMService
            from app.services.hybrid_extraction_service import HybridExtractionService

            logger.info(f"Starting construction metrics extraction for: {zip_file_path}")

            # Initialize services
            llm_service = LLMService()
            vision_service = HybridExtractionService()

            # Create agent
            agent = ConstructionMetricsAgent(
                llm_service=llm_service,
                vision_service=vision_service,
                db=db
            )

            # Extract project name from ZIP if not provided
            if not project_name:
                from pathlib import Path
                project_name = Path(zip_file_path).stem

            # Run extraction
            result = await agent.extract_metrics(
                zip_file_path=zip_file_path,
                project_name=project_name,
                session_id=session_id,
                model_id=model_id
            )

            logger.info(f"Construction metrics extraction complete: {result['metrics']}")

            return {
                "success": True,
                "result": result,
                **result  # Flatten result to top level
            }

        except Exception as e:
            logger.error(f"Construction metrics extraction failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "project_name": project_name or "Unknown",
                "metrics": {
                    "levels_above_ground": "NA",
                    "levels_below_ground": "NA",
                    "gross_floor_area_m2": "NA",
                    "external_area_m2": "NA",
                    "site_area_m2": "NA",
                    "building_height_m": "NA"
                },
                "confidence": 0.0,
                "sources": [],
                "details": {
                    "error": str(e)
                }
            }


# Global registry instance
tool_registry = ToolRegistry()
