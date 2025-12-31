# Taxonomy Classification - Technical Architecture

## System Architecture

### High-Level Architecture

The Taxonomy Classification system follows a modular, pipeline-based architecture that separates concerns and enables maintainability:

```
┌─────────────────────────────────────────────────────────────────┐
│                     Presentation Layer                          │
│                    (Streamlit Web UI)                          │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Application Layer                             │
│              (ContentClassification Class)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Prompt     │  │   LLM Chain  │  │   Output     │         │
│  │  Management  │  │  Orchestrator│  │   Parser     │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Integration Layer                             │
│                    (LangChain Framework)                        │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    External Services                            │
│                  (OpenAI API - GPT-4o-mini)                     │
└─────────────────────────────────────────────────────────────────┘
```

### Component Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        taxonomy.py                              │
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐   │
│  │              Data Models (Pydantic)                     │   │
│  │  ┌──────────────────────────────────────────────────┐  │   │
│  │  │  TaxonomyOutputModel                             │  │   │
│  │  │  - taxonomy_type: str                            │  │   │
│  │  │  - category: str                                 │  │   │
│  │  │  - sub_category: str                             │  │   │
│  │  │  - scores: float                                 │  │   │
│  │  └──────────────────────────────────────────────────┘  │   │
│  │  ┌──────────────────────────────────────────────────┐  │   │
│  │  │  TaxonomyOutputParser                            │  │   │
│  │  │  - results: list[TaxonomyOutputModel]            │  │   │
│  │  └──────────────────────────────────────────────────┘  │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐   │
│  │         ContentClassification Class                     │   │
│  │  ┌──────────────────────────────────────────────────┐  │   │
│  │  │  __init__()                                      │  │   │
│  │  │  - Load environment variables                    │  │   │
│  │  │  - Initialize LLM model                          │  │   │
│  │  │  - Define prompt template                        │  │   │
│  │  │  - Initialize output parser                      │  │   │
│  │  └──────────────────────────────────────────────────┘  │   │
│  │  ┌──────────────────────────────────────────────────┐  │   │
│  │  │  get_prompt()                                    │  │   │
│  │  │  - Create PromptTemplate with format instructions│  │   │
│  │  └──────────────────────────────────────────────────┘  │   │
│  │  ┌──────────────────────────────────────────────────┐  │   │
│  │  │  get_response(article, taxonomy)                 │  │   │
│  │  │  - Build and execute LangChain pipeline          │  │   │
│  │  └──────────────────────────────────────────────────┘  │   │
│  │  ┌──────────────────────────────────────────────────┐  │   │
│  │  │  to_dataframe(response)                          │  │   │
│  │  │  - Convert JSON response to DataFrame            │  │   │
│  │  └──────────────────────────────────────────────────┘  │   │
│  │  ┌──────────────────────────────────────────────────┐  │   │
│  │  │  get_taxonomy_data(article, taxonomy)            │  │   │
│  │  │  - Orchestrate full classification workflow      │  │   │
│  │  └──────────────────────────────────────────────────┘  │   │
│  └────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

### Classification Pipeline

```
1. User Input
   └─> Article text entered in Streamlit form
       │
2. Taxonomy Loading
   └─> JSON file loaded into memory
       │
3. Prompt Construction
   └─> PromptTemplate with format instructions
       │
       ├─> Input Variables: {text, taxonomy}
       └─> Format Instructions: JSON schema for output
       │
4. LangChain Execution
   └─> prompt | llm_model | output_parser
       │
       ├─> Prompt rendering with article and taxonomy
       ├─> LLM invocation (OpenAI API call)
       └─> JSON parsing with Pydantic validation
       │
5. Response Processing
   └─> Extract taxonomy classifications
       │
       ├─> Parse results array
       ├─> Extract fields: taxonomy_type, category, sub_category, scores
       └─> Convert to DataFrame
       │
6. Results Display
   └─> Streamlit dataframe widget
       └─> Sorted by score (descending)
```

### Detailed Data Flow Diagram

```
┌──────────────┐
│  User Types  │
│   Article    │
└──────┬───────┘
       │
       ▼
┌──────────────────┐
│  Streamlit Form  │
│   Submission     │
└──────┬───────────┘
       │
       ▼
┌────────────────────────────────────────┐
│  ContentClassification.get_taxonomy_data│
└──────┬─────────────────────────────────┘
       │
       ▼
┌────────────────────────────────────────┐
│  ContentClassification.get_response    │
└──────┬─────────────────────────────────┘
       │
       ├─> Load taxonomies.json
       │
       ▼
┌────────────────────────────────────────┐
│  ContentClassification.get_prompt      │
│  - Build PromptTemplate                │
│  - Add format instructions             │
└──────┬─────────────────────────────────┘
       │
       ▼
┌────────────────────────────────────────┐
│  LangChain Pipeline Execution          │
│  prompt | llm_model | output_parser    │
└──────┬─────────────────────────────────┘
       │
       ▼
┌────────────────────────────────────────┐
│  OpenAI API Call                       │
│  Model: gpt-4o-mini                    │
│  Temperature: 0                        │
└──────┬─────────────────────────────────┘
       │
       ▼
┌────────────────────────────────────────┐
│  JSON Response                         │
│  {                                     │
│    "results": [                        │
│      {                                 │
│        "taxonomy_type": "...",         │
│        "category": "...",              │
│        "sub_category": "...",          │
│        "scores": 9.5                   │
│      },                                │
│      ...                               │
│    ]                                   │
│  }                                     │
└──────┬─────────────────────────────────┘
       │
       ▼
┌────────────────────────────────────────┐
│  JsonOutputParser                      │
│  - Validate against Pydantic schema    │
│  - Parse JSON structure                │
└──────┬─────────────────────────────────┘
       │
       ▼
┌────────────────────────────────────────┐
│  ContentClassification.to_dataframe    │
│  - Extract fields from results         │
│  - Create DataFrame                    │
└──────┬─────────────────────────────────┘
       │
       ▼
┌────────────────────────────────────────┐
│  Sort by Score                         │
└──────┬─────────────────────────────────┘
       │
       ▼
┌────────────────────────────────────────┐
│  Streamlit Display                     │
│  st.dataframe(results)                 │
└────────────────────────────────────────┘
```

## Key Technical Components

### 1. Pydantic Models

#### TaxonomyOutputModel
```python
class TaxonomyOutputModel(BaseModel):
    taxonomy_type: str = Field(description="name of higher level taxonomy")
    category: str = Field(description="respective sub-taxonomy")
    sub_category: str = Field(description="respective sub-taxonomy's value")
    scores: float = Field(description="relevancy score between 0 and 10 for the article")
```

**Purpose**: Defines the structure for a single taxonomy classification result.

**Fields**:
- `taxonomy_type`: The main taxonomy category (e.g., "Topic-Based Taxonomies")
- `category`: The sub-category within the taxonomy (e.g., "General Topics")
- `sub_category`: The specific value (e.g., "Technology")
- `scores`: Relevancy score from 0 to 10

#### TaxonomyOutputParser
```python
class TaxonomyOutputParser(BaseModel):
    results: list[TaxonomyOutputModel]
```

**Purpose**: Wraps multiple taxonomy classifications into a results array.

**Usage**: Validates that the LLM returns a properly structured response with multiple classifications.

### 2. ContentClassification Class

#### Initialization
```python
def __init__(self):
    _ = load_dotenv(find_dotenv())
    self.api_key = os.getenv('API_KEY')
    self.llm_model = init_chat_model("gpt-4o-mini",
                                     model_provider="openai",
                                     temperature=0,
                                     api_key=self.api_key)
    self.output_parser = JsonOutputParser(pydantic_object=TaxonomyOutputParser)
```

**Responsibilities**:
- Load environment variables from .env file
- Extract OpenAI API key
- Initialize GPT-4o-mini model with zero temperature for deterministic results
- Create JSON output parser with Pydantic schema

#### Prompt Template
```python
self.prompt_template = """
    You will be provided with text and taxonomies delimited by triple quotes.
    text: This contains an article.
    taxonomy: This contains main taxonomy and sub-taxonomy. The sub-taxonomy
    is further categorized wherever possible.

    Your task is to classify the text against all taxonomy and it's sub-taxonomy
    with respective categories and provide the relevancy scores as well.

    Based on the relevancy score, do consider top 5 taxonomies.

    Format the output as JSON with the following keys such as:
    taxonomy_type
    category
    sub_category
    scores

    Note: Please mind that output should contain top 5 taxonomies.

    Content: ```{text}```
    Taxonomies: ```{taxonomy}```
"""
```

**Key Elements**:
- Clear instructions for the LLM
- Triple-quote delimiters for content separation
- Explicit field definitions
- Constraint: Return top 5 taxonomies
- Variable placeholders: {text}, {taxonomy}

### 3. LangChain Pipeline

#### Pipeline Structure
```python
chain = prompt | self.llm_model | self.output_parser
output = chain.invoke({"text": article, "taxonomy": taxonomy})
```

**Components**:
1. **Prompt**: PromptTemplate with format instructions
2. **LLM Model**: GPT-4o-mini with temperature=0
3. **Output Parser**: JsonOutputParser with Pydantic validation

**Execution Flow**:
- Prompt is rendered with input variables
- Rendered prompt sent to OpenAI API
- Response parsed and validated against schema
- Structured output returned

### 4. Data Transformation

#### DataFrame Conversion
```python
def to_dataframe(self, response):
    data = [{"taxonomy_type": i['taxonomy_type'],
             "category": i['category'],
             "sub_category": i['sub_category'],
             "score": i['scores']}
            for i in response['results']]
    df = pd.DataFrame(data)
    return df
```

**Purpose**: Transform JSON response into tabular format for display.

**Process**:
1. Extract fields from each result in the response
2. Build list of dictionaries
3. Convert to Pandas DataFrame
4. Return for sorting and display

## Technology Stack Deep Dive

### LangChain Framework

**Version**: 0.3.10

**Purpose**: Orchestrate LLM interactions with structured pipelines

**Key Features Used**:
- `init_chat_model`: Initialize LLM with provider abstraction
- `PromptTemplate`: Template management with variable injection
- `JsonOutputParser`: Structured output parsing with validation
- Pipeline operator (`|`): Chain components together

**Benefits**:
- Simplified LLM integration
- Reusable prompt templates
- Automatic output parsing
- Easy model switching

### OpenAI Integration

**Model**: GPT-4o-mini

**Configuration**:
- Temperature: 0 (deterministic outputs)
- Provider: OpenAI
- Authentication: API key via environment variable

**Why GPT-4o-mini**:
- Cost-effective for classification tasks
- Fast response times
- Sufficient capability for structured output
- Good balance of performance and cost

### Streamlit Framework

**Version**: 1.40.2

**Usage**:
- Web interface creation
- Form handling
- DataFrame display
- Spinner for loading states

**Components Used**:
```python
st.set_page_config(layout="wide")
st.title("Taxonomy Classification")
with st.form("sample_form"):
    text = st.text_area("Please input your article")
    button = st.form_submit_button("Submit")
if text and button:
    with st.spinner("Please wait!!!"):
        st.dataframe(classifier.get_taxonomy_data(text, taxonomy), width=1200)
```

### Pydantic

**Version**: Implicit (via LangChain dependencies)

**Purpose**: Data validation and schema definition

**Benefits**:
- Type safety
- Automatic validation
- Clear schema documentation
- Integration with LangChain parsers

## Configuration Management

### Environment Variables

Required in `.env` file:
```
API_KEY=your_openai_api_key_here
```

**Loading Mechanism**:
```python
from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv())
self.api_key = os.getenv('API_KEY')
```

### Taxonomy Configuration

**File Location**: `taxonomies.json` (hardcoded)

**Format**: Nested JSON structure
```json
{
  "Taxonomy Category": {
    "Sub-Category": ["Value1", "Value2", ...],
    ...
  },
  ...
}
```

**Loading**:
```python
with open("taxonomies.json", "r") as file:
    taxonomy = json.load(file)
```

## Performance Considerations

### Latency Sources

1. **API Call Latency**: Typically 1-3 seconds
2. **Network Latency**: 100-500ms
3. **Processing Time**: Minimal (<100ms)

### Total Response Time
Average: 2-5 seconds per classification

### Optimization Opportunities

1. **Caching**: Cache results for identical articles
2. **Batch Processing**: Process multiple articles in parallel
3. **Model Selection**: Use faster models for simpler cases
4. **Streaming**: Stream responses for better UX
5. **Async Processing**: Use async/await for non-blocking calls

## Error Handling

### Current Implementation
- Basic warning suppression for deprecation warnings
- No explicit error handling

### Missing Error Handling
- API key validation
- Network error handling
- Malformed JSON responses
- Invalid taxonomy structure
- Rate limiting handling
- Timeout management

## Security Considerations

### API Key Management
- Stored in .env file (not committed to version control)
- Loaded at runtime via environment variables
- Not exposed in code or logs

### Input Validation
- Limited input validation
- No sanitization of user input
- No length restrictions

### Recommendations
1. Add input length limits
2. Implement rate limiting
3. Add user authentication for production
4. Sanitize user inputs
5. Implement request logging (without sensitive data)
6. Add CORS configuration for API deployment

## Scalability Analysis

### Current Limitations
- Single-threaded processing
- No concurrent request handling
- In-memory taxonomy storage
- No request queuing

### Scaling Considerations

**Vertical Scaling**:
- Increase API rate limits
- Upgrade to faster OpenAI models
- Optimize prompt size

**Horizontal Scaling**:
- Deploy multiple Streamlit instances
- Implement load balancing
- Use message queues for async processing
- Cache frequent classifications

## Dependencies and Versions

```
langchain==0.3.10
langchain-community==0.3.10
langchain-core==0.3.22
langchain-openai==0.2.12
streamlit==1.40.2
pydantic (implicit via langchain)
pandas (implicit via streamlit)
python-dotenv (implicit)
```

## Code Quality and Maintainability

### Strengths
- Clear class structure
- Separation of concerns
- Type hints on Pydantic models
- Reusable components

### Areas for Improvement
- Add docstrings to methods
- Implement error handling
- Add type hints to all functions
- Extract configuration to separate file
- Add logging
- Implement unit tests
- Add input validation
