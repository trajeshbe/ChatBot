# Claude Skills - 3-Tier Enterprise Architecture

Welcome to the reorganized Claude Skills library, aligned with the Enterprise RAG Platform's 3-tier architecture.

---

## 🗺️ Quick Navigation

### By Architectural Tier

| Tier | Description | Skills Count | Directory |
|------|-------------|--------------|-----------|
| **🏗️ Tier 1** | Core Platform - Always deployed foundation | 7 | [tier-1-core-platform/](tier-1-core-platform/) |
| **🧩 Tier 2** | Use-Case Modules - Selectively enabled | 32 | [tier-2-modules/](tier-2-modules/) |
| **🎨 Tier 3** | Customer Implementations - Bespoke configs | 12 | [tier-3-customer-implementations/](tier-3-customer-implementations/) |

### By Capability

| Capability | Skills | Location |
|------------|--------|----------|
| **RAG/Chatbot** | 4 skills | [Tier 2 » core-rag](tier-2-modules/core-rag/) |
| **Data Extraction** | 4 skills | [Tier 2 » data-extraction](tier-2-modules/data-extraction/) |
| **NLP/Classification** | 5 skills | [Tier 2 » nlp-processing](tier-2-modules/nlp-processing/) |
| **Analytics** | 4 skills | [Tier 2 » analytics-engine](tier-2-modules/analytics-engine/) |
| **Query/SQL** | 3 skills | [Tier 2 » query-engine](tier-2-modules/query-engine/) |
| **Domain Verticals** | 12 skills | [Tier 2 » domain-verticals](tier-2-modules/domain-verticals/) |

### By Industry Vertical

| Industry | Skills | Location |
|----------|--------|----------|
| **Financial Services** | 3 skills | [domain-verticals/financial](tier-2-modules/domain-verticals/financial/) |
| **Supply Chain** | 3 skills | [domain-verticals/supply-chain](tier-2-modules/domain-verticals/supply-chain/) |
| **Mining** | 2 skills | [domain-verticals/mining](tier-2-modules/domain-verticals/mining/) |
| **Agriculture** | 2 skills | [domain-verticals/agriculture](tier-2-modules/domain-verticals/agriculture/) |
| **Human Resources** | 2 skills | [domain-verticals/human-resources](tier-2-modules/domain-verticals/human-resources/) |

---

## 🏗️ Tier 1: Core Platform

> **Always-deployed foundation components**

- [Platform Infrastructure](tier-1-core-platform/platform-infrastructure.md) - Kubernetes, Istio, Argo CD, GitOps
- [Database & Vector Storage](tier-1-core-platform/database-vector-storage.md) - PostgreSQL+pgvector, Redis, MinIO
- [LLM Providers](tier-1-core-platform/llm-providers.md) - OpenAI, Anthropic, vLLM, llama.cpp
- [Document Processing](tier-1-core-platform/document-processing.md) - Docling, PyMuPDF, document parsing
- [Authentication & RBAC](tier-1-core-platform/authentication-rbac.md) - FastAPI security, JWT, OPA
- [Observability & Monitoring](tier-1-core-platform/observability-monitoring.md) - OpenTelemetry, Grafana Stack
- [Prompt Library Management](tier-1-core-platform/prompt-library-management.md) - YAML prompts, Pydantic schemas

[**View All Tier 1 Skills →**](tier-1-core-platform/)

---

## 🧩 Tier 2: Use-Case Modules

> **Selectively-enabled capabilities you can mix and match**

### Core Modules

- [**Core RAG**](tier-2-modules/core-rag/) - Retrieval-Augmented Generation (4 skills)
- [**Data Extraction**](tier-2-modules/data-extraction/) - Structured data extraction (4 skills)
- [**NLP Processing**](tier-2-modules/nlp-processing/) - NER, classification, tagging (5 skills)
- [**Analytics Engine**](tier-2-modules/analytics-engine/) - Metrics & insights (4 skills)
- [**Query Engine**](tier-2-modules/query-engine/) - Natural language to SQL (3 skills)

### Domain Verticals

- [**Financial Services**](tier-2-modules/domain-verticals/financial/) - Financial analysis & compliance (3 skills)
- [**Supply Chain**](tier-2-modules/domain-verticals/supply-chain/) - Procurement & vendor management (3 skills)
- [**Mining Industry**](tier-2-modules/domain-verticals/mining/) - Mining operations & compliance (2 skills)
- [**Agriculture**](tier-2-modules/domain-verticals/agriculture/) - Agronomy & crop management (2 skills)
- [**Human Resources**](tier-2-modules/domain-verticals/human-resources/) - Talent search & skill matching (2 skills)

[**View All Tier 2 Modules →**](tier-2-modules/)

---

## 🎨 Tier 3: Customer Implementations

> **Customer-specific configurations and implementations**

- [British Council](tier-3-customer-implementations/british-council/) - Course recommendations & profile matching
- [Construction Monitoring](tier-3-customer-implementations/construction-monitoring/) - Document intelligence & planning analysis
- [CRU Organization](tier-3-customer-implementations/cru-org/) - Custom workflows
- [Grant Thornton](tier-3-customer-implementations/grant-thornton/) - Financial analysis & audit workflows
- [GT Motive](tier-3-customer-implementations/gt-motive/) - Automotive intelligence
- [Solera](tier-3-customer-implementations/solera/) - Insurance claims processing

[**View All Customer Implementations →**](tier-3-customer-implementations/)

---

## 🎯 Complexity Tiers (Prompt-First Approach)

Skills are categorized by implementation complexity:

- **🟢 Tier A (80%)**: Prompt-only - Single LLM call with structured output
- **🟡 Tier B (15%)**: Prompt + Light Logic - 2-3 sequential prompts
- **🔴 Tier C (5%)**: Full LangGraph - Multi-step workflows with state management

See [Prompt Library Integration Guide](../SKILLS_PROMPT_LIBRARY_INTEGRATION.md) for details.

---

## 📋 Architecture Context

This skills organization aligns with the **Enterprise 3-Tier AI Architecture**:

```
┌─────────────────────────────────────────┐
│  Tier 3: Customer Bespoke               │
│  • Branding & theme                     │
│  • Domain-specific prompts              │
│  • Custom integrations                  │
│  • Business logic                       │
├─────────────────────────────────────────┤
│  Tier 2: Use-Case Modules               │
│  • Selectively enabled                  │
│  • Mix and match capabilities           │
│  • Reusable across customers            │
├─────────────────────────────────────────┤
│  Tier 1: Core Platform                  │
│  • Always deployed                      │
│  • Foundation for all modules           │
│  • Shared infrastructure                │
└─────────────────────────────────────────┘
```

**Reference**: [Enterprise 3-Tier Architecture Plan](../Enterprise%203%20Tier%20AI%20Architecure%20plan/enterprise-rag-three-tier-architecture-plan.md)

---

## 🚀 For New Customers

When onboarding a new customer:

1. **Select Tier 2 Modules** based on use case requirements
2. **Configure Module Settings** with customer-specific parameters
3. **Create Tier 3 Skills** for customer-specific guidance
4. **Deploy** using Helm + Argo CD with customer configuration

See: [Customer Onboarding Guide](tier-3-customer-implementations/README.md)

---

## 🔧 Tech Stack

All skills leverage the **unified Enterprise RAG Stack**:

- **Frontend**: Next.js 14, React 18, Tailwind CSS, TypeScript
- **Backend**: FastAPI, Python 3.11, GraphQL (Strawberry)
- **AI/ML**: LangChain, LangGraph, OpenAI, Anthropic, vLLM, Sentence-Transformers
- **Data**: PostgreSQL+pgvector, Redis, MinIO, Apache Flink
- **Infrastructure**: Kubernetes, Istio, Argo CD, Tekton
- **Observability**: OpenTelemetry, Grafana Stack, Prometheus
- **Prompts**: YAML-based prompt library with Pydantic schemas

**Reference**: [GitHub Repository](https://github.com/trajeshbe/ChatBot/tree/claude/enterprise-rag-chatbot-stack-011CV55YJHaUYhTQVqsEU4iK)

---

## 📚 Documentation

- [Skills Reorganization Analysis](../SKILLS_REORGANIZATION_ANALYSIS.md) - Comprehensive mapping
- [Reorganization Summary](../SKILLS_REORGANIZATION_SUMMARY.md) - Executive summary
- [Prompt Library Integration](../SKILLS_PROMPT_LIBRARY_INTEGRATION.md) - Prompt-first approach
- [Quick Start Guide](../QUICK_START_PROMPT_FIRST_SKILLS.md) - Prompt engineering patterns

---

## 🔄 Migration from Legacy Skills

If you're looking for old skills, see:

- Old `prototypes/` → Now organized in `tier-2-modules/`
- Old `client-pocs/` → Now in `tier-3-customer-implementations/`
- Old `ml-platform/` → Split across `tier-1-core-platform/`

Legacy skills are preserved in their original locations with redirect notices.

---

**Last Updated**: 2025-12-23
**Status**: Production Ready
**Total Skills**: 51 (7 Tier 1 + 32 Tier 2 + 12 Tier 3)
