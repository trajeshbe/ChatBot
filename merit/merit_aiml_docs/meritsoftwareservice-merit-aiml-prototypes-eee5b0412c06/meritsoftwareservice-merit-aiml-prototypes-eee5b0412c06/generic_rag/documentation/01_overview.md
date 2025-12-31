# Generic RAG Prototype - Overview

## Table of Contents
1. [Introduction](#introduction)
2. [Purpose](#purpose)
3. [Key Features](#key-features)
4. [System Architecture](#system-architecture)
5. [Technology Stack](#technology-stack)
6. [Use Cases](#use-cases)
7. [Project Structure](#project-structure)

## Introduction

The Generic RAG (Retrieval-Augmented Generation) prototype is an advanced document question-answering system built with Streamlit. It leverages state-of-the-art natural language processing and machine learning techniques to enable users to upload PDF documents and interact with them through conversational AI.

This prototype implements a sophisticated RAG pipeline that combines:
- Document ingestion and processing
- Vector embeddings for semantic search
- Cross-encoder reranking for improved retrieval accuracy
- Large Language Models (LLMs) for natural language generation
- Conversational memory for context-aware interactions

## Purpose

The Generic RAG prototype serves as a flexible, production-ready framework for building intelligent document Q&A systems. It is designed to:

1. **Extract Knowledge**: Enable users to extract specific information from PDF documents without manual reading
2. **Provide Context-Aware Answers**: Deliver accurate, contextual responses based on document content
3. **Support Multiple LLM Providers**: Integrate with both HuggingFace and Groq API endpoints
4. **Handle Complex Documents**: Process documents with text and tables using advanced parsing techniques
5. **Maintain Conversation Context**: Remember previous interactions for coherent multi-turn conversations

## Key Features

### 1. Multi-Model Support
- Support for multiple LLM options from HuggingFace (Mistral, Mixtral) and Groq (Llama 3.1, Llama 3.2)
- Flexible model selection through dropdown interface
- Configurable model parameters (temperature, max tokens, top-k)

### 2. Advanced Document Processing
- **Standard PDF Processing**: Uses PyMuPDFLoader for text extraction
- **Table-Aware Processing**: Integrates LlamaParse for enhanced table extraction
- **Chunking Strategy**: Configurable chunk sizes with overlap for optimal retrieval
- **Parent Document Retrieval**: Maintains document hierarchy for better context

### 3. Intelligent Retrieval
- **Vector Database**: ChromaDB for persistent vector storage
- **Embedding Models**: Sentence-transformers for semantic embeddings
- **MMR (Maximal Marginal Relevance)**: Reduces redundancy in retrieved documents
- **Cross-Encoder Reranking**: BAAI/bge-reranker-base for precision improvement
- **Contextual Compression**: Reduces noise in retrieved content

### 4. User Experience
- **Streamlit Interface**: Clean, intuitive web-based UI
- **Tabbed Layout**: Separate tabs for document upload and chat
- **Streaming Responses**: Word-by-word response streaming for better UX
- **Source Citations**: Displays page numbers and content snippets from source documents
- **Conversation History**: Maintains chat history within session

### 5. Production Features
- **Error Handling**: Comprehensive exception handling with detailed logging
- **Session Management**: Streamlit session state for user isolation
- **Model Caching**: Cached model loading for performance optimization
- **Configurable Settings**: INI-based configuration for easy deployment

## System Architecture

### High-Level Architecture

```
┌─────────────────┐
│   Streamlit UI  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│      GenericRAG Class           │
│  ┌──────────────────────────┐   │
│  │  Document Processing     │   │
│  │  - PyMuPDFLoader        │   │
│  │  - LlamaParse           │   │
│  │  - Text Splitter        │   │
│  └──────────────────────────┘   │
│                                 │
│  ┌──────────────────────────┐   │
│  │  Vector Store           │   │
│  │  - ChromaDB             │   │
│  │  - Embeddings           │   │
│  │  - MMR Retrieval        │   │
│  └──────────────────────────┘   │
│                                 │
│  ┌──────────────────────────┐   │
│  │  LLM Chain              │   │
│  │  - Retriever            │   │
│  │  - Reranker             │   │
│  │  - LLM (HF/Groq)        │   │
│  │  - Memory               │   │
│  └──────────────────────────┘   │
└─────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│   External Services             │
│  - HuggingFace API              │
│  - Groq API                     │
│  - LlamaParse API               │
└─────────────────────────────────┘
```

### Data Flow

1. **Document Upload**: User uploads PDF through Streamlit interface
2. **Document Processing**:
   - File saved to input directory
   - PDF parsed using PyMuPDFLoader or LlamaParse (for tables)
   - Text split into chunks with configurable size
3. **Indexing**:
   - Chunks embedded using sentence-transformers
   - Vectors stored in ChromaDB with metadata
4. **Query Processing**:
   - User query embedded
   - MMR retrieval fetches top-10 relevant chunks
   - Cross-encoder reranks to top-3
   - Contextual compression filters noise
5. **Response Generation**:
   - LLM generates answer based on retrieved context
   - Source documents attached to response
   - Answer streamed to user with citations

## Technology Stack

### Core Framework
- **Streamlit**: Web application framework for the UI
- **LangChain**: Orchestration framework for RAG pipeline
- **Python 3.x**: Primary programming language

### Document Processing
- **PyMuPDF (fitz)**: PDF text extraction
- **LlamaParse**: Advanced PDF parsing with table support
- **RecursiveCharacterTextSplitter**: Text chunking

### Vector Store & Retrieval
- **ChromaDB**: Vector database for embeddings storage
- **Sentence-Transformers**: Embedding models (all-MiniLM-L6-v2)
- **BAAI/bge-reranker-base**: Cross-encoder reranking

### Language Models
- **HuggingFace Inference API**:
  - mistralai/Mistral-7B-Instruct-v0.1
  - mistralai/Mistral-7B-Instruct-v0.2
  - mistralai/Mixtral-8x7B-Instruct-v0.1
- **Groq API**:
  - llama-3.1-70b-versatile
  - llama-3.2-11b-vision-preview
  - mixtral-8x7b-32768

### Supporting Libraries
- **ConfigParser**: Configuration management
- **Logging**: Error tracking and debugging
- **ChromaDB**: Persistent client for vector storage

## Use Cases

### 1. Legal Document Analysis
Extract key information from contracts, agreements, and legal documents with precise source citations.

### 2. Research Paper Q&A
Query academic papers and research documents to quickly find specific methodologies, results, or references.

### 3. Technical Documentation Assistant
Navigate complex technical manuals, API documentation, or system specifications.

### 4. Financial Report Analysis
Extract insights from financial statements, annual reports, and regulatory filings, including tabular data.

### 5. Policy & Compliance Review
Search and analyze policy documents, compliance guidelines, and regulatory frameworks.

### 6. Medical Literature Review
Query medical literature, clinical guidelines, and research papers for evidence-based information.

## Project Structure

```
generic_rag/
├── rag.py                  # Main application (deprecated/legacy)
├── rag_table.py            # Enhanced version with table support (current)
├── utils.py                # Utility classes (logging, config)
├── config.ini              # Configuration file (API keys, model settings)
├── requirements.txt        # Python dependencies
├── documentation/          # Documentation folder
│   ├── 01_overview.md
│   ├── 02_installation_setup.md
│   ├── 03_architecture_design.md
│   ├── 04_api_reference.md
│   └── 05_user_guide.md
├── input/                  # Uploaded PDF files (created at runtime)
├── DB/                     # ChromaDB vector store (created at runtime)
└── logs/                   # Application logs (created at runtime)
```

## Version Information

- **Current Version**: 2.0 (rag_table.py)
- **Legacy Version**: 1.0 (rag.py)
- **Framework**: LangChain v0.2.x
- **Python**: 3.x compatible
- **Last Updated**: 2024

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Configure API keys in config.ini
# [default]
# hf_key = your_huggingface_key
# llama_parser_key = your_llama_parse_key
# groq_key = your_groq_key

# Run application
streamlit run rag_table.py
```

## License & Attribution

This prototype is part of the Merit AI/ML prototypes collection developed for KIAA projects. It demonstrates best practices in RAG system implementation and serves as a foundation for production deployments.

---

**Document Version**: 1.0
**Last Updated**: December 2024
**Maintained By**: Merit Software Services
