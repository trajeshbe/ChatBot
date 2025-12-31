# Deployment Guide

## Table of Contents
1. [Deployment Overview](#deployment-overview)
2. [Local Development Setup](#local-development-setup)
3. [Production Deployment](#production-deployment)
4. [Docker Deployment](#docker-deployment)
5. [Cloud Deployment Options](#cloud-deployment-options)
6. [Configuration Management](#configuration-management)
7. [Security Hardening](#security-hardening)
8. [Monitoring and Maintenance](#monitoring-and-maintenance)
9. [Backup and Recovery](#backup-and-recovery)
10. [Scaling Considerations](#scaling-considerations)

## Deployment Overview

### Deployment Architecture

The Procurement Matcher can be deployed in several configurations:

```
┌─────────────────────────────────────────────────────┐
│              Deployment Options                     │
├─────────────────────────────────────────────────────┤
│                                                     │
│  1. Local Development                              │
│     └─ Python + Streamlit (Port 8501)             │
│                                                     │
│  2. Docker Container                               │
│     └─ Containerized Application                  │
│                                                     │
│  3. Cloud Deployment                               │
│     ├─ AWS (EC2, ECS, App Runner)                │
│     ├─ Azure (App Service, Container Instances)   │
│     ├─ GCP (Cloud Run, Compute Engine)           │
│     └─ Heroku (Buildpack deployment)             │
│                                                     │
│  4. Enterprise Deployment                          │
│     ├─ Kubernetes Cluster                         │
│     ├─ Load Balancer                              │
│     ├─ Database Backend                           │
│     └─ Monitoring Stack                           │
└─────────────────────────────────────────────────────┘
```

### Prerequisites

**System Requirements**:
- Python 3.8 or higher (3.10+ recommended)
- 2GB RAM minimum (4GB recommended)
- 1GB disk space
- Internet connectivity for LLM API access

**Required Accounts**:
- OpenAI API account with active API key
- Cloud provider account (for cloud deployments)
- Docker Hub account (for container deployments)

## Local Development Setup

### Step 1: Clone or Download Application

```bash
# If using git
git clone <repository-url>
cd procurement_matcher

# Or extract from archive
unzip procurement_matcher.zip
cd procurement_matcher
```

### Step 2: Create Virtual Environment

**On Windows**:
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Verify activation
where python
# Should show path to venv\Scripts\python.exe
```

**On macOS/Linux**:
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Verify activation
which python
# Should show path to venv/bin/python
```

### Step 3: Install Dependencies

Create `requirements.txt`:

```txt
streamlit>=1.28.0
langchain>=0.1.0
langchain-core>=0.1.0
langchain-openai>=0.0.2
openai>=1.3.0
pydantic>=2.0.0
pymupdf>=1.23.0
pandas>=2.0.0
pyyaml>=6.0
python-dotenv>=1.0.0
loguru>=0.7.0
```

Install dependencies:
```bash
pip install -r requirements.txt

# Verify installation
pip list
```

### Step 4: Configure Environment Variables

Create `.env` file in the application root:

```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Optional: Other LLM providers
# ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# GOOGLE_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Optional: Logging level
LOG_LEVEL=INFO

# Optional: Custom data directory
# DATA_PATH=./data
```

**Security Note**: Never commit `.env` file to version control!

Create `.gitignore`:
```bash
# Environment
.env
venv/
__pycache__/
*.pyc

# Data
data/
logs/
*.pdf
*.txt

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db
```

### Step 5: Configure Application

Verify `config.yaml` exists:

```yaml
# Data storage directory
data_path: data

# LLM configuration
llm:
  model: gpt-4o-mini
  model_provider: openai
  temperature: 0
```

**Note**: Fix the typo "temmperature" to "temperature" if present.

### Step 6: Create Required Directories

```bash
# Create data directory
mkdir -p data

# Create logs directory (auto-created by application, but can pre-create)
mkdir -p logs

# Verify structure
ls -la
# Should show: data/ logs/ config.yaml .env
```

### Step 7: Test Installation

```bash
# Test Python imports
python -c "import streamlit; import langchain; import openai; print('All imports successful')"

# Test configuration loading
python -c "from config_reader import ConfigLoader; c = ConfigLoader(); print('Config loaded successfully')"

# Test OpenAI API key
python -c "import openai; import os; from dotenv import load_dotenv; load_dotenv(); openai.api_key = os.getenv('OPENAI_API_KEY'); print('API key configured')"
```

### Step 8: Run Application

```bash
# Start Streamlit application
streamlit run app.py

# Application will start on http://localhost:8501
```

Expected output:
```
You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.1.xxx:8501
```

### Step 9: Verify Functionality

1. Open browser to `http://localhost:8501`
2. Navigate to each tab (Legal, Procurement, Vendor Taxonomy)
3. Test with sample files
4. Verify results appear correctly

### Troubleshooting Local Setup

**Issue: "ModuleNotFoundError"**
```bash
# Ensure virtual environment is activated
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

**Issue: "Config file not found"**
```bash
# Verify config.yaml exists
ls config.yaml

# Check current directory
pwd

# Ensure running from application root
cd /path/to/procurement_matcher
streamlit run app.py
```

**Issue: "OpenAI API Error"**
```bash
# Check .env file exists
cat .env

# Verify API key format (should start with sk-)
# Test API key
python -c "import openai; import os; from dotenv import load_dotenv; load_dotenv(); client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY')); print('API key valid')"
```

## Production Deployment

### Production Checklist

Before deploying to production:

- [ ] Environment variables secured (not in code)
- [ ] API keys rotated and restricted
- [ ] Logging configured and tested
- [ ] Error handling verified
- [ ] File upload limits set
- [ ] Security headers configured
- [ ] HTTPS enabled
- [ ] Authentication implemented
- [ ] Monitoring configured
- [ ] Backup strategy defined

### Production Environment Setup

#### 1. Secure Configuration Management

**Use environment-specific configs**:

Create `config.prod.yaml`:
```yaml
data_path: /var/app/data

llm:
  model: gpt-4o-mini
  model_provider: openai
  temperature: 0

# Production-specific settings
max_file_size_mb: 10
max_batch_size: 20
session_timeout_minutes: 30
```

**Modify config_reader.py to support environment**:
```python
import os

def read_config(self):
    env = os.getenv('ENVIRONMENT', 'development')
    config_file = f"config.{env}.yaml" if env != 'development' else "config.yaml"

    if not os.path.exists(config_file):
        config_file = "config.yaml"  # Fallback

    with open(config_file, "r") as file:
        config_data = yaml.safe_load(file)

    return config_data
```

#### 2. Production Dependencies

Create `requirements.prod.txt`:
```txt
# Core dependencies
streamlit>=1.28.0
langchain>=0.1.0
langchain-core>=0.1.0
langchain-openai>=0.0.2
openai>=1.3.0
pydantic>=2.0.0
pymupdf>=1.23.0
pandas>=2.0.0
pyyaml>=6.0
python-dotenv>=1.0.0
loguru>=0.7.0

# Production extras
gunicorn>=21.2.0
uvicorn>=0.24.0
redis>=5.0.0  # For session management
psycopg2-binary>=2.9.9  # For PostgreSQL
prometheus-client>=0.19.0  # For metrics
```

#### 3. Process Management

Use a process manager for reliability:

**systemd service** (Linux):

Create `/etc/systemd/system/procurement-matcher.service`:
```ini
[Unit]
Description=Procurement Matcher Application
After=network.target

[Service]
Type=simple
User=appuser
WorkingDirectory=/opt/procurement_matcher
Environment="PATH=/opt/procurement_matcher/venv/bin"
EnvironmentFile=/opt/procurement_matcher/.env
ExecStart=/opt/procurement_matcher/venv/bin/streamlit run app.py --server.port 8501 --server.address 0.0.0.0
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable procurement-matcher
sudo systemctl start procurement-matcher
sudo systemctl status procurement-matcher
```

**Supervisor** (alternative):

Install supervisor:
```bash
sudo apt-get install supervisor
```

Create `/etc/supervisor/conf.d/procurement-matcher.conf`:
```ini
[program:procurement-matcher]
command=/opt/procurement_matcher/venv/bin/streamlit run app.py --server.port 8501 --server.address 0.0.0.0
directory=/opt/procurement_matcher
user=appuser
autostart=true
autorestart=true
stderr_logfile=/var/log/procurement-matcher/err.log
stdout_logfile=/var/log/procurement-matcher/out.log
environment=PATH="/opt/procurement_matcher/venv/bin"
```

Start:
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start procurement-matcher
```

#### 4. Reverse Proxy (Nginx)

Install Nginx:
```bash
sudo apt-get update
sudo apt-get install nginx
```

Create `/etc/nginx/sites-available/procurement-matcher`:
```nginx
server {
    listen 80;
    server_name procurement-matcher.example.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name procurement-matcher.example.com;

    # SSL certificates
    ssl_certificate /etc/letsencrypt/live/procurement-matcher.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/procurement-matcher.example.com/privkey.pem;

    # SSL settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # File upload size limit
    client_max_body_size 10M;

    # Proxy to Streamlit
    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support for Streamlit
        proxy_read_timeout 86400;
    }

    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/procurement-matcher /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### 5. SSL Certificate (Let's Encrypt)

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d procurement-matcher.example.com

# Auto-renewal is configured automatically
# Test renewal
sudo certbot renew --dry-run
```

## Docker Deployment

### Dockerfile

Create `Dockerfile`:

```dockerfile
# Use official Python runtime as base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data logs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run application
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  procurement-matcher:
    build: .
    container_name: procurement-matcher
    ports:
      - "8501:8501"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ENVIRONMENT=production
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./config.prod.yaml:/app/config.yaml
    restart: unless-stopped
    networks:
      - app-network

  # Optional: Nginx reverse proxy
  nginx:
    image: nginx:alpine
    container_name: procurement-matcher-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - procurement-matcher
    restart: unless-stopped
    networks:
      - app-network

networks:
  app-network:
    driver: bridge

volumes:
  data:
  logs:
```

### Build and Run

```bash
# Build image
docker build -t procurement-matcher:latest .

# Run container
docker run -d \
  --name procurement-matcher \
  -p 8501:8501 \
  -e OPENAI_API_KEY=${OPENAI_API_KEY} \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  procurement-matcher:latest

# Or use docker-compose
docker-compose up -d

# View logs
docker logs -f procurement-matcher

# Stop container
docker-compose down
```

### Docker Best Practices

1. **Use .dockerignore**:

```
# .dockerignore
__pycache__/
*.pyc
*.pyo
*.pyd
.env
.venv
venv/
*.log
.git/
.gitignore
data/
logs/
README.md
docs/
tests/
```

2. **Multi-stage builds** (optimization):

```dockerfile
# Build stage
FROM python:3.10-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.10-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application
COPY . .

RUN mkdir -p data logs

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

## Cloud Deployment Options

### AWS Deployment

#### Option 1: AWS EC2

**Launch EC2 Instance**:
1. Choose Ubuntu 22.04 LTS
2. Instance type: t3.medium (2 vCPU, 4GB RAM)
3. Configure security group:
   - Port 22 (SSH)
   - Port 80 (HTTP)
   - Port 443 (HTTPS)
4. Launch and SSH into instance

**Deploy Application**:
```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Python
sudo apt-get install python3.10 python3.10-venv python3-pip -y

# Clone application
git clone <repo-url>
cd procurement_matcher

# Setup (follow local setup steps)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with API keys

# Install and configure Nginx (see Production Deployment)
# Install and configure systemd service
```

#### Option 2: AWS ECS (Elastic Container Service)

**Prerequisites**:
- Docker image pushed to ECR (Elastic Container Registry)
- ECS cluster created

**Task Definition** (JSON):
```json
{
  "family": "procurement-matcher",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "procurement-matcher",
      "image": "123456789.dkr.ecr.us-east-1.amazonaws.com/procurement-matcher:latest",
      "portMappings": [
        {
          "containerPort": 8501,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "ENVIRONMENT",
          "value": "production"
        }
      ],
      "secrets": [
        {
          "name": "OPENAI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789:secret:openai-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/procurement-matcher",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

**Deploy**:
```bash
# Build and push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789.dkr.ecr.us-east-1.amazonaws.com

docker build -t procurement-matcher .
docker tag procurement-matcher:latest 123456789.dkr.ecr.us-east-1.amazonaws.com/procurement-matcher:latest
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/procurement-matcher:latest

# Create service
aws ecs create-service \
  --cluster procurement-cluster \
  --service-name procurement-matcher \
  --task-definition procurement-matcher:1 \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"
```

#### Option 3: AWS App Runner

**apprunner.yaml**:
```yaml
version: 1.0
runtime: python3
build:
  commands:
    build:
      - pip install -r requirements.txt
run:
  runtime-version: 3.10
  command: streamlit run app.py --server.port 8080 --server.address 0.0.0.0
  network:
    port: 8080
```

Deploy via AWS Console or CLI.

### Azure Deployment

#### Azure App Service

**Deploy using Azure CLI**:
```bash
# Login
az login

# Create resource group
az group create --name procurement-matcher-rg --location eastus

# Create App Service plan
az appservice plan create \
  --name procurement-matcher-plan \
  --resource-group procurement-matcher-rg \
  --sku B2 \
  --is-linux

# Create web app
az webapp create \
  --resource-group procurement-matcher-rg \
  --plan procurement-matcher-plan \
  --name procurement-matcher \
  --runtime "PYTHON:3.10"

# Configure app settings
az webapp config appsettings set \
  --resource-group procurement-matcher-rg \
  --name procurement-matcher \
  --settings OPENAI_API_KEY=${OPENAI_API_KEY}

# Deploy code
az webapp up \
  --resource-group procurement-matcher-rg \
  --name procurement-matcher \
  --runtime "PYTHON:3.10"
```

### Google Cloud Platform Deployment

#### Cloud Run

**Deploy to Cloud Run**:
```bash
# Enable Cloud Run API
gcloud services enable run.googleapis.com

# Build and deploy
gcloud run deploy procurement-matcher \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars OPENAI_API_KEY=${OPENAI_API_KEY} \
  --memory 2Gi \
  --cpu 1 \
  --timeout 300

# Get URL
gcloud run services describe procurement-matcher --region us-central1 --format 'value(status.url)'
```

### Heroku Deployment

**Procfile**:
```
web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
```

**Deploy**:
```bash
# Login
heroku login

# Create app
heroku create procurement-matcher

# Set environment variables
heroku config:set OPENAI_API_KEY=sk-xxxxx

# Deploy
git push heroku main

# Open app
heroku open
```

## Configuration Management

### Environment-Specific Configurations

**Development** (`config.yaml`):
```yaml
data_path: data
llm:
  model: gpt-4o-mini
  model_provider: openai
  temperature: 0
debug: true
log_level: DEBUG
```

**Production** (`config.prod.yaml`):
```yaml
data_path: /var/app/data
llm:
  model: gpt-4o-mini
  model_provider: openai
  temperature: 0
debug: false
log_level: INFO
max_file_size_mb: 10
rate_limit_per_minute: 30
```

### Secrets Management

**AWS Secrets Manager**:
```python
import boto3
import json

def get_secret(secret_name):
    client = boto3.client('secretsmanager', region_name='us-east-1')
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])

# Usage
secrets = get_secret('procurement-matcher/prod')
openai_key = secrets['OPENAI_API_KEY']
```

**Azure Key Vault**:
```python
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

def get_secret(vault_url, secret_name):
    credential = DefaultAzureCredential()
    client = SecretClient(vault_url=vault_url, credential=credential)
    return client.get_secret(secret_name).value

# Usage
openai_key = get_secret("https://my-vault.vault.azure.net/", "OPENAI-API-KEY")
```

## Security Hardening

### Application Security

1. **Input Validation**:

Add to `utils.py`:
```python
import os

def validate_file_upload(file, max_size_mb=10, allowed_extensions=['.pdf', '.txt']):
    # Check file size
    file.seek(0, os.SEEK_END)
    size_mb = file.tell() / (1024 * 1024)
    file.seek(0)

    if size_mb > max_size_mb:
        raise ValueError(f"File exceeds maximum size of {max_size_mb}MB")

    # Check extension
    _, ext = os.path.splitext(file.name)
    if ext.lower() not in allowed_extensions:
        raise ValueError(f"File type {ext} not allowed")

    return True
```

2. **Rate Limiting**:

Add to `app.py`:
```python
import time
from collections import defaultdict

class RateLimiter:
    def __init__(self, max_requests=10, window_seconds=60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)

    def is_allowed(self, user_id):
        now = time.time()
        self.requests[user_id] = [
            req_time for req_time in self.requests[user_id]
            if now - req_time < self.window_seconds
        ]

        if len(self.requests[user_id]) < self.max_requests:
            self.requests[user_id].append(now)
            return True
        return False

# Usage
limiter = RateLimiter(max_requests=10, window_seconds=60)
if not limiter.is_allowed(session_id):
    st.error("Rate limit exceeded. Please try again later.")
    st.stop()
```

3. **File Sanitization**:

```python
import re

def sanitize_filename(filename):
    # Remove path components
    filename = os.path.basename(filename)
    # Remove special characters
    filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
    return filename
```

### Infrastructure Security

1. **Firewall Rules**:
   - Allow only HTTPS (port 443)
   - Restrict SSH (port 22) to specific IPs
   - Block all other inbound traffic

2. **Network Security**:
   - Use VPC/Virtual Network
   - Private subnets for application servers
   - Public subnets only for load balancers

3. **Encryption**:
   - TLS 1.2+ for all connections
   - Encrypt data at rest
   - Encrypt backups

### Compliance

**GDPR Compliance**:
- Implement data retention policies
- Add user data deletion capabilities
- Log all data access
- Provide data export functionality

**SOC 2 Compliance**:
- Enable audit logging
- Implement access controls
- Regular security assessments
- Incident response procedures

## Monitoring and Maintenance

### Application Monitoring

**Health Check Endpoint**:

Add to `app.py`:
```python
import streamlit as st

def health_check():
    """Simple health check for monitoring"""
    try:
        # Check config loaded
        assert hasattr(st.session_state, 'config_loaded')
        # Check LLM accessible
        # Add more checks as needed
        return {"status": "healthy", "timestamp": time.time()}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

**Prometheus Metrics**:

Add `metrics.py`:
```python
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
request_count = Counter('procurement_matcher_requests_total', 'Total requests', ['endpoint'])
processing_time = Histogram('procurement_matcher_processing_seconds', 'Processing time')
active_sessions = Gauge('procurement_matcher_active_sessions', 'Active sessions')

# Usage
with processing_time.time():
    result = process_vendor()
request_count.labels(endpoint='procurement').inc()
```

### Log Management

**Centralized Logging**:

```python
# Update log_writer.py for cloud logging
import logging
from google.cloud import logging as cloud_logging

def setup_cloud_logging():
    client = cloud_logging.Client()
    handler = cloud_logging.handlers.CloudLoggingHandler(client)
    cloud_logger = logging.getLogger('cloudLogger')
    cloud_logger.setLevel(logging.INFO)
    cloud_logger.addHandler(handler)
    return cloud_logger
```

**Log Aggregation** (ELK Stack):
- Elasticsearch: Store logs
- Logstash: Process logs
- Kibana: Visualize logs

### Performance Monitoring

**Application Performance Monitoring (APM)**:

Options:
- New Relic
- Datadog
- AWS CloudWatch
- Azure Monitor
- Google Cloud Monitoring

**Key Metrics to Monitor**:
- Request latency
- LLM API response time
- Error rate
- Success rate
- File processing time
- Memory usage
- CPU usage

### Alerting

**Alert Rules**:
```yaml
alerts:
  - name: HighErrorRate
    condition: error_rate > 0.05
    duration: 5m
    action: send_email

  - name: SlowResponse
    condition: response_time_p95 > 30s
    duration: 10m
    action: send_slack

  - name: ServiceDown
    condition: health_check != 200
    duration: 2m
    action: page_oncall
```

## Backup and Recovery

### Data Backup Strategy

**Files to Backup**:
- Configuration files
- Environment variables (encrypted)
- Uploaded documents (if stored)
- Log files (for audit)
- Application code (versioned in git)

**Backup Schedule**:
```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backups/procurement_matcher"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup data directory
tar -czf ${BACKUP_DIR}/data_${DATE}.tar.gz /var/app/data

# Backup logs
tar -czf ${BACKUP_DIR}/logs_${DATE}.tar.gz /var/app/logs

# Backup config
cp /var/app/config.prod.yaml ${BACKUP_DIR}/config_${DATE}.yaml

# Cleanup old backups (keep 30 days)
find ${BACKUP_DIR} -name "*.tar.gz" -mtime +30 -delete
```

**Automate with cron**:
```bash
# Run daily at 2 AM
0 2 * * * /usr/local/bin/backup.sh
```

### Disaster Recovery

**Recovery Plan**:

1. **Application Failure**:
   - Restart service: `sudo systemctl restart procurement-matcher`
   - Check logs: `tail -f /var/log/procurement-matcher/error.log`
   - Rollback if needed

2. **Data Loss**:
   - Restore from latest backup
   - Verify data integrity
   - Resume operations

3. **Complete Infrastructure Loss**:
   - Provision new infrastructure
   - Restore from backups
   - Update DNS if needed
   - Verify all services operational

**Recovery Time Objective (RTO)**: 4 hours
**Recovery Point Objective (RPO)**: 24 hours

## Scaling Considerations

### Vertical Scaling

**Increase Resources**:
- More CPU for faster processing
- More RAM for larger files
- Faster disk I/O for file operations

**AWS EC2 Example**:
```bash
# Resize instance
aws ec2 modify-instance-attribute \
  --instance-id i-xxxxx \
  --instance-type t3.large
```

### Horizontal Scaling

**Load Balancing**:

```
          ┌─────────────┐
          │ Load Balancer│
          └──────┬──────┘
                 │
      ┌──────────┼──────────┐
      │          │          │
  ┌───▼───┐  ┌──▼────┐  ┌──▼────┐
  │App 1  │  │App 2  │  │App 3  │
  └───────┘  └───────┘  └───────┘
```

**Session Stickiness**:
- Use sticky sessions for Streamlit
- Or implement shared session storage (Redis)

### Caching Strategy

**Response Caching**:

```python
import hashlib
import redis

cache = redis.Redis(host='localhost', port=6379, db=0)

def cached_llm_call(content, ttl=3600):
    # Generate cache key
    cache_key = hashlib.sha256(content.encode()).hexdigest()

    # Check cache
    cached = cache.get(cache_key)
    if cached:
        return json.loads(cached)

    # Call LLM
    result = llm_chain.invoke(content)

    # Store in cache
    cache.setex(cache_key, ttl, json.dumps(result))

    return result
```

### Database for Results

**SQLite for Simple Deployments**:
```python
import sqlite3

def init_db():
    conn = sqlite3.connect('results.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY,
            timestamp DATETIME,
            type TEXT,
            requirement TEXT,
            vendor TEXT,
            score REAL,
            justification TEXT
        )
    ''')
    conn.commit()
    return conn
```

**PostgreSQL for Production**:
```python
import psycopg2

def init_db():
    conn = psycopg2.connect(
        host="localhost",
        database="procurement_matcher",
        user="appuser",
        password=os.getenv("DB_PASSWORD")
    )
    return conn
```

## Maintenance Tasks

### Regular Maintenance

**Daily**:
- Monitor error logs
- Check disk space
- Verify backups completed

**Weekly**:
- Review application metrics
- Check API usage and costs
- Update dependencies (if needed)

**Monthly**:
- Security updates
- Performance review
- Capacity planning

**Quarterly**:
- Security audit
- Disaster recovery test
- Documentation update

### Update Procedure

```bash
# 1. Backup current version
tar -czf backup_$(date +%Y%m%d).tar.gz /opt/procurement_matcher

# 2. Pull updates
cd /opt/procurement_matcher
git pull

# 3. Update dependencies
source venv/bin/activate
pip install -r requirements.txt --upgrade

# 4. Test in staging
# ... run tests ...

# 5. Restart service
sudo systemctl restart procurement-matcher

# 6. Verify
curl http://localhost:8501/health

# 7. Monitor logs
tail -f logs/error_logs.json
```

## Conclusion

This deployment guide provides comprehensive instructions for deploying the Procurement Matcher in various environments. Key takeaways:

- **Start Simple**: Begin with local or Docker deployment
- **Security First**: Implement security measures before production
- **Monitor Always**: Set up monitoring and alerting from day one
- **Plan for Scale**: Design with future growth in mind
- **Backup Everything**: Regular backups are essential
- **Document Changes**: Keep deployment documentation current

For production deployments, prioritize security, reliability, and monitoring to ensure a robust and maintainable system.
