# Technical Architecture

## System Architecture

### High-Level Architecture

The Taxonomy Skillmatch system follows a layered architecture pattern with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────┐
│                  Presentation Layer                      │
│              (Streamlit Web Interface)                   │
└───────────────────┬─────────────────────────────────────┘
                    │
┌───────────────────┴─────────────────────────────────────┐
│                  Application Layer                       │
│           (ContentClassification Class)                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐  │
│  │ Prompt   │  │   LLM    │  │  Output Processing   │  │
│  │ Manager  │  │ Handler  │  │     & Parsing        │  │
│  └──────────┘  └──────────┘  └──────────────────────┘  │
└───────────────────┬─────────────────────────────────────┘
                    │
┌───────────────────┴─────────────────────────────────────┐
│              Integration Layer                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  LangChain   │  │   OpenAI     │  │   Pydantic   │  │
│  │  Framework   │  │     API      │  │  Validators  │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└───────────────────┬─────────────────────────────────────┘
                    │
┌───────────────────┴─────────────────────────────────────┐
│               Infrastructure Layer                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐  │
│  │ Config   │  │ Logging  │  │  Environment Vars    │  │
│  │ Manager  │  │ System   │  │     (.env)           │  │
│  └──────────┘  └──────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Component Architecture

### 1. Data Models (Pydantic)

#### TaxonomyOutputModel
**Purpose**: Defines the schema for individual taxonomy classification results

```python
class TaxonomyOutputModel(BaseModel):
    industry: str      # Level 1 - Industry classification
    domain: str        # Level 2 - Domain within industry
    group: str         # Level 3 - Occupation group
    sub_group: str     # Level 4 - Specific job role
    scores: float      # Relevancy percentage score
```

**Key Features**:
- Field-level descriptions for LLM guidance
- Type validation and coercion
- JSON serialization support

#### TaxonomyOutputParser
**Purpose**: Container for multiple taxonomy results

```python
class TaxonomyOutputParser(BaseModel):
    results: List[TaxonomyOutputModel]
```

**Key Features**:
- Validates list of results
- Ensures consistent structure
- Supports JSON parsing

### 2. Core Application Class

#### ContentClassification

**Responsibilities**:
1. LLM initialization and management
2. Prompt template creation and formatting
3. Chain orchestration (Prompt → LLM → Parser)
4. Response processing and transformation
5. Error handling and logging

**Class Diagram**:
```
ContentClassification
├── __init__()
│   ├── load_dotenv()
│   ├── initialize LLM (GPT-4o-mini)
│   ├── define prompt_template
│   └── create output_parser
│
├── get_prompt() → PromptTemplate
│   └── combines format instructions with template
│
├── get_response(content, taxonomy) → dict
│   ├── creates chain (prompt | llm | parser)
│   └── invokes chain with inputs
│
├── to_dataframe(response) → pd.DataFrame
│   └── transforms JSON to DataFrame
│
└── get_taxonomy_data(content, taxonomy) → pd.DataFrame
    ├── calls get_response()
    ├── calls to_dataframe()
    ├── sorts by score
    └── handles exceptions
```

### 3. LLM Integration Architecture

#### LangChain Integration Flow

```
Input Data
    │
    ▼
┌──────────────────┐
│ PromptTemplate   │ ← Format instructions from JsonOutputParser
│                  │ ← Input variables: {text, taxonomy}
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ GPT-4o-mini LLM  │ ← Temperature: 0 (deterministic)
│                  │ ← Provider: OpenAI
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ JsonOutputParser │ ← Pydantic schema validation
│                  │ ← Auto-format JSON structure
└────────┬─────────┘
         │
         ▼
    Parsed Output
```

**Chain Configuration**:
- **Type**: Sequential Chain (LCEL syntax: `|` operator)
- **Components**:
  1. PromptTemplate with dynamic variables
  2. ChatModel (GPT-4o-mini)
  3. JsonOutputParser with Pydantic schema

**LLM Parameters**:
```python
{
    "model": "gpt-4o-mini",
    "provider": "openai",
    "temperature": 0,        # Deterministic output
    "api_key": <from_env>    # Secure credential management
}
```

### 4. Configuration Management

#### Hydra-Based Configuration

**Structure**:
```yaml
taxonomy:
  taxonomy_log_file: "log.txt"
```

**Configuration Loader** (config.py):
```python
get_config_object(config_path=".", config_name="config.yaml")
```

**Features**:
- Version-based configuration (Hydra)
- File existence validation
- Type-safe access through dot notation
- Centralized configuration management

### 5. Logging System

#### Logging Architecture

**Components**:
- **log.py**: Logging utility module
- **log.txt**: Log file (configured via config.yaml)
- **Log Writer Function**: Structured logging with timestamps

**Log Entry Format**:
```
YYYY-MM-DD HH:MM:SS" <LOG_TYPE>: <message> "
```

**Log Types**:
- `INFO`: Informational messages
- `ERROR`: Error conditions with traceback details

**Error Logging Pattern**:
```python
exc_type, exc_obj, exc_tb = sys.exc_info()
error = f"{exc_type} | {exc_obj} | line {exc_tb.tb_lineno} | {exc_tb.tb_frame.f_code.co_filename}"
log.log_writer(error, "ERROR")
```

### 6. Streamlit Application Architecture

#### Application Flow

```
┌──────────────────┐
│   Page Config    │
│  (Wide Layout)   │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Session State   │
│  Initialization  │ ← st.session_state['data']
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   File Upload    │
│      Form        │
│  ┌────────────┐  │
│  │ CV (TXT)   │  │
│  │ Tax (JSON) │  │
│  │  [Submit]  │  │
│  └────────────┘  │
└────────┬─────────┘
         │
         ▼ (on submit)
┌──────────────────┐
│  File Reading    │
│  & Decoding      │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   Processing     │
│  (with spinner)  │ ← classifier.get_taxonomy_data()
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Results Display │
│  ┌────────────┐  │
│  │ Download   │  │
│  │ Top Match  │  │
│  │ DataFrame  │  │
│  └────────────┘  │
└──────────────────┘
```

#### Session State Management

**Purpose**: Persist data across Streamlit reruns

```python
if "data" not in st.session_state:
    st.session_state['data'] = pd.DataFrame()
```

**Usage**:
- Stores processing results
- Enables download functionality
- Maintains state during page interaction

### 7. Data Flow Architecture

#### End-to-End Data Pipeline

```
┌─────────────────┐
│  Resume (TXT)   │
└────────┬────────┘
         │ decode('utf-8')
         ▼
┌─────────────────┐    ┌──────────────────┐
│  Text Content   │    │  Taxonomy (JSON) │
└────────┬────────┘    └────────┬─────────┘
         │                      │
         └──────────┬───────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │   Prompt Template    │
         │   (with variables)   │
         └──────────┬───────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │    LLM Processing    │
         │    (GPT-4o-mini)     │
         └──────────┬───────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │   JSON Response      │
         │   {results: [...]}   │
         └──────────┬───────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │ Pydantic Validation  │
         │ & Parsing            │
         └──────────┬───────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │  Python Dictionary   │
         └──────────┬───────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │  DataFrame Creation  │
         │  (List Comprehension)│
         └──────────┬───────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │  Sorted DataFrame    │
         │  (by score)          │
         └──────────┬───────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │   Display & Export   │
         │   (CSV Download)     │
         └──────────────────────┘
```

## Prompt Engineering Architecture

### Prompt Template Structure

**Components**:

1. **System Instructions**:
   - Defines input format (text and taxonomy)
   - Explains taxonomy hierarchy
   - Specifies task objectives

2. **Task Definition**:
   - Compare skills from bio-data
   - Classify against job roles
   - Calculate relevancy scores
   - Return top 5 results

3. **Output Format Specification**:
   - JSON structure definition
   - Required keys enumeration
   - Example taxonomy paths

4. **Dynamic Variables**:
   - `{text}`: Resume content
   - `{taxonomy}`: Taxonomy structure
   - `{format_instruction}`: Auto-generated from parser

### Prompt Injection Points

```python
PromptTemplate(
    template="{format_instruction}\n\n\n" + self.prompt_template,
    input_variables=["text", "taxonomy"],
    partial_variables={
        "format_instruction": self.output_parser.get_format_instructions()
    }
)
```

**Key Design Decisions**:
- Format instructions prepended automatically
- Clear delimiters (triple quotes) for inputs
- Examples provided for context
- Temperature set to 0 for consistency

## Error Handling Architecture

### Exception Handling Strategy

**Levels**:

1. **Application Level** (get_taxonomy_data):
   ```python
   try:
       # Processing logic
   except Exception as e:
       # Detailed error logging
       # System exit with user message
   ```

2. **UI Level** (Streamlit):
   ```python
   try:
       # Display logic
   except Exception as e:
       # Error logging
       # User-friendly warning
   ```

**Error Information Captured**:
- Exception type
- Exception object/message
- Line number
- Source file name
- Timestamp

### Defensive Programming

**Safeguards**:
1. Config file existence check
2. Session state initialization
3. DataFrame length validation
4. File upload validation (type checking)

## Performance Considerations

### Optimization Strategies

1. **Temperature Setting**:
   - Set to 0 for deterministic, faster responses

2. **Model Selection**:
   - GPT-4o-mini for cost-efficiency and speed

3. **Caching**:
   - Session state prevents reprocessing

4. **Lazy Loading**:
   - LLM initialized once in constructor

### Bottlenecks

1. **API Latency**: OpenAI API round-trip time
2. **Resume Length**: Longer resumes = longer processing
3. **Taxonomy Size**: Larger taxonomies = more tokens
4. **Network Speed**: Internet connection dependency

## Security Architecture

### Security Measures

1. **API Key Management**:
   - Stored in `.env` file
   - Never hardcoded
   - Loaded via python-dotenv

2. **Input Validation**:
   - Pydantic schema validation
   - File type restrictions
   - JSON structure validation

3. **Error Message Sanitization**:
   - No sensitive data in logs
   - Generic user-facing messages

4. **Session Isolation**:
   - Streamlit session state per user
   - No cross-session data leakage

### Security Limitations

1. **No Authentication**: Open access to application
2. **No Encryption**: Data transmitted in plain text to API
3. **No Rate Limiting**: Potential for abuse
4. **No Input Sanitization**: Accepts any text content

## Scalability Considerations

### Current Limitations

1. **Single-threaded**: One request at a time
2. **In-memory Storage**: Session-based only
3. **No Queue System**: No async processing
4. **Stateless**: No historical data retention

### Potential Scaling Strategies

1. **Horizontal Scaling**:
   - Deploy multiple Streamlit instances
   - Load balancer distribution

2. **Async Processing**:
   - Background job queues (Celery, RQ)
   - Webhook-based results delivery

3. **Caching Layer**:
   - Redis for taxonomy data
   - Result caching for identical resumes

4. **Database Integration**:
   - Persistent storage of results
   - Batch processing capabilities

## Technology Decisions & Rationale

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| LLM Framework | LangChain | Standardized chains, prompt management, output parsing |
| LLM Provider | OpenAI (GPT-4o-mini) | Cost-effective, high quality, fast inference |
| Web Framework | Streamlit | Rapid prototyping, minimal code, built-in components |
| Data Validation | Pydantic | Type safety, automatic parsing, JSON schema support |
| Configuration | Hydra | YAML-based, type-safe, modular config management |
| Data Processing | Pandas | DataFrame operations, CSV export, data manipulation |
| Environment Mgmt | python-dotenv | Standard practice, secure credential handling |

## Dependencies Graph

```
taxonomy.py
    ├── langchain (init_chat_model)
    ├── langchain-core (PromptTemplate, JsonOutputParser)
    ├── langchain-openai (implicit via init_chat_model)
    ├── pydantic (BaseModel, Field)
    ├── streamlit (UI components)
    ├── pandas (DataFrame)
    ├── python-dotenv (load_dotenv, find_dotenv)
    ├── config.py
    │   └── hydra (initialize, compose)
    └── log.py
        └── config.py
```

## Design Patterns

### Patterns Used

1. **Singleton-like Initialization**:
   - LLM initialized once per instance

2. **Template Method**:
   - `get_taxonomy_data` orchestrates the flow

3. **Strategy Pattern**:
   - Swappable output parsers (JsonOutputParser)

4. **Chain of Responsibility**:
   - LangChain's pipe operator

5. **Data Transfer Object**:
   - Pydantic models for structured data

## Code Quality Measures

1. **Type Hints**: Used throughout for clarity
2. **Docstrings**: Comprehensive documentation
3. **Error Handling**: Try-except blocks with logging
4. **Separation of Concerns**: Modular file structure
5. **Configuration Externalization**: YAML-based config
6. **Dependency Injection**: Environment-based API keys

---

**Last Updated**: December 2025
