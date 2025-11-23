# Tech Stack Review (Enterprise RAG Application)

## Overview
Stack: Next.js/Tailwind frontend; Envoy/Contour ingress; Istio Ambient mesh; FastAPI + Strawberry GraphQL API; vLLM on Ray (GPU) with llama.cpp/Ollama CPU fallback; Postgres + pgvector; MinIO object store; Redis 7.2 (semantic cache); Prefect 3 + LangGraph agent DAGs; Feast on Flink; OTEL → Tempo/Loki/Mimir; OpenCost; Argo CD + Tekton; OPA Gatekeeper; DevContainer + Skaffold + mirrord dev loop.

## Pros (What’s Working)
- Clear separation of control plane (Argo CD, Tekton, OPA, OpenCost) and data/ML plane (vLLM/Ray, pgvector, Redis, MinIO).
- Retrieval features include hybrid search, session/short-term memory, semantic cache, and adaptive thresholds.
- Multi-provider LLM abstraction (OpenAI/Anthropic/vLLM/Ollama) with availability detection and default model fallback.
- Observability plumbing present (OTEL exporters, Tempo/Loki/Mimir) and cost visibility via OpenCost.
- GitOps and CI/CD foundations in place (Tekton + Argo CD) with DevContainer/Skaffold/mirrord for inner loop.

## Cons / Risks
- **Security posture**: Default secrets/creds and unauthenticated ingestion/LLM endpoints; TLS off for MinIO/DB/Redis; WAF/rate limits absent. OPA/Gatekeeper not enforced in code paths. Direct LLM bypass exposed.
- **Data safety**: Upload path lacks file allowlist, size caps, AV/PII/secret scrubbing; no tenant isolation in storage or retrieval queries. Prompt/tooling guardrails minimal; scraper/tool allowlists missing.
- **Reliability/quality**: Embedding cache not versioned; no reranker; chunking static (800/150) and may misfit docs. Hybrid SQL uses string interpolation (risk of injection, brittle). Critical init failures are non-fatal, causing partial availability. No readiness tied to dependencies.
- **Model policy/cost**: Default models prioritize small local models without quality gating; no per-tenant quotas, max tokens, or circuit breakers. Cost tracking not wired into LLM calls.
- **Observability gaps**: Limited structured spans for retrieval decisions, cache hits/misses, tool usage, or quality metrics; no SLOs/alerts (hallucination rate, empty-context rate, latency).
- **Platform ops**: Istio Ambient maturity/upgrade risk; Envoy/Contour adds hop/ops overhead without documented tuning (streaming, WebSocket, gRPC). Feast on Flink is heavy; governance/versioning plans not visible.

## Recommendations (Enterprise-Grade)
1) **Security & Access**
   - Enforce OIDC/JWT across REST/GraphQL; remove or lock `/api/v1/llm/test`. Add WAF + rate limiting at Envoy; strict mTLS in Istio Ambient; egress policies for tools/scrapers.
   - Externalize secrets (CSI/External Secrets); block startup on placeholder secrets/DEBUG in non-dev. Require TLS to Postgres/MinIO/Redis; enable MinIO SSE.
   - OPA Gatekeeper policies: non-root, seccomp/AppArmor, image signing/attestations, resource limits, TLS required, no default creds.

2) **Data Ingestion & Retrieval Safety**
   - File type/size allowlist, AV scan (ClamAV), PII/secret scrub before chunking/embedding. Per-tenant buckets/prefixes and RLS for docs/chunks.
   - Parameterize SQL for hybrid search; consider pg_trgm/TS or pgvector HNSW and a cross-encoder reranker. Sanitize keywords; add URL/tool allowlists and prompt-injection filters.
   - Version cache keys with embedding model; invalidate on model change; emit metrics for zero-embedding states.

3) **Model Policy & Cost**
   - Per-tenant/provider quotas, max tokens, and timeouts; circuit breakers for slow/failed providers. Policy-based model selection (quality/cost/latency tiers) informed by evaluations.
   - Emit cost metrics per call (labels consumable by OpenCost) and add budgets/alerts.

4) **Observability & SLOs**
   - OTEL spans/logs for retrieval thresholds tried, cache hit/miss, reranker scores, tool invocations, and guardrail decisions. Redact PII.
   - Define SLOs: p95 latency, answerable rate, citation coverage, hallucination/empty-context rate; alert on breaches.

5) **Reliability & Release**
   - Fail fast on missing dependencies (DB/MinIO/Redis/vLLM); readiness probes tied to service health. Autoscale vLLM/llama.cpp separately; request hedging and streaming end-to-end.
   - Canary/blue-green via Argo Rollouts; shadow traffic for retriever/reranker changes. Backups + tested restores for Postgres/MinIO; multi-AZ for stateful sets.

6) **Governance & DX**
   - Dataset/model provenance tracking; evaluation harness for RAG (faithfulness, grounding, latency, cost) in Tekton pipelines.
   - Preview envs per PR (Skaffold/mirrord); contract tests for GraphQL and tools; golden retrieval tests.

## Priority Quick Wins
- Gate ingestion/LLM endpoints with auth + rate limits; remove public LLM test path.
- Enforce non-placeholder secrets/TLS; block startup otherwise.
- Add file allowlist/size cap + AV/PII scrub before embedding; per-tenant scoping.
- Parameterize retriever queries and add a reranker; version embedding cache keys.
- Add OTEL spans for retrieval decisions and cache behavior; set initial SLOs and alerts.
