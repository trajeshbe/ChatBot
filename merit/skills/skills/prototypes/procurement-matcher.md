# Procurement Matcher

AI-powered procurement and legal case matching system with vendor taxonomy classification.

## What This Skill Does

This skill helps you work with the Procurement Matcher prototype - a multi-functional AI system that matches legal cases, evaluates vendor capabilities, and extracts structured vendor information.

## When to Use This Skill

- Understanding procurement vendor matching systems
- Working with legal case precedent matching
- Implementing vendor taxonomy classification
- Building AI-powered matching algorithms
- Analyzing vendor capabilities against requirements
- Processing legal and procurement documents

## Prototype Location

```
/mnt/d/Data/Projects/KIAA/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/
meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/procurement_matcher/
```

## Key Files

- `app.py` - Main Streamlit application with three modules
- `legal_profile.py` - Legal case matching logic
- `procurement.py` - Procurement vendor matching logic
- `vendor_mapping.py` - Vendor taxonomy classification
- `prompts/` - LLM prompt templates
- `documentation/` - Comprehensive 5-document suite

## Core Capabilities

### 1. Legal Case Matching
- Matches precedent legal cases with current cases
- Focuses on legal issues and reasoning patterns
- Returns confidence scores (0.0-1.0) with justifications
- Excludes commercial terms from evaluation
- Batch processing of multiple precedents

### 2. Procurement Vendor Matching
- Evaluates vendor capabilities against requirements
- Analyzes feature and capability alignment
- Provides detailed match justifications
- Excludes pricing/commercial terms
- Structured comparison output

### 3. Vendor Taxonomy Classification
- Extracts structured information from vendor descriptions
- Categories: vendor info, services, compliance, geography, risk, sustainability
- Comprehensive vendor profiling
- Unstructured text to structured data conversion

## Technical Stack

- **Framework**: Streamlit for multi-module interface
- **AI Model**: OpenAI GPT-4o-mini via LangChain
- **Data Validation**: Pydantic models for structured output
- **PDF Processing**: PyMuPDF for document text extraction
- **Language**: Python 3.8+

## Common Tasks

### Review System Architecture
```bash
cd /mnt/d/Data/Projects/KIAA/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/procurement_matcher
cat documentation/02_technical_architecture.md
```

### Examine Matching Logic
```bash
# Legal case matching
cat legal_profile.py

# Procurement matching
cat procurement.py

# Vendor taxonomy
cat vendor_mapping.py
```

### Review API Reference
```bash
cat documentation/03_api_reference.md
```

### Run the Application
```bash
streamlit run app.py
```

## Key Components

### Legal Profile Module
- **Purpose**: Match legal precedents with current cases
- **Input**: Current case (TXT), precedent cases (PDF batch)
- **Output**: Confidence scores with justifications
- **Focus**: Legal issues, reasoning, case law analysis

### Procurement Module
- **Purpose**: Match vendor capabilities with requirements
- **Input**: Requirements (TXT), vendor profiles (PDF batch)
- **Output**: Match scores with feature analysis
- **Focus**: Capabilities, qualifications, technical fit

### Vendor Taxonomy Module
- **Purpose**: Extract structured vendor information
- **Input**: Unstructured vendor description (TXT/PDF)
- **Output**: Structured taxonomy data (JSON)
- **Categories**:
  - Vendor information (name, size, location)
  - Services and products
  - Compliance and certifications
  - Geographic coverage
  - Risk factors
  - Sustainability practices

## Documentation Structure

1. **README.md** - Documentation index and quick start
2. **01_overview.md** - System overview and features
3. **02_technical_architecture.md** - Architecture and design
4. **03_api_reference.md** - Complete API documentation
5. **04_user_guide.md** - End-user instructions
6. **05_deployment_guide.md** - Deployment procedures

## Use Cases

### Legal Departments
- Find relevant case precedents quickly
- Analyze legal issue similarity
- Support case research with AI assistance

### Procurement Teams
- Evaluate vendor responses against RFPs
- Match vendor capabilities to requirements
- Automate initial vendor screening

### Vendor Management
- Extract structured vendor data from documents
- Build vendor capability databases
- Analyze vendor profiles systematically

## Data Models

### Legal Match Output
```python
{
    "confidence_score": 0.85,
    "justification": "Strong alignment on contract law issues...",
    "key_similarities": [...],
    "key_differences": [...]
}
```

### Procurement Match Output
```python
{
    "overall_match_score": 0.78,
    "feature_matches": [...],
    "capability_assessment": "...",
    "gaps": [...]
}
```

### Vendor Taxonomy Output
```python
{
    "vendor_info": {...},
    "services": [...],
    "compliance": [...],
    "geography": [...],
    "risk_factors": [...],
    "sustainability": {...}
}
```

## Integration Points

- OpenAI API for GPT-4o-mini model access
- LangChain for prompt management and orchestration
- Pydantic for data validation and structured output
- Streamlit for multi-tab user interface
- PyMuPDF for PDF text extraction

## Configuration

- API keys via `.env` file
- Model settings in `config.yaml`
- Data paths for input/output files
- Temperature and token limits configurable

## Best Practices

1. **File Preparation**: Use text-based PDFs, clear TXT files
2. **Batch Sizes**: Process 5-20 items at a time for optimal performance
3. **Validation**: Always review AI results with manual verification
4. **Prompts**: Customize prompts for domain-specific terminology
5. **API Management**: Monitor costs and rate limits

## Limitations

- Prototype status (no production authentication)
- Session-based (no persistent storage)
- Synchronous processing only
- Limited to OpenAI models
- File size limits not enforced
- English language only

## Example Workflows

### Legal Case Matching Workflow
1. Upload current case description (TXT)
2. Upload precedent cases (PDF batch)
3. System extracts text from PDFs
4. AI analyzes legal issues and reasoning
5. Results show confidence scores and justifications
6. Export results as dataframe

### Procurement Matching Workflow
1. Upload procurement requirements (TXT)
2. Upload vendor profiles (PDF batch)
3. System processes vendor capabilities
4. AI matches features against requirements
5. Results show match scores and gaps
6. Review and shortlist vendors

### Vendor Taxonomy Workflow
1. Upload vendor description (TXT or PDF)
2. System extracts unstructured text
3. AI categorizes into taxonomy structure
4. Results show structured vendor profile
5. Export to structured database

## Performance Considerations

- Processing time: 5-10 seconds per document
- Batch processing recommended for efficiency
- Large PDFs may require text extraction optimization
- API rate limits apply to concurrent requests

## Security Considerations

- No built-in authentication (prototype)
- API keys in environment variables
- File uploads stored temporarily
- Data sent to OpenAI API
- Consider on-premise LLM for sensitive data

## Related Prototypes

- **Planning Classifier** - Similar document classification approach
- **Vendor Recommendation** - Vendor matching and recommendation
- **Tender Intelligence** - Procurement opportunity matching

## Quick Reference

**Modules**: Legal Matching, Procurement Matching, Vendor Taxonomy
**AI Model**: GPT-4o-mini
**Input Formats**: PDF, TXT
**Output**: Dataframes with scores and justifications
**Tech Stack**: Python, Streamlit, LangChain, OpenAI, Pydantic
