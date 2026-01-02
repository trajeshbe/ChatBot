# Manual Testing Guide for Sample Data

Since the automated test script encountered upload issues, use this guide to manually test the sample data through the UI.

## Prerequisites

1. Ensure backend and frontend are running:
```bash
docker-compose ps
# Both backend and frontend should be "Up" and "healthy"
```

2. Open the frontend: http://localhost:3001

## Test 1: Construction Monitor (Planning Application)

### Upload Document
1. Click "Upload Files" button in the UI
2. Navigate to: `/sample_data/tier3_customer_pocs/construction_monitor/`
3. Select: `planning_application_sample.txt`
4. Wait for upload confirmation

### Test Generic RAG (Should Work)
Ask these questions in the chat:

**Q1:** "What is the planning application reference number?"
- **Expected:** Should find "2024/0245/FUL"
- **Result:** ✓ PASS / ✗ FAIL

**Q2:** "Who is the applicant for this planning application?"
- **Expected:** Should mention "Barrat Homes Ltd"
- **Result:** ✓ PASS / ✗ FAIL

**Q3:** "How many residential units are proposed?"
- **Expected:** Should mention "150 residential units"
- **Result:** ✓ PASS / ✗ FAIL

### Expected Specialized Features (Will NOT Work)
These features are documented as required but not yet implemented:

- ❌ Named Entity Recognition to tag all ORGANIZATION entities
- ❌ Relationship extraction (APPLICANT_FOR relationship)
- ❌ Timeline visualization of key dates
- ❌ Stakeholder network graph

---

## Test 2: British Council (Profile Matching)

### Upload Documents
1. Upload: `learner_profile_sample.json`
2. Upload: `course_catalog_sample.json`

### Test Generic RAG (Should Work)
**Q1:** "What is Ahmed Hassan's English level?"
- **Expected:** Should mention "B1 Intermediate"
- **Result:** ✓ PASS / ✗ FAIL

**Q2:** "What is the price of the IELTS Preparation course?"
- **Expected:** Should mention "£850"
- **Result:** ✓ PASS / ✗ FAIL

**Q3:** "Which learner has a C1 level?"
- **Expected:** Should mention "Maria Rodriguez"
- **Result:** ✓ PASS / ✗ FAIL

### Expected Specialized Features (Will NOT Work)
- ❌ Match Ahmed to suitable courses based on level, goals, budget, schedule
- ❌ Calculate match scores with explanations
- ❌ Generate personalized recommendations
- ❌ Multi-tab UI for profile viewing, course browsing, match results

---

## Test 3: Grant Thornton (Financial Analysis)

### Upload Documents
1. Upload: `company_financial_ratios.csv`
2. Upload: `credit_analysis_benchmarks.json`

### Test Generic RAG (Should Work)
**Q1:** "What is TechGlobal Inc's current ratio?"
- **Expected:** Should mention "2.45"
- **Result:** ✓ PASS / ✗ FAIL

**Q2:** "What industry is ManufactureCorp in?"
- **Expected:** Should mention "Manufacturing"
- **Result:** ✓ PASS / ✗ FAIL

**Q3:** "Which company has the highest Z-score?"
- **Expected:** Should mention "SoftwareServices Inc" with "4.85"
- **Result:** ✓ PASS / ✗ FAIL

### Expected Specialized Features (Will NOT Work)
- ❌ Calculate credit rating for each company
- ❌ Compare ratios to industry benchmarks
- ❌ Classify companies by risk zone (safe/grey/distress)
- ❌ Generate credit risk assessment report
- ❌ Peer group analysis and ranking

---

## Test 4: CRU Mining Intelligence

### Upload Document
1. Upload: `mining_market_report_sample.txt`

### Test Generic RAG (Should Work)
**Q1:** "What is the current copper spot price?"
- **Expected:** Should mention "$8,450 per tonne"
- **Result:** ✓ PASS / ✗ FAIL

**Q2:** "Which country is the largest copper producer?"
- **Expected:** Should mention "Chile" with "1.42 million tonnes"
- **Result:** ✓ PASS / ✗ FAIL

**Q3:** "What is the Q2 2024 price forecast range?"
- **Expected:** Should mention "$8,300 - $8,700"
- **Result:** ✓ PASS / ✗ FAIL

### Expected Specialized Features (Will NOT Work)
- ❌ Extract all production data into structured table
- ❌ Parse quarterly price forecasts into time-series chart
- ❌ Extract demand breakdown by region as data table
- ❌ Identify and extract all financial entities (prices, volumes, percentages)
- ❌ Generate multi-section report with tables and charts

---

## Test 5: Procurement Matcher

### Upload Documents
1. Upload: `rfp_construction_materials.txt`
2. Upload: `supplier_profiles.json`

### Test Generic RAG (Should Work)
**Q1:** "What is the estimated contract value for the RFP?"
- **Expected:** Should mention "£4.5 million - £5.2 million"
- **Result:** ✓ PASS / ✗ FAIL

**Q2:** "Which supplier is located in Reading?"
- **Expected:** Should mention "EcoStruct Materials PLC" at "8km"
- **Result:** ✓ PASS / ✗ FAIL

**Q3:** "What certifications does BuildMaster Materials Ltd have?"
- **Expected:** Should mention "ISO 9001:2015, ISO 14001:2015, ISO 45001:2018"
- **Result:** ✓ PASS / ✗ FAIL

### Expected Specialized Features (Will NOT Work)
- ❌ Extract all RFP requirements (materials, quantities, certifications)
- ❌ Match each supplier's capabilities to RFP requirements
- ❌ Calculate weighted match scores (Price 40%, Technical 30%, etc.)
- ❌ Rank suppliers by suitability
- ❌ Identify gaps (e.g., which requirements are not met)
- ❌ Generate shortlist with detailed scoring explanation

---

## Test Results Summary Template

Fill this out after testing:

```
=== MANUAL TEST RESULTS ===
Date: ___________
Tester: ___________

Construction Monitor:
  Generic RAG Q1: ✓ / ✗
  Generic RAG Q2: ✓ / ✗
  Generic RAG Q3: ✓ / ✗
  Overall: __/3 PASS

British Council:
  Generic RAG Q1: ✓ / ✗
  Generic RAG Q2: ✓ / ✗
  Generic RAG Q3: ✓ / ✗
  Overall: __/3 PASS

Grant Thornton:
  Generic RAG Q1: ✓ / ✗
  Generic RAG Q2: ✓ / ✗
  Generic RAG Q3: ✓ / ✗
  Overall: __/3 PASS

CRU Mining:
  Generic RAG Q1: ✓ / ✗
  Generic RAG Q2: ✓ / ✗
  Generic RAG Q3: ✓ / ✗
  Overall: __/3 PASS

Procurement Matcher:
  Generic RAG Q1: ✓ / ✗
  Generic RAG Q2: ✓ / ✗
  Generic RAG Q3: ✓ / ✗
  Overall: __/3 PASS

TOTAL GENERIC RAG: __/15 PASS (__%)
SPECIALIZED FEATURES WORKING: 0/5 modules (0%)
```

---

## Expected Outcome

**Generic RAG Tests:** Should pass 80-100% (12-15 out of 15 questions)
- Platform can extract and retrieve factual information from uploaded documents
- Basic question-answering works

**Specialized Features:** Will fail 100% (0 out of 5 modules)
- No NER/REL models deployed
- No matching algorithms implemented
- No financial calculation engines
- No structured extraction templates
- No specialized UIs

---

## Next Steps After Manual Testing

1. **Document results** in the template above
2. **If generic RAG fails:** Debug upload/processing/retrieval pipeline
3. **If generic RAG works:** Proceed with specialized feature implementation per roadmap:
   - Phase 1: Plugin architecture
   - Phase 2: Construction Monitor NER/REL POC
   - Phase 3: Matching algorithms for British Council & Procurement
   - Phase 4: Financial analysis, vision AI, specialized UIs

---

## Troubleshooting

### Upload Fails
- Check backend logs: `docker-compose logs backend --tail 50`
- Verify file permissions: `ls -la sample_data/tier3_customer_pocs/*/`
- Try uploading via curl:
  ```bash
  curl -X POST http://localhost:8000/api/v1/upload \
    -F "file=@sample_data/tier3_customer_pocs/construction_monitor/planning_application_sample.txt" \
    -F "session_id=test123"
  ```

### Query Returns No Results
- Check if document was processed: Look for "Document processed successfully" in logs
- Verify vector embeddings created: Check database `document_chunks` table
- Try simpler question first: "What is in this document?"

### Backend Not Responding
- Restart: `docker-compose restart backend`
- Check health: `curl http://localhost:8000/health`
- View logs: `docker-compose logs backend --follow`

---

**Last Updated:** January 1, 2026
