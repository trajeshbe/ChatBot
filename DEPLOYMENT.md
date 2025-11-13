# Deployment Guide - Enterprise RAG Chatbot

## Quick Start (5 Minutes)

### Prerequisites
- Docker Desktop installed and running
- 16GB+ RAM available
- 20GB+ disk space

### Steps

1. **Clone the repository** (already done)
   ```bash
   cd /home/user/ChatBot
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys (optional for local testing)
   ```

3. **Start the stack**
   ```bash
   # Option 1: Use the quick start script
   ./scripts/quick-start.sh

   # Option 2: Use Make
   make up

   # Option 3: Use Docker Compose directly
   docker-compose up -d
   ```

4. **Access the application**
   - Frontend: http://localhost:3001
   - Backend API: http://localhost:8000/api/docs
   - Grafana: http://localhost:3000 (admin/admin)

## What's Included

This repository contains a complete, production-ready RAG chatbot system with:

### ✅ Core Features
- [x] Conversational AI with chat interface
- [x] Document upload and processing (PDF, DOCX, TXT, JSON, MD)
- [x] Web scraping with URL input
- [x] Vector search with source references
- [x] Semantic caching for performance
- [x] Multi-LLM support (vLLM, llama.cpp, OpenAI)

### ✅ Backend Implementation
- [x] FastAPI REST API
- [x] GraphQL API with Strawberry
- [x] PostgreSQL + pgvector for vector storage
- [x] Redis for semantic caching
- [x] MinIO for object storage
- [x] Document processing with Docling
- [x] Embedding generation with Sentence Transformers
- [x] LLM service with fallback chain
- [x] RAG service with source tracking
- [x] Web scraping service
- [x] Prefect workflows
- [x] LangGraph agent orchestration

### ✅ Frontend Implementation
- [x] Next.js 14 with TypeScript
- [x] Modern chat interface
- [x] File upload with drag-and-drop
- [x] Web scraping UI
- [x] Source reference display
- [x] Real-time status updates
- [x] Responsive design with Tailwind CSS

### ✅ Infrastructure
- [x] Docker Compose for local development
- [x] Kubernetes manifests for production
- [x] Istio ambient mesh configuration
- [x] Envoy/Contour ingress
- [x] OPA Gatekeeper policies
- [x] Argo CD GitOps setup
- [x] Tekton CI/CD pipelines
- [x] Skaffold for dev workflow
- [x] DevContainer configuration

### ✅ Observability
- [x] OpenTelemetry tracing
- [x] Grafana Tempo for traces
- [x] Grafana Loki for logs
- [x] Grafana for visualization
- [x] OpenCost for cost tracking

### ✅ ML/AI Infrastructure
- [x] vLLM on Kube-Ray configuration
- [x] llama.cpp CPU fallback
- [x] Feast feature store setup
- [x] Apache Flink integration

### ✅ Documentation
- [x] Comprehensive README
- [x] Contributing guidelines
- [x] Deployment guide
- [x] Quick start script
- [x] Makefile with common commands

### ✅ Testing
- [x] Backend test structure
- [x] Frontend test setup
- [x] Integration test framework
- [x] pytest configuration

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                            │
│                     (Next.js + Tailwind)                    │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────┼──────────────────────────────────────┐
│                  Envoy Ingress                              │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────┼──────────────────────────────────────┐
│                Istio Service Mesh                           │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                FastAPI Backend                              │
│         (REST API + GraphQL + Agents)                       │
└─────┬────────┬────────┬────────┬─────────┬─────────────────┘
      │        │        │        │         │
┌─────▼──┐ ┌──▼───┐ ┌──▼────┐ ┌─▼─────┐ ┌─▼────────┐
│PostgreSQL│ │Redis │ │MinIO  │ │vLLM   │ │Prefect  │
│+pgvector│ │ VSS  │ │Object │ │/llama │ │Workflows│
└─────────┘ └──────┘ └───────┘ └───────┘ └─────────┘
      │        │        │        │         │
┌─────▼────────▼────────▼────────▼─────────▼─────────┐
│              OpenTelemetry                          │
│         (Tempo + Loki + Mimir)                      │
└─────────────────────────────────────────────────────┘
```

## Production Deployment

### Option 1: Kubernetes with Argo CD

```bash
# 1. Install prerequisites
kubectl create namespace rag-chatbot
kubectl create namespace argocd

# 2. Install Istio
istioctl install --set profile=ambient -y

# 3. Install Argo CD
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# 4. Deploy application
kubectl apply -f infrastructure/argocd/application.yaml

# 5. Monitor deployment
kubectl get pods -n rag-chatbot -w
```

### Option 2: Kubernetes with kubectl

```bash
# Deploy base manifests
kubectl apply -k infrastructure/kubernetes/base/

# Or deploy with production settings
kubectl apply -k infrastructure/kubernetes/overlays/prod/
```

### Option 3: Skaffold

```bash
# Development mode
cd devops/skaffold
skaffold dev

# Production deployment
skaffold run
```

## Configuration

### Environment Variables

Edit `.env` file:

```env
# OpenAI (optional - for fallback)
OPENAI_API_KEY=sk-...

# HuggingFace (optional - for custom models)
HUGGING_FACE_HUB_TOKEN=hf_...

# vLLM Model
VLLM_MODEL=TinyLlama/TinyLlama-1.1B-Chat-v1.0

# Enable features
DEBUG=true
ENABLE_TRACING=true
```

### GPU Support

For vLLM with GPU:
1. Install NVIDIA Docker runtime
2. Uncomment GPU sections in docker-compose.yml
3. Update VLLM_MODEL to a larger model

### Custom Models

Edit `docker-compose.yml`:
```yaml
vllm-service:
  command:
    - --model
    - meta-llama/Llama-2-13b-chat-hf  # Your model
```

## Monitoring & Debugging

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
```

### Check Health
```bash
# Backend health
curl http://localhost:8000/health

# Check all services
make health
```

### Access Dashboards
- Grafana: http://localhost:3000
- Prefect: http://localhost:4200
- MinIO: http://localhost:9001
- Redis Insight: http://localhost:8001

## Troubleshooting

### Services won't start
```bash
# Check Docker resources
docker system df

# Clean and restart
make clean
make up
```

### Out of memory
- Increase Docker Desktop memory limit to 16GB+
- Comment out vLLM in docker-compose.yml
- Use llama.cpp only

### Database connection errors
```bash
# Reset database
docker-compose down -v postgres
docker-compose up -d postgres
```

### Port conflicts
Edit docker-compose.yml to use different ports:
```yaml
ports:
  - "3002:3000"  # Change host port
```

## Performance Tuning

### For Local Development
- Use TinyLlama model (fast, small)
- Enable semantic caching
- Reduce chunk size if needed

### For Production
- Use larger, better models
- Scale backend replicas
- Enable GPU for vLLM
- Use production-grade PostgreSQL
- Enable connection pooling

## Security Checklist

- [ ] Change default passwords in .env
- [ ] Enable HTTPS with proper certificates
- [ ] Configure OPA policies
- [ ] Enable Istio mTLS
- [ ] Set up proper RBAC
- [ ] Use secrets manager (not .env files)
- [ ] Enable audit logging
- [ ] Configure firewall rules
- [ ] Scan images for vulnerabilities

## Scaling

### Horizontal Scaling
```bash
# Scale backend
docker-compose up -d --scale backend=3

# Or in Kubernetes
kubectl scale deployment backend --replicas=5 -n rag-chatbot
```

### Vertical Scaling
Edit resource limits in:
- `docker-compose.yml` for Docker
- `infrastructure/kubernetes/base/backend-deployment.yaml` for Kubernetes

## Cost Optimization

1. **Use semantic caching** - Already enabled
2. **Use local LLMs** - vLLM/llama.cpp instead of OpenAI
3. **Optimize chunk size** - Reduce to save on embeddings
4. **Monitor with OpenCost** - Track per-request costs
5. **Auto-scale down** - During low usage periods

## Backup & Recovery

### Backup Database
```bash
make backup-db
```

### Restore Database
```bash
make restore-db FILE=backup.sql
```

### Backup Documents
MinIO data is in Docker volume `minio_data` or can be synced to S3.

## Next Steps

1. **Test the system**
   - Upload some documents
   - Try web scraping
   - Ask questions and verify sources

2. **Customize**
   - Add your own models
   - Adjust chunk sizes
   - Customize UI theme

3. **Deploy to production**
   - Set up Kubernetes cluster
   - Configure monitoring
   - Enable security features

4. **Integrate**
   - Connect to your data sources
   - Add authentication
   - Integrate with your systems

## Support

- GitHub Issues: For bugs and features
- Documentation: Check README.md
- Community: Discussions tab

## License

MIT License - See LICENSE file
