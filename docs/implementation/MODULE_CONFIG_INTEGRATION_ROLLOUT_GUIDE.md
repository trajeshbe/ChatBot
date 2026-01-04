# Module Configuration Integration - Rollout Guide

> **Date**: 2026-01-03
> **Status**: 1/30 modules complete (sentiment_social ✅)
> **Pattern**: Validated and ready for systematic rollout
> **Estimated Time**: ~10 minutes per module (5 hours total for 29 remaining)

---

## 🎯 Objective

Integrate POCConfigManager saved configurations into all 30 domain vertical modules so that LLM calls use user-configured settings instead of hardcoded values.

---

## ✅ Completed POC: sentiment_social

**Files Modified**:
1. ✅ `backend/app/services/module_config_helper.py` - Created helper (shared by all modules)
2. ✅ `backend/app/tier_2/marketing/sentiment_social_service.py` - Service updated
3. ✅ `backend/app/tier_2/marketing/sentiment_social_routes.py` - Routes updated

**Result**: LLM calls now use configured model, temperature, and max_tokens from POCConfigManager!

---

## 📋 3-Step Pattern (Repeat for Each Module)

### Step 1: Update Service (*_service.py)

**File Pattern**: `backend/app/tier_2/{category}/{module}_service.py`

**Changes Required**:

#### A. Update Constructor
```python
# BEFORE
def __init__(self, db: Session, settings: Settings):
    self.db = db
    self.settings = settings
    # ...

# AFTER
def __init__(self, db: Session, settings: Settings, config: Optional[Dict[str, Any]] = None):
    self.db = db
    self.settings = settings
    self.config = config or {}  # ✅ Store config
    # ...
```

#### B. Update LLM Calls
```python
# BEFORE
response = await self.llm_service.generate_response(
    prompt=prompt,
    model="gpt-4o-mini",       # ❌ Hardcoded
    temperature=0.2,           # ❌ Hardcoded
    max_tokens=1000            # ❌ Hardcoded
)

# AFTER
# Get LLM parameters from module config
llm_config = self.config.get('llm', {}).get('default', {})
model = llm_config.get('model', 'gpt-4o-mini')
temperature = llm_config.get('temperature', 0.2)
max_tokens = llm_config.get('max_tokens', 1000)

response = await self.llm_service.generate_response(
    prompt=prompt,
    model=model,               # ✅ From config
    temperature=temperature,   # ✅ From config
    max_tokens=max_tokens      # ✅ From config
)
```

**Tip**: Search for `llm_service.generate_response` or `openai` or `anthropic` calls

---

### Step 2: Update Routes (*_routes.py)

**File Pattern**: `backend/app/tier_2/{category}/{module}_routes.py`

**Changes Required**:

#### A. Update Imports
```python
# BEFORE
from sqlalchemy.orm import Session

# AFTER
from sqlalchemy.ext.asyncio import AsyncSession  # ✅ Correct type
```

```python
# ADD THIS IMPORT
from app.services.module_config_helper import load_module_config
```

#### B. Update Endpoint Type Hints
```python
# BEFORE
async def analyze(..., db: Session = Depends(get_db)):

# AFTER
async def analyze(..., db: AsyncSession = Depends(get_db)):  # ✅ Correct type
```

#### C. Load Config and Pass to Service
```python
# BEFORE
try:
    service = ModuleService(db, settings)
    result = await service.analyze(request)

# AFTER
try:
    # Load module configuration
    module_config = await load_module_config(db, "module_name")  # ✅ Use actual module name
    logger.info(f"✓ Loaded config for module_name")

    # Initialize service with config
    service = ModuleService(db, settings, config=module_config)  # ✅ Pass config
    result = await service.analyze(request)
```

---

### Step 3: Test Integration

1. **Start Backend**: `docker-compose up -d backend`
2. **Open POCConfigManager**: Navigate to module panel, click "Configure"
3. **Modify Config**: Change model to `claude-3-5-sonnet-latest`, temperature to `0.8`
4. **Save Config**: Click "Save Changes"
5. **Make Request**: Test analyze endpoint
6. **Check Logs**: Verify log shows `✓ Using module config with model: claude-3-5-sonnet-latest`

---

## 📊 Module Checklist (30 Total)

### Marketing (2 modules)
- [x] ✅ sentiment_social (POC COMPLETE)
- [ ] campaign_optimizer

### Analytics (4 modules)
- [ ] customer_churn
- [ ] financial_anomaly
- [ ] predictive_analytics
- [ ] sales_performance

### Construction (4 modules)
- [ ] mine_scope
- [ ] planning_classifier
- [ ] building_metrics
- [ ] estimator_au

### Agriculture (2 modules)
- [ ] agri_taxonomy
- [ ] agronomy_decision

### HR/Talent (3 modules)
- [ ] talent_pulse
- [ ] talent_search
- [ ] taxonomy_skillmatch

### Procurement (4 modules)
- [ ] matcher
- [ ] spend_smart
- [ ] tender_intelligence
- [ ] vendor_recommendation

### Document Intelligence (2 modules)
- [ ] generic_rag
- [ ] relation_extractor

### Industry Verticals (5 modules)
- [ ] legal_document
- [ ] real_estate
- [ ] healthcare_diagnostics
- [ ] educational_content
- [ ] insurance_risk

### Advanced Capabilities (2 modules)
- [ ] code_analysis
- [ ] multilingual_translator

### E-Commerce (1 module)
- [ ] product_recommendation

### Maritime (1 module)
- [ ] maritime_logistics

---

## 🔍 Module Name Mapping

| Frontend Panel | Backend Module Name | Category |
|----------------|---------------------|----------|
| SentimentSocialPanel | `sentiment_social` | marketing |
| CampaignOptimizerPanel | `campaign_optimizer` | marketing |
| CustomerChurnPanel | `customer_churn` | analytics |
| FinancialAnomalyPanel | `financial_anomaly` | analytics |
| PredictiveAnalyticsPanel | `predictive_analytics` | analytics |
| SalesPerformancePanel | `sales_performance` | analytics |
| MineScopePanel | `mine_scope` | construction |
| PlanningClassifierPanel | `planning_classifier` | construction |
| BuildingMetricsPanel | `building_metrics` | construction |
| EstimatorAUPanel | `estimator_au` | construction |
| AgriTaxonomyPanel | `agri_taxonomy` | agriculture |
| AgronomyDecisionPanel | `agronomy_decision` | agriculture |
| TalentPulsePanel | `talent_pulse` | hr_talent |
| TalentSearchPanel | `talent_search` | hr_talent |
| TaxonomySkillmatchPanel | `taxonomy_skillmatch` | hr_talent |
| MatcherPanel | `matcher` | procurement |
| SpendSmartPanel | `spend_smart` | procurement |
| TenderIntelligencePanel | `tender_intelligence` | procurement |
| VendorRecommendationPanel | `vendor_recommendation` | procurement |
| GenericRAGPanel | `generic_rag` | document_intelligence |
| RelationExtractorPanel | `relation_extractor` | document_intelligence |
| LegalDocumentPanel | `legal_document` | industry_verticals |
| RealEstatePanel | `real_estate` | industry_verticals |
| HealthcareDiagnosticsPanel | `healthcare_diagnostics` | industry_verticals |
| EducationalContentPanel | `educational_content` | industry_verticals |
| InsuranceRiskPanel | `insurance_risk` | industry_verticals |
| CodeAnalysisPanel | `code_analysis` | advanced_capabilities |
| MultilingualTranslatorPanel | `multilingual_translator` | advanced_capabilities |
| ProductRecommendationPanel | `product_recommendation` | ecommerce |
| MaritimeReportPanel | `maritime_logistics` | maritime |

---

## 🛠️ Helper Reference

The `module_config_helper.py` provides these utilities:

```python
from app.services.module_config_helper import (
    load_module_config,        # Main function - loads 3-level config
    extract_llm_params,        # Extract LLM params as dict
    get_system_prompt,         # Get system prompt
    get_retrieval_params       # Get retrieval settings (top_k, etc.)
)
```

**Usage Example**:
```python
# Load full config
config = await load_module_config(db, "sentiment_social")

# Extract for direct use
llm_params = extract_llm_params(config)  # Returns {model, temperature, max_tokens, ...}
system_prompt = get_system_prompt(config)
retrieval = get_retrieval_params(config)  # Returns {top_k, rerank_top_k, min_score}
```

---

## 📝 Example: sentiment_social Integration

### Service Changes (sentiment_social_service.py)

**Lines 37-46**: Constructor update
```python
def __init__(self, db: Session, settings: Settings, config: Optional[Dict[str, Any]] = None):
    self.db = db
    self.settings = settings
    self.config = config or {}
    self.llm_service = LLMService(db, settings)

    logger.info("✓ SentimentSocialService initialized with tier_1 services")
    if config:
        logger.info(f"✓ Using module config with model: {config.get('llm', {}).get('default', {}).get('model', 'default')}")
```

**Lines 155-166**: First LLM call update
```python
# Get LLM parameters from module config
llm_config = self.config.get('llm', {}).get('default', {})
model = llm_config.get('model', 'gpt-4o-mini')
temperature = llm_config.get('temperature', 0.1)
max_tokens = llm_config.get('max_tokens', 400)

response = await self.llm_service.generate_response(
    prompt=prompt,
    model=model,
    temperature=temperature,
    max_tokens=max_tokens
)
```

**Lines 449-460**: Second LLM call update (similar pattern)

### Routes Changes (sentiment_social_routes.py)

**Lines 10, 15**: Import updates
```python
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.module_config_helper import load_module_config
```

**Line 36**: Type hint fix
```python
async def analyze_social_sentiment(
    request: SentimentSocialRequest,
    db: AsyncSession = Depends(get_db),  # ✅ AsyncSession not Session
    settings: Settings = Depends(get_settings)
):
```

**Lines 111-116**: Load and pass config
```python
# Load module configuration
module_config = await load_module_config(db, "sentiment_social")
logger.info(f"✓ Loaded config for sentiment_social")

# Initialize service with config
service = SentimentSocialService(db, settings, config=module_config)
```

---

## ⚡ Quick Commands

### Find LLM Calls in a Service
```bash
grep -n "llm_service.generate_response\|openai\|anthropic" backend/app/tier_2/{category}/{module}_service.py
```

### Find All LLM Calls in Category
```bash
grep -rn "llm_service.generate_response" backend/app/tier_2/marketing/
```

### Test Config Loading
```python
# In Python shell
from app.services.module_config_helper import load_module_config
from app.tier_1.infrastructure.database import AsyncSessionLocal

async with AsyncSessionLocal() as db:
    config = await load_module_config(db, "sentiment_social")
    print(config)
```

---

## 🚨 Common Issues

### Issue 1: Import Error for AsyncSession
**Error**: `NameError: name 'AsyncSession' is not defined`

**Fix**: Update import
```python
from sqlalchemy.ext.asyncio import AsyncSession  # Not sqlalchemy.orm.Session
```

### Issue 2: Config Not Loading
**Error**: Service still uses hardcoded values

**Fix**: Check:
1. Module name matches exactly: `"sentiment_social"` (not `"sentiment-social"` or `"sentimentSocial"`)
2. Config passed to service: `Service(db, settings, config=module_config)`
3. Service stores config: `self.config = config or {}`

### Issue 3: Type Mismatch
**Error**: `TypeError: 'Session' object has no attribute 'execute'`

**Fix**: Change `db: Session` to `db: AsyncSession` in route signature

---

## 📈 Progress Tracking

**Completed**: 1/30 (3.3%)
**Remaining**: 29/30 (96.7%)

**Estimated Completion**:
- At 10 min/module: ~5 hours
- At 5 min/module: ~2.5 hours (once pattern is familiar)

**Recommended Batch Size**: 5 modules per batch (test after each batch)

---

## 🎯 Success Criteria

For each module:

1. ✅ **Service accepts config**: Constructor has `config` parameter
2. ✅ **LLM calls use config**: No hardcoded model/temperature/max_tokens
3. ✅ **Routes load config**: Calls `load_module_config()`
4. ✅ **Routes pass config**: Service instantiated with `config=module_config`
5. ✅ **Type hints correct**: Routes use `AsyncSession` not `Session`
6. ✅ **Logs show config**: Backend logs show "✓ Loaded config for {module}"
7. ✅ **Config works**: POCConfigManager changes affect LLM behavior

---

## 🔄 Next Steps

1. **Batch 1** (Marketing): Apply to `campaign_optimizer`
2. **Batch 2** (Analytics): Apply to 4 analytics modules
3. **Batch 3** (Construction): Apply to 4 construction modules
4. **Continue systematically** through all categories
5. **Final testing**: End-to-end validation with different configs

---

**End of Module Configuration Integration Rollout Guide**
