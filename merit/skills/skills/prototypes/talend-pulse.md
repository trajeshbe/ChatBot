# TalentPulse

AI-powered resume screening and candidate evaluation system for recruitment automation.

## What This Skill Does

This skill helps you work with TalentPulse (note: directory is `talend_pulse`) - an AI system that automates resume screening by parsing job descriptions and matching candidates with detailed scoring.

## When to Use This Skill

- Understanding AI-powered recruitment systems
- Implementing resume parsing and analysis
- Building candidate evaluation algorithms
- Working with job description extraction
- Analyzing hiring workflows with AI
- Creating HR automation prototypes

## Prototype Location

```
/mnt/d/Data/Projects/KIAA/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/
meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/talend_pulse/
```

## Key Files

- `app.py` - Main Streamlit application
- `prompts.py` - LLM prompt templates for screening
- `templates.py` - Pydantic data models
- `utils.py` - Utility functions
- `config.ini` - Configuration settings
- `samples/` - Sample job descriptions and resumes
- `documentation/` - Comprehensive 5-document suite

## Core Capabilities

### Job Description Parsing
- Extracts structured requirements from unstructured JDs
- Identifies required skills, qualifications, experience
- Categorizes must-have vs nice-to-have requirements
- Understands context and implicit requirements

### Resume Analysis
- Parses PDF resumes automatically
- Extracts candidate skills, experience, education
- Maps experience to job requirements
- Identifies gaps and strengths

### Candidate Scoring
- Objective evaluation against job requirements
- Detailed scores with justifications
- Skills match assessment
- Experience level alignment
- Cultural fit indicators

### Comparative Analysis
- Ranks multiple candidates objectively
- Side-by-side comparison
- Highlights differentiators
- Supports shortlisting decisions

## Technical Stack

- **Framework**: Streamlit for web interface
- **AI Model**: OpenAI GPT-4o-mini via LangChain
- **PDF Processing**: PyMuPDF for resume extraction
- **Data Processing**: Pandas for results management
- **Monitoring**: LangSmith for LLM debugging
- **Language**: Python 3.8+

## Common Tasks

### Review Architecture
```bash
cd /mnt/d/Data/Projects/KIAA/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/talend_pulse
cat documentation/02_TECHNICAL_ARCHITECTURE.md
```

### Examine Prompts
```bash
# Review screening prompts
cat prompts.py
```

### Check Data Models
```bash
# Pydantic templates
cat templates.py
```

### Review Business Value
```bash
cat documentation/04_BUSINESS_VALUE.md
```

### Run Application
```bash
streamlit run app.py
```

## Workflow

### Complete Screening Process
1. **Upload Job Description** (PDF or TXT)
2. **JD Parsing** - AI extracts structured requirements
3. **Upload Resumes** - Batch upload candidate CVs (PDF)
4. **Resume Analysis** - AI extracts candidate profiles
5. **Matching** - System scores each candidate against requirements
6. **Results** - Detailed scores and justifications displayed
7. **Comparison** - Side-by-side candidate comparison
8. **Export** - Download results for further analysis

## Scoring System

### Overall Match Score (0-100)
- Composite score across all criteria
- Weighted by requirement priority
- Accounts for must-have requirements

### Detailed Criteria Scores
- **Skills Match**: Technical and soft skills alignment
- **Experience Level**: Years and relevance of experience
- **Education**: Degree and certifications match
- **Domain Knowledge**: Industry and domain expertise
- **Cultural Fit**: Values and work style alignment

### Justification Components
- Specific strengths identified
- Gap analysis
- Evidence from resume
- Recommendations for interview focus

## Data Models

### Job Description Schema
```python
{
    "title": str,
    "required_skills": List[str],
    "nice_to_have_skills": List[str],
    "experience_required": str,
    "education_required": str,
    "responsibilities": List[str]
}
```

### Candidate Profile Schema
```python
{
    "name": str,
    "skills": List[str],
    "experience": List[dict],
    "education": List[dict],
    "overall_score": float,
    "detailed_scores": dict,
    "justification": str
}
```

## Use Cases

### HR Departments
- Screen large volumes of applications quickly
- Reduce initial screening time by 90%
- Ensure consistent evaluation criteria
- Focus interviewer time on qualified candidates

### Recruitment Agencies
- Process multiple clients' requirements
- Rapid candidate matching
- Quality assurance in screening
- Scalable to any volume

### Hiring Managers
- Objective candidate comparison
- Data-driven hiring decisions
- Reduced bias in screening
- Documented evaluation rationale

### Talent Acquisition Teams
- Pipeline management
- Candidate pool analysis
- Skills gap identification
- Market intelligence on talent availability

## Key Benefits

### Efficiency Gains
- **90% time savings** in resume screening
- Process 100+ resumes in minutes
- Automated initial screening
- Focus on high-potential candidates

### Quality Improvements
- **Consistent evaluation** across all candidates
- Objective, data-driven decisions
- Reduced unconscious bias
- Standardized scoring criteria

### Scalability
- Handle any volume of applications
- No degradation in quality
- Parallel processing capability
- Rapid turnaround times

### Transparency
- Detailed justifications for all scores
- Evidence-based recommendations
- Audit trail for decisions
- Explainable AI outputs

## Integration Points

- OpenAI API for GPT-4o-mini model
- LangChain for prompt orchestration
- PyMuPDF for PDF resume parsing
- Streamlit for user interface
- LangSmith for monitoring and debugging

## Configuration

### config.ini
```ini
[LLM]
model = gpt-4o-mini
temperature = 0.0
max_tokens = 2000

[Screening]
batch_size = 10
score_threshold = 70
```

### Prompt Customization
- Prompts stored in `prompts.py`
- Easily customizable for different roles
- Domain-specific terminology support
- Company culture integration

## Best Practices

1. **JD Quality**: Provide clear, detailed job descriptions
2. **Resume Format**: Use text-based PDFs (not scanned images)
3. **Batch Sizes**: Process 5-20 resumes at a time
4. **Validation**: Always review AI results with manual verification
5. **Calibration**: Adjust scoring thresholds based on market

## Limitations

- Prototype status (no production authentication)
- No persistent storage (session-based)
- Synchronous processing only
- Limited to OpenAI models
- English language optimized
- No ATS integration (standalone)

## Example Results

### Sample Output
```
Candidate: Jane Smith
Overall Score: 87/100

Detailed Scores:
- Skills Match: 92/100
- Experience Level: 85/100
- Education: 90/100
- Domain Knowledge: 82/100

Strengths:
- Strong Python and ML skills (5 years experience)
- Relevant education (MS in Computer Science)
- Industry experience in fintech

Gaps:
- Limited cloud architecture experience
- No Kubernetes certification

Recommendation: Strong candidate for interview
Focus areas: Cloud deployment, containerization
```

## Performance Considerations

- Processing time: 5-10 seconds per resume
- JD parsing: 3-5 seconds
- Batch processing recommended for efficiency
- API rate limits apply to large volumes

## ROI Analysis

### Time Savings
- Manual screening: 10 minutes per resume
- AI screening: <1 minute per resume
- For 100 applicants: 15 hours → 1.5 hours saved

### Quality Improvements
- Consistent evaluation criteria
- No fatigue-related errors
- Comprehensive skills assessment
- Documented decision rationale

### Cost Reduction
- Reduced hiring cycle time
- Lower cost-per-hire
- Better candidate quality
- Reduced turnover from better matches

## Documentation Structure

1. **01_OVERVIEW.md** - System introduction and capabilities
2. **02_TECHNICAL_ARCHITECTURE.md** - Architecture and design
3. **03_USER_GUIDE.md** - Usage instructions and workflows
4. **04_BUSINESS_VALUE.md** - ROI analysis and business case
5. **05_DEPLOYMENT_GUIDE.md** - Deployment and operations

## Related Prototypes

- **TalentSearch** - Job posting analysis and recruiter matching
- **Taxonomy SkillMatch** - Skills taxonomy and matching
- **Planning Classifier** - Similar document classification approach

## Quick Reference

**Primary Function**: Automated resume screening and candidate evaluation
**Key Features**: JD parsing, resume analysis, scoring, comparison
**AI Model**: GPT-4o-mini
**Time Savings**: 90% reduction in screening time
**Input Formats**: PDF (resumes, JDs), TXT (JDs)
**Output**: Scores, justifications, rankings
**Tech Stack**: Python, Streamlit, LangChain, OpenAI, PyMuPDF
