# RAG Chatbot Review & Enterprise-Grade Guidelines

## Current Implementation Snapshot
- **LLM orchestration**: `backend/app/services/llm_service_enhanced.py` supports OpenAI, Anthropic, vLLM (Ray), Ollama, llama.cpp. Default priority favors local Ollama small models, then GPU/vLLM, then OpenAI/Claude. Keys pulled from DB (secrets_service) or env; missing keys silently disable providers. No per-request quotas/timeouts/cost guards.
- **RAG settings**: `backend/app/core/config.py` sets `CHUNK_SIZE=800`, `CHUNK_OVERLAP=150`, `TOP_K_RESULTS=5`, `SIMILARITY_THRESHOLD=0.75`, `MIN_SIMILARITY_THRESHOLD=0.60`, `NO_RELEVANT_DOCS_THRESHOLD=0.70`, `USE_SEMANTIC_CACHE=True` (Redis), `USE_VLLM=True`. Overrides allowed per request.
- **Ingestion & chunking**: `document_service.py` extracts via Docling (optional) or fallback (PDF/Docx/PPTX/JSON/MD), cleans text, chunks with RecursiveCharacterTextSplitter (semantic-ish separators), embeds with SentenceTransformer (cached in Redis). Embedding cache keyed only on text; no model/version in key. Upload endpoint ingests directly to MinIO/DB without auth, size/type guard, or AV.
- **Retriever pipeline (enhanced)**: `rag_service_enhanced.py`
  1) Preprocess + classify query (query_classifier). High-confidence AI-personal → direct LLM.
  2) Semantic cache check.
  3) Embed processed query.
  4) Short-term search (session docs) hybrid semantic+keyword with cascading thresholds.
  5) Long-term search (global) hybrid with limited fallback.
  6) Combine/dedupe (short-term priority) + conversation context.
  7) Generate with context (`generate_with_context`), or warning + general LLM if no context.
  8) Quality metrics evaluation; cache result; persist conversation.
- **Retriever SQL**: Hybrid queries interpolate keywords/embeddings into SQL text (`document_service.py`), which is brittle and risks injection if keywords aren’t sanitized.

## Strengths
- Memory hierarchy: session vs global + conversation context.
- Hybrid retrieval with fallback and diversification; adaptive thresholds.
- Multi-model LLM abstraction with availability detection; semantic cache for embeddings/results.

## Gaps to Address
- Auth/rate limits: Uploads, queries, and `/api/v1/llm/test` are unauthenticated; no quotas or circuit breakers.
- Ingestion safety: No file size/type allowlist, malware scan, PII/secret scrubbing, or tenant scoping before embedding/storage.
- Query safety: Keyword interpolation in SQL; no guard against prompt injection/tool abuse; no URL allowlist for scrapers in RAG loop.
- Quality/recall: Fixed chunk size; no reranker; thresholds static per doc type; cache not versioned by embedding model.
- Governance: No per-tenant isolation in retrieval; secrets and TLS not enforced; model selection not policy-driven (quality/cost/latency).
- Observability: Limited structured spans/logs around retrieval hits/misses, cache behavior, and tool calls; no SLOs or alerts for zero-embedding states.

## Enterprise-Grade Guidelines (Actionable)
1) **Security & Access**
   - Enforce authZ/authN (OIDC/JWT) on all endpoints; remove or restrict `/api/v1/llm/test`.
   - Per-route RBAC and rate limits (ingestion, scrape, LLM calls); add WAF and bot protections at ingress.
   - Require TLS to Postgres/MinIO/Redis; externalize secrets (CSI/External Secrets); block placeholder secrets at startup.

2) **Ingestion Hardening**
   - File allowlist + max size; AV scan (ClamAV) pre-embed; reject high-risk types.
   - PII/secret detection/redaction pipeline before storage/embedding.
   - Per-tenant buckets/prefixes and row-level ACLs; signed URLs for access.

3) **Retrieval Quality & Safety**
   - Parameterize SQL for hybrid search or move to pg_trgm/TS vectors; sanitize keywords.
   - Add cross-encoder reranker (e.g., `bge-reranker`) after initial ANN to reduce noise.
   - Dynamic chunking by doc type (shorter for FAQs/UI text, longer for narratives); maintain chunking config version.
   - Versioned cache keys (include embedding model name/version); invalidate on model upgrades.
   - Add guardrails: prompt-injection filters, URL allowlist for scraping, command/tool whitelists.

4) **LLM Policy & Cost Control**
   - Per-provider and per-tenant quotas; max tokens and timeouts; circuit breakers for slow/failed providers.
   - Policy-based model selection (latency/quality/cost tiers) rather than static priority; ensure evals drive defaults.
   - Log cost estimates per call (OpenCost labels) and emit metrics per provider/model.

5) **Observability & SLOs**
   - Emit OTEL spans for: cache hit/miss, retrieval thresholds tried, reranker scores, tools invoked, and quality metrics.
   - Define SLOs: p95 latency, answerable-rate, citation coverage, hallucination rate; alert on zero-embedding or empty-chunk conditions.
   - Add structured audit logs for uploads, admin actions, tool use, and LLM route decisions.

6) **Reliability & Testing**
   - Fail fast on missing embeddings/DB/MinIO connections; tie readiness/liveness to dependency health.
   - Add tests for: auth required on critical routes, ingestion validation, retrieval correctness (golden sets), cache hit paths, and classifier routing.
   - Canary/blue-green for model/reranker changes; shadow traffic for new retriever configs.

7) **Data & Tenant Governance**
   - Enforce per-tenant filters in retrieval SQL; include tenant in cache keys.
   - Row-level security on Postgres for documents/chunks; encrypt at rest (MinIO SSE, Postgres TDE/disk).
   - Metadata tagging for sensitivity and retention; expire or re-embed on policy changes.

8) **Performance & Scale**
   - Add ANN index tuning (HNSW) and partitioning; pre-warm Redis VSS/semantic cache for hot queries.
   - Autoscale vLLM/llama.cpp separately; request hedging and streaming end-to-end.

## Quick Wins
- Gate all ingestion/LLM endpoints behind auth + rate limits; remove `/api/v1/llm/test` from public surface.
- Add file allowlist + size cap + AV scan + PII scrub before chunking; reject unsafe uploads.
- Parameterize retriever SQL and add reranker; version cache keys with embedding model.
- Enforce non-placeholder secrets/TLS at startup; add OTEL spans for retrieval and cache decisions.
