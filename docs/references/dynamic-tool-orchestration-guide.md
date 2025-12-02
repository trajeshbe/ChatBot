# Dynamic Tool Orchestration for Resource-Constrained Agentic Systems

## The Core Problem

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              THE TOOL SELECTION CHALLENGE                            │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  You have:                                                                           │
│  ├── OCR Readers (Tesseract, EasyOCR, PaddleOCR)                                    │
│  ├── Document Parsers (Dockling, Unstructured, PyMuPDF)                             │
│  ├── PDF Tools (pdfplumber, pdf2image, camelot)                                     │
│  ├── Vision LLMs (Llama-Vision 8B)                                                  │
│  ├── Text LLMs (Qwen-Coder 7B, Qwen 2.5B)                                          │
│  └── Custom Tools (your registered application tools)                               │
│                                                                                      │
│  The agent needs to:                                                                 │
│  ├── Know what tools exist                                                           │
│  ├── Understand what each tool does                                                  │
│  ├── Choose the RIGHT tool for each task                                            │
│  ├── Handle tool failures gracefully                                                 │
│  └── Chain tools together intelligently                                              │
│                                                                                      │
│  With constraints:                                                                   │
│  ├── 8GB GPU (can't run multiple LLMs)                                              │
│  ├── 16GB CPU RAM                                                                    │
│  └── Small orchestrator model (Qwen 2.5B)                                           │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Architecture Overview: The Tool Orchestration Layer

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                   USER REQUEST                                       │
│                    "Extract floor counts from these PDFs"                           │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              ORCHESTRATOR AGENT                                      │
│                              (Qwen 2.5B - Always Loaded)                            │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │                         TOOL REGISTRY ACCESS                                 │    │
│  │  "I have access to these tools: [list with descriptions]"                   │    │
│  │  "For this task, I should use: ..."                                         │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              TOOL REGISTRY                                           │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐        │
│  │   CATEGORY:   │  │   CATEGORY:   │  │   CATEGORY:   │  │   CATEGORY:   │        │
│  │   PDF_READER  │  │   OCR         │  │   VISION_LLM  │  │   CUSTOM      │        │
│  ├───────────────┤  ├───────────────┤  ├───────────────┤  ├───────────────┤        │
│  │ • pdfplumber  │  │ • tesseract   │  │ • llama_vis   │  │ • your_tool_1 │        │
│  │ • pymupdf     │  │ • easyocr     │  │               │  │ • your_tool_2 │        │
│  │ • dockling    │  │ • paddleocr   │  │               │  │ • your_tool_3 │        │
│  └───────────────┘  └───────────────┘  └───────────────┘  └───────────────┘        │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              TOOL EXECUTOR                                           │
│                    (Handles loading, execution, resource management)                │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Part 1: The Tool Registry System

### Tool Definition Schema

```python
"""
tool_registry.py - Central tool registration and discovery system
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable, Union
from enum import Enum
import json
from abc import ABC, abstractmethod

class ToolCategory(Enum):
    """Tool categories for smart routing"""
    PDF_TEXT_EXTRACT = "pdf_text_extract"
    PDF_TO_IMAGE = "pdf_to_image"
    OCR = "ocr"
    VISION_LLM = "vision_llm"
    TEXT_LLM = "text_llm"
    TABLE_EXTRACT = "table_extract"
    DOCUMENT_PARSE = "document_parse"
    FILE_SYSTEM = "file_system"
    CUSTOM = "custom"

class ResourceRequirement(Enum):
    """Resource requirements for tool selection"""
    CPU_ONLY = "cpu_only"
    GPU_LIGHT = "gpu_light"      # < 2GB VRAM
    GPU_MEDIUM = "gpu_medium"    # 2-4GB VRAM
    GPU_HEAVY = "gpu_heavy"      # 4-8GB VRAM
    EXTERNAL_API = "external_api"

@dataclass
class ToolCapability:
    """What a tool can do"""
    input_types: List[str]       # ["pdf", "image", "text"]
    output_types: List[str]      # ["text", "json", "image"]
    handles_scanned: bool        # Can handle scanned/image PDFs
    handles_tables: bool         # Can extract tables
    handles_handwriting: bool    # Can read handwriting
    accuracy_rating: float       # 0.0 - 1.0
    speed_rating: float          # 0.0 - 1.0 (1.0 = fastest)

@dataclass
class ToolDefinition:
    """Complete tool definition"""
    name: str
    description: str
    category: ToolCategory
    resource_requirement: ResourceRequirement
    capabilities: ToolCapability
    
    # Schema for LLM to understand how to call
    parameters_schema: Dict[str, Any]
    
    # Actual callable or import path
    implementation: Union[Callable, str]
    
    # Dependencies
    requires_models: List[str] = field(default_factory=list)
    conflicts_with: List[str] = field(default_factory=list)
    
    # Runtime info
    is_loaded: bool = False
    avg_execution_time_ms: float = 0
    failure_rate: float = 0
    
    def to_prompt_description(self) -> str:
        """Generate description for LLM prompt"""
        return f"""
Tool: {self.name}
Category: {self.category.value}
Description: {self.description}
Inputs: {', '.join(self.capabilities.input_types)}
Outputs: {', '.join(self.capabilities.output_types)}
Best for: {'scanned docs, ' if self.capabilities.handles_scanned else ''}{'tables, ' if self.capabilities.handles_tables else ''}{'handwriting' if self.capabilities.handles_handwriting else 'digital text'}
Resource: {self.resource_requirement.value}
Parameters: {json.dumps(self.parameters_schema, indent=2)}
"""


class ToolRegistry:
    """
    Central registry for all available tools
    Supports dynamic registration and discovery
    """
    
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self._categories: Dict[ToolCategory, List[str]] = {}
        self._loaded_models: List[str] = []
        
    def register(self, tool: ToolDefinition):
        """Register a new tool"""
        self._tools[tool.name] = tool
        
        if tool.category not in self._categories:
            self._categories[tool.category] = []
        self._categories[tool.category].append(tool.name)
        
        print(f"Registered tool: {tool.name} [{tool.category.value}]")
    
    def register_from_mcp(self, mcp_tool_definition: dict):
        """Register tool from MCP (Model Context Protocol) format"""
        
        # Convert MCP schema to our format
        tool = ToolDefinition(
            name=mcp_tool_definition["name"],
            description=mcp_tool_definition.get("description", ""),
            category=self._infer_category(mcp_tool_definition),
            resource_requirement=ResourceRequirement.CPU_ONLY,  # MCP tools usually external
            capabilities=ToolCapability(
                input_types=self._extract_input_types(mcp_tool_definition),
                output_types=["text", "json"],
                handles_scanned=False,
                handles_tables=False,
                handles_handwriting=False,
                accuracy_rating=0.8,
                speed_rating=0.7
            ),
            parameters_schema=mcp_tool_definition.get("inputSchema", {}),
            implementation=f"mcp://{mcp_tool_definition['name']}"
        )
        
        self.register(tool)
    
    def register_custom_tool(
        self,
        name: str,
        description: str,
        category: str,
        parameters: Dict[str, Any],
        implementation: Callable,
        input_types: List[str] = None,
        output_types: List[str] = None,
        resource: str = "cpu_only"
    ):
        """
        Easy registration for custom tools
        This is what your application would call to register tools
        """
        
        tool = ToolDefinition(
            name=name,
            description=description,
            category=ToolCategory(category) if category in [c.value for c in ToolCategory] else ToolCategory.CUSTOM,
            resource_requirement=ResourceRequirement(resource),
            capabilities=ToolCapability(
                input_types=input_types or ["any"],
                output_types=output_types or ["text"],
                handles_scanned=False,
                handles_tables=False,
                handles_handwriting=False,
                accuracy_rating=0.8,
                speed_rating=0.8
            ),
            parameters_schema=parameters,
            implementation=implementation
        )
        
        self.register(tool)
    
    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """Get tool by name"""
        return self._tools.get(name)
    
    def get_tools_by_category(self, category: ToolCategory) -> List[ToolDefinition]:
        """Get all tools in a category"""
        tool_names = self._categories.get(category, [])
        return [self._tools[name] for name in tool_names]
    
    def get_tools_for_task(
        self,
        input_type: str,
        task_hint: str = None,
        max_resource: ResourceRequirement = ResourceRequirement.GPU_HEAVY
    ) -> List[ToolDefinition]:
        """
        Get tools that can handle a specific input type
        Filtered by resource constraints
        """
        
        resource_order = [
            ResourceRequirement.CPU_ONLY,
            ResourceRequirement.GPU_LIGHT,
            ResourceRequirement.GPU_MEDIUM,
            ResourceRequirement.GPU_HEAVY,
            ResourceRequirement.EXTERNAL_API
        ]
        
        max_idx = resource_order.index(max_resource)
        allowed_resources = set(resource_order[:max_idx + 1])
        
        matching_tools = []
        
        for tool in self._tools.values():
            # Check input type match
            if input_type in tool.capabilities.input_types or "any" in tool.capabilities.input_types:
                # Check resource constraint
                if tool.resource_requirement in allowed_resources:
                    matching_tools.append(tool)
        
        # Sort by accuracy then speed
        matching_tools.sort(
            key=lambda t: (t.capabilities.accuracy_rating, t.capabilities.speed_rating),
            reverse=True
        )
        
        return matching_tools
    
    def generate_tools_prompt(self, categories: List[ToolCategory] = None) -> str:
        """
        Generate a prompt describing available tools for the LLM
        This is how the agent "learns" about tools
        """
        
        prompt_parts = ["# Available Tools\n"]
        
        tools_to_include = []
        if categories:
            for cat in categories:
                tools_to_include.extend(self.get_tools_by_category(cat))
        else:
            tools_to_include = list(self._tools.values())
        
        # Group by category for clarity
        by_category = {}
        for tool in tools_to_include:
            cat = tool.category.value
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(tool)
        
        for category, tools in by_category.items():
            prompt_parts.append(f"\n## {category.upper()}\n")
            for tool in tools:
                prompt_parts.append(tool.to_prompt_description())
        
        return "\n".join(prompt_parts)
    
    def _infer_category(self, mcp_def: dict) -> ToolCategory:
        """Infer category from MCP tool definition"""
        name_lower = mcp_def.get("name", "").lower()
        desc_lower = mcp_def.get("description", "").lower()
        
        if "ocr" in name_lower or "ocr" in desc_lower:
            return ToolCategory.OCR
        elif "pdf" in name_lower:
            return ToolCategory.PDF_TEXT_EXTRACT
        elif "vision" in name_lower or "image" in name_lower:
            return ToolCategory.VISION_LLM
        else:
            return ToolCategory.CUSTOM
    
    def _extract_input_types(self, mcp_def: dict) -> List[str]:
        """Extract input types from MCP schema"""
        schema = mcp_def.get("inputSchema", {})
        properties = schema.get("properties", {})
        
        types = []
        for prop_name, prop_def in properties.items():
            if "file" in prop_name.lower() or "path" in prop_name.lower():
                types.append("file")
            elif "image" in prop_name.lower():
                types.append("image")
            elif "text" in prop_name.lower():
                types.append("text")
        
        return types or ["any"]


# Global registry instance
TOOL_REGISTRY = ToolRegistry()
```

### Registering Built-in Tools

```python
"""
builtin_tools.py - Register all built-in tools
"""

from tool_registry import (
    TOOL_REGISTRY, 
    ToolDefinition, 
    ToolCategory, 
    ResourceRequirement,
    ToolCapability
)

def register_builtin_tools():
    """Register all built-in tools"""
    
    # =========================================
    # PDF TEXT EXTRACTION TOOLS
    # =========================================
    
    TOOL_REGISTRY.register(ToolDefinition(
        name="pymupdf_extract",
        description="Fast PDF text extraction using PyMuPDF. Best for digital PDFs with selectable text. Very fast but cannot handle scanned documents.",
        category=ToolCategory.PDF_TEXT_EXTRACT,
        resource_requirement=ResourceRequirement.CPU_ONLY,
        capabilities=ToolCapability(
            input_types=["pdf"],
            output_types=["text"],
            handles_scanned=False,
            handles_tables=False,
            handles_handwriting=False,
            accuracy_rating=0.95,
            speed_rating=1.0
        ),
        parameters_schema={
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Path to PDF file"},
                "pages": {"type": "array", "items": {"type": "integer"}, "description": "Page numbers to extract (optional, default all)"}
            },
            "required": ["file_path"]
        },
        implementation="tools.pdf.pymupdf_extract"
    ))
    
    TOOL_REGISTRY.register(ToolDefinition(
        name="pdfplumber_extract",
        description="PDF text and table extraction using pdfplumber. Good for structured documents with tables. Slower than PyMuPDF but handles tables well.",
        category=ToolCategory.PDF_TEXT_EXTRACT,
        resource_requirement=ResourceRequirement.CPU_ONLY,
        capabilities=ToolCapability(
            input_types=["pdf"],
            output_types=["text", "json"],
            handles_scanned=False,
            handles_tables=True,
            handles_handwriting=False,
            accuracy_rating=0.90,
            speed_rating=0.7
        ),
        parameters_schema={
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Path to PDF file"},
                "extract_tables": {"type": "boolean", "description": "Also extract tables", "default": False}
            },
            "required": ["file_path"]
        },
        implementation="tools.pdf.pdfplumber_extract"
    ))
    
    TOOL_REGISTRY.register(ToolDefinition(
        name="dockling_parse",
        description="Advanced document parsing using Dockling. Understands document structure, sections, headers. Best for complex documents that need structural understanding.",
        category=ToolCategory.DOCUMENT_PARSE,
        resource_requirement=ResourceRequirement.CPU_ONLY,
        capabilities=ToolCapability(
            input_types=["pdf", "docx", "html"],
            output_types=["json", "markdown"],
            handles_scanned=False,
            handles_tables=True,
            handles_handwriting=False,
            accuracy_rating=0.92,
            speed_rating=0.5
        ),
        parameters_schema={
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Path to document"},
                "output_format": {"type": "string", "enum": ["json", "markdown"], "default": "json"}
            },
            "required": ["file_path"]
        },
        implementation="tools.document.dockling_parse"
    ))
    
    # =========================================
    # PDF TO IMAGE TOOLS
    # =========================================
    
    TOOL_REGISTRY.register(ToolDefinition(
        name="pdf2image_convert",
        description="Convert PDF pages to images. Required before using OCR or Vision LLM on PDFs. Configurable DPI for quality/speed tradeoff.",
        category=ToolCategory.PDF_TO_IMAGE,
        resource_requirement=ResourceRequirement.CPU_ONLY,
        capabilities=ToolCapability(
            input_types=["pdf"],
            output_types=["image"],
            handles_scanned=True,
            handles_tables=False,
            handles_handwriting=False,
            accuracy_rating=1.0,
            speed_rating=0.6
        ),
        parameters_schema={
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Path to PDF file"},
                "dpi": {"type": "integer", "description": "Resolution (72-300)", "default": 150},
                "pages": {"type": "array", "items": {"type": "integer"}, "description": "Pages to convert"},
                "output_dir": {"type": "string", "description": "Output directory for images"}
            },
            "required": ["file_path", "output_dir"]
        },
        implementation="tools.pdf.pdf2image_convert"
    ))
    
    # =========================================
    # OCR TOOLS
    # =========================================
    
    TOOL_REGISTRY.register(ToolDefinition(
        name="tesseract_ocr",
        description="Tesseract OCR for text extraction from images. Good general-purpose OCR, fast, runs on CPU. Works well for printed text.",
        category=ToolCategory.OCR,
        resource_requirement=ResourceRequirement.CPU_ONLY,
        capabilities=ToolCapability(
            input_types=["image"],
            output_types=["text"],
            handles_scanned=True,
            handles_tables=False,
            handles_handwriting=False,
            accuracy_rating=0.80,
            speed_rating=0.8
        ),
        parameters_schema={
            "type": "object",
            "properties": {
                "image_path": {"type": "string", "description": "Path to image file"},
                "language": {"type": "string", "description": "OCR language", "default": "eng"},
                "config": {"type": "string", "description": "Tesseract config options"}
            },
            "required": ["image_path"]
        },
        implementation="tools.ocr.tesseract_ocr"
    ))
    
    TOOL_REGISTRY.register(ToolDefinition(
        name="easyocr_extract",
        description="EasyOCR for text extraction. GPU-accelerated, good for multiple languages and slightly better accuracy than Tesseract. Handles some handwriting.",
        category=ToolCategory.OCR,
        resource_requirement=ResourceRequirement.GPU_LIGHT,
        capabilities=ToolCapability(
            input_types=["image"],
            output_types=["text", "json"],
            handles_scanned=True,
            handles_tables=False,
            handles_handwriting=True,
            accuracy_rating=0.85,
            speed_rating=0.6
        ),
        parameters_schema={
            "type": "object",
            "properties": {
                "image_path": {"type": "string", "description": "Path to image file"},
                "languages": {"type": "array", "items": {"type": "string"}, "default": ["en"]},
                "return_boxes": {"type": "boolean", "description": "Return bounding boxes", "default": False}
            },
            "required": ["image_path"]
        },
        implementation="tools.ocr.easyocr_extract",
        requires_models=["easyocr"]
    ))
    
    TOOL_REGISTRY.register(ToolDefinition(
        name="paddleocr_extract",
        description="PaddleOCR for high-accuracy text extraction. Best accuracy for printed text, excellent for tables and structured layouts. GPU recommended.",
        category=ToolCategory.OCR,
        resource_requirement=ResourceRequirement.GPU_LIGHT,
        capabilities=ToolCapability(
            input_types=["image"],
            output_types=["text", "json"],
            handles_scanned=True,
            handles_tables=True,
            handles_handwriting=False,
            accuracy_rating=0.92,
            speed_rating=0.5
        ),
        parameters_schema={
            "type": "object",
            "properties": {
                "image_path": {"type": "string", "description": "Path to image file"},
                "use_angle_cls": {"type": "boolean", "description": "Detect text angle", "default": True},
                "lang": {"type": "string", "default": "en"}
            },
            "required": ["image_path"]
        },
        implementation="tools.ocr.paddleocr_extract",
        requires_models=["paddleocr"]
    ))
    
    # =========================================
    # TABLE EXTRACTION TOOLS
    # =========================================
    
    TOOL_REGISTRY.register(ToolDefinition(
        name="camelot_tables",
        description="Extract tables from PDFs using Camelot. Best for PDFs with clear table structures. Returns structured data.",
        category=ToolCategory.TABLE_EXTRACT,
        resource_requirement=ResourceRequirement.CPU_ONLY,
        capabilities=ToolCapability(
            input_types=["pdf"],
            output_types=["json", "csv"],
            handles_scanned=False,
            handles_tables=True,
            handles_handwriting=False,
            accuracy_rating=0.88,
            speed_rating=0.6
        ),
        parameters_schema={
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Path to PDF file"},
                "pages": {"type": "string", "description": "Page range e.g. '1-3' or 'all'", "default": "all"},
                "flavor": {"type": "string", "enum": ["lattice", "stream"], "default": "lattice"}
            },
            "required": ["file_path"]
        },
        implementation="tools.tables.camelot_extract"
    ))
    
    # =========================================
    # VISION LLM TOOLS
    # =========================================
    
    TOOL_REGISTRY.register(ToolDefinition(
        name="llama_vision_analyze",
        description="Analyze images using Llama Vision 8B. Best for understanding complex diagrams, architectural drawings, reading annotations. Most powerful but requires GPU and is slow.",
        category=ToolCategory.VISION_LLM,
        resource_requirement=ResourceRequirement.GPU_HEAVY,
        capabilities=ToolCapability(
            input_types=["image"],
            output_types=["text", "json"],
            handles_scanned=True,
            handles_tables=True,
            handles_handwriting=True,
            accuracy_rating=0.95,
            speed_rating=0.2
        ),
        parameters_schema={
            "type": "object",
            "properties": {
                "image_path": {"type": "string", "description": "Path to image file"},
                "prompt": {"type": "string", "description": "Analysis prompt/question"},
                "max_tokens": {"type": "integer", "description": "Max response tokens", "default": 500}
            },
            "required": ["image_path", "prompt"]
        },
        implementation="tools.vision.llama_vision_analyze",
        requires_models=["llama-vision-8b"],
        conflicts_with=["qwen_coder_7b"]  # Can't load both at once
    ))
    
    # =========================================
    # TEXT LLM TOOLS
    # =========================================
    
    TOOL_REGISTRY.register(ToolDefinition(
        name="qwen_coder_extract",
        description="Use Qwen Coder 7B for complex text understanding and extraction. Best for interpreting specifications, generating extraction code, understanding context.",
        category=ToolCategory.TEXT_LLM,
        resource_requirement=ResourceRequirement.GPU_HEAVY,
        capabilities=ToolCapability(
            input_types=["text"],
            output_types=["text", "json", "code"],
            handles_scanned=False,
            handles_tables=False,
            handles_handwriting=False,
            accuracy_rating=0.90,
            speed_rating=0.3
        ),
        parameters_schema={
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to analyze"},
                "prompt": {"type": "string", "description": "Extraction prompt"},
                "output_format": {"type": "string", "enum": ["text", "json"], "default": "text"}
            },
            "required": ["text", "prompt"]
        },
        implementation="tools.llm.qwen_coder_extract",
        requires_models=["qwen-coder-7b"],
        conflicts_with=["llama-vision-8b"]
    ))
    
    TOOL_REGISTRY.register(ToolDefinition(
        name="qwen_small_reason",
        description="Use Qwen 2.5B for light reasoning and orchestration. Fast, always available, good for planning and simple extraction.",
        category=ToolCategory.TEXT_LLM,
        resource_requirement=ResourceRequirement.GPU_LIGHT,
        capabilities=ToolCapability(
            input_types=["text"],
            output_types=["text", "json"],
            handles_scanned=False,
            handles_tables=False,
            handles_handwriting=False,
            accuracy_rating=0.75,
            speed_rating=0.8
        ),
        parameters_schema={
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to process"},
                "prompt": {"type": "string", "description": "Processing prompt"}
            },
            "required": ["text", "prompt"]
        },
        implementation="tools.llm.qwen_small_reason",
        requires_models=["qwen-2.5b"]
    ))
    
    # =========================================
    # FILE SYSTEM TOOLS
    # =========================================
    
    TOOL_REGISTRY.register(ToolDefinition(
        name="list_files",
        description="List files in a directory with optional filtering by extension.",
        category=ToolCategory.FILE_SYSTEM,
        resource_requirement=ResourceRequirement.CPU_ONLY,
        capabilities=ToolCapability(
            input_types=["path"],
            output_types=["json"],
            handles_scanned=False,
            handles_tables=False,
            handles_handwriting=False,
            accuracy_rating=1.0,
            speed_rating=1.0
        ),
        parameters_schema={
            "type": "object",
            "properties": {
                "directory": {"type": "string", "description": "Directory path"},
                "extension": {"type": "string", "description": "Filter by extension (e.g., '.pdf')"},
                "recursive": {"type": "boolean", "default": False}
            },
            "required": ["directory"]
        },
        implementation="tools.filesystem.list_files"
    ))
    
    TOOL_REGISTRY.register(ToolDefinition(
        name="read_file",
        description="Read file contents. Supports text files.",
        category=ToolCategory.FILE_SYSTEM,
        resource_requirement=ResourceRequirement.CPU_ONLY,
        capabilities=ToolCapability(
            input_types=["path"],
            output_types=["text"],
            handles_scanned=False,
            handles_tables=False,
            handles_handwriting=False,
            accuracy_rating=1.0,
            speed_rating=1.0
        ),
        parameters_schema={
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "File path"},
                "encoding": {"type": "string", "default": "utf-8"}
            },
            "required": ["file_path"]
        },
        implementation="tools.filesystem.read_file"
    ))
    
    TOOL_REGISTRY.register(ToolDefinition(
        name="write_file",
        description="Write content to a file.",
        category=ToolCategory.FILE_SYSTEM,
        resource_requirement=ResourceRequirement.CPU_ONLY,
        capabilities=ToolCapability(
            input_types=["text"],
            output_types=["path"],
            handles_scanned=False,
            handles_tables=False,
            handles_handwriting=False,
            accuracy_rating=1.0,
            speed_rating=1.0
        ),
        parameters_schema={
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Output file path"},
                "content": {"type": "string", "description": "Content to write"}
            },
            "required": ["file_path", "content"]
        },
        implementation="tools.filesystem.write_file"
    ))
    
    print(f"Registered {len(TOOL_REGISTRY._tools)} built-in tools")


# Register on import
register_builtin_tools()
```

---

## Part 2: The Smart Tool Router

This is the key component that decides WHICH tool to use for each task.

```python
"""
tool_router.py - Intelligent tool selection without heavy LLM
Uses heuristics + small model for smart routing
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from enum import Enum
import re
import mimetypes
from pathlib import Path

from tool_registry import (
    TOOL_REGISTRY,
    ToolDefinition,
    ToolCategory,
    ResourceRequirement
)

class DocumentType(Enum):
    """Detected document types"""
    DIGITAL_PDF = "digital_pdf"         # PDF with selectable text
    SCANNED_PDF = "scanned_pdf"         # PDF that's actually images
    IMAGE = "image"
    ARCHITECTURAL_DRAWING = "arch_drawing"
    SPREADSHEET = "spreadsheet"
    WORD_DOC = "word_doc"
    TEXT_FILE = "text_file"
    UNKNOWN = "unknown"

@dataclass
class RoutingDecision:
    """Result of tool routing"""
    primary_tool: str
    fallback_tools: List[str]
    preprocessing_tools: List[str]
    confidence: float
    reasoning: str

class SmartToolRouter:
    """
    Routes tasks to appropriate tools using heuristics first,
    LLM only when needed
    """
    
    def __init__(self, registry=TOOL_REGISTRY, max_gpu_memory_gb: float = 8.0):
        self.registry = registry
        self.max_gpu_memory = max_gpu_memory_gb
        
        # Track what's currently loaded
        self.loaded_heavy_model: Optional[str] = None
        
    def route(
        self,
        file_path: str,
        task_type: str,
        context: Dict = None
    ) -> RoutingDecision:
        """
        Main routing logic
        Uses heuristics first, LLM for complex cases
        """
        
        # Step 1: Detect document type
        doc_type = self._detect_document_type(file_path)
        
        # Step 2: Get task requirements
        task_reqs = self._parse_task_requirements(task_type)
        
        # Step 3: Apply routing rules
        decision = self._apply_routing_rules(doc_type, task_reqs, context or {})
        
        # Step 4: Check resource constraints
        decision = self._apply_resource_constraints(decision)
        
        return decision
    
    def _detect_document_type(self, file_path: str) -> DocumentType:
        """
        Detect document type using heuristics
        NO LLM NEEDED - pure Python
        """
        
        path = Path(file_path)
        suffix = path.suffix.lower()
        
        # File extension based detection
        if suffix == ".pdf":
            # Check if digital or scanned
            return self._detect_pdf_type(file_path)
        elif suffix in [".jpg", ".jpeg", ".png", ".tiff", ".bmp"]:
            return self._detect_image_type(file_path)
        elif suffix in [".xlsx", ".xls", ".csv"]:
            return DocumentType.SPREADSHEET
        elif suffix in [".docx", ".doc"]:
            return DocumentType.WORD_DOC
        elif suffix in [".txt", ".md"]:
            return DocumentType.TEXT_FILE
        else:
            return DocumentType.UNKNOWN
    
    def _detect_pdf_type(self, pdf_path: str) -> DocumentType:
        """
        Detect if PDF is digital or scanned
        Uses PyMuPDF - no LLM needed
        """
        
        try:
            import fitz
            doc = fitz.open(pdf_path)
            
            # Sample first 3 pages
            text_chars = 0
            image_area = 0
            total_area = 0
            
            for page_num in range(min(3, len(doc))):
                page = doc[page_num]
                
                # Count text characters
                text = page.get_text()
                text_chars += len(text.strip())
                
                # Count image area
                for img in page.get_images():
                    try:
                        xref = img[0]
                        rect = page.get_image_bbox(xref)
                        if rect:
                            image_area += rect.width * rect.height
                    except:
                        pass
                
                total_area += page.rect.width * page.rect.height
            
            doc.close()
            
            # Decision logic
            if text_chars > 100:
                # Has substantial text - digital PDF
                return DocumentType.DIGITAL_PDF
            elif image_area > total_area * 0.5:
                # More than 50% images - scanned
                return DocumentType.SCANNED_PDF
            else:
                # Probably scanned or image-based
                return DocumentType.SCANNED_PDF
                
        except Exception as e:
            print(f"Error detecting PDF type: {e}")
            return DocumentType.SCANNED_PDF  # Assume scanned (safer)
    
    def _detect_image_type(self, image_path: str) -> DocumentType:
        """
        Detect if image is architectural drawing or regular image
        Uses simple heuristics - no LLM
        """
        
        filename_lower = Path(image_path).name.lower()
        
        # Check filename for hints
        arch_keywords = ["arch", "floor", "plan", "section", "elevation", "dwg", "cad", "drawing"]
        
        if any(kw in filename_lower for kw in arch_keywords):
            return DocumentType.ARCHITECTURAL_DRAWING
        
        # Could add image analysis here (aspect ratio, color histogram, etc.)
        # For now, default to regular image
        return DocumentType.IMAGE
    
    def _parse_task_requirements(self, task_type: str) -> Dict:
        """
        Parse what the task needs
        """
        
        task_lower = task_type.lower()
        
        reqs = {
            "needs_ocr": False,
            "needs_table_extraction": False,
            "needs_vision_understanding": False,
            "needs_text_extraction": False,
            "needs_structural_parsing": False,
            "accuracy_priority": "balanced"  # "speed", "balanced", "accuracy"
        }
        
        # Keyword detection
        if any(kw in task_lower for kw in ["ocr", "scanned", "handwrit"]):
            reqs["needs_ocr"] = True
        
        if any(kw in task_lower for kw in ["table", "grid", "spreadsheet", "schedule"]):
            reqs["needs_table_extraction"] = True
        
        if any(kw in task_lower for kw in ["drawing", "diagram", "floor", "section", "visual", "image"]):
            reqs["needs_vision_understanding"] = True
        
        if any(kw in task_lower for kw in ["text", "extract", "read", "content"]):
            reqs["needs_text_extraction"] = True
        
        if any(kw in task_lower for kw in ["structure", "section", "header", "parse"]):
            reqs["needs_structural_parsing"] = True
        
        if "fast" in task_lower or "quick" in task_lower:
            reqs["accuracy_priority"] = "speed"
        elif "accurate" in task_lower or "precise" in task_lower:
            reqs["accuracy_priority"] = "accuracy"
        
        return reqs
    
    def _apply_routing_rules(
        self,
        doc_type: DocumentType,
        task_reqs: Dict,
        context: Dict
    ) -> RoutingDecision:
        """
        Core routing logic based on document type and requirements
        """
        
        preprocessing = []
        primary = None
        fallbacks = []
        confidence = 0.0
        reasoning = ""
        
        # ============================================
        # RULE SET: Based on document type
        # ============================================
        
        if doc_type == DocumentType.DIGITAL_PDF:
            # Digital PDF - start with fast text extraction
            if task_reqs["needs_table_extraction"]:
                primary = "pdfplumber_extract"
                fallbacks = ["camelot_tables", "pymupdf_extract"]
                confidence = 0.9
                reasoning = "Digital PDF with tables - using pdfplumber for table support"
            elif task_reqs["needs_structural_parsing"]:
                primary = "dockling_parse"
                fallbacks = ["pdfplumber_extract", "pymupdf_extract"]
                confidence = 0.85
                reasoning = "Digital PDF needing structure - using Dockling"
            else:
                primary = "pymupdf_extract"
                fallbacks = ["pdfplumber_extract"]
                confidence = 0.95
                reasoning = "Digital PDF - using fast PyMuPDF extraction"
        
        elif doc_type == DocumentType.SCANNED_PDF:
            # Scanned PDF - needs OCR pipeline
            preprocessing = ["pdf2image_convert"]
            
            if task_reqs["needs_vision_understanding"]:
                primary = "llama_vision_analyze"
                fallbacks = ["paddleocr_extract", "easyocr_extract"]
                confidence = 0.85
                reasoning = "Scanned PDF needing understanding - Vision LLM with OCR fallback"
            else:
                # Accuracy vs speed choice for OCR
                if task_reqs["accuracy_priority"] == "speed":
                    primary = "tesseract_ocr"
                    fallbacks = ["easyocr_extract"]
                    confidence = 0.8
                    reasoning = "Scanned PDF, speed priority - using Tesseract"
                else:
                    primary = "paddleocr_extract"
                    fallbacks = ["easyocr_extract", "tesseract_ocr"]
                    confidence = 0.85
                    reasoning = "Scanned PDF - using PaddleOCR for accuracy"
        
        elif doc_type == DocumentType.ARCHITECTURAL_DRAWING:
            # Architectural drawings - definitely need Vision LLM
            preprocessing = ["pdf2image_convert"] if Path(context.get("file_path", "")).suffix == ".pdf" else []
            
            primary = "llama_vision_analyze"
            fallbacks = ["paddleocr_extract"]  # OCR as fallback for text annotations
            confidence = 0.9
            reasoning = "Architectural drawing - using Vision LLM for understanding"
        
        elif doc_type == DocumentType.IMAGE:
            if task_reqs["needs_vision_understanding"]:
                primary = "llama_vision_analyze"
                fallbacks = ["easyocr_extract"]
                confidence = 0.85
                reasoning = "Image needing understanding - Vision LLM"
            else:
                primary = "tesseract_ocr"
                fallbacks = ["easyocr_extract", "paddleocr_extract"]
                confidence = 0.8
                reasoning = "Image text extraction - using Tesseract"
        
        elif doc_type == DocumentType.SPREADSHEET:
            primary = "read_file"  # Direct pandas read
            fallbacks = []
            confidence = 0.95
            reasoning = "Spreadsheet - direct reading"
        
        elif doc_type == DocumentType.WORD_DOC:
            primary = "dockling_parse"
            fallbacks = ["pymupdf_extract"]  # Convert to PDF first
            confidence = 0.85
            reasoning = "Word document - using Dockling parser"
        
        else:
            # Unknown - try text extraction
            primary = "read_file"
            fallbacks = ["pymupdf_extract"]
            confidence = 0.5
            reasoning = "Unknown document type - attempting text read"
        
        return RoutingDecision(
            primary_tool=primary,
            fallback_tools=fallbacks,
            preprocessing_tools=preprocessing,
            confidence=confidence,
            reasoning=reasoning
        )
    
    def _apply_resource_constraints(self, decision: RoutingDecision) -> RoutingDecision:
        """
        Modify decision based on current resource usage
        """
        
        primary_tool = self.registry.get_tool(decision.primary_tool)
        
        if not primary_tool:
            return decision
        
        # Check if tool conflicts with currently loaded model
        if self.loaded_heavy_model and self.loaded_heavy_model in primary_tool.conflicts_with:
            # Need to use a fallback or plan for model swap
            for fallback_name in decision.fallback_tools:
                fallback_tool = self.registry.get_tool(fallback_name)
                if fallback_tool and self.loaded_heavy_model not in fallback_tool.conflicts_with:
                    # Found compatible fallback
                    return RoutingDecision(
                        primary_tool=fallback_name,
                        fallback_tools=[decision.primary_tool] + [f for f in decision.fallback_tools if f != fallback_name],
                        preprocessing_tools=decision.preprocessing_tools,
                        confidence=decision.confidence * 0.9,
                        reasoning=f"Using {fallback_name} to avoid model swap (was {decision.primary_tool})"
                    )
            
            # No compatible fallback - will need model swap
            decision.reasoning += f" (Note: Will require unloading {self.loaded_heavy_model})"
        
        return decision
    
    def set_loaded_model(self, model_name: str):
        """Track which heavy model is loaded"""
        self.loaded_heavy_model = model_name
    
    def clear_loaded_model(self):
        """Clear loaded model tracking"""
        self.loaded_heavy_model = None


class ToolChainPlanner:
    """
    Plans sequences of tool calls for complex tasks
    """
    
    def __init__(self, router: SmartToolRouter, registry=TOOL_REGISTRY):
        self.router = router
        self.registry = registry
    
    def plan_extraction_chain(
        self,
        file_path: str,
        extraction_targets: List[str],
        context: Dict = None
    ) -> List[Dict]:
        """
        Plan a sequence of tool calls to extract target information
        
        Returns list of steps:
        [
            {"tool": "pdf2image_convert", "params": {...}, "purpose": "..."},
            {"tool": "llama_vision_analyze", "params": {...}, "purpose": "..."},
            ...
        ]
        """
        
        steps = []
        context = context or {}
        context["file_path"] = file_path
        
        # Get routing decision
        task_description = f"extract {', '.join(extraction_targets)}"
        decision = self.router.route(file_path, task_description, context)
        
        # Add preprocessing steps
        for preprocess_tool in decision.preprocessing_tools:
            tool_def = self.registry.get_tool(preprocess_tool)
            if tool_def:
                steps.append({
                    "tool": preprocess_tool,
                    "params": self._generate_default_params(tool_def, file_path),
                    "purpose": f"Preprocessing: {tool_def.description[:100]}",
                    "output_key": f"{preprocess_tool}_output"
                })
        
        # Add primary extraction step
        primary_tool = self.registry.get_tool(decision.primary_tool)
        if primary_tool:
            steps.append({
                "tool": decision.primary_tool,
                "params": self._generate_extraction_params(primary_tool, extraction_targets),
                "purpose": decision.reasoning,
                "output_key": "primary_extraction",
                "fallbacks": decision.fallback_tools
            })
        
        # Add validation step if using LLM
        if primary_tool and primary_tool.category in [ToolCategory.VISION_LLM, ToolCategory.TEXT_LLM]:
            steps.append({
                "tool": "qwen_small_reason",
                "params": {
                    "text": "{{primary_extraction}}",
                    "prompt": f"Validate extracted data for: {', '.join(extraction_targets)}. Return JSON with confidence scores."
                },
                "purpose": "Validation and confidence scoring",
                "output_key": "validated_extraction"
            })
        
        return steps
    
    def _generate_default_params(self, tool: ToolDefinition, file_path: str) -> Dict:
        """Generate default parameters for a tool"""
        
        params = {}
        schema = tool.parameters_schema.get("properties", {})
        
        for param_name, param_def in schema.items():
            if "file" in param_name.lower() or "path" in param_name.lower():
                params[param_name] = file_path
            elif "default" in param_def:
                params[param_name] = param_def["default"]
        
        return params
    
    def _generate_extraction_params(self, tool: ToolDefinition, targets: List[str]) -> Dict:
        """Generate extraction-specific parameters"""
        
        params = {}
        schema = tool.parameters_schema.get("properties", {})
        
        for param_name, param_def in schema.items():
            if param_name == "prompt":
                # Generate extraction prompt
                params[param_name] = self._build_extraction_prompt(targets)
            elif "file" in param_name.lower() or "path" in param_name.lower():
                params[param_name] = "{{input_file}}"
            elif "text" in param_name.lower():
                params[param_name] = "{{previous_output}}"
            elif "default" in param_def:
                params[param_name] = param_def["default"]
        
        return params
    
    def _build_extraction_prompt(self, targets: List[str]) -> str:
        """Build extraction prompt for LLM tools"""
        
        return f"""Extract the following information:
{chr(10).join(f'- {target}' for target in targets)}

Return ONLY a JSON object with these keys:
{chr(10).join(f'  "{target}": <value or null>' for target in targets)}

Be precise. Use null if information is not found."""
```

---

## Part 3: The Tool Executor

Handles actual tool execution with resource management.

```python
"""
tool_executor.py - Execute tools with resource management
"""

import importlib
import gc
import torch
from typing import Dict, Any, Optional, Callable
from pathlib import Path
import json
import time

from tool_registry import TOOL_REGISTRY, ToolDefinition, ResourceRequirement

class ToolExecutor:
    """
    Executes tools with proper resource management
    Handles model loading/unloading for GPU tools
    """
    
    def __init__(self, gpu_memory_limit_gb: float = 8.0):
        self.gpu_memory_limit = gpu_memory_limit_gb
        self.loaded_models: Dict[str, Any] = {}
        self.execution_stats: Dict[str, Dict] = {}
        
    def execute(
        self,
        tool_name: str,
        params: Dict[str, Any],
        context: Dict = None
    ) -> Dict[str, Any]:
        """
        Execute a tool with given parameters
        
        Returns:
        {
            "success": bool,
            "output": Any,
            "error": Optional[str],
            "execution_time_ms": float
        }
        """
        
        start_time = time.time()
        
        tool = TOOL_REGISTRY.get_tool(tool_name)
        if not tool:
            return {
                "success": False,
                "output": None,
                "error": f"Tool not found: {tool_name}",
                "execution_time_ms": 0
            }
        
        try:
            # Prepare resources
            self._prepare_resources(tool)
            
            # Resolve parameter templates
            resolved_params = self._resolve_params(params, context or {})
            
            # Get implementation
            impl = self._get_implementation(tool)
            
            # Execute
            output = impl(**resolved_params)
            
            execution_time = (time.time() - start_time) * 1000
            
            # Update stats
            self._update_stats(tool_name, execution_time, success=True)
            
            return {
                "success": True,
                "output": output,
                "error": None,
                "execution_time_ms": execution_time
            }
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            self._update_stats(tool_name, execution_time, success=False)
            
            return {
                "success": False,
                "output": None,
                "error": str(e),
                "execution_time_ms": execution_time
            }
    
    def execute_chain(
        self,
        steps: list,
        initial_context: Dict = None
    ) -> Dict[str, Any]:
        """
        Execute a chain of tool calls
        
        Each step's output is available to subsequent steps via context
        """
        
        context = initial_context.copy() if initial_context else {}
        results = []
        
        for i, step in enumerate(steps):
            tool_name = step["tool"]
            params = step["params"]
            output_key = step.get("output_key", f"step_{i}_output")
            fallbacks = step.get("fallbacks", [])
            
            print(f"Step {i+1}/{len(steps)}: {tool_name}")
            print(f"  Purpose: {step.get('purpose', 'N/A')}")
            
            # Try primary tool
            result = self.execute(tool_name, params, context)
            
            # Try fallbacks if primary failed
            if not result["success"] and fallbacks:
                for fallback in fallbacks:
                    print(f"  Primary failed, trying fallback: {fallback}")
                    result = self.execute(fallback, params, context)
                    if result["success"]:
                        break
            
            # Store result in context for next steps
            context[output_key] = result["output"] if result["success"] else None
            
            results.append({
                "step": i,
                "tool": tool_name,
                "result": result
            })
            
            # Stop chain if critical step failed
            if not result["success"] and step.get("critical", True):
                print(f"  FAILED: {result['error']}")
                break
            
            print(f"  Completed in {result['execution_time_ms']:.0f}ms")
        
        return {
            "steps": results,
            "final_context": context,
            "success": all(r["result"]["success"] for r in results)
        }
    
    def _prepare_resources(self, tool: ToolDefinition):
        """Prepare resources before tool execution"""
        
        # Check if we need to manage GPU memory
        if tool.resource_requirement in [ResourceRequirement.GPU_MEDIUM, ResourceRequirement.GPU_HEAVY]:
            
            # Check for conflicts
            for conflict in tool.conflicts_with:
                if conflict in self.loaded_models:
                    print(f"Unloading conflicting model: {conflict}")
                    self._unload_model(conflict)
            
            # Load required models
            for required_model in tool.requires_models:
                if required_model not in self.loaded_models:
                    print(f"Loading required model: {required_model}")
                    self._load_model(required_model)
    
    def _load_model(self, model_name: str):
        """Load a model into memory"""
        
        # Clear GPU memory first
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        # Model-specific loading logic
        if model_name == "llama-vision-8b":
            from transformers import AutoProcessor, LlavaForConditionalGeneration
            
            model_id = "llava-hf/llava-1.5-7b-hf"
            processor = AutoProcessor.from_pretrained(model_id)
            model = LlavaForConditionalGeneration.from_pretrained(
                model_id,
                torch_dtype=torch.float16,
                device_map="auto",
                load_in_4bit=True,
                low_cpu_mem_usage=True
            )
            
            self.loaded_models[model_name] = {"model": model, "processor": processor}
            
        elif model_name == "qwen-coder-7b":
            from transformers import AutoTokenizer, AutoModelForCausalLM
            
            model_id = "Qwen/Qwen2.5-Coder-7B-Instruct"
            tokenizer = AutoTokenizer.from_pretrained(model_id)
            model = AutoModelForCausalLM.from_pretrained(
                model_id,
                torch_dtype=torch.float16,
                device_map="auto",
                load_in_4bit=True,
                low_cpu_mem_usage=True
            )
            
            self.loaded_models[model_name] = {"model": model, "tokenizer": tokenizer}
            
        elif model_name == "qwen-2.5b":
            from transformers import AutoTokenizer, AutoModelForCausalLM
            
            model_id = "Qwen/Qwen2.5-1.5B-Instruct"
            tokenizer = AutoTokenizer.from_pretrained(model_id)
            model = AutoModelForCausalLM.from_pretrained(
                model_id,
                torch_dtype=torch.float16,
                device_map="auto",
                load_in_4bit=True
            )
            
            self.loaded_models[model_name] = {"model": model, "tokenizer": tokenizer}
        
        print(f"GPU Memory after loading {model_name}: {torch.cuda.memory_allocated()/1e9:.2f} GB")
    
    def _unload_model(self, model_name: str):
        """Unload a model from memory"""
        
        if model_name in self.loaded_models:
            del self.loaded_models[model_name]
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            print(f"GPU Memory after unloading {model_name}: {torch.cuda.memory_allocated()/1e9:.2f} GB")
    
    def _get_implementation(self, tool: ToolDefinition) -> Callable:
        """Get the actual implementation function"""
        
        impl = tool.implementation
        
        if callable(impl):
            return impl
        
        if isinstance(impl, str):
            if impl.startswith("mcp://"):
                # MCP tool - return MCP caller
                tool_name = impl.replace("mcp://", "")
                return self._create_mcp_caller(tool_name)
            else:
                # Import from module path
                module_path, func_name = impl.rsplit(".", 1)
                module = importlib.import_module(module_path)
                return getattr(module, func_name)
        
        raise ValueError(f"Invalid implementation: {impl}")
    
    def _create_mcp_caller(self, tool_name: str) -> Callable:
        """Create a callable that invokes an MCP tool"""
        
        def mcp_caller(**kwargs):
            # This would integrate with your MCP client
            # For now, placeholder
            from mcp_client import call_mcp_tool
            return call_mcp_tool(tool_name, kwargs)
        
        return mcp_caller
    
    def _resolve_params(self, params: Dict, context: Dict) -> Dict:
        """Resolve template parameters like {{previous_output}}"""
        
        resolved = {}
        
        for key, value in params.items():
            if isinstance(value, str) and value.startswith("{{") and value.endswith("}}"):
                # Template variable
                var_name = value[2:-2]
                resolved[key] = context.get(var_name, value)
            else:
                resolved[key] = value
        
        return resolved
    
    def _update_stats(self, tool_name: str, execution_time: float, success: bool):
        """Update execution statistics"""
        
        if tool_name not in self.execution_stats:
            self.execution_stats[tool_name] = {
                "total_calls": 0,
                "successful_calls": 0,
                "total_time_ms": 0,
                "avg_time_ms": 0
            }
        
        stats = self.execution_stats[tool_name]
        stats["total_calls"] += 1
        stats["total_time_ms"] += execution_time
        stats["avg_time_ms"] = stats["total_time_ms"] / stats["total_calls"]
        
        if success:
            stats["successful_calls"] += 1
    
    def cleanup(self):
        """Cleanup all loaded models"""
        
        for model_name in list(self.loaded_models.keys()):
            self._unload_model(model_name)
```

---

## Part 4: The Agentic Loop with Tool Use

Now we tie it all together in the agentic loop.

```python
"""
agentic_loop.py - Main agentic loop with dynamic tool use
"""

import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from tool_registry import TOOL_REGISTRY, ToolCategory
from tool_router import SmartToolRouter, ToolChainPlanner
from tool_executor import ToolExecutor

@dataclass
class AgentState:
    """Current state of the agent"""
    task: str
    context: Dict[str, Any]
    completed_steps: List[Dict]
    pending_steps: List[Dict]
    extracted_data: Dict[str, Any]
    iteration: int
    max_iterations: int

class ConstructionDocumentAgent:
    """
    Agentic loop for construction document analysis
    Uses small LLM for orchestration, routes to tools intelligently
    """
    
    def __init__(
        self,
        orchestrator_model: str = "qwen-2.5b",
        gpu_memory_limit: float = 8.0,
        max_iterations: int = 20
    ):
        self.router = SmartToolRouter(max_gpu_memory_gb=gpu_memory_limit)
        self.planner = ToolChainPlanner(self.router)
        self.executor = ToolExecutor(gpu_memory_limit_gb=gpu_memory_limit)
        self.max_iterations = max_iterations
        
        # Load orchestrator (small, always resident)
        self.orchestrator = self._load_orchestrator(orchestrator_model)
        
    def _load_orchestrator(self, model_name: str):
        """Load the small orchestrator model"""
        
        from transformers import AutoTokenizer, AutoModelForCausalLM
        import torch
        
        model_id = "Qwen/Qwen2.5-1.5B-Instruct"
        
        tokenizer = AutoTokenizer.from_pretrained(model_id)
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            torch_dtype=torch.float16,
            device_map="auto",
            load_in_4bit=True
        )
        
        return {"model": model, "tokenizer": tokenizer}
    
    def run(
        self,
        task: str,
        files: List[str],
        extraction_targets: List[str]
    ) -> Dict[str, Any]:
        """
        Main entry point for running the agent
        
        Args:
            task: Description of what to extract
            files: List of file paths to process
            extraction_targets: Specific fields to extract
                               e.g., ["floors_above", "floors_below", "gfa", "external_area"]
        
        Returns:
            Extraction results for all files
        """
        
        results = {}
        
        for file_path in files:
            print(f"\n{'='*60}")
            print(f"Processing: {file_path}")
            print(f"{'='*60}")
            
            # Initialize agent state
            state = AgentState(
                task=task,
                context={"file_path": file_path, "targets": extraction_targets},
                completed_steps=[],
                pending_steps=[],
                extracted_data={},
                iteration=0,
                max_iterations=self.max_iterations
            )
            
            # Run agentic loop for this file
            file_result = self._process_file(state)
            results[file_path] = file_result
        
        return results
    
    def _process_file(self, state: AgentState) -> Dict[str, Any]:
        """
        Agentic loop for processing a single file
        """
        
        # Step 1: Plan initial tool chain
        initial_plan = self.planner.plan_extraction_chain(
            file_path=state.context["file_path"],
            extraction_targets=state.context["targets"],
            context=state.context
        )
        
        state.pending_steps = initial_plan
        
        # Step 2: Execute planned steps
        while state.pending_steps and state.iteration < state.max_iterations:
            state.iteration += 1
            
            current_step = state.pending_steps.pop(0)
            
            print(f"\nIteration {state.iteration}: {current_step['tool']}")
            
            # Execute step
            result = self.executor.execute(
                tool_name=current_step["tool"],
                params=current_step["params"],
                context=state.context
            )
            
            # Update context with result
            output_key = current_step.get("output_key", f"step_{state.iteration}")
            state.context[output_key] = result["output"]
            
            # Record completed step
            state.completed_steps.append({
                "step": current_step,
                "result": result
            })
            
            if result["success"]:
                # Check if we need to adjust plan based on output
                adjustment = self._maybe_adjust_plan(state, result)
                
                if adjustment:
                    state.pending_steps = adjustment + state.pending_steps
                
                # Extract any data from result
                self._extract_data(state, result)
            else:
                print(f"  Step failed: {result['error']}")
                
                # Try fallbacks if available
                if current_step.get("fallbacks"):
                    fallback_step = current_step.copy()
                    fallback_step["tool"] = current_step["fallbacks"][0]
                    fallback_step["fallbacks"] = current_step["fallbacks"][1:]
                    state.pending_steps.insert(0, fallback_step)
        
        # Step 3: Validate and finalize
        final_result = self._finalize_extraction(state)
        
        return final_result
    
    def _maybe_adjust_plan(self, state: AgentState, result: Dict) -> Optional[List[Dict]]:
        """
        Use orchestrator LLM to decide if plan needs adjustment
        Only called when complex decision needed
        """
        
        # Quick heuristic checks first (no LLM)
        output = result.get("output", "")
        
        if isinstance(output, str):
            # Check if extraction was successful
            targets = state.context.get("targets", [])
            missing_targets = []
            
            for target in targets:
                if target not in state.extracted_data or state.extracted_data[target] is None:
                    missing_targets.append(target)
            
            if not missing_targets:
                # All targets found, no adjustment needed
                return None
            
            # Check if output suggests scanned document
            if "no text found" in output.lower() or len(output.strip()) < 50:
                # Might be scanned - add OCR step
                return [{
                    "tool": "pdf2image_convert",
                    "params": {"file_path": state.context["file_path"], "output_dir": "/tmp/images"},
                    "purpose": "Convert to images for OCR",
                    "output_key": "images"
                }, {
                    "tool": "paddleocr_extract",
                    "params": {"image_path": "{{images}}"},
                    "purpose": "OCR on converted images",
                    "output_key": "ocr_text"
                }]
        
        # For complex cases, use orchestrator LLM
        return self._llm_plan_adjustment(state, result)
    
    def _llm_plan_adjustment(self, state: AgentState, result: Dict) -> Optional[List[Dict]]:
        """
        Use small LLM to decide plan adjustment
        Called only for complex decisions
        """
        
        # Build compact prompt
        tools_summary = self._get_tools_summary()
        
        prompt = f"""Task: {state.task}
Targets: {state.context['targets']}
Current extracted: {json.dumps(state.extracted_data)}
Last step output preview: {str(result.get('output', ''))[:500]}

Available tools: {tools_summary}

What tool should be used next to find missing data?
Reply with ONLY the tool name, or "DONE" if complete.
Tool:"""

        # Run inference
        response = self._run_orchestrator(prompt)
        
        tool_name = response.strip().split()[0]
        
        if tool_name == "DONE" or tool_name not in [t.name for t in TOOL_REGISTRY._tools.values()]:
            return None
        
        # Get tool and create step
        tool = TOOL_REGISTRY.get_tool(tool_name)
        if tool:
            return [{
                "tool": tool_name,
                "params": self._generate_params_for_missing(tool, state),
                "purpose": f"LLM decided: find missing {state.context['targets']}",
                "output_key": f"llm_step_{state.iteration}"
            }]
        
        return None
    
    def _run_orchestrator(self, prompt: str) -> str:
        """Run the orchestrator LLM"""
        
        import torch
        
        tokenizer = self.orchestrator["tokenizer"]
        model = self.orchestrator["model"]
        
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=50,
                do_sample=False,
                temperature=0.1,
                pad_token_id=tokenizer.eos_token_id
            )
        
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract just the generated part
        if prompt in response:
            response = response[len(prompt):].strip()
        
        return response
    
    def _get_tools_summary(self) -> str:
        """Get compact tools summary for LLM"""
        
        summaries = []
        for tool in TOOL_REGISTRY._tools.values():
            summaries.append(f"{tool.name}: {tool.description[:80]}")
        
        return "\n".join(summaries[:10])  # Limit to 10 tools
    
    def _generate_params_for_missing(self, tool, state: AgentState) -> Dict:
        """Generate parameters targeting missing data"""
        
        missing = [t for t in state.context["targets"] if t not in state.extracted_data]
        
        params = {}
        schema = tool.parameters_schema.get("properties", {})
        
        for param_name, param_def in schema.items():
            if "file" in param_name.lower() or "path" in param_name.lower():
                params[param_name] = state.context["file_path"]
            elif param_name == "prompt":
                params[param_name] = f"Extract: {', '.join(missing)}. Return JSON."
            elif "default" in param_def:
                params[param_name] = param_def["default"]
        
        return params
    
    def _extract_data(self, state: AgentState, result: Dict):
        """Extract target data from tool result"""
        
        output = result.get("output")
        
        if not output:
            return
        
        targets = state.context.get("targets", [])
        
        # Try to parse as JSON
        if isinstance(output, str):
            try:
                # Try to find JSON in output
                import re
                json_match = re.search(r'\{[^{}]*\}', output, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group())
                    for target in targets:
                        if target in data and data[target] is not None:
                            state.extracted_data[target] = data[target]
            except json.JSONDecodeError:
                pass
            
            # Regex extraction fallback
            patterns = {
                "floors_above": r"floors?\s*(?:above|over)\s*(?:ground)?[:\s]*(\d+)",
                "floors_below": r"(?:basement|underground|below)[:\s]*(\d+)",
                "gfa": r"(?:gfa|gross\s*floor\s*area)[:\s]*([\d,]+\.?\d*)",
                "external_area": r"(?:external|site)\s*area[:\s]*([\d,]+\.?\d*)"
            }
            
            for target in targets:
                if target not in state.extracted_data and target in patterns:
                    match = re.search(patterns[target], output, re.IGNORECASE)
                    if match:
                        try:
                            state.extracted_data[target] = float(match.group(1).replace(",", ""))
                        except ValueError:
                            pass
        
        elif isinstance(output, dict):
            for target in targets:
                if target in output and output[target] is not None:
                    state.extracted_data[target] = output[target]
    
    def _finalize_extraction(self, state: AgentState) -> Dict[str, Any]:
        """Finalize and validate extraction results"""
        
        return {
            "file": state.context["file_path"],
            "extracted_data": state.extracted_data,
            "iterations": state.iteration,
            "steps_executed": len(state.completed_steps),
            "confidence": self._calculate_confidence(state)
        }
    
    def _calculate_confidence(self, state: AgentState) -> Dict[str, str]:
        """Calculate confidence for each extracted field"""
        
        confidence = {}
        
        for target in state.context.get("targets", []):
            if target in state.extracted_data:
                # Check how many sources confirmed
                sources = sum(1 for step in state.completed_steps 
                             if step["result"]["success"] and target in str(step["result"].get("output", "")))
                
                if sources >= 2:
                    confidence[target] = "HIGH"
                elif sources == 1:
                    confidence[target] = "MEDIUM"
                else:
                    confidence[target] = "LOW"
            else:
                confidence[target] = "NOT_FOUND"
        
        return confidence
    
    def cleanup(self):
        """Cleanup resources"""
        self.executor.cleanup()


# ============================================
# USAGE EXAMPLE
# ============================================

if __name__ == "__main__":
    # Register your custom tools first
    TOOL_REGISTRY.register_custom_tool(
        name="my_custom_extractor",
        description="My custom construction data extractor",
        category="custom",
        parameters={
            "type": "object",
            "properties": {
                "file_path": {"type": "string"},
                "extraction_type": {"type": "string"}
            },
            "required": ["file_path"]
        },
        implementation=lambda file_path, extraction_type="all": {"status": "extracted"},
        input_types=["pdf"],
        output_types=["json"]
    )
    
    # Create agent
    agent = ConstructionDocumentAgent(
        gpu_memory_limit=8.0,
        max_iterations=15
    )
    
    # Run extraction
    results = agent.run(
        task="Extract building metrics from construction documents",
        files=[
            "/data/projects/project_1/DA_Approval.pdf",
            "/data/projects/project_1/Architectural_Combined.pdf"
        ],
        extraction_targets=[
            "floors_above",
            "floors_below", 
            "gfa",
            "external_area"
        ]
    )
    
    # Print results
    print("\n" + "="*60)
    print("FINAL RESULTS")
    print("="*60)
    print(json.dumps(results, indent=2))
    
    # Cleanup
    agent.cleanup()
```

---

## Part 5: MCP Integration

If you're using MCP (Model Context Protocol), here's how to integrate:

```python
"""
mcp_integration.py - MCP tool integration
"""

from typing import Dict, Any, List
import json

class MCPToolBridge:
    """
    Bridge between our tool registry and MCP protocol
    """
    
    def __init__(self, mcp_server_url: str = None):
        self.mcp_server_url = mcp_server_url
        self.mcp_tools: Dict[str, Dict] = {}
        
    def discover_mcp_tools(self) -> List[Dict]:
        """
        Discover tools from MCP server
        This would connect to your MCP server and get available tools
        """
        
        # In real implementation, this would call:
        # GET {mcp_server_url}/tools
        
        # For now, example MCP tool definitions
        mcp_tools = [
            {
                "name": "construction_db_lookup",
                "description": "Look up project data in construction database",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "project_id": {"type": "string"},
                        "fields": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["project_id"]
                }
            },
            {
                "name": "drawing_annotation_reader",
                "description": "Read annotations from CAD/BIM drawings",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string"},
                        "annotation_types": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["file_path"]
                }
            }
        ]
        
        self.mcp_tools = {t["name"]: t for t in mcp_tools}
        return mcp_tools
    
    def register_mcp_tools_to_registry(self, registry):
        """Register discovered MCP tools to our tool registry"""
        
        for tool_def in self.mcp_tools.values():
            registry.register_from_mcp(tool_def)
    
    def call_mcp_tool(self, tool_name: str, params: Dict) -> Any:
        """
        Call an MCP tool
        
        In real implementation, this would:
        POST {mcp_server_url}/tools/{tool_name}/call
        """
        
        # Placeholder - implement actual MCP call
        import requests
        
        if self.mcp_server_url:
            response = requests.post(
                f"{self.mcp_server_url}/tools/{tool_name}/call",
                json=params
            )
            return response.json()
        
        return {"error": "MCP server not configured"}


# Global MCP client
mcp_client = None

def init_mcp(server_url: str):
    """Initialize MCP integration"""
    global mcp_client
    mcp_client = MCPToolBridge(server_url)
    mcp_client.discover_mcp_tools()
    mcp_client.register_mcp_tools_to_registry(TOOL_REGISTRY)

def call_mcp_tool(tool_name: str, params: Dict) -> Any:
    """Call MCP tool (used by executor)"""
    if mcp_client:
        return mcp_client.call_mcp_tool(tool_name, params)
    raise RuntimeError("MCP not initialized")
```

---

## Summary: How the Agent Learns About and Uses Tools

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                        HOW THE AGENT KNOWS ABOUT TOOLS                              │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  1. TOOL REGISTRY                                                                   │
│     ├── All tools registered at startup                                             │
│     ├── Each tool has: name, description, capabilities, parameters                  │
│     ├── Custom tools registered via register_custom_tool()                          │
│     └── MCP tools discovered and registered automatically                           │
│                                                                                      │
│  2. SMART ROUTER (No LLM needed for most decisions)                                 │
│     ├── Detects document type (digital PDF, scanned, image, drawing)               │
│     ├── Matches capabilities to requirements                                         │
│     ├── Considers resource constraints (GPU memory)                                 │
│     └── Returns: primary tool + fallbacks                                           │
│                                                                                      │
│  3. SMALL ORCHESTRATOR LLM (Qwen 2.5B - only when needed)                          │
│     ├── Given compact tool list when complex decision needed                        │
│     ├── Decides next step when heuristics insufficient                              │
│     └── Validates extraction results                                                │
│                                                                                      │
│  4. TOOL EXECUTOR                                                                   │
│     ├── Manages model loading/unloading                                              │
│     ├── Handles resource conflicts                                                   │
│     ├── Executes tool chains                                                         │
│     └── Falls back on failures                                                       │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

This architecture lets your agent smartly choose tools while respecting your 8GB GPU constraint!
