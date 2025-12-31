# Build Snapshots - Quick Reference

**Purpose**: This directory contains comprehensive build snapshots for reproducible builds of the Enterprise RAG Chatbot application.

---

## 📄 Available Snapshots

### 1. Backend Build Snapshot
**File**: `BUILD_SNAPSHOT_BACKEND.md`

Complete snapshot including:
- Docker base image (Playwright Python v1.48.0-jammy with SHA256)
- Python version (3.10.x)
- All 180+ pip packages with exact versions
- System packages (libpq-dev, libssl-dev, etc.)
- Build commands and reproduction steps

**Use this when:**
- Reproducing backend builds from scratch
- Debugging dependency conflicts
- Upgrading Python packages
- Setting up new development environments

### 2. Frontend Build Snapshot
**File**: `BUILD_SNAPSHOT_FRONTEND.md`

Complete snapshot including:
- Docker base image (Node 20 Alpine)
- Node.js and npm versions
- All npm packages (production + dev dependencies)
- Multi-stage build breakdown
- Package-lock.json importance

**Use this when:**
- Reproducing frontend builds
- Debugging npm dependency issues
- Upgrading Node packages
- Understanding the build pipeline

---

## 🎯 Why Build Snapshots Matter

### Problem: "It Works on My Machine"
Without version pinning:
- Base images with `latest` tag change over time
- Dependencies auto-upgrade to incompatible versions
- Builds that worked yesterday fail today
- No way to reproduce exact production environment

### Solution: Comprehensive Snapshots
With these snapshots:
- ✅ Exact base image versions (with SHA256 hashes)
- ✅ Every dependency version documented
- ✅ System package versions captured
- ✅ Build commands preserved
- ✅ Known issues documented
- ✅ Can reproduce builds months/years later

---

## 🔧 How to Use These Snapshots

### For Reproducible Builds

#### Backend
```bash
# Use exact base image SHA from snapshot
docker build \
  --build-arg BASE_IMAGE=mcr.microsoft.com/playwright/python@sha256:6bbd515848db4042068571135979b6ee6d330a794b28e037e3a6ccd7f2abfa26 \
  -t rag-backend:reproducible \
  ./backend

# Or use regular build (relies on pinned versions in requirements.txt)
docker-compose build --no-cache backend
```

#### Frontend
```bash
# npm ci uses exact versions from package-lock.json
cd frontend
npm ci  # NOT npm install
npm run build

# Or use Docker
docker-compose build --no-cache frontend
```

### For Debugging Dependency Issues

1. **Check Current Versions**
   ```bash
   # Backend
   docker-compose exec backend pip list

   # Frontend
   docker-compose exec frontend npm list
   ```

2. **Compare Against Snapshot**
   - Open `BUILD_SNAPSHOT_BACKEND.md` or `BUILD_SNAPSHOT_FRONTEND.md`
   - Find discrepancies
   - Identify which version changed

3. **Rollback or Fix**
   ```bash
   # Backend - pin specific version
   pip install package-name==X.Y.Z

   # Frontend - use exact package-lock.json
   npm ci
   ```

### For New Environments

1. Read the appropriate snapshot document
2. Verify your environment matches:
   - Docker version
   - Base OS (if not using Docker)
   - Network access to package repositories
3. Follow "How to Reproduce" section
4. Run tests to verify build

---

## 🔄 Keeping Snapshots Up to Date

### When to Update Snapshots

Update these files when you:
- Upgrade major dependencies (Python, Node.js, frameworks)
- Change base Docker images
- Resolve compatibility issues
- Make significant architectural changes

### How to Update

#### Backend Snapshot
```bash
# After successful build:
docker-compose exec backend pip freeze > backend/requirements.freeze.txt
docker-compose exec backend python --version
docker-compose exec backend uname -a

# Then manually update BUILD_SNAPSHOT_BACKEND.md with:
# - New package versions
# - Date of update
# - Reason for changes
# - Any compatibility notes
```

#### Frontend Snapshot
```bash
# After successful build:
docker-compose exec frontend npm list --all > frontend/npm-list-snapshot.txt
docker-compose exec frontend npm list --json > frontend/npm-list-snapshot.json
docker-compose exec frontend node --version
docker-compose exec frontend npm --version

# Then manually update BUILD_SNAPSHOT_FRONTEND.md with:
# - New package versions
# - Date of update
# - Reason for changes
# - Breaking changes
```

---

## 📊 Snapshot Comparison Tool

Use this script to quickly compare current environment against snapshot:

```bash
#!/bin/bash
# compare-with-snapshot.sh

echo "=== Backend Comparison ==="
echo "Current Python packages:"
docker-compose exec backend pip list | head -20

echo -e "\n=== Frontend Comparison ==="
echo "Current npm packages:"
docker-compose exec frontend npm list --depth=0

echo -e "\n📄 Full snapshots available in:"
echo "- BUILD_SNAPSHOT_BACKEND.md"
echo "- BUILD_SNAPSHOT_FRONTEND.md"
```

---

## 🚨 Critical Files for Reproducibility

### Backend
- ✅ `backend/requirements.txt` - **MUST commit**
- ✅ `backend/Dockerfile` - **MUST commit**
- ✅ `BUILD_SNAPSHOT_BACKEND.md` - **MUST commit**
- ⚠️ `backend/requirements.freeze.txt` - Generated, optional
- ❌ `backend/.env` - **NEVER commit** (contains secrets)

### Frontend
- ✅ `frontend/package.json` - **MUST commit**
- ✅ `frontend/package-lock.json` - **CRITICAL - MUST commit**
- ✅ `frontend/Dockerfile` - **MUST commit**
- ✅ `BUILD_SNAPSHOT_FRONTEND.md` - **MUST commit**
- ⚠️ `frontend/npm-list-snapshot.txt` - Generated, optional
- ❌ `frontend/.env.local` - **NEVER commit** (may contain API keys)

**Key Point**: `package-lock.json` is MORE important than `package.json` for reproducibility!

---

## 🏗️ Build Architecture Overview

```
┌─────────────────────────────────────────┐
│  BUILD SNAPSHOT DOCUMENTS               │
│  (This directory)                       │
└──────────────┬──────────────────────────┘
               │
               ├─────────────────────────────┬──────────────────────────┐
               │                             │                          │
               ▼                             ▼                          ▼
┌──────────────────────┐    ┌────────────────────────┐   ┌──────────────────────┐
│  BACKEND             │    │  FRONTEND              │   │  INFRASTRUCTURE      │
│                      │    │                        │   │                      │
│  Base: Playwright    │    │  Base: Node 20 Alpine  │   │  Docker Compose      │
│  Python v1.48.0      │    │                        │   │  Kubernetes          │
│  Ubuntu 22.04        │    │  Multi-stage build     │   │  CI/CD               │
│                      │    │                        │   │                      │
│  180+ Python pkgs    │    │  1000+ npm packages    │   │  Orchestration       │
│  requirements.txt    │    │  package-lock.json     │   │  configs             │
└──────────────────────┘    └────────────────────────┘   └──────────────────────┘
```

---

## 📚 Additional Documentation

For more context, see:
- `README.md` - Main project documentation
- `CLAUDE.md` - AI assistant development guide
- `CONTRIBUTING.md` - Contribution guidelines
- `docs/architecture/DEPLOYMENT.md` - Deployment guide
- `docs/setup/` - Setup guides for various environments

---

## 🔐 Security Notes

1. **Never Commit Secrets**: Snapshots document versions, NOT secrets
2. **Audit Dependencies**: Run security audits regularly
   ```bash
   # Backend
   docker-compose exec backend pip-audit

   # Frontend
   docker-compose exec frontend npm audit
   ```
3. **Update Vulnerabilities**: When security issues found, update and refresh snapshot
4. **Base Image Security**: Monitor security advisories for:
   - Playwright images
   - Node.js images
   - Ubuntu/Alpine base images

---

## ❓ FAQ

### Q: Do I need to update snapshots every time I change a dependency?
**A:** Only for major changes. Minor/patch updates can be noted in commit messages.

### Q: What if the exact versions in the snapshot are no longer available?
**A:** This is rare but possible. Use the closest compatible versions and document the change.

### Q: Can I use these snapshots for non-Docker deployments?
**A:** Yes! The package versions apply regardless of deployment method.

### Q: How do I know if my build matches the snapshot?
**A:** Run the comparison commands above and check for version mismatches.

### Q: Should I commit the generated `.freeze` or snapshot files?
**A:** Optional but recommended for maximum reproducibility.

---

## 📝 Version History

| Date | Backend | Frontend | Notes |
|------|---------|----------|-------|
| 2025-11-25 | v1.0 | v1.0 | Initial snapshots created |
| 2025-11-25 | v1.0.1 | v1.0.1 | Tool tracking fix applied |

---

**Last Updated**: 2025-11-25
**Maintained By**: Development Team
**Review Frequency**: After major dependency updates or quarterly
