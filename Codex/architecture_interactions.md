# Service Architecture & Interactions (Enterprise RAG Chatbot)

Audience: New engineers. Purpose: Understand what each service does and how data moves between them.

## Core Services and Their Roles
- **Frontend (Next.js + Tailwind)**: Chat UI, uploads, model picker, eval dashboards. Calls API via REST/GraphQL.
- **Ingress (Envoy/Contour)**: TLS termination, routing, rate limits/WAF hooks. First hop into the cluster.
- **Mesh (Istio Ambient)**: mTLS between all workloads, traffic policies, telemetry. No sidecars needed.
- **API (FastAPI + Strawberry GraphQL)**: Single backend service exposing endpoints for chat, upload, scraping, tools, health. Wires together downstream services.
- **RAG Services (in API process)**:
  - `rag_service_enhanced`: Orchestrates query classification, semantic cache, retrieval (session + global), context assembly, LLM call, quality metrics, caching, conversation logging.
  - `rag_service` (basic): Simpler retrieval without session hierarchy.
- **Document Service**: Owns ingestion: store raw file to MinIO, persist metadata in Postgres, extract text, clean, chunk, embed, save chunks/embeddings to Postgres.
- **Embedding Service**: Loads SentenceTransformer model; produces embeddings; caches embeddings in Redis.
- **Scraper Service**: Fetches URLs (requests/BeautifulSoup/trafilatura; Playwright optional), cleans content, stores raw to MinIO, pushes through Document Service for chunking/embedding.
- **LLM Service (Enhanced)**: Multi-provider client. Chooses from OpenAI/Anthropic/vLLM (Ray)/Ollama/llama.cpp based on availability; exposes `generate` and `generate_with_context` for RAG.
- **Agent/Orchestration (Prefect 3 + LangGraph)**: Runs DAGs for ingestion, evaluation, and tool-calling agents. Invokes scraper/document services and LLM service inside flows.
- **Data Plane**:
  - Postgres + pgvector: Documents, chunks, embeddings, sessions, conversations.
  - Redis: Semantic cache for embeddings/query results.
  - MinIO: Object store for raw docs and artifacts.
  - Feast on Flink: Feature store for real-time features (optional enrichment/routing).
- **Observability/Cost**: OTEL exporters → Tempo (traces), Loki (logs), Mimir (metrics); OpenCost for spend.
- **Platform/GitOps**: Tekton (CI/build/test/eval), Argo CD (deploy), OPA Gatekeeper (admission/policy), DevContainer/Skaffold/mirrord (dev loop).

## How Services Interact (Happy Paths)
### A) Document Ingestion (Upload/Scrape)
1) Frontend sends file/URL → **API** (REST/GraphQL).
2) **API** calls **Document Service** (uploads) or **Scraper Service** (URLs).
3) Raw content → **MinIO** (object storage); metadata row → **Postgres**.
4) **Document Service** extracts text, cleans, chunks, embeds (via **Embedding Service**).
5) Embeddings/chunks saved to **Postgres/pgvector**; embeddings cached in **Redis**; document optionally linked to a chat session (short-term memory).
6) Prefect flows can orchestrate the same steps for batch ingestion/evals.

### B) Query Handling (RAG)
1) Frontend sends query → **API**.
2) **RAG Service** classifies query (document vs general/AI-personal).
   - High-confidence AI-personal → direct **LLM Service** (no retrieval).
3) Semantic cache check in **Redis**; if hit, return cached answer.
4) Embed query via **Embedding Service**.
5) Retrieve context via **Document Service**:
   - Short-term: session-linked docs (semantic + keyword + fallback).
   - Long-term: global docs (semantic + keyword + fallback).
6) Combine/dedupe context + recent conversation history.
7) Call **LLM Service** `generate_with_context` → routes to vLLM (Ray), Ollama/llama.cpp, or OpenAI/Anthropic.
8) Return answer + sources + quality metrics; cache result in **Redis**; log conversation in **Postgres**.

### C) Scraper/Tooling via Agents
- **Prefect/LangGraph** agents can call **Scraper Service** and **LLM Service** as tools, then push results through **Document Service** for storage/embedding.

## Control/Support Flows
- **Ingress/Mesh**: Envoy routes external traffic to API; Istio Ambient enforces mTLS/policies for service-to-service calls (API → Postgres/Redis/MinIO/vLLM/Ollama/Prefect).
- **GitOps/CI**: Tekton builds/tests/signs images and can run evals; Argo CD applies manifests/Helm; Gatekeeper policies enforce security baselines.
- **Observability**: OTEL clients in API/services send traces/logs/metrics to Tempo/Loki/Mimir; costs labeled for OpenCost.

## What to Watch (for new engineers)
- Auth/rate limits are not enforced by default—must be added around API ingress for production.
- Upload path lacks file allowlist/size/AV/PII checks; MinIO/DB/Redis defaults are insecure out-of-the-box.
- Retriever hybrid SQL currently interpolates keywords/embeddings—needs parameterization/reranker.

## Mental Model
- Edge (Envoy) → Mesh (Istio) → API (FastAPI/GraphQL) → Services (RAG, Document, Embedding, Scraper, LLM) → Data stores (Postgres/pgvector, Redis, MinIO) → LLM runtimes (vLLM/Ray, Ollama/llama.cpp, OpenAI/Anthropic) → Observability/Cost sidecars (Tempo/Loki/Mimir, OpenCost) with CI/CD/GitOps keeping it consistent.

Use this as the map: ingestion populates Postgres/pgvector/MinIO; queries pull from those stores, add chat context, and call an LLM. Prefect/agents automate multi-step workflows. Envoy/Istio secure and observe the traffic; Tekton/Argo deploy and govern it.
