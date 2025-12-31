# Generic RAG Prototype - Documentation

## Overview

This documentation folder contains comprehensive guides for the Generic RAG (Retrieval-Augmented Generation) prototype - an advanced document question-answering system built with Streamlit, LangChain, and multiple LLM providers.

## Documentation Structure

The documentation is organized into five main documents, designed to be read in sequence for new users or accessed independently as reference material.

### 1. Overview ([01_overview.md](01_overview.md))

**Target Audience**: Everyone - developers, users, stakeholders

**Contents**:
- Introduction to the Generic RAG prototype
- Purpose and key features
- System architecture overview
- Technology stack
- Use cases and applications
- Project structure
- Quick start guide

**Read this first if**:
- You're new to the project
- You want to understand what the system does
- You need a high-level overview
- You're evaluating the prototype for your needs

---

### 2. Installation & Setup Guide ([02_installation_setup.md](02_installation_setup.md))

**Target Audience**: Developers, system administrators, technical users

**Contents**:
- Prerequisites and system requirements
- Step-by-step installation instructions
- Configuration guide
- API keys setup (HuggingFace, Groq, LlamaParse)
- Directory structure setup
- Troubleshooting common installation issues
- Verification procedures

**Read this if**:
- You're setting up the application for the first time
- You're encountering installation problems
- You need to configure API keys
- You're deploying to a new environment

---

### 3. Architecture & Design ([03_architecture_design.md](03_architecture_design.md))

**Target Audience**: Developers, architects, advanced technical users

**Contents**:
- Detailed system architecture
- Component design and responsibilities
- Data flow diagrams
- RAG pipeline explanation (standard and table-aware)
- Class hierarchy and relationships
- Design patterns used
- Database schema
- API integration details
- Performance considerations and optimization

**Read this if**:
- You're extending or modifying the codebase
- You need to understand the internal workings
- You're optimizing performance
- You're integrating with other systems
- You're troubleshooting complex issues

---

### 4. API Reference ([04_api_reference.md](04_api_reference.md))

**Target Audience**: Developers, technical integrators

**Contents**:
- Complete API documentation for all classes
- Method signatures with parameters and return types
- Code examples for each method
- Session state variables reference
- Configuration parameters documentation
- External API specifications
- Usage examples

**Read this if**:
- You're developing custom features
- You need detailed method documentation
- You're integrating the prototype into another application
- You're debugging specific functions
- You need to understand configuration options

---

### 5. User Guide ([05_user_guide.md](05_user_guide.md))

**Target Audience**: End users, non-technical users, new users

**Contents**:
- Getting started tutorial
- Document upload guide
- LLM model selection guide
- How to ask effective questions
- Understanding responses and citations
- Advanced features (table processing, conversation memory)
- Best practices
- Troubleshooting common issues
- Use case examples
- FAQ

**Read this if**:
- You're using the application for the first time
- You want to improve your question-asking skills
- You need to process documents with tables
- You're encountering user-facing issues
- You want to see example workflows

---

## Quick Navigation

### For New Users
1. Start with [01_overview.md](01_overview.md)
2. Follow [02_installation_setup.md](02_installation_setup.md) to set up
3. Use [05_user_guide.md](05_user_guide.md) to start using the application

### For Developers
1. Read [01_overview.md](01_overview.md) for context
2. Study [03_architecture_design.md](03_architecture_design.md) for system design
3. Reference [04_api_reference.md](04_api_reference.md) while coding

### For System Administrators
1. Review [01_overview.md](01_overview.md) for requirements
2. Follow [02_installation_setup.md](02_installation_setup.md) for deployment
3. Consult [03_architecture_design.md](03_architecture_design.md) for scaling

### For Troubleshooting
1. Check relevant section in [02_installation_setup.md](02_installation_setup.md) for setup issues
2. See [05_user_guide.md](05_user_guide.md) for user-facing problems
3. Review [03_architecture_design.md](03_architecture_design.md) for technical issues

---

## Document Conventions

### Code Examples
All code examples are syntax-highlighted and include context:

```python
# Example code with comments
obj = GenericRAG()
obj.render_UI()
```

### Command Line Examples
Commands are shown with expected output:

```bash
# Command description
command --with-flags

# Expected output
Output shown here
```

### Configuration Examples
Configuration snippets show actual file content:

```ini
[default]
hf_key = your_key_here
llm_temperature = 0.1
```

### Diagrams
ASCII diagrams illustrate architecture and flow:

```
Component A → Component B → Component C
```

---

## Key Features Documented

### Core Functionality
- PDF document upload and processing
- Multiple LLM provider support (HuggingFace, Groq)
- Vector database (ChromaDB) for semantic search
- Cross-encoder reranking for precision
- Conversational memory
- Source citation with page numbers

### Advanced Features
- Table-aware processing with LlamaParse
- Parent-child document retrieval
- MMR (Maximal Marginal Relevance) search
- Contextual compression
- Streaming responses
- Model caching

### Developer Features
- Comprehensive error handling
- Structured logging
- Session state management
- Configuration-driven setup
- Extensible class hierarchy

---

## Technology Stack

### Primary Technologies
- **Streamlit**: Web interface framework
- **LangChain**: RAG pipeline orchestration
- **ChromaDB**: Vector database
- **PyMuPDF**: PDF text extraction
- **LlamaParse**: Advanced PDF parsing

### ML/AI Components
- **Sentence-Transformers**: Embedding generation
- **HuggingFace Models**: LLM inference
- **Groq API**: Fast LLM inference
- **Cross-Encoders**: Document reranking

### Supporting Libraries
- Python 3.8+
- ConfigParser, logging, sys, os
- See requirements.txt for complete list

---

## Version Information

**Documentation Version**: 1.0
**Last Updated**: December 2024
**Prototype Version**: 2.0 (rag_table.py)
**Maintained By**: Merit Software Services

---

## Document Maintenance

### Keeping Documentation Updated

When making changes to the codebase:

1. **Update Relevant Documents**:
   - New features → Update 01_overview.md and 05_user_guide.md
   - Code changes → Update 04_api_reference.md
   - Architecture changes → Update 03_architecture_design.md
   - Setup changes → Update 02_installation_setup.md

2. **Version Control**:
   - Increment document version numbers
   - Update "Last Updated" dates
   - Note breaking changes prominently

3. **Review Process**:
   - Test all code examples
   - Verify commands and outputs
   - Check links and cross-references
   - Ensure consistency across documents

---

## Getting Help

### Documentation Issues
If you find errors or gaps in the documentation:
1. Note the specific document and section
2. Describe the issue or confusion
3. Suggest improvements if possible

### Application Issues
Refer to:
- **Installation problems**: [02_installation_setup.md](02_installation_setup.md) - Troubleshooting section
- **Usage questions**: [05_user_guide.md](05_user_guide.md) - FAQ and Troubleshooting sections
- **Technical issues**: [03_architecture_design.md](03_architecture_design.md) - Error Handling section

### External Resources
- **LangChain**: https://python.langchain.com/docs/
- **Streamlit**: https://docs.streamlit.io/
- **ChromaDB**: https://docs.trychroma.com/
- **HuggingFace**: https://huggingface.co/docs

---

## Contributing to Documentation

### Style Guidelines
- Use clear, concise language
- Include practical examples
- Explain "why" not just "how"
- Use consistent formatting
- Add diagrams where helpful

### Structure Guidelines
- Use hierarchical headings (##, ###, ####)
- Include table of contents for long documents
- Cross-reference related sections
- Group related information logically

### Code Guidelines
- Test all code examples before documenting
- Include comments in complex code
- Show expected output
- Explain error cases

---

## License & Attribution

This documentation is part of the Generic RAG prototype developed by Merit Software Services for KIAA projects. All rights reserved.

---

## Document Index

| Document | File | Pages | Target Audience |
|----------|------|-------|-----------------|
| Overview | 01_overview.md | ~8 | Everyone |
| Installation & Setup | 02_installation_setup.md | ~12 | Technical users |
| Architecture & Design | 03_architecture_design.md | ~15 | Developers |
| API Reference | 04_api_reference.md | ~20 | Developers |
| User Guide | 05_user_guide.md | ~18 | End users |

**Total Documentation**: ~73 pages of comprehensive guides

---

**Happy Learning!**

For the best experience, read the documents in order if you're new to the project, or jump directly to the section you need if you're looking for specific information.
