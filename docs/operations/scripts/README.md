# Operations Scripts Inventory

> **Last Updated**: 2025-11-27
> **Purpose**: Comprehensive index of all operational scripts for testing, debugging, validation, and maintenance

---

## Directory Structure

```
scripts/
├── testing/           # Test scripts for all features and workflows
├── debugging/         # Diagnostic and inspection scripts
├── validation/        # Validation and verification scripts
└── maintenance/       # Maintenance and cleanup scripts
```

---

## Testing Scripts

### Comprehensive Test Suites

#### `test_comprehensive_chatbot.sh`
**Purpose**: Complete end-to-end chat interface testing
**Usage**: `./test_comprehensive_chatbot.sh`
**Tests**:
- Document upload
- Chat query processing
- Response generation
- Source attribution
- Session management

**Prerequisites**: All services running

---

#### `test_document_handling_comprehensive.sh`
**Purpose**: Comprehensive document processing pipeline testing
**Usage**: `./test_document_handling_comprehensive.sh`
**Tests**:
- PDF upload and processing
- DOCX parsing
- Text extraction
- Chunking strategy
- Embedding generation
- Database storage

**Expected Output**: All documents processed successfully

---

#### `test_chat_comprehensive.sh`
**Purpose**: Chat functionality stress testing
**Usage**: `./test_chat_comprehensive.sh`
**Tests**:
- Multiple query types
- Session persistence
- Multi-turn conversations
- Context management
- Error handling

---

### Project Estimator Testing

#### `test_project_estimator.sh`
**Purpose**: Project Estimator workflow validation
**Usage**: `./test_project_estimator.sh`
**Tests**:
- 7-agent workflow execution
- BRD generation
- Excel file creation
- Task breakdown
- Cost estimation

**Prerequisites**: Sample project files in `docs/features/project_estimator/estimate_one/`

---

#### `test_project_estimator_validation.py`
**Purpose**: Meta-validation layer testing
**Usage**: `python test_project_estimator_validation.py`
**Tests**:
- Validator agent execution
- Validation report generation
- Contextual team selection
- Task specificity validation
- Alignment score calculation

**Expected Output**:
```json
{
  "validation_report": {
    "teams_selected": ["Backend", "Frontend", "DevOps"],
    "alignment_score": 0.85,
    "generic_tasks_found": 0
  }
}
```

---

#### `test_project_estimator_multifile.py`
**Purpose**: Multi-file upload testing for Project Estimator
**Usage**: `python test_project_estimator_multifile.py`
**Tests**:
- Multiple file upload
- File aggregation
- Context merging
- Comprehensive analysis

---

#### `test_agent11_integration.sh`
**Purpose**: Agent 11 (EDA) integration testing
**Usage**: `./test_agent11_integration.sh`
**Tests**:
- Complexity analysis
- EDA report generation
- Debate resolution
- State persistence

---

#### `test_agent_12_debate_coordinator.py`
**Purpose**: Agent 12 (Debate Coordinator) testing
**Usage**: `python test_agent_12_debate_coordinator.py`
**Tests**:
- Multi-agent debate
- Consensus building
- Conflict resolution

---

#### `test_estimate_one_phase3.sh`
**Purpose**: Phase 3 project estimation testing
**Usage**: `./test_estimate_one_phase3.sh`
**Tests**:
- Model selection
- Extraction accuracy
- Download endpoints

---

### RAG Pipeline Testing

#### `test_rag_pipeline.py`
**Purpose**: RAG query pipeline testing
**Usage**: `python test_rag_pipeline.py`
**Tests**:
- Document retrieval
- Embedding search
- Context assembly
- LLM generation
- Source attribution

**Expected Output**:
```
✓ Embeddings generated
✓ Vector search successful
✓ Context assembled
✓ Response generated with sources
```

---

#### `test_vector_search.py`
**Purpose**: Vector similarity search testing
**Usage**: `python test_vector_search.py`
**Tests**:
- Embedding generation
- Cosine similarity calculation
- Top-K retrieval
- Threshold filtering

---

#### `test_direct_aadhan_search.py`
**Purpose**: Direct database search testing
**Usage**: `python test_direct_aadhan_search.py`
**Tests**:
- Direct SQL queries
- Embedding comparison
- Retrieval accuracy

---

### Web Scraping Testing

#### `test_scraper_text_extraction.py`
**Purpose**: Web scraper text extraction testing
**Usage**: `python test_scraper_text_extraction.py`
**Tests**:
- URL fetching
- Content extraction
- Text cleaning
- Storage

---

#### `test_all_scraper_compliance.sh`
**Purpose**: Comprehensive scraping compliance testing
**Usage**: `./test_all_scraper_compliance.sh`
**Tests**:
- robots.txt checking
- Rate limiting
- User agent rotation
- Proxy usage
- Auth handling

---

#### `test_scraping_compliance.sh`
**Purpose**: Scraping compliance engine testing
**Usage**: `./test_scraping_compliance.sh`
**Tests**:
- Compliance rules
- Request throttling
- Error handling

---

#### `test_compliance_enforcement.sh`
**Purpose**: Compliance enforcement testing
**Usage**: `./test_compliance_enforcement.sh`
**Tests**:
- Rule validation
- Blocking logic
- Bypass prevention

---

### Template Extraction Testing

#### `test_template_extraction_now.sh`
**Purpose**: Template extraction feature testing
**Usage**: `./test_template_extraction_now.sh`
**Tests**:
- CSS selector generation
- Template creation
- Field mapping
- Template validation

---

#### `test_template_extraction_ui.py`
**Purpose**: Template extraction UI testing
**Usage**: `python test_template_extraction_ui.py`
**Tests**:
- UI workflow
- Template saving
- Preview generation

---

#### `test_phase3_extraction.py`
**Purpose**: Phase 3 extraction testing
**Usage**: `python test_phase3_extraction.py`
**Tests**:
- Extraction accuracy
- Field mapping
- Data validation

---

#### `test_save_template.sh`
**Purpose**: Template saving functionality
**Usage**: `./test_save_template.sh`
**Tests**:
- Template persistence
- Retrieval
- Update operations

---

#### `test_integrated_smart_mapping.py`
**Purpose**: Smart template mapping testing
**Usage**: `python test_integrated_smart_mapping.py`
**Tests**:
- Auto field detection
- Intelligent mapping
- Validation

---

#### `test_smart_template_mapping.py`
**Purpose**: Smart mapping algorithm testing
**Usage**: `python test_smart_template_mapping.py`
**Tests**:
- Field similarity
- Mapping confidence
- Auto-correction

---

#### `test_bharti_extraction.py`
**Purpose**: Bharti-specific extraction testing
**Usage**: `python test_bharti_extraction.py`
**Tests**:
- Custom selectors
- Data extraction
- Validation

---

#### `test_fixed_template.py`
**Purpose**: Fixed template testing
**Usage**: `python test_fixed_template.py`
**Tests**:
- Pre-defined templates
- Field consistency
- Error handling

---

### UI Testing

#### `test_ui_debug.py`
**Purpose**: UI flow debugging and testing
**Usage**: `python test_ui_debug.py`
**Tests**:
- Component rendering
- User interactions
- State management
- API communication

---

#### `test_ui_extraction.py`
**Purpose**: UI extraction workflow testing
**Usage**: `python test_ui_extraction.py`
**Tests**:
- Extraction UI
- User inputs
- Results display

---

#### `test_ui_playwright.py`
**Purpose**: Playwright UI testing
**Usage**: `python test_ui_playwright.py`
**Tests**:
- Browser automation
- UI interactions
- Screenshot capture

---

#### `test_ui_thresholds.sh`
**Purpose**: UI threshold controls testing
**Usage**: `./test_ui_thresholds.sh`
**Tests**:
- Slider controls
- Value updates
- Backend sync

---

#### `test_ui_backend_flow.sh`
**Purpose**: Frontend-backend flow testing
**Usage**: `./test_ui_backend_flow.sh`
**Tests**:
- API calls
- Data flow
- Error propagation

---

### Model Testing

#### `test_phase3_model_selection.py`
**Purpose**: Model selection logic testing
**Usage**: `python test_phase3_model_selection.py`
**Tests**:
- Model availability
- Fallback chain
- Performance comparison

---

#### `test_ollama_ui.py`
**Purpose**: Ollama local model UI testing
**Usage**: `python test_ollama_ui.py`
**Tests**:
- Model listing
- Selection
- Query execution

---

#### `test_vision_tool.py`
**Purpose**: Vision model testing (multiple copies for different contexts)
**Usage**: `python test_vision_tool.py`
**Tests**:
- Image analysis
- OCR
- Visual question answering

---

### Playwright Testing

#### `test_playwright_minimal.py`
**Purpose**: Minimal Playwright setup testing
**Usage**: `python test_playwright_minimal.py`
**Tests**:
- Browser launch
- Page navigation
- Basic interaction

---

#### `navigation_quick_test.sh`
**Purpose**: Quick navigation agent testing
**Usage**: `./navigation_quick_test.sh`
**Tests**:
- Page navigation
- Element detection
- Click actions

---

### Workflow Testing

#### `test_simple_workflow.py`
**Purpose**: Simple workflow execution testing
**Usage**: `python test_simple_workflow.py`
**Tests**:
- Basic workflow
- State generation
- File persistence

---

#### `test_all_parameters_flow.sh`
**Purpose**: All parameter variations testing
**Usage**: `./test_all_parameters_flow.sh`
**Tests**:
- Different input combinations
- Edge cases
- Error handling

---

#### `test_feedback_flow.sh`
**Purpose**: User feedback flow testing
**Usage**: `./test_feedback_flow.sh`
**Tests**:
- Feedback submission
- Processing
- Response updates

---

### Integration Testing

#### `test_e2e_complete.sh`
**Purpose**: Complete end-to-end testing
**Usage**: `./test_e2e_complete.sh`
**Tests**:
- Full user workflow
- All features
- Integration points

---

#### `comprehensive_test.sh`
**Purpose**: Comprehensive system testing
**Usage**: `./comprehensive_test.sh`
**Tests**:
- All major features
- Performance
- Stability

---

#### `test_estimator.sh`
**Purpose**: Estimator feature testing
**Usage**: `./test_estimator.sh`
**Tests**:
- Estimation accuracy
- Output format
- Edge cases

---

### Validation Testing

#### `test_validator_simple.sh`
**Purpose**: Simple validator testing
**Usage**: `./test_validator_simple.sh`
**Tests**:
- Basic validation rules
- Pass/fail logic
- Error messages

---

#### `test_aadhan_retrieval.sh`
**Purpose**: Aadhan document retrieval testing
**Usage**: `./test_aadhan_retrieval.sh`
**Tests**:
- Specific document search
- Retrieval accuracy
- Response quality

---

### Chat Feature Testing

#### `test_chat_compliance_fix.sh`
**Purpose**: Chat compliance fix validation
**Usage**: `./test_chat_compliance_fix.sh`
**Tests**:
- Compliance rules in chat
- Content filtering
- Response validation

---

#### `test_chat_amazon.sh`
**Purpose**: Amazon-specific chat testing
**Usage**: `./test_chat_amazon.sh`
**Tests**:
- Amazon product queries
- Scraping integration
- Response formatting

---

#### `test_response_quality_fix.sh`
**Purpose**: Response quality improvement testing
**Usage**: `./test_response_quality_fix.sh`
**Tests**:
- Response relevance
- Source quality
- Answer completeness

---

### Phase Testing

#### `test_phase6_with_estimate_one.py`
**Purpose**: Phase 6 with Estimate One project testing
**Usage**: `python test_phase6_with_estimate_one.py`
**Tests**:
- Phase 6 features
- Estimate One integration
- Output validation

---

#### `test_phase6_eda_endpoints.py`
**Purpose**: Phase 6 EDA endpoints testing
**Usage**: `python test_phase6_eda_endpoints.py`
**Tests**:
- EDA API endpoints
- Download functionality
- Response format

---

#### `phase6_tests.sh`
**Purpose**: Phase 6 comprehensive testing
**Usage**: `./phase6_tests.sh`
**Tests**:
- All Phase 6 features
- Integration
- Regression prevention

---

#### `test_extraction_verbose.py`
**Purpose**: Verbose extraction testing
**Usage**: `python test_extraction_verbose.py`
**Tests**:
- Detailed extraction logs
- Step-by-step validation
- Error diagnostics

---

## Debugging Scripts

### RAG Pipeline Debugging

#### `debug_rag_pipeline.py`
**Purpose**: Comprehensive RAG pipeline debugging
**Usage**:
```bash
python debug_rag_pipeline.py "your query here"
python debug_rag_pipeline.py --analyze-documents
python debug_rag_pipeline.py --test-embedding "test text"
```

**Features**:
- Trace full RAG flow
- Check embeddings
- Analyze chunking
- Test thresholds
- Query classification
- Retrieval analysis

**Output**: Detailed diagnostic report

---

### Document Debugging

#### `diagnose_chunks.py`
**Purpose**: Document chunking analysis
**Usage**: `python diagnose_chunks.py`
**Features**:
- Chunk size distribution
- Overlap analysis
- Content quality
- Embedding coverage

**Output**: Chunking statistics and recommendations

---

### Web Scraping Inspection

#### `inspect_screener.py`
**Purpose**: Screener.in page inspection
**Usage**: `python inspect_screener.py`
**Features**:
- CSS selector discovery
- Page structure analysis
- Data availability check
- Selector validation

**Output**: Recommended CSS selectors

---

#### `inspect_drenting.py`
**Purpose**: Drenting website inspection
**Usage**: `python inspect_drenting.py`
**Features**:
- Page structure
- Element identification
- Content extraction

---

#### `inspect_drenting_detailed.py`
**Purpose**: Detailed Drenting analysis
**Usage**: `python inspect_drenting_detailed.py`
**Features**:
- Deep structure analysis
- All selectors
- Content mapping

---

#### `inspect_new_website.py`
**Purpose**: Generic website inspection
**Usage**: `python inspect_new_website.py <url>`
**Features**:
- Auto-detect structure
- Suggest selectors
- Identify content blocks

---

### Monitoring

#### `monitor_thresholds.sh`
**Purpose**: Real-time threshold monitoring
**Usage**: `./monitor_thresholds.sh`
**Features**:
- Watch retrieval scores
- Track threshold effectiveness
- Alert on anomalies

**Output**: Continuous monitoring display

---

## Maintenance Scripts

#### `scraper_service_working.py`
**Purpose**: Working scraper service reference implementation
**Usage**: Reference only
**Features**:
- Known-good implementation
- Template for fixes
- Best practices

---

#### `fix_scraper_indentation.py`
**Purpose**: Auto-fix scraper code indentation issues
**Usage**: `python fix_scraper_indentation.py`
**Features**:
- Detect indentation errors
- Auto-correct
- Validate syntax

---

#### `auto_endpoint.py`
**Purpose**: Auto-generate API endpoints
**Usage**: `python auto_endpoint.py <spec_file>`
**Features**:
- Generate boilerplate
- Create routes
- Add validation

---

## Script Usage Patterns

### Quick Testing Pattern

```bash
# 1. Start services
docker-compose up -d

# 2. Run comprehensive test
./test_comprehensive_chatbot.sh

# 3. Check logs if issues
docker-compose logs backend | grep ERROR

# 4. Debug specific issue
cd backend && python debug_rag_pipeline.py "test query"
```

### Development Testing Pattern

```bash
# 1. Make code changes
# Edit files...

# 2. Rebuild
docker-compose build backend

# 3. Restart
docker-compose up -d backend

# 4. Run targeted tests
./test_rag_pipeline.py

# 5. Validate
./test_e2e_complete.sh
```

### Debugging Pattern

```bash
# 1. Identify issue from logs
docker-compose logs backend | grep ERROR

# 2. Run diagnostic script
python debug_rag_pipeline.py "failing query"

# 3. Inspect specific component
python inspect_screener.py

# 4. Validate fix
./test_comprehensive_chatbot.sh
```

---

## Prerequisites

### Common Requirements

- Docker and Docker Compose running
- All services started: `docker-compose up -d`
- Database initialized: `./scripts/setup/setup-database.sh`
- Python 3.11+ for Python scripts
- Bash for shell scripts

### Service-Specific Requirements

**RAG Testing**:
- Documents uploaded
- Embeddings generated
- PostgreSQL with pgvector

**Web Scraping Testing**:
- Playwright installed
- Browser dependencies
- Network access

**Project Estimator Testing**:
- Sample files in `docs/features/project_estimator/estimate_one/`
- LLM API keys configured
- State directory: `/tmp/project_estimator_states/`

**LLM Testing**:
- API keys set in environment
- Ollama running (for local models)
- Models pulled

---

## Interpreting Test Results

### Successful Test

```
✓ Test passed
✓ All checks completed
✓ Output validated
Status: SUCCESS
```

### Failed Test

```
✗ Test failed
Error: [specific error message]
Expected: X
Got: Y
Status: FAILED
```

### Partial Success

```
⚠ Test completed with warnings
- Warning 1: [description]
- Warning 2: [description]
Status: PARTIAL
```

---

## Best Practices

### Before Running Tests

1. **Check service health**: `docker-compose ps`
2. **Check backend logs**: `docker-compose logs --tail=50 backend`
3. **Verify prerequisites**: Database initialized, models available
4. **Clear caches if needed**: `docker-compose exec redis redis-cli FLUSHALL`

### After Running Tests

1. **Review output**: Check for errors or warnings
2. **Check logs**: Look for any exceptions
3. **Validate state**: Ensure system in expected state
4. **Clean up**: Remove test data if needed

### Test Development

1. **Start small**: Test one feature at a time
2. **Add assertions**: Validate all outputs
3. **Handle errors**: Proper error messages
4. **Document**: Add usage instructions
5. **Make idempotent**: Tests should be repeatable

---

## Troubleshooting Tests

### Test Hangs

```bash
# Check if service is responding
curl http://localhost:8000/health

# Check for deadlocks
docker-compose logs backend | grep -E "(deadlock|timeout)"

# Restart services
docker-compose restart
```

### Test Fails Intermittently

```bash
# Check resource usage
docker stats

# Check for race conditions
# Add delays or retries in test

# Check network issues
docker-compose logs | grep -E "(connection|timeout)"
```

### Test Produces Wrong Results

```bash
# Verify test data
# Check input files exist and are correct

# Verify service state
# Ensure clean state before test

# Run debug script
python debug_rag_pipeline.py "test query"
```

---

## Contributing New Scripts

### Script Template

```bash
#!/usr/bin/env bash
# Script Name: test_new_feature.sh
# Purpose: Test new feature implementation
# Prerequisites: Services running, data loaded
# Usage: ./test_new_feature.sh

set -e  # Exit on error

echo "=================================="
echo "Testing New Feature"
echo "=================================="

# Test setup
# ...

# Run tests
# ...

# Validation
# ...

# Report results
echo "✓ All tests passed"
```

### Adding to Inventory

1. Add script to appropriate directory
2. Update this README with entry
3. Add usage example
4. Document prerequisites
5. Add to OPERATIONS_GUIDE.md if applicable

---

## Related Documentation

- **Operations Guide**: `docs/operations/guides/OPERATIONS_GUIDE.md`
- **Testing Guide**: `docs/testing/TESTING_GUIDE.md`
- **Debug Guide**: `docs/debugging/RAG_DEBUGGING_GUIDE.md`
- **Main Scripts**: `scripts/README.md`

---

**Last Updated**: 2025-11-27
**Maintainer**: DevOps Team
**Version**: 1.0
