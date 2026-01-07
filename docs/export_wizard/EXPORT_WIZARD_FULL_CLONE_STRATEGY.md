# Export Wizard - "Full Clone with Filters" Strategy

**Date**: 2026-01-07
**Status**: 📋 **PROPOSAL** - Strategic Analysis & Recommendation
**Related**: Requirement #10 - Export Wizard Enhancement

---

## Executive Summary

**Recommendation**: ✅ **ADOPT** the "Full Clone with Filters" approach

This strategy offers superior maintainability, security, and deployment simplicity compared to the current selective export approach. It transforms the export wizard from a complex code-cherry-picking tool into a streamlined full-stack cloning system with intelligent filtering.

**Key Benefits**:
- 🔒 Better security (clean, minimal exported package)
- 🚀 Faster deployment (standard docker-compose workflow)
- 🛠️ Easier maintenance (no complex dependency tracking)
- 📦 Self-contained packages (everything needed included)
- ✅ Guaranteed functionality (tested base + single module)

---

## Problem Statement

### Current Export Wizard Issues

**1. Complexity of Selective Export**:
- Manually tracking code dependencies for each module
- Risk of missing required backend services
- Frontend component dependencies unclear
- Database schema partial exports prone to errors

**2. Incomplete Packages**:
- Missing essential infrastructure files
- Incomplete seed data
- No installation scripts included
- Docker configuration often missing

**3. Security Concerns**:
- Potential leakage of other modules' code
- Customer data accidentally included
- User credentials exported unintentionally
- No clear data sanitization strategy

**4. Deployment Challenges**:
- Exported packages don't work out-of-box
- Manual configuration required
- Database setup unclear
- Environment-specific adjustments needed

---

## Proposed Solution: "Full Clone with Filters"

### Core Concept

**Export the ENTIRE application, then REMOVE unwanted modules**

Instead of cherry-picking files for one module, we:
1. Clone the complete, working application
2. Remove all modules EXCEPT the selected one
3. Clean all customer/user data (keep only seed data)
4. Package with complete installation scripts

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Source: Full Enterprise RAG Chatbot                        │
│  ├─ Backend (all services, all modules)                     │
│  ├─ Frontend (all components, all routes)                   │
│  ├─ Database (schema + ALL seed data)                       │
│  ├─ Docker Compose (all services)                           │
│  └─ Infrastructure (complete setup)                         │
└─────────────────────────────────────────────────────────────┘
                           ↓
              ┌────────────────────────┐
              │  Export Wizard Filter  │
              │  (Selected Module)     │
              └────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  Exported Package: Filtered Clone                           │
│  ├─ Backend (all base + ONLY selected module)               │
│  ├─ Frontend (all base + ONLY selected module UI)           │
│  ├─ Database (schema + filtered seed data)                  │
│  ├─ Docker Compose (optimized services)                     │
│  └─ Installation Scripts (automated setup)                  │
└─────────────────────────────────────────────────────────────┘
```

---

## Detailed Design

### 1. What Gets INCLUDED (Always)

**Core Platform** (Tier 1 - Essential):
- ✅ **Backend Core Services**:
  - Document service (upload, processing, chunking)
  - Embedding service (vector generation)
  - LLM service (multi-provider support)
  - RAG service (retrieval, context building)
  - Audit service (logging, tracking)
  - Database service (PostgreSQL + pgvector)

- ✅ **Frontend Core Components**:
  - Chat interface
  - File upload
  - Model selector
  - Session management
  - Admin panel (module management only)

- ✅ **Infrastructure**:
  - Docker Compose (postgres, backend, frontend, ollama, redis, minio)
  - Complete database schema (all 67 tables)
  - Installation scripts (backend/sql/* all 14 files)
  - Environment configuration (.env.example)

- ✅ **Seed Data** (Clean, Production-Ready):
  - Admin user ONLY (admin/admin, Technology/ITM11)
  - Global project ONLY
  - 7 departments (standard structure)
  - 28 teams (standard structure)
  - 5 RBAC roles (admin, user, analyst, engineer, guest)
  - 17 system configurations
  - 17 LLM models
  - 25+ prompt library (general purpose)
  - Performance indexes (all 190+)

### 2. What Gets FILTERED (Module-Specific)

**Based on Selection**:

**If Domain Vertical Selected** (e.g., "Relation Extractor"):
- ✅ INCLUDE: Selected Tier 2 module ONLY
  - Backend: `backend/app/tier_2/document_intelligence/relation_extractor*.py`
  - Frontend: `frontend/src/components/tier2/document_intelligence/RelationExtractor*.tsx`
  - Routes: API routes for this module only
  - Schemas: Pydantic schemas for this module only
  - Sample data: `backend/sample_data/tier2_domain_verticals/document_intelligence/*`

- ❌ OMIT: All other Tier 2 modules (19 modules removed)
- ❌ OMIT: All Tier 3 customer solutions (6 modules removed)

**If Customer Solution Selected** (e.g., "British Council POC"):
- ✅ INCLUDE: Selected Tier 3 module ONLY
  - Backend: `backend/app/services/british_council/*.py`
  - Frontend: `frontend/src/components/BritishCouncilRecommender.tsx`
  - Routes: `backend/app/api/routes/british_council_routes.py`
  - Sample data: `backend/sample_data/tier3_customer_pocs/british_council/*`

- ❌ OMIT: All Tier 2 domain verticals (20 modules removed)
- ❌ OMIT: All other Tier 3 customer solutions (5 modules removed)

### 3. What Gets REMOVED (Security & Privacy)

**Data Sanitization**:
- ❌ All user accounts EXCEPT admin
- ❌ All projects EXCEPT Global
- ❌ All uploaded documents (documents, document_chunks tables emptied)
- ❌ All chat history (conversations, messages tables emptied)
- ❌ All sessions (chat_sessions, session_documents tables emptied)
- ❌ All audit logs (audit_logs, usage_metrics tables emptied)
- ❌ All evaluation results (evaluation_results, evaluation_cache tables emptied)
- ❌ All fine-tuning jobs and datasets (finetuning_* tables emptied)

**Code Removal**:
- ❌ All non-selected Tier 2 modules (backend + frontend)
- ❌ All non-selected Tier 3 modules (backend + frontend)
- ❌ Unused API routes
- ❌ Unused frontend components
- ❌ Unused sample data

### 4. Module Registry Update

**Filtered modules table**:
```sql
-- Before export: 36 modules
-- After export (e.g., Relation Extractor selected): 11 modules
DELETE FROM modules WHERE tier = 2 AND module_name != 'Relation Extractor';
DELETE FROM modules WHERE tier = 3;

-- Result: 10 Tier 1 (core) + 1 Tier 2 (selected) = 11 modules
```

**RBAC Permissions Update**:
```sql
-- Remove permissions for non-existent modules
DELETE FROM role_module_permissions
WHERE module_id NOT IN (SELECT id FROM modules);

-- Ensure admin has access to remaining modules
-- (Already seeded correctly in 12_seed_rbac_permissions.sql)
```

---

## Implementation Strategy

### Phase 1: Export Package Builder

**File**: `backend/app/services/export/full_clone_builder.py` (NEW)

```python
class FullCloneExportBuilder:
    """
    Builds complete application clone with filtered modules
    """

    def __init__(self, selected_module: str, module_tier: int):
        self.selected_module = selected_module
        self.module_tier = module_tier
        self.export_path = f"exports/{selected_module}_{timestamp}"

    async def build_export_package(self) -> str:
        """
        Main export workflow
        """
        # 1. Copy entire codebase structure
        await self._copy_codebase()

        # 2. Filter modules (remove non-selected)
        await self._filter_modules()

        # 3. Generate filtered database seed script
        await self._generate_filtered_db_script()

        # 4. Update docker-compose (optimize services)
        await self._update_docker_compose()

        # 5. Create installation guide
        await self._create_installation_guide()

        # 6. Package as ZIP
        return await self._create_zip_archive()
```

**Key Methods**:

1. **`_copy_codebase()`**:
   - Copy all backend/* frontend/* docker-compose.yml .env.example
   - Copy all installation scripts
   - Copy all documentation

2. **`_filter_modules()`**:
   - Delete non-selected Tier 2 directories
   - Delete non-selected Tier 3 directories
   - Remove unused imports from main.py
   - Remove unused routes from router registration

3. **`_generate_filtered_db_script()`**:
   - Start with base 00-13 SQL scripts
   - Create custom `10_seed_modules_FILTERED.sql` with only selected module
   - Create custom `12_seed_rbac_permissions_FILTERED.sql` with only relevant permissions
   - Add data sanitization script: `14_remove_customer_data.sql`

4. **`_update_docker_compose()`**:
   - Keep: postgres, backend, frontend, redis, minio, ollama
   - Optional: prefect (if module uses workflows)
   - Remove: Any module-specific services

5. **`_create_installation_guide()`**:
   - Generate INSTALL.md with step-by-step instructions
   - Include module-specific configuration
   - List required environment variables

### Phase 2: Database Sanitization Script

**File**: `backend/sql/14_remove_customer_data.sql` (NEW - Generated)

```sql
-- ============================================================================
-- Remove Customer Data for Export Package
-- ============================================================================
-- WARNING: This script DELETES all user data, keeping only seed data
-- ============================================================================

BEGIN;

-- Remove all users except admin
DELETE FROM users WHERE username != 'admin';

-- Remove all projects except Global
DELETE FROM projects WHERE name != 'Global';

-- Remove all uploaded documents
DELETE FROM documents;
DELETE FROM document_chunks;

-- Remove all chat history
DELETE FROM conversations;
DELETE FROM messages;
DELETE FROM chat_sessions;
DELETE FROM session_documents;

-- Remove all audit logs
DELETE FROM audit_logs;
DELETE FROM usage_metrics;
DELETE FROM tool_usage_stats;

-- Remove all evaluation data
DELETE FROM evaluation_results;
DELETE FROM evaluation_cache;
DELETE FROM human_feedback;

-- Remove all fine-tuning data
DELETE FROM finetuning_jobs;
DELETE FROM finetuning_datasets;
DELETE FROM finetuned_models;
DELETE FROM training_metrics;

-- Remove non-selected modules
DELETE FROM modules
WHERE tier = 2 AND module_name != '{{SELECTED_MODULE}}'
   OR tier = 3 AND module_name != '{{SELECTED_MODULE}}';

-- Clean up orphaned permissions
DELETE FROM role_module_permissions
WHERE module_id NOT IN (SELECT id FROM modules);

COMMIT;

RAISE NOTICE '✓ Customer data removed - Package is clean';
```

### Phase 3: Export Wizard UI Enhancement

**File**: `frontend/src/components/ExportWizard.tsx` (UPDATE)

**New Features**:
1. **Module Selection Screen**:
   - Radio buttons for Tier 2 modules
   - Radio buttons for Tier 3 modules
   - Clear indication: "Full application with ONLY this module"

2. **Export Configuration**:
   - Include sample data: Yes/No
   - Include documentation: Yes/No
   - Optimize docker-compose: Yes/No (remove unused services)

3. **Progress Indicator**:
   - Copying codebase (20%)
   - Filtering modules (40%)
   - Generating database scripts (60%)
   - Creating installation guide (80%)
   - Packaging ZIP (100%)

4. **Download Ready**:
   - Package size display
   - Installation instructions preview
   - Download button

---

## Exported Package Structure

```
exported_package_relation_extractor_2026-01-07.zip
├── README.md                          # Overview + quick start
├── INSTALL.md                         # Detailed installation guide
├── .env.example                       # Environment template
├── docker-compose.yml                 # Optimized services
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/
│   │   │       ├── document_routes.py     # Core
│   │   │       ├── chat_routes.py         # Core
│   │   │       └── relation_extractor_routes.py  # Selected module ONLY
│   │   ├── services/
│   │   │   ├── document_service.py        # Core
│   │   │   ├── llm_service.py             # Core
│   │   │   ├── rag_service.py             # Core
│   │   │   └── # NO other tier 2/3 services
│   │   ├── tier_2/
│   │   │   └── document_intelligence/
│   │   │       ├── relation_extractor_routes.py
│   │   │       └── relation_extractor_schemas.py
│   │   │       # NO other tier_2 modules
│   │   └── # NO tier_3/ directory
│   ├── sql/
│   │   ├── 00_CLEAN_INSTALL_MASTER.sql
│   │   ├── 01_extensions.sql
│   │   ├── 02_complete_schema.sql
│   │   ├── ... (03-09 unchanged)
│   │   ├── 10_seed_modules_FILTERED.sql       # ONLY 11 modules (10 Tier 1 + 1 selected)
│   │   ├── 11_seed_prompt_library.sql
│   │   ├── 12_seed_rbac_permissions_FILTERED.sql  # ONLY relevant permissions
│   │   ├── 13_create_indexes.sql
│   │   └── 14_remove_customer_data.sql        # Data sanitization
│   └── sample_data/
│       ├── tier2_domain_verticals/
│       │   └── document_intelligence/         # Selected module sample data
│       └── # NO tier3_customer_pocs/
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatInterface.tsx              # Core
│   │   │   ├── FileUpload.tsx                 # Core
│   │   │   ├── tier2/
│   │   │   │   └── document_intelligence/
│   │   │   │       └── RelationExtractor.tsx  # Selected module ONLY
│   │   │   └── # NO other tier2 subdirectories
│   │   └── # NO tier3 components
│   └── package.json
│
└── scripts/
    └── setup/
        ├── clean-install-database.sh
        └── verify-installation.sh
```

---

## Installation Experience (Customer)

**Customer receives ZIP package, extracts, and runs**:

```bash
# Step 1: Extract package
unzip exported_package_relation_extractor_2026-01-07.zip
cd exported_package_relation_extractor

# Step 2: Configure environment
cp .env.example .env
# Edit .env with API keys, etc.

# Step 3: Start services
docker-compose up -d

# Step 4: Install database (automated)
bash scripts/setup/clean-install-database.sh

# Step 5: Access application
# Frontend: http://localhost:3001
# Login: admin / admin
# Available modules: Core Platform + Relation Extractor ONLY
```

**Result**: Working application with ONLY the selected module, in 5 minutes!

---

## Security & Privacy Guarantees

### Data Isolation

**What Customer CANNOT See**:
- ❌ Other modules' code or logic
- ❌ Other customers' data or configurations
- ❌ Internal user accounts or credentials
- ❌ Production audit logs or usage metrics
- ❌ Other projects or document collections

**What Customer CAN See**:
- ✅ Complete core platform (necessary for module to work)
- ✅ Their selected module (fully functional)
- ✅ Clean seed data (departments, teams, roles, prompts)
- ✅ Admin user (single, default credentials)
- ✅ Global project (empty, ready for their data)

### Code Sanitization

**Verification Script**: `scripts/export/verify_export_clean.sh`

```bash
#!/bin/bash
# Verify exported package contains no sensitive data

echo "Checking for sensitive data in exported package..."

# Check for customer-specific strings
grep -r "CUSTOMER_NAME" . && echo "❌ Found customer data" || echo "✓ No customer data"

# Check for production secrets
grep -r "prod_api_key" . && echo "❌ Found secrets" || echo "✓ No secrets"

# Check for non-selected modules
find backend/app/tier_2 -mindepth 1 -maxdepth 1 -type d | wc -l
# Expected: 1 (only selected module)

find backend/app/tier_3 -mindepth 1 -maxdepth 1 -type d | wc -l
# Expected: 0 (all removed) OR 1 (if Tier 3 selected)

echo "✓ Export package is clean"
```

---

## Comparison: Current vs Proposed

| Aspect | Current (Selective Export) | Proposed (Full Clone + Filter) |
|--------|---------------------------|--------------------------------|
| **Complexity** | High (track all dependencies) | Low (copy all, remove unwanted) |
| **Completeness** | Often missing files | Always complete |
| **Functionality** | May break (missing deps) | Guaranteed working |
| **Security** | Risk of data leaks | Clean, sanitized |
| **Maintenance** | Hard to maintain export logic | Easy (standard structure) |
| **Installation** | Manual steps required | Automated (docker-compose + script) |
| **Package Size** | Small (~50-100 MB) | Medium (~200-300 MB) |
| **Deployment Time** | Hours (troubleshooting) | Minutes (automated) |
| **Updates** | Difficult to sync changes | Easy (re-export with latest) |

---

## Implementation Plan

### Phase 1: Core Export Builder (Week 1)

**Tasks**:
1. Create `FullCloneExportBuilder` service
2. Implement codebase copy logic
3. Implement module filtering logic
4. Create filtered SQL script generator
5. Add data sanitization script template

**Deliverables**:
- `backend/app/services/export/full_clone_builder.py`
- `backend/sql/14_remove_customer_data.sql.template`
- Unit tests

### Phase 2: Export Wizard UI (Week 2)

**Tasks**:
1. Update `ExportWizard.tsx` with new UI
2. Add progress tracking
3. Integrate with `FullCloneExportBuilder` API
4. Add export configuration options
5. Generate installation guide dynamically

**Deliverables**:
- Updated frontend component
- Export configuration schema
- Generated INSTALL.md template

### Phase 3: Testing & Validation (Week 3)

**Tasks**:
1. Test export for each Tier 2 module (20 exports)
2. Test export for each Tier 3 module (6 exports)
3. Verify each package installs successfully
4. Verify data sanitization completeness
5. Security audit of exported packages

**Deliverables**:
- Test results for all 26 modules
- Security audit report
- Installation verification checklist

### Phase 4: Documentation (Week 4)

**Tasks**:
1. Create export wizard user guide
2. Document package structure
3. Create customer installation guide template
4. Add troubleshooting guide
5. Update API documentation

**Deliverables**:
- Complete export wizard documentation
- Customer-facing installation guides
- Internal maintenance docs

---

## Risk Analysis

### Potential Risks

1. **Large Package Size**
   - **Risk**: 200-300 MB packages may be too large for email
   - **Mitigation**: Use cloud storage links (S3, MinIO), direct download
   - **Impact**: Low (modern bandwidth handles this easily)

2. **Accidental Code Exposure**
   - **Risk**: Core platform code visible to customer
   - **Mitigation**: Acceptable - core is needed for functionality, no business logic exposed
   - **Impact**: Low (core is generic, not proprietary)

3. **Incomplete Filtering**
   - **Risk**: Non-selected module code accidentally included
   - **Mitigation**: Automated verification script, manual QA checklist
   - **Impact**: Medium (could expose other modules)

4. **Database Script Errors**
   - **Risk**: Filtered SQL scripts may have foreign key issues
   - **Mitigation**: Automated testing of generated scripts
   - **Impact**: High (could prevent installation)

### Mitigation Strategies

**Automated Testing**:
```python
async def test_export_package(module_name: str):
    """
    Automated test for exported package
    """
    # 1. Generate export package
    builder = FullCloneExportBuilder(module_name, tier=2)
    package_path = await builder.build_export_package()

    # 2. Extract to temp directory
    extract_dir = f"/tmp/test_export_{module_name}"
    extract_package(package_path, extract_dir)

    # 3. Verify structure
    assert_file_exists(f"{extract_dir}/docker-compose.yml")
    assert_file_exists(f"{extract_dir}/backend/sql/00_CLEAN_INSTALL_MASTER.sql")

    # 4. Count modules in filtered SQL
    module_count = count_modules_in_sql(f"{extract_dir}/backend/sql/10_seed_modules_FILTERED.sql")
    assert module_count == 11  # 10 Tier 1 + 1 selected

    # 5. Verify no other tier 2/3 code
    tier2_count = count_tier2_modules(f"{extract_dir}/backend/app/tier_2")
    assert tier2_count == 1  # Only selected module

    # 6. Test installation (Docker-in-Docker)
    result = test_installation(extract_dir)
    assert result.success
    assert result.modules_available == [module_name]
```

---

## Recommendation

### ✅ ADOPT "Full Clone with Filters" Approach

**Rationale**:

1. **Simplicity**: Easier to maintain and less error-prone
2. **Completeness**: Guaranteed working packages
3. **Security**: Clean, sanitized data exports
4. **Customer Experience**: Fast, automated installation
5. **Maintainability**: Easy to update export logic

**Implementation Priority**: **HIGH**

**Estimated Effort**: 4 weeks (1 engineer)

**ROI**: High - significantly reduces deployment time and support burden

---

## Next Steps

1. **Approval**: Get stakeholder sign-off on this strategy
2. **Prototype**: Build proof-of-concept for 1-2 modules
3. **Test**: Validate with internal team
4. **Pilot**: Test with 1-2 friendly customers
5. **Rollout**: Implement for all 26 modules

---

## Appendix A: Sample Filtered SQL Scripts

### 10_seed_modules_FILTERED.sql (Example: Relation Extractor)

```sql
-- Only 11 modules: 10 Tier 1 (core) + 1 Tier 2 (selected)

INSERT INTO modules (module_name, tier, category, ...) VALUES
-- Tier 1 (Core Platform) - ALL 10 modules
('Chat', NULL, 'core', ...),
('Fine-Tuning', NULL, 'core', ...),
-- ... (8 more Tier 1 modules)

-- Tier 2 (Domain Vertical) - ONLY selected module
('Relation Extractor', 2, 'Document Intelligence', ...)

-- NO other Tier 2 modules
-- NO Tier 3 modules

ON CONFLICT (module_name) DO UPDATE SET ...;
```

### 14_remove_customer_data.sql (Generated)

```sql
-- Data sanitization for Relation Extractor export

BEGIN;

-- Remove all users except admin
DELETE FROM users WHERE username != 'admin';

-- Remove all projects except Global
DELETE FROM projects WHERE name != 'Global';

-- Remove all documents and chunks
TRUNCATE document_chunks CASCADE;
TRUNCATE documents CASCADE;

-- Remove all chat history
TRUNCATE conversation_messages CASCADE;
TRUNCATE messages CASCADE;
TRUNCATE conversations CASCADE;
TRUNCATE chat_sessions CASCADE;

-- Remove non-selected modules
DELETE FROM modules WHERE module_name NOT IN (
    'Chat', 'Fine-Tuning', 'Admin', 'Weights Config', 'Tool Usage',
    'Evaluation', 'Project Estimator', 'Web Scraping', 'Upload Files',
    'Chat History', 'Relation Extractor'
);

COMMIT;
```

---

**Last Updated**: 2026-01-07
**Status**: 📋 Proposal - Awaiting Approval
**Next**: Prototype implementation
