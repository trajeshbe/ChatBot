# Deployment Guide

## Table of Contents

1. [Introduction](#introduction)
2. [Deployment Prerequisites](#deployment-prerequisites)
3. [Local Deployment](#local-deployment)
4. [Cloud Deployment Options](#cloud-deployment-options)
5. [Docker Deployment](#docker-deployment)
6. [Production Deployment](#production-deployment)
7. [Security Hardening](#security-hardening)
8. [Performance Optimization](#performance-optimization)
9. [Monitoring and Logging](#monitoring-and-logging)
10. [Backup and Recovery](#backup-and-recovery)
11. [Maintenance and Updates](#maintenance-and-updates)
12. [Troubleshooting Deployment Issues](#troubleshooting-deployment-issues)

---

## Introduction

This guide provides comprehensive instructions for deploying the Taxonomy Skillmatch prototype in various environments, from local development to production cloud deployments.

### Deployment Objectives

- Ensure reliable application availability
- Maintain security and data privacy
- Optimize performance and cost
- Enable scalability and monitoring
- Facilitate maintenance and updates

### Deployment Scenarios

1. **Development**: Local testing and development
2. **Staging**: Pre-production testing environment
3. **Production**: Live deployment for end users
4. **Enterprise**: Large-scale deployment with integrations

---

## Deployment Prerequisites

### Technical Requirements

#### Hardware Requirements

**Minimum**:
- CPU: 2 cores
- RAM: 4GB
- Storage: 10GB
- Network: Stable internet connection

**Recommended**:
- CPU: 4 cores
- RAM: 8GB
- Storage: 20GB SSD
- Network: High-speed internet (10+ Mbps)

#### Software Requirements

- Python 3.8 or higher
- pip (Python package manager)
- Git (for version control)
- Virtual environment tool (venv or virtualenv)

#### Cloud Platform Requirements (if applicable)

- AWS/Azure/GCP account
- Appropriate IAM permissions
- Budget allocation for compute and API costs

### Dependencies Checklist

- [ ] Python 3.8+ installed
- [ ] pip updated to latest version
- [ ] Virtual environment created
- [ ] All packages from requirements.txt installed
- [ ] OpenAI API key obtained
- [ ] Environment variables configured
- [ ] Config files in place

### Access Requirements

- OpenAI API key with sufficient credits
- Server or cloud platform credentials (for remote deployment)
- Domain name (optional, for production)
- SSL certificate (optional, for HTTPS)

---

## Local Deployment

### Step 1: Environment Setup

#### Create Project Directory

```bash
mkdir taxonomy_skillmatch_deployment
cd taxonomy_skillmatch_deployment
```

#### Clone or Copy Project Files

```bash
# If using Git
git clone <repository_url> .

# Or manually copy files to directory
```

#### Verify File Structure

```bash
ls -la
# Should show: taxonomy.py, config.py, log.py, config.yaml, requirements.txt
```

### Step 2: Virtual Environment Setup

#### Create Virtual Environment

**On Windows**:
```bash
python -m venv venv
```

**On macOS/Linux**:
```bash
python3 -m venv venv
```

#### Activate Virtual Environment

**On Windows**:
```bash
venv\Scripts\activate
```

**On macOS/Linux**:
```bash
source venv/bin/activate
```

#### Verify Activation

```bash
which python  # Should point to venv directory
```

### Step 3: Install Dependencies

```bash
# Upgrade pip first
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

# Verify installation
pip list
```

**Expected Packages**:
- langchain==0.3.10
- langchain-community==0.3.10
- langchain-core==0.3.22
- langchain-openai==0.2.12
- streamlit==1.40.2
- Plus dependencies (pydantic, pandas, etc.)

### Step 4: Configure Environment Variables

#### Create .env File

```bash
touch .env  # macOS/Linux
# Or create manually on Windows
```

#### Add API Key

```
API_KEY=sk-your-openai-api-key-here
```

**Important**: Never commit `.env` file to version control!

#### Create .gitignore (if using Git)

```
.env
*.pyc
__pycache__/
venv/
log.txt
*.log
.DS_Store
```

### Step 5: Verify Configuration

#### Check config.yaml

```bash
cat config.yaml
```

Should contain:
```yaml
taxonomy:
  taxonomy_log_file: "log.txt"
```

#### Test Configuration Loading

```bash
python -c "from config import get_config_object; print(get_config_object())"
```

### Step 6: Launch Application

```bash
streamlit run taxonomy.py
```

**Expected Output**:
```
You can now view your Streamlit app in your browser.

Local URL: http://localhost:8501
Network URL: http://192.168.x.x:8501
```

### Step 7: Verify Deployment

1. Open browser to http://localhost:8501
2. Verify UI loads correctly
3. Test with sample resume and taxonomy
4. Check results display properly
5. Test CSV download

### Local Deployment Commands Reference

```bash
# Start application
streamlit run taxonomy.py

# Start on specific port
streamlit run taxonomy.py --server.port 8502

# Start with auto-reload disabled
streamlit run taxonomy.py --server.fileWatcherType none

# Stop application
# Press Ctrl+C in terminal
```

---

## Cloud Deployment Options

### Option 1: Streamlit Community Cloud

**Advantages**:
- Free hosting for public apps
- Easy deployment from GitHub
- Automatic HTTPS
- Built-in secrets management

**Limitations**:
- Public access only (unless paid tier)
- Limited resources
- Streamlit branding

#### Deployment Steps

1. **Prepare Repository**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin <github_repo_url>
   git push -u origin main
   ```

2. **Create requirements.txt** (ensure it's up to date)

3. **Add .streamlit/config.toml** (optional):
   ```toml
   [theme]
   primaryColor = "#F63366"
   backgroundColor = "#FFFFFF"
   secondaryBackgroundColor = "#F0F2F6"
   textColor = "#262730"
   font = "sans serif"
   ```

4. **Deploy via Streamlit Cloud**:
   - Visit https://share.streamlit.io/
   - Sign in with GitHub
   - Click "New app"
   - Select repository, branch, and main file (taxonomy.py)
   - Add API_KEY to secrets

5. **Configure Secrets**:
   - In Streamlit Cloud dashboard
   - Go to App settings > Secrets
   - Add:
     ```toml
     API_KEY = "sk-your-key-here"
     ```

### Option 2: Heroku Deployment

**Advantages**:
- Free tier available
- Easy scaling
- Add-ons ecosystem
- Custom domains

**Limitations**:
- Sleeps after inactivity (free tier)
- Limited free hours
- Requires Procfile

#### Deployment Steps

1. **Install Heroku CLI**:
   ```bash
   # macOS
   brew tap heroku/brew && brew install heroku

   # Windows
   # Download from heroku.com
   ```

2. **Create Heroku App**:
   ```bash
   heroku login
   heroku create taxonomy-skillmatch-app
   ```

3. **Create Procfile**:
   ```
   web: sh setup.sh && streamlit run taxonomy.py
   ```

4. **Create setup.sh**:
   ```bash
   mkdir -p ~/.streamlit/

   echo "\
   [server]\n\
   headless = true\n\
   port = $PORT\n\
   enableCORS = false\n\
   \n\
   " > ~/.streamlit/config.toml
   ```

5. **Set Environment Variables**:
   ```bash
   heroku config:set API_KEY=sk-your-key-here
   ```

6. **Deploy**:
   ```bash
   git add .
   git commit -m "Deploy to Heroku"
   git push heroku main
   ```

7. **Open Application**:
   ```bash
   heroku open
   ```

### Option 3: AWS Deployment (EC2)

**Advantages**:
- Full control over environment
- Scalable resources
- Integration with AWS services
- Custom configurations

**Limitations**:
- Requires more setup
- Costs based on usage
- Requires AWS knowledge

#### Deployment Steps

1. **Launch EC2 Instance**:
   - Choose Ubuntu Server 22.04 LTS
   - Select instance type (t2.micro for testing, t2.medium for production)
   - Configure security group (allow port 8501)
   - Create or select key pair

2. **Connect to Instance**:
   ```bash
   ssh -i your-key.pem ubuntu@<instance-public-ip>
   ```

3. **Install Dependencies**:
   ```bash
   # Update system
   sudo apt update && sudo apt upgrade -y

   # Install Python
   sudo apt install python3-pip python3-venv -y

   # Create project directory
   mkdir ~/taxonomy_skillmatch
   cd ~/taxonomy_skillmatch
   ```

4. **Upload Project Files**:
   ```bash
   # From local machine
   scp -i your-key.pem -r ./* ubuntu@<instance-ip>:~/taxonomy_skillmatch/
   ```

5. **Setup Application**:
   ```bash
   # Create virtual environment
   python3 -m venv venv
   source venv/bin/activate

   # Install requirements
   pip install -r requirements.txt

   # Create .env file
   echo "API_KEY=sk-your-key-here" > .env
   ```

6. **Run with Screen (keeps running after disconnect)**:
   ```bash
   # Install screen
   sudo apt install screen -y

   # Start screen session
   screen -S streamlit

   # Run application
   streamlit run taxonomy.py --server.port 8501 --server.address 0.0.0.0

   # Detach: Ctrl+A then D
   # Reattach: screen -r streamlit
   ```

7. **Access Application**:
   - Navigate to http://<instance-public-ip>:8501

8. **Optional: Setup Nginx Reverse Proxy**:
   ```bash
   # Install Nginx
   sudo apt install nginx -y

   # Configure Nginx
   sudo nano /etc/nginx/sites-available/taxonomy
   ```

   Add:
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://localhost:8501;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
           proxy_set_header Host $host;
           proxy_cache_bypass $http_upgrade;
       }
   }
   ```

   Enable and restart:
   ```bash
   sudo ln -s /etc/nginx/sites-available/taxonomy /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

### Option 4: Azure App Service

**Advantages**:
- Managed platform
- Easy scaling
- Integration with Azure services
- Auto-deployment from Git

**Limitations**:
- Costs based on tier
- Less control than VMs
- Azure-specific knowledge needed

#### Deployment Steps

1. **Install Azure CLI**:
   ```bash
   curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
   ```

2. **Login to Azure**:
   ```bash
   az login
   ```

3. **Create Resource Group**:
   ```bash
   az group create --name taxonomy-rg --location eastus
   ```

4. **Create App Service Plan**:
   ```bash
   az appservice plan create --name taxonomy-plan --resource-group taxonomy-rg --sku B1 --is-linux
   ```

5. **Create Web App**:
   ```bash
   az webapp create --resource-group taxonomy-rg --plan taxonomy-plan --name taxonomy-skillmatch --runtime "PYTHON:3.11"
   ```

6. **Configure Startup Command**:
   ```bash
   az webapp config set --resource-group taxonomy-rg --name taxonomy-skillmatch --startup-file "streamlit run taxonomy.py --server.port 8000 --server.address 0.0.0.0"
   ```

7. **Set Environment Variables**:
   ```bash
   az webapp config appsettings set --resource-group taxonomy-rg --name taxonomy-skillmatch --settings API_KEY="sk-your-key-here"
   ```

8. **Deploy via Git**:
   ```bash
   # Get deployment URL
   az webapp deployment source config-local-git --name taxonomy-skillmatch --resource-group taxonomy-rg

   # Add remote and push
   git remote add azure <deployment-url>
   git push azure main
   ```

### Option 5: Google Cloud Platform (Cloud Run)

**Advantages**:
- Serverless, pay-per-use
- Auto-scaling
- Fully managed
- Easy deployment

**Limitations**:
- Requires containerization
- Cold start latency
- GCP knowledge needed

#### Deployment Steps (see Docker section below for containerization)

---

## Docker Deployment

### Why Docker?

- Consistent environment across deployments
- Easy scaling and orchestration
- Simplified dependency management
- Portable across cloud providers

### Step 1: Create Dockerfile

Create `Dockerfile` in project root:

```dockerfile
# Use official Python runtime as base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8501

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY taxonomy.py .
COPY config.py .
COPY log.py .
COPY config.yaml .

# Create directory for logs
RUN mkdir -p /app/logs

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Run application
CMD ["streamlit", "run", "taxonomy.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Step 2: Create .dockerignore

```
.env
.git
.gitignore
venv/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
log.txt
*.log
.DS_Store
README.md
documentation/
```

### Step 3: Build Docker Image

```bash
docker build -t taxonomy-skillmatch:latest .
```

### Step 4: Run Docker Container

```bash
docker run -d \
  --name taxonomy-app \
  -p 8501:8501 \
  -e API_KEY=sk-your-key-here \
  taxonomy-skillmatch:latest
```

### Step 5: Verify Container

```bash
# Check running containers
docker ps

# View logs
docker logs taxonomy-app

# Access shell
docker exec -it taxonomy-app /bin/bash
```

### Step 6: Access Application

Navigate to http://localhost:8501

### Docker Commands Reference

```bash
# Build image
docker build -t taxonomy-skillmatch:latest .

# Run container
docker run -d -p 8501:8501 --name taxonomy-app taxonomy-skillmatch:latest

# Stop container
docker stop taxonomy-app

# Start container
docker start taxonomy-app

# Remove container
docker rm taxonomy-app

# View logs
docker logs -f taxonomy-app

# Push to registry (after tagging)
docker tag taxonomy-skillmatch:latest your-registry/taxonomy-skillmatch:latest
docker push your-registry/taxonomy-skillmatch:latest
```

### Docker Compose (Optional)

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  taxonomy-app:
    build: .
    container_name: taxonomy-skillmatch
    ports:
      - "8501:8501"
    environment:
      - API_KEY=${API_KEY}
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

Run with:
```bash
docker-compose up -d
```

---

## Production Deployment

### Production Checklist

#### Pre-Deployment

- [ ] Code reviewed and tested
- [ ] Dependencies updated and locked
- [ ] Security audit completed
- [ ] Performance testing done
- [ ] Backup strategy defined
- [ ] Monitoring setup configured
- [ ] Documentation updated
- [ ] Rollback plan prepared

#### Infrastructure

- [ ] Server/cloud instance provisioned
- [ ] Load balancer configured (if needed)
- [ ] SSL certificate obtained and installed
- [ ] Domain name configured
- [ ] Firewall rules set
- [ ] Backup storage allocated

#### Application

- [ ] Environment variables set securely
- [ ] Logging configured for production
- [ ] Error handling verified
- [ ] API keys secured
- [ ] Rate limiting implemented (if applicable)
- [ ] Health checks configured

#### Security

- [ ] HTTPS enabled
- [ ] API keys in secure secrets management
- [ ] Input validation verified
- [ ] Dependencies scanned for vulnerabilities
- [ ] Access control implemented
- [ ] Audit logging enabled

### Production Configuration

#### Streamlit Configuration (.streamlit/config.toml)

```toml
[server]
headless = true
port = 8501
enableCORS = false
enableXsrfProtection = true
maxUploadSize = 10

[browser]
serverAddress = "your-domain.com"
gatherUsageStats = false

[theme]
primaryColor = "#F63366"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"
```

#### Environment Variables (Production)

```bash
# API Configuration
API_KEY=<secure-key-from-secrets-manager>

# Application Settings
ENVIRONMENT=production
LOG_LEVEL=INFO
MAX_UPLOAD_SIZE=10485760  # 10MB in bytes

# Feature Flags
ENABLE_ANALYTICS=true
ENABLE_ERROR_TRACKING=true
```

### Process Management with Systemd (Linux)

Create `/etc/systemd/system/taxonomy.service`:

```ini
[Unit]
Description=Taxonomy Skillmatch Application
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/taxonomy_skillmatch
Environment="PATH=/opt/taxonomy_skillmatch/venv/bin"
Environment="API_KEY=<your-key>"
ExecStart=/opt/taxonomy_skillmatch/venv/bin/streamlit run taxonomy.py --server.port 8501 --server.address 0.0.0.0
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable taxonomy.service
sudo systemctl start taxonomy.service
sudo systemctl status taxonomy.service
```

### Load Balancing (Multiple Instances)

#### Nginx Load Balancer Configuration

```nginx
upstream taxonomy_backend {
    least_conn;
    server 127.0.0.1:8501;
    server 127.0.0.1:8502;
    server 127.0.0.1:8503;
}

server {
    listen 80;
    server_name your-domain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://taxonomy_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;

        # Timeout settings
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

### Auto-Scaling (AWS Example)

Create Launch Template and Auto Scaling Group with CloudFormation or Terraform.

---

## Security Hardening

### API Key Management

#### Use Secrets Manager (AWS)

```bash
# Store secret
aws secretsmanager create-secret \
    --name taxonomy/api-key \
    --secret-string '{"API_KEY":"sk-your-key-here"}'

# Retrieve in application (modify config.py)
import boto3
import json

def get_secret():
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId='taxonomy/api-key')
    secret = json.loads(response['SecretString'])
    return secret['API_KEY']
```

#### Use Azure Key Vault

```python
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

credential = DefaultAzureCredential()
client = SecretClient(vault_url="https://your-vault.vault.azure.net/", credential=credential)
api_key = client.get_secret("API-KEY").value
```

### Input Validation

Add to taxonomy.py:

```python
def validate_file_size(file, max_size_mb=10):
    """Validate uploaded file size"""
    file.seek(0, 2)  # Seek to end
    size = file.tell()
    file.seek(0)  # Reset
    max_bytes = max_size_mb * 1024 * 1024
    if size > max_bytes:
        raise ValueError(f"File size exceeds {max_size_mb}MB limit")
    return True

def sanitize_input(text):
    """Basic sanitization of text input"""
    # Remove potentially harmful patterns
    import re
    # Add sanitization logic as needed
    return text.strip()
```

### Rate Limiting

Implement rate limiting for API calls:

```python
from datetime import datetime, timedelta
import streamlit as st

def check_rate_limit(max_requests=10, time_window_minutes=60):
    """Simple rate limiting using session state"""
    if 'request_times' not in st.session_state:
        st.session_state['request_times'] = []

    now = datetime.now()
    cutoff = now - timedelta(minutes=time_window_minutes)

    # Remove old requests
    st.session_state['request_times'] = [
        t for t in st.session_state['request_times'] if t > cutoff
    ]

    # Check limit
    if len(st.session_state['request_times']) >= max_requests:
        return False

    # Add current request
    st.session_state['request_times'].append(now)
    return True
```

### HTTPS Configuration

Ensure SSL/TLS is enabled:

1. **Obtain SSL Certificate**:
   - Use Let's Encrypt (free)
   - Purchase from CA
   - Use cloud provider's certificate service

2. **Configure Web Server** (Nginx example above)

3. **Force HTTPS** (redirect HTTP to HTTPS)

### Firewall Rules

**AWS Security Group**:
```
Inbound Rules:
- Port 443 (HTTPS): 0.0.0.0/0
- Port 22 (SSH): Your-IP-Only

Outbound Rules:
- All traffic: 0.0.0.0/0 (for API calls)
```

**Linux UFW**:
```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

---

## Performance Optimization

### Application-Level Optimizations

#### Caching Results

```python
from functools import lru_cache
import hashlib

@lru_cache(maxsize=100)
def cached_classification(content_hash, taxonomy_hash):
    """Cache results for identical inputs"""
    # Implementation
    pass

def get_hash(content):
    return hashlib.md5(content.encode()).hexdigest()
```

#### Streamlit Caching

```python
@st.cache_data
def load_taxonomy(taxonomy_file):
    """Cache taxonomy loading"""
    return json.load(taxonomy_file)

@st.cache_resource
def get_classifier():
    """Cache classifier initialization"""
    return ContentClassification()
```

### Infrastructure Optimizations

1. **Use CDN** for static assets
2. **Enable Gzip compression** in web server
3. **Optimize instance size** based on load
4. **Use SSD storage** for faster I/O
5. **Configure swap** for memory-intensive operations

### Database Caching (if implementing persistence)

Consider Redis for caching:

```python
import redis
import json

r = redis.Redis(host='localhost', port=6379, db=0)

def get_cached_result(resume_hash):
    cached = r.get(f"result:{resume_hash}")
    if cached:
        return json.loads(cached)
    return None

def cache_result(resume_hash, result, expire=3600):
    r.setex(f"result:{resume_hash}", expire, json.dumps(result))
```

---

## Monitoring and Logging

### Application Logging

Enhanced logging setup:

```python
import logging
from logging.handlers import RotatingFileHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('app.log', maxBytes=10485760, backupCount=5),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Usage
logger.info("Processing resume")
logger.error("Error occurred", exc_info=True)
```

### Metrics Collection

Track key metrics:

```python
import time

metrics = {
    'total_requests': 0,
    'successful_classifications': 0,
    'errors': 0,
    'avg_processing_time': 0
}

def track_request(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        try:
            result = func(*args, **kwargs)
            metrics['successful_classifications'] += 1
            return result
        except Exception as e:
            metrics['errors'] += 1
            raise
        finally:
            duration = time.time() - start
            metrics['total_requests'] += 1
            # Update average
            metrics['avg_processing_time'] = (
                (metrics['avg_processing_time'] * (metrics['total_requests'] - 1) + duration) /
                metrics['total_requests']
            )
    return wrapper
```

### Health Check Endpoint

Add health check:

```python
# In taxonomy.py, add a simple health check
if st.sidebar.button("Health Check"):
    try:
        # Test LLM connectivity
        test_response = classifier.llm_model.invoke("test")
        st.sidebar.success("System healthy")
    except Exception as e:
        st.sidebar.error(f"System unhealthy: {str(e)}")
```

### Cloud Monitoring Services

- **AWS CloudWatch**: Logs, metrics, alarms
- **Azure Monitor**: Application insights
- **Google Cloud Operations**: Logging and monitoring
- **Third-party**: Datadog, New Relic, Prometheus + Grafana

---

## Backup and Recovery

### Backup Strategy

#### Configuration Files

```bash
# Automated backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/taxonomy"

mkdir -p $BACKUP_DIR
tar -czf $BACKUP_DIR/config_$DATE.tar.gz \
    config.yaml \
    .env \
    .streamlit/

# Keep only last 30 days
find $BACKUP_DIR -name "config_*.tar.gz" -mtime +30 -delete
```

#### Log Files

```bash
# Log rotation with logrotate
# /etc/logrotate.d/taxonomy

/opt/taxonomy_skillmatch/log.txt {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0644 www-data www-data
}
```

### Disaster Recovery Plan

1. **Regular Backups**: Daily automated backups
2. **Offsite Storage**: Store backups in different region
3. **Version Control**: Keep code in Git repository
4. **Documentation**: Maintain deployment runbooks
5. **Testing**: Regularly test restoration procedures

### Recovery Procedures

#### Application Recovery

```bash
# Stop current application
sudo systemctl stop taxonomy.service

# Restore from backup
cd /opt/taxonomy_skillmatch
tar -xzf /backups/taxonomy/config_YYYYMMDD_HHMMSS.tar.gz

# Restart application
sudo systemctl start taxonomy.service
```

#### Database Recovery (if implemented)

```bash
# Restore from backup
# Example for PostgreSQL
pg_restore -d taxonomy_db /backups/db_backup.dump
```

---

## Maintenance and Updates

### Update Procedures

#### Dependency Updates

```bash
# Check for outdated packages
pip list --outdated

# Update specific package
pip install --upgrade langchain

# Update all packages (with caution)
pip install --upgrade -r requirements.txt

# Freeze updated dependencies
pip freeze > requirements.txt
```

#### Application Updates

```bash
# 1. Backup current version
sudo systemctl stop taxonomy.service
cp -r /opt/taxonomy_skillmatch /opt/taxonomy_skillmatch_backup

# 2. Pull updates
cd /opt/taxonomy_skillmatch
git pull origin main

# 3. Install new dependencies
source venv/bin/activate
pip install -r requirements.txt

# 4. Test in staging (if available)

# 5. Deploy to production
sudo systemctl start taxonomy.service

# 6. Verify
curl http://localhost:8501/_stcore/health
```

### Maintenance Schedule

**Daily**:
- Monitor error logs
- Check API usage and costs
- Review performance metrics

**Weekly**:
- Review system health
- Check disk space
- Analyze user feedback

**Monthly**:
- Update dependencies (patch versions)
- Review and update documentation
- Conduct security audit
- Test backup restoration

**Quarterly**:
- Major dependency updates
- Performance optimization review
- Capacity planning
- Disaster recovery testing

### Rollback Procedures

```bash
# If update causes issues:

# 1. Stop service
sudo systemctl stop taxonomy.service

# 2. Restore backup
rm -rf /opt/taxonomy_skillmatch
mv /opt/taxonomy_skillmatch_backup /opt/taxonomy_skillmatch

# 3. Restart service
sudo systemctl start taxonomy.service

# 4. Verify
curl http://localhost:8501/_stcore/health

# 5. Investigate issue in dev environment
```

---

## Troubleshooting Deployment Issues

### Common Deployment Issues

#### Issue: Application Won't Start

**Symptoms**: Service fails to start, immediate exit

**Diagnosis**:
```bash
# Check service status
sudo systemctl status taxonomy.service

# View recent logs
sudo journalctl -u taxonomy.service -n 50

# Check application logs
tail -f /opt/taxonomy_skillmatch/log.txt
```

**Solutions**:
- Verify Python version
- Check dependencies installed
- Verify environment variables set
- Check file permissions
- Ensure port is available

#### Issue: Port Already in Use

**Symptoms**: "Address already in use" error

**Diagnosis**:
```bash
# Check what's using the port
sudo lsof -i :8501
# Or
sudo netstat -tulpn | grep 8501
```

**Solutions**:
```bash
# Kill process using port
sudo kill -9 <PID>

# Or change Streamlit port
streamlit run taxonomy.py --server.port 8502
```

#### Issue: Out of Memory

**Symptoms**: Application crashes, OOM killer messages

**Diagnosis**:
```bash
# Check memory usage
free -h
top

# Check logs for OOM
dmesg | grep -i "out of memory"
```

**Solutions**:
- Increase instance RAM
- Add swap space
- Optimize application code
- Implement caching

#### Issue: Slow Performance

**Symptoms**: Long response times, timeouts

**Diagnosis**:
```bash
# Monitor system resources
htop

# Check network latency
ping api.openai.com

# Profile application
python -m cProfile taxonomy.py
```

**Solutions**:
- Upgrade instance size
- Optimize LLM calls
- Implement caching
- Use CDN
- Enable compression

#### Issue: SSL Certificate Errors

**Symptoms**: HTTPS not working, certificate warnings

**Diagnosis**:
```bash
# Check certificate validity
openssl x509 -in /path/to/cert.pem -text -noout

# Test SSL
openssl s_client -connect your-domain.com:443
```

**Solutions**:
- Renew expired certificate
- Verify certificate chain
- Check Nginx configuration
- Restart Nginx

#### Issue: API Rate Limits

**Symptoms**: 429 errors from OpenAI API

**Diagnosis**:
- Check OpenAI dashboard for usage
- Review application logs for error rates

**Solutions**:
- Implement exponential backoff
- Add request queuing
- Upgrade OpenAI tier
- Implement local caching

### Debugging Tools

**System Level**:
```bash
# System resources
htop
iotop
iftop

# Process monitoring
ps aux | grep streamlit

# Network debugging
tcpdump -i any port 8501
```

**Application Level**:
```bash
# Python debugging
python -m pdb taxonomy.py

# Streamlit debugging
streamlit run taxonomy.py --logger.level=debug

# Trace system calls
strace -p <PID>
```

### Getting Help

1. **Check Logs**: Always start with log files
2. **Review Documentation**: Consult official docs
3. **Search Issues**: GitHub issues, Stack Overflow
4. **Community Forums**: Streamlit forum, LangChain Discord
5. **Professional Support**: Consider paid support if needed

---

## Deployment Checklist

### Pre-Deployment

- [ ] All tests passing
- [ ] Code reviewed
- [ ] Documentation updated
- [ ] Dependencies locked
- [ ] Environment variables configured
- [ ] Secrets secured
- [ ] Backup plan in place

### Deployment

- [ ] Infrastructure provisioned
- [ ] Application deployed
- [ ] Health checks passing
- [ ] SSL configured (production)
- [ ] Monitoring enabled
- [ ] Logging configured
- [ ] Alerts set up

### Post-Deployment

- [ ] Smoke tests completed
- [ ] Performance verified
- [ ] Security audit passed
- [ ] Backup verified
- [ ] Documentation updated
- [ ] Team notified
- [ ] Rollback plan tested

---

## Conclusion

This deployment guide provides comprehensive instructions for deploying the Taxonomy Skillmatch prototype across various environments. Choose the deployment strategy that best fits your requirements, resources, and technical expertise.

For production deployments, prioritize security, monitoring, and maintainability. Regular updates and proactive monitoring will ensure a reliable and performant application.

---

**Last Updated**: December 2025
**Version**: 1.0 (Prototype)
