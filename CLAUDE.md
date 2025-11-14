# CLAUDE.md - AI Assistant Development Guide

> **Last Updated**: 2025-11-14
> **Purpose**: Comprehensive guide for AI assistants working with this codebase

---

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [Repository Structure](#repository-structure)
3. [Tech Stack & Dependencies](#tech-stack--dependencies)
4. [Development Workflows](#development-workflows)
5. [Code Architecture](#code-architecture)
6. [Database Schema](#database-schema)
7. [API Endpoints](#api-endpoints)
8. [Testing Guidelines](#testing-guidelines)
9. [Deployment](#deployment)
10. [AI Assistant Guidelines](#ai-assistant-guidelines)
11. [Common Commands](#common-commands)
12. [Troubleshooting](#troubleshooting)

---

## Project Overview

### What This Project Does
This is an **Enterprise RAG (Retrieval-Augmented Generation) Chatbot** that combines document processing, semantic search, and LLM inference to provide intelligent question-answering capabilities with source attribution.

### Key Features
- **Document Processing**: Upload and process PDF, DOCX, TXT, JSON, MD files using Docling
- **Web Scraping**: Intelligent content extraction from URLs with Playwright
- **Vector Search**: Semantic search using PostgreSQL + pgvector (384-dimensional embeddings)
- **Multiple LLM Support**: OpenAI, Anthropic Claude, Ollama (local), vLLM
- **Memory Hierarchy**: Short-term (session) and long-term (all documents) memory
- **Semantic Caching**: Redis VSS for query result caching
- **Real-time Observability**: OpenTelemetry, Grafana, Tempo, Loki
- **GraphQL + REST APIs**: Dual API support with Strawberry GraphQL
- **Admin Dashboard**: User management, sessions, audit logs, usage metrics

### Current Status
- **Main Branch**: Production-ready code
- **Active Development**: Branch naming convention `claude/claude-md-*`
- **Last Major Update**: Memory hierarchy and audit logging system (see STATUS.md)

---

## Repository Structure

```
ChatBot/
├── backend/                    # FastAPI Python backend
│   ├── app/
│   │   ├── agents/            # LangGraph agent workflows
│   │   ├── api/               # API layer
│   │   │   ├── graphql/       # GraphQL schema and resolvers
│   │   │   ├── rest/          # REST API endpoints
│   │   │   └── routes/        # Route definitions
│   │   ├── core/              # Core configuration and database
│   │   ├── models/            # SQLAlchemy ORM models
│   │   │   ├── database.py           # Core tables
│   │   │   └── database_enhanced.py  # RBAC and audit tables
│   │   ├── schemas/           # Pydantic request/response models
│   │   ├── services/          # Business logic layer
│   │   │   ├── document_service.py   # File upload & processing
│   │   │   ├── embedding_service.py  # Vector embeddings
│   │   │   ├── llm_service.py        # LLM client management
│   │   │   ├── rag_service.py        # RAG query pipeline
│   │   │   ├── scraper_service.py    # Web scraping
│   │   │   └── audit_service.py      # Audit logging
│   │   ├── utils/             # Helper utilities
│   │   ├── main.py            # Application entry point
│   │   └── main_enhanced.py   # Enhanced version with RBAC
│   ├── migrations/            # Alembic database migrations
│   ├── tests/                 # Backend test suite
│   └── requirements.txt       # Python dependencies
│
├── frontend/                   # Next.js 14 React frontend
│   ├── src/
│   │   ├── components/        # React components
│   │   │   ├── ChatInterface.tsx         # Main chat UI
│   │   │   ├── ChatInterfaceEnhanced.tsx # With session support
│   │   │   ├── FileUpload.tsx            # File upload UI
│   │   │   ├── ModelSelector.tsx         # LLM model picker
│   │   │   ├── WebScraper.tsx            # Web scraping UI
│   │   │   └── UploadedFilesList.tsx     # Document list
│   │   ├── pages/             # Next.js pages
│   │   │   ├── index.tsx      # Main application page
│   │   │   ├── admin.tsx      # Admin dashboard
│   │   │   └── _app.tsx       # App wrapper
│   │   └── styles/            # CSS and Tailwind styles
│   └── package.json           # Node.js dependencies
│
├── infrastructure/            # Kubernetes and cloud configs
│   ├── kubernetes/           # K8s manifests
│   ├── argocd/              # GitOps configs
│   ├── istio/               # Service mesh configs
│   ├── contour/             # Ingress configs
│   └── opa/                 # Policy enforcement
│
├── ml/                       # ML/MLOps components
│   ├── feast/               # Feature store configs
│   └── vllm/                # vLLM deployment configs
│
├── observability/            # Monitoring stack
│   ├── tempo/               # Distributed tracing
│   └── opencost/            # Cost monitoring
│
├── devops/                   # DevOps tooling
│   └── skaffold/            # Local K8s development
│
├── scripts/                  # Utility scripts
│
├── docker-compose.yml        # Local development stack
├── Makefile                  # Common development commands
├── .env.example              # Environment variable template
├── .gitignore                # Git ignore patterns
│
└── Documentation Files:
    ├── README.md                      # Main project documentation
    ├── CONTRIBUTING.md                # Contribution guidelines
    ├── DEPLOYMENT.md                  # Deployment instructions
    ├── ADMIN_GUIDE.md                 # Admin dashboard guide
    ├── MEMORY_HIERARCHY_GUIDE.md      # Architecture deep dive
    ├── QUICKSTART.md                  # Quick start guide
    ├── STATUS.md                      # Current project status
    └── CLAUDE.md                      # This file
```

---

## Tech Stack & Dependencies

### Backend (Python 3.11)

#### Core Framework
- **FastAPI 0.111.0**: Async web framework, main API server
- **Uvicorn 0.30.0**: ASGI server
- **Pydantic 2.8.2**: Data validation and settings management
- **Strawberry GraphQL 0.235.0**: GraphQL implementation

#### Database & Storage
- **PostgreSQL 16 + pgvector**: Vector database (384-dimensional embeddings)
- **SQLAlchemy 2.0.25**: ORM framework
- **Alembic 1.13.1**: Database migrations
- **Redis 5.0.1**: Semantic caching and sessions
- **MinIO 7.2.3**: S3-compatible object storage

#### AI & LLM
- **OpenAI 1.40.0**: OpenAI API client
- **Anthropic 0.39.0**: Claude API client
- **Sentence Transformers 2.3.1**: Embedding generation
- **LangChain 0.2.16**: LLM framework and agent orchestration
- **LangGraph 0.2.16**: Agent workflow DAGs

#### Document Processing
- **PyPDF2 3.0.1**: PDF text extraction
- **python-docx 1.1.0**: Word document parsing
- **python-pptx 0.6.23**: PowerPoint parsing
- **openpyxl 3.1.2**: Excel file parsing
- **BeautifulSoup4 4.12.3**: HTML parsing

#### Web Scraping
- **Playwright 1.41.0**: Browser automation
- **httpx 0.27.0**: Async HTTP client
- **trafilatura 1.6.3**: Content extraction

#### Workflow & Orchestration
- **Prefect 3.0.0**: Workflow orchestration

#### Observability
- **OpenTelemetry API/SDK 1.25.0**: Distributed tracing
- **Prometheus Client 0.20.0**: Metrics

### Frontend (TypeScript)

#### Core Framework
- **Next.js 14.1.0**: React framework with SSR
- **React 18.2.0**: UI library
- **TypeScript 5.3.3**: Type-safe JavaScript

#### UI & Styling
- **Tailwind CSS 3.4.1**: Utility-first CSS framework
- **Lucide React 0.316.0**: Icon library
- **React Markdown 9.0.1**: Markdown rendering
- **React Syntax Highlighter 15.5.0**: Code highlighting

#### API Communication
- **GraphQL 16.8.1**: GraphQL client
- **graphql-request 6.1.0**: GraphQL queries
- **Axios 1.6.7**: HTTP client

#### File Upload
- **React Dropzone 14.2.3**: Drag-and-drop file uploads

### Infrastructure

#### Container Orchestration
- **Docker & Docker Compose**: Local development
- **Kubernetes 1.28+**: Production orchestration
- **Skaffold**: Local K8s development
- **mirrord**: Remote debugging

#### Service Mesh & Networking
- **Istio Ambient Mesh**: Zero-trust networking
- **Envoy (Contour)**: Ingress gateway
- **OPA Gatekeeper**: Policy enforcement

#### CI/CD & GitOps
- **Argo CD**: GitOps continuous delivery
- **Tekton**: CI/CD pipelines

#### Observability
- **Grafana**: Unified visualization
- **Grafana Tempo**: Trace backend
- **Grafana Loki**: Log aggregation
- **Grafana Mimir**: Metrics storage
- **OpenCost**: Cost monitoring

#### ML Infrastructure
- **Kube-Ray**: Distributed Ray clusters
- **vLLM**: GPU-accelerated LLM inference
- **Feast**: Feature store

---

## Development Workflows

### Local Development Setup

1. **Clone Repository**
   ```bash
   git clone <repository-url>
   cd ChatBot
   ```

2. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

3. **Start Services**
   ```bash
   # Using Makefile (recommended)
   make up

   # Or using Docker Compose directly
   docker-compose up -d
   ```

4. **Verify Services**
   ```bash
   make status
   make health
   ```

### Branch Management

#### Branch Naming Convention
- Feature branches: `feature/<feature-name>`
- Bug fixes: `fix/<bug-description>`
- Claude AI sessions: `claude/claude-md-<session-id>`

#### Current Development Branch
```bash
# Always check the active branch before making changes
git branch --show-current

# Current active branch: claude/claude-md-mhyl086tqdwcgbjq-01XF7tJdophxiTiCxWsfCZ8S
```

### Commit Guidelines

Follow **Conventional Commits** format:

```
<type>: <description>

[optional body]

[optional footer]
```

#### Commit Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, no logic change)
- `refactor`: Code refactoring
- `test`: Test additions or changes
- `chore`: Build process or tooling changes
- `perf`: Performance improvements

#### Examples
```bash
feat: add semantic caching for embeddings
fix: resolve database connection timeout
docs: update API documentation
refactor: simplify RAG service query logic
```

### Code Style

#### Python (Backend)
- **Style Guide**: PEP 8
- **Formatter**: Black
- **Linter**: Pylint
- **Type Hints**: Required for all functions
- **Docstrings**: Required for all public functions

```python
from typing import List, Dict, Optional

def process_document(
    file_path: str,
    chunk_size: int = 512
) -> List[Dict[str, Any]]:
    """
    Process a document and split it into chunks.

    Args:
        file_path: Path to the document file
        chunk_size: Size of each chunk in characters

    Returns:
        List of chunks with metadata
    """
    pass
```

#### TypeScript/React (Frontend)
- **Style Guide**: Airbnb React/JSX
- **Linter**: ESLint
- **Formatter**: Prettier (via ESLint)
- **Components**: Functional components with hooks
- **Type Safety**: Strict TypeScript mode

```typescript
interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  sources?: Source[];
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  sessionId
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  // Component logic
};
```

### Testing Workflow

#### Backend Tests
```bash
# Run all tests
make test-backend

# Run with coverage
cd backend && pytest tests/ -v --cov=app --cov-report=html

# Run specific test file
pytest tests/test_document_service.py -v
```

#### Frontend Tests
```bash
# Run all tests
make test-frontend

# Run in watch mode
cd frontend && npm test

# Run E2E tests
npm run test:e2e
```

#### Integration Tests
```bash
# Ensure services are running
make up

# Run integration tests
./test-integration.sh
```

### Code Review Process

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**
   - Write code
   - Add tests (maintain >80% coverage)
   - Update documentation

3. **Run Tests & Linting**
   ```bash
   make test
   make lint
   ```

4. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

5. **Push to Remote**
   ```bash
   git push -u origin feature/your-feature-name
   ```

6. **Create Pull Request**
   - Fill out PR template
   - Link related issues
   - Request reviews

---

## Code Architecture

### Backend Architecture Patterns

#### Layered Architecture
```
Request → API Layer → Service Layer → Data Layer → Database
```

1. **API Layer** (`app/api/`)
   - REST endpoints (`routes/`)
   - GraphQL schema (`graphql/`)
   - Request validation (Pydantic schemas)

2. **Service Layer** (`app/services/`)
   - Business logic
   - External API calls
   - Data transformation

3. **Data Layer** (`app/models/`)
   - SQLAlchemy ORM models
   - Database operations

#### Key Services

##### Document Service (`document_service.py`)
- Handles file uploads
- Processes documents (PDF, DOCX, etc.)
- Chunks text for embedding
- Stores in MinIO + PostgreSQL

##### Embedding Service (`embedding_service.py`)
- Generates 384-dimensional embeddings
- Uses sentence-transformers
- Caches embeddings in Redis

##### RAG Service (`rag_service.py`)
- **Memory Hierarchy**:
  1. Check short-term memory (session documents) FIRST
  2. Fallback to long-term memory (all documents) if needed
- Vector similarity search
- Context assembly
- Source attribution

##### LLM Service (`llm_service.py`)
- Multi-provider support (OpenAI, Anthropic, Ollama)
- Automatic fallback chain
- Token usage tracking
- Cost calculation

##### Audit Service (`audit_service.py`)
- Logs all user actions
- Tracks API usage
- Records latency and errors

#### Dependency Injection
Services use dependency injection for testability:

```python
from app.core.database import get_db
from sqlalchemy.orm import Session

@router.post("/api/v1/query")
async def query_documents(
    query: QueryRequest,
    db: Session = Depends(get_db)
):
    # Use db session
    pass
```

### Frontend Architecture

#### Component Hierarchy
```
_app.tsx
└── index.tsx (Main Page)
    ├── ChatInterface / ChatInterfaceEnhanced
    ├── FileUpload
    ├── WebScraper
    ├── ModelSelector
    └── UploadedFilesList
```

#### State Management
- **Local State**: useState for component-specific state
- **Session Management**: sessionId stored in localStorage
- **API Communication**: Axios for REST, graphql-request for GraphQL

#### Component Pattern
```typescript
// Presentational component
export const ChatMessage: React.FC<{ message: Message }> = ({ message }) => {
  return <div>{message.content}</div>;
};

// Container component with logic
export const ChatInterface: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);

  const sendMessage = async (content: string) => {
    // API call logic
  };

  return <ChatMessage message={messages[0]} />;
};
```

---

## Database Schema

### Core Tables

#### Documents
```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(512) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_size INTEGER NOT NULL,
    source_type VARCHAR(50) NOT NULL,  -- 'upload' or 'scrape'
    source_url VARCHAR(1024),
    meta_info JSONB,
    upload_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed BOOLEAN DEFAULT FALSE,
    processing_error TEXT
);
```

#### Document Chunks
```sql
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(384),  -- pgvector type
    meta_info JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Vector similarity search index
CREATE INDEX idx_chunks_embedding ON document_chunks
USING ivfflat (embedding vector_cosine_ops);
```

#### Conversations & Messages
```sql
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    meta_info JSONB
);

CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL,  -- 'user' or 'assistant'
    content TEXT NOT NULL,
    sources JSONB,
    model_used VARCHAR(100),
    tokens_used INTEGER,
    latency_ms FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Enhanced Tables (RBAC & Audit)

#### Users
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    role VARCHAR(50) NOT NULL,  -- 'admin', 'user', 'readonly'
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### Chat Sessions
```sql
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(255) UNIQUE NOT NULL,
    user_id UUID REFERENCES users(id),
    title VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);
```

#### Session Documents (Short-term Memory)
```sql
CREATE TABLE session_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(255) REFERENCES chat_sessions(session_id),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(session_id, document_id)
);
```

#### Audit Logs
```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    session_id VARCHAR(255),
    action VARCHAR(100) NOT NULL,  -- 'upload', 'query', 'scrape', etc.
    details JSONB,
    ip_address VARCHAR(50),
    latency_ms FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Database Migrations

Migrations are managed with Alembic:

```bash
# Create new migration
cd backend
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

---

## API Endpoints

### REST API (FastAPI)

#### Base URL
- Local: `http://localhost:8000`
- Production: Configured in environment

#### Health Check
```
GET /health
GET /api/v1/health
```

#### Document Upload
```
POST /api/v1/upload
Content-Type: multipart/form-data

Body:
- file: File
- session_id: string (optional)

Response:
{
  "document_id": "uuid",
  "filename": "string",
  "status": "processing"
}
```

#### Query RAG System
```
POST /api/v1/query
Content-Type: application/json

Body:
{
  "query": "string",
  "session_id": "string",
  "model": "gpt-4" | "claude-3" | "ollama/mistral",
  "top_k": 5
}

Response:
{
  "answer": "string",
  "sources": [
    {
      "document_id": "uuid",
      "filename": "string",
      "content": "string",
      "score": 0.95
    }
  ],
  "model_used": "string",
  "tokens": 1234,
  "latency_ms": 567.89
}
```

#### Web Scraping
```
POST /api/v1/scrape
Content-Type: application/json

Body:
{
  "urls": ["https://example.com"],
  "scrape_prompt": "string (optional)",
  "session_id": "string (optional)"
}

Response:
{
  "job_id": "uuid",
  "status": "processing"
}
```

#### List Documents
```
GET /api/v1/documents?session_id={session_id}

Response:
{
  "documents": [
    {
      "id": "uuid",
      "filename": "string",
      "file_type": "pdf",
      "upload_date": "2024-01-01T00:00:00Z",
      "processed": true
    }
  ]
}
```

#### Admin Endpoints
```
GET /api/v1/admin/users
GET /api/v1/admin/sessions
GET /api/v1/admin/audit-logs?limit=100&offset=0
GET /api/v1/admin/usage-metrics?start_date=2024-01-01&end_date=2024-12-31
GET /api/v1/sessions/{session_id}
```

### GraphQL API (Strawberry)

#### Endpoint
```
POST /graphql
GET /graphql (GraphQL Playground)
```

#### Example Queries
```graphql
# Query documents
query GetDocuments($sessionId: String) {
  documents(sessionId: $sessionId) {
    id
    filename
    fileType
    uploadDate
    processed
  }
}

# Query RAG
mutation QueryRAG($input: QueryInput!) {
  query(input: $input) {
    answer
    sources {
      documentId
      filename
      content
      score
    }
    modelUsed
    tokens
    latencyMs
  }
}
```

---

## Testing Guidelines

### Test Coverage Requirements
- **Minimum Coverage**: 80%
- **Critical Paths**: 100% (RAG pipeline, document processing)

### Backend Testing

#### Unit Tests
Located in `backend/tests/`

```python
# tests/test_document_service.py
import pytest
from app.services.document_service import DocumentService

@pytest.fixture
def document_service():
    return DocumentService()

def test_chunk_document(document_service):
    text = "Long document text..."
    chunks = document_service.chunk_text(text, chunk_size=512)

    assert len(chunks) > 0
    assert all(len(chunk) <= 512 for chunk in chunks)
```

#### Integration Tests
```python
# tests/test_rag_pipeline.py
def test_end_to_end_rag(client, test_document):
    # Upload document
    response = client.post(
        "/api/v1/upload",
        files={"file": test_document}
    )
    assert response.status_code == 200

    # Query document
    response = client.post(
        "/api/v1/query",
        json={"query": "What is this document about?"}
    )
    assert response.status_code == 200
    assert "answer" in response.json()
```

### Frontend Testing

#### Component Tests
```typescript
// __tests__/ChatInterface.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { ChatInterface } from '../components/ChatInterface';

describe('ChatInterface', () => {
  it('renders chat input', () => {
    render(<ChatInterface />);
    const input = screen.getByPlaceholderText(/ask a question/i);
    expect(input).toBeInTheDocument();
  });

  it('sends message on submit', async () => {
    render(<ChatInterface />);
    const input = screen.getByPlaceholderText(/ask a question/i);
    const button = screen.getByRole('button', { name: /send/i });

    fireEvent.change(input, { target: { value: 'Test query' } });
    fireEvent.click(button);

    // Assert message sent
  });
});
```

### Running Tests

```bash
# All tests
make test

# Backend only
make test-backend

# Frontend only
make test-frontend

# With coverage report
cd backend && pytest --cov=app --cov-report=html
cd frontend && npm test -- --coverage
```

---

## Deployment

### Local Development (Docker Compose)

```bash
# Start all services
make up

# Check status
make status

# View logs
make logs

# Stop services
make down
```

### Kubernetes Deployment

#### Prerequisites
- Kubernetes cluster (1.28+)
- kubectl configured
- Helm 3+
- Istio installed

#### Deploy with kubectl
```bash
# Apply base manifests
kubectl apply -k infrastructure/kubernetes/base/

# Apply production overlays
kubectl apply -k infrastructure/kubernetes/overlays/prod/
```

#### Deploy with Argo CD
```bash
# Apply Argo CD application
kubectl apply -f infrastructure/argocd/application.yaml

# Monitor deployment
kubectl get applications -n argocd
```

#### Deploy with Skaffold (Development)
```bash
cd devops/skaffold
skaffold dev  # Hot reload
skaffold run  # One-time deploy
```

---

## AI Assistant Guidelines

### Critical Rules for AI Development

#### 1. Always Read Before Writing
- **NEVER** edit a file without reading it first
- Use `Read` tool to understand current state
- Check for existing patterns and conventions

#### 2. Understand Context
- Read STATUS.md for current project state
- Check recent commits: `git log -10 --oneline`
- Review related files before making changes

#### 3. Maintain Code Quality
- Follow existing code patterns
- Add type hints (Python) and types (TypeScript)
- Write docstrings and comments
- Add tests for new features

#### 4. Database Changes
- **NEVER** modify database models without creating migration
- Test migrations locally before committing
- Consider backward compatibility

#### 5. Dependency Management
- Check compatibility before adding dependencies
- Update requirements.txt or package.json
- Document why dependency was added

#### 6. Error Handling
- Always include try-except blocks for external calls
- Log errors with appropriate context
- Return meaningful error messages to users

#### 7. Security Considerations
- **NEVER** commit secrets or API keys
- Validate and sanitize all user inputs
- Use parameterized queries (SQLAlchemy ORM)
- Follow OWASP security best practices

#### 8. Performance
- Use async/await for I/O operations
- Implement caching where appropriate
- Optimize database queries (avoid N+1)
- Profile before optimizing

#### 9. Git Workflow
- Create feature branches for changes
- Write meaningful commit messages
- Push to designated branch (check current branch)
- Never force push to main/master

#### 10. Testing Requirements
- Write tests for new features
- Run test suite before committing: `make test`
- Ensure tests pass in CI/CD pipeline

### Common Development Tasks

#### Adding a New API Endpoint

1. **Define Pydantic Schema** (`app/schemas/`)
```python
from pydantic import BaseModel

class NewFeatureRequest(BaseModel):
    param1: str
    param2: int

class NewFeatureResponse(BaseModel):
    result: str
    status: str
```

2. **Implement Service Logic** (`app/services/`)
```python
class NewFeatureService:
    def __init__(self, db: Session):
        self.db = db

    async def process(self, request: NewFeatureRequest) -> NewFeatureResponse:
        # Business logic here
        pass
```

3. **Create API Route** (`app/api/routes/` or `app/main.py`)
```python
@router.post("/api/v1/new-feature", response_model=NewFeatureResponse)
async def new_feature_endpoint(
    request: NewFeatureRequest,
    db: Session = Depends(get_db)
):
    service = NewFeatureService(db)
    return await service.process(request)
```

4. **Add Tests**
```python
def test_new_feature(client):
    response = client.post(
        "/api/v1/new-feature",
        json={"param1": "test", "param2": 123}
    )
    assert response.status_code == 200
```

#### Adding a Database Table

1. **Define Model** (`app/models/database.py`)
```python
class NewTable(Base):
    __tablename__ = "new_table"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

2. **Create Migration**
```bash
cd backend
alembic revision --autogenerate -m "add new_table"
```

3. **Review and Apply Migration**
```bash
# Review generated migration in migrations/versions/
alembic upgrade head
```

#### Adding a Frontend Component

1. **Create Component** (`frontend/src/components/`)
```typescript
import React, { useState } from 'react';

interface NewComponentProps {
  initialValue: string;
}

export const NewComponent: React.FC<NewComponentProps> = ({ initialValue }) => {
  const [value, setValue] = useState(initialValue);

  return (
    <div className="p-4">
      <input
        value={value}
        onChange={(e) => setValue(e.target.value)}
        className="border rounded px-3 py-2"
      />
    </div>
  );
};
```

2. **Add to Page**
```typescript
import { NewComponent } from '../components/NewComponent';

export default function Home() {
  return (
    <div>
      <NewComponent initialValue="test" />
    </div>
  );
}
```

### Debugging Tips

#### Backend Issues
```bash
# Check backend logs
make logs-backend

# Check specific error
docker-compose logs backend | grep ERROR

# Access backend shell
make shell-backend

# Check database
make db-shell
```

#### Frontend Issues
```bash
# Check frontend logs
make logs-frontend

# Rebuild frontend
docker-compose build frontend
docker-compose up -d frontend
```

#### Database Issues
```bash
# Check PostgreSQL status
docker-compose exec postgres pg_isready

# Query database
docker-compose exec postgres psql -U postgres -d ragchatbot -c "SELECT COUNT(*) FROM documents;"

# Check pgvector extension
docker-compose exec postgres psql -U postgres -d ragchatbot -c "SELECT * FROM pg_extension WHERE extname='vector';"
```

---

## Common Commands

### Makefile Commands

```bash
make help              # Show all available commands
make install           # Install dependencies
make up                # Start all services
make down              # Stop all services
make down-v            # Stop services and remove volumes
make logs              # Show all logs
make logs-backend      # Show backend logs only
make logs-frontend     # Show frontend logs only
make status            # Show service status
make health            # Check service health
make test              # Run all tests
make test-backend      # Run backend tests
make test-frontend     # Run frontend tests
make build             # Build Docker images
make rebuild           # Rebuild without cache
make shell-backend     # Open backend shell
make shell-frontend    # Open frontend shell
make db-shell          # Open PostgreSQL shell
make redis-cli         # Open Redis CLI
make format            # Format code (Black + Prettier)
make lint              # Lint code (Pylint + ESLint)
make deploy-k8s        # Deploy to Kubernetes
make backup-db         # Backup PostgreSQL database
```

### Docker Commands

```bash
# View running containers
docker-compose ps

# Restart specific service
docker-compose restart backend

# Rebuild specific service
docker-compose build backend
docker-compose up -d backend

# Remove all volumes (clean slate)
docker-compose down -v
docker system prune -a -f
```

### Git Commands

```bash
# Check current branch
git branch --show-current

# View recent commits
git log -10 --oneline

# Create feature branch
git checkout -b feature/new-feature

# Stage and commit changes
git add .
git commit -m "feat: add new feature"

# Push to remote
git push -u origin feature/new-feature

# View changes
git diff
git status
```

### Database Commands

```bash
# Create database and apply migrations
./setup-database.sh

# Manual migration
cd backend
alembic upgrade head

# Rollback migration
alembic downgrade -1

# Check migration history
alembic history
alembic current
```

---

## Troubleshooting

### Common Issues

#### 1. Backend Won't Start

**Symptom**: Backend container keeps restarting

**Diagnosis**:
```bash
docker-compose logs backend
./diagnose-backend.sh
```

**Common Causes**:
- Missing dependencies: Check requirements.txt
- Database not ready: Wait for postgres healthcheck
- Import errors: Check Python syntax and imports
- Port conflicts: Check if port 8000 is in use

**Solution**:
```bash
# Rebuild backend
docker-compose build backend --no-cache
docker-compose up -d backend

# Check logs
docker-compose logs -f backend
```

#### 2. Database Connection Errors

**Symptom**: "Could not connect to database"

**Diagnosis**:
```bash
docker-compose logs postgres
docker-compose exec postgres pg_isready
```

**Solution**:
```bash
# Restart PostgreSQL
docker-compose restart postgres

# Reset database (WARNING: loses data)
docker-compose down -v postgres
docker-compose up -d postgres
./setup-database.sh
```

#### 3. Frontend Build Errors

**Symptom**: "Error: Cannot find module..."

**Solution**:
```bash
# Reinstall dependencies
cd frontend
rm -rf node_modules package-lock.json
npm install

# Or rebuild container
docker-compose build frontend --no-cache
docker-compose up -d frontend
```

#### 4. LLM Service Not Working

**Symptom**: "LLM service unavailable"

**Check Ollama**:
```bash
curl http://localhost:11434/api/tags
docker-compose logs ollama
```

**Solution**:
```bash
# Pull a model (first time)
docker-compose exec ollama ollama pull mistral

# Restart Ollama
docker-compose restart ollama
```

#### 5. Documents Not Processing

**Symptom**: Documents uploaded but not searchable

**Diagnosis**:
```bash
./check-documents.sh
./diagnose-documents.sh
```

**Check Database**:
```bash
docker-compose exec postgres psql -U postgres -d ragchatbot -c \
  "SELECT filename, processed, processing_error FROM documents;"
```

**Solution**:
- Check MinIO access: http://localhost:9001
- Check document_service.py logs
- Verify embeddings are being generated

#### 6. Vector Search Not Working

**Symptom**: No relevant results returned

**Check pgvector**:
```bash
docker-compose exec postgres psql -U postgres -d ragchatbot -c \
  "SELECT COUNT(*) FROM document_chunks WHERE embedding IS NOT NULL;"
```

**Check Index**:
```bash
docker-compose exec postgres psql -U postgres -d ragchatbot -c \
  "SELECT * FROM pg_indexes WHERE tablename='document_chunks';"
```

### Diagnostic Scripts

```bash
./diagnose-backend.sh        # Backend health check
./diagnose-documents.sh      # Document processing status
./diagnose-llama.sh          # LLM service status
./validate-services.sh       # All services health check
./check-documents.sh         # Document database status
./check-backend-errors.sh    # Backend error logs
```

### Service Endpoints for Testing

```bash
# Backend health
curl http://localhost:8000/health

# Ollama status
curl http://localhost:11434/api/tags

# MinIO (login via browser)
open http://localhost:9001  # minioadmin/minioadmin

# Grafana (login via browser)
open http://localhost:3000  # admin/admin

# Redis Insight
open http://localhost:8002
```

### Reset Everything (Clean Slate)

```bash
# WARNING: This will delete ALL data
docker-compose down -v
docker system prune -a -f
make up
./setup-database.sh
```

---

## Additional Resources

### Documentation Files
- **README.md**: Main project documentation
- **CONTRIBUTING.md**: Contribution guidelines
- **DEPLOYMENT.md**: Detailed deployment instructions
- **ADMIN_GUIDE.md**: Admin dashboard usage
- **MEMORY_HIERARCHY_GUIDE.md**: Architecture deep dive (600+ lines)
- **QUICKSTART.md**: Quick reference guide
- **STATUS.md**: Current project status

### External Documentation
- FastAPI: https://fastapi.tiangolo.com
- Next.js: https://nextjs.org/docs
- PostgreSQL + pgvector: https://github.com/pgvector/pgvector
- LangChain: https://python.langchain.com
- Ollama: https://ollama.ai/docs

### Service URLs (Local Development)
- Frontend: http://localhost:3001
- Backend API: http://localhost:8000
- API Docs (Swagger): http://localhost:8000/api/docs
- GraphQL Playground: http://localhost:8000/graphql
- Grafana: http://localhost:3000 (admin/admin)
- MinIO Console: http://localhost:9001 (minioadmin/minioadmin)
- Redis Insight: http://localhost:8002

---

## Version History

| Date       | Version | Changes                                      |
|------------|---------|----------------------------------------------|
| 2025-11-14 | 1.0.0   | Initial comprehensive CLAUDE.md created      |

---

## Questions or Issues?

If you encounter issues or have questions:
1. Check this documentation first
2. Review STATUS.md for known issues
3. Check existing documentation in the repository
4. Review recent git commits for context
5. Run diagnostic scripts for debugging

---

**End of CLAUDE.md**
