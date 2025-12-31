# TalentSearch - System Architecture

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture Patterns](#architecture-patterns)
3. [Component Architecture](#component-architecture)
4. [Data Flow](#data-flow)
5. [Class Hierarchy](#class-hierarchy)
6. [LLM Integration](#llm-integration)
7. [Database Design](#database-design)
8. [Security Considerations](#security-considerations)

## System Overview

TalentSearch implements a multi-layered architecture combining web interface, business logic, AI processing, and data persistence layers. The system follows an object-oriented design with inheritance-based component organization.

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Presentation Layer                     │
│                    (Streamlit UI)                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │  Search  │  │  Alerts  │  │ Upload   │  │ Helpers │ │
│  │   Tab    │  │   Tab    │  │   Tab    │  │         │ │
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘ │
└─────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────────┐
│                    Business Logic Layer                  │
│  ┌──────────────┐  ┌───────────────┐  ┌──────────────┐ │
│  │  SearchJob   │  │CreateAlerts   │  │MetaCreation  │ │
│  │              │  │               │  │              │ │
│  └──────────────┘  └───────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────────┐
│                    AI/LLM Layer                          │
│  ┌──────────────┐  ┌───────────────┐  ┌──────────────┐ │
│  │  LangChain   │  │  OpenAI API   │  │  Prompt      │ │
│  │  Chains      │  │  (GPT-4o-mini)│  │  Templates   │ │
│  └──────────────┘  └───────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────────┐
│                    Data Layer                            │
│  ┌──────────────┐  ┌───────────────┐  ┌──────────────┐ │
│  │  SQLite DB   │  │  Session      │  │  File        │ │
│  │ (example.db) │  │  State        │  │  Storage     │ │
│  └──────────────┘  └───────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## Architecture Patterns

### 1. Inheritance-Based Design

The application uses a hierarchical inheritance pattern for code reuse and logical organization:

```python
CustomLogger (Base)
    └── ConfigLoader
        └── RecruitersList
            └── CreateAlerts
                └── MetaCreation
                    └── SearchJob
                        └── CreateUI
```

**Benefits:**
- Configuration and logging available to all components
- Progressive feature enhancement through inheritance chain
- Single source of truth for shared functionality
- Simplified dependency injection

### 2. Chain of Responsibility Pattern

LangChain implements the chain pattern for LLM operations:

```python
Prompt Template → LLM → Parser → Output
```

This allows:
- Sequential processing of data
- Easy modification of processing steps
- Error handling at each stage
- Reusable chain components

### 3. Session State Pattern

Streamlit's session state manages application state:

```python
st.session_state = {
    "data": DataFrame,           # Raw uploaded data
    "meta_response": DataFrame,  # Processed metadata
    "tagged": bool,              # Data processing flag
    "filter": list               # Active filters
}
```

### 4. Template Method Pattern

Used in rendering methods where the base structure is defined but specific implementations vary:

```python
class CreateUI:
    def render_ui(self):
        # Template structure
        with self.tab1:
            self.render_search()
        with self.tab2:
            self.render_alerts()
        with self.tab3:
            self.render_upload_page()
```

## Component Architecture

### 1. Interface Layer (`interface/`)

#### SearchJob (`search.py`)
**Purpose**: Manages job search functionality using SQL and semantic queries

**Key Components:**
- SQL query chain creation
- Natural language to SQL conversion
- Query cleaning and execution
- Results filtering and display

**Dependencies:**
- LangChain SQL tools
- SQLDatabase utility
- Custom filter module

#### CreateAlerts (`alerts.py`)
**Purpose**: Displays recruiter-specific job alerts

**Key Components:**
- Recruiter filtering
- Job-recruiter mapping display
- Recruiter selection interface

**Dependencies:**
- RecruitersList base class
- Pydantic parsers
- Custom prompts

#### MetaCreation (`upload.py`)
**Purpose**: Handles file upload and metadata generation

**Key Components:**
- File upload handling (Excel/CSV)
- Metadata extraction via LLM
- Database population
- Data cleaning and transformation

**Process Flow:**
```
Upload → Parse → Extract Metadata → Match Recruiters → Store in DB
```

#### RecruitersList (`recruiter.py`)
**Purpose**: Manages recruiter profiles and configuration

**Key Components:**
- Recruiter list management
- Output column configuration
- Corporate title definitions

### 2. Utility Layer (`utils/`)

#### ConfigLoader (`config_reader.py`)
**Purpose**: Central configuration management

**Responsibilities:**
- Load configuration from `config.ini`
- Initialize LLM client
- Load recruiter profiles
- Set up LangSmith tracing
- Create required directories

**Key Features:**
```python
- LLM initialization with OpenAI
- Environment variable management
- Configuration validation
- Automatic directory creation
```

#### CustomLogger (`log_writer.py`)
**Purpose**: Application-wide logging

**Features:**
- Timestamped log files
- Error tracking with line numbers
- Daily log rotation
- Structured error reporting

**Log Structure:**
```
./logs/DD-MM-YY/HH.log
```

#### CustomFilter (`custom_filter.py`)
**Purpose**: Dynamic DataFrame filtering in UI

**Filter Types:**
- Categorical (multiselect)
- Numeric (slider range)
- DateTime (date range)
- Text (substring/regex)

#### CustomPrompts (`custom_prompts.py`)
**Purpose**: LLM prompt templates

**Templates:**
1. **prompt_recruiter**: Match jobs to recruiters
2. **prompt_job**: Extract job metadata
3. **prompt_job_type**: Classify job types

#### CustomTemplates (`custom_templates.py`)
**Purpose**: Pydantic data validation models

**Models:**
1. **RecruiterTemplate**: Recruiter matching output
2. **JobTemplate**: Job metadata structure
3. **SectorTemplate**: Job type classification

## Data Flow

### Upload and Processing Flow

```
┌──────────────┐
│ User Upload  │
│ (Excel/CSV)  │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ File Parser  │
│ (Pandas)     │
└──────┬───────┘
       │
       ▼
┌──────────────────────┐
│ Metadata Extraction  │
│ (LLM Chain 1)        │
│ - Domain/Sector      │
│ - Location           │
│ - Work arrangement   │
│ - Seniority          │
│ - Salary             │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ Job Type Matching    │
│ (LLM Chain 2)        │
│ - Business sector    │
│ - Specific job type  │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ Recruiter Matching   │
│ (LLM Chain 3)        │
│ - Best fit recruiter │
│ - Relevance score    │
│ - Justification      │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ Data Cleaning        │
│ - Formatting         │
│ - Capitalization     │
│ - Date parsing       │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ Content Generation   │
│ (Concatenate fields) │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ SQLite Storage       │
│ (example.db)         │
└──────────────────────┘
```

### Search Flow

```
┌──────────────┐
│ User Query   │
│ (Natural     │
│  Language)   │
└──────┬───────┘
       │
       ▼
┌──────────────────────┐
│ LLM SQL Generation   │
│ - Parse intent       │
│ - Generate SQL       │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ Query Cleaning       │
│ - Extract SELECT     │
│ - Validate syntax    │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ Database Execution   │
│ (SQLite)             │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ Results Filtering    │
│ - Apply user filters │
│ - Format display     │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ UI Rendering         │
│ - DataFrame          │
│ - Expandable details │
└──────────────────────┘
```

## Class Hierarchy

### Detailed Class Structure

```
┌─────────────────────────────────────────────────────────┐
│ CustomLogger                                            │
├─────────────────────────────────────────────────────────┤
│ + setup_logger()                                        │
│ + write_error_log(exc_type, exc_tb, msg)               │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│ ConfigLoader                                            │
├─────────────────────────────────────────────────────────┤
│ - config: ConfigParser                                  │
│ - config_data: dict                                     │
│ - llm: ChatModel                                        │
│ - picklist: dict                                        │
├─────────────────────────────────────────────────────────┤
│ + read_config() → dict                                  │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│ RecruitersList                                          │
├─────────────────────────────────────────────────────────┤
│ - recruiters_list: list                                 │
│ - output_columns: list                                  │
│ - corporate_titles: list                                │
├─────────────────────────────────────────────────────────┤
│ + render_recruites()                                    │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│ CreateAlerts                                            │
├─────────────────────────────────────────────────────────┤
│ - recruiter_parser: JsonOutputParser                    │
│ - prompt_recruiter: PromptTemplate                      │
│ - recruiter_chain: Chain                                │
├─────────────────────────────────────────────────────────┤
│ + render_alerts()                                       │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│ MetaCreation                                            │
├─────────────────────────────────────────────────────────┤
│ - template_df: DataFrame                                │
│ - domain_dict: dict                                     │
│ - job_parser: JsonOutputParser                          │
│ - prompt_job: PromptTemplate                            │
│ - job_chain: Chain                                      │
├─────────────────────────────────────────────────────────┤
│ + get_joblist(data) → list                              │
│ + create_jobtype_prompt(data) → Chain                   │
│ + create_meta(df) → DataFrame                           │
│ + render_upload_page()                                  │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│ SearchJob                                               │
├─────────────────────────────────────────────────────────┤
│ - db: SQLDatabase                                       │
├─────────────────────────────────────────────────────────┤
│ + clean_query(x) → str                                  │
│ + create_sql_chain() → Chain                            │
│ + render_search()                                       │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│ CreateUI                                                │
├─────────────────────────────────────────────────────────┤
│ - tab1: Tab (Search)                                    │
│ - tab2: Tab (Alerts)                                    │
│ - tab3: Tab (Upload)                                    │
├─────────────────────────────────────────────────────────┤
│ + render_ui()                                           │
└─────────────────────────────────────────────────────────┘
```

## LLM Integration

### LangChain Architecture

TalentSearch uses LangChain for structured LLM interactions:

#### 1. Chain Composition

**Job Metadata Chain:**
```python
prompt_job | llm → content → job_parser → structured_output
```

**Recruiter Matching Chain:**
```python
prompt_recruiter | llm → content → recruiter_parser → match_result
```

**SQL Query Chain:**
```python
create_sql_query_chain | clean_query | execute_query → results
```

#### 2. Prompt Engineering

**Structure:**
- System instruction
- Format requirements (JSON schema)
- Context data (domain lists, recruiters)
- User input (job posting)

**Example Flow:**
```
Job Post → Prompt Template → LLM → JSON Response → Pydantic Validation → Structured Data
```

#### 3. Output Parsing

Using Pydantic models for validation:
```python
class JobTemplate(BaseModel):
    company_name: str
    domain: str
    sector: str
    work_arrangement: str
    # ... additional fields
```

### LangSmith Integration

**Tracing Configuration:**
```python
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGCHAIN_PROJECT"] = "Sowmya"
```

**Benefits:**
- Request/response logging
- Performance monitoring
- Error tracking
- Cost analysis

## Database Design

### SQLite Schema

**Table: users**

The system uses a dynamic schema based on `output_columns`:

| Column Name | Type | Description |
|------------|------|-------------|
| job_title | TEXT | Position title |
| description | TEXT | Job description |
| company_name | TEXT | Employer name |
| domain | TEXT | Business domain |
| sector | TEXT | Business sector |
| work_arrangement | TEXT | Work mode (Remote/Hybrid/On-site) |
| location_city | TEXT | City |
| location_country | TEXT | Country |
| location_region | TEXT | Region |
| contract_type | TEXT | Contract type (Permanent/Contract) |
| seniority | TEXT | Seniority level |
| date_posted | TEXT | Posting date |
| salary_low | TEXT | Minimum salary |
| salary_high | TEXT | Maximum salary |
| type_of_job | TEXT | Specific job type |
| recruiter_name | TEXT | Assigned recruiter |
| relevence_score | TEXT | Match score (0-100) |
| justification | TEXT | Matching rationale |
| content | TEXT | Concatenated searchable content |

### Database Operations

**Create/Replace:**
```python
meta_df.to_sql('users', conn, if_exists='replace', index=False)
```

**Query Execution:**
```python
execute_query = QuerySQLDataBaseTool(db=self.db)
```

**Full-Text Search:**
Uses the `content` column which concatenates all fields for comprehensive text search.

## Security Considerations

### API Key Management

**Current Implementation:**
- Uses `.env` file for API keys
- Environment variables loaded via `python-dotenv`

**Recommendations:**
- Never commit `.env` to version control
- Use secret management services for production
- Rotate keys regularly
- Implement key-based access controls

### Data Privacy

**Current State:**
- SQLite database stored locally
- No encryption at rest
- Session state in memory only

**Production Recommendations:**
- Encrypt database files
- Implement user authentication
- Add role-based access control (RBAC)
- Sanitize uploaded data
- Implement audit logging

### Input Validation

**Current Protections:**
- Pydantic model validation
- SQL query cleaning via regex
- File type restrictions (.xlsx, .csv)

**Additional Measures:**
- Add file size limits
- Implement virus scanning for uploads
- Validate SQL queries before execution
- Rate limiting for API calls

### LLM Security

**Risks:**
- Prompt injection attacks
- Data leakage through prompts
- Uncontrolled API costs

**Mitigations:**
- Validate and sanitize user inputs
- Limit token usage per request
- Monitor API usage
- Implement timeout mechanisms

## Scalability Considerations

### Current Limitations

1. **SQLite**: Single-user, file-based database
2. **Sample Size**: Limited to 2 records per upload
3. **Synchronous Processing**: Sequential LLM calls
4. **No Caching**: Repeated API calls for same queries

### Scaling Recommendations

1. **Database Migration**
   - Move to PostgreSQL or MySQL for multi-user support
   - Implement connection pooling
   - Add database indexes for frequent queries

2. **Async Processing**
   - Use async LLM calls for parallel processing
   - Implement job queue (Celery, RQ)
   - Add progress tracking for long operations

3. **Caching Strategy**
   - Cache LLM responses for identical inputs
   - Use Redis for session management
   - Implement query result caching

4. **Load Balancing**
   - Multiple Streamlit instances
   - Reverse proxy (nginx)
   - Session affinity for user sessions

## Error Handling

### Current Strategy

**Try-Except Blocks:**
- Wrapper around UI components
- Database operations
- LLM API calls

**Logging:**
- Error details logged with stack trace
- Timestamped log files
- Structured error messages

### Recovery Mechanisms

1. **Graceful Degradation:**
   - Display warning messages to users
   - Continue operation when possible

2. **State Management:**
   - Clear corrupted session state
   - Reload from database on errors

3. **User Feedback:**
   - Informative error messages
   - Spinner indicators during processing
   - Success confirmations

## Performance Optimization

### Current Implementation

1. **Limited Batch Size**: Process only 2 records
2. **Dataframe Operations**: Efficient pandas operations
3. **SQL Indexing**: Implicit SQLite indexes

### Optimization Opportunities

1. **Batch Processing**: Process multiple records in parallel
2. **Lazy Loading**: Load data on-demand instead of all at once
3. **Query Optimization**: Add explicit indexes on frequently queried columns
4. **Response Caching**: Cache LLM responses for identical inputs
5. **Pagination**: Implement pagination for large result sets

## Future Architecture Enhancements

1. **Microservices Architecture**
   - Separate services for upload, processing, search
   - API gateway for service coordination
   - Independent scaling of components

2. **Event-Driven Design**
   - Pub/sub pattern for job processing
   - Real-time alerts via WebSockets
   - Asynchronous notifications

3. **Vector Search Integration**
   - ChromaDB for semantic similarity
   - Hybrid search (SQL + vector)
   - Improved relevance matching

4. **API Layer**
   - REST API for programmatic access
   - GraphQL for flexible queries
   - Webhook support for integrations

5. **Machine Learning Pipeline**
   - Custom model fine-tuning
   - Automated recruiter matching
   - Continuous learning from feedback
