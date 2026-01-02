# Merit Skills → Three-Tier Architecture Implementation Plan

**Date**: 2026-01-01
**Status**: Planning Phase
**Objective**: Integrate 30+ Merit AI skills into modular three-tier plug-and-play architecture

---

## 📊 Skills Inventory

### **Tier 2: Domain Verticals / Use Cases** (24 Skills)

#### 🏗️ Construction & Infrastructure (4 skills)
1. **Construction Metrics Extractor** ✅ **ALREADY IMPLEMENTED**
2. **Project Estimator** ✅ **ALREADY IMPLEMENTED**
3. **Planning Classifier** - Classify planning documents
4. **Mine Scope** - Mining project scope analysis

#### 📄 Document Intelligence (3 skills)
1. **Docu-Extract** - 18-field structured data extraction from PDFs/images
2. **Relation Extractor** - Entity relationship extraction
3. **Generic RAG** - Document Q&A with table awareness

#### 💼 Procurement & Finance (4 skills)
1. **Procurement Matcher** - Match tenders to suppliers
2. **Vendor Recommendation** - AI-powered vendor selection
3. **Tender Intelligence** - Tender document analysis
4. **Spend Smart** - Spend analysis and optimization

#### 👥 HR & Talent Management (3 skills)
1. **Talent Search** - Resume matching and search
2. **Taxonomy SkillMatch** - Skills taxonomy and matching
3. **Talend Pulse** - Talent analytics dashboard

#### 🌾 Agriculture (2 skills)
1. **Agri Taxonomy** - Agricultural classification
2. **Agronomy Decision Support** - Crop management recommendations

#### 📧 Marketing & Communications (2 skills)
1. **Email Campaign Analyzer** - Campaign performance analysis
2. **Email Bounce Intelligence** - Bounce pattern analysis

#### 🏷️ E-commerce & Retail (1 skill)
1. **Fashion Tagging** - Automated product tagging

#### 🚢 Maritime (1 skill)
1. **Maritime Report Generation** - Automated maritime reports

#### 🔍 Analytics & Intelligence (4 skills)
1. **Bot Detect Analyzer** - Bot traffic analysis
2. **Credit Profile Analyzer** - Credit risk assessment
3. **Taxonomy Classification** - Multi-domain taxonomy
4. **Dashboard** - Generic analytics dashboard

---

### **Tier 3: Customer-Specific** (6 Skills)

1. **British Council POC** - Education sector specific
2. **Construction Monitor POC** ✅ **PARTIALLY IMPLEMENTED** - NER/REL for construction docs
3. **CRU POC** - Commodity research unit specific
4. **Grand Thornton POC** - Audit/consulting specific
5. **GT Motive POC** - Automotive specific
6. **Solera POC** - Insurance/automotive specific

---

### **Infrastructure Enhancement** (1 Platform)

1. **Merit ML Platform** - Model training, deployment, monitoring

---

## 🏗️ Three-Tier Architecture Mapping

```
┌─────────────────────────────────────────────────────────────┐
│ TIER 1: Core Platform (Existing - DO NOT MODIFY)           │
├─────────────────────────────────────────────────────────────┤
│ ✓ Infrastructure (config, database, security, GPU, MinIO)  │
│ ✓ LLM Services (OpenAI, Claude, Ollama, vLLM)             │
│ ✓ Embeddings (semantic, intelligent, reranker)             │
│ ✓ Document Processing (Docling, OCR, vision, hybrid)       │
│ ✓ RAG (retrieval, pipeline, semantic cache)                │
│ ✓ Agents (agent_state, tool_registry, engines)             │
│ ✓ Platform Services (auth, RBAC, audit, tracking)          │
│ ✓ Fine-tuning (trainers, rewards, GPU pool)                │
│ ✓ Evaluation (RAGAS, quality metrics)                      │
│ ✓ Data Extraction (webscraper, template extraction)        │
│ ✓ NLP Processing (classifier, translator, analyzer)        │
│ ✓ Export (project estimator, excel, BRD)                   │
│ ✓ CV Processing (OpenCV measurements)                      │
│ ✓ Utilities (text compression, MinIO paths)                │
└─────────────────────────────────────────────────────────────┘
                            ↓ (extends)
┌─────────────────────────────────────────────────────────────┐
│ TIER 2: Domain Verticals / Use Cases (NEW - PLUGGABLE)     │
├─────────────────────────────────────────────────────────────┤
│ → construction/                                             │
│    ├── __init__.py                                          │
│    ├── planning_classifier_service.py                       │
│    ├── mine_scope_service.py                                │
│    └── routes.py                                            │
│                                                             │
│ → document_intelligence/                                    │
│    ├── docu_extract_service.py                              │
│    ├── relation_extractor_service.py                        │
│    ├── generic_rag_service.py                               │
│    └── routes.py                                            │
│                                                             │
│ → procurement/                                              │
│    ├── matcher_service.py                                   │
│    ├── vendor_recommendation_service.py                     │
│    ├── tender_intelligence_service.py                       │
│    ├── spend_smart_service.py                               │
│    └── routes.py                                            │
│                                                             │
│ → hr_talent/                                                │
│    ├── talent_search_service.py                             │
│    ├── taxonomy_skillmatch_service.py                       │
│    ├── talend_pulse_service.py                              │
│    └── routes.py                                            │
│                                                             │
│ → agriculture/                                              │
│    ├── agri_taxonomy_service.py                             │
│    ├── agronomy_decision_service.py                         │
│    └── routes.py                                            │
│                                                             │
│ → marketing/                                                │
│    ├── email_campaign_analyzer_service.py                   │
│    ├── email_bounce_intelligence_service.py                 │
│    └── routes.py                                            │
│                                                             │
│ → ecommerce/                                                │
│    ├── fashion_tagging_service.py                           │
│    └── routes.py                                            │
│                                                             │
│ → maritime/                                                 │
│    ├── report_generation_service.py                         │
│    └── routes.py                                            │
│                                                             │
│ → analytics/                                                │
│    ├── bot_detect_analyzer_service.py                       │
│    ├── credit_profile_analyzer_service.py                   │
│    ├── taxonomy_classification_service.py                   │
│    ├── dashboard_service.py                                 │
│    └── routes.py                                            │
└─────────────────────────────────────────────────────────────┘
                            ↓ (customizes)
┌─────────────────────────────────────────────────────────────┐
│ TIER 3: Customer-Specific (NEW - PLUGGABLE)                │
├─────────────────────────────────────────────────────────────┤
│ → british_council/                                          │
│    ├── config.yaml                                          │
│    ├── custom_service.py                                    │
│    └── routes.py                                            │
│                                                             │
│ → cru/                                                      │
│    ├── config.yaml                                          │
│    ├── custom_service.py                                    │
│    └── routes.py                                            │
│                                                             │
│ → grand_thornton/                                           │
│    ├── config.yaml                                          │
│    ├── custom_service.py                                    │
│    └── routes.py                                            │
│                                                             │
│ → gt_motive/                                                │
│    ├── config.yaml                                          │
│    ├── custom_service.py                                    │
│    └── routes.py                                            │
│                                                             │
│ → solera/                                                   │
│    ├── config.yaml                                          │
│    ├── custom_service.py                                    │
│    └── routes.py                                            │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Implementation Strategy

### **Phase 1: Foundation (Week 1-2)**

#### 1.1 Backend Module System
```python
# backend/app/tier_2/__init__.py
from .registry import ModuleRegistry

registry = ModuleRegistry()

# backend/app/tier_2/registry.py
class ModuleRegistry:
    """
    Dynamic module registry for pluggable domain vertical modules.
    Supports enable/disable, dependency injection, lifecycle management.
    """
    def __init__(self):
        self.modules = {}
        self.enabled_modules = set()

    def register(self, name: str, module_class, dependencies: list = None):
        """Register a domain vertical module"""
        pass

    def enable(self, name: str):
        """Enable a module and mount its routes"""
        pass

    def disable(self, name: str):
        """Disable a module and unmount its routes"""
        pass

    def get_enabled_modules(self) -> list:
        """Return list of enabled modules with metadata"""
        pass
```

#### 1.2 Database Schema for Module Management
```sql
-- migrations/030_add_module_management.sql
CREATE TYPE module_tier AS ENUM ('tier_2', 'tier_3');
CREATE TYPE module_status AS ENUM ('enabled', 'disabled', 'installing', 'error');

CREATE TABLE skill_modules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    tier module_tier NOT NULL,
    category VARCHAR(50) NOT NULL,  -- construction, procurement, hr_talent, etc.
    display_name VARCHAR(200) NOT NULL,
    description TEXT,
    version VARCHAR(20) DEFAULT '1.0.0',
    status module_status DEFAULT 'disabled',
    dependencies JSON,  -- ['tier_1.rag', 'tier_1.document_processing']
    config JSON,  -- module-specific configuration
    icon VARCHAR(50),  -- UI icon name
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE module_activations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    module_id UUID REFERENCES skill_modules(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    activated_by UUID REFERENCES users(id),
    activated_at TIMESTAMPTZ DEFAULT NOW(),
    config_override JSON,
    UNIQUE(module_id, project_id)
);

CREATE INDEX idx_skill_modules_tier ON skill_modules(tier);
CREATE INDEX idx_skill_modules_category ON skill_modules(category);
CREATE INDEX idx_skill_modules_status ON skill_modules(status);
CREATE INDEX idx_module_activations_project ON module_activations(project_id);
```

#### 1.3 Frontend Module Menu System
```typescript
// frontend/src/components/ModuleSelector.tsx
interface Module {
  id: string;
  name: string;
  tier: 'tier_2' | 'tier_3';
  category: string;
  displayName: string;
  description: string;
  icon: string;
  status: 'enabled' | 'disabled' | 'installing' | 'error';
  dependencies: string[];
}

interface ModuleCategory {
  name: string;
  displayName: string;
  icon: string;
  modules: Module[];
}

export const ModuleSelector: React.FC = () => {
  const [categories, setCategories] = useState<ModuleCategory[]>([]);
  const [activeTab, setActiveTab] = useState<'verticals' | 'customer'>('verticals');

  // Render module cards organized by category
};
```

---

### **Phase 2: Tier 2 Module Template (Week 3)**

#### 2.1 Standard Module Structure
```
backend/app/tier_2/{category}/
├── __init__.py              # Module exports
├── service.py               # Business logic using Tier 1
├── routes.py                # FastAPI routes
├── schemas.py               # Pydantic models
├── models.py                # Database models (if needed)
├── config.py                # Module configuration
├── README.md                # Documentation
└── tests/                   # Module-specific tests
    ├── test_service.py
    └── test_routes.py
```

#### 2.2 Example: Document Intelligence Module
```python
# backend/app/tier_2/document_intelligence/service.py
from app.tier_1.llm.llm_service import LLMService
from app.tier_1.document_processing.vision_service import VisionService
from app.tier_1.rag.rag_service import RAGService

class DocuExtractService:
    """
    18-field structured data extraction from planning documents.
    Leverages Tier 1: Vision, LLM, RAG services.
    """

    EXTRACTION_FIELDS = [
        "project_name", "address", "project_status", "storeys",
        "gfa", "site_area", "zoning", "heritage_designation",
        "architect", "developer", "planning_consultant",
        "residential_units", "unit_types", "commercial_uses",
        "amenities", "parking_levels", "parking_spaces", "public_realm"
    ]

    def __init__(self, llm_service: LLMService, vision_service: VisionService):
        self.llm = llm_service
        self.vision = vision_service

    async def extract(self, document_id: str, format: str) -> dict:
        """Extract 18 structured fields from document"""
        # Use Tier 1 services for extraction
        pass

# backend/app/tier_2/document_intelligence/routes.py
from fastapi import APIRouter, Depends
from app.tier_1.platform_services.rbac_middleware import require_permission

router = APIRouter(prefix="/api/v1/modules/document-intelligence", tags=["Document Intelligence"])

@router.post("/extract")
@require_permission("module:document_intelligence:extract")
async def extract_document(
    document_id: str,
    service: DocuExtractService = Depends()
):
    return await service.extract(document_id, format="json")
```

---

### **Phase 3: Priority Module Implementation (Week 4-8)**

#### High-Value Quick Wins (Implement First)
1. **Docu-Extract** (Week 4) - High demand, uses existing Vision service
2. **Procurement Matcher** (Week 5) - Extends RAG, valuable for RFPs
3. **Talent Search** (Week 6) - Resume parsing, uses document + RAG
4. **Email Campaign Analyzer** (Week 7) - Marketing analytics
5. **Dashboard** (Week 8) - Generic analytics module

#### Tech Stack Mapping
```yaml
Skill: Docu-Extract
Tier 1 Dependencies:
  - tier_1.llm.llm_service (GPT-4 Vision)
  - tier_1.document_processing.vision_service
  - tier_1.document_processing.document_service
  - tier_1.rag.rag_service (for context)
New Capabilities:
  - 18-field extraction schema
  - Smart page selection
  - Multi-format support (PDF, DOCX, PNG, JPEG)
API Endpoint: /api/v1/modules/document-intelligence/extract

Skill: Procurement Matcher
Tier 1 Dependencies:
  - tier_1.rag.rag_service
  - tier_1.embeddings.embedding_service
  - tier_1.rag.reranker
  - tier_1.nlp_processing.query_classifier
New Capabilities:
  - Tender document parsing
  - Supplier database management
  - Matching algorithm (semantic + rule-based)
API Endpoint: /api/v1/modules/procurement/match

Skill: Talent Search
Tier 1 Dependencies:
  - tier_1.document_processing.document_service (resume parsing)
  - tier_1.rag.rag_service
  - tier_1.nlp_processing.query_classifier
  - tier_1.nlp_processing.content_analyzer
New Capabilities:
  - Resume/CV parsing
  - Skills taxonomy
  - Candidate matching
API Endpoint: /api/v1/modules/hr-talent/search
```

---

### **Phase 4: Frontend Integration (Week 9-10)**

#### 4.1 Module Marketplace UI
```typescript
// frontend/src/pages/modules.tsx
export default function ModulesPage() {
  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-6">AI Module Marketplace</h1>

      <Tabs defaultValue="verticals">
        <TabsList>
          <TabsTrigger value="verticals">Domain Verticals</TabsTrigger>
          <TabsTrigger value="customer">Customer-Specific</TabsTrigger>
        </TabsList>

        <TabsContent value="verticals">
          <ModuleCategoryGrid categories={tier2Categories} />
        </TabsContent>

        <TabsContent value="customer">
          <CustomerModuleList modules={tier3Modules} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
```

#### 4.2 Dynamic Module Sidebar
```typescript
// frontend/src/components/Sidebar.tsx
const Sidebar = () => {
  const { enabledModules } = useModules();

  return (
    <div className="sidebar">
      {/* Core Features */}
      <NavSection title="Core">
        <NavItem icon={<MessageSquare />} to="/chat" label="Chat" />
        <NavItem icon={<Upload />} to="/upload" label="Upload" />
        <NavItem icon={<Settings />} to="/settings" label="Settings" />
      </NavSection>

      {/* Enabled Domain Modules */}
      <NavSection title="Domain Verticals">
        {enabledModules
          .filter(m => m.tier === 'tier_2')
          .map(module => (
            <NavItem
              key={module.id}
              icon={module.icon}
              to={`/modules/${module.name}`}
              label={module.displayName}
            />
          ))}
      </NavSection>

      {/* Customer-Specific Modules */}
      <NavSection title="Customer-Specific">
        {enabledModules
          .filter(m => m.tier === 'tier_3')
          .map(module => (
            <NavItem
              key={module.id}
              icon={module.icon}
              to={`/customers/${module.name}`}
              label={module.displayName}
            />
          ))}
      </NavSection>

      {/* Module Marketplace */}
      <NavItem icon={<Package />} to="/modules/marketplace" label="+ Add Modules" />
    </div>
  );
};
```

---

### **Phase 5: Tier 3 Customer Modules (Week 11-14)**

#### 5.1 Customer Module Template
```python
# backend/app/tier_3/british_council/service.py
from app.tier_2.document_intelligence.docu_extract_service import DocuExtractService
from app.tier_2.hr_talent.talent_search_service import TalentSearchService

class BritishCouncilService:
    """
    Customer-specific implementation for British Council.
    Extends Tier 2 modules with custom business logic.
    """

    def __init__(self):
        self.docu_extract = DocuExtractService()
        self.talent_search = TalentSearchService()
        self.custom_fields = ["course_code", "accreditation_status"]

    async def process_application(self, doc_id: str):
        """Custom application processing workflow"""
        # 1. Extract standard fields (Tier 2)
        standard_data = await self.docu_extract.extract(doc_id)

        # 2. Extract custom British Council fields
        custom_data = await self._extract_custom_fields(doc_id)

        # 3. Apply custom business rules
        validated_data = await self._apply_bc_rules(standard_data, custom_data)

        return validated_data
```

#### 5.2 Customer Configuration
```yaml
# backend/app/tier_3/british_council/config.yaml
customer:
  name: "British Council"
  id: "british-council"
  tier: "tier_3"

extends_modules:
  - document_intelligence
  - hr_talent

custom_fields:
  - name: "course_code"
    type: "string"
    required: true
  - name: "accreditation_status"
    type: "enum"
    values: ["pending", "approved", "rejected"]

integrations:
  - name: "british_council_api"
    type: "rest"
    base_url: "https://api.britishcouncil.org"
    auth_type: "oauth2"

ui_customization:
  logo: "british_council_logo.png"
  primary_color: "#003366"
  theme: "professional"
```

---

## 🎨 UI/UX Design

### Main Navigation Structure
```
┌─────────────────────────────────────────────────┐
│ 🏠 Home                                         │
│ 💬 Chat                                         │
│ 📤 Upload                                       │
│ 🔍 Search                                       │
├─────────────────────────────────────────────────┤
│ 🏢 DOMAIN VERTICALS                             │
│ ├─ 🏗️ Construction (3)                          │
│ │   ├─ Planning Classifier                     │
│ │   ├─ Mine Scope Analyzer                     │
│ │   └─ Project Estimator ✓                     │
│ ├─ 📄 Document Intelligence (3)                 │
│ │   ├─ Docu-Extract                            │
│ │   ├─ Relation Extractor                      │
│ │   └─ Generic RAG                             │
│ ├─ 💼 Procurement (4)                           │
│ │   ├─ Tender Matcher                          │
│ │   ├─ Vendor Recommender                      │
│ │   ├─ Tender Intelligence                     │
│ │   └─ Spend Smart                             │
│ ├─ 👥 HR & Talent (3)                           │
│ │   ├─ Talent Search                           │
│ │   ├─ Skills Matcher                          │
│ │   └─ Talent Pulse Dashboard                  │
│ ├─ 🌾 Agriculture (2)                           │
│ ├─ 📧 Marketing (2)                             │
│ ├─ 🏷️ E-commerce (1)                            │
│ ├─ 🚢 Maritime (1)                              │
│ └─ 🔍 Analytics (4)                             │
├─────────────────────────────────────────────────┤
│ 🎯 CUSTOMER-SPECIFIC                            │
│ ├─ British Council                              │
│ ├─ CRU                                          │
│ ├─ Grant Thornton                               │
│ ├─ GT Motive                                    │
│ └─ Solera                                       │
├─────────────────────────────────────────────────┤
│ 📦 Module Marketplace                           │
│ ⚙️ Settings                                     │
│ 👤 Profile                                      │
└─────────────────────────────────────────────────┘
```

### Module Marketplace Screen
```
┌─────────────────────────────────────────────────────────────┐
│  AI Module Marketplace                        [ Verticals | Customer-Specific ]
│
│  🏗️ Construction & Infrastructure
│  ┌───────────┐ ┌───────────┐ ┌───────────┐
│  │ Planning  │ │ Mine Scope│ │ Project   │ ✓ Enabled
│  │ Classifier│ │ Analyzer  │ │ Estimator │
│  │ [Install] │ │ [Install] │ │ [Enabled] │
│  └───────────┘ └───────────┘ └───────────┘
│
│  📄 Document Intelligence
│  ┌───────────┐ ┌───────────┐ ┌───────────┐
│  │ Docu-     │ │ Relation  │ │ Generic   │
│  │ Extract   │ │ Extractor │ │ RAG       │
│  │ [Install] │ │ [Install] │ │ [Install] │
│  └───────────┘ └───────────┘ └───────────┘
│
│  💼 Procurement & Finance
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐
│  │ Tender    │ │ Vendor    │ │ Tender    │ │ Spend     │
│  │ Matcher   │ │ Recommend │ │ Intel     │ │ Smart     │
│  │ [Install] │ │ [Install] │ │ [Install] │ │ [Install] │
│  └───────────┘ └───────────┘ └───────────┘ └───────────┘
│
│  ... (more categories)
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 Module Lifecycle

### Installation Flow
```
1. User clicks [Install] on module card
   ↓
2. Backend validates dependencies (Tier 1 services available?)
   ↓
3. Create database entry in skill_modules table
   ↓
4. Mount module routes to FastAPI app
   ↓
5. Return module metadata to frontend
   ↓
6. Frontend adds module to sidebar navigation
   ↓
7. Module status: "enabled"
```

### Configuration Flow
```
1. User clicks module settings icon
   ↓
2. Load module config from database
   ↓
3. Display configuration form (per module schema)
   ↓
4. User updates settings
   ↓
5. Validate configuration
   ↓
6. Save to module_activations.config_override
   ↓
7. Reload module with new config
```

### Uninstallation Flow
```
1. User clicks [Disable] on enabled module
   ↓
2. Unmount module routes from FastAPI app
   ↓
3. Update skill_modules.status = 'disabled'
   ↓
4. Frontend removes from sidebar
   ↓
5. Module remains in database (can re-enable)
```

---

## 🔧 Technical Implementation Details

### Module Auto-Discovery
```python
# backend/app/tier_2/__init__.py
import os
import importlib
from pathlib import Path

def discover_modules():
    """Auto-discover and register all Tier 2 modules"""
    tier_2_path = Path(__file__).parent
    modules = {}

    for category_dir in tier_2_path.iterdir():
        if category_dir.is_dir() and not category_dir.name.startswith('_'):
            module_file = category_dir / "routes.py"
            if module_file.exists():
                # Import module
                module_path = f"app.tier_2.{category_dir.name}.routes"
                module = importlib.import_module(module_path)
                modules[category_dir.name] = {
                    "router": module.router,
                    "metadata": module.metadata if hasattr(module, 'metadata') else {}
                }

    return modules
```

### Dynamic Route Mounting
```python
# backend/app/main.py
from app.tier_2 import discover_modules

# Auto-mount all enabled Tier 2 modules
tier_2_modules = discover_modules()
for module_name, module_data in tier_2_modules.items():
    # Check if module is enabled in database
    if await is_module_enabled(module_name):
        app.include_router(module_data["router"])
        logger.info(f"Mounted Tier 2 module: {module_name}")
```

---

## 📊 Success Metrics

### Technical Metrics
- **Module Installation Time**: < 5 seconds
- **Module Response Time**: < 2 seconds (same as Tier 1)
- **Module Isolation**: No cross-module dependencies (only Tier 1)
- **Test Coverage**: >80% for each module

### Business Metrics
- **Time to Deploy New Vertical**: < 1 week
- **Customer Customization Time**: < 3 days
- **Module Adoption Rate**: Track installations per category
- **Module Performance**: Track usage, latency, errors per module

---

## 🚀 Next Steps

### Immediate Actions (This Week)
1. ✅ Review and approve this plan
2. Create database migration for module management (Phase 1.2)
3. Implement ModuleRegistry class (Phase 1.1)
4. Create frontend ModuleSelector component (Phase 1.3)

### Short Term (Next 2 Weeks)
1. Implement first Tier 2 module: Docu-Extract (Phase 3)
2. Create module template and generator script
3. Update UI with module marketplace

### Medium Term (Next 2 Months)
1. Implement 5 high-priority modules
2. Add 2 customer-specific modules
3. Load testing and performance optimization

### Long Term (Next 6 Months)
1. Complete all 24 Tier 2 modules
2. Complete all 6 Tier 3 customer modules
3. Module marketplace with analytics
4. Self-service module configuration

---

## 📝 Documentation Plan

1. **Module Developer Guide** - How to create new modules
2. **Module User Guide** - How to install and use modules
3. **API Reference** - All module endpoints
4. **Configuration Reference** - Module settings
5. **Migration Guide** - Tier 1 → Tier 2/3 mapping

---

**Created**: 2026-01-01
**Last Updated**: 2026-01-01
**Version**: 1.0
**Status**: **READY FOR APPROVAL** ✅
