# BidRadar - Deployment & Operations Guide

**Version:** 1.0
**Last Updated:** December 2025
**Audience:** DevOps Engineers, System Administrators, Technical Leads

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Database Initialization](#database-initialization)
6. [Running the Application](#running-the-application)
7. [Production Deployment](#production-deployment)
8. [Monitoring & Maintenance](#monitoring-maintenance)
9. [Backup & Recovery](#backup-recovery)
10. [Troubleshooting](#troubleshooting)
11. [Security Hardening](#security-hardening)
12. [Scaling Strategies](#scaling-strategies)

---

## Prerequisites

### System Requirements

**Minimum Requirements**:
- **OS**: Linux (Ubuntu 20.04+), macOS (10.15+), Windows 10+ with WSL2
- **Python**: 3.11 or higher
- **Memory**: 2 GB RAM (4 GB recommended)
- **Storage**: 1 GB free space (database growth: ~100MB per 10,000 tenders)
- **CPU**: 2 cores (4 cores recommended)

**Network Requirements**:
- Outbound internet access for:
  - Web scraping (LUPC portal)
  - OpenAI API calls
  - Package downloads (PyPI)
- Inbound access to port 8501 (Streamlit default) or configured port

### Software Dependencies

**Required**:
- Python 3.11+
- pip (Python package manager)
- Virtual environment (venv or conda)

**Recommended**:
- Git for version control
- systemd for service management (Linux)
- nginx or Apache for reverse proxy (production)
- PostgreSQL for production database (alternative to SQLite)

### External Services

**Required**:
- **OpenAI API Account**: Sign up at https://platform.openai.com/
  - API key with access to GPT-4o model
  - Sufficient credits/quota
  - Estimated cost: $10-50/month depending on usage

**Optional**:
- Email SMTP server for alert notifications
- Log aggregation service (e.g., Datadog, ELK stack)
- Monitoring service (e.g., Prometheus, Grafana)

---

## Environment Setup

### Creating a Virtual Environment

**Using venv** (recommended):
```bash
# Navigate to project directory
cd /path/to/tender_intelligence

# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

**Using conda**:
```bash
# Create conda environment
conda create -n bidradar python=3.11

# Activate environment
conda activate bidradar
```

### Installing Dependencies

**Using pip** (with pyproject.toml):
```bash
# Ensure you're in the virtual environment
pip install --upgrade pip

# Install dependencies
pip install -e .

# Or install from requirements.txt if generated:
pip install -r requirements.txt
```

**Manual installation**:
```bash
pip install streamlit>=1.45.1
pip install openai>=1.82.0
pip install pandas>=2.2.3
pip install plotly>=6.1.1
pip install scikit-learn>=1.6.1
pip install spacy>=3.8.7
pip install beautifulsoup4>=4.13.4
pip install trafilatura>=2.0.0
pip install requests>=2.32.3
```

### Installing spaCy Language Model

**Required for entity extraction**:
```bash
# Download English language model
python -m spacy download en_core_web_sm

# Verify installation
python -c "import spacy; nlp = spacy.load('en_core_web_sm'); print('spaCy model loaded successfully')"
```

**Troubleshooting spaCy installation**:
```bash
# If download fails, try direct installation
pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.0/en_core_web_sm-3.7.0-py3-none-any.whl

# Or disable SSL verification (not recommended for production)
python -m spacy download en_core_web_sm --no-ssl-verify
```

---

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Required: OpenAI API Configuration
OPENAI_API_KEY=sk-your-api-key-here

# Optional: Database Configuration
DATABASE_PATH=tender_platform.db

# Optional: Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=tender_platform.log

# Optional: Scraping Configuration
SCRAPING_DELAY=1  # Seconds between requests
SCRAPING_TIMEOUT=10  # Request timeout in seconds
USER_AGENT=Mozilla/5.0 (compatible; BidRadar/1.0)

# Optional: Application Configuration
APP_PORT=8501
APP_HOST=0.0.0.0
DEBUG_MODE=False

# Optional: Email Configuration (for alerts)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@example.com
SMTP_PASSWORD=your-email-password
SMTP_FROM=noreply@bidradar.com

# Optional: Cache Configuration
RECOMMENDATION_CACHE_TIMEOUT=3600  # 1 hour in seconds
```

**Setting environment variables** (alternative to .env):
```bash
# Linux/macOS:
export OPENAI_API_KEY="sk-your-api-key-here"

# Windows (Command Prompt):
set OPENAI_API_KEY=sk-your-api-key-here

# Windows (PowerShell):
$env:OPENAI_API_KEY="sk-your-api-key-here"
```

### Streamlit Configuration

Create `.streamlit/config.toml`:

```toml
[server]
port = 8501
address = "0.0.0.0"
headless = true
enableCORS = false
enableXsrfProtection = true

[browser]
gatherUsageStats = false
serverAddress = "localhost"
serverPort = 8501

[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"

[logger]
level = "info"
messageFormat = "%(asctime)s %(levelname)s: %(message)s"

[client]
showErrorDetails = false
toolbarMode = "minimal"

[runner]
magicEnabled = true
fastReruns = true
```

### Application Configuration

Edit `config.py` (create if doesn't exist):

```python
import os

# Database Configuration
DATABASE_PATH = os.getenv('DATABASE_PATH', 'tender_platform.db')

# API Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_MODEL = 'gpt-4o'

# Scraping Configuration
SCRAPING_DELAY = int(os.getenv('SCRAPING_DELAY', 1))
SCRAPING_TIMEOUT = int(os.getenv('SCRAPING_TIMEOUT', 10))
USER_AGENT = os.getenv('USER_AGENT', 'Mozilla/5.0')

# Cache Configuration
RECOMMENDATION_CACHE_TIMEOUT = int(os.getenv('RECOMMENDATION_CACHE_TIMEOUT', 3600))

# Logging Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', 'tender_platform.log')

# Feature Flags
ENABLE_WEB_SCRAPING = os.getenv('ENABLE_WEB_SCRAPING', 'true').lower() == 'true'
ENABLE_AI_ASSISTANT = os.getenv('ENABLE_AI_ASSISTANT', 'true').lower() == 'true'
ENABLE_EMAIL_ALERTS = os.getenv('ENABLE_EMAIL_ALERTS', 'false').lower() == 'true'
```

---

## Database Initialization

### Automatic Initialization

The database is automatically initialized when the application first runs:

```python
# In Database class __init__
def __init__(self, db_path: str = "tender_platform.db"):
    self.db_path = db_path
    self.init_database()  # Creates tables and indices
```

### Manual Initialization

To manually initialize or reset the database:

```bash
# Python script
python -c "from utils.database import Database; db = Database(); print('Database initialized')"
```

### Loading Demo Data

To populate the database with sample data:

```bash
# Run demo data script
python create_demo_data.py

# Expected output:
# Successfully populated database with 15 tenders and 3 vendors
```

**Demo data includes**:
- 15 realistic LUPC-style tenders
- 3 vendor profiles
- Sample interactions and interests
- Various categories, values, and deadlines

### Database Schema Verification

Verify table creation:

```bash
# Using SQLite command-line tool
sqlite3 tender_platform.db ".schema"

# Or using Python
python -c "
import sqlite3
conn = sqlite3.connect('tender_platform.db')
cursor = conn.cursor()
cursor.execute(\"SELECT name FROM sqlite_master WHERE type='table'\")
print('Tables:', [row[0] for row in cursor.fetchall()])
conn.close()
"
```

Expected tables:
- tenders
- vendors
- vendor_interests
- recommendation_feedback

---

## Running the Application

### Development Mode

**Basic startup**:
```bash
# Ensure virtual environment is activated
streamlit run app.py

# Application will start on http://localhost:8501
```

**With custom configuration**:
```bash
# Custom port
streamlit run app.py --server.port 8080

# Custom host (allow external access)
streamlit run app.py --server.address 0.0.0.0

# With browser auto-open disabled
streamlit run app.py --server.headless true
```

**With logging**:
```bash
# Redirect logs to file
streamlit run app.py 2>&1 | tee app.log

# With verbose logging
LOG_LEVEL=DEBUG streamlit run app.py
```

### Production Mode

**Using systemd** (Linux):

Create `/etc/systemd/system/bidradar.service`:

```ini
[Unit]
Description=BidRadar Tender Intelligence Platform
After=network.target

[Service]
Type=simple
User=bidradar
WorkingDirectory=/opt/bidradar
Environment="PATH=/opt/bidradar/venv/bin"
EnvironmentFile=/opt/bidradar/.env
ExecStart=/opt/bidradar/venv/bin/streamlit run app.py --server.port 8501 --server.address 0.0.0.0
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and start service**:
```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable bidradar

# Start service
sudo systemctl start bidradar

# Check status
sudo systemctl status bidradar

# View logs
sudo journalctl -u bidradar -f
```

**Using supervisor** (alternative):

Create `/etc/supervisor/conf.d/bidradar.conf`:

```ini
[program:bidradar]
directory=/opt/bidradar
command=/opt/bidradar/venv/bin/streamlit run app.py --server.port 8501 --server.address 0.0.0.0
user=bidradar
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/bidradar/app.log
environment=OPENAI_API_KEY="your-key-here"
```

**Using Docker** (recommended for production):

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY pyproject.toml .

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Download spaCy model
RUN python -m spacy download en_core_web_sm

# Copy application code
COPY . .

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run application
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

**Build and run Docker container**:
```bash
# Build image
docker build -t bidradar:latest .

# Run container
docker run -d \
    --name bidradar \
    -p 8501:8501 \
    -e OPENAI_API_KEY="your-key-here" \
    -v $(pwd)/tender_platform.db:/app/tender_platform.db \
    bidradar:latest

# View logs
docker logs -f bidradar

# Stop container
docker stop bidradar
```

**Docker Compose** (full stack):

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  bidradar:
    build: .
    ports:
      - "8501:8501"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - DATABASE_PATH=/data/tender_platform.db
    volumes:
      - ./data:/data
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Optional: PostgreSQL for production database
  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=bidradar
      - POSTGRES_USER=bidradar
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  # Optional: Nginx reverse proxy
  nginx:
    image: nginx:latest
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - bidradar
    restart: unless-stopped

volumes:
  postgres_data:
```

**Start with Docker Compose**:
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

---

## Production Deployment

### Reverse Proxy Configuration

**Nginx configuration** (`/etc/nginx/sites-available/bidradar`):

```nginx
upstream bidradar {
    server 127.0.0.1:8501;
}

server {
    listen 80;
    server_name bidradar.example.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name bidradar.example.com;

    # SSL Configuration
    ssl_certificate /etc/nginx/ssl/bidradar.crt;
    ssl_certificate_key /etc/nginx/ssl/bidradar.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Logging
    access_log /var/log/nginx/bidradar_access.log;
    error_log /var/log/nginx/bidradar_error.log;

    location / {
        proxy_pass http://bidradar;
        proxy_http_version 1.1;

        # WebSocket support (required for Streamlit)
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Proxy headers
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 7d;
        proxy_send_timeout 7d;
        proxy_read_timeout 7d;
    }

    # Health check endpoint
    location /_stcore/health {
        proxy_pass http://bidradar/_stcore/health;
        access_log off;
    }
}
```

**Enable site**:
```bash
# Create symbolic link
sudo ln -s /etc/nginx/sites-available/bidradar /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

### SSL Certificate Setup

**Using Let's Encrypt (Certbot)**:
```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d bidradar.example.com

# Auto-renewal is configured automatically
# Test renewal:
sudo certbot renew --dry-run
```

### Database Migration to PostgreSQL

**Install PostgreSQL**:
```bash
sudo apt-get install postgresql postgresql-contrib
```

**Create database and user**:
```sql
-- As postgres user
CREATE DATABASE bidradar;
CREATE USER bidradar WITH PASSWORD 'your-secure-password';
GRANT ALL PRIVILEGES ON DATABASE bidradar TO bidradar;
```

**Migrate SQLite to PostgreSQL** (using pgloader):
```bash
# Install pgloader
sudo apt-get install pgloader

# Create migration script
cat > migrate.load <<EOF
LOAD DATABASE
     FROM sqlite://tender_platform.db
     INTO postgresql://bidradar:password@localhost/bidradar

WITH include no drop, create tables, create indexes, reset sequences

SET work_mem to '16MB', maintenance_work_mem to '512 MB';
EOF

# Run migration
pgloader migrate.load
```

**Update application configuration**:
```python
# Install psycopg2
pip install psycopg2-binary

# Update database.py to use PostgreSQL connection
import psycopg2

class Database:
    def __init__(self):
        self.connection_string = os.getenv(
            'DATABASE_URL',
            'postgresql://bidradar:password@localhost/bidradar'
        )
```

---

## Monitoring & Maintenance

### Application Monitoring

**Health Check Endpoint**:
```bash
# Check application health
curl http://localhost:8501/_stcore/health

# Expected response: {"status": "ok"}
```

**System Resource Monitoring**:
```bash
# Monitor CPU and memory usage
top -p $(pgrep -f streamlit)

# Or using htop (more detailed)
htop -p $(pgrep -f streamlit)
```

**Application Logs**:
```bash
# Tail application logs
tail -f tender_platform.log

# Search for errors
grep ERROR tender_platform.log | tail -20

# Count error types
grep ERROR tender_platform.log | awk '{print $4}' | sort | uniq -c
```

### Database Monitoring

**Database size**:
```bash
# SQLite
ls -lh tender_platform.db

# PostgreSQL
psql -U bidradar -d bidradar -c "SELECT pg_size_pretty(pg_database_size('bidradar'));"
```

**Table statistics**:
```sql
-- Record counts
SELECT 'tenders' as table_name, COUNT(*) as count FROM tenders
UNION ALL
SELECT 'vendors', COUNT(*) FROM vendors
UNION ALL
SELECT 'vendor_interests', COUNT(*) FROM vendor_interests;

-- Category distribution
SELECT category, COUNT(*) as count
FROM tenders
GROUP BY category
ORDER BY count DESC;

-- Recent activity
SELECT DATE(created_at) as date, COUNT(*) as new_tenders
FROM tenders
WHERE created_at > datetime('now', '-30 days')
GROUP BY DATE(created_at)
ORDER BY date;
```

### Scheduled Maintenance Tasks

**Daily tasks** (cron):
```bash
# Edit crontab
crontab -e

# Add daily tender scraping at 6 AM
0 6 * * * cd /opt/bidradar && /opt/bidradar/venv/bin/python -c "from utils.web_scraper import TenderScraper; from utils.database import Database; scraper = TenderScraper(); db = Database(); tenders = scraper.scrape_lupc_tenders(); db.store_tenders(tenders)"

# Add daily database cleanup at 2 AM (remove old data)
0 2 * * * cd /opt/bidradar && /opt/bidradar/venv/bin/python -c "from utils.database import Database; db = Database(); db.cleanup_old_data(days_old=365)"

# Add daily backup at 3 AM
0 3 * * * cp /opt/bidradar/tender_platform.db /opt/bidradar/backups/tender_platform_$(date +\%Y\%m\%d).db
```

**Weekly tasks**:
```bash
# Add weekly log rotation
0 0 * * 0 cd /opt/bidradar && mv tender_platform.log tender_platform.log.$(date +\%Y\%m\%d) && touch tender_platform.log

# Add weekly backup cleanup (keep 4 weeks)
0 4 * * 0 find /opt/bidradar/backups -name "*.db" -mtime +28 -delete
```

### Performance Monitoring

**Prometheus metrics** (optional, requires instrumentation):

Add to `app.py`:
```python
from prometheus_client import Counter, Histogram, start_http_server

# Define metrics
search_counter = Counter('bidradar_searches_total', 'Total searches')
recommendation_histogram = Histogram('bidradar_recommendation_duration_seconds',
                                    'Recommendation generation time')
```

**Grafana dashboards**:
- Application uptime
- Request rate and latency
- Database query performance
- Cache hit rates
- Error rates

---

## Backup & Recovery

### Backup Strategy

**Daily automated backups**:
```bash
#!/bin/bash
# /opt/bidradar/scripts/backup.sh

BACKUP_DIR="/opt/bidradar/backups"
DB_FILE="/opt/bidradar/tender_platform.db"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/tender_platform_${DATE}.db"

# Create backup directory if it doesn't exist
mkdir -p ${BACKUP_DIR}

# Copy database file
cp ${DB_FILE} ${BACKUP_FILE}

# Compress backup
gzip ${BACKUP_FILE}

# Remove backups older than 30 days
find ${BACKUP_DIR} -name "*.db.gz" -mtime +30 -delete

echo "Backup completed: ${BACKUP_FILE}.gz"
```

**Make script executable and schedule**:
```bash
chmod +x /opt/bidradar/scripts/backup.sh

# Add to crontab (daily at 3 AM)
crontab -e
# Add: 0 3 * * * /opt/bidradar/scripts/backup.sh >> /var/log/bidradar-backup.log 2>&1
```

**Offsite backup**:
```bash
# Using rsync to remote server
rsync -avz /opt/bidradar/backups/ user@backup-server:/backups/bidradar/

# Using AWS S3
aws s3 sync /opt/bidradar/backups/ s3://my-bucket/bidradar-backups/

# Using Google Cloud Storage
gsutil rsync -r /opt/bidradar/backups/ gs://my-bucket/bidradar-backups/
```

### Recovery Procedures

**Restore from backup**:
```bash
#!/bin/bash
# /opt/bidradar/scripts/restore.sh

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    exit 1
fi

# Stop application
sudo systemctl stop bidradar

# Backup current database (just in case)
cp /opt/bidradar/tender_platform.db /opt/bidradar/tender_platform.db.before_restore

# Restore from backup
if [[ $BACKUP_FILE == *.gz ]]; then
    gunzip -c $BACKUP_FILE > /opt/bidradar/tender_platform.db
else
    cp $BACKUP_FILE /opt/bidradar/tender_platform.db
fi

# Fix permissions
chown bidradar:bidradar /opt/bidradar/tender_platform.db

# Start application
sudo systemctl start bidradar

echo "Database restored from $BACKUP_FILE"
```

**Disaster recovery checklist**:
1. Stop application
2. Identify latest good backup
3. Run restore script
4. Verify database integrity
5. Test application functionality
6. Resume normal operations
7. Document incident

---

## Troubleshooting

### Common Issues

#### Application won't start

**Symptom**: `streamlit run app.py` fails

**Diagnosis**:
```bash
# Check Python version
python --version  # Must be 3.11+

# Check if port is already in use
netstat -tuln | grep 8501

# Check virtual environment
which python  # Should point to venv

# Check dependencies
pip list | grep streamlit
```

**Solutions**:
```bash
# Reinstall dependencies
pip install --force-reinstall streamlit

# Use different port
streamlit run app.py --server.port 8502

# Check for errors in detail
streamlit run app.py --logger.level=debug
```

#### Database errors

**Symptom**: "Database locked" or "OperationalError"

**Diagnosis**:
```bash
# Check file permissions
ls -l tender_platform.db

# Check for locked processes
lsof tender_platform.db

# Check database integrity
sqlite3 tender_platform.db "PRAGMA integrity_check;"
```

**Solutions**:
```bash
# Fix permissions
chmod 664 tender_platform.db

# Kill processes holding lock
# (Identify PID from lsof, then)
kill <PID>

# Repair database
sqlite3 tender_platform.db ".recover" | sqlite3 tender_platform_recovered.db
```

#### AI Assistant not responding

**Symptom**: "API error" or timeouts

**Diagnosis**:
```bash
# Check API key
echo $OPENAI_API_KEY

# Test API connectivity
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     https://api.openai.com/v1/models

# Check rate limits and quota
# (View in OpenAI dashboard)
```

**Solutions**:
```bash
# Verify API key is correct
# Check OpenAI dashboard for:
# - API key validity
# - Account balance
# - Rate limit status

# Reduce temperature or max_tokens if hitting limits
# Update ai_assistant.py
```

#### Web scraping failures

**Symptom**: "No tenders scraped" or connection errors

**Diagnosis**:
```bash
# Test connectivity to LUPC
curl -I https://www.lupc.ac.uk

# Check for IP blocking
curl -A "BidRadar/1.0" https://www.lupc.ac.uk

# Verify trafilatura works
python -c "import trafilatura; print(trafilatura.fetch_url('https://www.lupc.ac.uk'))"
```

**Solutions**:
```bash
# Increase timeout in web_scraper.py
# Change: timeout=10 to timeout=30

# Add more delay between requests
# Change: time.sleep(1) to time.sleep(2)

# Update User-Agent if being blocked
# Edit USER_AGENT in .env file
```

### Performance Issues

#### Slow recommendations

**Diagnosis**:
```python
# Add timing to ml_engine.py
import time
start = time.time()
recommendations = self._generate_recommendations(...)
print(f"Recommendation time: {time.time() - start:.2f}s")
```

**Solutions**:
- Reduce tender count with filters
- Implement pagination
- Increase cache timeout
- Use background processing for large datasets

#### High memory usage

**Diagnosis**:
```bash
# Monitor memory
ps aux | grep streamlit

# Profile memory (install memory_profiler)
pip install memory_profiler
mprof run app.py
mprof plot
```

**Solutions**:
- Limit data loading (use LIMIT in SQL queries)
- Clear cache periodically
- Use generators instead of lists
- Optimize pandas operations (use chunks)

---

## Security Hardening

### Application Security

**Environment variable protection**:
```bash
# Set restrictive permissions on .env
chmod 600 .env
chown bidradar:bidradar .env

# Never commit .env to version control
echo ".env" >> .gitignore
```

**Input validation**:
```python
# Add to database.py
import re

def validate_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

def sanitize_input(text):
    # Remove SQL injection attempts
    dangerous_chars = ["'", '"', ';', '--', '/*', '*/']
    for char in dangerous_chars:
        text = text.replace(char, '')
    return text
```

**SQL injection prevention**:
```python
# Always use parameterized queries
cursor.execute("SELECT * FROM tenders WHERE id = ?", (tender_id,))

# NEVER do this:
cursor.execute(f"SELECT * FROM tenders WHERE id = '{tender_id}'")
```

### Network Security

**Firewall configuration**:
```bash
# Allow only necessary ports
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw deny 8501/tcp   # Block direct Streamlit access (use nginx)
sudo ufw enable
```

**Rate limiting** (nginx):
```nginx
# Add to nginx.conf
limit_req_zone $binary_remote_addr zone=bidradar_limit:10m rate=10r/s;

server {
    location / {
        limit_req zone=bidradar_limit burst=20 nodelay;
        # ... rest of config
    }
}
```

### Database Security

**PostgreSQL hardening**:
```sql
-- Use strong password
ALTER USER bidradar WITH PASSWORD 'very-secure-password-here';

-- Restrict connections
-- In pg_hba.conf:
# local   bidradar    bidradar                              md5
# host    bidradar    bidradar    127.0.0.1/32            md5

-- Disable remote access (if not needed)
-- In postgresql.conf:
# listen_addresses = 'localhost'
```

**SQLite hardening**:
```bash
# Restrict file permissions
chmod 640 tender_platform.db
chown bidradar:bidradar tender_platform.db
```

---

## Scaling Strategies

### Vertical Scaling

**Increase resources**:
- More CPU cores for concurrent processing
- More RAM for larger datasets and caching
- Faster storage (SSD) for database operations

**Application tuning**:
```python
# Optimize database queries
# Add indices for frequently queried columns

# Implement result pagination
def get_tenders_paginated(page=1, per_page=50):
    offset = (page - 1) * per_page
    cursor.execute(
        "SELECT * FROM tenders ORDER BY created_at DESC LIMIT ? OFFSET ?",
        (per_page, offset)
    )
    return cursor.fetchall()

# Use connection pooling (for PostgreSQL)
from sqlalchemy import create_engine
engine = create_engine('postgresql://...', pool_size=20, max_overflow=0)
```

### Horizontal Scaling

**Load balancing** (multiple Streamlit instances):

```nginx
upstream bidradar_cluster {
    least_conn;
    server 127.0.0.1:8501;
    server 127.0.0.1:8502;
    server 127.0.0.1:8503;
}

server {
    location / {
        proxy_pass http://bidradar_cluster;
        # ... other proxy settings
    }
}
```

**Shared state** (Redis for caching):
```python
import redis

# Initialize Redis connection
redis_client = redis.Redis(host='localhost', port=6379, db=0)

# Cache recommendations
def get_recommendations_cached(vendor_name):
    cache_key = f"recommendations:{vendor_name}"
    cached = redis_client.get(cache_key)

    if cached:
        return json.loads(cached)

    # Generate fresh recommendations
    recommendations = generate_recommendations(vendor_name)

    # Cache for 1 hour
    redis_client.setex(cache_key, 3600, json.dumps(recommendations))

    return recommendations
```

### Database Scaling

**Read replicas**:
```python
# Master for writes
master_db = Database('postgresql://master-host/bidradar')

# Replica for reads
replica_db = Database('postgresql://replica-host/bidradar')

# Route queries
def get_tenders():
    return replica_db.get_all_tenders()  # Read from replica

def store_tender(tender):
    return master_db.store_tenders([tender])  # Write to master
```

**Database partitioning**:
```sql
-- Partition tenders by year
CREATE TABLE tenders_2024 PARTITION OF tenders
    FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');

CREATE TABLE tenders_2025 PARTITION OF tenders
    FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');
```

---

## Conclusion

This deployment guide provides comprehensive instructions for deploying and maintaining the BidRadar platform in various environments. For production deployments, always follow security best practices, implement proper monitoring, and maintain regular backups.

**Quick Reference**:
- **Development**: `streamlit run app.py`
- **Production**: Use systemd/Docker + nginx + PostgreSQL
- **Monitoring**: Check logs, database stats, and health endpoints
- **Backups**: Daily automated backups with 30-day retention
- **Support**: Refer to troubleshooting section and application logs

---

## Document Control

**Version**: 1.0
**Last Updated**: December 2025
**Next Review**: March 2026
**Maintained by**: DevOps Team
