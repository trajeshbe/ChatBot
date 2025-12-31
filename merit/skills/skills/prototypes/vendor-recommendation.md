# Vendor Recommendation

AI-powered tender-to-vendor matching and recommendation system.

## What This Skill Does

This skill helps you work with the Vendor Recommendation prototype - an AI system that matches tender documents with vendor profiles, providing relevance scores and recommendations for optimal vendor-tender pairings.

## When to Use This Skill

- Understanding tender-vendor matching systems
- Implementing AI-powered recommendation engines
- Working with PDF document analysis for procurement
- Building vendor evaluation systems
- Analyzing tender requirements against capabilities
- Creating procurement automation tools

## Prototype Location

```
/mnt/d/Data/Projects/KIAA/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/
meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/vendor_recommendation/
```

## Key Files

- `app.py` - Main Streamlit application (3KB)
- `tender_mapping.py` - Tender analysis logic (2.6KB)
- `vendor.py` - Vendor profile processing (2.2KB)
- `tender_prompt.py` - Tender analysis prompts
- `vendor_prompt.py` - Vendor matching prompts
- `utils.py` - Utility functions
- `config_reader.py` - Configuration management
- `log_writer.py` - Logging utilities (2KB)
- `data/` - Sample tender and vendor data
- `documentation/` - Technical documentation

## Core Capabilities

### Tender Analysis
- Extracts key requirements from tender PDFs
- Identifies technical specifications
- Analyzes scope of work
- Determines evaluation criteria
- Categorizes tender complexity

### Vendor Profiling
- Processes vendor profile text files
- Extracts capabilities and experience
- Identifies certifications and qualifications
- Analyzes past performance
- Maps vendor strengths

### Matching and Scoring
- AI-powered tender-vendor matching
- Relevance scores (0-100)
- Detailed match justifications
- Gap analysis (vendor vs requirements)
- Multi-criteria evaluation

### Recommendation Generation
- Ranks vendors by match score
- Provides evidence-based recommendations
- Highlights strengths and gaps
- Suggests focus areas for proposals
- Supports shortlisting decisions

## Technical Stack

- **Framework**: Streamlit for web interface
- **AI Model**: OpenAI GPT-4o-mini via LangChain
- **PDF Processing**: PyMuPDF for tender extraction
- **Configuration**: YAML-based config management
- **Logging**: Custom logging with structured output
- **Language**: Python 3.8+

## Common Tasks

### Review Code
```bash
cd /mnt/d/Data/Projects/KIAA/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/vendor_recommendation

# Main application
cat app.py

# Tender analysis
cat tender_mapping.py

# Vendor processing
cat vendor.py

# Prompts
cat tender_prompt.py
cat vendor_prompt.py
```

### Run Application
```bash
streamlit run app.py
```

### Check Configuration
```bash
cat config.yaml
```

### Review Sample Data
```bash
ls data/
```

## Data Flow

```
1. Upload Tender PDF(s)
   ↓
2. Extract Text from PDFs
   ↓
3. AI Analyzes Tender Requirements
   ↓
4. Upload Vendor Profile (TXT)
   ↓
5. AI Processes Vendor Capabilities
   ↓
6. Match Vendor to Tenders
   ↓
7. Calculate Relevance Scores
   ↓
8. Generate Recommendations
```

## Key Components

### TenderMapping Class
- **Purpose**: Extract and analyze tender requirements
- **Methods**:
  - `extract_tender_info()` - Parse tender documents
  - `analyze_requirements()` - Identify key criteria
  - `assess_complexity()` - Evaluate tender complexity

### VendorProfile Class
- **Purpose**: Process and structure vendor information
- **Methods**:
  - `parse_profile()` - Extract vendor details
  - `identify_capabilities()` - Map skills and services
  - `get_certifications()` - List qualifications

### Matching Engine
- Compares vendor capabilities to tender requirements
- Calculates multi-dimensional match scores
- Generates detailed justifications
- Identifies gaps and opportunities

## Matching Criteria

### Technical Fit
- Required technologies and platforms
- Technical expertise alignment
- Solution architecture match
- Integration capabilities

### Experience
- Relevant project experience
- Industry domain knowledge
- Similar engagement history
- Client references in sector

### Capabilities
- Team skills and expertise
- Service offerings alignment
- Delivery methodology fit
- Innovation and approach

### Compliance
- Certifications and accreditations
- Regulatory compliance
- Security standards
- Quality assurance

### Commercial
- Company size and scale
- Geographic coverage
- Pricing competitiveness
- Contract terms flexibility

## Scoring System

### Relevance Score (0-100)
- **90-100**: Excellent match, highly recommended
- **75-89**: Strong match, recommended
- **60-74**: Good match, consider with caveats
- **40-59**: Moderate match, significant gaps exist
- **0-39**: Poor match, not recommended

### Score Components
Each score considers:
- Requirement alignment (40%)
- Experience relevance (30%)
- Capability match (20%)
- Compliance and certifications (10%)

## Output Format

### Recommendation Structure
```python
{
    "vendor_name": str,
    "tender_title": str,
    "relevance_score": int,  # 0-100
    "justification": str,
    "strengths": List[str],
    "gaps": List[str],
    "recommendations": List[str],
    "risk_factors": List[str]
}
```

### Example Output
```
Vendor: TechCorp Solutions
Tender: Cloud Migration Project
Relevance Score: 87/100

Strengths:
- Extensive AWS cloud experience (10+ projects)
- ISO 27001 certified
- Previous UK public sector work
- Strong technical team

Gaps:
- Limited Azure experience
- No specific healthcare sector projects
- Team size may be small for project scale

Recommendations:
- Focus proposal on AWS expertise
- Partner for Azure components
- Highlight adaptability and learning capability
- Emphasize public sector experience

Risk Level: Medium-Low
```

## Use Cases

### Procurement Teams
- Shortlist vendors for tenders
- Objective vendor evaluation
- Reduce evaluation time
- Ensure compliance alignment

### Vendors/Suppliers
- Identify best-fit opportunities
- Understand competitive positioning
- Prepare targeted proposals
- Prioritize bid efforts

### Consultants
- Support client tender processes
- Vendor market analysis
- Procurement strategy
- Due diligence support

## Integration Points

- OpenAI API for GPT-4o-mini
- LangChain for prompt orchestration
- PyMuPDF for PDF processing
- Streamlit for user interface
- YAML for configuration
- Custom logging infrastructure

## Configuration

### config.yaml
```yaml
model:
  name: gpt-4o-mini
  temperature: 0.0
  max_tokens: 2000

data_path: data/

logging:
  level: INFO
  path: logs/
```

### Environment Variables
```bash
OPENAI_API_KEY=your_api_key_here
```

## Best Practices

1. **Tender Documents**: Use clear, detailed PDFs
2. **Vendor Profiles**: Comprehensive capability descriptions
3. **Multiple Vendors**: Compare multiple vendors per tender
4. **Score Interpretation**: Use scores as guidance, not absolute truth
5. **Gap Analysis**: Focus on addressing identified gaps in proposals
6. **Validation**: Manual review of AI recommendations

## Limitations

- Prototype status (not production-ready)
- No persistent storage
- Single-user interface
- Limited to PDF and TXT inputs
- Requires OpenAI API access
- English language optimized
- No automated vendor database

## Example Workflows

### Basic Matching Workflow
1. Upload tender document(s) (PDF)
2. System extracts requirements
3. Upload vendor profile (TXT)
4. System analyzes capabilities
5. AI generates match scores
6. Review recommendations
7. Export results

### Multi-Vendor Comparison Workflow
1. Upload single tender PDF
2. Upload multiple vendor profiles
3. System matches each vendor to tender
4. Compare scores side-by-side
5. Review strengths and gaps for each
6. Shortlist top vendors
7. Generate comparison report

### Bid/No-Bid Decision Workflow
1. Upload tender opportunity
2. Upload your company profile
3. Review relevance score
4. Analyze gaps and requirements
5. Consider risks identified
6. Make bid/no-bid decision
7. If bid: use recommendations for proposal

## Performance Considerations

- PDF processing: 2-5 seconds per document
- Text extraction quality depends on PDF format
- AI analysis: 5-10 seconds per vendor-tender pair
- Concurrent processing limited by API rates
- Large batches require sequential processing

## Logging and Monitoring

### Log Structure
```
logs/
└── YYYY-MM-DD/
    └── tender_recommendations.log
```

### Log Contents
- Timestamp for each operation
- Tender and vendor processed
- Relevance scores calculated
- Processing time
- Errors and warnings

## Customization Options

### Prompt Customization
- Modify `tender_prompt.py` for tender analysis
- Adjust `vendor_prompt.py` for vendor evaluation
- Add domain-specific criteria
- Include regulatory requirements

### Scoring Customization
- Adjust score component weights
- Add custom evaluation criteria
- Set threshold scores for categories
- Include risk assessment factors

### Output Customization
- Additional metadata fields
- Custom report formats
- Integration with procurement systems
- Automated email notifications

## Related Prototypes

- **Tender Intelligence** - Comprehensive tender platform
- **Procurement Matcher** - Procurement and legal matching
- **SpendSmart** - Procurement analytics

## Comparison with Related Systems

### vs Procurement Matcher
- **Vendor Recommendation**: Tender → Vendor matching
- **Procurement Matcher**: Requirements → Vendor matching + legal cases

### vs Tender Intelligence
- **Vendor Recommendation**: Focused on vendor matching
- **Tender Intelligence**: Full tender platform with search, AI assistant, analytics

## Quick Reference

**Primary Function**: Match tenders to vendors with AI-powered recommendations
**Input**: Tender PDFs, Vendor profile TXT files
**Output**: Relevance scores (0-100), justifications, recommendations
**AI Model**: GPT-4o-mini via LangChain
**Key Features**: Tender analysis, vendor profiling, matching, scoring, recommendations
**Use Cases**: Vendor shortlisting, bid/no-bid decisions, competitive analysis
**Tech Stack**: Python, Streamlit, LangChain, OpenAI, PyMuPDF
