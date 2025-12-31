# Zero-Shot NER Prototype - Deployment Guide

## Table of Contents
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Development Deployment](#development-deployment)
- [Production Deployment](#production-deployment)
- [Docker Deployment](#docker-deployment)
- [Cloud Deployment](#cloud-deployment)
- [Troubleshooting](#troubleshooting)
- [Maintenance](#maintenance)

## Prerequisites

### System Requirements

#### Hardware Requirements

**Minimum Configuration**:
- CPU: 4 cores (x86_64)
- RAM: 8GB
- Storage: 5GB free space
- Network: Internet connection for initial setup

**Recommended Configuration**:
- CPU: 8+ cores (x86_64)
- RAM: 16GB or more
- Storage: 10GB+ free space
- GPU: NVIDIA GPU with 8GB+ VRAM (optional, for faster inference)
- Network: High-bandwidth connection

**Storage Breakdown**:
- Python environment: ~2GB
- GLiNER model: ~1.5GB
- NuNER model: ~1.5GB (if enabled)
- Dependencies: ~500MB
- Logs and cache: ~500MB

#### Software Requirements

**Operating System**:
- Linux (Ubuntu 20.04+, CentOS 8+, or similar)
- Windows 10/11 with WSL2 (recommended) or native
- macOS 11+ (Big Sur or later)

**Python**:
- Version: 3.8, 3.9, 3.10, or 3.11
- Package manager: pip or conda

**Additional Tools**:
- Git (for cloning repository)
- curl or wget (for testing)
- Text editor or IDE

**Optional**:
- Docker (for containerized deployment)
- NVIDIA Docker runtime (for GPU support in containers)
- nginx or Apache (for reverse proxy in production)

### Network Requirements

**Required Ports**:
- **5000**: Flask API server (default, configurable)
- **8501**: Streamlit web interface (default, configurable)

**Firewall Configuration**:
```bash
# For Linux (ufw)
sudo ufw allow 5000/tcp
sudo ufw allow 8501/tcp

# For Linux (firewalld)
sudo firewall-cmd --permanent --add-port=5000/tcp
sudo firewall-cmd --permanent --add-port=8501/tcp
sudo firewall-cmd --reload
```

**Outbound Access**:
- Hugging Face Hub (huggingface.co): For model downloads
- PyPI (pypi.org): For package installation
- GitHub (github.com): For spaCy model downloads

## Installation

### Step 1: Clone or Extract Project

```bash
# If using Git
git clone <repository-url>
cd zero_shot_ner

# Or extract from archive
unzip zero_shot_ner.zip
cd zero_shot_ner
```

### Step 2: Set Up Python Environment

#### Option A: Using venv (Recommended)

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate

# On Windows (Command Prompt):
venv\Scripts\activate.bat

# On Windows (PowerShell):
venv\Scripts\Activate.ps1
```

#### Option B: Using conda

```bash
# Create conda environment
conda create -n zero_shot_ner python=3.10

# Activate environment
conda activate zero_shot_ner
```

### Step 3: Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

# Download spaCy language model
python -m spacy download en_core_web_sm
```

**Installation Output**:
You should see packages being installed. The process may take 5-10 minutes depending on your internet connection.

**Verify Installation**:
```bash
# Check installed packages
pip list | grep -E "(Flask|streamlit|gliner|spacy|utca)"

# Expected output (versions may vary):
# Flask                     3.0.3
# streamlit                 1.35.0
# gliner                    0.2.2
# spacy                     3.7.5
# utca                      0.1.2
```

### Step 4: Download Models

Models are downloaded automatically on first run. To pre-download:

```python
# Create a Python script: download_models.py
from api.helpers import APIHelper

helper = APIHelper()
print("Models downloaded successfully!")
```

Run the script:
```bash
python download_models.py
```

**Model Download Process**:
1. Checks `models/` directory for existing models
2. Downloads from Hugging Face Hub if not found
3. Caches models locally for future use

**Expected Download Locations**:
```
models/
├── NuNER_Zero/
│   └── models--numind--NuNER_Zero/
│       └── snapshots/9c23c2051d3e9a4a8b8ce0d132911e0000aa53c1/
└── gliner-multitask-large-v0.5/
    └── models--knowledgator--gliner-multitask-large-v0.5/
        └── snapshots/f7fd7f124545e2cf5b89d83e9e8e499d2fe6a145/
```

## Configuration

### Configuration File: `config.ini`

```ini
[path]
# Model paths (relative to project root)
numind_path = models/NuNER_Zero
gliner_path = models/gliner-multitask-large-v0.5

# Model repository IDs
numind_repo_id = numind/NuNER_Zero
gliner_repo_id = knowledgator/gliner-multitask-large-v0.5

[api]
# Server configuration
port = 5000
ip = localhost

# Startup command
flask_start_cmd = python api/model_api.py

# Auto-shutdown after N hours of inactivity
time_delta = 5

# Compute device: cpu or cuda
device = cpu

# Authentication credentials
usr = zero_shot
pwd = P@ssw0rd

# Enable both models (True) or GLiNER only (False)
both_models = False
```

### Configuration Parameters Explained

| Parameter | Description | Values | Recommendation |
|-----------|-------------|--------|----------------|
| `port` | API server port | 1024-65535 | 5000 (default) or 8000 |
| `ip` | API bind address | IP address or hostname | `localhost` (dev), `0.0.0.0` (prod) |
| `device` | Compute device | `cpu`, `cuda` | `cpu` (compatible), `cuda` (faster) |
| `time_delta` | Auto-shutdown hours | Integer | 5 (dev), disable in prod |
| `both_models` | Load both models | `True`, `False` | `False` (saves memory) |
| `usr`, `pwd` | API credentials | Any string | **Change in production!** |

### Environment-Specific Configurations

#### Development Configuration
```ini
[api]
port = 5000
ip = localhost
device = cpu
time_delta = 2
both_models = True
```

#### Production Configuration
```ini
[api]
port = 5000
ip = 0.0.0.0
device = cuda
time_delta = 24  # Or very large number to prevent auto-shutdown
both_models = False
usr = <strong_username>
pwd = <strong_password>
```

### Security Configuration

**Change Default Credentials**:
```ini
[api]
usr = production_user_$(openssl rand -hex 4)
pwd = $(openssl rand -base64 32)
```

**Use Environment Variables** (Optional):
```bash
export ZS_NER_USER="your_username"
export ZS_NER_PASS="your_password"
```

Modify `api/model_api.py` to read from environment:
```python
import os
self.users = {
    os.getenv('ZS_NER_USER', self.config_data['usr']):
    os.getenv('ZS_NER_PASS', self.config_data['pwd'])
}
```

## Development Deployment

### Quick Start for Development

```bash
# 1. Activate virtual environment
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows

# 2. Start Streamlit interface (recommended for development)
streamlit run launch.py

# Streamlit will output:
#   You can now view your Streamlit app in your browser.
#   Local URL: http://localhost:8501
#   Network URL: http://192.168.1.x:8501
```

**What Happens**:
1. Streamlit server starts on port 8501
2. Web interface loads in your default browser
3. On first prediction request, Flask API automatically starts
4. Models are loaded (may take 30-60 seconds)
5. Predictions become available

### Running API Server Independently

```bash
# Start API server manually
python api/model_api.py

# Expected output:
# model loading...
# NER loaded
# * Running on all addresses (0.0.0.0)
# * Running on http://127.0.0.1:5000
# * Running on http://192.168.1.x:5000
```

### Running Both Components Separately

**Terminal 1 - API Server**:
```bash
source venv/bin/activate
python api/model_api.py
```

**Terminal 2 - Streamlit Interface**:
```bash
source venv/bin/activate
streamlit run launch.py
```

### Development with GPU

If you have a CUDA-compatible GPU:

```bash
# Verify CUDA availability
python -c "import torch; print(f'CUDA Available: {torch.cuda.is_available()}')"

# If True, update config.ini:
# device = cuda

# Restart services
```

## Production Deployment

### Production Considerations

1. **Security**:
   - Change default credentials
   - Use HTTPS with SSL/TLS certificates
   - Implement rate limiting
   - Use reverse proxy (nginx/Apache)

2. **Reliability**:
   - Use process manager (systemd, supervisor, pm2)
   - Implement health checks
   - Set up monitoring and alerting
   - Configure log rotation

3. **Performance**:
   - Use GPU if available
   - Disable auto-shutdown (set high `time_delta`)
   - Configure worker processes for Flask
   - Implement caching strategies

4. **Scalability**:
   - Use load balancer for multiple instances
   - Implement queue system for batch processing
   - Consider containerization with Kubernetes

### Production Setup with systemd

#### Create systemd Service for API

**File**: `/etc/systemd/system/zero-shot-ner-api.service`

```ini
[Unit]
Description=Zero-Shot NER API Server
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/zero_shot_ner
Environment="PATH=/opt/zero_shot_ner/venv/bin"
ExecStart=/opt/zero_shot_ner/venv/bin/python /opt/zero_shot_ner/api/model_api.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/zero-shot-ner/api.log
StandardError=append:/var/log/zero-shot-ner/api-error.log

[Install]
WantedBy=multi-user.target
```

#### Create systemd Service for Streamlit

**File**: `/etc/systemd/system/zero-shot-ner-ui.service`

```ini
[Unit]
Description=Zero-Shot NER Streamlit UI
After=network.target zero-shot-ner-api.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/zero_shot_ner
Environment="PATH=/opt/zero_shot_ner/venv/bin"
ExecStart=/opt/zero_shot_ner/venv/bin/streamlit run launch.py --server.port=8501 --server.address=0.0.0.0
Restart=always
RestartSec=10
StandardOutput=append:/var/log/zero-shot-ner/ui.log
StandardError=append:/var/log/zero-shot-ner/ui-error.log

[Install]
WantedBy=multi-user.target
```

#### Enable and Start Services

```bash
# Create log directory
sudo mkdir -p /var/log/zero-shot-ner
sudo chown www-data:www-data /var/log/zero-shot-ner

# Reload systemd
sudo systemctl daemon-reload

# Enable services to start on boot
sudo systemctl enable zero-shot-ner-api
sudo systemctl enable zero-shot-ner-ui

# Start services
sudo systemctl start zero-shot-ner-api
sudo systemctl start zero-shot-ner-ui

# Check status
sudo systemctl status zero-shot-ner-api
sudo systemctl status zero-shot-ner-ui
```

### Nginx Reverse Proxy

**File**: `/etc/nginx/sites-available/zero-shot-ner`

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/ssl/certs/your-cert.crt;
    ssl_certificate_key /etc/ssl/private/your-key.key;

    # API Endpoint
    location /api/ {
        proxy_pass http://localhost:5000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Increase timeout for model loading
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
    }

    # Streamlit UI
    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Streamlit-specific settings
        proxy_read_timeout 86400;
    }
}
```

**Enable site**:
```bash
sudo ln -s /etc/nginx/sites-available/zero-shot-ner /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Docker Deployment

### Dockerfile

Create `Dockerfile` in project root:

```dockerfile
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt && \
    python -m spacy download en_core_web_sm

# Copy application code
COPY . .

# Create directories for models and logs
RUN mkdir -p models logs

# Expose ports
EXPOSE 5000 8501

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Default command (can be overridden)
CMD ["streamlit", "run", "launch.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  api:
    build: .
    container_name: zero-shot-ner-api
    command: python api/model_api.py
    ports:
      - "5000:5000"
    volumes:
      - ./models:/app/models
      - ./logs:/app/logs
      - ./config.ini:/app/config.ini
    environment:
      - DEVICE=cpu
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/"]
      interval: 30s
      timeout: 10s
      retries: 3

  ui:
    build: .
    container_name: zero-shot-ner-ui
    command: streamlit run launch.py --server.port=8501 --server.address=0.0.0.0
    ports:
      - "8501:8501"
    depends_on:
      - api
    volumes:
      - ./config.ini:/app/config.ini
    restart: unless-stopped

volumes:
  models:
  logs:
```

### Build and Run with Docker

```bash
# Build image
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild and restart
docker-compose up -d --build
```

### Docker with GPU Support

Update `docker-compose.yml`:

```yaml
services:
  api:
    # ... other configuration ...
    runtime: nvidia
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
      - DEVICE=cuda
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

**Prerequisites**: Install NVIDIA Docker runtime

## Cloud Deployment

### AWS EC2 Deployment

#### 1. Launch EC2 Instance

- **Instance Type**: t3.large or larger (GPU: g4dn.xlarge)
- **OS**: Ubuntu 22.04 LTS
- **Storage**: 20GB+ EBS volume
- **Security Group**: Allow ports 22, 80, 443, 5000, 8501

#### 2. Connect and Setup

```bash
# Connect to instance
ssh -i your-key.pem ubuntu@your-ec2-ip

# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install -y python3-pip python3-venv nginx

# Clone/upload project
git clone <repository-url>
cd zero_shot_ner

# Follow installation steps from above
```

#### 3. Configure Security

```bash
# Configure firewall
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable

# Set up SSL with Let's Encrypt
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### Google Cloud Platform (GCP)

Similar steps using GCP Compute Engine:
- Use n1-standard-2 or n1-highmem-2 instance
- Configure VPC firewall rules
- Use Cloud Load Balancing for high availability

### Azure Deployment

Deploy using Azure VM:
- Use Standard_D2s_v3 or larger
- Configure Network Security Group
- Use Azure Application Gateway for SSL termination

### Kubernetes Deployment

Create `k8s-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: zero-shot-ner
spec:
  replicas: 2
  selector:
    matchLabels:
      app: zero-shot-ner
  template:
    metadata:
      labels:
        app: zero-shot-ner
    spec:
      containers:
      - name: api
        image: your-registry/zero-shot-ner:latest
        ports:
        - containerPort: 5000
        env:
        - name: DEVICE
          value: "cpu"
        resources:
          requests:
            memory: "4Gi"
            cpu: "2"
          limits:
            memory: "8Gi"
            cpu: "4"
---
apiVersion: v1
kind: Service
metadata:
  name: zero-shot-ner-service
spec:
  selector:
    app: zero-shot-ner
  ports:
  - port: 80
    targetPort: 5000
  type: LoadBalancer
```

## Troubleshooting

### Common Issues

#### 1. Port Already in Use

**Error**: `Address already in use`

**Solution**:
```bash
# Find process using port 5000
lsof -i :5000  # Linux/macOS
netstat -ano | findstr :5000  # Windows

# Kill the process
kill -9 <PID>  # Linux/macOS
taskkill /F /PID <PID>  # Windows

# Or change port in config.ini
```

#### 2. Models Not Downloading

**Error**: `Connection timeout` or `Failed to download model`

**Solutions**:
- Check internet connection
- Verify firewall allows outbound HTTPS
- Try manual download:
```bash
python -c "from huggingface_hub import snapshot_download; snapshot_download('knowledgator/gliner-multitask-large-v0.5', cache_dir='models/gliner-multitask-large-v0.5')"
```

#### 3. CUDA Out of Memory

**Error**: `CUDA out of memory`

**Solutions**:
- Use CPU mode: `device = cpu` in config.ini
- Reduce batch size (modify model_api.py)
- Use a GPU with more VRAM
- Process shorter texts

#### 4. Import Errors

**Error**: `ModuleNotFoundError: No module named 'X'`

**Solution**:
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall requirements
pip install -r requirements.txt

# Verify spaCy model
python -m spacy download en_core_web_sm
```

#### 5. API Not Responding

**Symptoms**: Requests timeout or connection refused

**Solutions**:
```bash
# Check if API is running
curl http://localhost:5000/

# Check logs
tail -f logs/$(date +%d-%m-%y)/*.log

# Restart API
pkill -f model_api.py
python api/model_api.py
```

### Debug Mode

Enable debug logging:

**Modify `utils.py`**:
```python
logging.basicConfig(
    level=logging.DEBUG,  # Change from INFO
    # ... rest of config
)
```

**Run Flask in debug mode** (development only):
```python
# In model_api.py
self.app.run(debug=True, ...)
```

### Performance Issues

**Slow inference**:
- Switch to GPU: `device = cuda`
- Reduce text length
- Lower threshold to reduce entity count
- Disable both_models if not needed

**High memory usage**:
- Set `both_models = False`
- Use CPU mode
- Restart API periodically

## Maintenance

### Log Management

**Log Location**: `logs/DD-MM-YY/HH.log`

**Log Rotation**:
```bash
# Manual cleanup
find logs/ -type f -mtime +30 -delete

# Automated with cron
crontab -e
# Add: 0 0 * * * find /path/to/zero_shot_ner/logs -type f -mtime +30 -delete
```

### Model Updates

```bash
# Backup existing models
mv models models.backup

# Download new versions
python download_models.py

# Test new models
# If successful, remove backup:
rm -rf models.backup
```

### Dependency Updates

```bash
# Check for updates
pip list --outdated

# Update specific package
pip install --upgrade package_name

# Update all (with caution)
pip install --upgrade -r requirements.txt

# Test after updates
```

### Monitoring

**Health Check Script** (`monitor.sh`):
```bash
#!/bin/bash
API_URL="http://localhost:5000/"

if curl -f -s $API_URL > /dev/null; then
    echo "API is healthy"
    exit 0
else
    echo "API is down, restarting..."
    systemctl restart zero-shot-ner-api
    exit 1
fi
```

**Run with cron**:
```bash
*/5 * * * * /path/to/monitor.sh >> /var/log/zero-shot-ner-monitor.log 2>&1
```

### Backup Strategy

**What to backup**:
- Configuration: `config.ini`
- Custom code modifications
- Logs (if needed for audit)

**Not needed**:
- `models/` (can be re-downloaded)
- `venv/` (can be recreated)
- Python packages

```bash
# Backup script
tar -czf backup-$(date +%Y%m%d).tar.gz config.ini api/ interface/ *.py
```

---

**Document Version**: 1.0
**Last Updated**: December 2025
**Prototype Status**: Active Development
