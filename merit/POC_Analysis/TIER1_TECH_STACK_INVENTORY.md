# Tier 1 Core Tech Stack Inventory

> **Last Updated**: 2026-01-02
> **Purpose**: Comprehensive inventory of existing Tier 1 services and components available for POC implementations

---

## Table of Contents

1. [Backend Services](#backend-services)
2. [Database & Storage](#database--storage)
3. [Frontend Components](#frontend-components)
4. [Infrastructure](#infrastructure)
5. [Reusability Matrix](#reusability-matrix)

---

## Backend Services

### 1. LLM Services (`tier_1/llm/`)

| Service | Capabilities | Models Supported |
|---------|--------------|------------------|
| **LLMService** | Multi-provider LLM orchestration | OpenAI (GPT-4, GPT-4o, GPT-4o-mini), Claude (Sonnet, Opus), vLLM (local GPU), Ollama (local CPU), llama.cpp |
| **MCPServerService** | Model Context Protocol server integration | N/A |
| **OllamaDeploymentService** | Ollama model deployment & lifecycle | All Ollama models |
| **OllamaModelService** | Ollama model management | All Ollama models |

**Key Features**:
- Automatic GPU detection
- Dynamic model switching & fallback
- Cost tracking & usage metrics
- Unified API across all providers
- Streaming support
- Temperature/token control

---

### 2. Embeddings & Vector Services (`tier_1/embeddings/`)

| Service | Capabilities | Models |
|---------|--------------|--------|
| **EmbeddingService** | Text-to-vector embeddings with Redis caching | Sentence-Transformers (all-MiniLM-L6-v2 - 384 dim) |
| **IntelligentEmbeddingService** | Multi-strategy embeddings (text, table, visual, code, numerical) | Multiple specialized models |
| **RerankerService** | Cross-encoder reranking for improved relevance | Cross-encoder models |

**Key Features**:
- Redis VSS semantic caching
- Multi-dimensional vector support (384, 256, 512, 768 dims)
- Content-aware embedding strategy selection
- Batch processing
- Tool usage tracking

**Vector Dimensions**:
- Text semantic: 384 (all-MiniLM-L6-v2)
- Table embeddings: 512
- Visual embeddings: 512 (CLIP)
- Numerical embeddings: 256
- Code embeddings: 768 (CodeBERT)

---

### 3. RAG Services (`tier_1/rag/`)

| Service | Capabilities |
|---------|--------------|
| **RAGService** | Memory hierarchy (session + global), intelligent retrieval, source attribution |
| **IntelligentRetrievalService** | Smart retrieval with query classification |
| **MultiStrategyRAG** | Multiple retrieval strategies (vector, keyword, hybrid) |
| **ConfidenceScorer** | Confidence scoring for retrieved chunks |
| **ElasticsearchService** | Elasticsearch integration for keyword search |
| **RankFusionService** | Reciprocal rank fusion for multi-source results |
| **QueryReformulationService** | Query expansion & reformulation |

**Key Features**:
- Memory hierarchy: Session docs (short-term) → All docs (long-term)
- Hybrid search (vector + keyword)
- Reciprocal rank fusion
- Query reformulation
- Confidence scoring
- Security guardrails
- Audit logging

---

### 4. Document Processing (`tier_1/document_processing/`)

| Service | Capabilities | Supported Formats |
|---------|--------------|-------------------|
| **DocumentService** | Upload, process, chunk, embed, store | PDF, DOCX, TXT, JSON, MD, CSV, XLSX, HTML |
| **ContentAnalyzer** | Intelligent content type detection | Tables, code, text, numerical data |
| **HybridExtractionService** | Multi-strategy extraction (OCR, vision, parsing) | Images, PDFs, scanned docs |
| **OCRService** | OCR with Tesseract | Images, scanned PDFs |
| **VisionService** | Vision-based extraction (GPT-4 Vision) | Images, complex PDFs |

**Key Features**:
- MinIO storage integration
- Automatic chunking (configurable size)
- Multi-strategy embedding
- Processing status tracking
- Error handling & retry
- Metadata extraction

---

### 5. Data Extraction (`tier_1/data_extraction/`)

**Advanced Web Scraping Suite**:

| Component | Purpose |
|-----------|---------|
| **ScraperService** | Main orchestration service |
| **ScraperEngine** | Playwright-powered scraping |
| **NavigationAgent** | Intelligent page navigation |
| **FormHandler** | Automated form filling |
| **ComplianceEngine** | Robots.txt, rate limiting, proxies |
| **Extractors** | CSS, XPath, Regex, LLM-based, Ultra-smart |
| **Outputs** | JSON, CSV, Excel, Parquet, XML |
| **TemplateParser** | Template-based extraction |

**Key Features**:
- Playwright automation
- Multi-strategy extraction (CSS, XPath, Regex, LLM)
- Anti-detection measures
- Rate limiting & proxy rotation
- Template management
- Output format flexibility

---

### 6. NLP Processing (`tier_1/nlp_processing/`)

| Service | Capabilities |
|---------|--------------|
| **QueryClassifier** | Query intent classification |
| **DynamicQueryClassifier** | Adaptive query classification |
| **ComplexityAnalyzerService** | Query complexity analysis |
| **TaskComplexityAnalyzer** | Task difficulty estimation |
| **TranslationService** | Multi-language translation |
| **MultiChannelProcessor** | Multi-channel NLP processing |

---

### 7. Agent Services (`tier_1/agents/`)

| Component | Purpose |
|-----------|---------|
| **AgentService** | LangGraph-based agent workflows |
| **AgentSandboxManager** | Sandboxed agent execution |
| **TaskRouter** | Agent task routing |
| **TerminalSessionManager** | Terminal session management |
| **Engines** | ClaudeCode CLI, Codex CLI, Default |

**Key Features**:
- LangGraph workflows
- Sandboxed execution
- Multi-engine support
- State management

---

### 8. Fine-tuning Services (`tier_1/finetuning/`)

| Service | Capabilities |
|---------|--------------|
| **FinetuningService** | Distributed training orchestration |
| **GPUPoolManager** | GPU allocation & management |
| **HyperparameterTuningService** | Optuna-based hyperparameter tuning |
| **ModelEvaluationService** | Model evaluation & benchmarking |
| **ModelRegistryService** | Model versioning & registry |
| **Trainers** | SFT, PEFT, RLHF (PPO, GRPO), Unsloth |

**Key Features**:
- Celery-based distributed training
- GPU pool management
- Checkpointing & resume
- MinIO artifact storage
- Multiple training strategies

---

### 9. Platform Services (`tier_1/platform_services/`)

| Service | Capabilities |
|---------|--------------|
| **AuditService** | Action logging, usage tracking |
| **AuthService** | User authentication |
| **RBACService** | Role-based access control |
| **SecurityGuardrails** | Input validation, safety checks |
| **SecretsService** | Secure credential management |
| **APIUsageTracker** | API usage metering |
| **ToolUsageTracker** | Tool call tracking |

---

### 10. Export Services (`tier_1/export/`)

| Service | Capabilities |
|---------|--------------|
| **ExportService** | Multi-format export (PDF, DOCX, Excel, JSON) |
| **EDAAnalyzer** | Exploratory data analysis |
| **ProjectEstimatorService** | Project estimation |
| **BRDGenerationService** | Business requirements document generation |

---

### 11. Evaluation Services (`tier_1/evaluation/`)

| Service | Capabilities |
|---------|--------------|
| **EvaluationService** | RAG pipeline evaluation |
| **QualityMetricsService** | Quality metrics calculation |
| **RagasEvaluator** | RAGAS framework integration |

---

### 12. Infrastructure Services (`tier_1/infrastructure/`)

| Component | Purpose |
|-----------|---------|
| **Database** | PostgreSQL + pgvector connection management |
| **Config** | Centralized settings management |
| **GPUResourceManager** | GPU resource allocation |
| **MinIOPathBuilder** | MinIO path construction |
| **Security** | Security utilities |

---

## Database & Storage

### PostgreSQL Schema (`models/database.py`)

**Core Tables**:

| Table | Purpose | Key Fields |
|-------|---------|------------|
| **documents** | Document metadata | id, filename, file_path, file_type, source_type, processing_status, minio_path, project_id, uploaded_by |
| **document_chunks** | Text chunks with multi-dimensional embeddings | id, document_id, content, embedding (384), table_embedding (512), visual_embedding (512), numerical_embedding (256), code_embedding (768), embedding_strategy |
| **conversations** | Chat sessions | id, session_id, project_id, title, summary |
| **messages** | Chat messages | id, conversation_id, role, content, sources, model_used, tokens_used, latency_ms |
| **users** | User accounts | id, username, email, role, department, team |
| **projects** | Project organization | id, name, description, owner_id, department, team |
| **session_documents** | Short-term memory | session_id, document_id (unique constraint) |
| **audit_logs** | Audit trail | id, user_id, action, details, latency_ms, created_at |
| **web_scrape_jobs** | Web scraping jobs | id, url, status, config, results |
| **finetuning_jobs** | Fine-tuning jobs | id, model_name, dataset_path, status, gpu_allocated |

**Vector Indexes** (Critical):
```sql
CREATE INDEX idx_chunks_embedding ON document_chunks
USING ivfflat (embedding vector_cosine_ops);
```

### MinIO Object Storage

- Document storage (hierarchical by project/department/team)
- Fine-tuning artifacts (models, checkpoints, logs)
- Export outputs

### Redis

- Semantic caching (Redis VSS)
- Session management
- Rate limiting

### Elasticsearch (Optional)

- Full-text keyword search
- Complement to vector search

---

## Frontend Components

**Location**: `frontend/src/components/`

### Existing Components

| Component | Purpose | Status |
|-----------|---------|--------|
| **ChatInterfaceEnhanced** | Main chat interface with session support | ✅ Production |
| **FileUpload** | Drag-drop file upload | ✅ Production |
| **WebScraper** | Web scraping interface | ✅ Production |
| **ModelSelector** | LLM model selection | ✅ Production |
| **UploadedFilesList** | Document management | ✅ Production |
| **BritishCouncilRecommender** | British Council POC UI | ✅ Tier 3 POC |
| **CRUMiningIntelligence** | CRU Mining POC UI | ✅ Tier 3 POC |
| **GrantThorntonExtraction** | Grant Thornton POC UI | ✅ Tier 3 POC |
| **DocumentExtractionPanel** | Generic document extraction | ✅ Production |
| **ExtractionResults** | Extraction results display | ✅ Production |
| **ModuleInterface** | Module navigation | ✅ Production |
| **EvaluationDashboard** | RAG evaluation dashboard | ✅ Production |
| **AgentTaskMonitor** | Agent task monitoring | ✅ Production |
| **BrainView** | Knowledge graph visualization | ✅ Production |

### Frontend Tech Stack

- **Framework**: Next.js 14 + React 18 + TypeScript 5.3
- **UI**: Tailwind CSS 3.4
- **Icons**: Lucide React 0.316
- **Markdown**: React Markdown 9.0
- **API**: Axios 1.6, GraphQL 16.8
- **State**: Local state (useState), sessionId (localStorage)

---

## Infrastructure

### Containerization & Orchestration

- **Docker**: Multi-stage builds
- **Docker Compose**: Local development
- **Kubernetes**: Production deployment
- **Istio**: Service mesh (ambient mode)
- **Argo CD**: GitOps deployment

### Observability

- **OpenTelemetry**: Distributed tracing
- **Grafana**: Visualization
- **Tempo**: Trace backend
- **Loki**: Log aggregation
- **Mimir**: Metrics storage
- **Prometheus**: Metrics scraping

### CI/CD

- **Argo CD**: Continuous deployment
- **Tekton**: Pipeline orchestration
- **Skaffold**: Development workflow

---

## Reusability Matrix

### Service Reusability by POC Category

| POC Category | High Reusability (70-90%) | Medium (50-70%) | Low (30-50%) |
|--------------|---------------------------|-----------------|--------------|
| **Document Intelligence** | DocumentService, RAGService, EmbeddingService, LLMService, ExportService | OCRService, VisionService | - |
| **NLP/Classification** | LLMService, EmbeddingService, NLPProcessing services | - | Custom ML models |
| **Data Extraction** | ScraperService, LLMService, DocumentService | Template services | - |
| **HR/Talent** | EmbeddingService, LLMService, RAGService, DocumentService | - | Custom CV parsing |
| **Procurement** | RAGService, EmbeddingService, LLMService, ExportService | ScraperService | Neo4j integration |
| **Analytics** | LLMService, ExportService, AuditService | - | Scikit-learn ML models |
| **Maritime** | LLMService, ExportService, TemplateEngine | DocumentService | - |
| **Agriculture** | LLMService, EmbeddingService | - | Domain taxonomy DB |

---

## Key Reusable Patterns

### 1. Service Structure Pattern (Tier 2)

```
backend/app/tier_2/{category}/{poc_name}_service.py
backend/app/tier_2/{category}/{poc_name}_routes.py
backend/app/tier_2/{category}/{poc_name}_schemas.py
```

**Example** (Agri Taxonomy):
```python
# Service
class AgriTaxonomyService:
    def __init__(self, db: Session, settings: Settings):
        self.db = db
        self.llm_service = LLMService(db, settings)  # ✅ Reuse Tier 1

# Route
@router.post("/api/v2/agriculture/agri-taxonomy/classify")
async def classify_crops(request: TaxonomyRequest, db: Session = Depends(get_db)):
    service = AgriTaxonomyService(db, settings)
    return await service.classify_crops(request)
```

### 2. Database Integration Pattern

```python
from app.models.database import Base, Column, UUID, JSON
from app.tier_1.infrastructure.database import get_db

class POCResults(Base):
    __tablename__ = "poc_results"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    poc_name = Column(String(100), nullable=False)
    input_data = Column(JSON, nullable=False)
    output_data = Column(JSON, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
```

### 3. LLM Integration Pattern

```python
from app.tier_1.llm.llm_service import LLMService

# In service __init__
self.llm_service = LLMService(db, settings)

# Usage
response = await self.llm_service.generate_response(
    prompt=prompt,
    model="gpt-4o-mini",
    temperature=0.0,
    max_tokens=500
)
```

### 4. Document Processing Pattern

```python
from app.tier_1.document_processing.document_service import document_service

# Upload & process
doc = await document_service.upload_document(
    file=file,
    session_id=session_id,
    user_id=user_id
)

# Extract chunks
chunks = await document_service.get_document_chunks(doc.id)
```

### 5. RAG Pattern

```python
from app.tier_1.rag.rag_service import RAGService

rag_service = RAGService()
result = await rag_service.query(
    query_text=query,
    session_id=session_id,
    top_k=5
)
```

---

## Implementation Recommendations

### For Each POC:

1. **Start with placeholders**: Use existing Tier 2 structure
2. **Reuse Tier 1 services**: LLM, Embedding, RAG, Document processing
3. **Add POC-specific logic**: Only what's unique to the POC
4. **Follow patterns**: Service/Route/Schema structure
5. **Database tables**: Add POC-specific tables if needed
6. **Frontend components**: Create matching UI components
7. **Integration**: Wire backend → frontend → database

### Technology Gaps (New Components Needed):

1. **ML Model Service**: Scikit-learn model hosting (RandomForest, GradientBoosting)
2. **Vision Processing Service**: GPT-4 Vision integration (fashion tagging, image analysis)
3. **Template Engine Service**: Jinja2 + DOCX/PDF generation (reports, documents)
4. **Multi-LLM Router**: HuggingFace, Groq integration
5. **Email Parser Service**: MIME parsing, bounce classification
6. **Neo4j Integration**: Knowledge graph (for Spend Smart)
7. **Reference Data Service**: Companies, assets, commodities (mining, maritime)

---

## Summary Statistics

| Category | Count |
|----------|-------|
| **Tier 1 Service Categories** | 12 |
| **Total Tier 1 Services** | 50+ |
| **Database Tables** | 15+ core tables |
| **Vector Dimensions** | 5 types (384, 256, 512, 768) |
| **LLM Providers** | 5 (OpenAI, Claude, vLLM, Ollama, llama.cpp) |
| **Document Formats** | 10+ (PDF, DOCX, TXT, JSON, MD, CSV, XLSX, HTML, etc.) |
| **Frontend Components** | 30+ production components |
| **Export Formats** | 6 (PDF, DOCX, Excel, JSON, CSV, Parquet) |

---

**Next Steps**:
1. ✅ POC documentation analysis complete
2. ✅ Tier 1 stack inventory complete
3. ⏭️ Consolidate tech requirements & create reuse matrix
4. ⏭️ Create leveraged implementation plan
5. ⏭️ Begin POC implementations

---

**End of Document**
