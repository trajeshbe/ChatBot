# TalentPulse - Technical Architecture

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Component Architecture](#component-architecture)
3. [Data Flow Architecture](#data-flow-architecture)
4. [Class Diagrams](#class-diagrams)
5. [Technology Stack Details](#technology-stack-details)
6. [API & Integration Points](#api--integration-points)
7. [Security Architecture](#security-architecture)
8. [Performance & Scalability](#performance--scalability)

---

## Architecture Overview

TalentPulse follows a modular, layered architecture pattern that separates concerns across presentation, business logic, AI processing, and data layers.

### High-Level Architecture

```mermaid
graph TB
    subgraph "Presentation Layer"
        UI[Streamlit Web Interface]
        FORMS[Form Components]
        DISPLAY[Data Display Components]
    end

    subgraph "Application Layer"
        CONTROLLER[ResumeApp Controller]
        CONFIG[Configuration Manager]
        UTILS[Utility Services]
    end

    subgraph "Business Logic Layer"
        JD_PROCESSOR[Job Description Processor]
        RESUME_PROCESSOR[Resume Processor]
        SCORING_ENGINE[Scoring Engine]
        DATA_TRANSFORMER[Data Transformation Service]
    end

    subgraph "AI/ML Layer"
        CHAIN_MANAGER[LangChain Chain Manager]
        JD_CHAIN[Job Parsing Chain]
        SCORE_CHAIN[Scoring Chain]
        PARSER[JSON Output Parsers]
    end

    subgraph "External Services"
        OPENAI[OpenAI API - GPT-4o-mini]
        LANGSMITH[LangSmith Tracing]
    end

    subgraph "Data Processing Layer"
        PDF_EXTRACTOR[PyMuPDF Extractor]
        DATAFRAME_PROC[Pandas Processor]
    end

    subgraph "Infrastructure Layer"
        LOGGER[Custom Logger]
        ERROR_HANDLER[Error Handler]
        LOG_FILES[(Log Files)]
    end

    UI --> CONTROLLER
    FORMS --> CONTROLLER
    CONTROLLER --> CONFIG
    CONTROLLER --> JD_PROCESSOR
    CONTROLLER --> RESUME_PROCESSOR
    CONTROLLER --> SCORING_ENGINE
    CONTROLLER --> DATA_TRANSFORMER

    JD_PROCESSOR --> JD_CHAIN
    RESUME_PROCESSOR --> SCORE_CHAIN
    SCORING_ENGINE --> SCORE_CHAIN

    JD_CHAIN --> CHAIN_MANAGER
    SCORE_CHAIN --> CHAIN_MANAGER
    CHAIN_MANAGER --> PARSER
    CHAIN_MANAGER --> OPENAI
    CHAIN_MANAGER --> LANGSMITH

    RESUME_PROCESSOR --> PDF_EXTRACTOR
    DATA_TRANSFORMER --> DATAFRAME_PROC

    CONTROLLER --> DISPLAY
    UTILS --> LOGGER
    LOGGER --> ERROR_HANDLER
    ERROR_HANDLER --> LOG_FILES
```

---

## Component Architecture

### 1. Application Components

#### ResumeApp (Main Controller)
**File**: `app.py`

**Responsibilities**:
- Application initialization and configuration
- LangChain setup and chain management
- Orchestration of job and resume processing
- UI rendering and user interaction handling

**Key Methods**:
```python
class ResumeApp(Utils, ScoreTemplate):
    def __init__(self)
    def create_chain(self, prompt)
    def get_parsed_output(self, res)
    def reduce_content(self, sort_data)
    def render_ui(self)
```

**Architecture Pattern**: Inherits from multiple base classes (Utils, ScoreTemplate) following the Mixin pattern.

#### Utils (Utility Service)
**File**: `utils.py`

**Responsibilities**:
- Configuration file reading and parsing
- Logging infrastructure setup
- Error handling and logging

**Key Methods**:
```python
class Utils(CustomLogger):
    def __init__(self)
    def read_config(self)
```

#### CustomLogger (Logging Service)
**File**: `utils.py`

**Responsibilities**:
- Centralized logging configuration
- Time-based log file organization
- Error traceback formatting

**Key Methods**:
```python
class CustomLogger:
    def __init__(self)
    def setup_logger(self)
    def write_error_log(self, exc_type, exc_tb, msg)
```

### 2. Data Model Components

#### Job Template
**File**: `templates.py`

**Structure**:
```python
class JobTemplate(BaseModel):
    Job_Title: str
    Job_description: str
    Educational_Qualification: str
    Experience: float
    Programming_Skills: List[str]
    AI_ML_Skills: List[str]
    Other_Skills: List[str]
```

**Purpose**: Defines structured schema for job description parsing.

#### Score Templates
**File**: `templates.py`

Dynamic template creation based on job requirements:

```python
class ScoreTemplate:
    def create_score_template(self, job_dict):
        # Creates dynamic Pydantic models:
        - ExperienceRequired
        - Role
        - EducationQualification
        - AIMLScore
        - ProgrammingScore
        - OtherSkillScore
        - CandidateScore (main model)
```

**Pattern**: Factory pattern for dynamic model generation.

### 3. Prompt Management

**File**: `prompts.py`

**Templates**:
1. **job_prompt**: Extracts and classifies job posting content
2. **score_prompt**: Evaluates resumes against job requirements

**Structure**:
```python
score_prompt = """
    You are an helpful assistant in evaluating and scoring...
    {format_instruction}
    Job Details: {content}
    CV: {cv}
"""
```

---

## Data Flow Architecture

### Complete Data Flow Diagram

```mermaid
flowchart TD
    START([User Uploads Files])

    subgraph "Input Processing"
        JD_UPLOAD[Job Description Upload - TXT]
        RESUME_UPLOAD[Resume Upload - PDF]
        FORM_SUBMIT[Submit Form]
    end

    subgraph "Job Description Processing"
        JD_READ[Read JD Text Content]
        JD_PROMPT[Apply Job Prompt Template]
        JD_LLM[Send to GPT-4o-mini]
        JD_PARSE[Parse JSON Response]
        JD_STRUCT[Structured Job Data]
    end

    subgraph "Dynamic Template Creation"
        TEMPLATE_GEN[Generate Score Template]
        PARSER_CREATE[Create JSON Parser]
        PROMPT_CREATE[Create Score Prompt]
    end

    subgraph "Resume Processing Loop"
        PDF_READ[Extract PDF Text - PyMuPDF]
        COMBINE_INPUT[Combine JD + Resume]
        SCORE_PROMPT[Apply Score Prompt]
        SCORE_LLM[Send to GPT-4o-mini]
        SCORE_PARSE[Parse Score JSON]
        SCORE_STRUCT[Structured Score Data]
    end

    subgraph "Data Transformation"
        COLLECT[Collect All Scores]
        SORT[Sort by Overall Score]
        DF_INDIVIDUAL[Create Individual DataFrames]
        DF_MERGE[Merge Comparison DataFrame]
        DF_SUMMARY[Create Summary DataFrame]
    end

    subgraph "Presentation"
        DISPLAY_SUMMARY[Display Summary Table]
        DISPLAY_COMPARISON[Display Comparison Table]
        DISPLAY_INDIVIDUAL[Display Individual Scores]
    end

    START --> JD_UPLOAD
    START --> RESUME_UPLOAD
    JD_UPLOAD --> FORM_SUBMIT
    RESUME_UPLOAD --> FORM_SUBMIT

    FORM_SUBMIT --> JD_READ
    JD_READ --> JD_PROMPT
    JD_PROMPT --> JD_LLM
    JD_LLM --> JD_PARSE
    JD_PARSE --> JD_STRUCT

    JD_STRUCT --> TEMPLATE_GEN
    TEMPLATE_GEN --> PARSER_CREATE
    TEMPLATE_GEN --> PROMPT_CREATE

    FORM_SUBMIT --> PDF_READ
    PDF_READ --> COMBINE_INPUT
    PARSER_CREATE --> COMBINE_INPUT
    PROMPT_CREATE --> COMBINE_INPUT
    JD_STRUCT --> COMBINE_INPUT

    COMBINE_INPUT --> SCORE_PROMPT
    SCORE_PROMPT --> SCORE_LLM
    SCORE_LLM --> SCORE_PARSE
    SCORE_PARSE --> SCORE_STRUCT

    SCORE_STRUCT --> COLLECT
    COLLECT --> SORT
    SORT --> DF_INDIVIDUAL
    SORT --> DF_MERGE
    SORT --> DF_SUMMARY

    DF_SUMMARY --> DISPLAY_SUMMARY
    DF_MERGE --> DISPLAY_COMPARISON
    DF_INDIVIDUAL --> DISPLAY_INDIVIDUAL

    DISPLAY_INDIVIDUAL --> END([Results Displayed])
    DISPLAY_COMPARISON --> END
    DISPLAY_SUMMARY --> END

    style START fill:#90EE90
    style END fill:#FFB6C1
```

### Detailed Processing Steps

#### Step 1: Job Description Processing
```mermaid
sequenceDiagram
    participant UI as Streamlit UI
    participant App as ResumeApp
    participant Prompt as PromptTemplate
    participant Chain as LangChain
    participant LLM as OpenAI GPT-4o-mini
    participant Parser as JsonOutputParser

    UI->>App: Submit JD Text
    App->>Prompt: Apply job_prompt template
    Prompt-->>App: Formatted prompt with instructions
    App->>Chain: invoke(jd_content)
    Chain->>LLM: API call with prompt
    LLM-->>Chain: Raw JSON response
    Chain-->>Parser: Parse response
    Parser-->>App: JobTemplate object
    App->>App: Store structured job data
```

#### Step 2: Resume Processing
```mermaid
sequenceDiagram
    participant UI as Streamlit UI
    participant App as ResumeApp
    participant PDF as PyMuPDF
    participant Template as ScoreTemplate
    participant Chain as LangChain
    participant LLM as OpenAI GPT-4o-mini
    participant Parser as JsonOutputParser

    UI->>App: Upload PDF Resume
    App->>PDF: fitz.open(stream=pdf_bytes)
    PDF-->>App: Extracted text content

    App->>Template: create_score_template(job_dict)
    Template-->>App: resume_parser, prompt_score

    loop For each resume
        App->>Chain: invoke(jd_content, cv_text)
        Chain->>LLM: API call with combined prompt
        LLM-->>Chain: Score JSON response
        Chain-->>Parser: Parse score data
        Parser-->>App: CandidateScore object
        App->>App: Append to results list
    end
```

#### Step 3: Data Transformation
```mermaid
flowchart LR
    subgraph "Input"
        SCORES[List of Score Dicts]
    end

    subgraph "Transformation Process"
        EXTRACT[Extract Skill Scores]
        FLATTEN[Flatten Nested Dicts]
        EXPLODE[Explode Lists to Rows]
        RENAME[Rename Columns by Candidate]
    end

    subgraph "Merge Process"
        MERGE[Reduce with pd.merge]
        JOIN_KEYS[On: Specification + Required]
    end

    subgraph "Output"
        DF_INDIV[Individual DataFrames]
        DF_MERGED[Merged Comparison DataFrame]
    end

    SCORES --> EXTRACT
    EXTRACT --> FLATTEN
    FLATTEN --> EXPLODE
    EXPLODE --> RENAME
    RENAME --> DF_INDIV
    DF_INDIV --> MERGE
    JOIN_KEYS --> MERGE
    MERGE --> DF_MERGED
```

---

## Class Diagrams

### Core Class Structure

```mermaid
classDiagram
    class CustomLogger {
        +logger: logging
        +__init__()
        +setup_logger()
        +write_error_log(exc_type, exc_tb, msg)
    }

    class Utils {
        +config: ConfigParser
        +config_data: dict
        +__init__()
        +read_config()
    }

    class ScoreTemplate {
        +create_score_template(job_dict)
        +ExperienceRequired: BaseModel
        +Role: BaseModel
        +EducationQualification: BaseModel
        +AIMLScore: BaseModel
        +ProgrammingScore: BaseModel
        +OtherSkillScore: BaseModel
        +CandidateScore: BaseModel
    }

    class ResumeApp {
        +llm: ChatModel
        +db_path: str
        +job_parser: JsonOutputParser
        +prompt_job: PromptTemplate
        +resume_parser: JsonOutputParser
        +__init__()
        +create_chain(prompt)
        +get_parsed_output(res)
        +reduce_content(sort_data)
        +render_ui()
    }

    class JobTemplate {
        +Job_Title: str
        +Job_description: str
        +Educational_Qualification: str
        +Experience: float
        +Programming_Skills: List[str]
        +AI_ML_Skills: List[str]
        +Other_Skills: List[str]
    }

    CustomLogger <|-- Utils
    Utils <|-- ResumeApp
    ScoreTemplate <|-- ResumeApp
    ResumeApp ..> JobTemplate : uses
```

### Data Model Relationships

```mermaid
classDiagram
    class JobTemplate {
        +Job_Title: str
        +Job_description: str
        +Educational_Qualification: str
        +Experience: float
        +Programming_Skills: List~str~
        +AI_ML_Skills: List~str~
        +Other_Skills: List~str~
    }

    class CandidateScore {
        +Candidate_Name: str
        +Educational_Qualification: Dict
        +Experience: Dict
        +Job_Role: Dict
        +Programming_Skills: Dict
        +AI_ML_Skills: Dict
        +Other_Skills: Dict
        +Resume_Score: float
    }

    class ExperienceRequired {
        +Required: float
        +Score: str
        +Justification: str
    }

    class Role {
        +Required: str
        +Score: str
        +Justification: str
    }

    class EducationQualification {
        +Required: str
        +Score: str
        +Justification: str
    }

    class SkillScore {
        +Score: str
        +Justification: str
    }

    JobTemplate --> CandidateScore : influences structure
    CandidateScore *-- ExperienceRequired
    CandidateScore *-- Role
    CandidateScore *-- EducationQualification
    CandidateScore *-- SkillScore
```

---

## Technology Stack Details

### Core Framework Stack

```mermaid
graph TB
    subgraph "Frontend Layer"
        ST[Streamlit 1.38.0]
    end

    subgraph "LLM Orchestration"
        LC[LangChain 0.3.1]
        LC_CORE[LangChain-Core 0.3.7]
        LC_OPENAI[LangChain-OpenAI 0.2.1]
        LC_COMM[LangChain-Community 0.3.1]
    end

    subgraph "AI/ML Services"
        OPENAI[OpenAI 1.50.2 - GPT-4o-mini]
        LANGSMITH[LangSmith 0.1.129]
        TRANSFORMERS[Transformers 4.45.1]
        HF[HuggingFace Hub 0.25.1]
    end

    subgraph "Data Processing"
        PANDAS[Pandas 2.2.3]
        PYMUPDF[PyMuPDF 1.24.10]
        NUMPY[NumPy via dependencies]
    end

    subgraph "ML Support"
        TORCH[PyTorch 2.4.1]
        SKLEARN[Scikit-Learn 1.5.2]
        SCIPY[SciPy 1.14.1]
        SENT_TRANS[Sentence-Transformers 3.1.1]
    end

    subgraph "Infrastructure"
        DOTENV[Python-Dotenv]
        PYDANTIC[Pydantic via LangChain]
    end

    ST --> LC
    LC --> LC_CORE
    LC --> LC_OPENAI
    LC --> LC_COMM
    LC_OPENAI --> OPENAI
    LC --> LANGSMITH
    LC --> PYDANTIC

    ST --> PANDAS
    ST --> PYMUPDF

    TRANSFORMERS --> TORCH
    TRANSFORMERS --> HF
    SENT_TRANS --> TORCH
    SKLEARN --> SCIPY
```

### Dependency Matrix

| Component | Purpose | Version | Critical Dependencies |
|-----------|---------|---------|----------------------|
| Streamlit | Web UI Framework | 1.38.0 | Tornado, Pandas |
| LangChain | LLM Orchestration | 0.3.1 | Pydantic, AsyncIO |
| OpenAI | LLM Provider | 1.50.2 | HTTPX, Tiktoken |
| PyMuPDF | PDF Processing | 1.24.10 | Native libs |
| Pandas | Data Manipulation | 2.2.3 | NumPy |
| PyTorch | ML Framework | 2.4.1 | CUDA (optional) |
| LangSmith | Monitoring | 0.1.129 | Requests |

---

## API & Integration Points

### External API Integrations

```mermaid
graph LR
    subgraph "TalentPulse System"
        APP[Application Core]
    end

    subgraph "OpenAI Services"
        API_CHAT[Chat Completions API]
        API_EMBED[Embeddings API - Unused]
    end

    subgraph "LangSmith Services"
        LS_TRACE[Tracing API]
        LS_MONITOR[Monitoring Dashboard]
    end

    subgraph "Configuration"
        ENV[.env File]
        CONFIG[config.ini]
    end

    APP -->|API Calls| API_CHAT
    APP -->|Telemetry| LS_TRACE
    LS_TRACE --> LS_MONITOR
    ENV -.->|OPEN_AI_KEY| APP
    ENV -.->|LANGCHAIN_API_KEY| APP
    CONFIG -.->|Settings| APP
```

### API Call Flow

#### OpenAI Chat Completion
```python
# Model Configuration
model: gpt-4o-mini
temperature: 0
provider: openai

# Request Structure
{
    "model": "gpt-4o-mini",
    "messages": [
        {
            "role": "system",
            "content": "<prompt_template>"
        },
        {
            "role": "user",
            "content": "<job_description | resume>"
        }
    ],
    "temperature": 0
}

# Response Structure
{
    "id": "chatcmpl-xxx",
    "object": "chat.completion",
    "created": timestamp,
    "model": "gpt-4o-mini",
    "choices": [{
        "message": {
            "role": "assistant",
            "content": "```json\n{...}\n```"
        }
    }]
}
```

### Configuration Management

```mermaid
flowchart LR
    subgraph "Configuration Sources"
        ENV_FILE[.env File]
        CONFIG_FILE[config.ini]
    end

    subgraph "Environment Variables"
        LANGCHAIN_API[LANGCHAIN_API_KEY]
        OPENAI_API[OPEN_AI_KEY]
    end

    subgraph "Config Parameters"
        TRACING[langchain_tracing_v2]
        ENDPOINT[langchain_endpoint]
        PROJECT[langchain_project]
        MODEL[model]
        PROVIDER[model_provider]
        TEMP[temperature]
    end

    subgraph "Application"
        CONFIG_LOADER[ConfigParser]
        ENV_LOADER[dotenv]
        APP_INIT[Application Init]
    end

    ENV_FILE --> ENV_LOADER
    CONFIG_FILE --> CONFIG_LOADER
    ENV_LOADER --> LANGCHAIN_API
    ENV_LOADER --> OPENAI_API
    CONFIG_LOADER --> TRACING
    CONFIG_LOADER --> ENDPOINT
    CONFIG_LOADER --> PROJECT
    CONFIG_LOADER --> MODEL
    CONFIG_LOADER --> PROVIDER
    CONFIG_LOADER --> TEMP

    LANGCHAIN_API --> APP_INIT
    OPENAI_API --> APP_INIT
    TRACING --> APP_INIT
    ENDPOINT --> APP_INIT
    PROJECT --> APP_INIT
    MODEL --> APP_INIT
    PROVIDER --> APP_INIT
    TEMP --> APP_INIT
```

---

## Security Architecture

### Security Layers

```mermaid
graph TB
    subgraph "Application Security"
        API_KEY[API Key Management]
        ENV_VAR[Environment Variables]
        NO_STORE[No Data Persistence]
    end

    subgraph "Data Security"
        MEMORY[In-Memory Processing]
        TEMP_FILES[Temporary File Handling]
        LOG_SANITIZE[Log Sanitization]
    end

    subgraph "Network Security"
        HTTPS[HTTPS API Calls]
        TLS[TLS 1.2+]
    end

    subgraph "Access Control"
        LOCAL[Local Deployment]
        NO_AUTH[No Built-in Auth]
    end

    API_KEY --> ENV_VAR
    MEMORY --> TEMP_FILES
    HTTPS --> TLS
```

### Security Considerations

#### Current Implementation
- **API Keys**: Stored in `.env` file (not version controlled)
- **Data Handling**: Resumes processed in-memory only
- **Logging**: Error logs may contain stack traces (no PII)
- **Network**: HTTPS for all external API calls

#### Security Recommendations
1. **Authentication**: Implement user authentication for production
2. **Authorization**: Role-based access control
3. **Data Encryption**: Encrypt sensitive data at rest
4. **Audit Logging**: Enhanced logging for compliance
5. **Rate Limiting**: Prevent API abuse
6. **Input Validation**: Enhanced PDF validation
7. **CORS**: Configure for web deployments

---

## Performance & Scalability

### Performance Characteristics

```mermaid
graph LR
    subgraph "Processing Time Factors"
        PDF_SIZE[PDF Size/Pages]
        NUM_RESUMES[Number of Resumes]
        LLM_LATENCY[LLM API Latency]
        TEXT_LENGTH[Text Length]
    end

    subgraph "Bottlenecks"
        API_CALLS[Sequential API Calls]
        PDF_PARSE[PDF Text Extraction]
        JSON_PARSE[JSON Parsing]
    end

    subgraph "Performance Metrics"
        TIME_PER_RESUME[~5-10s per resume]
        CONCURRENT[No Parallelization]
        TOTAL_TIME[Linear Scaling]
    end

    PDF_SIZE --> PDF_PARSE
    NUM_RESUMES --> API_CALLS
    TEXT_LENGTH --> LLM_LATENCY

    PDF_PARSE --> TIME_PER_RESUME
    API_CALLS --> CONCURRENT
    LLM_LATENCY --> TIME_PER_RESUME

    CONCURRENT --> TOTAL_TIME
```

### Performance Profile

| Metric | Current State | Optimization Opportunity |
|--------|---------------|-------------------------|
| Resume Processing | Sequential | Parallel async processing |
| API Calls | Synchronous | Async/await implementation |
| PDF Parsing | Per-file | Batch processing |
| Memory Usage | Low (streaming) | Good as-is |
| CPU Usage | Low | Good as-is |
| Network I/O | High (API calls) | Caching, batching |

### Scalability Architecture

```mermaid
graph TB
    subgraph "Current Architecture"
        direction TB
        SINGLE[Single Process]
        SEQ[Sequential Processing]
        SYNC[Synchronous I/O]
    end

    subgraph "Scalable Architecture"
        direction TB
        MULTI[Multi-Process]
        PARALLEL[Parallel Processing]
        ASYNC[Async I/O]
        QUEUE[Task Queue]
        CACHE[Response Cache]
    end

    subgraph "Production Considerations"
        LB[Load Balancer]
        WORKERS[Worker Pool]
        REDIS[Redis Cache]
        CELERY[Celery Tasks]
    end

    SINGLE -.Upgrade.-> MULTI
    SEQ -.Upgrade.-> PARALLEL
    SYNC -.Upgrade.-> ASYNC

    PARALLEL --> QUEUE
    ASYNC --> CACHE

    MULTI --> WORKERS
    QUEUE --> CELERY
    CACHE --> REDIS
    WORKERS --> LB
```

### Optimization Recommendations

#### Short-term (Prototype Level)
1. **Async Processing**: Convert to async/await for API calls
2. **Concurrent Resumes**: Process multiple resumes in parallel
3. **Response Caching**: Cache job description parsing results
4. **Batch API Calls**: If API supports batching

#### Long-term (Production)
1. **Microservices**: Separate PDF processing, LLM calls, scoring
2. **Message Queue**: RabbitMQ/Redis for job processing
3. **Database**: Store results for analytics
4. **CDN**: For static assets
5. **Horizontal Scaling**: Multiple application instances
6. **Auto-scaling**: Based on queue depth

### Resource Requirements

#### Development Environment
- **CPU**: 2+ cores
- **RAM**: 4GB minimum
- **Storage**: 1GB for dependencies
- **Network**: Stable internet for API calls

#### Production Environment (100 resumes/day)
- **CPU**: 4+ cores
- **RAM**: 8GB minimum
- **Storage**: 10GB (logs, cache)
- **Network**: 10Mbps+, low latency to OpenAI

---

## Error Handling Architecture

```mermaid
flowchart TD
    ERROR[Error Occurs]

    subgraph "Error Detection"
        PYTHON[Python Exception]
        API[API Error]
        VALIDATION[Validation Error]
    end

    subgraph "Error Handling"
        TRY_CATCH[Try-Except Block]
        EXTRACT[Extract Error Details]
        LOG[Log Error]
    end

    subgraph "Error Response"
        USER_MSG[User-Friendly Message]
        LOGGER_CALL[write_error_log]
        FILE_WRITE[Write to Log File]
    end

    subgraph "Recovery"
        GRACEFUL[Graceful Degradation]
        EXIT[System Exit if Critical]
    end

    ERROR --> PYTHON
    ERROR --> API
    ERROR --> VALIDATION

    PYTHON --> TRY_CATCH
    API --> TRY_CATCH
    VALIDATION --> TRY_CATCH

    TRY_CATCH --> EXTRACT
    EXTRACT --> LOG
    LOG --> LOGGER_CALL
    LOGGER_CALL --> FILE_WRITE

    EXTRACT --> USER_MSG
    USER_MSG --> GRACEFUL
    FILE_WRITE --> EXIT
```

### Error Categories

1. **Configuration Errors**: Missing config.ini or .env
2. **API Errors**: OpenAI rate limits, network issues
3. **Parsing Errors**: Invalid JSON from LLM
4. **File Errors**: Corrupted PDFs, unsupported formats
5. **Data Errors**: Missing required fields

---

## Deployment Architecture

### Local Deployment

```mermaid
graph TB
    subgraph "Developer Machine"
        CODE[Source Code]
        VENV[Virtual Environment]
        CONFIG[Config Files]

        subgraph "Running Process"
            STREAMLIT[Streamlit Server :8501]
            APP_PROC[Python Process]
        end
    end

    subgraph "External Services"
        OPENAI_CLOUD[OpenAI API]
        LANGSMITH_CLOUD[LangSmith]
    end

    CODE --> VENV
    CONFIG --> VENV
    VENV --> APP_PROC
    APP_PROC --> STREAMLIT

    STREAMLIT -->|API Calls| OPENAI_CLOUD
    STREAMLIT -->|Telemetry| LANGSMITH_CLOUD
```

### Cloud Deployment Options

```mermaid
graph TB
    subgraph "Deployment Options"
        STREAMLIT_CLOUD[Streamlit Cloud]
        HEROKU[Heroku]
        AWS[AWS EC2/ECS]
        DOCKER[Docker Container]
    end

    subgraph "Considerations"
        COST[Cost]
        SCALE[Scalability]
        MAINT[Maintenance]
        SECURITY[Security]
    end

    STREAMLIT_CLOUD -.-> COST
    STREAMLIT_CLOUD -.-> SCALE
    HEROKU -.-> COST
    AWS -.-> SCALE
    AWS -.-> SECURITY
    DOCKER -.-> MAINT
```

---

## Monitoring & Observability

### Monitoring Stack

```mermaid
graph LR
    subgraph "Application"
        APP[TalentPulse]
    end

    subgraph "Logging"
        CUSTOM_LOG[Custom Logger]
        LOG_FILES[Daily Log Files]
    end

    subgraph "LLM Monitoring"
        LANGSMITH[LangSmith Tracing]
        TRACES[Trace Data]
    end

    subgraph "Metrics"
        PROC_TIME[Processing Time]
        API_CALLS[API Call Count]
        ERRORS[Error Rate]
    end

    APP --> CUSTOM_LOG
    CUSTOM_LOG --> LOG_FILES

    APP --> LANGSMITH
    LANGSMITH --> TRACES

    APP -.-> PROC_TIME
    APP -.-> API_CALLS
    APP -.-> ERRORS
```

### Observable Metrics

1. **Performance Metrics**
   - Time per resume processed
   - Total processing time
   - PDF parsing time
   - API response time

2. **Quality Metrics**
   - JSON parsing success rate
   - Score distribution
   - LLM prompt token usage

3. **System Metrics**
   - Error frequency
   - Log file size
   - Memory usage

---

## Conclusion

TalentPulse's architecture is designed for:
- **Simplicity**: Easy to understand and maintain
- **Modularity**: Clear separation of concerns
- **Extensibility**: Easy to add features
- **Reliability**: Comprehensive error handling
- **Observability**: Detailed logging and tracing

The current architecture serves well as a prototype and can be evolved into a production-grade system with the recommended scalability and security enhancements.
