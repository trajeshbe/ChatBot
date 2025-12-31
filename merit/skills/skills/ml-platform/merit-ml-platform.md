# Merit ML Platform - Enterprise Knowledge Agent Skill

You are an expert AI assistant specialized in the Merit ML Platform, a production-grade microservices platform for AI/ML workloads. This skill provides comprehensive guidance on architecture, development, deployment, and operations.

## Platform Overview

The Merit ML Platform is a Flask-based enterprise system featuring:

- **REST API Layer**: Flask with HTTP Basic Auth
- **Microservices Architecture**: Modular design with multiple specialized workers
- **AI/ML Integration**: OpenAI GPT-4o-mini, HuggingFace embeddings
- **Vector Storage**: ChromaDB for semantic search
- **Observability**: Opik monitoring integration
- **Document Processing**: Multi-format support (HTML, PDF, Excel)
- **RAG Pipeline**: LangGraph-based agentic workflows

## Core Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface Layer                      │
│              Streamlit UI | Azure Bot Framework              │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                      API Gateway                             │
│         Flask REST API with HTTP Basic Auth                  │
│         Endpoints: /talend_pulse, /chat_with_ai              │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                  Application Layer                           │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│   │Talend Pulse  │  │Extractive QA │  │Custom Parser │     │
│   │   Module     │  │    Module    │  │   Module     │     │
│   └──────────────┘  └──────────────┘  └──────────────┘     │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                     AI/ML Layer                              │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│   │LLM Chain     │  │Doc Retriever │  │Prompt Eng    │     │
│   │Builder       │  │              │  │Templates     │     │
│   └──────────────┘  └──────────────┘  └──────────────┘     │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                    Data Layer                                │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│   │ChromaDB      │  │Doc Loader    │  │Document      │     │
│   │Vector Store  │  │              │  │Transformer   │     │
│   └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│               External Services                              │
│   OpenAI API | Opik Monitoring | Azure Bot Service          │
└─────────────────────────────────────────────────────────────┘
```

### Key Modules

1. **NER Module**: Named Entity Recognition (GLiNER-based, zero-shot)
2. **REL Module**: Relationship Extraction
3. **Extractive QA Module**: RAG-based question answering
4. **Talend Pulse Module**: Profile matching and recommendations
5. **Custom Parser Module**: Financial data extraction
6. **Database Module**: Data persistence operations

## Configuration Management

### Config File Structure

```
project_root/
├── config/
│   ├── common_config.yaml      # LLM, API, monitoring settings
│   ├── rag_config.yaml          # RAG pipeline parameters
│   └── talend_pulse_config.yaml # Module-specific config
├── prompt_engineering/
│   └── prompt/
│       ├── pulse_prompts.yaml   # Prompt templates
│       └── rag_prompt.yaml      # RAG prompts
└── utils/
    ├── config_reader.py         # Config loading utility
    └── log_writer.py            # Logging utility
```

### Common Configuration Pattern

```yaml
# config/common_config.yaml
llm_config:
  llm_model: "gpt-4o-mini"
  llm_model_provider: "openai"
  llm_kwargs:
    temperature: 0
    max_tokens: 1000

utils_params:
  opik_host: "http://localhost:5173"
  opik_project_name: "project_name"

api_params:
  port: 5003
  host: "0.0.0.0"
  allowed_extension: [".pdf", ".xlsx"]

prompt_path: "prompt_engineering/prompt"
```

### RAG Configuration Pattern

```yaml
# config/rag_config.yaml
main_params:
  delete_create_collection: false
  main_path: "data/documents"
  collection_name: "knowledge_base"
  persist_directory: "data/chromadb"
  base_depth: 2
  additional_data_path: "data/additional"

  embed_model_params:
    embed_model_name: "sentence-transformers/all-MiniLM-L6-v2"
    embed_cache_folder: "models/embeddings"
    embed_kwargs:
      model_kwargs:
        device: "cpu"
      encode_kwargs:
        normalize_embeddings: true
    reranker_model: "cross-encoder/ms-marco-MiniLM-L-6-v2"
    reranker_cache_dir: "models/reranker"

doc_loader_params:
  data_path: "data/source_docs.xlsx"
  similarity_threshold: 0.5
  content_type: "html"

rag_params:
  retriever:
    retriever_type: "reranker"
    retriever_kwargs:
      base_kwargs:
        search_type: "similarity"
        search_kwargs:
          k: 10
      reranker_kwargs:
        top_n: 5
```

## API Development Guide

### Adding a New REST API Endpoint

**Step 1: Define Pydantic Payload Model**

```python
# api.py
from pydantic import BaseModel, Field, FilePath

class NewEndpointPayload(BaseModel):
    """Validate incoming request data"""
    input_text: str = Field(..., min_length=1, max_length=5000)
    options: dict = Field(default_factory=dict)
```

**Step 2: Add Route to Flask App**

```python
# api.py
class App(Extractor, TalendPulse, NewModule):
    def __init__(self):
        super().__init__()
        self.app = Flask(__name__)
        CORS(self.app)
        self.auth = HTTPBasicAuth()
        self.users = {os.environ['usr']: os.environ['pwd']}
        self.start_app()

    def start_app(self):
        @self.auth.verify_password
        def verify_password(username, password):
            if username in self.users and \
                    self.users.get(username) == password:
                return username

        @self.app.route('/new_endpoint', methods=['POST'])
        @self.auth.login_required
        def new_endpoint_handler():
            """
            Process new endpoint requests.

            Expected JSON payload:
                {
                    "input_text": "your input here",
                    "options": {"key": "value"}
                }

            Returns:
                Response: JSON with processing results
            """
            try:
                data = request.get_json()
                payload = NewEndpointPayload(**data)

                # Process with your module
                result = self.process_new_task(
                    payload.input_text,
                    payload.options
                )

                return jsonify({"result": result}), 200

            except ValidationError as ve:
                return jsonify({
                    "error": "Invalid input",
                    "required_fields": [e['loc'][0] for e in ve.errors()]
                }), 400

            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                self.logger.error(
                    str(e),
                    extra={
                        "error_type": exc_type.__name__,
                        "error": exc_obj,
                        "message": str(e),
                    },
                )
                return jsonify({"error": "Service not available"}), 503
```

**Step 3: Test the Endpoint**

```python
import requests
import os

url = "http://localhost:5003/new_endpoint"
payload = {
    "input_text": "test input",
    "options": {"mode": "fast"}
}

response = requests.post(
    url,
    json=payload,
    auth=(os.environ['usr'], os.environ['pwd'])
)

print(response.json())
```

## Module Development

### Creating a New Processing Module

**Step 1: Create Module Structure**

```
modules/
└── new_module/
    ├── __init__.py
    ├── processor.py          # Main processing logic
    ├── models.py             # ML models loading
    └── utils.py              # Helper functions
```

**Step 2: Implement Module Base Class**

```python
# modules/new_module/processor.py
import sys
from utils.utils import Utils

class NewModule(Utils):
    """
    New processing module for specific task.
    """

    def __init__(self):
        super().__init__()
        self.module_config = self.config_data.get('new_module_params', {})
        self.load_models()

    def load_models(self):
        """Load required ML models."""
        try:
            # Load your models here
            print("---Models loaded for NewModule---")
        except Exception as e:
            self.logger.error(f"Failed to load models: {e}")
            raise

    def process_new_task(self, input_text: str, options: dict):
        """
        Process input and return results.

        Args:
            input_text (str): Input text to process
            options (dict): Processing options

        Returns:
            dict: Processing results
        """
        try:
            # Track with Opik
            result = self.llm.invoke(
                input_text,
                config={
                    "callbacks": [self.opik_tracer],
                    "task": "NewModule_Processing"
                }
            )

            return {
                "processed": result.content,
                "metadata": options
            }

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            self.logger.error(
                str(e),
                extra={
                    "error_type": exc_type.__name__,
                    "error": exc_obj,
                    "message": str(e),
                },
            )
            raise Exception(e)
```

**Step 3: Add Module Config**

```yaml
# config/new_module_config.yaml
new_module_params:
  model_path: "models/new_module"
  batch_size: 32
  threshold: 0.7
  max_workers: 4
```

## RAG Pipeline Implementation

### Building a Custom RAG Chain

**Step 1: Define Graph State**

```python
# modules/custom_rag/pipeline.py
from typing_extensions import TypedDict
from typing import List, Dict

class GraphState(TypedDict):
    question: str
    translated_query: str
    generation: str
    documents: List[str]
    source_links: List[str]
    search_kwargs: Dict
    metadata: Dict
```

**Step 2: Implement Pipeline Nodes**

```python
from langgraph.graph import END, StateGraph, START
from modules.extractive_qa.vector_db.chroma_vector import ExtendedChroma
from modules.extractive_qa.llm.llm_chain_builder import ChainBuilder

class CustomRAGPipeline(ChainBuilder):
    def __init__(
        self,
        documents,
        collection_name: str,
        embed_function,
        reranker_model=None,
        persist_directory: str = "./chromadb",
        delete_create_collection: bool = False,
    ):
        super().__init__()

        # Initialize vector store
        if delete_create_collection:
            self.vector_store = ExtendedChroma.from_documents(
                documents=documents,
                embedding=embed_function,
                collection_name=collection_name,
                persist_directory=persist_directory,
                delete_and_recreate_collection=delete_create_collection,
            )
        else:
            self.vector_store = ExtendedChroma(
                embed_function=embed_function,
                collection_name=collection_name,
                persist_directory=persist_directory,
            )

        self.reranker_model = reranker_model
        self.rag_llm = self.rag_chain()

    def query_validator(self, state: dict):
        """Validate and refine user query."""
        print("---VALIDATING QUERY---")
        prompt = f"{self.prompts['query_validator']}\n\nQuery: {state['question']}"
        translated_query = self.llm.invoke(prompt)

        return {
            "translated_query": translated_query.content,
            "question": state["question"],
        }

    def retriever_node(self, state: dict):
        """Retrieve relevant documents."""
        print("---RETRIEVING DOCUMENTS---")
        question = state["question"]
        translated_query = state["translated_query"]

        # Get retriever
        self.retriever = self.get_retriever(
            retriever_type=self.rag_params["retriever"]["retriever_type"],
            vector_store=self.vector_store,
            reranker_model=self.reranker_model,
            **self.rag_params["retriever"]["retriever_kwargs"],
        )

        documents = self.retriever.invoke(translated_query)

        return {
            "documents": documents,
            "question": question,
            "translated_query": translated_query,
        }

    def generate(self, state: dict):
        """Generate answer using LLM."""
        print("---GENERATING ANSWER---")
        question = state["question"]
        documents = state["documents"]
        translated_query = state["translated_query"]

        generation = self.rag_llm.invoke(
            {"context": documents, "question": translated_query}
        )

        return {
            "documents": documents,
            "question": question,
            "generation": generation,
            "translated_query": translated_query,
        }

    def compile(self):
        """Compile the RAG workflow."""
        workflow = StateGraph(GraphState)

        # Add nodes
        workflow.add_node("query_validator", self.query_validator)
        workflow.add_node("retriever", self.retriever_node)
        workflow.add_node("generate", self.generate)

        # Build graph
        workflow.add_edge(START, "query_validator")
        workflow.add_edge("query_validator", "retriever")
        workflow.add_edge("retriever", "generate")
        workflow.add_edge("generate", END)

        # Compile and return
        return workflow.compile()
```

**Step 3: Use the Pipeline**

```python
# Usage example
from modules.custom_rag.pipeline import CustomRAGPipeline
from langchain_huggingface.embeddings import HuggingFaceEmbeddings

# Load embeddings
embed_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# Initialize pipeline
pipeline = CustomRAGPipeline(
    documents=loaded_documents,
    collection_name="custom_collection",
    embed_function=embed_model,
    persist_directory="./data/chromadb"
)

# Compile and invoke
rag_chain = pipeline.compile()
response = rag_chain.invoke(
    {"question": "What is the platform architecture?"},
    config={
        "callbacks": [opik_tracer],
        "task": "Custom_RAG"
    }
)

print(response["generation"])
```

## Vector Database Operations

### ChromaDB Management

**Creating Collections**

```python
from modules.extractive_qa.vector_db.chroma_vector import ExtendedChroma
from langchain_huggingface.embeddings import HuggingFaceEmbeddings

# Initialize embeddings
embed_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    cache_folder="./models/embeddings"
)

# Create new collection from documents
vector_store = ExtendedChroma.from_documents(
    documents=documents,
    embedding=embed_model,
    collection_name="new_collection",
    persist_directory="./data/chromadb",
    delete_and_recreate_collection=True  # Delete if exists
)

# Or load existing collection
vector_store = ExtendedChroma(
    embed_function=embed_model,
    collection_name="existing_collection",
    persist_directory="./data/chromadb",
    delete_and_recreate_collection=False
)
```

**Querying Collections**

```python
# Similarity search
results = vector_store.similarity_search(
    query="What are the key features?",
    k=5,
    filter={"source": "documentation"}
)

# Get retriever
retriever = vector_store.as_retriever(
    search_type="similarity",
    search_kwargs={
        "k": 10,
        "filter": {"mode": "faq"}
    }
)

# Use retriever
docs = retriever.invoke("How to deploy the platform?")
```

**Advanced Retrieval with Re-ranking**

```python
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from modules.extractive_qa.doc_retriever.document_retriever import Retriever

# Load re-ranker model
reranker_model = HuggingFaceCrossEncoder(
    model_name="cross-encoder/ms-marco-MiniLM-L-6-v2",
    model_kwargs={"cache_dir": "./models/reranker"}
)

# Create retriever with re-ranking
retriever_class = Retriever(
    vector_store=vector_store,
    search_type="similarity",
    search_kwargs={"k": 10}
)

reranked_retriever = retriever_class.reranker_retriever(
    reranker_model=reranker_model,
    top_n=5
)

# Retrieve and re-rank
final_docs = reranked_retriever.invoke("What is the deployment process?")
```

## Document Processing

### Loading Multi-Format Documents

```python
# modules/extractive_qa/loader/document_loader.py
import pandas as pd
from langchain_core.documents import Document

class DocLoader:
    def __init__(self, dataframe: pd.DataFrame, folder_path: str, depth: int = 2):
        self.df = dataframe
        self.folder_path = folder_path
        self.depth = depth

    def load(self, similarity_threshold: float = 0.5, content_type: str = "html"):
        """
        Load documents from various sources.

        Args:
            similarity_threshold: Deduplication threshold
            content_type: Type of content (html, pdf, txt)

        Returns:
            List[Document]: Loaded documents
        """
        documents = []

        for idx, row in self.df.iterrows():
            if content_type == "html":
                docs = self.load_html(row['url'])
            elif content_type == "pdf":
                docs = self.load_pdf(row['file_path'])
            else:
                docs = self.load_text(row['file_path'])

            documents.extend(docs)

        # Deduplicate
        unique_docs = self.deduplicate_documents(
            documents,
            similarity_threshold
        )

        return unique_docs

    def load_additional_info(self, additional_path: str):
        """Load supplementary documents."""
        # Implementation for loading additional data
        pass
```

### HTML Parsing with BeautifulSoup

```python
# modules/extractive_qa/loader/bs_html_parser.py
from bs4 import BeautifulSoup
from langchain_core.documents import Document

def parse_html_to_documents(html_content: str, url: str) -> List[Document]:
    """
    Parse HTML content and extract structured information.

    Args:
        html_content: Raw HTML string
        url: Source URL for metadata

    Returns:
        List[Document]: Parsed documents with metadata
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    documents = []

    # Remove unwanted elements
    for element in soup.find_all(['script', 'style', 'nav', 'footer']):
        element.decompose()

    # Extract main content
    main_content = soup.find('main') or soup.find('article') or soup.body

    if main_content:
        # Split by sections
        sections = main_content.find_all(['section', 'div'], class_=['content'])

        for section in sections:
            text = section.get_text(separator='\n', strip=True)

            if len(text) > 100:  # Filter short sections
                doc = Document(
                    page_content=text,
                    metadata={
                        "source": url,
                        "type": "html",
                        "section": section.get('id', 'unknown')
                    }
                )
                documents.append(doc)

    return documents
```

### Document Chunking and Transformation

```python
# modules/extractive_qa/loader/document_transformer.py
from langchain.text_splitter import RecursiveCharacterTextSplitter

class DocumentTransformer:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

    def transform(self, documents: List[Document]) -> List[Document]:
        """
        Split documents into chunks.

        Args:
            documents: List of documents to split

        Returns:
            List[Document]: Chunked documents
        """
        chunks = []

        for doc in documents:
            # Split document
            doc_chunks = self.text_splitter.split_documents([doc])

            # Add chunk metadata
            for idx, chunk in enumerate(doc_chunks):
                chunk.metadata['chunk_id'] = idx
                chunk.metadata['total_chunks'] = len(doc_chunks)

            chunks.extend(doc_chunks)

        return chunks
```

## Prompt Engineering

### Prompt Template Management

**Creating Pydantic Models for Structured Output**

```python
# prompt_engineering/template/pulse_templates.py
from pydantic import BaseModel, Field
from typing import List

class CourseInfo(BaseModel):
    Course: List[str] = Field(description="List of recommended courses")
    Matching_Score: List[int] = Field(description="Scores 0-100 for each course")
    Justification: List[str] = Field(description="Reasoning for each recommendation")

class LearnerProfile(BaseModel):
    Learner_Name: str = Field(description="Name of the learner")
    courses_info: CourseInfo = Field(description="Course recommendations")
```

**Defining Prompt Templates**

```yaml
# prompt_engineering/prompt/pulse_prompts.yaml
pulse_prompt: |
  You are an expert educational advisor. Analyze the student profile and match them with suitable courses.

  Student Profile:
  {student_details}

  Available Courses:
  {course_info}

  Instructions:
  1. Analyze the student's background, interests, and goals
  2. Match them with the most suitable courses (top 5)
  3. Provide matching scores (0-100) based on relevance
  4. Justify your recommendations

  {format_instruction}

query_validator: |
  You are a query optimization expert. Refine the following user query to be more specific and search-friendly.

  Original Query: {question}

  Return only the refined query without explanation.

rag_prompt: |
  Answer the question based ONLY on the provided context. If the answer cannot be found in the context, respond with "I don't know."

  Context:
  {context}

  Question: {question}

  Answer:
```

**Using Prompts in Code**

```python
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

# Load prompts
prompts = self.load_yaml_data("prompt_engineering/prompt/pulse_prompts.yaml")

# Create parser for structured output
parser = JsonOutputParser(pydantic_object=LearnerProfile)

# Create prompt template
prompt = PromptTemplate(
    template=prompts["pulse_prompt"],
    input_variables=["student_details", "course_info"],
    partial_variables={"format_instruction": parser.get_format_instructions()}
)

# Create chain
chain = prompt | self.llm | parser

# Invoke
result = chain.invoke({
    "student_details": student_data,
    "course_info": course_catalog
})
```

## Monitoring and Observability

### Opik Integration

**Setup Opik Tracer**

```python
# utils/utils.py
import opik
from opik.integrations.langchain import OpikTracer

def setup_opik_tracer(self):
    """Configure Opik for LLM monitoring."""
    opik.configure(
        use_local=True,
        url=self.config_data["utils_params"]["opik_host"]
    )

    self.opik_tracer = OpikTracer(
        project_name=self.utils_params["opik_project_name"]
    )
```

**Using Opik in Chains**

```python
# Track LLM calls
response = self.llm.invoke(
    prompt,
    config={
        "callbacks": [self.opik_tracer],
        "task": "Profile_Matching",
        "metadata": {
            "user_id": user_id,
            "session_id": session_id
        }
    }
)

# Track RAG pipeline
response = self.rag_chain.invoke(
    {"question": query},
    config={
        "callbacks": [self.opik_tracer],
        "collection_name": collection_name,
        "task": "Extractive_QA"
    }
)
```

**Custom Tracking**

```python
from opik import track

@track(name="custom_processing", project_name="platform")
def process_document(doc_path: str):
    """Custom function with tracking."""
    # Processing logic
    result = perform_analysis(doc_path)
    return result
```

## Logging Best Practices

### Structured Logging

```python
# utils/log_writer.py
import logging
import json

class StructuredLogger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        # JSON formatter
        formatter = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
            '"module": "%(name)s", "message": "%(message)s", '
            '"extra": %(extra)s}'
        )

        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def log_with_context(self, level: str, message: str, **kwargs):
        """Log with additional context."""
        extra_data = json.dumps(kwargs)
        getattr(self.logger, level)(message, extra={'extra': extra_data})
```

**Usage in Modules**

```python
try:
    result = process_data(input_data)
except Exception as e:
    exc_type, exc_obj, exc_tb = sys.exc_info()
    self.logger.error(
        str(e),
        extra={
            "error_type": exc_type.__name__,
            "error": str(exc_obj),
            "message": str(e),
            "line_number": exc_tb.tb_lineno,
            "function": exc_tb.tb_frame.f_code.co_name
        }
    )
    raise Exception(e)
```

## Deployment Guide

### Local Development Setup

```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set environment variables
export OPENAI_API_KEY="your-api-key"
export usr="api_username"
export pwd="api_password"

# 4. Start API server
python api.py

# 5. Start Streamlit UI (separate terminal)
streamlit run app.py
```

### Docker Deployment

**Dockerfile**

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create directories
RUN mkdir -p data/chromadb models/embeddings models/reranker

# Expose port
EXPOSE 5003

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5003/test || exit 1

# Run application
CMD ["python", "api.py"]
```

**docker-compose.yml**

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "5003:5003"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - usr=${API_USERNAME}
      - pwd=${API_PASSWORD}
    volumes:
      - ./data:/app/data
      - ./models:/app/models
      - ./logs:/app/logs
    restart: unless-stopped
    networks:
      - ml-platform

  streamlit:
    build:
      context: .
      dockerfile: Dockerfile.streamlit
    ports:
      - "8501:8501"
    environment:
      - usr=${API_USERNAME}
      - pwd=${API_PASSWORD}
    depends_on:
      - api
    networks:
      - ml-platform

  opik:
    image: comet-ml/opik:latest
    ports:
      - "5173:5173"
    volumes:
      - opik-data:/app/data
    networks:
      - ml-platform

networks:
  ml-platform:
    driver: bridge

volumes:
  opik-data:
```

### Production Deployment Checklist

- [ ] Set strong authentication credentials
- [ ] Configure HTTPS/TLS certificates
- [ ] Set up reverse proxy (nginx/traefik)
- [ ] Configure rate limiting
- [ ] Set up monitoring and alerting
- [ ] Configure log aggregation
- [ ] Set up automated backups (ChromaDB, models)
- [ ] Configure secrets management (Vault, AWS Secrets Manager)
- [ ] Set up CI/CD pipeline
- [ ] Configure auto-scaling policies
- [ ] Set up health checks and liveness probes
- [ ] Configure resource limits (CPU, memory)
- [ ] Set up disaster recovery plan

## Performance Optimization

### Vector Database Optimization

```python
# Batch processing for large datasets
from chromadb.utils.batch_utils import create_batches

def batch_add_documents(vector_store, documents, batch_size=100):
    """Add documents in batches for better performance."""
    texts = [doc.page_content for doc in documents]
    metadatas = [doc.metadata for doc in documents]

    for batch in create_batches(
        api=vector_store._client,
        ids=[str(uuid.uuid4()) for _ in texts],
        metadatas=metadatas,
        documents=texts,
    ):
        vector_store.add_texts(
            texts=batch[3] if batch[3] else [],
            metadatas=batch[2] if batch[2] else None,
            ids=batch[0]
        )
```

### Caching Strategies

```python
from functools import lru_cache
import hashlib

class CachedRetriever:
    def __init__(self, retriever):
        self.retriever = retriever
        self.cache = {}

    def get_cache_key(self, query: str) -> str:
        """Generate cache key from query."""
        return hashlib.md5(query.encode()).hexdigest()

    def retrieve(self, query: str):
        """Retrieve with caching."""
        cache_key = self.get_cache_key(query)

        if cache_key in self.cache:
            print("---CACHE HIT---")
            return self.cache[cache_key]

        print("---CACHE MISS---")
        results = self.retriever.invoke(query)
        self.cache[cache_key] = results

        return results
```

### Model Loading Optimization

```python
class ModelManager:
    """Singleton pattern for model management."""
    _instance = None
    _models = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load_model(self, model_name: str, model_type: str):
        """Load model once and reuse."""
        cache_key = f"{model_type}_{model_name}"

        if cache_key not in self._models:
            if model_type == "embedding":
                self._models[cache_key] = HuggingFaceEmbeddings(
                    model_name=model_name,
                    cache_folder="./models/embeddings"
                )
            elif model_type == "reranker":
                self._models[cache_key] = HuggingFaceCrossEncoder(
                    model_name=model_name
                )

        return self._models[cache_key]
```

## Debugging and Troubleshooting

### Common Issues and Solutions

**Issue: OpenAI Authentication Error**

```python
# Check API key
import openai
import os

try:
    openai.api_key = os.getenv("OPENAI_API_KEY")
    openai.models.list()
    print("✓ OpenAI API key is valid")
except Exception as e:
    print(f"✗ OpenAI Authentication Error: {e}")
    print("Please check your API key in environment variables")
```

**Issue: ChromaDB Collection Not Found**

```python
# List available collections
import chromadb

client = chromadb.PersistentClient(path="./data/chromadb")
collections = client.list_collections()
print("Available collections:", [c.name for c in collections])

# Create collection if missing
if "collection_name" not in [c.name for c in collections]:
    print("Creating missing collection...")
    # Re-run document ingestion
```

**Issue: Service Unavailable (503)**

```python
# Check service health
import requests

def check_service_health(host: str, port: int):
    """Verify service is running."""
    try:
        response = requests.get(f"http://{host}:{port}/test")
        if response.status_code == 200:
            print("✓ Service is healthy")
            return True
        else:
            print(f"✗ Service returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Service is not reachable: {e}")
        return False

check_service_health("localhost", 5003)
```

### Debugging Tools

```python
# Enable verbose logging
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Debug LangChain chains
from langchain.globals import set_debug, set_verbose

set_debug(True)
set_verbose(True)

# Inspect RAG pipeline state
def debug_rag_state(state: dict):
    """Print RAG pipeline state for debugging."""
    print("\n=== RAG State Debug ===")
    print(f"Question: {state.get('question')}")
    print(f"Translated Query: {state.get('translated_query')}")
    print(f"Documents Retrieved: {len(state.get('documents', []))}")
    print(f"Generation: {state.get('generation')[:200]}...")
    print("=" * 40 + "\n")
```

## Testing Strategies

### Unit Testing

```python
# tests/test_modules.py
import pytest
from modules.talend_pulse.talend_pulse import TalendPulse

class TestTalendPulse:
    @pytest.fixture
    def pulse_module(self):
        """Create TalendPulse instance for testing."""
        return TalendPulse()

    def test_load_course_files(self, pulse_module):
        """Test course file loading."""
        course_info = pulse_module.load_course_files()
        assert isinstance(course_info, str)
        assert len(course_info) > 0

    def test_get_structured_output(self, pulse_module):
        """Test structured output generation."""
        test_data = {
            "Learner_Name": "Test Student",
            "courses_info": {
                "Course": ["Python Programming", "Data Science"],
                "Matching_Score": [95, 88],
                "Justification": ["Strong match", "Good fit"]
            }
        }

        df = pulse_module.get_structured_output(test_data)
        assert not df.empty
        assert "Course" in df.columns
        assert df["Matching_Score"].max() == 95
```

### Integration Testing

```python
# tests/test_api.py
import pytest
import requests
import os

class TestAPI:
    BASE_URL = "http://localhost:5003"
    AUTH = (os.environ['usr'], os.environ['pwd'])

    def test_health_endpoint(self):
        """Test health check endpoint."""
        response = requests.get(f"{self.BASE_URL}/test")
        assert response.status_code == 200
        assert response.json()["result"] == "Hi, Welcome."

    def test_chat_endpoint(self):
        """Test chat endpoint."""
        payload = {"query": "What is the platform architecture?"}
        response = requests.post(
            f"{self.BASE_URL}/chat_with_ai",
            json=payload,
            auth=self.AUTH
        )
        assert response.status_code == 200
        assert "response" in response.json()

    def test_authentication_required(self):
        """Test authentication is enforced."""
        payload = {"query": "test query"}
        response = requests.post(
            f"{self.BASE_URL}/chat_with_ai",
            json=payload
        )
        assert response.status_code == 401
```

## Security Best Practices

### Environment Variables Management

```python
# config/env_template.py
"""
Template for environment variables.
Copy to .env and fill with actual values.
"""

REQUIRED_ENV_VARS = {
    "OPENAI_API_KEY": "Your OpenAI API key",
    "usr": "API username for authentication",
    "pwd": "API password for authentication",
    "OPIK_HOST": "Opik monitoring host URL (optional)",
}

def validate_environment():
    """Validate all required environment variables are set."""
    import os
    missing_vars = []

    for var, description in REQUIRED_ENV_VARS.items():
        if not os.getenv(var):
            missing_vars.append(f"{var}: {description}")

    if missing_vars:
        raise EnvironmentError(
            "Missing required environment variables:\n" +
            "\n".join(missing_vars)
        )

    print("✓ All required environment variables are set")
```

### Input Validation

```python
from pydantic import BaseModel, Field, validator

class SecurePayload(BaseModel):
    query: str = Field(..., min_length=1, max_length=5000)

    @validator('query')
    def sanitize_query(cls, v):
        """Sanitize user input."""
        # Remove potential injection attacks
        forbidden_patterns = ['<script', 'javascript:', 'onerror=']
        for pattern in forbidden_patterns:
            if pattern.lower() in v.lower():
                raise ValueError(f"Forbidden pattern detected: {pattern}")
        return v.strip()
```

### Rate Limiting

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["100 per hour", "20 per minute"]
)

@app.route('/chat_with_ai', methods=['POST'])
@limiter.limit("10 per minute")
@auth.login_required
def ai_extractor():
    # Endpoint logic
    pass
```

## Advanced Patterns

### Multi-Model Ensemble

```python
class EnsembleRAG:
    """Ensemble multiple models for better results."""

    def __init__(self, models: List[str]):
        self.models = [
            init_chat_model(model=m, model_provider="openai")
            for m in models
        ]

    def ensemble_generate(self, prompt: str):
        """Generate responses from all models and combine."""
        responses = []

        for model in self.models:
            response = model.invoke(prompt)
            responses.append(response.content)

        # Combine using a meta-model or voting
        final_response = self.combine_responses(responses)
        return final_response

    def combine_responses(self, responses: List[str]) -> str:
        """Combine multiple responses intelligently."""
        # Use another LLM to synthesize best answer
        synthesis_prompt = f"""
        Multiple AI models provided these answers:
        {chr(10).join(f"{i+1}. {r}" for i, r in enumerate(responses))}

        Synthesize the best answer combining insights from all responses.
        """
        meta_model = self.models[0]
        return meta_model.invoke(synthesis_prompt).content
```

### Async Processing

```python
import asyncio
from typing import List

class AsyncPipeline:
    """Asynchronous processing pipeline."""

    async def async_retrieve(self, queries: List[str]):
        """Retrieve documents for multiple queries concurrently."""
        tasks = [
            self.retriever.ainvoke(query)
            for query in queries
        ]
        results = await asyncio.gather(*tasks)
        return results

    async def async_generate(self, contexts: List[str], questions: List[str]):
        """Generate answers concurrently."""
        tasks = [
            self.llm.ainvoke({"context": ctx, "question": q})
            for ctx, q in zip(contexts, questions)
        ]
        results = await asyncio.gather(*tasks)
        return results
```

## When to Use This Skill

Use this skill when you need help with:

1. **Architecture & Design**: Understanding platform components and data flow
2. **API Development**: Adding new endpoints or modifying existing ones
3. **Module Creation**: Building new processing modules (NER, QA, custom parsers)
4. **RAG Implementation**: Creating or customizing RAG pipelines
5. **Vector Database**: Managing ChromaDB collections and retrieval
6. **Document Processing**: Loading, parsing, and transforming documents
7. **Prompt Engineering**: Creating and managing prompt templates
8. **Deployment**: Local, Docker, or cloud deployment strategies
9. **Monitoring**: Implementing Opik tracking and logging
10. **Debugging**: Troubleshooting common platform issues
11. **Performance**: Optimizing retrieval, caching, and model loading
12. **Security**: Authentication, validation, and secure practices
13. **Testing**: Unit and integration testing strategies

## Key Files Reference

- **API Layer**: `api.py`, `app.py`
- **Modules**: `modules/extractive_qa/`, `modules/talend_pulse/`
- **Vector DB**: `modules/extractive_qa/vector_db/chroma_vector.py`
- **Pipeline**: `modules/extractive_qa/agentic_pipeline.py`
- **Config**: `config/common_config.yaml`, `config/rag_config.yaml`
- **Utils**: `utils/utils.py`, `utils/config_reader.py`, `utils/log_writer.py`
- **Prompts**: `prompt_engineering/prompt/*.yaml`

## Next Steps

When helping users, always:

1. Understand their specific use case
2. Reference relevant code examples from the platform
3. Provide complete, production-ready code
4. Include error handling and logging
5. Add monitoring with Opik
6. Follow security best practices
7. Include testing examples
8. Explain architectural implications

Remember: This is a production platform. All code must be enterprise-grade with proper error handling, logging, monitoring, and security.
