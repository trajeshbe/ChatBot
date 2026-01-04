# Module-Specific Export Enhancement Design

**Date**: 2026-01-04
**Issue**: Current export system exports generic config but NOT module-specific code
**Solution**: Add `ModuleCodeExtractor` to package actual module implementation

---

## Problem Statement

Current export creates a generic standalone package but **doesn't include the actual module code**:

### What's Currently Exported (Generic)
✅ Configuration JSON
✅ Documents & Embeddings (Parquet)
✅ Infrastructure (Docker Compose, K8s, AWS)
✅ Database load scripts
✅ API client examples
✅ License key
✅ README

### What's MISSING (Module-Specific)
❌ Backend service logic (`*_service.py`)
❌ API routes (`*_routes.py`)
❌ Pydantic schemas (`*_schemas.py`)
❌ Frontend component (`*Panel.tsx`)
❌ Module-specific dependencies
❌ Module-specific documentation
❌ Sample data for testing

**Result**: Customer gets infrastructure but NO actual module functionality!

---

## Solution Architecture

### New Component: `ModuleCodeExtractor`

```python
class ModuleCodeExtractor:
    """Extract module-specific code files for standalone deployment."""

    async def extract_module_code(
        self,
        module_name: str,
        export_dir: Path
    ) -> ModuleCodeExtractionResult:
        """
        Extract all code files needed for module to work standalone.

        Returns:
            ModuleCodeExtractionResult with files_exported, total_size
        """
```

### Files to Extract

#### 1. Backend Code (Python)
```
backend/
├── app/
│   ├── main.py                    # FastAPI app (filtered for this module)
│   ├── tier_2/
│   │   └── {category}/
│   │       ├── __init__.py
│   │       ├── {module}_service.py    # ← Core logic
│   │       ├── {module}_routes.py     # ← API endpoints
│   │       └── {module}_schemas.py    # ← Request/Response models
│   ├── tier_1/                    # Shared tier 1 services (RAG, LLM, etc.)
│   │   ├── rag/
│   │   ├── llm/
│   │   └── infrastructure/
│   └── models/                    # Database models (if needed)
├── requirements.txt               # Python dependencies
└── Dockerfile                     # Container image
```

#### 2. Frontend Code (TypeScript/React)
```
frontend/
├── src/
│   ├── components/
│   │   └── tier2/
│   │       └── {category}/
│   │           └── {Module}Panel.tsx  # ← UI component
│   ├── pages/
│   │   └── index.tsx              # Entry point (filtered)
│   └── config/
│       └── modules.ts             # Module metadata
├── package.json                   # NPM dependencies
└── Dockerfile                     # Container image
```

#### 3. Sample Data & Tests
```
sample_data/
└── tier2_domain_verticals/
    └── {category}/
        ├── sample_input.json
        ├── sample_output.json
        └── README.md

tests/
└── tier2/
    └── test_{module}.py
```

#### 4. Documentation
```
docs/
├── API.md                         # API documentation
├── USAGE.md                       # How to use the module
├── DEPLOYMENT.md                  # Deployment guide
└── ARCHITECTURE.md                # Technical architecture
```

---

## Implementation Plan

### Phase 1: Module Code Extraction

**File**: `backend/app/services/export/module_code_extractor.py`

```python
from pathlib import Path
from typing import Dict, List, Set
import shutil
import ast

class ModuleCodeExtractor:
    """Extract module-specific code files."""

    # Module file mappings (category -> module -> files)
    MODULE_FILES = {
        "procurement": {
            "matcher": {
                "backend": [
                    "app/tier_2/procurement/matcher_service.py",
                    "app/tier_2/procurement/matcher_routes.py",
                    "app/tier_2/procurement/matcher_schemas.py",
                ],
                "frontend": [
                    "src/components/tier2/procurement/ProcurementMatcherPanel.tsx"
                ],
                "dependencies": {
                    "python": ["pandas", "numpy", "fuzzywuzzy"],
                    "npm": []
                }
            },
            # ... more modules
        },
        # ... more categories
    }

    async def extract_module_code(
        self,
        module_name: str,
        export_dir: Path
    ) -> Dict[str, Any]:
        """
        Extract all code files for a module.

        Steps:
        1. Identify module category and files
        2. Copy backend service/routes/schemas
        3. Copy frontend component
        4. Copy shared Tier 1 dependencies
        5. Resolve Python imports and create requirements.txt
        6. Resolve NPM dependencies and create package.json
        7. Copy sample data
        8. Generate module-specific README
        """

        # 1. Find module category and file list
        category, files = self._get_module_files(module_name)

        # 2. Copy backend files
        backend_dir = export_dir / "backend"
        for file_path in files["backend"]:
            self._copy_file(PROJECT_ROOT / file_path, backend_dir / file_path)

        # 3. Copy frontend files
        frontend_dir = export_dir / "frontend"
        for file_path in files["frontend"]:
            self._copy_file(PROJECT_ROOT / file_path, frontend_dir / file_path)

        # 4. Copy shared Tier 1 services
        tier1_files = await self._resolve_tier1_dependencies(files["backend"])
        for file_path in tier1_files:
            self._copy_file(PROJECT_ROOT / file_path, backend_dir / file_path)

        # 5. Generate requirements.txt
        python_deps = self._resolve_python_dependencies(
            files["backend"] + tier1_files
        )
        self._write_requirements(backend_dir / "requirements.txt", python_deps)

        # 6. Generate package.json
        npm_deps = self._resolve_npm_dependencies(files["frontend"])
        self._write_package_json(frontend_dir / "package.json", npm_deps)

        # 7. Copy sample data
        sample_data = await self._copy_sample_data(module_name, export_dir)

        # 8. Generate module README
        await self._generate_module_readme(
            module_name=module_name,
            category=category,
            export_dir=export_dir,
            files_exported=len(files["backend"]) + len(files["frontend"])
        )

        return {
            "backend_files": len(files["backend"]) + len(tier1_files),
            "frontend_files": len(files["frontend"]),
            "python_dependencies": len(python_deps),
            "npm_dependencies": len(npm_deps),
            "sample_data_files": sample_data["count"]
        }

    def _resolve_tier1_dependencies(
        self,
        backend_files: List[str]
    ) -> List[str]:
        """
        Parse Python files to find Tier 1 imports.

        Example:
            from app.tier_1.rag import RAGService
            from app.tier_1.llm import LLMService

        Returns list of Tier 1 files to include.
        """
        tier1_imports = set()

        for file_path in backend_files:
            with open(PROJECT_ROOT / file_path) as f:
                tree = ast.parse(f.read())

            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    if node.module and "tier_1" in node.module:
                        # Extract file path from import
                        module_path = node.module.replace(".", "/") + ".py"
                        tier1_imports.add(module_path)

        return list(tier1_imports)

    def _resolve_python_dependencies(
        self,
        python_files: List[str]
    ) -> Set[str]:
        """
        Parse Python files to find external package imports.

        Returns set of package names (e.g., {"pandas", "numpy"}).
        """
        external_imports = set()
        stdlib_modules = {...}  # Standard library modules

        for file_path in python_files:
            with open(PROJECT_ROOT / file_path) as f:
                tree = ast.parse(f.read())

            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    module = node.module if isinstance(node, ast.ImportFrom) else node.names[0].name
                    root_module = module.split('.')[0]

                    if root_module not in stdlib_modules and root_module != "app":
                        external_imports.add(root_module)

        return external_imports
```

### Phase 2: Update PackageBuilder

**File**: `backend/app/services/export/package_builder.py`

```python
from .module_code_extractor import ModuleCodeExtractor

class PackageBuilder:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.config_extractor = ConfigurationExtractor(db)
        self.doc_migrator = DocumentMigrator(db)
        self.infra_generator = InfrastructureGenerator()
        self.code_extractor = ModuleCodeExtractor()  # NEW

    async def build_export_package(self, ...):
        # ... existing code ...

        # NEW STEP: Extract module-specific code
        await self._update_job_progress(export_job, 50, "Extracting module code")

        code_stats = await self.code_extractor.extract_module_code(
            module_name=module_name,
            export_dir=export_dir
        )

        logger.info(f"✅ Module code extracted:")
        logger.info(f"   Backend files: {code_stats['backend_files']}")
        logger.info(f"   Frontend files: {code_stats['frontend_files']}")
        logger.info(f"   Python deps: {code_stats['python_dependencies']}")
        logger.info(f"   NPM deps: {code_stats['npm_dependencies']}")

        # ... continue with infrastructure generation ...
```

### Phase 3: Module Registry

**File**: `backend/app/services/export/module_registry.py`

```python
"""
Module Registry - Centralized mapping of modules to their files.

This makes it easy to add new modules and ensures consistency.
"""

from typing import Dict, List
from dataclasses import dataclass

@dataclass
class ModuleFiles:
    backend: List[str]
    frontend: List[str]
    tier1_dependencies: List[str]
    python_packages: List[str]
    npm_packages: List[str]
    sample_data: List[str]

# Module registry - maps module_id to files
MODULE_REGISTRY: Dict[str, ModuleFiles] = {
    # PROCUREMENT
    "matcher": ModuleFiles(
        backend=[
            "app/tier_2/procurement/matcher_service.py",
            "app/tier_2/procurement/matcher_routes.py",
            "app/tier_2/procurement/matcher_schemas.py",
        ],
        frontend=[
            "src/components/tier2/procurement/ProcurementMatcherPanel.tsx"
        ],
        tier1_dependencies=[
            "app/tier_1/llm/llm_service.py",
            "app/tier_1/rag/rag_service.py",
        ],
        python_packages=["pandas", "fuzzywuzzy"],
        npm_packages=[],
        sample_data=[
            "sample_data/tier2_domain_verticals/procurement_matcher/rfp_construction_materials.txt",
            "sample_data/tier2_domain_verticals/procurement_matcher/supplier_profiles.json",
        ]
    ),

    # Add all 31 modules here...
}
```

---

## Export Package Structure (After Enhancement)

```
{module_name}_export_{package_id}/
├── README.md                      # Module-specific deployment guide
├── LICENSE.key                    # RSA-signed license
├── config.json                    # Module configuration
├── .env.example                   # Environment variables template
│
├── backend/                       # ← NEW: Actual backend code
│   ├── app/
│   │   ├── main.py               # FastAPI app (module-specific)
│   │   ├── tier_1/               # Shared services (RAG, LLM, etc.)
│   │   └── tier_2/
│   │       └── {category}/
│   │           ├── {module}_service.py
│   │           ├── {module}_routes.py
│   │           └── {module}_schemas.py
│   ├── requirements.txt          # Python dependencies
│   └── Dockerfile
│
├── frontend/                      # ← NEW: Actual frontend code
│   ├── src/
│   │   └── components/
│   │       └── tier2/
│   │           └── {category}/
│   │               └── {Module}Panel.tsx
│   ├── package.json              # NPM dependencies
│   └── Dockerfile
│
├── data/                          # Documents & embeddings (existing)
│   ├── documents/
│   │   └── *.pdf, *.txt
│   ├── embeddings.parquet
│   └── load_embeddings.py
│
├── infrastructure/                # Deployment configs (existing)
│   ├── docker-compose.yml
│   ├── kubernetes/
│   └── aws/
│
├── sample_data/                   # ← NEW: Module-specific test data
│   ├── sample_input.json
│   ├── sample_output.json
│   └── README.md
│
└── docs/                          # ← NEW: Module documentation
    ├── API.md
    ├── USAGE.md
    └── DEPLOYMENT.md
```

---

## Testing Strategy

### 1. Unit Tests
```python
def test_module_code_extraction():
    """Test that module files are correctly identified and copied."""

def test_dependency_resolution():
    """Test that Python/NPM dependencies are correctly resolved."""

def test_tier1_dependency_discovery():
    """Test that Tier 1 imports are correctly discovered."""
```

### 2. Integration Test
```python
async def test_full_module_export():
    """Test complete export of a Tier 2 module (e.g., procurement matcher)."""

    # Export module
    package = await package_builder.build_export_package(
        module_name="matcher",
        customer_name="Test Customer",
        deployment_type=DeploymentType.DOCKER_COMPOSE
    )

    # Verify package contents
    assert (package_dir / "backend/app/tier_2/procurement/matcher_service.py").exists()
    assert (package_dir / "frontend/src/components/tier2/procurement/ProcurementMatcherPanel.tsx").exists()
    assert (package_dir / "requirements.txt").exists()
    assert (package_dir / "package.json").exists()

    # Verify dependencies
    requirements = (package_dir / "requirements.txt").read_text()
    assert "pandas" in requirements
    assert "fastapi" in requirements

    # Verify it can be deployed
    subprocess.run(["docker-compose", "up", "-d"], cwd=package_dir, check=True)

    # Test API endpoint
    response = requests.post("http://localhost:8000/api/v1/modules/matcher/match", ...)
    assert response.status_code == 200
```

### 3. E2E Test
```bash
# Extract and deploy module
tar -xzf matcher_export_abc123.tar.gz
cd matcher_export_abc123
docker-compose up -d

# Wait for services
sleep 30

# Test module API
curl -X POST http://localhost:8000/api/v1/modules/matcher/match \
  -H "Content-Type: application/json" \
  -d @sample_data/sample_input.json

# Verify frontend
curl http://localhost:3000

# Cleanup
docker-compose down
```

---

## Implementation Timeline

### Week 1: Core Infrastructure
- [ ] Create `ModuleCodeExtractor` class
- [ ] Implement file copying logic
- [ ] Implement dependency resolution (Python AST parsing)
- [ ] Create `MODULE_REGISTRY` with all 31 modules

### Week 2: Integration
- [ ] Update `PackageBuilder` to call `ModuleCodeExtractor`
- [ ] Add code extraction to export workflow
- [ ] Update export progress tracking
- [ ] Add code stats to export manifest

### Week 3: Testing
- [ ] Unit tests for code extraction
- [ ] Integration test for 1 Tier 2 module
- [ ] E2E test with Docker deployment
- [ ] Test all 31 modules

### Week 4: Documentation & Rollout
- [ ] Generate module-specific READMEs
- [ ] Update export wizard UI with code export info
- [ ] Add "Export with Code" toggle option
- [ ] Production deployment

---

## Open Questions

1. **Shared Dependencies**: How to handle Tier 1 services that multiple modules use?
   - **Answer**: Copy all used Tier 1 files into each export (self-contained)

2. **Database Migrations**: Should we include module-specific migrations?
   - **Answer**: Yes, include migrations in `backend/migrations/`

3. **Frontend Dependencies**: Include entire Next.js app or just component?
   - **Answer**: Include minimal Next.js app with only that module's component

4. **Versioning**: How to version exported modules?
   - **Answer**: Use git commit hash + export timestamp

5. **Updates**: How do customers get updates after export?
   - **Answer**: Phase 2 feature - webhook for update notifications

---

## Benefits

### For Customers
✅ **Complete Working Application** - Not just config, actual code
✅ **Self-Contained** - No dependency on platform
✅ **Customizable** - Can modify code for their needs
✅ **Production Ready** - Includes Docker/K8s configs
✅ **Documented** - API docs, usage guide, samples

### For Us
✅ **Demonstrates Value** - Shows what we built
✅ **Reduces Support** - Customers can debug themselves
✅ **Enables White-Label** - Easy to rebrand
✅ **Revenue Opportunity** - Premium export tier with code
✅ **Competitive Advantage** - Unique offering in market

---

**Next Steps**:
1. Review this design with team
2. Get approval for implementation
3. Start with Phase 1 (ModuleCodeExtractor)
4. Test with 1 Tier 2 module (procurement matcher)
5. Roll out to all 31 modules

**Estimated Effort**: 4 weeks (1 engineer)
**Priority**: High (customer-facing feature)
**Risk**: Low (existing code, just packaging)
