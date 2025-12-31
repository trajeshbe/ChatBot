# Tier 1: Core Platform Skills

**Status**: Always Deployed
**Purpose**: Foundation components that power all modules and customer implementations

---

## Overview

Tier 1 skills provide guidance on the core platform infrastructure that is deployed in every instance of the Enterprise RAG Platform. These components form the foundation that Tier 2 modules and Tier 3 customer implementations build upon.

---

## Skills Inventory

| Skill | Description | Key Technologies |
|-------|-------------|------------------|
| [platform-infrastructure.md](platform-infrastructure.md) | Kubernetes orchestration, service mesh, GitOps | Kubernetes, Istio Ambient, Argo CD, Tekton |
| [database-vector-storage.md](database-vector-storage.md) | Vector databases, caching, object storage | PostgreSQL+pgvector, Redis, MinIO |
| [llm-providers.md](llm-providers.md) | LLM abstraction layer and provider management | OpenAI, Anthropic, vLLM, llama.cpp |
| [document-processing.md](document-processing.md) | Document parsing and chunking | Docling, PyMuPDF, LlamaParse |
| [authentication-rbac.md](authentication-rbac.md) | Authentication, authorization, security | FastAPI Security, JWT, OPA Gatekeeper |
| [observability-monitoring.md](observability-monitoring.md) | Tracing, metrics, logging | OpenTelemetry, Grafana, Prometheus |
| [prompt-library-management.md](prompt-library-management.md) | Centralized prompt management | YAML prompts, Pydantic schemas |

---

## Architecture Context

### Platform Layers

```
┌──────────────────────────────────────────────────┐
│  TIER 1: CORE PLATFORM (Always Deployed)        │
├──────────────────────────────────────────────────┤
│                                                  │
│  Infrastructure Layer                            │
│  ├─ Kubernetes + Istio                          │
│  ├─ Argo CD (GitOps)                            │
│  └─ Tekton (CI/CD)                              │
│                                                  │
│  Data Layer                                      │
│  ├─ PostgreSQL + pgvector                       │
│  ├─ Redis + RediSearch                          │
│  └─ MinIO (S3-compatible)                       │
│                                                  │
│  AI/ML Layer                                     │
│  ├─ LLM Providers (OpenAI, Anthropic, vLLM)    │
│  ├─ Document Processing (Docling)               │
│  └─ Prompt Library (YAML-based)                 │
│                                                  │
│  Security Layer                                  │
│  ├─ Authentication (JWT, OAuth2)                │
│  ├─ RBAC (OPA Gatekeeper)                       │
│  └─ Network Policies                            │
│                                                  │
│  Observability Layer                             │
│  ├─ OpenTelemetry                               │
│  ├─ Grafana Stack                               │
│  └─ Prometheus                                   │
│                                                  │
└──────────────────────────────────────────────────┘
```

---

## When to Reference These Skills

### For Platform Engineers
- Setting up new environments
- Configuring infrastructure components
- Troubleshooting platform issues
- Upgrading platform versions

### For Module Developers
- Understanding platform capabilities
- Integrating with platform services
- Using platform abstractions (LLM, storage, etc.)
- Following platform patterns

### For Customer Implementations
- Understanding deployment architecture
- Configuring customer-specific settings
- Troubleshooting deployment issues
- Scaling and performance tuning

---

## Common Platform Patterns

### 1. LLM Provider Abstraction

All modules use the platform's LLM abstraction:

```python
from app.core.llm import get_llm_provider

# Platform handles provider selection, rate limiting, fallbacks
llm = get_llm_provider(
    model_name="gpt-4o",
    temperature=0.7
)

response = llm.invoke(prompt)
```

### 2. Vector Storage Pattern

```python
from app.core.database import get_vector_store

# Platform manages connection pooling, indexing
vector_store = get_vector_store(
    collection_name="customer_documents",
    embedding_model="sentence-transformers/all-MiniLM-L6-v2"
)

results = vector_store.similarity_search(query, k=5)
```

### 3. Prompt Library Pattern

```python
from app.core.prompts import PromptManager

# Centralized prompt management
prompt_manager = PromptManager()
prompts = prompt_manager.load_prompts("core-rag")

response = llm.invoke(prompts["generation_prompt"])
```

### 4. Observability Pattern

```python
from app.core.observability import get_tracer
import opik

# Automatic tracing for all LLM calls
tracer = get_tracer(project_name="module-name")

with tracer.trace("operation_name"):
    result = llm.invoke(prompt)
```

---

## Platform Configuration

### Environment Variables

Key platform configurations set via environment variables:

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/ragdb
REDIS_URL=redis://localhost:6379
MINIO_ENDPOINT=http://localhost:9000

# LLM Providers
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Observability
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
OPIK_API_KEY=...

# Prompts
PROMPT_PATH=prompt_engineering/prompt
```

### Helm Values (Deployment)

```yaml
# Platform-wide settings
platform:
  namespace: rag-platform
  replicas: 3

database:
  host: postgresql
  port: 5432
  poolSize: 20

llm:
  defaultProvider: openai
  fallbackProvider: anthropic
  timeout: 30

observability:
  enabled: true
  sampling: 0.1
```

---

## Platform Upgrade Strategy

When upgrading platform components:

1. **Review Tier 1 Skills** for version-specific guidance
2. **Test in Non-Prod** environment first
3. **Validate Tier 2 Modules** still work
4. **Update Customer Configs** if needed
5. **Monitor Observability** dashboards

---

## Related Documentation

- [Enterprise 3-Tier Architecture Plan](../../Enterprise%203%20Tier%20AI%20Architecure%20plan/enterprise-rag-three-tier-architecture-plan.md)
- [GitHub Repository](https://github.com/trajeshbe/ChatBot/tree/claude/enterprise-rag-chatbot-stack-011CV55YJHaUYhTQVqsEU4iK)
- [Tier 2 Modules](../tier-2-modules/)
- [Tier 3 Customer Implementations](../tier-3-customer-implementations/)

---

**Last Updated**: 2025-12-23
**Skills Count**: 7
**Status**: Production Ready
