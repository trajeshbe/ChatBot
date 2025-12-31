# TalentSearch

AI-powered job posting analysis, recruiter matching, and semantic search platform.

## What This Skill Does

This skill helps you work with TalentSearch - an intelligent job recruitment platform that uses LLMs and semantic search to automatically tag job postings, match them with specialized recruiters, and enable advanced search capabilities.

## When to Use This Skill

- Understanding intelligent job posting systems
- Implementing recruiter matching algorithms
- Working with semantic search for recruitment
- Building job taxonomy classifiers
- Analyzing recruitment workflows
- Creating AI-powered staffing platforms

## Prototype Location

```
/mnt/d/Data/Projects/KIAA/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/
meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/talent_search/
```

## Key Files

- `app.py` - Main Streamlit application entry point
- `config.ini` - Configuration settings
- `recruiter.json` - Recruiter profiles and specializations
- `interface/` - UI components (alerts, search, upload, recruiter)
- `utils/` - Utility modules (prompts, templates, logging, config)
- `data/` - Sample data and taxonomy files

## Core Capabilities

### 1. Intelligent Job Posting Analysis
- Automated metadata extraction from job descriptions
- Domain and sector classification using predefined taxonomies
- Seniority level identification (Intern to Senior Leadership)
- Work arrangement detection (remote, hybrid, onsite)
- Contract type classification
- Salary range extraction
- Location parsing (city, country, region)

### 2. Recruiter Matching System
- AI-powered recruiter assignment based on job characteristics
- Relevance scoring (0-100) with detailed justification
- Multi-criteria matching: industry, location, seniority
- Specialized recruiter profiles for different sectors
- Automated alert routing to relevant recruiters

### 3. Advanced Search Capabilities
- **Natural Language Search**: Semantic understanding of queries
- **SQL-based Querying**: LLM-generated SQL from natural language
- **Keyword Search**: Traditional text-based search
- **Multi-filter Search**: Real-time filtering by multiple criteria
- **Semantic Embeddings**: ChromaDB vector search

### 4. Alert Management
- Recruiter-specific job alerts
- Filtering by recruiter assignments
- Comprehensive job posting views
- Real-time notification system

### 5. Data Upload and Processing
- Excel (.xlsx) and CSV (.csv) support
- Tagged and untagged data processing
- Automated metadata generation
- SQLite database storage
- Full-text search indexing

## Technical Stack

- **Framework**: Streamlit for web interface
- **AI/ML**: OpenAI GPT-4o-mini, Sentence Transformers
- **Orchestration**: LangChain for LLM chains
- **Vector DB**: ChromaDB for semantic search
- **Database**: SQLite for job storage
- **Data**: Pandas for manipulation
- **PDF**: PyMuPDF for document processing
- **Monitoring**: LangSmith for LLM tracing

## Common Tasks

### Review Architecture
```bash
cd /mnt/d/Data/Projects/KIAA/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/talent_search
cat documentation/ARCHITECTURE.md
```

### Examine Components
```bash
# Upload interface
cat interface/upload.py

# Search functionality
cat interface/search.py

# Recruiter matching
cat interface/recruiter.py

# Custom prompts
cat utils/custom_prompts.py
```

### Run Application
```bash
streamlit run app.py
```

## Recruiter Profiles

### 6 Specialized Recruiters

1. **Alex Morgan** - Finance Specialist
   - Industries: Finance, Investment Banking, Fintech
   - Regions: Global financial centers
   - Seniority: All levels

2. **Jordan Lee** - Engineering & Infrastructure
   - Industries: Energy, Construction, Environmental
   - Regions: EMEA, Americas
   - Seniority: Technical roles

3. **Taylor Brooks** - Supply Chain & Logistics
   - Industries: Transportation, Warehousing, Distribution
   - Regions: Global
   - Seniority: Mid-senior to Senior

4. **Casey Blake** - Life Sciences
   - Industries: Pharmaceuticals, Biotechnology, Medical
   - Regions: North America, Europe
   - Seniority: Research to Executive

5. **Riley Anderson** - IT & Technology
   - Industries: Cybersecurity, Software, Cloud
   - Regions: Global tech hubs
   - Seniority: Developer to CTO

6. **Morgan Bennett** - Legal & Regulatory
   - Industries: Corporate Law, Compliance, Regulatory
   - Regions: Major legal markets
   - Seniority: Associate to Partner

## Seniority Levels

- **Intern**: Entry-level, internships
- **Junior**: 0-2 years experience
- **Mid-senior**: 3-7 years experience
- **Senior**: 7-15 years experience
- **Senior Leadership**: C-suite, VP, Director

## Data Flow

```
Upload Job Data
    ↓
Extract Metadata (LLM)
    ↓
Store in SQLite + ChromaDB
    ↓
Match with Recruiters (LLM)
    ↓
Generate Alerts
    ↓
Enable Search (Semantic + SQL)
```

## Job Metadata Schema

```python
{
    "job_title": str,
    "company": str,
    "domain": str,           # Primary industry
    "sector": str,           # Sub-sector
    "seniority_level": str,  # Career level
    "work_arrangement": str, # Remote/Hybrid/Onsite
    "contract_type": str,    # Permanent/Contract/Temporary
    "salary_min": int,
    "salary_max": int,
    "city": str,
    "country": str,
    "region": str,
    "matched_recruiter": str,
    "relevance_score": int,  # 0-100
    "match_justification": str
}
```

## Search Capabilities

### Natural Language Examples
```
"Find software engineer jobs in London"
"Show me all remote finance roles"
"List senior positions matched to Alex Morgan"
"What IT jobs are available in Germany?"
"Find high-paying legal roles"
```

### Query Processing
1. User enters natural language query
2. GPT-4o-mini understands intent
3. System generates SQL or semantic search
4. Query executes against database
5. Results filtered and ranked
6. Displayed with relevant metadata

### Semantic Search Features
- Embedding-based similarity
- Context-aware matching
- Handles synonyms and variations
- Cross-lingual understanding
- Relevance ranking

## Use Cases

### For Recruitment Agencies
- Automatically categorize incoming job postings
- Route jobs to specialized recruiters efficiently
- Track job distributions by industry/location
- Analyze market trends and demand

### For HR Departments
- Organize internal job postings
- Match positions with recruiter expertise
- Generate analytics on hiring needs
- Monitor requisition status

### For Job Boards
- Enhance search with semantic capabilities
- Provide intelligent job recommendations
- Improve user experience with better filtering
- Enable natural language search

### For Staffing Platforms
- Automate job classification workflows
- Optimize recruiter workload distribution
- Improve placement success rates
- Reduce time-to-fill metrics

## Integration Points

- OpenAI API for GPT-4o-mini
- LangChain for prompt chaining
- LangSmith for monitoring
- ChromaDB for vector storage
- SQLite for structured data
- Sentence Transformers for embeddings

## Configuration

### config.ini
```ini
[default]
output_columns = job_title,company,domain,sector,seniority_level
db_path = db
input_path = input

[llm]
llm_model = gpt-4o-mini
model_provider = openai
temperature = 0
max_tokens = 10000
```

### Environment Variables
```bash
OPEN_AI_KEY=your_openai_key
LANGCHAIN_KEY=your_langchain_key
```

## Best Practices

1. **Data Quality**: Clean, consistent job descriptions
2. **Taxonomy Alignment**: Use standard domain/sector classifications
3. **Recruiter Profiles**: Keep recruiter specializations updated
4. **Search Optimization**: Combine semantic and keyword search
5. **Monitoring**: Track LLM costs and performance

## Limitations

- Requires OpenAI API access (paid service)
- LLM processing time-intensive for large datasets
- Sample processing limited to 2 records per upload (configurable)
- Company name hardcoded to "citibank" in some flows
- Requires stable internet connection
- English language optimized

## Example Workflows

### Job Upload and Classification Workflow
1. Upload Excel/CSV with job postings
2. System extracts metadata using LLM
3. Jobs classified into taxonomies
4. Recruiter matching performed
5. Relevance scores calculated
6. Data stored in database
7. Search index updated

### Recruiter Alert Workflow
1. New job classified and matched
2. Relevant recruiters identified
3. Relevance score calculated with justification
4. Alert generated for recruiter
5. Recruiter reviews job details
6. Takes action on opportunity

### Semantic Search Workflow
1. User enters natural language query
2. Query embedded as vector
3. Semantic similarity search performed
4. Results ranked by relevance
5. Metadata displayed
6. User drills into job details

## Performance Considerations

- Metadata extraction: 5-10 seconds per job (LLM)
- Semantic search: <1 second
- SQL search: <100ms
- Database storage: <50ms per record
- Batch uploads recommended for efficiency

## Related Prototypes

- **TalentPulse** - Resume screening and candidate evaluation
- **Taxonomy SkillMatch** - Skills taxonomy matching
- **Taxonomy Classification** - General taxonomy classification

## Quick Reference

**Primary Function**: Intelligent job posting analysis and recruiter matching
**Key Features**: Auto-tagging, recruiter matching, semantic search, alerts
**AI Model**: GPT-4o-mini with sentence embeddings
**Data Sources**: Excel, CSV files
**Search Types**: Natural language, semantic, SQL, filters
**Recruiters**: 6 specialized profiles
**Seniority Levels**: 5 tiers (Intern to Senior Leadership)
**Tech Stack**: Python, Streamlit, LangChain, OpenAI, ChromaDB, SQLite
