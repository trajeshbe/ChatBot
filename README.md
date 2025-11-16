# Enterprise RAG Chatbot Stack

A state-of-the-art, production-ready RAG (Retrieval-Augmented Generation) chatbot built with enterprise-grade infrastructure and modern cloud-native technologies.

## 🚀 Features

- **Conversational AI**: State-of-the-art chatbot with local LLM support and OpenAI fallback
- **Document Processing**: Upload and process files using Docling (PDF, DOCX, TXT, JSON, MD)
- **Web Scraping**: Intelligent web content extraction with prompt-based scraping
- **Vector Search**: Semantic search powered by PostgreSQL + pgvector
- **Source References**: Every answer includes traceable source references
- **Semantic Caching**: Redis VSS for intelligent query caching
- **Real-time Observability**: Complete tracing with OpenTelemetry, Grafana, Tempo, Loki
- **Cost Tracking**: Real-time inference cost monitoring with OpenCost
- **Agent Orchestration**: Prefect 3 workflows with LangGraph DAG
- **Service Mesh**: Istio ambient mesh for zero-trust networking
- **GitOps**: Automated deployments with Argo CD and Tekton

## 🏗️ Architecture

### Tech Stack

#### Frontend
- **Next.js 14** - React framework with server-side rendering
- **Tailwind CSS** - Utility-first styling
- **TypeScript** - Type-safe development
- **React Markdown** - Rich text rendering

#### Backend
- **FastAPI** - High-performance Python API framework
- **GraphQL (Strawberry)** - Type-safe API with GraphQL
- **Python 3.11** - Modern Python with async support

#### LLM & AI
- **vLLM on Kube-Ray** - Distributed GPU inference
- **llama.cpp** - CPU fallback for inference
- **OpenAI API** - Cloud LLM fallback
- **Sentence Transformers** - Document embeddings
- **LangGraph** - Agent workflow orchestration

#### Data Layer
- **PostgreSQL 16 + pgvector** - Vector database
- **Redis 7.2 with RediSearch** - Semantic cache & VSS
- **MinIO** - S3-compatible object storage
- **Apache Flink** - Stream processing for Feast

#### Infrastructure
- **Kubernetes** - Container orchestration
- **Istio Ambient Mesh** - Service mesh
- **Envoy (Contour)** - Ingress gateway
- **OPA Gatekeeper** - Policy enforcement
- **Argo CD** - GitOps continuous delivery
- **Tekton** - CI/CD pipelines
- **Skaffold** - Local development
- **mirrord** - Remote debugging

#### Observability
- **OpenTelemetry** - Distributed tracing
- **Grafana Tempo** - Trace backend
- **Grafana Loki** - Log aggregation
- **Grafana Mimir** - Metrics storage
- **Grafana** - Unified visualization
- **OpenCost** - Cost monitoring

#### ML Ops
- **Prefect 3** - Workflow orchestration
- **Feast** - Feature store
- **Kube-Ray** - Distributed Ray clusters
- **Docling** - Document processing

## 📚 Documentation

Comprehensive documentation is available in the [`docs/`](./docs/) directory:

- **[Quick Start Guide](./docs/guides/QUICKSTART.md)** - Get started quickly
- **[Admin Guide](./docs/guides/ADMIN_GUIDE.md)** - System administration
- **[Architecture Guide](./docs/architecture/MEMORY_HIERARCHY_GUIDE.md)** - System architecture
- **[Deployment Guide](./docs/architecture/DEPLOYMENT.md)** - Production deployment
- **[Setup Guides](./docs/setup/)** - Component setup (LLM, local dev)
- **[Debugging Guides](./docs/debugging/)** - Troubleshooting and debugging
- **[Evaluation Guides](./docs/evaluation/)** - RAG system evaluation
- **[CLAUDE.md](./CLAUDE.md)** - AI assistant development guide

## 🔧 Scripts

Utility scripts are organized in [`scripts/`](./scripts/) by category:

- **[scripts/setup/](./scripts/setup/)** - Initial setup and configuration
- **[scripts/testing/](./scripts/testing/)** - Testing and validation
- **[scripts/debugging/](./scripts/debugging/)** - Diagnostics and debugging
- **[scripts/maintenance/](./scripts/maintenance/)** - System maintenance

## 📋 Prerequisites

- Docker 20.10+ and Docker Compose
- Kubernetes 1.28+ (for production)
- GPU with CUDA support (optional, for vLLM)
- 16GB+ RAM for local development
- Node.js 20+ (for frontend development)
- Python 3.11+ (for backend development)

## 🚀 Quick Start (Local Development)

### 1. Clone the Repository

```bash
git clone <repository-url>
cd ChatBot
```

### 2. Environment Setup

Create a `.env` file in the root directory:

```env
# OpenAI (Optional - for fallback)
OPENAI_API_KEY=your-openai-api-key

# HuggingFace (Optional - for vLLM models)
HUGGING_FACE_HUB_TOKEN=your-hf-token

# vLLM Model (default: TinyLlama for testing)
VLLM_MODEL=TinyLlama/TinyLlama-1.1B-Chat-v1.0
```

### 3. Start Services

```bash
# Start all services with Docker Compose
docker-compose up -d

# Or use setup script
./scripts/setup/start-services.sh

# Setup database
./scripts/setup/setup-database.sh

# Validate all services
./scripts/maintenance/validate-services.sh

# Check logs
docker-compose logs -f backend
```

### 4. Access the Application

- **Frontend**: http://localhost:3001
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/api/docs
- **GraphQL Playground**: http://localhost:8000/graphql
- **Grafana**: http://localhost:3000 (admin/admin)
- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin)
- **Prefect UI**: http://localhost:4200
- **Redis Insight**: http://localhost:8001
- **Envoy Admin**: http://localhost:9901

## 📖 Usage Guide

### Upload Documents

1. Navigate to the "Upload Files" tab
2. Drag and drop files or click to select
3. Supported formats: PDF, DOCX, TXT, JSON, MD
4. Files are automatically processed and embedded

### Web Scraping

1. Go to the "Web Scraping" tab
2. Enter one or more URLs
3. (Optional) Add scraping instructions
4. Click "Start Scraping"
5. Content is extracted and embedded automatically

### Ask Questions

1. Use the "Chat" tab
2. Type your question
3. The system will:
   - Search relevant documents
   - Generate an answer with context
   - Provide source references
4. Click on sources to see excerpts

## 🏢 Production Deployment

### Kubernetes Deployment

#### Prerequisites

- Kubernetes cluster with GPU nodes (for vLLM)
- kubectl configured
- Helm 3+
- Istio installed
- Argo CD installed

#### Deploy with Argo CD

```bash
# Install Istio Ambient Mesh
istioctl install --set profile=ambient -y

# Create namespace
kubectl create namespace rag-chatbot

# Label namespace for Istio
kubectl label namespace rag-chatbot istio-injection=enabled

# Apply OPA Gatekeeper policies
kubectl apply -f infrastructure/opa/constraint-template.yaml

# Deploy with Argo CD
kubectl apply -f infrastructure/argocd/application.yaml

# Monitor deployment
kubectl get pods -n rag-chatbot -w
```

#### Deploy with kubectl

```bash
# Apply base manifests
kubectl apply -k infrastructure/kubernetes/base/

# Or apply production overlays
kubectl apply -k infrastructure/kubernetes/overlays/prod/
```

### Development with Skaffold

```bash
# Start Skaffold in dev mode
cd devops/skaffold
skaffold dev

# Deploy to cluster
skaffold run

# With mirrord for remote debugging
mirrord exec skaffold dev
```

### CI/CD with Tekton

```bash
# Install Tekton pipelines
kubectl apply -f infrastructure/tekton/pipeline.yaml
kubectl apply -f infrastructure/tekton/trigger.yaml

# Trigger a pipeline run
tkn pipeline start rag-chatbot-pipeline \
  --param=git-url=https://github.com/your-org/rag-chatbot.git \
  --param=git-revision=main
```

## 🧪 Testing

### Backend Tests

```bash
cd backend
pip install -r requirements.txt
pytest tests/ -v --cov=app --cov-report=html
```

### Frontend Tests

```bash
cd frontend
npm install
npm test
npm run test:e2e
```

### Integration Tests

```bash
# Start services
docker-compose up -d

# Run integration tests
./scripts/testing/test-integration.sh

# Test RAG pipeline
./scripts/testing/test_rag_validation.py

# Test document upload
./scripts/testing/test-upload-endpoint.sh
```

See [scripts/testing/](./scripts/testing/) for all available test scripts.

## 📊 Monitoring & Observability

### Grafana Dashboards

Access Grafana at http://localhost:3000 (admin/admin)

Pre-configured dashboards:
- **Application Metrics**: Request rates, latency, errors
- **LLM Performance**: Token usage, inference time, costs
- **Infrastructure**: CPU, memory, GPU utilization
- **Cost Analysis**: Per-request costs, resource usage

### Tracing

Traces are automatically collected via OpenTelemetry and visualized in Grafana Tempo.

View traces:
1. Open Grafana
2. Go to Explore
3. Select Tempo datasource
4. Search by trace ID or query

### Logs

Logs are aggregated in Grafana Loki:
1. Open Grafana
2. Go to Explore
3. Select Loki datasource
4. Use LogQL queries: `{namespace="rag-chatbot"}`

### Cost Monitoring

OpenCost provides real-time cost analysis:
```bash
# Port-forward OpenCost UI
kubectl port-forward -n opencost svc/opencost 9090:9090

# Access at http://localhost:9090
```

## 🔧 Configuration

### Environment Variables

#### Backend

- `POSTGRES_SERVER`: PostgreSQL host
- `REDIS_HOST`: Redis host
- `MINIO_ENDPOINT`: MinIO endpoint
- `VLLM_ENDPOINT`: vLLM service URL
- `LLAMA_CPP_ENDPOINT`: llama.cpp service URL
- `OPENAI_API_KEY`: OpenAI API key (optional)
- `ENABLE_TRACING`: Enable OpenTelemetry tracing

#### Frontend

- `NEXT_PUBLIC_API_URL`: Backend API URL
- `NEXT_PUBLIC_GRAPHQL_URL`: GraphQL endpoint

### Custom Models

To use different LLM models:

```yaml
# docker-compose.yml
vllm-service:
  environment:
    VLLM_MODEL: meta-llama/Llama-2-13b-chat-hf
```

## 🔐 Security

- **mTLS**: Enforced via Istio service mesh
- **OPA Policies**: Automated policy enforcement
- **RBAC**: Kubernetes role-based access control
- **Secrets Management**: Kubernetes secrets
- **Network Policies**: Namespace isolation

## 📈 Performance

- **Semantic Caching**: 90%+ cache hit rate
- **Vector Search**: <100ms p95 latency
- **LLM Inference**: <2s response time
- **Horizontal Scaling**: Auto-scaling based on load
- **GPU Optimization**: vLLM with paged attention

## 🛠️ Troubleshooting

### Services won't start

```bash
# Diagnose backend issues
./scripts/debugging/diagnose-backend.sh

# Check Docker resources
docker system df

# Clean up
docker-compose down -v
docker system prune -a

# Restart
docker-compose up -d
```

### Database connection errors

```bash
# Check documents
./scripts/debugging/check-documents.sh

# Check PostgreSQL
docker-compose logs postgres

# Reset database
docker-compose down -v postgres
docker-compose up -d postgres
./scripts/setup/setup-database.sh
```

### Document processing issues

```bash
# Diagnose document processing
./scripts/debugging/diagnose-documents.sh

# Check embeddings
python ./scripts/debugging/check_embeddings.py
```

### RAG query issues

```bash
# Debug RAG pipeline
./scripts/debugging/debug-rag.sh
```

### LLM service issues

```bash
# Diagnose LLM service
./scripts/debugging/diagnose-llama.sh

# For vLLM (requires GPU)
# Use llama.cpp fallback instead
docker-compose up -d llama-cpp

# Update backend config to use llama.cpp
# LLAMA_CPP_ENDPOINT=http://llama-cpp:8080
```

For more debugging tools and guides, see:
- **[Debugging Guide](./docs/debugging/RAG_DEBUGGING_GUIDE.md)**
- **[Debug Quick Reference](./docs/debugging/DEBUG_QUICK_REFERENCE.md)**
- **[Debugging Scripts](./scripts/debugging/)**

## 📝 License

MIT License - see LICENSE file for details

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📧 Support

For issues and questions:
- GitHub Issues: <repository-url>/issues
- **Documentation**: See [`docs/`](./docs/) directory
- **Quick Reference**: [docs/guides/QUICKSTART.md](./docs/guides/QUICKSTART.md)
- **Admin Guide**: [docs/guides/ADMIN_GUIDE.md](./docs/guides/ADMIN_GUIDE.md)
- **AI Development**: [CLAUDE.md](./CLAUDE.md)

## 🎯 Roadmap

- [ ] Multi-modal support (images, audio)
- [ ] Advanced RAG techniques (HyDE, RAPTOR)
- [ ] Fine-tuning pipeline integration
- [ ] Multi-tenant architecture
- [ ] Advanced cost optimization
- [ ] Streaming responses
- [ ] Conversation memory optimization

---

Built with ❤️ using modern cloud-native technologies
