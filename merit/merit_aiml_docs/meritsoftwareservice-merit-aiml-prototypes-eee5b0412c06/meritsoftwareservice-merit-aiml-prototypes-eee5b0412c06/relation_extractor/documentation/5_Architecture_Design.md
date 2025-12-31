# Relation Extractor Prototype - Architecture & Design

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Design Principles](#design-principles)
3. [Component Architecture](#component-architecture)
4. [Data Flow](#data-flow)
5. [Technology Stack Deep Dive](#technology-stack-deep-dive)
6. [Design Patterns](#design-patterns)
7. [Security Architecture](#security-architecture)
8. [Scalability Considerations](#scalability-considerations)
9. [Performance Architecture](#performance-architecture)
10. [Future Architecture Enhancements](#future-architecture-enhancements)

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        User Interface                        │
│                      (Streamlit Web App)                     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │   App.py    │  │  Config      │  │  Output Schema   │  │
│  │ (Main Logic)│◄─┤  Loader      │  │  & Templates     │  │
│  └─────────────┘  └──────────────┘  └──────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   LangChain Framework                        │
│  ┌────────────┐  ┌─────────────┐  ┌────────────────────┐  │
│  │  Prompt    │→ │  LLM Chain  │→ │  Output Parser     │  │
│  │  Template  │  │             │  │  (Pydantic-based)  │  │
│  └────────────┘  └─────────────┘  └────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   External Services                          │
│  ┌────────────────┐              ┌─────────────────────┐   │
│  │  OpenAI API    │              │   LangSmith         │   │
│  │  (GPT-4o-mini) │              │   (Monitoring)      │   │
│  └────────────────┘              └─────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Supporting Systems                        │
│  ┌────────────────┐              ┌─────────────────────┐   │
│  │  Logging       │              │   Configuration     │   │
│  │  System        │              │   Management        │   │
│  └────────────────┘              └─────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Architecture Layers

#### 1. Presentation Layer (Streamlit)
- **Responsibility**: User interface and interaction
- **Components**: Text input, submit button, output display
- **Technology**: Streamlit framework

#### 2. Application Layer
- **Responsibility**: Business logic and orchestration
- **Components**: App class, configuration management, schema definitions
- **Technology**: Python, Pydantic, LangChain

#### 3. Integration Layer
- **Responsibility**: LLM interaction and output parsing
- **Components**: LangChain prompt chains, output parsers
- **Technology**: LangChain framework

#### 4. External Services Layer
- **Responsibility**: AI model inference and monitoring
- **Components**: OpenAI API, LangSmith
- **Technology**: REST APIs, cloud services

#### 5. Support Layer
- **Responsibility**: Logging, configuration, error handling
- **Components**: Custom logger, config reader
- **Technology**: Python logging, YAML

## Design Principles

### 1. Separation of Concerns

The application follows clear separation of concerns:

```python
# Configuration - Isolated in utils/config_reader.py
class ConfigLoader:
    """Handles all configuration loading"""

# Logging - Isolated in utils/log_writer.py
class CustomLogger:
    """Handles all logging operations"""

# Schema - Isolated in utils/output_schema.py
class OutputTemplate:
    """Handles schema and prompt definitions"""

# Application - Orchestrates all components
class App(ConfigLoader, OutputTemplate):
    """Main application logic"""
```

**Benefits:**
- Easy to maintain and test individual components
- Changes to one component don't affect others
- Clear responsibility boundaries

### 2. Inheritance-Based Composition

Uses Python's multiple inheritance for component integration:

```python
class App(ConfigLoader, OutputTemplate):
    def __init__(self):
        super().__init__()  # Initialize ConfigLoader
        OutputTemplate.__init__(self)  # Initialize OutputTemplate
```

**Benefits:**
- Reusable components
- Clean integration of functionality
- Single point of initialization

### 3. Configuration-Driven Design

All configurable parameters are externalized to `config.yaml`:

```yaml
llm_details:
  llm_model: "gpt-4o-mini"
  model_provider: "openai"
  temperature: 0
```

**Benefits:**
- No code changes for configuration updates
- Easy environment-specific configurations
- Clear visibility of all settings

### 4. Schema-First Approach

Output structure is defined using Pydantic models before implementation:

```python
class FieldRelations(BaseModel):
    source: str = Field(description="source of the relation")
    relation: str = Field(description="relation between source and target")
    target: str = Field(description="target of the source related")
    score: float = Field(description="a confidence score between 0.0 to 1.0")
```

**Benefits:**
- Type safety and validation
- Auto-generated format instructions for LLM
- Clear data contracts

### 5. Error Handling Strategy

Comprehensive error handling at all levels:

```python
try:
    # Operation
except Exception as e:
    exc_type, exc_obj, exc_tb = sys.exc_info()
    msg = exc_obj.args[0]
    self.write_error_log(exc_type, exc_tb, msg)
```

**Benefits:**
- Detailed error logging
- Graceful failure handling
- Debugging information preservation

## Component Architecture

### Component Diagram

```
┌────────────────────────────────────────────────────────────┐
│                        App Component                        │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  __init__()                                          │  │
│  │  - Load configuration                                │  │
│  │  - Initialize LLM                                    │  │
│  │  - Set up Streamlit                                  │  │
│  │  - Configure logging                                 │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  render_app()                                        │  │
│  │  - Create UI form                                    │  │
│  │  - Handle user input                                 │  │
│  │  - Invoke LLM chain                                  │  │
│  │  - Parse and display results                         │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                              │
│  Uses:                                                      │
│  ├─ ConfigLoader (inherited)                               │
│  ├─ OutputTemplate (inherited)                             │
│  ├─ Streamlit (composition)                                │
│  └─ LangChain (composition)                                │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│                   ConfigLoader Component                    │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  __init__()                                          │  │
│  │  - Initialize logger                                 │  │
│  │  - Load environment variables                        │  │
│  │  - Read configuration file                           │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  read_config()                                       │  │
│  │  - Validate config file exists                       │  │
│  │  - Parse YAML                                        │  │
│  │  - Return configuration dict                         │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                              │
│  Uses:                                                      │
│  ├─ CustomLogger (inherited)                               │
│  ├─ python-dotenv                                          │
│  └─ PyYAML                                                 │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│                  CustomLogger Component                     │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  setup_logger()                                      │  │
│  │  - Configure logging                                 │  │
│  │  - Create log directories                            │  │
│  │  - Set up log formatting                             │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  write_error_log()                                   │  │
│  │  - Extract error details                             │  │
│  │  - Format error message                              │  │
│  │  - Write to log file                                 │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                              │
│  Uses:                                                      │
│  └─ Python logging module                                  │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│                 OutputTemplate Component                    │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  Pydantic Models:                                    │  │
│  │  ├─ FieldRelations                                   │  │
│  │  ├─ Relations                                        │  │
│  │  └─ FinalRelation                                    │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  __init__()                                          │  │
│  │  - Define prompt template                            │  │
│  │  - Initialize JSON parser                            │  │
│  │  - Create prompt with format instructions            │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                              │
│  Uses:                                                      │
│  ├─ Pydantic                                               │
│  ├─ LangChain JsonOutputParser                            │
│  └─ LangChain PromptTemplate                              │
└────────────────────────────────────────────────────────────┘
```

### Component Interactions

```
User Input
    │
    ▼
┌───────────────┐
│  Streamlit UI │
└───────┬───────┘
        │ text input
        ▼
┌───────────────┐
│   App.py      │
└───────┬───────┘
        │ invokes
        ▼
┌───────────────────┐
│  LangChain Chain  │
│  (prompt | llm)   │
└───────┬───────────┘
        │ sends to
        ▼
┌───────────────┐         ┌──────────────┐
│  OpenAI API   │────────►│  LangSmith   │
└───────┬───────┘  logs   └──────────────┘
        │ returns
        ▼
┌───────────────────┐
│  Output Parser    │
│  (Pydantic-based) │
└───────┬───────────┘
        │ structured data
        ▼
┌───────────────┐
│  Streamlit UI │
│  (display)    │
└───────────────┘
```

## Data Flow

### End-to-End Data Flow

```
1. User Input Phase
   ┌─────────────────────────────────────┐
   │ User enters text in Streamlit form  │
   └──────────────┬──────────────────────┘
                  │ Raw text string
                  ▼

2. Prompt Construction Phase
   ┌─────────────────────────────────────┐
   │ PromptTemplate formats input        │
   │ - Adds format instructions          │
   │ - Inserts user text                 │
   │ - Adds task description             │
   └──────────────┬──────────────────────┘
                  │ Formatted prompt
                  ▼

3. LLM Invocation Phase
   ┌─────────────────────────────────────┐
   │ LangChain chain executes:           │
   │ - Sends prompt to OpenAI            │
   │ - Logs to LangSmith                 │
   │ - Waits for response                │
   └──────────────┬──────────────────────┘
                  │ LLM response (JSON string)
                  ▼

4. Parsing Phase
   ┌─────────────────────────────────────┐
   │ JsonOutputParser processes:         │
   │ - Validates against Pydantic schema │
   │ - Converts to Python objects        │
   │ - Handles validation errors         │
   └──────────────┬──────────────────────┘
                  │ Structured Python dict
                  ▼

5. Display Phase
   ┌─────────────────────────────────────┐
   │ Streamlit renders:                  │
   │ - Displays "Extracted Output"       │
   │ - Shows formatted JSON              │
   │ - Or shows error message            │
   └─────────────────────────────────────┘
```

### Data Transformation Flow

```
Input Text (String)
    "John works at Microsoft in Seattle."
    │
    ▼
Prompt (String)
    """
    {format_instructions}

    You are an expert at understanding how LLMs uncover relationships...

    Content: John works at Microsoft in Seattle.
    """
    │
    ▼
LLM Response (String)
    """
    {
      "relationships": [
        {
          "employment": {
            "type": "professional",
            "nature": "work_relationship",
            "relationships": [
              {
                "job": {
                  "source": "John",
                  "relation": "works at",
                  "target": "Microsoft",
                  "score": 0.95
                }
              }
            ]
          }
        }
      ]
    }
    """
    │
    ▼
Parsed Object (Python Dict)
    {
      "relationships": [
        {
          "employment": Relations(
            type="professional",
            nature="work_relationship",
            relationships=[
              {
                "job": FieldRelations(
                  source="John",
                  relation="works at",
                  target="Microsoft",
                  score=0.95
                )
              }
            ]
          )
        }
      ]
    }
    │
    ▼
Displayed Output (Streamlit)
    Formatted JSON display in web interface
```

### Error Flow

```
Exception Occurs
    │
    ▼
sys.exc_info() Called
    │
    ├─ exc_type
    ├─ exc_obj
    └─ exc_tb
    │
    ▼
write_error_log() Called
    │
    ├─ Extract filename from traceback
    ├─ Extract line number
    └─ Format error message
    │
    ▼
Logger.error() Called
    │
    ▼
Log File Written
    logs/DD-MM-YY/HH.log
    │
    ▼
User Notification
    Streamlit warning or system exit
```

## Technology Stack Deep Dive

### Frontend Technology

#### Streamlit
- **Version**: 1.28.0+
- **Purpose**: Web interface framework
- **Key Features Used**:
  - `st.set_page_config()`: Page layout configuration
  - `st.title()`: Main heading
  - `st.form()`: Form container
  - `st.text_area()`: Text input
  - `st.form_submit_button()`: Submit button
  - `st.spinner()`: Loading indicator
  - `st.write()`: Output display
  - `st.warning()`: Error messages

**Architecture Pattern**: Component-based UI rendering

### Backend Technology

#### LangChain Framework
- **Version**: 0.1.0+
- **Purpose**: LLM application framework
- **Components Used**:
  - `init_chat_model()`: LLM initialization
  - `PromptTemplate`: Prompt management
  - `JsonOutputParser`: Output parsing
  - LCEL (LangChain Expression Language): Chain composition

**Architecture Pattern**: Chain-based composition using `|` operator

```python
chain = prompt | llm | parser
```

#### Pydantic
- **Version**: 2.5.0+
- **Purpose**: Data validation and schema definition
- **Features Used**:
  - `BaseModel`: Schema base class
  - `Field`: Field-level metadata
  - Type hints: Type validation
  - Nested models: Hierarchical structures

**Architecture Pattern**: Schema-first validation

### External Services

#### OpenAI API
- **Model**: GPT-4o-mini
- **Usage**: Relationship extraction inference
- **Integration**: Via LangChain's `init_chat_model()`
- **Configuration**: API key via environment variables

**Communication Pattern**: REST API over HTTPS

#### LangSmith
- **Purpose**: LLM application monitoring and debugging
- **Features Used**:
  - Request/response logging
  - Token usage tracking
  - Performance monitoring
  - Error tracking

**Integration Pattern**: Automatic via LangChain environment variables

### Support Libraries

#### python-dotenv
- **Purpose**: Environment variable management
- **Usage**: Load `.env` file into `os.environ`

#### PyYAML
- **Purpose**: YAML configuration parsing
- **Usage**: Parse `config.yaml` into Python dict

#### Python Logging
- **Purpose**: Application logging
- **Features Used**:
  - File-based logging
  - Log level configuration
  - Custom formatters

## Design Patterns

### 1. Template Method Pattern

**Location**: `OutputTemplate` class

```python
class OutputTemplate:
    def __init__(self):
        # Template for prompt construction
        prompt_template = """..."""
        self.prompt = PromptTemplate(
            template="{format_instructions}\n\n" + prompt_template + "\n\nContent: {content}",
            ...
        )
```

**Purpose**: Define skeleton of prompt structure with customizable content

### 2. Chain of Responsibility Pattern

**Location**: LangChain pipeline

```python
self.chat = self.prompt | self.llm
```

**Purpose**: Pass request through a chain of processing steps:
1. Prompt formatting
2. LLM inference
3. Output parsing (implicit)

### 3. Strategy Pattern

**Location**: LLM model selection

```python
self.llm = init_chat_model(
    model=self.config_data['llm_details']['llm_model'],
    model_provider=self.config_data['llm_details']['model_provider'],
    ...
)
```

**Purpose**: Allow runtime selection of LLM provider and model

### 4. Singleton Pattern

**Location**: Configuration loading

```python
class ConfigLoader:
    def __init__(self):
        self.config_data = self.read_config()  # Loaded once
```

**Purpose**: Ensure configuration is loaded once and reused

### 5. Facade Pattern

**Location**: `App` class

```python
class App(ConfigLoader, OutputTemplate):
    # Provides simple interface hiding complex subsystems
```

**Purpose**: Simplify interface to complex subsystems (LangChain, Streamlit, logging)

### 6. Factory Pattern

**Location**: LLM initialization

```python
init_chat_model(
    model=model_name,
    model_provider=provider
)
```

**Purpose**: Create LLM instances without specifying exact class

## Security Architecture

### 1. API Key Management

**Security Measures**:
- Keys stored in `.env` file (not in code)
- `.env` excluded from version control
- Environment variables loaded at runtime
- No key logging or display

**Best Practice Implementation**:
```python
load_dotenv()  # Loads from .env
# OPENAI_API_KEY now in os.environ
```

### 2. Input Validation

**Current State**: Limited input validation

**Recommendations**:
- Sanitize user input
- Implement length limits
- Validate character encoding
- Check for malicious patterns

### 3. Error Message Security

**Current State**: Generic error messages to users

**Implementation**:
```python
try:
    # Processing
except:
    st.warning("Please try again...")  # Generic message
    # Detailed logging in files only
```

**Purpose**: Prevent information disclosure to users

### 4. Logging Security

**Security Measures**:
- Logs stored locally
- No sensitive data logged
- Log files not accessible via web interface

**Log Directory Structure**:
```
logs/
└── DD-MM-YY/
    └── HH.log  # Not web-accessible
```

### 5. Transport Security

**Current State**: Relies on external service HTTPS

**Communication**:
- OpenAI API: HTTPS enforced
- LangSmith: HTTPS enforced
- Streamlit: HTTP (local development)

**Production Recommendation**: Deploy behind HTTPS proxy

## Scalability Considerations

### Current Architecture Limitations

1. **Single-threaded Processing**: One request at a time
2. **Synchronous Operations**: Blocking I/O for API calls
3. **No Caching**: Repeated queries re-processed
4. **In-memory State**: Limited to single instance
5. **No Load Balancing**: Single application instance

### Scalability Enhancement Options

#### 1. Horizontal Scaling

**Current State**: Single instance

**Enhancement**:
```
┌─────────────┐
│ Load        │
│ Balancer    │
└──────┬──────┘
       │
       ├──────► App Instance 1
       ├──────► App Instance 2
       └──────► App Instance N
```

**Implementation**: Deploy multiple Streamlit instances behind load balancer

#### 2. Caching Layer

**Current State**: No caching

**Enhancement**:
```python
import hashlib
from functools import lru_cache

@lru_cache(maxsize=100)
def extract_relations(text_hash):
    # Extract relationships
    pass

# Usage
text_hash = hashlib.sha256(text.encode()).hexdigest()
result = extract_relations(text_hash)
```

**Benefits**:
- Reduce API calls
- Faster response times
- Lower costs

#### 3. Asynchronous Processing

**Current State**: Synchronous

**Enhancement**:
```python
import asyncio
from langchain.chat_models import init_chat_model

async def async_extract(text):
    # Async LLM call
    response = await async_llm.ainvoke({"content": text})
    return response
```

**Benefits**:
- Better resource utilization
- Handle concurrent requests
- Improved throughput

#### 4. Message Queue Integration

**Current State**: Direct processing

**Enhancement**:
```
User Request → Queue → Worker Pool → Response Queue → User
```

**Technologies**: Redis Queue, Celery, RabbitMQ

**Benefits**:
- Decouple request handling
- Enable batch processing
- Improve fault tolerance

## Performance Architecture

### Performance Characteristics

#### Current Performance Metrics

**Typical Response Time**:
- Prompt construction: <10ms
- LLM API call: 2-10 seconds
- Parsing: <50ms
- Total: 2-10 seconds (dominated by LLM)

**Bottlenecks**:
1. **LLM API Latency**: External network call
2. **Token Processing**: Based on input/output length
3. **Parsing Complexity**: Depends on output size

### Performance Optimization Strategies

#### 1. Prompt Optimization

```python
# Concise prompt = fewer tokens = faster response
prompt_template = """
Extract relationships as JSON.
Format: {format_instructions}
Text: {content}
"""
```

#### 2. Model Selection

```yaml
# Faster model for less complex tasks
llm_details:
  llm_model: "gpt-3.5-turbo"  # Faster than gpt-4o-mini
  temperature: 0
```

#### 3. Streaming Responses

**Future Enhancement**:
```python
# Stream tokens as they arrive
for chunk in llm.stream(prompt):
    st.write(chunk)
```

#### 4. Connection Pooling

**Current**: New connection per request

**Enhancement**: Reuse HTTP connections to OpenAI

## Future Architecture Enhancements

### 1. Microservices Architecture

**Vision**:
```
┌─────────────────┐
│   API Gateway   │
└────────┬────────┘
         │
         ├──────► Extraction Service
         ├──────► Validation Service
         ├──────► Storage Service
         └──────► Analytics Service
```

### 2. Event-Driven Architecture

**Vision**:
```
User Input → Event Bus → Processors → Result Store → Notification
```

**Benefits**:
- Loose coupling
- Better scalability
- Async processing

### 3. Multi-Model Support

**Vision**:
```python
# Support multiple LLM providers
providers = {
    "openai": GPT4oMini,
    "anthropic": Claude,
    "cohere": Command,
}

# Dynamic selection based on task
model = providers[config.provider](config)
```

### 4. Result Storage

**Vision**:
```
┌──────────────┐
│  PostgreSQL  │  ← Store extracted relationships
└──────────────┘

┌──────────────┐
│   Neo4j      │  ← Graph database for relationships
└──────────────┘

┌──────────────┐
│   Redis      │  ← Cache layer
└──────────────┘
```

### 5. Batch Processing Pipeline

**Vision**:
```
Document Upload → Queue → Batch Processor → Result Store → Export
```

**Features**:
- Process multiple documents
- Scheduled processing
- Bulk export

### 6. Monitoring and Observability

**Vision**:
```
Application
    ├─► Prometheus (Metrics)
    ├─► Grafana (Visualization)
    ├─► ELK Stack (Logs)
    └─► Jaeger (Tracing)
```

### 7. API-First Architecture

**Vision**: Expose REST API for integration

```python
@app.post("/extract")
async def extract_relationships(text: str):
    result = await extractor.extract(text)
    return {"relationships": result}
```

### 8. CI/CD Pipeline

**Vision**:
```
Code Commit → Tests → Build → Deploy → Monitor
     │
     ├─► Unit Tests
     ├─► Integration Tests
     ├─► Security Scan
     └─► Performance Tests
```

## Deployment Architecture

### Current Deployment

**Type**: Local development server

**Characteristics**:
- Single machine
- Direct execution
- File-based logging
- No redundancy

### Production Deployment Options

#### Option 1: Cloud Platform (Streamlit Cloud)

```
GitHub Repo → Streamlit Cloud → HTTPS Endpoint
```

**Pros**:
- Simple deployment
- Automatic SSL
- Built-in scaling

**Cons**:
- Limited customization
- Vendor lock-in

#### Option 2: Container Deployment

```
Dockerfile → Docker Image → Container Registry → Kubernetes/ECS
```

**Pros**:
- Portable
- Scalable
- Version control

**Cons**:
- More complex setup
- Infrastructure management

#### Option 3: Serverless

```
API Gateway → Lambda Function → LLM API
```

**Pros**:
- Auto-scaling
- Pay per use
- No server management

**Cons**:
- Cold start latency
- Execution time limits

## Conclusion

The Relation Extractor prototype demonstrates a clean, modular architecture suitable for rapid prototyping and demonstration purposes. The architecture prioritizes:

1. **Simplicity**: Easy to understand and modify
2. **Modularity**: Clear separation of concerns
3. **Configurability**: Externalized settings
4. **Extensibility**: Easy to add new features

For production deployment, consider implementing the suggested enhancements around scalability, performance, security, and monitoring.

---

**Document Version**: 1.0
**Last Updated**: December 2025
