# Merit ML Platform (Knowledge Agent) - Documentation

**Version**: 1.0.0
**Last Updated**: December 2024
**Platform Type**: Production-Ready Microservices AI/ML Platform

---

## Overview

This folder contains comprehensive documentation for the **Merit ML Platform (Knowledge Agent)**, an enterprise-grade distributed AI/ML platform providing Named Entity Recognition, Relation Extraction, Question Answering, and Resume Scoring capabilities through a unified Flask REST API with Redis Streams-based distributed processing.

---

## Documentation Structure

### 📋 [01_Platform_Overview.md](./01_Platform_Overview.md)
**Executive Summary & High-Level Architecture**

**Target Audience**: Executives, Product Managers, Architects

**Contents**:
- Platform capabilities and features
- Technology stack overview
- High-level architecture diagrams
- Use cases and target users
- Success metrics

**Read this first** to understand what the platform does and its business value.

---

### 🏗️ [02_Technical_Architecture.md](./02_Technical_Architecture.md)
**System Design & Implementation Details**

**Target Audience**: Software Engineers, DevOps, Architects

**Contents**:
- Detailed system architecture
- Redis Streams patterns and consumer groups
- Worker management and lifecycle
- Database design (SQLite, ChromaDB)
- Security architecture
- Performance characteristics
- Monitoring and observability

**Read this** to understand how the platform works internally and how to extend it.

---

### 📡 [03_API_Reference.md](./03_API_Reference.md)
**Complete API Documentation**

**Target Audience**: Application Developers, Integration Engineers

**Contents**:
- Authentication and authorization
- Endpoint specifications (NER, REL, QA, Talend Pulse)
- Request/response schemas
- Error handling
- Code examples (Python, cURL, JavaScript)
- Best practices

**Read this** to integrate with the platform via REST API.

---

### 🚀 [04_Deployment_Guide.md](./04_Deployment_Guide.md)
**Installation, Configuration & Operations**

**Target Audience**: DevOps Engineers, System Administrators

**Contents**:
- System requirements (hardware, software)
- Step-by-step installation instructions
- Configuration management
- Redis setup and tuning
- Worker deployment strategies
- Monitoring and health checks
- Troubleshooting guide
- Security hardening
- Backup and recovery procedures

**Read this** to deploy and operate the platform in production.

---

### 📖 [05_User_Guide.md](./05_User_Guide.md)
**How to Use Each API Endpoint with Examples**

**Target Audience**: End Users, Data Scientists, Business Analysts

**Contents**:
- Getting started guide
- Step-by-step tutorials for each module
- Real-world usage examples
- Best practices and tips
- Common use cases
- Troubleshooting common issues
- FAQ

**Read this** to learn how to use the platform effectively.

---

### 🔧 [06_Module_Documentation.md](./06_Module_Documentation.md)
**Detailed Module-Level Technical Documentation**

**Target Audience**: ML Engineers, Contributors, Advanced Users

**Contents**:
- NER module (GLiNER zero-shot entity extraction)
- Relation Extraction module (LLM-based)
- Extractive QA module (RAG with LangGraph)
- Profile Match module (Talend Pulse resume scoring)
- Custom Parser module (PDF-to-Markdown)
- Database module (SQLite operations)
- Utility modules

**Read this** to understand module internals, customize behavior, or contribute code.

---

### 💼 [07_Business_Value.md](./07_Business_Value.md)
**ROI Analysis, Use Cases & Competitive Advantages**

**Target Audience**: Executives, Business Leaders, Decision Makers

**Contents**:
- Business value proposition
- ROI analysis with real numbers
- Industry-specific use cases
- Competitive advantages
- Cost-benefit analysis
- Implementation roadmap
- Success metrics and KPIs
- Case studies

**Read this** to understand the business case and justify investment.

---

## Quick Start

### For Business Leaders
1. Read [01_Platform_Overview.md](./01_Platform_Overview.md) for high-level understanding
2. Read [07_Business_Value.md](./07_Business_Value.md) for ROI and business case
3. Review [05_User_Guide.md](./05_User_Guide.md) to see practical applications

### For Technical Decision Makers
1. Read [01_Platform_Overview.md](./01_Platform_Overview.md) for capabilities
2. Read [02_Technical_Architecture.md](./02_Technical_Architecture.md) for system design
3. Review [04_Deployment_Guide.md](./04_Deployment_Guide.md) for infrastructure requirements

### For Developers
1. Read [03_API_Reference.md](./03_API_Reference.md) for API documentation
2. Read [05_User_Guide.md](./05_User_Guide.md) for usage examples
3. Refer to [06_Module_Documentation.md](./06_Module_Documentation.md) as needed

### For DevOps/SRE
1. Read [04_Deployment_Guide.md](./04_Deployment_Guide.md) for deployment
2. Read [02_Technical_Architecture.md](./02_Technical_Architecture.md) for monitoring
3. Keep [04_Deployment_Guide.md](./04_Deployment_Guide.md) handy for troubleshooting

---

## Platform Capabilities Summary

### 1. Named Entity Recognition (NER)
- **Technology**: GLiNER (zero-shot learning)
- **Input**: PDF documents
- **Output**: Entities with types, spans, confidence scores
- **Use Cases**: Contract analysis, invoice processing, resume parsing

### 2. Relation Extraction (REL)
- **Technology**: OpenAI GPT-4o-mini
- **Input**: Text + entities
- **Output**: Relationship triples (head-relation-tail)
- **Use Cases**: Knowledge graphs, contract relationships, org charts

### 3. Extractive QA
- **Technology**: RAG (ChromaDB + BAAI embeddings + GPT-4o-mini)
- **Input**: Document collection + questions
- **Output**: Answers with source attribution
- **Use Cases**: Knowledge management, customer support, research

### 4. Talend Pulse (Resume Scoring)
- **Technology**: LLM-based skill matching
- **Input**: Job description + resumes
- **Output**: Scored candidates with justifications
- **Use Cases**: Recruitment automation, talent acquisition

### 5. Custom Parser
- **Technology**: Marker (PDF-to-Markdown) + semantic chunking
- **Input**: PDF documents
- **Output**: Structured Markdown with headers
- **Use Cases**: Document preprocessing for all modules

---

## Technology Stack

### Core Framework
- **Flask**: REST API server
- **Redis Streams**: Distributed task queue
- **SQLite**: Caching and persistence
- **Python 3.8+**: Core language

### AI/ML Stack
- **GLiNER**: Named Entity Recognition
- **OpenAI GPT-4o-mini**: Large Language Model
- **LangChain + LangGraph**: LLM orchestration
- **ChromaDB**: Vector database
- **BAAI/llm-embedder**: Embeddings (768-dim)
- **BAAI/bge-reranker-large**: Cross-encoder reranker

### Infrastructure
- **NVIDIA GPU**: CUDA acceleration for GLiNER
- **SFTP**: Document storage and retrieval
- **Opik**: LLM observability and monitoring
- **Systemd**: Service management (production)

---

## Architecture Highlights

### Distributed Processing
- **Redis Streams**: Asynchronous task queuing
- **Consumer Groups**: Load balancing across workers
- **Worker Pools**: Configurable parallelism per service
- **Dead Letter Queues**: Fault tolerance and retry logic

### Scalability
- **Horizontal Scaling**: Add workers to increase throughput
- **Caching**: SQLite and ChromaDB reduce redundant processing
- **Batch Processing**: Efficient multi-file handling
- **GPU Acceleration**: High-performance inference

### Security
- **HTTP Basic Authentication**: API access control
- **Environment Variables**: Credential management
- **Encryption**: HTTPS (recommended), SFTP, Redis password
- **Audit Logging**: Request tracking and monitoring

---

## Performance Metrics

| Service | Throughput | Latency | Accuracy |
|---------|------------|---------|----------|
| **NER** | 50-100 pages/min | 1-2s/page | 85-95% |
| **REL** | 20-30 pages/min | 3-5s/page | High (LLM) |
| **QA Indexing** | 100 pages/min | <1s/page | N/A |
| **QA Chat** | 10 queries/min | 2-3s/query | >85% |
| **Talend Pulse** | 5-10 CVs/min | 10-15s/CV | High (LLM) |

---

## Key Features

### Production-Ready
- ✅ Distributed worker management
- ✅ Automatic retry and error handling
- ✅ Dead-letter queues for failed tasks
- ✅ Comprehensive monitoring (Opik)
- ✅ SQLite caching for performance
- ✅ Session management for QA workflows

### Developer-Friendly
- ✅ REST API with clear documentation
- ✅ Pydantic validation for all inputs
- ✅ Request ID tracking
- ✅ Structured error responses
- ✅ Code examples in multiple languages

### Enterprise-Grade
- ✅ 99.9% uptime capability
- ✅ Horizontal scalability
- ✅ Multi-environment support (dev/test/prod)
- ✅ Security best practices
- ✅ Backup and recovery procedures

---

## System Requirements

### Minimum
- **CPU**: 8 cores
- **RAM**: 16 GB
- **GPU**: NVIDIA GPU with 8GB VRAM
- **Storage**: 50 GB SSD
- **OS**: Ubuntu 20.04+ or equivalent Linux

### Recommended (Production)
- **CPU**: 16+ cores
- **RAM**: 32 GB+
- **GPU**: NVIDIA A100/V100 (16GB+ VRAM)
- **Storage**: 200 GB NVMe SSD
- **OS**: Ubuntu 22.04 LTS

---

## Getting Started

### 1. Deploy the Platform
Follow [04_Deployment_Guide.md](./04_Deployment_Guide.md) for step-by-step installation.

### 2. Test the API
Use examples from [03_API_Reference.md](./03_API_Reference.md) to verify deployment.

### 3. Implement Use Cases
Follow tutorials in [05_User_Guide.md](./05_User_Guide.md) for your specific needs.

### 4. Monitor and Optimize
Use [02_Technical_Architecture.md](./02_Technical_Architecture.md) and [04_Deployment_Guide.md](./04_Deployment_Guide.md) for operational excellence.

---

## Support & Contribution

### Documentation Feedback
If you find errors or have suggestions for improving this documentation, please contact the platform maintainers.

### Code Contributions
Refer to [06_Module_Documentation.md](./06_Module_Documentation.md) to understand module internals before contributing.

### Issue Reporting
Use the troubleshooting sections in [04_Deployment_Guide.md](./04_Deployment_Guide.md) and [05_User_Guide.md](./05_User_Guide.md) first, then escalate if needed.

---

## License & Legal

**Platform**: Merit ML Platform (Knowledge Agent)
**Organization**: Merit Software Services
**Project**: KIAA (Knowledge & Intelligence Augmentation Agent)

---

## Document Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | December 2024 | Initial comprehensive documentation |

---

## Additional Resources

### External Documentation
- **GLiNER**: https://github.com/urchade/GLiNER
- **LangChain**: https://python.langchain.com/
- **LangGraph**: https://langchain-ai.github.io/langgraph/
- **ChromaDB**: https://docs.trychroma.com/
- **Redis Streams**: https://redis.io/docs/data-types/streams/
- **Opik**: https://www.comet.com/docs/opik/

### API Endpoints Quick Reference
```
GET  /                   # Health check
POST /ner                # Named Entity Recognition
POST /rel                # Relation Extraction
POST /qa_indexer         # QA Document Indexing
POST /qa_chat            # QA Question Answering
POST /talend_pulse       # Resume Scoring
```

### Default Configuration
- **API Port**: 5001
- **Redis Host**: 172.27.140.191:6380
- **Opik Host**: http://172.27.141.49:5173/api
- **SFTP Host**: 125.16.95.60

---

**For questions or support, consult the relevant documentation file above or contact your system administrator.**
