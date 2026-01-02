# Quick Start: Testing Sample Data

## 5-Minute Test (Minimum Viable Testing)

### Option 1: Via Frontend UI (Recommended)

1. **Start services:**
   ```bash
   docker-compose up -d
   ```

2. **Open UI:** http://localhost:3001

3. **Upload ONE sample file:**
   - Click "Upload Files"
   - Select: `sample_data/tier3_customer_pocs/construction_monitor/planning_application_sample.txt`
   - Wait for green "Upload successful" message

4. **Ask ONE test question:**
   - Type: "What is the planning application reference number?"
   - Press Enter

5. **Expected Result:**
   - ✅ **PASS:** Answer mentions "2024/0245/FUL"
   - ✗ **FAIL:** Error message or no answer

### Option 2: Via cURL (Quick Backend Test)

```bash
# Test 1: Upload document
curl -X POST http://localhost:8000/api/v1/upload \
  -F "file=@sample_data/tier3_customer_pocs/construction_monitor/planning_application_sample.txt" \
  -F "session_id=quicktest"

# Test 2: Query
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the planning application reference number?",
    "session_id": "quicktest",
    "use_rag": true
  }'
```

---

## What This Test Proves

### ✅ If Test PASSES:
- Generic RAG pipeline is working
- Document upload functional
- Text extraction operational
- Vector embeddings generated
- Semantic search working
- LLM integration functional

**Conclusion:** Platform ready for specialized feature development

### ✗ If Test FAILS:
- Check backend health: `docker-compose ps backend`
- View logs: `docker-compose logs backend --tail 50`
- Restart services: `docker-compose restart backend`
- See `/scripts/testing/use_cases/manual_test_guide.md` for troubleshooting

---

## Full Testing

For comprehensive testing of all 5 modules with 15 test cases, see:
- `/scripts/testing/use_cases/manual_test_guide.md` - Detailed manual testing instructions
- `/sample_data/README.md` - Complete sample data documentation
- `/SAMPLE_DATA_AND_TESTING_SUMMARY.md` - Executive summary and findings

---

## Sample Data Locations

All sample data files are in `/sample_data/`:

- **Construction Monitor:** `tier3_customer_pocs/construction_monitor/`
- **British Council:** `tier3_customer_pocs/british_council/`
- **Grant Thornton:** `tier3_customer_pocs/grant_thornton/`
- **CRU Mining:** `tier3_customer_pocs/cru/`
- **Procurement Matcher:** `tier2_domain_verticals/procurement_matcher/`

Each directory contains 2-3 sample files totaling ~150KB of realistic test data.

---

## Next Steps

1. ✅ Complete 5-minute quick test (above)
2. If passing, proceed to full manual testing (15 test cases)
3. Review findings in `SAMPLE_DATA_AND_TESTING_SUMMARY.md`
4. Plan specialized feature implementation based on identified gaps

---

**Quick Reference:**
- UI: http://localhost:3001
- API Docs: http://localhost:8000/api/docs
- GraphQL: http://localhost:8000/graphql
