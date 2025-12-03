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
                llm_provider="ollama",
                model_id="qwen2.5:1.5b",  # Fast, lightweight model
                temperature=0.1,  # Low temperature for consistent classification
                max_tokens=10
            )

            classification = result.get("text", "").strip().upper()

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
            user_preferences: User preferences

        Returns:
            RoutingDecision with primary tool, fallbacks, and reasoning
        """
        logger.info(f"🎯 TaskRouter: Analyzing query and {len(documents or [])} documents")

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

        # Determine primary tool and fallback chain
        if not file_types or file_types == [FileType.UNKNOWN]:
            # No documents or unknown type → use document_rag
            primary_tool = "document_rag"
            fallback_chain = ["document_rag"]
            reasoning = "No documents attached or unknown file type - using document RAG for knowledge base search"

        elif len(file_types) == 1:
            # Single file type → optimize for that type
            file_type = file_types[0]
            primary_tool, fallback_chain = self.select_tools_for_file_type(
                file_type, available_memory, complexity
            )
            reasoning = (
                f"Single {file_type.value} file detected. "
                f"Using {primary_tool} (memory required: {self.tool_memory_requirements.get(primary_tool, 0)}MB, "
                f"available: {available_memory:.0f}MB)"
            )

        else:
            # Multiple file types → use most comprehensive tool
            primary_tool = "document_rag"

            # Build combined fallback chain
            all_tools = []
            for ft in file_types:
                tools, _ = self.select_tools_for_file_type(ft, available_memory, complexity)
                if tools not in all_tools:
                    all_tools.append(tools)

            fallback_chain = all_tools if all_tools else ["document_rag"]
            reasoning = (
                f"Multiple file types detected: {[ft.value for ft in file_types]}. "
                f"Using document_rag to search across all documents"
            )

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
