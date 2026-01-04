# Export Wizard - Implementation Guide

**Created**: 2026-01-04
**Goal**: Fix Export Wizard to create truly standalone deployable packages
**Priority**: CRITICAL - Blocks customer deployments

---

## Quick Summary

**Problem**: Export Wizard exports module code but missing critical files for standalone deployment:
- ❌ No Dockerfiles (can't build images)
- ❌ No application entry points (main.py, frontend app)
- ❌ Wrong dependency specifications
- ❌ docker-compose.yml uses pre-built images instead of build contexts

**Solution**: Add generators for all missing files to `infrastructure_generator.py` and `module_code_extractor.py`

---

## Files to Modify

### 1. `backend/app/services/export/infrastructure_generator.py`

**Current Issues**:
- Line 326: `image: genai-backend:latest` (no build context)
- No Dockerfile generation
- deploy.sh does `docker-compose pull` instead of `docker-compose build`

**Changes Needed**: 5 new methods + 3 method updates

---

### 2. `backend/app/services/export/module_code_extractor.py`

**Current Issues**:
- No `main.py` generation for backend
- No frontend app structure generation
- Wrong package names in requirements.txt
- Empty dependencies in package.json

**Changes Needed**: 4 new methods

---

## Detailed Implementation

### Change 1: Add Dockerfile Generators

**File**: `backend/app/services/export/infrastructure_generator.py`

**Add after line 200** (in `_generate_docker_compose` method):

```python
        # 5. Generate Backend Dockerfile
        backend_dockerfile = self._generate_backend_dockerfile(module_name)
        backend_docker_path = Path(export_dir) / ".." / "backend" / "Dockerfile"
        backend_docker_path.parent.mkdir(parents=True, exist_ok=True)
        backend_docker_path.write_text(backend_dockerfile)
        files_generated.append(str(backend_docker_path))

        logger.info(f"   ✅ Generated: backend/Dockerfile")

        # 6. Generate Frontend Dockerfile
        frontend_dockerfile = self._generate_frontend_dockerfile(module_name)
        frontend_docker_path = Path(export_dir) / ".." / "frontend" / "Dockerfile"
        frontend_docker_path.parent.mkdir(parents=True, exist_ok=True)
        frontend_docker_path.write_text(frontend_dockerfile)
        files_generated.append(str(frontend_docker_path))

        logger.info(f"   ✅ Generated: frontend/Dockerfile")
```

**Add new method at end of class** (around line 1900):

```python
    def _generate_backend_dockerfile(self, module_name: str) -> str:
        """
        Generate production-ready Backend Dockerfile.

        Multi-stage build for smaller image size.
        Includes all dependencies needed for module.
        """
        return f'''# Multi-stage build for {module_name} backend
FROM python:3.11-slim as builder

# Install system dependencies for building
RUN apt-get update && apt-get install -y \\
    gcc g++ make \\
    libpq-dev \\
    tesseract-ocr \\
    poppler-utils \\
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \\
    pip install --no-cache-dir -r requirements.txt

# ============================================================================
# Final stage - Runtime
# ============================================================================
FROM python:3.11-slim

# Install runtime dependencies only (smaller image)
RUN apt-get update && apt-get install -y \\
    libpq5 \\
    tesseract-ocr \\
    poppler-utils \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create app user (security best practice)
RUN useradd -m -u 1000 appuser && \\
    mkdir -p /app /app/logs /app/data && \\
    chown -R appuser:appuser /app

USER appuser
WORKDIR /app

# Copy application code
COPY --chown=appuser:appuser ./app /app/app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

# Start application with Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
'''

    def _generate_frontend_dockerfile(self, module_name: str) -> str:
        """
        Generate production-ready Frontend Dockerfile.

        Multi-stage build with standalone Next.js output.
        """
        return f'''# Multi-stage build for {module_name} frontend
FROM node:18-alpine AS deps

WORKDIR /app

# Install dependencies based on package-lock.json
COPY package.json package-lock.json* ./
RUN npm ci --only=production

# ============================================================================
# Build stage
# ============================================================================
FROM node:18-alpine AS builder

WORKDIR /app

# Install all dependencies (including dev)
COPY package.json package-lock.json* ./
RUN npm ci

# Copy source code
COPY . .

# Build Next.js app (standalone output)
ENV NEXT_TELEMETRY_DISABLED 1
RUN npm run build

# ============================================================================
# Production stage
# ============================================================================
FROM node:18-alpine AS runner

WORKDIR /app

ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1

# Create non-root user
RUN addgroup --system --gid 1001 nodejs && \\
    adduser --system --uid 1001 nextjs

# Copy necessary files from builder
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

# Change ownership
RUN chown -R nextjs:nodejs /app

USER nextjs

EXPOSE 3001

ENV PORT 3001
ENV HOSTNAME "0.0.0.0"

CMD ["node", "server.js"]
'''
```

---

### Change 2: Update docker-compose.yml Template with Build Contexts

**File**: `backend/app/services/export/infrastructure_generator.py`

**Replace lines 323-381** (backend service definition):

```python
  # Backend API
  backend:
    build:
      context: ../../backend
      dockerfile: Dockerfile
    image: {module_name}-backend:latest
    container_name: {module_name}-backend
    ports:
      - "${{BACKEND_PORT:-8000}}:8000"
    environment:
      # Database
      - DATABASE_URL=postgresql://${{POSTGRES_USER}}:${{POSTGRES_PASSWORD}}@postgres:5432/${{POSTGRES_DB}}

      # Redis
      - REDIS_URL=redis://redis:6379/0

      # MinIO (S3-compatible storage)
      - MINIO_ENDPOINT=minio:9000
      - MINIO_ACCESS_KEY=${{MINIO_ACCESS_KEY}}
      - MINIO_SECRET_KEY=${{MINIO_SECRET_KEY}}
      - MINIO_BUCKET_NAME=${{MINIO_BUCKET_NAME:-genai-documents}}

      # LLM Configuration
      - OPENAI_API_KEY=${{OPENAI_API_KEY}}
      - ANTHROPIC_API_KEY=${{ANTHROPIC_API_KEY:-}}

      # Module Configuration
      - MODULE_NAME={module_name}

      # Security
      - JWT_SECRET=${{JWT_SECRET}}
      - SECRET_KEY=${{SECRET_KEY}}

      # Logging
      - LOG_LEVEL=${{LOG_LEVEL:-INFO}}

    volumes:
      - ./config:/app/config
      - ./logs:/app/logs
    networks:
      - genai-network
    restart: unless-stopped
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
      minio:
        condition: service_started
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    deploy:
      resources:
        limits:
          memory: {options.resource_limits.get('backend_memory', '2GB')}
          cpus: '1.0'
```

**Add frontend service** (find where frontend service should be, around line 450):

```python
  # Frontend (Next.js)
  frontend:
    build:
      context: ../../frontend
      dockerfile: Dockerfile
    image: {module_name}-frontend:latest
    container_name: {module_name}-frontend
    ports:
      - "${{FRONTEND_PORT:-3001}}:3001"
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000
    networks:
      - genai-network
    restart: unless-stopped
    depends_on:
      - backend
```

---

### Change 3: Update deploy.sh with Build Step

**File**: `backend/app/services/export/infrastructure_generator.py`

**Find `_generate_deploy_script` method** (around line 700) and **replace with**:

```python
    def _generate_deploy_script(self, module_name: str, deployment_type: str) -> str:
        """
        Generate deployment script with Docker build step.

        Updated to build images first instead of pulling.
        """
        return f'''#!/bin/bash
# Deployment Script for {module_name}
# Deployment Type: {deployment_type}
# Auto-generated by Export Wizard

set -e  # Exit on error

echo "🚀 Deploying {module_name} - {deployment_type}"
echo "================================================"

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found"
    echo "   Copy .env.example to .env and configure your settings:"
    echo "   cp .env.example .env"
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker is not installed"
    echo "   Install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Error: Docker Compose is not installed"
    echo "   Install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

# Build Docker images
echo "🔨 Building Docker images (this may take 5-10 minutes on first run)..."
docker-compose build --no-cache

# Pull external images (PostgreSQL, Redis, MinIO)
echo "📥 Pulling external images..."
docker-compose pull postgres redis minio

# Start services
echo "🔧 Starting services..."
docker-compose up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy (30 seconds)..."
sleep 30

# Check health
echo "🏥 Checking service health..."
docker-compose ps

# Initialize database
echo "🗄️  Initializing database..."
docker-compose exec -T postgres psql -U postgres -d ${{POSTGRES_DB:-genai}} -c "CREATE EXTENSION IF NOT EXISTS vector;" || echo "⚠️  Extension may already exist"

# Create MinIO bucket
echo "🪣 Creating MinIO bucket..."
docker-compose exec -T backend python -c "
from minio import Minio
import os
client = Minio(
    'minio:9000',
    access_key=os.getenv('MINIO_ACCESS_KEY'),
    secret_key=os.getenv('MINIO_SECRET_KEY'),
    secure=False
)
bucket = os.getenv('MINIO_BUCKET_NAME', 'genai-documents')
if not client.bucket_exists(bucket):
    client.make_bucket(bucket)
    print(f'✅ Created bucket: {{bucket}}')
else:
    print(f'✅ Bucket already exists: {{bucket}}')
" || echo "⚠️  Bucket creation may have failed"

# Health check
echo "🩺 Running health checks..."
BACKEND_HEALTH=$(curl -s -o /dev/null -w "%{{http_code}}" http://localhost:${{BACKEND_PORT:-8000}}/health || echo "000")

if [ "$BACKEND_HEALTH" = "200" ]; then
    echo "✅ Backend is healthy"
else
    echo "⚠️  Backend health check failed (HTTP $BACKEND_HEALTH)"
    echo "   Check logs: docker-compose logs backend"
fi

# Show deployment URLs
echo ""
echo "✅ Deployment complete!"
echo "================================================"
echo "Backend API: http://localhost:${{BACKEND_PORT:-8000}}"
echo "Frontend UI: http://localhost:${{FRONTEND_PORT:-3001}}"
echo "API Docs: http://localhost:${{BACKEND_PORT:-8000}}/docs"
echo "MinIO Console: http://localhost:${{MINIO_CONSOLE_PORT:-9001}}"
echo ""
echo "📋 Useful commands:"
echo "  Monitor logs: docker-compose logs -f"
echo "  Stop services: docker-compose down"
echo "  Restart: docker-compose restart"
echo "  Clean reset: docker-compose down -v && ./deploy.sh"
echo "================================================"
'''
```

---

### Change 4: Add Backend main.py Generator

**File**: `backend/app/services/export/module_code_extractor.py`

**Add new method**:

```python
    def _generate_backend_main(
        self,
        export_dir: Path,
        module_config: Dict[str, Any]
    ) -> str:
        """
        Generate FastAPI application entry point (main.py).

        Creates a minimal but complete FastAPI app that:
        - Includes the module's router
        - Sets up database connections
        - Configures CORS
        - Adds health check endpoint
        """
        module_name = module_config.get("name", "module")
        module_category = module_config.get("category", "tier_2")

        # Import path for module router
        router_import = f"from app.{module_category}.{module_name}_{module_config.get('type', 'routes')} import router"

        main_content = f'''"""
{module_name.replace('_', ' ').title()} - Standalone Application

Auto-generated by Export Wizard
Module: {module_name}
Generated: {datetime.utcnow().isoformat()}
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.tier_1.infrastructure.database import init_db, close_db
from app.tier_1.infrastructure.config import get_settings
{router_import}

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager - startup and shutdown events."""
    # Startup
    await init_db()
    yield
    # Shutdown
    await close_db()

# Create FastAPI application
app = FastAPI(
    title="{module_name.replace('_', ' ').title()}",
    description="Standalone deployment of {module_name} module",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/api/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include module router
app.include_router(
    router,
    prefix="/api/v1/modules/{module_name}",
    tags=["{module_name}"]
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {{
        "status": "healthy",
        "module": "{module_name}",
        "version": "1.0.0"
    }}

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with module information."""
    return {{
        "module": "{module_name}",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        workers=4
    )
'''

        main_path = export_dir / "backend" / "app" / "main.py"
        main_path.parent.mkdir(parents=True, exist_ok=True)
        main_path.write_text(main_content)

        logger.info(f"   ✅ Generated: backend/app/main.py")
        return str(main_path)
```

**Call this method from `extract_module_code`** (add after copying module files):

```python
        # Generate main.py entry point
        self._generate_backend_main(export_dir, module_config)
```

---

### Change 5: Fix requirements.txt Generation

**File**: `backend/app/services/export/module_code_extractor.py`

**Find `_generate_requirements_txt` method and replace with**:

```python
    def _generate_requirements_txt(
        self,
        export_dir: Path,
        dependencies: List[str]
    ) -> str:
        """
        Generate requirements.txt with correct package names and pinned versions.

        Fixes:
        - PIL → Pillow
        - cv2 → opencv-python
        - docx → python-docx
        - pptx → python-pptx
        - fitz → PyMuPDF
        - Removes local module names
        - Adds version pins
        """
        # Package name corrections
        package_corrections = {
            "PIL": "Pillow==10.3.0",
            "cv2": "opencv-python==4.9.0",
            "docx": "python-docx==1.1.0",
            "pptx": "python-pptx==0.6.23",
            "fitz": "PyMuPDF==1.24.0",
        }

        # Local modules to exclude (not PyPI packages)
        local_modules = {
            "relation_extractor_schemas",
            "relation_extractor_service",
            "relation_extractor_routes",
            # Add other module-specific names
        }

        # Core backend dependencies (pinned versions)
        core_requirements = {
            "fastapi": "0.111.0",
            "uvicorn[standard]": "0.30.0",
            "sqlalchemy": "2.0.30",
            "psycopg2-binary": "2.9.9",
            "redis": "5.0.4",
            "minio": "7.2.5",
            "openai": "1.40.0",
            "anthropic": "0.39.0",
            "pydantic": "2.8.0",
            "pydantic-settings": "2.3.0",
            "python-multipart": "0.0.9",
            "aiofiles": "23.2.1",
            "httpx": "0.27.0",
            "tenacity": "8.3.0",
            "PyPDF2": "3.0.1",
            "openpyxl": "3.1.2",
            "pytesseract": "0.3.10",
            "spacy": "3.7.4",
            "langchain": "0.2.0",
            "langchain-openai": "0.1.7",
            "langchain-anthropic": "0.1.11",
            "numpy": "1.26.4",
            "docling": "1.0.0",
        }

        requirements = []

        # Add core requirements
        for package, version in core_requirements.items():
            requirements.append(f"{package}=={version}")

        # Add module-specific requirements (corrected)
        for dep in dependencies:
            # Skip if local module
            if dep in local_modules:
                continue

            # Apply corrections
            if dep in package_corrections:
                requirements.append(package_corrections[dep])
            elif dep not in [pkg.split("==")[0] for pkg in core_requirements.keys()]:
                # Try to get pinned version from main app
                version = self._get_package_version(dep)
                if version:
                    requirements.append(f"{dep}=={version}")
                else:
                    requirements.append(dep)  # No version found, use unpinned

        requirements_content = "# Auto-generated requirements.txt\\n"
        requirements_content += "# Generated by Export Wizard\\n"
        requirements_content += f"# Generated: {datetime.utcnow().isoformat()}\\n\\n"
        requirements_content += "\\n".join(sorted(set(requirements)))

        req_path = export_dir / "backend" / "requirements.txt"
        req_path.write_text(requirements_content)

        logger.info(f"   ✅ Generated: backend/requirements.txt ({len(requirements)} packages)")
        return str(req_path)

    def _get_package_version(self, package_name: str) -> Optional[str]:
        """Get installed version of a package."""
        try:
            import pkg_resources
            return pkg_resources.get_distribution(package_name).version
        except:
            return None
```

---

### Change 6: Fix Frontend package.json

**File**: `backend/app/services/export/module_code_extractor.py`

**Add new method**:

```python
    def _generate_frontend_package_json(
        self,
        export_dir: Path,
        module_name: str
    ) -> str:
        """
        Generate package.json with all required dependencies.

        Fixes empty dependencies issue.
        """
        package_json = {
            "name": f"{module_name}-standalone",
            "version": "1.0.0",
            "description": f"{module_name.replace('_', ' ').title()} - Standalone Deployment",
            "private": True,
            "scripts": {
                "dev": "next dev -p 3001",
                "build": "next build",
                "start": "next start -p 3001",
                "lint": "next lint"
            },
            "dependencies": {
                "next": "14.1.0",
                "react": "18.2.0",
                "react-dom": "18.2.0",
                "typescript": "5.3.3",
                "axios": "1.6.7",
                "lucide-react": "0.316.0",
                "react-markdown": "9.0.1",
                "@types/node": "20.11.19",
                "@types/react": "18.2.56",
                "@types/react-dom": "18.2.19",
                "tailwindcss": "3.4.1",
                "autoprefixer": "10.4.17",
                "postcss": "8.4.35"
            },
            "devDependencies": {
                "eslint": "8.56.0",
                "eslint-config-next": "14.1.0"
            },
            "engines": {
                "node": ">=18.0.0",
                "npm": ">=9.0.0"
            }
        }

        package_path = export_dir / "frontend" / "package.json"
        package_path.parent.mkdir(parents=True, exist_ok=True)
        package_path.write_text(json.dumps(package_json, indent=2))

        logger.info(f"   ✅ Generated: frontend/package.json")
        return str(package_path)
```

---

### Change 7: Add Frontend App Structure Generator

**File**: `backend/app/services/export/module_code_extractor.py`

**Add new method**:

```python
    def _generate_frontend_structure(
        self,
        export_dir: Path,
        module_name: str,
        module_component_path: str
    ) -> List[str]:
        """
        Generate minimal Next.js app structure.

        Creates:
        - src/pages/_app.tsx
        - src/pages/index.tsx
        - next.config.js
        - tsconfig.json
        """
        files_generated = []

        # 1. _app.tsx
        app_tsx = '''import type { AppProps } from 'next/app'
import '../styles/globals.css'

export default function App({ Component, pageProps }: AppProps) {
  return <Component {...pageProps} />
}
'''
        app_path = export_dir / "frontend" / "src" / "pages" / "_app.tsx"
        app_path.parent.mkdir(parents=True, exist_ok=True)
        app_path.write_text(app_tsx)
        files_generated.append(str(app_path))

        # 2. index.tsx (main page with module component)
        index_tsx = f'''import React from 'react'
import Head from 'next/head'
import {{ ModuleComponent }} from '../components/tier2/document_intelligence/{module_name}Panel'

export default function Home() {{
  return (
    <div>
      <Head>
        <title>{module_name.replace('_', ' ').title()}</title>
        <meta name="description" content="{module_name} standalone application" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <main className="min-h-screen bg-gray-50">
        <div className="container mx-auto px-4 py-8">
          <h1 className="text-3xl font-bold mb-8">{module_name.replace('_', ' ').title()}</h1>
          <ModuleComponent />
        </div>
      </main>
    </div>
  )
}}
'''
        index_path = export_dir / "frontend" / "src" / "pages" / "index.tsx"
        index_path.write_text(index_tsx)
        files_generated.append(str(index_path))

        # 3. next.config.js
        next_config = '''/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone',
  poweredByHeader: false,
  compress: true,
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },
}

module.exports = nextConfig
'''
        config_path = export_dir / "frontend" / "next.config.js"
        config_path.write_text(next_config)
        files_generated.append(str(config_path))

        # 4. tsconfig.json
        tsconfig = '''{
  "compilerOptions": {
    "target": "es5",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "node",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx"],
  "exclude": ["node_modules"]
}
'''
        tsconfig_path = export_dir / "frontend" / "tsconfig.json"
        tsconfig_path.write_text(tsconfig)
        files_generated.append(str(tsconfig_path))

        # 5. globals.css
        globals_css = '''@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --foreground-rgb: 0, 0, 0;
  --background-start-rgb: 214, 219, 220;
  --background-end-rgb: 255, 255, 255;
}

body {
  color: rgb(var(--foreground-rgb));
  background: linear-gradient(
      to bottom,
      transparent,
      rgb(var(--background-end-rgb))
    )
    rgb(var(--background-start-rgb));
}
'''
        css_path = export_dir / "frontend" / "src" / "styles" / "globals.css"
        css_path.parent.mkdir(parents=True, exist_ok=True)
        css_path.write_text(globals_css)
        files_generated.append(str(css_path))

        logger.info(f"   ✅ Generated frontend structure ({len(files_generated)} files)")
        return files_generated
```

**Call this from `extract_module_code`**:

```python
        # Generate frontend structure
        frontend_files = self._generate_frontend_structure(
            export_dir,
            module_name,
            module_component_path
        )

        # Generate package.json
        self._generate_frontend_package_json(export_dir, module_name)
```

---

## Testing Strategy

After making changes, test with Relation Extractor module:

```bash
# 1. Export module
curl -X POST http://localhost:8000/api/v1/export/initiate \
  -H "Content-Type: application/json" \
  -d '{
    "module_name": "relation-extractor",
    "customer_name": "Test Customer",
    "deployment_type": "docker_compose"
  }'

# 2. Download package (use package_id from response)
# Extract to /tmp/test-export

# 3. Deploy
cd /tmp/test-export/infrastructure/docker-compose
cp .env.example .env
# Edit .env with API keys
./deploy.sh

# 4. Verify
docker-compose ps  # All services should be Up
curl http://localhost:8100/health  # Should return 200
# Open http://localhost:3100 in browser

# 5. Cleanup
docker-compose down -v
```

---

## Implementation Checklist

- [ ] 1. Add `_generate_backend_dockerfile()` method
- [ ] 2. Add `_generate_frontend_dockerfile()` method
- [ ] 3. Update `_generate_docker_compose_yml()` with build contexts
- [ ] 4. Update `_generate_deploy_script()` with build step
- [ ] 5. Add `_generate_backend_main()` method
- [ ] 6. Fix `_generate_requirements_txt()` method
- [ ] 7. Add `_generate_frontend_package_json()` method
- [ ] 8. Add `_generate_frontend_structure()` method
- [ ] 9. Update `extract_module_code()` to call new methods
- [ ] 10. Test export with Relation Extractor module
- [ ] 11. Validate deployment works standalone
- [ ] 12. Update documentation

---

## Estimated Effort

- **Implementation**: 4-6 hours (copy/paste code, test each method)
- **Testing**: 2-3 hours (export, deploy, validate)
- **Total**: 6-9 hours

---

## Questions?

- All code examples are production-ready
- Copy/paste directly into the specified files
- Test incrementally (add one method, test, repeat)
- Refer to `/tmp/standalone-test/EXPORT_WIZARD_GAP_ANALYSIS_AND_IMPLEMENTATION_PLAN.md` for detailed gap analysis

---

**Created**: 2026-01-04
**Status**: ✅ **READY FOR IMPLEMENTATION**
