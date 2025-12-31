# Taxonomy SkillMatch

AI-powered resume and skills classification using hierarchical job taxonomy.

## What This Skill Does

This skill helps you work with the Taxonomy SkillMatch prototype - an AI system that classifies resumes and profiles against a 4-level job industry taxonomy (Industry → Domain → Group → Sub-Group) with relevancy scoring.

## When to Use This Skill

- Understanding skills-based taxonomy matching
- Implementing resume classification systems
- Working with hierarchical job taxonomies
- Building candidate-job matching algorithms
- Analyzing skills against industry standards
- Creating recruitment taxonomy tools

## Prototype Location

```
/mnt/d/Data/Projects/KIAA/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/
meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/taxonomy_skillmatch/
```

## Key Files

- `taxonomy.py` - Main Streamlit application
- `config.py` - Configuration loader
- `log.py` - Logging utilities
- `config.yaml` - Configuration settings
- `requirements.txt` - Python dependencies
- `documentation/` - Technical documentation

## Core Capabilities

### Resume Taxonomy Classification
- Classifies resumes against 4-level job taxonomy
- **Level 1**: Industry (e.g., Technology, Finance, Healthcare)
- **Level 2**: Domain (e.g., Software Development, Investment Banking)
- **Level 3**: Group (e.g., Web Development, Trading)
- **Level 4**: Sub-Group (e.g., Frontend Developer, Equity Trader)

### Relevancy Scoring
- Provides relevancy score (0.0-1.0) for each classification
- Scores indicate how well resume matches each taxonomy level
- Multiple top matches with scores
- Evidence-based scoring from resume content

### Multi-level Analysis
- Analyzes skills at multiple taxonomy levels
- Identifies primary and secondary career paths
- Maps experience to industry standards
- Supports career transition analysis

## Technical Stack

- **Framework**: Streamlit for web interface
- **AI Model**: OpenAI GPT-4o-mini via LangChain
- **Validation**: Pydantic for structured output
- **Logging**: Custom logging with date-based organization
- **Language**: Python 3.8+

## Common Tasks

### Review Code
```bash
cd /mnt/d/Data/Projects/KIAA/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/taxonomy_skillmatch

# Main application
cat taxonomy.py

# Configuration
cat config.py

# Logging
cat log.py
```

### Run Application
```bash
streamlit run taxonomy.py
```

### Check Configuration
```bash
cat config.yaml
```

## Data Models

### Taxonomy Output Model
```python
{
    "industry": str,      # Level 1: Type of industry
    "domain": str,        # Level 2: Domain within industry
    "group": str,         # Level 3: Group within domain
    "sub_group": str,     # Level 4: Specific job role
    "scores": float       # Relevancy score (0.0-1.0)
}
```

### Classification Result
```python
{
    "results": [
        {
            "industry": "Technology",
            "domain": "Software Development",
            "group": "Web Development",
            "sub_group": "Full Stack Developer",
            "scores": 0.89
        },
        # Additional matches...
    ]
}
```

## Taxonomy Hierarchy

### 4-Level Structure

**Level 1: Industry**
- Broad industry categories (Technology, Finance, Healthcare, etc.)

**Level 2: Domain**
- Specialized domains within each industry
- Example (Technology): Software, Hardware, Networking, Data Science

**Level 3: Group**
- Functional groups within each domain
- Example (Software): Web Dev, Mobile Dev, Backend, Frontend

**Level 4: Sub-Group**
- Specific job roles and titles
- Example (Web Dev): Full Stack Developer, Frontend Engineer, Backend Engineer

### Example Taxonomy Path
```
Technology
  └─ Software Development
      └─ Web Development
          └─ Full Stack Developer
```

## Use Cases

### Recruitment and Staffing
- Automatically classify candidate resumes
- Match candidates to job openings
- Identify transferable skills
- Support career path planning

### HR and Talent Management
- Analyze workforce skill distribution
- Identify skills gaps
- Plan training and development
- Support internal mobility

### Career Services
- Help job seekers identify career options
- Suggest alternative career paths
- Analyze skills against market demand
- Provide career guidance

### Workforce Analytics
- Analyze talent pool composition
- Track skills trends
- Benchmark against industry standards
- Support strategic workforce planning

## Key Components

### ContentClassification Class
- Main classification engine
- LangChain integration
- Pydantic output parsing
- Multi-level taxonomy handling

### Configuration Module
- Loads settings from config.yaml
- Manages API keys and model settings
- Configurable taxonomy paths

### Logging Module
- Structured logging
- Date-based log organization
- Error tracking
- Performance monitoring

### Streamlit UI
- Resume text input
- Real-time classification
- Results display with scores
- Export functionality

## Integration Points

- OpenAI API for GPT-4o-mini
- LangChain for prompt orchestration
- Pydantic for data validation
- Streamlit for user interface
- Custom logging infrastructure

## Configuration

### config.yaml
```yaml
llm:
  model: gpt-4o-mini
  temperature: 0.0
  max_tokens: 2000

taxonomy:
  levels: 4

logging:
  level: INFO
  path: logs/
```

### Environment Variables
```bash
OPENAI_API_KEY=your_api_key_here
```

## Best Practices

1. **Resume Quality**: Provide detailed, well-formatted resumes
2. **Taxonomy Design**: Ensure taxonomy is comprehensive and current
3. **Score Interpretation**: Review high-scoring matches manually
4. **Multi-match Analysis**: Consider multiple classifications
5. **Regular Updates**: Keep taxonomy aligned with market trends

## Limitations

- Prototype status (no production features)
- No persistent storage
- Single resume processing at a time
- Limited to predefined taxonomy structure
- English language optimized
- Requires OpenAI API access

## Example Workflows

### Resume Classification Workflow
1. User uploads or pastes resume text
2. System extracts key skills and experience
3. AI analyzes against 4-level taxonomy
4. Top matches identified with scores
5. Results displayed hierarchically
6. User reviews and exports classifications

### Batch Analysis Workflow (Programmatic)
1. Load batch of resumes
2. Initialize classifier
3. Process each resume
4. Aggregate classifications
5. Analyze distribution across taxonomy
6. Generate insights report

### Career Path Analysis Workflow
1. Classify current resume
2. Identify primary path (highest score)
3. Identify secondary paths
4. Suggest related roles
5. Map career progression options

## Scoring Interpretation

### Score Ranges
- **0.8 - 1.0**: Excellent match, highly relevant
- **0.6 - 0.8**: Good match, relevant skills present
- **0.4 - 0.6**: Moderate match, some transferable skills
- **0.2 - 0.4**: Weak match, limited relevance
- **0.0 - 0.2**: Poor match, minimal alignment

### Factors Influencing Scores
- Direct experience in taxonomy level
- Relevant skills mentioned
- Time spent in related roles
- Education and certifications
- Project experience
- Industry terminology usage

## Performance Considerations

- Classification time: 5-10 seconds per resume
- Token usage depends on resume length
- API rate limits apply
- Longer resumes may require text truncation

## Customization Options

### Taxonomy Customization
- Define custom industry taxonomies
- Adjust hierarchy levels
- Add domain-specific categories
- Update role definitions

### Scoring Customization
- Adjust score weighting by level
- Prioritize certain taxonomy branches
- Account for career transitions
- Include recency factors

### Output Customization
- Number of top matches returned
- Additional metadata inclusion
- Score threshold filtering
- Visualization formats

## Related Prototypes

- **TalentPulse** - Resume screening and evaluation
- **TalentSearch** - Job posting and recruiter matching
- **Taxonomy Classification** - General taxonomy classification

## Comparison with TalentPulse

### TalentPulse
- Focuses on job-resume matching
- Scores candidates against specific JD
- One-to-one comparison

### Taxonomy SkillMatch
- Focuses on taxonomy classification
- Maps to standard job categories
- One-to-many classification
- Industry-standard taxonomies

## Quick Reference

**Primary Function**: Classify resumes against 4-level job taxonomy
**Taxonomy Levels**: Industry → Domain → Group → Sub-Group
**AI Model**: GPT-4o-mini via LangChain
**Output**: Multi-level classifications with relevancy scores
**Input**: Resume text (PDF, TXT, or paste)
**Scoring**: 0.0 to 1.0 relevancy scores
**Use Cases**: Recruitment, HR, career services, workforce analytics
**Tech Stack**: Python, Streamlit, LangChain, OpenAI, Pydantic
