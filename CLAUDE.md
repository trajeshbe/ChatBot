# CLAUDE.md - AI Assistant Development Guide

> **Last Updated**: 2025-12-18
> **Purpose**: Comprehensive guide for AI assistants working with this codebase

---

## 📋 Quick Navigation

| Section | Purpose |
|---------|---------|
| [Project Overview](#project-overview) | What this system does |
| [Quick Start](#quick-start) | Get running in 5 minutes |
| [Repository Structure](#repository-structure) | Where to find things |
| [Tech Stack](#tech-stack) | Technologies used |
| [Architecture](#architecture) | System design patterns |
| [Database](#database) | Schema and migrations |
| [API Reference](#api-reference) | Endpoints and queries |
| [AI Assistant Rules](#ai-assistant-rules) | **CRITICAL: Read before coding** |
| [Common Tasks](#common-tasks) | Recipes for frequent operations |
| [Commands](#commands) | Makefile, Docker, Git, DB |
| [Troubleshooting](#troubleshooting) | Debug common issues |

---

## Project Overview

**Enterprise RAG Chatbot** combining document processing, semantic search, and LLM inference for intelligent Q&A with source attribution.

### Key Features
- **Document Processing**: PDF, DOCX, TXT, JSON, MD via Docling
- **Web Scraping**: Playwright-powered intelligent extraction
- **Vector Search**: PostgreSQL + pgvector (384-dim embeddings)
- **Multi-LLM**: OpenAI, Claude, Ollama, vLLM
- **Fine-Tuning**: Distributed training with Celery, GPU allocation, checkpointing
- **Memory Hierarchy**: Session-scoped (short-term) + global (long-term)
- **Caching**: Redis VSS semantic cache
- **Observability**: OpenTelemetry, Grafana, Tempo, Loki
- **APIs**: REST + GraphQL (Strawberry)
- **RBAC**: Role-based access, audit logging, usage metrics

### Current Status
- **Main Branch**: `claude/enterprise-rag-chatbot-stack-011CV55YJHaUYhTQVqsEU4iK`
- **Latest**: Fine-tuning v1, Claude CLI with MinIO artifacts
- **Details**: See `STATUS.md`

---

## Quick Start

```bash
# 1. Clone and configure
git clone <repository-url> && cd ChatBot
cp .env.example .env
# Edit .env with API keys

# 2. Start services
make up

# 3. Verify
make health

# 4. Access
# Frontend: http://localhost:3001
# API: http://localhost:8000/api/docs
# GraphQL: http://localhost:8000/graphql
```

**First time?** See `docs/guides/QUICKSTART.md` for detailed setup.

---

## Repository Structure

```
ChatBot/
├── backend/                    # FastAPI Python backend
│   ├── app/
│   │   ├── agents/            # LangGraph agent workflows
│   │   ├── api/               # REST + GraphQL endpoints
│   │   ├── services/          # Business logic (document, RAG, LLM, audit, finetuning)
│   │   ├── models/            # SQLAlchemy ORM (database.py, database_enhanced.py)
│   │   ├── schemas/           # Pydantic models
│   │   ├── tasks/             # Celery tasks (finetuning_tasks.py)
│   │   └── main.py            # Entry point (main_enhanced.py for RBAC)
│   ├── migrations/            # Alembic DB migrations
│   └── tests/                 # Test suite
│
├── frontend/                   # Next.js 14 + TypeScript
│   └── src/
│       ├── components/        # React components (ChatInterface, FileUpload, etc.)
│       └── pages/             # Next.js pages (index.tsx, admin.tsx)
│
├── infrastructure/            # K8s, Argo CD, Istio, OPA configs
├── ml/                        # Feast, vLLM
├── observability/             # Tempo, OpenCost
├── docs/                      # Organized documentation
│   ├── guides/               # QUICKSTART, ADMIN_GUIDE, GRAPHQL_EXAMPLES
│   ├── architecture/         # MEMORY_HIERARCHY_GUIDE, DEPLOYMENT
│   ├── setup/                # LOCAL_LLM_SETUP, MULTI_MODEL_SETUP
│   ├── debugging/            # RAG_DEBUGGING_GUIDE, DEBUG_QUICK_REFERENCE
│   └── evaluation/           # EVALUATION_GUIDE, RAG_EVALUATION
│
├── scripts/                   # Utility scripts
│   ├── setup/                # setup-database.sh, start-services.sh
│   ├── testing/              # test-integration.sh
│   ├── debugging/            # diagnose-backend.sh, debug-rag.sh
│   └── maintenance/          # validate-services.sh
│
├── docker-compose.yml        # Local dev stack
├── Makefile                  # Common commands
└── .env.example              # Environment template
```

---

## Tech Stack

### Backend (Python 3.11)

| Category | Stack |
|----------|-------|
| **Framework** | FastAPI 0.111, Uvicorn 0.30, Pydantic 2.8 |
| **Database** | PostgreSQL 16 + pgvector, SQLAlchemy 2.0, Alembic 1.13 |
| **Storage** | MinIO 7.2, Redis 5.0 |
| **AI/LLM** | OpenAI 1.40, Anthropic 0.39, Sentence-Transformers 2.3, LangChain 0.2, LangGraph 0.2 |
| **Documents** | PyPDF2, python-docx, openpyxl, BeautifulSoup4 |
| **Scraping** | Playwright 1.41, httpx 0.27, trafilatura 1.6 |
| **Orchestration** | Prefect 3.0, Celery 5.3, pynvml 11.5, Optuna 3.5 |
| **Observability** | OpenTelemetry 1.25, Prometheus 0.20 |
| **GraphQL** | Strawberry 0.235 |

### Frontend (TypeScript)

| Category | Stack |
|----------|-------|
| **Framework** | Next.js 14.1, React 18.2, TypeScript 5.3 |
| **UI** | Tailwind 3.4, Lucide React 0.316, React Markdown 9.0 |
| **API** | GraphQL 16.8, Axios 1.6 |

### Infrastructure

| Category | Stack |
|----------|-------|
| **Containers** | Docker, K8s 1.28+, Skaffold, mirrord |
| **Service Mesh** | Istio Ambient, Envoy (Contour), OPA Gatekeeper |
| **CI/CD** | Argo CD, Tekton |
| **Observability** | Grafana, Tempo, Loki, Mimir, OpenCost |
| **ML** | Kube-Ray, vLLM, Feast |

---

## Architecture

### Backend: Layered Architecture
```
Request → API Layer → Service Layer → Data Layer → Database
         (routes/)   (services/)     (models/)
```

### Key Services

| Service | Purpose | File |
|---------|---------|------|
| **Document** | Upload, process, chunk, store (MinIO + PostgreSQL) | `document_service.py` |
| **Embedding** | Generate 384-dim vectors, cache in Redis | `embedding_service.py` |
| **RAG** | Memory hierarchy: session docs → all docs, vector search | `rag_service.py` |
| **LLM** | Multi-provider (OpenAI, Claude, Ollama), fallback, tracking | `llm_service.py` |
| **Audit** | Log actions, track usage, latency, errors | `audit_service.py` |
| **Fine-tuning** | Distributed training, GPU allocation | `services/finetuning/` |

### Frontend: Component Hierarchy
```
_app.tsx
└── index.tsx
    ├── ChatInterfaceEnhanced (session support)
    ├── FileUpload (drag-drop)
    ├── WebScraper
    ├── ModelSelector
    └── UploadedFilesList
```

**State Management**: Local state (useState), sessionId (localStorage), API (Axios/GraphQL)

### Dependency Injection Pattern
```python
from app.core.database import get_db
from sqlalchemy.orm import Session

@router.post("/api/v1/query")
async def query(query: QueryRequest, db: Session = Depends(get_db)):
    # Use db session
```

**Architecture Deep Dive**: See `docs/architecture/MEMORY_HIERARCHY_GUIDE.md` (600+ lines)

---

## Database

### Core Tables

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `documents` | Uploaded/scraped files | id, filename, file_path, source_type, processed |
| `document_chunks` | Text chunks with embeddings | document_id, content, embedding VECTOR(384) |
| `conversations` | Chat sessions | session_id, created_at |
| `messages` | Chat messages | conversation_id, role, content, sources, tokens_used |
| `users` | User accounts | username, email, role (RBAC) |
| `chat_sessions` | Session metadata | session_id, user_id, title |
| `session_documents` | Short-term memory | session_id, document_id (unique pair) |
| `audit_logs` | Audit trail | user_id, action, details, latency_ms |

### Vector Index (Critical for Performance)
```sql
CREATE INDEX idx_chunks_embedding ON document_chunks
USING ivfflat (embedding vector_cosine_ops);
```

### Migrations (Alembic)
```bash
cd backend

# Create migration
alembic revision --autogenerate -m "description"

# Apply
alembic upgrade head

# Rollback
alembic downgrade -1

# Status
alembic current
alembic history
```

---

## API Reference

### REST Endpoints (FastAPI)

**Base URL**: `http://localhost:8000`

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/api/v1/upload` | POST | Upload file (multipart/form-data) |
| `/api/v1/query` | POST | RAG query (JSON body) |
| `/api/v1/scrape` | POST | Web scraping job |
| `/api/v1/documents` | GET | List documents (query: session_id) |
| `/api/v1/admin/users` | GET | List users |
| `/api/v1/admin/audit-logs` | GET | Audit logs (query: limit, offset) |
| `/api/v1/finetuning/jobs` | GET/POST | Fine-tuning jobs |
| `/api/v1/finetuning/jobs/{id}/submit` | POST | Submit job to Celery queue |
| `/api/v1/finetuning/gpu/status` | GET | GPU availability |

**Full API Docs**: http://localhost:8000/api/docs (Swagger UI)

### GraphQL Endpoint

**URL**: `http://localhost:8000/graphql`

**Example Query**:
```graphql
query GetDocuments($sessionId: String) {
  documents(sessionId: $sessionId) {
    id filename fileType processed
  }
}
```

**Examples**: See `docs/guides/GRAPHQL_EXAMPLES.md`

---

## AI Assistant Rules

### ⚠️ CRITICAL: Read Before Any Code Changes

#### 1. Always Read Before Writing
- **NEVER** edit files without reading them first
- Check existing patterns and conventions
- Review related files for context

#### 2. Understand Context
- Read `STATUS.md` for current state
- Check recent commits: `git log -10 --oneline`
- Verify current branch: `git branch --show-current`

#### 3. Code Quality Standards
- **Python**: PEP 8, type hints, docstrings required
- **TypeScript**: Strict mode, functional components, proper interfaces
- Follow existing code patterns
- Add tests for new features (>80% coverage)

#### 4. Database Changes
- **NEVER** modify models without Alembic migration
- Test migrations locally before committing
- Check backward compatibility

#### 5. Security (OWASP)
- **NEVER** commit secrets/API keys
- Validate and sanitize all inputs
- Use parameterized queries (ORM)
- Try-except for external calls

#### 6. Git Workflow
- Create feature branches: `feature/<name>`
- Conventional commits: `feat:`, `fix:`, `docs:`, etc.
- Push to current branch (check first!)
- Never force push to main

#### 7. Testing Requirements
- Run `make test` before commits
- Maintain >80% coverage
- Critical paths (RAG, document processing) = 100%

#### 8. Performance
- Use async/await for I/O
- Cache where appropriate
- Avoid N+1 queries
- Profile before optimizing

#### 9. Documentation
- Update docs/ when adding features
- Keep CLAUDE.md current
- Add comments for complex logic

#### 10. Dependency Management
- Check compatibility before adding deps
- Update requirements.txt / package.json
- Document rationale in commit

---

## Common Tasks

### Adding an API Endpoint

```python
# 1. Schema (app/schemas/)
from pydantic import BaseModel

class FeatureRequest(BaseModel):
    param: str

class FeatureResponse(BaseModel):
    result: str

# 2. Service (app/services/)
class FeatureService:
    def __init__(self, db: Session):
        self.db = db

    async def process(self, req: FeatureRequest) -> FeatureResponse:
        # Logic here
        pass

# 3. Route (app/api/routes/ or main.py)
@router.post("/api/v1/feature", response_model=FeatureResponse)
async def feature_endpoint(req: FeatureRequest, db: Session = Depends(get_db)):
    return await FeatureService(db).process(req)

# 4. Test
def test_feature(client):
    response = client.post("/api/v1/feature", json={"param": "test"})
    assert response.status_code == 200
```

### Adding a Database Table

```python
# 1. Model (app/models/database.py)
class NewTable(Base):
    __tablename__ = "new_table"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)

# 2. Migration
cd backend
alembic revision --autogenerate -m "add new_table"

# 3. Review migrations/versions/xxx_add_new_table.py

# 4. Apply
alembic upgrade head
```

### Adding a Frontend Component

```typescript
// 1. Component (frontend/src/components/)
import React, { useState } from 'react';

interface Props {
  value: string;
}

export const NewComponent: React.FC<Props> = ({ value }) => {
  const [state, setState] = useState(value);
  return <input value={state} onChange={(e) => setState(e.target.value)} />;
};

// 2. Use in page
import { NewComponent } from '../components/NewComponent';

export default function Home() {
  return <NewComponent value="test" />;
}
```

---

## Commands

### Makefile

| Command | Purpose |
|---------|---------|
| `make up` | Start all services |
| `make down` | Stop all services |
| `make logs` | Show all logs |
| `make logs-backend` | Backend logs only |
| `make status` | Service status |
| `make health` | Health check |
| `make test` | Run all tests |
| `make build` | Build Docker images |
| `make shell-backend` | Open backend shell |
| `make db-shell` | PostgreSQL shell |
| `make format` | Format code (Black + Prettier) |
| `make lint` | Lint code |

**Full list**: `make help`

### Docker Compose

```bash
docker-compose ps                          # Running containers
docker-compose logs -f backend             # Follow backend logs
docker-compose restart backend             # Restart service
docker-compose build backend --no-cache    # Rebuild
docker-compose down -v                     # Clean slate (deletes data)
```

### Git

```bash
git branch --show-current                  # Current branch
git log -10 --oneline                      # Recent commits
git checkout -b feature/name               # New branch
git add . && git commit -m "feat: desc"    # Commit
git push -u origin feature/name            # Push
```

### Database

```bash
# Setup
./scripts/setup/setup-database.sh

# Migrations
cd backend
alembic upgrade head         # Apply
alembic downgrade -1         # Rollback
alembic current              # Current version

# Query
docker-compose exec postgres psql -U postgres -d ragchatbot -c "SELECT COUNT(*) FROM documents;"
```

---

## Troubleshooting

### Quick Diagnostics

```bash
# All services health
./scripts/maintenance/validate-services.sh

# Backend issues
./scripts/debugging/diagnose-backend.sh

# Document processing
./scripts/debugging/diagnose-documents.sh

# RAG pipeline
./scripts/debugging/debug-rag.sh
```

### Common Issues

| Issue | Diagnosis | Solution |
|-------|-----------|----------|
| **Backend won't start** | `docker-compose logs backend` | `docker-compose build backend --no-cache && docker-compose up -d backend` |
| **Database connection error** | `docker-compose exec postgres pg_isready` | `docker-compose restart postgres` |
| **Frontend build error** | Check logs | `cd frontend && rm -rf node_modules && npm install` |
| **Ollama unavailable** | `curl http://localhost:11434/api/tags` | `docker-compose exec ollama ollama pull mistral` |
| **Documents not processing** | `./scripts/debugging/diagnose-documents.sh` | Check MinIO access, document_service logs |
| **Vector search fails** | Check pgvector: `SELECT COUNT(*) FROM document_chunks WHERE embedding IS NOT NULL;` | Verify index exists, regenerate embeddings |

### Service Endpoints (Testing)

```bash
curl http://localhost:8000/health          # Backend
curl http://localhost:11434/api/tags       # Ollama

# Browser-based
http://localhost:3001                      # Frontend
http://localhost:9001                      # MinIO (minioadmin/minioadmin)
http://localhost:3000                      # Grafana (admin/admin)
http://localhost:8002                      # Redis Insight
```

### Reset Everything (Nuclear Option)

```bash
# WARNING: Deletes ALL data
docker-compose down -v
docker system prune -a -f
make up
./scripts/setup/setup-database.sh
```

---

## Additional Resources

### Documentation

| Category | Files |
|----------|-------|
| **Root** | README.md, CONTRIBUTING.md, STATUS.md |
| **Guides** | `docs/guides/` - QUICKSTART, ADMIN_GUIDE, GRAPHQL_EXAMPLES |
| **Architecture** | `docs/architecture/` - MEMORY_HIERARCHY_GUIDE, DEPLOYMENT |
| **Setup** | `docs/setup/` - LOCAL_LLM_SETUP, MULTI_MODEL_SETUP |
| **Debugging** | `docs/debugging/` - RAG_DEBUGGING_GUIDE, DEBUG_QUICK_REFERENCE |
| **Evaluation** | `docs/evaluation/` - EVALUATION_GUIDE, RAG_EVALUATION |

### External Links
- [FastAPI Docs](https://fastapi.tiangolo.com)
- [Next.js Docs](https://nextjs.org/docs)
- [pgvector](https://github.com/pgvector/pgvector)
- [LangChain](https://python.langchain.com)
- [Ollama](https://ollama.ai/docs)

### Local URLs
- Frontend: http://localhost:3001
- Backend API: http://localhost:8000
- Swagger UI: http://localhost:8000/api/docs
- GraphQL: http://localhost:8000/graphql
- Grafana: http://localhost:3000 (admin/admin)
- MinIO: http://localhost:9001 (minioadmin/minioadmin)
- Redis Insight: http://localhost:8002

---

## Version History

| Date | Version | Changes |
|------|---------|---------|
| 2025-11-14 | 1.0.0 | Initial comprehensive CLAUDE.md |
| 2025-11-16 | 1.1.0 | Repository reorganization (docs + scripts) |
| 2025-12-18 | 1.2.0 | Optimized: reduced 1615→~850 lines, improved scannability |

---

## Questions or Issues?

1. **Check this doc first** - Use TOC for navigation
2. **Review STATUS.md** - Current state and known issues
3. **Check organized docs** - `docs/setup/`, `docs/debugging/`, `docs/architecture/`, `docs/evaluation/`
4. **Review recent commits** - `git log -10 --oneline`
5. **Run diagnostics** - `./scripts/debugging/diagnose-*.sh`
6. **Check READMEs** - Each `docs/` subdirectory has navigation

---

**End of CLAUDE.md**
