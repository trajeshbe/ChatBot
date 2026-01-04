# Deployment Documentation

This directory contains deployment guides, strategies, and specialized component deployment documentation.

## Contents

### Deployment Guides
- **DOCKER_DEPLOYMENT_GUIDE.md** - Docker-based deployment guide
- **SPECIALIZED_COMPONENTS_DEPLOYMENT.md** - Specialized component deployment

## Deployment Options

### 1. Docker Compose (Local/Development)
```bash
docker-compose up -d
```

**Features**:
- Full stack deployment
- PostgreSQL + pgvector
- Redis caching
- MinIO object storage
- Automatic service linking

### 2. Kubernetes (Production)
**Location**: `/infrastructure/`

**Features**:
- Scalable deployment
- Service mesh (Istio Ambient)
- Monitoring (Grafana, Tempo)
- Policy enforcement (OPA Gatekeeper)

### 3. Standalone Module Export
**Via Export Wizard**

**Features**:
- Self-contained deployment
- Automated initialization
- Health checks
- Production-ready configuration

## Deployment Architecture

### Services
1. **Backend** - FastAPI application (port 8000)
2. **Frontend** - Next.js application (port 3001)
3. **PostgreSQL** - Database with pgvector (port 5432)
4. **Redis** - Caching and sessions (port 6379)
5. **MinIO** - Object storage (port 9000, console 9001)

### Infrastructure Components
- **Nginx/Envoy** - API Gateway
- **Grafana** - Monitoring dashboards
- **Tempo** - Distributed tracing
- **Loki** - Log aggregation
- **Prometheus** - Metrics collection

## Environment Configuration

### Required Variables
```bash
# Database
POSTGRES_PASSWORD=<secure-password>
DATABASE_URL=postgresql://...

# LLM API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Security
JWT_SECRET=<32-character-secret>
SECRET_KEY=<32-character-secret>
```

See `.env.example` for complete configuration.

## Health Checks

### Backend Health
```bash
curl http://localhost:8000/health
```

### Frontend Health
```bash
curl http://localhost:3001
```

### Database Health
```bash
docker-compose exec postgres pg_isready
```

## Troubleshooting

### Common Issues
1. **Port Conflicts** - Check ports 8000, 3001, 5432, 6379, 9000
2. **Database Connection** - Verify PostgreSQL is running
3. **Missing API Keys** - Check .env configuration
4. **Docker Issues** - Try `docker-compose down -v && docker-compose up -d`

See `/docs/troubleshooting/` for detailed debugging guides.

## Related Documentation
- [Setup Guides](../setup/)
- [Export Wizard](../export_wizard/)
- [Configuration](../configuration/)
- [Troubleshooting](../troubleshooting/)

---
**Last Updated**: 2026-01-04
