"""
Task Router - Intelligent Query and Document Routing System

Analyzes incoming requests and routes them to optimal tools based on:
- File types attached (PDF, images, Excel, etc.)
- Query complexity (simple Q&A vs complex analysis)
- System resources (memory, GPU availability)
- Tool capabilities and fallback chains
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
import re
import mimetypes
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class FileType(str, Enum):
    """Detected file types"""
    PDF = "pdf"
    IMAGE = "image"
    EXCEL = "excel"
    WORD = "word"
    TEXT = "text"
    JSON = "json"
    UNKNOWN = "unknown"


class QueryComplexity(str, Enum):
    """Query complexity levels"""
    SIMPLE = "simple"          # Simple Q&A, fact lookup
    MODERATE = "moderate"      # Analysis, comparison
    COMPLEX = "complex"        # Multi-step reasoning, synthesis
    ANALYTICAL = "analytical"  # Data analysis, visualization


@dataclass
class RoutingDecision:
    """Routing decision with tool selection and fallback chain"""
    primary_tool: str
    fallback_chain: List[str]
    tool_params: Dict[str, Any]
    reasoning: str
    estimated_memory_mb: int
    requires_gpu: bool
    file_types: List[FileType]
    complexity: QueryComplexity


class TaskRouter:
    """
    Intelligent task routing based on query and document analysis

    Routes tasks to optimal tools with fallback chains:
    - PDF documents → docling_pdf → document_rag → ocr (if scanned)
    - Images → vision_analysis → ocr
    - Excel files → analyze_excel_workbook → document_rag
    - Simple Q&A → document_rag
    - Complex analysis → enhanced_rag_agent with multi-tool
    """

    def __init__(self):
        """Initialize task router with tool configurations"""

        # Tool memory requirements (MB)
        self.tool_memory_requirements = {
            "vision_analysis": 5100,      # LLaMA 3.2 Vision 11B
            "docling_pdf": 500,            # Docling processing
            "ocr": 200,                    # Tesseract/EasyOCR
            "document_rag": 100,           # Vector search
            "analyze_excel_workbook": 300, # Pandas analysis
            "smart_extraction": 400,       # Web scraping with LLM
            "compress_text_for_llm": 50    # Text compression
        }

        # Tool fallback chains by file type
        # PHILOSOPHY: Local tools first (CPU-only), LLM vision LAST resort
        # Based on resource-constrained-agentic-workflow best practices:
        # - PREPROCESSING OVER INFERENCE: Use regex, heuristics, traditional tools BEFORE LLM
        # - LLM = last resort, not first choice
        # - Extract first with local tools, then augment LLM with extracted data

        self.fallback_chains = {
            FileType.PDF: [
                "docling_pdf",      # Primary: Advanced PDF processing (CPU-only, 500MB)
                "ocr",             # Fallback 1: OCR for scanned PDFs (CPU/GPU-light, 200MB)
                "document_rag",     # Fallback 2: RAG search if already indexed (CPU-only, 100MB)
                "vision_analysis"   # Fallback 3: Vision LLM (GPU-heavy, 5100MB) - LAST RESORT
            ],
            FileType.IMAGE: [
                "ocr",             # Primary: OCR for text extraction (CPU/GPU-light, 200MB)
                "document_rag",     # Fallback 1: RAG if image is indexed (CPU-only, 100MB)
                "vision_analysis"   # Fallback 2: Vision LLM (GPU-heavy, 5100MB) - LAST RESORT
            ],
            FileType.EXCEL: [
                "analyze_excel_workbook",  # Primary: Excel analyzer (CPU-only, 300MB)
                "document_rag",            # Fallback: RAG search
            ],
            FileType.WORD: [
                "document_rag",    # Primary: RAG search (CPU-only, 100MB)
                "ocr"              # Fallback: OCR if complex layout (CPU/GPU-light, 200MB)
            ],
            FileType.TEXT: [
                "document_rag"     # Primary: RAG search (CPU-only, 100MB)
            ],
            FileType.JSON: [
                "document_rag"     # Primary: RAG search (CPU-only, 100MB)
            ]
        }

        # Complexity indicators
        self.complexity_patterns = {
            QueryComplexity.SIMPLE: [
                r'\b(what is|who is|when|where|define|explain)\b',
                r'\b(list|show me|tell me about)\b'
            ],
            QueryComplexity.MODERATE: [
                r'\b(compare|contrast|difference between|similar to)\b',
                r'\b(summarize|overview|main points)\b'
            ],
            QueryComplexity.COMPLEX: [
                r'\b(analyze|evaluate|assess|critique)\b',
                r'\b(how to|steps to|process for|workflow)\b',
                r'\b(design|plan|strategy|approach)\b'
            ],
            QueryComplexity.ANALYTICAL: [
                r'\b(calculate|compute|measure|quantify)\b',
                r'\b(visualize|plot|chart|graph)\b',
                r'\b(correlation|trend|pattern|insight)\b',
                r'\b(statistics|statistical|regression|model)\b'
            ]
        }

        logger.info("TaskRouter initialized with tool configurations")

    def detect_file_types(self, documents: List[Dict[str, Any]]) -> List[FileType]:
        """
        Detect file types from document metadata

        Args:
            documents: List of document dicts with filename/file_type

        Returns:
            List of detected FileType enums
        """
        detected_types = []

        for doc in documents:
            filename = doc.get('filename', '')
            file_type = doc.get('file_type', '')
            mime_type = doc.get('mime_type', '')

            # Check file extension
            ext = Path(filename).suffix.lower() if filename else ''

            if ext in ['.pdf'] or 'pdf' in file_type.lower():
                detected_types.append(FileType.PDF)
            elif ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff'] or 'image' in file_type.lower():
                detected_types.append(FileType.IMAGE)
            elif ext in ['.xlsx', '.xls', '.csv'] or 'excel' in file_type.lower() or 'spreadsheet' in file_type.lower():
                detected_types.append(FileType.EXCEL)
            elif ext in ['.docx', '.doc'] or 'word' in file_type.lower():
                detected_types.append(FileType.WORD)
            elif ext in ['.txt', '.md', '.text']:
                detected_types.append(FileType.TEXT)
            elif ext in ['.json']:
                detected_types.append(FileType.JSON)
            else:
                # Try to detect from mime type
                if mime_type:
                    if 'pdf' in mime_type:
                        detected_types.append(FileType.PDF)
                    elif 'image' in mime_type:
                        detected_types.append(FileType.IMAGE)
                    elif 'excel' in mime_type or 'spreadsheet' in mime_type:
                        detected_types.append(FileType.EXCEL)
                    elif 'word' in mime_type or 'msword' in mime_type:
                        detected_types.append(FileType.WORD)
                    else:
                        detected_types.append(FileType.UNKNOWN)
                else:
                    detected_types.append(FileType.UNKNOWN)

        # Remove duplicates while preserving order
        seen = set()
        unique_types = []
        for ft in detected_types:
            if ft not in seen:
                seen.add(ft)
                unique_types.append(ft)

        return unique_types

    async def analyze_query_complexity_llm(self, query: str) -> QueryComplexity:
        """
        Analyze query complexity using LLM (intelligent classification)

        Args:
            query: User's query text

        Returns:
            QueryComplexity enum
        """
        try:
            from app.services.llm_service import llm_service

            # Use lightweight local model for classification (fast, no cost)
            classification_prompt = f"""Classify the complexity of this user query into ONE of these categories:

SIMPLE: Basic questions, fact lookup, simple Q&A
- Examples: "What is X?", "Who is Y?", "Define Z", "List the items"

MODERATE: Comparisons, summaries, multi-part questions
- Examples: "Compare X and Y", "Summarize the document", "What are the main points?"

COMPLEX: Multi-step reasoning, analysis, evaluation, workflows
- Examples: "Analyze the data and provide insights", "How would you approach this?", "Design a solution for..."

ANALYTICAL: Data analysis, calculations, visualizations, statistical queries
- Examples: "Calculate the correlation", "Plot a graph showing X vs Y", "What's the trend?"

User Query: "{query}"

Respond with ONLY ONE WORD: SIMPLE, MODERATE, COMPLEX, or ANALYTICAL"""

            # Call LLM (using local Ollama for speed)
            result = await llm_service.generate(
                prompt=classification_prompt,
                model_id="qwen2.5:1.5b",  # Fast, lightweight model
                temperature=0.1,  # Low temperature for consistent classification
                max_tokens=10
            )

            classification = result.get("content", "").strip().upper()

            # Map to enum
            complexity_map = {
                "SIMPLE": QueryComplexity.SIMPLE,
                "MODERATE": QueryComplexity.MODERATE,
                "COMPLEX": QueryComplexity.COMPLEX,
                "ANALYTICAL": QueryComplexity.ANALYTICAL
            }

            complexity = complexity_map.get(classification, QueryComplexity.SIMPLE)
            logger.info(f"🤖 LLM classified query complexity: {complexity.value} (raw: {classification})")
            return complexity

        except Exception as e:
            logger.warning(f"LLM complexity classification failed: {e}. Falling back to keyword-based.")
            return self.analyze_query_complexity_fallback(query)

    async def analyze_query_complexity(self, query: str) -> QueryComplexity:
        """
        Analyze query complexity (tries LLM first, falls back to keywords)

        Args:
            query: User's query text

        Returns:
            QueryComplexity enum
        """
        try:
            # Try LLM-based classification first
            return await self.analyze_query_complexity_llm(query)
        except Exception as e:
            logger.warning(f"LLM classification failed, using keyword-based: {e}")
            return self.analyze_query_complexity_fallback(query)

    def analyze_query_complexity_fallback(self, query: str) -> QueryComplexity:
        """
        Fallback: Analyze query complexity based on keywords (if LLM fails)

        Args:
            query: User's query text

        Returns:
            QueryComplexity enum
        """
        query_lower = query.lower()

        # Check patterns in order of complexity (highest first)
        for complexity, patterns in reversed(list(self.complexity_patterns.items())):
            for pattern in patterns:
                if re.search(pattern, query_lower, re.IGNORECASE):
                    logger.info(f"Query complexity detected (fallback): {complexity.value} (matched: {pattern})")
                    return complexity

        # Default to SIMPLE if no patterns match
        return QueryComplexity.SIMPLE

    async def analyze_query_content_llm(self, query: str) -> Dict[str, Any]:
        """
        Analyze query content using LLM to detect visual keywords and tool requirements

        Uses local Ollama (qwen2.5:1.5b) to intelligently detect when queries
        mention visual content like diagrams, charts, images, etc.

        Args:
            query: User's query text

        Returns:
            Dict with:
                - requires_vision: bool - whether vision tools are needed
                - suggested_tools: List[str] - recommended tools
                - confidence: float - confidence score
                - reasoning: str - explanation
        """
        try:
            from app.services.llm_service import llm_service

            # Structured prompt for content analysis
            analysis_prompt = f"""Analyze this query and determine if it requires visual content analysis tools.

Query: "{query}"

Visual content indicators:
- Mentions of: diagram, chart, figure, image, graph, table, drawing, illustration
- Mentions of: blueprint, schematic, floor plan, map, screenshot, photo, picture
- Mentions of: scanned document, scan, visual, shown in image

Respond with ONLY a JSON object (no markdown, no code blocks):
{{
    "requires_vision": true/false,
    "suggested_tools": ["tool_name"],
    "confidence": 0.0 to 1.0,
    "reasoning": "brief explanation"
}}

Tool options:
- vision_analysis: For analyzing diagrams, charts, images, visual content
- ocr: For extracting text from scanned documents or images
- document_rag: For searching uploaded text documents
- docling_pdf: For advanced PDF processing

If query mentions visual content → requires_vision=true, suggest vision_analysis or ocr
Otherwise → requires_vision=false, suggest document_rag"""

            # Use ultra-fast Qwen 1.5B model
            result = await llm_service.generate(
                prompt=analysis_prompt,
                max_tokens=200,
                temperature=0.1,  # Low temperature for consistent analysis
                model_id="qwen2.5:1.5b"  # Same model as query classification
            )

            # Extract and parse response
            response_text = result.get('content', '').strip()
            if response_text.startswith('```'):
                lines = response_text.split('\n')
                response_text = '\n'.join(lines[1:-1]) if len(lines) > 2 else response_text
                response_text = response_text.replace('```json', '').replace('```', '').strip()

            analysis = json.loads(response_text)

            # Validate response
            required_fields = {'requires_vision', 'suggested_tools', 'confidence', 'reasoning'}
            if not all(field in analysis for field in required_fields):
                raise ValueError(f"Missing required fields in analysis response")

            logger.info(
                f"🤖 LLM content analysis: requires_vision={analysis['requires_vision']}, "
                f"tools={analysis['suggested_tools']}, confidence={analysis['confidence']:.2f}"
            )

            return analysis

        except Exception as e:
            logger.warning(f"LLM content analysis failed: {e}. Using fallback.")
            # Fallback to simple keyword detection
            query_lower = query.lower()
            visual_keywords = [
                'diagram', 'chart', 'figure', 'image', 'graph', 'table',
                'drawing', 'illustration', 'blueprint', 'schematic', 'floor plan',
                'map', 'screenshot', 'photo', 'picture', 'scanned', 'scan', 'visual'
            ]

            requires_vision = any(keyword in query_lower for keyword in visual_keywords)

            return {
                "requires_vision": requires_vision,
                "suggested_tools": ["vision_analysis", "document_rag"] if requires_vision else ["document_rag"],
                "confidence": 0.7 if requires_vision else 0.8,
                "reasoning": f"Fallback keyword detection - found visual keywords" if requires_vision else "No visual keywords detected"
            }

    def check_system_resources(self) -> Dict[str, Any]:
        """
        Check available system resources

        Returns:
            Dict with available_memory_mb, has_gpu, etc.
        """
        import psutil

        # Get available memory
        memory = psutil.virtual_memory()
        available_mb = memory.available / (1024 * 1024)

        # Check if GPU is available (placeholder - could check nvidia-smi)
        has_gpu = False  # TODO: Implement actual GPU detection

        return {
            "available_memory_mb": available_mb,
            "total_memory_mb": memory.total / (1024 * 1024),
            "memory_percent_used": memory.percent,
            "has_gpu": has_gpu
        }

    def select_tools_for_file_type(
        self,
        file_type: FileType,
        available_memory_mb: float,
        query_complexity: QueryComplexity
    ) -> Tuple[str, List[str]]:
        """
        Select primary tool and fallback chain for file type

        Args:
            file_type: Detected file type
            available_memory_mb: Available system memory
            query_complexity: Query complexity level

        Returns:
            Tuple of (primary_tool, fallback_chain)
        """
        # Get default fallback chain
        fallback_chain = self.fallback_chains.get(file_type, ["document_rag"])

        # Filter tools by memory requirements
        available_tools = [
            tool for tool in fallback_chain
            if self.tool_memory_requirements.get(tool, 0) <= available_memory_mb
        ]

        if not available_tools:
            logger.warning(
                f"No tools available for {file_type.value} with {available_memory_mb:.0f}MB memory. "
                f"Using document_rag as fallback."
            )
            return "document_rag", ["document_rag"]

        # Select primary tool (first available)
        primary_tool = available_tools[0]

        # Special cases based on complexity
        if query_complexity == QueryComplexity.ANALYTICAL:
            # For analytical queries, prefer tools that can extract structured data
            if file_type == FileType.EXCEL and "analyze_excel_workbook" in available_tools:
                primary_tool = "analyze_excel_workbook"
            elif file_type == FileType.PDF and "docling_pdf" in available_tools:
                primary_tool = "docling_pdf"

        return primary_tool, available_tools

    async def route(
        self,
        query: str,
        documents: Optional[List[Dict[str, Any]]] = None,
        session_id: Optional[str] = None,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> RoutingDecision:
        """
        Route task to optimal tool with fallback chain

        Args:
            query: User's query
            documents: List of documents attached (with metadata)
            session_id: Session ID for context
            user_preferences: User preferences (includes strategy_weights and multi_tool_weights)

        Returns:
            RoutingDecision with primary tool, fallbacks, and reasoning
        """
        logger.info(f"🎯 TaskRouter: Analyzing query and {len(documents or [])} documents")

        # Extract user-configured weights (these should OVERRIDE LLM content analysis)
        strategy_weights = user_preferences.get('strategy_weights', {}) if user_preferences else {}
        multi_tool_weights = user_preferences.get('multi_tool_weights', {}) if user_preferences else {}

        # Tool weight mappings (map frontend weight names to backend tool names)
        # Priority: strategy_weights.tool_X (frontend slider) > multi_tool_weights.X (legacy)
        tool_weight_map = {
            'navigation_agent': strategy_weights.get('tool_navigation', multi_tool_weights.get('navigation_agent', 0.0)),
            'smart_extraction': strategy_weights.get('tool_web_scraping', multi_tool_weights.get('smart_extraction', 0.0)),
            'template_extraction': multi_tool_weights.get('template_extraction', 0.0),
            'vision_analysis': multi_tool_weights.get('vision_analysis', 0.0),
            'ocr': strategy_weights.get('tool_ocr', 0.0),
            'docling_pdf': strategy_weights.get('tool_docling', 0.0),
            'document_rag': strategy_weights.get('rag_hybrid', 0.25),  # Default RAG weight
        }

        logger.info(f"⚖️  User-configured tool weights: {tool_weight_map}")

        # Find highest weighted tool (user's explicit preference)
        max_weight_tool = max(tool_weight_map.items(), key=lambda x: x[1])
        user_preferred_tool, user_weight = max_weight_tool

        # Analyze query complexity
        complexity = await self.analyze_query_complexity(query)
        logger.info(f"📊 Query complexity: {complexity.value}")

        # Detect file types
        file_types = self.detect_file_types(documents or [])
        logger.info(f"📄 Detected file types: {[ft.value for ft in file_types]}")

        # Check system resources
        resources = self.check_system_resources()
        available_memory = resources["available_memory_mb"]
        logger.info(f"💾 Available memory: {available_memory:.0f} MB ({resources['memory_percent_used']:.1f}% used)")

        # 🎯 ROUTING DECISION LOGIC:
        # Priority 1: User-configured weights > 0.5 (explicit user preference - HIGHEST PRIORITY)
        # Priority 2: LLM content analysis (intelligent query understanding)
        # Priority 3: File type-based routing (default fallback)

        if user_weight > 0.5:
            # User has explicitly configured a tool weight > 0.5
            # This overrides ALL other routing logic (including LLM content analysis)
            logger.info(f"✅ USER PREFERENCE OVERRIDE: {user_preferred_tool} (weight: {user_weight:.2f})")

            primary_tool = user_preferred_tool

            # Build appropriate fallback chain based on user's preferred tool
            if user_preferred_tool == 'navigation_agent':
                fallback_chain = ['navigation_agent', 'smart_extraction', 'document_rag']
            elif user_preferred_tool == 'smart_extraction':
                fallback_chain = ['smart_extraction', 'navigation_agent', 'document_rag']
            elif user_preferred_tool == 'template_extraction':
                fallback_chain = ['template_extraction', 'smart_extraction', 'document_rag']
            elif user_preferred_tool == 'vision_analysis':
                fallback_chain = ['vision_analysis', 'ocr', 'document_rag']
            elif user_preferred_tool == 'ocr':
                fallback_chain = ['ocr', 'vision_analysis', 'document_rag']
            elif user_preferred_tool == 'docling_pdf':
                fallback_chain = ['docling_pdf', 'ocr', 'document_rag']
            else:
                fallback_chain = ['document_rag']

            reasoning = (
                f"User explicitly configured {user_preferred_tool} with weight {user_weight:.2f} (> 0.5 threshold). "
                f"Respecting user preference over content analysis."
            )

        else:
            # User has NOT set strong preference (weight <= 0.5)
            # Use intelligent LLM content analysis
            logger.info("🔍 Analyzing query intent with LLM (user weight <= 0.5)")
            content_analysis = await self.analyze_query_content_llm(query)

            # Determine primary tool and fallback chain based on QUERY INTENT
            if content_analysis["requires_vision"]:
                # 👁️ VISUAL QUERY DETECTED - prioritize vision_analysis
                logger.info(f"👁️ Visual query detected: {content_analysis['reasoning']} (confidence: {content_analysis['confidence']:.2f})")

                primary_tool = "vision_analysis"

                # Build fallback chain: vision first, then document-specific tools
                if file_types and file_types != [FileType.UNKNOWN]:
                    # Documents attached - add document-specific tools to fallback
                    doc_tools = []
                    for file_type in file_types:
                        _, file_tools = self.select_tools_for_file_type(file_type, available_memory, complexity)
                        # Add all tools from the fallback chain (not just primary)
                        for tool in file_tools:
                            if tool not in doc_tools and tool != "vision_analysis":
                                doc_tools.append(tool)

                    # Vision first, then document tools, then general RAG
                    fallback_chain = ["vision_analysis"] + doc_tools + ["document_rag"]
                    # Remove duplicates while preserving order
                    seen = set()
                    fallback_chain = [x for x in fallback_chain if not (x in seen or seen.add(x))]

                    reasoning = (
                        f"Visual query detected: {content_analysis['reasoning']}. "
                        f"Files: {[ft.value for ft in file_types]}. "
                        f"Using vision_analysis → {' → '.join(doc_tools)} → document_rag"
                    )
                else:
                    # No documents - vision analysis with RAG fallback
                    fallback_chain = ["vision_analysis", "document_rag"]
                    reasoning = (
                        f"Visual query detected: {content_analysis['reasoning']}. "
                        f"No attachments. Using vision_analysis → document_rag"
                    )

            else:
                # 📚 TEXT-BASED QUERY - use document-specific tools or RAG
                logger.info(f"📚 Text-based query detected (confidence: {content_analysis['confidence']:.2f})")

                if not file_types or file_types == [FileType.UNKNOWN]:
                    # No documents - use general RAG
                    primary_tool = "document_rag"
                    fallback_chain = ["document_rag"]
                    reasoning = (
                        f"Text-based query, no attachments. "
                        f"Using document_rag (confidence: {content_analysis['confidence']:.2f})"
                    )
                    logger.info(f"📚 No files - using document_rag")

                elif len(file_types) == 1:
                    # Single file type - optimize for that type
                    file_type = file_types[0]
                    primary_tool, fallback_chain = self.select_tools_for_file_type(
                        file_type, available_memory, complexity
                    )
                    reasoning = (
                        f"Text-based query with {file_type.value} file. "
                        f"Using {primary_tool} (memory: {self.tool_memory_requirements.get(primary_tool, 0)}MB)"
                    )
                    logger.info(f"📄 Single {file_type.value} - using {primary_tool}")

                else:
                    # Multiple file types - use comprehensive tool
                    primary_tool = "document_rag"

                    # Build combined fallback chain
                    all_tools = []
                    for ft in file_types:
                        tools, _ = self.select_tools_for_file_type(ft, available_memory, complexity)
                        if tools not in all_tools:
                            all_tools.append(tools)

                    fallback_chain = all_tools if all_tools else ["document_rag"]
                    reasoning = (
                        f"Text-based query with multiple file types: {[ft.value for ft in file_types]}. "
                        f"Using document_rag → {' → '.join(all_tools)}"
                    )
                    logger.info(f"📚 Multiple files - using document_rag with fallbacks")

        # Build tool parameters
        # Note: file_types is NOT passed to tool_params as it's not a parameter
        # accepted by the RAG tool wrapper. It's metadata for routing decision only.
        tool_params = {
            "query": query,
            "session_id": session_id,
            "complexity": complexity.value,
            "available_memory_mb": available_memory
        }

        # Merge user preferences
        if user_preferences:
            tool_params.update(user_preferences)

        # Create routing decision
        decision = RoutingDecision(
            primary_tool=primary_tool,
            fallback_chain=fallback_chain,
            tool_params=tool_params,
            reasoning=reasoning,
            estimated_memory_mb=self.tool_memory_requirements.get(primary_tool, 100),
            requires_gpu=primary_tool == "vision_analysis",
            file_types=file_types,
            complexity=complexity
        )

        logger.info(
            f"✅ Routing decision:\n"
            f"   Primary: {decision.primary_tool}\n"
            f"   Fallback: {' → '.join(decision.fallback_chain)}\n"
            f"   Reason: {decision.reasoning}"
        )

        return decision


# Global singleton instance
task_router = TaskRouter()
