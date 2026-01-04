# Module Configuration Integration Issue & Fix

> **Date**: 2026-01-03
> **Priority**: HIGH - Affects all 30 domain vertical modules
> **Status**: POC Complete (1/30) - Pattern Validated ✅
> **Impact**: POCConfigManager configurations not applied to LLM calls
> **Rollout Guide**: See `MODULE_CONFIG_INTEGRATION_ROLLOUT_GUIDE.md`

---

## 🐛 Issue Description

### Problem
The POCConfigManager UI successfully saves module configurations (prompts, models, parameters, thresholds, etc.) to the backend database at `/api/v1/module-config/modules/{module_name}`, but these configurations are **NOT being loaded and applied** when making actual LLM calls through the module analyze endpoints.

### Current Behavior
1. User opens POCConfigManager for a module (e.g., `sentiment_social`)
2. User configures LLM settings (model, temperature, max_tokens, prompts, etc.)
3. Configuration is successfully saved to backend (`PUT /api/v1/module-config/modules/sentiment_social`)
4. User makes analyze request (`POST /api/v1/modules/sentiment-social/analyze`)
5. **ISSUE**: Backend service uses default/hardcoded config instead of saved configuration

### Root Cause
Frontend panels send minimal request bodies (e.g., `{ text: textInput }`) without any reference to module configuration. Backend services instantiate without loading the saved module config.

**Example:**
```typescript
// Frontend (SentimentSocialPanel.tsx line 31-35)
const response = await axios.post(
  'http://localhost:8000/api/v1/modules/sentiment-social/analyze',
  { text: textInput },  // ❌ No module_name or config reference
  { headers: { 'Content-Type': 'application/json' } }
)
```

**Backend (sentiment_social_routes.py line 110-111):**
```python
service = SentimentSocialService(db, settings)  // ❌ Not loading module config
result = await service.analyze_social_sentiment(request)
```

---

## 📊 Scope of Impact

### Affected Modules (30 Total)

**Analytics (4 modules)**:
- customer_churn
- financial_anomaly
- predictive_analytics
- sales_performance

**Construction (4 modules)**:
- mine_scope
- planning_classifier
- building_metrics
- estimator_au

**Agriculture (2 modules)**:
- agri_taxonomy
- agronomy_decision

**Marketing (2 modules)**:
- campaign_optimizer
- sentiment_social

**HR/Talent (3 modules)**:
- talent_pulse
- talent_search
- taxonomy_skillmatch

**Procurement (4 modules)**:
- matcher
- spend_smart
- tender_intelligence
- vendor_recommendation

**Document Intelligence (2 modules)**:
- generic_rag
- relation_extractor

**Legal (1 module)**:
- legal_document

**Real Estate (1 module)**:
- real_estate

**Healthcare (1 module)**:
- healthcare_diagnostics

**Industry Verticals (2 modules)**:
- educational_content (education)
- insurance_risk (insurance)

**Advanced Capabilities (2 modules)**:
- code_analysis
- multilingual_translator

**E-Commerce (1 module)**:
- product_recommendation

**Maritime (1 module)**:
- maritime_logistics

---

## 🔧 Solution Approach

### Option 1: Backend Auto-Load (RECOMMENDED)
Backend automatically loads module config based on the endpoint route.

**Advantages**:
- No frontend changes needed
- Cleaner API design
- Follows REST principles (URL defines resource)

**Implementation**:
1. Extract module_name from request path in route handler
2. Load config from database using existing module_config service
3. Pass config to service constructor
4. Service applies config to LLM calls

**Example Fix:**
```python
# backend/app/tier_2/marketing/sentiment_social_routes.py

from app.services.module_config_service import get_module_config

@router.post("/analyze", response_model=SentimentSocialResponse)
async def analyze_social_sentiment(
    request: SentimentSocialRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings)
):
    try:
        # Load saved module configuration
        module_config = await get_module_config(
            db,
            module_name="sentiment_social",
            user_id=request.user_id  # Optional user-specific override
        )

        # Pass config to service
        service = SentimentSocialService(db, settings, config=module_config)
        result = await service.analyze_social_sentiment(request)

        return result
    except Exception as e:
        ...
```

### Option 2: Frontend Explicit Passing
Frontend includes module_name in every request body.

**Advantages**:
- Explicit and traceable
- Allows request-level overrides

**Disadvantages**:
- Requires updating all 30 panel components
- More verbose API calls

---

## 📋 Implementation Plan

### Phase 1: Backend Infrastructure ✅
- [x] Module configuration database models exist
- [x] Module configuration API routes exist (`/api/v1/module-config/`)
- [x] POCConfigManager UI working

### Phase 2: Service Integration (IN PROGRESS)
**Step 1**: Create Module Config Helper
```python
# backend/app/services/module_config_helper.py
async def load_module_config(
    db: Session,
    module_name: str,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Load module configuration from database.
    Returns merged config (base + user overrides).
    """
    pass
```

**Step 2**: Update Service Base Classes
Add `config` parameter to all service constructors:
```python
class SentimentSocialService:
    def __init__(self, db: Session, settings: Settings, config: Optional[Dict] = None):
        self.db = db
        self.settings = settings
        self.config = config or {}  # Use passed config or empty dict
```

**Step 3**: Apply Config in LLM Calls
Services use `self.config` for LLM parameters:
```python
async def call_llm(self, prompt: str):
    model = self.config.get('llm', {}).get('primary', {}).get('model', 'gpt-4o-mini')
    temperature = self.config.get('llm', {}).get('primary', {}).get('temperature', 0.2)

    response = await openai_client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=[...]
    )
```

**Step 4**: Update All 30 Module Routes
For each module route file, add config loading:
- Analytics: 4 files
- Construction: 4 files
- Agriculture: 2 files
- Marketing: 2 files
- HR/Talent: 3 files
- Procurement: 4 files
- Document Intelligence: 2 files
- Legal: 1 file
- Real Estate: 1 file
- Healthcare: 1 file
- Industry Verticals: 2 files
- Advanced Capabilities: 2 files
- E-Commerce: 1 file
- Maritime: 1 file

**Total**: 29 route files (some modules share routes)

### Phase 3: Testing & Validation
1. Create test module configuration
2. Save via POCConfigManager
3. Make analyze request
4. Verify correct model/parameters used in LLM call
5. Validate prompts applied correctly
6. Test user-specific overrides

---

## 🧪 Test Plan

### Test Case 1: Model Selection
1. Set module to use `claude-3-5-sonnet-latest` in POCConfigManager
2. Make analyze request
3. Verify backend logs show Claude model being called (not default GPT)

### Test Case 2: Temperature Override
1. Set temperature to 0.8 (creative) in POCConfigManager
2. Make analyze request
3. Verify LLM call includes `temperature=0.8`

### Test Case 3: Custom Prompts
1. Modify system prompt in POCConfigManager
2. Make analyze request
3. Verify custom prompt sent to LLM

### Test Case 4: Retrieval Parameters
1. Set `top_k=20`, `rerank_top_k=10` in POCConfigManager
2. Make RAG query
3. Verify retrieval uses custom k values

---

## 📝 Files to Modify

### Backend Routes (29 files)
```
backend/app/tier_2/analytics/
  - customer_churn_routes.py
  - financial_anomaly_routes.py
  - predictive_analytics_routes.py
  - sales_performance_routes.py

backend/app/tier_2/construction/
  - mine_scope_routes.py
  - planning_classifier_routes.py
  - building_metrics_routes.py (if exists)
  - estimator_au_routes.py

backend/app/tier_2/agriculture/
  - agri_taxonomy_routes.py
  - agronomy_decision_routes.py

backend/app/tier_2/marketing/
  - campaign_optimizer_routes.py
  - sentiment_social_routes.py

backend/app/tier_2/hr_talent/
  - talent_pulse_routes.py
  - talent_search_routes.py
  - taxonomy_skillmatch_routes.py

backend/app/tier_2/procurement/
  - matcher_routes.py
  - spend_smart_routes.py
  - tender_intelligence_routes.py
  - vendor_recommendation_routes.py

backend/app/tier_2/document_intelligence/
  - generic_rag_routes.py
  - relation_extractor_routes.py

backend/app/tier_2/industry_verticals/
  - legal_document_routes.py
  - real_estate_routes.py
  - healthcare_diagnostics_routes.py
  - educational_content_routes.py (if exists)
  - insurance_risk_routes.py (if exists)

backend/app/tier_2/advanced_capabilities/
  - code_analysis_routes.py
  - multilingual_translator_routes.py

backend/app/tier_2/ecommerce/
  - product_recommendation_routes.py

backend/app/tier_2/maritime/
  - maritime_logistics_routes.py
```

### Backend Services (29+ files)
All corresponding `*_service.py` files need constructor updates.

---

## ✅ Success Criteria

1. **Configuration Persistence**: Saved configs remain in database
2. **Configuration Loading**: Services load correct config automatically
3. **LLM Parameter Application**: LLM calls use configured model, temperature, etc.
4. **Prompt Application**: Custom prompts sent to LLM
5. **Retrieval Parameters**: RAG queries use configured top_k, rerank_top_k
6. **User Overrides**: User-specific configs override global defaults
7. **Backward Compatibility**: Modules without saved config use sensible defaults

---

## ✅ POC Implementation Complete

### Files Created/Modified (sentiment_social)

**Helper Service** (shared by all 30 modules):
- ✅ `backend/app/services/module_config_helper.py` - Config loading utilities

**POC Module** (sentiment_social):
- ✅ `backend/app/tier_2/marketing/sentiment_social_service.py` - Service accepts and uses config
- ✅ `backend/app/tier_2/marketing/sentiment_social_routes.py` - Routes load and pass config

**Documentation**:
- ✅ `docs/implementation/MODULE_CONFIG_INTEGRATION_ROLLOUT_GUIDE.md` - Complete rollout guide

### Changes Summary

**Service Pattern**:
```python
def __init__(self, db: Session, settings: Settings, config: Optional[Dict[str, Any]] = None):
    self.config = config or {}
    # ...

# In LLM calls:
llm_config = self.config.get('llm', {}).get('default', {})
model = llm_config.get('model', 'gpt-4o-mini')
temperature = llm_config.get('temperature', 0.2)
max_tokens = llm_config.get('max_tokens', 1000)
```

**Routes Pattern**:
```python
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.module_config_helper import load_module_config

@router.post("/analyze")
async def analyze(request, db: AsyncSession = Depends(get_db), settings = Depends(get_settings)):
    module_config = await load_module_config(db, "sentiment_social")
    service = SentimentSocialService(db, settings, config=module_config)
    # ...
```

**Result**: Module now respects POCConfigManager settings! ✅

---

## 🚀 Next Steps

1. ✅ Document issue (this file)
2. ✅ Create module config helper service
3. ✅ Update 1 module as proof of concept (sentiment_social)
4. ✅ Test POC and create rollout guide
5. ⏳ Roll out to remaining 29 modules systematically (see rollout guide)
6. ⏳ Create validation test suite
7. ⏳ Update main documentation

---

**End of Module Configuration Integration Issue Document**
