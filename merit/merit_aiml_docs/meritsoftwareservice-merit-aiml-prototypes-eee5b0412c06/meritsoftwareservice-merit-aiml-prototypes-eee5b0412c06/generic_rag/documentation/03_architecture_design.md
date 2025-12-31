# Generic RAG Prototype - Architecture & Design

## Table of Contents
1. [System Architecture Overview](#system-architecture-overview)
2. [Component Design](#component-design)
3. [Data Flow](#data-flow)
4. [RAG Pipeline](#rag-pipeline)
5. [Class Hierarchy](#class-hierarchy)
6. [Key Design Patterns](#key-design-patterns)
7. [Database Schema](#database-schema)
8. [API Integration](#api-integration)
9. [Performance Considerations](#performance-considerations)

## System Architecture Overview

### Layered Architecture

The Generic RAG prototype follows a three-tier architecture:

```
┌─────────────────────────────────────────────────────────┐
│                  Presentation Layer                      │
│  ┌──────────────────────────────────────────────────┐   │
│  │           Streamlit Web Interface                │   │
│  │  - Upload Tab  - Chat Tab  - Model Selection    │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                          ║
                          ▼
┌─────────────────────────────────────────────────────────┐
│                   Business Logic Layer                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │  GenericRAG  │  │    Utils     │  │CustomLogger  │   │
│  │    Class     │  │    Class     │  │    Class     │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │         LangChain Pipeline Components            │   │
│  │  - DocumentLoader  - TextSplitter               │   │
│  │  - Retriever       - LLM Chain                  │   │
│  │  - Memory          - Compressor                 │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                          ║
                          ▼
┌─────────────────────────────────────────────────────────┐
│                    Data Layer                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │   ChromaDB   │  │  File System │  │    Logs      │   │
│  │ Vector Store │  │   (PDFs)     │  │  (Date-Hour) │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
└─────────────────────────────────────────────────────────┘
                          ║
                          ▼
┌─────────────────────────────────────────────────────────┐
│                  External Services                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ HuggingFace  │  │   Groq API   │  │  LlamaParse  │   │
│  │     API      │  │              │  │     API      │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
└─────────────────────────────────────────────────────────┘
```

## Component Design

### 1. CustomLogger Class

**Purpose**: Centralized logging and error tracking

**Responsibilities**:
- Configure logging with date-based organization
- Create hourly log files
- Format error messages with file and line information
- Provide error logging interface

**Key Methods**:
```python
setup_logger()          # Initialize logging configuration
write_error_log()       # Log exceptions with context
```

**Log Structure**:
```
logs/
├── 20-12-24/          # Day folder (DD-MM-YY)
│   ├── 09.log         # Hour log file
│   ├── 10.log
│   └── 11.log
```

### 2. Utils Class

**Purpose**: Configuration management and utility functions

**Inheritance**: Inherits from CustomLogger

**Responsibilities**:
- Read and parse config.ini file
- Create necessary directories
- Provide configuration data to other components
- Handle configuration errors

**Key Methods**:
```python
read_config()           # Parse config.ini and setup directories
```

**Configuration Flow**:
```
config.ini → ConfigParser → config_data dict → Application
```

### 3. GenericRAG Class

**Purpose**: Main application logic and RAG pipeline orchestration

**Inheritance**: Inherits from Utils (and transitively from CustomLogger)

**Responsibilities**:
- Initialize Streamlit UI
- Manage session state
- Load and cache ML models
- Process document uploads
- Create and manage vector database
- Initialize LLM chains
- Handle user conversations
- Stream responses

**Key Components**:
```python
# Model Management
load_models()           # Cache embedding and reranking models

# Document Processing
load_doc()              # Load and split PDF documents
save_uploaded_file()    # Save uploaded files to disk

# Vector Database
create_db()             # Create ChromaDB from documents
load_db()               # Load existing ChromaDB
clear_collection()      # Clear existing collections

# LLM Chain
initialize_llmchain()   # Create conversational retrieval chain
initialize_LLM()        # Initialize LLM with parameters
init_base_llm()         # Initialize standalone LLM

# Database Initialization
initialize_database()   # End-to-end document indexing

# Conversation
conversation()          # Process queries and generate responses
stream_data()           # Stream responses word-by-word

# UI
render_UI()             # Main UI rendering logic
```

## Data Flow

### Document Upload Flow

```
User uploads PDF
       ↓
save_uploaded_file() → File saved to input/
       ↓
load_doc() → PyMuPDFLoader or LlamaParse
       ↓
RecursiveCharacterTextSplitter → Chunks
       ↓
create_db() → Embeddings generated
       ↓
ChromaDB → Vectors persisted
       ↓
Session state updated
```

### Query Processing Flow

```
User enters query
       ↓
conversation() called with qa_chain
       ↓
Query embedded by embeddings model
       ↓
MMR Retrieval → Top 10 chunks from ChromaDB
       ↓
CrossEncoderReranker → Top 3 chunks
       ↓
ContextualCompressionRetriever → Filtered content
       ↓
ConversationalRetrievalChain → LLM generates answer
       ↓
Response + Source documents
       ↓
stream_data() → Streamed to user
```

### Session State Management

```python
st.session_state = {
    'models': True,                    # Models loaded flag
    'embeddings': SentenceTransformer, # Cached embedding model
    'ranker_model': HuggingFaceCrossEncoder, # Cached reranker
    'fpath': "/path/to/file.pdf",     # Uploaded file path
    'vector_db': ChromaDB,             # Vector database instance
    'vector_status': True,             # Vector DB ready flag
    'qa_chain': ConversationalChain,   # LLM chain instance
    'llm': str,                        # Selected LLM name
    'table': False,                    # Table processing flag
    'messages': [                      # Conversation history
        {
            'role': 'assistant',
            'content': 'How can I help you?',
            'resource': []
        }
    ]
}
```

## RAG Pipeline

### Standard RAG Pipeline (Without Tables)

```
┌─────────────────────────────────────────────────┐
│ 1. Document Loading                             │
│    PyMuPDFLoader → Pages with metadata          │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ 2. Text Splitting                               │
│    RecursiveCharacterTextSplitter               │
│    chunk_size=250, chunk_overlap=0              │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ 3. Embedding Generation                         │
│    SentenceTransformer(all-MiniLM-L6-v2)        │
│    384-dimensional vectors                      │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ 4. Vector Storage                               │
│    ChromaDB persistent storage                  │
│    Collection: 'sample'                         │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ 5. Retrieval                                    │
│    MMR (Maximal Marginal Relevance)             │
│    k=10, lambda_mult=0.25                       │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ 6. Reranking                                    │
│    CrossEncoderReranker (bge-reranker-base)     │
│    top_n=3                                      │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ 7. Contextual Compression                       │
│    Filter irrelevant content                    │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ 8. LLM Generation                               │
│    HuggingFaceEndpoint or ChatGroq              │
│    temperature=0.1, max_tokens=1200             │
└─────────────────────────────────────────────────┘
```

### Enhanced RAG Pipeline (With Tables)

```
┌─────────────────────────────────────────────────┐
│ 1. Document Parsing                             │
│    LlamaParse → Markdown with tables            │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ 2. Parent Document Storage                      │
│    Full pages stored as parent documents        │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ 3. Child Document Splitting                     │
│    RecursiveCharacterTextSplitter               │
│    chunk_size=250, chunk_overlap=100            │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ 4. Dual Storage                                 │
│    ChromaDB: Child chunks (searchable)          │
│    InMemoryStore: Parent docs (retrievable)     │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ 5. ParentDocumentRetriever                      │
│    Search children, return parents              │
│    Preserves table structure                    │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ 6. LLM Generation                               │
│    Full context with intact tables              │
└─────────────────────────────────────────────────┘
```

## Class Hierarchy

```
┌─────────────────────┐
│   CustomLogger      │
│                     │
│ - setup_logger()    │
│ - write_error_log() │
└──────────┬──────────┘
           │
           │ inherits
           ↓
┌─────────────────────┐
│       Utils         │
│                     │
│ - read_config()     │
│ - config_data       │
└──────────┬──────────┘
           │
           │ inherits
           ↓
┌─────────────────────────────────────────┐
│            GenericRAG                   │
│                                         │
│ Document Processing:                    │
│ - load_doc()                           │
│ - save_uploaded_file()                 │
│                                         │
│ Vector DB:                             │
│ - create_db()                          │
│ - load_db()                            │
│ - clear_collection()                   │
│                                         │
│ Model Management:                      │
│ - load_models()                        │
│ - initialize_llmchain()                │
│ - initialize_LLM()                     │
│ - init_base_llm()                      │
│                                         │
│ Conversation:                          │
│ - conversation()                       │
│ - stream_data()                        │
│                                         │
│ Database:                              │
│ - initialize_database()                │
│                                         │
│ UI:                                    │
│ - render_UI()                          │
└─────────────────────────────────────────┘
```

## Key Design Patterns

### 1. Inheritance Pattern
- CustomLogger → Utils → GenericRAG
- Promotes code reuse and separation of concerns
- Each class adds specific functionality

### 2. Singleton Pattern (via Streamlit Caching)
```python
@st.cache_resource
def load_models(_self, embedder, ranker):
    # Models loaded once and cached
    # Prevents redundant loading
```

### 3. Factory Pattern
```python
def initialize_llmchain():
    # Conditionally creates different LLM types
    if llm_model in groq_models:
        llm = ChatGroq(...)
    else:
        llm = HuggingFaceEndpoint(...)
```

### 4. Strategy Pattern
```python
def load_doc(file_path, chunk_size, chunk_overlap, is_table=False):
    if not is_table:
        loader = PyMuPDFLoader(file_path)
    else:
        parser = LlamaParse(...)
```

### 5. Chain of Responsibility (LangChain)
```python
Query → Retriever → Reranker → Compressor → LLM → Response
```

### 6. Observer Pattern (Streamlit Session State)
- Session state changes trigger UI updates
- Reactive programming model

## Database Schema

### ChromaDB Collection Structure

```python
Collection: "sample" (configurable)
{
    "ids": ["uuid-1", "uuid-2", ...],
    "embeddings": [[0.1, 0.2, ...], [0.3, 0.4, ...], ...],
    "metadatas": [
        {
            "page": 1,
            "source": "/path/to/file.pdf"
        },
        {
            "page": 2,
            "source": "/path/to/file.pdf"
        }
    ],
    "documents": [
        "Chunk text content...",
        "Another chunk text..."
    ]
}
```

### Vector Dimensions
- **Embedding Model**: all-MiniLM-L6-v2
- **Dimensions**: 384
- **Distance Metric**: Cosine similarity (default in ChromaDB)

### Indexing Strategy
- **HNSW (Hierarchical Navigable Small World)**: Default ChromaDB index
- **Fast approximate nearest neighbor search**
- **Trade-off**: Speed vs. accuracy (configurable)

## API Integration

### HuggingFace Integration
```python
from langchain_huggingface import HuggingFaceEndpoint

llm = HuggingFaceEndpoint(
    repo_id="mistralai/Mistral-7B-Instruct-v0.2",
    temperature=0.1,
    max_new_tokens=1200,
    top_k=3,
    huggingfacehub_api_token=hf_key
)
```

**Models Used**:
- mistralai/Mistral-7B-Instruct-v0.1
- mistralai/Mistral-7B-Instruct-v0.2
- mistralai/Mixtral-8x7B-Instruct-v0.1

### Groq Integration
```python
from langchain_groq import ChatGroq

llm = ChatGroq(
    model="llama-3.1-70b-versatile",
    temperature=0.1,
    groq_api_key=groq_key
)
```

**Models Used**:
- llama-3.1-70b-versatile
- llama-3.2-11b-vision-preview
- mixtral-8x7b-32768

### LlamaParse Integration
```python
from llama_parse import LlamaParse

parser = LlamaParse(
    result_type="markdown",
    api_key=llama_parser_key
)
documents = parser.load_data(file_path=file_path)
```

**Features**:
- Advanced table extraction
- Layout preservation
- Markdown output format

## Performance Considerations

### Bottlenecks

1. **Document Upload & Processing**
   - PDF parsing time: O(n) where n = number of pages
   - Embedding generation: O(m) where m = number of chunks
   - ChromaDB indexing: O(m log m)

2. **Query Processing**
   - Vector search: O(log n) with HNSW index
   - Reranking: O(k) where k = retrieved documents
   - LLM inference: Depends on model size and API latency

### Optimization Strategies

#### 1. Model Caching
```python
@st.cache_resource
def load_models(_self, embedder, ranker):
    # Loaded once per application lifecycle
```

#### 2. Batch Processing
- Embeddings generated in batches (default: 32)
- Reduces API calls and memory overhead

#### 3. MMR Retrieval
```python
retriever = vector_db.as_retriever(
    search_type="mmr",
    search_kwargs={'k': 10, 'lambda_mult': 0.25}
)
```
- Retrieves diverse documents
- Reduces redundancy
- lambda_mult controls diversity-relevance trade-off

#### 4. Reranking
```python
compressor = CrossEncoderReranker(model=ranker_model, top_n=3)
```
- Refines top-k results
- Higher precision than embedding similarity alone

#### 5. Persistent Vector Store
- ChromaDB persists to disk
- No re-indexing required between sessions
- Fast startup times

### Scalability

#### Horizontal Scaling
- Multiple Streamlit instances with shared ChromaDB backend
- Load balancer for user distribution
- Session affinity for conversation continuity

#### Vertical Scaling
- Increase RAM for larger documents
- GPU acceleration for embeddings (optional)
- SSD storage for faster ChromaDB operations

### Memory Management

```python
# Approximate memory usage
Embeddings model: ~100 MB
Reranker model: ~500 MB
ChromaDB in-memory: ~10 MB per 1000 chunks
Session state: ~5 MB per user
Total baseline: ~700 MB + (chunks * 0.01 MB) + (users * 5 MB)
```

### Latency Analysis

```
Document Upload (100-page PDF):
├── File save: ~100ms
├── PDF parsing: ~2s (PyMuPDF) or ~10s (LlamaParse)
├── Text splitting: ~500ms
├── Embedding generation: ~5s
└── ChromaDB indexing: ~1s
Total: ~8s (PyMuPDF) or ~18s (LlamaParse)

Query Processing:
├── Query embedding: ~50ms
├── Vector search: ~100ms
├── Reranking: ~200ms
├── LLM inference: ~2-10s (depends on model)
└── Response streaming: ~1s
Total: ~3-12s
```

## Error Handling Architecture

### Error Propagation

```
Exception occurs
       ↓
sys.exc_info() captures details
       ↓
write_error_log() logs to file
       ↓
st.error() displays to user
       ↓
sys.exit() or continue (depends on severity)
```

### Error Categories

1. **Configuration Errors**: Missing config.ini, invalid API keys
2. **File Errors**: Upload failures, permission issues
3. **Processing Errors**: PDF parsing failures, embedding errors
4. **Database Errors**: ChromaDB connection issues
5. **API Errors**: LLM API failures, rate limits
6. **Runtime Errors**: Memory errors, timeout issues

### Recovery Strategies

- **Retry Logic**: Implicit in API libraries
- **Fallback Models**: User can switch LLMs
- **Session Isolation**: Errors don't affect other users
- **Graceful Degradation**: Non-RAG mode when vector DB unavailable

---

**Document Version**: 1.0
**Last Updated**: December 2024
**Maintained By**: Merit Software Services
