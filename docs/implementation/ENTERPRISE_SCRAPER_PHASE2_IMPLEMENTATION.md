# Enterprise Web Scraper - Phase 2 Implementation Summary

> **Implementation Date**: 2025-11-16
> **Status**: ✅ Complete - Phase 2 (Template System & Field Mapping)
> **Lines of Code**: ~3,500 new lines

---

## 🎯 What Was Implemented

This implementation delivers **Phase 2** of the Enterprise Web Scraper platform, focusing on:

1. **Template System** - Excel/CSV/JSON template parsing and management
2. **Data Extractors** - Multiple extraction strategies (CSS, XPath, Regex, LLM, Structured)
3. **Field Mapping & Validation** - Data transformation and quality validation
4. **Template Storage** - PostgreSQL + MinIO integration for template management

---

## 📦 New Components Created

### 1. Template Management System (`backend/app/services/webscraper/templates/`)

#### `template_models.py` (415 lines)
- **Pydantic Models** for template system
- **SourceHint**: Configuration for field extraction strategies
- **ValidationRule**: Field validation rules
- **TransformationRule**: Data transformation rules
- **FieldDefinition**: Complete field specifications
- **ExtractionTemplate**: Full template schema
- **ExtractionJob**: Job execution tracking
- **ExtractionResult**: Individual extraction results
- **ExtractionSchedule**: Scheduled extraction jobs

**Key Classes**:
```python
class SourceHint(BaseModel):
    type: Literal["css", "xpath", "regex", "llm", "jsonpath", "structured"]
    selector: Optional[str] = None  # CSS selector
    xpath: Optional[str] = None  # XPath expression
    pattern: Optional[str] = None  # Regex pattern
    prompt: Optional[str] = None  # LLM extraction prompt
    path: Optional[str] = None  # JSONPath

class FieldDefinition(BaseModel):
    name: str
    type: Literal["string", "integer", "float", "boolean", "date", "datetime", "array", "object"]
    required: bool = False
    source_hint: Optional[SourceHint] = None
    validation: Optional[ValidationRule] = None
    transformation: Optional[TransformationRule] = None
```

#### `template_parser.py` (360 lines)
- **Parses templates** from multiple formats
- **Supported Formats**: Excel (.xlsx, .xls), CSV, JSON, YAML
- **Excel/CSV Structure**:
  ```
  | field_name | type    | required | source_type | source_value | validation | transformation |
  |------------|---------|----------|-------------|--------------|------------|----------------|
  | name       | string  | yes      | css         | .title       | min:2      | trim           |
  | price      | float   | no       | regex       | \$(\d+)      | min:0      | extract_number |
  ```

**Key Methods**:
- `parse_file(file_path)` - Auto-detect and parse any supported format
- `parse_excel(file_path)` - Parse Excel templates
- `parse_csv(file_path)` - Parse CSV templates
- `parse_json(file_path)` - Parse JSON templates
- `parse_yaml(file_path)` - Parse YAML templates

#### `template_validator.py` (280 lines)
- **Template validation** - Ensure template structure is correct
- **Data validation** - Validate extracted data against template rules
- **Quality scoring** - Calculate data quality metrics

**Validation Rules Supported**:
- **String**: `min_length`, `max_length`, `regex`, `enum`
- **Numeric**: `min_value`, `max_value`
- **Date**: `date_format`, `min_date`, `max_date`

**Key Methods**:
- `validate_template(template_data)` - Validate template structure
- `validate_extracted_data(data, fields)` - Validate extracted data
- Returns `ValidationReport` with:
  - `is_valid: bool`
  - `errors: List[Dict]`
  - `quality_score: float`
  - `completeness: float`
  - `accuracy: float`

#### `field_mapper.py` (150 lines)
- **Map extracted data** to template fields
- **Type conversion** - Convert values to specified types
- **Transformations** - Apply data transformations

**Supported Transformations**:
- Text: `to_lowercase`, `to_uppercase`, `title_case`, `trim`, `normalize_whitespace`
- Pattern: `replace`, `split`, `join`
- Extraction: `extract_number`, `extract_email`, `extract_phone`, `remove_html`

**Key Methods**:
- `map_data(extracted_data, field_definitions)` - Map and transform data
- `_convert_type(value, target_type)` - Type conversion
- `_apply_transformation(value, transformation)` - Apply transformations

#### `template_storage.py` (205 lines)
- **PostgreSQL storage** for template metadata
- **MinIO storage** for template files
- **Template versioning**
- **CRUD operations**

**Key Methods**:
- `create_template(template_data, file_path)` - Create new template
- `get_template(template_id)` - Retrieve template by ID
- `list_templates(active_only, limit, offset)` - List templates with pagination
- `update_template(template_id, updates)` - Update template
- `delete_template(template_id)` - Soft delete (set `is_active=False`)
- `upload_template_file(file_content, filename)` - Upload to MinIO

---

### 2. Data Extractors (`backend/app/services/webscraper/extractors/`)

#### `css_extractor.py` (235 lines)
- **CSS selector-based extraction** from HTML
- **Fallback chain support** - Try multiple selectors
- **Attribute extraction** - Extract attributes instead of text
- **Table extraction** - Parse HTML tables to dictionaries
- **List extraction** - Extract list items

**Key Methods**:
```python
extract(html_content, selector, attribute=None, fallback_selectors=None, multiple=False)
extract_table(html_content, table_selector='table')
extract_list(html_content, list_selector='ul, ol')
```

#### `xpath_extractor.py` (215 lines)
- **XPath expression extraction** from HTML/XML
- **Namespace support** for XML
- **Attribute extraction**
- **Table extraction**

**Key Methods**:
```python
extract(content, xpath, attribute=None, multiple=False, is_xml=False, namespaces=None)
extract_with_fallback(content, xpath_expressions, attribute=None)
extract_table(content, table_xpath='//table')
```

#### `regex_extractor.py` (280 lines)
- **Pattern-based extraction** from text
- **Named group extraction**
- **Common pattern library** (20+ predefined patterns)

**Common Patterns**:
- `email`, `url`, `phone_us`, `phone_intl`, `ssn`, `zip_code`
- `credit_card`, `ipv4`, `date_iso`, `date_us`, `time`
- `currency_usd`, `number`, `integer`, `hex_color`

**Key Methods**:
```python
extract(text, pattern, group=0, multiple=False)
extract_named_groups(text, pattern, multiple=False)
extract_common(text, pattern_name, multiple=True)
extract_emails(text)
extract_urls(text)
extract_phone_numbers(text, format='us')
extract_numbers(text, integer_only=False)
```

#### `llm_extractor.py` (345 lines)
- **LLM-powered extraction** using Ollama, OpenAI, Anthropic
- **Structured output** - Extract according to schema
- **Multi-field extraction** - Extract multiple fields in one call
- **Confidence scoring**

**Key Methods**:
```python
async extract(content, prompt, field_name, field_type, llm_provider="ollama")
async extract_multiple_fields(content, field_definitions, llm_provider="ollama")
async extract_structured(content, schema, llm_provider="ollama")
```

**Example Usage**:
```python
# Extract a single field
result = await llm_extractor.extract(
    content="Founded in 1998, Acme Corp has 500 employees",
    prompt="Extract the founding year",
    field_name="founded_year",
    field_type="integer",
    llm_provider="ollama"
)
# Result: 1998
```

#### `structured_extractor.py` (350 lines)
- **JSON extraction** with JSONPath
- **JSON-LD** structured data extraction
- **Microdata** extraction (Schema.org)
- **OpenGraph** metadata extraction
- **Meta tags** extraction

**Key Methods**:
```python
extract_json(json_content, path=None)
extract_json_ld(html_content, type_filter=None)
extract_microdata(html_content, itemtype=None)
extract_opengraph(html_content)
extract_schema_org(html_content, schema_type=None)
extract_all_structured_data(html_content)
```

#### `extractor_factory.py` (250 lines)
- **Factory pattern** for extractor creation
- **Extraction with hints** - Use SourceHint configuration
- **Automatic fallback** to LLM if primary extraction fails
- **Capability reporting**

**Key Methods**:
```python
create_extractor(extractor_type)
async extract_with_hint(content, source_hint, field_name, field_type)
async extract_with_fallback(content, source_hints, field_name)
async extract_with_default_fallback(content, source_hint, field_name)  # Auto-fallback to LLM
get_extractor_capabilities()
```

---

## 🗄️ Database Changes

### Migration: `backend/migrations/add_extraction_templates.sql` (220 lines)

#### New Tables Created:

**1. extraction_templates**
```sql
CREATE TABLE extraction_templates (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    template_type VARCHAR(50) NOT NULL,  -- excel, csv, json, yaml
    template_file_path VARCHAR(512),     -- MinIO path
    schema_definition JSONB NOT NULL,
    fields JSONB NOT NULL,               -- Field definitions
    validation_rules JSONB,
    transformation_rules JSONB,
    version INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE
);
```

**2. extraction_jobs**
```sql
CREATE TABLE extraction_jobs (
    id UUID PRIMARY KEY,
    job_name VARCHAR(255) NOT NULL,
    template_id UUID REFERENCES extraction_templates(id),
    urls JSONB NOT NULL,
    scraper_config JSONB,
    status VARCHAR(50) DEFAULT 'pending',
    progress_percentage INTEGER DEFAULT 0,
    urls_total INTEGER,
    urls_processed INTEGER DEFAULT 0,
    records_extracted INTEGER DEFAULT 0,
    quality_score FLOAT,
    validation_errors JSONB,
    output_format VARCHAR(50) NOT NULL,
    output_file_path VARCHAR(512),
    delivery_method VARCHAR(50),
    delivery_config JSONB,
    delivery_status VARCHAR(50),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    execution_time_ms FLOAT,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE
);
```

**3. extraction_results**
```sql
CREATE TABLE extraction_results (
    id UUID PRIMARY KEY,
    job_id UUID REFERENCES extraction_jobs(id),
    source_url VARCHAR(1024) NOT NULL,
    source_index INTEGER,
    extracted_data JSONB NOT NULL,
    raw_content TEXT,
    extraction_confidence FLOAT,
    validation_errors JSONB,
    scraped_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE
);
```

**4. extraction_job_schedules**
```sql
CREATE TABLE extraction_job_schedules (
    id UUID PRIMARY KEY,
    job_name VARCHAR(255) NOT NULL,
    template_id UUID REFERENCES extraction_templates(id),
    schedule_type VARCHAR(50) NOT NULL,  -- one_time, recurring, event_triggered
    cron_expression VARCHAR(100),
    next_run_at TIMESTAMP WITH TIME ZONE,
    urls JSONB NOT NULL,
    scraper_config JSONB,
    output_format VARCHAR(50) NOT NULL,
    delivery_method VARCHAR(50) NOT NULL,
    delivery_config JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    last_run_at TIMESTAMP WITH TIME ZONE,
    last_run_status VARCHAR(50),
    last_job_id UUID,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE
);
```

**Indexes Created**:
- `idx_extraction_templates_active` - Active templates
- `idx_extraction_templates_type` - Template type
- `idx_extraction_jobs_template` - Jobs by template
- `idx_extraction_jobs_status` - Jobs by status
- `idx_extraction_jobs_created` - Jobs by creation date
- `idx_extraction_results_job` - Results by job
- `idx_extraction_schedules_active` - Active schedules
- `idx_extraction_schedules_next_run` - Next run time

**Triggers**:
- Auto-update `updated_at` on row modification

---

## 📁 Files Created

```
backend/app/services/webscraper/
├── extractors/
│   ├── __init__.py                     (26 lines)
│   ├── css_extractor.py                (235 lines) ⭐
│   ├── xpath_extractor.py              (215 lines) ⭐
│   ├── regex_extractor.py              (280 lines) ⭐
│   ├── llm_extractor.py                (345 lines) ⭐
│   ├── structured_extractor.py         (350 lines) ⭐
│   └── extractor_factory.py            (250 lines) ⭐
│
├── templates/
│   ├── __init__.py                     (TBD)
│   ├── template_models.py              (415 lines) ⭐
│   ├── template_parser.py              (360 lines) ⭐
│   ├── template_validator.py           (280 lines) ⭐
│   ├── field_mapper.py                 (150 lines) ⭐
│   └── template_storage.py             (205 lines) ⭐

backend/migrations/
└── add_extraction_templates.sql        (220 lines) ⭐

Total: ~3,500 lines of new code
```

---

## 🚀 Usage Examples

### Example 1: Create Template from JSON

```json
{
  "name": "Product Data Extraction",
  "description": "Extract product information from e-commerce sites",
  "template_type": "json",
  "schema_definition": {
    "version": "1.0",
    "type": "product_data"
  },
  "fields": [
    {
      "name": "product_name",
      "type": "string",
      "required": true,
      "source_hint": {
        "type": "css",
        "selector": "h1.product-title, .product-name"
      },
      "validation": {
        "min_length": 2,
        "max_length": 200
      }
    },
    {
      "name": "price",
      "type": "float",
      "required": true,
      "source_hint": {
        "type": "regex",
        "pattern": "\\$([\\d,]+\\.\\d{2})",
        "group": 1
      },
      "transformation": "extract_number",
      "validation": {
        "min_value": 0
      }
    },
    {
      "name": "availability",
      "type": "string",
      "required": false,
      "source_hint": {
        "type": "llm",
        "prompt": "Is this product in stock? Return 'in_stock' or 'out_of_stock'"
      },
      "validation": {
        "enum": ["in_stock", "out_of_stock", "preorder"]
      }
    }
  ]
}
```

### Example 2: Create Template from Excel

Excel template structure:
| field_name   | type    | required | source_type | source_value          | validation | transformation |
|--------------|---------|----------|-------------|-----------------------|------------|----------------|
| title        | string  | yes      | css         | .article-title        | min:5      | trim           |
| author       | string  | yes      | css         | .author-name          |            | title_case     |
| publish_date | date    | no       | regex       | Published: (.*)       |            |                |
| category     | string  | yes      | jsonpath    | $.category            | enum:tech,business,health |  |

### Example 3: Use Extractors Directly

```python
from backend.app.services.webscraper.extractors import ExtractorFactory

# Initialize factory
factory = ExtractorFactory(llm_service=llm_service)

# Extract with CSS
html = "<div class='price'>$99.99</div>"
price_text = factory.css_extractor.extract(html, ".price")
# Result: "$99.99"

# Extract with Regex
text = "Contact us at support@example.com"
emails = factory.regex_extractor.extract_emails(text)
# Result: ["support@example.com"]

# Extract with LLM
content = "Founded in 1998, Acme Corp has grown to 500 employees"
result = await factory.llm_extractor.extract(
    content=content,
    prompt="Extract the number of employees",
    field_name="employee_count",
    field_type="integer",
    llm_provider="ollama"
)
# Result: 500

# Extract structured data
html_with_jsonld = """
<script type="application/ld+json">
{
  "@context": "http://schema.org",
  "@type": "Product",
  "name": "Acme Widget",
  "price": "29.99"
}
</script>
"""
structured = factory.structured_extractor.extract_json_ld(html_with_jsonld)
# Result: [{"@context": "...", "@type": "Product", "name": "Acme Widget", ...}]
```

### Example 4: Extract with Source Hint

```python
from backend.app.services.webscraper.extractors import ExtractorFactory

factory = ExtractorFactory(llm_service=llm_service)

html = "<h1 class='title'>Amazing Product</h1>"

source_hint = {
    "type": "css",
    "selector": "h1.title",
    "fallback_selectors": [".product-title", ".heading"]
}

result = await factory.extract_with_hint(
    content=html,
    source_hint=source_hint,
    field_name="product_name",
    field_type="string"
)
# Result: "Amazing Product"

# If CSS fails, automatically fallback to LLM
result_with_auto_fallback = await factory.extract_with_default_fallback(
    content=html,
    source_hint=source_hint,
    field_name="product_name",
    field_type="string",
    llm_provider="ollama"
)
```

---

## 📊 Key Features

### Multi-Strategy Extraction
- **6 extraction strategies**: CSS, XPath, Regex, LLM, JSONPath, Structured
- **Automatic fallback chain**: Try multiple strategies until one succeeds
- **LLM fallback**: Automatically use LLM if other strategies fail

### Template Flexibility
- **Multiple formats**: Excel, CSV, JSON, YAML
- **Field-level configuration**: Each field can use different extraction strategy
- **Validation rules**: Enforce data quality constraints
- **Transformations**: Clean and normalize extracted data

### Data Quality
- **Validation scoring**: Automatic quality score calculation
- **Completeness metrics**: Track missing vs present fields
- **Accuracy metrics**: Track validation errors
- **Field-level errors**: Detailed error reporting per field

### Storage & Management
- **PostgreSQL metadata**: Fast queries and filtering
- **MinIO file storage**: Template files stored separately
- **Versioning**: Track template versions
- **Soft delete**: Never lose template history

---

## 🔧 Dependencies Added

Added to `requirements.txt`:

```txt
# Phase 2: Template System & Data Extraction
jsonpath-ng==1.6.1               # JSONPath support
pandas>=2.0.0                    # Data manipulation
xlsxwriter>=3.1.9                # Excel writing
fastexcel>=0.2.0                 # Fast Excel reading
pyarrow>=14.0.0                  # Parquet support
```

---

## ✅ Implementation Checklist

### Phase 2 - Template System (✅ COMPLETE)

#### Template Management
- [x] Pydantic models for templates
- [x] Template parser (Excel, CSV, JSON, YAML)
- [x] Template validator
- [x] Field mapper
- [x] Template storage (PostgreSQL + MinIO)

#### Data Extractors
- [x] CSS selector extractor
- [x] XPath extractor
- [x] Regex extractor
- [x] LLM extractor (Ollama, OpenAI, Anthropic)
- [x] Structured data extractor (JSON-LD, Microdata, OpenGraph)
- [x] Extractor factory with fallback chains

#### Database
- [x] extraction_templates table
- [x] extraction_jobs table
- [x] extraction_results table
- [x] extraction_job_schedules table
- [x] Indexes and triggers
- [x] Sample template data

#### Dependencies
- [x] jsonpath-ng
- [x] pandas
- [x] xlsxwriter
- [x] fastexcel
- [x] pyarrow

---

## 📝 Next Steps (Phase 3 & Beyond)

### Phase 3 - LangGraph Extraction Workflow (Planned)
- [ ] Extraction workflow DAG with LangGraph
- [ ] Parallel URL processing
- [ ] Data consolidation node
- [ ] Transformation node
- [ ] Validation node
- [ ] Output generation node
- [ ] Delivery node

### Phase 4 - Data Processing Pipeline (Planned)
- [ ] Data cleaning utilities
- [ ] Data transformer
- [ ] Deduplicator
- [ ] Quality scorer

### Phase 5 - Output Generation & Delivery (Planned)
- [ ] Rich Excel generator (formatting, charts)
- [ ] CSV, JSON, XML, Parquet generators
- [ ] Email delivery
- [ ] Webhook delivery
- [ ] Cloud storage upload (S3, GCS, Azure)

### Phase 6 - API & Frontend (Planned)
- [ ] REST API endpoints for template management
- [ ] REST API endpoints for extraction jobs
- [ ] Frontend extraction wizard
- [ ] Frontend template builder
- [ ] Frontend job monitoring dashboard

---

## 🎉 Summary

**Phase 2** delivers a production-ready template-based extraction system:

✅ **Flexible Templates**: Support Excel, CSV, JSON, YAML
✅ **Multi-Strategy Extraction**: 6 different extraction methods
✅ **LLM Integration**: Ollama, OpenAI, Anthropic for intelligent extraction
✅ **Data Quality**: Comprehensive validation and scoring
✅ **Storage**: PostgreSQL + MinIO integration
✅ **Extensible**: Easy to add new extractors and transformations

**Total Implementation**: ~3,500 lines across 13 new modules

**Ready for Phase 3**: LangGraph Workflows & Data Processing! 🚀
