# Generic RAG (Retrieval-Augmented Generation)

You are an AI assistant specialized in the **Generic RAG** prototype, an advanced document question-answering system built with Streamlit, LangChain, and multiple LLM providers.

## Project Overview

Generic RAG is a production-ready document Q&A system that uses Retrieval-Augmented Generation to answer questions based on PDF documents. It features multiple LLM providers (HuggingFace, Groq), vector database search, cross-encoder reranking, and optional table-aware processing.

**Location**: `/mnt/d/Data/Projects/KIAA/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/generic_rag/`

## Core Capabilities

### Standard RAG Features
- PDF document upload and processing
- Vector database (ChromaDB) for semantic search
- Cross-encoder reranking for precision
- Conversational memory
- Source citation with page numbers
- Multiple LLM providers (HuggingFace, Groq)

### Advanced Features (rag_table.py)
- Table-aware processing with LlamaParse
- Parent-child document retrieval
- MMR (Maximal Marginal Relevance) search
- Contextual compression
- Streaming responses
- Model caching

## Technology Stack

```
Framework: Streamlit
AI/ML: LangChain, ChromaDB, Sentence-Transformers
LLM Providers: HuggingFace Hub, Groq API
PDF Processing: PyMuPDF, LlamaParse
Embeddings: all-MiniLM-L6-v2 (sentence-transformers)
Reranking: Cross-encoders (ms-marco-MiniLM)
Configuration: ConfigParser
```

## Architecture

### Component Structure

```
rag.py                 # Standard RAG implementation
rag_table.py          # Table-aware RAG (advanced)
config.ini            # Configuration file
utils/
  ├── pdf_processor.py
  ├── vector_store.py
  └── llm_manager.py
```

### RAG Pipeline

```
PDF Upload
  ↓
Text Extraction (PyMuPDF or LlamaParse)
  ↓
Document Chunking
  ↓
Embedding Generation
  ↓
Vector Store (ChromaDB)
  ↓
User Question
  ↓
Similarity Search + MMR
  ↓
Cross-Encoder Reranking
  ↓
Context Assembly
  ↓
LLM Generation with Sources
```

## Common Implementation Tasks

### 1. Running the Application

```bash
cd /mnt/d/Data/Projects/KIAA/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/generic_rag/

# Install dependencies
pip install streamlit langchain chromadb sentence-transformers pypdf

# Configure API keys in config.ini
# [default]
# hf_key = your_huggingface_key
# groq_key = your_groq_key (optional)
# llama_parse_key = your_llama_parse_key (for table support)

# Run standard RAG
streamlit run rag.py

# Or run table-aware RAG
streamlit run rag_table.py
```

### 2. Configuration (config.ini)

```ini
[default]
# API Keys
hf_key = hf_xxxxxxxxxxxxx
groq_key = gsk_xxxxxxxxxxxxx
llama_parse_key = llx_xxxxxxxxxxxxx

# LLM Settings
llm_temperature = 0.1
max_tokens = 1000

# Retrieval Settings
chunk_size = 500
chunk_overlap = 100
top_k = 5
rerank_top_k = 3

# Embedding Model
embedding_model = sentence-transformers/all-MiniLM-L6-v2

# Vector Store
vector_db_path = ./chroma_db
```

### 3. Processing a Document and Asking Questions

```python
from generic_rag import GenericRAG

# Initialize RAG system
rag = GenericRAG()

# Upload and process PDF
pdf_path = "document.pdf"
rag.process_document(pdf_path)

# Ask questions
question = "What is the main topic of this document?"
answer = rag.ask_question(question)

# Answer includes:
{
    'answer': 'The main topic is...',
    'sources': [
        {'page': 5, 'content': '...'},
        {'page': 12, 'content': '...'}
    ],
    'confidence': 0.85
}
```

### 4. Using Different LLM Providers

```python
# HuggingFace Models
rag = GenericRAG(llm_provider='huggingface', model='mistralai/Mistral-7B-Instruct-v0.2')

# Groq API (faster inference)
rag = GenericRAG(llm_provider='groq', model='mixtral-8x7b-32768')

# OpenAI (if configured)
rag = GenericRAG(llm_provider='openai', model='gpt-4-turbo')
```

### 5. Table-Aware Document Processing

```python
from rag_table import TableAwareRAG

# Initialize with LlamaParse for table extraction
rag = TableAwareRAG(use_llamaparse=True)

# Process document with tables
rag.process_document_with_tables("financial_report.pdf")

# Ask questions about tables
question = "What was the revenue in Q3 2023?"
answer = rag.ask_question(question)
# Returns: "The revenue in Q3 2023 was $2.5M" (with table source)
```

## Advanced Features

### MMR Search (Diversity)

```python
# Maximal Marginal Relevance for diverse results
retriever = rag.vector_store.as_retriever(
    search_type="mmr",
    search_kwargs={
        "k": 5,  # Number of documents
        "fetch_k": 20,  # Candidates for MMR
        "lambda_mult": 0.7  # 0=diversity, 1=relevance
    }
)
```

### Cross-Encoder Reranking

```python
from sentence_transformers import CrossEncoder

# Rerank retrieved documents
reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

def rerank_documents(query, documents, top_k=3):
    """Rerank documents using cross-encoder"""

    # Score each document
    pairs = [[query, doc.page_content] for doc in documents]
    scores = reranker.predict(pairs)

    # Sort by score
    scored_docs = list(zip(documents, scores))
    scored_docs.sort(key=lambda x: x[1], reverse=True)

    # Return top K
    return [doc for doc, score in scored_docs[:top_k]]
```

### Conversational Memory

```python
from langchain.memory import ConversationBufferMemory

# Add conversation history
memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True
)

# Multi-turn conversation
rag.ask_question("What is the revenue?", memory=memory)
rag.ask_question("How does that compare to last year?", memory=memory)
# Second question uses context from first
```

### Streaming Responses

```python
def ask_with_streaming(question):
    """Stream LLM response token-by-token"""

    for chunk in rag.llm.stream(question):
        yield chunk.content
        # Display in Streamlit: st.write_stream(ask_with_streaming(q))
```

## Document Chunking Strategies

### Fixed-Size Chunking

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=100,
    separators=["\n\n", "\n", ". ", " ", ""]
)

chunks = splitter.split_text(document_text)
```

### Semantic Chunking

```python
from langchain.text_splitter import SemanticChunker

splitter = SemanticChunker(
    embeddings=embeddings_model,
    breakpoint_threshold_type="percentile",  # or "standard_deviation"
    breakpoint_threshold_amount=0.8
)

chunks = splitter.split_text(document_text)
```

### Parent-Child Retrieval

```python
# Create parent and child chunks
parent_splitter = RecursiveCharacterTextSplitter(chunk_size=2000)
child_splitter = RecursiveCharacterTextSplitter(chunk_size=400)

parent_docs = parent_splitter.split_documents(documents)
child_docs = []

for parent in parent_docs:
    children = child_splitter.split_documents([parent])
    for child in children:
        child.metadata['parent_id'] = parent.metadata['id']
        child_docs.append(child)

# Retrieve children, return parents for context
```

## Best Practices

### Document Preparation

1. **Clean PDFs**: Ensure text-searchable (not scanned images)
2. **OCR if Needed**: Pre-process scanned documents
3. **File Size**: Large PDFs (>100MB) may need splitting
4. **Quality**: Better source = better answers
5. **Metadata**: Include page numbers, sections

### Question Formulation

1. **Specific**: "What was Q3 revenue?" vs. "Tell me about revenue"
2. **Contextual**: Provide context if multi-turn
3. **One Topic**: Avoid multiple questions in one
4. **Clear**: Use precise terminology
5. **Answerable**: Ensure info exists in document

### Performance Optimization

1. **Chunk Size**: 300-700 tokens optimal
2. **Top K**: Start with 3-5 retrieval results
3. **Reranking**: Use for better precision
4. **Caching**: Cache embeddings and vector stores
5. **Model Selection**: Balance speed vs. accuracy

## Debugging Guide

### Common Issues

**Issue**: Low answer quality
```python
# Increase retrieval k
retriever = vector_store.as_retriever(search_kwargs={"k": 10})

# Add reranking
reranked = rerank_documents(query, retrieved_docs, top_k=3)

# Try different LLM
rag = GenericRAG(model='larger_model')
```

**Issue**: Slow processing
```python
# Use Groq for faster inference
rag = GenericRAG(llm_provider='groq')

# Reduce chunk size
splitter = RecursiveCharacterTextSplitter(chunk_size=300)

# Cache vector store
rag.save_vector_store('cached_db')
rag.load_vector_store('cached_db')  # On next run
```

**Issue**: Sources not accurate
```python
# Enable source tracking
rag.enable_source_tracking = True

# Use smaller chunks for precision
splitter = RecursiveCharacterTextSplitter(
    chunk_size=300,
    chunk_overlap=50
)
```

## Documentation References

**Comprehensive Documentation**: `/documentation/` folder
- `README.md`: Documentation index
- `01_overview.md`: System overview
- `02_installation_setup.md`: Setup guide
- `03_architecture_design.md`: Architecture details
- `04_api_reference.md`: API documentation
- `05_user_guide.md`: User guide

**Project Status**: Production-ready
**Last Updated**: December 2024
