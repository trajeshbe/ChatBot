# Dynamic POC Configuration - Quick Reference

**Date:** 2026-01-02
**Main Document:** `DYNAMIC_POC_CONFIGURATION_ARCHITECTURE.md`

---

## TL;DR - What This Achieves

Transform all Customer Solutions from **hardcoded** configurations to **UI-configurable** systems, enabling:

✅ **Zero-code POC deployment** - Configure new customers in minutes via UI
✅ **A/B testing** - Test different prompts, models, and parameters
✅ **Customer self-service** - Let customers tune their own deployment
✅ **Faster iteration** - No code changes or deployments required

---

## Audit Results

**143 hardcoded values identified across Tier 2 & 3:**

| Category | Count | Examples |
|----------|-------|----------|
| LLM Models | 21 | `"gpt-4o-mini"`, `"claude-3-sonnet"` |
| Prompts | 47 | `"You are a helpful assistant..."` |
| Hyperparameters | 28 | `temperature=0.0`, `max_tokens=500` |
| Thresholds | 14 | `confidence > 0.8` |
| Regex Patterns | 8 | `r"\b[A-Z]{3}\d{4}\b"` |
| Other | 25 | Scoring weights, retrieval params |

---

## Architecture at a Glance

### 3-Level Configuration Hierarchy

```
┌─────────────────────────────────────────┐
│ Level 1: Global Defaults                │
│ (Fallback for all POCs)                 │
└──────────────┬──────────────────────────┘
               │ Inherits & Overrides
               ▼
┌─────────────────────────────────────────┐
│ Level 2: POC-Specific Configuration     │
│ (Per-customer/Per-POC settings)         │
└──────────────┬──────────────────────────┘
               │ Inherits & Overrides
               ▼
┌─────────────────────────────────────────┐
│ Level 3: User-Specific Overrides        │
│ (A/B testing, personal preferences)     │
└─────────────────────────────────────────┘
```

**Resolution Order:** User Override → POC Config → Global Defaults

---

## Database Schema (6 Tables)

### Core Tables

1. **`poc_configurations`** - Base config for each POC
2. **`poc_user_overrides`** - Per-user/customer overrides
3. **`config_versions`** - Version history (audit trail)
4. **`config_schemas`** - JSON schemas for validation
5. **`config_templates`** - Reusable templates
6. **`config_audit_logs`** - Detailed change tracking

**Storage:** PostgreSQL JSONB (queryable + flexible)

---

## API Endpoints

### Key Routes (`/api/v1/poc-config`)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/pocs` | GET | List all POCs |
| `/pocs/{name}` | GET | Get POC config (with overrides) |
| `/pocs/{name}` | PUT | Update POC config |
| `/pocs/{name}/overrides` | POST | Set user-specific overrides |
| `/pocs/{name}/versions` | GET | Get version history |
| `/pocs/{name}/versions/{v}/restore` | POST | Restore previous version |
| `/templates` | GET | List templates |

---

## Frontend UI (6 Tabs per POC)

### Configuration Management UI

```
┌──────────────────────────────────────────────────┐
│ POC Configuration: British Council               │
├──────────────────────────────────────────────────┤
│ Tabs:                                            │
│  📝 Prompts     - System & user prompts          │
│  🤖 Models      - LLM selection & fallbacks      │
│  ⚙️ Parameters  - Temperature, max_tokens, etc.  │
│  🎯 Thresholds  - Confidence scores, top_k       │
│  📊 Scoring     - Weights & scoring factors      │
│  🔍 Advanced    - Features, regex, cache         │
└──────────────────────────────────────────────────┘
```

Each POC UI gets a **⚙️ Configure POC** button that opens this interface.

---

## Code Refactoring Pattern

### Before (Hardcoded)

```python
response = await llm_service.generate_response(
    prompt,
    model="gpt-4o-mini",      # HARDCODED
    temperature=0.0,           # HARDCODED
    max_tokens=500             # HARDCODED
)
```

### After (Dynamic)

```python
# Load config once during initialization
config = await poc_config_service.get_config(
    db=db,
    poc_name="british_council",
    user_id=user_id  # Includes user overrides
)

# Use config values
llm_config = config['llm']['profile_analyzer']
response = await llm_service.generate_response(
    prompt,
    model=llm_config['model'],               # FROM CONFIG
    temperature=llm_config['temperature'],   # FROM CONFIG
    max_tokens=llm_config['max_tokens']      # FROM CONFIG
)
```

---

## Implementation Timeline

### 7-Week Plan

| Week | Tasks | Deliverables |
|------|-------|--------------|
| **Week 1** | Infrastructure setup | Database schema, API routes, POCConfigService |
| **Week 2** | British Council migration (PoC) | First POC fully configurable |
| **Week 3** | CRU + GT Motive migration | 3/6 POCs configurable |
| **Week 4** | Grant Thornton + Solera | 5/6 POCs configurable |
| **Week 5** | Construction Monitor + Tier 2 | 6/6 POCs + core services configurable |
| **Week 6** | Frontend UI development | Full UI for configuration management |
| **Week 7** | Testing & documentation | Production-ready system |

---

## Configuration Example (British Council)

### Full Config Structure

```json
{
  "llm": {
    "profile_analyzer": {
      "model": "gpt-4o-mini",
      "temperature": 0.0,
      "max_tokens": 500
    },
    "answer_synthesis": {
      "model": "gpt-4o-mini",
      "temperature": 0.2,
      "max_tokens": 800
    }
  },
  "prompts": {
    "system": {
      "profile_extraction": "Extract a structured user profile...",
      "course_recommendation": "Based on the user profile..."
    },
    "user": {
      "profile_query_template": "User background: {background}..."
    }
  },
  "scoring": {
    "weights": {
      "semantic": 0.6,
      "profile": 0.4
    },
    "profile_factors": {
      "education_match": 0.3,
      "format_match": 0.2,
      "availability_match": 0.2,
      "skill_intersection": 0.3
    },
    "thresholds": {
      "match_threshold": 0.8,
      "high_match": 0.9
    }
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

---

## Per-POC Hardcoded Values Summary

### British Council
- **21 hardcoded values** total
- Models: `gpt-4o-mini` (1 usage)
- Prompts: Profile extraction (2 prompts)
- Scoring weights: 5 values (semantic, profile, education, format, skills)
- Thresholds: 1 value (match_threshold)
- Retrieval: 3 values (initial_top_k, rerank_top_k, final_count)

### CRU Mining
- **18 hardcoded values** total
- Models: `gpt-4o-mini` (2 usages)
- Prompts: Query classification, answer synthesis
- Retrieval: pgvector_top_k, elasticsearch_size, rrf_k, rerank_top_k

### Grant Thornton
- **8 hardcoded values** total
- Models: `gpt-4o-mini` (1 usage)
- Prompts: Query processing
- Parameters: temperature=0.3

### GT Motive
- **24 hardcoded values** total
- Models: `gpt-4o-mini` (2 usages)
- Prompts: Part extraction, query processing
- Regex: 4 part code patterns
- Confidence thresholds: 3 values
- Validation rules: 3 values

### Solera
- **16 hardcoded values** total
- Models: `gpt-4o-mini` (1 usage)
- Prompts: Damage assessment
- Regex: 1 VIN pattern, 3 part code patterns
- Assessment logic: severity, cost, time
- Thresholds: 1 value (cost escalation)

### Construction Monitor
- **19 hardcoded values** total
- Models: `gpt-4o-mini` (3 usages)
- Prompts: Entity extraction, relation extraction, query processing
- Entity types: 8 types
- Relation types: 6 types

---

## Benefits & ROI

### Operational Benefits

| Before | After |
|--------|-------|
| 2-5 days to deploy new POC | < 1 hour via UI configuration |
| Code changes for parameter tuning | Real-time updates via sliders |
| Restart required for config changes | Zero-downtime updates |
| Hard to A/B test prompts | Easy experimentation |
| Engineers handle all tuning | Customers self-serve 50% of changes |

### Expected ROI

- **10x faster** POC deployment
- **50% reduction** in engineering support tickets
- **30% increase** in experimentation velocity
- **Zero downtime** for configuration changes

---

## Security Features

1. **Access Control**
   - Only admins can modify global/POC configs
   - Users can only override their own settings

2. **Input Validation**
   - JSON schema validation for all configs
   - Prompt sanitization (prevent injection)

3. **Audit Logging**
   - Full change history
   - Who, what, when, why tracked
   - IP address and user agent logged

4. **Rate Limiting**
   - Max 10 config updates per minute
   - Prevents abuse

---

## Migration Checklist (Per POC)

```markdown
### Phase 1: Audit
- [ ] Identify all hardcoded LLM models
- [ ] Identify all hardcoded prompts
- [ ] Identify all hardcoded hyperparameters
- [ ] Identify all hardcoded thresholds
- [ ] Document current behavior

### Phase 2: Configuration Design
- [ ] Design configuration JSON structure
- [ ] Create JSON schema for validation
- [ ] Define default values

### Phase 3: Database Setup
- [ ] Insert POC configuration record
- [ ] Insert configuration schema
- [ ] Create default template

### Phase 4: Code Refactoring
- [ ] Add config loading to service
- [ ] Replace all hardcoded values
- [ ] Add error handling

### Phase 5: Testing
- [ ] Unit tests: config loading
- [ ] Integration tests: same behavior
- [ ] Performance tests: no regression

### Phase 6: Frontend Integration
- [ ] Add config button to POC UI
- [ ] Test all 6 tabs

### Phase 7: Documentation
- [ ] Update POC README
- [ ] Document configuration options
```

---

## Quick Start for Developers

### 1. Access Existing Config (Read)

```python
from app.services.poc_config_service import poc_config_service

async def my_poc_function(db: Session, user_id: str):
    # Load config with user overrides
    config = await poc_config_service.get_config(
        db=db,
        poc_name="british_council",
        user_id=user_id
    )

    # Access config values
    model = config['llm']['profile_analyzer']['model']
    temp = config['llm']['profile_analyzer']['temperature']
    prompt = config['prompts']['system']['profile_extraction']
```

### 2. Update Config (Write)

```python
async def update_temperature(db: Session, new_temp: float):
    await poc_config_service.update_config(
        db=db,
        poc_name="british_council",
        updates={
            "llm": {
                "profile_analyzer": {
                    "temperature": new_temp
                }
            }
        },
        changed_by=current_user.id,
        change_reason="Optimizing for better results"
    )
```

### 3. Set User Override

```python
async def set_user_preference(db: Session, user_id: str):
    await poc_config_service.set_override(
        db=db,
        poc_name="british_council",
        user_id=user_id,
        overrides={
            "llm": {
                "profile_analyzer": {
                    "temperature": 0.1  # User wants slightly more creative
                }
            }
        }
    )
```

---

## Files to Review

### Main Documentation
- **`DYNAMIC_POC_CONFIGURATION_ARCHITECTURE.md`** (Complete architecture, 1500+ lines)
  - Full database schema
  - Complete API design
  - Detailed UI mockups
  - Code examples
  - Migration strategy
  - 7-week implementation plan

### Audit Report (From exploration)
- **Hardcoded values audit** (143 instances identified)
- **Per-POC breakdown** (British Council: 21, CRU: 18, GT Motive: 24, etc.)
- **Per-service breakdown** (LLM service, Vision service, OCR service)

---

## Next Actions

### Immediate (This Week)
1. **Review Architecture** - Stakeholder sign-off on design
2. **Approve Timeline** - Confirm 7-week plan
3. **Assign Resources** - 1 full-time developer

### Week 1 (Infrastructure)
1. **Create Database Migration**
   ```bash
   cd backend
   alembic revision -m "add_poc_configuration_tables"
   ```
2. **Implement POCConfigService**
3. **Create API Routes**
4. **Write Unit Tests**

### Week 2 (PoC Migration)
1. **Migrate British Council** (proof of concept)
2. **Test End-to-End**
3. **Document Learnings**

---

## Success Metrics

### Technical
- ✅ 100% of hardcoded values moved to config
- ✅ < 100ms API response time for config retrieval
- ✅ > 99% config update success rate
- ✅ Zero-downtime deployments

### Business
- ✅ < 1 hour POC deployment time (from 2-5 days)
- ✅ 50% of config changes by customers (self-service)
- ✅ 10+ A/B experiments per month
- ✅ 30% reduction in support tickets

---

## FAQs

**Q: Will this slow down POC performance?**
A: No. Config is loaded once during initialization and cached. Adds < 10ms overhead.

**Q: What happens if config is invalid?**
A: JSON schema validation prevents invalid configs from being saved. Existing config remains active.

**Q: Can we roll back bad configurations?**
A: Yes. Full version history allows instant rollback to any previous version.

**Q: How do we handle config conflicts?**
A: 3-level hierarchy with clear resolution order: User Override → POC Config → Global Defaults.

**Q: What if a POC doesn't have a config yet?**
A: Falls back to global defaults. No breaking changes.

**Q: Can we test configs before deploying?**
A: Yes. Each tab has "Test with Sample" buttons for validation before saving.

---

## Contact & Support

**Questions?** See full architecture document: `DYNAMIC_POC_CONFIGURATION_ARCHITECTURE.md`

**Implementation Team:**
- Backend Lead: [TBD]
- Frontend Lead: [TBD]
- DevOps: [TBD]

**Timeline:** 7 weeks (start date TBD)

---

**Last Updated:** 2026-01-02
**Version:** 1.0
**Status:** Design Phase - Awaiting Approval
