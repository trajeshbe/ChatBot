# End-to-End System Overview (Enterprise RAG Chatbot)

Audience: New engineers who need to understand what runs where, how requests flow, and why each component exists.

## Big Picture
- Users talk to a web UI (Next.js/Tailwind).
- Traffic enters through Envoy/Contour ingress and flows inside the Istio Ambient mesh (mTLS, policy, telemetry).
- The API layer is FastAPI + Strawberry GraphQL. It exposes chat, upload, scraping, and model selection endpoints.
- RAG pipeline: documents are uploaded/scraped → stored in MinIO → chunked/embedded → stored in Postgres/pgvector → retrieved and reranked → fed to LLM for answers.
- LLM runtimes: vLLM on Ray for GPU models; Ollama/llama.cpp for CPU fallback; OpenAI/Anthropic for external models.
- State and metadata: Postgres (relational), Redis (semantic cache), MinIO (object storage), Feast on Flink (feature store for online features), Prefect (DAGs and agents) with LangGraph inside flows.
- Observability: OTEL traces/logs/metrics → Tempo/Loki/Mimir; costs tracked by OpenCost.
- Platform: Argo CD (GitOps deploy), Tekton (CI/pipelines), OPA Gatekeeper (admission policy), DevContainer/Skaffold/mirrord (dev loop).

## Components and Purpose
- **Frontend (Next.js + Tailwind)**: Chat UI, file uploads, model selection, evaluation dashboards. Talks to API via REST/GraphQL.
- **Ingress (Envoy/Contour)**: Terminates TLS, routes to services, applies rate limits/WAF/auth if configured.
- **Service Mesh (Istio Ambient)**: Provides mTLS between services, traffic policies, telemetry without sidecars.
- **API (FastAPI + Strawberry GraphQL)**: Hosts routes for health, chat, upload, scraping, MCP tools. Wires services together and enforces settings.
- **RAG Services**
  - `rag_service_enhanced`: End-to-end query handling: classify query → check semantic cache → embed → search short-term (session docs) and long-term (global docs) → combine context → call LLM → log quality and cache.
  - `rag_service` (basic): Simpler path without session hierarchy.
- **Document Service**: Handles upload to MinIO, metadata in Postgres, text extraction (Docling/fallback), cleaning, chunking (RecursiveCharacterTextSplitter), embedding, and chunk persistence.
- **Embedding Service**: SentenceTransformer model to create vectors; caches embeddings in Redis (semantic cache).
- **Retrieval/Storage**
  - Postgres + pgvector: Stores documents and chunk embeddings; queried via hybrid SQL (semantic + keyword) with thresholds and fallback.
  - Redis: Caches embeddings and semantic query results to speed repeats.
  - MinIO: Object store for raw documents and artifacts (S3-compatible).
- **LLM Service (Enhanced)**: Multi-provider client; picks available models based on keys/hardware; supports OpenAI, Anthropic, vLLM, Ollama, llama.cpp. Provides `generate` and `generate_with_context` for RAG.
- **Agents/Tools**: Prefect flows + LangGraph orchestrate scraping, ingestion, evaluation. MCP tool registry integrates external tools if installed.
- **Scraper Service**: Fetches URLs (requests/BeautifulSoup/trafilatura; Playwright optional), filters content, stores in MinIO, and triggers processing.
- **Feature Store (Feast on Flink)**: Serves/updates online features that can enrich prompts or routing decisions.
- **Observability**: OTEL instrumentation hooks exist; intended to send traces/metrics/logs to Tempo/Loki/Mimir. Quality metrics computed for RAG responses.
- **Cost**: OpenCost monitors per-resource costs; intended to label workloads for $/inference tracking.
- **Platform/Governance**: Argo CD (deploy manifests), Tekton (build/test/eval pipelines), OPA Gatekeeper (policy enforcement), DevContainer/Skaffold/mirrord (dev setup and live-reload).

## Key Data Flows
### 1) Document Ingestion (Upload/Scrape)
1. User uploads a file (REST) or triggers scrape (URL).
2. API hands bytes/URL to Document/Scraper Service.
3. Raw file stored in MinIO; metadata row created in Postgres.
4. Text extraction → cleaning → chunking (size 800, overlap 150 by default).
5. Embeddings generated; chunks with embeddings stored in Postgres (pgvector).
6. Optional: associate document with a chat session (short-term memory).

### 2) Query Handling (RAG)
1. User sends query via chat endpoint (REST/GraphQL).
2. Query classifier decides if it’s document-related vs. general/AI-personal.
   - High-confidence AI-personal → direct LLM (no retrieval).
3. Semantic cache check (Redis) for similar past queries.
4. Embed query; run hybrid search:
   - Short-term: session-linked docs first (semantic + keyword, cascading thresholds).
   - Long-term: global docs (semantic + keyword, fallback thresholds).
5. Combine/dedupe chunks; add recent conversation history.
6. Call `generate_with_context` on LLM service (model chosen or default).
7. Return answer + sources + quality metrics; cache result; log conversation.

### 3) Model Selection
- Model registry tracks availability by provider and hardware.
- Default order: local small Ollama → GPU/vLLM → OpenAI/Claude → CPU fallback.
- API can accept `model_id`; otherwise uses default. No hard cost/latency policy baked in yet.

### 4) Orchestration & Tools
- Prefect 3 DAGs run ingestion, evaluation, and agent workflows (LangGraph for tool calling). Scraper and document processing can be steps in these flows. MCP integrates external tools if present.

### 5) Observability & Cost
- FastAPI and services have OTEL hooks; data should flow to Tempo (traces), Loki (logs), Mimir (metrics). Quality metrics are computed per RAG answer. OpenCost ingests K8s resource labels for spend tracking.

## Important Config Defaults (from `backend/app/core/config.py`)
- Chunking: `CHUNK_SIZE=800`, `CHUNK_OVERLAP=150`
- Retrieval: `TOP_K_RESULTS=5`, `SIMILARITY_THRESHOLD=0.75`, `MIN_SIMILARITY_THRESHOLD=0.60`, `NO_RELEVANT_DOCS_THRESHOLD=0.70`
- LLM: `USE_VLLM=True`, default model priority favors local Ollama small models.
- Storage: Postgres/pgvector, Redis (semantic cache), MinIO (`MINIO_SECURE=False` by default), Feast path `/app/feast`.
- Scraping: Enabled, multiple strategies; Playwright off by default.

## Integration Notes
- FastAPI wires services: document_service, scraper_service, rag_service_enhanced/basic, embedding_service, llm_service_enhanced/basic, MCP tools.
- RAG enhanced service uses document_service search APIs and embedding_service; falls back to basic rag_service cache helpers.
- LLM service pulls keys from DB via secrets_service or env; uses httpx for local runtimes; OpenAI/Anthropic SDKs for external.
- Redis and Postgres must be reachable at configured hosts; MinIO must have bucket `documents` accessible.
- Prefect/Feast are referenced by paths/URLs; ensure deployments match config.

## How to Explain This to a New Hire
- Think of three planes: **edge/mesh** (Envoy + Istio), **API/logic** (FastAPI + services), **data/ML** (MinIO, Postgres/pgvector, Redis, LLM runtimes).
- A user uploads docs → they get chunked/embedded and stored. When the user asks a question, the system finds the best chunks, adds chat history, and asks an LLM to answer with citations.
- Multiple LLM backends exist; the system tries local models first, then external if available. Caches help speed up repeats.
- Observability and cost stacks run alongside to keep track of health and spend; GitOps/CI keep deployments consistent.

## Gaps to Be Aware Of (for newcomers)
- Auth/rate limits not enforced by default; direct LLM test endpoint is open.
- Ingestion lacks file type/size/AV/PII safeguards.
- Retrieval SQL is interpolated (needs parameterization/reranker) and cache keys aren’t versioned by embedding model.
- TLS off for MinIO/DB/Redis by default; secrets are placeholders—must be fixed for production.

## Suggested First Hardening Tasks
1) Add authN/Z + rate limiting to chat/upload/LLM endpoints; remove or lock `/api/v1/llm/test`.
2) Add file allowlist/size cap + AV/PII scrub before chunking; tenant scoping for storage/retrieval.
3) Parameterize retriever queries and add reranker; version embedding/cache keys; enforce TLS and non-placeholder secrets at startup.
4) Wire OTEL spans for retrieval decisions and cache behavior; set SLOs (latency/answerable/citation quality).
