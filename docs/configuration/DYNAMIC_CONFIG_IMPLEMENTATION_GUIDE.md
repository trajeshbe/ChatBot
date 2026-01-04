# Dynamic Configuration Implementation Guide

**Date:** 2026-01-03
**Status:** ✅ Core Infrastructure Complete
**Purpose:** Enable UI-based dynamic configuration for all Domain Verticals (Tier 2) and Customer Solutions (Tier 3)

---

## 📋 Implementation Summary

This implementation brings the **Dynamic POC Configuration Architecture** to life, enabling:

✅ **Zero-code configuration** - Configure any module via UI in minutes
✅ **A/B testing** - Test different prompts, models, and parameters
✅ **Customer self-service** - Allow customers to tune their own deployment
✅ **Faster iteration** - No code changes or deployments required
✅ **Version control** - Track all configuration changes over time
✅ **Multi-tenancy ready** - Per-customer configurations with inheritance

---

## 🎯 What Was Implemented

### 1. Database Schema ✅

**File:** `backend/migrations/025_add_dynamic_configuration_tables.sql`

**Tables Created:**
- `module_configurations` - Base config for each Tier 2/3 module
- `module_user_overrides` - Per-user/customer overrides
- `config_versions` - Version history (audit trail)
- `config_schemas` - JSON schemas for validation
- `config_templates` - Reusable templates
- `config_audit_logs` - Detailed change tracking

**Features:**
- JSONB storage for flexible configuration
- GIN indexes for fast querying
- Foreign key relationships with users
- Version tracking with diffs
- A/B testing support

### 2. Database Models ✅

**File:** `backend/app/models/module_configuration.py`

**Models:**
- `ModuleConfiguration` - SQLAlchemy ORM for module configs
- `ModuleUserOverride` - User-specific overrides
- `ConfigVersion` - Version history
- `ConfigSchema` - Validation schemas
- `ConfigTemplate` - Configuration templates
- `ConfigAuditLog` - Audit trail

### 3. Pydantic Schemas ✅

**File:** `backend/app/schemas/module_config_schemas.py`

**Schemas:**
- `LLMConfig` - LLM model configuration
- `PromptConfig` - Prompt templates
- `ParametersConfig` - General parameters
- `ThresholdsConfig` - Confidence thresholds
- `ScoringConfig` - Scoring weights
- `RetrievalConfig` - Vector search configuration
- `FeaturesConfig` - Feature flags
- `ModuleConfigData` - Complete module config
- Request/Response models for all API operations

### 4. POCConfigService ✅

**File:** `backend/app/services/poc_config_service.py`

**Features:**
- 3-level configuration hierarchy (Global → Module → User)
- Deep merge algorithm for config inheritance
- Configuration validation against JSON schemas
- Version management with restore capability
- Template-based configuration creation
- In-memory caching for performance
- Comprehensive audit logging

**Key Methods:**
```python
# Get merged configuration with 3-level resolution
config = await poc_config_service.get_config(
    db=db,
    module_name="talent_search",
    user_id=user_id
)

# Update module configuration (creates new version)
await poc_config_service.update_module_config(
    db=db,
    module_name="talent_search",
    updates={"llm": {"model": "gpt-4"}},
    changed_by=user_id,
    change_reason="Upgrading to GPT-4"
)

# Set user-specific overrides
await poc_config_service.set_user_override(
    db=db,
    module_name="talent_search",
    user_id=user_id,
    overrides={"llm": {"temperature": 0.5}}
)
```

### 5. API Routes ✅

**File:** `backend/app/api/routes/module_config_routes.py`

**Endpoints:**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/module-config/modules` | GET | List all modules |
| `/api/v1/module-config/modules/{name}` | GET | Get module config (with overrides) |
| `/api/v1/module-config/modules` | POST | Create new module config |
| `/api/v1/module-config/modules/{name}` | PUT | Update module config |
| `/api/v1/module-config/modules/{name}/overrides` | POST | Set user overrides |
| `/api/v1/module-config/modules/{name}/overrides` | DELETE | Clear user overrides |
| `/api/v1/module-config/modules/{name}/versions` | GET | Get version history |
| `/api/v1/module-config/modules/{name}/versions/{v}/restore` | POST | Restore previous version |
| `/api/v1/module-config/templates` | GET | List templates |
| `/api/v1/module-config/modules/{name}/from-template` | POST | Create from template |
| `/api/v1/module-config/modules/{name}/validate` | POST | Validate config |

**Registered in:** `backend/app/main.py:2672-2678`

### 6. Frontend POCConfigManager Component ✅

**File:** `frontend/src/components/POCConfigManager.tsx`

**Features:**
- 6-tab interface: Prompts, Models, Parameters, Thresholds, Scoring, Advanced
- Real-time change tracking
- Auto-save with unsaved changes warning
- Error handling and success messages
- Responsive modal design
- Support for all configuration types

**Tabs:**

1. **📝 Prompts Tab**
   - Edit system prompts
   - Edit user prompt templates
   - Support for variable placeholders `{variable_name}`

2. **🤖 Models Tab**
   - Select LLM model per stage
   - Configure temperature (slider)
   - Configure max_tokens
   - Support for multiple stages (e.g., profile_analyzer, query_processor)

3. **⚙️ Parameters Tab**
   - Retrieval configuration (top_k, rerank_top_k)
   - Custom parameters (batch_size, timeout, etc.)

4. **🎯 Thresholds Tab**
   - Confidence thresholds (sliders 0-1)
   - Min confidence, high quality, match thresholds

5. **📊 Scoring Tab**
   - Scoring weights (semantic, keyword, etc.)
   - Scoring factors (recency, relevance, etc.)
   - Visual percentage display

6. **🔍 Advanced Tab**
   - Feature flags (checkboxes)
   - enable_caching, enable_debug_logging, etc.

**Usage:**
```tsx
import { POCConfigManager } from '@/components/POCConfigManager';

// In your component
<POCConfigManager
  moduleName="talent_search"
  userId={currentUser.id}
  onClose={() => setShowConfig(false)}
/>
```

---

## 🚀 How to Use

### Step 1: Run Database Migration

```bash
cd backend

# Connect to PostgreSQL
docker-compose exec postgres psql -U postgres -d ragchatbot

# Run the migration SQL file
\i /path/to/migrations/025_add_dynamic_configuration_tables.sql

# Or use psql directly
psql -U postgres -d ragchatbot -f migrations/025_add_dynamic_configuration_tables.sql

# Verify tables created
\dt module_*
\dt config_*
```

### Step 2: Create Module Configuration

You can create configurations via API or directly in the database.

**Option A: Via API (Recommended)**

```bash
curl -X POST http://localhost:8000/api/v1/module-config/modules \
  -H "Content-Type: application/json" \
  -d '{
    "module_name": "talent_search",
    "display_name": "Talent Search & Matching",
    "description": "AI-powered talent search and job matching",
    "module_type": "tier2_domain_vertical",
    "category": "hr_talent",
    "config": {
      "llm": {
        "default": {
          "model": "gpt-4o-mini",
          "temperature": 0.2,
          "max_tokens": 1000
        }
      },
      "prompts": {
        "system": {
          "main": "You are an AI assistant specialized in talent matching."
        },
        "user": {
          "query_template": "Find candidates for: {job_description}"
        }
      },
      "thresholds": {
        "min_confidence": 0.7,
        "high_match": 0.9
      },
      "scoring": {
        "weights": {
          "skills_match": 0.6,
          "experience_match": 0.4
        }
      },
      "features": {
        "enable_caching": true,
        "enable_debug_logging": false
      }
    }
  }'
```

**Option B: Directly in Database**

```sql
INSERT INTO module_configurations (module_name, display_name, module_type, category, config)
VALUES (
    'talent_search',
    'Talent Search & Matching',
    'tier2_domain_vertical',
    'hr_talent',
    '{
        "llm": {
            "default": {
                "model": "gpt-4o-mini",
                "temperature": 0.2,
                "max_tokens": 1000
            }
        },
        "prompts": {
            "system": {
                "main": "You are an AI assistant specialized in talent matching."
            }
        },
        "thresholds": {
            "min_confidence": 0.7
        },
        "features": {
            "enable_caching": true
        }
    }'::jsonb
);
```

### Step 3: Use Configuration in Backend Service

**Before (Hardcoded):**
```python
# backend/app/tier_2/hr_talent/talent_search_service.py

response = await llm_service.generate_response(
    prompt,
    model="gpt-4o-mini",      # HARDCODED
    temperature=0.2,           # HARDCODED
    max_tokens=1000            # HARDCODED
)

if confidence > 0.7:  # HARDCODED
    # ...
```

**After (Dynamic):**
```python
from app.services.poc_config_service import poc_config_service

class TalentSearchService:
    def __init__(self, db: Session, user_id: Optional[str] = None):
        self.db = db
        self.user_id = user_id
        self.config = None

    async def _load_config(self):
        """Load configuration with user overrides"""
        if not self.config:
            self.config = await poc_config_service.get_config(
                db=self.db,
                module_name="talent_search",
                user_id=self.user_id
            )

    async def search_candidates(self, query: str):
        await self._load_config()

        # Get LLM settings from config
        llm_config = self.config['llm']['default']

        response = await llm_service.generate_response(
            prompt,
            model=llm_config['model'],               # FROM CONFIG
            temperature=llm_config['temperature'],   # FROM CONFIG
            max_tokens=llm_config['max_tokens']      # FROM CONFIG
        )

        # Get threshold from config
        min_confidence = self.config['thresholds']['min_confidence']

        if confidence > min_confidence:  # FROM CONFIG
            # ...
```

### Step 4: Integrate UI in Frontend

Add a configuration button to your module UI:

```tsx
// frontend/src/components/tier2/TalentSearchModule.tsx

import React, { useState } from 'react';
import { POCConfigManager } from '@/components/POCConfigManager';

export const TalentSearchModule: React.FC = () => {
  const [showConfig, setShowConfig] = useState(false);

  return (
    <div className="module-container">
      <div className="module-header">
        <h1>Talent Search & Matching</h1>
        <button
          onClick={() => setShowConfig(true)}
          className="config-button"
        >
          ⚙️ Configure Module
        </button>
      </div>

      {showConfig && (
        <POCConfigManager
          moduleName="talent_search"
          userId={currentUser.id}
          onClose={() => setShowConfig(false)}
        />
      )}

      {/* Existing module UI */}
      <div className="module-content">
        {/* ... */}
      </div>
    </div>
  );
};
```

---

## 📝 Configuration Examples

### Example 1: British Council Course Recommendations

```json
{
  "llm": {
    "profile_analyzer": {
      "model": "gpt-4o-mini",
      "temperature": 0.0,
      "max_tokens": 500
    },
    "course_recommender": {
      "model": "gpt-4o-mini",
      "temperature": 0.2,
      "max_tokens": 800
    }
  },
  "prompts": {
    "system": {
      "profile_extraction": "Extract a structured user profile from this text...",
      "course_recommendation": "Based on the user profile, recommend courses..."
    },
    "user": {
      "query_template": "User background: {background}\nFind courses matching..."
    }
  },
  "scoring": {
    "weights": {
      "semantic": 0.6,
      "profile": 0.4
    },
    "factors": {
      "education_match": 0.3,
      "format_match": 0.2,
      "availability_match": 0.2,
      "skill_intersection": 0.3
    }
  },
  "thresholds": {
    "match_threshold": 0.8,
    "high_match": 0.9
  },
  "retrieval": {
    "initial_top_k": 10,
    "rerank_top_k": 5,
    "final_recommendations": 5
  },
  "features": {
    "enable_reranking": true,
    "enable_profile_extraction": true,
    "enable_caching": true
  }
}
```

### Example 2: Procurement Matcher

```json
{
  "llm": {
    "default": {
      "model": "gpt-4o-mini",
      "temperature": 0.1,
      "max_tokens": 1500
    }
  },
  "prompts": {
    "system": {
      "matcher": "You are an AI specialized in matching RFPs with suppliers."
    },
    "user": {
      "rfp_analysis": "Analyze this RFP: {rfp_text}\nFind matching suppliers."
    }
  },
  "thresholds": {
    "min_match_score": 0.75,
    "high_confidence": 0.9
  },
  "scoring": {
    "weights": {
      "capability_match": 0.5,
      "experience": 0.3,
      "cost": 0.2
    }
  },
  "retrieval": {
    "top_k": 20,
    "rerank_top_k": 10
  },
  "features": {
    "enable_semantic_search": true,
    "enable_price_analysis": true
  }
}
```

### Example 3: GT Motive (Automotive Parts)

```json
{
  "llm": {
    "part_extractor": {
      "model": "gpt-4o-mini",
      "temperature": 0.0,
      "max_tokens": 800
    }
  },
  "prompts": {
    "system": {
      "part_extraction": "Extract automotive part codes and descriptions..."
    }
  },
  "parameters": {
    "part_code_patterns": [
      "\\b[A-Z]{3}\\d{4}\\b",
      "\\b\\d{6}[A-Z]{2}\\b"
    ]
  },
  "thresholds": {
    "extraction_confidence": 0.8,
    "part_match_threshold": 0.85
  },
  "features": {
    "enable_regex_extraction": true,
    "enable_fuzzy_matching": true
  }
}
```

---

## 🔄 Migration Checklist for Existing Modules

Use this checklist to migrate an existing Tier 2/3 module to dynamic configuration:

### Phase 1: Audit ✅
- [ ] Identify all hardcoded LLM models
- [ ] Identify all hardcoded prompts
- [ ] Identify all hardcoded hyperparameters
- [ ] Identify all hardcoded thresholds
- [ ] Identify all hardcoded regex patterns
- [ ] Identify all hardcoded scoring weights
- [ ] Document current behavior (for testing)

### Phase 2: Configuration Design ✅
- [ ] Design configuration JSON structure
- [ ] Create JSON schema for validation (optional)
- [ ] Define default values
- [ ] Test configuration with sample data

### Phase 3: Database Setup ✅
- [ ] Insert module configuration record (via API or SQL)
- [ ] Verify config retrieval works
- [ ] Test config merging with user overrides

### Phase 4: Code Refactoring ✅
- [ ] Add `poc_config_service` import
- [ ] Add `_load_config()` method to service class
- [ ] Replace all hardcoded models with `config['llm'][...]['model']`
- [ ] Replace all hardcoded prompts with `config['prompts'][...]`
- [ ] Replace all hardcoded parameters with `config['parameters'][...]`
- [ ] Replace all hardcoded thresholds with `config['thresholds'][...]`
- [ ] Add error handling for missing config

### Phase 5: Testing ✅
- [ ] Unit tests: config loading works
- [ ] Integration tests: same behavior as before
- [ ] Integration tests: config updates work
- [ ] Integration tests: user overrides work
- [ ] Performance tests: no regression

### Phase 6: Frontend Integration ✅
- [ ] Add "⚙️ Configure Module" button to module UI
- [ ] Import and use `POCConfigManager` component
- [ ] Test all 6 tabs work correctly
- [ ] Test saving/resetting changes

### Phase 7: Documentation ✅
- [ ] Update module README
- [ ] Document configuration options
- [ ] Add troubleshooting guide

---

## 🎯 Next Steps

### Immediate (This Week)

1. **Run Database Migration**
   ```bash
   docker-compose exec postgres psql -U postgres -d ragchatbot -f migrations/025_add_dynamic_configuration_tables.sql
   ```

2. **Create Configurations for All Modules**
   - Tier 2 Domain Verticals (30 modules)
   - Tier 3 Customer Solutions (6 modules)
   - See [Module List](#module-list) below

3. **Refactor Services to Use Dynamic Config**
   - Start with highest-priority modules
   - Follow the migration checklist

### Week 2-3: Tier 3 Customer Solutions

Migrate all 6 Customer Solutions:
- British Council (`british_council`)
- CRU Mining (`cru`)
- Grant Thornton (`grant_thornton`)
- GT Motive (`gt_motive`)
- Solera (`solera`)
- Construction Monitor (`construction_monitor`)

### Week 4-6: Tier 2 Domain Verticals

Migrate all 30 Domain Vertical modules (see list below)

### Week 7: Advanced Features

- Template library expansion
- A/B testing framework UI
- Configuration diff viewer
- Bulk configuration import/export

---

## 📊 Module List

### Tier 3 Customer Solutions (6)

| Module Name | Display Name | Category | Priority |
|-------------|--------------|----------|----------|
| `british_council` | British Council Course Recommendations | education | High |
| `cru` | CRU Mining Intelligence | mining | High |
| `grant_thornton` | Grant Thornton Financial Extraction | finance | High |
| `gt_motive` | GT Motive Automotive Parts | automotive | High |
| `solera` | Solera Claims Processing | insurance | High |
| `construction_monitor` | Construction Monitor | construction_monitoring | High |

### Tier 2 Domain Verticals (30)

#### Procurement (4)
- `procurement_matcher` - RFP/Supplier Matching
- `vendor_recommendation` - Vendor Recommendation
- `tender_intelligence` - Tender Intelligence
- `spend_smart` - Spend Analytics

#### HR & Talent (3)
- `talent_search` - Talent Search & Matching
- `taxonomy_skillmatch` - Taxonomy-Based Skill Matching
- `talent_pulse` - Talent Analytics

#### Agriculture (2)
- `agri_taxonomy` - Agricultural Taxonomy
- `agronomy_decision` - Agronomy Decision Support

#### Analytics (4)
- `predictive_analytics` - Predictive Analytics
- `customer_churn` - Customer Churn Prediction
- `sales_performance` - Sales Performance Analytics
- `financial_anomaly` - Financial Anomaly Detection

#### Construction (3)
- `planning_classifier` - Planning Application Classifier
- `mine_scope` - Mine Scope Analysis
- `estimator_au` - Australian Cost Estimator

#### Document Intelligence (2)
- `generic_rag` - Generic RAG
- `relation_extractor` - Relation Extraction

#### E-commerce (1)
- `product_recommendation` - Product Recommendation

#### Industry Verticals (5)
- `healthcare_diagnostics` - Healthcare Diagnostics
- `legal_document` - Legal Document Analysis
- `real_estate` - Real Estate Intelligence
- `insurance_risk` - Insurance Risk Assessment
- `educational_content` - Educational Content Generation

#### Maritime (1)
- `maritime_logistics` - Maritime Logistics

#### Marketing (2)
- `sentiment_social` - Sentiment Analysis & Social Media
- `campaign_optimizer` - Campaign Optimization

#### Advanced Capabilities (2)
- `multilingual_translator` - Multilingual Translation
- `code_analysis` - Code Analysis & Review

---

## 🔒 Security Features

### 1. Access Control
- Only admins can modify global/module configurations
- Users can only override their own settings
- Role-based access control (RBAC) integration ready

### 2. Input Validation
- JSON schema validation for all configs
- Prompt sanitization (prevent injection)
- Range validation for numeric values

### 3. Audit Logging
- Full change history tracked
- Who, what, when, why recorded
- IP address and user agent logged
- Supports compliance and debugging

### 4. Rate Limiting
- Max 10 config updates per minute per user
- Prevents abuse and accidental floods

---

## 📈 Expected Benefits

### Technical Metrics
- ✅ 100% of hardcoded values moved to config
- ✅ < 100ms API response time for config retrieval
- ✅ > 99% config update success rate
- ✅ Zero-downtime deployments

### Business Metrics
- ✅ < 1 hour POC deployment time (from 2-5 days)
- ✅ 50% of config changes by customers (self-service)
- ✅ 10+ A/B experiments per month
- ✅ 30% reduction in support tickets

---

## 🐛 Troubleshooting

### Issue: Config not loading

**Symptom:** Module still uses hardcoded values

**Solution:**
1. Check if migration ran: `\dt module_configurations`
2. Check if config exists: `SELECT * FROM module_configurations WHERE module_name = 'your_module';`
3. Check backend logs for errors
4. Verify `poc_config_service` is imported and used

### Issue: Changes not saving

**Symptom:** UI shows success but config unchanged

**Solution:**
1. Check API response: Network tab in DevTools
2. Verify user permissions
3. Check for validation errors
4. Ensure database is writable

### Issue: Frontend shows empty config

**Symptom:** POCConfigManager opens but no fields visible

**Solution:**
1. Check browser console for errors
2. Verify API endpoint is responding
3. Check if config has required structure
4. Ensure CORS is configured correctly

---

## 📚 Related Documentation

- **Full Architecture:** `DYNAMIC_POC_CONFIGURATION_ARCHITECTURE.md`
- **Quick Reference:** `DYNAMIC_POC_CONFIG_QUICK_REFERENCE.md`
- **Database Schema:** `backend/migrations/025_add_dynamic_configuration_tables.sql`
- **API Documentation:** http://localhost:8000/api/docs (after starting backend)

---

## ✅ Implementation Checklist

- [x] Database schema created
- [x] Database models implemented
- [x] Pydantic schemas defined
- [x] POCConfigService implemented
- [x] API routes created
- [x] Routes registered in main.py
- [x] Frontend POCConfigManager built
- [x] Documentation completed
- [ ] Database migration run
- [ ] Module configurations created
- [ ] Services refactored to use config
- [ ] Frontend integration in all modules
- [ ] End-to-end testing
- [ ] Production deployment

---

**Last Updated:** 2026-01-03
**Status:** ✅ Core Infrastructure Complete - Ready for Module Migration
**Next:** Run database migration and start creating module configurations
