# Planning Document Classifier - Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying the Planning Document Classifier in various environments. It covers installation, configuration, deployment options, security considerations, and operational best practices.

### Target Audience
- DevOps engineers
- System administrators
- Cloud engineers
- IT deployment specialists

### Prerequisites Knowledge
- Basic Python development
- Command line/terminal usage
- Environment variable configuration
- Web server deployment concepts

---

## Table of Contents

1. [Installation](#installation)
2. [Configuration](#configuration)
3. [Deployment Options](#deployment-options)
4. [Security Configuration](#security-configuration)
5. [Monitoring and Maintenance](#monitoring-and-maintenance)
6. [Troubleshooting](#troubleshooting)
7. [Performance Optimization](#performance-optimization)
8. [Backup and Recovery](#backup-and-recovery)

---

## Installation

### System Requirements

#### Minimum Requirements
- **Operating System**: Linux, macOS, or Windows
- **Python**: 3.11 or higher
- **RAM**: 512MB available
- **Storage**: 500MB free space
- **Network**: Outbound HTTPS access (port 443)
- **CPU**: 1 core

#### Recommended Specifications
- **Operating System**: Linux (Ubuntu 20.04+ or similar)
- **Python**: 3.11 or 3.12
- **RAM**: 1GB available (2GB for production)
- **Storage**: 2GB free space
- **Network**: Low-latency internet connection
- **CPU**: 2+ cores

#### External Dependencies
- **OpenAI API**: Active API key with GPT-4o access
- **Internet Access**: Required for API communication
- **PDF Support**: System-level PDF libraries (automatically handled)

### Step 1: Clone or Extract Source Code

#### Option A: From Git Repository
```bash
# Clone repository
git clone <repository-url>
cd planning_classifier

# Verify contents
ls -la
# Should see: app.py, classifier.py, pdf_processor.py, pyproject.toml
```

#### Option B: From Archive
```bash
# Extract archive
unzip planning_classifier.zip
cd planning_classifier

# Verify contents
ls -la
```

### Step 2: Set Up Python Environment

#### Create Virtual Environment (Recommended)
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate

# On Windows:
venv\Scripts\activate

# Verify activation
which python  # Should point to venv/bin/python
```

#### Verify Python Version
```bash
python --version
# Should output: Python 3.11.x or higher
```

### Step 3: Install Dependencies

#### Option A: Using UV (Modern, Recommended)
```bash
# Install UV if not already installed
pip install uv

# Install dependencies from pyproject.toml
uv pip install -e .

# Verify installation
uv pip list
```

#### Option B: Using pip with requirements.txt
```bash
# Create requirements.txt from pyproject.toml
cat > requirements.txt << EOF
streamlit>=1.46.1
pymupdf>=1.26.3
openai>=1.95.1
python-dotenv>=1.0.0
EOF

# Install dependencies
pip install -r requirements.txt

# Verify installation
pip list
```

#### Verify Installation
```bash
# Test imports
python -c "import streamlit; import fitz; import openai; print('All imports successful')"
```

### Step 4: System-Level Dependencies (Linux)

#### Ubuntu/Debian
```bash
# Update package list
sudo apt-get update

# Install PDF processing libraries
sudo apt-get install -y \
    libfreetype6-dev \
    libharfbuzz-dev \
    libjpeg-dev \
    libopenjp2-7-dev

# Verify installation
ldconfig -p | grep mupdf
```

#### CentOS/RHEL
```bash
# Install development tools
sudo yum groupinstall "Development Tools"

# Install PDF libraries
sudo yum install -y \
    freetype-devel \
    harfbuzz-devel \
    libjpeg-turbo-devel \
    openjpeg2-devel
```

#### macOS
```bash
# Using Homebrew
brew install mupdf freetype harfbuzz jpeg-turbo openjpeg

# Verify installation
brew list | grep mupdf
```

### Step 5: Verify Installation

#### Run Quick Test
```bash
# Test Streamlit installation
streamlit hello

# Should open browser with Streamlit demo
# Press Ctrl+C to stop
```

#### Test Application Imports
```bash
# Create test script
cat > test_imports.py << 'EOF'
import streamlit as st
import fitz
from openai import OpenAI
import os

print("✓ Streamlit imported successfully")
print("✓ PyMuPDF (fitz) imported successfully")
print("✓ OpenAI imported successfully")
print("\nAll dependencies installed correctly!")
EOF

# Run test
python test_imports.py

# Clean up
rm test_imports.py
```

---

## Configuration

### Environment Variables

#### Required Variables

**OPENAI_API_KEY**
```bash
export OPENAI_API_KEY="sk-proj-your-api-key-here"
```

- **Purpose**: Authentication for OpenAI API
- **Format**: String starting with `sk-`
- **Required**: Yes
- **Security**: Keep confidential, never commit to version control

#### Optional Variables

**STREAMLIT_SERVER_PORT**
```bash
export STREAMLIT_SERVER_PORT=8501
```
- **Purpose**: Set custom port for Streamlit server
- **Default**: 8501
- **Range**: 1024-65535

**STREAMLIT_SERVER_ADDRESS**
```bash
export STREAMLIT_SERVER_ADDRESS="0.0.0.0"
```
- **Purpose**: Set server bind address
- **Default**: localhost
- **Production**: Use 0.0.0.0 to accept external connections

### Configuration Files

#### .env File (Recommended)

Create `.env` in project root:
```bash
# .env file for Planning Document Classifier

# OpenAI API Configuration
OPENAI_API_KEY=sk-proj-your-actual-key-here

# Optional: Server Configuration
# STREAMLIT_SERVER_PORT=8501
# STREAMLIT_SERVER_ADDRESS=0.0.0.0
```

**Security Note**: Add `.env` to `.gitignore`:
```bash
echo ".env" >> .gitignore
```

#### Streamlit Configuration

Create `.streamlit/config.toml`:
```toml
[server]
# Server runs in headless mode (no browser auto-open)
headless = true

# Bind to all interfaces
address = "0.0.0.0"

# Default port
port = 8501

# Disable CORS for internal use
enableCORS = false

# Enable XSRF protection
enableXsrfProtection = true

[browser]
# Don't auto-open browser
gatherUsageStats = false

[theme]
# Optional: Customize appearance
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"
```

#### Application Configuration

No additional application-specific configuration files required. All configuration via environment variables and Streamlit config.

### Validation Script

Create configuration validation script:
```bash
cat > validate_config.py << 'EOF'
#!/usr/bin/env python3
import os
import sys

def validate():
    """Validate deployment configuration."""
    errors = []
    warnings = []

    # Check Python version
    if sys.version_info < (3, 11):
        errors.append(f"Python 3.11+ required, found {sys.version}")

    # Check OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        errors.append("OPENAI_API_KEY environment variable not set")
    elif not api_key.startswith("sk-"):
        warnings.append("OPENAI_API_KEY format seems incorrect")

    # Check imports
    try:
        import streamlit
        print(f"✓ Streamlit {streamlit.__version__}")
    except ImportError:
        errors.append("Streamlit not installed")

    try:
        import fitz
        print(f"✓ PyMuPDF installed")
    except ImportError:
        errors.append("PyMuPDF not installed")

    try:
        from openai import OpenAI
        print(f"✓ OpenAI client installed")
    except ImportError:
        errors.append("OpenAI client not installed")

    # Report results
    if errors:
        print("\n❌ ERRORS:")
        for error in errors:
            print(f"  - {error}")
        return False

    if warnings:
        print("\n⚠️  WARNINGS:")
        for warning in warnings:
            print(f"  - {warning}")

    print("\n✅ Configuration valid!")
    return True

if __name__ == "__main__":
    sys.exit(0 if validate() else 1)
EOF

chmod +x validate_config.py
python validate_config.py
```

---

## Deployment Options

### Option 1: Local Development

#### Quick Start
```bash
# Set environment variable
export OPENAI_API_KEY="sk-your-key-here"

# Run application
streamlit run app.py

# Access at http://localhost:8501
```

#### With Custom Port
```bash
streamlit run app.py --server.port 8080
```

#### With Custom Address
```bash
streamlit run app.py --server.address 0.0.0.0 --server.port 8080
```

### Option 2: Replit Deployment

#### Configuration Files

**`.replit`** (already provided):
```toml
modules = ["python-3.11"]

[nix]
channel = "stable-24_05"
packages = ["freetype", "gumbo", "harfbuzz", "jbig2dec",
            "libjpeg_turbo", "mupdf", "openjpeg", "swig", "xcbuild"]

[deployment]
deploymentTarget = "autoscale"
run = ["streamlit", "run", "app.py", "--server.port", "5000"]

[[ports]]
localPort = 5000
externalPort = 80
```

#### Deployment Steps

1. **Create Replit Account**
   - Visit https://replit.com
   - Sign up or log in

2. **Import Project**
   - Click "Create Repl"
   - Select "Import from GitHub" or "Upload files"
   - Select Python as language

3. **Configure Secrets**
   - Click "Secrets" (lock icon) in left panel
   - Add key: `OPENAI_API_KEY`
   - Add value: Your API key
   - Click "Add secret"

4. **Deploy**
   - Click "Run" button
   - Application auto-deploys
   - Access via provided URL

5. **Production Deployment**
   - Click "Deploy" tab
   - Choose deployment plan
   - Configure domain (optional)
   - Deploy to production

### Option 3: Docker Deployment

#### Dockerfile

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libfreetype6-dev \
    libharfbuzz-dev \
    libjpeg-dev \
    libopenjp2-7-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy application files
COPY pyproject.toml .
COPY app.py .
COPY classifier.py .
COPY pdf_processor.py .
COPY .streamlit/ .streamlit/

# Install Python dependencies
RUN pip install --no-cache-dir \
    streamlit>=1.46.1 \
    pymupdf>=1.26.3 \
    openai>=1.95.1 \
    python-dotenv>=1.0.0

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run application
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

#### docker-compose.yml

Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  planning-classifier:
    build: .
    ports:
      - "8501:8501"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

#### Build and Run

```bash
# Build image
docker build -t planning-classifier:latest .

# Run container
docker run -d \
  -p 8501:8501 \
  -e OPENAI_API_KEY="sk-your-key-here" \
  --name planning-classifier \
  planning-classifier:latest

# Or use docker-compose
docker-compose up -d

# View logs
docker logs -f planning-classifier

# Stop container
docker stop planning-classifier
```

### Option 4: Cloud Platform Deployment

#### AWS (EC2)

**Launch Instance**:
```bash
# Connect to instance
ssh -i your-key.pem ubuntu@your-instance-ip

# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Python 3.11
sudo apt-get install -y python3.11 python3.11-venv python3-pip

# Clone application
git clone <your-repo-url>
cd planning_classifier

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variable
export OPENAI_API_KEY="sk-your-key-here"

# Run with nohup for persistence
nohup streamlit run app.py --server.port 8501 --server.address 0.0.0.0 &

# Or use systemd service (see below)
```

**Systemd Service** (`/etc/systemd/system/planning-classifier.service`):
```ini
[Unit]
Description=Planning Document Classifier
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/planning_classifier
Environment="PATH=/home/ubuntu/planning_classifier/venv/bin"
Environment="OPENAI_API_KEY=sk-your-key-here"
ExecStart=/home/ubuntu/planning_classifier/venv/bin/streamlit run app.py --server.port 8501 --server.address 0.0.0.0
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable planning-classifier
sudo systemctl start planning-classifier
sudo systemctl status planning-classifier
```

#### AWS (ECS with Docker)

**Task Definition** (JSON):
```json
{
  "family": "planning-classifier",
  "containerDefinitions": [
    {
      "name": "planning-classifier",
      "image": "your-registry/planning-classifier:latest",
      "memory": 1024,
      "cpu": 512,
      "essential": true,
      "portMappings": [
        {
          "containerPort": 8501,
          "hostPort": 8501,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "OPENAI_API_KEY",
          "value": "sk-your-key-here"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/planning-classifier",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

#### Google Cloud Platform (Cloud Run)

```bash
# Build and push image
gcloud builds submit --tag gcr.io/PROJECT_ID/planning-classifier

# Deploy to Cloud Run
gcloud run deploy planning-classifier \
  --image gcr.io/PROJECT_ID/planning-classifier \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars OPENAI_API_KEY=sk-your-key-here \
  --memory 1Gi \
  --cpu 1 \
  --port 8501

# Get service URL
gcloud run services describe planning-classifier \
  --platform managed \
  --region us-central1 \
  --format 'value(status.url)'
```

#### Heroku

**Procfile**:
```
web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
```

**Deployment**:
```bash
# Login to Heroku
heroku login

# Create app
heroku create your-app-name

# Set environment variable
heroku config:set OPENAI_API_KEY=sk-your-key-here

# Deploy
git push heroku main

# Open app
heroku open
```

#### Azure (App Service)

```bash
# Login to Azure
az login

# Create resource group
az group create --name planning-classifier-rg --location eastus

# Create App Service plan
az appservice plan create \
  --name planning-classifier-plan \
  --resource-group planning-classifier-rg \
  --sku B1 \
  --is-linux

# Create web app
az webapp create \
  --name planning-classifier \
  --resource-group planning-classifier-rg \
  --plan planning-classifier-plan \
  --runtime "PYTHON:3.11"

# Configure environment variable
az webapp config appsettings set \
  --name planning-classifier \
  --resource-group planning-classifier-rg \
  --settings OPENAI_API_KEY=sk-your-key-here

# Deploy code
az webapp up --name planning-classifier --resource-group planning-classifier-rg
```

---

## Security Configuration

### API Key Management

#### Best Practices

1. **Never Hardcode API Keys**
```python
# ❌ BAD - Never do this
OPENAI_API_KEY = "sk-hardcoded-key"

# ✅ GOOD - Always use environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
```

2. **Use Secret Management Services**
- AWS Secrets Manager
- Azure Key Vault
- Google Secret Manager
- HashiCorp Vault

3. **Rotate Keys Regularly**
```bash
# Generate new OpenAI API key
# Update in environment/secrets
# Test with new key
# Deactivate old key
```

4. **Restrict Key Permissions**
- Use API keys with minimal required permissions
- Set usage limits in OpenAI dashboard
- Monitor API usage

### Network Security

#### Firewall Configuration

**Allow Outbound HTTPS**:
```bash
# UFW (Ubuntu)
sudo ufw allow out 443/tcp

# iptables
sudo iptables -A OUTPUT -p tcp --dport 443 -j ACCEPT
```

**Restrict Inbound Access**:
```bash
# Allow only specific IPs
sudo ufw allow from 203.0.113.0/24 to any port 8501

# Or allow from internal network only
sudo ufw allow from 10.0.0.0/8 to any port 8501
```

#### HTTPS/TLS Configuration

**Using Nginx Reverse Proxy**:

`/etc/nginx/sites-available/planning-classifier`:
```nginx
server {
    listen 80;
    server_name planning-classifier.example.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name planning-classifier.example.com;

    ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_read_timeout 86400;
    }
}
```

Enable configuration:
```bash
sudo ln -s /etc/nginx/sites-available/planning-classifier /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Authentication

#### Basic Authentication with Nginx

```nginx
location / {
    auth_basic "Restricted Access";
    auth_basic_user_file /etc/nginx/.htpasswd;

    proxy_pass http://localhost:8501;
    # ... rest of proxy config
}
```

Create password file:
```bash
sudo apt-get install apache2-utils
sudo htpasswd -c /etc/nginx/.htpasswd admin
```

#### OAuth2 Proxy (Advanced)

For enterprise SSO integration, use oauth2-proxy:
```bash
# Install oauth2-proxy
wget https://github.com/oauth2-proxy/oauth2-proxy/releases/download/v7.4.0/oauth2-proxy-v7.4.0.linux-amd64.tar.gz
tar xzf oauth2-proxy-v7.4.0.linux-amd64.tar.gz

# Configure for your OAuth provider (Google, Azure AD, etc.)
# See: https://oauth2-proxy.github.io/oauth2-proxy/
```

### Data Security

#### Document Handling

- Documents processed in memory only
- No persistent storage by default
- Automatic cleanup after processing

#### Logging Security

```python
# Ensure no sensitive data in logs
# Update classifier.py if needed
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ❌ Don't log document content
# logger.info(f"Processing: {document_text}")

# ✅ Log metadata only
logger.info(f"Processing document with {len(document_text)} characters")
```

### Security Checklist

- [ ] OpenAI API key stored securely (environment variable or secret manager)
- [ ] API key not in version control
- [ ] HTTPS enabled for production
- [ ] Firewall configured appropriately
- [ ] Authentication implemented (if required)
- [ ] Regular security updates applied
- [ ] Monitoring and alerting configured
- [ ] Audit logging enabled
- [ ] Data retention policy defined
- [ ] Incident response plan documented

---

## Monitoring and Maintenance

### Application Monitoring

#### Health Check Endpoint

Streamlit provides built-in health check:
```bash
curl http://localhost:8501/_stcore/health
# Response: {"status": "ok"}
```

#### Custom Health Check Script

```bash
cat > health_check.sh << 'EOF'
#!/bin/bash

URL="http://localhost:8501/_stcore/health"
TIMEOUT=10

response=$(curl -s -o /dev/null -w "%{http_code}" --max-time $TIMEOUT $URL)

if [ "$response" = "200" ]; then
    echo "✓ Application healthy"
    exit 0
else
    echo "✗ Application unhealthy (HTTP $response)"
    exit 1
fi
EOF

chmod +x health_check.sh
```

#### Monitoring with systemd

```bash
# Check service status
sudo systemctl status planning-classifier

# View recent logs
sudo journalctl -u planning-classifier -n 100

# Follow logs
sudo journalctl -u planning-classifier -f
```

### Log Management

#### Streamlit Logs

```bash
# Default log location
~/.streamlit/logs/

# View logs
tail -f ~/.streamlit/logs/streamlit.log
```

#### Application Logs

Configure logging in `app.py`:
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/planning-classifier/app.log'),
        logging.StreamHandler()
    ]
)
```

#### Log Rotation

`/etc/logrotate.d/planning-classifier`:
```
/var/log/planning-classifier/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 ubuntu ubuntu
    sharedscripts
    postrotate
        systemctl reload planning-classifier > /dev/null 2>&1 || true
    endscript
}
```

### Performance Monitoring

#### Metrics to Track

1. **Request Metrics**
   - Documents processed per hour/day
   - Average processing time
   - Error rate

2. **System Metrics**
   - CPU usage
   - Memory usage
   - Disk I/O
   - Network traffic

3. **API Metrics**
   - OpenAI API latency
   - API error rate
   - Token usage
   - API costs

#### Monitoring with Prometheus (Example)

```python
# Install prometheus_client
# pip install prometheus-client

from prometheus_client import Counter, Histogram, start_http_server

# Metrics
documents_processed = Counter('documents_processed_total', 'Total documents processed')
processing_time = Histogram('document_processing_seconds', 'Time spent processing documents')
classification_errors = Counter('classification_errors_total', 'Total classification errors')

# Start metrics server on port 9090
start_http_server(9090)
```

### Maintenance Tasks

#### Regular Tasks

**Daily**:
- Check application health
- Review error logs
- Monitor API usage

**Weekly**:
- Review performance metrics
- Check disk space
- Update dependencies (if needed)

**Monthly**:
- Security patches
- Dependency updates
- Cost analysis
- Performance review

#### Update Procedure

```bash
# Backup current version
cp -r planning_classifier planning_classifier_backup

# Update code
git pull origin main

# Update dependencies
pip install --upgrade -r requirements.txt

# Test in staging
streamlit run app.py --server.port 8502

# If successful, restart production
sudo systemctl restart planning-classifier

# Verify
curl http://localhost:8501/_stcore/health
```

---

## Troubleshooting

### Common Issues

#### Application Won't Start

**Symptom**: Error when running `streamlit run app.py`

**Check**:
```bash
# Verify Python version
python --version

# Check dependencies
pip list | grep streamlit
pip list | grep pymupdf
pip list | grep openai

# Test imports
python -c "import streamlit; import fitz; from openai import OpenAI"

# Check port availability
netstat -tuln | grep 8501
```

**Solutions**:
- Reinstall dependencies
- Use different port
- Check Python version

#### API Key Errors

**Symptom**: "OpenAI API key not found" error

**Check**:
```bash
# Verify environment variable
echo $OPENAI_API_KEY

# Check .env file
cat .env | grep OPENAI_API_KEY

# Test API key
python -c "import os; from openai import OpenAI; client = OpenAI(api_key=os.getenv('OPENAI_API_KEY')); print('API key valid')"
```

**Solutions**:
- Set environment variable: `export OPENAI_API_KEY=sk-...`
- Create .env file with correct key
- Verify key is active in OpenAI dashboard

#### PDF Extraction Failures

**Symptom**: "Failed to extract text from PDF" errors

**Check**:
```bash
# Verify PDF library
python -c "import fitz; print(fitz.__doc__)"

# Test with sample PDF
python << EOF
import fitz
doc = fitz.open("test.pdf")
print(f"Pages: {doc.page_count}")
print(f"Text: {doc[0].get_text()[:100]}")
EOF
```

**Solutions**:
- Install system PDF libraries
- Update PyMuPDF: `pip install --upgrade pymupdf`
- Test with different PDF

#### High Memory Usage

**Symptom**: Application consuming excessive RAM

**Check**:
```bash
# Monitor memory
top -p $(pgrep -f streamlit)

# Check for large files
ls -lh *.pdf
```

**Solutions**:
- Implement file size limits
- Increase truncation threshold
- Add memory limits in Docker/systemd

### Debug Mode

Enable Streamlit debug mode:
```bash
streamlit run app.py --logger.level=debug
```

Or in `.streamlit/config.toml`:
```toml
[logger]
level = "debug"
```

### Getting Help

#### Collect Diagnostic Information

```bash
# System information
uname -a
python --version
pip list

# Application logs
tail -n 100 ~/.streamlit/logs/streamlit.log

# Error messages
sudo journalctl -u planning-classifier --since "1 hour ago"

# Resource usage
free -h
df -h
```

Include this information when seeking support.

---

## Performance Optimization

### Application Performance

#### Text Truncation Tuning

Adjust truncation limits in `classifier.py`:
```python
# Increase for better accuracy (slower)
truncate_text_for_llm(extracted_text, max_chars=60000)

# Decrease for faster processing (less accurate)
truncate_text_for_llm(extracted_text, max_chars=30000)
```

#### API Performance

Optimize OpenAI API calls:
```python
# Reduce max_tokens for faster responses
max_tokens=500  # Instead of 1000

# Increase temperature slightly for faster inference
temperature=0.5  # Instead of 0.3
```

### Infrastructure Optimization

#### Caching

Implement caching for repeated documents:
```python
import hashlib
from functools import lru_cache

@lru_cache(maxsize=100)
def classify_document_cached(text_hash):
    # Classification logic
    pass

# Use with hash
text_hash = hashlib.md5(extracted_text.encode()).hexdigest()
result = classify_document_cached(text_hash)
```

#### Load Balancing

Deploy multiple instances behind load balancer:
```nginx
upstream planning_classifier {
    server localhost:8501;
    server localhost:8502;
    server localhost:8503;
}

server {
    location / {
        proxy_pass http://planning_classifier;
    }
}
```

#### Resource Limits

Set limits in systemd service:
```ini
[Service]
MemoryLimit=1G
CPUQuota=150%
```

Or in Docker:
```bash
docker run \
  --memory="1g" \
  --cpus="1.5" \
  planning-classifier
```

---

## Backup and Recovery

### Backup Strategy

#### Application Code
```bash
# Backup script
cat > backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backups/planning-classifier"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR
tar -czf $BACKUP_DIR/app_$DATE.tar.gz \
    app.py classifier.py pdf_processor.py \
    pyproject.toml .streamlit/

# Keep only last 30 days
find $BACKUP_DIR -name "app_*.tar.gz" -mtime +30 -delete
EOF

chmod +x backup.sh
```

#### Configuration
```bash
# Backup environment and config
cp .env .env.backup
cp .streamlit/config.toml .streamlit/config.toml.backup
```

### Disaster Recovery

#### Recovery Procedure

1. **Restore from backup**:
```bash
tar -xzf app_backup.tar.gz -C /opt/planning-classifier/
```

2. **Restore configuration**:
```bash
cp .env.backup .env
```

3. **Reinstall dependencies**:
```bash
pip install -r requirements.txt
```

4. **Restart service**:
```bash
sudo systemctl restart planning-classifier
```

5. **Verify operation**:
```bash
curl http://localhost:8501/_stcore/health
```

---

## Appendix

### Deployment Checklist

**Pre-Deployment**:
- [ ] Python 3.11+ installed
- [ ] All dependencies installed
- [ ] OpenAI API key obtained
- [ ] Configuration validated
- [ ] Test run completed successfully

**Deployment**:
- [ ] Application deployed
- [ ] Environment variables set
- [ ] Service configured (if applicable)
- [ ] Firewall rules configured
- [ ] HTTPS configured (production)

**Post-Deployment**:
- [ ] Health check passing
- [ ] Test document processed successfully
- [ ] Monitoring configured
- [ ] Backup strategy implemented
- [ ] Documentation updated with deployment details

### Port Reference

| Service | Default Port | Purpose |
|---------|-------------|---------|
| Streamlit | 8501 | Main application |
| Prometheus | 9090 | Metrics (optional) |
| Nginx | 80/443 | Reverse proxy |

### Useful Commands Reference

```bash
# Start application
streamlit run app.py

# Custom port
streamlit run app.py --server.port 8080

# Check health
curl http://localhost:8501/_stcore/health

# View logs
tail -f ~/.streamlit/logs/streamlit.log

# Restart service
sudo systemctl restart planning-classifier

# Check service status
sudo systemctl status planning-classifier

# Monitor resources
htop
```

---

**Document Version**: 1.0
**Last Updated**: December 2025
**Deployment Target**: Production-ready

For additional deployment support, consult the technical architecture documentation or contact the development team.
