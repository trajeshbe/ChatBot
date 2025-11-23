# Comprehensive Tool Usage Tracking System

> **Last Updated**: 2025-11-23
> **Status**: Implemented (Backend Complete, Frontend Dashboard Pending)
> **Impact**: Full visibility into tool usage, performance, and contribution

---

## Overview

This system provides **comprehensive tracking** of all tools and services used throughout the application, enabling:

1. **Usage Analytics**: Which tools are used most frequently
2. **Performance Metrics**: Latency, throughput, P95 metrics per tool
3. **Cost Attribution**: Track API costs (OpenAI, Anthropic, etc.)
4. **Quality Metrics**: Tool contribution to overall quality
5. **Troubleshooting**: Identify bottlenecks and failures
6. **ROI Analysis**: Understand which tools provide best value

---

## Architecture

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Services                      │
│  (Document Processing, Web Scraping, RAG, LLM, MCP)        │
└────────────────────┬────────────────────────────────────────┘
                     │ tool_tracker.track_tool_usage()
                     ↓
┌─────────────────────────────────────────────────────────────┐
│              Tool Usage Tracking Service                     │
│      (app/services/tool_usage_tracker.py)                   │
│                                                              │
│  • Context manager for automatic tracking                    │
│  • Records: latency, success/failure, tokens, cost          │
│  • Aggregation queries                                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│                PostgreSQL Database                           │
│                                                              │
│  tool_usage_stats table:                                     │
│  - tool_category (document_processing, web_scraping, etc.)  │
│  - tool_name (docling, playwright, gpt-4, etc.)             │
│  - operation (parse_pdf, scrape_url, generate_response)     │
│  - latency_ms, tokens_used, cost_usd, quality_score        │
│                                                              │
│  tool_usage_summary materialized view:                       │
│  - Aggregated statistics for fast dashboard queries         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│             Tool Statistics API                              │
│      (app/api/routes/tool_stats_routes.py)                  │
│                                                              │
│  GET /api/v1/tool-stats/summary                             │
│  GET /api/v1/tool-stats/timeline                            │
│  GET /api/v1/tool-stats/categories                          │
│  GET /api/v1/tool-stats/top-tools                           │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│            Evaluation Dashboard (Frontend)                   │
│               [TO BE IMPLEMENTED]                            │
│                                                              │
│  • Tool usage charts and graphs                             │
│  • Cost breakdown by tool                                    │
│  • Performance metrics per tool                              │
│  • Timeline visualization                                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Tool Categories

The system tracks tools across these categories:

### 1. Document Processing (`document_processing`)
Tools for parsing and extracting text from documents:
- `docling` - Advanced PDF, DOCX, PPTX parsing
- `tesseract_ocr` - OCR for scanned documents
- `pypdf2` - Fallback PDF text extraction
- `python_docx` - Word document processing
- `python_pptx` - PowerPoint processing
- `openpyxl` - Excel file processing

### 2. Web Scraping (`web_scraping`)
Tools for extracting content from web pages:
- `playwright` - Browser automation
- `ultra_smart_extractor` - LLM-based intelligent extraction
- `template_extractor` - Template-based extraction
- `css_extractor` - CSS selector extraction
- `xpath_extractor` - XPath-based extraction
- `llm_extractor` - Direct LLM extraction

### 3. RAG Services (`rag_service`)
Retrieval and ranking components:
- `vector_search` - Semantic similarity search with pgvector
- `cross_encoder_reranker` - Two-stage retrieval reranking
- `query_reformulation` - Query expansion (acronyms + synonyms)
- `query_classifier` - Query type classification
- `quality_metrics` - RAGAS evaluation

### 4. Embedding Services (`embedding`)
Text embedding generation:
- `sentence_transformers` - General embedding framework
- `all-MiniLM-L6-v2` - Fast 384-dim embeddings
- `bge-base-en-v1.5` - Better quality embeddings

### 5. LLM Services (`llm_service`)
Language model inference:
- `gpt-4` - OpenAI GPT-4
- `gpt-3.5-turbo` - OpenAI GPT-3.5 Turbo
- `claude-3-opus` - Anthropic Claude 3 Opus
- `claude-3-sonnet` - Anthropic Claude 3 Sonnet
- `ollama/mistral` - Local Mistral via Ollama
- `ollama/llama2` - Local Llama 2 via Ollama

### 6. Caching Services (`caching`)
Semantic caching with Redis:
- `redis_cache` - General Redis caching
- `semantic_cache` - Semantic similarity-based caching

### 7. MCP Tools (`mcp_tool`)
External MCP server tools:
- Dynamically populated based on connected MCP servers

---

## Database Schema

### `tool_usage_stats` Table

```sql
CREATE TABLE tool_usage_stats (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Tool identification
    tool_category VARCHAR(50) NOT NULL,
    tool_name VARCHAR(100) NOT NULL,
    tool_version VARCHAR(50),

    -- Context
    session_id VARCHAR(255),
    user_id UUID REFERENCES users(id),

    -- Operation details
    operation VARCHAR(100),
    input_size INTEGER,
    output_size INTEGER,

    -- Performance metrics
    latency_ms FLOAT NOT NULL,
    success BOOLEAN NOT NULL DEFAULT TRUE,
    error_message TEXT,

    -- Resource usage
    tokens_used INTEGER,
    cost_usd DECIMAL(10, 6),

    -- Quality metrics
    quality_score FLOAT,
    metadata JSONB,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### `tool_usage_summary` Materialized View

Pre-aggregated statistics for fast dashboard queries:

```sql
CREATE MATERIALIZED VIEW tool_usage_summary AS
SELECT
    tool_category,
    tool_name,
    COUNT(*) as total_invocations,
    COUNT(*) FILTER (WHERE success = TRUE) as successful_invocations,
    COUNT(*) FILTER (WHERE success = FALSE) as failed_invocations,
    AVG(latency_ms) as avg_latency_ms,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY latency_ms) as median_latency_ms,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms) as p95_latency_ms,
    SUM(tokens_used) as total_tokens_used,
    SUM(cost_usd) as total_cost_usd,
    AVG(quality_score) as avg_quality_score,
    ROUND(100.0 * COUNT(*) FILTER (WHERE success = TRUE) / COUNT(*), 2) as success_rate_pct
FROM tool_usage_stats
GROUP BY tool_category, tool_name;
```

---

## Usage Guide

### How to Instrument a Service

#### Context Manager Pattern (Recommended)

```python
from app.services.tool_usage_tracker import tool_tracker, ToolCategory

async def process_document(file_path: str, db: AsyncSession):
    """Process a document with automatic tool tracking"""

    # Track tool usage with context manager
    async with tool_tracker.track_tool_usage(
        category=ToolCategory.DOCUMENT_PROCESSING,
        tool_name="docling",
        operation="parse_pdf",
        db=db,
        session_id=session_id,
        input_size=file_size
    ) as tracker:
        # Your processing logic here
        result = await docling.parse_pdf(file_path)

        # Set output metrics
        tracker.set_output_size(len(result['content']))
        tracker.set_quality_score(result['confidence'])

        # Add custom metadata
        tracker.set_metadata('pages', result['num_pages'])
        tracker.set_metadata('has_images', result['has_images'])

        return result

# If an exception occurs, it's automatically recorded with success=False
```

#### Direct Recording Pattern

For simple cases without complex context:

```python
from app.services.tool_usage_tracker import tool_tracker, ToolCategory
import time

async def simple_operation(db: AsyncSession):
    start_time = time.time()

    try:
        result = await perform_operation()
        success = True
        error = None
    except Exception as e:
        success = False
        error = str(e)

    latency_ms = (time.time() - start_time) * 1000

    # Record directly
    await tool_tracker.record_tool_usage(
        category=ToolCategory.WEB_SCRAPING,
        tool_name="playwright",
        operation="scrape_url",
        latency_ms=latency_ms,
        success=success,
        error_message=error,
        db=db
    )
```

### Instrumentation Examples

#### Document Processing Service

```python
# In app/services/document_service.py

from app.services.tool_usage_tracker import tool_tracker, ToolCategory

async def process_pdf_with_docling(file_path: str, db: AsyncSession):
    """Process PDF with Docling and track usage"""

    file_size = os.path.getsize(file_path)

    async with tool_tracker.track_tool_usage(
        category=ToolCategory.DOCUMENT_PROCESSING,
        tool_name="docling",
        operation="parse_pdf",
        tool_version="2.62.0",
        input_size=file_size,
        db=db
    ) as tracker:
        result = await docling.convert(file_path)

        tracker.set_output_size(len(result.document.export_to_markdown()))
        tracker.set_quality_score(result.confidence_score)
        tracker.set_metadata('num_pages', result.num_pages)

        return result
```

#### Web Scraping Service

```python
# In app/services/scraper_service_enhanced.py

from app.services.tool_usage_tracker import tool_tracker, ToolCategory

async def scrape_with_playwright(url: str, db: AsyncSession):
    """Scrape URL with Playwright and track usage"""

    async with tool_tracker.track_tool_usage(
        category=ToolCategory.WEB_SCRAPING,
        tool_name="playwright",
        operation="scrape_url",
        input_size=len(url),
        db=db
    ) as tracker:
        content = await playwright_scrape(url)

        tracker.set_output_size(len(content))
        tracker.set_metadata('url', url)
        tracker.set_metadata('dom_elements', content.get('dom_count'))

        return content
```

#### LLM Service

```python
# In app/services/llm_service.py

from app.services.tool_usage_tracker import tool_tracker, ToolCategory

async def generate_with_gpt4(prompt: str, db: AsyncSession):
    """Generate response with GPT-4 and track usage"""

    async with tool_tracker.track_tool_usage(
        category=ToolCategory.LLM_SERVICE,
        tool_name="gpt-4",
        operation="generate_response",
        input_size=len(prompt),
        db=db
    ) as tracker:
        response = await openai.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )

        content = response.choices[0].message.content
        tokens = response.usage.total_tokens
        cost = calculate_cost(tokens, "gpt-4")

        tracker.set_output_size(len(content))
        tracker.set_tokens_used(tokens)
        tracker.set_cost(cost)
        tracker.set_metadata('model', response.model)

        return content
```

---

## API Endpoints

### Get Summary Statistics

```bash
GET /api/v1/tool-stats/summary?days=7&category=llm_service

Response:
{
  "summary": {
    "total_tools": 6,
    "total_invocations": 1234,
    "total_successful": 1200,
    "total_failed": 34,
    "total_tokens_used": 500000,
    "total_cost_usd": 15.50,
    "date_range": {
      "start": "2025-11-16T00:00:00Z",
      "end": "2025-11-23T00:00:00Z",
      "days": 7
    }
  },
  "by_category": {
    "llm_service": [
      {
        "tool_category": "llm_service",
        "tool_name": "gpt-4",
        "total_invocations": 456,
        "successful_invocations": 450,
        "failed_invocations": 6,
        "avg_latency_ms": 2345.67,
        "median_latency_ms": 2100.00,
        "p95_latency_ms": 4500.00,
        "total_tokens_used": 250000,
        "total_cost_usd": 12.50,
        "success_rate_pct": 98.68
      }
    ]
  }
}
```

### Get Usage Timeline

```bash
GET /api/v1/tool-stats/timeline?days=7&tool_name=gpt-4

Response:
{
  "timeline": [
    {
      "date": "2025-11-23",
      "tool_category": "llm_service",
      "tool_name": "gpt-4",
      "invocations": 89,
      "successful": 87,
      "avg_latency_ms": 2234.56
    },
    {
      "date": "2025-11-22",
      "tool_category": "llm_service",
      "tool_name": "gpt-4",
      "invocations": 102,
      "successful": 100,
      "avg_latency_ms": 2145.78
    }
  ]
}
```

### Get Top Tools

```bash
GET /api/v1/tool-stats/top-tools?limit=10&sort_by=cost

Response:
{
  "top_tools": [
    {
      "tool_category": "llm_service",
      "tool_name": "gpt-4",
      "total_cost_usd": 12.50,
      "total_invocations": 456
    },
    {
      "tool_category": "llm_service",
      "tool_name": "claude-3-opus",
      "total_cost_usd": 3.00,
      "total_invocations": 123
    }
  ],
  "sort_by": "cost"
}
```

---

## Frontend Dashboard (To Be Implemented)

### Proposed UI Components

#### 1. Tool Usage Overview Card

```
┌────────────────────────────────────────────┐
│  Tool Usage Overview (Last 7 Days)         │
├────────────────────────────────────────────┤
│  Total Tools: 18                           │
│  Total Invocations: 5,432                  │
│  Success Rate: 98.5%                       │
│  Total Cost: $45.67                        │
│  Total Tokens: 2.3M                        │
└────────────────────────────────────────────┘
```

#### 2. Tool Category Breakdown (Pie Chart)

```
Document Processing: 35%
Web Scraping: 20%
RAG Services: 25%
LLM Services: 15%
Caching: 5%
```

#### 3. Top Tools by Invocations (Bar Chart)

```
gpt-4                 ████████████ 1,234
vector_search         ██████████ 987
docling              ████████ 765
playwright           ██████ 543
cross_encoder_reranker ████ 321
```

#### 4. Cost Breakdown (Stacked Bar Chart by Day)

```
Shows daily cost breakdown by tool category
```

#### 5. Performance Metrics Table

```
┌──────────────┬───────────┬─────────┬───────────┬────────┐
│ Tool         │ Invocations│ Avg(ms) │ P95(ms)   │ Success│
├──────────────┼───────────┼─────────┼───────────┼────────┤
│ gpt-4        │ 1,234     │ 2,345   │ 4,500     │ 98.5%  │
│ docling      │ 765       │ 1,234   │ 2,100     │ 99.2%  │
│ playwright   │ 543       │ 3,456   │ 8,900     │ 96.7%  │
└──────────────┴───────────┴─────────┴───────────┴────────┘
```

---

## Benefits

### 1. Operational Insights
- **Identify bottlenecks**: Which tools are slowest?
- **Find failures**: Which tools fail most often?
- **Track usage patterns**: When are tools most used?

### 2. Cost Management
- **Track API costs**: Know exactly what you're spending
- **Optimize model selection**: Compare GPT-4 vs Claude vs local models
- **Budget forecasting**: Predict future costs based on trends

### 3. Quality Analysis
- **Tool contribution**: Which tools improve output quality most?
- **A/B testing**: Compare tool effectiveness
- **ROI analysis**: Cost vs. quality tradeoff

### 4. Troubleshooting
- **Error diagnosis**: Quick identification of failing tools
- **Performance debugging**: Find performance regressions
- **Session analysis**: Trace tool usage per session

---

## Implementation Status

### ✅ Completed

1. **Database Schema** (`migrations/005_add_tool_usage_tracking.sql`)
   - `tool_usage_stats` table
   - `tool_usage_summary` materialized view
   - Indexes and queries optimized

2. **Tool Usage Tracking Service** (`app/services/tool_usage_tracker.py`)
   - Context manager for automatic tracking
   - Direct recording method
   - Aggregation queries
   - Timeline queries

3. **API Endpoints** (`app/api/routes/tool_stats_routes.py`)
   - Summary statistics
   - Timeline data
   - Top tools
   - Category listing

4. **Router Registration** (`app/main.py`)
   - Tool stats router registered
   - Graceful error handling

### ⏳ Pending

1. **Service Instrumentation**
   - Document processing services
   - Web scraping services
   - RAG services
   - LLM services
   - MCP tool tracking

2. **Frontend Dashboard**
   - Tool usage overview component
   - Charts and graphs
   - Performance metrics table
   - Cost breakdown visualization
   - Integration with evaluation dashboard

3. **Testing**
   - Unit tests for tracker
   - Integration tests
   - Load testing

---

## Next Steps

### Phase 1: Core Instrumentation (High Priority)
1. Instrument LLM service (highest cost/impact)
2. Instrument document processing (high usage)
3. Instrument RAG services (cross-encoder, reformulation)

### Phase 2: Extended Instrumentation (Medium Priority)
1. Instrument web scraping tools
2. Instrument caching services
3. Instrument MCP tool usage

### Phase 3: Frontend Dashboard (High Priority)
1. Create ToolUsageDashboard component
2. Add charts and visualizations
3. Integrate with existing evaluation UI

### Phase 4: Advanced Features (Future)
1. Alerting on anomalies (sudden cost spikes, failures)
2. Automated optimization recommendations
3. Comparative analysis (tool A vs tool B)
4. Export capabilities (CSV, PDF reports)

---

## Cost Estimation

### OpenAI API Costs

```python
GPT_4_COST_PER_1K_TOKENS = {
    'input': 0.03,
    'output': 0.06
}

GPT_3_5_TURBO_COST_PER_1K_TOKENS = {
    'input': 0.0015,
    'output': 0.002
}
```

### Anthropic API Costs

```python
CLAUDE_3_OPUS_COST_PER_1K_TOKENS = {
    'input': 0.015,
    'output': 0.075
}

CLAUDE_3_SONNET_COST_PER_1K_TOKENS = {
    'input': 0.003,
    'output': 0.015
}
```

---

## Changelog

| Date | Version | Changes |
|------|---------|---------|
| 2025-11-23 | 1.0.0 | Initial comprehensive tool usage tracking system |

---

**End of Document**
