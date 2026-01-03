# Technology Consolidation & Component Reuse Matrix
## Leveraging Tier 1 Stack for 23 Merit AIML POCs

> **Last Updated**: 2026-01-02
> **Purpose**: Comprehensive mapping of POC requirements to existing Tier 1 components, identifying reuse opportunities and technology gaps

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Component Reuse Matrix](#component-reuse-matrix)
3. [Technology Consolidation](#technology-consolidation)
4. [Gap Analysis](#gap-analysis)
5. [Database Schema Mapping](#database-schema-mapping)
6. [Frontend Component Mapping](#frontend-component-mapping)
7. [Implementation Priority Matrix](#implementation-priority-matrix)

---

## Executive Summary

### Reusability Overview

| Reusability Tier | POC Count | Percentage | Implementation Effort |
|------------------|-----------|------------|----------------------|
| **High (70-90%)** | 14 POCs | 61% | Low - Mostly configuration |
| **Medium (50-70%)** | 7 POCs | 30% | Medium - Moderate new development |
| **Low (30-50%)** | 2 POCs | 9% | High - Significant new components |

### Key Findings

✅ **Highly Reusable Services** (Used by 70%+ of POCs):
- **LLMService**: 23/23 POCs (100%)
- **EmbeddingService**: 18/23 POCs (78%)
- **DocumentService**: 15/23 POCs (65%)
- **RAGService**: 12/23 POCs (52%)
- **ExportService**: 16/23 POCs (70%)

⚠️ **Technology Gaps** (Need to Build):
- **ML Model Service**: Scikit-learn hosting (4 POCs)
- **Vision Processing Service**: GPT-4 Vision integration (1 POC)
- **Template Engine Service**: Jinja2 + DOCX/PDF generation (3 POCs)
- **Email Parser Service**: MIME parsing (2 POCs)
- **Neo4j Service**: Knowledge graph (1 POC)

🎯 **Quick Wins** (High Reusability, Low Effort):
1. Generic RAG (90% reusability)
2. Relation Extractor (85% reusability)
3. Docu Extract (85% reusability)
4. Taxonomy Classification (80% reusability)
5. Talent Pulse (75% reusability)

---

## Component Reuse Matrix

### POC-to-Service Mapping

| POC # | POC Name | LLM | Embed | RAG | Doc | Export | Scraper | ML | Vision | Template | Neo4j | Reuse % |
|-------|----------|-----|-------|-----|-----|--------|---------|----|----|----------|-------|---------|
| 1 | Agri Taxonomy | ✅ | ✅ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | **80%** |
| 2 | Agronomy Decision (3 modules) | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | **70%** |
| 3 | Bot Detect Analyzer | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | **60%** |
| 4 | Credit Profile Analyzer | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ | **75%** |
| 5 | Dashboard (Central Portal) | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | **90%** |
| 6 | Docu Extract | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | **85%** |
| 7 | Email Bounce Intelligence | ✅ | ✅ | ❌ | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | **65%** |
| 8 | Email Campaign Analyzer | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | **60%** |
| 9 | Fashion Tagging | ✅ | ✅ | ❌ | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | **70%** |
| 10 | Generic RAG | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | **90%** |
| 11 | Maritime Report Gen | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ | **80%** |
| 12 | MineScope CRU | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | **85%** |
| 13 | Planning Classifier | ✅ | ✅ | ❌ | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | **75%** |
| 14 | Procurement Matcher | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | **85%** |
| 15 | Relation Extractor | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | **85%** |
| 16 | Spend Smart | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ | **65%** |
| 17 | Talent Pulse | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | **75%** |
| 18 | Talent Search | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | **80%** |
| 19 | Taxonomy Classification | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | **80%** |
| 20 | Taxonomy Skillmatch | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | **75%** |
| 21 | Tender Intelligence | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | **80%** |
| 22 | Vendor Recommendation | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | **80%** |
| 23 | Zero Shot NER (Flexitag) | ✅ | ✅ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | **80%** |
| **TOTAL** | **23 POCs** | 23 | 20 | 16 | 22 | 23 | 4 | 5 | 1 | 2 | 1 | **Avg: 77%** |

**Legend**:
- ✅ = Component is used by POC
- ❌ = Component not needed
- **Reuse %** = Percentage of POC functionality covered by existing Tier 1 services

---

## Technology Consolidation

### 1. LLM & AI Model Requirements

#### Existing Coverage (Tier 1 LLMService)

| Provider | Models Available | POCs Using |
|----------|-----------------|------------|
| **OpenAI** | GPT-4, GPT-4o, GPT-4o-mini, GPT-3.5-turbo | 20 POCs (87%) |
| **Anthropic** | Claude Sonnet, Claude Opus | 0 POCs (available but unused) |
| **vLLM** | Mistral, Llama (local GPU) | 0 POCs (available but unused) |
| **Ollama** | All Ollama models (local CPU) | 0 POCs (available but unused) |

✅ **Assessment**: Existing LLMService covers 100% of POC requirements

#### New Requirements (Vision Models)

| Model Type | Use Case | POCs |
|------------|----------|------|
| **GPT-4 Vision** | Fashion image attribute extraction | Fashion Tagging (1 POC) |

⚠️ **Gap**: Need to add GPT-4 Vision support to LLMService or create VisionService

---

### 2. Embedding & Vector Search Requirements

#### Existing Coverage (Tier 1 EmbeddingService)

| Embedding Type | Model | Dimension | POCs Using |
|----------------|-------|-----------|------------|
| **Text Semantic** | all-MiniLM-L6-v2 | 384 | 18 POCs (78%) |
| **OpenAI** | text-embedding-ada-002 | 1536 | 2 POCs (9%) |
| **Table Structure** | Custom | 512 | 0 POCs |
| **Visual** | CLIP | 512 | 1 POC (Fashion Tagging) |

✅ **Assessment**: 90% coverage. Minor additions needed for OpenAI embeddings

---

### 3. Document Processing Requirements

#### Existing Coverage (Tier 1 DocumentService)

| Format | Supported | POCs Using |
|--------|-----------|------------|
| **PDF** | ✅ Yes (PyPDF2, Docling) | 12 POCs (52%) |
| **DOCX** | ✅ Yes (python-docx) | 8 POCs (35%) |
| **CSV** | ✅ Yes (Pandas) | 20 POCs (87%) |
| **TXT** | ✅ Yes (native) | 15 POCs (65%) |
| **JSON** | ✅ Yes (native) | 18 POCs (78%) |
| **XLSX** | ✅ Yes (openpyxl) | 10 POCs (43%) |
| **Email (MIME)** | ❌ **GAP** | 2 POCs (9%) |
| **Images (JPG, PNG)** | ✅ Yes (OCR + Vision) | 1 POC (4%) |

⚠️ **Gap**: Need EmailParserService for MIME parsing

---

### 4. Database & Storage Requirements

#### Existing Infrastructure

| Component | Technology | Coverage |
|-----------|-----------|----------|
| **Relational DB** | PostgreSQL 16 + pgvector | ✅ 100% |
| **Vector Search** | pgvector (384, 512, 768 dims) | ✅ 90% |
| **Object Storage** | MinIO | ✅ 100% |
| **Cache** | Redis (VSS) | ✅ 100% |
| **Full-text Search** | Elasticsearch (optional) | ✅ 100% |
| **Graph DB** | Neo4j | ❌ **GAP** (1 POC) |

⚠️ **Gap**: Need Neo4j integration for Spend Smart knowledge graph

#### New Tables Needed (See Database Schema Mapping section)

---

### 5. Machine Learning Requirements

#### Existing Coverage

| ML Task | Tier 1 Support | Coverage |
|---------|----------------|----------|
| **LLM Inference** | ✅ LLMService | 100% |
| **Embeddings** | ✅ EmbeddingService | 100% |
| **Classification (Traditional ML)** | ❌ **GAP** | 0% |
| **Regression (Traditional ML)** | ❌ **GAP** | 0% |

#### New Requirements (Traditional ML)

| POC | Model Type | Library | Purpose |
|-----|------------|---------|---------|
| **Agronomy Decision** | RandomForest, GradientBoosting | Scikit-learn | Yield prediction, disease detection |
| **Bot Detect Analyzer** | RandomForest | Scikit-learn | Bot classification |
| **Email Bounce Intelligence** | Logistic Regression, RandomForest | Scikit-learn | Bounce classification |
| **Email Campaign Analyzer** | RandomForest | Scikit-learn | Bot detection |
| **Planning Classifier** | MultiLabel classifier | Scikit-learn | Planning document classification |

⚠️ **Gap**: Need **MLModelService** to host Scikit-learn models

**Recommendation**:
```python
# backend/app/tier_1/ml_models/ml_model_service.py
class MLModelService:
    """Host and serve Scikit-learn models"""

    async def load_model(self, model_path: str, model_type: str)
    async def predict(self, model_id: str, features: List[float])
    async def train_model(self, training_data, model_config)
    async def save_model(self, model, model_id: str)
```

---

### 6. Export & Reporting Requirements

#### Existing Coverage (Tier 1 ExportService)

| Format | Supported | POCs Using |
|--------|-----------|------------|
| **JSON** | ✅ Yes | 23 POCs (100%) |
| **CSV** | ✅ Yes | 20 POCs (87%) |
| **Excel (XLSX)** | ✅ Yes (openpyxl) | 16 POCs (70%) |
| **PDF** | ✅ Yes (ReportLab) | 5 POCs (22%) |
| **DOCX** | ✅ Partial | 3 POCs (13%) |

#### New Requirements (Template-based Reports)

| POC | Document Type | Template Engine | Purpose |
|-----|--------------|-----------------|---------|
| **Credit Profile Analyzer** | DOCX | Jinja2 + python-docx | Structured credit reports |
| **Maritime Report** | DOCX/PDF | Jinja2 + docxtpl | Casualty reports |

⚠️ **Gap**: Need **TemplateEngineService** for Jinja2 + DOCX generation

**Recommendation**:
```python
# backend/app/tier_1/export/template_engine_service.py
class TemplateEngineService:
    """Generate documents from Jinja2 templates"""

    async def render_docx(self, template_path: str, context: Dict)
    async def render_pdf(self, template_path: str, context: Dict)
    async def load_template(self, template_id: str)
    async def save_template(self, template: str, template_id: str)
```

---

### 7. Web Scraping Requirements

#### Existing Coverage (Tier 1 ScraperService)

| Feature | Supported | POCs Using |
|---------|-----------|------------|
| **Playwright Automation** | ✅ Yes | 4 POCs (17%) |
| **CSS/XPath Extraction** | ✅ Yes | 4 POCs (17%) |
| **LLM Extraction** | ✅ Yes | 4 POCs (17%) |
| **Rate Limiting** | ✅ Yes | 4 POCs (17%) |
| **Proxy Rotation** | ✅ Yes | 4 POCs (17%) |

✅ **Assessment**: 100% coverage for scraping POCs (MineScope, Spend Smart, Talent Search, Tender Intelligence)

---

## Gap Analysis

### Summary of New Components Needed

| # | Component | Priority | POCs Affected | Effort | Timeline |
|---|-----------|----------|---------------|--------|----------|
| 1 | **MLModelService** | 🔴 **High** | 5 POCs (22%) | Medium | 2-3 weeks |
| 2 | **VisionService** | 🟡 **Medium** | 1 POC (4%) | Low | 1 week |
| 3 | **TemplateEngineService** | 🟡 **Medium** | 3 POCs (13%) | Low | 1-2 weeks |
| 4 | **EmailParserService** | 🟡 **Medium** | 2 POCs (9%) | Low | 1 week |
| 5 | **Neo4jService** | 🟢 **Low** | 1 POC (4%) | High | 3-4 weeks |
| 6 | **OpenAI Embeddings Support** | 🟡 **Medium** | 2 POCs (9%) | Very Low | 2-3 days |
| 7 | **Reference Data Service** | 🟡 **Medium** | 3 POCs (13%) | Low | 1 week |

### Detailed Gap Analysis

#### 1. MLModelService (Priority: High)

**Purpose**: Host and serve Scikit-learn ML models for traditional ML tasks

**Functionality**:
- Model training (RandomForest, GradientBoosting, Logistic Regression)
- Model persistence (joblib/pickle)
- Prediction API (REST endpoints)
- Model versioning & registry
- Feature preprocessing
- Model evaluation metrics

**Technology Stack**:
- Scikit-learn 1.3+
- Joblib (model persistence)
- FastAPI (endpoints)
- PostgreSQL (model metadata)
- MinIO (model storage)

**API Design**:
```python
POST /api/v1/ml/train
POST /api/v1/ml/predict
GET  /api/v1/ml/models
GET  /api/v1/ml/models/{model_id}
DELETE /api/v1/ml/models/{model_id}
```

**Integration**:
```python
from app.tier_1.ml_models.ml_model_service import MLModelService

ml_service = MLModelService()
prediction = await ml_service.predict(
    model_id="bot_detector_rf",
    features=[0.8, 120, 0.3, ...]  # Engagement rate, emails sent, etc.
)
```

---

#### 2. VisionService (Priority: Medium)

**Purpose**: GPT-4 Vision integration for image analysis

**Functionality**:
- Image-to-text description
- Attribute extraction from images
- Multi-image analysis
- Batch processing

**Technology Stack**:
- OpenAI GPT-4 Vision API
- PIL/Pillow (image preprocessing)
- Base64 encoding

**API Design**:
```python
POST /api/v1/vision/analyze
POST /api/v1/vision/extract-attributes
POST /api/v1/vision/batch-analyze
```

**Integration**:
```python
from app.tier_1.llm.vision_service import VisionService

vision_service = VisionService()
attributes = await vision_service.extract_attributes(
    image_path="fashion_item.jpg",
    attribute_schema=FashionAttributeSchema
)
```

---

#### 3. TemplateEngineService (Priority: Medium)

**Purpose**: Generate DOCX/PDF documents from Jinja2 templates

**Functionality**:
- Jinja2 template rendering
- DOCX generation (python-docx + docxtpl)
- PDF generation (ReportLab or WeasyPrint)
- Template management (CRUD)
- Template versioning

**Technology Stack**:
- Jinja2
- python-docx
- docxtpl
- WeasyPrint or ReportLab
- MinIO (template storage)

**API Design**:
```python
POST /api/v1/templates/render-docx
POST /api/v1/templates/render-pdf
GET  /api/v1/templates
POST /api/v1/templates/upload
```

---

#### 4. EmailParserService (Priority: Medium)

**Purpose**: Parse MIME email messages and classify bounces

**Functionality**:
- MIME message parsing
- Bounce classification (hard/soft/transient)
- Header extraction
- Attachment handling
- Bounce pattern matching

**Technology Stack**:
- email (Python stdlib)
- mailparser
- Regex patterns

**API Design**:
```python
POST /api/v1/email/parse
POST /api/v1/email/classify-bounce
POST /api/v1/email/extract-headers
```

---

#### 5. Neo4jService (Priority: Low)

**Purpose**: Knowledge graph for Spend Smart POC

**Functionality**:
- Graph creation & querying
- Relationship mapping
- Cypher query execution
- Graph visualization data

**Technology Stack**:
- Neo4j Python driver
- Cypher query language
- Docker Neo4j container

**API Design**:
```python
POST /api/v1/graph/create-nodes
POST /api/v1/graph/create-relationships
POST /api/v1/graph/query
GET  /api/v1/graph/visualize
```

---

#### 6. OpenAI Embeddings Support (Priority: Medium)

**Enhancement**: Add OpenAI embeddings to EmbeddingService

**Changes**:
```python
# In tier_1/embeddings/embedding_service.py
async def generate_embedding(
    self,
    text: str,
    model: str = "sentence-transformers"  # or "openai"
) -> List[float]:
    if model == "openai":
        return await self._openai_embed(text)  # ✅ Add this
    else:
        return await self._sentence_transformer_embed(text)
```

---

#### 7. Reference Data Service (Priority: Medium)

**Purpose**: Manage reference datasets (companies, commodities, assets)

**Functionality**:
- CRUD for reference data
- Search & filter
- Data validation
- Bulk import/export

**POCs Using**:
- MineScope (mining companies, commodities)
- Maritime Report (vessel types, incident types)
- Spend Smart (supplier database)

**Database Tables**:
```sql
CREATE TABLE reference_companies (...);
CREATE TABLE reference_commodities (...);
CREATE TABLE reference_assets (...);
```

---

## Database Schema Mapping

### New Tables Required by POC

| POC | Tables | Purpose |
|-----|--------|---------|
| **Agri Taxonomy** | `agri_taxonomy_results` | Store taxonomy extraction results |
| **Agronomy Decision** | `agronomy_predictions`, `agronomy_models` | Store predictions + ML models |
| **Bot Detect** | `email_bot_analysis`, `email_patterns` | Bot detection results |
| **Credit Profile** | `credit_profiles`, `credit_reports` | Credit analysis data |
| **Docu Extract** | `planning_extractions`, `planning_entities` | Planning document extractions |
| **Email Bounce** | `email_bounces`, `bounce_patterns` | Bounce analysis |
| **Email Campaign** | `campaign_analysis` | Campaign analysis results |
| **Fashion Tagging** | `fashion_attributes`, `fashion_ontology` | Fashion attribute data |
| **Generic RAG** | `rag_queries`, `rag_results` | RAG query logs (use existing tables) |
| **Maritime Report** | `maritime_reports`, `maritime_templates` | Casualty reports |
| **MineScope** | `mining_reports`, `mining_entities`, `mining_variables` | Mining intelligence |
| **Planning Classifier** | `planning_classifications` | Classification results |
| **Procurement Matcher** | `procurement_matches`, `legal_cases` | Procurement matching |
| **Relation Extractor** | `entity_relations`, `extracted_entities` | Entity-relationship data |
| **Spend Smart** | `procurement_graph_nodes`, `procurement_graph_edges` | Neo4j sync tables |
| **Talent Pulse** | `resume_screenings`, `candidate_scores` | Resume screening results |
| **Talent Search** | `job_postings`, `recruiter_matches` | Job posting analysis |
| **Taxonomy Classification** | `taxonomy_results` | Multi-taxonomy classification |
| **Taxonomy Skillmatch** | `skill_matches`, `skill_taxonomy` | Resume-to-taxonomy matching |
| **Tender Intelligence** | `tender_listings`, `tender_matches` | Tender discovery |
| **Vendor Recommendation** | `vendor_recommendations` | Vendor matching |
| **Zero Shot NER** | `ner_extractions`, `ner_entities` | NER extraction results |

**Total New Tables**: ~45 tables across 23 POCs

**Recommendation**: Use a generic `poc_results` table with JSONB for rapid prototyping:

```sql
CREATE TABLE poc_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    poc_name VARCHAR(100) NOT NULL,
    session_id VARCHAR(255),
    user_id UUID REFERENCES users(id),
    input_data JSONB NOT NULL,
    output_data JSONB NOT NULL,
    processing_time_ms INT,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_poc_results_poc_name ON poc_results(poc_name);
CREATE INDEX idx_poc_results_session_id ON poc_results(session_id);
```

---

## Frontend Component Mapping

### Existing Patterns (Tier 3 POCs)

✅ **Reference Implementations**:
- `BritishCouncilRecommender.tsx` (form + results)
- `CRUMiningIntelligence.tsx` (upload + extraction)
- `GrantThorntonExtraction.tsx` (document extraction)

### Component Patterns Needed

| POC Category | UI Pattern | Components Needed |
|--------------|-----------|-------------------|
| **Text Classification** (5 POCs) | Text input → Submit → Results display | `<TextInputPanel>`, `<ClassificationResults>` |
| **Document Extraction** (8 POCs) | File upload → Process → Structured output | `<FileUploadPanel>`, `<ExtractionResults>` (existing) |
| **CSV Analysis** (10 POCs) | CSV upload → Analyze → Charts + Export | `<CSVUploadPanel>`, `<AnalysisDashboard>`, `<ChartDisplay>` |
| **Image Analysis** (1 POC) | Image upload → Attributes → Display | `<ImageUploadPanel>`, `<AttributeDisplay>` |
| **Report Generation** (3 POCs) | Form input → Generate → Download | `<ReportForm>`, `<ReportPreview>`, `<DownloadButton>` |
| **Search & Match** (5 POCs) | Query input → Search → Results list | `<SearchBar>`, `<MatchResults>`, `<FilterPanel>` |

### Reusable Frontend Components

**Create Component Library**:
```
frontend/src/components/poc/
├── inputs/
│   ├── TextInputPanel.tsx
│   ├── CSVUploadPanel.tsx
│   ├── ImageUploadPanel.tsx
│   └── JSONInputPanel.tsx
├── results/
│   ├── ClassificationResults.tsx
│   ├── ExtractionResults.tsx (existing)
│   ├── AnalysisDashboard.tsx
│   └── MatchResults.tsx
├── controls/
│   ├── SubmitButton.tsx
│   ├── ExportButton.tsx
│   └── FilterPanel.tsx
└── shared/
    ├── LoadingSpinner.tsx
    ├── ErrorDisplay.tsx
    └── SuccessBanner.tsx
```

---

## Implementation Priority Matrix

### Phase 1: Infrastructure (Weeks 1-4)

**Build New Services** (4 weeks):

| Week | Component | Effort | POCs Unblocked |
|------|-----------|--------|----------------|
| 1-2 | MLModelService | Medium | 5 POCs |
| 2 | VisionService | Low | 1 POC |
| 3 | TemplateEngineService | Low | 3 POCs |
| 3 | EmailParserService | Low | 2 POCs |
| 4 | OpenAI Embeddings | Very Low | 2 POCs |
| 4 | ReferenceDataService | Low | 3 POCs |

**Deliverables**:
- 6 new Tier 1 services
- API documentation
- Unit tests (>80% coverage)
- Integration tests

---

### Phase 2: Quick Wins (Weeks 5-8)

**Implement High-Reusability POCs** (4 weeks):

| Week | POC | Reuse % | Effort | Team |
|------|-----|---------|--------|------|
| 5 | Generic RAG | 90% | 3 days | 1 dev |
| 5 | Docu Extract | 85% | 4 days | 1 dev |
| 6 | Relation Extractor | 85% | 4 days | 1 dev |
| 6 | Procurement Matcher | 85% | 5 days | 1 dev |
| 7 | Taxonomy Classification | 80% | 5 days | 1 dev |
| 7 | Tender Intelligence | 80% | 5 days | 1 dev |
| 8 | Talent Pulse | 75% | 5 days | 1 dev |
| 8 | Planning Classifier | 75% | 5 days | 1 dev |

**Deliverables**:
- 8 POCs implemented (backend + frontend)
- Integration tests
- User documentation

---

### Phase 3: Medium Complexity (Weeks 9-14)

**Implement Medium-Reusability POCs** (6 weeks):

| Week | POC | Reuse % | Complexity | Effort |
|------|-----|---------|------------|--------|
| 9 | Agri Taxonomy | 80% | Low | 5 days |
| 9-10 | MineScope CRU | 85% | Medium | 7 days |
| 10-11 | Maritime Report Gen | 80% | Medium | 8 days |
| 11-12 | Credit Profile Analyzer | 75% | Medium | 8 days |
| 12-13 | Talent Search | 80% | Medium | 7 days |
| 13 | Vendor Recommendation | 80% | Low | 5 days |
| 13-14 | Zero Shot NER | 80% | Medium | 6 days |

**Deliverables**:
- 7 POCs implemented
- End-to-end testing
- User training materials

---

### Phase 4: Complex POCs (Weeks 15-20)

**Implement Low-Reusability POCs** (6 weeks):

| Week | POC | Reuse % | Complexity | Effort |
|------|-----|---------|------------|--------|
| 15-17 | Agronomy Decision (3 modules) | 70% | High | 15 days |
| 17-18 | Spend Smart | 65% | High | 10 days |
| 18-19 | Fashion Tagging | 70% | Medium | 8 days |
| 19 | Email Bounce Intelligence | 65% | Medium | 6 days |
| 20 | Email Campaign Analyzer | 60% | Medium | 5 days |
| 20 | Bot Detect Analyzer | 60% | Medium | 5 days |

**Special**:
- Week 16-17: Neo4j setup for Spend Smart
- Week 18: Vision service integration for Fashion Tagging

**Deliverables**:
- 6 complex POCs implemented
- Performance optimization
- Scalability testing

---

### Phase 5: Dashboard & Integration (Weeks 21-22)

**Central Dashboard** (2 weeks):

| Week | Component | Effort |
|------|-----------|--------|
| 21 | Dashboard backend | 3 days |
| 21 | Dashboard frontend | 4 days |
| 22 | Module integration | 3 days |
| 22 | Final testing | 2 days |

**Deliverables**:
- Central POC dashboard
- Module navigation
- User role management
- System-wide testing

---

## Summary & Recommendations

### Technology Stack Consolidation

✅ **Keep Existing**:
- FastAPI (replace all Streamlit UIs)
- PostgreSQL + pgvector (replace in-memory storage)
- React + TypeScript (replace Streamlit)
- LLMService (100% coverage)
- EmbeddingService (95% coverage)
- DocumentService (90% coverage)
- RAGService (70% coverage)
- ExportService (90% coverage)

➕ **Add New Components** (6 services):
1. MLModelService (Scikit-learn)
2. VisionService (GPT-4 Vision)
3. TemplateEngineService (Jinja2 + DOCX/PDF)
4. EmailParserService (MIME parsing)
5. Neo4jService (Knowledge graph)
6. ReferenceDataService (Master data)

### Implementation Metrics

| Metric | Value |
|--------|-------|
| **Total POCs** | 23 |
| **Average Reusability** | 77% |
| **High-Reusability POCs** | 14 (61%) |
| **New Services Needed** | 6 |
| **Total Implementation Time** | 22 weeks (5.5 months) |
| **Team Size** | 4 developers |
| **Total Developer-Weeks** | 88 weeks |
| **Developer-Months** | 22 months (parallelized to 5.5 months) |

### Success Criteria

✅ **Technical**:
- All 23 POCs integrated into unified platform
- >80% code reuse from Tier 1
- <500ms average response time
- >99.5% uptime

✅ **Business**:
- Single sign-on (SSO) across all POCs
- Unified UI/UX experience
- Centralized analytics dashboard
- Role-based access control

---

**Next Steps**:
1. ✅ POC analysis complete
2. ✅ Tech stack inventory complete
3. ✅ Consolidation & reuse matrix complete
4. ⏭️ Create detailed implementation plan
5. ⏭️ Begin Phase 1: Infrastructure development

---

**End of Document**
