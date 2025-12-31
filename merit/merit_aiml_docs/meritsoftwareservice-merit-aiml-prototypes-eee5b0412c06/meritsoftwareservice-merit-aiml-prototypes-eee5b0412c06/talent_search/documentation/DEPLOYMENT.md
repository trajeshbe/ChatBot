# TalentSearch - Deployment Guide

## Table of Contents
1. [System Requirements](#system-requirements)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Environment Setup](#environment-setup)
5. [Database Setup](#database-setup)
6. [Running the Application](#running-the-application)
7. [Production Deployment](#production-deployment)
8. [Scaling Considerations](#scaling-considerations)
9. [Monitoring and Maintenance](#monitoring-and-maintenance)
10. [Security Hardening](#security-hardening)
11. [Troubleshooting](#troubleshooting)
12. [Backup and Recovery](#backup-and-recovery)

---

## System Requirements

### Minimum Requirements

**Hardware:**
- CPU: 2 cores, 2.0 GHz or higher
- RAM: 4 GB minimum
- Storage: 10 GB available space
- Network: Stable internet connection (for API calls)

**Software:**
- Operating System: Windows 10/11, macOS 10.14+, Linux (Ubuntu 18.04+)
- Python: 3.8 or higher (3.10+ recommended)
- pip: Latest version
- Git (optional, for version control)

### Recommended Requirements

**Hardware:**
- CPU: 4 cores, 2.5 GHz or higher
- RAM: 8 GB or more
- Storage: 50 GB available space (for logs and data)
- Network: High-speed internet (1 Mbps+ for API calls)

**Software:**
- Python: 3.10 or 3.11
- Virtual environment manager (venv, conda)
- Modern web browser (Chrome, Firefox, Edge)

### Cloud Deployment (Optional)

**AWS:**
- EC2 instance: t3.medium or larger
- S3: For file storage and backups
- RDS: For production database (PostgreSQL)

**Azure:**
- VM: Standard B2s or larger
- Blob Storage: For file storage
- Azure Database for PostgreSQL

**Google Cloud:**
- Compute Engine: e2-medium or larger
- Cloud Storage: For file storage
- Cloud SQL: For PostgreSQL

---

## Installation

### Step 1: Verify Python Installation

```bash
# Check Python version
python --version
# or
python3 --version

# Should output: Python 3.8.x or higher
```

If Python is not installed:
- **Windows**: Download from [python.org](https://www.python.org/downloads/)
- **macOS**: `brew install python3`
- **Linux**: `sudo apt-get install python3 python3-pip`

### Step 2: Create Project Directory

```bash
# Create and navigate to project directory
mkdir talent_search_deployment
cd talent_search_deployment
```

### Step 3: Clone or Copy Project Files

**Option A: Using Git**
```bash
git clone <repository_url>
cd talent_search
```

**Option B: Manual Copy**
```bash
# Copy all project files to current directory
# Ensure directory structure matches:
# talent_search/
# ├── app.py
# ├── config.ini
# ├── requirements.txt
# ├── recruiter.json
# ├── interface/
# ├── utils/
# ├── data/
# └── documentation/
```

### Step 4: Create Virtual Environment

**Using venv (recommended):**
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate

# macOS/Linux:
source venv/bin/activate
```

**Using conda:**
```bash
# Create conda environment
conda create -n talentsearch python=3.10

# Activate environment
conda activate talentsearch
```

### Step 5: Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install required packages
pip install -r requirements.txt
```

**Installation time:** 5-10 minutes depending on internet speed

**Verify installation:**
```bash
pip list | grep streamlit
pip list | grep langchain
pip list | grep openai
```

### Step 6: Verify Installation

```bash
# Check for critical imports
python -c "import streamlit; import langchain; import openai; print('Installation successful')"
```

Expected output: `Installation successful`

---

## Configuration

### File Structure Verification

Ensure the following files exist:

```
talent_search/
├── app.py                     # Main application
├── config.ini                 # Configuration file
├── requirements.txt           # Dependencies
├── recruiter.json            # Recruiter profiles
├── .env                      # Environment variables (create this)
├── interface/
│   ├── __init__.py
│   ├── alerts.py
│   ├── helpers.py
│   ├── recruiter.py
│   ├── search.py
│   └── upload.py
├── utils/
│   ├── __init__.py
│   ├── config_reader.py
│   ├── custom_filter.py
│   ├── custom_prompts.py
│   ├── custom_templates.py
│   └── log_writer.py
├── data/
│   ├── Phaidon_business_sectors.xlsx
│   ├── samples.xlsx
│   └── meta_sample.xlsx
└── documentation/
    ├── README.md
    ├── ARCHITECTURE.md
    ├── API_REFERENCE.md
    ├── USER_GUIDE.md
    └── DEPLOYMENT.md
```

### config.ini Configuration

**Location:** Root directory (`talent_search/config.ini`)

**Default configuration:**
```ini
[default]
output_columns = ["job_title",
    "description",
    "company_name",
    "domain",
    "sector",
    "work_arrangement",
    "location_city",
    "location_country",
    "location_region",
    "contract_type",
    "seniority",
    "date_posted",
    "salary_low",
    "salary_high",
    "type_of_job",
    "recruiter_name",
    "relevence_score",
    "justification",
    "content"
    ]
db_path = db
input_path = input

[llm_config]
llm_model = gpt-4o-mini
model_provider = openai
temperature = 0
max_tokens = 10000
```

**Configuration options:**

| Parameter | Description | Default | Options |
|-----------|-------------|---------|---------|
| output_columns | Fields to display | [see above] | Add/remove fields |
| db_path | Database directory | db | Any valid path |
| input_path | Upload directory | input | Any valid path |
| llm_model | LLM model name | gpt-4o-mini | gpt-4, gpt-3.5-turbo, etc. |
| model_provider | LLM provider | openai | openai, groq, etc. |
| temperature | Model creativity | 0 | 0.0 - 2.0 |
| max_tokens | Response limit | 10000 | 1000 - 100000 |

**Customization examples:**

**Change LLM model:**
```ini
llm_model = gpt-4
```

**Increase max tokens:**
```ini
max_tokens = 15000
```

**Add custom paths:**
```ini
db_path = /var/lib/talentsearch/db
input_path = /var/lib/talentsearch/input
```

### recruiter.json Configuration

**Location:** Root directory (`talent_search/recruiter.json`)

**Structure:**
```json
{
    "recruiters": [
        {
            "Name": "Recruiter Name",
            "Profile": "Specialization",
            "Focus": "Description of focus areas",
            "Location/Region": "Geographic coverage",
            "Seniority Level": "Levels handled",
            "Industry": "Industry sectors"
        }
    ],
    "corporate_titles": [
        "Intern",
        "Junior",
        "Mid-senior",
        "Senior",
        "Senior Leadership"
    ]
}
```

**Adding a new recruiter:**
```json
{
    "Name": "Sam Wilson",
    "Profile": "Healthcare Talent Specialist",
    "Focus": "Recruiting healthcare professionals",
    "Location/Region": "North America, Europe",
    "Seniority Level": "Entry to Senior",
    "Industry": "Healthcare, Medical Services"
}
```

**Modifying seniority levels:**
```json
"corporate_titles": [
    "Entry Level",
    "Associate",
    "Senior Associate",
    "Manager",
    "Director",
    "VP",
    "C-Suite"
]
```

### Domain Taxonomy Configuration

**Location:** `data/Phaidon_business_sectors.xlsx`

**Structure:**
| Domain | Business Sectors | Job type |
|--------|------------------|----------|
| Finance | Investment Banking | Investment Analyst, Trader, ... |
| IT | Software Development | Software Engineer, Developer, ... |

**To customize:**
1. Open file in Excel
2. Add/modify domains, sectors, and job types
3. Save file
4. Restart application

---

## Environment Setup

### Create .env File

**Location:** Root directory (`talent_search/.env`)

**Required content:**
```env
# OpenAI Configuration
OPEN_AI_KEY=sk-your-openai-api-key-here

# LangChain/LangSmith Configuration
LANGCHAIN_KEY=lc-your-langchain-api-key-here

# Optional: Override default settings
# LANGCHAIN_PROJECT=YourProjectName
# LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
```

**Obtaining API Keys:**

#### OpenAI API Key

1. Go to [https://platform.openai.com/](https://platform.openai.com/)
2. Sign up or log in
3. Navigate to API Keys section
4. Click "Create new secret key"
5. Copy key and paste in .env file

**Cost considerations:**
- GPT-4o-mini: ~$0.15 per 1M input tokens, ~$0.60 per 1M output tokens
- Estimated cost: $0.01-0.05 per job processing
- Monitor usage at [https://platform.openai.com/usage](https://platform.openai.com/usage)

#### LangChain API Key

1. Go to [https://smith.langchain.com/](https://smith.langchain.com/)
2. Sign up or log in
3. Navigate to Settings → API Keys
4. Create new API key
5. Copy key and paste in .env file

**Note:** LangSmith is optional for tracing and monitoring. The application will work without it.

### Environment Variable Verification

```bash
# Linux/macOS
cat .env

# Windows
type .env

# Verify keys are set
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('OpenAI:', 'Set' if os.getenv('OPEN_AI_KEY') else 'Missing'); print('LangChain:', 'Set' if os.getenv('LANGCHAIN_KEY') else 'Missing')"
```

### File Permissions

**Linux/macOS:**
```bash
# Secure .env file
chmod 600 .env

# Ensure application files are readable
chmod 644 config.ini recruiter.json
chmod 755 app.py

# Make directories writable for logs and database
chmod 755 db input logs
```

**Windows:**
```powershell
# Right-click .env → Properties → Security
# Remove access for all users except current user
```

---

## Database Setup

### SQLite Configuration (Default)

TalentSearch uses SQLite by default for simplicity.

**Database file:** `example.db` (created automatically on first upload)

**No manual setup required.** The database is created automatically when you:
1. Upload job data
2. Click Submit in Upload tab

**Verify database creation:**
```bash
# After first upload, check for database file
ls -la example.db

# View database schema
sqlite3 example.db ".schema users"
```

**Expected schema:**
```sql
CREATE TABLE users (
    job_title TEXT,
    description TEXT,
    company_name TEXT,
    domain TEXT,
    sector TEXT,
    work_arrangement TEXT,
    location_city TEXT,
    location_country TEXT,
    location_region TEXT,
    contract_type TEXT,
    seniority TEXT,
    date_posted TEXT,
    salary_low TEXT,
    salary_high TEXT,
    type_of_job TEXT,
    recruiter_name TEXT,
    relevence_score TEXT,
    justification TEXT,
    content TEXT
);
```

### PostgreSQL Setup (Production)

For production deployments with multiple users, migrate to PostgreSQL.

#### Install PostgreSQL

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
```

**macOS:**
```bash
brew install postgresql
brew services start postgresql
```

**Windows:**
Download installer from [https://www.postgresql.org/download/](https://www.postgresql.org/download/)

#### Create Database

```bash
# Connect to PostgreSQL
sudo -u postgres psql

# Create database
CREATE DATABASE talentsearch;

# Create user
CREATE USER talentsearch_user WITH PASSWORD 'your_secure_password';

# Grant privileges
GRANT ALL PRIVILEGES ON DATABASE talentsearch TO talentsearch_user;

# Exit
\q
```

#### Update Code for PostgreSQL

**Modify `interface/search.py`:**

Change line 15 from:
```python
self.db = SQLDatabase.from_uri("sqlite:///example.db")
```

To:
```python
self.db = SQLDatabase.from_uri("postgresql://talentsearch_user:your_secure_password@localhost:5432/talentsearch")
```

**Update .env:**
```env
DATABASE_URL=postgresql://talentsearch_user:your_secure_password@localhost:5432/talentsearch
```

**Modify `interface/upload.py`:**

Change lines 140-143 from:
```python
conn = sqlite3.connect('example.db')
meta_df.to_sql('users', conn, if_exists='replace', index=False)
conn.commit()
conn.close()
```

To:
```python
from sqlalchemy import create_engine
engine = create_engine(os.getenv('DATABASE_URL'))
meta_df.to_sql('users', engine, if_exists='replace', index=False)
```

**Install PostgreSQL adapter:**
```bash
pip install psycopg2-binary
```

---

## Running the Application

### Development Mode

**Start the application:**
```bash
# Ensure virtual environment is activated
# venv\Scripts\activate (Windows)
# source venv/bin/activate (macOS/Linux)

# Run Streamlit
streamlit run app.py
```

**Expected output:**
```
You can now view your Streamlit app in your browser.

Local URL: http://localhost:8501
Network URL: http://192.168.1.100:8501
```

**Access the application:**
- Open browser
- Navigate to `http://localhost:8501`
- TalentSearch interface should appear

### Custom Port

```bash
# Run on custom port
streamlit run app.py --server.port 8080

# Access at http://localhost:8080
```

### Custom Host (Network Access)

```bash
# Allow network access
streamlit run app.py --server.address 0.0.0.0

# Access from other devices using:
# http://<your-ip-address>:8501
```

### Development Options

```bash
# Enable debug mode
streamlit run app.py --logger.level=debug

# Disable file watcher (for stability)
streamlit run app.py --server.fileWatcherType none

# Increase upload limit (default 200MB)
streamlit run app.py --server.maxUploadSize 500
```

### Verify Application Startup

**Checklist:**
- [ ] No errors in terminal
- [ ] Browser opens automatically
- [ ] "TalentSearch" title visible
- [ ] Three tabs displayed (Search, Alerts, Upload)
- [ ] No warning messages

**Common startup issues:**

| Issue | Cause | Solution |
|-------|-------|----------|
| Port already in use | Another app on 8501 | Use different port or kill process |
| Module not found | Missing dependency | Run `pip install -r requirements.txt` |
| Config file not found | Wrong directory | Run from project root |
| API key error | Missing .env | Create .env file with keys |

---

## Production Deployment

### Deployment Architecture

```
┌─────────────┐
│   Users     │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  Load Balancer  │
│    (Nginx)      │
└──────┬──────────┘
       │
       ▼
┌────────────────────────┐
│  Streamlit Instances   │
│  (Multiple processes)  │
└──────┬─────────────────┘
       │
       ▼
┌────────────────────────┐
│  PostgreSQL Database   │
└────────────────────────┘
```

### Using Streamlit Cloud

**Steps:**
1. Push code to GitHub repository
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect GitHub account
4. Select repository and branch
5. Set secrets (API keys) in Streamlit Cloud dashboard
6. Deploy

**Secrets configuration in Streamlit Cloud:**
```toml
# In Streamlit Cloud dashboard, add:
OPEN_AI_KEY = "sk-your-key-here"
LANGCHAIN_KEY = "lc-your-key-here"
```

### Using Docker

**Create Dockerfile:**

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create necessary directories
RUN mkdir -p logs db input

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run application
CMD ["streamlit", "run", "app.py", "--server.address", "0.0.0.0", "--server.port", "8501"]
```

**Create docker-compose.yml:**

```yaml
version: '3.8'

services:
  talentsearch:
    build: .
    ports:
      - "8501:8501"
    environment:
      - OPEN_AI_KEY=${OPEN_AI_KEY}
      - LANGCHAIN_KEY=${LANGCHAIN_KEY}
    volumes:
      - ./db:/app/db
      - ./logs:/app/logs
      - ./input:/app/input
    restart: unless-stopped

  postgres:
    image: postgres:14
    environment:
      - POSTGRES_DB=talentsearch
      - POSTGRES_USER=talentsearch_user
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  postgres_data:
```

**Build and run:**
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

### Using Nginx Reverse Proxy

**Install Nginx:**
```bash
# Ubuntu/Debian
sudo apt-get install nginx
```

**Configure Nginx:**

Create `/etc/nginx/sites-available/talentsearch`:

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

**Enable configuration:**
```bash
sudo ln -s /etc/nginx/sites-available/talentsearch /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Using SSL/HTTPS (Let's Encrypt)

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal is configured automatically
```

### Systemd Service (Linux)

Create `/etc/systemd/system/talentsearch.service`:

```ini
[Unit]
Description=TalentSearch Application
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/talentsearch
Environment="PATH=/opt/talentsearch/venv/bin"
ExecStart=/opt/talentsearch/venv/bin/streamlit run app.py --server.address 0.0.0.0 --server.port 8501
Restart=always

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable talentsearch
sudo systemctl start talentsearch
sudo systemctl status talentsearch
```

---

## Scaling Considerations

### Horizontal Scaling

**Run multiple Streamlit instances:**

```bash
# Instance 1
streamlit run app.py --server.port 8501

# Instance 2
streamlit run app.py --server.port 8502

# Instance 3
streamlit run app.py --server.port 8503
```

**Configure load balancer** to distribute traffic across instances.

### Database Connection Pooling

For PostgreSQL, use connection pooling:

```python
from sqlalchemy.pool import QueuePool
from sqlalchemy import create_engine

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20
)
```

### Caching Strategy

Implement Redis for caching LLM responses:

```python
import redis
import json

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def get_cached_response(key):
    cached = redis_client.get(key)
    return json.loads(cached) if cached else None

def cache_response(key, value, ttl=3600):
    redis_client.setex(key, ttl, json.dumps(value))
```

### Async Processing

Use Celery for background job processing:

```python
# celery_tasks.py
from celery import Celery

app = Celery('talentsearch', broker='redis://localhost:6379/0')

@app.task
def process_job_metadata(job_data):
    # Process metadata asynchronously
    return enriched_data
```

---

## Monitoring and Maintenance

### Application Monitoring

**Streamlit built-in metrics:**
- Access `http://localhost:8501/_stcore/health` for health check
- Monitor session count and memory usage

**LangSmith Monitoring:**
- Dashboard: [https://smith.langchain.com/](https://smith.langchain.com/)
- View LLM calls, latency, costs
- Debug prompts and responses

**System Monitoring:**

```bash
# Monitor processes
ps aux | grep streamlit

# Monitor memory usage
free -h

# Monitor disk space
df -h

# Monitor database size
du -sh example.db
```

### Log Management

**Log locations:**
- Application logs: `./logs/DD-MM-YY/HH.log`
- Streamlit logs: `~/.streamlit/logs/`

**Log rotation:**

Create `/etc/logrotate.d/talentsearch`:

```
/opt/talentsearch/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
}
```

**View logs:**
```bash
# View latest log
tail -f logs/$(date +%d-%m-%y)/$(date +%H).log

# Search for errors
grep ERROR logs/*/*.log
```

### Database Maintenance

**SQLite:**
```bash
# Compact database
sqlite3 example.db "VACUUM;"

# Integrity check
sqlite3 example.db "PRAGMA integrity_check;"
```

**PostgreSQL:**
```bash
# Vacuum database
psql -U talentsearch_user -d talentsearch -c "VACUUM ANALYZE;"

# Check database size
psql -U talentsearch_user -d talentsearch -c "SELECT pg_size_pretty(pg_database_size('talentsearch'));"
```

### Performance Tuning

**Streamlit configuration:**

Create `.streamlit/config.toml`:

```toml
[server]
maxUploadSize = 500
enableCORS = false
enableXsrfProtection = true

[browser]
gatherUsageStats = false

[runner]
magicEnabled = false
```

**Database indexes:**

```sql
-- Add indexes for frequently queried fields
CREATE INDEX idx_domain ON users(domain);
CREATE INDEX idx_sector ON users(sector);
CREATE INDEX idx_recruiter ON users(recruiter_name);
CREATE INDEX idx_date_posted ON users(date_posted);
```

---

## Security Hardening

### API Key Security

**Best practices:**
1. Never commit `.env` to version control
2. Use environment variables in production
3. Rotate keys regularly
4. Set spending limits on OpenAI account

**Git ignore:**

Create `.gitignore`:
```
.env
*.db
logs/
__pycache__/
venv/
.streamlit/secrets.toml
```

### Input Validation

**File upload restrictions:**

Update `upload.py` to add file size validation:

```python
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

if data and btn:
    if data.size > MAX_FILE_SIZE:
        st.error("File too large. Maximum size: 50MB")
        return
```

### SQL Injection Prevention

The application uses LangChain's SQL tools which have built-in protections. However, for additional security:

1. Use parameterized queries
2. Validate user inputs
3. Limit database user permissions

### Network Security

**Firewall rules:**
```bash
# Allow only necessary ports
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

**Disable debug mode in production:**
```python
# In app.py, ensure debug is off
st.set_page_config(layout="wide", page_title="TalentSearch")
# Do not use st.write() for debugging in production
```

### Authentication (Optional)

Add basic authentication using `streamlit-authenticator`:

```bash
pip install streamlit-authenticator
```

```python
# Add to app.py
import streamlit_authenticator as stauth

credentials = {
    "usernames": {
        "admin": {
            "name": "Admin User",
            "password": hashed_password
        }
    }
}

authenticator = stauth.Authenticate(credentials, ...)
name, authentication_status, username = authenticator.login('Login', 'main')

if authentication_status:
    # Show main app
    obj = CreateUI()
    obj.render_ui()
else:
    st.error('Username/password is incorrect')
```

---

## Troubleshooting

### Installation Issues

**Issue: pip install fails**
```bash
# Solution: Upgrade pip and try again
python -m pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir
```

**Issue: Module not found after install**
```bash
# Solution: Verify virtual environment is activated
which python  # Should show venv path
pip list | grep <module>
```

### Runtime Issues

**Issue: API key errors**
```bash
# Solution: Verify .env file
cat .env
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('OPEN_AI_KEY'))"
```

**Issue: Database locked**
```bash
# Solution: Close all connections
fuser example.db  # Shows processes using file
kill <pid>
```

**Issue: Port already in use**
```bash
# Solution: Kill process or use different port
# Linux/macOS:
lsof -ti:8501 | xargs kill

# Windows:
netstat -ano | findstr :8501
taskkill /PID <pid> /F

# Or use different port:
streamlit run app.py --server.port 8080
```

### Performance Issues

**Issue: Slow LLM responses**
- Check internet connection
- Verify OpenAI API status
- Consider switching to faster model
- Implement caching

**Issue: High memory usage**
- Limit result set size
- Clear session state regularly
- Restart application periodically

**Issue: Database queries slow**
- Add indexes to frequently queried columns
- Vacuum/analyze database
- Consider migration to PostgreSQL

---

## Backup and Recovery

### Backup Strategy

**Database backup:**
```bash
# SQLite
cp example.db backups/example_$(date +%Y%m%d).db

# PostgreSQL
pg_dump -U talentsearch_user talentsearch > backups/talentsearch_$(date +%Y%m%d).sql
```

**Full system backup:**
```bash
# Backup all important files
tar -czf talentsearch_backup_$(date +%Y%m%d).tar.gz \
    app.py \
    config.ini \
    recruiter.json \
    .env \
    interface/ \
    utils/ \
    data/ \
    example.db \
    logs/
```

**Automated backup script:**

Create `backup.sh`:
```bash
#!/bin/bash
BACKUP_DIR="/backups/talentsearch"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup database
cp example.db $BACKUP_DIR/example_$DATE.db

# Backup configuration
tar -czf $BACKUP_DIR/config_$DATE.tar.gz config.ini recruiter.json

# Keep only last 30 days
find $BACKUP_DIR -type f -mtime +30 -delete

echo "Backup completed: $DATE"
```

**Schedule with cron:**
```bash
# Run daily at 2 AM
0 2 * * * /opt/talentsearch/backup.sh >> /var/log/talentsearch_backup.log 2>&1
```

### Recovery Procedures

**Restore database:**
```bash
# SQLite
cp backups/example_20241220.db example.db

# PostgreSQL
psql -U talentsearch_user talentsearch < backups/talentsearch_20241220.sql
```

**Restore full system:**
```bash
tar -xzf talentsearch_backup_20241220.tar.gz -C /opt/talentsearch/
```

### Disaster Recovery Plan

1. **Regular backups**: Daily automated backups
2. **Off-site storage**: Copy backups to cloud storage (S3, Azure Blob)
3. **Test restores**: Monthly recovery drills
4. **Documentation**: Keep deployment docs updated
5. **Monitoring**: Alert on backup failures

---

## Appendix

### Environment Variables Reference

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| OPEN_AI_KEY | Yes | OpenAI API key | sk-proj-... |
| LANGCHAIN_KEY | Optional | LangSmith API key | lc-... |
| LANGCHAIN_PROJECT | Optional | LangSmith project name | TalentSearch |
| DATABASE_URL | Optional | PostgreSQL connection string | postgresql://... |

### Port Reference

| Port | Service | Protocol |
|------|---------|----------|
| 8501 | Streamlit (default) | HTTP |
| 5432 | PostgreSQL | TCP |
| 6379 | Redis (optional) | TCP |
| 80 | Nginx HTTP | HTTP |
| 443 | Nginx HTTPS | HTTPS |

### Directory Structure

```
talent_search/
├── app.py
├── config.ini
├── requirements.txt
├── recruiter.json
├── .env
├── .gitignore
├── example.db
├── interface/
├── utils/
├── data/
├── documentation/
├── db/          # Created automatically
├── input/       # Created automatically
├── logs/        # Created automatically
└── venv/        # Virtual environment
```

### Useful Commands

**Check application status:**
```bash
systemctl status talentsearch
```

**View real-time logs:**
```bash
tail -f logs/$(date +%d-%m-%y)/$(date +%H).log
```

**Restart application:**
```bash
systemctl restart talentsearch
```

**Check database size:**
```bash
du -sh example.db
```

**Monitor system resources:**
```bash
htop  # or top
```

**Test API connectivity:**
```bash
curl -X POST https://api.openai.com/v1/chat/completions \
  -H "Authorization: Bearer $OPEN_AI_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "test"}]}'
```

---

## Quick Start Checklist

- [ ] Python 3.8+ installed
- [ ] Virtual environment created and activated
- [ ] Dependencies installed from requirements.txt
- [ ] .env file created with API keys
- [ ] config.ini configured
- [ ] recruiter.json configured
- [ ] Data directory contains Phaidon_business_sectors.xlsx
- [ ] Application starts without errors
- [ ] Database created successfully on first upload
- [ ] Logs directory created
- [ ] Can access application in browser
- [ ] Test upload completed successfully
- [ ] Search functionality working
- [ ] Alerts displaying correctly

---

**Deployment complete! For ongoing support, refer to the documentation files and monitoring logs.**

For questions or issues, check:
- README.md - Project overview
- ARCHITECTURE.md - System design
- API_REFERENCE.md - Code documentation
- USER_GUIDE.md - Usage instructions
