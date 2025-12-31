# Backend Build Snapshot

**Generated**: 2025-11-25
**Purpose**: Complete snapshot of all dependencies and versions used in backend build for reproducibility

---

## 🐳 Docker Base Image

```dockerfile
FROM mcr.microsoft.com/playwright/python:v1.48.0-jammy
```

### Base Image Details
- **Image**: `mcr.microsoft.com/playwright/python`
- **Tag**: `v1.48.0-jammy`
- **SHA256**: `sha256:6bbd515848db4042068571135979b6ee6d330a794b28e037e3a6ccd7f2abfa26`
- **Base OS**: Ubuntu 22.04 LTS (Jammy Jellyfish)
- **Python Version**: 3.10.x (included in Playwright image)
- **Pre-installed Browsers**:
  - Chromium 1140 (at `/ms-playwright/`)
  - Firefox 1465
  - WebKit 2083

---

## 🐍 Python Version

```bash
Python 3.10.x (from Playwright base image)
pip 25.3 (upgraded during build)
```

---

## 📦 System Packages (apt-get)

Installed via `apt-get` on Ubuntu 22.04:

```bash
libpq-dev==14.19-0ubuntu0.22.04.1    # PostgreSQL development libraries
libpq5==14.19-0ubuntu0.22.04.1       # PostgreSQL client library
libssl-dev==3.0.2-0ubuntu1.20        # OpenSSL development libraries
libssl3==3.0.2-0ubuntu1.20           # OpenSSL library
```

---

## 🔧 Python Dependencies (pip)

### Core Web Framework
```
fastapi==0.111.0
uvicorn[standard]==0.30.0
python-multipart==0.0.9
pydantic==2.8.2
pydantic-settings==2.3.4
starlette==0.37.2
typing-extensions==4.15.0
fastapi-cli==0.0.16
```

### GraphQL
```
strawberry-graphql[fastapi]==0.235.0
graphql-core==3.2.3
```

### Database & Async
```
psycopg2-binary==2.9.9
asyncpg==0.29.0
sqlalchemy==2.0.25
pgvector==0.2.4
alembic==1.13.1
greenlet==3.2.4 / 3.1.1
async-timeout==5.0.1 / 4.0.3
```

### Object Storage & Caching
```
minio==7.2.3
redis==5.0.1
hiredis==2.3.2
```

### AI & LLM
```
openai==1.40.0
anthropic==0.39.0
sentence-transformers==2.3.1
torch==2.9.1
transformers==4.57.2
tiktoken==0.12.0
```

### LangChain Ecosystem
```
langchain==0.2.16
langchain-core==0.2.43
langchain-community==0.2.16
langchain-openai==0.1.22
langchain-text-splitters==0.2.4
langgraph==0.2.16
langgraph-checkpoint==1.0.12
langsmith==0.1.147
```

### Document Processing
```
docling==2.62.0
docling-core==2.52.0
docling-parse==4.7.1
docling-ibm-models==3.10.2
pypdf2==3.0.1
python-docx==1.1.2
python-pptx==1.0.2
openpyxl==3.1.5
beautifulsoup4==4.12.3
lxml==5.1.0
pypdfium2==4.30.0
```

### Computer Vision & OCR
```
numpy==1.26.4
opencv-python==4.9.0.80
Pillow==10.2.0
pytesseract==0.3.13
rapidocr==3.4.2
```

### Web Scraping & Automation
```
playwright==1.48.0
httpx==0.27.0
httpcore==1.0.9
aiohttp==3.13.2
trafilatura==1.6.3
robotexclusionrulesparser==1.7.1
urllib3==2.1.0
```

### Data Processing
```
pandas==2.3.3
pyarrow==22.0.0
xlsxwriter==3.2.9
fastexcel==0.18.0
jsonpath-ng==1.6.1
```

### NLP & Text Processing
```
sacremoses==0.1.1
sentencepiece==0.1.99
```

### Workflow Orchestration
```
prefect==3.0.0
```

### Observability
```
opentelemetry-api==1.25.0
opentelemetry-sdk==1.25.0
opentelemetry-instrumentation-fastapi==0.46b0
opentelemetry-exporter-otlp==1.25.0
prometheus-client==0.20.0
```

### Security & Authentication
```
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
argon2-cffi==25.1.0
pycryptodome==3.23.0
```

### Utilities
```
python-dotenv==1.0.0
tenacity==8.2.3
aiofiles==23.2.1
pyyaml==6.0.1
python-dateutil==2.8.2
click==8.3.1
tqdm==4.67.1
certifi==2025.11.12
```

### HTTP & Networking
```
h11==0.16.0
anyio==4.11.0
sniffio==1.3.1
idna==3.11
```

### Evaluation & Testing
```
ragas==0.1.7
deepeval==0.21.0
rouge-score==0.1.2
nltk==3.8.1
bert-score==0.3.13
detoxify==0.5.2
fairlearn==0.9.0
```

### ML & Scientific Computing
```
scikit-learn==1.7.2
scipy==1.15.3
huggingface-hub==1.1.5 / 0.36.0
accelerate==1.12.0
```

### Template & Data Handling
```
jinja2==3.1.6
ujson==5.11.0
orjson==3.11.4
email_validator==2.3.0
annotated-types==0.7.0
pydantic-core==2.20.1
```

### Other Dependencies
```
requests==2.32.5
dataclasses-json==0.6.7
six==1.17.0
Mako==1.3.10
distro==1.9.0
jiter==0.12.0
soupsieve==2.8
pyee==12.0.0
courlan==1.3.2
htmldate==1.9.4
filetype==1.2.0
rtree==1.4.1
typer==0.19.2
marko==2.2.1
pluggy==1.6.0
pylatexenc==2.10
polyfactory==3.0.0
```

---

## 🔍 How to Reproduce This Build

### Method 1: Using Exact Image SHA
```bash
# Use the exact base image SHA
docker build --build-arg BASE_IMAGE=mcr.microsoft.com/playwright/python@sha256:6bbd515848db4042068571135979b6ee6d330a794b28e037e3a6ccd7f2abfa26 -t rag-backend:reproducible .
```

### Method 2: Using This Snapshot
```bash
# 1. Verify Dockerfile matches:
FROM mcr.microsoft.com/playwright/python:v1.48.0-jammy

# 2. Verify requirements.txt matches the versions listed above

# 3. Build with no cache
docker-compose build --no-cache backend
```

### Method 3: Generate Fresh Snapshot (After Build Completes)
```bash
# Once backend container is running, generate pip freeze output:
docker-compose exec backend pip freeze > backend/requirements.freeze.txt
```

---

## 📝 Build Command Used

```bash
docker-compose build --no-cache backend
```

**Dockerfile Location**: `backend/Dockerfile`
**Requirements Location**: `backend/requirements.txt`

---

## 🎯 Key Notes for Reproducibility

1. **Base Image Pinning**: Always use the specific SHA256 digest to ensure exact base image
2. **Ubuntu Version**: Jammy (22.04) - no t64 transition issues
3. **Playwright Browsers**: Pre-installed at `/ms-playwright/` - DO NOT run `playwright install`
4. **Python Version**: Fixed by base image (3.10.x)
5. **System Packages**: Ubuntu package versions may change; consider pinning if critical
6. **pip Version**: Upgraded to 25.3 during build
7. **No Cache Flag**: Used `--no-cache` to ensure fresh dependency downloads

---

## 🚨 Known Compatibility Issues (Resolved)

- ❌ Ubuntu 24.04 (Noble) has t64 library transition issues - **AVOID**
- ✅ Ubuntu 22.04 (Jammy) is stable and recommended
- ✅ Playwright v1.48.0 is fully compatible with Jammy
- ✅ All Python dependencies are compatible with Pydantic 2.x and Prefect 3.0

---

## 📊 Build Statistics

- **Total Python Packages**: ~180+ packages (including dependencies)
- **Build Time**: ~5-15 minutes (no cache)
- **Final Image Size**: ~3-4 GB (with Playwright browsers)
- **Base Image Size**: ~2.5 GB

---

## 🔄 Update History

| Date | Change | Reason |
|------|--------|--------|
| 2025-11-25 | Initial snapshot created | Ensure reproducible builds |
| 2025-11-25 | Tool tracking fix applied | Fix frontend tool display |

---

**To update this snapshot after dependency changes:**
```bash
# After successful build:
docker-compose exec backend pip freeze > backend/requirements.freeze.txt
# Then manually update this document with new versions
```
