# Intelligent Query Routing & Classification - Implementation Plan

**Date**: 2025-12-05
**Priority**: CRITICAL
**Goal**: Robust query routing that handles all document types and query scenarios intelligently

---

## Current Issues Identified

### 1. Parameter Mismatch in Tool Calls
```
❌ docling_pdf failed: got an unexpected keyword argument 'query'
❌ ocr failed: got an unexpected keyword argument 'query'
```

**Problem**: TaskRouter passes `query` parameter, but tools expect different parameter names.

### 2. Vision Analysis Not Triggered
- Parallel extraction code exists but never runs
- Query flow stops at `document_rag` before reaching `vision_analysis`
- Vision tool should be triggered for visual/spatial questions

---

## Required Scenarios (User's Requirements)

### Text-Based Scenarios
1. **Direct LLM Questions** (no documents)
   - "What is Python?"
   - "Explain RAG architecture"
   - Route: → Direct LLM

2. **Uploaded Text Documents** (TXT, MD, JSON)
   - "Summarize this document"
   - Route: → document_rag (text embeddings)

3. **PDF with Text Content**
   - "What does the contract say about termination?"
   - Route: → document_rag (text embeddings) OR docling_pdf

### Vision-Based Scenarios
4. **Spatial/Visual Questions on PDFs**
   - "How many rooms in the floor plan?"
   - "Count the floors in the diagram"
   - Route: → vision_analysis (with parallel extraction)

5. **Uploaded Images** (PNG, JPG, JPEG)
   - "What's in this image?"
   - Route: → vision_analysis

6. **Images within PDF**
   - "Show me the photos from the report"
   - Route: → Multi-channel (CLIP visual embeddings) + vision_analysis

7. **Images within Word Documents** (DOCX)
   - "Extract the charts from the presentation"
   - Route: → docling + vision_analysis

### OCR Scenarios
8. **Scanned PDFs**
   - "Extract text from this scanned document"
   - Route: → ocr + vision_analysis

9. **Handwritten Notes**
   - "Read the handwritten notes"
   - Route: → vision_analysis (LLaMA 3.2 Vision)

---

## Solution Architecture

### Phase 1: Enhanced Query Classification

**What**: Classify queries into categories that map to tool selection

**Categories**:
```python
class QueryIntent:
    GENERAL_KNOWLEDGE = "general_knowledge"      # No docs needed
    TEXT_EXTRACTION = "text_extraction"          # Text from docs
    VISUAL_ANALYSIS = "visual_analysis"          # Images, diagrams
    SPATIAL_REASONING = "spatial_reasoning"      # Count, layout, position
    TABLE_EXTRACTION = "table_extraction"        # Structured data
    CODE_EXTRACTION = "code_extraction"          # Code snippets
    DOCUMENT_QA = "document_qa"                  # Text-based Q&A
    HYBRID_MULTIMODAL = "hybrid_multimodal"      # Text + images
```

**Classification Logic**:
```python
async def classify_query_intent(query: str, documents: List[Document]) -> QueryIntent:
    """
    Intelligent query classification

    Rules:
    1. Check keywords for visual/spatial intent
    2. Check document types (PDF, images, etc.)
    3. Check if query requires visual understanding
    4. Fallback to text-based if no visual indicators
    """

    # Visual keywords
    visual_keywords = [
        "count", "how many", "show me", "identify", "locate",
        "floor plan", "diagram", "chart", "graph", "image",
        "photo", "picture", "drawing", "sketch", "map",
        "layout", "position", "spatial", "arrangement"
    ]

    # Spatial reasoning keywords
    spatial_keywords = [
        "rooms", "floors", "levels", "areas", "sections",
        "zones", "quadrants", "left", "right", "top", "bottom",
        "north", "south", "east", "west", "center"
    ]

    query_lower = query.lower()

    # Check for visual intent
    has_visual_keywords = any(kw in query_lower for kw in visual_keywords)
    has_spatial_keywords = any(kw in query_lower for kw in spatial_keywords)

    # Check document types
    has_images = any(doc.file_type in ['png', 'jpg', 'jpeg', 'gif'] for doc in documents)
    has_pdfs = any(doc.file_type == 'pdf' for doc in documents)

    # Decision tree
    if has_spatial_keywords and (has_pdfs or has_images):
        return QueryIntent.SPATIAL_REASONING

    if has_visual_keywords and (has_pdfs or has_images):
        return QueryIntent.VISUAL_ANALYSIS

    if not documents:
        return QueryIntent.GENERAL_KNOWLEDGE

    if has_images:
        return QueryIntent.VISUAL_ANALYSIS

    # Default to document Q&A
    return QueryIntent.DOCUMENT_QA
```

### Phase 2: Unified Tool Parameter Interface

**Problem**: Each tool expects different parameters.

**Solution**: Create a unified `ToolContext` that all tools accept:

```python
@dataclass
class ToolContext:
    """Unified context for all tools"""

    # Query information
    query: str
    session_id: str

    # Document information
    documents: List[Document]
    file_paths: List[str]

    # Database and services
    db: AsyncSession
    llm_service: Any
    vision_service: Any
    embedding_service: Any

    # Configuration
    model_id: str
    top_k: int = 5
    similarity_threshold: float = 0.6

    # Metadata
    query_intent: Optional[QueryIntent] = None
    available_memory_mb: float = 0
    strategy_weights: Optional[Dict] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for legacy tool compatibility"""
        return {
            "query": self.query,
            "session_id": self.session_id,
            "db": self.db,
            "model_id": self.model_id,
            "top_k": self.top_k,
            # ... other fields
        }
```

**Update all tool wrappers to accept ToolContext**:

```python
async def _wrap_vision_analysis(self, context: ToolContext) -> Dict[str, Any]:
    """Updated to use ToolContext"""
    query = context.query
    session_id = context.session_id
    db = context.db
    # ...

async def _wrap_docling_pdf(self, context: ToolContext) -> Dict[str, Any]:
    """Updated to use ToolContext"""
    # ...

async def _wrap_ocr(self, context: ToolContext) -> Dict[str, Any]:
    """Updated to use ToolContext"""
    # ...
```

### Phase 3: Intelligent Tool Router

**What**: Route queries to the right tool based on classification + document type

```python
class IntelligentToolRouter:
    """
    Smart routing based on query intent and document characteristics
    """

    def __init__(self):
        self.routing_rules = {
            # Visual/Spatial queries
            QueryIntent.SPATIAL_REASONING: {
                "primary": "vision_analysis",
                "fallback": ["docling_pdf", "ocr", "document_rag"],
                "requires_documents": True,
                "document_types": ["pdf", "png", "jpg", "jpeg"]
            },

            QueryIntent.VISUAL_ANALYSIS: {
                "primary": "vision_analysis",
                "fallback": ["ocr", "document_rag"],
                "requires_documents": True,
                "document_types": ["pdf", "png", "jpg", "jpeg", "gif"]
            },

            # Text-based queries
            QueryIntent.DOCUMENT_QA: {
                "primary": "document_rag",
                "fallback": ["docling_pdf", "direct_llm"],
                "requires_documents": True,
                "document_types": ["pdf", "txt", "md", "json", "docx"]
            },

            QueryIntent.TEXT_EXTRACTION: {
                "primary": "docling_pdf",
                "fallback": ["ocr", "document_rag"],
                "requires_documents": True,
                "document_types": ["pdf", "docx"]
            },

            # No documents
            QueryIntent.GENERAL_KNOWLEDGE: {
                "primary": "direct_llm",
                "fallback": [],
                "requires_documents": False,
                "document_types": []
            },

            # Hybrid scenarios
            QueryIntent.HYBRID_MULTIMODAL: {
                "primary": "vision_analysis",
                "fallback": ["document_rag", "docling_pdf"],
                "requires_documents": True,
                "document_types": ["pdf", "docx"],
                "parallel_tools": ["vision_analysis", "document_rag"]  # Run both!
            }
        }

    async def route(
        self,
        context: ToolContext
    ) -> Dict[str, Any]:
        """
        Route query to appropriate tool(s)

        Returns:
            {
                "primary_tool": "vision_analysis",
                "fallback_chain": ["docling_pdf", "ocr"],
                "parallel_tools": [],  # Optional: run multiple tools
                "strategy": "sequential" | "parallel"
            }
        """

        # Step 1: Classify query intent
        intent = await classify_query_intent(
            context.query,
            context.documents
        )
        context.query_intent = intent

        # Step 2: Get routing rule
        rule = self.routing_rules.get(intent)

        # Step 3: Validate document requirements
        if rule["requires_documents"] and not context.documents:
            # No documents but query requires them
            return {
                "primary_tool": "direct_llm",
                "fallback_chain": [],
                "strategy": "sequential",
                "note": "No documents available, using direct LLM"
            }

        # Step 4: Check document type compatibility
        if context.documents:
            doc_types = set(doc.file_type for doc in context.documents)
            compatible = any(dt in rule["document_types"] for dt in doc_types)

            if not compatible:
                # Documents don't match expected types
                # Fallback to generic document_rag
                return {
                    "primary_tool": "document_rag",
                    "fallback_chain": ["direct_llm"],
                    "strategy": "sequential",
                    "note": f"Document types {doc_types} not compatible with {intent}"
                }

        # Step 5: Return routing decision
        return {
            "primary_tool": rule["primary"],
            "fallback_chain": rule["fallback"],
            "parallel_tools": rule.get("parallel_tools", []),
            "strategy": "parallel" if rule.get("parallel_tools") else "sequential",
            "intent": intent,
            "confidence": 0.9
        }
```

### Phase 4: Document Type Detection

**What**: Detect if PDF contains images, text, or both

```python
async def analyze_document_characteristics(file_path: str) -> Dict[str, Any]:
    """
    Analyze document to determine its characteristics

    Returns:
        {
            "has_text": True,
            "has_images": True,
            "has_tables": False,
            "has_diagrams": True,
            "text_percentage": 0.3,  # 30% text
            "image_percentage": 0.7,  # 70% images
            "page_count": 5,
            "recommended_tools": ["vision_analysis", "document_rag"]
        }
    """

    if not file_path.lower().endswith('.pdf'):
        # Non-PDF files
        ext = Path(file_path).suffix.lower()
        if ext in ['.png', '.jpg', '.jpeg', '.gif']:
            return {
                "has_text": False,
                "has_images": True,
                "recommended_tools": ["vision_analysis"]
            }
        else:
            return {
                "has_text": True,
                "has_images": False,
                "recommended_tools": ["document_rag", "docling_pdf"]
            }

    # PDF analysis
    import fitz
    doc = fitz.open(file_path)

    total_pages = len(doc)
    pages_with_text = 0
    pages_with_images = 0
    total_text_chars = 0

    for page_num in range(total_pages):
        page = doc[page_num]

        # Check for text
        text = page.get_text()
        if len(text.strip()) > 50:  # Significant text
            pages_with_text += 1
            total_text_chars += len(text)

        # Check for images
        images = page.get_images()
        if images:
            pages_with_images += 1

    doc.close()

    # Calculate percentages
    text_ratio = pages_with_text / total_pages
    image_ratio = pages_with_images / total_pages

    # Determine recommended tools
    recommended = []
    if image_ratio > 0.3:  # 30%+ images
        recommended.append("vision_analysis")
    if text_ratio > 0.3:  # 30%+ text
        recommended.extend(["document_rag", "docling_pdf"])
    if image_ratio > 0.5 and text_ratio > 0.3:
        # Hybrid document
        recommended.append("hybrid_multimodal")

    return {
        "has_text": text_ratio > 0.1,
        "has_images": image_ratio > 0.1,
        "text_percentage": text_ratio,
        "image_percentage": image_ratio,
        "page_count": total_pages,
        "recommended_tools": recommended,
        "document_type": "text-heavy" if text_ratio > 0.7
                        else "image-heavy" if image_ratio > 0.7
                        else "hybrid"
    }
```

---

## Implementation Steps

### Step 1: Fix Parameter Mismatch (IMMEDIATE)

**File**: `backend/app/agents/tool_registry.py`

**Change all tool wrappers to accept flexible kwargs**:

```python
async def _wrap_docling_pdf(self, **kwargs) -> Dict[str, Any]:
    """Extract content from PDFs using Docling"""

    # Extract parameters with flexible naming
    query = kwargs.get('query') or kwargs.get('question', '')
    session_id = kwargs.get('session_id')
    db = kwargs.get('db')
    file_path = kwargs.get('file_path')

    # If no file_path, find PDF in session
    if not file_path and session_id and db:
        documents = await self._get_session_documents(session_id, db)
        pdf_docs = [doc for doc in documents if doc.file_type == 'pdf']
        if pdf_docs:
            file_path = pdf_docs[0].file_path

    if not file_path:
        return {
            "success": False,
            "error": "No PDF file found in session"
        }

    # Rest of implementation...
```

### Step 2: Implement Query Classification (HIGH PRIORITY)

**File**: `backend/app/services/intelligent_query_classifier.py` (NEW)

Create the classification logic with visual/spatial keyword detection.

### Step 3: Implement Intelligent Router (HIGH PRIORITY)

**File**: `backend/app/services/intelligent_tool_router.py` (NEW)

Implement the routing logic based on classification + document characteristics.

### Step 4: Update EnhancedRAGAgent (CRITICAL)

**File**: `backend/app/agents/enhanced_rag_agent.py`

Replace TaskRouter with IntelligentToolRouter:

```python
async def process_query(self, query: str, **kwargs):
    # Step 1: Get documents
    documents = await self._get_session_documents(session_id, db)

    # Step 2: Analyze document characteristics
    doc_analysis = await analyze_document_characteristics(documents)

    # Step 3: Create ToolContext
    context = ToolContext(
        query=query,
        session_id=session_id,
        documents=documents,
        db=db,
        model_id=model_id,
        # ... other params
    )

    # Step 4: Route intelligently
    router = IntelligentToolRouter()
    routing = await router.route(context)

    # Step 5: Execute based on strategy
    if routing["strategy"] == "parallel":
        # Run multiple tools in parallel
        result = await self._execute_parallel(
            tools=routing["parallel_tools"],
            context=context
        )
    else:
        # Sequential execution with fallback
        result = await self._execute_sequential(
            primary=routing["primary_tool"],
            fallback=routing["fallback_chain"],
            context=context
        )

    return result
```

### Step 5: Add Document Analysis to Upload Pipeline

**File**: `backend/app/main.py` (upload endpoint)

Analyze documents on upload and store characteristics:

```python
@app.post("/api/v1/upload")
async def upload_file(...):
    # Existing upload logic

    # NEW: Analyze document characteristics
    doc_characteristics = await analyze_document_characteristics(file_path)

    # Store in document metadata
    document.meta_info = {
        **document.meta_info,
        "characteristics": doc_characteristics
    }

    await db.commit()
```

---

## Testing Scenarios

### Test 1: Direct LLM (No Documents)
```bash
Query: "What is Python?"
Expected: Route to direct_llm
```

### Test 2: Text Document Q&A
```bash
Upload: contract.pdf (text-heavy)
Query: "What are the payment terms?"
Expected: Route to document_rag
```

### Test 3: Visual/Spatial Query
```bash
Upload: floor_plan.pdf (image-heavy)
Query: "How many rooms in the ground floor?"
Expected: Route to vision_analysis → Trigger parallel extraction
```

### Test 4: Image File
```bash
Upload: photo.jpg
Query: "What's in this image?"
Expected: Route to vision_analysis
```

### Test 5: Scanned PDF
```bash
Upload: scanned_document.pdf (no text layer)
Query: "Extract the text"
Expected: Route to ocr → vision_analysis
```

### Test 6: Hybrid PDF
```bash
Upload: report.pdf (text + images)
Query: "Summarize the report and describe the charts"
Expected: Route to hybrid_multimodal → Parallel (document_rag + vision_analysis)
```

---

## Priority Implementation Order

1. **IMMEDIATE**: Fix parameter mismatch in tool wrappers
2. **HIGH**: Implement query classification
3. **HIGH**: Implement intelligent router
4. **HIGH**: Update EnhancedRAGAgent to use new router
5. **MEDIUM**: Add document analysis to upload pipeline
6. **MEDIUM**: Comprehensive testing

---

## Expected Improvements

### Before (Current)
- ❌ Tools fail due to parameter mismatch
- ❌ Vision analysis never triggered for visual queries
- ❌ No intelligent routing based on query type
- ❌ Fallback chain stops at first success

### After (Proposed)
- ✅ All tools accept flexible parameters
- ✅ Visual/spatial queries route to vision_analysis
- ✅ Intelligent classification based on query + documents
- ✅ Parallel execution for hybrid queries
- ✅ Document characteristics analyzed on upload
- ✅ Robust routing for all scenarios

---

**Date**: 2025-12-05
**Status**: PLAN READY - Ready for Implementation
**User Requirement**: "make it robust to handle situations with direct questions to llm, uploaded text with llm, question with direct rag for text, question with direct rag for vision, question with uploaded images, images within pdf, images within word etc etc"

