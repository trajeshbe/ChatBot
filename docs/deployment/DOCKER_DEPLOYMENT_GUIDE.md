# Docker Plug-and-Play Deployment for Customer Environments

**Last Updated**: 2026-01-03
**Purpose**: Enable customers to deploy our RAG solution in their own environment with minimal setup

---

## Overview

This guide shows how to package our entire RAG platform as a **plug-and-play Docker deployment** that customers can run in their own environment with:
- ✅ Single command deployment (`docker-compose up`)
- ✅ All components pre-configured
- ✅ Customer-specific branding and configuration
- ✅ Data isolation and security
- ✅ Offline/air-gapped support

---

## Deployment Models

### 1. **Full Stack Docker Compose** (Recommended)
**Use Case**: Customer has Docker infrastructure, wants complete control
**Deployment**: Single `docker-compose.yml` with all services
**Pros**: Easy deployment, full control, portable
**Cons**: Requires Docker knowledge, resource management

### 2. **Docker Swarm / Kubernetes**
**Use Case**: Customer has orchestration infrastructure
**Deployment**: Helm chart or Swarm stack
**Pros**: Production-ready, auto-scaling, HA
**Cons**: More complex setup

### 3. **Single Container + External DBs**
**Use Case**: Customer has existing PostgreSQL, Redis
**Deployment**: App container + config to connect external services
**Pros**: Minimal footprint, leverage existing infra
**Cons**: Requires customer DB setup

---

## Architecture: What Gets Containerized

```
┌─────────────────────────────────────────────────────────────────┐
│                    Customer Environment                          │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │               docker-compose.yml (Plug & Play)             │ │
│  │                                                            │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │ │
│  │  │ Frontend │  │ Backend  │  │PostgreSQL│  │  Redis   │ │ │
│  │  │  Next.js │  │  FastAPI │  │ +pgvector│  │  Cache   │ │ │
│  │  │  (3001)  │  │  (8000)  │  │  (5432)  │  │  (6379)  │ │ │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │ │
│  │                                                            │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │ │
│  │  │  MinIO   │  │  Ollama  │  │Elasticsrch│ │ Grafana  │ │ │
│  │  │  S3 API  │  │Local LLM │  │ Optional │  │ Optional │ │ │
│  │  │  (9000)  │  │ (11434)  │  │  (9200)  │  │  (3000)  │ │ │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │ │
│  │                                                            │ │
│  │  All services pre-configured, ready to run                │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  Volume Mounts:                                                 │
│  - ./customer_data:/app/data      (Persistent data)            │
│  - ./customer_config:/app/config  (Customer config)            │
│  - ./customer_models:/models      (Embeddings/LLMs)            │
└─────────────────────────────────────────────────────────────────┘
```

---

## Files Structure

```
customer-deployment-package/
├── docker-compose.yml              # Main orchestration file
├── docker-compose.minimal.yml      # Lightweight version (no optional services)
├── docker-compose.airgap.yml       # Air-gapped deployment
├── .env.customer.template          # Customer configuration template
├── README-DEPLOYMENT.md            # Quick start guide
├── scripts/
│   ├── init-customer.sh           # One-time initialization
│   ├── start.sh                   # Start services
│   ├── stop.sh                    # Stop services
│   ├── backup.sh                  # Backup customer data
│   ├── restore.sh                 # Restore from backup
│   └── update.sh                  # Update to new version
├── config/
│   ├── backend.env                # Backend environment
│   ├── frontend.env               # Frontend environment
│   ├── postgres-init.sql          # Database initialization
│   └── nginx.conf                 # Optional reverse proxy
├── images/
│   ├── backend.tar                # Pre-built backend image
│   ├── frontend.tar               # Pre-built frontend image
│   └── models.tar                 # Pre-downloaded models
└── customer_data/                 # Persistent storage (created on init)
    ├── postgres/                  # Database data
    ├── minio/                     # Document storage
    ├── redis/                     # Cache data
    └── logs/                      # Application logs
```

---

## docker-compose.yml (Full Stack)

```yaml
version: '3.8'

services:
  # Frontend - Next.js UI
  frontend:
    image: ${REGISTRY:-ourplatform}/rag-frontend:${VERSION:-latest}
    container_name: rag_frontend
    ports:
      - "${FRONTEND_PORT:-3001}:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000
      - NEXT_PUBLIC_TENANT_ID=${TENANT_ID:-customer-default}
      - NEXT_PUBLIC_BRANDING_LOGO=${CUSTOMER_LOGO_URL:-}
      - NEXT_PUBLIC_APP_TITLE=${APP_TITLE:-RAG Assistant}
    volumes:
      - ./customer_config/frontend.env:/app/.env.local
      - ./customer_config/branding:/app/public/branding
    depends_on:
      - backend
    restart: unless-stopped
    networks:
      - rag-network

  # Backend - FastAPI
  backend:
    image: ${REGISTRY:-ourplatform}/rag-backend:${VERSION:-latest}
    container_name: rag_backend
    ports:
      - "${BACKEND_PORT:-8000}:8000"
    environment:
      # Database
      - DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}

      # Redis
      - REDIS_URL=redis://redis:6379/0

      # MinIO (S3)
      - MINIO_ENDPOINT=minio:9000
      - MINIO_ACCESS_KEY=${MINIO_ACCESS_KEY}
      - MINIO_SECRET_KEY=${MINIO_SECRET_KEY}
      - MINIO_BUCKET_NAME=${MINIO_BUCKET:-rag-documents}

      # LLM Configuration
      - OPENAI_API_KEY=${OPENAI_API_KEY:-}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-}
      - OLLAMA_BASE_URL=http://ollama:11434
      - DEFAULT_LLM_PROVIDER=${LLM_PROVIDER:-ollama}
      - DEFAULT_MODEL=${DEFAULT_MODEL:-mistral}

      # Elasticsearch (optional)
      - ELASTICSEARCH_URL=${ELASTICSEARCH_URL:-http://elasticsearch:9200}
      - ELASTICSEARCH_ENABLED=${ELASTICSEARCH_ENABLED:-false}

      # Tenant Configuration
      - TENANT_ID=${TENANT_ID:-customer-default}
      - TENANT_NAME=${TENANT_NAME:-Customer}
      - MULTI_TENANT_MODE=${MULTI_TENANT_MODE:-false}

      # Security
      - SECRET_KEY=${SECRET_KEY}
      - JWT_SECRET=${JWT_SECRET}
      - ALLOWED_ORIGINS=${ALLOWED_ORIGINS:-http://localhost:3001}

      # Feature Flags
      - ENABLE_TELEMETRY=${ENABLE_TELEMETRY:-false}
      - ENABLE_AUDIT_LOGS=${ENABLE_AUDIT_LOGS:-true}
      - ENABLE_USAGE_TRACKING=${ENABLE_USAGE_TRACKING:-false}

    volumes:
      - ./customer_config/backend.env:/app/.env
      - ./customer_data/logs:/app/logs
      - ./customer_models:/app/models

    depends_on:
      - postgres
      - redis
      - minio

    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

    restart: unless-stopped
    networks:
      - rag-network

  # PostgreSQL + pgvector
  postgres:
    image: pgvector/pgvector:pg16
    container_name: rag_postgres
    ports:
      - "${POSTGRES_PORT:-5432}:5432"
    environment:
      - POSTGRES_DB=${POSTGRES_DB:-ragchatbot}
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - PGDATA=/var/lib/postgresql/data/pgdata
    volumes:
      - ./customer_data/postgres:/var/lib/postgresql/data
      - ./config/postgres-init.sql:/docker-entrypoint-initdb.d/init.sql
    restart: unless-stopped
    networks:
      - rag-network

  # Redis - Caching
  redis:
    image: redis:7-alpine
    container_name: rag_redis
    ports:
      - "${REDIS_PORT:-6379}:6379"
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD:-}
    volumes:
      - ./customer_data/redis:/data
    restart: unless-stopped
    networks:
      - rag-network

  # MinIO - S3-compatible storage
  minio:
    image: minio/minio:latest
    container_name: rag_minio
    ports:
      - "${MINIO_PORT:-9000}:9000"
      - "${MINIO_CONSOLE_PORT:-9001}:9001"
    environment:
      - MINIO_ROOT_USER=${MINIO_ACCESS_KEY}
      - MINIO_ROOT_PASSWORD=${MINIO_SECRET_KEY}
    command: server /data --console-address ":9001"
    volumes:
      - ./customer_data/minio:/data
    restart: unless-stopped
    networks:
      - rag-network

  # Ollama - Local LLM (optional)
  ollama:
    image: ollama/ollama:latest
    container_name: rag_ollama
    ports:
      - "${OLLAMA_PORT:-11434}:11434"
    volumes:
      - ./customer_data/ollama:/root/.ollama
      - ./customer_models:/models
    environment:
      - OLLAMA_MODELS=/models
    restart: unless-stopped
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: ${GPU_COUNT:-1}
              capabilities: [gpu]
    networks:
      - rag-network

  # Elasticsearch (optional - for keyword search)
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    container_name: rag_elasticsearch
    profiles: ["full"]  # Only start with --profile full
    ports:
      - "${ELASTICSEARCH_PORT:-9200}:9200"
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    volumes:
      - ./customer_data/elasticsearch:/usr/share/elasticsearch/data
    restart: unless-stopped
    networks:
      - rag-network

  # Grafana - Monitoring (optional)
  grafana:
    image: grafana/grafana:latest
    container_name: rag_grafana
    profiles: ["full"]  # Only start with --profile full
    ports:
      - "${GRAFANA_PORT:-3000}:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD:-admin}
      - GF_INSTALL_PLUGINS=redis-datasource
    volumes:
      - ./customer_data/grafana:/var/lib/grafana
      - ./config/grafana-datasources.yml:/etc/grafana/provisioning/datasources/datasources.yml
    restart: unless-stopped
    networks:
      - rag-network

networks:
  rag-network:
    driver: bridge

volumes:
  postgres_data:
  redis_data:
  minio_data:
  ollama_models:
```

---

## .env.customer.template

```bash
# ===================================
# CUSTOMER DEPLOYMENT CONFIGURATION
# ===================================
# Copy this file to .env and fill in your values

# Tenant Identification
TENANT_ID=customer-acme
TENANT_NAME=ACME Corporation
APP_TITLE=ACME RAG Assistant

# Version Control
VERSION=v1.0.0
REGISTRY=ourplatform

# Port Configuration
FRONTEND_PORT=3001
BACKEND_PORT=8000
POSTGRES_PORT=5432
REDIS_PORT=6379
MINIO_PORT=9000
MINIO_CONSOLE_PORT=9001
OLLAMA_PORT=11434
ELASTICSEARCH_PORT=9200
GRAFANA_PORT=3000

# Security (GENERATE STRONG PASSWORDS!)
SECRET_KEY=CHANGE_ME_LONG_RANDOM_STRING_32_CHARS_MIN
JWT_SECRET=CHANGE_ME_ANOTHER_RANDOM_STRING_32_CHARS_MIN
POSTGRES_PASSWORD=CHANGE_ME_STRONG_PASSWORD
REDIS_PASSWORD=CHANGE_ME_STRONG_PASSWORD
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=CHANGE_ME_STRONG_PASSWORD
GRAFANA_PASSWORD=admin

# Database
POSTGRES_DB=ragchatbot

# MinIO / S3
MINIO_BUCKET=rag-documents

# LLM Configuration
# Option 1: Use Ollama (local, offline)
LLM_PROVIDER=ollama
DEFAULT_MODEL=mistral

# Option 2: Use OpenAI (requires internet + API key)
# LLM_PROVIDER=openai
# DEFAULT_MODEL=gpt-4o-mini
# OPENAI_API_KEY=sk-...

# Option 3: Use Anthropic Claude (requires internet + API key)
# LLM_PROVIDER=anthropic
# DEFAULT_MODEL=claude-3-5-sonnet-20241022
# ANTHROPIC_API_KEY=sk-ant-...

# Elasticsearch (optional - for hybrid search)
ELASTICSEARCH_ENABLED=false
# ELASTICSEARCH_URL=http://elasticsearch:9200

# Multi-Tenant Mode
MULTI_TENANT_MODE=false

# Feature Flags
ENABLE_TELEMETRY=false
ENABLE_AUDIT_LOGS=true
ENABLE_USAGE_TRACKING=false

# GPU Configuration (for Ollama)
GPU_COUNT=1

# CORS / Security
ALLOWED_ORIGINS=http://localhost:3001,https://customer-domain.com

# Branding (optional)
CUSTOMER_LOGO_URL=/branding/logo.png
```

---

## Quick Start Scripts

### scripts/init-customer.sh

```bash
#!/bin/bash
set -e

echo "🚀 Initializing Customer RAG Deployment"
echo "======================================="

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env from template..."
    cp .env.customer.template .env
    echo "⚠️  IMPORTANT: Edit .env and set secure passwords!"
    echo "   Run: nano .env"
    read -p "Press ENTER after editing .env..."
fi

# Create data directories
echo "📂 Creating persistent data directories..."
mkdir -p customer_data/{postgres,redis,minio,ollama,elasticsearch,grafana,logs}
mkdir -p customer_config/branding
mkdir -p customer_models

# Set permissions
chmod -R 777 customer_data  # Adjust for production security

# Pull/load Docker images
echo "📥 Loading Docker images..."
if [ -f images/backend.tar ]; then
    echo "   Loading pre-built backend image..."
    docker load -i images/backend.tar
fi

if [ -f images/frontend.tar ]; then
    echo "   Loading pre-built frontend image..."
    docker load -i images/frontend.tar
fi

if [ ! -f images/backend.tar ]; then
    echo "   Pulling backend image from registry..."
    docker-compose pull backend frontend
fi

# Initialize database
echo "🗄️  Initializing PostgreSQL..."
docker-compose up -d postgres
sleep 10
docker-compose exec -T postgres psql -U postgres -d ragchatbot < config/postgres-init.sql || true

# Initialize MinIO bucket
echo "📦 Initializing MinIO bucket..."
docker-compose up -d minio
sleep 5

# Pull Ollama model (if using local LLM)
source .env
if [ "$LLM_PROVIDER" = "ollama" ]; then
    echo "🤖 Downloading Ollama model: $DEFAULT_MODEL..."
    docker-compose up -d ollama
    sleep 10
    docker-compose exec ollama ollama pull $DEFAULT_MODEL
fi

echo "✅ Initialization complete!"
echo ""
echo "Next steps:"
echo "  1. Review .env configuration"
echo "  2. Start services: ./scripts/start.sh"
echo "  3. Access UI: http://localhost:${FRONTEND_PORT:-3001}"
```

### scripts/start.sh

```bash
#!/bin/bash
set -e

echo "🚀 Starting RAG Services..."

# Check if initialized
if [ ! -f .env ]; then
    echo "❌ Not initialized. Run ./scripts/init-customer.sh first"
    exit 1
fi

# Start core services
echo "📦 Starting core services (Postgres, Redis, MinIO, Backend, Frontend)..."
docker-compose up -d postgres redis minio backend frontend

# Optional: Start Ollama if configured
source .env
if [ "$LLM_PROVIDER" = "ollama" ]; then
    echo "🤖 Starting Ollama (local LLM)..."
    docker-compose up -d ollama
fi

# Optional: Start Elasticsearch if enabled
if [ "$ELASTICSEARCH_ENABLED" = "true" ]; then
    echo "🔍 Starting Elasticsearch..."
    docker-compose --profile full up -d elasticsearch
fi

# Wait for health checks
echo "⏳ Waiting for services to be healthy..."
sleep 15

# Check health
docker-compose ps

echo ""
echo "✅ RAG Services Started!"
echo ""
echo "Access Points:"
echo "  Frontend:  http://localhost:${FRONTEND_PORT:-3001}"
echo "  Backend:   http://localhost:${BACKEND_PORT:-8000}"
echo "  API Docs:  http://localhost:${BACKEND_PORT:-8000}/api/docs"
echo "  MinIO:     http://localhost:${MINIO_CONSOLE_PORT:-9001}"
echo ""
echo "Logs: docker-compose logs -f"
echo "Stop:  ./scripts/stop.sh"
```

### scripts/stop.sh

```bash
#!/bin/bash
echo "🛑 Stopping RAG Services..."
docker-compose down
echo "✅ Services stopped (data preserved)"
echo "To remove all data: docker-compose down -v"
```

### scripts/backup.sh

```bash
#!/bin/bash
set -e

BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "💾 Creating backup: $BACKUP_DIR"

# Backup PostgreSQL
echo "  📊 Backing up PostgreSQL..."
docker-compose exec -T postgres pg_dump -U postgres ragchatbot > "$BACKUP_DIR/postgres_backup.sql"

# Backup MinIO (documents)
echo "  📄 Backing up MinIO..."
cp -r customer_data/minio "$BACKUP_DIR/minio_backup"

# Backup Redis (optional - cache usually not critical)
# docker-compose exec -T redis redis-cli --rdb - > "$BACKUP_DIR/redis_backup.rdb"

# Backup .env
cp .env "$BACKUP_DIR/env_backup"

echo "✅ Backup complete: $BACKUP_DIR"
echo "   Size: $(du -sh $BACKUP_DIR | cut -f1)"
```

---

## Air-Gapped Deployment (No Internet)

### docker-compose.airgap.yml

```yaml
# Minimal air-gapped deployment
# - Uses Ollama (no external API calls)
# - Pre-loaded models
# - No telemetry

version: '3.8'

services:
  frontend:
    image: file://./images/frontend.tar  # Pre-loaded image
    # ... rest same as main compose ...

  backend:
    image: file://./images/backend.tar  # Pre-loaded image
    environment:
      - OPENAI_API_KEY=  # Disabled
      - ANTHROPIC_API_KEY=  # Disabled
      - DEFAULT_LLM_PROVIDER=ollama
      - ENABLE_TELEMETRY=false
    # ... rest same as main compose ...

  ollama:
    image: file://./images/ollama.tar  # Pre-loaded image
    volumes:
      - ./customer_models:/root/.ollama  # Pre-downloaded models
    # ... rest same as main compose ...

  # Only include postgres, redis, minio (no elasticsearch, grafana)
```

### Pre-packaging for Air-Gapped

```bash
# On internet-connected build machine:
./scripts/package-airgap.sh

# This script creates airgap-package.tar.gz with:
# - All Docker images saved as .tar
# - All models pre-downloaded
# - Complete docker-compose config
# - Init scripts

# Customer then extracts and runs:
tar -xzf airgap-package.tar.gz
cd airgap-deployment
./scripts/init-airgap.sh
./scripts/start.sh
```

---

## Customer Onboarding Checklist

### Pre-Deployment
- [ ] Customer provides infrastructure requirements
  - [ ] Docker version (20.10+)
  - [ ] Available ports (3001, 8000, etc.)
  - [ ] Storage capacity (min 50GB for data)
  - [ ] RAM (min 16GB, 32GB recommended)
  - [ ] GPU availability (optional, for Ollama)
- [ ] Customer provides:
  - [ ] API keys (OpenAI/Anthropic) OR confirms local-only
  - [ ] Domain name / SSL certificates
  - [ ] Network/firewall rules
  - [ ] Backup requirements

### Deployment Steps
1. [ ] Transfer deployment package
2. [ ] Customer runs `./scripts/init-customer.sh`
3. [ ] Customer edits `.env` with secure passwords
4. [ ] Customer runs `./scripts/start.sh`
5. [ ] Verify services: `docker-compose ps`
6. [ ] Access frontend: `http://localhost:3001`
7. [ ] Create admin user
8. [ ] Upload initial documents
9. [ ] Test RAG query
10. [ ] Setup backups (cron `./scripts/backup.sh`)

### Post-Deployment
- [ ] Document access URLs
- [ ] Share admin credentials (securely)
- [ ] Schedule backup verification
- [ ] Setup monitoring (optional Grafana)
- [ ] Plan update cadence

---

## Customization for Customers

### White-Label Branding

```bash
# 1. Customer provides logo
customer_config/branding/logo.png

# 2. Set in .env
APP_TITLE="ACME RAG Assistant"
CUSTOMER_LOGO_URL=/branding/logo.png

# 3. Restart frontend
docker-compose restart frontend
```

### Custom Models

```bash
# 1. Pre-download embedding model
docker-compose exec backend python -c "
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('customer/custom-model')
model.save('/app/models/custom-embedding')
"

# 2. Update backend config
# backend/app/tier_1/infrastructure/config.py
EMBEDDING_MODEL = "/app/models/custom-embedding"

# 3. Rebuild image or mount volume
```

### Pre-Loaded Documents

```bash
# Before deployment, copy customer docs
mkdir -p customer_data/preload_documents/
cp /path/to/customer/docs/* customer_data/preload_documents/

# Update init script to auto-upload
# scripts/init-customer.sh
docker-compose exec backend python -c "
from app.services.document_service import DocumentService
# Upload all files in /app/preload_documents
"
```

---

## Resource Requirements

### Minimum (Light Workload)
- **CPU**: 4 cores
- **RAM**: 16 GB
- **Storage**: 50 GB SSD
- **Network**: 10 Mbps
- **GPU**: None (uses cloud LLMs)

### Recommended (Production)
- **CPU**: 8 cores
- **RAM**: 32 GB
- **Storage**: 200 GB SSD
- **Network**: 100 Mbps
- **GPU**: 1x NVIDIA (12GB VRAM) for Ollama

### High Performance
- **CPU**: 16+ cores
- **RAM**: 64+ GB
- **Storage**: 500 GB NVMe SSD
- **Network**: 1 Gbps
- **GPU**: 2x NVIDIA (24GB VRAM each)

---

## Licensing Model for Docker Deployments

### Option 1: License Key (Recommended)
```bash
# Customer receives license key
LICENSE_KEY=ACME-CORP-2024-XXXXX-XXXXX-XXXXX

# Add to .env
LICENSE_KEY=ACME-CORP-2024-XXXXX-XXXXX-XXXXX

# Backend validates on startup
# If invalid/expired: runs in limited mode or doesn't start
```

### Option 2: Time-Limited Trial
```bash
# Trial version expires after 30 days
DEPLOYMENT_DATE=2024-01-03
TRIAL_DAYS=30

# Backend checks on startup
# After trial: requires license key
```

### Option 3: Feature-Based Licensing
```bash
# License controls features
LICENSE_FEATURES=basic,document-upload,rag-query
# Enterprise license adds:
# LICENSE_FEATURES=basic,document-upload,rag-query,multi-user,api-access,analytics
```

---

## Update Process

### Rolling Updates

```bash
# Customer receives new images
./scripts/update.sh v1.1.0

# Script does:
# 1. Backup current state
# 2. Pull new images
# 3. Run migrations
# 4. Restart services
# 5. Verify health
# 6. Rollback if issues
```

### scripts/update.sh

```bash
#!/bin/bash
set -e

NEW_VERSION=$1
if [ -z "$NEW_VERSION" ]; then
    echo "Usage: ./update.sh v1.1.0"
    exit 1
fi

echo "🔄 Updating to version: $NEW_VERSION"

# 1. Backup
echo "💾 Creating pre-update backup..."
./scripts/backup.sh

# 2. Pull new images
echo "📥 Pulling new images..."
export VERSION=$NEW_VERSION
docker-compose pull backend frontend

# 3. Run migrations
echo "🗄️  Running database migrations..."
docker-compose up -d postgres
sleep 5
docker-compose run --rm backend alembic upgrade head

# 4. Restart services
echo "🔄 Restarting services..."
docker-compose up -d

# 5. Health check
echo "⏳ Waiting for services..."
sleep 15
HEALTH=$(curl -s http://localhost:8000/health | jq -r '.status')

if [ "$HEALTH" = "healthy" ]; then
    echo "✅ Update successful to $NEW_VERSION"
else
    echo "❌ Health check failed! Rolling back..."
    # Rollback logic here
    exit 1
fi
```

---

## Support & Troubleshooting

### Common Issues

**Issue**: Services won't start
```bash
# Check logs
docker-compose logs backend

# Common causes:
# - .env not configured
# - Ports already in use
# - Insufficient permissions on data directories
```

**Issue**: Frontend can't connect to backend
```bash
# Check backend health
curl http://localhost:8000/health

# Check network
docker-compose exec frontend ping backend

# Fix: Update NEXT_PUBLIC_API_URL in .env
```

**Issue**: Out of disk space
```bash
# Check usage
docker system df

# Clean up old images/logs
docker system prune -a
rm -rf customer_data/logs/*
```

### Customer Support Package

When deploying to customers, provide:

1. **Deployment Package** (ZIP/TAR)
   - All files from above
   - README with quick start
   - Support contact info

2. **Documentation** (PDF)
   - Architecture overview
   - Configuration reference
   - Troubleshooting guide
   - API documentation

3. **Training Materials**
   - Video walkthrough
   - Admin guide
   - End-user guide

4. **Support SLA**
   - Support email/portal
   - Response time commitments
   - Update schedule

---

## Cost Analysis for Customers

### Infrastructure Costs (Self-Hosted)

**AWS Example** (t3.xlarge + 200GB EBS):
- EC2: ~$120/month
- Storage: ~$20/month
- **Total**: ~$140/month

**Azure Example** (D4s_v3 + 200GB disk):
- VM: ~$140/month
- Storage: ~$15/month
- **Total**: ~$155/month

**On-Premises**:
- Server: $5,000 (one-time)
- Maintenance: $100/month
- **Amortized**: ~$200/month (2-year lifespan)

### Licensing Costs (Our Platform - Tier 4 Deployment Packages)

**Tier 4 - Starter**: $500/month
- Up to 10 users
- 100GB storage
- Email support
- Core RAG features only

**Tier 4 - Professional**: $1,500/month
- Unlimited users
- 500GB storage
- Priority support
- Custom branding
- Access to Tier 2 domain verticals

**Tier 4 - Enterprise**: $5,000/month
- Enterprise features
- Unlimited storage
- Dedicated support
- SLA guarantees
- Full Tier 2 + Tier 3 access
- Custom module development

---

## Next Steps

1. **Create Deployment Package**
   - Package all scripts and configs
   - Build and save Docker images
   - Create customer documentation

2. **Test Deployment**
   - Deploy to clean VM
   - Verify all services start
   - Test full workflow

3. **Customer Pilot**
   - Deploy to 1-2 pilot customers
   - Gather feedback
   - Refine process

4. **Production Rollout**
   - Standardize deployment
   - Create support runbooks
   - Train support team

---

**Last Updated**: 2026-01-03
**Maintained By**: Platform Engineering Team
**Customer Contact**: support@ourplatform.com
