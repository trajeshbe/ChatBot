# Architecture Documentation

System architecture, design patterns, and deployment documentation.

## 📖 Available Documentation

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

**Last Updated**: 2025-11-16
