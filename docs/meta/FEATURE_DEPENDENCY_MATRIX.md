# Feature Dependency Matrix

**Last Updated**: 2025-11-21
**Purpose**: Document which modules use which features and technologies

---

## Feature-to-Feature Usage Matrix

| Module/Feature | Smart Extraction | AI Navigation | Template Mapping | OCR Service | Translation | Document Service | Embedding Service | LLM Service | Playwright | Vector Search |
|----------------|------------------|---------------|------------------|-------------|-------------|------------------|-------------------|-------------|------------|---------------|
| **Smart Extraction** | - | ✅ (built-in) | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ GPT-4 | ✅ | ❌ |
| **AI Navigation** | ✅ (part of) | - | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ GPT-4 Turbo | ✅ | ❌ |
| **Template Mapping** | ✅ | ❌ | - | ❌ | ❌ | ❌ | ❌ | ✅ GPT-4 | ✅ | ❌ |
| **Auto Extraction** | ✅ | ✅ (if needed) | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ GPT-4 | ✅ | ❌ |
| **CSS Extraction** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| **Document Upload** | ❌ | ❌ | ❌ | ✅ (for PDFs) | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ |
| **RAG Chat** | ❌ | ❌ | ❌ | ✅ (indirect) | ❌ | ✅ | ✅ | ✅ GPT-4 | ❌ | ✅ pgvector |
| **Web Scraper** | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ GPT-4 | ✅ | ❌ |
| **Evaluation Dashboard** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ (judge) | ❌ | ❌ |
| **Project Estimator** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ GPT-4 | ❌ | ❌ |

---

## Detailed Feature Dependencies

### 1. Smart Extraction (`/api/v1/extract/ultra-smart`)

**Primary Purpose**: Zero-configuration data extraction from websites

**Uses**:
- ✅ **LLM Service** (GPT-4): For understanding page structure and extracting data
- ✅ **Playwright**: Browser automation for rendering dynamic content
- ✅ **AI Navigation** (built-in capability): When user instructions indicate navigation needed

**Used By**:
- Auto Extraction
- Template Mapping
- Web Scraper

**Technology Stack**:
```
User Request
    ↓
Smart Extraction Engine
    ↓
├─→ Playwright (page rendering)
├─→ LLM (GPT-4) (structure analysis)
├─→ AI Navigation (if "get all X" detected)
└─→ Structured JSON Output
```

---

### 2. AI Navigation

**Primary Purpose**: Autonomous website navigation based on natural language goals

**Uses**:
- ✅ **LLM Service** (GPT-4 Turbo): For understanding navigation intent and planning
- ✅ **Playwright**: For clicking links, filling forms, navigating pages
- ✅ **Smart Extraction**: For extracting data after navigation

**Used By**:
- Smart Extraction (when needed)
- Auto Extraction (when needed)
- Web Scraper

**Technology Stack**:
```
Natural Language Goal ("get all fantasy books")
    ↓
AI Navigation Agent
    ↓
├─→ LLM (intent parsing)
├─→ Playwright (page interaction)
├─→ Navigation Path Planning
└─→ Smart Extraction (final data extraction)
```

**Navigation Flow**:
1. Parse user intent with LLM
2. Identify target page/category
3. Plan navigation steps
4. Execute clicks/navigation with Playwright
5. Extract data with Smart Extraction

---

### 3. Template Mapping (`/api/v1/extract/smart-map-to-template`)

**Primary Purpose**: Map extracted data to custom template columns

**Uses**:
- ✅ **Smart Extraction**: To extract raw data from page
- ✅ **LLM Service** (GPT-4): For semantic field mapping
- ✅ **Playwright**: For page rendering

**Used By**:
- Web Scraper (when template provided)

**Technology Stack**:
```
URL + Template Columns
    ↓
Template Mapper
    ↓
├─→ Smart Extraction (raw data)
├─→ LLM (semantic matching)
│   └─→ "Price (GBP)" ≈ "price"
│   └─→ "Stock Status" ≈ "availability"
└─→ Mapped JSON Output
```

**Semantic Matching Example**:
- Template column: "Book Title" → Matched to: "title"
- Template column: "Price (GBP)" → Matched to: "price"
- Template column: "Stock Status" → Matched to: "availability"

---

### 4. Auto Extraction (`/api/v1/extract/auto`)

**Primary Purpose**: Ultimate zero-configuration extraction (no instructions needed)

**Uses**:
- ✅ **Smart Extraction**: Core extraction engine
- ✅ **AI Navigation**: If multi-page navigation detected
- ✅ **LLM Service** (GPT-4): For auto-detecting page structure
- ✅ **Playwright**: For page rendering

**Used By**:
- (Standalone feature)

**Technology Stack**:
```
URL Only (no instructions)
    ↓
Auto Extraction
    ↓
├─→ Page Analysis (LLM)
├─→ Structure Detection (LLM)
├─→ Smart Extraction
├─→ Auto-generate template name
└─→ Structured Output
```

**Auto-Detection Capabilities**:
- Detects if page is a list or detail view
- Identifies repeated structures
- Infers field types (title, price, availability)
- Generates appropriate column names

---

### 5. CSS Extraction (`/api/v1/extract/css`) ⚠️ NOT IMPLEMENTED

**Primary Purpose**: Traditional CSS selector-based extraction

**Would Use**:
- ✅ **Playwright**: For page rendering
- ✅ **CSS Selectors**: Manual selectors provided by user

**Technology Stack** (if implemented):
```
URL + CSS Selectors
    ↓
CSS Extractor
    ↓
├─→ Playwright (rendering)
├─→ CSS Query Execution
└─→ Structured Output
```

---

### 6. Document Upload (`/api/v1/upload`)

**Primary Purpose**: Upload and process documents for RAG

**Uses**:
- ✅ **Document Service**: Core document processing
- ✅ **OCR Service**: For PDF text extraction (Docling + RapidOCR)
- ✅ **Embedding Service**: Generate 384-dim vectors
- ✅ **MinIO**: S3-compatible file storage
- ✅ **PostgreSQL**: Metadata and chunk storage

**Used By**:
- RAG Chat (provides documents for search)

**Technology Stack**:
```
File Upload
    ↓
Document Service
    ↓
├─→ OCR (if PDF)
│   ├─→ Docling (primary)
│   └─→ Tesseract (fallback)
├─→ Text Chunking
├─→ Embedding Generation
│   └─→ sentence-transformers (384-dim)
├─→ MinIO Storage
└─→ PostgreSQL + pgvector
```

**Processing Pipeline**:
1. File upload (multipart/form-data)
2. OCR extraction (if PDF)
3. Text chunking (512 chars default)
4. Embedding generation (384 dimensions)
5. Vector storage (pgvector)
6. Session association

---

### 7. RAG Chat (`/api/v1/query`)

**Primary Purpose**: Query uploaded documents with semantic search

**Uses**:
- ✅ **Document Service**: Access uploaded documents
- ✅ **Embedding Service**: Query embedding generation
- ✅ **Vector Search** (pgvector): Semantic similarity search
- ✅ **LLM Service** (GPT-4): Answer generation
- ✅ **OCR Service** (indirect): Through documents uploaded with OCR

**Used By**:
- (Standalone feature - end-user facing)

**Technology Stack**:
```
User Query
    ↓
RAG Pipeline
    ↓
├─→ Query Embedding (sentence-transformers)
├─→ Vector Search (pgvector cosine similarity)
│   └─→ Top-K retrieval (default K=5)
├─→ Context Assembly
│   ├─→ Short-term memory (session docs)
│   └─→ Long-term memory (all docs)
├─→ LLM Generation (GPT-4)
│   └─→ Context + Query → Answer
└─→ Response + Sources
```

**Memory Hierarchy**:
1. **Short-term** (session): Search session documents first
2. **Long-term** (global): Fallback to all documents
3. **Source Attribution**: Return chunks with similarity scores

---

### 8. OCR Service

**Primary Purpose**: Extract text from PDFs and images

**Uses**:
- ✅ **Docling**: Primary OCR engine
- ✅ **RapidOCR**: Fast OCR component
- ✅ **Tesseract**: Fallback OCR engine

**Used By**:
- Document Upload (for PDF processing)
- RAG Chat (indirectly through uploaded PDFs)

**Technology Stack**:
```
PDF/Image File
    ↓
OCR Service
    ↓
├─→ Docling (primary)
│   └─→ RapidOCR integration
├─→ Tesseract (fallback)
└─→ Extracted Text
```

**Fallback Chain**:
1. Try Docling + RapidOCR (70% confidence)
2. If fails → Tesseract
3. Return best result

---

### 9. Translation Service

**Primary Purpose**: Translate text between languages

**Uses**:
- ✅ **LLM Service** (primary): GPT-4 translation
- ✅ **Transformers** (fallback): Helsinki-NLP models

**Used By**:
- (Can be used by any module needing translation - not currently integrated)

**Technology Stack**:
```
Text + Source Lang + Target Lang
    ↓
Translation Service
    ↓
├─→ LLM Backend (primary)
│   └─→ GPT-4 translation
├─→ Transformers (fallback)
│   └─→ Helsinki-NLP models
└─→ Translated Text + Confidence
```

**Fallback Chain**:
1. Try LLM translation (quality: high)
2. If fails → Transformers (quality: medium)
3. Return best result with confidence score

---

### 10. Web Scraper (Frontend Component)

**Primary Purpose**: UI for data extraction features

**Uses**:
- ✅ **Smart Extraction**: Primary extraction method
- ✅ **AI Navigation**: For multi-page scraping
- ✅ **Template Mapping**: When template provided
- ✅ **Auto Extraction**: Zero-config mode

**Used By**:
- (End-user facing UI component)

**Technology Stack**:
```
Web Scraper UI
    ↓
User Selects Mode
    ↓
├─→ Smart Extraction (with instructions)
├─→ Auto Extraction (no instructions)
├─→ Template Mapping (with template)
└─→ Results Display (table/JSON/CSV)
```

---

### 11. Evaluation Dashboard ⚠️ (Not Accessible)

**Primary Purpose**: RAG evaluation metrics and analytics

**Uses**:
- ✅ **LLM Service** (GPT-4): For LLM-as-Judge evaluations
- ✅ **RAGAS**: Evaluation framework
- ✅ **DeepEval**: Additional metrics
- ✅ **BERTScore**: Semantic similarity

**Used By**:
- (Internal analytics/monitoring)

**Technology Stack** (defined but not accessible):
```
RAG Response
    ↓
Evaluation Engine
    ↓
├─→ RAGAS Metrics
│   ├─→ Faithfulness
│   ├─→ Answer Relevancy
│   └─→ Context Precision/Recall
├─→ LLM-as-Judge (GPT-4)
├─→ DeepEval
├─→ BERTScore
└─→ Aggregated Scores + Dashboard
```

---

### 12. Project Estimator ⚠️ (Not Accessible)

**Primary Purpose**: AI-powered project estimation with 6-agent workflow

**Uses**:
- ✅ **LLM Service** (GPT-4): Powers all 6 agents
- ✅ **LangGraph**: Agent orchestration

**Used By**:
- (Standalone estimation tool)

**Technology Stack** (defined but not accessible):
```
Project Description
    ↓
6-Agent Workflow (LangGraph)
    ↓
├─→ Agent 1: Analyst
│   └─→ Extract requirements
├─→ Agent 2: Team Planner
│   └─→ Identify teams needed
├─→ Agent 3: Task Generator
│   └─→ Generate project tasks
├─→ Agent 4: Workflow Agent
│   └─→ Create phases/timeline
├─→ Agent 5: Rate Assignment
│   └─→ Map tasks to rates
└─→ Agent 6: Document Generator
    ├─→ BRD.pptx
    └─→ CostEstimate.xlsx
```

---

## Technology Stack Summary

### Backend Technologies

| Technology | Used By | Purpose |
|------------|---------|---------|
| **OpenAI GPT-4** | Smart Extraction, Template Mapping, Auto Extraction, RAG Chat, Evaluation, Project Estimator | LLM inference for understanding and generation |
| **OpenAI GPT-4 Turbo** | AI Navigation | Faster LLM for navigation planning |
| **Playwright** | Smart Extraction, AI Navigation, Template Mapping, Auto Extraction, CSS Extraction | Browser automation and rendering |
| **Docling** | OCR Service, Document Upload | Primary PDF/image OCR |
| **RapidOCR** | OCR Service | Fast OCR component |
| **Tesseract** | OCR Service | Fallback OCR |
| **sentence-transformers** | Document Upload, RAG Chat | 384-dim embedding generation |
| **pgvector** | Document Upload, RAG Chat | Vector similarity search |
| **PostgreSQL** | All modules | Database and vector storage |
| **MinIO** | Document Upload | S3-compatible file storage |
| **Redis** | RAG Chat | Semantic caching |
| **Transformers (Helsinki-NLP)** | Translation Service | Fallback translation |
| **LangGraph** | Project Estimator | Agent orchestration |
| **RAGAS** | Evaluation Dashboard | RAG evaluation metrics |
| **DeepEval** | Evaluation Dashboard | Additional evaluation |
| **BERTScore** | Evaluation Dashboard | Semantic similarity scoring |

---

## Feature Integration Patterns

### Pattern 1: LLM-Powered Extraction
```
User Input (natural language)
    ↓
LLM (GPT-4) - Understanding
    ↓
Playwright - Browser Automation
    ↓
LLM (GPT-4) - Data Structuring
    ↓
Structured Output (JSON)
```

**Used By**: Smart Extraction, AI Navigation, Template Mapping, Auto Extraction

---

### Pattern 2: Multi-Backend Fallback
```
Primary Backend (LLM)
    ↓
If Fails
    ↓
Secondary Backend (Transformers/Tesseract)
    ↓
Return Best Result + Confidence
```

**Used By**: Translation Service, OCR Service

---

### Pattern 3: RAG Pipeline
```
Documents
    ↓
OCR (if PDF) → Chunking → Embedding
    ↓
pgvector Storage
    ↓
Query → Embedding → Vector Search → Context
    ↓
LLM Generation
    ↓
Answer + Sources
```

**Used By**: Document Upload → RAG Chat

---

### Pattern 4: Agent Workflow
```
Input (description/requirements)
    ↓
LangGraph Orchestration
    ↓
├─→ Agent 1 (Analysis)
├─→ Agent 2 (Planning)
├─→ Agent 3 (Task Gen)
├─→ Agent 4 (Workflow)
├─→ Agent 5 (Costing)
└─→ Agent 6 (Documentation)
    ↓
Output (BRD + Excel)
```

**Used By**: Project Estimator

---

## External API Dependencies

| API Provider | Features Using It | Purpose | Cost Impact |
|--------------|------------------|---------|-------------|
| **OpenAI** | Smart Extraction, AI Navigation, Template Mapping, Auto Extraction, RAG Chat, Evaluation, Project Estimator | LLM inference | ~$0.50/test session |
| **None (Local)** | Transformers Translation, sentence-transformers embeddings | Free local inference | $0 |
| **None (Self-hosted)** | PostgreSQL, pgvector, MinIO, Redis, Playwright | Infrastructure | Infrastructure costs only |

---

## Data Flow: End-to-End Example

### Example: Web Scraping with AI Navigation

```
1. User Input:
   - URL: https://books.toscrape.com/
   - Instruction: "get all mystery books"

2. Smart Extraction receives request
   ↓
3. Detects navigation keywords ("get all X")
   ↓
4. Delegates to AI Navigation
   ↓
5. AI Navigation workflow:
   a. LLM (GPT-4 Turbo) parses intent
   b. Identifies target: "Mystery" category
   c. Playwright opens homepage
   d. LLM finds "Mystery" link
   e. Playwright clicks link
   f. Navigates to mystery page
   ↓
6. Smart Extraction takes over:
   a. LLM analyzes page structure
   b. Identifies book listing pattern
   c. Extracts: title, price, availability
   d. Structures data as JSON table
   ↓
7. Returns 20 mystery books with metadata:
   - success: true
   - row_count: 20
   - table: [{title, price, availability}, ...]
   - extraction_metadata:
       - navigation_path: [homepage, mystery category]
       - steps_taken: 2
```

---

## Performance Characteristics by Feature

| Feature | Avg Time | Items/Second | LLM Calls | Cost/Request |
|---------|----------|--------------|-----------|--------------|
| **Smart Extraction** | ~6s | 3.3 items/s | 1-2 | ~$0.05 |
| **AI Navigation** | ~12s | 1.7 items/s | 2-3 | ~$0.10 |
| **Template Mapping** | ~5s | 0.2 items/s | 1-2 | ~$0.05 |
| **Auto Extraction** | ~6s | 3.3 items/s | 1-2 | ~$0.05 |
| **Document Upload** | 0.17s | 5.9 files/s | 0 | $0 |
| **RAG Chat** | 2-4s | - | 1 | ~$0.02 |
| **OCR Service** | ~3.25s | - | 0 | $0 |
| **Translation** | ~4s | 0.25 sent/s | 0-1 | ~$0.01 |

---

## Recommendations for Feature Combination

### Best Practices

1. **E-Commerce Scraping**:
   - Use: **Auto Extraction** (fastest, zero-config)
   - Alternative: **Smart Extraction** with clear instructions
   - Add: **Template Mapping** for consistent schema

2. **Multi-Page Data Collection**:
   - Use: **Smart Extraction** with navigation keywords ("get all X")
   - Automatically engages: **AI Navigation**
   - Result: Autonomous multi-page extraction

3. **Document Processing for RAG**:
   - Use: **Document Upload** (includes OCR for PDFs)
   - Automatically uses: **OCR Service** → **Embedding Service**
   - Then use: **RAG Chat** for querying

4. **Competitive Analysis**:
   - Use: **Template Mapping** for consistent fields
   - Ensures: Same schema across competitors
   - Export: Structured comparison tables

5. **Content Translation**:
   - Use: **Translation Service** (automatic fallback)
   - Primary: LLM (high quality)
   - Fallback: Transformers (always works)

---

## Feature Maturity Status

| Feature | Status | Accessibility | Production Ready |
|---------|--------|---------------|------------------|
| **Smart Extraction** | ✅ Stable | ✅ Accessible | ✅ Yes |
| **AI Navigation** | ✅ Stable | ✅ Accessible | ✅ Yes |
| **Template Mapping** | ✅ Stable | ✅ Accessible | ✅ Yes |
| **Auto Extraction** | ✅ Stable | ✅ Accessible | ✅ Yes |
| **CSS Extraction** | ❌ Missing | ❌ 404 | ❌ No |
| **Document Upload** | ✅ Stable | ✅ Accessible | ✅ Yes |
| **RAG Chat** | ⚠️ Partial | ✅ Accessible | ⚠️ Needs API key |
| **OCR Service** | ✅ Stable | ✅ Accessible | ✅ Yes |
| **Translation** | ✅ Stable | ✅ Accessible | ✅ Yes |
| **Evaluation Dashboard** | ⚠️ Defined | ❌ Not accessible | ⚠️ Needs config |
| **Project Estimator** | ⚠️ Defined | ❌ Not accessible | ⚠️ Needs debug |

---

**Last Updated**: 2025-11-21
**Document Version**: 1.0
**Related Documents**:
- `COMPREHENSIVE_MODULE_TESTING_SUMMARY.md`
- `docs/features/samples/FINAL_TEST_RESULTS.md`
