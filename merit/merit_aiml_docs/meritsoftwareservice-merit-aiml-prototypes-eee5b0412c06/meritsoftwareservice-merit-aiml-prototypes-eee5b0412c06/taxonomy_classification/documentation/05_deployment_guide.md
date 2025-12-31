# Taxonomy Classification - Deployment Guide

## Table of Contents

1. [Deployment Overview](#deployment-overview)
2. [Development Environment Setup](#development-environment-setup)
3. [Production Considerations](#production-considerations)
4. [Deployment Options](#deployment-options)
5. [Cloud Deployment](#cloud-deployment)
6. [Containerization](#containerization)
7. [API Deployment](#api-deployment)
8. [Monitoring and Logging](#monitoring-and-logging)
9. [Security](#security)
10. [Performance Optimization](#performance-optimization)
11. [Maintenance and Updates](#maintenance-and-updates)

---

## Deployment Overview

### Deployment Types

This guide covers three main deployment scenarios:

1. **Development/Testing**: Local development environment
2. **Streamlit Cloud**: Quick web deployment for demos
3. **Production**: Scalable deployment with API access

### Architecture for Different Deployments

```
Development:
Local Machine → Streamlit → OpenAI API

Streamlit Cloud:
Users → Streamlit Cloud → OpenAI API

Production (API):
Users → Load Balancer → FastAPI Instances → OpenAI API
                     → Redis Cache
                     → Database (PostgreSQL)
```

---

## Development Environment Setup

### Prerequisites

- Python 3.8+
- pip or conda
- Git
- Text editor/IDE
- OpenAI API key

### Step-by-Step Setup

#### 1. Clone or Download the Project

```bash
cd /path/to/your/projects
# If using git:
git clone <repository-url>
cd taxonomy_classification

# Or simply navigate to the existing directory
cd /mnt/d/Data/Projects/KIAA/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/taxonomy_classification
```

#### 2. Create Virtual Environment

**Using venv:**
```bash
python -m venv venv

# Activate on Windows
venv\Scripts\activate

# Activate on macOS/Linux
source venv/bin/activate
```

**Using conda:**
```bash
conda create -n taxonomy python=3.10
conda activate taxonomy
```

#### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 4. Configure Environment

Create `.env` file:
```bash
echo "API_KEY=your-openai-api-key" > .env
```

**On Windows (PowerShell):**
```powershell
Set-Content -Path .env -Value "API_KEY=your-openai-api-key"
```

#### 5. Verify Installation

```bash
python -c "from taxonomy import ContentClassification; print('Setup successful!')"
```

#### 6. Run Development Server

```bash
streamlit run taxonomy.py
```

Access at: http://localhost:8501

---

## Production Considerations

### Before Deploying to Production

#### 1. Code Enhancements Required

**Error Handling:**
```python
# Add to ContentClassification.__init__
if not self.api_key:
    raise ValueError("API_KEY environment variable not set")

# Add to get_response method
def get_response(self, article, taxonomy):
    try:
        prompt = self.get_prompt()
        chain = prompt | self.llm_model | self.output_parser
        output = chain.invoke({"text": article, "taxonomy": taxonomy})
        return output
    except Exception as e:
        logging.error(f"Classification failed: {str(e)}")
        raise
```

**Input Validation:**
```python
def validate_input(text):
    if not text or not text.strip():
        raise ValueError("Text cannot be empty")
    if len(text) > 10000:
        raise ValueError("Text exceeds maximum length of 10000 characters")
    return text.strip()
```

**Logging:**
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('taxonomy_classification.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
```

#### 2. Configuration Management

Create `config.py`:
```python
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API Configuration
    OPENAI_API_KEY = os.getenv("API_KEY")
    MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0"))

    # Application Configuration
    TAXONOMY_FILE = os.getenv("TAXONOMY_FILE", "taxonomies.json")
    MAX_TEXT_LENGTH = int(os.getenv("MAX_TEXT_LENGTH", "10000"))
    TOP_N_RESULTS = int(os.getenv("TOP_N_RESULTS", "5"))

    # Cache Configuration
    ENABLE_CACHE = os.getenv("ENABLE_CACHE", "true").lower() == "true"
    CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))  # 1 hour

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "20"))

config = Config()
```

#### 3. Testing

Create `test_taxonomy.py`:
```python
import unittest
from taxonomy import ContentClassification
import json

class TestClassification(unittest.TestCase):
    def setUp(self):
        self.classifier = ContentClassification()
        with open("taxonomies.json", "r") as f:
            self.taxonomy = json.load(f)

    def test_classification(self):
        article = "Technology news about artificial intelligence"
        result = self.classifier.get_response(article, self.taxonomy)
        self.assertIn('results', result)
        self.assertTrue(len(result['results']) <= 5)

    def test_dataframe_conversion(self):
        response = {
            'results': [{
                'taxonomy_type': 'Test',
                'category': 'Cat',
                'sub_category': 'Sub',
                'scores': 8.0
            }]
        }
        df = self.classifier.to_dataframe(response)
        self.assertEqual(len(df), 1)

if __name__ == '__main__':
    unittest.main()
```

Run tests:
```bash
python -m pytest test_taxonomy.py
```

---

## Deployment Options

### Option 1: Streamlit Cloud (Easiest)

**Pros:**
- Free tier available
- Simple deployment
- Automatic HTTPS
- Good for demos and prototypes

**Cons:**
- Limited resources
- Public by default
- No API access
- Streamlit-only interface

#### Deployment Steps

1. **Prepare Repository**
   ```bash
   git init
   git add taxonomy.py requirements.txt taxonomies.json taxonomies_agri.json
   git commit -m "Initial commit"
   git remote add origin <your-github-repo>
   git push -u origin main
   ```

2. **Create .streamlit/secrets.toml**
   ```toml
   API_KEY = "your-openai-api-key-here"
   ```

3. **Update Code to Use Streamlit Secrets**
   ```python
   # In taxonomy.py
   import streamlit as st

   # Replace in __init__:
   self.api_key = st.secrets["API_KEY"]
   ```

4. **Deploy to Streamlit Cloud**
   - Visit https://share.streamlit.io/
   - Sign in with GitHub
   - Click "New app"
   - Select repository, branch, and main file (taxonomy.py)
   - Add secrets in advanced settings
   - Click "Deploy"

5. **Access Your App**
   - URL: https://share.streamlit.io/[username]/[repo-name]/[branch]/taxonomy.py

### Option 2: Heroku

**Pros:**
- Easy deployment
- Free tier available (limited hours)
- Custom domains
- Add-ons available

**Cons:**
- Sleeps after 30 min inactivity on free tier
- Limited resources on free tier

#### Deployment Steps

1. **Create Heroku Configuration**

Create `Procfile`:
```
web: sh setup.sh && streamlit run taxonomy.py --server.port=$PORT --server.address=0.0.0.0
```

Create `setup.sh`:
```bash
mkdir -p ~/.streamlit/

echo "\
[general]\n\
email = \"your-email@domain.com\"\n\
" > ~/.streamlit/credentials.toml

echo "\
[server]\n\
headless = true\n\
enableCORS=false\n\
port = $PORT\n\
" > ~/.streamlit/config.toml
```

2. **Deploy**
```bash
heroku login
heroku create taxonomy-classifier
git push heroku main
heroku config:set API_KEY=your-openai-api-key
heroku open
```

### Option 3: AWS EC2

**Pros:**
- Full control
- Scalable
- Professional deployment
- Can run API + Streamlit

**Cons:**
- Requires more setup
- Manual scaling
- Costs money

#### Deployment Steps

1. **Launch EC2 Instance**
   - Instance type: t2.medium or larger
   - OS: Ubuntu 22.04 LTS
   - Security group: Open ports 22 (SSH), 80 (HTTP), 443 (HTTPS), 8501 (Streamlit)

2. **Connect and Setup**
```bash
ssh -i your-key.pem ubuntu@your-ec2-ip

# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install python3-pip python3-venv nginx -y

# Create application directory
mkdir ~/taxonomy_classification
cd ~/taxonomy_classification
```

3. **Upload Application**
```bash
# On local machine
scp -i your-key.pem -r * ubuntu@your-ec2-ip:~/taxonomy_classification/
```

4. **Setup Application**
```bash
# On EC2 instance
cd ~/taxonomy_classification
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create .env file
echo "API_KEY=your-openai-api-key" > .env
```

5. **Create Systemd Service**

Create `/etc/systemd/system/taxonomy.service`:
```ini
[Unit]
Description=Taxonomy Classification Streamlit App
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/taxonomy_classification
Environment="PATH=/home/ubuntu/taxonomy_classification/venv/bin"
ExecStart=/home/ubuntu/taxonomy_classification/venv/bin/streamlit run taxonomy.py --server.port=8501 --server.address=0.0.0.0
Restart=always

[Install]
WantedBy=multi-user.target
```

6. **Start Service**
```bash
sudo systemctl daemon-reload
sudo systemctl enable taxonomy
sudo systemctl start taxonomy
sudo systemctl status taxonomy
```

7. **Configure Nginx Reverse Proxy**

Create `/etc/nginx/sites-available/taxonomy`:
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
sudo ln -s /etc/nginx/sites-available/taxonomy /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

8. **Setup SSL with Let's Encrypt**
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com
```

---

## Containerization

### Docker Deployment

#### Create Dockerfile

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY taxonomy.py .
COPY taxonomies.json .
COPY taxonomies_agri.json .

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Run application
ENTRYPOINT ["streamlit", "run", "taxonomy.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

#### Create .dockerignore

```
venv/
__pycache__/
*.pyc
.env
.git/
documentation/
*.md
```

#### Build and Run

```bash
# Build image
docker build -t taxonomy-classification .

# Run container
docker run -d \
  --name taxonomy \
  -p 8501:8501 \
  -e API_KEY=your-openai-api-key \
  taxonomy-classification

# View logs
docker logs -f taxonomy

# Stop container
docker stop taxonomy
```

#### Docker Compose

Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  taxonomy:
    build: .
    ports:
      - "8501:8501"
    environment:
      - API_KEY=${API_KEY}
    restart: unless-stopped
    volumes:
      - ./taxonomies.json:/app/taxonomies.json:ro
      - ./taxonomies_agri.json:/app/taxonomies_agri.json:ro
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

## API Deployment

### FastAPI Wrapper

Create `api.py`:
```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from taxonomy import ContentClassification
import json
import logging
from typing import List, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Taxonomy Classification API",
    description="AI-powered content classification API",
    version="1.0.0"
)

# Initialize classifier
classifier = ContentClassification()

# Load taxonomy
with open("taxonomies.json", "r") as f:
    taxonomy = json.load(f)

class ClassificationRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=10000)
    top_n: int = Field(5, ge=1, le=20)

class TaxonomyResult(BaseModel):
    taxonomy_type: str
    category: str
    sub_category: str
    score: float

class ClassificationResponse(BaseModel):
    results: List[TaxonomyResult]
    count: int

@app.get("/")
async def root():
    return {
        "service": "Taxonomy Classification API",
        "version": "1.0.0",
        "status": "operational"
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/classify", response_model=ClassificationResponse)
async def classify_text(request: ClassificationRequest):
    try:
        logger.info(f"Classification request received (length: {len(request.text)})")

        # Get classification
        response = classifier.get_response(request.text, taxonomy)

        # Limit results
        results = response['results'][:request.top_n]

        logger.info(f"Classification successful ({len(results)} results)")

        return ClassificationResponse(
            results=results,
            count=len(results)
        )

    except Exception as e:
        logger.error(f"Classification failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/taxonomies")
async def get_taxonomies():
    """Return available taxonomies"""
    return taxonomy

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### API Requirements

Update `requirements.txt`:
```
langchain==0.3.10
langchain-community==0.3.10
langchain-core==0.3.22
langchain-openai==0.2.12
streamlit==1.40.2
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0
```

### Run API Server

```bash
# Development
uvicorn api:app --reload

# Production
uvicorn api:app --host 0.0.0.0 --port 8000 --workers 4
```

### API Documentation

Access at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### API Usage Examples

**cURL:**
```bash
curl -X POST "http://localhost:8000/classify" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Article about artificial intelligence in healthcare",
    "top_n": 5
  }'
```

**Python:**
```python
import requests

response = requests.post(
    "http://localhost:8000/classify",
    json={
        "text": "Article about artificial intelligence in healthcare",
        "top_n": 5
    }
)

print(response.json())
```

**JavaScript:**
```javascript
fetch('http://localhost:8000/classify', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    text: 'Article about artificial intelligence in healthcare',
    top_n: 5
  })
})
.then(response => response.json())
.then(data => console.log(data));
```

---

## Monitoring and Logging

### Application Logging

Implement comprehensive logging:

```python
import logging
from logging.handlers import RotatingFileHandler

# Configure logging
def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # File handler with rotation
    file_handler = RotatingFileHandler(
        'taxonomy_classification.log',
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        '%(levelname)s - %(message)s'
    ))

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

logger = setup_logging()
```

### Metrics Collection

Create `metrics.py`:
```python
from datetime import datetime
import json
from pathlib import Path

class MetricsCollector:
    def __init__(self, metrics_file="metrics.jsonl"):
        self.metrics_file = Path(metrics_file)

    def log_classification(self, text_length, num_results, duration, success=True):
        metric = {
            "timestamp": datetime.utcnow().isoformat(),
            "text_length": text_length,
            "num_results": num_results,
            "duration_seconds": duration,
            "success": success
        }

        with open(self.metrics_file, 'a') as f:
            f.write(json.dumps(metric) + '\n')

    def get_stats(self):
        if not self.metrics_file.exists():
            return {}

        metrics = []
        with open(self.metrics_file, 'r') as f:
            for line in f:
                metrics.append(json.loads(line))

        if not metrics:
            return {}

        return {
            "total_requests": len(metrics),
            "successful": sum(1 for m in metrics if m['success']),
            "failed": sum(1 for m in metrics if not m['success']),
            "avg_duration": sum(m['duration_seconds'] for m in metrics) / len(metrics),
            "avg_text_length": sum(m['text_length'] for m in metrics) / len(metrics)
        }
```

### Health Monitoring

For production deployments, implement health checks:

```python
@app.get("/health")
async def health_check():
    checks = {
        "api": "healthy",
        "openai": "unknown",
        "taxonomy_loaded": taxonomy is not None
    }

    # Test OpenAI connection
    try:
        test_response = classifier.get_response(
            "Test article",
            {"Test": ["Value"]}
        )
        checks["openai"] = "healthy"
    except Exception as e:
        checks["openai"] = f"unhealthy: {str(e)}"

    all_healthy = all(
        v == "healthy" or v is True
        for v in checks.values()
    )

    status_code = 200 if all_healthy else 503

    return JSONResponse(
        status_code=status_code,
        content={"status": "healthy" if all_healthy else "unhealthy", "checks": checks}
    )
```

---

## Security

### Environment Variables

Never hardcode secrets. Use environment variables:

```python
# Good
api_key = os.getenv("API_KEY")

# Bad
api_key = "sk-proj-abc123..."
```

### Input Sanitization

```python
def sanitize_input(text):
    # Remove null bytes
    text = text.replace('\x00', '')

    # Limit length
    max_length = 10000
    if len(text) > max_length:
        text = text[:max_length]

    # Strip whitespace
    text = text.strip()

    return text
```

### Rate Limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/classify")
@limiter.limit("20/minute")
async def classify_text(request: Request, data: ClassificationRequest):
    # ... classification logic
    pass
```

### HTTPS/TLS

Always use HTTPS in production:

```bash
# Let's Encrypt with Certbot
sudo certbot --nginx -d yourdomain.com
```

### API Authentication

Implement API key authentication:

```python
from fastapi import Security, HTTPException
from fastapi.security.api_key import APIKeyHeader

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

async def get_api_key(api_key: str = Security(api_key_header)):
    if api_key != os.getenv("SERVICE_API_KEY"):
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return api_key

@app.post("/classify")
async def classify_text(
    request: ClassificationRequest,
    api_key: str = Depends(get_api_key)
):
    # ... classification logic
    pass
```

---

## Performance Optimization

### Caching

Implement Redis caching:

```python
import redis
import hashlib
import json

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def get_cache_key(text, taxonomy):
    content = f"{text}:{json.dumps(taxonomy, sort_keys=True)}"
    return hashlib.sha256(content.encode()).hexdigest()

def get_cached_result(text, taxonomy):
    key = get_cache_key(text, taxonomy)
    cached = redis_client.get(key)
    if cached:
        return json.loads(cached)
    return None

def cache_result(text, taxonomy, result, ttl=3600):
    key = get_cache_key(text, taxonomy)
    redis_client.setex(key, ttl, json.dumps(result))

# In get_response method:
def get_response(self, article, taxonomy):
    # Check cache first
    cached = get_cached_result(article, taxonomy)
    if cached:
        return cached

    # Get fresh result
    result = self._classify(article, taxonomy)

    # Cache result
    cache_result(article, taxonomy, result)

    return result
```

### Connection Pooling

```python
from langchain_openai import ChatOpenAI

# Use connection pooling
llm = ChatOpenAI(
    model_name="gpt-4o-mini",
    temperature=0,
    max_retries=3,
    request_timeout=30
)
```

### Async Processing

For batch operations:

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def classify_batch(articles, taxonomy):
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor(max_workers=5) as executor:
        tasks = [
            loop.run_in_executor(
                executor,
                classifier.get_taxonomy_data,
                article,
                taxonomy
            )
            for article in articles
        ]
        results = await asyncio.gather(*tasks)
    return results
```

---

## Maintenance and Updates

### Backup Strategy

```bash
# Backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/taxonomy_classification"

# Backup taxonomies
cp taxonomies.json "$BACKUP_DIR/taxonomies_$DATE.json"
cp taxonomies_agri.json "$BACKUP_DIR/taxonomies_agri_$DATE.json"

# Backup logs
cp taxonomy_classification.log "$BACKUP_DIR/logs_$DATE.log"

# Keep only last 30 days
find $BACKUP_DIR -name "*.json" -mtime +30 -delete
find $BACKUP_DIR -name "*.log" -mtime +30 -delete
```

### Update Procedure

1. **Test in development**
2. **Backup current state**
3. **Update dependencies**
   ```bash
   pip install -r requirements.txt --upgrade
   ```
4. **Run tests**
5. **Deploy to staging**
6. **Monitor for issues**
7. **Deploy to production**
8. **Monitor metrics**

### Rollback Plan

```bash
# Keep previous version
mv taxonomy.py taxonomy.py.backup
# Deploy new version
# If issues occur:
mv taxonomy.py.backup taxonomy.py
sudo systemctl restart taxonomy
```

---

## Cost Estimation

### OpenAI API Costs (GPT-4o-mini)

**Pricing** (as of 2025):
- Input: $0.15 per 1M tokens
- Output: $0.60 per 1M tokens

**Estimation:**
- Average article: 500 words ≈ 650 tokens
- Taxonomy: 300 tokens
- Output: 150 tokens
- Cost per classification: ~$0.001

**Monthly estimates:**
- 1,000 classifications: $1
- 10,000 classifications: $10
- 100,000 classifications: $100

### Infrastructure Costs

**Streamlit Cloud:**
- Free tier: 1 app
- Team: $250/month (multiple apps)

**AWS EC2:**
- t2.medium: ~$35/month
- t3.large: ~$70/month
- Plus data transfer costs

**Heroku:**
- Hobby: $7/month
- Standard 1X: $25/month
- Standard 2X: $50/month

---

This deployment guide provides comprehensive instructions for deploying the Taxonomy Classification system in various environments. Choose the deployment option that best fits your use case, scale, and budget requirements.
