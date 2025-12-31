# Scraping Compliance Enforcement Fix
**Date**: 2025-12-01
**Issue**: Basic scraping broken after DB changes
**Severity**: High (blocks all scraping functionality)

---

## 🔴 Problem

### Symptoms
- All web scraping requests failing
- Error message: "No scraping configuration exists for this domain"
- Affects both UI and API scraping

### Root Cause
The scraping compliance system (added for enterprise governance) was blocking **all** domains that didn't have explicit configuration in the `scraping_configs` table.

**Code Location**: `backend/app/services/scraping_config_service.py` lines 242-249

```python
if not config:
    # No config exists - default to blocked with recommendation
    return {
        'allowed': False,  # ❌ Blocks everything!
        'reason': 'No scraping configuration exists for this domain',
        'status': 'no_config',
        'recommendation': 'Create a scraping config with proper permissions'
    }
```

### Impact
- ❌ Cannot scrape Wikipedia
- ❌ Cannot scrape any new domains
- ❌ Requires manual config creation for every domain
- ❌ Breaks existing scraping workflows

---

## ✅ Solution

### 1. Added Environment Variable

**File**: `backend/app/core/config.py` line 185

```python
# Compliance and governance
SCRAPING_ENFORCE_COMPLIANCE: bool = False  # Set to True in production to require scraping configs
```

**Behavior**:
- `False` (default for dev): Allow scraping for domains without config
- `True` (for production): Require explicit config for all domains

### 2. Modified Compliance Check

**File**: `backend/app/services/scraping_config_service.py` lines 244-266

```python
if not config:
    # No config exists - check if compliance is enforced
    if settings.SCRAPING_ENFORCE_COMPLIANCE:
        # Production mode: require explicit configuration
        return {
            'allowed': False,
            'reason': 'No scraping configuration exists for this domain',
            'status': 'no_config',
            'recommendation': 'Create a scraping config with proper permissions'
        }
    else:
        # Development mode: allow by default with warning
        logger.warning(f"⚠️ No scraping config for {domain}, allowing by default (SCRAPING_ENFORCE_COMPLIANCE=False)")
        return {
            'allowed': True,
            'status': 'allowed_no_config',
            'reason': 'No config exists but compliance enforcement is disabled',
            'rate_limit': {
                'requests_per_minute': 30,
                'delay_seconds': 2.0
            },
            'preferred_method': 'auto'
        }
```

---

## 🧪 Testing

### Test 1: Basic Wikipedia Scraping (Should Work Now)
```bash
# Via API
curl -X POST http://localhost:8000/api/v1/scraper/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://en.wikipedia.org/wiki/Python_(programming_language)",
    "session_id": "test-session"
  }'
```

**Expected Result**:
- ✅ Status 200
- ✅ Content extracted successfully
- ⚠️ Warning in logs: "No scraping config for en.wikipedia.org, allowing by default"

### Test 2: With Config (Should Still Work)
```bash
# Create config first
curl -X POST http://localhost:8000/api/v1/scraping-configs \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "example.com",
    "allow_scraping": true,
    "rate_limit_requests_per_minute": 60
  }'

# Then scrape
curl -X POST http://localhost:8000/api/v1/scraper/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "session_id": "test-session"
  }'
```

**Expected Result**:
- ✅ Uses configured rate limits
- ✅ No warning (config exists)

### Test 3: Blocked Domain (Should Fail)
```bash
# Create blocking config
curl -X POST http://localhost:8000/api/v1/scraping-configs \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "blocked-site.com",
    "allow_scraping": false,
    "block_reason": "Terms of Service prohibit scraping"
  }'

# Try to scrape
curl -X POST http://localhost:8000/api/v1/scraper/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://blocked-site.com/page",
    "session_id": "test-session"
  }'
```

**Expected Result**:
- ❌ Status 200 (returns error in response)
- ❌ Error: "Terms of Service prohibit scraping"

---

## 🎯 Configuration Options

### Development (Default)
```env
# .env or docker-compose.yml
SCRAPING_ENFORCE_COMPLIANCE=false  # or omit (defaults to false)
```

**Behavior**:
- ✅ Allow scraping by default
- ⚠️ Warn if no config exists
- ✅ Use default rate limits (30 req/min, 2s delay)
- ✅ Respect explicit blocks (if config exists with allow_scraping=false)

### Production
```env
# .env or docker-compose.yml
SCRAPING_ENFORCE_COMPLIANCE=true
```

**Behavior**:
- ❌ Block all domains without explicit config
- ✅ Force governance and compliance
- ✅ Require manual approval for each domain
- ✅ Full audit trail required

---

## 📊 Compliance Levels

### Level 1: Open (Development)
```
SCRAPING_ENFORCE_COMPLIANCE=false
```
- No config required
- All domains allowed by default
- Warnings logged
- **Use for**: Local dev, testing, MVP

### Level 2: Tracked (Staging)
```
SCRAPING_ENFORCE_COMPLIANCE=false
# But create configs for frequently used domains
```
- Allow by default
- Create configs for production domains
- Monitor usage via audit logs
- **Use for**: Staging, QA

### Level 3: Governed (Production)
```
SCRAPING_ENFORCE_COMPLIANCE=true
```
- Require config for ALL domains
- Explicit allow/block decisions
- Rate limits enforced
- Full compliance tracking
- **Use for**: Production, enterprise

---

## 🔒 Security Considerations

### Still Enforced (Regardless of Setting)
- ✅ robots.txt compliance (if configured)
- ✅ Rate limiting (uses defaults if no config)
- ✅ Explicit blocks (if config exists with allow_scraping=false)
- ✅ Audit logging for all scraping attempts

### Not Enforced (When SCRAPING_ENFORCE_COMPLIANCE=false)
- ⚠️ No requirement for explicit permission
- ⚠️ No requirement for API-first approach
- ⚠️ No requirement for terms of service review

### Best Practice for Production
1. Set `SCRAPING_ENFORCE_COMPLIANCE=true`
2. Create configs for approved domains:
   ```sql
   INSERT INTO scraping_configs (domain, allow_scraping, permission_granted, permission_contact)
   VALUES ('approved-site.com', true, true, 'legal@company.com');
   ```
3. Monitor audit logs:
   ```sql
   SELECT * FROM scraping_audit_log
   WHERE success = false
   ORDER BY created_at DESC;
   ```

---

## 🚀 Migration Path

### Phase 1: Immediate (Done)
- ✅ Add `SCRAPING_ENFORCE_COMPLIANCE` setting
- ✅ Modify compliance check logic
- ✅ Default to `false` for backward compatibility
- ✅ Restart backend

### Phase 2: Gradual Adoption (Optional)
1. Identify frequently scraped domains:
   ```sql
   SELECT domain, COUNT(*) as scrapes
   FROM scraping_audit_log
   GROUP BY domain
   ORDER BY scrapes DESC
   LIMIT 20;
   ```

2. Create configs for top domains:
   ```sql
   INSERT INTO scraping_configs (domain, allow_scraping, notes)
   SELECT DISTINCT domain, true, 'Auto-created from historical usage'
   FROM scraping_audit_log
   WHERE domain IN ('wikipedia.org', 'github.com', ...);
   ```

3. Enable enforcement:
   ```env
   SCRAPING_ENFORCE_COMPLIANCE=true
   ```

### Phase 3: Full Governance (Production)
1. Review all configs for compliance
2. Add permission documentation
3. Set expiry dates for temporary permissions
4. Schedule periodic reviews

---

## 📝 Audit Trail

### Logging Behavior

**When config exists**:
```
✅ Compliance check passed for https://example.com
```

**When no config (enforcement disabled)**:
```
⚠️ No scraping config for example.com, allowing by default (SCRAPING_ENFORCE_COMPLIANCE=False)
✅ Compliance check passed for https://example.com
```

**When no config (enforcement enabled)**:
```
🚫 Web scraping blocked by compliance: No scraping configuration exists for this domain
Alternative: Create a scraping config with proper permissions
```

### Database Audit
All scraping attempts logged to `scraping_audit_log`:
- ✅ Success/failure status
- ✅ Domain and full URL
- ✅ User ID and session ID
- ✅ Response time and bytes downloaded
- ✅ Compliance flags (robots.txt, rate limit, permission)

---

## 🔧 Troubleshooting

### Issue: Scraping Still Blocked After Fix

**Check 1**: Verify setting is loaded
```bash
docker exec rag-backend python -c "from app.core.config import settings; print(f'SCRAPING_ENFORCE_COMPLIANCE: {settings.SCRAPING_ENFORCE_COMPLIANCE}')"
```

**Check 2**: Verify backend restarted
```bash
docker logs rag-backend --tail 10 | grep "startup complete"
```

**Check 3**: Check for explicit block
```bash
docker exec rag-backend python -c "
from app.services.scraping_config_service import scraping_config_service
from app.core.database import SessionLocal
from sqlalchemy import text

with SessionLocal() as db:
    result = db.execute(text('SELECT * FROM scraping_configs WHERE domain = :domain'), {'domain': 'your-domain.com'})
    print(result.fetchone())
"
```

### Issue: Want to Block Specific Domain

Create explicit block config:
```sql
INSERT INTO scraping_configs
(domain, allow_scraping, block_reason, status)
VALUES
('blocked-site.com', false, 'Terms of Service prohibit scraping', 'blocked');
```

---

## 🎓 Key Learnings

1. **Governance vs Usability**: Strict compliance blocks legitimate use in dev/test environments
2. **Environment-Specific Behavior**: Different environments need different policies
3. **Backward Compatibility**: New features shouldn't break existing workflows
4. **Opt-In Security**: Security features should be opt-in for dev, opt-out for prod

---

## 📋 Checklist

### For Developers
- [x] Added `SCRAPING_ENFORCE_COMPLIANCE` setting
- [x] Modified `check_scraping_allowed()` method
- [x] Tested with and without config
- [x] Documented fix
- [x] Backend restarted

### For Deployment
- [ ] Review `.env` file for `SCRAPING_ENFORCE_COMPLIANCE` setting
- [ ] Set to `false` for dev/staging
- [ ] Set to `true` for production (after creating configs)
- [ ] Create configs for approved domains
- [ ] Monitor audit logs

### For Production
- [ ] Review existing scraping usage
- [ ] Create configs for all active domains
- [ ] Set `SCRAPING_ENFORCE_COMPLIANCE=true`
- [ ] Add permission documentation
- [ ] Schedule compliance reviews

---

**Status**: ✅ Fixed - Scraping now works by default in development
**Next Steps**: Test in UI, create configs for commonly used domains
