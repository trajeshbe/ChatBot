# Email Campaign Analyzer - Deployment Guide

## Table of Contents

1. [Deployment Options](#deployment-options)
2. [Local Development Setup](#local-development-setup)
3. [Streamlit Cloud Deployment](#streamlit-cloud-deployment)
4. [Docker Deployment](#docker-deployment)
5. [Production Environment Setup](#production-environment-setup)
6. [Configuration Management](#configuration-management)
7. [Security Considerations](#security-considerations)
8. [Monitoring and Maintenance](#monitoring-and-maintenance)
9. [Scaling Considerations](#scaling-considerations)
10. [Troubleshooting Deployment](#troubleshooting-deployment)
11. [CI/CD Integration](#cicd-integration)
12. [Backup and Recovery](#backup-and-recovery)

---

## Deployment Options

### Comparison Matrix

| Option | Complexity | Cost | Scalability | Control | Best For |
|--------|-----------|------|-------------|---------|----------|
| Local Dev | Low | Free | N/A | Full | Development, Testing |
| Streamlit Cloud | Low | Free/Paid | Medium | Limited | Quick Deployment, Demos |
| Docker | Medium | Varies | High | Full | Production, Containers |
| Cloud VMs | Medium | Varies | High | Full | Custom Infrastructure |
| Kubernetes | High | Varies | Very High | Full | Enterprise Scale |

### Decision Guide

**Choose Local Development if**:
- Testing and development
- Personal use only
- No external access needed
- Learning the system

**Choose Streamlit Cloud if**:
- Quick deployment needed
- Small to medium user base
- Limited technical resources
- Free tier acceptable

**Choose Docker if**:
- Production deployment
- Need containerization
- Multiple instances
- Custom infrastructure

**Choose Cloud VMs if**:
- Full control required
- Specific security requirements
- Custom networking needs
- Long-running services

**Choose Kubernetes if**:
- Enterprise scale
- High availability required
- Complex orchestration
- Advanced DevOps team

---

## Local Development Setup

### Prerequisites

**System Requirements**:
- Operating System: Windows 10+, macOS 10.14+, or Linux (Ubuntu 18.04+)
- Python: 3.11 or higher
- RAM: 4GB minimum, 8GB recommended
- Disk Space: 500MB for dependencies
- Internet: Required for initial setup

**Software Requirements**:
- Python 3.11+ with pip
- Git (optional, for version control)
- Text editor or IDE (VS Code, PyCharm, etc.)

### Step-by-Step Installation

#### 1. Install Python

**Windows**:
```bash
# Download from python.org and install
# Or use Chocolatey:
choco install python --version=3.11
```

**macOS**:
```bash
# Using Homebrew:
brew install python@3.11
```

**Linux (Ubuntu/Debian)**:
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip
```

#### 2. Clone or Download Project

**Using Git**:
```bash
git clone <repository-url>
cd email_campaign_analyzer
```

**Or Download Manually**:
- Download ZIP from repository
- Extract to desired location
- Navigate to directory

#### 3. Create Virtual Environment

**All Platforms**:
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate

# macOS/Linux:
source venv/bin/activate
```

**Verification**:
```bash
# Should show (venv) in terminal prompt
which python  # macOS/Linux
where python  # Windows
# Should point to venv directory
```

#### 4. Install Dependencies

**Using pyproject.toml** (Recommended):
```bash
pip install --upgrade pip
pip install .
```

**Or Manual Installation**:
```bash
pip install streamlit==1.46.1
pip install pandas==2.3.0
pip install numpy==2.3.1
pip install plotly==6.2.0
pip install scikit-learn==1.7.0
pip install joblib==1.5.1
pip install openpyxl==3.1.5
```

**Verification**:
```bash
pip list
# Should show all required packages with correct versions
```

#### 5. Run Application

**Start Streamlit**:
```bash
streamlit run app.py
```

**Expected Output**:
```
You can now view your Streamlit app in your browser.

Local URL: http://localhost:8501
Network URL: http://192.168.1.x:8501
```

**Access Application**:
- Open browser
- Navigate to `http://localhost:8501`
- Application should load

#### 6. Configure Settings (Optional)

**Create .streamlit/config.toml**:
```toml
[server]
port = 8501
headless = true
enableCORS = false
enableXsrfProtection = true

[browser]
gatherUsageStats = false
serverAddress = "localhost"
serverPort = 8501

[theme]
primaryColor = "#3366cc"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"
```

### Development Workflow

**Making Changes**:
1. Edit Python files
2. Save changes
3. Streamlit auto-reloads
4. Refresh browser if needed

**Stopping Application**:
- Press `Ctrl+C` in terminal
- Or close terminal window

**Restarting**:
```bash
streamlit run app.py
```

### Common Development Issues

**Problem**: "Module not found" error
**Solution**:
```bash
# Ensure virtual environment activated
source venv/bin/activate  # or venv\Scripts\activate
# Reinstall dependencies
pip install -r requirements.txt
```

**Problem**: Port 8501 already in use
**Solution**:
```bash
# Use different port
streamlit run app.py --server.port 8502
```

**Problem**: Changes not reflecting
**Solution**:
- Check file saved
- Hard refresh browser (Ctrl+F5)
- Restart Streamlit server
- Clear Streamlit cache: Click menu → "Clear cache"

---

## Streamlit Cloud Deployment

### Prerequisites

**Requirements**:
- GitHub account
- Repository with code
- Streamlit Cloud account (free or paid)

### Preparation Steps

#### 1. Prepare Repository

**Required Files**:
```
email_campaign_analyzer/
├── app.py
├── feature_extractor.py
├── bot_detector.py
├── utils.py
├── create_model.py
├── requirements.txt
├── .streamlit/
│   └── config.toml
├── email_bot_detector_model.pkl
└── README.md
```

**Create requirements.txt**:
```txt
streamlit==1.46.1
pandas==2.3.0
numpy==2.3.1
plotly==6.2.0
scikit-learn==1.7.0
joblib==1.5.1
openpyxl==3.1.5
```

**Or generate automatically**:
```bash
pip freeze > requirements.txt
```

#### 2. Push to GitHub

```bash
# Initialize git (if not already)
git init

# Create .gitignore
echo "venv/" > .gitignore
echo "__pycache__/" >> .gitignore
echo "*.pyc" >> .gitignore
echo ".DS_Store" >> .gitignore

# Add files
git add .

# Commit
git commit -m "Initial commit for Streamlit Cloud deployment"

# Add remote
git remote add origin <your-github-repo-url>

# Push
git push -u origin main
```

#### 3. Deploy to Streamlit Cloud

**Steps**:
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click "New app"
4. Select repository
5. Select branch (main/master)
6. Select main file (app.py)
7. Click "Deploy"

**Advanced Settings** (Optional):
```python
# Python version
Python 3.11

# Requirements file
requirements.txt

# Secrets management
# Add in Streamlit Cloud dashboard under Settings → Secrets
```

#### 4. Configure Secrets (If Needed)

**In Streamlit Cloud Dashboard**:
- Navigate to app settings
- Click "Secrets"
- Add configuration in TOML format:

```toml
[general]
max_upload_size = 200

[model]
default_threshold = 0.5
```

**Access in Code**:
```python
import streamlit as st

max_size = st.secrets["general"]["max_upload_size"]
```

### Post-Deployment

**Monitoring**:
- Check logs in Streamlit Cloud dashboard
- Monitor app status
- Review resource usage

**Updates**:
- Push changes to GitHub
- Streamlit Cloud auto-deploys on push
- Monitor deployment logs

**Custom Domain** (Paid Plans):
- Go to app settings
- Click "Custom domain"
- Follow DNS configuration instructions
- Verify domain

### Streamlit Cloud Limitations

**Free Tier**:
- 1 private app or unlimited public apps
- Community support only
- Limited resources (1 CPU, 1GB RAM)
- No custom domain
- Apps sleep after inactivity

**Paid Tiers**:
- More apps
- More resources
- Custom domains
- Priority support
- Always-on apps

**Resource Limits**:
- File upload: 200MB default
- Memory: 1-8GB depending on plan
- Execution time: No hard limit but resources are limited

### Best Practices for Streamlit Cloud

1. **Optimize Performance**:
   - Use `@st.cache_data` for expensive operations
   - Minimize dependencies
   - Optimize data processing

2. **Handle Errors Gracefully**:
   - Comprehensive error handling
   - User-friendly error messages
   - Logging for debugging

3. **Secure Sensitive Data**:
   - Use Streamlit Secrets
   - Don't commit credentials
   - Use environment variables

4. **Monitor Usage**:
   - Check logs regularly
   - Monitor resource consumption
   - Optimize as needed

---

## Docker Deployment

### Prerequisites

**Requirements**:
- Docker installed (Docker Desktop on Windows/Mac)
- Basic Docker knowledge
- Command line access

### Dockerfile Creation

**Create Dockerfile**:
```dockerfile
# Use official Python runtime
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Run Streamlit
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Docker Compose (Optional)

**Create docker-compose.yml**:
```yaml
version: '3.8'

services:
  email-analyzer:
    build: .
    ports:
      - "8501:8501"
    environment:
      - STREAMLIT_SERVER_HEADLESS=true
      - STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
    volumes:
      - ./data:/app/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### Building and Running

#### Build Image

```bash
# Build Docker image
docker build -t email-analyzer:latest .

# Verify image created
docker images | grep email-analyzer
```

#### Run Container

**Single Container**:
```bash
# Run container
docker run -p 8501:8501 email-analyzer:latest

# Run in detached mode
docker run -d -p 8501:8501 --name email-analyzer email-analyzer:latest

# Run with volume mount
docker run -d -p 8501:8501 \
  -v $(pwd)/data:/app/data \
  --name email-analyzer \
  email-analyzer:latest
```

**Using Docker Compose**:
```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild and restart
docker-compose up -d --build
```

#### Verify Deployment

```bash
# Check container status
docker ps

# View logs
docker logs email-analyzer

# Check health
docker inspect --format='{{.State.Health.Status}}' email-analyzer

# Access application
curl http://localhost:8501
```

### Docker Optimization

#### Multi-Stage Build

```dockerfile
# Build stage
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application
COPY . .

EXPOSE 8501

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

#### .dockerignore

**Create .dockerignore**:
```
venv/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
.git
.gitignore
*.md
.DS_Store
.env
.venv
*.log
data/
*.pkl.bak
```

### Docker Best Practices

1. **Security**:
   - Use official base images
   - Run as non-root user
   - Scan for vulnerabilities
   - Keep images updated

2. **Performance**:
   - Use multi-stage builds
   - Minimize layer count
   - Optimize caching
   - Use .dockerignore

3. **Maintainability**:
   - Tag images properly
   - Document in README
   - Version control Dockerfile
   - Use docker-compose for local development

---

## Production Environment Setup

### Cloud Provider Options

#### AWS Deployment

**EC2 Instance**:
```bash
# Launch EC2 instance (Ubuntu 22.04)
# Instance type: t3.medium (2 vCPU, 4GB RAM)

# SSH into instance
ssh -i keypair.pem ubuntu@<instance-ip>

# Install dependencies
sudo apt update
sudo apt install -y python3.11 python3-pip docker.io

# Clone repository
git clone <repo-url>
cd email_campaign_analyzer

# Option 1: Direct Python
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py --server.port 80

# Option 2: Docker
sudo docker build -t email-analyzer .
sudo docker run -d -p 80:8501 email-analyzer
```

**ECS (Fargate)**:
```yaml
# Task definition
{
  "family": "email-analyzer",
  "containerDefinitions": [
    {
      "name": "email-analyzer",
      "image": "your-ecr-repo/email-analyzer:latest",
      "cpu": 1024,
      "memory": 2048,
      "portMappings": [
        {
          "containerPort": 8501,
          "protocol": "tcp"
        }
      ]
    }
  ]
}
```

#### Google Cloud Platform

**Cloud Run**:
```bash
# Build and push to Container Registry
gcloud builds submit --tag gcr.io/PROJECT-ID/email-analyzer

# Deploy to Cloud Run
gcloud run deploy email-analyzer \
  --image gcr.io/PROJECT-ID/email-analyzer \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2
```

**Compute Engine**:
```bash
# Create VM instance
gcloud compute instances create email-analyzer \
  --machine-type=e2-medium \
  --zone=us-central1-a \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud

# SSH and setup
gcloud compute ssh email-analyzer
# Follow similar setup as AWS EC2
```

#### Azure

**App Service**:
```bash
# Create App Service
az webapp up \
  --name email-analyzer \
  --resource-group myResourceGroup \
  --runtime "PYTHON:3.11" \
  --sku B1

# Configure startup
az webapp config set \
  --name email-analyzer \
  --resource-group myResourceGroup \
  --startup-file "streamlit run app.py --server.port=8000"
```

**Container Instances**:
```bash
# Deploy container
az container create \
  --resource-group myResourceGroup \
  --name email-analyzer \
  --image email-analyzer:latest \
  --cpu 2 \
  --memory 4 \
  --port 8501 \
  --dns-name-label email-analyzer
```

### Reverse Proxy Setup (Nginx)

**Install Nginx**:
```bash
sudo apt install nginx
```

**Configure Nginx** (/etc/nginx/sites-available/email-analyzer):
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

        # WebSocket support
        proxy_read_timeout 86400;
    }
}
```

**Enable Site**:
```bash
sudo ln -s /etc/nginx/sites-available/email-analyzer /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### SSL/TLS Setup

**Using Let's Encrypt**:
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal is configured automatically
```

**Nginx SSL Configuration** (added by Certbot):
```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # Strong SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    location / {
        proxy_pass http://localhost:8501;
        # ... (rest of configuration)
    }
}
```

### Process Management (Systemd)

**Create Service File** (/etc/systemd/system/email-analyzer.service):
```ini
[Unit]
Description=Email Campaign Analyzer
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/email_campaign_analyzer
Environment="PATH=/home/ubuntu/email_campaign_analyzer/venv/bin"
ExecStart=/home/ubuntu/email_campaign_analyzer/venv/bin/streamlit run app.py --server.port=8501 --server.address=localhost
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and Start Service**:
```bash
sudo systemctl enable email-analyzer
sudo systemctl start email-analyzer
sudo systemctl status email-analyzer
```

---

## Configuration Management

### Environment Variables

**Create .env File**:
```bash
# Application settings
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Detection settings
DEFAULT_BOT_THRESHOLD=0.5
MAX_UPLOAD_SIZE_MB=200

# Feature flags
ENABLE_ML_PREDICTIONS=true
ENABLE_ADVANCED_ANALYTICS=true
```

**Load in Application**:
```python
import os
from dotenv import load_dotenv

load_dotenv()

PORT = os.getenv('STREAMLIT_SERVER_PORT', '8501')
THRESHOLD = float(os.getenv('DEFAULT_BOT_THRESHOLD', '0.5'))
```

### Configuration Files

**config.yaml**:
```yaml
server:
  port: 8501
  host: "0.0.0.0"
  max_upload_size: 200

detection:
  default_threshold: 0.5
  weights:
    void: 0.35
    opens_only: 0.25
    instant_activity: 0.20
    unusual_patterns: 0.15
    duration: 0.05
  thresholds:
    frequency: 10.0
    duration: 2.0
    instant_threshold: 1.0

features:
  enable_ml: true
  enable_dashboard: true
  enable_export: true

logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

**Load Configuration**:
```python
import yaml

with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

BOT_THRESHOLD = config['detection']['default_threshold']
WEIGHTS = config['detection']['weights']
```

### Secrets Management

**For Production**:
- Use cloud provider secret managers:
  - AWS Secrets Manager
  - GCP Secret Manager
  - Azure Key Vault
- Environment variables for non-sensitive config
- Never commit secrets to git

**Example (AWS Secrets Manager)**:
```python
import boto3
import json

def get_secret(secret_name):
    client = boto3.client('secretsmanager', region_name='us-east-1')
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])

# Use in application
secrets = get_secret('email-analyzer/prod')
api_key = secrets['api_key']
```

---

## Security Considerations

### Application Security

**Input Validation**:
```python
# Validate file uploads
def validate_upload(file):
    if file.size > MAX_SIZE:
        raise ValueError("File too large")

    if file.type not in ALLOWED_TYPES:
        raise ValueError("Invalid file type")

    return True
```

**Authentication** (Optional):
```python
import streamlit as st

def check_password():
    """Returns True if user has correct password."""

    def password_entered():
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        return False

    elif not st.session_state["password_correct"]:
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        st.error("Password incorrect")
        return False

    else:
        return True

if check_password():
    # Main application
    main()
```

### Infrastructure Security

**Firewall Rules**:
```bash
# Allow only necessary ports
sudo ufw allow 22/tcp  # SSH
sudo ufw allow 80/tcp  # HTTP
sudo ufw allow 443/tcp # HTTPS
sudo ufw enable
```

**Security Groups** (AWS):
```json
{
  "IpPermissions": [
    {
      "FromPort": 80,
      "ToPort": 80,
      "IpProtocol": "tcp",
      "IpRanges": [{"CidrIp": "0.0.0.0/0"}]
    },
    {
      "FromPort": 443,
      "ToPort": 443,
      "IpProtocol": "tcp",
      "IpRanges": [{"CidrIp": "0.0.0.0/0"}]
    }
  ]
}
```

**Regular Updates**:
```bash
# System updates
sudo apt update && sudo apt upgrade -y

# Python package updates
pip install --upgrade -r requirements.txt

# Docker image updates
docker pull python:3.11-slim
docker build -t email-analyzer:latest .
```

### Data Security

**File Upload Security**:
- Validate file types
- Scan for malware
- Set size limits
- Isolate uploaded files
- Clean up after processing

**Session Security**:
- No data persistence by default
- Clear session state on exit
- No logging of sensitive data
- Secure token management

---

## Monitoring and Maintenance

### Logging Setup

**Application Logging**:
```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/email-analyzer/app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Use in application
logger.info("Analysis started for %d sessions", len(data))
logger.error("Error processing file: %s", error_message)
```

**System Logging**:
```bash
# View Streamlit logs
journalctl -u email-analyzer -f

# View Nginx logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log

# View Docker logs
docker logs -f email-analyzer
```

### Monitoring Tools

**Prometheus Metrics** (Optional):
```python
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
requests_total = Counter('app_requests_total', 'Total requests')
analysis_duration = Histogram('analysis_duration_seconds', 'Analysis duration')
active_sessions = Gauge('active_sessions', 'Active sessions')

# Use in application
requests_total.inc()
with analysis_duration.time():
    results = detector.analyze(data)
```

**Health Checks**:
```python
# Add health endpoint
@app.route('/health')
def health():
    return {'status': 'healthy', 'timestamp': datetime.now().isoformat()}
```

### Maintenance Tasks

**Daily**:
- Check application logs for errors
- Monitor resource usage (CPU, memory)
- Verify backups completed

**Weekly**:
- Review performance metrics
- Check disk space
- Update dependencies if needed

**Monthly**:
- Security updates
- Log rotation
- Performance optimization review
- Backup verification

**Quarterly**:
- Major version updates
- Security audit
- Capacity planning review
- Documentation updates

---

## Scaling Considerations

### Vertical Scaling

**Increase Resources**:
```bash
# AWS EC2 - Change instance type
aws ec2 modify-instance-attribute \
  --instance-id i-xxxxx \
  --instance-type t3.large

# Docker - Increase limits
docker run -d \
  --memory="4g" \
  --cpus="2.0" \
  email-analyzer:latest
```

### Horizontal Scaling

**Load Balancer Setup** (Nginx):
```nginx
upstream email_analyzer {
    server 127.0.0.1:8501;
    server 127.0.0.1:8502;
    server 127.0.0.1:8503;
}

server {
    listen 80;

    location / {
        proxy_pass http://email_analyzer;
        # ... proxy settings
    }
}
```

**Docker Swarm**:
```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml email-analyzer

# Scale service
docker service scale email-analyzer=3
```

**Kubernetes Deployment**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: email-analyzer
spec:
  replicas: 3
  selector:
    matchLabels:
      app: email-analyzer
  template:
    metadata:
      labels:
        app: email-analyzer
    spec:
      containers:
      - name: email-analyzer
        image: email-analyzer:latest
        ports:
        - containerPort: 8501
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
```

### Performance Optimization

**Caching**:
```python
import streamlit as st

@st.cache_data
def load_model():
    return joblib.load('model.pkl')

@st.cache_data(ttl=3600)  # Cache for 1 hour
def process_data(data_hash):
    return expensive_operation(data)
```

**Database for Results** (Optional):
```python
import sqlite3

def save_results(results):
    conn = sqlite3.connect('results.db')
    results.to_sql('analysis_results', conn, if_exists='append')
    conn.close()
```

---

## Troubleshooting Deployment

### Common Issues

**Port Conflicts**:
```bash
# Find process using port
lsof -i :8501  # macOS/Linux
netstat -ano | findstr :8501  # Windows

# Kill process
kill -9 <PID>  # macOS/Linux
```

**Permission Errors**:
```bash
# Fix file permissions
chmod +x app.py
chown -R user:group /path/to/app

# Docker socket permissions
sudo usermod -aG docker $USER
newgrp docker
```

**Memory Issues**:
```bash
# Check memory usage
free -h
docker stats

# Increase swap (Linux)
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

**SSL Certificate Issues**:
```bash
# Renew certificate
sudo certbot renew

# Test renewal
sudo certbot renew --dry-run

# Force renewal
sudo certbot renew --force-renewal
```

---

## CI/CD Integration

### GitHub Actions

**Create .github/workflows/deploy.yml**:
```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt

    - name: Run tests
      run: |
        python -m pytest tests/

    - name: Build Docker image
      run: |
        docker build -t email-analyzer:${{ github.sha }} .

    - name: Deploy to server
      env:
        SSH_PRIVATE_KEY: ${{ secrets.SSH_PRIVATE_KEY }}
      run: |
        # Add deployment commands
        echo "Deploying to production..."
```

### GitLab CI/CD

**Create .gitlab-ci.yml**:
```yaml
stages:
  - build
  - test
  - deploy

build:
  stage: build
  script:
    - docker build -t email-analyzer:latest .

test:
  stage: test
  script:
    - pip install -r requirements.txt
    - pytest tests/

deploy:
  stage: deploy
  script:
    - docker push registry.gitlab.com/your-project/email-analyzer:latest
    - ssh user@server "docker pull registry.gitlab.com/your-project/email-analyzer:latest"
    - ssh user@server "docker-compose up -d"
  only:
    - main
```

---

## Backup and Recovery

### Backup Strategy

**What to Backup**:
- Application code (in version control)
- Configuration files
- Trained ML models
- Logs (if needed for compliance)
- No user data (system is stateless)

**Automated Backups**:
```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup configuration
tar -czf $BACKUP_DIR/config_$DATE.tar.gz /etc/nginx /home/ubuntu/email_campaign_analyzer/.streamlit

# Backup models
cp /home/ubuntu/email_campaign_analyzer/*.pkl $BACKUP_DIR/

# Keep only last 30 days
find $BACKUP_DIR -mtime +30 -delete

# Upload to S3 (optional)
aws s3 sync $BACKUP_DIR s3://my-backups/email-analyzer/
```

**Cron Job**:
```bash
# Add to crontab
0 2 * * * /home/ubuntu/backup.sh
```

### Disaster Recovery

**Recovery Steps**:
1. Provision new server
2. Install dependencies
3. Restore configuration from backup
4. Deploy latest code from git
5. Restore models
6. Start services
7. Verify functionality

**Recovery Time Objective (RTO)**: < 4 hours
**Recovery Point Objective (RPO)**: < 24 hours (configuration only, no user data)

---

**Version**: 1.0
**Last Updated**: December 2025
**Status**: Production Ready
