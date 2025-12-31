# Zero-Shot NER Prototype - Architecture Documentation

## Table of Contents
- [System Architecture](#system-architecture)
- [Component Design](#component-design)
- [Data Flow](#data-flow)
- [Model Architecture](#model-architecture)
- [Class Structure](#class-structure)
- [Design Patterns](#design-patterns)
- [Security Architecture](#security-architecture)
- [Performance Considerations](#performance-considerations)

## System Architecture

### High-Level Architecture

The Zero-Shot NER prototype follows a three-tier architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                        │
│  ┌──────────────────────┐     ┌──────────────────────┐     │
│  │  Streamlit Web UI    │     │   External Clients   │     │
│  │   (Port 8501)        │     │   (HTTP Requests)    │     │
│  └──────────────────────┘     └──────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│  ┌──────────────────────────────────────────────────────┐   │
│  │            Flask RESTful API Server                  │   │
│  │                 (Port 5000)                          │   │
│  │  ┌────────────┐  ┌────────────┐  ┌─────────────┐   │   │
│  │  │    /ner    │  │ /relation  │  │      /      │   │   │
│  │  │  endpoint  │  │  endpoint  │  │  health     │   │   │
│  │  └────────────┘  └────────────┘  └─────────────┘   │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                      Model Layer                             │
│  ┌──────────────────────┐     ┌──────────────────────┐     │
│  │   GLiNER Pipeline    │     │  NuNER Pipeline      │     │
│  │  - Entity Extract    │     │  - Entity Extract    │     │
│  │  - Relation Extract  │     │  (Optional)          │     │
│  └──────────────────────┘     └──────────────────────┘     │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │          UTCA Framework Integration                  │   │
│  │   (GLiNERPredictor, GLiNER, GLiNERRelationExtraction)│   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Component Interaction

```
┌──────────────┐
│   User       │
└──────┬───────┘
       │
       ▼
┌──────────────────┐
│ Streamlit App    │─────────┐
│ (streamlit_app.py)│         │
└──────┬───────────┘         │
       │                     │
       │ HTTP Request        │ API Health Check
       │                     │ & Startup
       ▼                     ▼
┌──────────────────┐  ┌──────────────┐
│ Inference        │  │ check_api.py │
│ (inference.py)   │  └──────────────┘
└──────┬───────────┘
       │
       │ POST /ner or /relation
       ▼
┌─────────────────────────────────┐
│   Flask API (model_api.py)      │
│  - Authentication               │
│  - Input Validation             │
│  - Request Routing              │
└──────┬──────────────────────────┘
       │
       ├─────────────────┬────────────────┐
       ▼                 ▼                ▼
┌──────────────┐  ┌─────────────┐  ┌────────────┐
│ ZeroShotNer  │  │ZeroShotRel  │  │ APIHelper  │
└──────────────┘  └─────────────┘  └────────────┘
       │                 │                │
       └─────────────────┴────────────────┘
                         │
                         ▼
              ┌──────────────────┐
              │  Model Predictors│
              │  - GLiNER        │
              │  - NuNER         │
              └──────────────────┘
```

## Component Design

### 1. Presentation Layer

#### Streamlit Web Interface (`interface/streamlit_app.py`)

**Purpose**: Provides user-friendly web interface for testing and demonstration

**Key Components**:
- `App` class: Main application controller
- `ner_form()`: NER input form and results display
- `relation_form()`: Relation extraction form and results display
- Session state management for multi-model outputs

**Responsibilities**:
- Render input forms with appropriate fields
- Handle user interactions and form submissions
- Display results with color-coded entity visualization
- Manage API connectivity and health checks
- Coordinate between tabs (NER and Relation Extraction)

#### API Client (`interface/inference.py`)

**Purpose**: Abstraction layer for API communication

**Methods**:
- `get_ner_output()`: Sends NER requests to Flask API
- `get_relation_output()`: Sends relation extraction requests

**Features**:
- HTTP Basic Authentication handling
- JSON request/response processing
- Error handling and user feedback

#### API Health Manager (`interface/check_api.py`)

**Purpose**: Ensures API availability before making requests

**Key Methods**:
- `is_flask_api_running()`: Checks if API is accessible
- `start_flask_api()`: Launches API server if not running
- `check_required_path()`: Validates configuration paths

**Features**:
- Automatic API startup with progress indication
- Platform-independent process management
- Configuration validation

### 2. Application Layer

#### Flask API Server (`api/model_api.py`)

**Purpose**: Central RESTful API server handling all inference requests

**Class**: `ZeroShotAPI`

**Inheritance Hierarchy**:
```
ZeroShotAPI
├── APIHelper
│   └── Utils
├── ZeroShotNer
└── ZeroShotRelation
```

**Endpoints**:

1. **GET /**
   - Health check endpoint
   - Returns: "welcome" with 200 status
   - Updates last request timestamp

2. **POST /ner**
   - Named entity recognition
   - Authentication: Required (HTTP Basic Auth)
   - Validates input using `NERRequestModel`
   - Returns: HTML-rendered entity visualization

3. **POST /relation**
   - Relation extraction
   - Authentication: Required (HTTP Basic Auth)
   - Validates input using `RelationRequestModel`
   - Returns: JSON array of extracted relations

**Features**:
- HTTP Basic Authentication
- Pydantic-based input validation
- Automatic inactivity monitoring
- Thread-based background monitoring
- Comprehensive error handling

#### Input Validators (`api/input_validators.py`)

**Purpose**: Pydantic models for request validation

**Models**:

1. **NERRequestModel**
```python
class NERRequestModel(BaseModel):
    model: str              # "numind" or "gliner"
    input_text: str         # min 10 characters
    labels: list            # each label min 3 characters
    threshold: float        # default 0.5
    nested_ner: bool        # default False
```

2. **RelationRequestModel**
```python
class RelationRequestModel(BaseModel):
    input_text: str         # min 30 characters
    labels: list            # entity labels
    relation: str           # relation name (min 3 chars)
    pairs: str              # pair filter string
    threshold: str          # optional distance threshold
```

**Validation Features**:
- Field type checking
- Length constraints
- Custom validators for model names and labels
- Detailed error messages

### 3. Model Layer

#### API Helper (`api/helpers.py`)

**Purpose**: Model initialization and resource management

**Class**: `APIHelper` (extends `Utils`)

**Key Responsibilities**:
1. **Model Management**
   - `init_predictor()`: Initialize GLiNER and NuNER predictors
   - `check_model_availability()`: Download models if not cached
   - Configuration-based model loading

2. **Pipeline Construction**
   - `init_ner_pipe()`: Build NER processing pipeline
   - `init_relation_pipe()`: Build relation extraction pipeline
   - UTCA framework integration

3. **Resource Monitoring**
   - `check_inactivity_and_kill()`: Monitor API usage
   - `kill_process_on_port()`: Clean shutdown on timeout
   - Configurable inactivity threshold

**Pipeline Architecture**:

```python
# NER Pipeline
ner_pipe = (
    GLiNER(predictor, preprocess=GLiNERPreprocessor(threshold=0.5))
    | RenameAttribute("output", "entities")
)

# Relation Extraction Pipeline
rel_pipe = (
    GLiNER(predictor, preprocess=GLiNERPreprocessor(threshold=0.5))
    | RenameAttribute("output", "entities")
    | GLiNERRelationExtraction(
        predictor,
        preprocess=(
            GLiNERPreprocessor(threshold=0.5)
            | GLiNERRelationExtractionPreprocessor()
        )
    )
)
```

#### Zero-Shot NER (`api/zero_shot_ner.py`)

**Purpose**: Core entity extraction logic

**Class**: `ZeroShotNer`

**Key Methods**:

1. **`predict_entity(model, flag, text, labels, threshold, nested_ner)`**
   - Main prediction interface
   - Handles both GLiNER and NuNER models
   - Returns spaCy Doc object with entities

2. **`create_doc_bin(record, text, labels)`**
   - Converts model output to spaCy Doc
   - Handles entity span creation
   - Manages NER pipeline labels

3. **`merge_entities(entities)`**
   - Merges adjacent entities with same label
   - Specific to NuNER model output
   - Prevents entity fragmentation

**Entity Processing Flow**:
```
Input Text + Labels
       ↓
Model Prediction
       ↓
Entity List (with scores)
       ↓
Entity Merging (if NuNER)
       ↓
spaCy Doc Creation
       ↓
Entity Span Validation
       ↓
Final Doc with Entities
```

#### Zero-Shot Relation Extraction (`api/zero_shot_relation.py`)

**Purpose**: Relation extraction between entities

**Class**: `ZeroShotRelation`

**Key Method**: `get_relation_result(model, relation, text, pairs_filter, labels, distance_threshold)`

**Features**:
- Parse pair filter strings (e.g., "person -> organization")
- Optional distance threshold for relation candidates
- Returns structured relation output

**Relation Processing Flow**:
```
Input Text + Entity Labels + Relation Definition
       ↓
Parse Pair Filters
       ↓
Model Inference (with distance constraint if specified)
       ↓
Relation Extraction
       ↓
Structured Output (entity pairs with relation)
```

### 4. Utility Layer

#### Logging and Configuration (`utils.py`)

**Classes**:

1. **CustomLogger**
   - Time-based log file organization (by date and hour)
   - Structured error logging with stack traces
   - Log directory auto-creation

2. **Utils** (extends CustomLogger)
   - Configuration file parsing
   - Color code generation for entity visualization
   - API startup management
   - spaCy displacy options generation

**Logging Structure**:
```
logs/
└── DD-MM-YY/
    ├── 00.log
    ├── 01.log
    └── ...
```

**Configuration Management**:
- INI file parsing
- Section-based organization
- Dynamic configuration dictionary
- Validation and error handling

## Data Flow

### Entity Extraction Flow

```
1. User Input (Web UI)
   ├── Text: "John works at Microsoft"
   └── Labels: ["person", "organization"]

2. Streamlit Form Submission
   └── inference.py: get_ner_output()

3. HTTP POST to /ner
   {
     "model": "gliner",
     "input_text": "John works at Microsoft",
     "labels": ["person", "organization"],
     "threshold": 0.5,
     "nested_ner": false
   }

4. Input Validation (NERRequestModel)
   └── Validate fields and constraints

5. Model Prediction
   ├── Select model (GLiNER or NuNER)
   ├── Run prediction pipeline
   └── Extract entities with scores

6. Entity Processing
   ├── Merge adjacent entities (if NuNER)
   ├── Create spaCy Doc
   └── Generate color codes

7. Visualization
   └── displacy.render() → HTML output

8. Response
   {
     "render_data": "<div>...colored HTML...</div>"
   }

9. Display in Web UI
   └── st.markdown(render_data, unsafe_allow_html=True)
```

### Relation Extraction Flow

```
1. User Input (Web UI)
   ├── Text: "John works at Microsoft in Seattle"
   ├── Labels: ["person", "organization", "location"]
   ├── Relation: "works_for"
   └── Pairs: "person -> organization"

2. HTTP POST to /relation
   {
     "input_text": "...",
     "labels": ["person", "organization", "location"],
     "relation": "works_for",
     "pairs": "person -> organization",
     "threshold": ""
   }

3. Input Validation (RelationRequestModel)

4. Relation Extraction Pipeline
   ├── Step 1: Entity Extraction
   │   └── Identify all entities with labels
   ├── Step 2: Pair Filtering
   │   └── Filter entity pairs by specified types
   ├── Step 3: Relation Classification
   │   └── Classify relations between pairs
   └── Step 4: Apply Distance Threshold (if specified)

5. Response
   {
     "relations": [
       {
         "head": {"text": "John", "type": "person", "start": 0, "end": 4},
         "tail": {"text": "Microsoft", "type": "organization", "start": 14, "end": 23},
         "relation": "works_for",
         "score": 0.89
       }
     ]
   }

6. Display in Web UI
   └── st.write(relations)
```

## Model Architecture

### GLiNER (Generalist and Lightweight Named Entity Recognition)

**Architecture Type**: Transformer-based zero-shot NER

**Key Characteristics**:
- Multi-task learning approach
- No task-specific training required
- Handles arbitrary entity types
- Supports relation extraction

**Model Configuration**:
```python
GLiNERPredictor(
    GLiNERPredictorConfig(
        model_name="knowledgator/gliner-multitask-large-v0.5",
        device="cpu"  # or "cuda"
    )
)
```

**Pipeline Components**:
1. **GLiNER**: Entity extraction task
2. **GLiNERPreprocessor**: Input preprocessing and threshold filtering
3. **GLiNERRelationExtraction**: Relation identification between entities
4. **GLiNERRelationExtractionPreprocessor**: Relation-specific preprocessing

### NuNER Zero

**Architecture Type**: Zero-shot NER specialist

**Key Characteristics**:
- Optimized for zero-shot scenarios
- May produce fragmented entities (requires merging)
- Alternative model for comparison

**Model Configuration**:
```python
GLiNERPredictor(
    GLiNERPredictorConfig(
        model_name="numind/NuNER_Zero",
        device="cpu"
    )
)
```

### UTCA Framework Integration

**Universal Text Classification Architecture (UTCA)** provides:
- Standardized predictor interface
- Pipeline composition with `|` operator
- Attribute transformation utilities
- Consistent preprocessing approach

**Benefits**:
- Model-agnostic pipeline design
- Easy model swapping
- Composable processing steps
- Unified inference interface

## Class Structure

### Inheritance Diagram

```
CustomLogger
    └── Utils
            └── APIHelper
                    └── ZeroShotAPI
                            ├── (mixin) ZeroShotNer
                            └── (mixin) ZeroShotRelation

CustomLogger
    └── Utils
            └── StartAPI
                    └── App
                            └── (mixin) Inference
```

### Class Responsibilities

| Class | File | Primary Responsibility |
|-------|------|------------------------|
| `CustomLogger` | utils.py | Logging infrastructure |
| `Utils` | utils.py | Configuration, color generation, API management |
| `APIHelper` | api/helpers.py | Model initialization, pipeline creation |
| `ZeroShotNer` | api/zero_shot_ner.py | Entity extraction logic |
| `ZeroShotRelation` | api/zero_shot_relation.py | Relation extraction logic |
| `ZeroShotAPI` | api/model_api.py | Flask API server, routing, authentication |
| `NERRequestModel` | api/input_validators.py | NER request validation |
| `RelationRequestModel` | api/input_validators.py | Relation request validation |
| `StartAPI` | interface/check_api.py | API health and startup |
| `Inference` | interface/inference.py | API client methods |
| `App` | interface/streamlit_app.py | Streamlit UI controller |

## Design Patterns

### 1. Multiple Inheritance Pattern
The API server uses multiple inheritance to compose functionality:
```python
class ZeroShotAPI(APIHelper, ZeroShotNer, ZeroShotRelation):
    pass
```

**Benefits**:
- Separation of concerns
- Modular functionality
- Easy testing of individual components

### 2. Pipeline Pattern (UTCA)
Processing steps connected using the pipe operator:
```python
pipeline = Step1() | Step2() | Step3()
result = pipeline.run(input_data)
```

**Benefits**:
- Clear data flow
- Composable processing
- Easy pipeline modification

### 3. Singleton Configuration
Configuration read once and shared via session state:
```python
if "config" not in st.session_state:
    self.config_data = self.read_config()
    st.session_state['config'] = self.config_data
```

### 4. Strategy Pattern
Model selection at runtime based on configuration:
```python
model = self.ner_numind if model_name == "numind" else self.ner_gliner
```

### 5. Observer Pattern
Background thread monitoring API activity:
```python
inactivity_thread = threading.Thread(target=self.check_inactivity_and_kill)
inactivity_thread.daemon = True
inactivity_thread.start()
```

## Security Architecture

### Authentication

**Method**: HTTP Basic Authentication (Flask-HTTPAuth)

**Configuration**:
```ini
[api]
usr = zero_shot
pwd = P@ssw0rd
```

**Implementation**:
```python
@self.auth.verify_password
def verify_password(username, password):
    if username in self.users and self.users.get(username) == password:
        return username
```

**Protected Endpoints**:
- POST /ner
- POST /relation

**Unprotected Endpoints**:
- GET / (health check)

### Input Validation

**Strategy**: Pydantic model validation

**Validation Checks**:
- Type validation
- Length constraints (min/max)
- Allowed value sets (model names)
- Custom field validators

**Error Handling**:
```python
try:
    valid_data = NERRequestModel(**data)
except ValidationError as e:
    error_messages = [err['msg'] for err in e.errors()]
    return jsonify({"error": ", ".join(error_messages)}), 400
```

### Resource Protection

1. **Automatic Shutdown**: Server terminates after inactivity period
2. **Port Management**: Clean process termination on shutdown
3. **Model Caching**: Downloaded models stored locally
4. **Log Rotation**: Time-based log file organization

## Performance Considerations

### Model Loading

**Strategy**: Load models once at server startup
- Models initialized in `APIHelper.__init__()`
- Shared across all requests
- Device configuration (CPU/GPU) from config

**Optimization**:
```python
if self.both_model:
    self.ner_numind = self.init_ner_pipe(self.predictor_numind)
else:
    self.ner_numind = None  # Skip if not needed
```

### Model Caching

**Local Cache Structure**:
```
models/
├── NuNER_Zero/
│   └── models--numind--NuNER_Zero/
│       └── snapshots/
│           └── 9c23c2051d3e9a4a8b8ce0d132911e0000aa53c1/
└── gliner-multitask-large-v0.5/
    └── models--knowledgator--gliner-multitask-large-v0.5/
        └── snapshots/
            └── f7fd7f124545e2cf5b89d83e9e8e499d2fe6a145/
```

**Benefits**:
- Faster startup after first run
- No repeated downloads
- Offline operation after initial setup

### Request Processing

**Stateless Design**: Each request processed independently
- No server-side session state
- Concurrent request handling
- Simple horizontal scaling

**Response Streaming**: Not implemented (future optimization)

### Memory Management

**Considerations**:
- Models loaded in memory permanently (during server lifetime)
- spaCy Doc objects created per request (garbage collected)
- Entity list size proportional to text length and label count

**Optimization Opportunities**:
- Batch processing for multiple texts
- Model quantization for reduced memory footprint
- GPU acceleration for faster inference

### API Auto-Shutdown

**Purpose**: Resource conservation in development/testing

**Configuration**:
```ini
time_delta = 5  # Hours of inactivity before shutdown
```

**Implementation**:
- Background thread checks every hour
- Compares current time to last request
- Kills server process if threshold exceeded

**Trade-offs**:
- Saves resources when idle
- Adds startup latency on next request
- Suitable for development, not production with load balancer

---

**Document Version**: 1.0
**Last Updated**: December 2025
**Prototype Status**: Active Development
