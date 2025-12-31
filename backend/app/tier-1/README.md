# Tier 1: Core Platform

**Status**: Always Deployed
**Purpose**: Foundation services required by all deployments

## Categories

- **infrastructure/**: Config, database, security, cache, storage
- **llm/**: LLM abstraction layer (OpenAI, Claude, Ollama, vLLM)
- **embeddings/**: Embedding and reranking services
- **document_processing/**: Document upload, OCR, vision, extraction
- **rag/**: RAG services and pipeline
- **agents/**: Agent framework and engines
- **platform_services/**: Auth, RBAC, audit, secrets, usage tracking
- **finetuning/**: Model fine-tuning infrastructure
- **evaluation/**: Evaluation and quality metrics
- **data_extraction/**: Web scraping and template extraction
- **nlp_processing/**: NLP services (translation, analysis, etc.)
- **export/**: Export and reporting services
- **cv_processing/**: Computer vision services
- **utilities/**: Shared utility functions

## Import Pattern

```python
from app.tier_1.llm.llm_service import LLMService
from app.tier_1.rag.rag_service import RAGService
```

See [THREE_TIER_REORGANIZATION_PLAN.md](../../docs/architecture/THREE_TIER_REORGANIZATION_PLAN.md) for full details.
