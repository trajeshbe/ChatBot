# Standalone Deployment Test - Critical Findings

**Date**: 2026-01-04
**Package Tested**: `relation-extractor_export_de5f2a65-acce-446f-ab93-67a5c843e331.tar.gz`
**Status**: 🔴 **CRITICAL BUGS FOUND** - Deployment blocked

---

## Executive Summary

Tested standalone deployment of exported Relation Extractor package. Found **3 critical bugs** that prevent deployment and require **4 manual interventions**.

**Result**: Package is **NOT plug-and-play** ready. Requires immediate fixes to Phase 2 code.

---

## 🔴 CRITICAL BUGS (Blockers)

### Bug #1: Missing package-lock.json ❌
**Severity**: CRITICAL
**Impact**: Frontend build fails immediately

**Error**:
```
npm error The `npm ci` command can only install with an existing package-lock.json
```

**Root Cause**: Export Wizard does not copy `package-lock.json` from main frontend

**Fix Required in Export Wizard**:
```python
# In module_code_extractor.py _generate_frontend_structure()
# Add after copying package.json:

# Copy package-lock.json if it exists
source_lock = Path(self.config.frontend_dir) / "package-lock.json"
if source_lock.exists():
    dest_lock = frontend_dir / "package-lock.json"
    shutil.copy2(source_lock, dest_lock)
    logger.info(f"   ✅ Copied package-lock.json")
```

**Alternative**: Update Dockerfile to use `npm install` instead of `npm ci`

---

### Bug #2: Double Braces in next.config.js ❌
**Severity**: CRITICAL
**Impact**: Next.js build fails with syntax error

**Error**:
```
SyntaxError: Unexpected token '{'
```

**Generated Code** (WRONG):
```javascript
const nextConfig = {{    // ❌ Double braces!
  reactStrictMode: true,
  env: {{              // ❌ Double braces!
    API_BASE_URL: process.env.API_BASE_URL,
  }},                  // ❌ Double braces!
}}
```

**Should Be**:
```javascript
const nextConfig = {     // ✅ Single braces
  reactStrictMode: true,
  env: {               // ✅ Single braces
    API_BASE_URL: process.env.API_BASE_URL,
  },                   // ✅ Single braces
}
```

**Root Cause**: Python f-string escaping issue in `module_code_extractor.py`

**Location**: `backend/app/services/export/module_code_extractor.py`, `_generate_frontend_structure()` method

**Fix Required**:
```python
# In _generate_frontend_structure() method, lines ~860-880
# WRONG (current code):
next_config_content = f'''/** @type {{{{import('next').NextConfig}}}} */
const nextConfig = {{{{
  reactStrictMode: true,
  output: 'standalone',
  env: {{{{
    API_BASE_URL: process.env.API_BASE_URL || 'http://localhost:8000',
  }}}},
}}}}'''

# CORRECT (should be):
next_config_content = '''/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone',
  env: {
    API_BASE_URL: process.env.API_BASE_URL || 'http://localhost:8000',
  },
}'''
```

**Impact**: Every exported package has broken next.config.js!

---

### Bug #3: npm ci Requires package-lock.json ❌
**Severity**: HIGH
**Impact**: Frontend Dockerfile fails if package-lock.json missing

**Current Dockerfile**:
```dockerfile
RUN npm ci  # Requires package-lock.json
```

**Fix Options**:
1. Include package-lock.json (recommended)
2. Change to: `RUN npm install --legacy-peer-deps`

**Fix Required in**: `infrastructure_generator.py`, `_generate_frontend_dockerfile()` method

```python
# Option 1: If package-lock.json exists
if has_package_lock:
    dockerfile_content += 'RUN npm ci\n'
else:
    dockerfile_content += 'RUN npm install --legacy-peer-deps\n'

# Option 2: Always use npm install for exported packages
dockerfile_content += 'RUN npm install --legacy-peer-deps\n'
```

---

##  Manual Interventions Required

### 1. Create .env File
**Time**: 5 minutes
**Complexity**: Medium

**Steps**:
1. Copy `.env.example` to `.env`
2. Configure all [REQUIRED] fields:
   - `POSTGRES_PASSWORD`
   - `MINIO_ACCESS_KEY` / `MINIO_SECRET_KEY`
   - `JWT_SECRET` (min 32 chars)
   - `SECRET_KEY` (min 32 chars)
   - `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`
3. Adjust ports if conflicts exist

**Automation Potential**: HIGH - Can pre-configure most values

---

### 2. Update Container Names
**Time**: 2 minutes
**Complexity**: Low

**Issue**: Default names conflict with main app

**Command**:
```bash
sed -i 's/container_name: genai-/container_name: standalone-relext-/g' docker-compose.yml
```

**Automation**: Should use customer/module-specific prefix

---

### 3. Fix Port Conflicts
**Time**: 2 minutes
**Complexity**: Medium

**Conflicts Found**:
- Grafana: 3000 (main app)
- Loki: 3100 (main app)
- Postgres: 5433 (main app)
- Redis: 6380 (main app)
- MinIO: 9000-9001 (main app)
- Prometheus: 9090 (main app)

**Automation**: Need port conflict detection

---

### 4. Fix Generated Code Bugs
**Time**: 5 minutes
**Complexity**: High

**Required Fixes**:
1. Fix next.config.js double braces
2. Change npm ci to npm install
3. Add package-lock.json (or remove npm ci)

**Automation**: Fix Phase 2 code generation

---

## Database Isolation ✅

**Verified**: Standalone package is completely isolated

- ✅ Separate Docker network
- ✅ Separate PostgreSQL container
- ✅ Separate database (`relation_extractor_standalone`)
- ✅ Separate volumes
- ✅ Different external port (5434 vs 5433)

**No risk to main app database.**

---

## Port Allocation Used

| Service | Main App | Standalone | Status |
|---------|----------|------------|--------|
| Backend | 8000 | 8100 | ✅ |
| Frontend | 3001 | 3200 | ✅ |
| Grafana | 3000 | 3002 | ✅ |
| Loki | 3100 | N/A | ✅ |
| Postgres | 5433 | 5434 | ✅ |
| Redis | 6380 | 6381 | ✅ |
| MinIO | 9000-9001 | 9100-9101 | ✅ |
| Prometheus | 9090 | 9091 | ✅ |

---

## Files Modified During Testing

### Created:
1. `.env` - Runtime configuration (based on .env.example)

### Modified:
1. `docker-compose.yml` - Container names, monitoring ports
2. `frontend/Dockerfile` - npm ci → npm install
3. `frontend/next.config.js` - Fixed double braces

---

## Immediate Action Items

### Priority 1: Fix Code Generation Bugs (CRITICAL)

**File**: `backend/app/services/export/module_code_extractor.py`

**Fix #1 - next.config.js double braces** (Line ~860-880):
```python
# Remove f-string, use plain triple quotes
next_config_content = '''/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone',
  env: {
    API_BASE_URL: process.env.API_BASE_URL || 'http://localhost:8000',
  },
}

module.exports = nextConfig
'''
```

**Fix #2 - Copy package-lock.json** (Add after line ~285):
```python
# Copy package-lock.json if it exists
source_package_lock = Path("frontend/package-lock.json")
if source_package_lock.exists():
    dest_package_lock = frontend_dir / "package-lock.json"
    shutil.copy2(source_package_lock, dest_package_lock)
    logger.info(f"   ✅ Copied package-lock.json")
else:
    logger.warning(f"   ⚠️  package-lock.json not found, exported package will use npm install")
```

### Priority 2: Improve Automation

**File**: `backend/app/services/export/infrastructure_generator.py`

**Enhancement #1 - Unique container names**:
```python
def _generate_docker_compose(self, config):
    customer_name = config.get("customer_name", "standalone")
    module_name = config.get("module_name")
    container_prefix = f"{customer_name}_{module_name}"

    # Use in all container_name fields
    container_name = f"{container_prefix}_{service}"
```

**Enhancement #2 - Port conflict detection**:
```python
def detect_port_conflicts(ports: List[int]) -> Dict[str, int]:
    """Detect port conflicts and suggest alternatives."""
    import socket

    available_ports = {}
    for service, port in ports.items():
        while is_port_in_use(port):
            port += 100
        available_ports[service] = port
    return available_ports
```

**Enhancement #3 - Pre-configured .env**:
```python
def _generate_env_file_preconfigured(self, config):
    """Generate pre-configured .env instead of just .env.example"""
    import secrets

    env_vars = {
        "MODULE_NAME": config["module_name"],
        "POSTGRES_PASSWORD": f"standalone_{config['module_name']}_db_" + secrets.token_urlsafe(16),
        "MINIO_SECRET_KEY": "standalone_minio_" + secrets.token_urlsafe(16),
        "JWT_SECRET": secrets.token_urlsafe(32),
        "SECRET_KEY": secrets.token_urlsafe(32),
        # Ports auto-detected
        "BACKEND_PORT": detect_available_port(8000),
        "FRONTEND_PORT": detect_available_port(3001),
        # ... etc
    }
```

---

## Deployment Status

### Build Progress:
- ✅ Backend Dockerfile: Built successfully
- ❌ Frontend Dockerfile: Failed (double braces in next.config.js)
- ⏹️  Deployment: Blocked

### After Fixes Applied:
- ✅ next.config.js syntax fixed
- ✅ npm ci → npm install changed
- ⏳ Ready to retry deployment

---

## Success Criteria for Phase 2.1 (Bug Fixes)

- [ ] Export generates valid next.config.js (single braces)
- [ ] Export includes package-lock.json OR uses npm install
- [ ] Frontend builds successfully
- [ ] Backend builds successfully
- [ ] All services start without errors

## Success Criteria for Phase 3 (Automation)

- [ ] Unique container names generated automatically
- [ ] Port conflicts detected and avoided
- [ ] Pre-configured .env generated (not just example)
- [ ] Zero manual interventions required
- [ ] Deploy script runs successfully end-to-end

---

## Testing Recommendation

After fixing bugs:
1. Re-export Relation Extractor module
2. Extract to clean directory
3. Run `./deploy.sh` without ANY manual changes
4. Verify all services start successfully
5. Test module functionality

---

## Estimated Fix Time

- **Bug Fixes (P1)**: 1-2 hours
  - Fix next.config.js: 15 minutes
  - Add package-lock.json: 30 minutes
  - Update Dockerfile logic: 15 minutes
  - Testing: 30 minutes

- **Automation (P2)**: 4-6 hours
  - Container naming: 1 hour
  - Port detection: 2 hours
  - Pre-configured .env: 2 hours
  - Testing: 1 hour

**Total**: 5-8 hours for production-ready plug-and-play deployment

---

## Conclusion

**Current State**: Export Wizard generates non-functional packages due to code generation bugs.

**Blockers**:
1. Double braces in next.config.js (syntax error)
2. Missing package-lock.json (build failure)
3. Manual configuration required

**Recommendation**:
1. **URGENT**: Fix Phase 2 bugs before any customer deliveries
2. **HIGH**: Implement Phase 3 automation for true plug-and-play
3. **MEDIUM**: Add export validation/testing before packaging

**Risk**: Current exports will fail for customers. **DO NOT DELIVER** until bugs fixed.

---

**Test Report Created**: 2026-01-04
**Bugs Severity**: CRITICAL
**Action Required**: IMMEDIATE
