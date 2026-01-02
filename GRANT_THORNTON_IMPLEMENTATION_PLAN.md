# Grant Thornton POC - Complete Implementation Plan

**Status:** In Progress
**Start Date:** January 1, 2026
**Target Completion:** January 15, 2026 (2 weeks)
**Estimated Effort:** 80-120 hours

---

## Executive Summary

Implementing the complete Grant Thornton financial datapoint extraction and ratio calculation system as documented in `/merit/merit_aiml_docs/.../grand_thornton_poc/`.

**Current State:** 2% complete (48-line stub)
**Target State:** 100% functional implementation (~4,000 lines)

---

## Implementation Phases

### Phase 1: Core Infrastructure (Days 1-2) ✅ STARTING NOW

**Components:**
1. **PDF Parser Module** (`backend/app/services/grant_thornton/pdf_parser.py`)
   - Marker PDF to Markdown conversion
   - PyMuPDF page splitting
   - Header-based chunking with metadata
   - MD5 hash generation

2. **Configuration System** (`backend/app/services/grant_thornton/config.py`)
   - YAML config loader (config.yaml, prompts.yaml)
   - Excel config loader (datapoints_prompt.xlsx, calculation_formula.xlsx, final_calculation_formula.xlsx)
   - Environment variable management

3. **Data Models** (`backend/app/schemas/grant_thornton_schemas.py`)
   - Pydantic models for extraction output
   - Ratio calculation schemas
   - Request/response models

**Deliverables:**
- [ ] PDF parsing with Marker integration
- [ ] Document chunking with header hierarchy
- [ ] Configuration management system
- [ ] Pydantic schemas for all data types

**Dependencies:**
```bash
pip install pymupdf marker-pdf pyyaml openpyxl
```

---

### Phase 2: Vector & Retrieval (Days 3-5)

**Components:**
1. **Embedding Service** (`backend/app/services/grant_thornton/embedding_service.py`)
   - BAAI/bge-large-en-v1.5 integration
   - GPU acceleration (CUDA)
   - Batch processing for performance

2. **Vector Store** (`backend/app/services/grant_thornton/vector_store.py`)
   - ChromaDB collection management
   - MD5-based collection naming (deduplication)
   - Persistent storage in `vector_store/`
   - MMR retriever configuration

3. **Reranker** (`backend/app/services/grant_thornton/reranker.py`)
   - BAAI/bge-reranker-large cross-encoder
   - Top-N reranking (k=20 → top 2)
   - GPU-accelerated inference

4. **Two-Stage Retrieval** (`backend/app/services/grant_thornton/retrieval_service.py`)
   - Stage 1: Initial context (3 financial statement queries → 6 chunks)
   - Stage 2: Agent tool for dynamic search
   - Integration with vector store + reranker

**Deliverables:**
- [ ] BAAI embeddings working on GPU
- [ ] ChromaDB with MD5 caching functional
- [ ] Cross-encoder reranker deployed
- [ ] Two-stage retrieval tested

**Dependencies:**
```bash
pip install sentence-transformers chromadb torch FlagEmbedding
```

---

### Phase 3: Extraction Engine (Days 6-9)

**Components:**
1. **LangGraph Agent** (`backend/app/services/grant_thornton/agent_service.py`)
   - LangGraph create_react_agent setup
   - Tool definition: search_financial_details
   - Streaming output support
   - Error handling and retry logic (2 attempts)

2. **Extraction Pipeline** (`backend/app/services/grant_thornton/extraction_pipeline.py`)
   - Load datapoints from Excel
   - Loop through 50+ datapoints
   - Invoke agent for each datapoint
   - Structured output parsing (ValueSchema)
   - Stream results in real-time

3. **Output Parser** (`backend/app/services/grant_thornton/output_parser.py`)
   - JsonOutputParser integration
   - Schema validation
   - Default value handling (0, 0, "Not Applicable")
   - Metadata enrichment

**Deliverables:**
- [ ] LangGraph agent with tool access
- [ ] Extraction loop for 50+ datapoints
- [ ] JSON output parsing with validation
- [ ] Retry logic with fallback
- [ ] Real-time streaming

**Dependencies:**
```bash
pip install langgraph langchain-openai langchain-core
```

---

### Phase 4: Calculation Engines (Days 10-12)

**Components:**
1. **Formula Normalizer** (`backend/app/services/grant_thornton/formula_normalizer.py`)
   - Symbol conversion (÷ → /, × → *, − → -)
   - Multi-word to Python variables (snake_case)
   - Field mapping application
   - Special character handling

2. **Sub-Calculation Engine** (`backend/app/services/grant_thornton/sub_calculation_engine.py`)
   - Load formulas from Excel (Sheet: "Additional Formulas")
   - Normalize formulas
   - Populate globals() namespace with extracted values
   - Evaluate formulas dynamically (eval())
   - Handle errors (ZeroDivisionError, NameError)
   - 12+ sub-calculations:
     - average_total_equity
     - tangible_net_worth
     - cash_profit
     - dso, dio, dpo
     - average_receivables/payables/inventory
     - debt_service
     - total_bank_borrowings

3. **Ratio Calculator** (`backend/app/services/grant_thornton/ratio_calculator.py`)
   - Load ratio formulas from Excel
   - Apply field mappings
   - Calculate 30+ financial ratios:
     - Liquidity: current_ratio, quick_ratio, cash_ratio, working_capital_ratio
     - Leverage: debt_to_equity, debt_to_assets, interest_coverage, equity_ratio
     - Profitability: ROA, ROE, net_margin, gross_margin, operating_margin, ebitda_margin
     - Efficiency: asset_turnover, inventory_turnover, receivables_turnover, dso, dio, dpo, cash_conversion_cycle
     - Growth: revenue_growth, earnings_growth, asset_growth
   - Round to 2 decimals
   - Error handling (division by zero → 0)

**Deliverables:**
- [ ] Formula normalization working
- [ ] Sub-calculation engine functional (12+ formulas)
- [ ] Ratio calculator complete (30+ ratios)
- [ ] Global namespace evaluation tested
- [ ] Zero-division handling

---

### Phase 5: API & Integration (Days 13-14)

**Components:**
1. **Main Service** (`backend/app/services/grant_thornton/grant_thornton_service.py`)
   - Orchestrate full pipeline
   - PDF → Parse → Embed → Extract → Calculate → Output
   - Caching logic (MD5-based)
   - Progress tracking

2. **FastAPI Endpoints** (`backend/app/api/routes/grant_thornton_routes.py`)
   - POST `/api/v1/grant-thornton/extract` - Upload PDF and extract
   - GET `/api/v1/grant-thornton/status/{job_id}` - Check progress
   - GET `/api/v1/grant-thornton/results/{md5_hash}` - Get cached results
   - SSE `/api/v1/grant-thornton/stream/{job_id}` - Real-time progress

3. **Caching Layer** (`backend/app/services/grant_thornton/cache_service.py`)
   - Excel output caching (output/{md5_hash}.xlsx)
   - Vector store caching (avoid re-embedding)
   - Result retrieval (<30 sec for cached documents)

4. **Excel Output** (`backend/app/services/grant_thornton/excel_exporter.py`)
   - Generate Excel with all extracted fields
   - Include definitions, page numbers, reference notes
   - Separate sheets: Extracted Data, Sub-Calculations, Ratios

**Deliverables:**
- [ ] Main orchestration service
- [ ] FastAPI endpoints with SSE
- [ ] Caching functional (instant retrieval)
- [ ] Excel export working
- [ ] Integration with existing backend

**Dependencies:**
```bash
pip install openpyxl pandas
```

---

### Phase 6: Configuration & Artifacts (Day 14)

**Create Configuration Files:**

1. **`backend/app/services/grant_thornton/config/config.yaml`**
```yaml
persist_directory: vector_store
input_excel_path: artifacts/datapoints_prompt.xlsx
sheet_name: "Prompt"
head_tags:
  "#": "#"
  "##": "##"
  "###": "###"
embed_model_name: BAAI/bge-large-en-v1.5
reranker_model_name: BAAI/bge-reranker-large
llm_model_name: gpt-4o-mini
retry_count: 2
sub_calculation_list: [...]
mapping_fields: {...}
```

2. **`backend/app/services/grant_thornton/config/prompts.yaml`**
```yaml
retriever_prompt:
  - "Standalone Statement of Profit and Loss"
  - "standalone Balance sheet"
  - "standalone Cash flow statement"
user_prompt: |
  You are a financial-ratio engine...
```

3. **`backend/app/services/grant_thornton/artifacts/datapoints_prompt.xlsx`**
- 50+ rows with: Fields to be extracted, Definition, Typical location, cleaned_field_name

4. **`backend/app/services/grant_thornton/artifacts/calculation_formula.xlsx`**
- Sheet "Additional Formulas" with sub-calculation formulas

5. **`backend/app/services/grant_thornton/artifacts/final_calculation_formula.xlsx`**
- 30+ ratio formulas with categories

**Deliverables:**
- [ ] All YAML configs created
- [ ] All Excel artifacts populated
- [ ] Directory structure setup
- [ ] .env updated with OPENAI_API_KEY

---

### Phase 7: Testing & Validation (Day 15)

**Test Cases:**

1. **Unit Tests**
   - PDF parsing: Test with sample annual report
   - Formula normalization: Test symbol conversion, field mapping
   - Sub-calculations: Verify all 12+ formulas
   - Ratio calculations: Verify all 30+ ratios

2. **Integration Tests**
   - End-to-end: Upload PDF → Extract → Calculate → Excel output
   - Caching: Verify MD5-based instant retrieval
   - Streaming: Test SSE real-time updates
   - Error handling: Test with incomplete data, division by zero

3. **Validation Against Sample Data**
   - Use sample data from `/sample_data/tier3_customer_pocs/grant_thornton/`
   - Verify accuracy of extracted values
   - Compare calculated ratios to benchmarks
   - Validate page references

4. **Performance Testing**
   - First run: Should complete in 15-20 minutes
   - Cached run: Should complete in <30 seconds
   - GPU utilization: >80% during embedding
   - Memory usage: <8GB

**Deliverables:**
- [ ] All unit tests passing
- [ ] Integration tests complete
- [ ] Sample data validation successful
- [ ] Performance targets met

---

## Success Criteria

### Functional Requirements
- ✅ Extract 50+ financial datapoints from PDF annual reports
- ✅ Calculate 12+ sub-calculations with formula engine
- ✅ Calculate 30+ financial ratios across 4 categories
- ✅ Provide page-level traceability for all extracted values
- ✅ Stream real-time progress during extraction
- ✅ Cache results for instant retrieval

### Performance Requirements
- ✅ First run: 15-20 minutes (full pipeline)
- ✅ Cached run: <30 seconds (instant retrieval)
- ✅ Accuracy: 95%+ extraction, 99%+ calculation
- ✅ GPU acceleration for embeddings and reranking

### Integration Requirements
- ✅ FastAPI endpoints in existing backend
- ✅ Compatible with current authentication
- ✅ Follows existing coding standards
- ✅ Comprehensive logging and error handling

---

## Risk Mitigation

### Technical Risks

**Risk 1: Marker PDF conversion quality**
- **Mitigation**: Fallback to PyMuPDF text extraction if Marker fails
- **Testing**: Validate with multiple PDF formats

**Risk 2: LLM extraction accuracy**
- **Mitigation**: Two-stage retrieval + retry logic
- **Testing**: Validate against known financial reports

**Risk 3: Formula evaluation errors**
- **Mitigation**: Comprehensive try-except with default values
- **Testing**: Edge cases (zero values, missing fields)

**Risk 4: GPU availability**
- **Mitigation**: CPU fallback for embeddings/reranking
- **Testing**: Run on both GPU and CPU environments

### Schedule Risks

**Risk 1: Dependency installation issues**
- **Mitigation**: Docker container with all dependencies pre-installed
- **Contingency**: +2 days buffer

**Risk 2: Integration conflicts**
- **Mitigation**: Namespace isolation (grant_thornton/*)
- **Contingency**: +1 day for conflict resolution

---

## Resource Requirements

### Compute Resources
- **GPU**: NVIDIA GPU with 8GB+ VRAM (for CUDA acceleration)
- **CPU**: 8+ cores recommended
- **RAM**: 16GB+ recommended
- **Storage**: 10GB+ for vector stores

### Software Dependencies
```bash
# Core ML libraries
sentence-transformers==2.3.1
chromadb==0.4.22
torch==2.1.0
FlagEmbedding==1.2.0

# LangChain ecosystem
langgraph==0.2.0
langchain==0.2.0
langchain-openai==0.1.0
langchain-core==0.2.0

# PDF processing
pymupdf==1.23.8
marker-pdf==0.2.0

# Data processing
pandas==2.1.0
openpyxl==3.1.2
pyyaml==6.0.1

# API
fastapi==0.111.0
python-multipart==0.0.9
```

### API Keys
- **OpenAI API Key**: Required for GPT-4o-mini extraction

---

## Monitoring & Observability

### Metrics to Track
- **Extraction Accuracy**: % of correctly extracted values
- **Processing Time**: Average time per document
- **Cache Hit Rate**: % of cached retrievals
- **GPU Utilization**: % during embedding/reranking
- **API Response Times**: P50, P95, P99
- **Error Rate**: % of failed extractions

### Logging
- All extraction attempts with timestamps
- Retry events with reasons
- Cache hits/misses
- LLM tool invocations
- Formula evaluation errors

---

## Next Steps

**Immediate (Next Hour):**
1. Start Phase 1 implementation
2. Create directory structure
3. Implement PDF parser module
4. Set up configuration system

**Today:**
- Complete Phase 1 (Core Infrastructure)
- Begin Phase 2 (Vector & Retrieval)

**This Week:**
- Complete Phases 2-4
- Begin Phase 5 (API Integration)

**Next Week:**
- Complete Phase 5-7
- Full end-to-end testing
- Deploy to production

---

**Status:** ✅ READY TO BEGIN IMPLEMENTATION
**Next Action:** Create directory structure and start PDF parser module
