# Merit ML Platform - Deployment Guide
## Installation, Configuration & Operations

---

## Table of Contents
1. [System Requirements](#system-requirements)
2. [Pre-Installation Checklist](#pre-installation-checklist)
3. [Installation Steps](#installation-steps)
4. [Configuration](#configuration)
5. [Redis Setup](#redis-setup)
6. [Worker Deployment](#worker-deployment)
7. [Monitoring & Health Checks](#monitoring--health-checks)
8. [Troubleshooting](#troubleshooting)
9. [Backup & Recovery](#backup--recovery)
10. [Security Hardening](#security-hardening)
11. [Performance Tuning](#performance-tuning)
12. [Upgrade Procedures](#upgrade-procedures)

---

## System Requirements

### Hardware Requirements

#### Minimum Configuration
- **CPU**: 8 cores (x86_64)
- **RAM**: 16 GB
- **GPU**: NVIDIA GPU with 8GB VRAM (CUDA 11.8+)
- **Storage**: 50 GB SSD
- **Network**: 1 Gbps Ethernet

#### Recommended Configuration (Production)
- **CPU**: 16+ cores (x86_64)
- **RAM**: 32 GB+
- **GPU**: NVIDIA A100/V100 or RTX 3090/4090 (16GB+ VRAM)
- **Storage**: 200 GB NVMe SSD
- **Network**: 10 Gbps Ethernet

### Software Requirements

#### Operating System
- **Linux**: Ubuntu 20.04/22.04 LTS (recommended)
- **Alternative**: CentOS 8, Red Hat Enterprise Linux 8+

#### Python Environment
- **Python**: 3.8, 3.9, 3.10, or 3.11
- **Package Manager**: pip, conda (Anaconda/Miniconda)

#### External Services
- **Redis**: 6.2+ (Redis Streams support required)
- **SFTP Server**: OpenSSH 7.4+ or compatible
- **Opik Server**: Latest version (for monitoring)

#### GPU Drivers
- **NVIDIA Driver**: 525+ (for CUDA 12.x)
- **CUDA Toolkit**: 11.8 or 12.x
- **cuDNN**: 8.6+

---

## Pre-Installation Checklist

### Network Access Verification

```bash
# Test Redis connectivity
nc -zv 172.27.140.191 6380

# Test SFTP connectivity
sftp -P 22 Merit_KIAA@125.16.95.60

# Test Opik connectivity
curl http://172.27.141.49:5173/api

# Test OpenAI API (if using)
curl https://api.openai.com/v1/models -H "Authorization: Bearer $OPENAI_API_KEY"
```

### Port Requirements

| Service | Port | Protocol | Direction |
|---------|------|----------|-----------|
| Flask API | 5001 | TCP | Inbound |
| Redis | 6380 | TCP | Outbound |
| SFTP | 22 | TCP | Outbound |
| Opik | 5173 | TCP | Outbound |
| OpenAI API | 443 | TCP | Outbound (HTTPS) |

### Firewall Configuration

```bash
# Allow Flask API port
sudo ufw allow 5001/tcp

# Allow outbound Redis connection
sudo ufw allow out 6380/tcp

# Allow outbound SFTP
sudo ufw allow out 22/tcp
```

---

## Installation Steps

### Step 1: Install System Dependencies

```bash
# Update package lists
sudo apt update && sudo apt upgrade -y

# Install build tools
sudo apt install -y build-essential git curl wget

# Install Python development headers
sudo apt install -y python3-dev python3-pip python3-venv

# Install CUDA toolkit (if not already installed)
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
sudo apt update
sudo apt install -y cuda-toolkit-12-0

# Verify GPU
nvidia-smi
```

### Step 2: Clone Repository

```bash
# Clone from Git repository
git clone <repository-url> merit-ml-platform
cd merit-ml-platform

# Or extract from archive
tar -xzf meritsoftwareservice-ml-cfd3ab12ec5f.tar.gz
cd meritsoftwareservice-ml-cfd3ab12ec5f
```

### Step 3: Create Python Virtual Environment

**Option A: Using venv**
```bash
# Create virtual environment
python3 -m venv venv

# Activate environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel
```

**Option B: Using Conda (Recommended)**
```bash
# Create conda environment
conda create -n kn_agent python=3.10 -y

# Activate environment
conda activate kn_agent

# Install CUDA support
conda install -c conda-forge cudatoolkit=11.8 -y
```

### Step 4: Install Python Dependencies

```bash
# Install core dependencies
pip install flask flask-httpauth pydantic python-dotenv

# Install Redis client
pip install redis

# Install LangChain ecosystem
pip install langchain langchain-core langchain-community langchain-huggingface langchain-chroma langgraph

# Install OpenAI client
pip install langchain-openai openai

# Install NER model dependencies
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install utca  # GLiNER wrapper

# Install document processing
pip install marker-pdf pymupdf

# Install embeddings and reranker
pip install sentence-transformers chromadb

# Install monitoring
pip install opik

# Install database
pip install sqlalchemy

# Install SFTP client
pip install paramiko

# Install utilities
pip install pandas pyyaml
```

**Or use requirements.txt** (if provided):
```bash
pip install -r requirements.txt
```

### Step 5: Download ML Models

```bash
# Create models directory
mkdir -p models

# Download GLiNER model (first run will auto-download)
python -c "
from utca.implementation.tasks import GLiNER
GLiNER.from_pretrained(
    'knowledgator/gliner-multitask-large-v0.5',
    cache_dir='models/gliner-multitask-large-v0.5'
)
"

# Download embedding models
python -c "
from sentence_transformers import SentenceTransformer
SentenceTransformer('BAAI/llm-embedder', cache_folder='/home/merit/.cache/huggingface/hub')
SentenceTransformer('BAAI/bge-reranker-large', cache_folder='/home/merit/.cache/huggingface/hub')
"
```

### Step 6: Configure Environment Variables

```bash
# Copy sample environment file
cp .env.sample .env

# Edit environment variables
nano .env
```

**Required Environment Variables** (`.env`):
```bash
# API Credentials
usr=api_username
pwd=secure_password_here

# LLM API Keys
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxx
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxx  # Optional

# Redis Credentials
REDIS_PASSWORD=redis_secure_password

# SFTP Credentials
SFTP_PASSWORD=sftp_password

# Deployment Mode
# "" for production, "_dev" for development, "_test" for testing
work_mode=
```

### Step 7: Configure Application

Edit `config.yaml`:

```yaml
# Model paths
model:
  gliner_path: /absolute/path/to/models/gliner-multitask-large-v0.5
  gliner_repo_id: knowledgator/gliner-multitask-large-v0.5

# API settings
api:
  port: 5001
  ip: 0.0.0.0  # Use 127.0.0.1 for localhost-only access

# LLM configuration
llm_details:
  llm_model: "gpt-4o-mini"
  model_provider: "openai"
  temperature: 0

# Redis connection
redis:
  host: "172.27.140.191"
  port: 6380

# Opik monitoring
opik:
  host: "http://172.27.141.49:5173/api"
  project_name: "KIAA"

# Worker configuration
workers:
  data_processor{{ work_mode }}:
    env_path: "/absolute/path/to/venv/bin/python"
    worker_file: "worker_manager.py"
    worker_name: "data_processor{{ work_mode }}"
    worker_count: 1
    is_active: True

  ner{{ work_mode }}:
    env_path: "/absolute/path/to/venv/bin/python"
    worker_file: "worker_manager.py"
    worker_name: "ner{{ work_mode }}"
    worker_count: 1
    is_active: True

  relation{{ work_mode }}:
    env_path: "/absolute/path/to/venv/bin/python"
    worker_file: "worker_manager.py"
    worker_name: "relation{{ work_mode }}"
    worker_count: 3
    is_active: True

  qa{{ work_mode }}:
    env_path: "/absolute/path/to/venv/bin/python"
    worker_file: "worker_manager.py"
    worker_name: "qa{{ work_mode }}"
    worker_count: 1
    is_active: True

  talend_pulse{{ work_mode }}:
    env_path: "/absolute/path/to/venv/bin/python"
    worker_file: "worker_manager.py"
    worker_name: "talend_pulse{{ work_mode }}"
    worker_count: 2
    is_active: True

# SFTP configuration
sftp_config:
  host: "125.16.95.60"
  username: "Merit_KIAA"
  ftp_folder: "/Merit_KIAA/"
  local_doc_path: "docs"

# RAG configuration
rag_config:
  embed_model: "BAAI/llm-embedder"
  ranker_model: "BAAI/bge-reranker-large"
  cache_dir: "/home/merit/.cache/huggingface/hub"
  persist_directory: "chroma_db"
  retriever_kwargs:
    search_kwargs:
      k: 50
      fetch_k: 15
      lambda_mult: 1
    search_type: "mmr"
  ranker_top_n: 3

# Database
db_params:
  sqlite_db_url: "sqlite:///cache.db"
```

**Important**: Update all paths to absolute paths for your environment.

### Step 8: Initialize Database

```bash
# Database will auto-initialize on first run
python -c "
from modules.db.cache_db_schema import Base
from sqlalchemy import create_engine
engine = create_engine('sqlite:///cache.db')
Base.metadata.create_all(engine)
print('Database initialized successfully')
"
```

### Step 9: Test Installation

```bash
# Test imports
python -c "
import flask
import redis
import langchain
from modules.ner.zero_shot_ner import ZeroShotNer
print('All imports successful')
"

# Test Redis connection
python -c "
import os
import redis
client = redis.StrictRedis(
    host='172.27.140.191',
    port=6380,
    password=os.environ['REDIS_PASSWORD']
)
print(f'Redis PING: {client.ping()}')
"
```

---

## Configuration

### Environment-Specific Configurations

#### Development Environment
```bash
# .env
work_mode=_dev

# Lower worker counts for dev
# In config.yaml:
workers:
  ner_dev:
    worker_count: 1
  relation_dev:
    worker_count: 1
```

#### Testing Environment
```bash
# .env
work_mode=_test

# Use separate streams for testing
# Streams will be: ner_stream_test, relation_stream_test, etc.
```

#### Production Environment
```bash
# .env
work_mode=

# Scale up worker counts
# In config.yaml:
workers:
  relation:
    worker_count: 5
  talend_pulse:
    worker_count: 4
```

### Worker Pool Sizing

**Guidelines**:
- **Data Processor**: 1 worker (I/O bound)
- **NER**: 1 worker per GPU (GPU bound)
- **Relation**: 3-5 workers (LLM API bound)
- **QA**: 1-2 workers (balanced)
- **Talend Pulse**: 2-4 workers (LLM API bound)

**Scaling Formula**:
```
optimal_workers = min(
    cpu_cores,
    gpu_memory_gb / 8,
    api_rate_limit / requests_per_second
)
```

---

## Redis Setup

### Install Redis Server

```bash
# Ubuntu/Debian
sudo apt install redis-server -y

# Configure Redis
sudo nano /etc/redis/redis.conf
```

### Redis Configuration

**Key Settings**:
```conf
# Network
bind 0.0.0.0
port 6380
protected-mode yes
requirepass your_redis_password

# Memory
maxmemory 4gb
maxmemory-policy allkeys-lru

# Persistence
save 900 1
save 300 10
save 60 10000

# Append-only file
appendonly yes
appendfsync everysec

# Streams
stream-node-max-bytes 4096
stream-node-max-entries 100
```

### Start Redis

```bash
# Enable and start Redis
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Check status
sudo systemctl status redis-server

# Test connection
redis-cli -h 172.27.140.191 -p 6380 -a your_redis_password ping
```

### Redis Streams Monitoring

```bash
# Monitor stream activity
redis-cli -h 172.27.140.191 -p 6380 -a your_redis_password

# Check stream info
XINFO STREAM ner_stream

# Check consumer groups
XINFO GROUPS ner_stream

# Check pending messages
XPENDING ner_stream kn_agent_group

# View stream length
XLEN ner_stream
```

---

## Worker Deployment

### Manual Worker Start

```bash
# Start Flask API
python app.py

# API will automatically start workers on first request
# Or manually trigger worker startup:
curl -u username:password http://localhost:5001/ner -X POST \
  -H "Content-Type: application/json" \
  -d '{"fileId": "test", "path": "test.pdf", "labels": ["test"]}'
```

### Systemd Service (Production)

Create service file:
```bash
sudo nano /etc/systemd/system/merit-ml-api.service
```

**Service Configuration**:
```ini
[Unit]
Description=Merit ML Platform API
After=network.target redis.service

[Service]
Type=simple
User=merit
Group=merit
WorkingDirectory=/home/merit/merit-ml-platform
Environment="PATH=/home/merit/anaconda3/envs/kn_agent/bin"
EnvironmentFile=/home/merit/merit-ml-platform/.env
ExecStart=/home/merit/anaconda3/envs/kn_agent/bin/python app.py
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Enable and Start**:
```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service
sudo systemctl enable merit-ml-api

# Start service
sudo systemctl start merit-ml-api

# Check status
sudo systemctl status merit-ml-api

# View logs
sudo journalctl -u merit-ml-api -f
```

### Docker Deployment

**Dockerfile**:
```dockerfile
FROM nvidia/cuda:12.0.0-runtime-ubuntu22.04

# Install Python
RUN apt update && apt install -y python3.10 python3-pip git

# Set working directory
WORKDIR /app

# Copy application files
COPY . /app

# Install dependencies
RUN pip install -r requirements.txt

# Download models
RUN python -c "from utca.implementation.tasks import GLiNER; GLiNER.from_pretrained('knowledgator/gliner-multitask-large-v0.5', cache_dir='/models')"

# Expose port
EXPOSE 5001

# Set environment
ENV PYTHONUNBUFFERED=1

# Start application
CMD ["python", "app.py"]
```

**Docker Compose** (`docker-compose.yml`):
```yaml
version: '3.8'

services:
  merit-ml-api:
    build: .
    ports:
      - "5001:5001"
    environment:
      - usr=${usr}
      - pwd=${pwd}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - REDIS_PASSWORD=${REDIS_PASSWORD}
      - SFTP_PASSWORD=${SFTP_PASSWORD}
      - work_mode=${work_mode}
    volumes:
      - ./cache.db:/app/cache.db
      - ./chroma_db:/app/chroma_db
      - ./docs:/app/docs
      - ./models:/models
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    restart: unless-stopped
    networks:
      - merit-network

networks:
  merit-network:
    driver: bridge
```

**Build and Run**:
```bash
# Build image
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

---

## Monitoring & Health Checks

### Application Health Check

```bash
# API health check
curl http://localhost:5001/

# Expected response: "welcome"
```

### Worker Status Check

```bash
# Check worker PIDs
cat scripts/.workers.pid

# Verify workers are running
ps aux | grep worker_manager.py

# Check worker logs (if using systemd)
sudo journalctl -u merit-ml-api -f | grep "Starting consumer"
```

### Redis Monitoring

```bash
# Connect to Redis CLI
redis-cli -h 172.27.140.191 -p 6380 -a your_redis_password

# Monitor real-time commands
MONITOR

# Check memory usage
INFO memory

# Check connected clients
CLIENT LIST

# Check stream statistics
XINFO STREAM ner_stream
XINFO STREAM relation_stream
XINFO STREAM qa_stream
```

### Database Monitoring

```bash
# Check database size
du -sh cache.db

# Count records
sqlite3 cache.db "SELECT COUNT(*) FROM doc_tbl;"
sqlite3 cache.db "SELECT COUNT(*) FROM ner_rel_tbl;"
sqlite3 cache.db "SELECT COUNT(*) FROM qa_tbl;"

# Check recent activity
sqlite3 cache.db "SELECT * FROM ner_rel_tbl ORDER BY updated_at DESC LIMIT 10;"
```

### Opik Dashboard

Access Opik monitoring:
```bash
# Open in browser
http://172.27.141.49:5173

# Navigate to project: KIAA
# View LLM traces, latencies, token usage
```

### Log Monitoring

```bash
# Tail application logs
tail -f /var/log/merit-ml-api.log

# Or with systemd
sudo journalctl -u merit-ml-api -f

# Filter by error level
sudo journalctl -u merit-ml-api -p err -f

# Search for specific request
sudo journalctl -u merit-ml-api | grep "request_id: abc-123"
```

### Performance Metrics

**Custom Monitoring Script** (`monitor.py`):
```python
import redis
import time

redis_client = redis.StrictRedis(
    host='172.27.140.191',
    port=6380,
    password='your_password',
    decode_responses=True
)

while True:
    stats = {
        'ner_stream': redis_client.xlen('ner_stream'),
        'relation_stream': redis_client.xlen('relation_stream'),
        'qa_stream': redis_client.xlen('qa_stream'),
        'status_stream': redis_client.xlen('status_stream_kn'),
        'ner_dlq': redis_client.xlen('ner_dead_letter_stream'),
        'relation_dlq': redis_client.xlen('relation_dead_letter_stream'),
    }

    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Stream Lengths: {stats}")
    time.sleep(60)
```

---

## Troubleshooting

### Common Issues

#### 1. Workers Not Starting

**Symptoms**: API responds but no processing occurs

**Diagnosis**:
```bash
# Check PID file
cat scripts/.workers.pid

# Check if workers are running
ps aux | grep worker_manager

# Check worker shell script
cat scripts/worker.sh
```

**Solution**:
```bash
# Kill existing workers
bash scripts/killer.sh

# Manually start workers
bash scripts/worker.sh

# Check logs for errors
sudo journalctl -u merit-ml-api -f
```

#### 2. Redis Connection Errors

**Symptoms**: `ConnectionError: Failed to connect to Redis`

**Diagnosis**:
```bash
# Test Redis connectivity
redis-cli -h 172.27.140.191 -p 6380 -a your_password ping

# Check firewall
sudo ufw status

# Check Redis service
sudo systemctl status redis-server
```

**Solution**:
```bash
# Ensure Redis is running
sudo systemctl start redis-server

# Check Redis password in .env
echo $REDIS_PASSWORD

# Verify config.yaml Redis settings
```

#### 3. GPU Not Detected

**Symptoms**: GLiNER falls back to CPU, slow processing

**Diagnosis**:
```bash
# Check NVIDIA driver
nvidia-smi

# Check CUDA
nvcc --version

# Check PyTorch CUDA
python -c "import torch; print(torch.cuda.is_available())"
```

**Solution**:
```bash
# Reinstall NVIDIA driver
sudo apt install nvidia-driver-525

# Reinstall PyTorch with CUDA
pip uninstall torch
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Reboot system
sudo reboot
```

#### 4. Model Download Failures

**Symptoms**: `FileNotFoundError` for GLiNER model

**Diagnosis**:
```bash
# Check model path in config.yaml
cat config.yaml | grep gliner_path

# Check if model exists
ls -la /path/to/models/gliner-multitask-large-v0.5
```

**Solution**:
```bash
# Download model manually
python -c "
from utca.implementation.tasks import GLiNER
GLiNER.from_pretrained(
    'knowledgator/gliner-multitask-large-v0.5',
    cache_dir='/absolute/path/to/models/gliner-multitask-large-v0.5'
)
"

# Update config.yaml with correct path
```

#### 5. SFTP Connection Failures

**Symptoms**: `AuthenticationException` or `SSHException`

**Diagnosis**:
```bash
# Test SFTP manually
sftp -P 22 Merit_KIAA@125.16.95.60

# Check SFTP password
echo $SFTP_PASSWORD
```

**Solution**:
```bash
# Update SFTP password in .env
SFTP_PASSWORD=correct_password

# Verify SFTP config in config.yaml
# Restart application
```

#### 6. Dead Letter Queue Buildup

**Symptoms**: Tasks in DLQ, status showing "Failed"

**Diagnosis**:
```bash
# Check DLQ length
redis-cli -h 172.27.140.191 -p 6380 -a password XLEN ner_dead_letter_stream

# Read DLQ messages
redis-cli -h 172.27.140.191 -p 6380 -a password XREAD COUNT 10 STREAMS ner_dead_letter_stream 0
```

**Solution**:
```bash
# Identify failure reason from DLQ messages
# Fix underlying issue (model, API key, file access)
# Manually reprocess failed tasks or clear DLQ
redis-cli -h 172.27.140.191 -p 6380 -a password DEL ner_dead_letter_stream
```

#### 7. ChromaDB Collection Errors

**Symptoms**: `Collection not found` errors in QA

**Diagnosis**:
```bash
# Check ChromaDB directory
ls -la chroma_db/

# Python check
python -c "
from langchain_chroma import Chroma
db = Chroma(persist_directory='chroma_db')
print(db._client.list_collections())
"
```

**Solution**:
```bash
# Re-index documents with /qa_indexer
# Ensure session_id is correct
# Check ChromaDB permissions
chmod -R 755 chroma_db/
```

---

## Backup & Recovery

### Database Backup

```bash
# Backup SQLite database
cp cache.db cache.db.backup.$(date +%Y%m%d_%H%M%S)

# Automated daily backup (crontab)
0 2 * * * cp /path/to/cache.db /path/to/backups/cache.db.$(date +\%Y\%m\%d)
```

### ChromaDB Backup

```bash
# Backup ChromaDB directory
tar -czf chroma_db_backup_$(date +%Y%m%d).tar.gz chroma_db/

# Restore ChromaDB
tar -xzf chroma_db_backup_20241220.tar.gz
```

### Redis Backup

```bash
# Trigger Redis save
redis-cli -h 172.27.140.191 -p 6380 -a password BGSAVE

# Copy RDB file
cp /var/lib/redis/dump.rdb /backups/redis_backup_$(date +%Y%m%d).rdb

# Restore Redis (stop Redis first)
sudo systemctl stop redis-server
sudo cp /backups/redis_backup_20241220.rdb /var/lib/redis/dump.rdb
sudo systemctl start redis-server
```

### Configuration Backup

```bash
# Backup all configs
tar -czf config_backup_$(date +%Y%m%d).tar.gz .env config.yaml modules/rel/prompt.yaml
```

---

## Security Hardening

### API Security

```bash
# Use strong passwords
usr=admin_$(openssl rand -hex 8)
pwd=$(openssl rand -base64 32)

# Consider adding HTTPS with reverse proxy (nginx)
sudo apt install nginx
```

**Nginx HTTPS Configuration**:
```nginx
server {
    listen 443 ssl;
    server_name api.merit-ml.com;

    ssl_certificate /etc/ssl/certs/merit-ml.crt;
    ssl_certificate_key /etc/ssl/private/merit-ml.key;

    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Redis Security

```bash
# Strong Redis password
REDIS_PASSWORD=$(openssl rand -base64 32)

# Bind to localhost only (if Redis on same machine)
# In /etc/redis/redis.conf:
bind 127.0.0.1

# Disable dangerous commands
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command CONFIG ""
```

### File Permissions

```bash
# Restrict .env file
chmod 600 .env

# Restrict database
chmod 600 cache.db

# Restrict PID file
chmod 600 scripts/.workers.pid

# Set proper ownership
sudo chown -R merit:merit /path/to/merit-ml-platform
```

### Environment Isolation

```bash
# Use separate environments per deployment
# Development: work_mode=_dev
# Testing: work_mode=_test
# Production: work_mode=

# Use separate Redis databases
# In config.yaml for each environment:
redis:
  host: "172.27.140.191"
  port: 6380
  db: 0  # Production
  # db: 1  # Development
  # db: 2  # Testing
```

---

## Performance Tuning

### GPU Optimization

```bash
# Set GPU memory growth (TensorFlow)
export TF_FORCE_GPU_ALLOW_GROWTH=true

# Set CUDA device
export CUDA_VISIBLE_DEVICES=0

# Enable mixed precision
# In GLiNER config (if supported)
```

### Worker Tuning

```yaml
# High throughput: Increase worker counts
relation{{ work_mode }}:
  worker_count: 5

# Adjust process_count (batch size per worker)
workers_config:
  ner{{ work_mode }}:
    process_count: 10  # Process 10 messages at once
```

### Redis Tuning

```conf
# Increase max clients
maxclients 10000

# Optimize memory
maxmemory-policy allkeys-lru
maxmemory 8gb

# Disable persistence for performance (not recommended)
save ""
appendonly no
```

### Database Optimization

```sql
-- Create indexes
CREATE INDEX IF NOT EXISTS idx_doc_fileId ON doc_tbl(fileId);
CREATE INDEX IF NOT EXISTS idx_ner_fileId ON ner_rel_tbl(fileId);
CREATE INDEX IF NOT EXISTS idx_qa_session ON qa_tbl(session_id);

-- Vacuum database periodically
VACUUM;
```

---

## Upgrade Procedures

### Minor Version Update

```bash
# Backup current installation
tar -czf merit-ml-backup-$(date +%Y%m%d).tar.gz .

# Pull latest code
git pull origin main

# Update dependencies
pip install -r requirements.txt --upgrade

# Restart service
sudo systemctl restart merit-ml-api
```

### Major Version Update

```bash
# 1. Backup everything
bash backup_all.sh

# 2. Stop services
sudo systemctl stop merit-ml-api
bash scripts/killer.sh

# 3. Update code
git checkout v2.0.0

# 4. Update dependencies
pip install -r requirements.txt --upgrade

# 5. Run migrations (if any)
python migrate.py

# 6. Test in staging
work_mode=_test python app.py

# 7. Deploy to production
sudo systemctl start merit-ml-api
```

---

## Quick Reference Commands

```bash
# Start API
python app.py

# Start API with systemd
sudo systemctl start merit-ml-api

# Stop workers
bash scripts/killer.sh

# Check worker status
ps aux | grep worker_manager

# Monitor logs
sudo journalctl -u merit-ml-api -f

# Check Redis streams
redis-cli -h 172.27.140.191 -p 6380 -a password XLEN ner_stream

# Test API
curl -u username:password http://localhost:5001/

# Backup database
cp cache.db cache.db.backup

# Clear cache
rm cache.db && python -c "from modules.db.cache_db_schema import Base; from sqlalchemy import create_engine; engine = create_engine('sqlite:///cache.db'); Base.metadata.create_all(engine)"
```

---

**Document Version**: 1.0.0
**Last Updated**: December 2024
**Platform**: Merit ML Platform - Knowledge Agent
