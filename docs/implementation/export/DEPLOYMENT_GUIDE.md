# Export Package - Deployment Guide

**Last Updated**: 2026-01-04
**Audience**: DevOps, System Administrators, Customers

---

## Overview

This guide explains how to deploy exported RAG module packages across different infrastructure platforms.

---

## Quick Start

```bash
# 1. Extract package
tar -xzf your-package.tar.gz
cd your-package/

# 2. Review README
cat README.md

# 3. Configure environment
cp config/.env.example config/.env
nano config/.env  # Edit with your settings

# 4. Deploy (choose your platform)
cd infrastructure/docker
docker-compose up -d

# 5. Verify
curl http://localhost:8000/health
```

---

## Platform-Specific Guides

### 🐳 Docker Compose

**Best for**: Development, testing, small deployments

#### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+
- 4GB RAM minimum
- 10GB disk space

#### Deployment Steps

```bash
# 1. Navigate to Docker infrastructure
cd infrastructure/docker/

# 2. Review configuration
cat docker-compose.yml

# 3. Configure environment
cp ../../config/.env.example ../../config/.env
nano ../../config/.env

# Required variables:
#   POSTGRES_PASSWORD=<strong-password>
#   REDIS_PASSWORD=<strong-password>
#   MINIO_ROOT_PASSWORD=<strong-password>
#   SECRET_KEY=<random-secret>

# 4. Start services
docker-compose up -d

# 5. Check status
docker-compose ps

# 6. View logs
docker-compose logs -f backend

# 7. Initialize database (first time only)
docker-compose exec backend alembic upgrade head

# 8. Create admin user (optional)
docker-compose exec backend python scripts/create_admin.py
```

#### Accessing Services

| Service | URL | Default Credentials |
|---------|-----|---------------------|
| Backend API | http://localhost:8000 | N/A |
| Frontend UI | http://localhost:3000 | N/A |
| API Docs | http://localhost:8000/api/docs | N/A |
| MinIO Console | http://localhost:9001 | From .env |
| PostgreSQL | localhost:5432 | From .env |

#### Stopping Services

```bash
# Stop (preserve data)
docker-compose stop

# Stop and remove containers
docker-compose down

# Stop, remove containers, and delete data
docker-compose down -v
```

---

### ☸️ Kubernetes

**Best for**: Production, scalable deployments, cloud-native

#### Prerequisites
- Kubernetes 1.24+
- kubectl configured
- Helm 3.0+ (optional but recommended)
- Ingress controller
- Storage class for PersistentVolumes

#### Deployment Steps

```bash
# 1. Navigate to Kubernetes infrastructure
cd infrastructure/kubernetes/

# 2. Review manifests
ls -la *.yaml

# 3. Create namespace
kubectl create namespace rag-module

# 4. Create secrets
kubectl create secret generic rag-secrets \
  --from-literal=postgres-password=<password> \
  --from-literal=redis-password=<password> \
  --from-literal=minio-password=<password> \
  --from-literal=secret-key=<random-key> \
  -n rag-module

# 5. Create ConfigMap
kubectl create configmap rag-config \
  --from-file=../../config/module_config.json \
  -n rag-module

# 6. Apply manifests
kubectl apply -f namespace.yaml
kubectl apply -f configmap.yaml
kubectl apply -f secrets.yaml
kubectl apply -f postgres-deployment.yaml
kubectl apply -f redis-deployment.yaml
kubectl apply -f backend-deployment.yaml
kubectl apply -f frontend-deployment.yaml
kubectl apply -f services.yaml
kubectl apply -f ingress.yaml

# 7. Wait for pods to be ready
kubectl get pods -n rag-module -w

# 8. Check deployment status
kubectl get all -n rag-module

# 9. Run database migrations
kubectl exec -it deployment/backend -n rag-module -- alembic upgrade head
```

#### Scaling

```bash
# Scale backend
kubectl scale deployment backend --replicas=3 -n rag-module

# Autoscaling
kubectl autoscale deployment backend \
  --cpu-percent=70 \
  --min=2 \
  --max=10 \
  -n rag-module
```

#### Accessing Services

```bash
# Get ingress address
kubectl get ingress -n rag-module

# Port forward for local access
kubectl port-forward svc/backend 8000:8000 -n rag-module
kubectl port-forward svc/frontend 3000:3000 -n rag-module
```

#### Updating

```bash
# Update deployment with new image
kubectl set image deployment/backend backend=new-image:tag -n rag-module

# Or apply updated manifests
kubectl apply -f backend-deployment.yaml -n rag-module
```

#### Monitoring

```bash
# View logs
kubectl logs -f deployment/backend -n rag-module

# Describe resources
kubectl describe pod <pod-name> -n rag-module

# Get events
kubectl get events -n rag-module --sort-by='.lastTimestamp'
```

---

### ☁️ AWS CloudFormation

**Best for**: AWS-specific deployments, infrastructure as code

#### Prerequisites
- AWS CLI configured
- IAM permissions for CloudFormation, ECS, RDS, etc.
- VPC and subnets configured
- SSL certificate in ACM (for HTTPS)

#### Deployment Steps

```bash
# 1. Navigate to AWS infrastructure
cd infrastructure/aws/cloudformation/

# 2. Review templates
ls -la *.yaml

# 3. Set parameters
cat > parameters.json << EOF
[
  {"ParameterKey": "Environment", "ParameterValue": "production"},
  {"ParameterKey": "VpcId", "ParameterValue": "vpc-xxxxx"},
  {"ParameterKey": "SubnetIds", "ParameterValue": "subnet-aaa,subnet-bbb"},
  {"ParameterKey": "DBPassword", "ParameterValue": "strong-password"},
  {"ParameterKey": "CertificateArn", "ParameterValue": "arn:aws:acm:..."}
]
EOF

# 4. Validate template
aws cloudformation validate-template \
  --template-body file://main.yaml

# 5. Create stack
aws cloudformation create-stack \
  --stack-name rag-module-prod \
  --template-body file://main.yaml \
  --parameters file://parameters.json \
  --capabilities CAPABILITY_IAM

# 6. Monitor stack creation
aws cloudformation describe-stacks \
  --stack-name rag-module-prod \
  --query 'Stacks[0].StackStatus'

# Watch events
aws cloudformation describe-stack-events \
  --stack-name rag-module-prod \
  --max-items 10

# 7. Get outputs
aws cloudformation describe-stacks \
  --stack-name rag-module-prod \
  --query 'Stacks[0].Outputs'
```

#### Stack Components

- **VPC**: Network isolation
- **ALB**: Application Load Balancer with HTTPS
- **ECS Fargate**: Containerized backend/frontend
- **RDS PostgreSQL**: Managed database with Multi-AZ
- **ElastiCache Redis**: Managed Redis cluster
- **S3**: Object storage (replaces MinIO)
- **CloudWatch**: Logging and monitoring
- **Parameter Store**: Secrets management

#### Updating Stack

```bash
# Update stack
aws cloudformation update-stack \
  --stack-name rag-module-prod \
  --template-body file://main.yaml \
  --parameters file://parameters.json \
  --capabilities CAPABILITY_IAM

# Monitor update
aws cloudformation wait stack-update-complete \
  --stack-name rag-module-prod
```

#### Deleting Stack

```bash
# Delete stack (WARNING: Deletes all resources!)
aws cloudformation delete-stack \
  --stack-name rag-module-prod

# Monitor deletion
aws cloudformation wait stack-delete-complete \
  --stack-name rag-module-prod
```

---

### 🖥️ Bare Metal / VM

**Best for**: On-premise deployments, air-gapped environments

#### Prerequisites
- Ubuntu 20.04+ or RHEL 8+
- 8GB RAM minimum
- 50GB disk space
- Python 3.10+
- Node.js 18+
- PostgreSQL 14+
- Redis 7+

#### Deployment Steps

```bash
# 1. Install system dependencies
sudo apt update
sudo apt install -y python3.10 python3-pip nodejs npm postgresql-14 redis-server

# 2. Setup PostgreSQL
sudo -u postgres createdb ragchatbot
sudo -u postgres createuser raguser
sudo -u postgres psql -c "ALTER USER raguser WITH PASSWORD 'password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ragchatbot TO raguser;"

# 3. Configure Redis
sudo systemctl enable redis-server
sudo systemctl start redis-server

# 4. Extract package
tar -xzf package.tar.gz
cd package/

# 5. Install backend dependencies
cd src/backend/
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 6. Configure backend
cp ../../config/.env.example ../../config/.env
nano ../../config/.env

# Set:
#   POSTGRES_SERVER=localhost
#   POSTGRES_USER=raguser
#   POSTGRES_PASSWORD=password
#   POSTGRES_DB=ragchatbot
#   REDIS_HOST=localhost

# 7. Run database migrations
alembic upgrade head

# 8. Install frontend dependencies
cd ../frontend/
npm install
npm run build

# 9. Setup systemd services
sudo cp ../../infrastructure/systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload

# 10. Start services
sudo systemctl enable rag-backend rag-frontend
sudo systemctl start rag-backend rag-frontend

# 11. Check status
sudo systemctl status rag-backend
sudo systemctl status rag-frontend
```

#### Nginx Configuration

```nginx
# /etc/nginx/sites-available/rag-module
server {
    listen 80;
    server_name example.com;

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/rag-module /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## Post-Deployment

### 1. Health Check

```bash
# Backend
curl http://localhost:8000/health

# Expected: {"status": "healthy"}

# API documentation
open http://localhost:8000/api/docs

# Frontend
curl http://localhost:3000

# Expected: HTML content
```

### 2. Functional Testing

Run the included test script:

```bash
cd scripts/
./test.sh

# Or manually test key endpoints
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "test query"}'
```

### 3. Performance Testing

```bash
# Load test with Apache Bench
ab -n 1000 -c 10 http://localhost:8000/health

# Or use provided stress test
cd scripts/
./stress-test.sh
```

### 4. Monitoring Setup

If monitoring was included in export:

```bash
# Access Grafana
open http://localhost:3000/grafana

# Default credentials (change immediately):
# Username: admin
# Password: admin

# Import dashboards from infrastructure/monitoring/dashboards/
```

---

## Configuration

### Environment Variables

Key variables to configure in `.env`:

```bash
# Database
POSTGRES_SERVER=postgres
POSTGRES_USER=raguser
POSTGRES_PASSWORD=<change-me>
POSTGRES_DB=ragchatbot

# Redis
REDIS_HOST=redis
REDIS_PASSWORD=<change-me>

# MinIO / S3
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=<change-me>
MINIO_SECRET_KEY=<change-me>

# Application
SECRET_KEY=<generate-random-key>
ENVIRONMENT=production
LOG_LEVEL=INFO

# LLM (if using API)
OPENAI_API_KEY=<your-key>
ANTHROPIC_API_KEY=<your-key>

# Module-specific (from module_config.json)
MODULE_NAME=matcher
MODULE_VERSION=1.0.0
```

### Security Hardening

```bash
# 1. Change all default passwords
# 2. Use strong SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"

# 3. Enable HTTPS (production)
# 4. Restrict network access
# 5. Enable firewall
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# 6. Regular updates
sudo apt update && sudo apt upgrade
```

---

## Troubleshooting

### Services Won't Start

```bash
# Check logs
docker-compose logs backend  # Docker
kubectl logs deployment/backend -n rag-module  # K8s
sudo journalctl -u rag-backend -f  # Systemd

# Common issues:
# - Database connection failed → Check POSTGRES_* vars
# - Redis connection failed → Check REDIS_HOST
# - Port already in use → Change port or stop conflicting service
```

### Database Migration Fails

```bash
# Check current version
alembic current

# Show migration history
alembic history

# Try manual migration
alembic upgrade head --sql  # Show SQL without executing
alembic upgrade head  # Execute migration
```

### Out of Memory

```bash
# Increase container memory (Docker)
# In docker-compose.yml:
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 4G

# Or increase VM/instance size
```

### Performance Issues

```bash
# Check resource usage
docker stats  # Docker
kubectl top pods -n rag-module  # K8s
htop  # Bare metal

# Scale up
docker-compose up -d --scale backend=3  # Docker
kubectl scale deployment backend --replicas=5 -n rag-module  # K8s
```

---

## Backup & Recovery

### Backup

```bash
# Database
pg_dump -U raguser -h localhost ragchatbot > backup.sql

# Documents (MinIO/S3)
mc mirror minio/documents ./backup/documents

# Configuration
tar -czf config-backup.tar.gz config/
```

### Recovery

```bash
# Restore database
psql -U raguser -h localhost ragchatbot < backup.sql

# Restore documents
mc mirror ./backup/documents minio/documents

# Restore configuration
tar -xzf config-backup.tar.gz
```

---

## Maintenance

### Updates

```bash
# Pull new image (Docker)
docker-compose pull backend
docker-compose up -d backend

# Update deployment (K8s)
kubectl set image deployment/backend backend=new-version -n rag-module

# Bare metal
cd src/backend
git pull  # If using git
source venv/bin/activate
pip install -r requirements.txt --upgrade
sudo systemctl restart rag-backend
```

### Log Rotation

```bash
# Docker (configure in daemon.json)
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}

# Systemd (configure logrotate)
/var/log/rag-backend/*.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    missingok
}
```

---

## Support

- **Documentation**: Check package README.md
- **Logs**: Always include logs when requesting support
- **Contact**: support@example.com
- **Emergency**: Contact your account manager

---

**Last Updated**: 2026-01-04
**Version**: 1.0.0
