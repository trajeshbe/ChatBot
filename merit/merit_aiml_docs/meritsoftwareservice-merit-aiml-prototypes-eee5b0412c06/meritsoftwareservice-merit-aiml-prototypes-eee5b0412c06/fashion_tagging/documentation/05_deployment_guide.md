# Fashion Image Tagger - Deployment Guide

## Table of Contents
1. [Deployment Overview](#deployment-overview)
2. [Prerequisites](#prerequisites)
3. [Local Development Setup](#local-development-setup)
4. [Replit Deployment](#replit-deployment)
5. [Cloud Platform Deployment](#cloud-platform-deployment)
6. [Docker Deployment](#docker-deployment)
7. [Production Configuration](#production-configuration)
8. [Monitoring and Maintenance](#monitoring-and-maintenance)
9. [Troubleshooting](#troubleshooting)
10. [Security Best Practices](#security-best-practices)

---

## Deployment Overview

The Fashion Image Tagger can be deployed in multiple environments, from local development to production cloud platforms. This guide covers various deployment scenarios and best practices.

### Deployment Options

| Option | Complexity | Best For | Pros | Cons |
|--------|-----------|----------|------|------|
| Local Dev | Low | Development & testing | Easy setup, fast iteration | Not accessible remotely |
| Replit | Low | Quick prototyping | Zero config, instant deploy | Limited resources |
| Streamlit Cloud | Low | Public demos | Free tier, easy setup | Performance limits |
| AWS/GCP/Azure | High | Production | Scalable, robust | Complex setup, higher cost |
| Docker | Medium | Containerized deploy | Portable, reproducible | Requires Docker knowledge |

---

## Prerequisites

### System Requirements

**Minimum:**
- Python 3.11 or higher
- 2 GB RAM
- 1 GB free disk space
- Internet connection

**Recommended:**
- Python 3.11+
- 4 GB RAM
- 5 GB free disk space
- Stable high-speed internet

### Required Accounts
1. **OpenAI Account**: With GPT-4o API access
2. **Deployment Platform Account**: (Replit, AWS, GCP, etc.)

### API Keys and Credentials
- OpenAI API key with GPT-4o access enabled
- Billing configured for OpenAI API usage

---

## Local Development Setup

### Step 1: Install Python

**Check Python Version:**
```bash
python --version
# Should output: Python 3.11.x or higher
```

**Install Python 3.11+ (if needed):**
- **macOS**: `brew install python@3.11`
- **Ubuntu/Debian**: `sudo apt install python3.11`
- **Windows**: Download from python.org

### Step 2: Clone or Download Project

```bash
# If using git
git clone <repository-url>
cd fashion_tagging

# Or extract from zip file
unzip fashion_tagging.zip
cd fashion_tagging
```

### Step 3: Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### Step 4: Install Dependencies

**Using UV (Recommended):**
```bash
# Install uv package manager
pip install uv

# Install dependencies from pyproject.toml
uv pip install -e .
```

**Using pip:**
```bash
pip install openai>=1.97.1 streamlit>=1.47.0 python-dotenv pillow
```

### Step 5: Configure Environment Variables

Create `.env` file in project root:
```bash
# .env file
OPENAI_API_KEY=sk-your-actual-api-key-here
```

**Security Note:**
- Never commit `.env` file to version control
- Add `.env` to `.gitignore`
- Use different keys for dev/staging/production

### Step 6: Verify Installation

```bash
# Verify fashion_ontology.json exists
ls fashion_ontology.json

# Test Python import
python -c "from fashion_analyzer import FashionAnalyzer; print('Success')"
```

### Step 7: Run Application

```bash
# Start Streamlit server
streamlit run app.py

# Application will open at http://localhost:8501
```

**Custom Port:**
```bash
streamlit run app.py --server.port 5000
```

**Network Access:**
```bash
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

---

## Replit Deployment

The project is already configured for Replit deployment.

### Initial Setup

1. **Import to Replit:**
   - Go to replit.com
   - Click "Create Repl"
   - Choose "Import from GitHub" or upload files

2. **Configure Secrets:**
   - Click "Secrets" (lock icon in sidebar)
   - Add secret: `OPENAI_API_KEY` = `sk-...`

3. **Verify Configuration:**
   - Check `.replit` file exists
   - Check `pyproject.toml` exists
   - Verify `fashion_ontology.json` is present

### Configuration Files

**.replit (Already Configured):**
```toml
modules = ["python-3.11"]

[nix]
channel = "stable-25_05"

[deployment]
deploymentTarget = "autoscale"
run = ["streamlit", "run", "app.py", "--server.port", "5000"]

[[ports]]
localPort = 5000
externalPort = 80
```

**pyproject.toml (Already Configured):**
```toml
[project]
name = "repl-nix-workspace"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "openai>=1.97.1",
    "streamlit>=1.47.0",
]
```

### Running on Replit

1. Click "Run" button
2. Wait for dependencies to install
3. Application starts on port 5000
4. Access via Replit webview or public URL

### Replit Deployment

1. Click "Deploy" button
2. Choose deployment type:
   - **Autoscale**: Automatic scaling (recommended)
   - **Reserved VM**: Dedicated resources
3. Configure domain (optional)
4. Click "Deploy"

---

## Cloud Platform Deployment

### Streamlit Cloud (Easiest)

**Step 1: Prepare Repository**
```bash
# Ensure requirements.txt exists
cat > requirements.txt << EOF
openai>=1.97.1
streamlit>=1.47.0
python-dotenv
pillow
EOF

# Commit all files
git add .
git commit -m "Prepare for Streamlit Cloud deployment"
git push
```

**Step 2: Deploy to Streamlit Cloud**
1. Go to share.streamlit.io
2. Click "New app"
3. Connect GitHub repository
4. Select branch and `app.py` file
5. Add secrets in "Advanced settings":
   ```toml
   OPENAI_API_KEY = "sk-..."
   ```
6. Click "Deploy"

**Streamlit Cloud Configuration:**
```toml
# .streamlit/config.toml
[theme]
primaryColor = "#FF4B4B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"

[server]
headless = true
enableCORS = false
port = 8501
```

### AWS Deployment (EC2)

**Step 1: Launch EC2 Instance**
```bash
# Instance type: t3.small or larger
# OS: Ubuntu 22.04 LTS
# Security group: Allow port 80, 443, 8501
```

**Step 2: Connect and Setup**
```bash
# Connect via SSH
ssh -i your-key.pem ubuntu@your-instance-ip

# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
sudo apt install python3.11 python3.11-venv python3-pip -y

# Clone repository
git clone <your-repo-url>
cd fashion_tagging
```

**Step 3: Configure Application**
```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
nano .env
# Add: OPENAI_API_KEY=sk-...
```

**Step 4: Setup Systemd Service**
```bash
# Create service file
sudo nano /etc/systemd/system/fashion-tagger.service
```

```ini
[Unit]
Description=Fashion Image Tagger
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/fashion_tagging
Environment="PATH=/home/ubuntu/fashion_tagging/venv/bin"
ExecStart=/home/ubuntu/fashion_tagging/venv/bin/streamlit run app.py --server.port 8501 --server.address 0.0.0.0
Restart=always

[Install]
WantedBy=multi-user.target
```

**Step 5: Start Service**
```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable and start service
sudo systemctl enable fashion-tagger
sudo systemctl start fashion-tagger

# Check status
sudo systemctl status fashion-tagger
```

**Step 6: Configure Nginx (Optional)**
```bash
# Install Nginx
sudo apt install nginx -y

# Configure reverse proxy
sudo nano /etc/nginx/sites-available/fashion-tagger
```

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
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/fashion-tagger /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Google Cloud Platform (Cloud Run)

**Step 1: Create Dockerfile**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8080
ENV STREAMLIT_SERVER_PORT=8080
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true

EXPOSE 8080

CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]
```

**Step 2: Build and Deploy**
```bash
# Install gcloud CLI
# Authenticate
gcloud auth login

# Set project
gcloud config set project your-project-id

# Build image
gcloud builds submit --tag gcr.io/your-project-id/fashion-tagger

# Deploy to Cloud Run
gcloud run deploy fashion-tagger \
  --image gcr.io/your-project-id/fashion-tagger \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars OPENAI_API_KEY=sk-...
```

### Azure App Service

**Step 1: Create Requirements**
```bash
# requirements.txt
openai>=1.97.1
streamlit>=1.47.0
python-dotenv
pillow
```

**Step 2: Create Startup Script**
```bash
# startup.sh
#!/bin/bash
streamlit run app.py --server.port 8000 --server.address 0.0.0.0
```

**Step 3: Deploy via Azure CLI**
```bash
# Login
az login

# Create resource group
az group create --name fashion-tagger-rg --location eastus

# Create App Service plan
az appservice plan create --name fashion-tagger-plan \
  --resource-group fashion-tagger-rg \
  --sku B1 --is-linux

# Create web app
az webapp create --resource-group fashion-tagger-rg \
  --plan fashion-tagger-plan \
  --name fashion-tagger \
  --runtime "PYTHON:3.11"

# Configure environment variables
az webapp config appsettings set --resource-group fashion-tagger-rg \
  --name fashion-tagger \
  --settings OPENAI_API_KEY=sk-...

# Deploy code
az webapp deployment source config-zip \
  --resource-group fashion-tagger-rg \
  --name fashion-tagger \
  --src fashion_tagging.zip
```

---

## Docker Deployment

### Dockerfile

```dockerfile
# Use official Python runtime
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml .
COPY requirements.txt* .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir openai>=1.97.1 streamlit>=1.47.0 python-dotenv pillow

# Copy application files
COPY app.py .
COPY fashion_analyzer.py .
COPY fashion_ontology.json .
COPY .streamlit/ .streamlit/

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Run application
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  fashion-tagger:
    build: .
    ports:
      - "8501:8501"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./attached_assets:/app/attached_assets
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Build and Run

```bash
# Build image
docker build -t fashion-tagger .

# Run container
docker run -p 8501:8501 \
  -e OPENAI_API_KEY=sk-... \
  fashion-tagger

# Or use docker-compose
echo "OPENAI_API_KEY=sk-..." > .env
docker-compose up -d
```

### Docker Hub Deployment

```bash
# Tag image
docker tag fashion-tagger your-username/fashion-tagger:latest

# Push to Docker Hub
docker login
docker push your-username/fashion-tagger:latest

# Pull and run on any machine
docker pull your-username/fashion-tagger:latest
docker run -p 8501:8501 -e OPENAI_API_KEY=sk-... your-username/fashion-tagger
```

---

## Production Configuration

### Environment Variables

**Required:**
```bash
OPENAI_API_KEY=sk-...  # OpenAI API key
```

**Optional:**
```bash
STREAMLIT_SERVER_PORT=8501  # Server port
STREAMLIT_SERVER_ADDRESS=0.0.0.0  # Server address
STREAMLIT_SERVER_HEADLESS=true  # Headless mode
STREAMLIT_SERVER_ENABLE_CORS=false  # CORS settings
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false  # Disable telemetry
```

### Streamlit Configuration

**Production config.toml:**
```toml
# .streamlit/config.toml

[server]
headless = true
address = "0.0.0.0"
port = 8501
enableCORS = false
enableXsrfProtection = true
maxUploadSize = 10  # MB

[browser]
gatherUsageStats = false
serverAddress = "your-domain.com"

[theme]
primaryColor = "#FF4B4B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"

[logger]
level = "info"
messageFormat = "%(asctime)s %(levelname)s: %(message)s"
```

### Performance Tuning

**config.toml optimizations:**
```toml
[server]
maxUploadSize = 10
maxMessageSize = 200
enableStaticServing = true
runOnSave = false

[runner]
magicEnabled = false
fastReruns = true
```

### Security Headers

**Nginx security headers:**
```nginx
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "no-referrer-when-downgrade" always;
add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
```

---

## Monitoring and Maintenance

### Logging

**Application Logs:**
```python
# Add to app.py for production logging
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/fashion-tagger/app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Log analysis events
logger.info(f"Analysis started for image: {uploaded_file.name}")
logger.info(f"Analysis completed: {result['ProductType']}")
logger.error(f"Analysis failed: {str(e)}")
```

**Streamlit Logs:**
```bash
# View systemd logs
sudo journalctl -u fashion-tagger -f

# View Docker logs
docker logs -f fashion-tagger

# View Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Health Monitoring

**Health Check Endpoint:**
```python
# Streamlit includes built-in health check
# Available at: http://your-domain:8501/_stcore/health
```

**Custom Monitoring Script:**
```python
# monitor.py
import requests
import time
import logging

def check_health(url):
    try:
        response = requests.get(f"{url}/_stcore/health", timeout=5)
        return response.status_code == 200
    except Exception as e:
        logging.error(f"Health check failed: {e}")
        return False

if __name__ == "__main__":
    app_url = "http://localhost:8501"
    while True:
        if check_health(app_url):
            print("✓ Application healthy")
        else:
            print("✗ Application unhealthy")
            # Send alert notification
        time.sleep(60)  # Check every minute
```

### Usage Analytics

**Track API Usage:**
```python
# Add to fashion_analyzer.py
import logging
from datetime import datetime

class FashionAnalyzer:
    def __init__(self):
        # ... existing code ...
        self.usage_log = logging.getLogger('usage')
        handler = logging.FileHandler('usage.log')
        self.usage_log.addHandler(handler)

    def analyze_image(self, image_bytes):
        start_time = datetime.now()
        try:
            result = # ... existing analysis code ...
            duration = (datetime.now() - start_time).total_seconds()

            # Log usage
            self.usage_log.info(json.dumps({
                'timestamp': start_time.isoformat(),
                'duration_seconds': duration,
                'product_type': result.get('ProductType'),
                'success': True
            }))

            return result
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            self.usage_log.error(json.dumps({
                'timestamp': start_time.isoformat(),
                'duration_seconds': duration,
                'error': str(e),
                'success': False
            }))
            raise
```

### Cost Monitoring

**OpenAI API Cost Tracking:**
```python
# cost_tracker.py
import json
from datetime import datetime

class CostTracker:
    COST_PER_1K_TOKENS = 0.01  # Update based on current pricing

    def __init__(self, log_file='costs.log'):
        self.log_file = log_file

    def log_api_call(self, tokens_used, image_detail='high'):
        cost = (tokens_used / 1000) * self.COST_PER_1K_TOKENS

        entry = {
            'timestamp': datetime.now().isoformat(),
            'tokens': tokens_used,
            'cost_usd': cost,
            'detail': image_detail
        }

        with open(self.log_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')

    def get_total_cost(self):
        total = 0
        with open(self.log_file, 'r') as f:
            for line in f:
                entry = json.loads(line)
                total += entry['cost_usd']
        return total
```

### Backup and Recovery

**Backup Configuration:**
```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backups/fashion-tagger"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup application files
tar -czf $BACKUP_DIR/app_$DATE.tar.gz \
  app.py \
  fashion_analyzer.py \
  fashion_ontology.json \
  .streamlit/ \
  pyproject.toml

# Backup environment configuration
cp .env $BACKUP_DIR/env_$DATE.backup

# Backup logs
tar -czf $BACKUP_DIR/logs_$DATE.tar.gz /var/log/fashion-tagger/

# Remove old backups (keep last 30 days)
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
```

**Restore Process:**
```bash
#!/bin/bash
# restore.sh

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: ./restore.sh <backup_file.tar.gz>"
    exit 1
fi

# Stop service
sudo systemctl stop fashion-tagger

# Extract backup
tar -xzf $BACKUP_FILE -C /app/fashion_tagging/

# Restart service
sudo systemctl start fashion-tagger

echo "Restore completed"
```

---

## Troubleshooting

### Common Deployment Issues

#### Port Already in Use
```bash
# Find process using port
sudo lsof -i :8501

# Kill process
sudo kill -9 <PID>

# Or use different port
streamlit run app.py --server.port 8502
```

#### Permission Denied
```bash
# Fix file permissions
chmod +x app.py
chmod 644 fashion_ontology.json

# Fix directory permissions
chmod 755 .streamlit/
```

#### Module Not Found
```bash
# Verify virtual environment is activated
which python  # Should show venv path

# Reinstall dependencies
pip install --upgrade -r requirements.txt

# Check Python path
python -c "import sys; print(sys.path)"
```

#### OpenAI API Errors
```bash
# Verify API key
echo $OPENAI_API_KEY

# Test API connection
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# Check API usage and limits
# Visit: https://platform.openai.com/usage
```

#### Streamlit Won't Start
```bash
# Clear Streamlit cache
streamlit cache clear

# Check Streamlit configuration
streamlit config show

# Run in debug mode
streamlit run app.py --logger.level=debug
```

### Production Issues

#### High Memory Usage
```bash
# Monitor memory
free -h
top -p $(pgrep -f streamlit)

# Restart service periodically
# Add to crontab: 0 3 * * * systemctl restart fashion-tagger
```

#### Slow Response Times
```bash
# Check API latency
# Monitor OpenAI API response times

# Add request timeout
# In fashion_analyzer.py, modify API call:
response = self.client.chat.completions.create(
    # ... existing params ...
    timeout=30
)
```

#### Connection Timeouts
```nginx
# Increase Nginx timeouts
proxy_connect_timeout 60s;
proxy_send_timeout 60s;
proxy_read_timeout 60s;
```

---

## Security Best Practices

### API Key Management

**Environment Variables (Recommended):**
```bash
# Use environment variables, never hardcode
export OPENAI_API_KEY=sk-...

# Or use .env file (exclude from git)
echo "OPENAI_API_KEY=sk-..." > .env
echo ".env" >> .gitignore
```

**Secrets Management (Production):**
```bash
# AWS Secrets Manager
aws secretsmanager create-secret \
  --name fashion-tagger/openai-key \
  --secret-string sk-...

# Google Secret Manager
gcloud secrets create openai-api-key \
  --data-file=- <<< "sk-..."

# Azure Key Vault
az keyvault secret set \
  --vault-name fashion-tagger-vault \
  --name openai-api-key \
  --value "sk-..."
```

### Input Validation

**File Upload Restrictions:**
```python
# Add to app.py
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_TYPES = ['jpg', 'jpeg', 'png', 'webp']

uploaded_file = st.file_uploader(...)
if uploaded_file:
    # Validate size
    if uploaded_file.size > MAX_FILE_SIZE:
        st.error("File too large. Maximum 10 MB.")
        st.stop()

    # Validate type
    file_type = uploaded_file.type.split('/')[-1]
    if file_type not in ALLOWED_TYPES:
        st.error("Invalid file type.")
        st.stop()
```

### Rate Limiting

**Simple Rate Limiter:**
```python
# rate_limiter.py
from datetime import datetime, timedelta
from collections import defaultdict

class RateLimiter:
    def __init__(self, max_requests=10, window_seconds=60):
        self.max_requests = max_requests
        self.window = timedelta(seconds=window_seconds)
        self.requests = defaultdict(list)

    def is_allowed(self, client_id):
        now = datetime.now()
        # Clean old requests
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if now - req_time < self.window
        ]

        # Check limit
        if len(self.requests[client_id]) >= self.max_requests:
            return False

        # Record request
        self.requests[client_id].append(now)
        return True
```

### HTTPS Configuration

**Let's Encrypt SSL (Free):**
```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal (cron)
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### Firewall Configuration

```bash
# UFW firewall
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable

# Deny direct access to Streamlit port
sudo ufw deny 8501/tcp
```

---

## Conclusion

This deployment guide covers multiple deployment scenarios from local development to production cloud platforms. Choose the deployment method that best fits your requirements:

- **Local/Replit**: Quick prototyping and testing
- **Streamlit Cloud**: Easy public demos
- **AWS/GCP/Azure**: Production-grade scalable deployments
- **Docker**: Portable containerized deployments

Always follow security best practices, monitor your deployment, and maintain regular backups for production systems.

For additional support, refer to:
- User Guide: `03_user_guide.md`
- Technical Architecture: `02_technical_architecture.md`
- API Reference: `04_api_reference.md`
