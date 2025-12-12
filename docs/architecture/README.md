# Architecture Documentation

System architecture, design patterns, and deployment documentation.

## 📖 Available Documentation

### [AGENT_ARCHITECTURE_AND_DATA_FLOW.md](./AGENT_ARCHITECTURE_AND_DATA_FLOW.md) ⭐ NEW
**Complete Agent Task System Architecture** (1543 lines)
- Docker-in-Docker configuration and container communication
- End-to-end data flow (request → execution → MinIO storage)
- MinIO organizational hierarchy and file movement
- Workspace management and security isolation
- Agentic loop implementation (THINK → ACT → OBSERVE)
- Security architecture (6 layers of protection)
- Project integration and multi-tenant isolation
- Download endpoint architecture with streaming
- Performance metrics and troubleshooting guide

### [SANDBOX_COMPARISON_ANALYSIS.md](./SANDBOX_COMPARISON_ANALYSIS.md) ⭐ NEW
**Comprehensive Sandbox Implementation Comparison**
- Our Docker-in-Docker vs E2B vs Claude Code vs OpenAI vs Modal
- Architecture, security, performance, and cost analysis
- Detailed pros/cons for each solution
- Head-to-head scenario comparisons
- Decision framework and recommendations
- Migration paths and future considerations

### [MEMORY_HIERARCHY_GUIDE.md](./MEMORY_HIERARCHY_GUIDE.md)
Comprehensive guide to the memory hierarchy architecture.
- Short-term memory (session-based)
- Long-term memory (global)
- RAG pipeline design
- Database schema
- Query flow diagrams

### [DEPLOYMENT.md](./DEPLOYMENT.md)
Deployment guide for various environments.
- Local development (Docker Compose)
- Kubernetes deployment
- Service mesh configuration (Istio)
- Observability setup (Grafana, Tempo, Loki)
- Security considerations

### [AGENT_TASK_RESOURCE_MANAGEMENT.md](./AGENT_TASK_RESOURCE_MANAGEMENT.md)
Agent task resource management and monitoring.
- Container resource limits
- Task queueing and scheduling
- Resource cleanup policies

---

## 🏗️ Key Architectural Concepts

### Memory Hierarchy
The system implements a two-tier memory system:
1. **Short-term memory**: Session-specific documents (checked first)
2. **Long-term memory**: All documents (fallback)

### RAG Pipeline
```
Query → Classification → Memory Selection → Vector Search → Context Assembly → LLM → Response
```

### Service Architecture
- **Backend**: FastAPI (Python 3.11)
- **Frontend**: Next.js 14 (TypeScript/React)
- **Database**: PostgreSQL 16 + pgvector
- **Cache**: Redis with VSS
- **Storage**: MinIO (S3-compatible)
- **Observability**: OpenTelemetry, Grafana stack

---

## 🔗 Related Documentation

- **Setup**: [../setup/](../setup/) - Component setup guides
- **Guides**: [../guides/ADMIN_GUIDE.md](../guides/ADMIN_GUIDE.md) - Admin operations
- **Main**: [../../CLAUDE.md](../../CLAUDE.md) - Development guide

---

**Last Updated**: 2025-12-12
