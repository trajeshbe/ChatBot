# Generation & Response - Core RAG Module

**Tier**: 2 (Use-Case Module) | **Module**: core-rag | **Complexity**: 🔴 Tier C
**Source**: `prototypes/generic-rag.md`

## Overview
LLM-based response generation with retrieved context and source citations.

## Prompt Template
See: `prompt_engineering/prompt/core_rag_prompts.yaml` → `generation_prompt`

## Key Pattern
Context + Question → LLM → Answer + Sources

## Related
[Retrieval](retrieval-semantic-search.md) | [Conversation Management](conversation-management.md)
