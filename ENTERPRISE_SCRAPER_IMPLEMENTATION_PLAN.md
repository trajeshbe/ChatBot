# 🎯 Enterprise Web Scraping & Data Extraction Platform - Implementation Plan

> **Last Updated**: 2025-11-16
> **Status**: Ready for Implementation
> **Estimated Timeline**: 6-8 weeks

---

## 📋 Executive Summary

This document outlines the transformation of the existing web scraping module into a **state-of-the-art B2B data extraction platform** comparable to enterprise solutions like Octoparse, ParseHub, and Apify, enhanced with LLM-powered extraction capabilities.

### Current State ✅
- ✅ Multi-strategy scraping (Trafilatura, BeautifulSoup, Playwright, Hybrid, Auto)
- ✅ LangGraph agent framework
- ✅ Prefect workflow orchestration
- ✅ Document processing pipeline (PostgreSQL + MinIO + Redis)
- ✅ Basic scraper configuration system

### Target State 🎯
- 🎯 Enterprise-grade compliance engine (robots.txt, rate limiting, proxies)
- 🎯 Template-based data extraction (Excel/CSV/JSON mapping)
- 🎯 LLM-powered field extraction workflow
- 🎯 Advanced scraping strategies (API, Sitemap, Recursive, Structured Data)
- 🎯 Multiple output formats with rich formatting
- 🎯 Job scheduling and automation
- 🎯 Visual extraction wizard UI

---

## 🏗️ Modular Architecture Design

### Directory Structure

```
backend/app/services/webscraper/          # 🆕 NEW: Modular web scraper package
│
├── __init__.py                           # Package exports
├── README.md                             # Scraper module documentation
│
├── core/                                 # Core scraping engine
│   ├── __init__.py
│   ├── scraper_engine.py                 # Main scraping orchestrator
│   ├── request_manager.py                # HTTP request handling
│   └── session_manager.py                # Browser session management
│
├── strategies/                           # Scraping strategies (ENHANCED)
│   ├── __init__.py
│   ├── base_strategy.py                  # ✅ EXISTS (from scraper_strategies.py)
│   ├── static_scraper.py                 # ✅ EXISTS (Trafilatura, BeautifulSoup)
│   ├── dynamic_scraper.py                # ✅ EXISTS (Playwright)
│   ├── api_scraper.py                    # 🆕 NEW: REST API discovery & consumption
│   ├── sitemap_crawler.py                # 🆕 NEW: Sitemap.xml-based crawling
│   ├── recursive_crawler.py              # 🆕 NEW: Link following with depth control
│   ├── structured_data_extractor.py      # 🆕 NEW: JSON-LD, microdata, OpenGraph
│   └── strategy_factory.py               # ✅ EXISTS (enhanced)
│
├── compliance/                           # 🆕 NEW: Legal & technical compliance
│   ├── __init__.py
│   ├── robots_txt_checker.py             # Robots.txt parser and validator
│   ├── rate_limiter.py                   # Per-domain rate limiting
│   ├── proxy_manager.py                  # Rotating proxy support
│   ├── user_agent_rotator.py             # User agent rotation
│   ├── auth_manager.py                   # Multi-auth support (Basic, OAuth2, JWT)
│   └── compliance_engine.py              # Main compliance orchestrator
│
├── templates/                            # 🆕 NEW: Template management system
│   ├── __init__.py
│   ├── template_parser.py                # Parse Excel/CSV/JSON templates
│   ├── template_validator.py             # Validate template schemas
│   ├── field_mapper.py                   # Map extracted data to template fields
│   ├── template_models.py                # Pydantic models for templates
│   └── template_storage.py               # Store templates in PostgreSQL/MinIO
│
├── extractors/                           # 🆕 NEW: Data extraction layer
│   ├── __init__.py
│   ├── css_extractor.py                  # CSS selector extraction
│   ├── xpath_extractor.py                # XPath extraction
│   ├── regex_extractor.py                # Pattern-based extraction
│   ├── llm_extractor.py                  # LLM-powered extraction
│   ├── structured_extractor.py           # JSON/XML/API extraction
│   └── extractor_factory.py              # Extractor selection
│
├── processing/                           # 🆕 NEW: Data processing pipeline
│   ├── __init__.py
│   ├── data_cleaner.py                   # Cleaning & normalization
│   ├── data_validator.py                 # Validation rules engine
│   ├── data_transformer.py               # Transformations (regex, lookups, calc)
│   ├── quality_scorer.py                 # Data quality metrics
│   └── deduplicator.py                   # Duplicate detection
│
├── outputs/                              # 🆕 NEW: Output generation
│   ├── __init__.py
│   ├── excel_generator.py                # Rich Excel output (formatting, charts)
│   ├── csv_generator.py                  # CSV output
│   ├── json_generator.py                 # JSON output
│   ├── xml_generator.py                  # XML output
│   ├── parquet_generator.py              # Parquet for analytics
│   └── output_factory.py                 # Output format selection
│
├── delivery/                             # 🆕 NEW: Result delivery
│   ├── __init__.py
│   ├── download_handler.py               # Direct download
│   ├── email_sender.py                   # Email delivery
│   ├── webhook_sender.py                 # Webhook/API delivery
│   ├── storage_uploader.py               # S3/GCS/Azure upload
│   └── database_inserter.py              # Direct DB insertion
│
├── scheduling/                           # 🆕 NEW: Job scheduling
│   ├── __init__.py
│   ├── job_scheduler.py                  # Cron-based scheduling (using Prefect)
│   ├── change_detector.py                # Detect content changes
│   ├── incremental_scraper.py            # Scrape only changes
│   └── job_queue.py                      # Job queue management
│
├── workflows/                            # 🆕 NEW: LangGraph workflows
│   ├── __init__.py
│   ├── extraction_workflow.py            # Main data extraction workflow
│   ├── workflow_nodes.py                 # Individual workflow nodes
│   ├── workflow_state.py                 # State management
│   └── workflow_tools.py                 # Tools for LangGraph agents
│
├── monitoring/                           # 🆕 NEW: Monitoring & alerting
│   ├── __init__.py
│   ├── job_monitor.py                    # Job status tracking
│   ├── metrics_collector.py              # Performance metrics
│   ├── alert_manager.py                  # Alert configuration & sending
│   └── health_checker.py                 # Service health monitoring
│
└── models/                               # 🆕 NEW: Database models (additions)
    ├── __init__.py
    ├── extraction_job.py                 # Extraction job model
    ├── extraction_template.py            # Template model
    ├── extraction_result.py              # Extraction result model
    └── job_schedule.py                   # Schedule model
```

### Integration with Existing Services

```python
# Existing services that will be LEVERAGED:
# ✅ app/services/document_service.py      - Store extracted data as documents
# ✅ app/services/embedding_service.py     - Generate embeddings for searchability
# ✅ app/services/llm_service.py          - LLM-powered extraction
# ✅ app/agents/rag_agent.py              - LangGraph agent framework
# ✅ PostgreSQL + pgvector                - Store structured/unstructured data
# ✅ MinIO                                - Store output files (Excel, CSV, etc.)
# ✅ Redis                                - Cache, rate limiting, job queue
# ✅ Prefect                              - Workflow orchestration
```

---

## 🚀 Implementation Phases

### **Phase 1: Foundation - Compliance & Advanced Strategies** (Week 1-2)

#### 1.1 Compliance Engine
**Files to Create:**
- `backend/app/services/webscraper/compliance/robots_txt_checker.py`
- `backend/app/services/webscraper/compliance/rate_limiter.py` (leverage Redis)
- `backend/app/services/webscraper/compliance/proxy_manager.py`
- `backend/app/services/webscraper/compliance/user_agent_rotator.py`
- `backend/app/services/webscraper/compliance/auth_manager.py`
- `backend/app/services/webscraper/compliance/compliance_engine.py`

**Features:**
- ✅ Robots.txt parsing and validation
- ✅ Per-domain rate limiting (using Redis)
- ✅ Proxy rotation (HTTP/SOCKS5)
- ✅ User agent rotation
- ✅ Multi-auth support (Basic, OAuth2, JWT, Session-based)
- ✅ Three compliance levels: `strict`, `balanced`, `aggressive`

**Database Changes:**
```sql
-- Add to existing WebScrapeJob table
ALTER TABLE web_scrape_jobs ADD COLUMN compliance_level VARCHAR(50) DEFAULT 'balanced';
ALTER TABLE web_scrape_jobs ADD COLUMN proxy_used VARCHAR(255);
ALTER TABLE web_scrape_jobs ADD COLUMN user_agent_used VARCHAR(512);
ALTER TABLE web_scrape_jobs ADD COLUMN auth_method VARCHAR(50);
```

#### 1.2 Advanced Scraping Strategies
**Files to Create:**
- `backend/app/services/webscraper/strategies/api_scraper.py`
- `backend/app/services/webscraper/strategies/sitemap_crawler.py`
- `backend/app/services/webscraper/strategies/recursive_crawler.py`
- `backend/app/services/webscraper/strategies/structured_data_extractor.py`

**Features:**
- ✅ API scraper: Auto-discover REST APIs, GraphQL endpoints
- ✅ Sitemap crawler: Parse sitemap.xml, crawl all URLs
- ✅ Recursive crawler: Follow links with depth/breadth controls
- ✅ Structured data: Extract JSON-LD, microdata, OpenGraph, Schema.org

**Configuration:**
```python
# Add to backend/app/core/config.py
class Settings(BaseSettings):
    # Advanced scraping strategies
    ENABLE_API_SCRAPING: bool = True
    ENABLE_SITEMAP_CRAWLING: bool = True
    ENABLE_RECURSIVE_CRAWLING: bool = True
    MAX_CRAWL_DEPTH: int = 3
    MAX_PAGES_PER_DOMAIN: int = 100

    # Compliance
    ENABLE_ROBOTS_TXT_CHECK: bool = True
    ENABLE_PROXY_ROTATION: bool = False
    PROXY_LIST: List[str] = []  # ["http://proxy1:8080", "socks5://proxy2:1080"]
```

---

### **Phase 2: Template System & Field Mapping** (Week 2-3)

#### 2.1 Template Management
**Files to Create:**
- `backend/app/services/webscraper/templates/template_parser.py`
- `backend/app/services/webscraper/templates/template_validator.py`
- `backend/app/services/webscraper/templates/field_mapper.py`
- `backend/app/services/webscraper/templates/template_models.py`
- `backend/app/services/webscraper/templates/template_storage.py`

**Database Models:**
```python
# backend/app/services/webscraper/models/extraction_template.py
class ExtractionTemplate(Base):
    __tablename__ = "extraction_templates"

    id: UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: str = Column(String(255), nullable=False)
    description: Optional[str] = Column(Text)
    template_type: str = Column(String(50))  # excel, csv, json, yaml
    template_file_path: str = Column(String(512))  # MinIO path
    schema_definition: Dict = Column(JSONB)  # Parsed template schema

    # Fields definition
    fields: List[Dict] = Column(JSONB)  # Field definitions
    validation_rules: Dict = Column(JSONB)  # Validation rules
    transformation_rules: Dict = Column(JSONB)  # Transformation rules

    # Metadata
    version: int = Column(Integer, default=1)
    owner_id: UUID = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    is_active: bool = Column(Boolean, default=True)
    created_at: DateTime = Column(DateTime(timezone=True), server_default=func.now())
    updated_at: DateTime = Column(DateTime(timezone=True), onupdate=func.now())
```

**Template Schema Example:**
```json
{
  "name": "Company Data Extraction",
  "description": "Extract company information from websites",
  "fields": [
    {
      "name": "company_name",
      "type": "string",
      "required": true,
      "source_hint": {
        "type": "css",
        "selector": ".company-name, h1.title"
      },
      "validation": {
        "min_length": 2,
        "max_length": 200
      }
    },
    {
      "name": "revenue",
      "type": "number",
      "required": false,
      "source_hint": {
        "type": "llm",
        "prompt": "Extract the annual revenue of the company"
      },
      "transformation": "extract_number",
      "validation": {
        "min_value": 0
      }
    },
    {
      "name": "founded_year",
      "type": "integer",
      "required": false,
      "source_hint": {
        "type": "regex",
        "pattern": "Founded in (\\d{4})"
      },
      "validation": {
        "min_value": 1800,
        "max_value": 2025
      }
    },
    {
      "name": "category",
      "type": "string",
      "required": true,
      "source_hint": {
        "type": "jsonpath",
        "path": "$.category"
      },
      "transformation": "to_lowercase",
      "validation": {
        "enum": ["technology", "finance", "healthcare", "retail"]
      }
    }
  ]
}
```

#### 2.2 Data Extractors
**Files to Create:**
- `backend/app/services/webscraper/extractors/css_extractor.py`
- `backend/app/services/webscraper/extractors/xpath_extractor.py`
- `backend/app/services/webscraper/extractors/regex_extractor.py`
- `backend/app/services/webscraper/extractors/llm_extractor.py` (leverage existing llm_service)
- `backend/app/services/webscraper/extractors/structured_extractor.py`
- `backend/app/services/webscraper/extractors/extractor_factory.py`

**Features:**
- ✅ Multiple extraction strategies per field
- ✅ Fallback chain: CSS → XPath → Regex → LLM
- ✅ LLM-powered extraction for complex fields
- ✅ JSONPath/XPath for structured data

---

### **Phase 3: LangGraph Data Extraction Workflow** (Week 3-4)

#### 3.1 Workflow Architecture
**Files to Create:**
- `backend/app/services/webscraper/workflows/extraction_workflow.py`
- `backend/app/services/webscraper/workflows/workflow_nodes.py`
- `backend/app/services/webscraper/workflows/workflow_state.py`
- `backend/app/services/webscraper/workflows/workflow_tools.py`

**Workflow Design:**
```python
# LangGraph Data Extraction Workflow
┌─────────────────────────────────────────────────────────┐
│         LangGraph Data Extraction Workflow              │
└─────────────────────────────────────────────────────────┘

[Start] → [Parse Template] → [Plan Extraction]
            ↓
         [Scrape Sources] (parallel execution)
            │
            ├─> Source 1 → [Extract Data]
            ├─> Source 2 → [Extract Data]
            └─> Source N → [Extract Data]
            ↓
         [Consolidate Data]
            ↓
         [Transform & Map to Template]
            ↓
         [Validate Data Quality]
            ↓
         [Generate Output]
            ↓
         [Deliver Results]
            ↓
         [End]
```

**Workflow Nodes:**
```python
# backend/app/services/webscraper/workflows/workflow_nodes.py

class ExtractionWorkflowNodes:
    """Nodes for the data extraction workflow"""

    @staticmethod
    async def parse_template_node(state: WorkflowState) -> WorkflowState:
        """Parse template and extract schema"""
        template = await template_parser.parse(state.template_id)
        state.template_schema = template.schema_definition
        state.fields = template.fields
        return state

    @staticmethod
    async def plan_extraction_node(state: WorkflowState) -> WorkflowState:
        """Analyze template and plan extraction strategy"""
        plan = ExtractionPlanner.create_plan(
            urls=state.urls,
            fields=state.fields
        )
        state.extraction_plan = plan
        return state

    @staticmethod
    async def scrape_sources_node(state: WorkflowState) -> WorkflowState:
        """Scrape all URLs in parallel"""
        results = await asyncio.gather(*[
            scraper.scrape(url, strategy=plan.strategy)
            for url, plan in state.extraction_plan.items()
        ])
        state.raw_data = results
        return state

    @staticmethod
    async def extract_data_node(state: WorkflowState) -> WorkflowState:
        """Extract fields from scraped content"""
        extracted = {}
        for field in state.fields:
            extractor = ExtractorFactory.create(field.source_hint.type)
            value = await extractor.extract(state.raw_data, field)
            extracted[field.name] = value
        state.extracted_data = extracted
        return state

    @staticmethod
    async def consolidate_node(state: WorkflowState) -> WorkflowState:
        """Consolidate data from multiple sources"""
        df = pd.DataFrame(state.extracted_data)
        state.consolidated_data = df
        return state

    @staticmethod
    async def transform_node(state: WorkflowState) -> WorkflowState:
        """Apply transformations"""
        for field in state.fields:
            if field.transformation:
                transformer = TransformerFactory.create(field.transformation)
                state.consolidated_data[field.name] = transformer.apply(
                    state.consolidated_data[field.name]
                )
        return state

    @staticmethod
    async def validate_node(state: WorkflowState) -> WorkflowState:
        """Validate data quality"""
        validator = DataValidator(state.fields)
        validation_result = validator.validate(state.consolidated_data)
        state.validation_results = validation_result
        state.quality_score = validation_result.overall_score
        return state

    @staticmethod
    async def generate_output_node(state: WorkflowState) -> WorkflowState:
        """Generate output file"""
        generator = OutputFactory.create(state.output_format)
        output_file = await generator.generate(
            data=state.consolidated_data,
            template=state.template_schema
        )
        state.output_file_path = output_file
        return state

    @staticmethod
    async def deliver_node(state: WorkflowState) -> WorkflowState:
        """Deliver results via configured channel"""
        delivery_handler = DeliveryFactory.create(state.delivery_method)
        delivery_result = await delivery_handler.deliver(
            file_path=state.output_file_path,
            config=state.delivery_config
        )
        state.delivery_status = delivery_result
        return state
```

**State Management:**
```python
# backend/app/services/webscraper/workflows/workflow_state.py

class WorkflowState(TypedDict):
    """State for extraction workflow"""
    # Input
    job_id: str
    template_id: str
    urls: List[str]
    output_format: str  # excel, csv, json, etc.
    delivery_method: str  # download, email, webhook, etc.
    delivery_config: Dict

    # Parsed template
    template_schema: Dict
    fields: List[FieldDefinition]

    # Extraction plan
    extraction_plan: Dict[str, ExtractionPlan]

    # Scraped data
    raw_data: List[ScrapedContent]

    # Extracted data
    extracted_data: Dict[str, Any]

    # Consolidated data
    consolidated_data: pd.DataFrame

    # Validation
    validation_results: ValidationReport
    quality_score: float

    # Output
    output_file_path: str

    # Delivery
    delivery_status: DeliveryResult

    # Errors
    errors: List[Dict]
```

---

### **Phase 4: Data Processing Pipeline** (Week 4-5)

#### 4.1 Data Cleaning & Transformation
**Files to Create:**
- `backend/app/services/webscraper/processing/data_cleaner.py`
- `backend/app/services/webscraper/processing/data_transformer.py`
- `backend/app/services/webscraper/processing/deduplicator.py`

**Cleaning Operations:**
```python
class DataCleaner:
    """Data cleaning utilities"""

    @staticmethod
    def remove_html_tags(text: str) -> str:
        """Remove HTML tags"""
        return BeautifulSoup(text, 'html.parser').get_text()

    @staticmethod
    def normalize_whitespace(text: str) -> str:
        """Normalize whitespace"""
        return ' '.join(text.split())

    @staticmethod
    def standardize_dates(date_str: str, format: str = "%Y-%m-%d") -> str:
        """Standardize date formats"""
        # Auto-detect and convert to standard format
        pass

    @staticmethod
    def parse_numbers(text: str, locale: str = "en_US") -> float:
        """Parse numbers with locale support"""
        # Handle $1,234.56, €1.234,56, etc.
        pass

    @staticmethod
    def extract_emails(text: str) -> List[str]:
        """Extract email addresses"""
        pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        return re.findall(pattern, text)

    @staticmethod
    def extract_phone_numbers(text: str, country: str = "US") -> List[str]:
        """Extract phone numbers"""
        # Use phonenumbers library
        pass
```

#### 4.2 Data Validation
**Files to Create:**
- `backend/app/services/webscraper/processing/data_validator.py`
- `backend/app/services/webscraper/processing/quality_scorer.py`

**Validation Rules:**
```python
class DataValidator:
    """Data validation engine"""

    def __init__(self, fields: List[FieldDefinition]):
        self.fields = fields

    def validate(self, data: pd.DataFrame) -> ValidationReport:
        """Validate data against template rules"""
        errors = []

        for field in self.fields:
            # Type validation
            if not self._validate_type(data[field.name], field.type):
                errors.append({
                    'field': field.name,
                    'error': 'type_mismatch',
                    'expected': field.type
                })

            # Required field validation
            if field.required and data[field.name].isna().any():
                errors.append({
                    'field': field.name,
                    'error': 'missing_required_field'
                })

            # Range validation
            if field.validation.get('min_value'):
                if (data[field.name] < field.validation['min_value']).any():
                    errors.append({
                        'field': field.name,
                        'error': 'below_min_value'
                    })

            # Enum validation
            if field.validation.get('enum'):
                invalid = ~data[field.name].isin(field.validation['enum'])
                if invalid.any():
                    errors.append({
                        'field': field.name,
                        'error': 'invalid_enum_value'
                    })

            # Regex validation
            if field.validation.get('regex'):
                pattern = field.validation['regex']
                invalid = ~data[field.name].str.match(pattern)
                if invalid.any():
                    errors.append({
                        'field': field.name,
                        'error': 'regex_validation_failed'
                    })

        # Quality scoring
        quality_score = self._calculate_quality_score(data, errors)

        return ValidationReport(
            errors=errors,
            quality_score=quality_score,
            completeness=self._calculate_completeness(data),
            accuracy=self._calculate_accuracy(errors),
            is_valid=len(errors) == 0
        )
```

---

### **Phase 5: Output Generation & Delivery** (Week 5-6)

#### 5.1 Output Formats
**Files to Create:**
- `backend/app/services/webscraper/outputs/excel_generator.py`
- `backend/app/services/webscraper/outputs/csv_generator.py`
- `backend/app/services/webscraper/outputs/json_generator.py`
- `backend/app/services/webscraper/outputs/xml_generator.py`
- `backend/app/services/webscraper/outputs/parquet_generator.py`

**Excel Generator (Rich Formatting):**
```python
# backend/app/services/webscraper/outputs/excel_generator.py
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border
from openpyxl.chart import BarChart, Reference

class ExcelGenerator:
    """Generate rich Excel files with formatting"""

    async def generate(
        self,
        data: pd.DataFrame,
        template: Dict,
        output_path: str,
        include_charts: bool = True,
        include_summary: bool = True
    ) -> str:
        """Generate Excel file with formatting"""

        # Write data to Excel
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Data sheet
            data.to_excel(writer, sheet_name='Data', index=False)

            # Summary sheet (if enabled)
            if include_summary:
                summary = self._create_summary(data)
                summary.to_excel(writer, sheet_name='Summary', index=False)

        # Apply formatting
        wb = load_workbook(output_path)
        ws = wb['Data']

        # Header formatting
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF")

        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center')

        # Auto-adjust column widths
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width

        # Add charts (if enabled)
        if include_charts:
            self._add_charts(wb, data)

        wb.save(output_path)
        return output_path

    def _create_summary(self, data: pd.DataFrame) -> pd.DataFrame:
        """Create summary statistics"""
        summary_data = {
            'Metric': [],
            'Value': []
        }

        summary_data['Metric'].append('Total Records')
        summary_data['Value'].append(len(data))

        summary_data['Metric'].append('Complete Records')
        summary_data['Value'].append(data.dropna().shape[0])

        summary_data['Metric'].append('Completion Rate')
        summary_data['Value'].append(f"{(data.dropna().shape[0] / len(data) * 100):.2f}%")

        return pd.DataFrame(summary_data)
```

#### 5.2 Delivery Channels
**Files to Create:**
- `backend/app/services/webscraper/delivery/download_handler.py`
- `backend/app/services/webscraper/delivery/email_sender.py`
- `backend/app/services/webscraper/delivery/webhook_sender.py`
- `backend/app/services/webscraper/delivery/storage_uploader.py` (leverage existing MinIO)

**Dependencies:**
```txt
# Add to requirements.txt
openpyxl>=3.1.2          # Excel generation with rich formatting
pandas>=2.0.0            # Data manipulation
pyarrow>=14.0.0          # Parquet support
fastexcel>=0.2.0         # Fast Excel reading
```

---

### **Phase 6: Scheduling & Frontend UI** (Week 6-7)

#### 6.1 Job Scheduling
**Files to Create:**
- `backend/app/services/webscraper/scheduling/job_scheduler.py`
- `backend/app/services/webscraper/scheduling/change_detector.py`
- `backend/app/services/webscraper/scheduling/incremental_scraper.py`

**Database Model:**
```python
# backend/app/services/webscraper/models/job_schedule.py
class ExtractionJobSchedule(Base):
    __tablename__ = "extraction_job_schedules"

    id: UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_name: str = Column(String(255), nullable=False)
    template_id: UUID = Column(UUID(as_uuid=True), ForeignKey("extraction_templates.id"))

    # Schedule configuration
    schedule_type: str = Column(String(50))  # one_time, recurring, event_triggered
    cron_expression: Optional[str] = Column(String(100))  # For recurring jobs
    next_run_at: Optional[DateTime] = Column(DateTime(timezone=True))

    # Scraping configuration
    urls: List[str] = Column(JSONB)
    scraper_config: Dict = Column(JSONB)

    # Output configuration
    output_format: str = Column(String(50))
    delivery_method: str = Column(String(50))
    delivery_config: Dict = Column(JSONB)

    # Status
    is_active: bool = Column(Boolean, default=True)
    last_run_at: Optional[DateTime] = Column(DateTime(timezone=True))
    last_run_status: Optional[str] = Column(String(50))

    # Metadata
    owner_id: UUID = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at: DateTime = Column(DateTime(timezone=True), server_default=func.now())
    updated_at: DateTime = Column(DateTime(timezone=True), onupdate=func.now())
```

**Leverage Prefect for Scheduling:**
```python
# backend/app/services/webscraper/scheduling/job_scheduler.py
from prefect import flow, task
from prefect.deployments import Deployment
from prefect.server.schemas.schedules import CronSchedule

@flow(name="extraction_job_flow")
async def extraction_job_flow(job_id: str):
    """Prefect flow for extraction jobs"""
    # Load job configuration
    job = await load_job_config(job_id)

    # Execute extraction workflow
    workflow = ExtractionWorkflow()
    result = await workflow.run(
        template_id=job.template_id,
        urls=job.urls,
        output_format=job.output_format,
        delivery_method=job.delivery_method
    )

    # Update job status
    await update_job_status(job_id, result)

    return result

async def schedule_extraction_job(schedule: ExtractionJobSchedule):
    """Schedule an extraction job with Prefect"""
    deployment = Deployment.build_from_flow(
        flow=extraction_job_flow,
        name=f"extraction-job-{schedule.id}",
        parameters={"job_id": str(schedule.id)},
        schedule=CronSchedule(cron=schedule.cron_expression),
        is_schedule_active=schedule.is_active
    )

    deployment_id = await deployment.apply()
    return deployment_id
```

#### 6.2 Frontend UI - Extraction Wizard
**Files to Create:**
- `frontend/src/components/webscraper/ExtractionWizard.tsx`
- `frontend/src/components/webscraper/TemplateUpload.tsx`
- `frontend/src/components/webscraper/SourceConfiguration.tsx`
- `frontend/src/components/webscraper/FieldMapping.tsx`
- `frontend/src/components/webscraper/OutputConfiguration.tsx`
- `frontend/src/components/webscraper/JobMonitor.tsx`

**Wizard Flow:**
```typescript
// frontend/src/components/webscraper/ExtractionWizard.tsx
import React, { useState } from 'react';

interface ExtractionWizardProps {
  onComplete: (config: ExtractionConfig) => void;
}

export const ExtractionWizard: React.FC<ExtractionWizardProps> = ({ onComplete }) => {
  const [currentStep, setCurrentStep] = useState(1);
  const [config, setConfig] = useState<Partial<ExtractionConfig>>({});

  const steps = [
    { id: 1, name: 'Upload Template', component: TemplateUpload },
    { id: 2, name: 'Configure Sources', component: SourceConfiguration },
    { id: 3, name: 'Map Fields', component: FieldMapping },
    { id: 4, name: 'Configure Output', component: OutputConfiguration },
    { id: 5, name: 'Review & Launch', component: ReviewAndLaunch },
  ];

  const handleNext = (stepData: any) => {
    setConfig({ ...config, ...stepData });
    setCurrentStep(currentStep + 1);
  };

  const handleBack = () => {
    setCurrentStep(currentStep - 1);
  };

  const handleLaunch = async () => {
    // Submit extraction job
    const response = await fetch('/api/v1/webscraper/extraction-jobs', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config),
    });

    const result = await response.json();
    onComplete(result);
  };

  const CurrentStepComponent = steps[currentStep - 1].component;

  return (
    <div className="extraction-wizard">
      {/* Wizard header with steps */}
      <div className="wizard-steps">
        {steps.map((step) => (
          <div
            key={step.id}
            className={`step ${step.id === currentStep ? 'active' : ''} ${
              step.id < currentStep ? 'completed' : ''
            }`}
          >
            <div className="step-number">{step.id}</div>
            <div className="step-name">{step.name}</div>
          </div>
        ))}
      </div>

      {/* Current step content */}
      <div className="wizard-content">
        <CurrentStepComponent
          config={config}
          onNext={handleNext}
          onBack={handleBack}
          onLaunch={handleLaunch}
        />
      </div>
    </div>
  );
};
```

**Job Monitor Dashboard:**
```typescript
// frontend/src/components/webscraper/JobMonitor.tsx
import React, { useEffect, useState } from 'react';

export const JobMonitor: React.FC<{ jobId: string }> = ({ jobId }) => {
  const [job, setJob] = useState<ExtractionJob | null>(null);
  const [logs, setLogs] = useState<string[]>([]);

  useEffect(() => {
    // Poll job status
    const interval = setInterval(async () => {
      const response = await fetch(`/api/v1/webscraper/extraction-jobs/${jobId}`);
      const data = await response.json();
      setJob(data);

      // Fetch logs
      const logsResponse = await fetch(`/api/v1/webscraper/extraction-jobs/${jobId}/logs`);
      const logsData = await logsResponse.json();
      setLogs(logsData.logs);
    }, 2000);

    return () => clearInterval(interval);
  }, [jobId]);

  if (!job) return <div>Loading...</div>;

  return (
    <div className="job-monitor">
      <h2>Extraction Job: {job.name}</h2>

      {/* Progress bar */}
      <div className="progress-bar">
        <div
          className="progress-fill"
          style={{ width: `${job.progress_percentage}%` }}
        >
          {job.progress_percentage}%
        </div>
      </div>

      {/* Status cards */}
      <div className="status-cards">
        <div className="card">
          <div className="card-title">Status</div>
          <div className={`card-value status-${job.status}`}>
            {job.status.toUpperCase()}
          </div>
        </div>

        <div className="card">
          <div className="card-title">URLs Processed</div>
          <div className="card-value">
            {job.urls_processed} / {job.urls_total}
          </div>
        </div>

        <div className="card">
          <div className="card-title">Records Extracted</div>
          <div className="card-value">{job.records_extracted}</div>
        </div>

        <div className="card">
          <div className="card-title">Quality Score</div>
          <div className="card-value">{job.quality_score}%</div>
        </div>
      </div>

      {/* Live logs */}
      <div className="logs-panel">
        <h3>Live Logs</h3>
        <div className="logs-content">
          {logs.map((log, index) => (
            <div key={index} className="log-entry">
              {log}
            </div>
          ))}
        </div>
      </div>

      {/* Actions */}
      {job.status === 'completed' && (
        <div className="actions">
          <button onClick={() => downloadResults(jobId)}>
            Download Results
          </button>
          <button onClick={() => viewResults(jobId)}>
            View Results
          </button>
        </div>
      )}
    </div>
  );
};
```

---

### **Phase 7: Testing & Documentation** (Week 7-8)

#### 7.1 Testing
**Files to Create:**
- `backend/tests/webscraper/test_compliance_engine.py`
- `backend/tests/webscraper/test_template_parser.py`
- `backend/tests/webscraper/test_extraction_workflow.py`
- `backend/tests/webscraper/test_data_validator.py`
- `backend/tests/webscraper/test_output_generators.py`

#### 7.2 Documentation
**Files to Create:**
- `docs/guides/WEBSCRAPER_QUICKSTART.md`
- `docs/guides/TEMPLATE_GUIDE.md`
- `docs/guides/EXTRACTION_WORKFLOW_GUIDE.md`
- `docs/architecture/WEBSCRAPER_ARCHITECTURE.md`
- `backend/app/services/webscraper/README.md`

---

## 🔧 Technology Stack Enhancements

### Backend Dependencies (Add to requirements.txt)
```txt
# Web scraping
playwright>=1.41.0           # Browser automation (already exists)
trafilatura>=1.6.3          # Content extraction (already exists)
beautifulsoup4>=4.12.3      # HTML parsing (already exists)
httpx>=0.27.0               # Async HTTP (already exists)

# NEW: Compliance & advanced scraping
robotexclusionrulesparser>=1.7.1  # Robots.txt parsing
aiohttp-socks>=0.8.4        # SOCKS proxy support
fake-useragent>=1.5.1       # User agent rotation
authlib>=1.3.0              # OAuth2/JWT authentication

# NEW: Data processing
openpyxl>=3.1.2             # Excel with rich formatting
xlsxwriter>=3.1.9           # Excel writing
pandas>=2.0.0               # Data manipulation
pyarrow>=14.0.0             # Parquet support
fastexcel>=0.2.0            # Fast Excel reading
lxml>=4.9.0                 # XML/XPath processing
jsonpath-ng>=1.6.1          # JSONPath support

# NEW: Validation
cerberus>=1.3.5             # Schema validation
jsonschema>=4.21.1          # JSON schema validation
pydantic>=2.8.2             # Already exists

# Workflow orchestration (already exists)
langchain>=0.2.16
langgraph>=0.2.16
prefect>=3.0.0

# Storage (already exists)
sqlalchemy>=2.0.25
asyncpg>=0.29.0
redis>=5.0.1
minio>=7.2.3
```

### Frontend Dependencies (Add to package.json)
```json
{
  "dependencies": {
    "@tanstack/react-table": "^8.11.0",
    "react-dropzone": "^14.2.3",
    "xlsx": "^0.18.5",
    "papaparse": "^5.4.1",
    "recharts": "^2.10.3",
    "react-syntax-highlighter": "^15.5.0"
  }
}
```

---

## 📊 API Endpoints

### New REST Endpoints
```python
# Template Management
POST   /api/v1/webscraper/templates                    # Upload template
GET    /api/v1/webscraper/templates                    # List templates
GET    /api/v1/webscraper/templates/{id}               # Get template
PUT    /api/v1/webscraper/templates/{id}               # Update template
DELETE /api/v1/webscraper/templates/{id}               # Delete template

# Extraction Jobs
POST   /api/v1/webscraper/extraction-jobs              # Create extraction job
GET    /api/v1/webscraper/extraction-jobs              # List jobs
GET    /api/v1/webscraper/extraction-jobs/{id}         # Get job status
GET    /api/v1/webscraper/extraction-jobs/{id}/logs    # Get job logs
GET    /api/v1/webscraper/extraction-jobs/{id}/results # Get job results
DELETE /api/v1/webscraper/extraction-jobs/{id}         # Cancel/delete job

# Scheduling
POST   /api/v1/webscraper/schedules                    # Create schedule
GET    /api/v1/webscraper/schedules                    # List schedules
GET    /api/v1/webscraper/schedules/{id}               # Get schedule
PUT    /api/v1/webscraper/schedules/{id}               # Update schedule
DELETE /api/v1/webscraper/schedules/{id}               # Delete schedule
POST   /api/v1/webscraper/schedules/{id}/trigger       # Trigger manually

# Capabilities
GET    /api/v1/webscraper/capabilities                 # Get scraper capabilities
GET    /api/v1/webscraper/strategies                   # List available strategies
```

---

## 🎯 Success Metrics

### Performance KPIs
- **Extraction Success Rate**: > 95%
- **Data Quality Score**: > 90%
- **Throughput**: > 100 URLs/hour
- **Average Latency**: < 5 seconds per URL
- **Cost per Extraction**: < $0.10

### Business Metrics
- **Templates Created**: Track adoption
- **Jobs Scheduled**: Measure automation
- **Integrations Active**: Track ecosystem growth
- **Data Volume**: Total records extracted

---

## ❓ Questions for User Confirmation

### 1. Priority Features
**Question**: Which phase should we prioritize first?
- **Option A**: Phase 1 (Compliance + Advanced Strategies) - Foundation
- **Option B**: Phase 2 (Template System) - Core feature
- **Option C**: Phase 3 (LangGraph Workflow) - Innovation
- **Recommendation**: **Phase 1 → Phase 2 → Phase 3** (sequential)

### 2. LLM Provider
**Question**: Which LLM provider should be the default for data extraction?
- **Option A**: OpenAI (GPT-4) - Best quality, cost $$
- **Option B**: Anthropic (Claude) - Good balance, cost $$
- **Option C**: Ollama (Local) - Free, requires GPU
- **Recommendation**: **OpenAI as default**, with Ollama fallback

### 3. Storage Strategy
**Question**: Where should we store templates and extraction results?
- **Option A**: PostgreSQL (structured data) + MinIO (files)
- **Option B**: MinIO only (simpler)
- **Option C**: PostgreSQL only (easier queries)
- **Recommendation**: **Option A** (leverage existing stack)

### 4. Compliance Level Default
**Question**: What should be the default compliance level?
- **Option A**: `strict` - Maximum compliance, slower
- **Option B**: `balanced` - Reasonable compliance, good performance
- **Option C**: `aggressive` - Minimal compliance, fastest
- **Recommendation**: **balanced** (good default for enterprise)

---

## 🚀 Next Steps

### Immediate Actions
1. ✅ Review and approve this implementation plan
2. ✅ Confirm priority order and preferences (answer questions above)
3. ✅ Create feature branch: `claude/enterprise-scraper-implementation`
4. ✅ Begin Phase 1 implementation

### Development Approach
- **Modular**: Each phase is self-contained and independently testable
- **Plug-and-Play**: New features integrate seamlessly with existing code
- **Backward Compatible**: Existing scraper functionality remains intact
- **Well Documented**: Comprehensive docs and examples

---

## 📝 Appendix

### A. File Organization Checklist
- [ ] Create `backend/app/services/webscraper/` package
- [ ] Move existing `scraper_strategies.py` to `strategies/` subpackage
- [ ] Create all new subdirectories (compliance, templates, extractors, etc.)
- [ ] Update imports across codebase
- [ ] Add `__init__.py` to all packages

### B. Database Migration Plan
- [ ] Create migration for `extraction_templates` table
- [ ] Create migration for `extraction_jobs` table
- [ ] Create migration for `extraction_job_schedules` table
- [ ] Create migration for `extraction_results` table
- [ ] Add indexes for performance

### C. Configuration Updates
- [ ] Add all new settings to `backend/app/core/config.py`
- [ ] Update `.env.example` with new variables
- [ ] Document environment variables in README

---

**End of Implementation Plan**
