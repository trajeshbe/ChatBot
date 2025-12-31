# Retrieval & Semantic Search - Core RAG Module

**Tier**: 2 (Use-Case Module)
**Module**: core-rag
**Complexity**: 🔴 Tier C (LangGraph)
**Dependencies**: [Tier 1] database-vector-storage, llm-providers

---

## Overview

Semantic search and document retrieval using vector embeddings. Core component of the RAG pipeline.

## Source Material

Based on: `.claude/skills/prototypes/generic-rag.md`

## Key Capabilities

### 1. Vector Search

```python
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# Standard embedding model (Tier 1 platform)
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# Vector search
results = vector_store.similarity_search(
    query=user_query,
    k=5,  # top_k from config
    filter={"customer_id": customer_id}
)
```

### 2. Hybrid Search (Vector + Keyword)

```python
# Combine vector similarity with keyword matching
hybrid_results = vector_store.similarity_search_with_score(
    query=user_query,
    k=10,
    filter={"customer_id": customer_id}
)

# Rerank by combining scores
reranked = rerank_hybrid(hybrid_results, keyword_boost=0.3)
```

### 3. Query Refinement

**Prompt** (`prompt_engineering/prompt/core_rag_prompts.yaml`):
```yaml
query_refinement_prompt: |
  Refine this user query for better document retrieval:

  Original Query: {question}

  Make it more specific and searchable.
  Return refined query only.
```

## Configuration

```yaml
# module.yaml
name: core-rag
config:
  retrieval:
    top_k: 5
    similarity_threshold: 0.7
    reranking_enabled: true
    reranking_model: "cross-encoder/ms-marco-MiniLM-L-6-v2"
    hybrid_search: false
    keyword_boost: 0.3
```

## Related Skills

- [Generation & Response](generation-response.md)
- [RAG Pipeline Workflows](rag-pipeline-workflows.md)
- [Tier 1: Database & Vector Storage](../../tier-1-core-platform/database-vector-storage.md)

---

**Last Updated**: 2025-12-23
**Status**: Production Ready
