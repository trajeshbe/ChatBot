# Enterprise RAG Chatbot - Fresh Installation Guide

> **Complete Step-by-Step Guide for New Machines**
>
> **Purpose**: Install and configure the Enterprise RAG Chatbot from scratch on a brand new machine
>
> **Time Required**: 30-45 minutes
>
> **Last Updated**: 2026-01-05

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [System Requirements](#system-requirements)
3. [Pre-Installation Checklist](#pre-installation-checklist)
4. [Step-by-Step Installation](#step-by-step-installation)
5. [Post-Installation Verification](#post-installation-verification)
6. [Configuration](#configuration)
7. [First-Time Usage](#first-time-usage)
8. [Troubleshooting](#troubleshooting)
9. [Next Steps](#next-steps)

---

## Prerequisites

### Required Software

Before starting, ensure you have the following installed:

| Software | Minimum Version | Recommended Version | Download Link |
|----------|----------------|---------------------|---------------|
| **Docker** | 20.10+ | 24.0+ | https://docs.docker.com/get-docker/ |
| **Docker Compose** | 2.0+ | 2.23+ | Included with Docker Desktop |
| **Git** | 2.30+ | 2.43+ | https://git-scm.com/downloads |
| **Node.js** | 18.x | 20.x (LTS) | https://nodejs.org/ |
| **Python** | 3.11+ | 3.11.7 | https://www.python.org/downloads/ |

### Optional but Recommended

- **WSL2** (Windows only): For better Docker performance
- **Visual Studio Code**: Recommended IDE
- **pgAdmin** or **DBeaver**: For database management (optional)

### API Keys Required

You'll need API keys for:

1. **OpenAI** (required for main functionality)
   - Get from: https://platform.openai.com/api-keys
   - Minimum: `gpt-4o-mini` access

2. **Anthropic Claude** (optional but recommended)
   - Get from: https://console.anthropic.com/
   - Models: `claude-3-5-sonnet-20241022`

3. **Hugging Face** (optional, for embeddings)
   - Get from: https://huggingface.co/settings/tokens

---

## System Requirements

### Minimum Requirements

- **OS**: Windows 10/11, macOS 12+, Ubuntu 20.04+
- **CPU**: 4 cores
- **RAM**: 8 GB
- **Disk Space**: 20 GB free
- **Internet**: Stable broadband connection

### Recommended Requirements

- **OS**: Windows 11, macOS 14+, Ubuntu 22.04+
- **CPU**: 8+ cores
- **RAM**: 16 GB
- **Disk Space**: 50 GB free (SSD recommended)
- **GPU**: Optional (for local LLM inference with Ollama)

### Port Requirements

Ensure these ports are available:

| Port | Service | Required |
|------|---------|----------|
| 3001 | Frontend | Yes |
| 8000 | Backend API | Yes |
| 5432 | PostgreSQL | Yes |
| 6379 | Redis | Yes |
| 9000 | MinIO API | Yes |
| 9001 | MinIO Console | Yes |
| 11434 | Ollama (optional) | No |

---

## Pre-Installation Checklist

Before proceeding, verify:

- [ ] Docker is installed and running
- [ ] Docker Compose is available
- [ ] Git is installed
- [ ] You have admin/sudo privileges
- [ ] All required ports are available
- [ ] You have at least one LLM API key (OpenAI or Anthropic)
- [ ] Stable internet connection
- [ ] 20+ GB free disk space

**Check Docker Installation**:
```bash
docker --version
docker-compose --version
docker ps
```

If all commands work without errors, you're ready to proceed!

---

## Step-by-Step Installation

### Step 1: Clone the Repository

```bash
# Navigate to your projects directory
cd ~/projects  # or C:\projects on Windows

# Clone the repository
git clone <repository-url> enterprise-rag-chatbot

# Navigate into the project
cd enterprise-rag-chatbot

# Verify the clone
ls -la
```

**Expected Output**: You should see directories like `backend/`, `frontend/`, `docs/`, `scripts/`, etc.

---

### Step 2: Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Open the .env file in your editor
# On Windows:
notepad .env
# On macOS:
open -e .env
# On Linux:
nano .env
# Or use VS Code:
code .env
```

**Required Configuration** - Update these values in `.env`:

```bash
# ============================================================================
# LLM API Keys (At least one is required)
# ============================================================================

# OpenAI (Recommended)
OPENAI_API_KEY=sk-proj-your-actual-openai-api-key-here

# Anthropic Claude (Optional but recommended)
ANTHROPIC_API_KEY=sk-ant-your-actual-anthropic-api-key-here

# ============================================================================
# Database Configuration
# ============================================================================
POSTGRES_DB=ragchatbot
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# ============================================================================
# MinIO Configuration (Object Storage)
# ============================================================================
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin
MINIO_ENDPOINT=minio:9000
MINIO_BUCKET_NAME=documents

# ============================================================================
# Redis Configuration (Caching)
# ============================================================================
REDIS_HOST=redis
REDIS_PORT=6379

# ============================================================================
# Application Configuration
# ============================================================================
BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3001

# Vector Embeddings
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
VECTOR_DIMENSIONS=384

# Default LLM Settings
DEFAULT_LLM_PROVIDER=openai
DEFAULT_MODEL=gpt-4o-mini
DEFAULT_TEMPERATURE=0.2
DEFAULT_MAX_TOKENS=1000

# ============================================================================
# Optional: Ollama Configuration (Local LLM)
# ============================================================================
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_DEFAULT_MODEL=mistral
```

**Important Notes**:
1. Replace `sk-proj-your-actual-openai-api-key-here` with your real API key
2. Keep `POSTGRES_PASSWORD` and `MINIO_ROOT_PASSWORD` secure in production
3. Don't commit `.env` to git (it's already in `.gitignore`)

---

### Step 3: Verify Docker Configuration

```bash
# Check if docker-compose.yml is present
ls -la docker-compose.yml

# Validate the configuration (optional)
docker-compose config

# Pull required base images (optional, speeds up build)
docker-compose pull postgres redis minio
```

**Expected Output**: No errors. If `docker-compose config` works, your configuration is valid.

---

### Step 4: Run the Automated Installation

We'll use the automated installation script that handles everything:

```bash
# Make the script executable (Linux/macOS)
chmod +x scripts/setup/initialize-fresh-install.sh

# Run the installation
./scripts/setup/initialize-fresh-install.sh
```

**On Windows (WSL)**: Use the same commands above
**On Windows (PowerShell)**: Use `bash scripts/setup/initialize-fresh-install.sh`

**What This Does**:
1. ✅ Builds Docker images for backend and frontend
2. ✅ Starts infrastructure services (PostgreSQL, Redis, MinIO)
3. ✅ Initializes database with all tables
4. ✅ Seeds organizational hierarchy (departments, teams, roles)
5. ✅ Creates default admin user
6. ✅ Starts application services
7. ✅ Runs health checks
8. ✅ Displays connection information

**Expected Duration**: 2-3 minutes

**Watch for**:
- Green checkmarks (✓) indicating successful steps
- Service URLs at the end
- Default credentials display

---

### Step 5: Monitor the Installation

While the installation runs, you'll see output like:

```
============================================================
  Enterprise RAG Chatbot - Fresh Installation
============================================================

Step 1: Checking prerequisites
✓ Docker is running
✓ PostgreSQL container is running
✓ Redis container is running

Step 2: Building Docker images
Building backend...
Building frontend...
✓ Docker images built

Step 3: Starting infrastructure services
✓ PostgreSQL started
✓ Redis started
✓ MinIO started

Step 4: Initializing database
✓ Database created
✓ Extensions enabled
✓ Base schema applied
✓ RBAC tables created
✓ 90+ tables initialized

Step 5: Starting application services
✓ Backend started
✓ Frontend started

Step 6: Running health checks
✓ Backend API healthy
✓ Frontend healthy
```

---

### Step 6: Verify Services Are Running

```bash
# Check all containers are running
docker-compose ps

# Expected output: All services should show "Up" status
# NAME                COMMAND              SERVICE     STATUS      PORTS
# rag-backend         ...                  backend     Up          0.0.0.0:8000->8000/tcp
# rag-frontend        ...                  frontend    Up          0.0.0.0:3001->3001/tcp
# rag-postgres        ...                  postgres    Up          0.0.0.0:5432->5432/tcp
# rag-redis           ...                  redis       Up          0.0.0.0:6379->6379/tcp
# rag-minio           ...                  minio       Up          0.0.0.0:9000-9001->9000-9001/tcp
```

If any service shows "Exited" or "Restarting", check logs:

```bash
# View logs for a specific service
docker-compose logs backend
docker-compose logs frontend

# Follow logs in real-time
docker-compose logs -f backend
```

---

## Post-Installation Verification

### Test 1: Backend Health Check

```bash
# Test backend API
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","database":"connected","timestamp":"2026-01-05T12:00:00Z"}
```

### Test 2: Frontend Access

Open your browser and navigate to:
- **Frontend**: http://localhost:3001

You should see the login page.

### Test 3: API Documentation

Open your browser and navigate to:
- **API Docs**: http://localhost:8000/api/docs
- **GraphQL Playground**: http://localhost:8000/graphql

### Test 4: Database Connection

```bash
# Connect to database
docker exec -it rag-postgres psql -U postgres -d ragchatbot

# Run a test query
SELECT COUNT(*) FROM users;

# Expected: Should return count (at least 1 for admin user)

# Exit
\q
```

### Test 5: MinIO (Object Storage)

Open your browser and navigate to:
- **MinIO Console**: http://localhost:9001
- **Credentials**: minioadmin / minioadmin

You should see the MinIO dashboard.

---

## Configuration

### Default Admin Credentials

After installation, you can log in with:

```
URL:      http://localhost:3001
Username: admin
Email:    admin@enterprise-rag.local
Password: admin123
```

**⚠️  SECURITY WARNING**: Change this password immediately!

### Change Admin Password

**Option 1: Via UI**
1. Log in with default credentials
2. Go to Profile Settings
3. Change password

**Option 2: Via API**
```bash
curl -X POST http://localhost:8000/api/v1/users/change-password \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "old_password": "admin123",
    "new_password": "YourSecurePassword123!"
  }'
```

**Option 3: Via Database**
```bash
# Generate new password hash in Python
docker exec -it rag-backend python3 -c "
import bcrypt
password = 'YourSecurePassword123!'
hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
print(hashed.decode())
"

# Update in database
docker exec -it rag-postgres psql -U postgres -d ragchatbot -c "
UPDATE users
SET hashed_password = '<paste-hash-here>'
WHERE username = 'admin';
"
```

---

## First-Time Usage

### 1. Log In

1. Open http://localhost:3001
2. Enter username: `admin`
3. Enter password: `admin123`
4. Click "Login"

### 2. Upload Your First Document

1. Click on "File Upload" in the sidebar
2. Drag and drop a PDF, DOCX, or TXT file
3. Wait for processing (you'll see a progress indicator)
4. Document will appear in the uploaded files list

### 3. Create a Chat Session

1. Click on "RAG Chat" in the sidebar
2. Click "New Session"
3. Give your session a name
4. Select the document(s) you want to query

### 4. Ask Your First Question

1. Type a question related to your document(s)
2. Press Enter or click Send
3. Wait for the AI response
4. You'll see:
   - AI-generated answer
   - Source citations
   - Confidence scores

### 5. Explore Features

- **Web Scraping**: Scrape content from websites
- **Data Extraction**: Extract structured data from documents
- **Evaluation Metrics**: View RAG performance metrics
- **Admin Panel**: Manage users, roles, and modules (admin only)

---

## Troubleshooting

### Issue 1: Docker Services Won't Start

**Symptoms**: `docker-compose ps` shows services as "Exited" or "Restarting"

**Solutions**:

```bash
# Check logs for specific service
docker-compose logs backend
docker-compose logs postgres

# Common fixes:

# 1. Port already in use
# Stop conflicting services or change ports in docker-compose.yml

# 2. Insufficient memory
# Increase Docker memory allocation in Docker Desktop settings

# 3. Permission issues (Linux)
sudo chown -R $USER:$USER .

# 4. Corrupted containers
docker-compose down -v
docker-compose up -d
```

---

### Issue 2: Frontend Shows "Cannot Connect to Backend"

**Symptoms**: Frontend loads but shows connection error

**Solutions**:

```bash
# 1. Check backend is running
docker-compose ps backend
docker-compose logs backend

# 2. Verify backend health
curl http://localhost:8000/health

# 3. Check environment variables
docker exec rag-backend env | grep BACKEND_URL

# 4. Restart frontend
docker-compose restart frontend
```

---

### Issue 3: Database Connection Errors

**Symptoms**: Backend logs show "could not connect to database"

**Solutions**:

```bash
# 1. Check PostgreSQL is running
docker-compose ps postgres
docker-compose logs postgres

# 2. Verify database exists
docker exec rag-postgres psql -U postgres -l | grep ragchatbot

# 3. Test connection
docker exec rag-postgres psql -U postgres -d ragchatbot -c "SELECT 1;"

# 4. Reinitialize database
docker-compose restart postgres
sleep 10
./scripts/setup/setup-database-complete.sh --skip-confirmation
```

---

### Issue 4: "No module named 'app'" or Import Errors

**Symptoms**: Backend container crashes with Python import errors

**Solutions**:

```bash
# 1. Rebuild backend image
docker-compose build backend --no-cache

# 2. Check requirements.txt
docker exec rag-backend pip list

# 3. Install missing dependencies
docker-compose down
docker-compose build backend
docker-compose up -d
```

---

### Issue 5: Frontend Build Errors

**Symptoms**: Frontend container shows build errors

**Solutions**:

```bash
# 1. Clear Next.js cache
docker-compose exec frontend rm -rf .next

# 2. Rebuild frontend
docker-compose build frontend --no-cache

# 3. Check Node.js version
docker-compose exec frontend node --version

# 4. Clean install
docker-compose down
rm -rf frontend/node_modules frontend/.next
docker-compose build frontend
docker-compose up -d
```

---

### Issue 6: "Out of Memory" Errors

**Symptoms**: Containers crash or services become unresponsive

**Solutions**:

1. **Increase Docker Memory** (Docker Desktop):
   - Open Docker Desktop Settings
   - Go to Resources
   - Increase Memory to at least 8 GB
   - Click "Apply & Restart"

2. **Reduce Service Load**:
   ```bash
   # Stop optional services
   docker-compose stop ollama
   ```

3. **Monitor Memory Usage**:
   ```bash
   docker stats
   ```

---

### Issue 7: API Keys Not Working

**Symptoms**: LLM requests fail with authentication errors

**Solutions**:

```bash
# 1. Verify API key in .env
cat .env | grep OPENAI_API_KEY

# 2. Check environment variables in container
docker exec rag-backend env | grep OPENAI_API_KEY

# 3. Restart backend to reload .env
docker-compose restart backend

# 4. Test API key manually
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer sk-proj-your-key-here"
```

---

### Issue 8: Embeddings Not Generated

**Symptoms**: Documents upload but chunks have no embeddings

**Solutions**:

```bash
# 1. Check embedding service logs
docker-compose logs backend | grep embedding

# 2. Verify embedding model
docker exec rag-backend python3 -c "
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
print('Model loaded successfully')
"

# 3. Check database chunks
docker exec rag-postgres psql -U postgres -d ragchatbot -c "
SELECT COUNT(*) FROM document_chunks WHERE embedding IS NOT NULL;
"

# 4. Reprocess documents
# Delete and re-upload documents
```

---

## Next Steps

### Recommended Actions After Installation

1. **Change Admin Password** ✓ (Critical!)
2. **Create Additional Users**:
   - Go to Admin Panel → User Management
   - Create users with appropriate roles

3. **Configure Organization**:
   - Set up your departments and teams
   - Assign users to departments

4. **Upload Sample Documents**:
   - Test with a few documents
   - Verify processing and querying works

5. **Configure LLM Preferences**:
   - Go to Settings → Model Configuration
   - Set default models and parameters

6. **Set Up Backup Strategy**:
   ```bash
   # Create backup script
   cat > backup.sh << 'EOF'
   #!/bin/bash
   DATE=$(date +%Y%m%d_%H%M%S)
   docker exec rag-postgres pg_dump -U postgres ragchatbot > backups/db_$DATE.sql
   docker exec rag-backend tar -czf - /app/data > backups/files_$DATE.tar.gz
   EOF
   chmod +x backup.sh
   ```

7. **Enable Monitoring** (Optional):
   - Set up Grafana dashboards
   - Configure alerts

8. **Review Security Settings**:
   - Enable HTTPS (production)
   - Configure CORS properly
   - Review RBAC permissions

---

## Advanced Configuration

### Enable Ollama for Local LLM Inference

```bash
# 1. Uncomment Ollama service in docker-compose.yml

# 2. Start Ollama
docker-compose up -d ollama

# 3. Pull a model
docker exec ollama ollama pull mistral

# 4. Test
curl http://localhost:11434/api/generate -d '{
  "model": "mistral",
  "prompt": "Hello, how are you?"
}'
```

### Configure Email Notifications

Add to `.env`:
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=noreply@your-domain.com
```

### Enable SSL/TLS (Production)

1. Obtain SSL certificates (Let's Encrypt recommended)
2. Update `docker-compose.yml` with certificate paths
3. Configure Nginx reverse proxy
4. Update `BACKEND_URL` and `FRONTEND_URL` to use HTTPS

---

## Useful Commands

### Daily Operations

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Restart a service
docker-compose restart backend

# View logs
docker-compose logs -f backend

# Check service status
docker-compose ps

# Open backend shell
docker-compose exec backend bash

# Open database shell
docker exec -it rag-postgres psql -U postgres -d ragchatbot
```

### Maintenance

```bash
# Backup database
docker exec rag-postgres pg_dump -U postgres ragchatbot > backup.sql

# Restore database
docker exec -i rag-postgres psql -U postgres ragchatbot < backup.sql

# Clean up Docker
docker system prune -a

# Update images
docker-compose pull
docker-compose up -d
```

---

## Getting Help

### Documentation

- **Complete Setup Guide**: `docs/setup/DATABASE_SETUP_GUIDE.md`
- **Quick Reference**: `docs/setup/DATABASE_QUICK_REFERENCE.md`
- **API Documentation**: http://localhost:8000/api/docs
- **Architecture Guide**: `CLAUDE.md`

### Diagnostic Tools

```bash
# Run health checks
./scripts/maintenance/validate-services.sh

# Diagnose backend issues
./scripts/debugging/diagnose-backend.sh

# Check database
./scripts/debugging/diagnose-documents.sh
```

### Common Issues

Check the [Troubleshooting](#troubleshooting) section above for solutions to common problems.

---

## Success Checklist

After completing installation, verify:

- [ ] All Docker containers are running (`docker-compose ps`)
- [ ] Backend health check passes (`curl http://localhost:8000/health`)
- [ ] Frontend is accessible (http://localhost:3001)
- [ ] Can log in with default credentials
- [ ] Admin password has been changed
- [ ] Can upload a test document
- [ ] Can query the document and get responses
- [ ] Database has 90+ tables
- [ ] MinIO console is accessible
- [ ] API documentation is accessible

---

## Installation Complete! 🎉

You now have a fully functional Enterprise RAG Chatbot installation!

**What You Can Do Now**:
1. Upload documents (PDF, DOCX, TXT, JSON)
2. Scrape web content
3. Ask questions about your documents
4. Extract structured data
5. View analytics and metrics
6. Manage users and permissions

**Next Steps**:
- Explore the UI features
- Read the user guides in `docs/guides/`
- Set up your organization structure
- Invite team members

**Need Help?**
- Check documentation in `docs/`
- Run diagnostic scripts in `scripts/debugging/`
- Review logs: `docker-compose logs -f`

---

**Installation Guide Version**: 1.0
**Last Updated**: 2026-01-05
**Maintainer**: Enterprise RAG Team

**Estimated Reading Time**: 15 minutes
**Estimated Installation Time**: 30-45 minutes
