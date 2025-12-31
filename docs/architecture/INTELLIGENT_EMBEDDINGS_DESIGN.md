# Intelligent Document-Type-Specific Embedding Strategy

**Date**: 2025-12-02
**Status**: 🚧 **DESIGN PHASE**
**Priority**: High (Performance & Accuracy Optimization)

---

## Problem Statement

**Current Implementation**: All documents use the same embedding model regardless of type:
```python
# Current: One-size-fits-all
embedding = sentence_transformers.encode(text)
# Used for: PDFs, images (after OCR), Excel, Word, code, etc.
```

**Issues:**
1. ❌ Images embedded as text lose spatial/visual information
2. ❌ Tables embedded as text lose structure and numerical relationships
3. ❌ Code embedded as text loses syntax and semantics
4. ❌ Scanned PDFs get poor quality text embeddings
5. ❌ Excel numerical data treated as text strings

---

## User's Question

> "the documents when uploaded are embedded into vector DB? should we apply intelligent embeddings for different types of documents based on the analysis??"

**Answer**: YES! We should apply different embedding strategies based on:
- Document type (PDF, image, Excel, code)
- Content type (tables, diagrams, text, numerical data)
- Document quality (digital vs scanned)
- Use case (semantic search vs exact match vs numerical similarity)

---

## Architecture: Multi-Strategy Embedding System

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                         DOCUMENT UPLOAD & ANALYSIS                                   │
└───────────────────────────────────────────┬─────────────────────────────────────────┘
                                            │
                                            ▼
                              ┌─────────────────────────┐
                              │   DOCUMENT ANALYZER     │
                              │   (TaskRouter)          │
                              │   Detects:              │
                              │   - File type           │
                              │   - Content type        │
                              │   - Quality             │
                              └──────────┬──────────────┘
                                         │
                    ┌────────────────────┼────────────────────┐
                    │                    │                    │
                    ▼                    ▼                    ▼
           ┌────────────────┐   ┌────────────────┐   ┌────────────────┐
           │   TEXT         │   │   TABLES       │   │   IMAGES       │
           │   DOCUMENTS    │   │   & DATA       │   │   & DIAGRAMS   │
           └────────┬───────┘   └────────┬───────┘   └────────┬───────┘
                    │                    │                    │
                    ▼                    ▼                    ▼
         ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
         │ Sentence         │  │ Table Structure  │  │ Vision Model     │
         │ Transformers     │  │ + Numerical      │  │ Embeddings       │
         │ (384-dim)        │  │ Embeddings       │  │ (CLIP/DINO)      │
         └──────────┬───────┘  └──────────┬───────┘  └──────────┬───────┘
                    │                     │                     │
                    └─────────────────────┴─────────────────────┘
                                          │
                                          ▼
                              ┌─────────────────────────┐
                              │   VECTOR DATABASE       │
                              │   (Multi-Index)         │
                              │   - text_embeddings     │
                              │   - table_embeddings    │
                              │   - image_embeddings    │
                              └─────────────────────────┘
```

---

## Embedding Strategy Matrix

| Document Type | Content Analysis | Primary Embedding | Secondary Embedding | Metadata |
|---------------|------------------|-------------------|---------------------|----------|
| **Digital PDF** | Text-heavy | Sentence-BERT (384-dim) | N/A | Layout structure |
| **Digital PDF** | Table-heavy | Table structure embeddings | Numerical embeddings | Column names, data types |
| **Scanned PDF** | Low quality | OCR + Sentence-BERT | Vision embeddings (fallback) | OCR confidence |
| **Scanned PDF** | High quality | OCR + Sentence-BERT | N/A | Text clarity |
| **Images** | Diagrams/Charts | Vision model (CLIP) | OCR (if text present) | Visual features |
| **Images** | Text screenshots | OCR + Sentence-BERT | Vision embeddings | Layout info |
| **Excel** | Numerical data | Numerical embeddings | Column header embeddings | Data types, stats |
| **Excel** | Mixed text/numbers | Hybrid (text + numerical) | N/A | Schema |
| **Code files** | Python/JS/etc | Code-BERT | Sentence-BERT (comments) | Syntax tree |
| **Word docs** | Text | Sentence-BERT | N/A | Document structure |

---

## Implementation Plan

### Phase 1: Document-Type Detection (DONE ✅)

**Already implemented in TaskRouter:**
```python
# task_router.py
file_types = self.detect_file_types(documents)
# Returns: [FileType.PDF, FileType.IMAGE, etc.]
```

### Phase 2: Content Analysis (NEW)

**Add content-type detection:**

```python
# backend/app/services/content_analyzer.py

from enum import Enum
from typing import Dict, Any

class ContentType(Enum):
    TEXT_HEAVY = "text_heavy"          # >80% text
    TABLE_HEAVY = "table_heavy"        # Multiple tables
    IMAGE_HEAVY = "image_heavy"        # Diagrams, charts
    CODE = "code"                      # Programming code
    NUMERICAL = "numerical"            # Spreadsheets, data
    MIXED = "mixed"                    # Mixed content

class ContentAnalyzer:
    """Analyze document content to determine embedding strategy"""

    async def analyze_content(
        self,
        file_path: str,
        file_type: FileType
    ) -> Dict[str, Any]:
        """
        Analyze document content

        Returns:
            {
                "content_type": ContentType,
                "has_tables": bool,
                "table_count": int,
                "has_images": bool,
                "image_count": int,
                "text_percentage": float,
                "is_scanned": bool,
                "ocr_confidence": float
            }
        """

        if file_type == FileType.PDF:
            return await self._analyze_pdf(file_path)
        elif file_type == FileType.IMAGE:
            return await self._analyze_image(file_path)
        elif file_type == FileType.EXCEL:
            return await self._analyze_excel(file_path)

    async def _analyze_pdf(self, file_path: str) -> Dict:
        """Analyze PDF content"""
        import fitz  # PyMuPDF

        doc = fitz.open(file_path)

        text_blocks = []
        image_count = 0
        table_count = 0

        for page in doc:
            # Check if scanned (no text layer)
            text = page.get_text()
            is_scanned = len(text.strip()) < 50  # Threshold

            # Count images
            image_count += len(page.get_images())

            # Detect tables (heuristic: lots of whitespace, numbers)
            # TODO: Use table detection library

        return {
            "content_type": self._classify_content(text_blocks, table_count, image_count),
            "has_tables": table_count > 0,
            "table_count": table_count,
            "has_images": image_count > 0,
            "image_count": image_count,
            "is_scanned": is_scanned
        }
```

### Phase 3: Embedding Strategy Selection

```python
# backend/app/services/embedding_service_enhanced.py

class EmbeddingStrategy(Enum):
    TEXT_SEMANTIC = "text_semantic"          # Sentence-BERT
    TABLE_STRUCTURE = "table_structure"      # Table embeddings
    NUMERICAL = "numerical"                  # Number embeddings
    VISION = "vision"                        # CLIP/DINO
    CODE = "code"                            # CodeBERT
    HYBRID = "hybrid"                        # Multi-modal

class IntelligentEmbeddingService:
    """
    Select and apply appropriate embedding strategy
    based on document type and content analysis
    """

    def __init__(self):
        # Keep existing embedding model for text
        self.text_model = SentenceTransformer('all-MiniLM-L6-v2')  # 384-dim

        # Add specialized models (lazy-loaded)
        self.table_model = None
        self.vision_model = None
        self.code_model = None

    async def select_strategy(
        self,
        file_type: FileType,
        content_analysis: Dict[str, Any]
    ) -> EmbeddingStrategy:
        """
        Select optimal embedding strategy

        Decision tree:
        1. If scanned PDF → Vision or OCR+Text
        2. If tables > 50% content → Table embeddings
        3. If code file → CodeBERT
        4. If numerical data → Numerical embeddings
        5. Default → Text semantic
        """

        # Scanned documents
        if content_analysis.get("is_scanned"):
            ocr_confidence = content_analysis.get("ocr_confidence", 0)
            if ocr_confidence < 0.7:
                return EmbeddingStrategy.VISION  # Low quality OCR → use vision
            else:
                return EmbeddingStrategy.TEXT_SEMANTIC  # High quality OCR

        # Table-heavy documents
        if content_analysis.get("content_type") == ContentType.TABLE_HEAVY:
            return EmbeddingStrategy.TABLE_STRUCTURE

        # Excel/numerical data
        if file_type == FileType.EXCEL:
            return EmbeddingStrategy.NUMERICAL

        # Code files
        if content_analysis.get("content_type") == ContentType.CODE:
            return EmbeddingStrategy.CODE

        # Images
        if file_type == FileType.IMAGE:
            has_text = content_analysis.get("has_text", False)
            if has_text:
                return EmbeddingStrategy.HYBRID  # Text + visual
            else:
                return EmbeddingStrategy.VISION

        # Default: Text semantic
        return EmbeddingStrategy.TEXT_SEMANTIC

    async def generate_embedding(
        self,
        content: str,
        strategy: EmbeddingStrategy,
        metadata: Dict[str, Any] = None
    ) -> np.ndarray:
        """Generate embedding using selected strategy"""

        if strategy == EmbeddingStrategy.TEXT_SEMANTIC:
            return self.text_model.encode(content)

        elif strategy == EmbeddingStrategy.TABLE_STRUCTURE:
            return await self._embed_table(content, metadata)

        elif strategy == EmbeddingStrategy.NUMERICAL:
            return await self._embed_numerical(content, metadata)

        elif strategy == EmbeddingStrategy.VISION:
            return await self._embed_visual(content, metadata)

        elif strategy == EmbeddingStrategy.CODE:
            return await self._embed_code(content)

        elif strategy == EmbeddingStrategy.HYBRID:
            # Combine multiple embeddings
            text_emb = self.text_model.encode(content)
            vision_emb = await self._embed_visual(content, metadata)
            return np.concatenate([text_emb, vision_emb])

    async def _embed_table(self, table_text: str, metadata: Dict) -> np.ndarray:
        """
        Embed table structure + content

        Approach:
        1. Parse table structure (rows, columns, headers)
        2. Embed column headers separately
        3. Embed numerical values using numerical embeddings
        4. Combine: [header_emb, numerical_emb, structure_emb]
        """
        # TODO: Implement table-specific embeddings
        # For now, fallback to text
        return self.text_model.encode(table_text)

    async def _embed_numerical(self, data: str, metadata: Dict) -> np.ndarray:
        """
        Embed numerical data

        Approach:
        1. Extract numerical values
        2. Compute statistics (mean, median, range)
        3. Embed column names/headers
        4. Create hybrid embedding: [stats_vector, header_emb]
        """
        # TODO: Implement numerical embeddings
        return self.text_model.encode(data)

    async def _embed_visual(self, image_path: str, metadata: Dict) -> np.ndarray:
        """
        Embed visual content using CLIP or DINO

        Approach:
        1. Load image
        2. Generate visual embedding (768-dim CLIP)
        3. Optionally combine with OCR text embedding
        """
        if self.vision_model is None:
            # Lazy load vision model
            from transformers import CLIPModel, CLIPProcessor
            self.vision_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
            self.vision_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

        # TODO: Implement vision embeddings
        return np.zeros(512)  # Placeholder

    async def _embed_code(self, code: str) -> np.ndarray:
        """
        Embed code using CodeBERT

        Approach:
        1. Use CodeBERT model
        2. Preserve syntax and semantics
        """
        if self.code_model is None:
            # Lazy load CodeBERT
            from transformers import AutoTokenizer, AutoModel
            self.code_model = AutoModel.from_pretrained("microsoft/codebert-base")
            self.code_tokenizer = AutoTokenizer.from_pretrained("microsoft/codebert-base")

        # TODO: Implement code embeddings
        return self.text_model.encode(code)
```

### Phase 4: Multi-Index Vector Database

**Extend PostgreSQL schema to support multiple embedding types:**

```sql
-- Add embedding strategy column
ALTER TABLE document_chunks
ADD COLUMN embedding_strategy VARCHAR(50) DEFAULT 'text_semantic';

-- Add secondary embeddings for hybrid approach
ALTER TABLE document_chunks
ADD COLUMN visual_embedding VECTOR(512);  -- CLIP embeddings

ALTER TABLE document_chunks
ADD COLUMN numerical_embedding VECTOR(128);  -- Numerical data

-- Create separate indexes for each embedding type
CREATE INDEX idx_chunks_visual_embedding
ON document_chunks USING ivfflat (visual_embedding vector_cosine_ops);

CREATE INDEX idx_chunks_numerical_embedding
ON document_chunks USING ivfflat (numerical_embedding vector_cosine_ops);
```

### Phase 5: Query-Time Strategy Selection

**Match query type to embedding strategy:**

```python
# During retrieval
async def query_with_intelligent_embedding(
    query: str,
    detected_query_type: str  # "table_search", "image_search", "code_search"
) -> List[Chunk]:
    """
    Use appropriate embedding strategy for query
    based on what user is searching for
    """

    if detected_query_type == "table_search":
        # User asking about table data
        query_embedding = embedding_service.generate_embedding(
            query,
            strategy=EmbeddingStrategy.TABLE_STRUCTURE
        )
        # Search in table_embedding index

    elif detected_query_type == "image_search":
        # User asking about visual content
        query_embedding = embedding_service.generate_embedding(
            query,
            strategy=EmbeddingStrategy.VISION
        )
        # Search in visual_embedding index

    else:
        # Default text search
        query_embedding = embedding_service.generate_embedding(
            query,
            strategy=EmbeddingStrategy.TEXT_SEMANTIC
        )
        # Search in text_embedding index
```

---

## Benefits

### 1. Improved Retrieval Accuracy
- ✅ Tables: Find by structure and numerical similarity, not just text
- ✅ Images: Visual similarity search (find similar diagrams)
- ✅ Code: Semantic code search (find similar functions)
- ✅ Numerical: Statistical similarity (find datasets with similar distributions)

### 2. Better User Experience
- ✅ "Find tables with sales data" → Searches table embeddings
- ✅ "Show me similar floor plans" → Visual similarity search
- ✅ "Find code that implements sorting" → Semantic code search

### 3. Resource Efficiency
- ✅ Lazy-load specialized models only when needed
- ✅ Use lightweight OCR for scanned docs instead of expensive vision models
- ✅ Cache embeddings per strategy

---

## Implementation Priority

### P0 (Critical - Do First)
1. **Content Analyzer**: Detect scanned vs digital PDFs
2. **OCR Strategy**: High-quality OCR → text embeddings, Low-quality → vision fallback
3. **Table Detection**: Identify table-heavy documents

### P1 (High Priority)
4. **Table Embeddings**: Structure + numerical similarity
5. **Vision Embeddings**: CLIP for diagrams/images
6. **Multi-Index Search**: Separate indexes for different embedding types

### P2 (Nice to Have)
7. **Code Embeddings**: CodeBERT for code files
8. **Hybrid Embeddings**: Combine text + visual for rich documents
9. **Numerical Embeddings**: Statistical similarity for data

---

## Example: Merit SelectScience PDF

**Current Approach:**
```
1. Upload PDF
2. Extract text with docling_pdf
3. Embed ALL text using Sentence-BERT
4. Store in vector DB
```

**Intelligent Approach:**
```
1. Upload PDF
2. Analyze content: "Contains 3 tables, 5 images, mostly text"
3. Route:
   - Text sections → Sentence-BERT (384-dim)
   - Tables → Table structure embeddings + numerical (256-dim)
   - Images → CLIP vision embeddings (512-dim)
4. Store multiple embedding types:
   - text_embedding (for semantic text search)
   - table_embedding (for table/data search)
   - visual_embedding (for diagram search)
5. Query: "What are the key metrics?"
   → Search table_embeddings (finds metrics in tables)
```

---

## Next Steps

1. ✅ **Current**: Optimize tool routing (docling first, vision last)
2. 🚧 **Next**: Implement Content Analyzer
3. 🔜 **Then**: Add table embedding strategy
4. 🔜 **Then**: Add vision embedding strategy
5. 🔜 **Finally**: Multi-index retrieval

---

## References

- `resource-constrained-agentic-workflow.md`: Extract first, augment LLM later
- `dynamic-tool-orchestration-guide.md`: Tool selection based on content type
- Current codebase: `backend/app/services/embedding_service.py`

---

**Status**: Design complete, awaiting implementation approval

**Recommendation**: Start with P0 items (content analyzer, OCR strategy, table detection) in next sprint.

---

**End of Design Document**
