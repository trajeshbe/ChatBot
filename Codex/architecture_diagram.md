# Architecture Diagram & Integrations (Enterprise RAG Stack)

```mermaid
flowchart LR
  subgraph Client
    UI[Next.js + Tailwind]
  end

  subgraph Edge
    Envoy[Envoy/Contour]
    Mesh[Istio Ambient]
  end

  subgraph API
    FastAPI[FastAPI + Strawberry GraphQL]
  end

  subgraph Orchestration
    Prefect[Prefect 3 + LangGraph]
    MCP[MCP/Tools]
  end

  subgraph LLM
    vLLM[vLLM on Kube-Ray]
    Llama[llama.cpp / Ollama CPU fallback]
  end

  subgraph Data
    PG[(Postgres + pgvector)]
    Redis[(Redis 7.2 VSS semantic cache)]
    MinIO[(MinIO object store)]
    Feast[Feast on Flink]
  end

  subgraph Observability
    OTEL[OTEL Collectors]
    Tempo[Grafana Tempo]
    Loki[Grafana Loki]
    Mimir[Grafana Mimir]
    OpenCost[OpenCost $/inference]
  end

  subgraph Platform
    Tekton[Tekton CI]
    Argo[Argo CD]
    OPA[OPA Gatekeeper]
    Devloop[DevContainer + Skaffold + mirrord]
  end

  UI -->|REST/GraphQL| Envoy --> Mesh --> FastAPI
  FastAPI -->|calls| Prefect
  Prefect -->|agent DAGs| vLLM
  Prefect --> Llama
  Prefect -->|ingest| MinIO
  Prefect -->|embed| PG
  Prefect -->|cache| Redis
  Prefect -->|features| Feast
  MCP --> Prefect
  FastAPI -->|retrieve| PG
  FastAPI -->|semantic cache| Redis
  FastAPI -->|store raw| MinIO
  vLLM -->|token usage| OpenCost
  Llama -->|token usage| OpenCost
  Mesh --> OTEL --> Tempo
  Mesh --> Loki
  Mesh --> Mimir
  Argo --> Edge
  Argo --> API
  Argo --> LLM
  Argo --> Data
  Tekton --> Argo
  Tekton -->|build/eval| API
  OPA -. admission .-> Argo
  OPA -. admission .-> Edge
  OPA -. admission .-> API
  Devloop -. inner loop .-> Tekton
```

## Integration Notes (Bullet Guide)
- **Frontend → API**: Next.js UI talks to FastAPI/Strawberry over REST/GraphQL for chat, uploads, model selection.
- **Ingress/Mesh**: Envoy/Contour terminates TLS and routes into Istio Ambient, which enforces mTLS/policies/telemetry for all services.
- **API → Orchestration**: FastAPI invokes Prefect/LangGraph flows for agent actions, scraping, ingestion, and evaluations; MCP tools can be surfaced into flows.
- **API → Data**: Stores raw docs in MinIO; writes metadata/chunks/embeddings to Postgres/pgvector; checks Redis for semantic cache.
- **Retrieval → LLM**: API/RAG services fetch context from Postgres/pgvector (optionally Redis cache), then call LLM service choosing vLLM (Ray) or llama.cpp CPU fallback (or external APIs if configured).
- **Features**: Feast on Flink serves features to Prefect/LangGraph or API for routing/scoring/personalization.
- **Observability**: OTEL exporters emit traces/logs/metrics to Tempo/Loki/Mimir; token/cost metrics labeled for OpenCost to compute $/inference.
- **Platform/GitOps**: Tekton builds/tests/evals and feeds Argo CD; Argo applies manifests/Helm; OPA Gatekeeper enforces admission policies (non-root, TLS, signing). DevContainer/Skaffold/mirrord support local dev and live-sync.

Use this diagram + bullets as a map for how requests, data, and control signals move through the stack.
