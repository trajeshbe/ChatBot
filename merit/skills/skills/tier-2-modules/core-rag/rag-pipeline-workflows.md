# RAG Pipeline Workflows - Core RAG Module

**Tier**: 2 (Use-Case Module) | **Module**: core-rag | **Complexity**: 🔴 Tier C
**Source**: `prototypes/generic-rag.md`

## Overview
LangGraph-based RAG workflow: Query → Retrieve → Rerank → Generate → Cite

## Workflow Nodes
1. validate_query - Refine user query
2. retrieve_documents - Vector search
3. rerank_results - Cross-encoder reranking
4. generate_response - LLM generation
5. format_output - Add citations

## Related
[Retrieval](retrieval-semantic-search.md) | [Generation](generation-response.md)
